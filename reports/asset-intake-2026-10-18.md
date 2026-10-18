# Asset intake incident report — 2026-10-18 AI daily bulletin

- **Asset:** `2026-10-18-ai-daily-bulletin.jpg`
- **Expected size:** 886785 bytes (declared by the generation step)
- **Intended repository path:** `posts/2026-10-18-ai-daily-bulletin.jpg`
  (the standard daily-bulletin location used by every previous bulletin)
- **Status:** transfer **NOT performed** — the original file bytes are not
  reachable from any environment that holds the GitHub token. No substitute
  file was created, and no success is claimed.

## 1. What was reported

The tool used to register the file on GitHub reported that it "has no access
to the local file" and that the binary content "must be transferred to it".

## 2. Evidence gathered (2026-10-18, all checks executed for real)

| # | Check | Result |
|---|---|---|
| 1 | Full local sandbox search by name (`2026-10-18*`) | not present |
| 2 | Full local sandbox search by exact size (886785 bytes) | not present |
| 3 | Git dangling objects / stash / reflog (local clone) | empty — fresh shallow clone at `12601e5` |
| 4 | Tree of all 11 remote branches searched for the file | not present on any branch |
| 5 | Same trees searched for any file of 886785 bytes | no match |
| 6 | All workflow run artifacts (10 runs inspected) | only `media-validation` / `publish-plan` JSON reports — no images |
| 7 | Tags and releases | none |
| 8 | Repository push events | last push 2026-10-17T21:17:50Z (manual web upload of an unrelated PNG, commit `12601e5`); **zero writes on 2026-10-18** |
| 9 | Arena connectors `github` and `windsor` | both **unsupported** in this environment |
| 10 | Real write path available | `gh` CLI + token, authenticated as `aftabcollege-gif` (verified by API reads and by the self-test below) |

Additional context: branch `access-test` contains
`access-tests/chatgpt-write-permission-2026-10-16.txt` ("GitHub write-access
verification test") — the bulletin was generated in an external assistant
sandbox, whose GitHub file tool takes UTF-8 text parameters and cannot open
local files.

## 3. Root cause

An **interface and environment mismatch**, not a truncated upload:

1. the image was generated in a sandbox environment that the chat-side
   GitHub "create file" tool cannot read — the tool never had the bytes;
2. that tool accepts only UTF-8 **text** content: raw JPEG bytes are not
   valid UTF-8, and base64 passed as "text" would be re-encoded (corrupted)
   or rejected, with request-size limits able to truncate a ~1.18 MB payload;
3. consequently the transfer **never started**: no blob, no commit, no
   branch, no artifact references the file (checks 4–8 above). This rules
   out a partial transfer, interrupted upload or Base64 truncation — the
   failure mode is "no bytes ever left the generation sandbox".

Size analysis: 886785 bytes → base64 = ceil(886785/3)×4 = **1,182,380
characters** (~1.13 MB) — well within the GitHub Git Data API limits, so a
single-request blob upload is safe once the bytes are available.

## 4. Fix shipped — `scripts/github/commit_asset.py`

A Git Data API bridge that runs where the file is and transfers the bytes
themselves: PRECHECK → IDENTITY → BLOB (one base64 POST, blob SHA
cross-checked locally) → COMMIT (base_tree preserves all existing paths,
fast-forward-only ref update, race retries) → VERIFY (blob read back,
byte-for-byte size + SHA-256 comparison) → REPORT (per-stage JSON log).
Full contract documented in the README section
"External media intake (Git Data API bridge)".

## 5. Mechanism self-test (executed for real on 2026-10-18)

Run against GitHub on isolated scratch branch `transfer-selftest-20261018`
(created from `main`@`12601e5`, deleted afterwards):

| Test | Scenario | Result |
|---|---|---|
| A | full transfer of a real bulletin JPEG (163123 B) → blob → tree → commit `1192e11e` → branch updated → API blob read-back: size and SHA-256 identical to local | **PASS** (exit 0) |
| A′ | independent verification via the git protocol (`git fetch` + `git cat-file`): size 163123, SHA-256 `d6012eb6d3a9c1f2…` == local | **PASS** |
| B | 2234976-byte PNG payload, base64 of 2979968 chars in one request (2.7× the pending bulletin's payload) → commit `1a614e88`, read-back identical | **PASS** (exit 0) |
| C | re-run of A (identical bytes already at path) | **SKIP_IDENTICAL**, no duplicate commit (exit 0) |
| D | different bytes to an occupied path | **BLOCKED** — refuses to overwrite an existing file (exit 1) |
| E | `--expected-size 886785` against a 163123-byte file | **precheck FAIL** — aborts before any network write (exit 1) |

During test A the self-test itself caught a real bug (sub-directory tree
verification) and the check was fixed and re-run — the gate does fail when
it should.

## 6. Blocker — required input for the pending transfer

The original `2026-10-18-ai-daily-bulletin.jpg` (886785 bytes) must be
supplied as **bytes** from wherever it was generated. Accepted channels:

1. attach the file to the working session (it lands in the workspace and the
   bridge runs directly), or
2. upload it through the GitHub web UI to any branch/path (the bridge then
   moves it to `posts/…` without touching the bytes), or
3. place it on any storage this environment can reach.

What is **not** acceptable (per the incident constraints): regenerating the
image, re-compressing, converting format, or substituting another file.

Once the bytes are available:

```bash
GH_TOKEN=… python3 scripts/github/commit_asset.py \
  --file 2026-10-18-ai-daily-bulletin.jpg \
  --repo-path posts/2026-10-18-ai-daily-bulletin.jpg \
  --owner aftabcollege-gif --repo AI_Learning --branch main \
  --expected-size 886785
```

## 7. Publishing status (Windsor / Instagram)

Not requested, not claimed. The file is not in the repository, so there is
no pinned public URL to hand to a publisher, and `publish.py` correctly
refuses to publish anything that has not passed the media gate with a
matching receipt. The Windsor connector is unsupported in this environment;
publishing runs through the existing receipt contract
(`reports/publish-receipts.json`). No upload, acceptance or published state
exists for this asset.

## 8. Residual limitations

- Workflow run logs and artifact contents for run `39030721038` (2026-10-17,
  publish-gate exit 1) could not be downloaded from this sandbox (network
  egress restrictions; only annotations were readable, and they carry no
  reason detail). That failure predates this incident and concerns the Oct
  17 renders; it is recorded here explicitly rather than guessed at.
- The pending bulletin's SVG source (if one exists) has also not been
  committed; the render pipeline therefore cannot validate the package until
  either the source or the final JPEG is ingested.
