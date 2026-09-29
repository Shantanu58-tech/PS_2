from fastapi import APIRouter

from app.api.deps import fetch_all
from app.config import settings

router = APIRouter()


@router.get("/demographics")
async def get_demographics(scope: str = "global", organic_only: bool = False):
    """Aggregate-only cohort estimates. No per-account output exists anywhere
    in the API: buckets under K_ANON are withheld (only their number is
    reported) and released counts carry Laplace noise (DP_EPSILON)."""
    rows = await fetch_all(
        "SELECT dimension, bucket, count FROM demo_aggregates WHERE scope=? AND organic_only=? "
        "ORDER BY dimension, count DESC",
        (scope, int(organic_only)),
    )
    dims: dict[str, dict] = {}
    for r in rows:
        d = dims.setdefault(r["dimension"], {"buckets": [], "suppressed_buckets": 0})
        if r["bucket"] == "suppressed":
            d["suppressed_buckets"] += 1
        else:
            d["buckets"].append({"bucket": r["bucket"], "count": r["count"]})
    computed = await fetch_all("SELECT MAX(computed_at) AS t FROM demo_aggregates")
    return {
        "dimensions": dims,
        "aggregates": [r for r in rows if r["bucket"] != "suppressed"],
        "k_anon": settings.k_anon,
        "dp_epsilon": settings.dp_epsilon,
        "organic_only": organic_only,
        "computed_at": computed[0]["t"] if computed else None,
        "method": "Bio/location cue matching (rule-based), minors excluded, cohort counts only.",
    }
