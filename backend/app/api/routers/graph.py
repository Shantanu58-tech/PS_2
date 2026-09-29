from fastapi import APIRouter
import aiosqlite
from app.config import settings

router = APIRouter()


@router.get("/graph")
async def get_graph(organic_only: bool = False, limit: int = 500):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        edges = await db.execute_fetchall(
            "SELECT * FROM edges ORDER BY ts DESC LIMIT ?", (limit,)
        )
    return {"edges": [dict(e) for e in edges]}


@router.get("/graph/spread")
async def get_spread():
    return {"frames": []}


@router.get("/influencers")
async def get_influencers(limit: int = 20):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT src_account, COUNT(*) as edge_count FROM edges GROUP BY src_account ORDER BY edge_count DESC LIMIT ?",
            (limit,),
        )
    return {"influencers": [dict(r) for r in rows]}
