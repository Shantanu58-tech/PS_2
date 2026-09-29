import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.config import settings

router = APIRouter()


@router.get("/eval/summary")
async def eval_summary():
    path = Path(settings.eval_dir) / "summary.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"status": "not_yet_measured", "message": "Run `make eval` to generate eval/reports/summary.json"}


@router.get("/eval/reports/{name}", response_class=PlainTextResponse)
async def eval_report(name: str):
    path = Path(settings.eval_dir) / f"{Path(name).stem}.md"
    if not path.exists():
        return PlainTextResponse("not yet measured", status_code=404)
    return path.read_text(encoding="utf-8")
