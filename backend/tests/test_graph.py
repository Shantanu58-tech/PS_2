"""Graph metrics on hand-built graphs (PRD 8.E acceptance) and the GraphStore interface."""
import networkx as nx

from app.analytics.graph import bridge_accounts, compute_kols
from app.analytics.graph_store import Neo4jGraphStore, NetworkXGraphStore, get_graph_store


def test_star_centre_is_top_kol_with_full_cascade():
    G = nx.DiGraph()
    for i in range(10):
        G.add_edge(f"leaf{i}", "hub", weight=1.0)  # leaves reply to / repost the hub
    top = compute_kols(G, top_n=1)[0]
    assert top["account_id"] == "hub" and top["cascade_size"] == 10 and top["role"] == "originator"


def test_chain_cascade_counts_indirect_spread():
    G = nx.DiGraph([("c", "b"), ("b", "a")])
    kols = {k["account_id"]: k for k in compute_kols(G, top_n=3)}
    assert kols["a"]["cascade_size"] == 2 and kols["c"]["cascade_size"] == 0


def test_two_cluster_bridge_ranks_first():
    G = nx.DiGraph()
    for grp in ("a", "b"):
        members = [f"{grp}{i}" for i in range(8)]
        for u in members:
            for v in members:
                if u != v:
                    G.add_edge(u, v, weight=1.0)
    G.add_edge("bridge", "a0", weight=1.0)
    G.add_edge("bridge", "b0", weight=1.0)
    G.add_edge("a1", "bridge", weight=1.0)
    G.add_edge("b1", "bridge", weight=1.0)
    assert bridge_accounts(G, top_n=3)[0]["account_id"] == "bridge"


def test_graph_store_default_and_neo4j_with_mock_driver(analysed_db):
    assert get_graph_store().name == "networkx"
    G = NetworkXGraphStore().graph(analysed_db)
    assert G.number_of_edges() > 0

    class Session:
        def __init__(self, log):
            self.log = log

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def run(self, cypher, **params):
            self.log.append(cypher)
            if cypher.startswith("MATCH (a:Account)-[r:INTERACTS]"):
                return [{"src": "u1", "dst": "u2", "kind": "reply", "weight": 1.0, "ts": "t"}]
            return []

    class Driver:
        def __init__(self):
            self.log: list[str] = []

        def session(self):
            return Session(self.log)

    d = Driver()
    store = Neo4jGraphStore(driver=d)
    assert store.sync(analysed_db)["synced"] > 0
    assert any("UNWIND" in c for c in d.log)
    H = store.graph(analysed_db, organic_only=True)
    assert H.has_edge("u1", "u2") and any("coord_score" in c for c in d.log)


def test_bridge_account_ranks_high_in_scenario(analysed_db, mini_scenario):
    from app.analytics.graph import build_graph

    _, truth = mini_scenario
    ids = [b["account_id"] for b in bridge_accounts(build_graph(analysed_db), top_n=10)]
    assert truth["bridge_account_id"] in ids
