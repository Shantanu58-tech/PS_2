import asyncio

from fastapi import APIRouter

from app.analytics.graph import graph_payload, segment_spread, spread_frames
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
    """KOLs + bridges, precomputed by the analytics `influence` stage."""
    import json

    from app.analytics.graph import compute_influence

    view = "organic" if organic_only else "raw"
    row = await fetch_all("SELECT payload_json FROM influence_cache WHERE view=?", (view,))
    if not row:
        await asyncio.to_thread(compute_influence, settings.db_path)
        row = await fetch_all("SELECT payload_json FROM influence_cache WHERE view=?", (view,))
    payload = json.loads(row[0]["payload_json"]) if row else {"influencers": [], "bridges": []}
    payload["influencers"] = payload["influencers"][:limit]
    return payload


@router.get("/graph/spread")
async def get_spread(topic_id: int | None = None):
    if topic_id is None:
        top = await fetch_all(
            "SELECT topic_id FROM topics ORDER BY nature='manufactured' DESC, "
            "(SELECT COUNT(*) FROM topic_assign ta WHERE ta.topic_id=topics.topic_id) DESC LIMIT 1")
        if not top:
            return {"topic_id": None, "frames": []}
        topic_id = top[0]["topic_id"]
    frames = await asyncio.to_thread(spread_frames, settings.db_path, topic_id)
    return {"topic_id": topic_id, "frames": frames}


@router.post("/graph/sync")
async def sync_graph_store():
    return await asyncio.to_thread(get_graph_store().sync, settings.db_path)


@router.get("/graph/segment-spread")
async def get_segment_spread(topic_id: int | None = None):
    """How a topic moved between audience segments over time (PS E)."""
    if topic_id is None:
        top = await fetch_all(
            "SELECT topic_id FROM topics ORDER BY nature='manufactured' DESC, "
            "(SELECT COUNT(*) FROM topic_assign ta WHERE ta.topic_id=topics.topic_id) DESC LIMIT 1")
        if not top:
            return {"topic_id": None, "segments": [], "frames": [], "summary": []}
        topic_id = top[0]["topic_id"]
    return await asyncio.to_thread(segment_spread, settings.db_path, topic_id)
