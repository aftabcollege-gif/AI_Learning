#!/usr/bin/env bash
# Install and *verify* everything the Instagram media pipeline needs.
#
# Nothing here assumes a tool exists: every dependency is probed, installed when
# missing, then verified by actually running it.  The script finishes with an
# end-to-end smoke test that renders a real SVG to a 1080x1920 JPEG, so a broken
# runner image is detected here instead of three steps later.
#
# Exit codes: 0 = toolchain proven, 1 = cannot render (pipeline must stop).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FONT_SRC="${ROOT}/assets/fonts"
FONT_DST="${HOME}/.fonts"
FAILED=0
NOTES=()

log()  { printf '%s\n' "$*"; }
ok()   { printf '  [OK]   %s\n' "$*"; }
warn() { printf '  [WARN] %s\n' "$*"; NOTES+=("$*"); }
fail() { printf '  [FAIL] %s\n' "$*"; FAILED=1; }

log "======================================================================"
log "TOOLCHAIN — verifying the media pipeline environment"
log "======================================================================"
log "runner: $(uname -srm)"
if [ -r /etc/os-release ]; then . /etc/os-release; log "os    : ${PRETTY_NAME:-unknown}"; fi
log ""

# --------------------------------------------------------------------------
# 1. system packages
# --------------------------------------------------------------------------
log "── 1. system packages ───────────────────────────────────────────────"
APT_PACKAGES=(
  librsvg2-bin          # rsvg-convert: primary SVG renderer
  imagemagick           # convert/identify/compare: raster -> JPEG + metrics
  fonts-dejavu-core     # DejaVu Sans: Latin + geometric glyphs
  fonts-noto-core       # Noto Naskh/Sans Arabic: Persian fallback
  fonts-noto-color-emoji # colour emoji coverage
  fontconfig            # fc-match / fc-list (font + coverage queries)
)
OPTIONAL_PACKAGES=(
  fonts-vazirmatn       # preferred Persian face (vendored copy is primary)
)

missing_pkgs=()
for pkg in "${APT_PACKAGES[@]}"; do
  if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
    ok "package present: ${pkg}"
  else
    missing_pkgs+=("$pkg")
  fi
done

if [ "${#missing_pkgs[@]}" -gt 0 ]; then
  log "  installing: ${missing_pkgs[*]}"
  export DEBIAN_FRONTEND=noninteractive
  for attempt in 1 2 3; do
    if sudo apt-get update -qq && sudo apt-get install -y -qq --no-install-recommends "${missing_pkgs[@]}"; then
      break
    fi
    warn "apt-get attempt ${attempt} failed; retrying in $((attempt * 10))s"
    sleep $((attempt * 10))
  done
  if [ "${attempt:-1}" -ge 3 ] && ! command -v rsvg-convert >/dev/null 2>&1; then
    warn "trying a plain (non-quiet) apt-get install for visibility"
    sudo apt-get install -y "${missing_pkgs[@]}" 2>&1 | tail -20 || true
  fi
fi

for pkg in "${OPTIONAL_PACKAGES[@]}"; do
  if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
    ok "optional package present: ${pkg}"
  else
    sudo apt-get install -y -qq --no-install-recommends "$pkg" >/dev/null 2>&1 \
      && ok "optional package installed: ${pkg}" \
      || warn "optional package unavailable: ${pkg} (vendored/repo fonts are used instead)"
  fi
done
log ""

# --------------------------------------------------------------------------
# 2. renderer + image tooling, verified by execution
# --------------------------------------------------------------------------
log "── 2. renderers and image tooling ───────────────────────────────────"
RENDERER_FOUND=0
for tool in rsvg-convert resvg inkscape convert magick identify compare; do
  if path="$(command -v "$tool" 2>/dev/null)"; then
    version="$("$path" --version 2>&1 | head -1 || true)"
    [ -n "$version" ] || version="$("$path" -version 2>&1 | head -1 || true)"
    ok "${tool} -> ${path} (${version:-no version output})"
    case "$tool" in rsvg-convert|resvg|inkscape) RENDERER_FOUND=1 ;; esac
  else
    log "  [---- ] ${tool} not installed"
  fi
