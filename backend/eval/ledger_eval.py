"""Ledger: single-byte tamper trials on a scratch copy; verify time at 10k and
100k records (synthetic ledger built with the real LedgerWriter)."""
from __future__ import annotations

import random
import shutil
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from app.db.session import init_db_sync
from app.ledger.chain import LedgerWriter
from app.ledger.verify import verify_chain
from eval.common import md_table, write_report

FIELDS = ["payload_canonical", "record_hash", "entry_hash", "prev_entry_hash", "collected_at", "collector_id"]


def tamper_trials(db: str, n: int = 1000, seed: int = 7) -> dict:
    rng = random.Random(seed)
    tmp = Path(tempfile.mkdtemp(prefix="prahari_tamper_eval_"))
    try:
        scratch = str(tmp / "scratch.db")
        with sqlite3.connect(db) as src, sqlite3.connect(scratch) as dst:
            src.backup(dst)
        detected = at_seq = 0
        by_field = {f: [0, 0] for f in FIELDS}
        with sqlite3.connect(scratch) as conn:
            conn.execute("DROP TRIGGER IF EXISTS raw_no_update")
            max_seq = conn.execute("SELECT MAX(seq) FROM raw_records").fetchone()[0]
            for _ in range(n):
                seq = rng.randint(1, max_seq)
                field = rng.choice(FIELDS)
                orig = conn.execute(f"SELECT {field} FROM raw_records WHERE seq=?", (seq,)).fetchone()[0]
                pos = rng.randrange(len(orig))
                new_ch = chr((ord(orig[pos]) + rng.randint(1, 25)) % 0x7F or 0x41)
                mutated = orig[:pos] + new_ch + orig[pos + 1:]
                if mutated == orig:
                    mutated = orig[:pos] + ("A" if orig[pos] != "A" else "B") + orig[pos + 1:]
                conn.execute(f"UPDATE raw_records SET {field}=? WHERE seq=?", (mutated, seq))
                conn.commit()
                res = verify_chain(scratch)
                ok = res["status"] == "FAIL"
                detected += ok
                at_seq += ok and res.get("seq") in (seq, seq + 1)
                by_field[field][0] += ok
                by_field[field][1] += 1
                conn.execute(f"UPDATE raw_records SET {field}=? WHERE seq=?", (orig, seq))
                conn.commit()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {"trials": n, "detected": detected, "detection_rate": round(detected / n, 4),
            "localized_at_seq_rate": round(at_seq / n, 4),
            "by_field": {f: f"{d}/{t}" for f, (d, t) in by_field.items()}}


def verify_timing(sizes: tuple[int, ...] = (10_000, 100_000)) -> list[dict]:
    rows = []
    for n in sizes:
        tmp = Path(tempfile.mkdtemp(prefix="prahari_verify_"))
        try:
            db = str(tmp / "ledger.db")
            init_db_sync(db)
            w = LedgerWriter(db)
            t0 = time.perf_counter()
            with sqlite3.connect(db) as conn:
                for i in range(n):
                    w.append(conn, "synthetic", "bench", datetime.now(timezone.utc),
                             {"i": i, "text": f"benchmark record {i}"}, commit=False)
                    if i % 5000 == 0:
                        conn.commit()
                w.flush(conn, n)
                conn.commit()
            write_s = time.perf_counter() - t0
            t1 = time.perf_counter()
            res = verify_chain(db)
            rows.append({"records": n, "write_seconds": round(write_s, 2),
                         "verify_seconds": round(time.perf_counter() - t1, 2), "status": res["status"]})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return rows


def evaluate(built: dict, trials: int = 1000, sizes: tuple[int, ...] = (10_000, 100_000)) -> dict:
    tam = tamper_trials(built["db"], trials)
    timing = verify_timing(sizes)
    lines = [f"Single-character mutations of one random field of one random record, {trials} trials "
             "(scratch copy; append-only triggers dropped on the copy only).", "",
             *md_table([tam], ["trials", "detected", "detection_rate", "localized_at_seq_rate"]), "",
             *md_table([{"field": k, "detected/trials": v} for k, v in tam["by_field"].items()],
                       ["field", "detected/trials"]),
             "", "## Verification time", "", *md_table(timing, ["records", "write_seconds", "verify_seconds", "status"])]
    write_report("ledger", "Evidence ledger evaluation", lines)
    return {"tamper_detection_rate": tam["detection_rate"], "tamper_trials": trials,
            "tamper_localized_rate": tam["localized_at_seq_rate"], "tamper_by_field": tam["by_field"],
            "verify_timing": timing,
            "verify_100k_seconds": next((r["verify_seconds"] for r in timing if r["records"] == 100_000), None)}
