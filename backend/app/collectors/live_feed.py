"""Live feeds: real posts fetched now from a fixed allowlist of public sources on
each platform, scored with the lexicon emotion model and the sector rules.

| platform | source                                   | how                                          |
|----------|------------------------------------------|----------------------------------------------|
| telegram | public news channels                     | Telethon, the connected session              |
| x        | public accounts (PIB, fact-check, news)  | twscrape with burner-account cookies         |
| youtube  | news channels: videos + viewer comments  | channel RSS (free) + Data API commentThreads |
| reddit   | public subreddits                        | the subreddit's official RSS feed            |

Read-only and safe for the public demo: sources come only from settings
(LIVE_*), results are cached per platform (one fetch per TTL no matter how many
visitors), and nothing is written to the database. The analysed scenario keeps
its own timeline; the live feeds show the collectors working against the real
platforms right now. Instagram and Facebook have no public feed or free API for
other people's pages, so they stay on the official-export path.
"""
from __future__ import annotations

import asyncio
import html
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from app.config import settings

TTL_OK = 600      # seconds a successful fetch is reused
TTL_ERROR = 120   # seconds a failure is reused (avoid hammering a platform)
PER_SOURCE = 12
LIVE_PLATFORMS = ("telegram", "x", "youtube", "reddit")
UA = "Mozilla/5.0 (compatible; Deepastambha/1.0; +https://deepastambha.onrender.com)"

_locks: dict[str, asyncio.Lock] = {}
_cache: dict[str, dict[str, Any]] = {}

_HASHTAG = re.compile(r"#[\wऀ-ॿ]+", re.UNICODE)
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]{3,}")
_TAG = re.compile(r"<[^>]+>")
_STOP = set("""this that with from have will been were their about after over into more than they them what when
where which while would could should there these those your just also only here said says like being other amid
news read full story latest today year years first make made gets take takes know does such very much many most
some into onto upon under still ever even back well week month time times video watch click link subscribe""".split())


def _split(value: str) -> list[str]:
    return [c.strip().lstrip("@") for c in value.split(",") if c.strip()]


def channels() -> list[str]:
    return _split(settings.live_tg_channels)


def _strict_sector(text: str) -> str:
    """Sector only on strong evidence (two or more keyword hits); news copy is broad."""
    from app.analytics.situation import SECTORS

    t = " " + re.sub(r"\s+", " ", text.lower()) + " "
    scores = {s["id"]: sum(t.count(k) for k in s["keywords"]) for s in SECTORS}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] >= 2 else "other"


def clean_text(text: str) -> str:
    """Drop raw links, HTML and "via <Paper>" / "Read more" trailers; the post link is shown separately."""
    text = html.unescape(_TAG.sub(" ", text or ""))
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+(via\s+(The\s+)?[A-Z][\w]*(\s[A-Z][\w]*){0,3}|Read more.*|Catch the complete story.*)\s*$", "", text)
    text = re.sub(r"\s*🔗\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _post(platform: str, source: str, source_title: str, pid: str, date: datetime | str | None, text: str,
          link: str, kind: str = "post", **metrics: Any) -> dict[str, Any] | None:
    from app.analytics.situation import SECTOR_NAME
    from app.nlp.emotion import lexicon_scores

    text = clean_text(text)
    if not text:
        return None
    if isinstance(date, datetime):
        date = (date if date.tzinfo else date.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).isoformat()
    sector = _strict_sector(text)
    return {
        "platform": platform, "source": source, "source_title": source_title, "id": str(pid), "kind": kind,
        "date": date, "text": text[:600], "link": link, "hashtags": _HASHTAG.findall(text)[:6],
        "metrics": {k: v for k, v in metrics.items() if v is not None},
        "emotions": {k: round(v, 3) for k, v in lexicon_scores(text).items()},
        "sector": sector, "sector_name": SECTOR_NAME.get(sector, sector),
        # Telegram-era field names kept for older clients
        "channel": source, "channel_title": source_title,
        "views": metrics.get("views"), "forwards": metrics.get("forwards"),
    }


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
        "top_terms": [w for w, _ in (tags.most_common(8) or words.most_common(8))][:8],
        "sectors": [{"sector": s, "posts": n} for s, n in sectors.most_common()],
    }


