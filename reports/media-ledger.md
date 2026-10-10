
## Validation run 2026-10-03T22:04:46Z

- run: `local` commit: `local`
- renderer: `convert` imagemagick: `Version: ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25 https://imagemagick.org`
- **FINAL STATUS: BLOCKED**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-10-03/01-guided-vision-story-baseline.jpg` | story | 0x0 | 14 KB | sRGB | - | `bae17c079fe568e6…` | FAIL |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 0x0 | 15 KB | sRGB | - | `1ca23631e6c0bb48…` | FAIL |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.png` | story | 1080x1920 | 8 KB | sRGB | - | `489f988e435a2f00…` | FAIL |
| `stories/2026-10-03/01-guided-vision-story-optimized.png` | story | 0x0 | 15 KB | - | - | `34f8a73e1b3487d7…` | FAIL |

**Blocking reasons**

- stories/2026-10-03/01-guided-vision-story-baseline.jpg: JPEG_MAGIC_INVALID — not a real JPEG: missing FFD8FF header or FFD9 end marker
- stories/2026-10-03/01-guided-vision-story-baseline.jpg: FILE_UNDECODABLE — image decoder produced no pixels (reported 'JPG|0|0|sRGB||16|srgb') — the file is truncated, corrupt or not an image at all
- stories/2026-10-03/01-guided-vision-story.jpg: JPEG_MAGIC_INVALID — not a real JPEG: missing FFD8FF header or FFD9 end marker
- stories/2026-10-03/01-guided-vision-story.jpg: FILE_UNDECODABLE — image decoder produced no pixels (reported 'JPG|0|0|sRGB||16|srgb') — the file is truncated, corrupt or not an image at all
- stories/2026-09-18/01-ai-photo-editing-prompts.png: IMAGE_BLANK — legacy asset is a blank frame (std=0.0000, colors=1) — it must not be published or kept
- stories/2026-10-03/01-guided-vision-story-optimized.png: FILE_UNDECODABLE — no pixels decoded ('')

## Validation run 2026-10-03T22:07:48Z

- run: `local` commit: `local`
- renderer: `convert` imagemagick: `Version: ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25 https://imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 316 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `5a86ebf8f1bdb402…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 338 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `4ba31035515a65c0…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 268 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `f081f55014da983b…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 294 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `f81d3a0d7135deac…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 261 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `45013b2d7aeb08dd…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:08:34Z

- run: `local` commit: `local`
- renderer: `convert` imagemagick: `Version: ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25 https://imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 316 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `5a86ebf8f1bdb402…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 338 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `4ba31035515a65c0…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 268 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `f081f55014da983b…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 294 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `f81d3a0d7135deac…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 261 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `45013b2d7aeb08dd…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:12:24Z

- run: `local` commit: `local`
- renderer: `convert` imagemagick: `Version: ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25 https://imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 316 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `5a86ebf8f1bdb402…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 338 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `4ba31035515a65c0…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 268 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `f081f55014da983b…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 294 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `f81d3a0d7135deac…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 261 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `45013b2d7aeb08dd…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:12:55Z

- run: `local` commit: `local`
- renderer: `convert` imagemagick: `Version: ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25 https://imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 316 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `5a86ebf8f1bdb402…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 338 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `4ba31035515a65c0…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 268 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `f081f55014da983b…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 294 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `f81d3a0d7135deac…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 261 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `45013b2d7aeb08dd…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:13:10Z

- run: `local` commit: `local`
- renderer: `convert` imagemagick: `Version: ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25 https://imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 316 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `5a86ebf8f1bdb402…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 338 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `4ba31035515a65c0…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 268 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `f081f55014da983b…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 294 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `f81d3a0d7135deac…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 261 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `45013b2d7aeb08dd…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:20:09Z

- run: `local` commit: `local`
- renderer: `convert` imagemagick: `Version: ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25 https://imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 316 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `5a86ebf8f1bdb402…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 338 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `4ba31035515a65c0…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 268 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `f081f55014da983b…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 294 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `f81d3a0d7135deac…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 261 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `45013b2d7aeb08dd…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:21:58Z

- run: `37158086038` commit: `6a0be954256d2587ce2e5f126e065d1794c8c9ae`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 186 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `3f6d196eb0887b5c…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:22:03Z

- run: `37158086038` commit: `6a0be954256d2587ce2e5f126e065d1794c8c9ae`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 186 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `3f6d196eb0887b5c…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:22:39Z

