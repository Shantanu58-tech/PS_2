import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.analytics.cases import generate_brief, generate_certificate
from app.api.deps import connect, fetch_all, fetch_one
from app.config import settings

router = APIRouter()


class CreateCase(BaseModel):
    alert_id: int
    title: str


@router.post("/cases")
async def create_case(body: CreateCase):
    if not await fetch_one("SELECT alert_id FROM alerts WHERE alert_id=?", (body.alert_id,)):
        raise HTTPException(404, "alert not found")
    now = datetime.now(timezone.utc).isoformat()
    async with connect() as db:
        cursor = await db.execute(
            "INSERT INTO cases (alert_id, title, created_at) VALUES (?,?,?)", (body.alert_id, body.title[:200], now))
        await db.execute("UPDATE alerts SET status='cased' WHERE alert_id=?", (body.alert_id,))
        await db.commit()
        case_id = cursor.lastrowid
    assert case_id is not None
    brief = await asyncio.to_thread(generate_brief, settings.db_path, case_id)
    cert = await asyncio.to_thread(generate_certificate, settings.db_path, case_id)
    return {"case_id": case_id, "title": body.title, "brief_url": f"/api/cases/{case_id}/brief",
            "certificate_url": f"/api/cases/{case_id}/certificate", "brief_path": brief, "cert_path": cert}


@router.get("/cases")
async def list_cases():
    rows = await fetch_all(
        "SELECT c.*, a.priority, a.headline, "
        "(SELECT COUNT(*) FROM certificates ce WHERE ce.case_id=c.case_id) AS n_certificates "
        "FROM cases c LEFT JOIN alerts a ON a.alert_id=c.alert_id ORDER BY c.case_id DESC")
    return {"cases": rows}


@router.get("/cases/{case_id}")
async def get_case(case_id: int):
    row = await fetch_one("SELECT * FROM cases WHERE case_id=?", (case_id,))
    if not row:
        raise HTTPException(404, "case not found")
    certs = await fetch_all("SELECT * FROM certificates WHERE case_id=? ORDER BY cert_id", (case_id,))
    return {**row, "certificates": certs, "brief_url": f"/api/cases/{case_id}/brief",
            "certificate_url": f"/api/cases/{case_id}/certificate"}


async def _serve(case_id: int, kind: str) -> HTMLResponse:
    if kind == "brief":
        row = await fetch_one("SELECT brief_path AS p FROM cases WHERE case_id=?", (case_id,))
    else:
        row = await fetch_one(
            "SELECT pdf_path AS p FROM certificates WHERE case_id=? ORDER BY cert_id DESC LIMIT 1", (case_id,))
    if not row or not row["p"] or not Path(row["p"]).exists():
        raise HTTPException(404, f"{kind} not generated")
    return HTMLResponse(Path(row["p"]).read_text(encoding="utf-8"))


@router.get("/cases/{case_id}/brief", response_class=HTMLResponse)
async def case_brief(case_id: int):
    return await _serve(case_id, "brief")


@router.get("/cases/{case_id}/certificate", response_class=HTMLResponse)
async def case_certificate(case_id: int):
    return await _serve(case_id, "certificate")


@router.post("/cases/{case_id}/regenerate")
async def regenerate(case_id: int):
    if not await fetch_one("SELECT case_id FROM cases WHERE case_id=?", (case_id,)):
        raise HTTPException(404, "case not found")
    await asyncio.to_thread(generate_brief, settings.db_path, case_id)
    await asyncio.to_thread(generate_certificate, settings.db_path, case_id)
    return {"ok": True}


@router.post("/summaries/topic/{topic_id}")
async def summarize_topic_endpoint(topic_id: int):
    from app.analytics.summarize import SummaryRejected, summarize_topic

    try:
        return await asyncio.to_thread(summarize_topic, settings.db_path, topic_id)
    except RuntimeError as exc:  # key missing
        raise HTTPException(503, str(exc)) from exc
    except SummaryRejected as exc:
        raise HTTPException(422, f"summary rejected by safety checks: {exc}") from exc


@router.get("/summaries/topic/{topic_id}")
async def get_topic_summary(topic_id: int):
    import json

    row = await fetch_one("SELECT * FROM summaries WHERE scope='topic' AND scope_id=?", (str(topic_id),))
    if not row:
        return {"topic_id": topic_id, "summary": None, "enabled": bool(settings.gemini_api_key)}
    return {"topic_id": topic_id, "model": row["model"], "created_at": row["created_at"],
            **json.loads(row["summary"]), "enabled": bool(settings.gemini_api_key)}
