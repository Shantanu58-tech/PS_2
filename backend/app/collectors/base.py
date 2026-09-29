from __future__ import annotations
from typing import Protocol, AsyncIterator
from datetime import datetime
from app.models.canonical import RawRecord


class Collector(Protocol):
    name: str

    async def stream(self, targets: list[str]) -> AsyncIterator[RawRecord]: ...
    async def backfill(self, target: str, limit: int) -> AsyncIterator[RawRecord]: ...
