"""API contract tests on the analysed mini scenario (FastAPI TestClient)."""
import json

import pytest
from fastapi.testclient import TestClient

FORBIDDEN_KEYS = {"age_bracket", "inferred_age", "inferred_state", "inferred_interest", "gender",
                  "per_account_demographics", "individual_demographic"}


@pytest.fixture(scope="module")
def client(analysed_db):
    from app.config import settings
    from app.main import app
    from app.pipeline.workers import reset_ingestors

    old = settings.db_path
    settings.db_path = analysed_db
    reset_ingestors()
    with TestClient(app) as c:
        yield c
    settings.db_path = old
    reset_ingestors()


def _walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_keys(v)


GET_ENDPOINTS = [
    "/healthz", "/api/posts?limit=5", "/api/timeline/emotions", "/api/timeline/compare", "/api/topics",
    "/api/graph?max_nodes=40", "/api/influencers?limit=5", "/api/graph/spread", "/api/coordination/clusters",
    "/api/behaviour", "/api/lineage", "/api/lineage/images", "/api/demographics", "/api/alerts",
    "/api/ledger/status", "/api/collectors", "/api/search?q=dam", "/api/traceability", "/api/pipeline/status",
    "/api/platforms", "/api/platforms/x", "/api/keywords/trending", "/api/graph/segment-spread",
    "/api/timeline/emotions?kind=comments", "/api/timeline/emotions?kind=posts&platform=x",
    "/api/situation", "/api/demographics?scope=live",
]


@pytest.mark.parametrize("path", GET_ENDPOINTS)
def test_get_endpoints_ok_and_no_per_account_demographics(client, path):
    r = client.get(path)
    assert r.status_code == 200, r.text
    assert not FORBIDDEN_KEYS & set(_walk_keys(r.json()))


def test_no_route_exposes_individual_demographics(client):
    paths = list(client.get("/openapi.json").json()["paths"])
    assert any(p.startswith("/api/demographics") for p in paths)
    assert not [p for p in paths if "demographic" in p and "{" in p]


def test_demographics_are_aggregate_with_privacy_params(client):
    j = client.get("/api/demographics").json()
    assert j["k_anon"] == 10 and j["dp_epsilon"] > 0
    for d in j["dimensions"].values():
        assert all(b["count"] >= 10 for b in d["buckets"])


def test_verify_and_tamper_simulation_on_scratch_copy(client):
    assert client.post("/api/ledger/verify").json()["status"] == "PASS"
    r = client.post("/api/ledger/tamper-sim?seq=3").json()
    assert r["scratch_copy"] and r["verify_result"]["status"] == "FAIL" and r["detected_at_expected_seq"]
    assert client.post("/api/ledger/verify").json()["status"] == "PASS"  # real ledger untouched


def test_replay_twice_refused(client):
    assert client.post("/api/replay/start", json={}).status_code == 409


def test_case_brief_and_draft_certificate(client):
    alert = client.get("/api/alerts").json()["alerts"][0]
    case = client.post("/api/cases", json={"alert_id": alert["alert_id"], "title": "t"}).json()
    brief = client.get(case["brief_url"]).text
    cert = client.get(case["certificate_url"]).text
    assert "Evidence index" in brief
    assert "DRAFT" in cert and "Section 63" in cert
    assert client.get("/api/audit").json()["entries"]


def test_search_survives_fts_syntax(client):
    assert client.get('/api/search?q=%22bad:query(').status_code == 200


def test_traceability_is_computed_not_asserted(client):
    rows = client.get("/api/traceability").json()["requirements"]
    assert {r["ps"] for r in rows} >= {"A", "B", "C", "D", "E", "Theme"}
    assert all("metric_value" in r and isinstance(r["tests_present"], dict) for r in rows)


def test_summary_disabled_without_key(client):
    tid = client.get("/api/topics").json()["topics"][0]["topic_id"]
    assert client.post(f"/api/summaries/topic/{tid}").status_code == 503


def test_eval_summary_serves_file_or_not_measured(client):
    j = client.get("/api/eval/summary").json()
    assert "generated_at" in j or j["status"] == "not_yet_measured"
    json.dumps(j)


def test_demo_readonly_blocks_writes_but_allows_demo_actions(client):
    from app.config import settings

    settings.demo_readonly = True
    try:
        assert client.post("/api/replay/start", json={"force": True}).status_code == 403
        assert client.post("/api/pipeline/run").status_code == 403
        assert client.post("/api/collectors/x/targets?target=abc").status_code == 403
        assert client.post("/api/ledger/verify").json()["status"] == "PASS"
        assert client.get("/healthz").json()["demo_readonly"] is True
    finally:
        settings.demo_readonly = False


def test_platforms_cover_all_six_ps_sources(client):
    j = client.get("/api/platforms").json()
    names = [p["platform"] for p in j["platforms"]]
    assert names == ["x", "telegram", "instagram", "facebook", "reddit", "youtube"]
    tiers = {p["platform"]: p["tier"] for p in j["platforms"]}
    assert tiers["x"] == tiers["telegram"] == "essential"
    assert tiers["instagram"] == tiers["facebook"] == "desirable"
    assert all(p["connection"] in ("connected", "ready", "import", "demo") for p in j["platforms"])
    assert client.get("/api/platforms/myspace").status_code == 404


