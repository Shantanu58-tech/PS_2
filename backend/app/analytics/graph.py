from __future__ import annotations
import sqlite3
import json
import networkx as nx
from datetime import datetime, timezone


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
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        edges = conn.execute(
            f"SELECT src_account, dst_account, kind, weight, ts FROM edges {where} LIMIT 100000",
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
        bc = nx.betweenness_centrality(G, k=min(200, len(G.nodes)), weight="weight")
    except Exception:
        bc = {n: 0.0 for n in G.nodes}
    cascade_size = {n: len(nx.descendants(G, n)) for n in list(G.nodes)[:500]}
    ranked = sorted(
        G.nodes,
        key=lambda n: pr.get(n, 0) * 0.4 + cascade_size.get(n, 0) * 0.001 + bc.get(n, 0) * 0.3,
        reverse=True,
    )[:top_n]
    return [
        {
            "account_id": n,
            "pagerank": pr.get(n, 0),
            "betweenness": bc.get(n, 0),
            "cascade_size": cascade_size.get(n, 0),
        }
        for n in ranked
    ]
