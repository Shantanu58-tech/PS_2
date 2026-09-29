"""Test setup: fast deterministic fallbacks (no model downloads needed).

EMBED_BACKEND=hashing and the transformer pipelines marked unavailable, so
tests exercise the full code paths in seconds. Model-backed behaviour is
measured by the eval harness instead.
"""
import os
import sqlite3
from pathlib import Path

import pytest

os.environ.setdefault("EMBED_BACKEND", "hashing")
os.environ.setdefault("EMOTION_CACHE", "0")
os.environ["ENABLE_OTS"] = "false"  # never contact real calendars from tests
# Tests must never call real services, even when backend/.env holds real
# credentials: an empty env var overrides the .env file value.
for _secret in ("GEMINI_API_KEY", "X_AUTH_TOKEN", "X_CT0", "TG_API_ID", "TG_API_HASH", "TG_SESSION_STRING",
                "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "YT_API_KEY", "HF_TOKEN"):
    os.environ[_secret] = ""


@pytest.fixture(autouse=True)
def _lexicon_only(monkeypatch):
    import app.nlp.emotion as emotion

    monkeypatch.setattr(emotion, "_failed", {"sentiment", "emotion", "sarcasm", "nli"})
    yield


@pytest.fixture()
def db_path(tmp_path) -> str:
    from app.db.session import init_db_sync
    from app.pipeline.workers import reset_ingestors

    path = str(tmp_path / "test.db")
    init_db_sync(path)
    reset_ingestors()
    yield path
    reset_ingestors()


@pytest.fixture(scope="session")
def mini_scenario(tmp_path_factory) -> tuple[str, dict]:
    """A small full scenario (organic background scaled down) + truth."""
    import json

    from scenario.generate import generate_scenario

    d = tmp_path_factory.mktemp("scenario")
    out = d / "scenario_v1.jsonl"
    truth = generate_scenario(7, str(out), str(d / "media"), organic_target=3000)
    return str(out), {**truth, "_media_dir": str(d / "media"), "_truth": json.loads((d / "truth.json").read_text(encoding="utf-8"))}


@pytest.fixture(scope="session")
def analysed_db(tmp_path_factory, mini_scenario) -> str:
    """Mini scenario replayed through the ledger pipeline + all analytics."""
    import app.nlp.emotion as emotion
    from app.config import settings
    from app.db.session import init_db_sync
    from app.pipeline.workers import reset_ingestors

    scenario, truth = mini_scenario
    db = str(tmp_path_factory.mktemp("adb") / "analysed.db")
    init_db_sync(db)
    reset_ingestors()
    old_media = settings.media_dir
    settings.media_dir = truth["_media_dir"]
    old_failed = emotion._failed
    emotion._failed = {"sentiment", "emotion", "sarcasm", "nli"}
    try:
        from app.collectors.replay import run_replay_sync

        run_replay_sync(scenario, db, analytics=True)
    finally:
        settings.media_dir = old_media
        emotion._failed = old_failed
        reset_ingestors()
    return db


def rows(db: str, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with sqlite3.connect(db) as c:
        c.row_factory = sqlite3.Row
        return c.execute(sql, params).fetchall()


FIXTURES = Path(__file__).parent / "fixtures"
