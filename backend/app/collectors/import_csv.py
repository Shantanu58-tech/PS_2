"""Instagram / Facebook import adapter (PS "desirable" platforms).

Neither platform offers a free live API for public posts, so, as the PRD
states openly, these are ingested from analyst-supplied exports (Meta Content
Library / CrowdTangle-style CSV, or Instagram data-download JSON flattened to
CSV). Rows go through the same ledger -> normaliser path as live data.

Recognised columns (case-insensitive; first match wins):
  post_id:   id, post_id, url, link
  author_id: author_id, account_id, page_id, user_id, handle, username, page_name
  text:      text, message, caption, description, content
  created:   created_at, post_created, timestamp, date, created_time
  parent:    parent_id, parent_post_id, reply_to
  kind:      kind, type
  likes/comments/shares: likes, total_interactions, comments, shares
"""
from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from app.models.canonical import RawRecord

FIELDS = {
    "post_id": ["id", "post_id", "url", "link"],
    "author_id": ["author_id", "account_id", "page_id", "user_id", "handle", "username", "user_name", "page_name"],
    "text": ["text", "message", "caption", "description", "content"],
    "created_at": ["created_at", "post_created", "timestamp", "date", "created_time"],
    "parent_post_id": ["parent_id", "parent_post_id", "reply_to"],
    "kind": ["kind", "type"],
}
METRICS = ["likes", "total_interactions", "comments", "shares", "views"]
_METRIC_KEYS = {m.replace("_", " "): m for m in METRICS}
KIND_MAP = {"comment": "comment", "reply": "reply", "share": "repost", "reel": "post", "photo": "post",
            "video": "post", "status": "post", "link": "post", "album": "post", "post": "post"}


def _pick(row: dict[str, str], names: list[str]) -> str | None:
    lower = {k.lower().strip().replace(" ", "_"): v for k, v in row.items() if k}
    for n in names:
        if lower.get(n):
            return lower[n].strip()
    return None


def _iso(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()
    v = value.strip()
    if v.upper().endswith(" IST"):  # %Z does not reliably parse IST
        dt = datetime.strptime(v[:-4].strip(), "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30))).astimezone(timezone.utc).isoformat()
    if v.isdigit():  # unix seconds
        return datetime.fromtimestamp(int(v), tz=timezone.utc).isoformat()
    for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(v, fmt)
            return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()
        except ValueError:
            continue
    return datetime.fromisoformat(v.replace("Z", "+00:00")).isoformat()


def rows_to_records(rows: Iterator[dict[str, str]], platform: str, source: str) -> Iterator[RawRecord]:
    if platform not in ("instagram", "facebook"):
        raise ValueError("platform must be instagram or facebook")
    for i, row in enumerate(rows):
        text = _pick(row, FIELDS["text"]) or ""
        post_id = _pick(row, FIELDS["post_id"]) or hashlib.sha256(f"{source}:{i}:{text}".encode()).hexdigest()[:16]
        kind = KIND_MAP.get((_pick(row, FIELDS["kind"]) or "post").lower(), "post")
        payload = {
            "platform": platform,
            "post_id": post_id,
            "author_id": _pick(row, FIELDS["author_id"]) or "unknown",
            "kind": kind,
            "text": text,
            "created_at": _iso(_pick(row, FIELDS["created_at"])),
            "parent_post_id": _pick(row, FIELDS["parent_post_id"]),
            "metrics": {_METRIC_KEYS.get(k.lower().strip(), k.lower().strip()): v for k, v in row.items()
                        if k and k.lower().strip().replace(" ", "_") in METRICS and v},
            # Real exports are not synthetic; the bundled demo sample marks itself.
            "synthetic": (_pick(row, ["synthetic"]) or "").lower() in ("1", "true", "yes"),
            "import_source": source,
        }
        yield RawRecord(platform=platform, collector_id=f"import_csv:{platform}",
                        collected_at=datetime.now(timezone.utc), payload=payload)


def read_csv(path: str | Path, platform: str) -> list[RawRecord]:
    p = Path(path)
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(rows_to_records(csv.DictReader(f), platform, p.name))


def read_csv_text(text: str, platform: str, source: str = "upload") -> list[RawRecord]:
    return list(rows_to_records(csv.DictReader(io.StringIO(text)), platform, source))
