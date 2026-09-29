from __future__ import annotations
import sqlite3
from datetime import timezone
from app.models.canonical import RawRecord
from app.pipeline.normalize import normalize
from app.db.repo import upsert_post, upsert_account
from app.config import settings
import aiosqlite


async def ingest_record(raw: RawRecord) -> None:
    post, acc = normalize(raw)
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        if acc:
            await upsert_account(db, acc)
        await upsert_post(db, post)
        if post.text:
            edges = []
            if post.parent_post_id:
                edges.append((
                    post.platform, post.author_id,
                    post.platform, post.parent_post_id[:50],
                    "reply", post.created_at.isoformat(), post.post_id, 1.0,
                ))
            if post.origin_post_id:
                kind = "repost" if post.kind == "repost" else "forward"
                weight = 0.8 if kind == "repost" else 0.9
                edges.append((
                    post.platform, post.author_id,
                    post.platform, post.origin_post_id[:50],
                    kind, post.created_at.isoformat(), post.post_id, weight,
                ))
            for m in post.mentions:
                edges.append((
                    post.platform, post.author_id,
                    post.platform, m,
                    "mention", post.created_at.isoformat(), post.post_id, 0.3,
                ))
            if edges:
                await db.executemany(
                    "INSERT INTO edges (src_platform,src_account,dst_platform,dst_account,kind,ts,post_id,weight) VALUES (?,?,?,?,?,?,?,?)",
                    edges,
                )
                await db.commit()
