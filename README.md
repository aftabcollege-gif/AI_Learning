# AI_Learning — Instagram media pipeline

Publishing Instagram media is a chain, and a green workflow is **not** evidence
that a usable image was produced. This repository therefore treats the media
file itself as the thing under test:

```
SOURCE SVG ─▶ RENDER ─▶ CONVERT ─▶ VALIDATE ─▶ VISUAL QA ─▶ COMMIT
                                                              │
                          VERIFY PUBLIC URL ─▶ PUBLISH ─▶ VERIFY PUBLISHED MEDIA
```

Nothing is committed and nothing is published unless the **FINAL PUBLISH GATE**
reports `PASS`.

## Why this exists

The 2026-10-03 incident: the workflow reported success while committing files
that were not images at all. `stories/2026-10-03/01-guided-vision-story.jpg`
started with the bytes `e1 95 81` (no JPEG header, no `FFD9` end marker) and
decoded to `0x0` pixels, and `stories/2026-09-18/01-ai-photo-editing-prompts.png`
was a fully blank white 1080×1920 frame. Both would have published as broken or
empty Stories. The old pipeline only asked "does `rsvg-convert` exit 0?".

Detected causes, all now enforced against:

| Class | Defect found | Now caught by |
|---|---|---|
| File | corrupt/garbage bytes named `.jpg` | `JPEG_MAGIC_INVALID`, `FILE_UNDECODABLE` (real pixel decode) |
| File | blank white frame | `IMAGE_BLANK`, `IMAGE_FLAT` |
| Geometry | wrong canvas / Story-Post swap | `SVG_ASPECT_MISMATCH`, `DIMENSIONS_WRONG`, `STORY_POST_SWAPPED` |
| Colour | chroma subsampling, non-sRGB | `CHROMA_SUBSAMPLING`, `COLORSPACE_NOT_SRGB` |
| Text | clipped Persian headlines | `TEXT_OVERFLOW` (measured with real font metrics) |
| Text | Persian rendered as tofu boxes | `FONT_GLYPH_MISSING`, `FONT_NO_ARABIC_COVERAGE` |
| Assets | external image URL in a source | `SVG_EXTERNAL_REFERENCE` |
| Assets | stale file republished | `STALE_ASSET`, `PROVENANCE_STALE` |
| Publish | URL serves an older revision | byte + SHA-256 comparison of the fetched file |
| Publish | upload "succeeded", media wrong | publisher receipt must match the validated SHA-256 |

## Pipeline stages

All commands are run from the repository root.

```bash
# 1. Install and *verify* renderers, fonts, ImageMagick (exits 1 if it cannot render)
bash scripts/instagram/ensure_toolchain.sh

# 2. Render every SVG to a publish-grade JPEG with a recovery chain
python3 scripts/instagram/render.py --root .

# 3. FINAL PUBLISH GATE — inspect the artefacts, not the renderer's exit code
python3 scripts/instagram/validate.py --root . --write-manifest

# 4. Prove the QA layer itself catches bad media
python3 scripts/instagram/selftest.py --root .

# 5. Build (and verify) the publishing plan
python3 scripts/instagram/publish.py --root . \
  --owner aftabcollege-gif --repo AI_Learning --commit "$(git rev-parse HEAD)"
```

### Stage 1 — `ensure_toolchain.sh`

Probes every dependency, installs what is missing, then verifies by execution:
package install with retries, renderer probes with versions, an ImageMagick
policy check (a restrictive `policy.xml` silently breaks conversions), font
installation and Persian/emoji coverage, and finally an end-to-end smoke render
that must yield a `1080x1920` JPEG with real pixel variance. Exit code `1` means
**do not render** — the caller must stop.

### Stage 2 — `render.py`

Deterministic `SVG → JPEG` with an actual recovery chain:

1. retry 1 — primary renderer, primary options;
2. retry 2 — primary renderer, corrected options;
3. retry 2b — each fallback renderer (`rsvg-convert` → `resvg` → `inkscape` →
   ImageMagick → in-process `resvg-py`);
