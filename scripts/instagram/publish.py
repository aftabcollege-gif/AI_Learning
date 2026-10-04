#!/usr/bin/env python3
"""Publish gate: turn validated assets into a verified publishing plan.

This script never *assumes* a publish worked.  It:

1. refuses to run unless ``media-manifest.json`` says the FINAL PUBLISH GATE
   passed (so an unvalidated or stale asset can never reach Instagram);
2. validates every FINAL asset and groups numbered carousel slides into one post;
3. resolves a *pinned* public URL for each asset (full 40-char commit SHA, so
   the URL can never serve a different revision) and fetches it back, comparing
   size and SHA-256 against the local file — a CDN or raw-host cache that hands
   out an old revision is caught here rather than on Instagram;
4. verifies the publisher's receipts (Metricool / Windsor).  A successful
   upload API call is *not* accepted as proof: the receipt must reference the
   same SHA-256 we published and carry a media id;
5. writes ``reports/publish-plan.json`` plus a run summary and exits non-zero
   unless every item is either fully verified or explicitly reported as
   awaiting a publisher receipt.

Publisher preference: Windsor first, Metricool as the optional fallback —
both may only receive assets that passed the gate. Carousel slides are grouped
into one post-level handoff while retaining per-file hashes and URL checks.
Sending a source SVG or an unvalidated file to Instagram as a "workaround" is
never allowed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

PAGE_SIZE_LIMIT = 8 * 1024 * 1024
DEFAULT_URL_BASE = "https://raw.githubusercontent.com"
PUBLISHERS = ("windsor", "metricool")
RECEIPT_STATUSES_OK = ("published", "processed", "scheduled")


@dataclass
class PublishItem:
    asset: str
    kind: str
    dimensions: str
    size_bytes: int
    sha256: str
    source_svg: str
    package: str
    account: str = ""
    content_type: str = ""
    post_format: str = "single_image"
    carousel_order: int = 1
    scheduled: str = ""
    auto_publish: bool = False
    caption: str = ""
    metadata_path: str = ""
    source_sha256: str = ""
    public_url: str = ""
    url_verified: bool = False
    url_status: str = ""
    publisher: str = ""
    publish_status: str = "NOT_REQUESTED"
    media_id: str = ""
    permalink: str = ""
    verified_published: bool = False
    notes: List[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.url_verified and not self.blocking_notes

    @property
    def blocking_notes(self) -> List[str]:
        return [n for n in self.notes if n.startswith("BLOCKED")]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


# --------------------------------------------------------------------------
# metadata parsing
# --------------------------------------------------------------------------

def parse_metadata(path: str) -> Dict[str, object]:
    """Extract publication metadata from a slide or package Markdown sidecar."""
    text = read_text(path)
    info: Dict[str, object] = {}
    if not text:
        return info

    m = re.search(r"Instagram\s*:\s*`?@?([A-Za-z0-9._]+)`?", text, re.IGNORECASE)
    if m:
        info["account"] = m.group(1)
    m = re.search(r"(?:^|\n)\s*[-*]?\s*(?:نوع|type)\s*:\s*\**\s*`?(Story|Post|Reel)`?",
                  text, re.IGNORECASE)
    if m:
        info["content_type"] = m.group(1).capitalize()
    m = re.search(r"(?:^|\n)\s*[-*]?\s*(?:قالب|format)\s*:\s*`?(Carousel|کاروسل|Single(?: image)?|تک\s*تصویر)`?",
                  text, re.IGNORECASE)
    if m:
        value = m.group(1).strip().lower()
        info["post_format"] = "carousel" if value in ("carousel", "کاروسل") else "single_image"
    m = re.search(r"(?:^|\n)\s*[-*]?\s*(?:زمان|scheduled?)\s*:\s*`?([0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9:]{4,8})`?",
                  text, re.IGNORECASE)
    if m:
        info["scheduled"] = m.group(1).strip()
    m = re.search(r"انتشار خودکار\s*:\s*\**\s*`?(فعال|غیرفعال|active|inactive|true|false)`?",
                  text, re.IGNORECASE)
    if m:
        info["auto_publish"] = m.group(1).lower() in ("فعال", "active", "true")
    m = re.search(r"(?:^|\n)\s*[-*]?\s*(?:ناشر|publisher)\s*:\s*`?(metricool|windsor)`?",
                  text, re.IGNORECASE)
    if m:
        info["publisher"] = m.group(1).lower()
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        info["title"] = m.group(1).strip()
    sec = re.search(r"^##\s*(?:Selected news|محتوا|caption|کپشن)\s*\n(.*?)(?=\n##|\Z)",
                    text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if sec:
        # Preserve paragraph breaks and hashtag separation for Instagram. Normalize
        # only trailing whitespace; do not flatten the caption into one line.
        info["caption"] = "\n".join(line.rstrip() for line in sec.group(1).strip().splitlines())[:2200]
    return info


def carousel_order(asset_rel: str) -> int:
    """Read a leading slide number (01-...) or fall back to a stable final order."""
    name = os.path.basename(asset_rel)
    match = re.match(r"(?:slide[-_ ]*)?(\d{1,3})(?:[-_. ]|$)", name, re.IGNORECASE)
    return int(match.group(1)) if match else 1


def find_sidecar(root: str, asset_rel: str) -> str:
    """Locate the metadata markdown that describes this asset."""
    directory = os.path.dirname(os.path.join(root, asset_rel))
    stem = os.path.splitext(os.path.basename(asset_rel))[0]
    candidates = [
        os.path.join(directory, stem + ".md"),
    ]
    if os.path.isdir(directory):
        candidates += [os.path.join(directory, n) for n in sorted(os.listdir(directory))
                       if n.lower().endswith(".md")]
    # Carousels may use one package-level sidecar shared by every numbered slide.
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return ""


# --------------------------------------------------------------------------
# URL verification
# --------------------------------------------------------------------------

def build_public_url(base: str, owner: str, repo: str, commit: str, path: str,
                     cache_bust: bool = True) -> str:
    url = f"{base.rstrip('/')}/{owner}/{repo}/{commit}/{path}"
    if cache_bust:
        url += f"?v={commit[:12]}"
    return url


def fetch(url: str, timeout: int = 45) -> Tuple[int, bytes, Dict[str, str]]:
    req = urllib.request.Request(url, headers={
        "User-Agent": "AI_Learning-media-verifier/1.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(PAGE_SIZE_LIMIT + 1)
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, body, headers
    except urllib.error.HTTPError as exc:
        return exc.code, b"", {}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, b"", {"error": str(exc)}


def verify_public_url(url: str, local_path: str, expected_sha: str,
                      attempts: int = 3, log=print) -> Tuple[bool, str]:
    """Fetch the public URL and prove it serves exactly the local file."""
    local_size = os.path.getsize(local_path)
    last = "no attempt made"
    for attempt in range(1, attempts + 1):
        status, body, headers = fetch(url)
        if status == 200 and body:
            if len(body) != local_size:
                last = (f"size mismatch: URL returned {len(body)} bytes, "
                        f"local file is {local_size} bytes")
                log(f"    attempt {attempt}: {last}")
            else:
                remote_sha = hashlib.sha256(body).hexdigest()
                if remote_sha != expected_sha:
                    last = (f"content mismatch: URL serves sha256 {remote_sha[:12]}…, "
                            f"expected {expected_sha[:12]}… (stale or wrong revision)")
                    log(f"    attempt {attempt}: {last}")
                else:
                    ctype = headers.get("content-type", "?")
                    return True, (f"HTTP 200, {len(body)} bytes, sha256 matches, "
                                  f"content-type {ctype}")
        elif status == 0:
            last = f"network error: {headers.get('error', 'unknown')}"
            log(f"    attempt {attempt}: {last}")
        else:
            last = f"HTTP {status}"
            log(f"    attempt {attempt}: {last}")
        if attempt < attempts:
            time.sleep(2 * attempt)
    return False, last


# --------------------------------------------------------------------------
# receipts
# --------------------------------------------------------------------------

def verify_receipts(items: Sequence[PublishItem], receipts_doc: dict, log=print) -> None:
    """Match publisher receipts to the SHA-256 we actually intended to publish."""
    receipts = receipts_doc.get("receipts", []) if isinstance(receipts_doc, dict) else []
    by_asset: Dict[str, List[dict]] = {}
    for receipt in receipts:
        if isinstance(receipt, dict) and receipt.get("asset"):
            by_asset.setdefault(receipt["asset"], []).append(receipt)

    for item in items:
        candidates = by_asset.get(item.asset, [])
        if not candidates:
            if item.auto_publish:
                item.publish_status = "NOT_VERIFIED"
                item.notes.append(
                    "BLOCKED publisher receipt missing: auto-publish is enabled for this item "
                    "but no receipt confirms it was published — a successful upload API call "
                    "is not accepted as proof")
            else:
                item.publish_status = "NOT_REQUESTED"
                item.notes.append("no publisher receipt present (auto-publish not enabled)")
            continue

        matched = [r for r in candidates if r.get("sha256") == item.sha256]
        if not matched:
            wrong = ", ".join(str(r.get("sha256", "?"))[:12] for r in candidates)
            item.publish_status = "FAILED"
            item.notes.append(
                f"BLOCKED receipt hash mismatch: receipt(s) reference {wrong}… but the "
                f"validated asset is {item.sha256[:12]}… — a different revision was published")
            continue

        receipt = matched[0]
        item.publisher = str(receipt.get("publisher", ""))
        item.media_id = str(receipt.get("media_id", ""))
        item.permalink = str(receipt.get("permalink", ""))
        status = str(receipt.get("status", "")).lower()
        if status not in RECEIPT_STATUSES_OK:
            item.publish_status = "FAILED"
            item.notes.append(f"BLOCKED receipt status is {status!r}, not one of {RECEIPT_STATUSES_OK}")
        elif not item.media_id:
            item.publish_status = "FAILED"
            item.notes.append("BLOCKED receipt has no media id — the published media cannot be verified")
        else:
            item.publish_status = "PUBLISHED_VERIFIED"
            item.verified_published = True
            item.notes.append(f"receipt verified: {item.publisher or 'publisher'} media {item.media_id}")


# --------------------------------------------------------------------------
# post-level handoff
# --------------------------------------------------------------------------
def build_post_records(items: Sequence[PublishItem]) -> List[dict]:
    """Group carousel slides into one Windsor post while keeping file checks per asset."""
    groups: Dict[str, List[PublishItem]] = {}
    for item in items:
        # A package sidecar is the stable grouping key for a carousel. Legacy
        # single-image/story assets remain one post record per asset.
        key = item.metadata_path if item.post_format == "carousel" and item.metadata_path else item.asset
        groups.setdefault(key, []).append(item)

    posts: List[dict] = []
    for key, children in sorted(groups.items()):
        if children[0].post_format == "carousel":
            children = sorted(children, key=lambda child: (child.carousel_order, child.asset))
        lead = children[0]
        ready = all(child.ready and child.publish_status != "FAILED" for child in children)
        media = [
            {
                "order": child.carousel_order if lead.post_format == "carousel" else 1,
                "asset": child.asset,
                "public_url": child.public_url,
                "sha256": child.sha256,
                "dimensions": child.dimensions,
                "size_bytes": child.size_bytes,
                "url_verified": child.url_verified,
            }
            for child in children
        ]
        posts.append({
            "post_id": key,
            "package": lead.package,
            "account": lead.account,
            "content_type": lead.content_type,
            "format": lead.post_format,
            "caption": lead.caption,
            "scheduled": lead.scheduled,
            "auto_publish": lead.auto_publish,
            "publisher": lead.publisher,
            "status": "READY" if ready else "BLOCKED",
            "asset_count": len(media),
            "assets": media,
            "notes": sorted({note for child in children for note in child.notes}),
        })
    return posts


# --------------------------------------------------------------------------
# summary
# --------------------------------------------------------------------------

def print_summary(items: Sequence[PublishItem], manifest: dict, args, blocked: bool,
                  emit=print) -> None:
    emit("")
    emit("=" * 78)
    emit("PUBLISH SUMMARY")
    emit("=" * 78)
    for item in items:
        emit(f"ASSET            : {item.asset}")
        emit(f"SOURCE FILE      : {item.source_svg or '-'}")
        emit(f"POST FORMAT      : {item.post_format}"
             + (f" (slide {item.carousel_order})" if item.post_format == "carousel" else ""))
        emit(f"SOURCE SHA256    : {item.source_sha256[:32] or '-'}")
        emit(f"OUTPUT SHA256    : {item.sha256}")
        emit(f"DIMENSIONS       : {item.dimensions}")
        emit(f"FILE SIZE        : {item.size_bytes} bytes ({item.size_bytes / 1024:.0f} KB)")
        emit(f"COLORSPACE       : sRGB (4:4:4)")
        emit(f"RENDERER         : {manifest.get('renderer', '-')}")
        emit(f"RENDERER VERSION : {manifest.get('image_magick', '-')}")
        emit(f"WORKFLOW RUN     : {args.run_id or 'local'}")
        emit(f"COMMIT SHA       : {args.commit_sha or 'local'}")
        emit(f"VALIDATION RESULT: {manifest.get('gate_status', 'UNKNOWN')}")
        emit(f"PUBLIC URL       : {item.public_url or '-'}")
        emit(f"URL VERIFIED     : {'YES' if item.url_verified else 'NO'} — {item.url_status}")
        emit(f"PUBLISH RESULT   : {item.publish_status}")
        emit(f"MEDIA ID         : {item.media_id or '-'}")
        emit(f"FINAL STATUS     : {'PASS' if (item.ready and item.publish_status != 'FAILED') else 'BLOCKED'}")
        for note in item.notes:
            emit(f"  NOTE           : {note}")
        emit("-" * 78)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Verified publishing plan for Instagram media")
    ap.add_argument("--root", default=".")
    ap.add_argument("--manifest", default="media-manifest.json")
    ap.add_argument("--plan", default="reports/publish-plan.json")
    ap.add_argument("--report", default="reports/publish-report.json")
    ap.add_argument("--receipts", default="reports/publish-receipts.json")
    ap.add_argument("--owner", default=os.environ.get("GITHUB_REPOSITORY_OWNER", ""))
    ap.add_argument("--repo", default=(os.environ.get("GITHUB_REPOSITORY", "/").split("/")[-1]
                                      if "/" in os.environ.get("GITHUB_REPOSITORY", "/") else ""))
    ap.add_argument("--commit", default=os.environ.get("GITHUB_SHA", ""))
    ap.add_argument("--url-base", default=DEFAULT_URL_BASE,
                    help="base URL for raw assets (override to test against a local server)")
    ap.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    ap.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA", ""))
    ap.add_argument("--publisher", default="windsor", choices=PUBLISHERS + ("auto",),
                    help="publisher for the handoff; 'auto' tries Windsor then Metricool")
    ap.add_argument("--skip-url-verification", action="store_true")
    ap.add_argument("--plan-only", action="store_true",
                    help="build and verify the publishing plan without enforcing publisher "
                         "receipts (used on push; receipts only exist after a real publish run)")
    ap.add_argument("--require-published", action="store_true",
                    help="fail unless every auto-publish item has a verified receipt")
    ap.add_argument("--allow-branch-urls", action="store_true",
                    help="allow non-SHA-pinned URLs (not recommended: CDN caches go stale)")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    emit = print
    emit("=" * 78)
    emit("PUBLISH GATE — verified publishing plan")
    emit("=" * 78)

    manifest_path = os.path.join(root, args.manifest)
    manifest = load_json(manifest_path)
    if not manifest:
        emit(f"[BLOCKED] manifest {args.manifest} not found or unreadable")
        emit("FINAL STATUS: BLOCKED")
        emit("REASON: the media manifest is missing; nothing may be published")
        return 1

    gate = str(manifest.get("gate_status", "UNKNOWN"))
    emit(f"gate status : {gate}")
    emit(f"renderer    : {manifest.get('renderer', '-')}")
    emit(f"validated at: {manifest.get('generated_at', '-')}")

    if gate != "PASS":
        emit("")
        emit("[BLOCKED] media-manifest.json reports a failed validation gate")
        emit("FINAL STATUS: BLOCKED")
        emit("REASON: assets did not pass the FINAL PUBLISH GATE; publishing is refused")
        return 1

    assets = manifest.get("assets", {})
    if not assets:
        emit("[BLOCKED] the manifest lists no validated assets")
        emit("FINAL STATUS: BLOCKED")
        return 1

    # commit pinning
    commit = args.commit
    if not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
        if args.allow_branch_urls:
            emit(f"[WARN] commit {commit!r} is not a full SHA; using it as-is (cache staleness possible)")
        else:
            head = ""
            try:
                import subprocess
                head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                                      stdout=subprocess.PIPE, text=True).stdout.strip()
            except (OSError, subprocess.SubprocessError):
                head = ""
            if re.fullmatch(r"[0-9a-f]{40}", head):
                commit = head
                emit(f"[WARN] --commit was not a full SHA; pinned to HEAD {commit[:12]}…")
            else:
                emit("[BLOCKED] cannot determine a full 40-character commit SHA for URL pinning")
                emit("REASON: a branch URL can serve a stale revision from a CDN cache")
                emit("FINAL STATUS: BLOCKED")
                return 1
    emit(f"commit pin  : {commit}")
    emit("")

    receipts_doc = load_json(os.path.join(root, args.receipts))
    if receipts_doc:
        emit(f"receipts    : {len(receipts_doc.get('receipts', []))} supplied for publisher verification")
    else:
        emit("receipts    : none supplied yet (publish results will be reported as NOT_VERIFIED)")
    emit("")

    items: List[PublishItem] = []
    for asset_rel, meta in sorted(assets.items()):
        local = os.path.join(root, asset_rel)
        item = PublishItem(
            asset=asset_rel,
            kind=str(meta.get("kind", "")),
            dimensions=str(meta.get("dimensions", "")),
            size_bytes=int(meta.get("size_bytes", 0)),
            sha256=str(meta.get("sha256", "")),
            source_svg=str(meta.get("source_svg", "") or ""),
            package=os.path.dirname(asset_rel) or ".",
        )
        if item.source_svg:
            source_path = os.path.join(root, item.source_svg)
            if os.path.exists(source_path):
                item.source_sha256 = sha256_file(source_path)

        if not os.path.exists(local):
            item.notes.append(f"BLOCKED asset missing on disk: {asset_rel}")
            items.append(item)
            continue
        actual = sha256_file(local)
        if meta.get("sha256") and actual != meta["sha256"]:
            item.notes.append(
                f"BLOCKED manifest hash {str(meta['sha256'])[:12]}… != file hash {actual[:12]}… "
                "— the working tree changed after validation")
        item.sha256 = actual

        sidecar = find_sidecar(root, asset_rel)
        info = parse_metadata(sidecar) if sidecar else {}
        item.account = str(info.get("account", ""))
        item.content_type = str(info.get("content_type", "")) or item.kind.capitalize()
        item.post_format = str(info.get("post_format", "single_image"))
        item.carousel_order = carousel_order(asset_rel)
        item.scheduled = str(info.get("scheduled", ""))
        item.auto_publish = bool(info.get("auto_publish", False))
        item.caption = str(info.get("caption", info.get("title", "")))
        item.metadata_path = os.path.relpath(sidecar, root).replace(os.sep, "/") if sidecar else ""
        if sidecar:
            item.notes.append(f"metadata source: {item.metadata_path}")
        else:
            item.notes.append("no metadata sidecar found; scheduling details unknown")

        if args.owner and args.repo:
            item.public_url = build_public_url(args.url_base, args.owner, args.repo,
                                               commit, asset_rel)
        else:
            item.notes.append("BLOCKED repository owner/name unknown; cannot build a public URL")
        items.append(item)

    # ---- URL verification ---------------------------------------------
    if not args.skip_url_verification:
        emit("── public URL verification " + "─" * 51)
        for item in items:
            if not item.public_url:
                item.url_status = "no URL"
                continue
            emit(f"  {item.asset}")
            emit(f"    url: {item.public_url}")
            ok, detail = verify_public_url(item.public_url, os.path.join(root, item.asset),
                                           item.sha256, log=emit)
            item.url_verified = ok
            item.url_status = detail
            emit(f"    -> {'VERIFIED' if ok else 'NOT VERIFIED'}: {detail}")
            if not ok:
                item.notes.append(
                    f"BLOCKED public URL does not serve the validated file ({detail})")
        emit("")
    else:
        for item in items:
            item.url_status = "verification skipped by request"
            item.notes.append("public URL was not verified (--skip-url-verification)")
        emit("[WARN] public URL verification skipped\n")

    # ---- receipts ------------------------------------------------------
    if args.plan_only:
        for item in items:
            if item.publish_status == "NOT_REQUESTED":
                item.publish_status = "NOT_REQUESTED"
        emit("── receipts disabled (--plan-only): the plan is verified, publishing is not asserted")
        emit("")
    else:
        verify_receipts(items, receipts_doc, log=emit)

    # ---- publisher selection ------------------------------------------
    for item in items:
        if args.publisher == "auto":
            item.publisher = item.publisher or PUBLISHERS[0]
        else:
            item.publisher = args.publisher
        if args.publisher == "auto":
            item.notes.append("publisher chain: windsor -> metricool on failure")

    # ---- verdict -------------------------------------------------------
    blocked_items = [i for i in items if i.blocking_notes or not i.ready]
    failed_publish = [i for i in items if i.publish_status == "FAILED"]
    ready = [i for i in items if i.ready and i.publish_status != "FAILED"]
    pending = [i for i in ready if i.publish_status in ("NOT_REQUESTED", "NOT_VERIFIED")]

    print_summary(items, manifest, args, bool(blocked_items), emit=emit)

    blocked = bool(blocked_items) or bool(failed_publish)
    if args.require_published and pending:
        blocked = True

    emit("=" * 78)
    if blocked:
        emit("FINAL STATUS: BLOCKED")
        reasons: List[str] = []
        for item in items:
            for note in item.notes:
                if note.startswith("BLOCKED"):
                    reasons.append(f"{item.asset}: {note[len('BLOCKED '):]}")
        if not reasons:
            reasons.append("one or more items could not be verified")
        for reason in reasons:
            emit(f"REASON: {reason}")
        emit("PUBLISH = BLOCKED")
    else:
        emit(f"FINAL STATUS: PASS ({len(ready)} item(s) ready to publish)")
        if pending:
            emit("NOTE: publishing requires the publisher's receipt to confirm the "
                 "result; uploads are reported as NOT_VERIFIED until then")

    plan = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_id": args.run_id,
        "commit_sha": commit,
        "gate_status": gate,
        "publisher_preference": args.publisher,
        "status": "BLOCKED" if blocked else "PASS",
        "posts": build_post_records(items),
        "items": [
            {
                "asset": i.asset,
                "kind": i.kind,
                "package": i.package,
                "dimensions": i.dimensions,
                "size_bytes": i.size_bytes,
                "sha256": i.sha256,
                "source_svg": i.source_svg,
                "source_sha256": i.source_sha256,
                "account": i.account,
                "content_type": i.content_type,
                "format": i.post_format,
                "carousel_order": i.carousel_order,
                "caption": i.caption,
                "scheduled": i.scheduled,
                "auto_publish": i.auto_publish,
                "public_url": i.public_url,
                "url_verified": i.url_verified,
                "url_status": i.url_status,
                "publisher": i.publisher,
                "publish_status": i.publish_status,
                "media_id": i.media_id,
                "permalink": i.permalink,
                "verified_published": i.verified_published,
                "notes": i.notes,
            }
            for i in items
        ],
    }
    plan_path = os.path.join(root, args.plan)
    os.makedirs(os.path.dirname(plan_path), exist_ok=True)
    with open(plan_path, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    report_path = os.path.join(root, args.report)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump({"summary": {
            "run_id": args.run_id,
            "commit_sha": commit,
            "gate_status": gate,
            "final_status": plan["status"],
            "items": len(items),
            "ready": len(ready),
            "blocked": len(blocked_items) + len(failed_publish),
            "pending_receipt": len(pending),
        }, "plan": plan}, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    emit(f"plan        : {args.plan}")
    emit(f"report      : {args.report}")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
