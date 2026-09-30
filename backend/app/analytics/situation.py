"""National situation picture for the first page (PS A–E at a glance).

Everything here is aggregate and derived from stored data:
- sectors: each topic is assigned to one sector by keyword evidence in its
  label, keywords and posts (a transparent rule, not a model);
- states: posts are attributed to a state only through the author's public
  profile location, and a state is released only when at least K_ANON distinct
  accounts back it (no per-account geography ever leaves this module);
- narratives: topics pushed by coordinated accounts, with the coordinated
  group and its most active amplifiers (behaviour, not identity);
- hot topics: the biggest bursts, with raw vs organic anxiety.
The result is cached per data version because it scans every post.
"""
from __future__ import annotations

import re
import sqlite3
import threading
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from app.analytics.demographics import _infer_state
from app.config import settings

HIGH_PRIORITY = 70

SECTORS: list[dict[str, Any]] = [
    {"id": "infra", "name": "Critical Infrastructure", "keywords": [
        "dam", "reservoir", "breach", "evacuat", "bhago", "toot", "bridge", "power grid", "blackout",
        "pipeline", "railway", "nuclear", "damcrack", "floodalert", "varunapur"]},
    {"id": "disaster", "name": "Weather & Disaster", "keywords": [
        "rain", "monsoon", "baarish", "storm", "cyclone", "flood", "earthquake", "landslide", "heatwave",
        "power cut", "paani", "waterlog", "weather"]},
    {"id": "economy", "name": "Economy & Prices", "keywords": [
        "petrol", "diesel", "fuel", "price", "mehenga", "mehnga", "inflation", "tax", "stock", "market",
        "rupee", "upi", "bank", "gst", "salary"]},
    {"id": "education", "name": "Education & Exams", "keywords": [
        "exam", "neet", "jee", "board", "result", "paper leak", "student", "padhai", "college", "school",
        "boardexams"]},
    {"id": "civic", "name": "Governance & Civic", "keywords": [
        "government", "sarkar", "election", "policy", "traffic", "metro", "road", "sadak", "municipal",
        "police", "jam", "commute", "civic"]},
    {"id": "health", "name": "Public Health", "keywords": [
        "hospital", "vaccine", "covid", "dengue", "health", "doctor", "medicine", "dawai", "contaminat",
        "outbreak"]},
    {"id": "defence", "name": "Defence & Security", "keywords": [
        "army", "border", " lac ", " loc ", "terror", "militant", "military", "jawan", "defence", "drone",
        "infiltrat", "ceasefire"]},
    {"id": "tech", "name": "Technology & Telecom", "keywords": [
        " ai ", "app", "startup", "tech", "internet", "5g", "cyber", "software", "launched", "gadget"]},
    {"id": "culture", "name": "Sports, Culture & Media", "keywords": [
        "cricket", "match", "teamindia", "indvsaus", "kohli", "six", "wicket", "bollywood", "film", "movie",
        "picture", "diwali", "holi", "festival", "song", "celebrat", "foodie", "newrelease"]},
]
SECTOR_NAME = {s["id"]: s["name"] for s in SECTORS} | {"other": "Other"}

_lock = threading.Lock()
_cache: dict[str, Any] = {}


def _sector_for(text: str) -> str:
    t = " " + re.sub(r"\s+", " ", text.lower()) + " "
    scores = {s["id"]: sum(t.count(k) for k in s["keywords"]) for s in SECTORS}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "other"


def _level(sector: dict) -> str:
    if sector["posts"] == 0:
        return "quiet"
    if sector["priority_alerts"] > 0 and sector["manufactured"] > 0:
        return "critical"
    if sector["manufactured"] > 0 or sector["coordinated_share"] >= 0.10:
        return "elevated"
    if sector["coordinated_share"] >= 0.02 or sector["max_burst"] >= 3:
        return "watch"
    return "normal"


def _version(conn: sqlite3.Connection) -> str:
    n, end = conn.execute("SELECT COUNT(*), MAX(created_at) FROM posts").fetchone()
    a = conn.execute("SELECT COUNT(*), COALESCE(MAX(alert_id), 0) FROM alerts").fetchone()
    t = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
    return f"{n}:{end}:{a[0]}:{a[1]}:{t}"