4. retry 3 — rebuilt source SVG with enforced canvas geometry;
5. otherwise **fail**: no JPEG is written, nothing is committed.

Every attempt is rasterised first and the raster must prove itself (exact
geometry, decodable pixels, not blank, not a flat fill) before it may become a
JPEG. Alpha is flattened onto the artwork's own border colour, so a transparent
canvas can never become a white (or black) rectangle. Provenance — renderer,
version, quality, output hash — is written to `reports/render-log.json`.

### Stage 3 — `validate.py` (FINAL PUBLISH GATE)

Gate 1 lints every source SVG: XML validity, canvas aspect versus the Instagram
target, external references, scripts, `foreignObject`, embedded raster
integrity, font resolution, real glyph coverage, and **measured** text overflow
(using the actual font advance widths) with a per-element near-edge warning.

Gate 2 validates every artefact: file size, JPEG magic bytes (`FFD8FF` … `FFD9`),
a real pixel decode, exact Story `1080x1920` / Post `1080x1350` geometry, swap
detection, sRGB, 4:4:4, absence of alpha, and visual integrity (blank, flat
colour, near-black, colour count). Gate 2b audits legacy PNGs so a blank or
unreadable leftover can never be picked up by a fallback publisher.

Gate 3 maps sources to outputs: one canonical JPEG per SVG, matching aspect
ratios, manifest hash freshness, and recorded render provenance. A single-image
package has one FINAL JPEG; a carousel package may have several numbered slides,
all validated independently at the Post geometry. It writes
`reports/media-validation.json`, appends `reports/media-ledger.md`, and refreshes
`media-manifest.json` — which is only written with `gate_status: PASS` when
everything above holds.

Exit code `0` means **PASS**; `1` means `PUBLISH = BLOCKED` with explicit
reasons.

### Stage 4 — `selftest.py`

Feeds the gate deliberately broken artefacts (blank frame, wrong dimensions,
Story/Post swap, 4:2:0 subsampling, near-black frame, truncated garbage,
zero-byte file, stale hash, aspect mismatch) plus SVG lint traps (malformed XML,
external image, wrong aspect, clipped text, `<script>`, `<foreignObject>`, tofu
emoji) and asserts each is rejected — and that healthy media is accepted. A
validator that never fails is worthless; this suite is what keeps it honest.

### Stage 5 — `publish.py`

Refuses to run unless `media-manifest.json` reports `gate_status: PASS`, then
builds a pinned public URL for every asset (`…/<full-40-char-SHA>/<path>`),
fetches it back and compares **byte size and SHA-256** against the validated
file. A CDN or raw host serving a stale revision is caught here rather than on
Instagram. Windsor is the preferred publisher (Metricool is an optional
fallback). The plan keeps per-file hashes and URLs in `items[]`, and groups
numbered carousel slides into one post-level record in `posts[]`, with the
caption and ordered media URLs together. Publisher receipts must reference the
validated SHA-256 and carry a media id — a successful upload API call is
explicitly *not* accepted as proof. Outputs: `reports/publish-plan.json`,
`reports/publish-report.json`.

`--plan-only` verifies the handoff without asserting a publish (used on `push`);
`--require-published` fails unless every auto-publish item has a verified
receipt. GitHub creates the verified plan; it does not call Windsor to publish.
Schedule and publish the selected `posts[]` record in Windsor, then provide a
receipt if you want the repository to verify the live result.

## Naming and identity rules

- One package per date: `stories/<date>/…`; single posts use
  `posts/<date>-<slug>.*`, while carousel packages use
  `posts/<date>-<slug>/…`.
- Each source SVG renders to exactly one `<source-stem>.jpg`. Single-image
  packages have one final JPEG; carousels use numbered slide files (`01-…`,
  `02-…`) in the same package. There is no "first JPG found" fallback.
- Story = `1080x1920`, each Post/carousel slide = `1080x1350`, JPEG, sRGB,
  4:4:4, ≤ 8 MB.
