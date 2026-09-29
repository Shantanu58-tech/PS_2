from __future__ import annotations
import json
import sqlite3
import numpy as np
from datetime import datetime, timezone
from app.nlp.embed import embed
from app.analytics.burst import kleinberg_bursts


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def run_topics(db_path: str, window_hours: int = 24, tau_assign: float = 0.55, tau_match: float = 0.80) -> None:
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        now_ts = datetime.now(timezone.utc).isoformat()
        cutoff = f"{datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()}"
        rows = conn.execute(
            "SELECT platform, post_id, text FROM posts WHERE created_at >= ? AND text != '' LIMIT 50000",
            (cutoff,),
        ).fetchall()

        if len(rows) < 10:
            return

        texts = [r["text"] for r in rows]
        post_keys = [(r["platform"], r["post_id"]) for r in rows]

        try:
            vecs = embed(texts)
        except Exception:
            return

        existing = conn.execute(
            "SELECT topic_id, label, keywords, centroid FROM topics WHERE status='active'"
        ).fetchall()

        existing_topics = []
        for t in existing:
            centroid = np.frombuffer(t["centroid"], dtype=np.float32) if t["centroid"] else None
            if centroid is not None:
                existing_topics.append((t["topic_id"], t["label"], t["keywords"], centroid))

        try:
            from bertopic import BERTopic
            from sklearn.feature_extraction.text import CountVectorizer
            topic_model = BERTopic(language="multilingual", calculate_probabilities=True, verbose=False)
            topics_arr, probs = topic_model.fit_transform(texts)
        except Exception:
            return

        topic_info = topic_model.get_topic_info()
        new_centroids: dict[int, np.ndarray] = {}
        for topic_id in set(topics_arr):
            if topic_id == -1:
                continue
            mask = np.array(topics_arr) == topic_id
            if mask.sum() > 0:
                new_centroids[topic_id] = vecs[mask].mean(axis=0)

        topic_id_map: dict[int, int] = {}
        for new_t, centroid in new_centroids.items():
            best_match = None
            best_sim = tau_match
            for (existing_id, _, _, ex_centroid) in existing_topics:
                sim = _cosine(centroid, ex_centroid)
                if sim > best_sim:
                    best_sim = sim
                    best_match = existing_id
            if best_match is not None:
                topic_id_map[new_t] = best_match
                conn.execute(
                    "UPDATE topics SET centroid=?, last_seen=? WHERE topic_id=?",
                    (centroid.astype(np.float32).tobytes(), now_ts, best_match),
                )
            else:
                topic_words = topic_model.get_topic(new_t)
                keywords = json.dumps([w for w, _ in topic_words[:5]] if topic_words else [])
                label = " ".join([w for w, _ in topic_words[:3]] if topic_words else ["topic"])
                cursor = conn.execute(
                    "INSERT INTO topics (label, keywords, centroid, first_seen, last_seen, status) VALUES (?,?,?,?,?,?)",
                    (label, keywords, centroid.astype(np.float32).tobytes(), now_ts, now_ts, "active"),
                )
                topic_id_map[new_t] = cursor.lastrowid

        for i, (platform, post_id) in enumerate(post_keys):
            new_t = topics_arr[i]
            if new_t == -1:
                continue
            mapped_t = topic_id_map.get(new_t)
            if mapped_t is None:
                continue
            prob = float(probs[i].max()) if hasattr(probs[i], "max") else 0.5
            conn.execute(
                "INSERT OR REPLACE INTO topic_assign (platform, post_id, topic_id, prob) VALUES (?,?,?,?)",
                (platform, post_id, mapped_t, prob),
            )

        conn.commit()
