#!/usr/bin/env python3
"""ImageMagick-backed inspection helpers for Instagram media validation.

Design notes
------------
* ImageMagick 6 (`convert`/`identify`/`compare`) and ImageMagick 7 (`magick`)
  are both supported.  The correct invocation is discovered at runtime.
* ImageMagick 6 returns exit code 0 even when a file cannot be decoded, and it
  happily prints `0x0` dimensions for a truncated/garbage file.  Therefore we
  never trust exit codes or a single `identify` call: every file must survive a
  real pixel decode (`decode_stats`) before it may be published.
* Nothing in here shells out to the network, so results are deterministic.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

# JPEG sampling factor emitted by ImageMagick for 4:4:4 (no chroma subsampling).
SAMPLING_444 = "1x1,1x1,1x1"


class ToolError(RuntimeError):
    """Raised when a required ImageMagick binary is unavailable."""


def run(cmd: Sequence[str], timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a command capturing text output. Never raises on non-zero exit."""
    return subprocess.run(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        errors="replace",
    )


@dataclass
class Toolchain:
    """Resolved ImageMagick binaries plus the renderer inventory."""

    magick: Optional[str] = None          # IM7 multicall binary
    convert: Optional[str] = None
    identify: Optional[str] = None        # full command prefix, e.g. ["magick", "identify"]
    compare: Optional[str] = None
    versions: Dict[str, str] = field(default_factory=dict)

    # ---- construction -------------------------------------------------
    @classmethod
    def detect(cls) -> "Toolchain":
        tc = cls()
        tc.magick = shutil.which("magick")
        tc.convert = shutil.which("convert")
        tc.identify = shutil.which("identify")
        tc.compare = shutil.which("compare")

        if tc.magick:
            tc.versions["imagemagick"] = first_line(run([tc.magick, "-version"]).stdout)
        elif tc.convert:
            tc.versions["imagemagick"] = first_line(run([tc.convert, "-version"]).stdout)

        for name, path in (("convert", tc.convert), ("identify", tc.identify),
                           ("compare", tc.compare)):
            if path:
                tc.versions[name] = first_line(run([path, "-version"]).stdout)
        return tc

    # ---- command builders ---------------------------------------------
    def _im(self, sub: str) -> List[str]:
        """Return the argv prefix for an ImageMagick sub-command."""
        if self.magick:
            return [self.magick, sub]
        if sub == "identify" and self.identify:
            return [self.identify]
        if sub == "convert" and self.convert:
            return [self.convert]
        if sub == "compare" and self.compare:
            return [self.compare]
        raise ToolError(f"ImageMagick sub-command '{sub}' is not available")

    def require(self) -> None:
        if not (self.magick or (self.convert and self.identify)):
            raise ToolError("ImageMagick is not installed (need magick or convert+identify)")

    def identify_fmt(self, fmt: str, path: str) -> str:
        res = run(self._im("identify") + ["-format", fmt, path])
        return (res.stdout or "").strip()

    def info_fmt(self, args: List[str], path: str, fmt: str) -> str:
        """`convert <file> <args...> -format <fmt> info:` — for pixel statistics."""
        res = run(self._im("convert") + [path] + args + ["-format", fmt, "info:"])
        return (res.stdout or "").strip()

    def to_jpeg(self, src: str, dst: str, quality: int, background: str = "#000000",
                flatten: bool = False) -> CompletedProcess:
        args = [src]
        if flatten:
            args += ["-background", background, "-alpha", "remove", "-alpha", "off"]
        args += [
            "-colorspace", "sRGB",
            "-sampling-factor", "4:4:4",
            "-define", "jpeg:dct-method=float",
            "-interlace", "none",
            "-strip",
            "-quality", str(quality),
            dst,
        ]
        return run(self._im("convert") + args)

    def to_png(self, src: str, dst: str) -> CompletedProcess:
        return run(self._im("convert") + [src, "-strip", dst])


def first_line(text: str) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _floats(values: Sequence[str]) -> Optional[List[float]]:
    try:
        return [float(v) for v in values]
    except (TypeError, ValueError):
        return None


