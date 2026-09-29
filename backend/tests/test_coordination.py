"""Coordination detector: scripted cadence vs organic replies."""
import numpy as np

from app.analytics.coordination import account_scores, cross_account_dup_ratio


def _vecs(texts):
    from app.nlp.embed import embed

    return embed(texts)


def test_scripted_accounts_score_high_single_repliers_low():
    authors, times, texts = [], [], []
    for a in range(10):  # scripted: 5 posts each every 90 s, templated text
        for j in range(5):
            authors.append(f"bot{a}")
            times.append(1000 + 90 * j + a * 2)
            texts.append("BREAKING dam cracked evacuate now")
    for r in range(10):  # organic: one reply each, spread out
        authors.append(f"user{r}")
        times.append(5000 + 400 * r)
        texts.append(f"is this real? worried about family {r}")
    vecs = _vecs(texts)
    dup = cross_account_dup_ratio(texts, authors, vecs)
    scores = account_scores(authors, times, vecs, dup)
    assert all(scores[f"bot{a}"]["score"] >= 0.7 for a in range(10))
    assert all(scores[f"user{r}"]["score"] < 0.7 for r in range(10))
    assert scores["bot0"]["regularity"] > 0.5 and scores["user0"]["repetition"] == 0.0


def test_cross_account_dup_ignores_self_repeats():
    texts = ["same text"] * 4 + ["other words entirely"]
    authors = ["a", "a", "a", "a", "b"]
    assert cross_account_dup_ratio(texts, authors, _vecs(texts)) == 0.0


def test_scenario_detection_quality(analysed_db, mini_scenario):
    from tests.conftest import rows

    _, truth = mini_scenario
    coord = set(truth["coordinated_account_ids"])
    flagged = {r[0] for r in rows(analysed_db, "SELECT DISTINCT account_id FROM coord_accounts WHERE score >= 0.7")}
    precision = len(flagged & coord) / max(1, len(flagged))
    assert precision >= 0.9
    fans = set(truth["fan_club_account_ids"])
    assert len(flagged & fans) <= 2  # legitimate fan swarm must not be labelled coordinated
    reasons = rows(analysed_db, "SELECT reasons_json FROM coord_accounts LIMIT 1")[0][0]
    assert "co_sync" in reasons and "cluster_hn" in reasons  # "why" panel inputs stored
    assert np.isfinite(len(flagged))
