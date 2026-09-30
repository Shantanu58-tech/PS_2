from __future__ import annotations
import sqlite3
import networkx as nx


def build_graph(db_path: str, since: str | None = None, organic_only: bool = False) -> nx.DiGraph:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        clauses = []
        params = []
        if since:
            clauses.append("e.ts >= ?")
            params.append(since)
        if organic_only:
            clauses.append(
                "NOT EXISTS (SELECT 1 FROM coord_accounts ca WHERE ca.platform=e.src_platform "
                "AND ca.account_id=e.src_account AND ca.score >= 0.7)"
            )
        clauses.append("e.dst_account NOT LIKE 'post:%'")
        where = "WHERE " + " AND ".join(clauses)
        edges = conn.execute(
            f"SELECT src_account, dst_account, kind, weight, ts FROM edges e {where} LIMIT 100000",
            params,
        ).fetchall()

    G = nx.DiGraph()
    for e in edges:
        src = e["src_account"]
        dst = e["dst_account"]
        if G.has_edge(src, dst):
            G[src][dst]["weight"] += e["weight"]
        else:
            G.add_edge(src, dst, weight=e["weight"], kind=e["kind"], ts=e["ts"])
    return G


def compute_kols(G: nx.DiGraph, top_n: int = 20) -> list[dict]:
    if len(G.nodes) == 0:
        return []
    try:
        pr = nx.pagerank(G, weight="weight")
    except Exception:
        pr = {n: 0.0 for n in G.nodes}
    try:
        bc = nx.betweenness_centrality(G, k=min(200, len(G.nodes)), weight="weight", seed=7)
    except Exception:
        bc = {n: 0.0 for n in G.nodes}
    # Edges run interactor -> original author, so the accounts an author set off
    # (repliers, reposters, and theirs) are its ancestors.
    cascade_size = {n: len(nx.ancestors(G, n)) for n in G.nodes}
    # Cascade influence is the primary KOL signal (PRD 8.E); each component
    # is normalised to [0, 1] so no single scale dominates.
    def norm(d: dict) -> dict:
        top = max(d.values(), default=0) or 1
        return {k: v / top for k, v in d.items()}

    c_n, p_n, b_n = norm(cascade_size), norm(pr), norm(bc)
    score = {n: 0.5 * c_n.get(n, 0) + 0.3 * p_n.get(n, 0) + 0.2 * b_n.get(n, 0) for n in G.nodes}
    ranked = sorted(G.nodes, key=lambda n: score[n], reverse=True)[:top_n]
    return [
        {
            "account_id": n,
            "influence": round(score[n], 4),
            "pagerank": pr.get(n, 0),
            "betweenness": bc.get(n, 0),
            "cascade_size": cascade_size.get(n, 0),
            "role": "originator" if cascade_size.get(n, 0) > G.out_degree(n) else "amplifier",
        }
        for n in ranked
    ]


def graph_payload(G: nx.DiGraph, db_path: str, max_nodes: int = 250) -> dict:
    """Top accounts by weighted degree plus the edges among them, with
    community (greedy modularity), coordination score and KOL metrics."""
    if len(G) == 0:
        return {"nodes": [], "edges": [], "communities": 0, "total_nodes": 0, "total_edges": 0}
    deg = dict(G.degree(weight="weight"))
    keep = sorted(deg, key=lambda n: deg[n], reverse=True)[:max_nodes]
    H = G.subgraph(keep).copy()
    try:
        comms = list(nx.community.greedy_modularity_communities(H.to_undirected(), weight="weight"))
    except Exception:
        comms = [set(H.nodes)]
    community = {n: i for i, c in enumerate(comms) for n in c}
    pr = nx.pagerank(H, weight="weight") if len(H) else {}
    with sqlite3.connect(db_path) as conn:
        coord = dict(conn.execute(
            "SELECT account_id, MAX(score) FROM coord_accounts GROUP BY account_id"
        ).fetchall())
        behaviour = dict(conn.execute(
            "SELECT account_id, MAX(likelihood) FROM account_behaviour GROUP BY account_id"
        ).fetchall())
    nodes = [
        {"id": n, "degree": round(deg[n], 2), "community": community.get(n, 0),
         "pagerank": round(pr.get(n, 0.0), 5), "coord_score": round(coord.get(n, 0.0) or 0.0, 3),
         "coordinated": (coord.get(n) or 0.0) >= 0.7,
         "behaviour_likelihood": round(behaviour.get(n, 0.0) or 0.0, 3)}
        for n in H.nodes
    ]
    edges = [{"source": u, "target": v, "weight": round(d.get("weight", 1.0), 2), "kind": d.get("kind")}
             for u, v, d in H.edges(data=True)]
    return {"nodes": nodes, "edges": edges, "communities": len(comms),
            "total_nodes": G.number_of_nodes(), "total_edges": G.number_of_edges()}


