"""Cross-platform narrative lineage.

For a topic (or a coordination cluster) we report the *earliest observed*
post per platform, the platform hand-offs in time order, explicit
repost/forward chains, and near-duplicate images (perceptual hash, Hamming
distance <= threshold). "Earliest observed" means earliest in monitored
sources - the true origin may be outside coverage.
"""
from __future__ import annotations

import sqlite3

import imagehash
from PIL import Image

CAVEAT = "Earliest observed in monitored sources; true origin may be outside coverage."


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
            """
            SELECT m.media_id, m.phash, MIN(p.created_at) AS first_seen,
                   (SELECT p2.platform FROM post_media pm2 JOIN posts p2
                      ON p2.platform=pm2.platform AND p2.post_id=pm2.post_id
                    WHERE pm2.media_id=m.media_id ORDER BY p2.created_at LIMIT 1) AS platform,
                   COUNT(pm.post_id) AS n_posts
            FROM media m
            JOIN post_media pm ON pm.media_id=m.media_id
            JOIN posts p ON p.platform=pm.platform AND p.post_id=pm.post_id
            WHERE m.phash IS NOT NULL
            GROUP BY m.media_id
            """
        ).fetchall()
    pairs = []
    hashes = [(r["media_id"], phash_hex_to_int(r["phash"]), r["platform"], r["first_seen"], r["n_posts"])
              for r in rows]
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            d = hamming(hashes[i][1], hashes[j][1])
            if d <= threshold:
                a, b = sorted((hashes[i], hashes[j]), key=lambda h: h[3])
                pairs.append({
                    "media_id_a": a[0], "platform_a": a[2], "first_seen_a": a[3], "posts_a": a[4],
                    "media_id_b": b[0], "platform_b": b[2], "first_seen_b": b[3], "posts_b": b[4],
                    "hamming": d, "threshold": threshold,
                })
    return pairs


def _lineage_from_posts(conn: sqlite3.Connection, posts: list[sqlite3.Row]) -> dict:
    if not posts:
        return {"platforms": [], "hops": [], "chains": [], "earliest_observed": None, "caveat": CAVEAT}
    first_by_platform: dict[str, sqlite3.Row] = {}
    counts: dict[str, int] = {}
    for r in posts:
        counts[r["platform"]] = counts.get(r["platform"], 0) + 1
        if r["platform"] not in first_by_platform:
            first_by_platform[r["platform"]] = r
    ordered = sorted(first_by_platform.values(), key=lambda r: r["created_at"])
    t0 = ordered[0]["created_at"]
    platforms = [
        {"platform": r["platform"], "first_post_id": r["post_id"], "first_seen": r["created_at"],
         "author_id": r["author_id"], "text": r["text"][:280], "n_posts": counts[r["platform"]],
         "has_media": bool(conn.execute(
             "SELECT 1 FROM post_media WHERE platform=? AND post_id=?", (r["platform"], r["post_id"])
         ).fetchone())}
        for r in ordered
    ]
    hops = [
        {"from": a["platform"], "to": b["platform"], "from_ts": a["created_at"], "to_ts": b["created_at"]}
        for a, b in zip(ordered, ordered[1:])
    ]
    ids = {r["post_id"] for r in posts}
    chains = [
        {"src": r["origin_post_id"], "dst": r["post_id"], "platform": r["platform"], "ts": r["created_at"]}
        for r in posts if r["origin_post_id"] and r["origin_post_id"] in ids
    ][:200]
    return {"platforms": platforms, "hops": hops, "chains": chains, "earliest_observed": t0,
            "origin_candidate": platforms[0], "n_posts": len(posts), "caveat": CAVEAT}


_POST_COLS = "p.platform, p.post_id, p.author_id, p.text, p.created_at, p.origin_post_id"


def topic_lineage(db_path: str, topic_id: int) -> dict:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        posts = conn.execute(
            f"SELECT {_POST_COLS} FROM topic_assign ta JOIN posts p "
            "ON p.platform=ta.platform AND p.post_id=ta.post_id WHERE ta.topic_id=? ORDER BY p.created_at",
            (topic_id,),
        ).fetchall()
        # widen with explicit forward/repost ancestors that fell outside the topic
        origins = {r["origin_post_id"] for r in posts if r["origin_post_id"]} - {r["post_id"] for r in posts}
        if origins:
            q = ",".join("?" * len(origins))
            posts = sorted(
                list(posts) + conn.execute(
                    f"SELECT {_POST_COLS} FROM posts p WHERE p.post_id IN ({q})", tuple(origins)
                ).fetchall(),
                key=lambda r: r["created_at"],
            )
        return {"topic_id": topic_id, **_lineage_from_posts(conn, posts)}


def build_text_lineage(db_path: str, cluster_id: int, threshold: float = 0.82) -> dict:
    """Lineage of the posts written by a coordination cluster's accounts."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT topic_id FROM coord_clusters WHERE cluster_id=?", (cluster_id,)).fetchone()
        if not row:
            return {"cluster_id": cluster_id, "platforms": [], "hops": [], "chains": [],
                    "earliest_observed": None, "caveat": CAVEAT}
        posts = conn.execute(
            f"SELECT {_POST_COLS} FROM topic_assign ta JOIN posts p "
            "ON p.platform=ta.platform AND p.post_id=ta.post_id "
            "JOIN coord_accounts ca ON ca.platform=p.platform AND ca.account_id=p.author_id "
            "AND ca.cluster_id=? WHERE ta.topic_id=? ORDER BY p.created_at",
            (cluster_id, row["topic_id"]),
        ).fetchall()
        return {"cluster_id": cluster_id, "topic_id": row["topic_id"], **_lineage_from_posts(conn, posts)}
