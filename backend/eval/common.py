"""Shared eval helpers: build (or reuse) an analysed DB per scenario seed."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

from app.config import ROOT, settings

settings.enable_ots = False  # evals must not stamp throwaway DBs on public calendars

EVAL_DATA = Path(settings.data_dir) / "eval"
REPORTS = Path(settings.eval_dir)
VALIDATION_SEED = 7
HELDOUT_SEED = 11


def scenario_paths(seed: int) -> tuple[Path, Path]:
    if seed == VALIDATION_SEED:
        return Path(settings.scenario_path), Path(settings.scenario_path).with_name("truth.json")
    s = ROOT / "replay" / f"scenario_seed{seed}.jsonl"
    return s, s.with_name(f"truth_scenario_seed{seed}.json")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def build_db(seed: int, force: bool = False) -> dict[str, Any]:
    """Replay + analytics for a seed into data/eval/seed<N>.db (cached by scenario hash)."""
    from app.collectors.replay import run_replay_sync
    from app.db.session import init_db_sync
    from app.pipeline.analytics import run_all_analytics
    from app.pipeline.workers import reset_ingestors
    from scenario.generate import generate_scenario

    scenario, truth_path = scenario_paths(seed)
    if not scenario.exists():
        generate_scenario(seed, str(scenario), settings.media_dir if seed == VALIDATION_SEED else None)
    EVAL_DATA.mkdir(parents=True, exist_ok=True)
    db = EVAL_DATA / f"seed{seed}.db"
    meta_path = EVAL_DATA / f"seed{seed}.meta.json"
    digest = _digest(scenario)
    if not force and db.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta.get("scenario_digest") == digest:
            return {**meta, "db": str(db), "truth": json.loads(truth_path.read_text(encoding="utf-8"))}
    for p in (db, Path(str(db) + "-wal"), Path(str(db) + "-shm")):
        if p.exists():
            os.remove(p)
    init_db_sync(str(db))
    reset_ingestors()
    t0 = time.perf_counter()
    n = run_replay_sync(str(scenario), str(db), analytics=False)
    ingest_s = time.perf_counter() - t0
    t1 = time.perf_counter()
    stages = run_all_analytics(str(db))
    analytics_s = time.perf_counter() - t1
    meta = {"seed": seed, "scenario_digest": digest, "records": n, "ingest_seconds": round(ingest_s, 1),
            "analytics_seconds": round(analytics_s, 1),
            "stage_seconds": {k: v["seconds"] for k, v in stages.items()}}
    meta_path.write_text(json.dumps(meta, indent=2))
    return {**meta, "db": str(db), "truth": json.loads(truth_path.read_text(encoding="utf-8"))}


def connect(db: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn


def prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4), "tp": tp, "fp": fp, "fn": fn}


def write_report(name: str, title: str, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.md").write_text(f"# {title}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def md_table(rows: list[dict], cols: list[str]) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return out