def bridge_accounts(G: nx.DiGraph, top_n: int = 10) -> list[dict]:
    """Accounts connecting otherwise separate communities (betweenness on the
    undirected graph, restricted to nodes touching >1 community)."""
    if len(G) < 3:
        return []
    U = G.to_undirected()
    comms = list(nx.community.greedy_modularity_communities(U, weight="weight"))
    community = {n: i for i, c in enumerate(comms) for n in c}
    bc = nx.betweenness_centrality(U, k=min(300, len(U)), seed=7)
    out = []
    for n in sorted(bc, key=lambda x: bc[x], reverse=True):
        touched = {community[m] for m in U.neighbors(n)} | {community[n]}
        if len(touched) > 1:
            out.append({"account_id": n, "betweenness": round(bc[n], 5), "communities_touched": len(touched)})
        if len(out) >= top_n:
            break
    return out


def spread_frames(db_path: str, topic_id: int, max_frames: int = 48) -> list[dict]:
    """Cumulative spread of a topic by hour: posts, accounts, platforms."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT strftime('%Y-%m-%dT%H:00:00Z', p.created_at) AS h, p.author_id, p.platform "
            "FROM topic_assign ta JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id "
            "WHERE ta.topic_id=? ORDER BY p.created_at",
            (topic_id,),
        ).fetchall()
    frames: list[dict] = []
    accounts: set[str] = set()
    platforms: dict[str, int] = {}
    n = 0
    for h, author, platform in rows:
        n += 1
        accounts.add(author)
        platforms[platform] = platforms.get(platform, 0) + 1
        if frames and frames[-1]["hour"] == h:
            frames[-1].update(posts=n, accounts=len(accounts), platforms=dict(platforms))
        else:
            frames.append({"hour": h, "posts": n, "accounts": len(accounts), "platforms": dict(platforms)})
    return frames[-max_frames:]


def compute_influence(db_path: str, top_n: int = 50) -> dict:
    """Precompute KOL and bridge rankings for the raw and organic-only views,
    each with the account's rank in the other view."""
    import json
    from datetime import datetime, timezone

    views = {v: build_graph(db_path, organic_only=(v == "organic")) for v in ("raw", "organic")}
    kols = {v: compute_kols(G, top_n=max(top_n, 500)) for v, G in views.items()}
    rank = {v: {k["account_id"]: i + 1 for i, k in enumerate(ks)} for v, ks in kols.items()}
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        coord = dict(conn.execute("SELECT account_id, MAX(score) FROM coord_accounts GROUP BY account_id").fetchall())
        for v, G in views.items():
            other = "organic" if v == "raw" else "raw"
            top = []
            for i, k in enumerate(kols[v][:top_n]):
                score = coord.get(k["account_id"]) or 0.0
                top.append({**k, "rank": i + 1, "rank_other_view": rank[other].get(k["account_id"]),
                            "coord_score": round(score, 3), "coordinated": score >= 0.7})
            payload = {"influencers": top, "bridges": bridge_accounts(G, top_n=8), "organic_only": v == "organic"}
            conn.execute("INSERT OR REPLACE INTO influence_cache (view, payload_json, computed_at) VALUES (?,?,?)",
                         (v, json.dumps(payload), now))
        conn.commit()
    return {v: G.number_of_nodes() for v, G in views.items()}