def _source_row(source: str, title: str, posts: list[dict[str, Any]], error: str | None = None) -> dict[str, Any]:
    mine = [p for p in posts if p["source"] == source]
    row = {"username": source, "title": title, "posts": len(mine),
           "latest": max((p["date"] for p in mine if p["date"]), default=None)}
    if error:
        row["error"] = error
    return row


# ---------------------------------------------------------------- Telegram
async def _fetch_telegram() -> dict[str, Any]:
    from app.collectors.telegram_telethon import TelegramCollector

    if not (settings.tg_api_id and settings.tg_api_hash and settings.tg_session_string):
        return {"connected": False, "reason": "No Telegram session configured."}
    client = TelegramCollector()._client()
    await asyncio.wait_for(client.connect(), 20)
    try:
        if not await client.is_user_authorized():
            return {"connected": False, "reason": "Telegram session is not authorised."}
        posts: list[dict[str, Any]] = []
        srcs: list[dict[str, Any]] = []
        for username in channels():
            try:
                entity = await asyncio.wait_for(client.get_entity(username), 15)
                msgs = await asyncio.wait_for(client.get_messages(entity, limit=PER_SOURCE), 20)
            except Exception as exc:  # one bad channel must not sink the feed
                srcs.append(_source_row(username, username, [], type(exc).__name__))
                continue
            title = getattr(entity, "title", username)
            for m in msgs:
                p = _post("telegram", username, title, m.id, m.date, m.message or "", f"https://t.me/{username}/{m.id}",
                          views=getattr(m, "views", None), forwards=getattr(m, "forwards", None),
                          has_media=bool(getattr(m, "media", None)) or None)
                if p:
                    posts.append(p)
            srcs.append(_source_row(username, title, posts))
        return {"connected": True, "channels": srcs, "posts": posts}
    finally:
        await client.disconnect()


# ---------------------------------------------------------------- X
async def _fetch_x() -> dict[str, Any]:
    from twscrape import gather

    from app.collectors.x_twscrape import XCollector

    if not (settings.x_auth_token and settings.x_ct0):
        return {"connected": False, "reason": "No X session configured."}
    api = await XCollector()._get_api()
    posts: list[dict[str, Any]] = []
    srcs: list[dict[str, Any]] = []
    for handle in _split(settings.live_x_accounts):
        try:
            user = await asyncio.wait_for(api.user_by_login(handle), 25)
            if user is None:
                raise LookupError("account not found")
            tweets = await asyncio.wait_for(gather(api.user_tweets(user.id, limit=PER_SOURCE)), 40)
        except Exception as exc:
            srcs.append(_source_row(handle, handle, [], type(exc).__name__))
            continue
        title = getattr(user, "displayname", None) or handle
        for t in tweets[:PER_SOURCE]:
            if getattr(t, "retweetedTweet", None) is not None:
                continue  # a repost carries someone else's text; keep the account's own voice
            p = _post("x", handle, title, t.id, t.date, t.rawContent, f"https://x.com/{handle}/status/{t.id}",
                      views=getattr(t, "viewCount", None), likes=t.likeCount, reposts=t.retweetCount,
                      replies=t.replyCount)
            if p:
                posts.append(p)
        srcs.append(_source_row(handle, title, posts))
    if not posts and srcs and all(s.get("error") for s in srcs):
        return {"connected": False, "reason": f"X fetch failed ({srcs[0]['error']}).", "channels": srcs}
    return {"connected": True, "channels": srcs, "posts": posts}


# ---------------------------------------------------------------- YouTube
_ATOM = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
         "media": "http://search.yahoo.com/mrss/"}


def _get(url: str, **params: Any) -> Any:
    import requests

    r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=20)
    r.raise_for_status()
    return r


