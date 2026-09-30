"""In-process cache for expensive read endpoints, keyed by a cheap data version.

The free host has a tenth of a CPU core; recomputing topic ranking, lineage or
the interaction graph on every request made some pages take 10+ seconds. The
version changes whenever new posts, topics, alerts or analytics results land,
so cached answers are never stale; they are just not recomputed for every visitor.
"""
from __future__ import annotations

import asyncio
import sqlite3
from typing import Any, Awaitable, Callable

from app.config import settings
from app.pipeline import events

_values: dict[str, tuple[str, Any]] = {}
_locks: dict[str, asyncio.Lock] = {}


def data_version(db_path: str | None = None) -> str:
    with sqlite3.connect(db_path or settings.db_path) as conn:
        row = conn.execute(
            "SELECT (SELECT MAX(rowid) FROM posts), (SELECT MAX(topic_id) FROM topics), "
            "(SELECT COUNT(*) FROM topics), (SELECT MAX(alert_id) FROM alerts)").fetchone()
    return f"{settings.db_path}|{row}|{events.status['analytics'].get('finished_at')}"


async def cached(key: str, compute: Callable[[], Awaitable[Any]]) -> Any:
    version = await asyncio.to_thread(data_version)
    hit = _values.get(key)
    if hit and hit[0] == version:
        return hit[1]
    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:  # one computation per key even when many visitors arrive at once
        hit = _values.get(key)
        if hit and hit[0] == version:
            return hit[1]
        value = await compute()
        _values[key] = (version, value)
        return value


def clear() -> None:
    _values.clear()
