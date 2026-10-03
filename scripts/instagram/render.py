#!/usr/bin/env python3
"""Deterministic SVG -> Instagram JPEG renderer with a real recovery chain.

Why this exists
---------------
A one-liner `rsvg-convert … && convert …` in a workflow has no way to notice
that it produced a blank frame, a stretched image or nothing at all — and the
previous version of this pipeline published exactly such files.

Rendering therefore goes through a chain that must *prove* its output:

    Retry 1  primary renderer, corrected options
    Retry 2  fallback renderer (resvg / inkscape / ImageMagick)
    Retry 3  rebuilt source (re-serialised SVG with enforced canvas geometry)
    fail    -> non-zero exit, nothing is committed, publishing stays blocked

Every attempt is rasterised first (PNG) and only converted to JPEG after the
raster passes an in-memory check: exact target geometry, real decodable pixels,
not blank and not a flat fill.  Alpha is flattened onto the artwork's own border
colour so a transparent canvas can never turn into a white (or black) rectangle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mediacheck as mc                                  # noqa: E402
from mediacheck import Toolchain                          # noqa: E402

GEOMETRY = {"story": (1080, 1920), "post": (1080, 1350)}


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
DEFAULT_QUALITY = int(os.environ.get("JPEG_QUALITY", "95"))
BLANK_STD_FLOOR = 0.006
FLAT_COLOR_FLOOR = 2


@dataclass
class Renderer:
    name: str
    kind: str                 # 'rsvg' | 'resvg' | 'inkscape' | 'imagemagick'
    path: str

    def version(self) -> str:
        if self.kind == "pyresvg":
            try:
                import resvg_py
                return f"resvg {getattr(resvg_py, '__resvg_version__', '?')} (python binding)"
            except Exception:
                return self.path
        for flag in ("--version", "-version", "-v"):
            try:
                res = subprocess.run([self.path, flag], stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True,
                                     timeout=30, errors="replace")
                line = mc.first_line(res.stdout)
                if line:
                    return line
            except (OSError, subprocess.SubprocessError):
                continue
        return self.path


def resvg_py_available() -> bool:
    try:
        import resvg_py  # noqa: F401
        return True
    except Exception:
        return False


def discover_renderers() -> List[Renderer]:
    """Return renderers in preference order (best fidelity first)."""
    found: List[Renderer] = []
    for name, kind in (("rsvg-convert", "rsvg"), ("resvg", "resvg"), ("inkscape", "inkscape")):
        path = shutil.which(name)
        if path:
            found.append(Renderer(name, kind, path))
    # The resvg Python binding is a fully independent Rust renderer; it is used
    # for cross-checking when present (and for authoring on machines without apt).
    if resvg_py_available():
        found.append(Renderer("resvg-py", "pyresvg", "python:resvg_py"))
    for name, kind in (("magick", "imagemagick"), ("convert", "imagemagick")):
        path = shutil.which(name)
        if path:
            found.append(Renderer(name, kind, path))
            break
    return found


def font_dirs_for_render() -> List[str]:
    """Directories handed to in-process renderers so fonts resolve identically."""
    dirs = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "assets", "fonts"),
        os.path.expanduser("~/.fonts"),
        os.path.expanduser("~/.local/share/fonts"),
        "/usr/share/fonts",
        "/usr/local/share/fonts",
    ]
    return [d for d in dirs if os.path.isdir(d)]


# --------------------------------------------------------------------------
# rasterisation
# --------------------------------------------------------------------------

class _Result:
    """Minimal stand-in for CompletedProcess for in-process renderers."""

    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def rasterize(rnd: Renderer, svg: str, png: str, width: int, height: int,
              variant: int = 0):
    """Rasterise `svg` to `png` at exactly width x height."""
    if rnd.kind == "pyresvg":
        try:
            import resvg_py
            data = resvg_py.svg_to_bytes(
                svg_path=svg,
                width=width,
                height=height,
                font_dirs=font_dirs_for_render(),
                font_family="Vazirmatn",
                sans_serif_family="Vazirmatn",
            )
            if not data:
                return _Result(1, stderr="resvg returned no bytes")
            with open(png, "wb") as fh:
                fh.write(bytes(data))
            return _Result(0)
        except Exception as exc:  # noqa: BLE001 — surfaced in the attempt log
            return _Result(1, stderr=f"{type(exc).__name__}: {exc}")
    if rnd.kind == "rsvg":
        cmd = [rnd.path, "-f", "png", "-w", str(width), "-h", str(height)]
        if variant == 1:
            cmd += ["--dpi", "96"]
        cmd += ["-o", png, svg]
        return mc.run(cmd)
    if rnd.kind == "resvg":
        cmd = [rnd.path, "--width", str(width), "--height", str(height)]
        if variant == 1:
            cmd.append("--zoom")
            cmd.append("1")
        cmd += [svg, png]
        return mc.run(cmd)
    if rnd.kind == "inkscape":
        cmd = [rnd.path, svg, f"--export-filename={png}", f"--export-width={width}",
               f"--export-height={height}"]
        if variant == 1:
            cmd += ["--export-background=#000000", "--export-background-opacity=255"]
        return mc.run(cmd)
    # ImageMagick: use -density and explicit -resize so the box is exact.
    prefix = [rnd.path, "convert"] if os.path.basename(rnd.path) == "magick" else [rnd.path]
    cmd = prefix + ["-background", "none", "-density", "96", svg, "-resize",
                    f"{width}x{height}!", "-strip", png]
    if variant == 1:
        cmd = prefix + ["-background", "none", "-density", "192", svg,
                        "-resize", f"{width}x{height}!", "-strip", png]
    return mc.run(cmd)


def raster_ok(tc: Toolchain, png: str, width: int, height: int) -> Tuple[bool, str]:
    """Verify a freshly written raster before it is allowed to become a JPEG."""
    if not os.path.exists(png) or os.path.getsize(png) == 0:
        return False, "rasteriser produced no output file"
    meta = mc.read_meta(tc, png)
    if not meta.decodable:
        return False, f"raster is not decodable ({meta.raw[:60]!r})"
    if (meta.width, meta.height) != (width, height):
        return False, f"raster is {meta.dimensions}, expected {width}x{height}"
    stats = mc.decode_stats(tc, png)
    if not stats.ok:
        return False, stats.error
    if stats.unique_colors >= 0 and stats.unique_colors < FLAT_COLOR_FLOOR:
        return False, f"raster is a single flat fill ({stats.unique_colors} colour(s))"
    if stats.gray_std < BLANK_STD_FLOOR:
        return False, f"raster is blank (pixel std {stats.gray_std:.4f})"
    return True, f"std={stats.gray_std:.4f} mean={stats.gray_mean:.4f} colors={stats.unique_colors}"


# --------------------------------------------------------------------------
# recovery helpers
# --------------------------------------------------------------------------

def rebuild_svg(svg: str, out_svg: str, width: int, height: int) -> str:
    """Re-serialise an SVG with enforced canvas geometry (Retry 3)."""
    tree = ET.parse(svg)
    root = tree.getroot()
    root.set("width", str(width))
    root.set("height", str(height))
    view_box = root.get("viewBox")
    if not view_box:
        root.set("viewBox", f"0 0 {width} {height}")
    else:
        parts = [p for p in view_box.replace(",", " ").split() if p]
        if len(parts) == 4:
            # Preserve the drawing units, only normalise the origin.
            root.set("viewBox", " ".join(parts))
    tree.write(out_svg, encoding="utf-8", xml_declaration=True)
    return out_svg


def border_color_hex(tc: Toolchain, png: str) -> str:
    """Pick a flatten backdrop from the raster's own opaque border pixels."""
    vals = tc.identify_fmt("%[fx:mean.r]|%[fx:mean.g]|%[fx:mean.b]",
                           f"{png}[1x1+0+0]")
    parsed = None
    if "|" in vals:
        try:
            parsed = [float(v) for v in vals.split("|")[:3]]
        except ValueError:
            parsed = None
    if not parsed:
        return "#000000"
    return mc.rgb_to_hex(parsed)


