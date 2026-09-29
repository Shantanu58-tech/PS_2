"""Windowed topic re-clustering with centroid matching.

The data range is cut into fixed windows (default 24 h, by post time). Each
window is clustered independently; every new cluster is matched to an
existing topic when the cosine similarity of centroids exceeds ``tau_match``
(the topic continues, its centroid is updated as a running mean), otherwise a
new topic is created. Posts join a cluster only if their similarity to the
cluster centroid is at least ``tau_assign``.

Engines: "agglomerative" (default; deterministic, average-linkage cosine) or
"bertopic" (TOPIC_ENGINE=bertopic; stochastic via UMAP).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timedelta

import numpy as np

from app.nlp.embed import embed

MIN_CLUSTER_POSTS = 15
STOPWORDS = {
    "the", "a", "an", "is", "are", "to", "of", "in", "on", "and", "for", "this", "that", "it",
    "be", "by", "all", "so", "why", "what", "has", "have", "now", "today", "again", "just", "my",
    "our", "we", "i", "me", "you", "yaar", "bhai", "hai", "kya", "ho", "gaya", "se", "ki", "ke",
    "ka", "aaj", "sach", "mein", "bhi", "main", "tha", "haan", "baat", "raha", "yahi", "wah",
}


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"#?[a-z][a-z0-9]+", text.lower()) if t.lstrip("#") not in STOPWORDS]


def ctfidf_keywords(cluster_texts: dict[int, list[str]], top_n: int = 5) -> dict[int, list[str]]:
    """Class-based TF-IDF: terms frequent in one cluster and rare in others."""
    tf: dict[int, dict[str, int]] = {}
    df: dict[str, int] = {}
    for cid, texts in cluster_texts.items():
        counts: dict[str, int] = {}
        for t in texts:
            for tok in _tokens(t):
                counts[tok] = counts.get(tok, 0) + 1
        tf[cid] = counts
        for tok in counts:
            df[tok] = df.get(tok, 0) + 1
    n = max(1, len(cluster_texts))
    out: dict[int, list[str]] = {}
    for cid, counts in tf.items():
        total = sum(counts.values()) or 1
        scored = sorted(
            counts, key=lambda w: (counts[w] / total) * np.log(1 + n / df[w]), reverse=True
        )
        out[cid] = scored[:top_n]
    return out


def _cluster_agglomerative(vecs: np.ndarray, distance_threshold: float = 0.35) -> np.ndarray:
    from sklearn.cluster import AgglomerativeClustering

    if len(vecs) < 2:
        return np.zeros(len(vecs), dtype=int)
    model = AgglomerativeClustering(
        n_clusters=None, metric="cosine", linkage="average", distance_threshold=distance_threshold
    )
    return model.fit_predict(vecs)


def _cluster_bertopic(texts: list[str], vecs: np.ndarray) -> np.ndarray:
    from bertopic import BERTopic

    model = BERTopic(language="multilingual", verbose=False)
    labels, _ = model.fit_transform(texts, embeddings=vecs)
    return np.asarray(labels)


def cluster_window(texts: list[str], engine: str = "agglomerative") -> tuple[np.ndarray, np.ndarray]:
    """Return (labels per text, vectors). Label -1 = noise."""
    vecs = embed(texts)
    unique = list(dict.fromkeys(texts))
    uvecs = embed(unique)
    if engine == "bertopic":
        ulabels = _cluster_bertopic(unique, uvecs)
    else:
        ulabels = _cluster_agglomerative(uvecs)
    by_text = dict(zip(unique, ulabels))
    labels = np.array([by_text[t] for t in texts])
    # small clusters -> noise
    ids, counts = np.unique(labels, return_counts=True)
    small = {i for i, c in zip(ids, counts) if c < MIN_CLUSTER_POSTS}
    labels = np.array([-1 if lab in small else lab for lab in labels])
    return labels, vecs


def run_topics(
    db_path: str,
    window_hours: int = 24,
    tau_assign: float = 0.55,
    tau_match: float = 0.80,
    engine: str | None = None,
) -> int:
    """Recompute topics over the full data range. Returns the number of topics."""
    engine = engine or os.environ.get("TOPIC_ENGINE", "agglomerative")
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("DELETE FROM topic_assign")
        conn.execute("DELETE FROM topics")
        lo, hi = conn.execute(
            "SELECT MIN(created_at), MAX(created_at) FROM posts WHERE text != ''"
        ).fetchone()
        if not lo:
            conn.commit()
            return 0
        start, end = _parse(lo), _parse(hi)

        # topic_id -> (centroid, n_posts)
        topics: dict[int, tuple[np.ndarray, int]] = {}
        ws = start
        while ws <= end:
            we = ws + timedelta(hours=window_hours)
            rows = conn.execute(
                "SELECT platform, post_id, text, created_at FROM posts "
                "WHERE created_at >= ? AND created_at < ? AND text != ''",
                (ws.isoformat(), we.isoformat()),
            ).fetchall()
            ws = we
            if len(rows) < MIN_CLUSTER_POSTS:
                continue
            texts = [r["text"] for r in rows]
            labels, vecs = cluster_window(texts, engine)
            cluster_ids = sorted(set(labels.tolist()) - {-1})
            keywords = ctfidf_keywords(
                {c: [t for t, lab in zip(texts, labels) if lab == c] for c in cluster_ids}
            )
            for c in cluster_ids:
                mask = labels == c
                centroid = vecs[mask].mean(axis=0)
                members = [i for i in np.where(mask)[0]
                           if _cosine(vecs[i], centroid) >= tau_assign]
                if len(members) < MIN_CLUSTER_POSTS:
                    continue
                times = [rows[i]["created_at"] for i in members]
                best_id, best_sim = None, tau_match
                for tid, (tc, _) in topics.items():
                    sim = _cosine(centroid, tc)
                    if sim > best_sim:
                        best_id, best_sim = tid, sim
                if best_id is None:
                    kw = keywords.get(c, [])
                    label = " ".join(k.lstrip("#") for k in kw[:3]) or "topic"
                    cur = conn.execute(
                        "INSERT INTO topics (label, keywords, centroid, first_seen, last_seen, status) "
                        "VALUES (?,?,?,?,?,?)",
                        (label, json.dumps(kw), centroid.astype(np.float32).tobytes(),
                         min(times), max(times), "active"),
                    )
                    assert cur.lastrowid is not None
                    tid = cur.lastrowid
                    topics[tid] = (centroid, len(members))
                else:
                    tid = best_id
                    old, n_old = topics[tid]
                    merged = (old * n_old + centroid * len(members)) / (n_old + len(members))
                    topics[tid] = (merged, n_old + len(members))
                    conn.execute(
                        "UPDATE topics SET centroid=?, last_seen=MAX(last_seen, ?), "
                        "first_seen=MIN(first_seen, ?) WHERE topic_id=?",
                        (merged.astype(np.float32).tobytes(), max(times), min(times), tid),
                    )
                conn.executemany(
                    "INSERT INTO topic_assign (platform, post_id, topic_id, prob) VALUES (?,?,?,?)",
                    [(rows[i]["platform"], rows[i]["post_id"], tid,
                      round(_cosine(vecs[i], centroid), 4)) for i in members],
                )
        conn.commit()
        return len(topics)