- run: `local` commit: `local`
- renderer: `convert` imagemagick: `Version: ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25 https://imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 186 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `3f6d196eb0887b5c…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:24:12Z

- run: `local` commit: `local`
- renderer: `convert` imagemagick: `Version: ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25 https://imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 317 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `ceee6e57798cb357…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:26:40Z

- run: `37158338453` commit: `4c09e8ac118c51973aad5d2c414fce71bb1bb45c`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 314 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `fe4cd04c62f9b3ee…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:26:49Z

- run: `37158338453` commit: `4c09e8ac118c51973aad5d2c414fce71bb1bb45c`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 314 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `fe4cd04c62f9b3ee…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:29:44Z

- run: `37158520106` commit: `33351bf6f415ce574c0fcc36aa6f41e0dc3fd8fa`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 314 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `fe4cd04c62f9b3ee…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:29:51Z

- run: `37158520106` commit: `33351bf6f415ce574c0fcc36aa6f41e0dc3fd8fa`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 314 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `fe4cd04c62f9b3ee…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:33:38Z

- run: `37158739492` commit: `d496f32d72a39816a2b261bd5559ebbf981966ec`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 314 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `fe4cd04c62f9b3ee…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-03T22:33:47Z

- run: `37158739492` commit: `d496f32d72a39816a2b261bd5559ebbf981966ec`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 314 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `fe4cd04c62f9b3ee…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-10T14:44:12Z

- run: `38060319656` commit: `543ea6989ba020a7e4473605f82f6c51d5962aaa`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-06/chatgpt-try-on-natural-results.jpg` | story | 1080x1920 | 244 KB | sRGB | `stories/2026-10-06/chatgpt-try-on-natural-results.svg` | `45baa88252ed7567…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `stories/2026-10-10/chatgpt-intelligent-ui-budget-tool.jpg` | story | 1080x1920 | 338 KB | sRGB | `stories/2026-10-10/chatgpt-intelligent-ui-budget-tool.svg` | `c3a27029b817c5c1…` | PASS |
| `stories/2026-10-04/gemini-guided-vision-story.jpg` | story | 1080x1920 | 276 KB | sRGB | `stories/2026-10-04/gemini-guided-vision-story.svg` | `0c74092b5defb6ac…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 314 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `fe4cd04c62f9b3ee…` | PASS |
| `posts/2026-10-04-ai-news-bulletin.jpg` | post | 1080x1350 | 264 KB | sRGB | `posts/2026-10-04-ai-news-bulletin.svg` | `bd28fc60f00d680c…` | PASS |
| `posts/2026-10-05-ai-daily-bulletin.jpg` | post | 1080x1350 | 297 KB | sRGB | `posts/2026-10-05-ai-daily-bulletin.svg` | `f269dfaca0077616…` | PASS |
| `posts/2026-10-06-ai-daily-bulletin.jpg` | post | 1080x1350 | 72 KB | sRGB | `posts/2026-10-06-ai-daily-bulletin.svg` | `4459ca8225ae3ef9…` | PASS |
| `posts/2026-10-07-ai-daily-bulletin-final.jpg` | post | 1080x1350 | 181 KB | sRGB | `posts/2026-10-07-ai-daily-bulletin-final.svg` | `2ddf99069ed60c1a…` | PASS |
| `posts/2026-10-07-ai-daily-bulletin.jpg` | post | 1080x1350 | 37 KB | sRGB | `posts/2026-10-07-ai-daily-bulletin.svg` | `9499e68c24be0cbf…` | PASS |
| `posts/2026-10-09-ai-daily-bulletin.jpg` | post | 1080x1350 | 319 KB | sRGB | `posts/2026-10-09-ai-daily-bulletin.svg` | `8d870c5737c59068…` | PASS |
| `posts/2026-10-10-ai-daily-bulletin-full.jpg` | post | 1080x1350 | 206 KB | sRGB | `posts/2026-10-10-ai-daily-bulletin-full.svg` | `7f12a262417942db…` | PASS |
| `posts/2026-10-10-ai-daily-bulletin.jpg` | post | 1080x1350 | 41 KB | sRGB | `posts/2026-10-10-ai-daily-bulletin.svg` | `3d89e891fc130f12…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |

## Validation run 2026-10-10T14:45:19Z

