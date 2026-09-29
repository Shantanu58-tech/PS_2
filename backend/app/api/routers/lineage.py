import asyncio

from fastapi import APIRouter

from app.analytics.lineage import build_text_lineage, find_near_duplicate_images, topic_lineage
from app.api.deps import fetch_all
from app.config import settings

router = APIRouter()


@router.get("/lineage")
async def lineage_overview():
    """Lineage for the most coordinated topics plus near-duplicate images."""
    topics = await fetch_all(
        "SELECT topic_id, label, nature, coordinated_share FROM topics "
        "ORDER BY coordinated_share DESC, (SELECT COUNT(*) FROM topic_assign ta WHERE ta.topic_id=topics.topic_id) DESC "
        "LIMIT 5")
    lineages = []
    for t in topics:
        lin = await asyncio.to_thread(topic_lineage, settings.db_path, t["topic_id"])
        if len(lin.get("platforms", [])) >= 1:
            lineages.append({**t, **lin, "chains": lin["chains"][:30]})
    images = await asyncio.to_thread(find_near_duplicate_images, settings.db_path)
    return {"topics": lineages, "image_matches": images}


@router.get("/lineage/topic/{topic_id}")
async def lineage_for_topic(topic_id: int):
    return await asyncio.to_thread(topic_lineage, settings.db_path, topic_id)


@router.get("/lineage/images")
async def image_matches(threshold: int = 10):
    return {"matches": await asyncio.to_thread(find_near_duplicate_images, settings.db_path, threshold)}


@router.get("/lineage/{cluster_id}")
async def get_lineage(cluster_id: int):
    return await asyncio.to_thread(build_text_lineage, settings.db_path, cluster_id)
