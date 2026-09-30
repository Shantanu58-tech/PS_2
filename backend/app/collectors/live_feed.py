"""Live Telegram feed: real posts fetched now from a fixed allowlist of public
news channels, scored with the lexicon emotion model and the sector rules.

Read-only and safe for the public demo: channels come only from settings
(LIVE_TG_CHANNELS), results are cached (one fetch per TTL no matter how many
visitors), and nothing is written to the database. The analysed scenario keeps
its own timeline; the live feed shows that the collector works against the
real platform right now.
"""
from __future__ import annotations

import asyncio
import re
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.config import settings

TTL_OK = 600      # seconds a successful fetch is reused
TTL_ERROR = 120   # seconds a failure is reused (avoid hammering Telegram)
PER_CHANNEL = 12
_lock = asyncio.Lock()
_cache: dict[str, Any] = {"at": 0.0, "value": None, "ttl": 0}

_HASHTAG = re.compile(r"#[\wऀ-ॿ]+", re.UNICODE)
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]{3,}")
_STOP = set("""this that with from have will been were their about after over into more than they them what when
where which while would could should there these those your just also only here said says like being other amid
news read full story latest today year years first make made gets take takes know does such very much many most
some into onto upon under still ever even back well week month time times video watch click link subscribe""".split())


def _strict_sector(text: str) -> str:
    """Sector only on strong evidence (two or more keyword hits); news copy is broad."""
    from app.analytics.situation import SECTORS

    t = " " + re.sub(r"\s+", " ", text.lower()) + " "
    scores = {s["id"]: sum(t.count(k) for k in s["keywords"]) for s in SECTORS}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] >= 2 else "other"


def channels() -> list[str]:
    return [c.strip().lstrip("@") for c in settings.live_tg_channels.split(",") if c.strip()]


def _summarise(posts: list[dict[str, Any]]) -> dict[str, Any]:
    words: Counter[str] = Counter()
    tags: Counter[str] = Counter()
    sectors: Counter[str] = Counter()
    for p in posts:
        tags.update(t.lower() for t in p["hashtags"])
        words.update(w.lower() for w in _WORD.findall(p["text"]) if w.lower() not in _STOP)
        sectors[p["sector"]] += 1
    anx = [p["emotions"]["anxiety"] for p in posts]
    return {
        "posts": len(posts),
        "anxiety": round(sum(anx) / len(anx), 3) if anx else None,
        "top_terms": [w for w, _ in (tags.most_common(8) or words.most_common(8))][:8] if tags else
                     [w for w, _ in words.most_common(8)],
        "sectors": [{"sector": s, "posts": n} for s, n in sectors.most_common()],
    }


async def _fetch() -> dict[str, Any]:
    from app.analytics.situation import SECTOR_NAME
    from app.collectors.telegram_telethon import TelegramCollector
    from app.nlp.emotion import lexicon_scores

    client = TelegramCollector()._client()
    await asyncio.wait_for(client.connect(), 20)
    try:
        if not await client.is_user_authorized():
            return {"connected": False, "reason": "Telegram session is not authorised."}
        posts: list[dict[str, Any]] = []
        chans: list[dict[str, Any]] = []
        for username in channels():
            try:
                entity = await asyncio.wait_for(client.get_entity(username), 15)
                msgs = await asyncio.wait_for(client.get_messages(entity, limit=PER_CHANNEL), 20)
            except Exception as exc:  # one bad channel must not sink the feed
                chans.append({"username": username, "title": username, "error": type(exc).__name__, "posts": 0})
                continue
            title = getattr(entity, "title", username)
            kept = 0
            for m in msgs:
                # drop raw links and "via <Paper>" trailers; the post link is shown separately
                text = re.sub(r"https?://\S+", "", m.message or "")
                text = re.sub(r"\s+(via\s+(The\s+)?[A-Z][\w]*(\s[A-Z][\w]*){0,3}|Read more.*|Catch the complete story.*)\s*$", "", text)
                text = re.sub(r"\s*🔗\s*", " ", text).strip()
                if not text:
                    continue
                kept += 1
                sector = _strict_sector(text)
                posts.append({
                    "channel": username, "channel_title": title, "id": m.id,
                    "date": m.date.astimezone(timezone.utc).isoformat() if m.date else None,
                    "text": text[:600], "views": getattr(m, "views", None), "forwards": getattr(m, "forwards", None),
                    "has_media": bool(getattr(m, "media", None)), "link": f"https://t.me/{username}/{m.id}",
                    "hashtags": _HASHTAG.findall(text)[:6],
                    "emotions": {k: round(v, 3) for k, v in lexicon_scores(text).items()},
                    "sector": sector, "sector_name": SECTOR_NAME.get(sector, sector),
                })
            chans.append({"username": username, "title": title, "posts": kept,
                          "latest": max((p["date"] for p in posts if p["channel"] == username), default=None)})
        posts.sort(key=lambda p: p["date"] or "", reverse=True)
        return {"connected": True, "channels": chans, "posts": posts, "summary": _summarise(posts),
                "scoring": "lexicon-v1 (live)", "fetched_at": datetime.now(timezone.utc).isoformat()}
    finally:
        await client.disconnect()


async def live_telegram() -> dict[str, Any]:
    if not (settings.tg_api_id and settings.tg_api_hash and settings.tg_session_string):
        return {"connected": False, "reason": "No Telegram session configured.", "posts": [], "channels": []}
    async with _lock:
        if _cache["value"] is not None and time.monotonic() - _cache["at"] < _cache["ttl"]:
            return {**_cache["value"], "cached": True}
        try:
            value = await asyncio.wait_for(_fetch(), 60)
            ttl = TTL_OK if value.get("connected") else TTL_ERROR
        except Exception as exc:
            value = {"connected": False, "reason": f"Telegram fetch failed: {type(exc).__name__}", "posts": [], "channels": []}
            ttl = TTL_ERROR
        _cache.update(at=time.monotonic(), value=value, ttl=ttl)
        return {**value, "cached": False}
