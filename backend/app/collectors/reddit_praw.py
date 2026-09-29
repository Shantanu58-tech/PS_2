from __future__ import annotations
from datetime import datetime, timezone
from typing import AsyncIterator
from app.models.canonical import RawRecord
from app.config import settings


class RedditCollector:
    name = "reddit"

    async def stream(self, targets: list[str]) -> AsyncIterator[RawRecord]:
        if not settings.reddit_client_id:
            return
        try:
            import praw
        except ImportError:
            return
        reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
        sub = "+".join(targets) if targets else "india+worldnews"
        for c in reddit.subreddit(sub).stream.comments(skip_existing=True):
            payload = {
                "id": c.id,
                "author": str(c.author),
                "body": c.body,
                "created_utc": c.created_utc,
                "link_id": c.link_id,
                "parent_id": c.parent_id,
                "subreddit": str(c.subreddit),
                "score": c.score,
            }
            yield RawRecord(
                platform="reddit",
                collector_id=self.name,
                collected_at=datetime.now(timezone.utc),
                payload=payload,
            )

    async def backfill(self, target: str, limit: int = 200) -> AsyncIterator[RawRecord]:
        async for r in self.stream([target]):
            yield r
