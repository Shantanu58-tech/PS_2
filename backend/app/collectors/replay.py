from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from app.models.canonical import RawRecord
from app.pipeline.workers import ingest_record


async def start_replay_bg(scenario_path: str, speed: int = 60) -> None:
    path = Path(scenario_path)
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(l) for l in lines if l.strip() and not l.startswith("#")]
    if not records:
        return
    records.sort(key=lambda r: r.get("created_at", ""))
    t0_sim = records[0].get("created_at", datetime.now(timezone.utc).isoformat())
    t0_real = datetime.now(timezone.utc)
    for rec in records:
        raw = RawRecord(
            platform=rec.get("platform", "synthetic"),
            collector_id="replay",
            collected_at=datetime.now(timezone.utc),
            payload=rec,
        )
        await ingest_record(raw)
        await asyncio.sleep(0.01 / max(1, speed))
