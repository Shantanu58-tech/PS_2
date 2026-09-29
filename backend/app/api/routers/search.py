from fastapi import APIRouter
import aiosqlite
from app.config import settings

router = APIRouter()


@router.get("/search")
async def search(q: str, limit: int = 20):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT p.* FROM posts p JOIN posts_fts f ON p.rowid=f.rowid WHERE posts_fts MATCH ? LIMIT ?",
            (q, limit),
        )
    return {"results": [dict(r) for r in rows], "query": q}
