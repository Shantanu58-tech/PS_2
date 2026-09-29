"""Coordinated-behaviour detection.

Stage 1 (cluster): per narrative cluster (near-identical text or identical
hashtag set in a 30-min window - PRD 8.V2), the timing null-model signals (binned normalised
entropy Hn, Goh-Barabasi burstiness B, synchrony S) plus the near-duplicate
ratio give a logistic cluster score.

Stage 2 (account): inside a flagged cluster each account is scored on its own
behaviour, so organic users who merely reply to a campaign are not labelled:
  * co_sync   - share of its posts with a near-duplicate post by a *different*
                account within SYNC_WINDOW seconds,
  * regularity - max(0, -B) of its own inter-post gaps (scripted cadence),
  * repetition - min(1, (n_posts-1)/3).
Scores >= 0.7 are treated as coordinated by the "organic only" views.
"""
from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone

import numpy as np

from app.analytics.burst import burstiness, norm_entropy

# S, (1-Hn), max(0,-B) of the merged stream, cross-account dup ratio,
# share of posts from accounts with a regular (scripted) own cadence.
WEIGHTS = [2.0, 2.0, 1.0, 1.5, 3.0]
BIAS = 4.0
REGULAR_B = 0.5  # own-gap burstiness <= -0.5 counts as a regular cadence
SCORE_THRESHOLD = 0.7
MIN_POSTS = 20
MIN_ACCOUNTS = 8
SYNC_WINDOW = 60
DUP_SIM = 0.9

ACCOUNT_WEIGHTS = {"co_sync": 2.5, "regularity": 2.0, "repetition": 2.0, "cluster_dup": 1.0}
ACCOUNT_BIAS = 3.5


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _synchrony(timestamps: list[float], n: int, window: float = SYNC_WINDOW) -> float:
    """Share of posts followed by another post within `window` seconds."""
    if n == 0:
        return 0.0
    ts = sorted(timestamps)
    sync_count = sum(1 for i in range(len(ts) - 1) if ts[i + 1] - ts[i] <= window)
    return sync_count / n


def _ts(s: str) -> float:
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()


def cross_account_dup_ratio(texts: list[str], authors: list[str], vecs: np.ndarray) -> float:
    """Share of posts whose text has a near-duplicate (cos >= DUP_SIM) written
    by a *different* account. Computed over unique texts for speed."""
    uniq: dict[str, int] = {}
    for t in texts:
        uniq.setdefault(t, len(uniq))
    idx = [uniq[t] for t in texts]
    uvecs = np.zeros((len(uniq), vecs.shape[1]), dtype=np.float32)
    for i, u in enumerate(idx):
        uvecs[u] = vecs[i]
    n = np.linalg.norm(uvecs, axis=1)
    n[n == 0] = 1.0
    unit = uvecs / n[:, None]
    near = (unit @ unit.T) >= DUP_SIM  # includes identical text (diagonal)
    authors_of: dict[int, set[str]] = {}
    for u, a in zip(idx, authors):
        authors_of.setdefault(u, set()).add(a)
    hits = 0
    for u, a in zip(idx, authors):
        partners: set[str] = set()
        for v in np.where(near[u])[0]:
            partners |= authors_of[int(v)]
        if partners - {a}:
            hits += 1
    return hits / len(texts) if texts else 0.0


def account_scores(
    authors: list[str], times: list[float], vecs: np.ndarray, cluster_dup: float
) -> dict[str, dict[str, float]]:
    order = np.argsort(times)
    t_sorted = [times[i] for i in order]
    norms = np.linalg.norm(vecs, axis=1)
    norms[norms == 0] = 1.0
    unit = vecs / norms[:, None]

    co_hits: dict[str, int] = {}
    counts: dict[str, int] = {}
    own_times: dict[str, list[float]] = {}
    for rank, i in enumerate(order):
        a = authors[i]
        counts[a] = counts.get(a, 0) + 1
        own_times.setdefault(a, []).append(times[i])
        hit = False
        for direction in (-1, 1):
            r = rank + direction
            while 0 <= r < len(order) and abs(t_sorted[r] - times[i]) <= SYNC_WINDOW:
                j = order[r]
                if authors[j] != a and float(unit[i] @ unit[j]) >= DUP_SIM:
                    hit = True
                    break
                r += direction
            if hit:
                break
        co_hits[a] = co_hits.get(a, 0) + int(hit)

    out: dict[str, dict[str, float]] = {}
    for a, n in counts.items():
        own = sorted(own_times[a])
        gaps = [own[k + 1] - own[k] for k in range(len(own) - 1)]
        feats = {
            "co_sync": co_hits[a] / n,
            "regularity": max(0.0, -burstiness(gaps)) if n >= 3 else 0.0,
            "repetition": min(1.0, (n - 1) / 3),
            "cluster_dup": cluster_dup,
            "n_posts": float(n),
        }
        raw = sum(ACCOUNT_WEIGHTS[k] * feats[k] for k in ACCOUNT_WEIGHTS) - ACCOUNT_BIAS
        feats["score"] = _sigmoid(raw)
        out[a] = feats
    return out


HASHTAG_WINDOW_S = 1800  # identical hashtag sets within the same 30-min window


