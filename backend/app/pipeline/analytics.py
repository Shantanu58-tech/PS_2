"""Analytics orchestrator: runs every derived-data stage in dependency order.

emotions -> edge resolution -> topics -> coordination -> series/bursts ->
topic classification -> demographics -> behaviour -> forecast -> signals ->
OTS anchoring. Each stage is a full, idempotent recompute of its tables
(raw_records / posts are never modified).
"""
from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Callable

from app.pipeline import events


def score_emotions(db_path: str, batch: int = 2000) -> dict[str, int]:
    from app.nlp.emotion import analyze_batch

    n = 0
    with sqlite3.connect(db_path) as conn:
        while True:
            rows = conn.execute(
                "SELECT p.platform, p.post_id, p.text FROM posts p WHERE NOT EXISTS "
                "(SELECT 1 FROM post_emotions pe WHERE pe.platform=p.platform AND pe.post_id=p.post_id) "
                "LIMIT ?",
                (batch,),
            ).fetchall()
            if not rows:
                break
            results = analyze_batch([r[2] for r in rows])
            conn.executemany(
                "INSERT OR REPLACE INTO post_emotions (platform, post_id, anxiety, excitement, supportive, "
                "against, sarcasm, neutral, sentiment, model_version) VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    (r[0], r[1], e["anxiety"], e["excitement"], e["supportive"], e["against"],
                     e["sarcasm"], e["neutral"], e["sentiment"], e["model_version"])
                    for r, e in zip(rows, results)
                ],
            )
            conn.commit()
            n += len(rows)
            events.set_status("analytics", stage=f"emotions ({n} posts)")
    return {"scored": n}


def _stages() -> list[tuple[str, Callable[[str], Any]]]:
    from app.analytics.behaviour import compute_behaviour
    from app.analytics.coordination import run_coordination
    from app.analytics.demographics import compute_demographics
    from app.analytics.forecast import compute_forecasts
    from app.analytics.signals import generate_signals
    from app.analytics.topics import run_topics
    from app.analytics.trends import classify_topics, compute_series_and_bursts
    from app.ledger.ots import anchor_pending_checkpoints
    from app.pipeline.workers import resolve_pending_edges

    return [
        ("emotions", score_emotions),
        ("edges", resolve_pending_edges),
        ("topics", run_topics),
        ("coordination", run_coordination),
        ("trends", compute_series_and_bursts),
        ("classify", classify_topics),
        ("demographics", lambda db: {
            "raw": compute_demographics(db, organic_only=False),
            "organic": compute_demographics(db, organic_only=True),
        }),
        ("behaviour", compute_behaviour),
        ("forecast", compute_forecasts),
        ("signals", generate_signals),
        ("ots", anchor_pending_checkpoints),
    ]


def run_all_analytics(db_path: str) -> dict[str, Any]:
    events.set_status(
        "analytics", state="running", stage=None, error=None,
        started_at=datetime.now(timezone.utc).isoformat(), finished_at=None,
    )
    report: dict[str, Any] = {}
    stage = ""
    try:
        for stage, fn in _stages():
            events.set_status("analytics", stage=stage)
            t0 = time.perf_counter()
            result = fn(db_path)
            report[stage] = {"result": result, "seconds": round(time.perf_counter() - t0, 2)}
            events.publish("analytics_stage_done", stage=stage, result=report[stage])
    except Exception as exc:
        events.set_status("analytics", state="error", error=f"{stage}: {exc}")
        raise
    events.set_status(
        "analytics", state="done", stage=None, finished_at=datetime.now(timezone.utc).isoformat(),
    )
    events.publish("alerts_updated")
    return report
