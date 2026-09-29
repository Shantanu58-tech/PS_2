from fastapi import APIRouter
import aiosqlite
from app.config import settings

router = APIRouter()


@router.get("/alerts")
async def list_alerts(status: str | None = None, limit: int = 50):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        if status:
            rows = await db.execute_fetchall(
                "SELECT * FROM alerts WHERE status=? ORDER BY priority DESC LIMIT ?",
                (status, limit),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT * FROM alerts ORDER BY priority DESC LIMIT ?", (limit,)
            )
    return {"alerts": [dict(r) for r in rows]}


@router.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: int):
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            "UPDATE alerts SET status='acked' WHERE alert_id=?", (alert_id,)
        )
        await db.commit()
    return {"ok": True}