def _find(parent: list[int], i: int) -> int:
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def narrative_clusters(posts: list[sqlite3.Row], block: int = 2048) -> list[tuple[str, list[int]]]:
    """Candidate narrative clusters (PRD 8.V2) as connected components of posts
    linked by any of:
      * near-identical text (cosine >= DUP_SIM) posted within the same hour,
      * a shared hashtag within the same 30-minute window,
      * an explicit repost / forward chain (origin_post_id).
    Links are time-bounded so organic reuse of common phrases cannot chain the
    whole timeline together; topic modelling is not involved, so fragmented
    topics cannot hide a campaign."""
    import re

    from app.nlp.embed import embed
    from app.nlp.hinglish import normalize_for_model

    n_posts = len(posts)
    parent = list(range(n_posts))

    def union(a: int, b: int) -> None:
        ra, rb = _find(parent, a), _find(parent, b)
        if ra != rb:
            parent[ra] = rb

    # near-duplicate text groups over unique normalised texts
    keys = [normalize_for_model(r["text"]).lower() for r in posts]
    uniq = list(dict.fromkeys(keys))
    uindex = {k: i for i, k in enumerate(uniq)}
    vecs = embed(uniq)
    nrm = np.linalg.norm(vecs, axis=1)
    nrm[nrm == 0] = 1.0
    unit = (vecs / nrm[:, None]).astype(np.float32)
    tparent = list(range(len(uniq)))
    for a in range(0, len(uniq), block):
        sims = unit[a:a + block] @ unit.T
        for i, j in zip(*np.where(sims >= DUP_SIM)):
            ri, rj = _find(tparent, a + int(i)), _find(tparent, int(j))
            if ri != rj:
                tparent[ri] = rj

    first_in: dict[tuple, int] = {}
    by_id = {r["post_id"]: i for i, r in enumerate(posts)}
    for i, r in enumerate(posts):
        t = _ts(r["created_at"])
        hour, half = int(t // 3600), int(t // HASHTAG_WINDOW_S)
        link_keys = [("text", _find(tparent, uindex[keys[i]]), hour)]
        link_keys += [("tag", tag, half) for tag in {x.lower() for x in re.findall(r"#\w+", r["text"])}]
        for k in link_keys:
            if k in first_in:
                union(i, first_in[k])
            else:
                first_in[k] = i
        origin = r["origin_post_id"]
        if origin and origin in by_id:
            union(i, by_id[origin])

    comps: dict[int, list[int]] = {}
    for i in range(n_posts):
        comps.setdefault(_find(parent, i), []).append(i)
    return [(f"component:{root}", sorted(m)) for root, m in comps.items() if len(m) >= MIN_POSTS]


def run_coordination(db_path: str) -> dict[str, int]:
    from app.nlp.embed import embed

    flagged: set[str] = set()
    n_clusters = 0
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("DELETE FROM coord_accounts")
        conn.execute("DELETE FROM coord_clusters")
        all_posts = conn.execute(
            "SELECT p.platform, p.post_id, p.author_id, p.created_at, p.text, p.origin_post_id, "
            "(SELECT ta.topic_id FROM topic_assign ta WHERE ta.platform=p.platform AND ta.post_id=p.post_id "
            " LIMIT 1) AS topic_id FROM posts p WHERE p.text != '' ORDER BY p.created_at"
        ).fetchall()
        if not all_posts:
            return {"clusters": 0, "coordinated_accounts": 0}

        for basis, members in narrative_clusters(all_posts):
            posts = [all_posts[i] for i in members]
            unique_accounts = {r["author_id"] for r in posts}
            if len(unique_accounts) < MIN_ACCOUNTS:
                continue

            timestamps = [_ts(r["created_at"]) for r in posts]
            gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
            B = burstiness(gaps)
            Hn = norm_entropy(gaps)
            S = _synchrony(timestamps, len(timestamps))

            authors = [r["author_id"] for r in posts]
            vecs = embed([r["text"] for r in posts])
            dup_ratio = cross_account_dup_ratio([r["text"] for r in posts], authors, vecs)
            scores = account_scores(authors, timestamps, vecs, dup_ratio)
            reg_share = sum(
                f["n_posts"] for f in scores.values() if f["regularity"] >= REGULAR_B
            ) / len(posts)

            raw_score = (
                WEIGHTS[0] * S + WEIGHTS[1] * (1.0 - Hn) + WEIGHTS[2] * max(0.0, -B)
                + WEIGHTS[3] * dup_ratio + WEIGHTS[4] * reg_share - BIAS
            )
            cluster_score = _sigmoid(raw_score)
            if cluster_score < SCORE_THRESHOLD:
                continue

            topics = [r["topic_id"] for r in posts if r["topic_id"] is not None]
            topic_id = max(set(topics), key=topics.count) if topics else None
            cur = conn.execute(
                "INSERT INTO coord_clusters (topic_id, n_posts, n_accounts, hn, burstiness, sync, "
                "dup_ratio, regular_share, score, basis, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (topic_id, len(posts), len(unique_accounts), Hn, B, S, dup_ratio, reg_share,
                 cluster_score, basis.split("@")[0][:120], datetime.now(timezone.utc).isoformat()),
            )
            cluster_id = cur.lastrowid
            n_clusters += 1

            platforms_of: dict[str, set[str]] = {}
            for r in posts:
                platforms_of.setdefault(r["author_id"], set()).add(r["platform"])
            for acc_id, feats in scores.items():
                reasons = {**{k: round(v, 4) for k, v in feats.items()},
                           "cluster_score": round(cluster_score, 4), "cluster_hn": round(Hn, 4),
                           "cluster_burstiness": round(B, 4), "cluster_sync": round(S, 4),
                           "cluster_basis": basis.split("@")[0][:120]}
                conn.executemany(
                    "INSERT OR REPLACE INTO coord_accounts (platform, account_id, cluster_id, score, reasons_json) "
                    "VALUES (?,?,?,?,?)",
                    [(plat, acc_id, cluster_id, feats["score"], json.dumps(reasons))
                     for plat in sorted(platforms_of[acc_id])],
                )
                if feats["score"] >= SCORE_THRESHOLD:
                    flagged.add(acc_id)
        conn.commit()
    return {"clusters": n_clusters, "coordinated_accounts": len(flagged)}
