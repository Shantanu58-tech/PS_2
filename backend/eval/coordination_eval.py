"""Coordination detector: account-level P/R/F1 vs ground truth, baselines,
per-signal ablation, decoy false positives. Weights were set on the
validation seed; the headline numbers are from the held-out seed."""
from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from eval.common import connect, md_table, prf, write_report

THRESHOLD = 0.7


def _flagged(db: str) -> set[str]:
    with connect(db) as c:
        return {r[0] for r in c.execute(
            "SELECT DISTINCT account_id FROM coord_accounts WHERE score >= ?", (THRESHOLD,))}


def _population(db: str) -> set[str]:
    with connect(db) as c:
        return {r[0] for r in c.execute("SELECT DISTINCT author_id FROM posts")}


def _score(flagged: set[str], truth: set[str]) -> dict:
    return prf(len(flagged & truth), len(flagged - truth), len(truth - flagged))


def baseline_age_ratio(db: str) -> set[str]:
    """Flag young accounts (< 365 days old at first post) with low follower ratio."""
    out = set()
    with connect(db) as c:
        rows = c.execute(
            "SELECT a.account_id, a.created_at, a.followers, a.following, MIN(p.created_at) AS first "
            "FROM accounts a JOIN posts p ON p.author_id=a.account_id GROUP BY a.account_id").fetchall()
    for r in rows:
        if not r["created_at"]:
            continue
        age = (datetime.fromisoformat(r["first"]) - datetime.fromisoformat(r["created_at"])).days
        ratio = (r["followers"] or 0) / max(1, r["following"] or 1)
        if age < 365 and ratio < 0.5:
            out.add(r["account_id"])
    return out


def baseline_exact_dup(db: str, window_s: int = 60, min_accounts: int = 5) -> set[str]:
    """Flag accounts posting an exact text also posted by >= min_accounts others within window."""
    with connect(db) as c:
        rows = c.execute("SELECT author_id, text, created_at FROM posts ORDER BY text, created_at").fetchall()
    out: set[str] = set()
    by_text: dict[str, list[tuple[float, str]]] = {}
    for r in rows:
        by_text.setdefault(r["text"], []).append((datetime.fromisoformat(r["created_at"]).timestamp(), r["author_id"]))
    for items in by_text.values():
        if len(items) < min_accounts:
            continue
        j = 0
        for i in range(len(items)):
            while items[i][0] - items[j][0] > window_s:
                j += 1
            accts = {a for _, a in items[j:i + 1]}
            if len(accts) >= min_accounts:
                out |= accts
    return out


def ablation(db: str, truth: set[str]) -> list[dict]:
    """Re-run coordination on a scratch copy with one signal's weight zeroed."""
    import app.analytics.coordination as co

    rows = []
    tmp = Path(tempfile.mkdtemp(prefix="deepastambha_abl_"))
    try:
        scratch = str(tmp / "abl.db")
        with sqlite3.connect(db) as src, sqlite3.connect(scratch) as dst:
            src.backup(dst)
        base_w, base_aw = list(co.WEIGHTS), dict(co.ACCOUNT_WEIGHTS)
        cluster_names = ["sync", "1-Hn", "max(0,-B)", "cross_account_dup", "regular_share"]
        variants = [("full model", None, None)]
        variants += [(f"cluster -{n}", i, None) for i, n in enumerate(cluster_names)]
        variants += [(f"account -{k}", None, k) for k in base_aw]
        for name, ci, ak in variants:
            co.WEIGHTS[:] = base_w
            co.ACCOUNT_WEIGHTS.clear()
            co.ACCOUNT_WEIGHTS.update(base_aw)
            if ci is not None:
                co.WEIGHTS[ci] = 0.0
            if ak is not None:
                co.ACCOUNT_WEIGHTS[ak] = 0.0
            co.run_coordination(scratch)
            rows.append({"variant": name, **_score(_flagged(scratch), truth)})
        co.WEIGHTS[:] = base_w
        co.ACCOUNT_WEIGHTS.clear()
        co.ACCOUNT_WEIGHTS.update(base_aw)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return rows


def evaluate(built: dict, heldout: dict) -> dict:
    results = {}
    for label, b in (("validation_seed", built), ("heldout_seed", heldout)):
        truth = set(b["truth"]["coordinated_account_ids"])
        flagged = _flagged(b["db"])
        decoy = set(b["truth"].get("fan_club_account_ids", []))
        with connect(b["db"]) as c:
            decoy |= {r[0] for r in c.execute(
                "SELECT DISTINCT author_id FROM posts WHERE post_id LIKE 'cricket_%' OR post_id LIKE 'fanclub_%'")}
        results[label] = {
            "seed": b["truth"]["scenario_seed"],
            "ours": _score(flagged, truth),
            "baseline_age_ratio": _score(baseline_age_ratio(b["db"]), truth),
            "baseline_exact_duplicate": _score(baseline_exact_dup(b["db"]), truth),
            "decoy_accounts_flagged": len(flagged & decoy),
            "fan_club_flagged": len(flagged & set(b["truth"].get("fan_club_account_ids", []))),
            "population_accounts": len(_population(b["db"])),
        }
    abl = ablation(heldout["db"], set(heldout["truth"]["coordinated_account_ids"]))
    h = results["heldout_seed"]
    lines = [
        f"Threshold: account score >= {THRESHOLD}. Weights set on seed {built['truth']['scenario_seed']}; "
        f"headline = held-out seed {h['seed']}.", "",
        "## Account-level detection", "",
        *md_table([{"seed": results[k]["seed"], "method": m, **results[k][m]}
                   for k in results for m in ("ours", "baseline_age_ratio", "baseline_exact_duplicate")],
                  ["seed", "method", "precision", "recall", "f1", "tp", "fp", "fn"]),
        "", f"Decoy (cricket + fan-club) accounts flagged on held-out seed: {h['decoy_accounts_flagged']} "
        f"(fan-club: {h['fan_club_flagged']})", "",
        "## Ablation (held-out seed; one weight zeroed at a time)", "",
        *md_table(abl, ["variant", "precision", "recall", "f1", "tp", "fp", "fn"]),
        "", "Limitations: scenario is synthetic; scripted accounts follow one template family. "
        "Real campaigns vary cadence and content; expect lower recall on real data.",
    ]
    write_report("coordination", "Coordination detector evaluation", lines)
    return {
        "precision": h["ours"]["precision"], "recall": h["ours"]["recall"], "f1": h["ours"]["f1"],
        "heldout_seed": h["seed"], "validation_f1": results["validation_seed"]["ours"]["f1"],
        "baseline_age_ratio_f1": h["baseline_age_ratio"]["f1"],
        "baseline_exact_duplicate_f1": h["baseline_exact_duplicate"]["f1"],
        "decoy_accounts_flagged": h["decoy_accounts_flagged"], "fan_club_flagged": h["fan_club_flagged"],
        "ablation": abl, "detail": json.loads(json.dumps(results)),
    }
