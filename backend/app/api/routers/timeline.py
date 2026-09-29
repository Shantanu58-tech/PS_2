from fastapi import APIRouter
import aiosqlite
from app.config import settings

router = APIRouter()


@router.get("/timeline/emotions")
async def emotions_timeline(
    bucket: str = "1h",
    topic_id: int | None = None,
    organic_only: bool = False,
    platform: str | None = None,
):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        clauses = []
        params = []
        if platform:
            clauses.append("p.platform=?")
            params.append(platform)
        if organic_only:
            clauses.append(
                "NOT EXISTS (SELECT 1 FROM coord_accounts ca WHERE ca.platform=p.platform "
                "AND ca.account_id=p.author_id AND ca.score>=0.7)"
            )
        where = ("AND " + " AND ".join(clauses)) if clauses else ""
        rows = await db.execute_fetchall(
            f"""
            SELECT strftime('%Y-%m-%dT%H:00:00Z', pe.rowid) as bucket,
                   AVG(pe.anxiety) as anxiety, AVG(pe.excitement) as excitement,
                   AVG(pe.supportive) as supportive, AVG(pe.against) as against,
                   AVG(pe.sarcasm) as sarcasm, COUNT(*) as n
            FROM post_emotions pe
            JOIN posts p ON p.platform=pe.platform AND p.post_id=pe.post_id
            WHERE 1=1 {where}
            GROUP BY 1 ORDER BY 1
            """,
            params,
        )
    return {"buckets": [dict(r) for r in rows]}
