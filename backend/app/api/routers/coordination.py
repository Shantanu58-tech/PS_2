from fastapi import APIRouter, HTTPException

from app.api.deps import fetch_all, fetch_one, loads

router = APIRouter()

DISCLAIMER = ("Behaviour consistent with scripted amplification (timing + near-duplicate content). "
              "This is a statistical signal for analyst review, not an accusation.")


@router.get("/coordination/clusters")
async def list_clusters():
    rows = await fetch_all(
        "SELECT c.*, t.label AS topic_label, "
        "(SELECT COUNT(DISTINCT account_id) FROM coord_accounts ca WHERE ca.cluster_id=c.cluster_id "
        " AND ca.score >= 0.7) AS n_coordinated "
        "FROM coord_clusters c LEFT JOIN topics t ON t.topic_id=c.topic_id ORDER BY c.score DESC LIMIT 50"
    )
    return {"clusters": rows, "disclaimer": DISCLAIMER}


@router.get("/coordination/clusters/{cluster_id}")
async def get_cluster(cluster_id: int):
    cluster = await fetch_one(
        "SELECT c.*, t.label AS topic_label FROM coord_clusters c LEFT JOIN topics t "
        "ON t.topic_id=c.topic_id WHERE c.cluster_id=?", (cluster_id,))
    if not cluster:
        raise HTTPException(404, "cluster not found")
    accounts = await fetch_all(
        "SELECT account_id, GROUP_CONCAT(platform) AS platforms, MAX(score) AS score, reasons_json "
        "FROM coord_accounts WHERE cluster_id=? GROUP BY account_id ORDER BY score DESC",
        (cluster_id,),
    )
    for a in accounts:
        a["reasons"] = loads(a.pop("reasons_json"), {})
    # timing heatmap: posts per minute from coordinated vs other accounts
    heat = await fetch_all(
        """
        SELECT strftime('%Y-%m-%dT%H:%M:00Z', p.created_at) AS minute,
               SUM(CASE WHEN ca.score >= 0.7 THEN 1 ELSE 0 END) AS coordinated,
               SUM(CASE WHEN ca.score IS NULL OR ca.score < 0.7 THEN 1 ELSE 0 END) AS other
        FROM topic_assign ta
        JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id
        LEFT JOIN coord_accounts ca ON ca.platform=p.platform AND ca.account_id=p.author_id
             AND ca.cluster_id=?
        WHERE ta.topic_id=? GROUP BY 1 ORDER BY 1
        """,
        (cluster_id, cluster["topic_id"]),
    )
    evidence = await fetch_all(
        "SELECT p.platform, p.post_id, p.author_id, p.text, p.created_at, p.ledger_seq "
        "FROM posts p JOIN coord_accounts ca ON ca.platform=p.platform AND ca.account_id=p.author_id "
        "JOIN topic_assign ta ON ta.platform=p.platform AND ta.post_id=p.post_id "
        "WHERE ca.cluster_id=? AND ca.score >= 0.7 AND ta.topic_id=? ORDER BY p.created_at LIMIT 25",
        (cluster_id, cluster["topic_id"]),
    )
    fingerprint = await _fingerprint(cluster_id, cluster["topic_id"])
    return {"cluster": cluster, "accounts": accounts, "timing": heat, "evidence_posts": evidence,
            "fingerprint": fingerprint, "disclaimer": DISCLAIMER}


async def _fingerprint(cluster_id: int, topic_id: int | None) -> dict:
    """Synchrony fingerprint: post times of the flagged accounts next to ordinary accounts
    posting on the same topic in the same window, plus two plain comparisons."""
    from datetime import datetime
    from statistics import median

    flagged = await fetch_all(
        "SELECT p.author_id, p.created_at FROM posts p JOIN coord_accounts ca ON ca.platform=p.platform "
        "AND ca.account_id=p.author_id JOIN topic_assign ta ON ta.platform=p.platform AND ta.post_id=p.post_id "
        "WHERE ca.cluster_id=? AND ca.score >= 0.7 AND ta.topic_id=? ORDER BY p.created_at", (cluster_id, topic_id))
    if not flagged:
        return {"start": None, "end": None, "flagged": [], "organic": [], "compare": None}
    start, end = flagged[0]["created_at"], flagged[-1]["created_at"]
    organic = await fetch_all(
        "SELECT p.author_id, p.created_at FROM posts p JOIN topic_assign ta ON ta.platform=p.platform "
        "AND ta.post_id=p.post_id WHERE ta.topic_id=? AND p.created_at BETWEEN datetime(?, '-30 minutes') "
        "AND datetime(?, '+60 minutes') AND NOT EXISTS (SELECT 1 FROM coord_accounts ca WHERE "
        "ca.account_id=p.author_id AND ca.score >= 0.7) ORDER BY p.created_at", (topic_id, start, end))
    if len(organic) < 10:  # a narrative with few ordinary posters: compare with the whole topic
        organic = await fetch_all(
            "SELECT p.author_id, p.created_at FROM posts p JOIN topic_assign ta ON ta.platform=p.platform "
            "AND ta.post_id=p.post_id WHERE ta.topic_id=? AND NOT EXISTS (SELECT 1 FROM coord_accounts ca "
            "WHERE ca.account_id=p.author_id AND ca.score >= 0.7) ORDER BY p.created_at LIMIT 400", (topic_id,))

    def rows(posts: list[dict], n: int) -> list[dict]:
        by: dict[str, list[str]] = {}
        for p in posts:
            by.setdefault(p["author_id"], []).append(p["created_at"])
        top = sorted(by.items(), key=lambda kv: -len(kv[1]))[:n]
        return [{"account_id": a, "times": t} for a, t in top]

    def ts(x: str) -> float:
        return datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()

    def stats(posts: list[dict]) -> dict:
        times = sorted(ts(p["created_at"]) for p in posts)
        authors = [p["author_id"] for p in sorted(posts, key=lambda p: p["created_at"])]
        gaps: list[float] = []
        by: dict[str, list[float]] = {}
        for p in posts:
            by.setdefault(p["author_id"], []).append(ts(p["created_at"]))
        for t in by.values():
            t.sort()
            gaps += [b - a for a, b in zip(t, t[1:])]
        near = sum(1 for i in range(1, len(times)) if times[i] - times[i - 1] <= 60 and authors[i] != authors[i - 1])
        return {"posts": len(posts), "accounts": len(by),
                "median_gap_s": round(median(gaps)) if gaps else None,
                "within_minute": round(near / max(1, len(times) - 1), 3)}

    return {"start": start, "end": end, "flagged": rows(flagged, 24), "organic": rows(organic, 16),
            "compare": {"flagged": stats(flagged), "organic": stats(organic)}}


@router.get("/behaviour")
async def behaviour(limit: int = 30, min_likelihood: float = 0.0):
    rows = await fetch_all(
        "SELECT platform, account_id, likelihood, features_json FROM account_behaviour "
        "WHERE likelihood >= ? ORDER BY likelihood DESC LIMIT ?", (min_likelihood, limit))
    for r in rows:
        r["features"] = loads(r.pop("features_json"), {})
    dist = await fetch_all(
        "SELECT CAST(likelihood * 10 AS INT) / 10.0 AS bin, COUNT(*) AS n FROM account_behaviour GROUP BY 1 ORDER BY 1")
    return {
        "label": "Experimental behaviour likelihood",
        "caveat": "Heuristic score from posting-timing and content-reuse features only. Not validated on "
                  "real data; not an identification of automated accounts. Never uses demographics.",
        "accounts": rows,
        "distribution": dist,
    }
