from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.deps import connect, fetch_all
from app.collectors.health import registry
from app.config import settings
from app.pipeline import events

router = APIRouter()

CREDENTIALS = {
    "x": lambda: bool(settings.x_auth_token and settings.x_ct0),
    "telegram": lambda: bool(settings.tg_api_id and settings.tg_api_hash),
    "reddit": lambda: bool(settings.reddit_client_id and settings.reddit_client_secret),
    "youtube": lambda: bool(settings.yt_api_key),
}
TIERS = {"x": "essential", "telegram": "essential", "reddit": "appreciable", "youtube": "appreciable",
         "instagram": "desirable (CSV import)", "facebook": "desirable (CSV import)", "replay": "demo"}


@router.get("/collectors")
async def get_collectors():
    counts = {r["platform"]: r for r in await fetch_all(
        "SELECT platform, COUNT(*) AS records, MAX(collected_at) AS last_record FROM raw_records "
        "GROUP BY platform")}
    replay = events.status["replay"]
    out = {
        "replay": {"status": replay["state"], "tier": TIERS["replay"], "ingested": replay["ingested"],
                   "total": replay["total"], "last_record": replay.get("finished_at")},
    }
    for name in ("x", "telegram", "reddit", "youtube"):
        h = registry.get(name)
        has_creds = CREDENTIALS[name]()
        out[name] = {
            "status": h.state if has_creds else "credentials_missing",
            "tier": TIERS[name],
            "credentials": has_creds,
            "errors": h.errors,
            "circuit_open": h.circuit_open,
            "last_error": h.last_error,
            "records": counts.get(name, {}).get("records", 0),
            "last_record": counts.get(name, {}).get("last_record"),
        }
    for name in ("instagram", "facebook"):
        out[name] = {"status": "import_only", "tier": TIERS[name], "records": counts.get(name, {}).get("records", 0)}
    targets = await fetch_all("SELECT collector, target, added_at FROM collector_targets ORDER BY added_at")
    return {"collectors": out, "targets": targets, "mode": settings.mode}


@router.post("/collectors/{name}/targets")
async def add_target(name: str, target: str):
    if name not in CREDENTIALS:
        raise HTTPException(404, f"unknown live collector {name}")
    async with connect() as db:
        await db.execute(
            "INSERT OR IGNORE INTO collector_targets (collector, target, added_at) VALUES (?,?,?)",
            (name, target.strip(), datetime.now(timezone.utc).isoformat()))
        await db.commit()
    return {"ok": True, "collector": name, "target": target.strip()}


@router.post("/import/{platform}")
async def import_export(platform: str, file: UploadFile = File(...)):
    """Ingest an Instagram/Facebook export CSV through the ledger pipeline."""
    import asyncio

    from app.collectors.import_csv import read_csv_text
    from app.pipeline.workers import get_ingestor

    if platform not in ("instagram", "facebook"):
        raise HTTPException(400, "platform must be instagram or facebook")
    text = (await file.read()).decode("utf-8-sig", errors="replace")
    try:
        records = read_csv_text(text, platform, file.filename or "upload")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    n = await asyncio.to_thread(get_ingestor().ingest_many, records)
    return {"ok": True, "platform": platform, "ingested": n}
