"""Live mode: poll each configured collector for its targets, ingest through
the ledger pipeline, and recompute analytics periodically. A failing
collector degrades its own health only; the others keep running."""
from __future__ import annotations

import asyncio
import logging
import sqlite3

from app.config import settings
from app.pipeline import events

log = logging.getLogger("prahari.scheduler")

POLL_SECONDS = 300
ANALYTICS_SECONDS = 600


def _collectors() -> dict:
    from app.collectors.reddit_praw import RedditCollector
    from app.collectors.telegram_telethon import TelegramCollector
    from app.collectors.x_twscrape import XCollector
    from app.collectors.youtube_api import YouTubeCollector

    return {"x": XCollector(), "telegram": TelegramCollector(), "reddit": RedditCollector(),
            "youtube": YouTubeCollector()}


def _targets() -> dict[str, list[str]]:
    with sqlite3.connect(settings.db_path) as conn:
        rows = conn.execute("SELECT collector, target FROM collector_targets").fetchall()
    out: dict[str, list[str]] = {}
    for c, t in rows:
        out.setdefault(c, []).append(t)
    return out


async def collect_once(name: str, collector, targets: list[str]) -> int:
    from app.pipeline.workers import get_ingestor

    batch = []
    try:
        async for raw in collector.stream(targets):
            batch.append(raw)
    except Exception as exc:  # isolate: one collector never stops the others
        collector.health.failure(exc)
        log.warning("collector %s failed: %s", name, exc)
    if batch:
        await asyncio.to_thread(get_ingestor().ingest_many, batch)
        events.publish("ingested", collector=name, records=len(batch))
    return len(batch)


async def live_loop(stop: asyncio.Event) -> None:
    collectors = _collectors()
    last_analytics = 0.0
    loop = asyncio.get_running_loop()
    while not stop.is_set():
        targets = _targets()
        await asyncio.gather(*[
            collect_once(name, c, targets[name]) for name, c in collectors.items() if targets.get(name)
        ])
        if loop.time() - last_analytics >= ANALYTICS_SECONDS:
            from app.pipeline.analytics import run_all_analytics

            try:
                await asyncio.to_thread(run_all_analytics, settings.db_path)
            except Exception as exc:
                log.warning("analytics failed: %s", exc)
            last_analytics = loop.time()
        try:
            await asyncio.wait_for(stop.wait(), timeout=POLL_SECONDS)
        except asyncio.TimeoutError:
            pass
