"""EXPERIMENTAL account-behaviour likelihood (Backlog B3).

A heuristic logistic score of how *automated-looking* an account's posting
behaviour is. It uses only behavioural features - never inferred
demographics - and is always presented as "Experimental behaviour
likelihood" (never "bot"). It is not an accusation and is not validated
beyond the synthetic scenario.

Features (accounts with >= 2 posts):
  regularity   max(0, -B) of inter-post gaps (B = Goh-Barabasi burstiness)
  template     share of the account's posts whose text repeats one of its own
               earlier posts or a text used by >= 5 other accounts
  night_share  share of posts between 00:00 and 05:00 IST
  young        1 if the account was created < 180 days before its first post
  co_sync      co-posting feature from coordination analysis (0 if absent)
"""
from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone

from app.analytics.burst import burstiness

WEIGHTS = {"regularity": 1.5, "template": 1.5, "night_share": 0.5, "young": 0.5, "co_sync": 2.0}
BIAS = 2.5
IST = timezone(timedelta(hours=5, minutes=30))


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))


def compute_behaviour(db_path: str) -> dict[str, int]:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("DELETE FROM account_behaviour")
        text_accounts: dict[str, int] = {
            r[0]: r[1] for r in conn.execute(
                "SELECT text, COUNT(DISTINCT author_id) FROM posts GROUP BY text"
            ).fetchall()
        }
        co_sync: dict[tuple[str, str], float] = {}
        for r in conn.execute("SELECT platform, account_id, reasons_json FROM coord_accounts"):
            try:
                co_sync[(r[0], r[1])] = float(json.loads(r[2]).get("co_sync", 0.0))
            except (TypeError, ValueError):
                pass
        created = {
            (r[0], r[1]): r[2] for r in conn.execute(
                "SELECT platform, account_id, created_at FROM accounts WHERE created_at IS NOT NULL"
            )
        }
        rows = conn.execute(
            "SELECT platform, author_id, text, created_at FROM posts ORDER BY platform, author_id, created_at"
        ).fetchall()

        by_acc: dict[tuple[str, str], list[sqlite3.Row]] = {}
        for r in rows:
            by_acc.setdefault((r["platform"], r["author_id"]), []).append(r)

        out = []
        for key, posts in by_acc.items():
            if len(posts) < 2:
                continue
            times = [_parse(p["created_at"]) for p in posts]
            gaps = [(times[i + 1] - times[i]).total_seconds() for i in range(len(times) - 1)]
            seen: set[str] = set()
            templated = 0
            for p in posts:
                if p["text"] in seen or text_accounts.get(p["text"], 0) >= 5:
                    templated += 1
                seen.add(p["text"])
            young = 0.0
            if key in created:
                try:
                    young = float((times[0] - _parse(created[key])).days < 180)
                except ValueError:
                    pass
            feats = {
                "regularity": max(0.0, -burstiness(gaps)) if len(gaps) >= 2 else 0.0,
                "template": templated / len(posts),
                "night_share": sum(1 for t in times if t.astimezone(IST).hour < 5) / len(times),
                "young": young,
                "co_sync": co_sync.get(key, 0.0),
                "n_posts": float(len(posts)),
            }
            raw = sum(WEIGHTS[k] * feats[k] for k in WEIGHTS) - BIAS
            likelihood = 1.0 / (1.0 + math.exp(-raw))
            out.append((key[0], key[1], likelihood, json.dumps({k: round(v, 4) for k, v in feats.items()}), now))
        conn.executemany(
            "INSERT INTO account_behaviour (platform, account_id, likelihood, features_json, computed_at) "
            "VALUES (?,?,?,?,?)",
            out,
        )
        conn.commit()
    return {"accounts_scored": len(out)}
