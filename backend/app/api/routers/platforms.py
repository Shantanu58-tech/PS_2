"""Per-platform views (PS A) and trending keywords (PS D)."""
from __future__ import annotations

import asyncio
import re
import sqlite3
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.api.deps import ORGANIC_CLAUSE, fetch_all, fetch_one
from app.config import settings

router = APIRouter()

PLATFORMS = ["x", "telegram", "instagram", "facebook", "reddit", "youtube"]
TIER = {"x": "essential", "telegram": "essential", "instagram": "desirable", "facebook": "desirable",
        "reddit": "appreciable", "youtube": "appreciable"}
COMMENT_KINDS = ("reply", "comment")


def _connection(platform: str) -> str:
    """How the platform is wired up: connected (live session), ready (API
    credentials set), import (official data export) or demo (scenario only)."""
    s = settings
    if platform == "telegram":
        if s.tg_session_string:
            return "connected"
        return "ready" if (s.tg_api_id and s.tg_api_hash) else "demo"
    if platform == "x":
        return "ready" if (s.x_auth_token and s.x_ct0) else "demo"
    if platform == "reddit":
        return "ready" if (s.reddit_client_id and s.reddit_client_secret) else "demo"
    if platform == "youtube":
        return "ready" if s.yt_api_key else "demo"
    return "import"


@router.get("/platforms")
async def list_platforms():
    rows = {r["platform"]: r for r in await fetch_all(
        f"""
        SELECT p.platform, COUNT(*) AS posts, COUNT(DISTINCT p.author_id) AS accounts,
               SUM(CASE WHEN p.kind IN {COMMENT_KINDS} THEN 1 ELSE 0 END) AS comments,
               SUM(CASE WHEN p.kind='repost' THEN 1 ELSE 0 END) AS reposts,
               SUM(CASE WHEN {ORGANIC_CLAUSE} THEN 0 ELSE 1 END) AS coordinated,
               MIN(p.created_at) AS first_post, MAX(p.created_at) AS last_post
        FROM posts p GROUP BY p.platform
        """)}
    out = []
    for p in PLATFORMS:
        r = rows.get(p, {})
        posts = r.get("posts", 0) or 0
        out.append({
            "platform": p, "tier": TIER[p], "connection": _connection(p),
            "posts": posts, "accounts": r.get("accounts", 0) or 0,
            "comments": r.get("comments", 0) or 0, "reposts": r.get("reposts", 0) or 0,
            "coordinated_share": round((r.get("coordinated", 0) or 0) / posts, 4) if posts else 0.0,
            "first_post": r.get("first_post"), "last_post": r.get("last_post"),
        })
    return {"platforms": out}


@router.get("/platforms/{platform}")
async def platform_detail(platform: str):
    if platform not in PLATFORMS:
        raise HTTPException(404, "unknown platform")
    topics = await fetch_all(
        "SELECT t.topic_id, t.label, t.nature, COUNT(*) AS n FROM topic_assign ta "
        "JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id JOIN topics t ON t.topic_id=ta.topic_id "
        "WHERE p.platform=? GROUP BY t.topic_id ORDER BY n DESC LIMIT 6", (platform,))
    accounts = await fetch_all(
        f"SELECT p.author_id AS account_id, COUNT(*) AS posts, "
        f"SUM(CASE WHEN {ORGANIC_CLAUSE} THEN 0 ELSE 1 END) > 0 AS coordinated "
        "FROM posts p WHERE p.platform=? GROUP BY p.author_id ORDER BY posts DESC LIMIT 8", (platform,))
    for a in accounts:
        a["coordinated"] = bool(a["coordinated"])
        r = await fetch_one(
            "SELECT COUNT(*) AS n FROM posts c JOIN posts q ON q.platform=c.platform AND q.post_id=c.parent_post_id "
            "WHERE c.platform=? AND q.author_id=?", (platform, a["account_id"]))
        a["replies_received"] = r["n"] if r else 0
    emotions = await fetch_one(
        "SELECT AVG(pe.anxiety) AS anxiety, AVG(pe.excitement) AS excitement, AVG(pe.supportive) AS supportive, "
        "AVG(pe.against) AS against, AVG(pe.sarcasm) AS sarcasm, COUNT(*) AS n "
        "FROM post_emotions pe JOIN posts p ON p.platform=pe.platform AND p.post_id=pe.post_id WHERE p.platform=?",
        (platform,))
    recent = await fetch_all(
        "SELECT post_id, author_id, kind, text, created_at FROM posts WHERE platform=? "
        "ORDER BY created_at DESC LIMIT 6", (platform,))
    kinds = await fetch_all("SELECT kind, COUNT(*) AS n FROM posts WHERE platform=? GROUP BY kind ORDER BY n DESC",
                            (platform,))
    return {"platform": platform, "connection": _connection(platform), "tier": TIER[platform],
            "topics": topics, "accounts": accounts, "emotions": emotions, "recent": recent, "kinds": kinds}


_HASHTAG = re.compile(r"#[\wऀ-ॿ]+", re.UNICODE)
_cache: dict[str, object] = {}


def _trending_keywords(db_path: str, limit: int) -> dict:
    """Hashtags ranked two ways: viral spikes (peak hour vs the tag's usual
    hourly rate over the whole period) and most used overall."""
    with sqlite3.connect(db_path) as conn:
        n_posts, start, end = conn.execute("SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM posts").fetchone()
        key = f"{n_posts}:{end}:{limit}"
        if _cache.get("key") == key:
            return _cache["value"]  # type: ignore[return-value]
        if not end:
            return {"as_of": None, "viral": [], "top": []}
        total: Counter[str] = Counter()
        hourly: Counter[tuple[str, str]] = Counter()
        plats: dict[str, Counter[str]] = {}
        for text, created, platform in conn.execute("SELECT text, created_at, platform FROM posts"):
            for t in {t.lower() for t in _HASHTAG.findall(text or "")}:
                total[t] += 1
                hourly[(t, created[:13])] += 1
                plats.setdefault(t, Counter())[platform] += 1
    span_h = max(1.0, (datetime.fromisoformat(end.replace("Z", "+00:00"))
                       - datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds() / 3600)
    peak: dict[str, tuple[int, str]] = {}
    for (tag, hour), n in hourly.items():
        if n > peak.get(tag, (0, ""))[0]:
            peak[tag] = (n, hour)
    rows = []
    for tag, n in total.items():
        p, hour = peak[tag]
        usual = n / span_h
        rows.append({"keyword": tag, "posts": n, "peak_per_hour": p, "peak_at": f"{hour}:00:00Z",
                     "usual_per_hour": round(usual, 2), "spike": round(p / max(usual, 1.0), 1),
                     "platforms": [q for q, _ in plats[tag].most_common(3)]})
    viral = sorted((r for r in rows if r["peak_per_hour"] >= 10), key=lambda r: r["spike"], reverse=True)[:limit]
    top = sorted(rows, key=lambda r: r["posts"], reverse=True)[:limit]
    value = {"as_of": end, "viral": viral, "top": top}
    _cache.update(key=key, value=value)
    return value


@router.get("/keywords/trending")
async def trending_keywords(limit: int = 12):
    """Viral hashtags (biggest spike over their usual rate) and most-used hashtags."""
    return await asyncio.to_thread(_trending_keywords, settings.db_path, min(limit, 50))


@router.get("/live/telegram")
async def live_telegram_feed():
    """Real posts fetched now from the allowlisted public Telegram channels (cached)."""
    from app.collectors.live_feed import live_telegram

    return await live_telegram()
