from datetime import datetime, timezone
from app.models.canonical import RawRecord
from app.pipeline.normalize import normalize_x, normalize_reddit, normalize_telegram, normalize_youtube


def _raw(platform, payload):
    return RawRecord(platform=platform, collector_id="test", collected_at=datetime.now(timezone.utc), payload=payload)


def test_normalize_x_basic():
    payload = {
        "id": "123",
        "rawContent": "Hello world #test",
        "date": "2024-01-01T12:00:00+00:00",
        "author": {"id": "456", "username": "testuser"},
    }
    post, acc = normalize_x(_raw("x", payload))
    assert post.post_id == "123"
    assert post.platform == "x"
    assert "#test" not in post.hashtags or "test" in post.hashtags
    assert acc is not None
    assert acc.handle == "testuser"


def test_normalize_telegram_basic():
    payload = {
        "id": "789",
        "text": "Telegram message",
        "date": "2024-01-01T12:00:00+00:00",
        "channel": "@testchannel",
    }
    post, acc = normalize_telegram(_raw("telegram", payload))
    assert post.platform == "telegram"
    assert "testchannel" in post.post_id


def test_normalize_reddit_basic():
    payload = {
        "id": "abc",
        "body": "Reddit comment",
        "created_utc": 1704067200.0,
        "author": "redditor",
        "parent_id": "t3_xyz",
        "subreddit": "india",
        "score": 5,
    }
    post, acc = normalize_reddit(_raw("reddit", payload))
    assert post.platform == "reddit"
    assert post.kind == "post"


def test_normalize_youtube_basic():
    payload = {
        "id": "yt1",
        "text": "YouTube comment",
        "published_at": "2024-01-01T12:00:00Z",
        "author": "youtuber",
        "video_id": "abc123",
        "likes": 10,
    }
    post, acc = normalize_youtube(_raw("youtube", payload))
    assert post.platform == "youtube"
    assert post.kind == "comment"
