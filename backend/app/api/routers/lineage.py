import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.analytics.lineage import build_text_lineage, find_near_duplicate_images, topic_lineage
from app.api.deps import fetch_all, fetch_one
from app.config import settings

router = APIRouter()


@router.get("/lineage")
async def lineage_overview():
    """Lineage for the most coordinated topics plus near-duplicate images (cached per data version)."""
    from app.api.cache import cached

    return await cached("lineage", _lineage_overview)


async def _lineage_overview():
    topics = await fetch_all(
        "SELECT topic_id, label, nature, coordinated_share FROM topics "
        "ORDER BY coordinated_share DESC, (SELECT COUNT(*) FROM topic_assign ta WHERE ta.topic_id=topics.topic_id) DESC "
        "LIMIT 5")
    lineages = []
    for t in topics:
        lin = await asyncio.to_thread(topic_lineage, settings.db_path, t["topic_id"])
        if len(lin.get("platforms", [])) >= 1:
            origin = lin.get("origin_candidate")
            if origin and origin.get("author_id"):
                h = await fetch_one("SELECT handle FROM accounts WHERE account_id=? AND platform=?",
                                    (origin["author_id"], origin.get("platform")))
                origin = {**origin, "handle": (h or {}).get("handle") or origin["author_id"]}
            lineages.append({**t, **lin, "origin_candidate": origin, "chains": lin["chains"][:30]})
    images = await asyncio.to_thread(find_near_duplicate_images, settings.db_path)
    return {"topics": lineages, "image_matches": images, "image_families": image_families(images)}


def image_families(pairs: list[dict]) -> list[dict]:
    """Groups matching pairs into one family per picture: the earliest copy is the original and
    every later copy is listed once, with how far its fingerprint is from the original."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    info: dict[str, dict] = {}
    dist: dict[tuple[str, str], int] = {}
    for p in pairs:
        for side in ("a", "b"):
            info[p[f"media_id_{side}"]] = {"media_id": p[f"media_id_{side}"], "platform": p[f"platform_{side}"],
                                           "first_seen": p[f"first_seen_{side}"], "posts": p[f"posts_{side}"]}
        dist[(p["media_id_a"], p["media_id_b"])] = dist[(p["media_id_b"], p["media_id_a"])] = p["hamming"]
        parent[find(p["media_id_a"])] = find(p["media_id_b"])
    groups: dict[str, list[dict]] = {}
    for mid, m in info.items():
        groups.setdefault(find(mid), []).append(m)
    families = []
    for members in groups.values():
        members.sort(key=lambda m: m["first_seen"] or "")
        orig, copies = members[0], members[1:]
        families.append({
            "original": orig,
            "copies": [{**c, "hamming": dist.get((orig["media_id"], c["media_id"]))} for c in copies],
            "total_posts": sum(m["posts"] or 0 for m in members),
            "platforms": sorted({m["platform"] for m in members if m["platform"]}),
        })
    return sorted(families, key=lambda f: -f["total_posts"])


@router.get("/media/{media_id}")
async def media_file(media_id: str):
    """Serves a stored image (the synthetic meme copies) for thumbnails. Only files inside media_dir."""
    row = await fetch_one("SELECT kind, local_path FROM media WHERE media_id=?", (media_id,))
    if not row or row["kind"] != "image" or not row["local_path"]:
        raise HTTPException(404, "no such image")
    root = Path(settings.media_dir).resolve()
    path = (root / Path(row["local_path"].replace("\\", "/")).name).resolve()
    if path.parent != root or not path.is_file():
        raise HTTPException(404, "image file not available")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/lineage/topic/{topic_id}")
async def lineage_for_topic(topic_id: int):
    return await asyncio.to_thread(topic_lineage, settings.db_path, topic_id)


@router.get("/lineage/images")
async def image_matches(threshold: int = 10):
    return {"matches": await asyncio.to_thread(find_near_duplicate_images, settings.db_path, threshold)}


@router.get("/lineage/{cluster_id}")
async def get_lineage(cluster_id: int):
    return await asyncio.to_thread(build_text_lineage, settings.db_path, cluster_id)
