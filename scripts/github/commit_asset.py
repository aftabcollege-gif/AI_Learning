#!/usr/bin/env python3
"""Commit a locally generated binary media asset to GitHub via the Git Data API.

WHY THIS EXISTS (2026-10-18 incident)
-------------------------------------
An AI-generated bulletin JPEG (``2026-10-18-ai-daily-bulletin.jpg``, 886785
bytes) existed only inside the sandbox that generated it.  The chat-side
GitHub "create file" tool used in that environment (a) runs outside the
sandbox and cannot read local files, and (b) accepts only UTF-8 *text*
content, so raw JPEG bytes could never be handed to it.  The result: the
transfer never happened at all — the file is absent from every branch, not
truncated or corrupted.

This script is the real bridge.  It runs **where the file actually is**
(a CI runner, a developer machine, or an agent sandbox that holds a GitHub
token) and transfers the *bytes themselves* through the Git Data API:

  1. PRECHECK   — file exists, is a complete image (magic bytes), respects
                  ``--expected-size`` / ``--expected-sha256`` from the
                  generation step, and the repo's 8 MB media ceiling.
                  SHA-256 is recorded before any network call.
  2. IDENTITY   — if the exact same bytes already sit at the target path on
                  the target branch, stop with SKIP_IDENTICAL (re-running
                  the intake can never create a duplicate commit); if the
                  path holds *different* bytes, refuse unless
                  ``--force-replace`` is given (existing files are never
                  silently overwritten).
  3. BLOB       — POST ``/repos/{o}/{r}/git/blobs`` with the FULL base64
                  payload in a single request (no chunking, so no chunk can
                  be lost or reordered); the returned blob SHA is
                  cross-checked against the locally computed git blob SHA
                  before anything else happens.
  4. COMMIT     — read the branch head, create a tree on top of the head
                  tree (``base_tree`` preserves every existing path), create
                  a commit whose parent is the current head, then update the
                  branch ref with ``force=false`` (fast-forward only).  On a
                  422/409 race the head is re-read and the whole stage is
                  retried, so a concurrent push is never overwritten.
  5. VERIFY     — read the stored blob back through the API, decode it, and
                  require size AND SHA-256 equality with the local file;
                  confirm the branch ref points at the new commit and the
                  commit's tree really contains the path.  A green API call
                  alone is never accepted as proof.
  6. REPORT     — a per-stage JSON log (default
                  ``reports/asset-transfer-log.json``) with an independent
                  status for every stage.  Exit code 0 only when every stage
                  passed (or the asset was already present, byte-identical).

Security: the token is read from GH_TOKEN / GITHUB_TOKEN and is never
printed, logged, or written into any output file.

Usage
-----
    python3 scripts/github/commit_asset.py \
        --file 2026-10-18-ai-daily-bulletin.jpg \
        --repo-path posts/2026-10-18-ai-daily-bulletin.jpg \
        --owner aftabcollege-gif --repo AI_Learning --branch main \
        --expected-size 886785 \
        --message "Add 2026-10-18 AI daily bulletin"
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Sequence, Tuple

API_BASE = "https://api.github.com"
DEFAULT_MAX_BYTES = 8 * 1024 * 1024  # repository media policy: assets <= 8 MB
JPEG_SOI = b"\xff\xd8\xff"
JPEG_EOI = b"\xff\xd9"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
RETRYABLE_STATUS = (409, 429, 500, 502, 503, 504)
MAX_ATTEMPTS = 3

STAGE_ORDER = ("precheck", "identity", "blob", "commit", "verify", "report")


# ---------------------------------------------------------------------------
# stage log
# ---------------------------------------------------------------------------

class StageLog:
    """Per-stage status recording; the exit verdict is derived from it."""

    def __init__(self) -> None:
        self.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.stages: List[Dict[str, str]] = []

    def record(self, stage: str, status: str, detail: str = "") -> None:
        entry = {
            "stage": stage,
            "status": status,  # PASS | SKIP | FAIL | BLOCKED
            "detail": detail,
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.stages.append(entry)
        print(f"[{stage:>8}] {status:<7} {detail}".rstrip())

    def status_of(self, stage: str) -> Optional[str]:
        for entry in self.stages:
            if entry["stage"] == stage:
                return entry["status"]
        return None

    def all_ok(self) -> bool:
        return all(e["status"] in ("PASS", "SKIP") for e in self.stages)

    def write(self, path: str, extra: Dict[str, Any]) -> None:
        doc = {"started_at": self.started_at,
               "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "ok": self.all_ok()}
        doc.update(extra)
        doc["stages"] = self.stages
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")


# ---------------------------------------------------------------------------
# hashing helpers
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    """The SHA-1 git assigns a blob — lets us verify GitHub's answer locally."""
    header = b"blob %d\x00" % len(data)
    return hashlib.sha1(header + data).hexdigest()


