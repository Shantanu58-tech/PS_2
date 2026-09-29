from fastapi import APIRouter
from pydantic import BaseModel
import aiosqlite
from datetime import datetime, timezone
from app.config import settings

router = APIRouter()


class CreateCase(BaseModel):
    alert_id: int
    title: str


@router.post("/cases")
async def create_case(body: CreateCase):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute(
            "INSERT INTO cases (alert_id, title, created_at) VALUES (?,?,?)",
            (body.alert_id, body.title, now),
        )
        await db.commit()
        case_id = cursor.lastrowid
    return {"case_id": case_id, "title": body.title}


@router.get("/cases/{case_id}")
async def get_case(case_id: int):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute_fetchall(
            "SELECT * FROM cases WHERE case_id=?", (case_id,)
        )
    return dict(row[0]) if row else {"error": "not found"}