- Metadata may live beside each slide or once per package as `carousel.md`.
  Sidecars carry account, type, format, caption, schedule and auto-publish
  state. They never contain media URLs: pinned URLs come from the newest
  `reports/publish-plan.json`, so a hand-written URL cannot point at an old
  revision.

## Windsor carousel handoff

The current five-slide Persian carousel is in
`posts/2026-10-04-ai-learning-carousel/`. `carousel.md` is the source of truth
for its caption, hashtags, account, and posting state. After the GitHub workflow
passes, download the `publish-plan` workflow artifact and use the single
`posts[]` entry whose `package` matches that folder. Its `assets[]` are already
ordered and contain commit-pinned, byte-verified URLs for Windsor. The
`items[]` records remain available for per-file integrity checks.

The campaign is prepared but not scheduled or published: automatic publishing
is disabled and the time is intentionally left for Windsor. GitHub Actions
renders and verifies media; it does not log in to or call Windsor.

## Fonts

Persian typography must not depend on whatever the runner image happens to
ship. `assets/fonts/` vendors Vazirmatn (SIL OFL, see `OFL-Vazirmatn.txt`), and
`ensure_toolchain.sh` installs it into `~/.fonts` before rendering. Sources
declare an explicit stack:

```
Vazirmatn, 'Noto Naskh Arabic', 'Noto Sans Arabic', Tahoma, DejaVu Sans, sans-serif
```

Sources never use colour-emoji glyphs (👀 ☀ ✅): no emoji font is guaranteed to
exist, so such a glyph would render as tofu. Geometric symbols with broad
coverage (✓ ★ → ←) are used instead, and the lint step fails any character no
installed font can draw.

## Workflow

`.github/workflows/render-story-images.yml` runs four jobs: source validation,
render + FINAL PUBLISH GATE (then commit, rebase and push), a fallback-renderer
recovery check, and the publish gate.

Loop prevention: the trigger lists **only** render inputs (`**/*.svg`, the
scripts, the fonts, the workflow file). Committed JPEGs and reports can never
re-trigger the workflow. Concurrency is grouped per branch with
`cancel-in-progress: false`, so two renders never race, and the push step
rebases onto any new remote commit instead of overwriting it.

## Reports

| File | Contents |
|---|---|
| `media-manifest.json` | gate status, per-asset hash/size/geometry/metrics/renderer/commit |
| `reports/media-validation.json` | full machine-readable gate report |
| `reports/media-ledger.md` | append-only human history of every validation run |
| `reports/render-log.json` | which renderer produced which file, at which quality |
| `reports/publish-plan.json` | pinned URLs, verification results, receipts, media ids |
| `reports/publish-report.json` | run summary for the workflow step summary |
| `reports/publish-receipts.json` | receipts supplied by the external publisher (input) |

## Publisher receipts

`reports/publish-receipts.json` is the contract with Windsor (or Metricool when explicitly selected):

```json
{
  "receipts": [
    {
      "asset": "stories/2026-10-03/01-guided-vision-story.jpg",
      "sha256": "<must equal the validated asset hash>",
      "publisher": "metricool",
      "media_id": "17912...",
      "status": "published",
      "published_at": "2026-10-03T08:00:00Z",
      "permalink": "https://www.instagram.com/stories/..."
    }
  ]
}
```

A missing receipt for an auto-publish item is reported as `NOT_VERIFIED` — never
as success. Allowed statuses: `published`, `processed`, `scheduled`.

## Known limitations

- Public URL verification needs outbound network access to the raw host; when it
  is unavailable (restricted sandboxes) the plan reports the failure instead of
  claiming success. Run it in CI where `raw.githubusercontent.com` is reachable.
- Cross-renderer agreement is only checked when two *independent* renderers are
  installed; on a runner with `rsvg-convert` and `resvg` both present it runs
  automatically.
- Receipts must be supplied by the publishing integration; this repository
  cannot invent proof that Instagram accepted an upload.
