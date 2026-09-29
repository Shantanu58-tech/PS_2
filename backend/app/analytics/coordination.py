from __future__ import annotations
import json
import sqlite3
import numpy as np
from datetime import datetime, timezone
from app.analytics.burst import burstiness, norm_entropy


WEIGHTS = [2.0, 2.0, 1.0, 1.5, 2.5]
BIAS = 4.0
SCORE_THRESHOLD = 0.7
MIN_POSTS = 20
MIN_ACCOUNTS = 8
SYNC_WINDOW = 60


def _sigmoid(x: float) -> float:
    import math
    return 1.0 / (1.0 + math.exp(-x))


def _synchrony(timestamps: list[float], n: int, window: float = SYNC_WINDOW) -> float:
    if n == 0:
        return 0.0
    ts = sorted(timestamps)
    sync_count = 0
    for i in range(len(ts)):
        for j in range(i + 1, len(ts)):
            if ts[j] - ts[i] <= window:
                sync_count += 1
                break
            else:
                break
    return sync_count / n


def run_coordination(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        topic_rows = conn.execute(
            "SELECT DISTINCT ta.topic_id FROM topic_assign ta"
        ).fetchall()

        for trow in topic_rows:
            topic_id = trow["topic_id"]
            posts = conn.execute(
                """
                SELECT p.platform, p.post_id, p.author_id, p.created_at, p.text
                FROM posts p
                JOIN topic_assign ta ON ta.platform=p.platform AND ta.post_id=p.post_id
                WHERE ta.topic_id=?
                ORDER BY p.created_at
                """,
                (topic_id,),
            ).fetchall()

            if len(posts) < MIN_POSTS:
                continue

            unique_accounts = set(r["author_id"] for r in posts)
            if len(unique_accounts) < MIN_ACCOUNTS:
                continue

            timestamps = []
            for r in posts:
                try:
                    dt = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                    timestamps.append(dt.timestamp())
                except Exception:
                    pass

            gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
            B = burstiness(gaps)
            Hn = norm_entropy(gaps)
            S = _synchrony(timestamps, len(timestamps))

            texts = [r["text"] for r in posts]
            try:
                from app.nlp.embed import embed
                vecs = embed(texts)
                medoid = vecs.mean(axis=0)
                norms = np.linalg.norm(vecs, axis=1) * np.linalg.norm(medoid)
                sims = np.dot(vecs, medoid) / np.where(norms > 0, norms, 1)
                dup_ratio = float((sims >= 0.95).sum() / len(sims))
            except Exception:
                dup_ratio = 0.0

            raw_score = (
                WEIGHTS[0] * S
                + WEIGHTS[1] * (1.0 - Hn)
                + WEIGHTS[2] * max(0.0, -B)
                + WEIGHTS[3] * dup_ratio
                - BIAS
            )
            cluster_score = _sigmoid(raw_score)

            if cluster_score >= SCORE_THRESHOLD:
                now = datetime.now(timezone.utc).isoformat()
                cursor = conn.execute(
                    """
                    INSERT INTO coord_clusters (topic_id, n_posts, n_accounts, hn, burstiness, sync, dup_ratio, score, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)
                    """,
                    (topic_id, len(posts), len(unique_accounts), Hn, B, S, dup_ratio, cluster_score, now),
                )
                cluster_id = cursor.lastrowid

                for acc_id in unique_accounts:
                    acc_posts = [r for r in posts if r["author_id"] == acc_id]
                    acc_ts = []
                    for r in acc_posts:
                        try:
                            acc_ts.append(datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).timestamp())
                        except Exception:
                            pass
                    acc_gaps = [acc_ts[i + 1] - acc_ts[i] for i in range(len(acc_ts) - 1)]
                    acc_score = cluster_score
                    reasons = {
                        "sync": S,
                        "entropy": Hn,
                        "burstiness": B,
                        "dup_ratio": dup_ratio,
                        "cluster_score": cluster_score,
                    }
                    platform = acc_posts[0]["platform"] if acc_posts else "unknown"
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO coord_accounts (platform, account_id, cluster_id, score, reasons_json)
                        VALUES (?,?,?,?,?)
                        """,
                        (platform, acc_id, cluster_id, acc_score, json.dumps(reasons)),
                    )

        conn.commit()