def to_jpeg(tc: Toolchain, png: str, jpg: str, quality: int) -> Tuple[bool, str]:
    """Convert the verified raster to a publish-grade JPEG."""
    backdrop = border_color_hex(tc, png)
    res = tc.to_jpeg(png, jpg, quality=quality, background=backdrop, flatten=True)
    if not os.path.exists(jpg) or os.path.getsize(jpg) == 0:
        return False, f"conversion produced no output ({mc.first_line(res.stderr)})"
    if not mc.jpeg_magic_ok(jpg):
        return False, "output is not a valid JPEG (magic bytes wrong)"

    meta = mc.read_meta(tc, jpg)
    if not meta.is_jpeg:
        return False, f"output decodes as {meta.fmt or 'unknown'}, not JPEG"
    if not meta.decodable:
        return False, "output JPEG has no decodable pixels"
    if meta.sampling and meta.sampling.strip() != mc.SAMPLING_444:
        return False, f"chroma subsampling is {meta.sampling!r}, expected 4:4:4"
    if meta.colorspace.lower() != "srgb":
        return False, f"colourspace is {meta.colorspace!r}, expected sRGB"
    if meta.has_alpha:
        return False, "JPEG still carries an alpha channel"
    if os.path.getsize(jpg) > 8 * 1024 * 1024:
        return False, f"output is {os.path.getsize(jpg) / 1048576:.1f} MB (> 8 MB Instagram limit)"

    # Structural difference against the raster (catches a trashed conversion).
    diff = mc.rmse(tc, png, jpg)
    if diff is not None and diff > 0.08:
        return False, f"converted JPEG differs from the raster (RMSE {diff:.3f})"
    return True, f"quality={quality} sampling=4:4:4 backdrop={backdrop} size={os.path.getsize(jpg)}"


