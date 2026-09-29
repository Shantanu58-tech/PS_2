"""Analyst audit trail: every action writes an audit_log row AND a ledger
entry (collector_id="audit"), so the trail itself is tamper-evident.

It shares the ingestor's LedgerWriter (and lock): a second writer would cache
its own prev_hash and fork the chain.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any


def log_action(db_path: str, actor: str, action: str, detail: dict[str, Any] | None = None) -> int:
    from app.pipeline.workers import get_ingestor

    ing = get_ingestor(db_path)
    now = datetime.now(timezone.utc)
    payload = {"type": "audit", "actor": actor, "action": action, "detail": detail or {}, "ts": now.isoformat()}
    with ing._lock, sqlite3.connect(db_path) as conn:
        seq = ing.ledger.append(conn, "audit", "audit", now, payload, commit=False)
        ing.last_seq = seq
        conn.execute(
            "INSERT INTO audit_log (ts, actor, action, detail_json, ledger_seq) VALUES (?,?,?,?,?)",
            (now.isoformat(), actor, action, json.dumps(detail or {}), seq),
        )
        conn.commit()
    return seq