def _youtube_sync() -> dict[str, Any]:
    posts: list[dict[str, Any]] = []
    srcs: list[dict[str, Any]] = []
    for cid in _split(settings.live_yt_channels):
        try:
            root = ET.fromstring(_get("https://www.youtube.com/feeds/videos.xml", channel_id=cid).content)
        except Exception as exc:
            srcs.append(_source_row(cid, cid, [], type(exc).__name__))
            continue
        title = root.findtext("a:title", cid, _ATOM)
        videos = root.findall("a:entry", _ATOM)[:6]
        for i, e in enumerate(videos):
            vid = e.findtext("yt:videoId", "", _ATOM)
            desc = e.findtext("media:group/media:description", "", _ATOM) or ""
            views = e.find("media:group/media:community/media:statistics", _ATOM)
            p = _post("youtube", cid, title, vid, e.findtext("a:published", None, _ATOM),
                      (e.findtext("a:title", "", _ATOM) + ". " + desc.split("\n")[0]).strip(". "),
                      f"https://www.youtube.com/watch?v={vid}", kind="video",
                      views=int(views.get("views")) if views is not None and views.get("views") else None)
            if p:
                posts.append(p)
            # what viewers say under the two newest videos (Data API, 1 quota unit per call)
            if settings.yt_api_key and i < 2 and vid:
                try:
                    items = _get("https://www.googleapis.com/youtube/v3/commentThreads", part="snippet", videoId=vid,
                                 maxResults=8, order="time", textFormat="plainText", key=settings.yt_api_key).json()
                except Exception:
                    items = {}
                for it in items.get("items", []):
                    s = it["snippet"]["topLevelComment"]["snippet"]
                    c = _post("youtube", cid, title, it["id"], s.get("publishedAt"), s.get("textDisplay", ""),
                              f"https://www.youtube.com/watch?v={vid}&lc={it['id']}", kind="comment",
                              likes=s.get("likeCount"), replies=it["snippet"].get("totalReplyCount"))
                    if c:
                        c["on"] = p["text"][:120] if p else None
                        posts.append(c)
        srcs.append(_source_row(cid, title, posts))
    ok = any(not s.get("error") for s in srcs)
    return {"connected": ok, "channels": srcs, "posts": posts,
            **({} if ok else {"reason": "YouTube feeds could not be reached."})}


async def _fetch_youtube() -> dict[str, Any]:
    return await asyncio.to_thread(_youtube_sync)


# ---------------------------------------------------------------- Reddit
def _reddit_oauth(subs: list[str]) -> list[dict[str, Any]]:
    """Reddit's official API with an app-only token (a free "script" app). Needed on cloud servers:
    Reddit refuses anonymous requests from data-centre addresses."""
    import requests

    tok = requests.post("https://www.reddit.com/api/v1/access_token", data={"grant_type": "client_credentials"},
                        auth=(settings.reddit_client_id, settings.reddit_client_secret),
                        headers={"User-Agent": settings.reddit_user_agent or UA}, timeout=20)
    tok.raise_for_status()
    r = requests.get(f"https://oauth.reddit.com/r/{'+'.join(subs)}/new", params={"limit": 40, "raw_json": 1},
                     headers={"User-Agent": settings.reddit_user_agent or UA,
                              "Authorization": f"Bearer {tok.json()['access_token']}"}, timeout=20)
    r.raise_for_status()
    posts = []
    for c in r.json()["data"]["children"]:
        d = c["data"]
        p = _post("reddit", d["subreddit"], f"r/{d['subreddit']}", d["name"],
                  datetime.fromtimestamp(d["created_utc"], timezone.utc),
                  d["title"] + (". " + d["selftext"] if d.get("selftext") else ""),
                  "https://www.reddit.com" + d["permalink"], author=f"u/{d['author']}",
                  likes=d.get("score"), replies=d.get("num_comments"))
        if p:
            posts.append(p)
    return posts


