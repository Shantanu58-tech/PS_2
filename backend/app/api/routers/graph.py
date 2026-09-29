import asyncio

from fastapi import APIRouter

from app.analytics.graph import bridge_accounts, compute_kols, graph_payload, spread_frames
from app.analytics.graph_store import get_graph_store
from app.api.deps import fetch_all
from app.config import settings

router = APIRouter()


def _graph(organic_only: bool, since: str | None = None):
    return get_graph_store().graph(settings.db_path, since=since, organic_only=organic_only)


@router.get("/graph")
async def get_graph(organic_only: bool = False, max_nodes: int = 250, since: str | None = None):
    def work() -> dict:
        G = _graph(organic_only, since)
        return {**graph_payload(G, settings.db_path, max_nodes=min(max_nodes, 600)),
                "organic_only": organic_only, "store": get_graph_store().name}

    return await asyncio.to_thread(work)


@router.get("/influencers")
async def get_influencers(limit: int = 20, organic_only: bool = False):
    def work() -> dict:
        G = _graph(organic_only)
        kols = compute_kols(G, top_n=limit)
        # rank in the other view: "who actually influences vs who is pumped"
        other = {k["account_id"]: i + 1 for i, k in enumerate(compute_kols(_graph(not organic_only), top_n=500))}
        for i, k in enumerate(kols):
            k["rank"] = i + 1
            k["rank_other_view"] = other.get(k["account_id"])
        return {"influencers": kols, "bridges": bridge_accounts(G, top_n=8), "organic_only": organic_only}

    result = await asyncio.to_thread(work)
    coord = {r["account_id"]: r["score"] for r in await fetch_all(
        "SELECT account_id, MAX(score) AS score FROM coord_accounts GROUP BY account_id")}
    for k in result["influencers"]:
        k["coord_score"] = round(coord.get(k["account_id"], 0.0), 3)
        k["coordinated"] = coord.get(k["account_id"], 0.0) >= 0.7
    return result


@router.get("/graph/spread")
async def get_spread(topic_id: int | None = None):
    if topic_id is None:
        top = await fetch_all(
            "SELECT topic_id FROM topics ORDER BY coordinated_share DESC, "
            "(SELECT COUNT(*) FROM topic_assign ta WHERE ta.topic_id=topics.topic_id) DESC LIMIT 1")
        if not top:
            return {"topic_id": None, "frames": []}
        topic_id = top[0]["topic_id"]
    frames = await asyncio.to_thread(spread_frames, settings.db_path, topic_id)
    return {"topic_id": topic_id, "frames": frames}


@router.post("/graph/sync")
async def sync_graph_store():
    return await asyncio.to_thread(get_graph_store().sync, settings.db_path)
