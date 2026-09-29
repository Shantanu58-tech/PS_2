"""Collectors: golden-fixture normalisation per platform, payload builders,
IG/FB import, and resilience (backoff + circuit breaker)."""
import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.canonical import RawRecord
from app.pipeline.normalize import normalize
from tests.conftest import FIXTURES


def _raw(platform: str, payload: dict, collector: str | None = None) -> RawRecord:
    return RawRecord(platform=platform, collector_id=collector or platform,
                     collected_at=datetime.now(timezone.utc), payload=payload)


def test_x_golden_fixture():
    from app.collectors.x_twscrape import tweet_to_payload

    payload = tweet_to_payload((FIXTURES / "x_tweet.json").read_text())
    post, acc = normalize(_raw("x", payload))
    assert post.platform == "x" and post.post_id == "1854123456789012345"
    assert post.author_id == "99887766"
    assert post.kind == "quote" and post.origin_post_id == "1854120000000000000"
    assert "VarunapurDam" in post.hashtags and "cityalerts" in post.mentions
    assert post.created_at.tzinfo is not None
    assert acc.handle == "civicwatch" and acc.location_text == "Pune, India"
    assert acc.created_at.year == 2019 and acc.followers == 5400


def test_telegram_golden_fixture_keeps_forward_header():
    payload = json.loads((FIXTURES / "telegram_message.json").read_text())
    post, _ = normalize(_raw("telegram", payload))
    assert post.post_id == "@varunapur_updates_5012"
    assert post.kind == "forward"
    assert post.origin_post_id == "1300123456_811"  # structured fwd_from, not str(object)


def test_telegram_message_to_payload_from_telethon_like_object():
    from app.collectors.telegram_telethon import message_to_payload

    fwd = SimpleNamespace(from_id=SimpleNamespace(channel_id=77), channel_post=9,
                          date=datetime(2024, 11, 7, tzinfo=timezone.utc))
    msg = SimpleNamespace(id=1, date=datetime(2024, 11, 7, 1, tzinfo=timezone.utc), message="hi",
                          views=5, forwards=1, from_id=None, fwd_from=fwd, reply_to_msg_id=None, media=None)
    p = message_to_payload(msg, "@chan")
    assert p["fwd_from"] == {"from_id": "77", "channel_post": 9, "date": "2024-11-07T00:00:00+00:00"}


def test_reddit_golden_fixture():
    payload = json.loads((FIXTURES / "reddit_comment.json").read_text())
    post, acc = normalize(_raw("reddit", payload))
    assert post.kind == "comment" and post.parent_post_id == "kq3x1aa"
    assert post.channel_or_community == "pune" and acc.account_id == "pune_resident"


def test_youtube_golden_fixture_includes_replies_keyed_by_channel_id():
    from app.collectors.youtube_api import thread_to_payloads

    item = json.loads((FIXTURES / "youtube_thread.json").read_text())
    payloads = thread_to_payloads(item, "vid123")
    assert len(payloads) == 2
    top, reply = (normalize(_raw("youtube", p))[0] for p in payloads)
    assert top.kind == "comment" and top.author_id == "UCravi000111"
    assert reply.kind == "reply" and reply.parent_post_id == "UgzTOP123"


def test_facebook_csv_import():
    from app.collectors.import_csv import read_csv

    records = read_csv(FIXTURES / "facebook_export.csv", "facebook")
    assert len(records) == 2
    post, _ = normalize(records[0])
    assert post.platform == "facebook" and post.author_id == "varunapurnews"
    assert post.created_at.isoformat() == "2024-11-07T11:50:00+00:00"  # 17:20 IST
    assert post.synthetic is False


def test_import_rejects_other_platforms():
    from app.collectors.import_csv import read_csv_text

    with pytest.raises(ValueError):
        read_csv_text("text\nhello\n", "x")


def test_backoff_retries_then_succeeds():
    from app.collectors.health import CollectorHealth, call_with_backoff

    h = CollectorHealth("t")
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("boom")
        return "ok"

    async def no_sleep(_):
        return None

    assert asyncio.run(call_with_backoff(h, flaky, sleep=no_sleep)) == "ok"
    assert calls["n"] == 3 and h.errors == 2 and h.state == "ok"


def test_circuit_breaker_opens_and_blocks():
    from app.collectors.health import CircuitOpen, CollectorHealth, call_with_backoff

    h = CollectorHealth("t", failure_threshold=3)

    async def always_fail():
        raise TimeoutError("down")

    async def no_sleep(_):
        return None

    with pytest.raises(TimeoutError):
        asyncio.run(call_with_backoff(h, always_fail, retries=5, sleep=no_sleep))
    assert h.circuit_open and h.state == "circuit_open"
    with pytest.raises(CircuitOpen):
        asyncio.run(call_with_backoff(h, always_fail, sleep=no_sleep))


def test_collectors_without_credentials_yield_nothing():
    from app.collectors.reddit_praw import RedditCollector
    from app.collectors.x_twscrape import XCollector
    from app.collectors.youtube_api import YouTubeCollector

    async def drain(c):
        return [r async for r in c.stream(["t"])]

    for c in (XCollector(), RedditCollector(), YouTubeCollector()):
        assert asyncio.run(drain(c)) == []
        assert c.health.state == "credentials_missing"
