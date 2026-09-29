"""Windowed topic clustering with centroid matching; trends and bursts."""
from app.analytics.topics import ctfidf_keywords, run_topics
from tests.conftest import rows


def test_ctfidf_prefers_distinctive_terms():
    kw = ctfidf_keywords({0: ["dam crack evacuate", "dam crack now"], 1: ["cricket six win", "cricket win"]})
    assert "dam" in kw[0] and "cricket" in kw[1] and "dam" not in kw[1]


def test_topics_cover_scenario_and_keep_identity_across_windows(analysed_db):
    topics = rows(analysed_db, "SELECT topic_id, first_seen, last_seen FROM topics")
    assert len(topics) >= 5
    # background topics recur daily, so some topics must span > 1 window (identity kept)
    assert any(t["last_seen"][:10] != t["first_seen"][:10] for t in topics)


def test_rerun_is_idempotent(analysed_db, tmp_path):
    import shutil
    import sqlite3

    copy = str(tmp_path / "copy.db")
    with sqlite3.connect(analysed_db) as s, sqlite3.connect(copy) as d:
        s.backup(d)
    n1 = run_topics(copy)
    n2 = run_topics(copy)
    assert n1 == n2
    assert rows(copy, "SELECT COUNT(*) n FROM topic_assign")[0]["n"] == rows(
        copy, "SELECT COUNT(DISTINCT platform || post_id) n FROM topic_assign")[0]["n"]
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_series_has_organic_counts_and_manufactured_topic(analysed_db):
    s = rows(analysed_db, "SELECT SUM(count_all) a, SUM(count_organic) o FROM topic_series")[0]
    assert s["a"] >= s["o"] > 0
    assert rows(analysed_db, "SELECT COUNT(*) n FROM topics WHERE nature='manufactured'")[0]["n"] >= 1
    assert rows(analysed_db, "SELECT COUNT(*) n FROM bursts WHERE level >= 1")[0]["n"] >= 1


def test_rise_scores_rank_topics(analysed_db):
    from app.analytics.trends import rise_scores

    rise = rise_scores(analysed_db)
    assert rise and all({"rise", "novelty", "acceleration", "account_growth"} <= set(v) for v in rise.values())
