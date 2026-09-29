from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.config import settings

router = APIRouter()


class ReplayStart(BaseModel):
    speed: int = 60
    scenario: str = "replay/scenario_v1.jsonl"


@router.post("/replay/start")
async def start_replay(body: ReplayStart, bg: BackgroundTasks):
    from app.collectors.replay import start_replay_bg
    bg.add_task(start_replay_bg, body.scenario, body.speed)
    return {"ok": True, "scenario": body.scenario, "speed": body.speed}
