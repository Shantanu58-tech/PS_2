from fastapi import APIRouter
import aiosqlite

from app.config import settings
from app.db.repo import get_posts

router = APIRouter()


@router.get("/posts")
async def list_posts(
    platform: str | None = None,
    from_ts: str | None = None,
    to_ts: str | None = None,
    topic_id: int | None = None,
    q: str | None = None,
    organic_only: bool = False,
    limit: int = 100,
    cursor: str | None = None,
):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await get_posts(db, platform, from_ts, to_ts, topic_id, q, organic_only, min(limit, 500), cursor)
    return {"posts": rows, "count": len(rows), "next_cursor": rows[-1]["created_at"] if rows else None}


@router.get("/thread/{platform}/{post_id}")
async def thread(platform: str, post_id: str):
    """Reply/comment tree rooted at a post; replies whose parent was never
    collected are reported as orphans rather than silently dropped."""
    from app.api.deps import fetch_all, fetch_one

    root = await fetch_one("SELECT * FROM posts WHERE platform=? AND post_id=?", (platform, post_id))
    if not root:
        from fastapi import HTTPException

        raise HTTPException(404, "post not found")
    nodes = [root]
    frontier = [post_id]
    while frontier and len(nodes) < 2000:
        q = ",".join("?" * len(frontier))
        children = await fetch_all(
            f"SELECT * FROM posts WHERE parent_post_id IN ({q}) OR origin_post_id IN ({q}) ORDER BY created_at",
            frontier + frontier)
        children = [c for c in children if c["post_id"] not in {n["post_id"] for n in nodes}]
        nodes += children
        frontier = [c["post_id"] for c in children]
    orphans = await fetch_all(
        "SELECT COUNT(*) AS n FROM posts p WHERE p.parent_post_id IS NOT NULL AND NOT EXISTS "
        "(SELECT 1 FROM posts q WHERE q.post_id=p.parent_post_id)")
    return {"root": root, "posts": nodes, "count": len(nodes), "orphan_replies_global": orphans[0]["n"]}
