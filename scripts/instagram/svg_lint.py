#!/usr/bin/env python3
"""Static pre-flight linter for the SVG sources that feed the media pipeline.

Every problem that can be detected *before* rendering is detected here, because
a failure at this stage is far cheaper to diagnose than a washed-out JPEG.

Checks
------
1.  XML well-formedness.
2.  Canvas: usable width/height/viewBox and an aspect ratio that matches the
    Instagram target, so a render can never distort or crop the artwork.
3.  Self-containment: no remote/external references (the runner has no
    guaranteed outbound network for media hosts) and no scripts.
4.  Raster features unsupported by librsvg/resvg (``<foreignObject>``).
5.  Embedded ``data:`` images must decode.
6.  Fonts: the requested family stack must resolve, and the resolved fonts must
    actually contain glyphs for every character used.  Missing Arabic coverage
    renders Persian text as tofu boxes — a "renders fine but unreadable" bug
    that only a coverage check catches.
7.  Text overflow: estimated text extents must stay inside the canvas, so no
    headline or paragraph can be clipped at the edges.
"""

from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
NS = {"svg": SVG_NS, "xlink": XLINK_NS}

# Ranges that indicate "this is an emoji" — needs a colour emoji font.
_EMOJI_RANGES = (
    (0x1F300, 0x1FAFF),
    (0x1F000, 0x1F0FF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
    (0xFE0F, 0xFE0F),
    (0x2190, 0x21FF),
)

# Font families guaranteed to exist after scripts/instagram/ensure_toolchain.sh
# has run. They are also Persian/Arabic capable, which is what this project needs.
REQUIRED_FONT_FAMILIES = (
    "Vazirmatn",
    "Noto Naskh Arabic",
    "Noto Sans Arabic",
    "Noto Color Emoji",
    "DejaVu Sans",
)


def is_emoji(cp: int) -> bool:
    return any(lo <= cp <= hi for lo, hi in _EMOJI_RANGES)


def needs_arabic_coverage(codepoints: Set[int]) -> bool:
    for cp in codepoints:
        # Arabic, Arabic Supplement/Extended, and Persian presentation forms.
        if 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F or 0xFB50 <= cp <= 0xFEFF:
            return True
    return False


@dataclass
class Finding:
    level: str          # 'fail' | 'warn' | 'info'
    code: str
    message: str

    def line(self) -> str:
        marker = {"fail": "FAIL", "warn": "WARN", "info": "INFO"}[self.level]
        return f"[{marker}] {self.code}: {self.message}"


@dataclass
class LintResult:
    path: str
    width: Optional[float] = None
    height: Optional[float] = None
    view_x: float = 0.0
    view_y: float = 0.0
    findings: List[Finding] = field(default_factory=list)
    font_usage: Dict[str, int] = field(default_factory=dict)
    resolved_fonts: Dict[str, str] = field(default_factory=dict)
    text_elements: int = 0
    codepoints: int = 0

    @property
    def ok(self) -> bool:
        return not any(f.level == "fail" for f in self.findings)

    def report(self) -> str:
        head = f"--- SVG lint: {self.path}"
        if self.width and self.height:
            head += f"  ({int(self.width)}x{int(self.height)})"
        lines = [head]
        if not self.findings:
            lines.append("  [OK] no findings")
        for f in self.findings:
            lines.append("  " + f.line())
        return "\n".join(lines)


# --------------------------------------------------------------------------
# font helpers
# --------------------------------------------------------------------------

FONT_DIRS = (
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/.fonts"),
    os.path.expanduser("~/.local/share/fonts"),
)


class FontResolver:
    """Resolves font families to files and inspects glyph coverage.

    Prefers fontconfig's ``fc-match`` (present on GitHub runners).  When the
    fontconfig CLI is unavailable the resolver builds its own index from the
    installed font files, so the same checks keep working everywhere.
    """

    def __init__(self) -> None:
        self.fc_match = shutil.which("fc-match")
        self.fc_list = shutil.which("fc-list")
        self._cache: Dict[str, Optional[Tuple[str, str]]] = {}
        self._coverage: Dict[str, Optional[Set[int]]] = {}
        self._charset_cache: Dict[int, bool] = {}
        self._index: Optional[List[Tuple[str, str, str]]] = None  # (path, family, style)
        try:
            from fontTools.ttLib import TTFont  # noqa: F401
            self._tt = True
        except Exception:
            self._tt = False

    @property
    def have_fonttools(self) -> bool:
        return self._tt

    # -- fontconfig-free index -----------------------------------------
    def index(self) -> List[Tuple[str, str, str]]:
        if self._index is not None:
            return self._index
        entries: List[Tuple[str, str, str]] = []
        if self._tt:
            for directory in FONT_DIRS:
                if not os.path.isdir(directory):
                    continue
                for root, _dirs, files in os.walk(directory):
                    for name in sorted(files):
                        if not name.lower().endswith((".ttf", ".otf", ".ttc")):
                            continue
                        full = os.path.join(root, name)
                        family, style = self._names(full)
                        entries.append((full, family, style))
        self._index = entries
        return entries

    def _names(self, font_path: str) -> Tuple[str, str]:
        family, style = "", ""
        try:
            from fontTools.ttLib import TTFont
            with TTFont(font_path, fontNumber=0, lazy=True) as font:
                for record in font["name"].names:
                    if record.nameID == 1 and not family:
                        family = str(record).strip()
                    elif record.nameID == 2 and not style:
                        style = str(record).strip()
        except Exception:
            base = os.path.basename(font_path).rsplit(".", 1)[0]
            family = base.replace("-", " ")
        return family or os.path.basename(font_path), style

    def resolve(self, family_stack: str, bold: bool) -> Optional[Tuple[str, str]]:
        """Return (font file, matched family) for a CSS-ish font-family stack."""
        if not family_stack:
            return None
        key = f"{family_stack}|{bold}"
        if key in self._cache:
            return self._cache[key]
        value = self._resolve_fc(family_stack, bold) if self.fc_match else None
        if value is None:
            value = self._resolve_index(family_stack, bold)
        self._cache[key] = value
        return value

    def _resolve_fc(self, family_stack: str, bold: bool) -> Optional[Tuple[str, str]]:
        query = family_stack.strip().strip("'\"")
        if bold:
            query = f"{query}:weight=200"
        res = subprocess.run(
            [self.fc_match, "-f", "%{file}\t%{family}", query],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
            errors="replace",
        )
        out = (res.stdout or "").strip()
        if "\t" not in out:
            return None
        path, family = out.split("\t", 1)
        if not path or not os.path.exists(path):
            return None
        return path.strip(), family.split(",")[0].strip()

    def _resolve_index(self, family_stack: str, bold: bool) -> Optional[Tuple[str, str]]:
        families = [f.strip().strip("'\"") for f in family_stack.split(",") if f.strip()]
        generic = {"sans-serif", "serif", "monospace", "system-ui", "cursive", "fantasy"}
        for wanted in families:
            if wanted.lower() in generic:
                continue
            norm = wanted.lower().replace(" ", "")
            matches = [
                (path, fam, style) for path, fam, style in self.index()
                if fam.lower().replace(" ", "") == norm
            ]
            if not matches:
                continue
            def score(item: Tuple[str, str, str]) -> int:
                style = item[2].lower()
                if bold:
                    return 0 if "bold" in style else 1
                return 0 if "regular" in style or style in ("", "book") else (2 if "bold" in style else 1)
            matches.sort(key=score)
            path, fam, _style = matches[0]
            return path, fam
        return None

    def coverage(self, font_path: str) -> Optional[Set[int]]:
        if not self._tt:
            return None
        if font_path in self._coverage:
            return self._coverage[font_path]
        cps: Optional[Set[int]] = None
        try:
            from fontTools.ttLib import TTFont
            with TTFont(font_path, fontNumber=0, lazy=True) as font:
                cps = set(font.getBestCmap().keys())
        except Exception:
            cps = None
        self._coverage[font_path] = cps
        return cps

    def any_font_has(self, cp: int) -> bool:
        """Is there any installed font with a glyph for this codepoint?"""
        if cp in self._charset_cache:
            return self._charset_cache[cp]
        found = False
        if self.fc_list:
            res = subprocess.run(
                [self.fc_list, f":charset={cp:x}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=30, errors="replace",
            )
            found = bool((res.stdout or "").strip())
        if not found and self._tt:
            for directory in ("/usr/share/fonts", "/usr/local/share/fonts",
                              os.path.expanduser("~/.fonts"),
                              os.path.expanduser("~/.local/share/fonts")):
                if found:
                    break
                for root, _dirs, files in os.walk(directory):
                    for name in files:
                        if not name.lower().endswith((".ttf", ".otf", ".ttc")):
                            continue
                        cov = self.coverage(os.path.join(root, name))
                        if cov and cp in cov:
                            found = True
                            break
        self._charset_cache[cp] = found
        return found

    def advance(self, font_path: str, char: str) -> Optional[float]:
        """Advance width of a character in em units."""
        if not self._tt:
            return None
        try:
            from fontTools.ttLib import TTFont
            with TTFont(font_path, fontNumber=0, lazy=True) as font:
                cmap = font.getBestCmap()
                cp = ord(char)
                if cp not in cmap:
                    return None
                name = cmap[cp]
                upem = font["head"].unitsPerEm or 1000
                return font["hmtx"][name][0] / upem
        except Exception:
            return None


# --------------------------------------------------------------------------
# the linter
# --------------------------------------------------------------------------

def _parse_number(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    m = re.match(r"^\s*(-?[0-9]*\.?[0-9]+(?:e-?\d+)?)", value.strip())
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def lint_svg(path: str, target_w: int, target_h: int,
             fonts: Optional[FontResolver] = None,
             strict: bool = True) -> LintResult:
    fonts = fonts or FontResolver()
    result = LintResult(path=path)

    # ---- 1. XML ------------------------------------------------------
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        result.findings.append(Finding("fail", "SVG_XML_INVALID",
                                       f"XML is not well-formed: {exc}"))
        return result
    except OSError as exc:
        result.findings.append(Finding("fail", "SVG_UNREADABLE", str(exc)))
        return result

    root = tree.getroot()
    if _local(root.tag) != "svg":
        result.findings.append(Finding("fail", "SVG_ROOT_NOT_SVG",
                                       f"root element is <{_local(root.tag)}>"))
        return result

    # ---- 2. canvas ---------------------------------------------------
    width = _parse_number(root.get("width"))
    height = _parse_number(root.get("height"))
    view_box = root.get("viewBox")
    if view_box:
        parts = [p for p in re.split(r"[,\s]+", view_box.strip()) if p]
        if len(parts) != 4:
            result.findings.append(Finding("fail", "SVG_VIEWBOX_INVALID",
                                           f"viewBox must have 4 numbers, got {view_box!r}"))
            return result
        try:
            vx, vy, vw, vh = (float(p) for p in parts)
        except ValueError:
            result.findings.append(Finding("fail", "SVG_VIEWBOX_INVALID",
                                           f"viewBox is not numeric: {view_box!r}"))
            return result
        if vw <= 0 or vh <= 0:
            result.findings.append(Finding("fail", "SVG_VIEWBOX_INVALID",
                                           f"viewBox has non-positive size: {view_box!r}"))
            return result
        result.view_x, result.view_y = vx, vy
    else:
        vw = vh = None
        result.findings.append(Finding(
            "warn", "SVG_VIEWBOX_MISSING",
            "no viewBox; renderers fall back to width/height only"))

    if width is None or height is None:
        if vw and vh:
            width, height = vw, vh
            result.findings.append(Finding(
                "info", "SVG_SIZE_FROM_VIEWBOX",
                "width/height missing; using viewBox dimensions"))
        else:
            result.findings.append(Finding(
                "fail", "SVG_SIZE_UNKNOWN",
                "no usable width/height/viewBox — the canvas size is undefined"))
            return result

    if width <= 0 or height <= 0:
        result.findings.append(Finding("fail", "SVG_SIZE_INVALID",
                                       f"non-positive canvas size {width}x{height}"))
        return result
    result.width, result.height = width, height

    if vw and vh and abs((vw / vh) - (width / height)) > 0.01:
        result.findings.append(Finding(
            "warn", "SVG_VIEWBOX_ASPECT_MISMATCH",
            f"viewBox aspect {vw / vh:.4f} != width/height aspect {width / height:.4f}"))

    svg_aspect = width / height
    target_aspect = target_w / target_h
    if abs(svg_aspect - target_aspect) > 0.005:
        result.findings.append(Finding(
            "fail", "SVG_ASPECT_MISMATCH",
            (f"canvas aspect {svg_aspect:.4f} ({int(width)}x{int(height)}) does not match "
             f"the Instagram target {target_aspect:.4f} ({target_w}x{target_h}); "
             "rendering would stretch or crop the artwork")))

    # ---- 3. external references / scripts -----------------------------
    for elem in root.iter():
        tag = _local(elem.tag)
        if tag == "script":
            result.findings.append(Finding("fail", "SVG_SCRIPT",
                                           "<script> is not allowed in a publishable asset"))
        if tag == "foreignObject":
            result.findings.append(Finding(
                "fail", "SVG_FOREIGNOBJECT",
                "<foreignObject> is not rendered by librsvg/resvg — its content would vanish"))
        for attr, value in elem.attrib.items():
            name = _local(attr)
            if name.startswith("on"):
                result.findings.append(Finding("fail", "SVG_EVENT_HANDLER",
                                               f"event handler attribute '{name}' is not allowed"))
            if name in ("href", "src") or attr.endswith("}href"):
                val = (value or "").strip()
                if val and not val.startswith("#") and not val.startswith("data:"):
                    result.findings.append(Finding(
                        "fail", "SVG_EXTERNAL_REFERENCE",
                        f"<{tag}> references external resource {val[:110]!r}; "
                        "assets must be self-contained (CI may have no network access)"))
                if val.startswith("data:"):
                    _check_embedded(result, val, elem)
        if tag == "style" and elem.text:
            if re.search(r"@import|url\(\s*['\"]?https?:", elem.text):
                result.findings.append(Finding(
                    "fail", "SVG_EXTERNAL_REFERENCE",
                    "<style> block pulls in an external resource"))

    for unsupported in ("feTurbulence", "feDisplacementMap", "feDropShadow"):
        if any(_local(e.tag) == unsupported for e in root.iter()):
            result.findings.append(Finding(
                "warn", "SVG_FILTER_SUPPORT", f"<{unsupported}> renders inconsistently across renderers"))

    # ---- 4. fonts + text ---------------------------------------------
    _analyse_text(root, result, fonts, strict)

    # ---- 5. text overflow --------------------------------------------
    _check_text_overflow(root, result, fonts, width, height)

    return result


def _check_embedded(result: LintResult, value: str, elem: ET.Element) -> None:
    m = re.match(r"data:image/([a-zA-Z0-9.+-]+);base64,(.*)$", value, re.S)
    if not m:
        return
    if shutil.which("identify") is None and shutil.which("magick") is None:
        return
    raw = base64.b64decode(m.group(2)[: 4_000_000] + "==", validate=False)
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as fh:
        fh.write(raw)
        tmp = fh.name
    try:
        prefix = ["magick", "identify"] if shutil.which("magick") else ["identify"]
        res = subprocess.run(prefix + ["-format", "%w|%h", tmp],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, timeout=60, errors="replace")
        out = (res.stdout or "").strip()
        parts = out.split("|")
        if len(parts) != 2 or not parts[0].isdigit() or int(parts[0]) <= 0:
            result.findings.append(Finding(
                "fail", "SVG_EMBEDDED_IMAGE_INVALID",
                "embedded data: image does not decode to a valid raster"))
    finally:
        os.unlink(tmp)


def _iter_text_elements(root: ET.Element):
    for elem in root.iter():
        if _local(elem.tag) in ("text", "tspan"):
            yield elem


def _inherited(elem: ET.Element, parents: Dict[ET.Element, ET.Element],
               attr: str) -> Optional[str]:
    node: Optional[ET.Element] = elem
    while node is not None:
        if attr in node.attrib:
            return node.attrib[attr]
        node = parents.get(node)
    return None


def _text_content(elem: ET.Element) -> str:
    return "".join(elem.itertext())


def _analyse_text(root: ET.Element, result: LintResult, fonts: FontResolver,
                  strict: bool) -> None:
    parents: Dict[ET.Element, ET.Element] = {}
    for parent in root.iter():
        for child in parent:
            parents[child] = parent

    families_used: Dict[str, int] = {}
    codepoints: Set[int] = set()
    unresolved: Set[str] = set()

    for elem in _iter_text_elements(root):
        if _local(elem.tag) != "text":
            continue
        content = _text_content(elem).strip()
        if not content:
            continue
        result.text_elements += 1
        codepoints.update(ord(ch) for ch in content if not ch.isspace())

        family = _inherited(elem, parents, "font-family") or "sans-serif"
        weight = _inherited(elem, parents, "font-weight") or "normal"
        bold = str(weight).lower() in ("bold", "600", "700", "800", "900")
        families_used[family] = families_used.get(family, 0) + 1

        first_family = family.split(",")[0].strip().strip("'\"")
        if first_family and first_family not in ("sans-serif", "serif", "monospace"):
            resolved = fonts.resolve(family, bold)
            if resolved is None:
                unresolved.add(first_family)
            else:
                file_path, matched_family = resolved
                result.resolved_fonts[first_family] = matched_family
                if matched_family.lower().replace(" ", "") != first_family.lower().replace(" ", ""):
                    result.findings.append(Finding(
                        "warn", "FONT_FALLBACK",
                        f"'{first_family}' is not installed; fontconfig substituted "
                        f"'{matched_family}' ({os.path.basename(file_path)})"))

    result.font_usage = families_used
    result.codepoints = len(codepoints)

    if unresolved:
        result.findings.append(Finding(
            "warn", "FONT_UNRESOLVED",
            "font families could not be resolved via fontconfig: " + ", ".join(sorted(unresolved))))

    if not codepoints:
        result.findings.append(Finding("info", "SVG_NO_TEXT", "no text content found"))
        return

    if not fonts.have_fonttools:
        if needs_arabic_coverage(codepoints) and fonts.fc_list:
            res = subprocess.run([fonts.fc_list, ":lang=fa"], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, timeout=60,
                                 errors="replace")
            if not (res.stdout or "").strip():
                result.findings.append(Finding(
                    "fail", "FONT_ARABIC_MISSING",
                    "Persian/Arabic text is present but no Persian-capable font is installed"))
        elif needs_arabic_coverage(codepoints):
            result.findings.append(Finding(
                "warn", "FONT_COVERAGE_UNCHECKED",
                "fontTools unavailable — glyph coverage could not be verified"))
        return

    # Verify glyph coverage against the fonts that fontconfig will actually use.
    missing_any: Set[int] = set()
    missing_but_fallback: Set[int] = set()
    for family, _count in families_used.items():
        resolved = fonts.resolve(family, False) or fonts.resolve(family, True)
        if not resolved:
            continue
        cov = fonts.coverage(resolved[0])
        if cov is None:
            continue
        for cp in sorted(codepoints):
            if cp in cov:
                continue
            if fonts.any_font_has(cp):
                missing_but_fallback.add(cp)
            else:
                missing_any.add(cp)

    if missing_any:
        sample = "".join(chr(cp) for cp in sorted(missing_any)[:12])
        result.findings.append(Finding(
            "fail", "FONT_GLYPH_MISSING",
            (f"{len(missing_any)} character(s) have no glyph in any installed font: "
             f"{sample!r} (U+{', U+'.join(f'{cp:04X}' for cp in sorted(missing_any)[:8])})"
             " — they would render as empty boxes (tofu)")))
    if missing_but_fallback:
        sample = "".join(chr(cp) for cp in sorted(missing_but_fallback)[:12])
        result.findings.append(Finding(
            "warn", "FONT_GLYPH_FALLBACK",
            (f"{len(missing_but_fallback)} character(s) rely on font fallback "
             f"({sample!r}); install the primary font to keep rendering stable")))

    if needs_arabic_coverage(codepoints):
        has_arabic = False
        for family in families_used:
            resolved = fonts.resolve(family, False)
            if resolved and fonts.coverage(resolved[0]):
                cov = fonts.coverage(resolved[0]) or set()
                if any(0x0600 <= cp <= 0x06FF for cp in cov):
                    has_arabic = True
                    break
        if not has_arabic:
            result.findings.append(Finding(
                "fail", "FONT_NO_ARABIC_COVERAGE",
                "Persian/Arabic text present but no resolved font provides Arabic glyphs"))


def _check_text_overflow(root: ET.Element, result: LintResult, fonts: FontResolver,
                         width: float, height: float) -> None:
    if not fonts.have_fonttools:
        result.findings.append(Finding(
            "warn", "TEXT_OVERFLOW_UNCHECKED",
            "fontTools unavailable — text extents could not be measured"))
        return

    parents: Dict[ET.Element, ET.Element] = {}
    for parent in root.iter():
        for child in parent:
            parents[child] = parent

    tolerance = 2.0
    near_edge = 10.0
    measured = 0
    for elem in _iter_text_elements(root):
        if _local(elem.tag) != "text":
            continue
        content = _text_content(elem)
        if not content.strip():
            continue
        family = _inherited(elem, parents, "font-family") or "sans-serif"
        weight = _inherited(elem, parents, "font-weight") or "normal"
        bold = str(weight).lower() in ("bold", "600", "700", "800", "900")
        size = _parse_number(_inherited(elem, parents, "font-size") or "") or 16.0
        resolved = fonts.resolve(family, bold) or fonts.resolve(family, not bold)
        if not resolved:
            continue

        advance_sum = 0.0
        ok = True
        for ch in content:
            if ch.isspace():
                advance_sum += 0.28
                continue
            adv = fonts.advance(resolved[0], ch)
            if adv is None:
                ok = False
                break
            advance_sum += adv
        if not ok:
            continue
        text_w = advance_sum * size
        measured += 1

        anchor = (_inherited(elem, parents, "text-anchor") or "start").lower()
        x = _parse_number(elem.get("x")) or 0.0
        y = _parse_number(elem.get("y")) or 0.0
        if anchor == "middle":
            left = x - text_w / 2.0
        elif anchor == "end":
            left = x - text_w
        else:
            left = x
        right = left + text_w
        top = y - size * 0.85
        bottom = y + size * 0.30

        label = content.strip()[:38] + ("…" if len(content.strip()) > 38 else "")
        overflow = []
        if left < -tolerance:
            overflow.append(f"left by {-left:.0f}px")
        if right > width + tolerance:
            overflow.append(f"right by {right - width:.0f}px")
        if top < -tolerance:
            overflow.append(f"top by {-top:.0f}px")
        if bottom > height + tolerance:
            overflow.append(f"bottom by {bottom - height:.0f}px")
        if overflow:
            result.findings.append(Finding(
                "fail", "TEXT_OVERFLOW",
                (f"text '{label}' at y={y:.0f} (size {size:.0f}) overflows the canvas: "
                 + ", ".join(overflow) + " — it would be clipped")))
        else:
            margin = min(left, width - right, top, height - bottom)
            if margin < near_edge:
                result.findings.append(Finding(
                    "warn", "TEXT_NEAR_EDGE",
                    f"text '{label}' is only {margin:.1f}px from the canvas edge"))

    if measured == 0:
        result.findings.append(Finding(
            "warn", "TEXT_UNMEASURABLE", "no text element could be measured"))


def lint_pair(svg_path: str, target_w: int, target_h: int,
              fonts: Optional[FontResolver] = None) -> LintResult:
    return lint_svg(svg_path, target_w, target_h, fonts=fonts)
