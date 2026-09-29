from __future__ import annotations
from datetime import datetime, timezone
from typing import AsyncIterator
from app.models.canonical import RawRecord
from app.config import settings


class TelegramCollector:
    name = "telegram"

    async def stream(self, targets: list[str]) -> AsyncIterator[RawRecord]:
        if not settings.tg_api_id:
            return
        try:
            from telethon import TelegramClient, events
        except ImportError:
            return
        client = TelegramClient(settings.tg_session, int(settings.tg_api_id), settings.tg_api_hash)
        await client.start()
        for channel in targets:
            async for msg in client.iter_messages(channel, limit=200):
                payload = {
                    "id": msg.id,
                    "date": msg.date.isoformat() if msg.date else None,
                    "text": msg.text or "",
                    "views": getattr(msg, "views", None),
                    "forwards": getattr(msg, "forwards", None),
                    "channel": channel,
                    "fwd_from": str(msg.fwd_from) if msg.fwd_from else None,
                    "reply_to": msg.reply_to_msg_id,
                }
                yield RawRecord(
                    platform="telegram",
                    collector_id=self.name,
                    collected_at=datetime.now(timezone.utc),
                    payload=payload,
                )
        await client.disconnect()

    async def backfill(self, target: str, limit: int = 500) -> AsyncIterator[RawRecord]:
        async for r in self.stream([target]):
            yield r
