from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter()


@router.get("/eval/summary")
async def eval_summary():
    path = Path("eval/reports/summary.json")
    if path.exists():
        return json.loads(path.read_text())
    return {"status": "not_yet_measured", "message": "Run make eval to generate"}
