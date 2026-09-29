"""Shared helpers for the API routers."""
from __future__ import annotations

import json
from typing import Any, Iterable

import aiosqlite

from app.config import settings

COORD_THRESHOLD = 0.7
ORGANIC_CLAUSE = (
    "NOT EXISTS (SELECT 1 FROM coord_accounts ca WHERE ca.platform=p.platform "
    "AND ca.account_id=p.author_id AND ca.score >= 0.7)"
)


def connect() -> aiosqlite.Connection:
    return aiosqlite.connect(settings.db_path)


async def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[dict]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(sql, tuple(params))
    return [dict(r) for r in rows]


async def fetch_one(sql: str, params: Iterable[Any] = ()) -> dict | None:
    rows = await fetch_all(sql, params)
    return rows[0] if rows else None


def fts_query(q: str) -> str:
    """Turn free text into a safe FTS5 query: each word quoted, AND-ed.
    Raw user input (quotes, colons, operators) would otherwise be FTS5 syntax."""
    import re

    words = re.findall(r"[\w#@]+", q, flags=re.UNICODE)
    return " ".join('"' + w.replace('"', "") + '"' for w in words) or '""'


def loads(value: str | None, default: Any = None) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default
