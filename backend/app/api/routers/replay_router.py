import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.api.deps import fetch_one
from app.config import settings
from app.pipeline import events

router = APIRouter()


class ReplayStart(BaseModel):
    speed: int = 60
    scenario: str | None = None
    force: bool = False


@router.post("/replay/start")
async def start_replay(body: ReplayStart, bg: BackgroundTasks):
    from app.collectors.replay import start_replay_bg

    if events.status["replay"]["state"] == "running":
        raise HTTPException(409, "replay already running")
    existing = await fetch_one("SELECT COUNT(*) AS n FROM raw_records WHERE collector_id='replay'")
    if existing and existing["n"] and not body.force:
        # The ledger is append-only: replaying again would record every item twice.
        raise HTTPException(409, "scenario already ingested; POST /api/pipeline/run to recompute analytics, "
                                 "or pass force=true to append a second collection run")
    scenario = body.scenario or settings.scenario_path
    bg.add_task(start_replay_bg, scenario, body.speed)
    return {"ok": True, "scenario": scenario, "speed": body.speed}


@router.get("/pipeline/status")
async def pipeline_status():
    return events.status


@router.post("/pipeline/run")
async def run_pipeline(bg: BackgroundTasks):
    from app.pipeline.analytics import run_all_analytics

    if events.status["analytics"]["state"] == "running":
        raise HTTPException(409, "analytics already running")

    async def task() -> None:
        try:
            await asyncio.to_thread(run_all_analytics, settings.db_path)
        except Exception:
            pass  # state/error already published by run_all_analytics

    bg.add_task(task)
    return {"ok": True}
