"""Per-topic time series and burst detection.

topic_series: hourly counts per topic, all posts and organic-only (authors
with coordination score < 0.7). bursts: Kleinberg (gamma * ln n up-cost)
states >= 1 over each topic's post timestamps, mapped back to times.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from app.analytics.burst import kleinberg_bursts

COORD_THRESHOLD = 0.7


def _ts(s: str) -> float:
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()


def compute_series_and_bursts(db_path: str, gamma: float = 1.0) -> dict[str, int]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("DELETE FROM topic_series")
        conn.execute("DELETE FROM bursts")
        conn.execute(
            """
            INSERT INTO topic_series (topic_id, bucket_start, count_all, count_organic)
            SELECT ta.topic_id,
                   strftime('%Y-%m-%dT%H:00:00Z', p.created_at) AS bucket,
                   COUNT(*),
                   SUM(CASE WHEN EXISTS (
                        SELECT 1 FROM coord_accounts ca WHERE ca.platform=p.platform
                        AND ca.account_id=p.author_id AND ca.score >= ?) THEN 0 ELSE 1 END)
            FROM topic_assign ta
            JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id
            GROUP BY ta.topic_id, bucket
            """,
            (COORD_THRESHOLD,),
        )
        n_bursts = 0
        for (topic_id,) in conn.execute("SELECT topic_id FROM topics").fetchall():
            rows = conn.execute(
                "SELECT p.created_at FROM topic_assign ta JOIN posts p "
                "ON p.platform=ta.platform AND p.post_id=ta.post_id WHERE ta.topic_id=? "
                "ORDER BY p.created_at",
                (topic_id,),
            ).fetchall()
            stamps = [r[0] for r in rows]
            times = [_ts(s) for s in stamps]
            uniq = sorted(set(times))
            for b in kleinberg_bursts(times, gamma=gamma):
                # kleinberg indexes gaps over the de-duplicated timestamps
                start = datetime.fromtimestamp(uniq[b.start_idx], tz=timezone.utc)
                end = datetime.fromtimestamp(uniq[min(b.end_idx + 1, len(uniq) - 1)], tz=timezone.utc)
                conn.execute(
                    "INSERT INTO bursts (topic_id, start, end, level, weight) VALUES (?,?,?,?,?)",
                    (topic_id, start.isoformat(), end.isoformat(), b.level, b.weight),
                )
                n_bursts += 1
        conn.commit()
        series = conn.execute("SELECT COUNT(*) FROM topic_series").fetchone()[0]
    return {"series_rows": series, "bursts": n_bursts}


def classify_topics(db_path: str, share_threshold: float = 0.3) -> None:
    """Mark topics whose posts are mostly from coordinated accounts."""
    with sqlite3.connect(db_path) as conn:
        for (topic_id,) in conn.execute("SELECT topic_id FROM topics").fetchall():
            total, coord = conn.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN EXISTS (
                    SELECT 1 FROM coord_accounts ca WHERE ca.platform=p.platform
                    AND ca.account_id=p.author_id AND ca.score >= ?) THEN 1 ELSE 0 END)
                FROM topic_assign ta JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id
                WHERE ta.topic_id=?
                """,
                (COORD_THRESHOLD, topic_id),
            ).fetchone()
            share = (coord or 0) / max(1, total)
            conn.execute(
                "UPDATE topics SET nature=?, coordinated_share=? WHERE topic_id=?",
                ("manufactured" if share >= share_threshold else "organic", round(share, 4), topic_id),
            )
        conn.commit()


def rise_scores(db_path: str, recent_hours: int = 6) -> dict[int, dict[str, float]]:
    """PRD 8.D rising-trend score, per topic, as of the newest post:
        rise = 0.35 z(burst level) + 0.25 z(acceleration) + 0.20 z(novelty)
             + 0.20 z(unique-account growth)
    acceleration: second difference of EWMA-smoothed hourly counts at the end
    of the series; novelty: 1 - max cosine of the topic centroid to topics first
    seen more than 24 h earlier; growth: unique authors in the last
    `recent_hours` vs the previous `recent_hours`."""
    import numpy as np

    with sqlite3.connect(db_path) as conn:
        latest = conn.execute("SELECT MAX(created_at) FROM posts").fetchone()[0]
        if not latest:
            return {}
        now = datetime.fromisoformat(latest.replace("Z", "+00:00"))
        topics = conn.execute("SELECT topic_id, centroid, first_seen FROM topics").fetchall()
        feats: dict[int, list[float]] = {}
        cents = {t[0]: np.frombuffer(t[1], dtype=np.float32) for t in topics if t[1]}
        firsts = {t[0]: datetime.fromisoformat(t[2]) for t in topics}
        for tid, _, _ in topics:
            level = conn.execute("SELECT COALESCE(MAX(level), 0) FROM bursts WHERE topic_id=?", (tid,)).fetchone()[0]
            counts = [r[0] for r in conn.execute(
                "SELECT count_all FROM topic_series WHERE topic_id=? ORDER BY bucket_start", (tid,))]
            ew: list[float] = []
            a = 0.3
            for c in counts[-24:]:
                ew.append(c if not ew else a * c + (1 - a) * ew[-1])
            accel = (ew[-1] - 2 * ew[-2] + ew[-3]) if len(ew) >= 3 else 0.0
            older = [c for t2, c in cents.items() if t2 != tid and (firsts[tid] - firsts[t2]).total_seconds() > 86400]
            c0 = cents.get(tid)
            novelty = 1.0 - max((float(c0 @ o / ((np.linalg.norm(c0) * np.linalg.norm(o)) or 1)) for o in older),
                                default=0.0) if c0 is not None else 0.0

            def authors(lo: datetime, hi: datetime) -> int:
                return conn.execute(
                    "SELECT COUNT(DISTINCT p.author_id) FROM topic_assign ta JOIN posts p ON p.platform=ta.platform "
                    "AND p.post_id=ta.post_id WHERE ta.topic_id=? AND p.created_at > ? AND p.created_at <= ?",
                    (tid, lo.isoformat(), hi.isoformat())).fetchone()[0]
            win = timedelta(hours=recent_hours)
            growth = authors(now - win, now) - authors(now - 2 * win, now - win)
            feats[tid] = [float(level), float(accel), float(novelty), float(growth)]
    if not feats:
        return {}
    m = np.array(list(feats.values()))
    z = (m - m.mean(axis=0)) / np.where(m.std(axis=0) > 0, m.std(axis=0), 1.0)
    w = np.array([0.35, 0.25, 0.20, 0.20])
    return {tid: {"rise": round(float(z[i] @ w), 4), "burst_level": v[0], "acceleration": round(v[1], 3),
                  "novelty": round(v[2], 4), "account_growth": v[3]}
            for i, (tid, v) in enumerate(feats.items())}
