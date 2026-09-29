from __future__ import annotations
import imagehash
import sqlite3
import numpy as np
from pathlib import Path
from PIL import Image


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def phash_image(path: str) -> str | None:
    try:
        img = Image.open(path).convert("RGB")
        return str(imagehash.phash(img))
    except Exception:
        return None


def phash_hex_to_int(phash_str: str) -> int:
    try:
        return int(phash_str, 16)
    except Exception:
        return 0


def find_near_duplicate_images(db_path: str, threshold: int = 10) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT media_id, phash, platform FROM media WHERE phash IS NOT NULL"
        ).fetchall()

    if len(rows) < 2:
        return []

    pairs = []
    hashes = [(r["media_id"], phash_hex_to_int(r["phash"]), r["platform"]) for r in rows]
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            d = hamming(hashes[i][1], hashes[j][1])
            if d <= threshold:
                pairs.append({
                    "media_id_a": hashes[i][0],
                    "media_id_b": hashes[j][0],
                    "platform_a": hashes[i][2],
                    "platform_b": hashes[j][2],
                    "hamming": d,
                })
    return pairs


def build_text_lineage(db_path: str, cluster_id: int, threshold: float = 0.82) -> dict:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        posts = conn.execute(
            "SELECT p.platform, p.post_id, p.text, p.created_at, p.origin_post_id "
            "FROM posts p "
            "JOIN coord_accounts ca ON ca.platform=p.platform AND ca.account_id=p.author_id "
            "WHERE ca.cluster_id=? ORDER BY p.created_at",
            (cluster_id,),
        ).fetchall()

    if not posts:
        return {"nodes": [], "edges": [], "earliest_observed": None}

    earliest = posts[0]["created_at"] if posts else None
    nodes = [{"id": f"{r['platform']}_{r['post_id']}", "platform": r["platform"], "ts": r["created_at"]} for r in posts]
    edges = []
    for r in posts:
        if r["origin_post_id"]:
            edges.append({"src": r["origin_post_id"], "dst": f"{r['platform']}_{r['post_id']}", "kind": "forward"})

    return {
        "nodes": nodes,
        "edges": edges,
        "earliest_observed": earliest,
        "caveat": "Earliest in monitored sources; true origin may be outside coverage.",
    }
