"""National situation room (first page) and analyst review of signals."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.analytics.situation import situation
from app.api.deps import connect, fetch_one
from app.config import settings

router = APIRouter()


@router.get("/situation")
async def get_situation():
    """Sectors, states (k-anonymous), pushed narratives, hot topics and KPIs in one payload."""
    return await asyncio.to_thread(situation, settings.db_path)


class Review(BaseModel):
    action: Literal["approve", "watchlist", "dismiss"]
    note: str | None = None


@router.post("/alerts/{alert_id}/review")
async def review_alert(alert_id: int, body: Review):
    """Analyst review of a signal: approve (opens a case), keep on the watchlist, or dismiss.
    Every decision is written to the audit trail, which is itself in the hash chain."""
    from app.ledger.audit import log_action

    alert = await fetch_one("SELECT a.alert_id, a.headline, t.label FROM alerts a LEFT JOIN topics t "
                            "ON t.topic_id=a.topic_id WHERE a.alert_id=?", (alert_id,))
    if not alert:
        raise HTTPException(404, "alert not found")
    status = {"approve": "approved", "watchlist": "watchlist", "dismiss": "dismissed"}[body.action]
    async with connect() as db:
        await db.execute("UPDATE alerts SET status=? WHERE alert_id=?", (status, alert_id))
        await db.commit()
    seq = await asyncio.to_thread(log_action, settings.db_path, "analyst", f"signal_{status}",
                                  {"alert_id": alert_id, "note": (body.note or "")[:200],
                                   "at": datetime.now(timezone.utc).isoformat()})
    out = {"ok": True, "alert_id": alert_id, "status": status, "ledger_seq": seq}
    if body.action == "approve":
        from app.api.routers.cases import CreateCase, create_case

        out["case"] = await create_case(CreateCase(alert_id=alert_id, title=(alert["label"] or alert["headline"])[:80]))
    return out
