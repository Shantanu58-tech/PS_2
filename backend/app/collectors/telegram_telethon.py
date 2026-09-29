"""Telegram collector via Telethon (api_id/api_hash + one-time phone login).

Forward headers (message.fwd_from: original channel id / message id / date)
are kept as structured fields so lineage edges do not depend on ML.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from app.collectors.health import call_with_backoff, registry
from app.config import settings
from app.models.canonical import RawRecord


def _peer_id(peer: Any) -> str | None:
    if peer is None:
        return None
    for attr in ("channel_id", "user_id", "chat_id"):
        if getattr(peer, attr, None) is not None:
            return str(getattr(peer, attr))
    return str(peer)


def message_to_payload(msg: Any, channel: str) -> dict:
    fwd = getattr(msg, "fwd_from", None)
    fwd_payload = None
    if fwd is not None:
        fwd_payload = {
            "from_id": _peer_id(getattr(fwd, "from_id", None)),
            "channel_post": getattr(fwd, "channel_post", None),
            "date": fwd.date.isoformat() if getattr(fwd, "date", None) else None,
        }
    return {
        "id": msg.id,
        "date": msg.date.isoformat() if msg.date else None,
        "text": msg.message or "",
        "views": getattr(msg, "views", None),
        "forwards": getattr(msg, "forwards", None),
        "channel": channel,
        "from_id": _peer_id(getattr(msg, "from_id", None)),
        "fwd_from": fwd_payload,
        "reply_to": getattr(msg, "reply_to_msg_id", None),
        "has_media": bool(getattr(msg, "media", None)),
    }


class TelegramCollector:
    name = "telegram"

    def __init__(self) -> None:
        self.health = registry.get(self.name)

    def _client(self):
        from telethon import TelegramClient

        session = Path(settings.data_dir) / settings.tg_session
        return TelegramClient(str(session), int(settings.tg_api_id), settings.tg_api_hash)

    async def stream(self, targets: list[str], limit: int = 200) -> AsyncIterator[RawRecord]:
        if not (settings.tg_api_id and settings.tg_api_hash):
            self.health.state = "credentials_missing"
            return
        client = self._client()
        await client.start()  # first run prompts for phone + code (interactive, once)
        try:
            for channel in targets:
                try:
                    msgs = await call_with_backoff(
                        self.health, lambda: client.get_messages(channel, limit=limit))
                except Exception:
                    continue
                for msg in msgs:
                    self.health.success()
                    yield RawRecord(platform="telegram", collector_id=self.name,
                                    collected_at=datetime.now(timezone.utc),
                                    payload=message_to_payload(msg, channel))
        finally:
            await client.disconnect()

    async def backfill(self, target: str, limit: int = 500) -> AsyncIterator[RawRecord]:
        async for r in self.stream([target], limit=limit):
            yield r
