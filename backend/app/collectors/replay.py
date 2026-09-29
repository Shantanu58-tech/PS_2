"""Replay collector: streams a scenario JSONL through the same ingest pipeline
as live collectors (ledger -> normalise -> store), then runs analytics.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Iterator

from app.config import settings
from app.models.canonical import RawRecord
from app.pipeline import events

BATCH = 250


def read_scenario(scenario_path: str) -> list[dict]:
    path = Path(scenario_path)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines if line.strip() and not line.startswith("#")]
    records.sort(key=lambda r: r.get("created_at", ""))
    return records


def to_raw(rec: dict) -> RawRecord:
    return RawRecord(
        platform=rec.get("platform", "synthetic"),
        collector_id="replay",
        collected_at=datetime.now(timezone.utc),
        payload=rec,
    )


class ReplayCollector:
    name = "replay"

    def __init__(self, scenario_path: str | None = None) -> None:
        self.scenario_path = scenario_path or settings.scenario_path

    def iter_records(self) -> Iterator[RawRecord]:
        for rec in read_scenario(self.scenario_path):
            yield to_raw(rec)

    async def stream(self, targets: list[str]) -> AsyncIterator[RawRecord]:
        for raw in self.iter_records():
            yield raw

    async def backfill(self, target: str, limit: int = 500) -> AsyncIterator[RawRecord]:
        for i, raw in enumerate(self.iter_records()):
            if i >= limit:
                break
            yield raw


def run_replay_sync(scenario_path: str, db_path: str | None = None, analytics: bool | None = None) -> int:
    """Ingest a whole scenario in created_at order. Returns records ingested."""
    from app.pipeline.workers import get_ingestor

    records = read_scenario(scenario_path)
    events.set_status(
        "replay", state="running", ingested=0, total=len(records),
        started_at=datetime.now(timezone.utc).isoformat(), finished_at=None,
    )
    ingestor = get_ingestor(db_path)
    done = 0
    for i in range(0, len(records), BATCH):
        chunk = [to_raw(r) for r in records[i:i + BATCH]]
        ingestor.ingest_many(chunk, flush=False)
        done += len(chunk)
        events.set_status("replay", ingested=done)
    ingestor.flush()
    events.set_status("replay", state="done", finished_at=datetime.now(timezone.utc).isoformat())

    run_analytics = settings.auto_analytics if analytics is None else analytics
    if run_analytics and done:
        from app.pipeline.analytics import run_all_analytics
        run_all_analytics(db_path or settings.db_path)
    return done


async def start_replay_bg(scenario_path: str, speed: int = 60) -> None:
    # Records are ingested in created_at order in batches; wall-clock pacing by
    # simulated time is deliberately not done (see docs/DECISIONS.md), so
    # `speed` is accepted for API compatibility only.
    if events.status["replay"]["state"] == "running":
        return
    try:
        await asyncio.to_thread(run_replay_sync, scenario_path)
    except Exception as exc:  # surfaced to the UI instead of dying silently
        events.set_status("replay", state="error", error=str(exc))
