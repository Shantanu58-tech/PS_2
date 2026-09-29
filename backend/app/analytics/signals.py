"""Alert (signal card) generation from bursts.

priority = 100 * (0.35*B + 0.30*C + 0.20*S + 0.15*R) with
  B = min(1, burst level / 5)
  C = share of the burst's posts written by coordinated accounts (score >= 0.7)
  S = min(1, |anxiety shift| / 0.5): mean anxiety inside the burst window minus
      the topic's mean outside it
  R = reach percentile of the burst's post count among all bursts
One alert per topic (its strongest burst).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

COORD_THRESHOLD = 0.7
MIN_LEVEL = 1


def compute_priority(
    burst_level: float,
    coordinated_share: float,
    sentiment_shift: float,
    reach_percentile: float,
) -> float:
    B = min(1.0, burst_level / 5.0)
    C = coordinated_share
    S = min(1.0, abs(sentiment_shift) / 0.5)
    R = reach_percentile
    return 100.0 * (0.35 * B + 0.30 * C + 0.20 * S + 0.15 * R)


def _burst_stats(conn: sqlite3.Connection, topic_id: int, start: str, end: str) -> dict:
    row = conn.execute(
        """
        SELECT COUNT(*) AS n,
               SUM(CASE WHEN EXISTS (SELECT 1 FROM coord_accounts ca WHERE ca.platform=p.platform
                   AND ca.account_id=p.author_id AND ca.score >= ?) THEN 1 ELSE 0 END) AS coord,
               COUNT(DISTINCT p.author_id) AS accounts,
               AVG(pe.anxiety) AS anxiety,
               GROUP_CONCAT(DISTINCT p.platform) AS platforms
        FROM topic_assign ta
        JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id
        LEFT JOIN post_emotions pe ON pe.platform=p.platform AND pe.post_id=p.post_id
        WHERE ta.topic_id=? AND p.created_at >= ? AND p.created_at <= ?
        """,
        (COORD_THRESHOLD, topic_id, start, end),
    ).fetchone()
    base = conn.execute(
        """
        SELECT AVG(pe.anxiety) FROM topic_assign ta
        JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id
        JOIN post_emotions pe ON pe.platform=p.platform AND pe.post_id=p.post_id
        WHERE ta.topic_id=? AND (p.created_at < ? OR p.created_at > ?)
        """,
        (topic_id, start, end),
    ).fetchone()[0]
    n = row["n"] or 0
    return {
        "n_posts": n,
        "n_accounts": row["accounts"] or 0,
        "coordinated_share": (row["coord"] or 0) / n if n else 0.0,
        "anxiety_shift": (row["anxiety"] or 0.0) - (base if base is not None else (row["anxiety"] or 0.0)),
        "platforms": sorted((row["platforms"] or "").split(",")) if row["platforms"] else [],
    }


def generate_signals(db_path: str) -> int:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("DELETE FROM alerts WHERE status='new'")
        bursts = conn.execute(
            "SELECT b.topic_id, b.level, b.weight, b.start, b.end, t.label "
            "FROM bursts b JOIN topics t ON t.topic_id=b.topic_id WHERE b.level >= ?",
            (MIN_LEVEL,),
        ).fetchall()
        # strongest burst per topic
        best: dict[int, sqlite3.Row] = {}
        for b in bursts:
            cur = best.get(b["topic_id"])
            if cur is None or (b["level"], b["weight"]) > (cur["level"], cur["weight"]):
                best[b["topic_id"]] = b
        stats = {tid: _burst_stats(conn, tid, b["start"], b["end"]) for tid, b in best.items()}
        sizes = sorted(s["n_posts"] for s in stats.values())

        n_alerts = 0
        for tid, b in best.items():
            st = stats[tid]
            if st["n_posts"] < 10:
                continue
            reach = sum(1 for x in sizes if x <= st["n_posts"]) / len(sizes)
            priority = compute_priority(b["level"], st["coordinated_share"], st["anxiety_shift"], reach)
            kind = "Manufactured surge" if st["coordinated_share"] >= 0.3 else "Organic burst"
            headline = (
                f"{kind}: {b['label']} - {st['n_posts']} posts from {st['n_accounts']} accounts, "
                f"{st['coordinated_share'] * 100:.0f}% from coordinated accounts"
            )
            evidence = {
                "topic_id": tid,
                "burst_level": b["level"],
                "burst_weight": b["weight"],
                "coordinated_share": st["coordinated_share"],
                "anxiety_shift": st["anxiety_shift"],
                "reach_percentile": reach,
                "platforms": st["platforms"],
                "n_posts": st["n_posts"],
                "start": b["start"],
                "end": b["end"],
            }
            conn.execute(
                "INSERT INTO alerts (created_at, topic_id, priority, headline, evidence_json, status) "
                "VALUES (?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), tid, priority, headline, json.dumps(evidence), "new"),
            )
            n_alerts += 1
        conn.commit()
    return n_alerts