def situation(db_path: str | None = None) -> dict[str, Any]:
    db_path = db_path or settings.db_path
    with _lock:
        with sqlite3.connect(db_path) as conn:
            ver = _version(conn)
            if _cache.get("ver") == (db_path, ver):
                return _cache["value"]
            value = _compute(conn)
        _cache.update(ver=(db_path, ver), value=value)
        return value


def _compute(conn: sqlite3.Connection) -> dict[str, Any]:  # noqa: C901 - one pass, many aggregates
    k_anon = settings.k_anon
    coord = {(p, a): s for p, a, s in conn.execute(
        "SELECT platform, account_id, MAX(score) FROM coord_accounts GROUP BY 1, 2")}
    flagged = {key for key, s in coord.items() if s >= 0.7}
    state_of = {(p, a): _infer_state(loc) for p, a, loc in conn.execute(
        "SELECT platform, account_id, location_text FROM accounts")}
    topics = {r[0]: {"topic_id": r[0], "label": r[1], "keywords": r[2] or "", "nature": r[3],
                     "coordinated_share": r[4] or 0.0, "first_seen": r[5]}
              for r in conn.execute("SELECT topic_id, label, keywords, nature, coordinated_share, first_seen FROM topics")}
    bursts = dict(conn.execute("SELECT topic_id, MAX(level) FROM bursts GROUP BY 1").fetchall())
    alerts = [dict(zip(("alert_id", "topic_id", "priority", "status"), r)) for r in conn.execute(
        "SELECT alert_id, topic_id, priority, status FROM alerts ORDER BY priority DESC")]
    best_alert = {}
    for a in alerts:
        best_alert.setdefault(a["topic_id"], a)

    # one pass over posts joined with topic and anxiety
    per_topic: dict[int, dict[str, Any]] = defaultdict(lambda: {
        "posts": 0, "coord_posts": 0, "accounts": set(), "platforms": Counter(), "anx": 0.0, "anx_n": 0,
        "anx_org": 0.0, "anx_org_n": 0, "states": defaultdict(set), "state_posts": Counter(),
        "amplifiers": Counter(), "text": [], "reach_states": defaultdict(set), "reach_state_posts": Counter(),
        "reactions": 0, "react_anx": 0.0, "react_anx_n": 0})
    per_state: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "posts": 0, "coord_posts": 0, "accounts": set(), "anx": 0.0, "anx_n": 0, "topics": Counter(),
        "manufactured_posts": 0, "platforms": Counter()})
    platforms: Counter[str] = Counter()
    total_posts = 0
    topic_of = {(p, pid): tid for p, pid, tid in conn.execute("SELECT platform, post_id, topic_id FROM topic_assign")}
    manufactured_ids = {tid for tid, t in topics.items() if t["nature"] == "manufactured"}
    rows = conn.execute(
        "SELECT p.platform, p.author_id, p.text, ta.topic_id, pe.anxiety, p.parent_post_id FROM posts p "
        "LEFT JOIN topic_assign ta ON ta.platform=p.platform AND ta.post_id=p.post_id "
        "LEFT JOIN post_emotions pe ON pe.platform=p.platform AND pe.post_id=p.post_id")
    for platform, author, text, topic_id, anxiety, parent in rows:
        total_posts += 1
        platforms[platform] += 1
        key = (platform, author)
        is_coord = key in flagged
        st = state_of.get(key)
        # exposure: a post in a manufactured narrative, or a reply to one
        parent_tid = topic_of.get((platform, parent)) if parent else None
        exposure = topic_id if topic_id in manufactured_ids else parent_tid if parent_tid in manufactured_ids else None
        if exposure is not None:
            e = per_topic[exposure]
            if exposure != topic_id:
                e["reactions"] += 1
                if anxiety is not None:
                    e["react_anx"] += anxiety
                    e["react_anx_n"] += 1
            if st:
                e["reach_states"][st].add(key)
                e["reach_state_posts"][st] += 1
        if st:
            s = per_state[st]
            s["posts"] += 1
            s["coord_posts"] += is_coord
            s["accounts"].add(key)
            s["platforms"][platform] += 1
            if anxiety is not None:
                s["anx"] += anxiety
                s["anx_n"] += 1
            if topic_id is not None:
                s["topics"][topic_id] += 1
            if exposure is not None:
                s["manufactured_posts"] += 1
        if topic_id is None:
            continue
        t = per_topic[topic_id]
        t["posts"] += 1
        t["coord_posts"] += is_coord
        t["accounts"].add(key)
        t["platforms"][platform] += 1
        if is_coord:
            t["amplifiers"][key] += 1
        if anxiety is not None:
            t["anx"] += anxiety
            t["anx_n"] += 1
            if not is_coord:
                t["anx_org"] += anxiety
                t["anx_org_n"] += 1
        if st:
            t["states"][st].add(key)
            t["state_posts"][st] += 1
        if len(t["text"]) < 40:
            t["text"].append(text or "")

    # sectors
    topic_sector: dict[int, str] = {}
    for tid, t in topics.items():
        agg = per_topic.get(tid)
        blob = f"{t['label']} {t['keywords']} " + " ".join(agg["text"] if agg else [])
        topic_sector[tid] = _sector_for(blob)
    sectors: dict[str, dict[str, Any]] = {sid: {
        "id": sid, "name": SECTOR_NAME[sid], "posts": 0, "coord_posts": 0, "accounts": set(), "topics": 0,
        "manufactured": 0, "priority_alerts": 0, "max_burst": 0, "anx": 0.0, "anx_n": 0, "lead": None,
        "platforms": Counter()} for sid in [*(s["id"] for s in SECTORS), "other"]}
    for tid, agg in per_topic.items():
        if agg["posts"] == 0:
            continue
        sec = sectors[topic_sector.get(tid, "other")]
        sec["posts"] += agg["posts"]
        sec["coord_posts"] += agg["coord_posts"]
        sec["accounts"] |= agg["accounts"]
        sec["topics"] += 1
        sec["anx"] += agg["anx"]
        sec["anx_n"] += agg["anx_n"]
        sec["platforms"].update(agg["platforms"])
        sec["max_burst"] = max(sec["max_burst"], bursts.get(tid) or 0)
        manufactured = topics[tid]["nature"] == "manufactured"
        sec["manufactured"] += manufactured
        a = best_alert.get(tid)
        if a and a["priority"] >= HIGH_PRIORITY:
            sec["priority_alerts"] += 1
        rank = (manufactured, a["priority"] if a else 0, agg["posts"])
        if sec["lead"] is None or rank > sec["lead"][0]:
            sec["lead"] = (rank, tid)
    sector_out = []
    for sec in sectors.values():
        if sec["id"] == "other" and sec["posts"] == 0:
            continue
        lead = sec["lead"][1] if sec["lead"] else None
        row = {
            "id": sec["id"], "name": sec["name"], "posts": sec["posts"], "accounts": len(sec["accounts"]),
            "topics": sec["topics"], "manufactured": sec["manufactured"], "priority_alerts": sec["priority_alerts"],
            "max_burst": sec["max_burst"],
            "coordinated_share": round(sec["coord_posts"] / sec["posts"], 4) if sec["posts"] else 0.0,
            "anxiety": round(sec["anx"] / sec["anx_n"], 3) if sec["anx_n"] else None,
            "lead_topic": {"topic_id": lead, "label": topics[lead]["label"],
                           "nature": topics[lead]["nature"]} if lead is not None else None,
            "platforms": [p for p, _ in sec["platforms"].most_common(4)],
        }
        row["level"] = _level(row)
        sector_out.append(row)
    order = {"critical": 0, "elevated": 1, "watch": 2, "normal": 3, "quiet": 4}
    sector_out.sort(key=lambda s: (order[s["level"]], -s["posts"]))

    # states (k-anonymous)
    state_out = []
    for st, s in per_state.items():
        released = len(s["accounts"]) >= k_anon
        top = s["topics"].most_common(1)
        state_out.append({
            "state": st, "released": released,
            "posts": s["posts"] if released else None, "accounts": len(s["accounts"]) if released else None,
            "coordinated_share": round(s["coord_posts"] / s["posts"], 4) if released and s["posts"] else None,
            "anxiety": round(s["anx"] / s["anx_n"], 3) if released and s["anx_n"] else None,
            "manufactured_share": round(s["manufactured_posts"] / s["posts"], 4) if released and s["posts"] else None,
            "top_topic": {"topic_id": top[0][0], "label": topics[top[0][0]]["label"],
                          "sector": topic_sector.get(top[0][0], "other")} if released and top else None,
            "platforms": [p for p, _ in s["platforms"].most_common(3)] if released else [],
            "top_topics": [{"topic_id": tid, "label": topics[tid]["label"], "posts": n,
                            "sector": topic_sector.get(tid, "other"), "nature": topics[tid]["nature"]}
                           for tid, n in s["topics"].most_common(5)] if released else [],
        })
    state_out.sort(key=lambda s: -(s["posts"] or 0))
    located = sum(s["posts"] or 0 for s in state_out)

    # narratives pushed by coordinated accounts
    clusters = conn.execute(
        "SELECT cluster_id, topic_id, score, n_accounts, n_posts, sync FROM coord_clusters").fetchall() \
        if conn.execute("SELECT name FROM sqlite_master WHERE name='coord_clusters'").fetchone() else []
    by_topic_cluster: dict[int, list[dict]] = defaultdict(list)
    for cid, tid, score, n_acc, n_posts, sync in clusters:
        by_topic_cluster[tid].append({"cluster_id": cid, "score": round(score or 0, 3), "accounts": n_acc,
                                      "posts": n_posts, "sync": round(sync or 0, 3)})
    candidates = sorted(
        (tid for tid, agg in per_topic.items() if agg["posts"] and (agg["coord_posts"] > 0 or tid in manufactured_ids)),
        key=lambda tid: (topics[tid]["nature"] == "manufactured", per_topic[tid]["coord_posts"]), reverse=True)
    narratives = []
    for tid in candidates[:6]:
        agg, t = per_topic[tid], topics[tid]
        a = best_alert.get(tid)
        states_top = [st for st, _ in agg["reach_state_posts"].most_common() if len(agg["reach_states"][st]) >= k_anon][:4]
        narratives.append({
            "topic_id": tid, "label": t["label"], "nature": t["nature"], "sector": topic_sector.get(tid, "other"),
            "posts": agg["posts"], "accounts": len(agg["accounts"]),
            "coordinated_share": round(agg["coord_posts"] / agg["posts"], 4) if agg["posts"] else 0.0,
            "first_seen": t["first_seen"], "platforms": [p for p, _ in agg["platforms"].most_common()],
            "groups": by_topic_cluster.get(tid, []),
            "amplifiers": [{"account_id": acc, "platform": plat, "posts": n}
                           for (plat, acc), n in agg["amplifiers"].most_common(4)],
            "states": states_top, "reactions": agg["reactions"],
            "reaction_anxiety": round(agg["react_anx"] / agg["react_anx_n"], 3) if agg["react_anx_n"] else None,
            "alert": {"alert_id": a["alert_id"], "priority": round(a["priority"], 1), "status": a["status"]} if a else None,
        })

    # hot topics: busiest hour compared with the topic's usual hourly rate over the whole window
    series: dict[int, list[int]] = defaultdict(list)
    for tid, n in conn.execute("SELECT topic_id, count_all FROM topic_series"):
        series[tid].append(n or 0)
    lo, hi = conn.execute("SELECT MIN(created_at), MAX(created_at) FROM posts").fetchone()
    span_h = max(1.0, (datetime.fromisoformat(hi.replace("Z", "+00:00"))
                       - datetime.fromisoformat(lo.replace("Z", "+00:00"))).total_seconds() / 3600) if lo else 1.0
    hot = []
    for tid, counts in series.items():
        if tid not in per_topic or not counts or per_topic[tid]["posts"] < 30:
            continue
        agg = per_topic[tid]
        usual = max(1.0, agg["posts"] / span_h)
        spike = max(counts) / usual
        hot.append({
            "topic_id": tid, "label": topics[tid]["label"], "nature": topics[tid]["nature"],
            "sector": topic_sector.get(tid, "other"), "posts": agg["posts"], "spike": round(spike, 1),
            "burst_level": bursts.get(tid) or 0,
            "coordinated_share": round(agg["coord_posts"] / agg["posts"], 4) if agg["posts"] else 0.0,
            "anxiety": round(agg["anx"] / agg["anx_n"], 3) if agg["anx_n"] else None,
            "anxiety_organic": round(agg["anx_org"] / agg["anx_org_n"], 3) if agg["anx_org_n"] else None,
            "platforms": [p for p, _ in agg["platforms"].most_common(3)],
        })
    hot.sort(key=lambda h: h["spike"], reverse=True)

    # headline KPIs
    n_rec, n_cp = conn.execute(
        "SELECT (SELECT COUNT(*) FROM raw_records), (SELECT COUNT(*) FROM ledger_checkpoints)").fetchone()
    start, end = conn.execute("SELECT MIN(created_at), MAX(created_at) FROM posts").fetchone()
    high = [a for a in alerts if a["priority"] >= HIGH_PRIORITY]
    manufactured = [tid for tid, t in topics.items() if t["nature"] == "manufactured"]
    sync_vals = [c["sync"] for cs in by_topic_cluster.values() for c in cs]
    top_alert = high[0] if high else (alerts[0] if alerts else None)
    kpis = {
        "posts_secured": n_rec, "checkpoints": n_cp,
        "priority_alerts": len(high), "signals": len(alerts),
        "top_alert": ({"alert_id": top_alert["alert_id"], "topic_id": top_alert["topic_id"],
                       "label": topics.get(top_alert["topic_id"], {}).get("label"), "status": top_alert["status"]}
                      if top_alert else None),
        "coordinated_accounts": len(flagged), "sync_index": round(max(sync_vals), 2) if sync_vals else None,
        "manufactured_trends": len(manufactured), "topics": len(topics),
        "top_manufactured": topics[narratives[0]["topic_id"]]["label"] if narratives else None,
        "platforms": len(platforms), "states_released": sum(1 for s in state_out if s["released"]),
    }

    # plain-language situation report
    lead = narratives[0] if narratives and narratives[0]["nature"] == "manufactured" else None
    sitrep = {
        "as_of": end, "window_start": start, "posts": total_posts, "platforms": len(platforms),
        "located_share": round(located / total_posts, 3) if total_posts else 0.0,
        "level": "critical" if any(s["level"] == "critical" for s in sector_out) else
                 "elevated" if any(s["level"] == "elevated" for s in sector_out) else "normal",
        "lead": {
            "topic_id": lead["topic_id"], "label": lead["label"], "sector": SECTOR_NAME[lead["sector"]],
            "coordinated_share": lead["coordinated_share"], "posts": lead["posts"],
            "group_accounts": max((g["accounts"] for g in lead["groups"]), default=len(lead["amplifiers"])),
            "platforms": lead["platforms"], "states": lead["states"],
            "first_platform": _first_platform(conn, lead["topic_id"]),
            "reactions": lead["reactions"], "reaction_anxiety": lead["reaction_anxiety"],
        } if lead else None,
    }
    return {"sitrep": sitrep, "kpis": kpis, "sectors": sector_out, "states": state_out,
            "narratives": narratives, "hot_topics": hot[:8], "k_anon": k_anon,
            "sector_names": SECTOR_NAME, "topic_sectors": {str(tid): sec for tid, sec in topic_sector.items()},
            "computed_at": datetime.utcnow().isoformat() + "Z"}


def _first_platform(conn: sqlite3.Connection, topic_id: int) -> str | None:
    row = conn.execute(
        "SELECT p.platform FROM topic_assign ta JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id "
        "WHERE ta.topic_id=? ORDER BY p.created_at LIMIT 1", (topic_id,)).fetchone()
    return row[0] if row else None
