from fastapi import APIRouter
import aiosqlite
from app.config import settings

router = APIRouter()


@router.get("/demographics")
async def get_demographics(
    scope: str = "global",
    scope_id: str = "",
    topic_id: int | None = None,
    organic_only: bool = False,
):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT dimension, bucket, SUM(count) as count FROM demo_aggregates "
            "WHERE scope=? AND organic_only=? GROUP BY dimension, bucket ORDER BY dimension, count DESC",
            (scope, int(organic_only)),
        )
    return {"aggregates": [dict(r) for r in rows], "k_anon": settings.k_anon}
