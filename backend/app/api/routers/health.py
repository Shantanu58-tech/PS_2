from fastapi import APIRouter
from app.db.session import get_db_path
import aiosqlite

router = APIRouter()


@router.get("/healthz")
async def healthz():
    try:
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute("SELECT 1")
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}