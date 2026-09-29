from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone


def compute_priority(
    burst_level: float,
    coordinated_share: float,
    sentiment_shift: float,
    reach_percentile: float,
) -> float:
    B = min(1.0, burst_level / 5.0)
    C = coordinated_share
    S = min(1.0, sentiment_shift / 5.0)
    R = reach_percentile
    return 100.0 * (0.35 * B + 0.30 * C + 0.20 * S + 0.15 * R)


def generate_signals(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        bursts = conn.execute(
            "SELECT b.topic_id, b.level, b.weight, b.start, b.end, t.label "
            "FROM bursts b JOIN topics t ON t.topic_id=b.topic_id "
            "WHERE b.level >= 1 ORDER BY b.weight DESC LIMIT 20"
        ).fetchall()

        for burst in bursts:
            existing = conn.execute(
                "SELECT alert_id FROM alerts WHERE topic_id=? AND status='new'",
                (burst["topic_id"],),
            ).fetchone()
            if existing:
                continue

            coord = conn.execute(
                "SELECT COUNT(*) as n FROM coord_accounts ca "
                "JOIN topic_assign ta ON ta.platform=ca.platform AND ta.post_id IN "
                "(SELECT post_id FROM posts WHERE platform=ca.platform) "
                "WHERE ta.topic_id=? AND ca.score >= 0.7",
                (burst["topic_id"],),
            ).fetchone()
            total = conn.execute(
                "SELECT COUNT(*) as n FROM topic_assign WHERE topic_id=?",
                (burst["topic_id"],),
            ).fetchone()
            coord_n = coord["n"] if coord else 0
            total_n = total["n"] if total else 1
            coord_share = coord_n / max(1, total_n)

            priority = compute_priority(burst["level"], coord_share, 0.0, 0.5)
            headline = (
                f"{'Manufactured surge' if coord_share > 0.3 else 'Organic burst'}: "
                f"{burst['label']} -- {coord_n} coordinated accounts, "
                f"{coord_share*100:.0f}% coordinated"
            )
            evidence = {
                "topic_id": burst["topic_id"],
                "burst_level": burst["level"],
                "burst_weight": burst["weight"],
                "coordinated_share": coord_share,
                "start": burst["start"],
                "end": burst["end"],
            }
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO alerts (created_at, topic_id, priority, headline, evidence_json, status) "
                "VALUES (?,?,?,?,?,?)",
                (now, burst["topic_id"], priority, headline, json.dumps(evidence), "new"),
            )
        conn.commit()
