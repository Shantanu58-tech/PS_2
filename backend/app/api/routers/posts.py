from fastapi import APIRouter, Depends
import aiosqlite
from app.db.session import get_db
from app.db.repo import get_posts

router = APIRouter()


@router.get("/posts")
async def list_posts(
    platform: str | None = None,
    from_ts: str | None = None,
    to_ts: str | None = None,
    topic_id: int | None = None,
    q: str | None = None,
    organic_only: bool = False,
    limit: int = 100,
    cursor: str | None = None,
):
    async with aiosqlite.connect(__import__("app.config", fromlist=["settings"]).settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await get_posts(db, platform, from_ts, to_ts, topic_id, q, organic_only, limit, cursor)
    return {"posts": rows, "count": len(rows)}