def read_local(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# GitHub REST helper (stdlib only; token never appears in errors or logs)
# ---------------------------------------------------------------------------

class GitHubError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message


def api_request(token: str, method: str, path: str,
                body: Optional[Dict[str, Any]] = None,
                expect: Tuple[int, ...] = (200, 201)) -> Dict[str, Any]:
    """One API call with controlled retries for transient failures."""
    url = path if path.startswith("http") else API_BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    last_error = "no attempt made"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        request.add_header("User-Agent", "AI_Learning-asset-intake/1.0")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw.strip() else {}
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", "replace")
            message = _safe_message(payload)
            if exc.code in expect:
                return json.loads(payload) if payload.strip() else {}
            last_error = f"HTTP {exc.code}: {message}"
            if exc.code not in RETRYABLE_STATUS:
                raise GitHubError(exc.code, message)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = f"network error: {exc}"
        if attempt < MAX_ATTEMPTS:
            time.sleep(2 * attempt)
    raise GitHubError(0, last_error)


def _safe_message(payload: str) -> str:
    """Extract a short API error message; never leaks auth headers."""
    try:
        doc = json.loads(payload)
        message = str(doc.get("message", payload))
        return message[:300]
    except json.JSONDecodeError:
        return payload[:300]


# ---------------------------------------------------------------------------
# git data API operations
# ---------------------------------------------------------------------------

def get_branch_head(token: str, owner: str, repo: str, branch: str) -> str:
    """Current head commit SHA of the branch (handles names containing '/')."""
    for candidate in (branch, urllib.parse.quote(branch, safe="")):
        try:
            doc = api_request(token, "GET",
                              f"/repos/{owner}/{repo}/git/ref/heads/{candidate}")
            return str(doc["object"]["sha"])
        except GitHubError as exc:
            if exc.status == 404:
                continue
            raise
    raise GitHubError(404, f"branch refs/heads/{branch} not found")


def find_tree_entry(token: str, owner: str, repo: str, commit_sha: str,
                    path: str) -> Optional[Dict[str, Any]]:
    """Locate ``path`` in the commit's tree; None when it does not exist."""
    commit = api_request(token, "GET", f"/repos/{owner}/{repo}/git/commits/{commit_sha}")
    tree_sha = str(commit["tree"]["sha"])
    tree = api_request(token, "GET",
                       f"/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1")
    for entry in tree.get("tree", []):
        if entry.get("path") == path and entry.get("type") == "blob":
            return entry
    return None


def create_blob(token: str, owner: str, repo: str, content_b64: str) -> str:
    doc = api_request(token, "POST", f"/repos/{owner}/{repo}/git/blobs",
                      body={"content": content_b64, "encoding": "base64"},
                      expect=(200, 201))
    return str(doc["sha"])


def create_tree(token: str, owner: str, repo: str, base_tree: str,
                path: str, blob_sha: str) -> Dict[str, Any]:
    doc = api_request(token, "POST", f"/repos/{owner}/{repo}/git/trees",
                      body={"base_tree": base_tree,
                            "tree": [{"path": path, "mode": "100644",
                                      "type": "blob", "sha": blob_sha}]},
                      expect=(200, 201))
    return doc


def get_tree(token: str, owner: str, repo: str, tree_sha: str) -> List[Dict[str, Any]]:
    doc = api_request(token, "GET", f"/repos/{owner}/{repo}/git/trees/{tree_sha}")
    return list(doc.get("tree", []))


def resolve_path_in_tree(token: str, owner: str, repo: str, tree_sha: str,
                         path: str) -> Optional[Dict[str, Any]]:
    """Walk the tree hierarchy segment by segment to locate ``path``.

    POST /git/trees only returns the root level, so a sub-directory asset
    must be verified by descending into its subtrees.
    """
    entry: Optional[Dict[str, Any]] = None
    current_sha = tree_sha
    segments = [s for s in path.split("/") if s]
    for index, segment in enumerate(segments):
        entries = get_tree(token, owner, repo, current_sha)
        entry = next((e for e in entries if e.get("path") == segment), None)
        if entry is None:
            return None
        if index < len(segments) - 1:
            if entry.get("type") != "tree":
                return None
            current_sha = str(entry["sha"])
    return entry


def create_commit(token: str, owner: str, repo: str, message: str,
                  tree_sha: str, parent_sha: str) -> str:
    doc = api_request(token, "POST", f"/repos/{owner}/{repo}/git/commits",
                      body={"message": message, "tree": tree_sha,
                            "parents": [parent_sha]},
                      expect=(200, 201))
    return str(doc["sha"])


def update_branch(token: str, owner: str, repo: str, branch: str,
                  commit_sha: str) -> None:
    """Fast-forward only (force=false): concurrent commits are never lost."""
    api_request(token, "PATCH",
                f"/repos/{owner}/{repo}/git/refs/heads/{branch}",
                body={"sha": commit_sha, "force": False})


def read_blob(token: str, owner: str, repo: str, blob_sha: str) -> bytes:
    doc = api_request(token, "GET", f"/repos/{owner}/{repo}/git/blobs/{blob_sha}")
    if str(doc.get("encoding", "")).lower() != "base64" or "content" not in doc:
        raise GitHubError(0, "blob read-back is not base64 content")
    return base64.b64decode("".join(doc["content"].split()))


# ---------------------------------------------------------------------------
# precheck helpers
# ---------------------------------------------------------------------------

def check_magic(path: str, data: bytes) -> Tuple[bool, str]:
    lower = path.lower()
    if lower.endswith((".jpg", ".jpeg")):
        if data[:3] != JPEG_SOI:
            return False, "JPEG_MAGIC_INVALID: file does not start with FFD8FF"
        if not data.rstrip(b"\x00").endswith(JPEG_EOI):
            return False, "JPEG_EOI_MISSING: file does not end with FFD9"
        return True, "JPEG magic bytes present (FFD8FF ... FFD9)"
    if lower.endswith(".png"):
        if data[:8] != PNG_MAGIC:
            return False, "PNG_MAGIC_INVALID: file does not start with PNG signature"
        return True, "PNG signature present"
    return True, "magic check skipped (unsupported extension)"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Commit a binary asset to GitHub via the Git Data API, "
                    "transferring the file's own bytes (never a path or a URL).")
    parser.add_argument("--file", required=True,
                        help="local file whose bytes will be transferred")
    parser.add_argument("--repo-path", required=True,
                        help="destination path inside the repository")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--message", default="",
                        help="commit message (default mentions the asset path)")
    parser.add_argument("--expected-size", type=int, default=None,
                        help="exact byte size declared by the generation step")
    parser.add_argument("--expected-sha256", default=None,
                        help="SHA-256 declared by the generation step")
    parser.add_argument("--max-size", type=int, default=DEFAULT_MAX_BYTES,
                        help=f"hard ceiling in bytes (default {DEFAULT_MAX_BYTES})")
    parser.add_argument("--force-replace", action="store_true",
                        help="allow replacing a *different* file already at "
                             "--repo-path (existing files are protected by default)")
    parser.add_argument("--log", default="reports/asset-transfer-log.json",
                        help="where to write the per-stage JSON log")
    parser.add_argument("--dry-run", action="store_true",
                        help="run PRECHECK + IDENTITY only; no writes to GitHub")
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    log = StageLog()
    context: Dict[str, Any] = {
        "file": args.file,
        "repo_path": args.repo_path,
        "target": f"{args.owner}/{args.repo}@{args.branch}",
        "expected_size": args.expected_size,
        "expected_sha256": args.expected_sha256,
    }

    print("=" * 78)
    print("ASSET INTAKE — Git Data API binary transfer")
    print("=" * 78)
    print(f"file       : {args.file}")
    print(f"repo path  : {args.repo_path}")
    print(f"target     : {args.owner}/{args.repo} branch {args.branch}")
    print(f"started at : {log.started_at}")
    print()

    # ---- stage 1: PRECHECK ------------------------------------------------
    if not os.path.isfile(args.file):
        log.record("precheck", "FAIL", f"local file not found: {args.file}")
        log.write(args.log, context)
        return 1
    if not token:
        log.record("precheck", "FAIL",
                   "no GitHub token: set GH_TOKEN or GITHUB_TOKEN")
        log.write(args.log, context)
        return 1

    data = read_local(args.file)
    size = len(data)
    digest = sha256_bytes(data)
    context["size_bytes"] = size
    context["sha256"] = digest
    context["git_blob_sha"] = git_blob_sha(data)

    problems: List[str] = []
    if args.expected_size is not None and size != args.expected_size:
        problems.append(f"size mismatch: file is {size} bytes, expected "
                        f"{args.expected_size} (the bytes changed or the wrong "
                        f"file was given)")
    if size > args.max_size:
        problems.append(f"file exceeds the {args.max_size}-byte ceiling "
                        f"({size} bytes)")
    magic_ok, magic_detail = check_magic(args.repo_path, data)
    if not magic_ok:
        problems.append(magic_detail)
    if args.expected_sha256 and args.expected_sha256.lower() != digest:
        problems.append(f"sha256 mismatch: file hashes to {digest}, expected "
                        f"{args.expected_sha256}")
    if problems:
        log.record("precheck", "FAIL", "; ".join(problems))
        log.write(args.log, context)
        return 1
    log.record("precheck", "PASS",
               f"{size} bytes, sha256 {digest[:16]}…, {magic_detail}")

    # ---- stage 2: IDENTITY (idempotency + path protection) -----------------
    head = get_branch_head(token, args.owner, args.repo, args.branch)
    context["base_head"] = head
    existing = find_tree_entry(token, args.owner, args.repo, head, args.repo_path)
    if existing is not None:
        existing_sha = str(existing.get("sha", ""))
        if existing_sha == git_blob_sha(data):
            log.record("identity", "SKIP",
                       f"identical bytes already at {args.repo_path} on "
                       f"{args.branch} (blob {existing_sha[:12]}…); "
                       "no duplicate commit created")
            log.record("blob", "SKIP", "not needed")
            log.record("commit", "SKIP", "not needed")
            log.record("verify", "SKIP",
                       "asset already present; verified identical by blob SHA")
            log.write(args.log, context)
            return 0
        if not args.force_replace:
            log.record("identity", "BLOCKED",
                       f"{args.repo_path} already exists on {args.branch} with "
                       f"DIFFERENT bytes (blob {existing_sha[:12]}…); refusing "
                       "to overwrite an existing file without --force-replace")
            log.write(args.log, context)
            return 1
        log.record("identity", "PASS",
                   f"replacing existing {args.repo_path} (--force-replace given)")

    if args.dry_run:
        log.record("identity", "PASS",
                   f"dry run: {args.repo_path} is free on {args.branch}")
        log.record("blob", "SKIP", "dry run")
        log.record("commit", "SKIP", "dry run")
        log.record("verify", "SKIP", "dry run")
        log.write(args.log, context)
        return 0
    if existing is None:
        log.record("identity", "PASS",
                   f"{args.repo_path} does not exist on {args.branch} yet")

    # ---- stages 3+4: BLOB, then TREE/COMMIT/REF with race protection ------
    content_b64 = base64.b64encode(data).decode("ascii")
    context["base64_chars"] = len(content_b64)
    if len(content_b64) != ((size + 2) // 3) * 4:
        log.record("blob", "FAIL", "base64 encoding produced the wrong length")
        log.write(args.log, context)
        return 1

    blob_sha = create_blob(token, args.owner, args.repo, content_b64)
    if blob_sha != git_blob_sha(data):
        log.record("blob", "FAIL",
                   f"GitHub returned blob {blob_sha[:12]}… but the local bytes "
                   f"hash to blob {git_blob_sha(data)[:12]}… — the stored blob "
                   "is NOT the file on disk; aborting before any commit")
        log.write(args.log, context)
        return 1
    log.record("blob", "PASS",
               f"created blob {blob_sha[:12]}… (matches local git-blob hash; "
               f"base64 payload {len(content_b64)} chars in one request)")

    message = args.message or f"Add media asset {args.repo_path} (Git Data API intake)"
    commit_sha = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        head = get_branch_head(token, args.owner, args.repo, args.branch)
        context["base_head"] = head
        commit = api_request(token, "GET",
                             f"/repos/{args.owner}/{args.repo}/git/commits/{head}")
        base_tree = str(commit["tree"]["sha"])
        tree = create_tree(token, args.owner, args.repo, base_tree,
                           args.repo_path, blob_sha)
        tree_sha = str(tree["sha"])
        entry = resolve_path_in_tree(token, args.owner, args.repo,
                                     tree_sha, args.repo_path)
        if entry is None or entry.get("type") != "blob" or \
                str(entry.get("sha", "")) != blob_sha:
            log.record("commit", "FAIL",
                       f"new tree does not map {args.repo_path} to blob "
                       f"{blob_sha[:12]}…; aborting")
            log.write(args.log, context)
            return 1
        commit_sha = create_commit(token, args.owner, args.repo, message,
                                   tree_sha, head)
        try:
            update_branch(token, args.owner, args.repo, args.branch, commit_sha)
            log.record("commit", "PASS",
                       f"commit {commit_sha[:12]}… on top of {head[:12]}…; "
                       f"branch {args.branch} fast-forwarded (attempt {attempt})")
            break
        except GitHubError as exc:
            if exc.status in (409, 422) and attempt < MAX_ATTEMPTS:
                print(f"[  commit] RETRY   branch moved during the update "
                      f"(attempt {attempt}); re-reading head and rebuilding")
                time.sleep(2 * attempt)
                continue
            log.record("commit", "FAIL",
                       f"could not fast-forward {args.branch} after {attempt} "
                       f"attempt(s): {exc}")
            log.write(args.log, context)
            return 1
    context["commit_sha"] = commit_sha

    # ---- stage 5: VERIFY (never trust a green API response alone) ---------
    failures: List[str] = []
    stored = read_blob(token, args.owner, args.repo, blob_sha)
    if len(stored) != size:
        failures.append(f"read-back size {len(stored)} != local {size}")
    if sha256_bytes(stored) != digest:
        failures.append(f"read-back sha256 {sha256_bytes(stored)[:16]}… != "
                        f"local {digest[:16]}…")
    if not check_magic(args.repo_path, stored)[0]:
        failures.append("stored blob is not a decodable image by magic bytes")
    new_head = get_branch_head(token, args.owner, args.repo, args.branch)
    if new_head != commit_sha:
        failures.append(f"branch {args.branch} points at {new_head[:12]}…, "
                        f"not the new commit {commit_sha[:12]}…")
    entry = find_tree_entry(token, args.owner, args.repo, new_head, args.repo_path)
    if entry is None or str(entry.get("sha", "")) != blob_sha:
        failures.append(f"commit tree does not contain {args.repo_path} -> "
                        f"blob {blob_sha[:12]}…")
    if failures:
        log.record("verify", "FAIL", "; ".join(failures))
        log.write(args.log, context)
        return 1
    log.record("verify", "PASS",
               f"blob read back from GitHub: {len(stored)} bytes, sha256 "
               f"{sha256_bytes(stored)[:16]}… == local; branch and tree verified")

    # ---- stage 6: REPORT ----------------------------------------------------
    log.record("report", "PASS",
               f"stage log written to {args.log}; "
               f"https://github.com/{args.owner}/{args.repo}/blob/{commit_sha}/{args.repo_path}")
    log.write(args.log, context)

    print()
    print(f"TRANSFER VERIFIED — {args.repo_path} @ {args.owner}/{args.repo}"
          f"/{args.branch}")
    print(f"  commit : https://github.com/{args.owner}/{args.repo}/commit/{commit_sha}")
    print(f"  file   : https://github.com/{args.owner}/{args.repo}/blob/{commit_sha}/{args.repo_path}")
    print(f"  raw    : https://raw.githubusercontent.com/{args.owner}/{args.repo}/{commit_sha}/{args.repo_path}")
    print(f"  size   : {size} bytes   sha256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