@dataclass
class ImageMeta:
    path: str
    fmt: str = ""
    width: int = 0
    height: int = 0
    colorspace: str = ""
    sampling: str = ""
    depth: int = 0
    channels: str = ""
    raw: str = ""

    @property
    def dimensions(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def is_jpeg(self) -> bool:
        return self.fmt.upper() in ("JPEG", "JPG")

    @property
    def has_alpha(self) -> bool:
        return "a" in (self.channels or "").lower()

    @property
    def decodable(self) -> bool:
        return self.width > 0 and self.height > 0


def read_meta(tc: Toolchain, path: str) -> ImageMeta:
    """Read header metadata. Dimensions are the ground truth for decodability."""
    fmt = (
        "%m|%w|%h|%[colorspace]|%[jpeg:sampling-factor]|%z|%[channels]"
    )
    out = tc.identify_fmt(fmt, path)
    meta = ImageMeta(path=path, raw=out)
    parts = out.split("|")
    if len(parts) < 3:
        return meta
    meta.fmt = parts[0].strip()
    try:
        meta.width = int(parts[1])
        meta.height = int(parts[2])
    except ValueError:
        meta.width = meta.height = 0
    if len(parts) > 3:
        meta.colorspace = parts[3].strip()
    if len(parts) > 4:
        meta.sampling = parts[4].strip()
    if len(parts) > 5:
        try:
            meta.depth = int(parts[5])
        except ValueError:
            meta.depth = 0
    if len(parts) > 6:
        meta.channels = parts[6].strip()
    return meta


@dataclass
class DecodeStats:
    """Pixel statistics obtained by actually decoding the image."""

    gray_std: float = -1.0
    gray_mean: float = -1.0
    unique_colors: int = -1
    channel_means: Optional[List[float]] = None
    ok: bool = False
    error: str = ""


def decode_stats(tc: Toolchain, path: str) -> DecodeStats:
    """Force a full pixel decode and return statistics.

    A file that cannot be decoded yields ``ok=False`` — this is the check that
    catches truncated / garbage / zero-byte "images" that ``identify`` happily
    reports with a 0x0 geometry.
    """
    stats = DecodeStats()

    gray = tc.info_fmt(["-colorspace", "Gray"], path, "%[fx:standard_deviation]|%[fx:mean]")
    if not gray or "|" not in gray:
        stats.error = "gray statistics unavailable (decode failed)"
        return stats
    parsed = _floats(gray.split("|")[:2])
    if parsed is None:
        stats.error = f"non-numeric pixel statistics: {gray!r}"
        return stats
    stats.gray_std, stats.gray_mean = parsed[0], parsed[1]

    colors = tc.identify_fmt("%k", path + "[0]")
    try:
        stats.unique_colors = int(colors)
    except ValueError:
        stats.unique_colors = -1

    means = tc.identify_fmt("%[fx:mean.r]|%[fx:mean.g]|%[fx:mean.b]", path)
    mvals = _floats(means.split("|")[:3]) if "|" in means else None
    if mvals and len(mvals) == 3:
        stats.channel_means = mvals

    stats.ok = True
    return stats


def rmse(tc: Toolchain, a: str, b: str) -> Optional[float]:
    """Normalised RMSE (0..1) between two images of identical size."""
    res = run(tc._im("compare") + ["-metric", "RMSE", a, b, "null:"])
    text = (res.stderr or "") + (res.stdout or "")
    # ImageMagick prints: "<abs> (<normalised>)"; identical images can print "0"
    for token in text.split():
        if token.startswith("(") and token.endswith(")"):
            try:
                return float(token.strip("()"))
            except ValueError:
                continue
    if text.strip() in ("0", "0 (0)"):
        return 0.0
    return None


def border_mean_color(tc: Toolchain, path: str) -> Optional[List[float]]:
    """Mean RGB of the outermost 4px ring — used to choose a flatten backdrop."""
    means = tc.identify_fmt(
        "%[fx:mean.r]|%[fx:mean.g]|%[fx:mean.b]",
        f"{path}[1x1+0+0]",
    )
    vals = _floats(means.split("|")[:3]) if "|" in means else None
    return vals if vals and len(vals) == 3 else None


def rgb_to_hex(vals: Sequence[float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(v * 255))):02x}" for v in vals)


def jpeg_magic_ok(path: str) -> bool:
    """Cheap structural check: a JPEG must start with FFD8FF and end with FFD9."""
    try:
        if os.path.getsize(path) < 512:
            return False
        with open(path, "rb") as fh:
            head = fh.read(3)
            if head != b"\xff\xd8\xff":
                return False
            fh.seek(-2, os.SEEK_END)
            return fh.read(2) == b"\xff\xd9"
    except OSError:
        return False
