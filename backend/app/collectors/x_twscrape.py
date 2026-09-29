from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncIterator
from app.models.canonical import RawRecord
from app.config import settings


class XCollector:
    name = "x"

    async def stream(self, targets: list[str]) -> AsyncIterator[RawRecord]:
        if not settings.x_auth_token:
            return
        try:
            from twscrape import API, gather
        except ImportError:
            return
        api = API("accounts_x.db")
        await api.pool.add_account_cookies(
            settings.x_account_user,
            f"auth_token={settings.x_auth_token}; ct0={settings.x_ct0}",
        )
        for target in targets:
            try:
                user = await api.user_by_login(target)
                tweets = await gather(api.user_tweets(user.id, limit=50))
                for t in tweets:
                    payload = json.loads(t.json())
                    yield RawRecord(
                        platform="x",
                        collector_id=self.name,
                        collected_at=datetime.now(timezone.utc),
                        payload=payload,
                    )
            except Exception:
                await asyncio.sleep(5)

    async def backfill(self, target: str, limit: int = 100) -> AsyncIterator[RawRecord]:
        async for r in self.stream([target]):
            yield r
