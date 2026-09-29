from __future__ import annotations
import asyncio
from app.models.canonical import RawRecord


class IngestQueue:
    def __init__(self, maxsize: int = 10000) -> None:
        self._q: asyncio.Queue[RawRecord] = asyncio.Queue(maxsize=maxsize)

    async def put(self, record: RawRecord) -> None:
        await self._q.put(record)

    async def get(self) -> RawRecord:
        return await self._q.get()

    def qsize(self) -> int:
        return self._q.qsize()


_queue = IngestQueue()


def get_queue() -> IngestQueue:
    return _queue
