from fastapi import APIRouter
import aiosqlite
from app.config import settings

router = APIRouter()


@router.get("/lineage/{cluster_id}")
async def get_lineage(cluster_id: int):
    return {"cluster_id": cluster_id, "nodes": [], "edges": [], "earliest_observed": None}
