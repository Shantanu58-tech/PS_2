from fastapi import APIRouter, HTTPException

from app.api.deps import connect, fetch_all, loads

router = APIRouter()


def _alert(r: dict) -> dict:
    return {**r, "evidence": loads(r.get("evidence_json"), {})}


@router.get("/alerts")
async def list_alerts(status: str | None = None, limit: int = 50):
    if status:
        rows = await fetch_all(
            "SELECT a.*, t.label AS topic_label, t.nature FROM alerts a LEFT JOIN topics t ON t.topic_id=a.topic_id "
            "WHERE a.status=? ORDER BY a.priority DESC LIMIT ?", (status, limit))
    else:
        rows = await fetch_all(
            "SELECT a.*, t.label AS topic_label, t.nature FROM alerts a LEFT JOIN topics t ON t.topic_id=a.topic_id "
            "ORDER BY a.priority DESC LIMIT ?", (limit,))
    return {"alerts": [_alert(r) for r in rows]}


@router.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: int):
    async with connect() as db:
        cur = await db.execute("UPDATE alerts SET status='acked' WHERE alert_id=?", (alert_id,))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "alert not found")
    return {"ok": True}
