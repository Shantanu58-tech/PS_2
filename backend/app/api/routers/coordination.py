from fastapi import APIRouter
import aiosqlite
from app.config import settings

router = APIRouter()


@router.get("/coordination/clusters")
async def list_clusters():
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT * FROM coord_clusters ORDER BY score DESC LIMIT 50"
        )
    return {"clusters": [dict(r) for r in rows]}