def _reddit_sync() -> dict[str, Any]:
    subs = _split(settings.live_reddit_subs)
    if settings.reddit_client_id and settings.reddit_client_secret:
        posts = _reddit_oauth(subs)
        srcs = [_source_row(s, f"r/{s}", posts) for s in subs]
        for s in srcs:
            s["posts"] = sum(1 for p in posts if p["source"].lower() == s["username"].lower())
        return {"connected": True, "channels": srcs, "posts": posts}
    # no app key: the public RSS feed, one combined request per refresh (Reddit rate-limits
    # anonymous requests, so a refusal is reported and retried after TTL_ERROR)
    try:
        resp = _get(f"https://www.reddit.com/r/{'+'.join(subs)}/new/.rss", limit=40)
    except Exception as exc:
        code = getattr(getattr(exc, "response", None), "status_code", None)
        return {"connected": False, "channels": [],
                "reason": f"Reddit refused the public feed just now (HTTP {code}); it retries in two minutes. "
                          "A Reddit app key (REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET) makes it reliable."}
    root = ET.fromstring(resp.content)
    posts: list[dict[str, Any]] = []
    for e in root.findall("a:entry", _ATOM):
        sub = (e.find("a:category", _ATOM).get("term") if e.find("a:category", _ATOM) is not None else "") or ""
        body = e.findtext("a:content", "", _ATOM) or ""
        body = re.sub(r"submitted by .*$", "", html.unescape(_TAG.sub(" ", html.unescape(body))), flags=re.S)
        text = e.findtext("a:title", "", _ATOM) + (". " + body.strip() if body.strip() else "")
        link = (e.find("a:link", _ATOM).get("href") if e.find("a:link", _ATOM) is not None else "") or ""
        p = _post("reddit", sub or subs[0], f"r/{sub}" if sub else "Reddit", e.findtext("a:id", "", _ATOM),
                  e.findtext("a:updated", None, _ATOM), text, link,
                  author=(e.findtext("a:author/a:name", "", _ATOM) or "").lstrip("/"))
        if p:
            posts.append(p)
    srcs = [_source_row(s, f"r/{s}", posts) for s in subs]
    for s in srcs:  # Reddit returns the subreddit's canonical case
        s["posts"] = sum(1 for p in posts if p["source"].lower() == s["username"].lower())
    return {"connected": True, "channels": srcs, "posts": posts}


async def _fetch_reddit() -> dict[str, Any]:
    return await asyncio.to_thread(_reddit_sync)


FETCHERS: dict[str, Callable[[], Awaitable[dict[str, Any]]]] = {
    "telegram": _fetch_telegram, "x": _fetch_x, "youtube": _fetch_youtube, "reddit": _fetch_reddit,
}


async def live(platform: str) -> dict[str, Any]:
    """Cached live feed for one platform; never raises."""
    if platform not in FETCHERS:
        return {"platform": platform, "connected": False, "reason": "No live feed for this platform.",
                "posts": [], "channels": []}
    lock = _locks.setdefault(platform, asyncio.Lock())
    async with lock:
        c = _cache.get(platform)
        if c and time.monotonic() - c["at"] < c["ttl"]:
            return {**c["value"], "cached": True}
        try:
            value = await asyncio.wait_for(FETCHERS[platform](), 90)
        except Exception as exc:
            value = {"connected": False, "reason": f"{platform} fetch failed: {type(exc).__name__}"}
        posts = sorted(value.get("posts", []), key=lambda p: p["date"] or "", reverse=True)
        value = {"platform": platform, "channels": [], **value, "posts": posts,
                 "summary": _summarise(posts), "scoring": "lexicon-v1 (live)",
                 "fetched_at": datetime.now(timezone.utc).isoformat()}
        ttl = TTL_OK if value.get("connected") and posts else TTL_ERROR
        _cache[platform] = {"at": time.monotonic(), "value": value, "ttl": ttl}
        return {**value, "cached": False}


async def live_all() -> dict[str, Any]:
    """Every live platform, fetched in parallel; the newest posts across all of them."""
    feeds = await asyncio.gather(*(live(p) for p in LIVE_PLATFORMS))
    posts = sorted((p for f in feeds for p in f.get("posts", [])), key=lambda p: p["date"] or "", reverse=True)
    return {"platforms": [{k: f.get(k) for k in ("platform", "connected", "reason", "fetched_at")} |
                          {"posts": len(f.get("posts", []))} for f in feeds],
            "posts": posts, "summary": _summarise(posts)}


async def live_telegram() -> dict[str, Any]:
    return await live("telegram")
