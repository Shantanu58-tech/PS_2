from __future__ import annotations
from datetime import datetime, timezone
from typing import AsyncIterator
from app.models.canonical import RawRecord
from app.config import settings


class YouTubeCollector:
    name = "youtube"

    async def stream(self, targets: list[str]) -> AsyncIterator[RawRecord]:
        if not settings.yt_api_key:
            return
        try:
            from googleapiclient.discovery import build
        except ImportError:
            return
        yt = build("youtube", "v3", developerKey=settings.yt_api_key)
        for video_id in targets:
            token = None
            while True:
                try:
                    r = yt.commentThreads().list(
                        part="snippet,replies",
                        videoId=video_id,
                        maxResults=100,
                        pageToken=token,
                        textFormat="plainText",
                    ).execute()
                    for it in r["items"]:
                        s = it["snippet"]["topLevelComment"]["snippet"]
                        payload = {
                            "id": it["id"],
                            "video_id": video_id,
                            "author": s["authorDisplayName"],
                            "text": s["textDisplay"],
                            "published_at": s["publishedAt"],
                            "likes": s["likeCount"],
                        }
                        yield RawRecord(
                            platform="youtube",
                            collector_id=self.name,
                            collected_at=datetime.now(timezone.utc),
                            payload=payload,
                        )
                    token = r.get("nextPageToken")
                    if not token:
                        break
                except Exception:
                    break

    async def backfill(self, target: str, limit: int = 500) -> AsyncIterator[RawRecord]:
        async for r in self.stream([target]):
            yield r
