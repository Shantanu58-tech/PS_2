"""In-process event bus + pipeline status, consumed by the /api/stream SSE route.

Publishing is thread-safe: ingestion and analytics run in worker threads and
hand events to the asyncio loop with call_soon_threadsafe.
"""
from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone
from typing import Any

_subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
_loop: asyncio.AbstractEventLoop | None = None
_lock = threading.Lock()

status: dict[str, Any] = {
    "replay": {"state": "idle", "ingested": 0, "total": 0, "started_at": None, "finished_at": None},
    "analytics": {"state": "idle", "stage": None, "started_at": None, "finished_at": None, "error": None},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def bind_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop


def subscribe() -> asyncio.Queue[dict[str, Any]]:
    q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=500)
    with _lock:
        _subscribers.add(q)
    return q


def unsubscribe(q: asyncio.Queue[dict[str, Any]]) -> None:
    with _lock:
        _subscribers.discard(q)


def _deliver(event: dict[str, Any]) -> None:
    with _lock:
        subs = list(_subscribers)
    for q in subs:
        if q.full():
            try:
                q.get_nowait()  # drop oldest for slow consumers
            except asyncio.QueueEmpty:
                pass
        q.put_nowait(event)


def publish(kind: str, **data: Any) -> None:
    event = {"type": kind, "ts": _now(), **data}
    loop = _loop
    if loop is None or loop.is_closed():
        return
    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None
    if running is loop:
        _deliver(event)
    else:
        loop.call_soon_threadsafe(_deliver, event)


def set_status(section: str, **fields: Any) -> None:
    status[section].update(fields)
    publish(f"{section}_status", **status[section])
