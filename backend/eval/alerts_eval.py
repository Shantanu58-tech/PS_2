"""Signal Cards vs a naive keyword-volume baseline; online burst lead time;
gamma sensitivity; decoy must not produce a high-priority alert."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from app.analytics.burst import kleinberg_bursts
from eval.common import connect, md_table, write_report

HIGH = 70.0
RUMOUR_KEY = "varunapur"
DECOY_KEY = "indvsaus"


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def naive_baseline(db: str, z: float = 3.0) -> list[dict]:
    """Hourly per-keyword volume; alert when count > mean + z*std of the
    trailing 24 h (keywords = hashtags and lowercase words >= 5 chars)."""
    counts: dict[str, Counter] = defaultdict(Counter)
    with connect(db) as c:
        for r in c.execute("SELECT text, created_at FROM posts"):
            hour = _ts(r["created_at"]).replace(minute=0, second=0, microsecond=0)
            for w in {w.strip("#!.,?").lower() for w in r["text"].split() if len(w.strip("#!.,?")) >= 5}:
                counts[w][hour] += 1
    alerts = []
    all_hours = sorted({h for s in counts.values() for h in s})
    if not all_hours:
        return alerts
    # Every keyword is scanned from dataset start + 24 h with absent hours = 0,
    # so a brand-new keyword (no history) can fire; starting at the keyword's
    # own first appearance would make new narratives undetectable.
    t_start, t_end = all_hours[0] + timedelta(hours=24), all_hours[-1]
    for kw, series in counts.items():
        if sum(series.values()) < 30:
            continue
        h = t_start
        while h <= t_end:
            window = [series.get(h - timedelta(hours=k), 0) for k in range(1, 25)]
            mean = sum(window) / 24
            std = math.sqrt(sum((x - mean) ** 2 for x in window) / 24)
            if series.get(h, 0) > mean + z * max(std, 1.0) and series.get(h, 0) >= 10:
                alerts.append({"keyword": kw, "hour": h, "count": series[h]})
            h += timedelta(hours=1)
    return alerts


def online_detection(db: str, topic_id: int, step_min: int = 5, gamma: float = 1.0) -> datetime | None:
    """First time t at which Kleinberg on posts up to t shows a level>=1 burst
    that is still open (ends at the last observed post) - no hindsight."""
    with connect(db) as c:
        times = sorted(_ts(r[0]) for r in c.execute(
            "SELECT p.created_at FROM topic_assign ta JOIN posts p ON p.platform=ta.platform "
            "AND p.post_id=ta.post_id WHERE ta.topic_id=?", (topic_id,)))
    if len(times) < 5:
        return None
    t = times[0] + timedelta(minutes=step_min)
    while t <= times[-1] + timedelta(minutes=step_min):
        prefix = [x.timestamp() for x in times if x <= t]
        uniq = sorted(set(prefix))
        if len(uniq) >= 5:
            for b in kleinberg_bursts(prefix, gamma=gamma):
                if b.level >= 1 and b.end_idx >= len(uniq) - 3:
                    return t
        t += timedelta(minutes=step_min)
    return None


def _topic_for(db: str, key: str) -> list[int]:
    with connect(db) as c:
        rows = c.execute(
            "SELECT ta.topic_id, COUNT(*) n FROM topic_assign ta JOIN posts p ON p.platform=ta.platform "
            "AND p.post_id=ta.post_id WHERE lower(p.text) LIKE ? GROUP BY 1 ORDER BY n DESC", (f"%{key}%",)).fetchall()
    return [r[0] for r in rows]


def evaluate(built: dict) -> dict:
    db, truth = built["db"], built["truth"]
    t0 = _ts(truth["t0"])
    with connect(db) as c:
        alerts = [dict(r) for r in c.execute("SELECT * FROM alerts ORDER BY priority DESC")]
        topics = {r["topic_id"]: dict(r) for r in c.execute("SELECT topic_id, label, nature FROM topics")}
        span = c.execute("SELECT MIN(created_at), MAX(created_at) FROM posts").fetchone()
    days = max(1.0, (_ts(span[1]) - _ts(span[0])).total_seconds() / 86400)
    rumour_topics, decoy_topics = set(_topic_for(db, RUMOUR_KEY)[:3]), set(_topic_for(db, DECOY_KEY)[:5])
    decoy_topics -= rumour_topics

    high = [a for a in alerts if a["priority"] >= HIGH]
    rumour_high = [a for a in high if a["topic_id"] in rumour_topics]
    decoy_high = [a for a in high if a["topic_id"] in decoy_topics]

    naive = naive_baseline(db)
    naive_rumour = sorted(a["hour"] for a in naive if a["keyword"] == RUMOUR_KEY)
    # the naive detector can only fire once the hourly bucket has closed
    naive_first = naive_rumour[0] + timedelta(hours=1) if naive_rumour else None
    naive_decoy = [a for a in naive if a["keyword"] in (DECOY_KEY, "cricket", "teamindia")]

    ours_first = None
    for tid in rumour_topics:
        d = online_detection(db, tid)
        if d and (ours_first is None or d < ours_first):
            ours_first = d
    lead = ((naive_first - ours_first).total_seconds() / 60) if (naive_first and ours_first) else None

    gamma_rows = []
    for g in (0.5, 1.0, 2.0, 4.0):
        with connect(db) as c:
            n_bursts = 0
            for tid in topics:
                ts = [_ts(r[0]).timestamp() for r in c.execute(
                    "SELECT p.created_at FROM topic_assign ta JOIN posts p ON p.platform=ta.platform "
                    "AND p.post_id=ta.post_id WHERE ta.topic_id=?", (tid,))]
                n_bursts += sum(1 for b in kleinberg_bursts(ts, gamma=g) if b.level >= 1)
        gamma_rows.append({"gamma": g, "bursts_level>=1": n_bursts})

    out = {
        "high_priority_threshold": HIGH,
        "alerts_total": len(alerts), "alerts_per_day": round(len(alerts) / days, 2),
        "high_priority_alerts_per_day": round(len(high) / days, 2),
        "naive_alerts_per_day": round(len(naive) / days, 2),
        "injected_event_recall": 1.0 if rumour_high else 0.0,
        "rumour_alert_priority": max((a["priority"] for a in alerts if a["topic_id"] in rumour_topics), default=None),
        "decoy_high_priority_alerts": len(decoy_high),
        "decoy_max_priority": max((a["priority"] for a in alerts if a["topic_id"] in decoy_topics), default=None),
        "naive_decoy_alerts": len(naive_decoy),
        "t0_origin": truth["t0"],
        "ours_first_flag": ours_first.isoformat() if ours_first else None,
        "naive_first_flag": naive_first.isoformat() if naive_first else None,
        "lead_time_minutes": round(lead, 1) if lead is not None else None,
        "minutes_from_origin_to_our_flag": round((ours_first - t0).total_seconds() / 60, 1) if ours_first else None,
        "gamma_sensitivity": gamma_rows,
    }
    lines = [
        f"Seed {truth['scenario_seed']}; {days:.1f} days. High priority = P >= {HIGH}.", "",
        *md_table([
            {"metric": "alerts/day (ours, all)", "value": out["alerts_per_day"]},
            {"metric": "alerts/day (ours, high priority)", "value": out["high_priority_alerts_per_day"]},
            {"metric": "alerts/day (naive keyword z>3)", "value": out["naive_alerts_per_day"]},
            {"metric": "injected rumour alerted at high priority", "value": out["injected_event_recall"]},
            {"metric": "decoy high-priority alerts (ours)", "value": out["decoy_high_priority_alerts"]},
            {"metric": "decoy alerts (naive)", "value": out["naive_decoy_alerts"]},
            {"metric": "our first flag (online Kleinberg, 5-min steps)", "value": out["ours_first_flag"]},
            {"metric": "naive first flag (end of hourly bucket)", "value": out["naive_first_flag"]},
            {"metric": "lead time vs naive (min)", "value": out["lead_time_minutes"]},
        ], ["metric", "value"]),
        "", "## Gamma sensitivity (larger gamma = fewer bursts)", "",
        *md_table(gamma_rows, ["gamma", "bursts_level>=1"]),
        "", "Note: topic assignment is computed on the full replay; the online test re-runs Kleinberg on "
        "growing prefixes of the rumour topic's timestamps.",
    ]
    write_report("alerts", "Signal Cards and burst detection", lines)
    return json.loads(json.dumps(out, default=str))