def compute_segments(db_path: str, top_k: int = 4) -> dict:
    """Split the audience into segments for "spread between segments" (PS E):
    segment 0 is the coordinated group; the rest are the largest network
    communities (greedy modularity) of the remaining accounts, named by the
    platform most of their members post on."""
    from collections import Counter
    from datetime import datetime, timezone

    names = {"x": "X", "telegram": "Telegram", "reddit": "Reddit", "youtube": "YouTube",
             "instagram": "Instagram", "facebook": "Facebook"}
    G = build_graph(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        coord = {a for (a,) in conn.execute("SELECT account_id FROM coord_accounts WHERE score >= 0.7")}
        home = {a: p for a, p, _ in conn.execute(
            "SELECT author_id, platform, COUNT(*) AS n FROM posts GROUP BY 1, 2 ORDER BY n")}
        U = G.to_undirected()
        U.remove_nodes_from([n for n in list(U) if n in coord])
        comms = sorted(nx.community.greedy_modularity_communities(U, weight="weight"), key=len, reverse=True)             if len(U) else []
        member = {a: 0 for a in coord}
        for i, c in enumerate(comms):
            for n in c:
                member[n] = i + 1 if i < top_k else -1
        labels = [(0, "Coordinated group", len(coord), now)] if coord else []
        for i, c in enumerate(comms[:top_k]):
            plat = Counter(home.get(n) for n in c if home.get(n)).most_common(1)
            where = names.get(plat[0][0], plat[0][0]) if plat else "mixed"
            labels.append((i + 1, f"Community {'ABCDEFGH'[i]} · mostly {where}", len(c), now))
        conn.execute("DELETE FROM account_segments")
        conn.execute("DELETE FROM segment_labels")
        conn.executemany("INSERT INTO account_segments (account_id, segment) VALUES (?,?)", member.items())
        conn.executemany("INSERT INTO segment_labels (segment, label, size, computed_at) VALUES (?,?,?,?)", labels)
        conn.commit()
    return {"segments": len(labels), "accounts": len(member)}


def segment_spread(db_path: str, topic_id: int) -> dict:
    """Posts per hour on one topic, split by audience segment, plus when each
    segment was first reached and how anxious it was."""
    from datetime import datetime

    with sqlite3.connect(db_path) as conn:
        labels = {s: (lab, size) for s, lab, size in conn.execute("SELECT segment, label, size FROM segment_labels")}
        lo, hi = conn.execute(
            "SELECT MIN(p.created_at), MAX(p.created_at) FROM topic_assign ta JOIN posts p "
            "ON p.platform=ta.platform AND p.post_id=ta.post_id WHERE ta.topic_id=?", (topic_id,)).fetchone()
        span_h = ((datetime.fromisoformat(hi.replace("Z", "+00:00")) - datetime.fromisoformat(lo.replace("Z", "+00:00")))
                  .total_seconds() / 3600) if lo and hi else 0
        # Short-lived narratives get 10-minute buckets so the hand-offs are visible.
        bucket = ("strftime('%Y-%m-%dT%H:', p.created_at) || printf('%02d', "
                  "(CAST(strftime('%M', p.created_at) AS INTEGER) / 10) * 10) || ':00Z'") if span_h < 12             else "strftime('%Y-%m-%dT%H:00:00Z', p.created_at)"
        rows = conn.execute(
            f"SELECT {bucket} AS h, COALESCE(s.segment, -1), "
            "COUNT(*), AVG(pe.anxiety), MIN(p.created_at) "
            "FROM topic_assign ta JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id "
            "LEFT JOIN account_segments s ON s.account_id=p.author_id "
            "LEFT JOIN post_emotions pe ON pe.platform=p.platform AND pe.post_id=p.post_id "
            "WHERE ta.topic_id=? GROUP BY 1, 2 ORDER BY 1", (topic_id,)).fetchall()
    frames: dict[str, dict] = {}
    summary: dict[int, dict] = {}
    for h, seg, n, anx, first in rows:
        key = f"s{seg}" if seg in labels else "other"
        frames.setdefault(h, {"hour": h})
        frames[h][key] = frames[h].get(key, 0) + n
        s = summary.setdefault(seg if seg in labels else -1, {"posts": 0, "anx_sum": 0.0, "first_seen": first})
        s["posts"] += n
        s["anx_sum"] += (anx or 0.0) * n
        s["first_seen"] = min(s["first_seen"], first)
    segments = [{"key": f"s{i}", "label": lab, "size": size} for i, (lab, size) in sorted(labels.items())]
    segments.append({"key": "other", "label": "Other users", "size": None})
    out_summary = []
    for seg, s in summary.items():
        key = f"s{seg}" if seg in labels else "other"
        out_summary.append({"key": key, "label": labels[seg][0] if seg in labels else "Other users",
                            "first_seen": s["first_seen"], "posts": s["posts"],
                            "anxiety": round(s["anx_sum"] / s["posts"], 3) if s["posts"] else None})
    out_summary.sort(key=lambda r: r["first_seen"])
    return {"topic_id": topic_id, "bucket": "10m" if span_h < 12 else "1h", "segments": segments,
            "frames": list(frames.values()), "summary": out_summary}
