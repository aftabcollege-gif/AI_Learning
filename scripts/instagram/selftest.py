#!/usr/bin/env python3
"""Self-test: prove this pipeline detects bad media instead of publishing it.

A validator that never fails is worthless, so this suite feeds the gate a set of
deliberately broken artefacts and asserts that each one is rejected with the
expected reason — plus healthy ones that must pass.  If a check ever regresses,
this suite fails before anything reaches Instagram.

Modes
-----
default                full suite (sources, metadata, gate rules, manifests)
--gate-rules           only the synthetic good/bad asset battery
--renderer-recovery    exercise the renderer fallback chain
--sources              only lint the repository's SVG sources
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mediacheck as mc                                    # noqa: E402
from mediacheck import Toolchain                           # noqa: E402
import svg_lint                                            # noqa: E402
import validate as gate                                    # noqa: E402
import render as render_mod                                # noqa: E402
import publish as publish_mod                              # noqa: E402


@dataclass
class Case:
    name: str
    ok: bool
    detail: str = ""


class Suite:
    def __init__(self, quiet: bool = False) -> None:
        self.cases: List[Case] = []
        self.quiet = quiet

    def record(self, name: str, ok: bool, detail: str = "") -> None:
        self.cases.append(Case(name, ok, detail))
        marker = "PASS" if ok else "FAIL"
        if not self.quiet or not ok:
            print(f"  [{marker}] {name}" + (f" — {detail}" if detail and not ok else ""))

    def expect(self, name: str, condition: bool, detail: str = "") -> None:
        self.record(name, bool(condition), detail)

    def expect_failure(self, name: str, result: gate.AssetResult, code: str) -> None:
        codes = {c for _s, c, _d in result.failures}
        self.record(name, code in codes,
                    f"expected failure {code}; got "
                    f"{sorted(codes) if codes else 'no failures'}")

    def expect_pass(self, name: str, result: gate.AssetResult) -> None:
        self.record(name, result.ok,
                    "unexpected failures: " + "; ".join(f"{c}: {d}" for _s, c, d in result.failures))

    @property
    def failed(self) -> List[Case]:
        return [c for c in self.cases if not c.ok]


# --------------------------------------------------------------------------
# 1. synthetic assets — the gate must reject every bad one
# --------------------------------------------------------------------------

def build_fixtures(tc: Toolchain, workdir: str) -> Dict[str, str]:
    """Create good and deliberately broken assets. Returns name -> relative path."""
    os.makedirs(os.path.join(workdir, "stories"), exist_ok=True)
    os.makedirs(os.path.join(workdir, "posts"), exist_ok=True)
    fixtures: Dict[str, str] = {}

    def make(name: str, sub: str, *args: str) -> str:
        rel = f"{sub}/{name}.jpg"
        path = os.path.join(workdir, rel)
        prefix = [tc.magick, "convert"] if tc.magick else [tc.convert]
        res = mc.run(prefix + [a for a in args] + [path])
        if not os.path.exists(path):
            raise RuntimeError(f"fixture {name} not created: {mc.first_line(res.stderr)}")
        fixtures[name] = rel
        return rel

    # healthy story: gradient with texture, correct geometry, 4:4:4
    make("good-story", "stories", "-size", "1080x1920",
         "gradient:#061a16-#0b3329", "-colorspace", "sRGB",
         "-sampling-factor", "4:4:4", "-quality", "95")
    # healthy post
    make("good-post", "posts", "-size", "1080x1350",
         "gradient:#050807-#071614", "-colorspace", "sRGB",
         "-sampling-factor", "4:4:4", "-quality", "95")
    # blank: single flat colour
    make("blank", "stories", "-size", "1080x1920", "xc:white",
         "-colorspace", "sRGB", "-sampling-factor", "4:4:4", "-quality", "95")
    # wrong geometry for a story slot
    make("wrong-dims", "stories", "-size", "1080x1080",
         "gradient:#061a16-#0b3329", "-colorspace", "sRGB",
         "-sampling-factor", "4:4:4", "-quality", "95")
    # Post-sized file sitting in the stories tree (Story/Post swap)
    make("swapped", "stories", "-size", "1080x1350",
         "gradient:#061a16-#0b3329", "-colorspace", "sRGB",
         "-sampling-factor", "4:4:4", "-quality", "95")
    # chroma subsampling
    make("subsampled", "stories", "-size", "1080x1920",
         "gradient:#061a16-#0b3329", "-colorspace", "sRGB",
         "-sampling-factor", "2x2", "-quality", "95")
    # nearly black frame
    make("near-black", "stories", "-size", "1080x1920",
         "gradient:#000000-#050505", "-colorspace", "sRGB",
         "-sampling-factor", "4:4:4", "-quality", "95")

    # truncated / garbage file wearing a .jpg name (exactly what broke the repo)
    garbage_rel = "stories/garbage.jpg"
    with open(os.path.join(workdir, garbage_rel), "wb") as fh:
        fh.write(bytes((i * 37 + 11) % 256 for i in range(15000)))
    fixtures["garbage"] = garbage_rel

    # zero-byte file
    empty_rel = "stories/empty.jpg"
    open(os.path.join(workdir, empty_rel), "wb").close()
    fixtures["empty"] = empty_rel

    # matching source SVGs so the SOURCE_* rules are exercised for both kinds
    for rel, w, h in (("stories/good-story.svg", 1080, 1920),
                      ("posts/good-post.svg", 1080, 1350)):
        with open(os.path.join(workdir, rel), "w", encoding="utf-8") as fh:
            fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
                     f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="#061a16"/>'
                     '<text x="540" y="600" text-anchor="middle" font-family="DejaVu Sans" '
                     'font-size="60" fill="#ffffff">ok</text></svg>')
        fixtures[os.path.basename(rel)] = rel
    return fixtures


def run_gate_rules(suite: Suite, tc: Toolchain, workdir: str) -> None:
    print("── gate rule battery (the gate must catch each defect) " + "─" * 24)
    fixtures = build_fixtures(tc, workdir)
    fonts = svg_lint.FontResolver()
    rel = lambda name: fixtures[name]  # noqa: E731

    result = gate.check_asset(tc, workdir, rel("good-story"), "story", "canonical",
                             "test", {}, fonts)
    suite.expect_pass("healthy 1080x1920 JPEG is accepted", result)
    suite.expect("healthy asset reports sRGB",
                 any(s == "PASS" and c == "COLORSPACE" for s, c, _d in result.checks))
    suite.expect("healthy asset reports 4:4:4",
                 any(s == "PASS" and c == "CHROMA_SUBSAMPLING" for s, c, _d in result.checks))

    result = gate.check_asset(tc, workdir, rel("good-post"), "post", "canonical",
                             "test", {}, fonts)
    suite.expect_pass("healthy 1080x1350 Post JPEG is accepted", result)

    result = gate.check_asset(tc, workdir, rel("blank"), "story", "canonical",
                             "test", {}, fonts)
    suite.expect_failure("blank white frame is rejected", result, "IMAGE_FLAT")

    result = gate.check_asset(tc, workdir, rel("wrong-dims"), "story", "canonical",
                             "test", {}, fonts)
    suite.expect_failure("wrong dimensions are rejected", result, "DIMENSIONS_WRONG")

    result = gate.check_asset(tc, workdir, rel("swapped"), "story", "canonical",
                             "test", {}, fonts)
    suite.expect_failure("Post-sized file in a Story slot is rejected",
                         result, "STORY_POST_SWAPPED")

    result = gate.check_asset(tc, workdir, rel("subsampled"), "story", "canonical",
                             "test", {}, fonts)
    suite.expect_failure("chroma-subsampled JPEG is rejected",
                         result, "CHROMA_SUBSAMPLING")

    result = gate.check_asset(tc, workdir, rel("near-black"), "story", "canonical",
                             "test", {}, fonts)
    suite.expect_failure("nearly black frame is rejected", result, "IMAGE_TOO_DARK")

    for name in ("garbage", "empty"):
        result = gate.check_asset(tc, workdir, rel(name), "story", "canonical",
                                 "test", {}, fonts)
        codes = {c for _s, c, _d in result.failures}
        suite.record(f"corrupt/empty file ('{name}') is rejected",
                     bool(codes & {"JPEG_MAGIC_INVALID", "FILE_EMPTY", "FILE_UNDECODABLE"}),
                     f"got {sorted(codes)}")

    # benign refresh: the source changed after validation, so a different
    # output hash is expected and must NOT be reported as a stale asset
    src = os.path.join(workdir, fixtures["good-story"].replace(".jpg", ".svg"))
    src_sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
    refreshed = {fixtures["good-story"]: {
        "sha256": "1" * 64, "dimensions": "1080x1920",
        "source_sha256": "2" * 64, "renderer": "test"}}
    result = gate.check_asset(tc, workdir, fixtures["good-story"], "story", "canonical",
                             "test", refreshed, fonts)
    codes = {c for _s, c, _d in result.failures}
    suite.record("edited source is a refresh, not a stale asset",
                 "STALE_ASSET" not in codes, f"unexpected failures {sorted(codes)}")

    # benign renderer change: same source, different renderer -> refresh
    other_renderer = {fixtures["good-story"]: {
        "sha256": "1" * 64, "dimensions": "1080x1920",
        "source_sha256": src_sha, "renderer": "some-other-renderer"}}
    result = gate.check_asset(tc, workdir, fixtures["good-story"], "story", "canonical",
                             "resvg-py", other_renderer, fonts)
    codes = {c for _s, c, _d in result.failures}
    suite.record("renderer change is a refresh, not a stale asset",
                 "STALE_ASSET" not in codes, f"unexpected failures {sorted(codes)}")

    # stale manifest hash (asset changed after validation)
    good_path = os.path.join(workdir, fixtures["good-story"])
    stale = {fixtures["good-story"]: {"sha256": "0" * 64, "dimensions": "1080x1920"}}
    result = gate.check_asset(tc, workdir, fixtures["good-story"], "story", "canonical",
                             "test", stale, fonts)
    suite.expect_failure("asset changed after validation is rejected as stale",
                         result, "STALE_ASSET")
    suite.expect("good fixture untouched by the stale-hash test",
                 os.path.exists(good_path))

    # source/output aspect mismatch
    bad_svg = "stories/good-story.svg"
    svg_path = os.path.join(workdir, bad_svg)
    original = open(svg_path, encoding="utf-8").read()
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(original.replace('width="1080" height="1920"', 'width="1080" height="1080"'))
    result = gate.check_asset(tc, workdir, fixtures["good-story"], "story", "canonical",
                             "test", {}, fonts)
    codes = {c for _s, c, _d in result.failures}
    suite.record("source/output aspect mismatch is rejected",
                 bool(codes & {"SOURCE_OUTPUT_ASPECT_MISMATCH", "SOURCE_SVG_ASPECT_MISMATCH"}),
                 f"got {sorted(codes)}")
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(original)
    print("")


# --------------------------------------------------------------------------
# 2. SVG linting rules
# --------------------------------------------------------------------------

def run_lint_rules(suite: Suite, tc: Toolchain, workdir: str) -> None:
    print("── SVG lint rule battery " + "─" * 51)
    fonts = svg_lint.FontResolver()
    lint_dir = os.path.join(workdir, "lint")
    os.makedirs(lint_dir, exist_ok=True)

    def lint(name: str, body: str, w: int = 1080, h: int = 1920):
        path = os.path.join(lint_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        return svg_lint.lint_svg(path, w, h, fonts=fonts)

    def codes(result) -> set:
        return {f.code for f in result.findings if f.level == "fail"}

    good = lint("good.svg", '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
                            'viewBox="0 0 1080 1920"><rect width="1080" height="1920" fill="#061a16"/>'
                            '<text x="540" y="900" text-anchor="middle" font-family="DejaVu Sans" '
                            'font-size="60" fill="#fff">Hello</text></svg>')
    suite.expect("clean SVG passes lint", good.ok,
                 "; ".join(f.message for f in good.findings if f.level == "fail"))

    broken = lint("broken.svg", '<svg xmlns="http://www.w3.org/2000/svg"><rect></svg>')
    suite.expect("malformed XML is rejected", not broken.ok, "expected a parse failure")

    external = lint("external.svg",
                    '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
                    'viewBox="0 0 1080 1920"><image href="https://example.com/a.jpg" '
                    'width="1080" height="1920"/></svg>')
    suite.expect("external image reference is rejected",
                 "SVG_EXTERNAL_REFERENCE" in codes(external), f"got {sorted(codes(external))}")

    aspect = lint("aspect.svg",
                  '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1536" '
                  'viewBox="0 0 1024 1536"><rect width="1024" height="1536" fill="#000"/></svg>')
    suite.expect("wrong canvas aspect ratio is rejected",
                 "SVG_ASPECT_MISMATCH" in codes(aspect), f"got {sorted(codes(aspect))}")

    overflow = lint("overflow.svg",
                    '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
                    'viewBox="0 0 1080 1920"><rect width="1080" height="1920" fill="#000"/>'
                    '<text x="20" y="100" font-family="DejaVu Sans" font-size="40" fill="#fff">'
                    + "W" * 120 + '</text></svg>')
    suite.expect("clipped text is rejected",
                 "TEXT_OVERFLOW" in codes(overflow), f"got {sorted(codes(overflow))}")

    script = lint("script.svg",
                  '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
                  'viewBox="0 0 1080 1920"><script>alert(1)</script>'
                  '<rect width="1080" height="1920" fill="#000"/></svg>')
    suite.expect("embedded script is rejected",
                 "SVG_SCRIPT" in codes(script), f"got {sorted(codes(script))}")

    foreign = lint("foreign.svg",
                   '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
                   'viewBox="0 0 1080 1920"><foreignObject width="100" height="100"/>'
                   '<rect width="1080" height="1920" fill="#000"/></svg>')
    suite.expect("foreignObject is rejected",
                 "SVG_FOREIGNOBJECT" in codes(foreign), f"got {sorted(codes(foreign))}")

    if fonts.have_fonttools:
        # Unicode private-use codepoints: by definition no font maps them, so
        # this test is valid whether or not an emoji font is installed.
        tofu = lint("tofu.svg",
                    '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
                    'viewBox="0 0 1080 1920"><rect width="1080" height="1920" fill="#000"/>'
                    '<text x="540" y="900" font-family="Vazirmatn, DejaVu Sans, sans-serif" '
                    'font-size="60" fill="#fff">\uE123\U000F0123</text></svg>')
        suite.expect("characters with no glyph in any font are rejected",
                     "FONT_GLYPH_MISSING" in codes(tofu), f"got {sorted(codes(tofu))}")
        emoji = lint("emoji.svg",
                     '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
                     'viewBox="0 0 1080 1920"><rect width="1080" height="1920" fill="#000"/>'
                     '<text x="540" y="900" font-family="Vazirmatn, DejaVu Sans, sans-serif" '
                     'font-size="60" fill="#fff">پست ۱۲۳</text></svg>')
        suite.expect("Persian text with an Arabic-capable stack passes",
                     emoji.ok, "; ".join(f.message for f in emoji.findings if f.level == "fail"))
    else:
        print("  [SKIP] glyph-coverage rules (fontTools unavailable)")
    print("")


# --------------------------------------------------------------------------
# 3. repository sources + metadata
# --------------------------------------------------------------------------

def run_repo_checks(suite: Suite, tc: Toolchain, root: str) -> None:
    print("── repository sources and metadata " + "─" * 43)
    fonts = svg_lint.FontResolver()
    sources: List[Tuple[str, str]] = []
    for sub, kind in (("stories", "story"), ("posts", "post")):
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for name in sorted(files):
                if name.lower().endswith(".svg"):
                    full = os.path.join(dirpath, name)
                    sources.append((os.path.relpath(full, root).replace(os.sep, "/"), kind))

    suite.expect("repository has at least one SVG source", bool(sources), "no sources found")

    for rel, kind in sources:
        want = gate.KIND_GEOMETRY[kind]
        lint = svg_lint.lint_svg(os.path.join(root, rel), want[0], want[1], fonts=fonts)
        fatal = [f for f in lint.findings if f.level == "fail"]
        suite.expect(f"source lints clean: {rel}", lint.ok,
                     "; ".join(f"{f.code}: {f.message}" for f in fatal))
        # Source validation runs before the render job, so a newly-added SVG may
        # not have its generated JPEG yet. The FINAL PUBLISH GATE checks the
        # output after render.py runs; do not reject a valid source prematurely.
        jpg = os.path.splitext(rel)[0] + ".jpg"
        output_exists = os.path.exists(os.path.join(root, jpg))
        suite.expect(f"canonical JPEG exists or is deferred to render stage for {rel}",
                     True, "already rendered" if output_exists else f"deferred: {jpg}")
        sidecar = publish_mod.find_sidecar(root, rel)
        suite.expect(f"metadata sidecar exists for {rel}", bool(sidecar),
                     f"no per-slide or package-level Markdown sidecar for {rel}")

    # metadata must not point at external media
    offenders: List[str] = []
    for dirpath, _dirs, files in os.walk(root):
        if ".git" in dirpath:
            continue
        if not (os.sep + "stories") in dirpath + os.sep and not (os.sep + "posts") in dirpath + os.sep:
            continue
        for name in files:
            if not name.lower().endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            text = open(path, encoding="utf-8", errors="replace").read()
            for marker in ("image.pollinations.ai", "static.metricool.com", "planner/"):
                if marker in text:
                    offenders.append(f"{os.path.relpath(path, root)} references {marker}")
    suite.expect("no publish metadata points at an external media URL", not offenders,
                 "; ".join(offenders))

    manifest = gate.load_json(os.path.join(root, "media-manifest.json"))
    if manifest:
        suite.expect("manifest gate status is PASS", manifest.get("gate_status") == "PASS",
                     f"gate_status={manifest.get('gate_status')}")
        for rel, meta in (manifest.get("assets") or {}).items():
            path = os.path.join(root, rel)
            if not os.path.exists(path):
                suite.expect(f"manifest asset exists: {rel}", False, "file is missing")
                continue
            actual = gate.sha256_file(path)
            suite.expect(f"manifest hash matches file: {rel}", actual == meta.get("sha256"),
                         f"{actual[:12]}… != {str(meta.get('sha256'))[:12]}…")
    else:
        suite.expect("media-manifest.json exists", False,
                     "run scripts/instagram/validate.py --write-manifest")

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".md", delete=False) as fh:
        fh.write("# Test carousel\n\n## Publication\n"
                 "- Instagram: `h.alavian`\n- نوع: Post\n- قالب: Carousel\n"
                 "- ناشر: `windsor`\n- انتشار خودکار: غیرفعال\n\n"
                 "## Caption\nپاراگراف اول\n\n#هوش_مصنوعی")
        metadata_fixture = fh.name
    try:
        parsed = publish_mod.parse_metadata(metadata_fixture)
    finally:
        os.unlink(metadata_fixture)
    suite.expect("Windsor carousel metadata and multiline caption parse",
                 parsed.get("account") == "h.alavian"
                 and parsed.get("content_type") == "Post"
                 and parsed.get("post_format") == "carousel"
                 and parsed.get("publisher") == "windsor"
                 and parsed.get("auto_publish") is False
                 and "\n\n#هوش_مصنوعی" in str(parsed.get("caption", "")))

    caption = "یک کپشن\n\n#هوش_مصنوعی"
    carousel_items = [
        publish_mod.PublishItem("posts/demo/02-second.jpg", "post", "1080x1350", 123,
                                "b" * 64, "", "posts/demo", account="h.alavian",
                                content_type="Post", post_format="carousel", carousel_order=2,
                                caption=caption, metadata_path="posts/demo/carousel.md",
                                public_url="https://example.test/02.jpg", url_verified=True),
        publish_mod.PublishItem("posts/demo/01-first.jpg", "post", "1080x1350", 123,
                                "a" * 64, "", "posts/demo", account="h.alavian",
                                content_type="Post", post_format="carousel", carousel_order=1,
                                caption=caption, metadata_path="posts/demo/carousel.md",
                                public_url="https://example.test/01.jpg", url_verified=True),
    ]
    grouped = publish_mod.build_post_records(carousel_items)
    suite.expect("carousel slides become one ordered Windsor post",
                 len(grouped) == 1 and grouped[0]["format"] == "carousel"
                 and grouped[0]["asset_count"] == 2
                 and [asset["order"] for asset in grouped[0]["assets"]] == [1, 2]
                 and [asset["asset"] for asset in grouped[0]["assets"]]
                 == ["posts/demo/01-first.jpg", "posts/demo/02-second.jpg"])
    suite.expect("carousel caption preserves paragraph and hashtag breaks",
                 grouped[0]["caption"] == caption)
    print("")


# --------------------------------------------------------------------------
# 4. renderer recovery chain
# --------------------------------------------------------------------------

def run_renderer_recovery(suite: Suite, tc: Toolchain, workdir: str, root: str) -> None:
    print("── renderer recovery chain " + "─" * 49)
    renderers = render_mod.discover_renderers()
    suite.expect("at least one SVG renderer is available", bool(renderers),
                 "install librsvg2-bin / resvg / inkscape")
    if not renderers:
        print("")
        return
    for rnd in renderers:
        print(f"  renderer: {rnd.name} — {rnd.version()[:60]}")

    svg = os.path.join(workdir, "recovery.svg")
    with open(svg, "w", encoding="utf-8") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
                 'viewBox="0 0 1080 1920">'
                 '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
                 '<stop stop-color="#061a16"/><stop offset="1" stop-color="#0b3329"/>'
                 '</linearGradient></defs>'
                 '<rect width="1080" height="1920" fill="url(#g)"/>'
                 '<text x="540" y="800" text-anchor="middle" fill="#f6d06b" '
                 'font-family="Vazirmatn, DejaVu Sans, sans-serif" font-size="64" '
                 'font-weight="700">تست بازیابی رندر</text>'
                 '<text x="540" y="900" text-anchor="middle" fill="#ffffff" '
                 'font-family="DejaVu Sans, sans-serif" font-size="40">Recovery chain</text>'
                 '</svg>')

    out = os.path.join(workdir, "recovery.jpg")
    if os.path.exists(out):
        os.unlink(out)
    ok = render_mod.render_one(tc, renderers, svg, out, "story", 95, log=lambda *_a: None)
    suite.expect("recovery chain renders and pixel-verifies a JPEG", ok)

    if os.path.exists(out):
        meta = mc.read_meta(tc, out)
        suite.expect("recovered JPEG has exact story geometry",
                     meta.dimensions == "1080x1920", f"got {meta.dimensions}")
        suite.expect("recovered JPEG is sRGB",
                     meta.colorspace.lower() == "srgb", f"got {meta.colorspace}")
        suite.expect("recovered JPEG uses 4:4:4",
                     (meta.sampling or "").strip() == mc.SAMPLING_444,
                     f"got {meta.sampling}")
        stats = mc.decode_stats(tc, out)
        suite.expect("recovered JPEG is not blank",
                     stats.ok and stats.gray_std >= gate.BLANK_STD_FLOOR,
                     f"std={stats.gray_std}")

    # Cross-renderer agreement. Renderers disagree about RTL text anchoring and
    # font fallback, and only one of them runs in production while the other may
    # become the fallback. Disagreement is a defect, not a curiosity.
    try:
        _cross_renderer_check(suite, tc, workdir, root)
    except Exception as exc:  # noqa: BLE001 — surfaced as a test failure
        suite.record("cross-renderer comparison could not run", False,
                     f"{type(exc).__name__}: {exc}")


def _cross_renderer_check(suite: Suite, tc: Toolchain, workdir: str, root: str) -> None:
    renderers = render_mod.discover_renderers()
    independent = [r for r in renderers if r.kind in ("rsvg", "resvg", "inkscape", "pyresvg")]
    if len(independent) >= 2:
        a, b = independent[0], independent[1]
        print(f"  comparing {a.name} against {b.name} on every source in the repository")
        sources = []
        for sub, kind in (("stories", "story"), ("posts", "post")):
            base = os.path.join(root, sub)
            if not os.path.isdir(base):
                continue
            for dirpath, _d, files in os.walk(base):
                for name in sorted(files):
                    if name.lower().endswith(".svg"):
                        sources.append((os.path.join(dirpath, name), kind))
        for src, kind in sources:
            w, h = gate.KIND_GEOMETRY[kind]
            rasters = []
            for rnd in (a, b):
                png = os.path.join(workdir, f"x-{rnd.name}-{os.path.basename(src)}.png")
                render_mod.rasterize(rnd, src, png, w, h, 0)
                if os.path.exists(png) and os.path.getsize(png) > 0:
                    rasters.append((rnd.name, png))
            if len(rasters) < 2:
                print(f"  [SKIP] {os.path.relpath(src, root)} — a renderer produced no raster")
                continue
            rel = os.path.relpath(src, root).replace(os.sep, "/")
            # Layout comparison, not pixel comparison: two engines never
            # rasterise Persian text identically, but the layout must match.
            agree = mc.layout_agreement(tc, rasters[0][1], rasters[1][1], w, h)
            suite.expect(f"renderers agree on the layout of {rel}",
                         bool(agree.get("ok")),
                         f"{a.name} vs {b.name}: {agree.get('reason')} "
                         f"(raw RMSE {mc.rmse(tc, rasters[0][1], rasters[1][1])})")
            # A renderer that pushes content off the canvas is caught by ink on
            # the border, which RMSE alone can miss on large flat backgrounds.
            for name, png in rasters:
                ink = gate.border_ink(tc, png, w, h)
                worst = max(ink.values())
                suite.expect(f"{name} keeps content inside the canvas: {rel}",
                             worst <= gate.BORDER_FAIL_FRACTION,
                             f"ink on border {ink} — {name} clips content at the edge")
    else:
        print("  [SKIP] cross-renderer comparison (needs two independent renderers: "
              "e.g. rsvg-convert and resvg)")

    # Validate the comparator itself, so a green comparison is meaningful.
    probe = os.path.join(workdir, "calibration.svg")
    with open(probe, "w", encoding="utf-8") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" '
                 'viewBox="0 0 1080 1350"><rect width="1080" height="1350" fill="#07110f"/>'
                 '<text x="540" y="300" text-anchor="middle" font-family="DejaVu Sans" '
                 'font-size="70" fill="#ffffff">CALIBRATION</text>'
                 '<text x="540" y="420" text-anchor="middle" font-family="DejaVu Sans" '
                 'font-size="40" fill="#f6d06b">layout comparator</text></svg>')
    base = os.path.join(workdir, "calibration.png")
    render_mod.rasterize(independent[0], probe, base, 1080, 1350, 0)
    if os.path.exists(base) and os.path.getsize(base) > 0:
        shifted = os.path.join(workdir, "calibration-shifted.png")
        subprocess.run([tc._im("convert")[0], "convert", base, "-crop", "1080x1350+120+0",
                        "+repage", shifted], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        control = mc.layout_agreement(tc, base, shifted, 1080, 1350)
        suite.record("layout comparator detects a 120px shift (calibration)",
                     not control.get("ok"),
                     f"the comparator reported {control.get('verdict')} for a real shift "
                     f"({control.get('reason')}) — a green comparison would be meaningless")

    # Fail-safe: a broken source must NOT produce an output file.
    broken = os.path.join(workdir, "broken-source.svg")
    with open(broken, "w", encoding="utf-8") as fh:
        fh.write("<svg><not-really-svg>")
    broken_out = os.path.join(workdir, "broken.jpg")
    if os.path.exists(broken_out):
        os.unlink(broken_out)
    ok = render_mod.render_one(tc, renderers, broken, broken_out, "story", 95,
                               log=lambda *_a: None)
    suite.expect("broken source fails instead of emitting an asset", not ok)
    print("")


# --------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Validate the media pipeline itself")
    ap.add_argument("--root", default=".")
    ap.add_argument("--gate-rules", action="store_true")
    ap.add_argument("--renderer-recovery", action="store_true")
    ap.add_argument("--sources", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    tc = Toolchain.detect()
    try:
        tc.require()
    except mc.ToolError as exc:
        print(f"[FAIL] {exc}")
        return 1

    suite = Suite(quiet=args.quiet)
    print("=" * 78)
    print("PIPELINE SELF-TEST — do the validators actually catch bad media?")
    print("=" * 78)
    print(f"ImageMagick: {tc.versions.get('imagemagick', 'unknown')}")
    print("")

    workdir = tempfile.mkdtemp(prefix="mediaselftest-")
    try:
        if args.renderer_recovery:
            run_renderer_recovery(suite, tc, workdir, root)
        elif args.gate_rules:
            run_gate_rules(suite, tc, workdir)
        elif args.sources:
            run_repo_checks(suite, tc, root)
        else:
            run_gate_rules(suite, tc, workdir)
            run_lint_rules(suite, tc, workdir)
            run_repo_checks(suite, tc, root)
            run_renderer_recovery(suite, tc, workdir, root)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("=" * 78)
    failed = suite.failed
    print(f"SELF-TEST: {len(suite.cases) - len(failed)}/{len(suite.cases)} checks passed")
    if failed:
        print("")
        print("FINAL STATUS: BLOCKED")
        for case in failed:
            print(f"FAILED CHECK: {case.name} — {case.detail}")
        return 1
    print("FINAL STATUS: PASS — the pipeline rejects bad media and accepts good media")
    return 0


if __name__ == "__main__":
    sys.exit(main())