- run: `38060319656` commit: `543ea6989ba020a7e4473605f82f6c51d5962aaa`
- renderer: `rsvg-convert` imagemagick: `Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org`
- **FINAL STATUS: PASS**

| asset | kind | dimensions | size | colorspace | source | sha256 | result |
|---|---|---|---|---|---|---|---|
| `stories/2026-09-14/story01-ai-photo-editing.jpg` | story | 1080x1920 | 336 KB | sRGB | `stories/2026-09-14/story01-ai-photo-editing.svg` | `c1ea0a3766133c4f…` | PASS |
| `stories/2026-09-18/01-ai-photo-editing-prompts.jpg` | story | 1080x1920 | 266 KB | sRGB | `stories/2026-09-18/01-ai-photo-editing-prompts.svg` | `bea3bda179bffb71…` | PASS |
| `stories/2026-10-06/chatgpt-try-on-natural-results.jpg` | story | 1080x1920 | 244 KB | sRGB | `stories/2026-10-06/chatgpt-try-on-natural-results.svg` | `45baa88252ed7567…` | PASS |
| `stories/2026-10-02/01-ai-agent-prompt.jpg` | story | 1080x1920 | 291 KB | sRGB | `stories/2026-10-02/01-ai-agent-prompt.svg` | `0c7811fb09fa1949…` | PASS |
| `stories/2026-10-03/01-guided-vision-story.jpg` | story | 1080x1920 | 259 KB | sRGB | `stories/2026-10-03/01-guided-vision-story.svg` | `c3791346987bac38…` | PASS |
| `stories/2026-10-10/chatgpt-intelligent-ui-budget-tool.jpg` | story | 1080x1920 | 338 KB | sRGB | `stories/2026-10-10/chatgpt-intelligent-ui-budget-tool.svg` | `c3a27029b817c5c1…` | PASS |
| `stories/2026-10-04/gemini-guided-vision-story.jpg` | story | 1080x1920 | 276 KB | sRGB | `stories/2026-10-04/gemini-guided-vision-story.svg` | `0c74092b5defb6ac…` | PASS |
| `posts/2026-10-03-ai-news-bulletin.jpg` | post | 1080x1350 | 314 KB | sRGB | `posts/2026-10-03-ai-news-bulletin.svg` | `fe4cd04c62f9b3ee…` | PASS |
| `posts/2026-10-04-ai-news-bulletin.jpg` | post | 1080x1350 | 264 KB | sRGB | `posts/2026-10-04-ai-news-bulletin.svg` | `bd28fc60f00d680c…` | PASS |
| `posts/2026-10-05-ai-daily-bulletin.jpg` | post | 1080x1350 | 297 KB | sRGB | `posts/2026-10-05-ai-daily-bulletin.svg` | `f269dfaca0077616…` | PASS |
| `posts/2026-10-06-ai-daily-bulletin.jpg` | post | 1080x1350 | 72 KB | sRGB | `posts/2026-10-06-ai-daily-bulletin.svg` | `4459ca8225ae3ef9…` | PASS |
| `posts/2026-10-07-ai-daily-bulletin-final.jpg` | post | 1080x1350 | 181 KB | sRGB | `posts/2026-10-07-ai-daily-bulletin-final.svg` | `2ddf99069ed60c1a…` | PASS |
| `posts/2026-10-07-ai-daily-bulletin.jpg` | post | 1080x1350 | 37 KB | sRGB | `posts/2026-10-07-ai-daily-bulletin.svg` | `9499e68c24be0cbf…` | PASS |
| `posts/2026-10-09-ai-daily-bulletin.jpg` | post | 1080x1350 | 319 KB | sRGB | `posts/2026-10-09-ai-daily-bulletin.svg` | `8d870c5737c59068…` | PASS |
| `posts/2026-10-10-ai-daily-bulletin-full.jpg` | post | 1080x1350 | 206 KB | sRGB | `posts/2026-10-10-ai-daily-bulletin-full.svg` | `7f12a262417942db…` | PASS |
| `posts/2026-10-10-ai-daily-bulletin.jpg` | post | 1080x1350 | 41 KB | sRGB | `posts/2026-10-10-ai-daily-bulletin.svg` | `3d89e891fc130f12…` | PASS |
| `stories/2026-09-14/story01-ai-photo-editing.png` | story | 1080x1920 | 279 KB | sRGB | - | `bb6ce5520ca13faf…` | PASS |
