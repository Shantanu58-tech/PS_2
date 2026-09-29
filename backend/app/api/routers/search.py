from fastapi import APIRouter

from app.api.deps import fetch_all, fts_query

router = APIRouter()


@router.get("/search")
async def search(q: str, limit: int = 20, platform: str | None = None):
    clause = "AND p.platform=?" if platform else ""
    params = [fts_query(q)] + ([platform] if platform else []) + [min(limit, 200)]
    rows = await fetch_all(
        f"SELECT p.platform, p.post_id, p.author_id, p.text, p.created_at, p.lang, p.ledger_seq, "
        f"bm25(posts_fts) AS rank FROM posts_fts JOIN posts p ON p.rowid=posts_fts.rowid "
        f"WHERE posts_fts MATCH ? {clause} ORDER BY rank LIMIT ?",
        params,
    )
    return {"results": rows, "query": q}
