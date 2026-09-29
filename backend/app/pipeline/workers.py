"""Ingestion: raw record -> ledger (append-only, hash-chained) -> canonical tables.

Every record is written to ``raw_records`` through the LedgerWriter *before*
it is normalised, so each post carries the ``ledger_seq`` of the evidence it
came from.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import threading
from pathlib import Path
from typing import Iterable

from app.config import settings
from app.ledger.chain import LedgerWriter
from app.models.canonical import Account, Post, RawRecord
from app.nlp.langid import detect_lang
from app.pipeline.normalize import normalize


def _json_safe(payload: dict) -> dict:
    # Ledger payloads must be canonical-JSON serialisable.
    return json.loads(json.dumps(payload, default=str))


class Ingestor:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.ledger = LedgerWriter(db_path)
        self._lock = threading.Lock()
        self.last_seq = 0

    def ingest_many(self, raws: Iterable[RawRecord], flush: bool = True) -> int:
        n = 0
        with self._lock, sqlite3.connect(self.db_path) as conn:
            for raw in raws:
                self._ingest(conn, raw)
                n += 1
            conn.commit()
            if flush and self.last_seq:
                self.ledger.flush(conn, self.last_seq)
        return n

    def flush(self) -> None:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            if self.last_seq:
                self.ledger.flush(conn, self.last_seq)

    # -- internals -----------------------------------------------------
    def _ingest(self, conn: sqlite3.Connection, raw: RawRecord) -> None:
        payload = _json_safe(raw.payload)
        seq = self.ledger.append(conn, raw.platform, raw.collector_id, raw.collected_at, payload, commit=False)
        self.last_seq = seq
        post, acc = normalize(raw)
        post.ledger_seq = seq
        if not post.lang:
            post.lang = detect_lang(post.text)
        if acc:
            _upsert_account(conn, acc)
        inserted = _insert_post(conn, post)
        if inserted:
            _write_edges(conn, post)
            _attach_media(conn, post, payload.get("media") or [])


def _upsert_account(conn: sqlite3.Connection, acc: Account) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO accounts
        (platform, account_id, handle, display_name, bio, location_text,
         created_at, followers, following, verified, synthetic)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            acc.platform, acc.account_id, acc.handle, acc.display_name, acc.bio,
            acc.location_text, acc.created_at.isoformat() if acc.created_at else None,
            acc.followers, acc.following,
            int(acc.verified) if acc.verified is not None else None, int(acc.synthetic),
        ),
    )


def _insert_post(conn: sqlite3.Connection, post: Post) -> bool:
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO posts
        (platform, post_id, author_id, kind, text, created_at, collected_at,
         parent_post_id, root_post_id, origin_post_id, channel, lang,
         metrics_json, synthetic, ledger_seq)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            post.platform, post.post_id, post.author_id, post.kind, post.text,
            post.created_at.isoformat(), post.collected_at.isoformat(),
            post.parent_post_id, post.root_post_id, post.origin_post_id,
            post.channel_or_community, post.lang, json.dumps(post.metrics),
            int(post.synthetic), post.ledger_seq,
        ),
    )
    return cur.rowcount > 0


def _author_of(conn: sqlite3.Connection, post_id: str) -> tuple[str, str] | None:
    row = conn.execute(
        "SELECT platform, author_id FROM posts WHERE post_id=? LIMIT 1", (post_id,)
    ).fetchone()
    return (row[0], row[1]) if row else None


def _write_edges(conn: sqlite3.Connection, post: Post) -> None:
    """Account->account interaction edges.

    Reply / repost targets are resolved to the parent post's author. If the
    parent has not been ingested yet the edge points at ``post:<id>`` and is
    resolved later by ``resolve_pending_edges``.
    """
    ts = post.created_at.isoformat()
    edges: list[tuple] = []
    targets: list[tuple[str, str, float]] = []
    if post.parent_post_id:
        targets.append((post.parent_post_id, "reply", 1.0))
    if post.origin_post_id:
        kind = "repost" if post.kind == "repost" else "forward"
        targets.append((post.origin_post_id, kind, 0.8 if kind == "repost" else 0.9))
    for target_post, kind, weight in targets:
        resolved = _author_of(conn, target_post)
        dst_platform, dst_account = resolved if resolved else (post.platform, f"post:{target_post}")
        if dst_account == post.author_id:
            continue  # self-thread
        edges.append((post.platform, post.author_id, dst_platform, dst_account, kind, ts, post.post_id, weight))
    for m in post.mentions:
        # resolve @handle to the account id so the graph has one node per account
        row = conn.execute(
            "SELECT platform, account_id FROM accounts WHERE handle=? LIMIT 1", (m,)).fetchone()
        dst_platform, dst = (row[0], row[1]) if row else (post.platform, m)
        if dst != post.author_id:
            edges.append((post.platform, post.author_id, dst_platform, dst, "mention", ts, post.post_id, 0.3))
    if edges:
        conn.executemany(
            "INSERT INTO edges (src_platform,src_account,dst_platform,dst_account,kind,ts,post_id,weight) "
            "VALUES (?,?,?,?,?,?,?,?)",
            edges,
        )


def resolve_pending_edges(db_path: str) -> int:
    """Point edges that were written before their parent post at its author."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE edges SET
              dst_platform = (SELECT p.platform FROM posts p WHERE p.post_id = substr(edges.dst_account, 6) LIMIT 1),
              dst_account  = (SELECT p.author_id FROM posts p WHERE p.post_id = substr(edges.dst_account, 6) LIMIT 1)
            WHERE dst_account LIKE 'post:%'
              AND EXISTS (SELECT 1 FROM posts p WHERE p.post_id = substr(edges.dst_account, 6))
            """
        )
        conn.execute("DELETE FROM edges WHERE dst_account = src_account")
        conn.commit()
        return cur.rowcount


def _attach_media(conn: sqlite3.Connection, post: Post, media: list[dict]) -> None:
    from app.analytics.lineage import phash_image

    for m in media:
        local = m.get("local_path")
        if not local:
            continue
        path = Path(local)
        if not path.is_absolute():
            path = Path(settings.media_dir) / path
        if not path.exists():
            continue
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        media_id = m.get("media_id") or sha[:16]
        conn.execute(
            "INSERT OR IGNORE INTO media (media_id, kind, url, local_path, sha256, phash) VALUES (?,?,?,?,?,?)",
            (media_id, m.get("kind", "image"), m.get("url"), str(path), sha, phash_image(str(path))),
        )
        conn.execute(
            "INSERT INTO post_media (platform, post_id, media_id) VALUES (?,?,?)",
            (post.platform, post.post_id, media_id),
        )


_ingestors: dict[str, Ingestor] = {}
_ingestors_lock = threading.Lock()


def get_ingestor(db_path: str | None = None) -> Ingestor:
    path = db_path or settings.db_path
    with _ingestors_lock:
        if path not in _ingestors:
            _ingestors[path] = Ingestor(path)
        return _ingestors[path]


def reset_ingestors() -> None:
    with _ingestors_lock:
        _ingestors.clear()


async def ingest_record(raw: RawRecord) -> None:
    await asyncio.to_thread(get_ingestor().ingest_many, [raw], False)
