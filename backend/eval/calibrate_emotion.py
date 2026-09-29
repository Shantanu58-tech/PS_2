"""Rescore the eval DBs with the current emotion engine and tune per-label
decision thresholds on the VALIDATION seed only (PRD 11: "per-label thresholds
tuned on dev"). Writes app/nlp/emotion_thresholds.json; the held-out seed is
never used for tuning.

    cd backend && python -m eval.calibrate_emotion
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from eval.common import HELDOUT_SEED, VALIDATION_SEED, build_db
from eval.emotion_eval import LABELS, _eval_label, _scores

OUT = Path(__file__).resolve().parents[1] / "app" / "nlp" / "emotion_thresholds.json"


def rescore(db: str) -> None:
    """Replace post_emotions with the current engine's scores, then refresh the
    stages that consume them (signals use the anxiety shift)."""
    from app.analytics.signals import generate_signals
    from app.pipeline.analytics import score_emotions

    with sqlite3.connect(db) as conn:
        conn.execute("DELETE FROM post_emotions")
        conn.commit()
    score_emotions(db)
    generate_signals(db)


def tune(db: str, truth: dict) -> dict[str, dict]:
    positives = {k: set(truth["labels"][v]) for k, v in LABELS.items()}
    pool = set().union(*positives.values())
    scored = _scores(db, pool)
    best: dict[str, dict] = {}
    for label, pos in positives.items():
        cand = []
        for t in [x / 100 for x in range(30, 100)]:
            thresholded = {pid: {label: 1.0 if s[label] >= t else 0.0} for pid, s in scored.items()}
            cand.append((_eval_label(thresholded, pos, label)["f1"], -abs(t - 0.5), t))
        f1, _, t = max(cand)
        best[label] = {"threshold": t, "validation_f1": f1}
    return best


def main() -> None:
    from app.nlp import emotion

    val = build_db(VALIDATION_SEED)
    held = build_db(HELDOUT_SEED)
    rescore(val["db"])
    rescore(held["db"])
    tuned = tune(val["db"], val["truth"])
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    data[emotion.engine()] = {**{d: 0.5 for d in emotion.DIMENSIONS},
                              **{k: v["threshold"] for k, v in tuned.items()}}
    data["_tuned_on"] = {"seed": VALIDATION_SEED, "engine": emotion.engine(), "validation": tuned}
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    emotion.thresholds.cache_clear()
    print(f"thresholds -> {OUT}: {data[emotion.engine()]}")


if __name__ == "__main__":
    main()
