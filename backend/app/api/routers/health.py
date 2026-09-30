from fastapi import APIRouter
import aiosqlite

from app.config import settings
from app.db.session import get_db_path
from app.pipeline import events
from app.version import VERSION

router = APIRouter()


@router.get("/healthz")
async def healthz():
    base = {"service": "deepastambha", "version": VERSION, "mode": settings.mode,
            "demo_readonly": settings.demo_readonly}
    try:
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute("SELECT 1")
        return {"status": "ok", "db": "connected", **base, "pipeline": events.status}
    except Exception as e:
        return {"status": "degraded", "error": str(e), **base}
