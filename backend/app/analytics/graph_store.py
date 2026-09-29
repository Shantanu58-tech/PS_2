"""GraphStore interface (CLAUDE.md rule 6 / Backlog B2).

The interaction graph lives in SQLite `edges`; a GraphStore turns it into a
networkx.DiGraph for analytics. GRAPH_STORE=neo4j mirrors the edges into
Neo4j (sync) and reads the graph back with Cypher, so a production swap is a
config change. NetworkX in-memory remains the default (enough at demo scale).
"""
from __future__ import annotations

import sqlite3
from typing import Any, Protocol

import networkx as nx

from app.analytics.graph import build_graph
from app.config import settings


class GraphStore(Protocol):
    name: str

    def graph(self, db_path: str, since: str | None = None, organic_only: bool = False) -> nx.DiGraph: ...

    def sync(self, db_path: str) -> dict[str, Any]: ...


class NetworkXGraphStore:
    name = "networkx"

    def graph(self, db_path: str, since: str | None = None, organic_only: bool = False) -> nx.DiGraph:
        return build_graph(db_path, since=since, organic_only=organic_only)

    def sync(self, db_path: str) -> dict[str, Any]:
        return {"store": self.name, "synced": 0, "note": "reads SQLite directly"}


class Neo4jGraphStore:
    name = "neo4j"

    def __init__(self, driver: Any | None = None) -> None:
        if driver is None:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
            )
        self._driver = driver

    def sync(self, db_path: str, batch: int = 1000) -> dict[str, Any]:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT src_platform, src_account, dst_platform, dst_account, kind, ts, weight FROM edges"
            ).fetchall()
            coord = conn.execute(
                "SELECT platform, account_id, MAX(score) FROM coord_accounts GROUP BY platform, account_id"
            ).fetchall()
        with self._driver.session() as s:
            s.run("MATCH (n:Account) DETACH DELETE n")
            for i in range(0, len(rows), batch):
                s.run(
                    "UNWIND $rows AS r "
                    "MERGE (a:Account {id: r[1], platform: r[0]}) "
                    "MERGE (b:Account {id: r[3], platform: r[2]}) "
                    "CREATE (a)-[:INTERACTS {kind: r[4], ts: r[5], weight: r[6]}]->(b)",
                    rows=[list(r) for r in rows[i:i + batch]],
                )
            s.run(
                "UNWIND $rows AS r MATCH (a:Account {id: r[1], platform: r[0]}) SET a.coord_score = r[2]",
                rows=[list(r) for r in coord],
            )
        return {"store": self.name, "synced": len(rows)}

    def graph(self, db_path: str, since: str | None = None, organic_only: bool = False) -> nx.DiGraph:
        where = []
        if since:
            where.append("r.ts >= $since")
        if organic_only:
            where.append("coalesce(a.coord_score, 0) < 0.7")
        cypher = (
            "MATCH (a:Account)-[r:INTERACTS]->(b:Account) "
            + ("WHERE " + " AND ".join(where) + " " if where else "")
            + "RETURN a.id AS src, b.id AS dst, r.kind AS kind, r.weight AS weight, r.ts AS ts"
        )
        G = nx.DiGraph()
        with self._driver.session() as s:
            for rec in s.run(cypher, since=since):
                src, dst = rec["src"], rec["dst"]
                if G.has_edge(src, dst):
                    G[src][dst]["weight"] += rec["weight"]
                else:
                    G.add_edge(src, dst, weight=rec["weight"], kind=rec["kind"], ts=rec["ts"])
        return G


def get_graph_store() -> GraphStore:
    if settings.graph_store == "neo4j":
        return Neo4jGraphStore()
    return NetworkXGraphStore()
