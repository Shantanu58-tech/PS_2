"""Replay -> ledger -> canonical tables -> analytics, end to end on a mini scenario."""
from app.ledger.verify import verify_chain
from tests.conftest import rows


def test_every_post_has_a_ledger_entry(analysed_db):
    n_posts = rows(analysed_db, "SELECT COUNT(*) n FROM posts")[0]["n"]
    missing = rows(analysed_db, "SELECT COUNT(*) n FROM posts p WHERE NOT EXISTS "
                                "(SELECT 1 FROM raw_records r WHERE r.seq=p.ledger_seq)")[0]["n"]
    assert n_posts > 3000 and missing == 0
    assert verify_chain(analysed_db)["status"] == "PASS"


def test_replay_uses_canonical_ids_not_unknown(analysed_db):
    assert rows(analysed_db, "SELECT COUNT(*) n FROM posts WHERE post_id='unknown' OR author_id='unknown'")[0]["n"] == 0


def test_chronology_and_utc(analysed_db):
    ts = [r["created_at"] for r in rows(analysed_db, "SELECT created_at FROM posts ORDER BY created_at LIMIT 50")]
    assert ts == sorted(ts) and all(t.endswith("+00:00") for t in ts)


def test_thread_integrity_replies_resolve_or_flagged(analysed_db):
    orphans = rows(analysed_db, "SELECT COUNT(*) n FROM posts p WHERE p.parent_post_id IS NOT NULL AND NOT EXISTS "
                                "(SELECT 1 FROM posts q WHERE q.post_id=p.parent_post_id)")[0]["n"]
    assert orphans == 0  # the scenario only replies to collected posts


def test_edges_are_account_to_account(analysed_db):
    assert rows(analysed_db, "SELECT COUNT(*) n FROM edges WHERE dst_account LIKE 'post:%'")[0]["n"] == 0
    assert rows(analysed_db, "SELECT COUNT(*) n FROM edges WHERE kind='mention'")[0]["n"] > 0


def test_media_hashed_with_phash(analysed_db):
    media = rows(analysed_db, "SELECT media_id, sha256, phash FROM media")
    assert len(media) >= 3 and all(m["sha256"] and m["phash"] for m in media)


def test_analytics_populated(analysed_db):
    for table in ("post_emotions", "topics", "topic_assign", "topic_series", "demo_aggregates",
                  "account_behaviour", "forecasts"):
        assert rows(analysed_db, f"SELECT COUNT(*) n FROM {table}")[0]["n"] > 0, table


def test_planted_narrative_flagged_and_decoy_not_high_priority(analysed_db, mini_scenario):
    _, truth = mini_scenario
    coord = set(truth["coordinated_account_ids"])
    flagged = {r[0] for r in rows(analysed_db, "SELECT DISTINCT account_id FROM coord_accounts WHERE score >= 0.7")}
    assert len(flagged & coord) >= 0.8 * len(coord)
    alerts = rows(analysed_db, "SELECT a.priority, a.headline, t.label FROM alerts a JOIN topics t USING(topic_id)")
    decoy_high = [a for a in alerts if a["priority"] >= 70 and "manufactured" not in a["headline"].lower()]
    assert not decoy_high