# --------------------------------------------------------------------------
# main render loop
# --------------------------------------------------------------------------

def render_one(tc: Toolchain, renderers: Sequence[Renderer], svg: str, jpg: str,
               kind: str, quality: int, log=print,
               provenance: Optional[dict] = None) -> bool:
    width, height = GEOMETRY[kind]
    log(f"  source : {svg}")
    log(f"  target : {jpg}  ({width}x{height}, JPEG q{quality}, sRGB, 4:4:4)")

    if not os.path.exists(svg):
        log(f"  [FAIL] source SVG does not exist")
        return False

    tmpdir = tempfile.mkdtemp(prefix="render-")
    png = os.path.join(tmpdir, "raster.png")
    attempts: List[Tuple[Renderer, int, str]] = []
    for index, rnd in enumerate(renderers):
        attempts.append((rnd, 0, f"retry 1: {rnd.name} (primary options)"))
        attempts.append((rnd, 1, f"retry 2: {rnd.name} (corrected options)"))
    # Retry 3: rebuild the SVG from its own source and re-render.
    rebuilt = os.path.join(tmpdir, "rebuilt.svg")
    for rnd in renderers[:1]:
        attempts.append((rnd, 0, "retry 3: rebuilt source SVG"))

    for rnd, variant, label in attempts:
        log(f"  {label} [{rnd.version()[:60]}]")
        source = svg
        if label.startswith("retry 3"):
            try:
                rebuild_svg(svg, rebuilt, width, height)
                source = rebuilt
                log(f"    rebuilt canvas geometry -> {width}x{height}")
            except ET.ParseError as exc:
                log(f"    rebuild failed: {exc}")
                continue
        res = rasterize(rnd, source, png, width, height, variant)
        ok, detail = raster_ok(tc, png, width, height)
        if not ok:
            stderr = mc.first_line(res.stderr)[:120]
            log(f"    raster rejected: {detail}" + (f" | {stderr}" if stderr else ""))
            continue
        log(f"    raster OK: {detail}")
        cooked, detail2 = to_jpeg(tc, png, jpg, quality)
        if not cooked:
            log(f"    conversion rejected: {detail2}")
            continue
        log(f"    JPEG OK: {detail2}")
        log(f"  result : PASS via {rnd.name}")
        if provenance is not None:
            provenance[jpg] = {
                "renderer": rnd.name,
                "renderer_version": rnd.version(),
                "attempt": label,
                "quality": quality,
                "output_sha256": file_sha256(jpg),
                "rendered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        shutil.rmtree(tmpdir, ignore_errors=True)
        return True

    log("  result : FAIL — every renderer, option set and rebuild failed")
    shutil.rmtree(tmpdir, ignore_errors=True)
    return False


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Render Instagram media deterministically")
    ap.add_argument("--root", default=".")
    ap.add_argument("--quality", type=int, default=DEFAULT_QUALITY)
    ap.add_argument("--only", default=None, help="render a single source SVG")
    ap.add_argument("--kind", choices=("story", "post"), default=None)
    ap.add_argument("--list-renderers", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    renderers = discover_renderers()
    if args.list_renderers:
        for rnd in renderers:
            print(f"{rnd.name}\t{rnd.version()}")
        return 0 if renderers else 1

    tc = Toolchain.detect()
    tc.require()

    print("=" * 78)
    print("RENDER — deterministic SVG -> Instagram JPEG")
    print("=" * 78)
    if not renderers:
        print("[FAIL] no SVG renderer found (install librsvg2-bin)")
        return 1
    for rnd in renderers:
        print(f"renderer available: {rnd.name} — {rnd.version()[:70]}")
    print(f"ImageMagick       : {tc.versions.get('imagemagick', 'unknown')}")
    print("")

    if args.only:
        targets = [(os.path.relpath(os.path.abspath(args.only), root).replace(os.sep, "/"),
                    args.kind or ("post" if args.only.startswith(os.path.join(root, "posts"))
                                  or "/posts/" in args.only.replace("\\", "/") else "story"))]
    else:
        targets = []
        for sub, kind in (("stories", "story"), ("posts", "post")):
            base = os.path.join(root, sub)
            if not os.path.isdir(base):
                continue
            for dirpath, _dirs, files in os.walk(base):
                for name in sorted(files):
                    if name.lower().endswith(".svg"):
                        full = os.path.join(dirpath, name)
                        targets.append((os.path.relpath(full, root).replace(os.sep, "/"), kind))

    if not targets:
        print("[WARN] no source SVG found — nothing to render")
        return 0

    print(f"{len(targets)} source SVG(s) to render\n")
    provenance: Dict[str, dict] = {}
    failed: List[str] = []
    for rel, kind in targets:
        jpg = os.path.splitext(rel)[0] + ".jpg"
        ok = render_one(tc, renderers, os.path.join(root, rel), os.path.join(root, jpg),
                        kind, args.quality, provenance=provenance)
        print(f"  -> {rel}: {'OK' if ok else 'FAILED'}\n")
        if not ok:
            failed.append(rel)

    log_path = os.path.join(root, "reports", "render-log.json")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as fh:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "commit_sha": os.environ.get("GITHUB_SHA", ""),
            "quality": args.quality,
            "assets": dict(sorted(provenance.items())),
        }, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"render log: reports/render-log.json ({len(provenance)} asset(s))")
    print("=" * 78)
    if failed:
        print(f"RENDER FAILED for {len(failed)} source(s):")
        for rel in failed:
            print(f"  - {rel}")
        print("FINAL STATUS: BLOCKED")
        print("REASON: rendering failed; nothing will be committed and publishing stays blocked")
        return 1
    print(f"RENDER: PASS ({len(targets)} file(s) rendered and pixel-verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
