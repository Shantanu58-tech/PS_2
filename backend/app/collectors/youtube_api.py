"""YouTube comments via the Data API v3 (commentThreads.list, part=snippet,replies;
~1 quota unit per call, 10k/day default). The client is synchronous, so pages
are fetched in a worker thread. Authors are keyed by channel id, not display
name."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from app.collectors.health import call_with_backoff, registry
from app.config import settings
from app.models.canonical import RawRecord


def _comment(c: dict, video_id: str, parent: str | None) -> dict:
    s = c["snippet"]
    return {
        "id": c["id"],
        "video_id": video_id,
        "author": (s.get("authorChannelId") or {}).get("value") or s.get("authorDisplayName"),
        "author_name": s.get("authorDisplayName"),
        "text": s.get("textOriginal") or s.get("textDisplay") or "",
        "published_at": s.get("publishedAt"),
        "likes": s.get("likeCount", 0),
        "parent_id": parent,
    }


def thread_to_payloads(item: dict, video_id: str) -> list[dict]:
    top = item["snippet"]["topLevelComment"]
    out = [_comment(top, video_id, None)]
    for reply in (item.get("replies") or {}).get("comments", []):
        out.append(_comment(reply, video_id, top["id"]))
    return out


class YouTubeCollector:
    name = "youtube"

    def __init__(self) -> None:
        self.health = registry.get(self.name)

    async def stream(self, targets: list[str], max_pages: int = 5) -> AsyncIterator[RawRecord]:
        if not settings.yt_api_key:
            self.health.state = "credentials_missing"
            return
        from googleapiclient.discovery import build

        yt = build("youtube", "v3", developerKey=settings.yt_api_key, cache_discovery=False)
        for video_id in targets:
            token = None
            for _ in range(max_pages):
                def page(tok: Any = token) -> dict:
                    return yt.commentThreads().list(
                        part="snippet,replies", videoId=video_id, maxResults=100,
                        pageToken=tok, textFormat="plainText").execute()

                try:
                    r = await call_with_backoff(self.health, lambda: asyncio.to_thread(page))
                except Exception:
                    break
                for item in r.get("items", []):
                    for p in thread_to_payloads(item, video_id):
                        self.health.success()
                        yield RawRecord(platform="youtube", collector_id=self.name,
                                        collected_at=datetime.now(timezone.utc), payload=p)
                token = r.get("nextPageToken")
                if not token:
                    break

    async def backfill(self, target: str, limit: int = 500) -> AsyncIterator[RawRecord]:
        async for r in self.stream([target], max_pages=max(1, limit // 100)):
            yield r
