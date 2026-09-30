from fastapi import APIRouter, Query

from app.api.deps import ORGANIC_CLAUSE, fetch_all

router = APIRouter()

# SQLite strftime patterns per bucket size (timestamps are UTC; the UI shows IST).
BUCKETS = {"1h": "%Y-%m-%dT%H:00:00Z", "1d": "%Y-%m-%dT00:00:00Z"}


@router.get("/timeline/emotions")
async def emotions_timeline(
    bucket: str = Query("1h", pattern="^(1h|1d)$"),
    topic_id: int | None = None,
    organic_only: bool = False,
    platform: str | None = None,
    kind: str = Query("all", pattern="^(all|posts|comments)$"),
):
    """kind: all, posts (original posts and reposts) or comments (replies and comment threads)."""
    clauses: list[str] = []
    params: list[object] = []
    if platform:
        clauses.append("p.platform=?")
        params.append(platform)
    if kind == "comments":
        clauses.append("p.kind IN ('reply', 'comment')")
    elif kind == "posts":
        clauses.append("p.kind NOT IN ('reply', 'comment')")
    if organic_only:
        clauses.append(ORGANIC_CLAUSE)
    if topic_id is not None:
        clauses.append("EXISTS (SELECT 1 FROM topic_assign ta WHERE ta.platform=p.platform "
                       "AND ta.post_id=p.post_id AND ta.topic_id=?)")
        params.append(topic_id)
    where = ("AND " + " AND ".join(clauses)) if clauses else ""
    rows = await fetch_all(
        f"""
        SELECT strftime('{BUCKETS[bucket]}', p.created_at) AS bucket,
               AVG(pe.anxiety) AS anxiety, AVG(pe.excitement) AS excitement,
               AVG(pe.supportive) AS supportive, AVG(pe.against) AS against,
               AVG(pe.sarcasm) AS sarcasm, COUNT(*) AS n
        FROM post_emotions pe
        JOIN posts p ON p.platform=pe.platform AND p.post_id=pe.post_id
        WHERE 1=1 {where}
        GROUP BY 1 ORDER BY 1
        """,
        params,
    )
    return {"buckets": rows, "bucket": bucket, "organic_only": organic_only}


@router.get("/timeline/volume")
async def volume_timeline(bucket: str = Query("1h", pattern="^(1h|1d)$"), platform: str | None = None):
    params = [platform] if platform else []
    rows = await fetch_all(
        f"""
        SELECT strftime('{BUCKETS[bucket]}', p.created_at) AS bucket, p.platform, COUNT(*) AS n,
               SUM(CASE WHEN {ORGANIC_CLAUSE} THEN 0 ELSE 1 END) AS coordinated
        FROM posts p {"WHERE p.platform=?" if platform else ""}
        GROUP BY 1, 2 ORDER BY 1
        """,
        params,
    )
    return {"buckets": rows}


@router.get("/timeline/compare")
async def raw_vs_organic(
    topic_id: int | None = None,
    platform: str | None = None,
    kind: str = Query("all", pattern="^(all|posts|comments)$"),
):
    """Mean affect with and without coordinated accounts - the 'distortion'."""
    topic_clause = ("AND EXISTS (SELECT 1 FROM topic_assign ta WHERE ta.platform=p.platform "
                    "AND ta.post_id=p.post_id AND ta.topic_id=?)") if topic_id is not None else ""
    params: list[object] = [topic_id] if topic_id is not None else []
    if platform:
        topic_clause += " AND p.platform=?"
        params.append(platform)
    if kind == "comments":
        topic_clause += " AND p.kind IN ('reply', 'comment')"
    elif kind == "posts":
        topic_clause += " AND p.kind NOT IN ('reply', 'comment')"
    out = {}
    for label, extra in (("raw", ""), ("organic", f"AND {ORGANIC_CLAUSE}")):
        row = await fetch_all(
            f"""
            SELECT AVG(pe.anxiety) AS anxiety, AVG(pe.excitement) AS excitement,
                   AVG(pe.supportive) AS supportive, AVG(pe.against) AS against,
                   AVG(pe.sarcasm) AS sarcasm, COUNT(*) AS n
            FROM post_emotions pe JOIN posts p ON p.platform=pe.platform AND p.post_id=pe.post_id
            WHERE 1=1 {topic_clause} {extra}
            """,
            params,
        )
        out[label] = row[0] if row else {}
    return out
