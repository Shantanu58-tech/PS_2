"""X (Twitter) collector via twscrape (research-grade; burner-account cookies).

twscrape >= 0.20: cookie login is AccountsPool.add_account(..., cookies=...)
(the older add_account_cookies no longer exists) - see docs/DECISIONS.md.
Tweet JSON fields used: id, rawContent, date, user{...}, inReplyToTweetId,
retweetedTweet, quotedTweet, conversationId, likeCount, retweetCount.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from app.collectors.health import call_with_backoff, registry
from app.config import settings
from app.models.canonical import RawRecord


def tweet_to_payload(tweet_json: str | dict) -> dict:
    return json.loads(tweet_json) if isinstance(tweet_json, str) else dict(tweet_json)


class XCollector:
    name = "x"

    def __init__(self) -> None:
        self.health = registry.get(self.name)
        self._api = None

    async def _get_api(self):
        if self._api is None:
            from twscrape import API

            api = API(str(Path(settings.data_dir) / "twscrape_accounts.db"))
            await api.pool.add_account(
                settings.x_account_user or "burner", password="", email="", email_password="",
                cookies=f"auth_token={settings.x_auth_token}; ct0={settings.x_ct0}",
                proxy=settings.proxy_url or None,
            )
            self._api = api
        return self._api

    def _record(self, tweet) -> RawRecord:
        return RawRecord(platform="x", collector_id=self.name, collected_at=datetime.now(timezone.utc),
                         payload=tweet_to_payload(tweet.json()))

    async def stream(self, targets: list[str]) -> AsyncIterator[RawRecord]:
        if not (settings.x_auth_token and settings.x_ct0):
            self.health.state = "credentials_missing"
            return
        from twscrape import gather

        api = await self._get_api()
        for target in targets:
            try:
                if target.startswith(("#", "q:")):
                    query = target[2:] if target.startswith("q:") else target
                    tweets = await call_with_backoff(self.health, lambda: gather(api.search(query, limit=100)))
                else:
                    user = await call_with_backoff(self.health, lambda: api.user_by_login(target.lstrip("@")))
                    tweets = await call_with_backoff(self.health, lambda: gather(api.user_tweets(user.id, limit=100)))
            except Exception:
                continue  # health already records the failure; move to next target
            for t in tweets:
                self.health.success()
                yield self._record(t)

    async def replies(self, tweet_id: int, limit: int = 200) -> AsyncIterator[RawRecord]:
        from twscrape import gather

        api = await self._get_api()
        for t in await call_with_backoff(self.health, lambda: gather(api.tweet_replies(tweet_id, limit=limit))):
            yield self._record(t)

    async def backfill(self, target: str, limit: int = 100) -> AsyncIterator[RawRecord]:
        n = 0
        async for r in self.stream([target]):
            yield r
            n += 1
            if n >= limit:
                break
