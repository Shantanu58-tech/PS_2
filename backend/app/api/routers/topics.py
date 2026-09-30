from fastapi import APIRouter, HTTPException

from app.api.deps import fetch_all, fetch_one, loads

router = APIRouter()

_TOPIC_COLS = (
    "t.topic_id, t.label, t.keywords, t.first_seen, t.last_seen, t.status, t.nature, "
    "t.coordinated_share, (SELECT COUNT(*) FROM topic_assign ta WHERE ta.topic_id=t.topic_id) AS n_posts, "
    "(SELECT MAX(level) FROM bursts b WHERE b.topic_id=t.topic_id) AS max_burst_level"
)


def _topic(r: dict) -> dict:
    return {**r, "keywords": loads(r["keywords"], [])}


@router.get("/topics")
async def list_topics(limit: int = 50, sort: str = "volume"):
    from app.api.cache import cached

    return await cached(f"topics:{sort}:{limit}", lambda: _list_topics(limit, sort))


async def _list_topics(limit: int, sort: str):
    import asyncio

    from app.analytics.trends import rise_scores
    from app.config import settings

    order = {"volume": "n_posts DESC", "recent": "t.last_seen DESC",
             "coordinated": "t.coordinated_share DESC, n_posts DESC"}.get(sort, "n_posts DESC")
    rows = [_topic(r) for r in await fetch_all(f"SELECT {_TOPIC_COLS} FROM topics t ORDER BY {order}")]
    rise = await asyncio.to_thread(rise_scores, settings.db_path)
    for r in rows:
        r.update(rise.get(r["topic_id"], {"rise": None}))
    if sort == "rising":
        rows.sort(key=lambda r: r["rise"] if r["rise"] is not None else -1e9, reverse=True)
    return {"topics": rows[:limit]}


@router.get("/topics/{topic_id}")
async def get_topic(topic_id: int):
    row = await fetch_one(f"SELECT {_TOPIC_COLS} FROM topics t WHERE t.topic_id=?", (topic_id,))
    if not row:
        raise HTTPException(404, "topic not found")
    samples = await fetch_all(
        "SELECT p.platform, p.post_id, p.author_id, p.text, p.created_at, ta.prob FROM topic_assign ta "
        "JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id WHERE ta.topic_id=? "
        "ORDER BY ta.prob DESC LIMIT 8",
        (topic_id,),
    )
    platforms = await fetch_all(
        "SELECT p.platform, COUNT(*) AS n FROM topic_assign ta JOIN posts p "
        "ON p.platform=ta.platform AND p.post_id=ta.post_id WHERE ta.topic_id=? GROUP BY 1 ORDER BY 2 DESC",
        (topic_id,),
    )
    return {**_topic(row), "representative_posts": samples, "platforms": platforms}


@router.get("/topics/{topic_id}/series")
async def topic_series(topic_id: int):
    series = await fetch_all(
        "SELECT bucket_start, count_all, count_organic FROM topic_series WHERE topic_id=? ORDER BY bucket_start",
        (topic_id,),
    )
    bursts = await fetch_all("SELECT * FROM bursts WHERE topic_id=? ORDER BY start", (topic_id,))
    forecast = await fetch_all(
        "SELECT model, bucket_start, predicted, lower, upper FROM forecasts WHERE topic_id=? "
        "ORDER BY model, bucket_start",
        (topic_id,),
    )
    return {"series": series, "bursts": bursts, "forecast": forecast}


@router.get("/forecast/backtest")
async def forecast_backtest():
    from app.analytics.forecast import backtest
    from app.config import settings

    return backtest(settings.db_path)
