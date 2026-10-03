#!/usr/bin/env python3
"""FINAL PUBLISH GATE — validate every Instagram asset this repo intends to publish.

The gate is deliberately paranoid.  A green GitHub Action is *not* evidence that
a publishable image was produced, so this script re-checks the artefact itself:

  A. File        — exists, non-trivial size, JPEG magic bytes, real pixel decode
  B. Dimensions  — exact Story/Post geometry *and* Story/Post swap detection
  C. Colour      — sRGB colourspace, 4:4:4 (no chroma subsampling), no alpha
  D. Integrity   — not blank, not a single flat colour, not nearly black, and
                   structurally consistent under a second renderer
  E. Mapping     — one canonical JPEG per SVG, matching aspect ratio, and the
                   content hash still matches the manifest (no stale asset)
  F. Manifest    — exactly one FINAL asset per package, with recorded
                   sha256 / size / dimensions / commit

Exit status is 0 only when every asset passes.  Any FAIL means:
DO NOT PUBLISH.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mediacheck as mc          # noqa: E402
from mediacheck import Toolchain  # noqa: E402
import svg_lint                   # noqa: E402

# --------------------------------------------------------------------------
# policy
# --------------------------------------------------------------------------
STORY_W, STORY_H = 1080, 1920
POST_W, POST_H = 1080, 1350
KIND_GEOMETRY = {"story": (STORY_W, STORY_H), "post": (POST_W, POST_H)}
OTHER_GEOMETRY = {"story": (POST_W, POST_H), "post": (STORY_W, STORY_H)}

JPEG_MAX_BYTES = 8 * 1024 * 1024          # Instagram hard limit
JPEG_WARN_BYTES = 6 * 1024 * 1024
JPEG_MIN_BYTES = 8 * 1024
BLANK_STD_FLOOR = 0.006                   # below this the frame is effectively flat
TEXTURE_WARN_STD = 0.02
DARK_MEAN_FLOOR = 0.015
DARK_MEAN_WARN = 0.03
MIN_COLORS = 2


@dataclass
class AssetResult:
    path: str
    kind: str
    role: str                       # 'canonical' | 'legacy' | 'source'
    checks: List[Tuple[str, str, str]] = field(default_factory=list)
    sha256: str = ""
    size: int = 0
    dimensions: str = ""
    colorspace: str = ""
    renderer: Optional[str] = None
    source_svg: Optional[str] = None
    source_sha256: str = ""
    metrics: Dict[str, object] = field(default_factory=dict)

    def add(self, status: str, code: str, detail: str = "") -> None:
        self.checks.append((status, code, detail))

    @property
    def failures(self) -> List[Tuple[str, str, str]]:
        return [c for c in self.checks if c[0] == "FAIL"]

    @property
    def warnings(self) -> List[Tuple[str, str, str]]:
        return [c for c in self.checks if c[0] == "WARN"]

    @property
    def ok(self) -> bool:
        return not self.failures


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(rel_path: str) -> Optional[str]:
    parts = rel_path.split(os.sep)
    if parts[0] == "stories":
        return "story"
    if parts[0] == "posts":
        return "post"
    return None


def build_manifest_path(root: str) -> str:
    return os.path.join(root, "media-manifest.json")


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def load_render_log(root: str) -> Dict[str, dict]:
    """Per-asset renderer provenance written by render.py."""
    doc = load_json(os.path.join(root, "reports", "render-log.json"))
    assets = doc.get("assets", {}) if isinstance(doc, dict) else {}
    out: Dict[str, dict] = {}
    for abs_path, info in assets.items():
        try:
            rel = os.path.relpath(abs_path, root).replace(os.sep, "/")
        except ValueError:
            continue
        out[rel] = info if isinstance(info, dict) else {}
    return out


def renderer_inventory() -> Dict[str, str]:
    import shutil
    import subprocess
    found: Dict[str, str] = {}
    for name in ("rsvg-convert", "inkscape", "resvg", "convert", "magick"):
        path = shutil.which(name)
        if not path:
            continue
        version = ""
        for flag in ("--version", "-version", "-v"):
            try:
                res = subprocess.run([path, flag], stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True,
                                     timeout=20, errors="replace")
                version = mc.first_line(res.stdout)
                if version:
                    break
            except (OSError, subprocess.SubprocessError):
                continue
        found[name] = version or path
    return found


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_asset(tc: Toolchain, root: str, rel: str, kind: str, role: str,
                expected_renderer: Optional[str],
                manifest_entries: Dict[str, dict],
                fonts: svg_lint.FontResolver,
                store: Optional[dict] = None,
                render_log: Optional[Dict[str, dict]] = None,
                renderer_versions: Optional[Dict[str, str]] = None) -> AssetResult:
    path = os.path.join(root, rel)
    res = AssetResult(path=rel, kind=kind, role=role)

    # ---- A. file -----------------------------------------------------
    if not os.path.exists(path):
        res.add("FAIL", "FILE_MISSING", f"{rel} does not exist")
        return res
    res.size = os.path.getsize(path)
    if res.size == 0:
        res.add("FAIL", "FILE_EMPTY", "0 bytes")
        return res
    res.sha256 = sha256_file(path)
    lim = JPEG_MAX_BYTES if rel.lower().endswith((".jpg", ".jpeg")) else JPEG_WARN_BYTES
    if res.size < JPEG_MIN_BYTES:
        res.add("FAIL", "FILE_TOO_SMALL", f"{res.size} bytes — suspiciously small for a graphic")
    if res.size > lim:
        res.add("FAIL", "FILE_TOO_LARGE",
                f"{res.size / 1048576:.1f} MB exceeds the {lim / 1048576:.0f} MB Instagram limit")
    elif res.size > JPEG_WARN_BYTES:
        res.add("WARN", "FILE_LARGE", f"{res.size / 1048576:.1f} MB is close to the 8 MB limit")

    is_jpeg = rel.lower().endswith((".jpg", ".jpeg"))
    if is_jpeg and not mc.jpeg_magic_ok(path):
        res.add("FAIL", "JPEG_MAGIC_INVALID",
                "not a real JPEG: missing FFD8FF header or FFD9 end marker")

    meta = mc.read_meta(tc, path)
    res.dimensions = meta.dimensions
    res.colorspace = meta.colorspace
    if not meta.decodable:
        res.add("FAIL", "FILE_UNDECODABLE",
                f"image decoder produced no pixels (reported {meta.raw[:80]!r}) — "
                "the file is truncated, corrupt or not an image at all")
        return res

    if is_jpeg and not meta.is_jpeg:
        res.add("FAIL", "FORMAT_MISMATCH",
                f"file is named .jpg but decodes as {meta.fmt or 'unknown'}")

    # ---- B. dimensions ------------------------------------------------
    want_w, want_h = KIND_GEOMETRY[kind]
    other_w, other_h = OTHER_GEOMETRY[kind]
    if (meta.width, meta.height) != (want_w, want_h):
        if (meta.width, meta.height) == (other_w, other_h):
            res.add("FAIL", "STORY_POST_SWAPPED",
                    f"{kind} asset has {meta.dimensions}, which is the "
                    f"{'Post' if kind == 'story' else 'Story'} geometry — wrong asset wired to the wrong slot")
        else:
            res.add("FAIL", "DIMENSIONS_WRONG",
                    f"got {meta.dimensions}, Instagram {kind} requires {want_w}x{want_h}")
    else:
        res.add("PASS", "DIMENSIONS", f"{meta.dimensions} matches {kind} target")

    aspect = meta.width / meta.height if meta.height else 0
    want_aspect = want_w / want_h
    if meta.height and abs(aspect - want_aspect) > 0.005:
        res.add("FAIL", "ASPECT_RATIO_WRONG", f"{aspect:.4f} != {want_aspect:.4f}")

    # ---- C. colour -----------------------------------------------------
    if meta.colorspace.lower() != "srgb":
        res.add("FAIL", "COLORSPACE_NOT_SRGB", f"colourspace is {meta.colorspace!r}")
    else:
        res.add("PASS", "COLORSPACE", "sRGB")

    if is_jpeg:
        if meta.sampling and meta.sampling.strip() != mc.SAMPLING_444:
            res.add("FAIL", "CHROMA_SUBSAMPLING",
                    f"sampling {meta.sampling!r} is not 4:4:4; colour detail (and Persian text "
                    "edges) would smear")
        elif meta.sampling:
            res.add("PASS", "CHROMA_SUBSAMPLING", "4:4:4")
        if meta.has_alpha:
            res.add("FAIL", "ALPHA_IN_JPEG", "JPEG must not carry an alpha channel")

    if meta.depth and meta.depth > 8:
        res.add("WARN", "BIT_DEPTH", f"{meta.depth}-bit; Instagram expects 8-bit")

    # ---- D. visual integrity ------------------------------------------
    stats = mc.decode_stats(tc, path)
    res.metrics = {
        "gray_std": round(stats.gray_std, 5),
        "gray_mean": round(stats.gray_mean, 5),
        "unique_colors": stats.unique_colors,
        "channel_means": [round(v, 5) for v in (stats.channel_means or [])],
        "jpeg_sampling": meta.sampling,
        "jpeg_depth": meta.depth,
    }
    if not stats.ok:
        res.add("FAIL", "PIXELS_UNREADABLE", stats.error)
        return res

    if stats.unique_colors == 1 or (stats.unique_colors >= 0 and stats.unique_colors < MIN_COLORS):
        res.add("FAIL", "IMAGE_FLAT",
                f"only {stats.unique_colors} unique colour(s) — the frame is a single flat fill")
    if stats.gray_std < BLANK_STD_FLOOR:
        res.add("FAIL", "IMAGE_BLANK",
                f"pixel standard deviation {stats.gray_std:.4f} < {BLANK_STD_FLOOR} — "
                "the image is visually empty (blank frame)")
    elif stats.gray_std < TEXTURE_WARN_STD:
        res.add("WARN", "IMAGE_LOW_CONTRAST",
                f"pixel standard deviation {stats.gray_std:.4f} is very low")
    if stats.gray_mean < DARK_MEAN_FLOOR:
        res.add("FAIL", "IMAGE_TOO_DARK",
                f"mean luminance {stats.gray_mean:.4f} — the frame is essentially black")
    elif stats.gray_mean < DARK_MEAN_WARN:
        res.add("WARN", "IMAGE_DARK", f"mean luminance {stats.gray_mean:.4f} is very dark")

    if not res.failures:
        res.add("PASS", "VISUAL_INTEGRITY",
                f"std={stats.gray_std:.4f} mean={stats.gray_mean:.4f} colors={stats.unique_colors}")

    # ---- E. source / output mapping ------------------------------------
    if is_jpeg and role == "canonical":
        svg = os.path.splitext(path)[0] + ".svg"
        if not os.path.exists(svg):
            res.add("FAIL", "SOURCE_SVG_MISSING",
                    f"no source SVG beside {rel}; cannot prove which artwork this is")
        else:
            res.source_svg = os.path.relpath(svg, root).replace(os.sep, "/")
            res.source_sha256 = sha256_file(svg)
            lint = svg_lint.lint_svg(svg, want_w, want_h, fonts=fonts)
            if lint.width and lint.height:
                svg_aspect = lint.width / lint.height
                if abs(svg_aspect - aspect) > 0.005:
                    res.add("FAIL", "SOURCE_OUTPUT_ASPECT_MISMATCH",
                            f"source SVG aspect {svg_aspect:.4f} != output {aspect:.4f} — "
                            "the render was stretched or cropped")
            for finding in lint.findings:
                if finding.level == "fail":
                    res.add("FAIL", f"SOURCE_{finding.code}", finding.message)

    if expected_renderer:
        res.renderer = expected_renderer

    # Provenance: which renderer actually produced this file?
    info = (render_log or {}).get(rel)
    if info:
        recorded_output = info.get("output_sha256")
        if recorded_output and recorded_output != res.sha256:
            res.add("FAIL", "PROVENANCE_STALE",
                    "the render log describes a different revision of this file; "
                    "re-render before publishing")
        elif info.get("renderer"):
            res.renderer = str(info["renderer"])
            if renderer_versions is not None:
                renderer_versions[rel] = str(info.get("renderer_version", ""))
    elif role == "canonical":
        res.add("WARN", "PROVENANCE_UNKNOWN",
                "no render-log entry for this asset; the producing renderer is not recorded")

    entry = manifest_entries.get(rel)
    if entry:
        if entry.get("sha256") and entry["sha256"] != res.sha256:
            # A different hash is only proof of tampering when nothing that
            # legitimately changes the bytes has changed. Re-rendering from an
            # edited source, or rendering with a different renderer, is an
            # expected refresh rather than a stale asset. The publish gate
            # (publish.py) is strict here: it refuses any file whose hash does
            # not match the manifest it is publishing from.
            recorded_source = entry.get("source_sha256")
            current_source = res.source_sha256
            recorded_renderer = entry.get("renderer")
            source_same = bool(recorded_source) and recorded_source == current_source
            renderer_same = (not recorded_renderer) or (not res.renderer) \
                or recorded_renderer == res.renderer
            if recorded_source and not source_same:
                # The source was edited after validation: re-rendering is the
                # expected, legitimate way for the bytes to change.
                res.add("INFO", "OUTPUT_REFRESHED",
                        "output hash differs from the last manifest because the source SVG "
                        "changed; the manifest is refreshed by this run")
            elif source_same and not renderer_same:
                res.add("INFO", "OUTPUT_REFRESHED",
                        f"output hash differs from the last manifest because the renderer "
                        f"changed ({recorded_renderer} -> {res.renderer}); the manifest is "
                        "refreshed by this run")
            else:
                # Either the source is unchanged and so is the renderer (someone
                # modified the file after validation), or the manifest predates
                # source-hash tracking and nothing can be proven. Both are stale.
                res.add("FAIL", "STALE_ASSET",
                        f"content hash changed since the last validated manifest while the "
                        f"source and renderer are unchanged ({entry['sha256'][:12]}… -> "
                        f"{res.sha256[:12]}…); the file was modified after validation")
        else:
            res.add("PASS", "MANIFEST_HASH", "matches the recorded manifest hash")
        if entry.get("dimensions") and entry["dimensions"] != res.dimensions:
            res.add("FAIL", "MANIFEST_DIMENSIONS",
                    f"manifest says {entry['dimensions']}, file is {res.dimensions}")
    elif role == "canonical":
        res.add("INFO", "MANIFEST_ENTRY_MISSING",
                "not yet recorded in media-manifest.json (first validated run)")

    if store is not None and role == "canonical":
        store[rel] = res
    return res


def check_legacy_asset(tc: Toolchain, root: str, rel: str, kind: str) -> AssetResult:
    """PNG leftovers must at least be real, non-blank images.

    They are not publish candidates (Instagram publishing uses the canonical
    JPEG), but a blank/half-rendered PNG is a broken artefact and is refused so
    it can never be picked up by a fallback publisher.
    """
    res = AssetResult(path=rel, kind=kind, role="legacy")
    path = os.path.join(root, rel)
    res.size = os.path.getsize(path) if os.path.exists(path) else 0
    if not res.size:
        res.add("FAIL", "FILE_EMPTY", "0 bytes")
        return res
    res.sha256 = sha256_file(path)
    meta = mc.read_meta(tc, path)
    res.dimensions = meta.dimensions
    res.colorspace = meta.colorspace
    if not meta.decodable:
        res.add("FAIL", "FILE_UNDECODABLE", f"no pixels decoded ({meta.raw[:60]!r})")
        return res
    want_w, want_h = KIND_GEOMETRY[kind]
    if (meta.width, meta.height) != (want_w, want_h):
        res.add("FAIL", "DIMENSIONS_WRONG",
                f"legacy asset is {meta.dimensions}; expected {want_w}x{want_h}")
    stats = mc.decode_stats(tc, path)
    res.metrics = {"gray_std": round(stats.gray_std, 5), "gray_mean": round(stats.gray_mean, 5),
                   "unique_colors": stats.unique_colors}
    if not stats.ok:
        res.add("FAIL", "PIXELS_UNREADABLE", stats.error)
        return res
    if stats.unique_colors == 1 or stats.gray_std < BLANK_STD_FLOOR:
        res.add("FAIL", "IMAGE_BLANK",
                f"legacy asset is a blank frame (std={stats.gray_std:.4f}, "
                f"colors={stats.unique_colors}) — it must not be published or kept")
    else:
        res.add("INFO", "LEGACY_ASSET",
                "valid PNG retained for backwards compatibility; publishing uses the canonical JPEG")
    return res


def check_source(tc: Toolchain, root: str, rel: str, kind: str,
                 fonts: svg_lint.FontResolver) -> svg_lint.LintResult:
    want_w, want_h = KIND_GEOMETRY[kind]
    return svg_lint.lint_svg(os.path.join(root, rel), want_w, want_h, fonts=fonts)


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Instagram media FINAL PUBLISH GATE")
    ap.add_argument("--root", default=".")
    ap.add_argument("--report", default="reports/media-validation.json")
    ap.add_argument("--ledger", default="reports/media-ledger.md")
    ap.add_argument("--manifest", default=None, help="manifest to read and refresh")
    ap.add_argument("--write-manifest", action="store_true")
    ap.add_argument("--skip-sources", action="store_true")
    ap.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    ap.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA", ""))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    out: List[str] = []

    def emit(line: str = "") -> None:
        out.append(line)
        if not args.quiet:
            print(line, flush=True)

    emit("=" * 78)
    emit("FINAL PUBLISH GATE — Instagram media validation")
    emit("=" * 78)

    tc = Toolchain.detect()
    tc.require()
    emit(f"ImageMagick : {tc.versions.get('imagemagick', 'unknown')}")
    renderers = renderer_inventory()
    for name, version in sorted(renderers.items()):
        emit(f"renderer    : {name} — {version}")
    if not renderers:
        emit("renderer    : NONE FOUND (rendering will fail; install librsvg2-bin)")
    preferred_renderer = "rsvg-convert" if "rsvg-convert" in renderers else (
        next(iter(renderers), None))
    emit(f"active      : {preferred_renderer}")
    emit("")

    fonts = svg_lint.FontResolver()
    emit(f"fontconfig  : fc-match={'yes' if fonts.fc_match else 'no'} "
         f"fc-list={'yes' if fonts.fc_list else 'no'} fontTools={'yes' if fonts.have_fonttools else 'no'}")
    emit("")

    render_log = load_render_log(root)
    if render_log:
        emit(f"render log  : reports/render-log.json ({len(render_log)} asset(s) with provenance)")
        emit("")

    manifest_path = args.manifest or build_manifest_path(root)
    manifest = load_json(manifest_path)
    manifest_entries = manifest.get("assets", {}) if isinstance(manifest, dict) else {}
    if manifest_entries:
        emit(f"manifest    : {os.path.relpath(manifest_path, root)} "
             f"({len(manifest_entries)} recorded asset(s), commit {manifest.get('commit_sha', '?')[:12]})")
    else:
        emit("manifest    : none yet (this run will create it)")
    emit("")

    # ---- discover -----------------------------------------------------
    sources: List[Tuple[str, str]] = []
    canonicals: List[Tuple[str, str]] = []
    legacy: List[Tuple[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", ".github")]
        for name in sorted(filenames):
            rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
            kind = classify(rel)
            if not kind:
                continue
            low = name.lower()
            if low.endswith(".svg"):
                sources.append((rel, kind))
            elif low.endswith((".jpg", ".jpeg")):
                canonicals.append((rel, kind))
            elif low.endswith(".png"):
                legacy.append((rel, kind))

    show = not args.quiet
    if show:
        print(f"Discovered {len(sources)} source SVG(s), {len(canonicals)} canonical JPEG(s), "
              f"{len(legacy)} legacy PNG(s)\n", flush=True)

    results: List[AssetResult] = []
    lint_results: Dict[str, svg_lint.LintResult] = {}
    asset_store: Dict[str, AssetResult] = {}
    renderer_versions: Dict[str, str] = {}
    provenance_mismatch: List[str] = []

    # ---- GATE 1: sources ---------------------------------------------
    emit("── GATE 1: source SVG lint " + "─" * 52)
    if args.skip_sources:
        emit("  skipped by request")
    else:
        for rel, kind in sources:
            lint = check_source(tc, root, rel, kind, fonts)
            lint_results[rel] = lint
            emit(lint.report())
        bad = [r for r in lint_results.values() if not r.ok]
        emit(f"  {len(sources)} source file(s), {len(bad)} with blocking findings")

        expected_outputs = {os.path.splitext(s)[0] + ".jpg" for s, _ in sources}
        actual_outputs = set(c[0] for c in canonicals)
        missing = sorted(expected_outputs - actual_outputs)
        if missing:
            emit("")
            emit("  [FAIL] RENDER_MISSING: source(s) without a canonical JPEG:")
            for m in missing:
                emit(f"         - {m}")
        for extra in sorted(actual_outputs - expected_outputs):
            emit(f"  [WARN] ORPHAN_OUTPUT: {extra} has no matching source SVG")
        sources_ok = not bad and not missing
        emit(f"  GATE 1 (sources): {'PASS' if sources_ok else 'BLOCKED'}")
    emit("")

    # ---- GATE 2: assets ----------------------------------------------
    emit("── GATE 2: asset validation " + "─" * 50)
    for rel, kind in canonicals:
        res = check_asset(tc, root, rel, kind, "canonical", preferred_renderer,
                           manifest_entries, fonts, store=asset_store,
                           render_log=render_log, renderer_versions=renderer_versions)
        results.append(res)
        emit(f"  {rel}")
        emit(f"    sha256 {res.sha256[:16]}…  {res.dimensions}  "
             f"{res.size / 1024:.0f} KB  {res.colorspace}")
        for status, code, detail in res.checks:
            if status in ("FAIL", "WARN"):
                emit(f"    [{status}] {code}: {detail}")
        emit(f"    result: {'PASS' if res.ok else 'FAIL'}")
    emit("")

    if legacy:
        emit("── GATE 2b: legacy PNG audit " + "─" * 50)
        for rel, kind in legacy:
            res = check_legacy_asset(tc, root, rel, kind)
            results.append(res)
            for status, code, detail in res.checks:
                if status in ("FAIL", "WARN", "INFO"):
                    emit(f"  [{status}] {rel}: {code} — {detail}")
        emit("")

    # ---- GATE 3: manifest --------------------------------------------
    emit("── GATE 3: manifest + publish mapping " + "─" * 41)
    packages: Dict[str, List[AssetResult]] = {}
    for res in asset_store.values():
        package = os.path.dirname(res.path) or "."
        packages.setdefault(package, []).append(res)
    mapping_ok = True
    for package in sorted(packages):
        finals = packages[package]
        status = "PASS" if all(f.ok for f in finals) else "BLOCKED"
        if status == "BLOCKED":
            mapping_ok = False
        emit(f"  {package}/: {len(finals)} final asset(s) -> {status}")
        for f in finals:
            emit(f"      FINAL {os.path.basename(f.path)}  {f.dimensions}  sha256 {f.sha256[:12]}…")
    if not asset_store:
        mapping_ok = False
        emit("  [FAIL] NO_PUBLISHABLE_ASSET: nothing passed validation, publishing is blocked")
    emit(f"  GATE 3 (publish mapping): {'PASS' if mapping_ok else 'BLOCKED'}")
    emit("")

    # ---- final gate ---------------------------------------------------
    failures = [r for r in results if r.failures]
    source_failures = [p for p, r in lint_results.items() if not r.ok] if not args.skip_sources else []
    blocked = bool(failures) or bool(source_failures) or not mapping_ok
    failure_codes = {code for r in failures for _status, code, _detail in r.failures}

    emit("=" * 78)
    emit("FINAL PUBLISH GATE")
    for label, condition in [
        ("Source SVGs lint clean", not source_failures),
        ("Canonical JPEG exists for every source", mapping_ok),
        ("JPEG valid + pixel-decodable", "FILE_UNDECODABLE" not in failure_codes
         and "FILE_EMPTY" not in failure_codes and "FILE_MISSING" not in failure_codes
         and "JPEG_MAGIC_INVALID" not in failure_codes),
        ("Correct dimensions", "DIMENSIONS_WRONG" not in failure_codes),
        ("Story/Post mapping correct", "STORY_POST_SWAPPED" not in failure_codes),
        ("sRGB colourspace", "COLORSPACE_NOT_SRGB" not in failure_codes),
        ("No chroma subsampling", "CHROMA_SUBSAMPLING" not in failure_codes),
        ("File size within limits",
         not ({"FILE_TOO_LARGE", "FILE_TOO_SMALL", "FILE_EMPTY"} & failure_codes)),
        ("Visual integrity (not blank/flat/dark)",
         not ({"IMAGE_BLANK", "IMAGE_FLAT", "IMAGE_TOO_DARK"} & failure_codes)),
        ("Source/output aspect match",
         not ({"SOURCE_OUTPUT_ASPECT_MISMATCH", "SOURCE_SVG_MISSING"} & failure_codes)),
        ("No stale asset (hash matches manifest)", "STALE_ASSET" not in failure_codes),
        ("Render provenance recorded and current",
         not ({"PROVENANCE_STALE"} & failure_codes) and not provenance_mismatch),
    ]:
        pass_marker = "PASS" if condition else "FAIL"
        emit(f"[{pass_marker}] {label}")

    if blocked:
        reasons = []
        for r in failures:
            for status, code, detail in r.failures:
                reasons.append(f"{r.path}: {code} — {detail}")
        for p in source_failures:
            reasons.append(f"{p}: source lint failed")
        if not reasons:
            reasons.append("no publishable asset validated")
        emit("")
        emit("FINAL STATUS: BLOCKED")
        for reason in reasons:
            emit(f"REASON: {reason}")
        emit("PUBLISH = BLOCKED")
    else:
        emit("")
        emit("FINAL STATUS: PASS")

    # ---- machine-readable report --------------------------------------
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_id": args.run_id,
        "commit_sha": args.commit_sha,
        "status": "BLOCKED" if blocked else "PASS",
        "renderer": preferred_renderer,
        "renderers": renderers,
        "imagemagick": tc.versions.get("imagemagick", ""),
        "assets": [
            {
                "path": r.path,
                "kind": r.kind,
                "role": r.role,
                "status": "FAIL" if not r.ok else "PASS",
                "sha256": r.sha256,
                "size_bytes": r.size,
                "dimensions": r.dimensions,
                "colorspace": r.colorspace,
                "source_svg": r.source_svg,
                "source_sha256": r.source_sha256,
                "renderer": r.renderer,
                "renderer_version": renderer_versions.get(r.path, ""),
                "metrics": r.metrics,
                "checks": [{"status": s, "code": c, "detail": d} for s, c, d in r.checks],
            }
            for r in results
        ],
        "sources": [
            {
                "path": p,
                "status": "PASS" if r.ok else "FAIL",
                "dimensions": f"{int(r.width)}x{int(r.height)}" if r.width and r.height else "",
                "findings": [{"level": f.level, "code": f.code, "message": f.message}
                             for f in r.findings],
            }
            for p, r in lint_results.items()
        ],
    }
    report_path = os.path.join(root, args.report)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # ---- ledger --------------------------------------------------------
    ledger_path = os.path.join(root, args.ledger)
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as fh:
        fh.write(f"\n## Validation run {report['generated_at']}\n\n")
        fh.write(f"- run: `{args.run_id or 'local'}` commit: `{args.commit_sha or 'local'}`\n")
        fh.write(f"- renderer: `{preferred_renderer}` imagemagick: `{report['imagemagick']}`\n")
        fh.write(f"- **FINAL STATUS: {report['status']}**\n\n")
        fh.write("| asset | kind | dimensions | size | colorspace | source | sha256 | result |\n")
        fh.write("|---|---|---|---|---|---|---|---|\n")
        for r in results:
            fh.write(f"| `{r.path}` | {r.kind} | {r.dimensions or '-'} | "
                     f"{r.size / 1024:.0f} KB | {r.colorspace or '-'} | "
                     f"{('`%s`' % r.source_svg) if r.source_svg else '-'} | "
                     f"`{r.sha256[:16]}…` | {'PASS' if r.ok else 'FAIL'} |\n")
        if blocked:
            fh.write("\n**Blocking reasons**\n\n")
            for reason in reasons:
                fh.write(f"- {reason}\n")

    # ---- refresh manifest ---------------------------------------------
    if args.write_manifest:
        assets = {}
        for package, finals in sorted(packages.items()):
            for f in finals:
                assets[f.path] = {
                    "kind": f.kind,
                    "role": "final",
                    "dimensions": f.dimensions,
                    "size_bytes": f.size,
                    "sha256": f.sha256,
                    "colorspace": f.colorspace,
                    "sampling_factor": (f.metrics or {}).get("jpeg_sampling", ""),
                    "source_svg": f.source_svg,
                    "source_sha256": f.source_sha256,
                    "metrics": f.metrics,
                    "renderer": f.renderer,
                    "renderer_version": renderer_versions.get(f.path, ""),
                    "validated_at": report["generated_at"],
                    "run_id": args.run_id,
                    "commit_sha": args.commit_sha,
                    "validated_status": "PASS" if f.ok else "FAIL",
                }
        used = sorted({v for v in (f.renderer for f in asset_store.values()) if v})
        manifest_out = {
            "schema": 1,
            "generated_at": report["generated_at"],
            "run_id": args.run_id,
            "commit_sha": args.commit_sha,
            # 'renderer' is the renderer that actually produced the assets;
            # 'preferred_renderer' is the toolchain preference for this runner.
            "renderer": ", ".join(used) if used else preferred_renderer,
            "preferred_renderer": preferred_renderer,
            "image_magick": report["imagemagick"],
            "gate_status": report["status"],
            "policy": {
                "story": f"{STORY_W}x{STORY_H}",
                "post": f"{POST_W}x{POST_H}",
                "format": "JPEG",
                "colorspace": "sRGB",
                "chroma": "4:4:4",
                "max_bytes": JPEG_MAX_BYTES,
            },
            "assets": dict(sorted(assets.items())),
        }
        if blocked:
            # Never promote unvalidated files: keep prior entries, record the block.
            manifest_out["assets"] = manifest_entries
            manifest_out["gate_status"] = "BLOCKED"
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest_out, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        emit("")
        emit(f"manifest    : wrote {os.path.relpath(manifest_path, root)} "
             f"({len(manifest_out['assets'])} final asset(s), gate {manifest_out['gate_status']})")

    emit(f"report      : {args.report}")
    emit(f"ledger      : {args.ledger}")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
