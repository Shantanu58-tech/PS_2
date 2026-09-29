from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any
import aiosqlite
from app.models.canonical import Post, Account


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def upsert_account(db: aiosqlite.Connection, acc: Account) -> None:
    await db.execute(
        """
        INSERT OR REPLACE INTO accounts
        (platform, account_id, handle, display_name, bio, location_text,
         created_at, followers, following, verified, synthetic)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            acc.platform, acc.account_id, acc.handle, acc.display_name,
            acc.bio, acc.location_text,
            acc.created_at.isoformat() if acc.created_at else None,
            acc.followers, acc.following,
            int(acc.verified) if acc.verified is not None else None,
            int(acc.synthetic),
        ),
    )
    await db.commit()


async def upsert_post(db: aiosqlite.Connection, post: Post) -> None:
    await db.execute(
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
            post.channel_or_community, post.lang,
            json.dumps(post.metrics), int(post.synthetic), post.ledger_seq,
        ),
    )
    await db.commit()


async def get_posts(
    db: aiosqlite.Connection,
    platform: str | None = None,
    from_ts: str | None = None,
    to_ts: str | None = None,
    topic_id: int | None = None,
    q: str | None = None,
    organic_only: bool = False,
    limit: int = 100,
    cursor: str | None = None,
) -> list[dict]:
    clauses: list[str] = []
    params: list[Any] = []

    if platform:
        clauses.append("p.platform = ?")
        params.append(platform)
    if from_ts:
        clauses.append("p.created_at >= ?")
        params.append(from_ts)
    if to_ts:
        clauses.append("p.created_at <= ?")
        params.append(to_ts)
    if cursor:
        clauses.append("p.created_at < ?")
        params.append(cursor)
    if q:
        clauses.append("p.post_id IN (SELECT rowid FROM posts_fts WHERE posts_fts MATCH ?)")
        params.append(q)
    if organic_only:
        clauses.append(
            "NOT EXISTS (SELECT 1 FROM coord_accounts ca WHERE ca.platform=p.platform "
            "AND ca.account_id=p.author_id AND ca.score >= 0.7)"
        )
    if topic_id is not None:
        clauses.append(
            "EXISTS (SELECT 1 FROM topic_assign ta WHERE ta.platform=p.platform "
            "AND ta.post_id=p.post_id AND ta.topic_id=?)"
        )
        params.append(topic_id)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    async with db.execute(
        f"SELECT * FROM posts p {where} ORDER BY p.created_at DESC LIMIT ?", params
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]