def test_trending_keywords_rank_hashtags(client):
    j = client.get("/api/keywords/trending?limit=5").json()
    assert j["top"] and all(k["keyword"].startswith("#") for k in j["top"])
    assert [k["posts"] for k in j["top"]] == sorted((k["posts"] for k in j["top"]), reverse=True)


def test_comment_filter_splits_emotion_timeline(client):
    n = lambda kind: sum(b["n"] for b in client.get(f"/api/timeline/emotions?bucket=1d&kind={kind}").json()["buckets"])
    assert n("posts") + n("comments") == n("all")


def test_segment_spread_after_segments_stage(client, analysed_db):
    from app.analytics.graph import compute_segments

    compute_segments(analysed_db)
    j = client.get("/api/graph/segment-spread").json()
    assert j["segments"][0]["label"] == "Coordinated group"
    assert j["summary"] == sorted(j["summary"], key=lambda r: r["first_seen"])


def test_situation_is_aggregate_and_k_anonymous(client):
    j = client.get("/api/situation").json()
    assert {"sitrep", "kpis", "sectors", "states", "narratives", "hot_topics"} <= set(j)
    assert j["kpis"]["posts_secured"] > 0 and j["kpis"]["platforms"] >= 1
    levels = {"critical", "elevated", "watch", "normal", "quiet"}
    assert all(s["level"] in levels for s in j["sectors"])
    for st in j["states"]:  # a state is released only when enough distinct accounts back it
        assert st["released"] == (st["posts"] is not None)
        assert set(st) >= {"state", "released"} and "account_id" not in st
    for n in j["narratives"]:
        assert 0 <= n["coordinated_share"] <= 1


def test_signal_review_is_audited_and_approve_opens_a_case(client):
    alert = client.get("/api/alerts").json()["alerts"][0]
    r = client.post(f"/api/alerts/{alert['alert_id']}/review", json={"action": "watchlist"})
    assert r.status_code == 200 and r.json()["status"] == "watchlist" and r.json()["ledger_seq"] > 0
    audit = client.get("/api/audit").json()["entries"]
    assert any(e["action"] == "signal_watchlist" for e in audit)
    r = client.post(f"/api/alerts/{alert['alert_id']}/review", json={"action": "approve"})
    assert r.json()["case"]["case_id"] > 0
    assert client.post("/api/alerts/999999/review", json={"action": "dismiss"}).status_code == 404
    assert client.post(f"/api/alerts/{alert['alert_id']}/review", json={"action": "delete"}).status_code == 422


def test_network_nodes_carry_platform_and_details(client):
    g = client.get("/api/graph?max_nodes=40").json()
    assert all("platform" in n and "followers" in n for n in g["nodes"])
    node = g["nodes"][0]["id"]
    d = client.get(f"/api/graph/node/{node}").json()
    assert d["account_id"] == node and d["platforms"]
    assert not {"state", "age", "location_text", "inferred_state"} & set(d)
    assert client.get("/api/graph/node/does-not-exist").status_code == 404


def test_live_telegram_feed_is_safe_without_a_session(client):
    j = client.get("/api/live/telegram").json()
    assert j["connected"] is False and j["posts"] == []  # tests never hold real credentials


def test_live_feed_channels_come_only_from_config():
    from app.collectors.live_feed import _strict_sector, channels

    assert channels() and all(not c.startswith("@") for c in channels())
    assert _strict_sector("Dam breach: evacuate the reservoir area now") == "infra"
    assert _strict_sector("A quiet birthday at home") == "other"


def test_scoped_audience_is_aggregate_and_says_what_it_counts(client):
    topic = client.get("/api/topics?sort=coordinated&limit=1").json()
    tid = (topic.get("topics", topic))[0]["topic_id"]
    for scope in ("live", f"topic:{tid}"):
        j = client.get(f"/api/demographics?scope={scope}").json()
        assert j["coverage"]["unit"] == "accounts"
        assert j["coverage"]["accounts"] is None or j["coverage"]["accounts"] >= j["k_anon"]
        for d in j["dimensions"].values():
            assert all(b["count"] >= j["k_anon"] for b in d["buckets"])
        assert not FORBIDDEN_KEYS & set(_walk_keys(j))


def test_image_families_group_each_picture_once():
    from app.api.routers.lineage import image_families

    def pair(a, b, h):
        return {"media_id_a": a, "platform_a": "telegram", "first_seen_a": a, "posts_a": 1,
                "media_id_b": b, "platform_b": "x", "first_seen_b": b, "posts_b": 2, "hamming": h}
    fams = image_families([pair("1", "2", 4), pair("1", "3", 6), pair("2", "3", 2), pair("7", "8", 0)])
    assert len(fams) == 2
    big = fams[0]
    assert big["original"]["media_id"] == "1"
    assert [c["media_id"] for c in big["copies"]] == ["2", "3"]
    assert [c["hamming"] for c in big["copies"]] == [4, 6]


def test_media_endpoint_serves_only_known_images(client):
    assert client.get("/api/media/does-not-exist").status_code == 404
    assert client.get("/api/media/..%2F..%2Fetc%2Fpasswd").status_code == 404


def test_organic_graph_has_no_coordinated_accounts(analysed_db):
    import sqlite3

    from app.analytics.graph import build_graph

    with sqlite3.connect(analysed_db) as c:
        flagged = {a for (a,) in c.execute("SELECT account_id FROM coord_accounts WHERE score >= 0.7")}
    assert flagged
    assert not flagged & set(build_graph(analysed_db, organic_only=True).nodes)
