from fastapi import APIRouter
import aiosqlite
from app.config import settings

router = APIRouter()


@router.get("/topics")
async def list_topics():
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT * FROM topics ORDER BY last_seen DESC LIMIT 50"
        )
    return {"topics": [dict(r) for r in rows]}


@router.get("/topics/{topic_id}/series")
async def topic_series(topic_id: int):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT * FROM topic_series WHERE topic_id=? ORDER BY bucket_start",
            (topic_id,),
        )
        bursts = await db.execute_fetchall(
            "SELECT * FROM bursts WHERE topic_id=? ORDER BY start",
            (topic_id,),
        )
    return {"series": [dict(r) for r in rows], "bursts": [dict(r) for r in bursts]}