done
if ! command -v identify >/dev/null 2>&1 && ! command -v magick >/dev/null 2>&1; then
  fail "ImageMagick identify/magick missing — assets cannot be validated"
fi
if [ "$RENDERER_FOUND" -eq 0 ]; then
  fail "no SVG renderer available (need rsvg-convert, resvg or inkscape)"
fi
# ImageMagick policy can silently forbid the coders we need.
if command -v convert >/dev/null 2>&1; then
  if convert -list policy 2>/dev/null | grep -qiE 'pattern: (PNG|JPEG|SVG)' ; then
    if convert -list policy 2>/dev/null | grep -A3 -iE 'pattern: (PNG|JPEG)' | grep -qi 'rights: none'; then
      fail "ImageMagick policy disables PNG/JPEG coders (check /etc/ImageMagick-*/policy.xml)"
    else
      ok "ImageMagick policy allows the PNG/JPEG coders"
    fi
  else
    ok "ImageMagick policy has no blocking coder rules"
  fi
fi
log ""

# --------------------------------------------------------------------------
# 3. fonts (vendored first, then system)
# --------------------------------------------------------------------------
log "── 3. fonts ─────────────────────────────────────────────────────────"
mkdir -p "${FONT_DST}"
if [ -d "${FONT_SRC}" ]; then
  for font in "${FONT_SRC}"/*.ttf; do
    [ -e "$font" ] || continue
    cp -f "$font" "${FONT_DST}/"
    ok "installed $(basename "$font")"
  done
else
  warn "no vendored fonts in ${FONT_SRC}"
fi
if command -v fc-cache >/dev/null 2>&1; then
  fc-cache -f >/dev/null 2>&1 && ok "font cache rebuilt" || warn "fc-cache failed"
fi

if command -v fc-list >/dev/null 2>&1; then
  total="$(fc-list 2>/dev/null | wc -l)"
  ok "fontconfig sees ${total} font file(s)"
  if fc-list :lang=fa 2>/dev/null | grep -q .; then
    ok "Persian-capable font present: $(fc-list :lang=fa -f '%{family}\n' 2>/dev/null | sort -u | head -3 | paste -sd', ')"
  else
    fail "no Persian-capable font installed — Persian text would render as boxes"
  fi
  if fc-list :charset=1f600 2>/dev/null | grep -q .; then
    ok "emoji font present: $(fc-list :charset=1f600 -f '%{family}\n' 2>/dev/null | head -1)"
  else
    warn "no emoji font found — emoji would render as tofu (avoid emoji in new sources)"
  fi
  for family in "Vazirmatn" "Noto Naskh Arabic" "DejaVu Sans"; do
    matched="$(fc-match -f '%{family}' "${family}" 2>/dev/null || true)"
    if [ -n "$matched" ]; then
      ok "fc-match '${family}' -> ${matched}"
    fi
  done
else
  warn "fc-list unavailable — font coverage checks will be limited"
fi
log ""

# --------------------------------------------------------------------------
# 4. Python analysis dependencies (font glyph coverage + text metrics)
# --------------------------------------------------------------------------
log "── 4. python dependencies ───────────────────────────────────────────"
PY="${MEDIA_PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  fail "${PY} not found"
else
  ok "${PY} -> $($PY -V 2>&1)"
  if "$PY" -c "import fontTools" >/dev/null 2>&1; then
    ok "fontTools present ($("$PY" -c 'import fontTools;print(fontTools.version)' 2>/dev/null))"
  else
    if sudo apt-get install -y -qq python3-fonttools >/dev/null 2>&1 \
       && "$PY" -c "import fontTools" >/dev/null 2>&1; then
      ok "fontTools installed via apt"
    elif pip3 install --quiet --break-system-packages fonttools >/dev/null 2>&1 \
       && "$PY" -c "import fontTools" >/dev/null 2>&1; then
      ok "fontTools installed via pip"
    elif pip3 install --quiet fonttools >/dev/null 2>&1 \
       && "$PY" -c "import fontTools" >/dev/null 2>&1; then
      ok "fontTools installed via pip"
    else
      warn "fontTools unavailable — glyph-coverage and text-overflow checks degrade to warnings"
    fi
  fi
fi
log ""

# --------------------------------------------------------------------------
# 5. smoke test: prove the toolchain can actually produce a valid JPEG
# --------------------------------------------------------------------------
log "── 5. smoke test ────────────────────────────────────────────────────"
SMOKE_DIR="$(mktemp -d)"
trap 'rm -rf "${SMOKE_DIR}"' EXIT
cat > "${SMOKE_DIR}/smoke.svg" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920">
  <rect width="1080" height="1920" fill="#07110f"/>
  <text x="540" y="900" text-anchor="middle" fill="#f6d06b" font-family="Vazirmatn, 'Noto Naskh Arabic', DejaVu Sans, sans-serif" font-size="72" font-weight="700">تست فارسی ۱۲۳</text>
  <text x="540" y="1000" text-anchor="middle" fill="#ffffff" font-family="DejaVu Sans, sans-serif" font-size="48">Smoke Test ABC</text>
</svg>
SVG

if command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -f png -w 1080 -h 1920 -o "${SMOKE_DIR}/smoke.png" "${SMOKE_DIR}/smoke.svg" \
    && ok "rsvg-convert rendered the smoke SVG" || fail "rsvg-convert failed on the smoke SVG"
elif command -v resvg >/dev/null 2>&1; then
  resvg --width 1080 --height 1920 "${SMOKE_DIR}/smoke.svg" "${SMOKE_DIR}/smoke.png" \
    && ok "resvg rendered the smoke SVG" || fail "resvg failed on the smoke SVG"
elif command -v inkscape >/dev/null 2>&1; then
  inkscape "${SMOKE_DIR}/smoke.svg" --export-filename="${SMOKE_DIR}/smoke.png" \
    --export-width=1080 --export-height=1920 >/dev/null 2>&1 \
    && ok "inkscape rendered the smoke SVG" || fail "inkscape failed on the smoke SVG"
fi

if [ -f "${SMOKE_DIR}/smoke.png" ]; then
  IM=()
  command -v magick >/dev/null 2>&1 && IM=(magick) || IM=(convert)
  if "${IM[@]}" "${SMOKE_DIR}/smoke.png" -background '#000000' -alpha remove -alpha off \
       -colorspace sRGB -sampling-factor 4:4:4 -strip -quality 95 "${SMOKE_DIR}/smoke.jpg" 2>/dev/null; then
    geometry="$(identify -format '%wx%h' "${SMOKE_DIR}/smoke.jpg" 2>/dev/null)"
    fmt="$(identify -format '%m' "${SMOKE_DIR}/smoke.jpg" 2>/dev/null)"
    std="$(identify -format '%[fx:standard_deviation]' "${SMOKE_DIR}/smoke.jpg" 2>/dev/null)"
    if [ "$geometry" = "1080x1920" ] && [ "$fmt" = "JPEG" ]; then
      ok "smoke JPEG: ${fmt} ${geometry} (std=${std})"
    else
      fail "smoke JPEG has wrong geometry/format: ${fmt} ${geometry}"
    fi
    # A blank smoke render means fonts/config are broken.
    if [ -n "$std" ] && awk "BEGIN{exit !($std < 0.01)}"; then
      fail "smoke JPEG looks blank (std=${std}) — rendering is not trustworthy"
    fi
  else
    fail "ImageMagick could not convert the smoke raster to JPEG"
  fi
else
  fail "no smoke raster was produced"
fi
log ""

log "======================================================================"
if [ "$FAILED" -ne 0 ]; then
  log "TOOLCHAIN: FAILED — the media pipeline must not run"
  for note in "${NOTES[@]:-}"; do [ -n "$note" ] && log "  note: $note"; done
  exit 1
fi
log "TOOLCHAIN: PASS — renderers, fonts and image tooling verified end to end"
for note in "${NOTES[@]:-}"; do [ -n "$note" ] && log "  note: $note"; done
exit 0
