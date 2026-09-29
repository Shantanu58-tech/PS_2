from fastapi import APIRouter
from app.config import settings

router = APIRouter()

_collector_status: dict = {
    "replay": {"status": "idle", "last_record": None, "errors": 0},
    "x": {"status": "disabled" if not settings.x_auth_token else "idle", "last_record": None, "errors": 0},
    "telegram": {"status": "disabled" if not settings.tg_api_id else "idle", "last_record": None, "errors": 0},
    "reddit": {"status": "disabled" if not settings.reddit_client_id else "idle", "last_record": None, "errors": 0},
    "youtube": {"status": "disabled" if not settings.yt_api_key else "idle", "last_record": None, "errors": 0},
}


@router.get("/collectors")
async def get_collectors():
    return {"collectors": _collector_status}


@router.post("/collectors/{name}/targets")
async def add_target(name: str, target: str):
    return {"ok": True, "collector": name, "target": target}
