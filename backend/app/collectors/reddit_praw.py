"""Reddit collector via PRAW (script app). PRAW is synchronous, so calls run
in a worker thread to keep the event loop free."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from app.collectors.health import call_with_backoff, registry
from app.config import settings
from app.models.canonical import RawRecord


def comment_to_payload(c: Any) -> dict:
    return {
        "id": c.id,
        "author": str(c.author) if c.author else None,
        "body": c.body,
        "created_utc": c.created_utc,
        "link_id": c.link_id,
        "parent_id": c.parent_id,
        "subreddit": str(c.subreddit),
        "score": c.score,
    }


def submission_to_payload(s: Any) -> dict:
    return {
        "id": s.id,
        "author": str(s.author) if s.author else None,
        "selftext": f"{s.title}\n{s.selftext}".strip(),
        "created_utc": s.created_utc,
        "parent_id": "",
        "subreddit": str(s.subreddit),
        "score": s.score,
    }


class RedditCollector:
    name = "reddit"

    def __init__(self) -> None:
        self.health = registry.get(self.name)

    def _reddit(self):
        import praw

        return praw.Reddit(client_id=settings.reddit_client_id, client_secret=settings.reddit_client_secret,
                           user_agent=settings.reddit_user_agent)

    async def stream(self, targets: list[str], limit: int = 200) -> AsyncIterator[RawRecord]:
        if not (settings.reddit_client_id and settings.reddit_client_secret):
            self.health.state = "credentials_missing"
            return
        reddit = self._reddit()
        sub = "+".join(t.removeprefix("r/") for t in targets) if targets else "india"

        def fetch() -> list[dict]:
            sr = reddit.subreddit(sub)
            out = [submission_to_payload(s) for s in sr.new(limit=limit // 4)]
            out += [comment_to_payload(c) for c in sr.comments(limit=limit)]
            return out

        try:
            payloads = await call_with_backoff(self.health, lambda: asyncio.to_thread(fetch))
        except Exception:
            return
        for p in payloads:
            self.health.success()
            yield RawRecord(platform="reddit", collector_id=self.name,
                            collected_at=datetime.now(timezone.utc), payload=p)

    async def backfill(self, target: str, limit: int = 200) -> AsyncIterator[RawRecord]:
        async for r in self.stream([target], limit=limit):
            yield r
