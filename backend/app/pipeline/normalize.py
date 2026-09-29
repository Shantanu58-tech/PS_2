from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Literal
from app.models.canonical import Post, Account, RawRecord

PostKind = Literal["post", "reply", "repost", "quote", "forward", "comment"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#(\w+)", text)


def _extract_mentions(text: str) -> list[str]:
    return re.findall(r"@(\w+)", text)


def _extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://\S+", text)


def normalize_x(raw: RawRecord) -> tuple[Post, Account | None]:
    p = raw.payload
    text = p.get("rawContent") or p.get("text") or p.get("full_text") or ""
    author = p.get("author") or p.get("user") or {}
    author_id = str(p.get("author_id") or author.get("id") or "unknown")
    post_id = str(p.get("id") or p.get("post_id") or "unknown")
    created_raw = p.get("date") or p.get("created_at") or _now().isoformat()
    try:
        created_at = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
    except Exception:
        created_at = _now()

    kind: PostKind = "post"
    if p.get("inReplyToTweetId") or p.get("in_reply_to_tweet_id"):
        kind = "reply"
    elif p.get("retweetedTweet") or p.get("retweeted_tweet"):
        kind = "repost"
    elif p.get("quotedTweet") or p.get("quoted_tweet"):
        kind = "quote"

    post = Post(
        platform="x",
        post_id=post_id,
        author_id=author_id,
        kind=kind,
        text=text,
        created_at=created_at,
        collected_at=raw.collected_at,
        parent_post_id=str(p["inReplyToTweetId"]) if p.get("inReplyToTweetId") else None,
        origin_post_id=str(
            (p.get("retweetedTweet") or {}).get("id")
            or (p.get("quotedTweet") or {}).get("id")
            or ""
        ) or None,
        hashtags=_extract_hashtags(text),
        mentions=_extract_mentions(text),
        urls=_extract_urls(text),
        metrics={
            "likes": p.get("likeCount") or p.get("favorite_count") or 0,
            "reposts": p.get("retweetCount") or p.get("retweet_count") or 0,
        },
        synthetic=p.get("synthetic", False),
    )
    acc = None
    if author:
        acc = Account(
            platform="x",
            account_id=author_id,
            handle=author.get("username") or author.get("screen_name"),
            display_name=author.get("displayname") or author.get("name"),
            bio=author.get("rawDescription") or author.get("description"),
            location_text=author.get("location"),
            created_at=_parse_dt(author.get("created") or author.get("created_at")),
            followers=author.get("followersCount") or author.get("followers_count"),
            following=author.get("friendsCount") or author.get("friends_count"),
            verified=author.get("verified"),
        )
    return post, acc


def normalize_telegram(raw: RawRecord) -> tuple[Post, Account | None]:
    p = raw.payload
    text = p.get("text") or p.get("message") or ""
    channel = p.get("channel") or p.get("peer_id") or "unknown"
    msg_id = str(p.get("id") or "unknown")
    date_raw = p.get("date") or _now().isoformat()
    try:
        created_at = datetime.fromisoformat(str(date_raw).replace("Z", "+00:00"))
    except Exception:
        created_at = _now()

    fwd = p.get("fwd_from")
    origin = None
    if isinstance(fwd, dict) and fwd.get("from_id"):
        origin = f"{fwd['from_id']}_{fwd.get('channel_post') or ''}".rstrip("_")
    elif fwd:
        origin = str(fwd)
    post = Post(
        platform="telegram",
        post_id=f"{channel}_{msg_id}",
        author_id=str(p.get("from_id") or channel),
        kind="forward" if fwd else ("reply" if p.get("reply_to") else "post"),
        text=text,
        created_at=created_at,
        collected_at=raw.collected_at,
        parent_post_id=f"{channel}_{p['reply_to']}" if p.get("reply_to") else None,
        origin_post_id=origin,
        channel_or_community=channel,
        hashtags=_extract_hashtags(text),
        urls=_extract_urls(text),
        metrics={"views": p.get("views") or 0, "forwards": p.get("forwards") or 0},
        synthetic=p.get("synthetic", False),
    )
    return post, None


def normalize_reddit(raw: RawRecord) -> tuple[Post, Account | None]:
    p = raw.payload
    text = p.get("body") or p.get("selftext") or ""
    post_id = str(p.get("id") or "unknown")
    ts = p.get("created_utc") or 0
    created_at = datetime.fromtimestamp(float(ts), tz=timezone.utc) if ts else _now()
    post = Post(
        platform="reddit",
        post_id=post_id,
        author_id=str(p.get("author") or "unknown"),
        kind="comment" if (p.get("parent_id") or "").startswith("t1_") else "post",
        text=text,
        created_at=created_at,
        collected_at=raw.collected_at,
        parent_post_id=(p.get("parent_id") or "")[3:] or None,
        channel_or_community=str(p.get("subreddit") or ""),
        hashtags=_extract_hashtags(text),
        urls=_extract_urls(text),
        metrics={"score": p.get("score") or 0},
        synthetic=p.get("synthetic", False),
    )
    acc = Account(
        platform="reddit",
        account_id=str(p.get("author") or "unknown"),
        handle=str(p.get("author") or "unknown"),
    ) if p.get("author") else None
    return post, acc


def normalize_youtube(raw: RawRecord) -> tuple[Post, Account | None]:
    p = raw.payload
    text = p.get("text") or p.get("textDisplay") or ""
    post_id = str(p.get("id") or "unknown")
    date_raw = p.get("published_at") or p.get("publishedAt") or _now().isoformat()
    try:
        created_at = datetime.fromisoformat(str(date_raw).replace("Z", "+00:00"))
    except Exception:
        created_at = _now()
    post = Post(
        platform="youtube",
        post_id=post_id,
        author_id=str(p.get("author") or "unknown"),
        kind="reply" if p.get("parent_id") else "comment",
        text=text,
        created_at=created_at,
        collected_at=raw.collected_at,
        parent_post_id=p.get("parent_id"),
        channel_or_community=str(p.get("video_id") or ""),
        metrics={"likes": p.get("likes") or 0},
        synthetic=p.get("synthetic", False),
    )
    acc = Account(
        platform="youtube",
        account_id=str(p.get("author") or "unknown"),
        handle=str(p.get("author") or "unknown"),
    ) if p.get("author") else None
    return post, acc


_POST_PLATFORMS = {"x", "telegram", "reddit", "youtube", "instagram", "facebook", "synthetic"}
_POST_KINDS = {"post", "reply", "repost", "quote", "forward", "comment"}


def is_canonical_payload(p: dict) -> bool:
    """Scenario / replay records already use canonical field names."""
    return "post_id" in p and "author_id" in p


def normalize_synthetic(raw: RawRecord) -> tuple[Post, Account | None]:
    """Normalise a record that is already in canonical shape (scenario / replay).

    Replay records carry their original platform (x, telegram, ...) but use
    canonical field names (post_id, author_id, created_at), so they must not
    be routed through the platform-native normalisers.
    """
    p = raw.payload
    platform = p.get("platform", "synthetic")
    if platform not in _POST_PLATFORMS:
        platform = "synthetic"
    kind = p.get("kind", "post")
    if kind not in _POST_KINDS:
        kind = "post"
    text = p.get("text") or ""
    post = Post(
        platform=platform,
        post_id=str(p.get("post_id") or p.get("id") or "syn_unknown"),
        author_id=str(p.get("author_id") or "unknown"),
        kind=kind,
        text=text,
        created_at=datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")) if p.get("created_at") else _now(),
        collected_at=raw.collected_at,
        parent_post_id=p.get("parent_post_id"),
        origin_post_id=p.get("origin_post_id"),
        channel_or_community=p.get("channel_or_community"),
        lang=p.get("lang"),
        hashtags=[h.lstrip("#") for h in (p.get("hashtags") or [])] or _extract_hashtags(text),
        mentions=p.get("mentions") or _extract_mentions(text),
        urls=p.get("urls") or _extract_urls(text),
        metrics=p.get("metrics") or {},
        synthetic=bool(p.get("synthetic", True)),
    )
    acc = None
    a = p.get("account") or p.get("_account")
    if a:
        created = a.get("created_at")
        acc = Account(
            platform=platform,
            account_id=str(a.get("account_id") or p.get("author_id") or "unknown"),
            handle=a.get("handle"),
            display_name=a.get("display_name"),
            bio=a.get("bio"),
            location_text=a.get("location_text"),
            created_at=datetime.fromisoformat(str(created).replace("Z", "+00:00")) if created else None,
            followers=a.get("followers"),
            following=a.get("following"),
            verified=a.get("verified"),
            synthetic=bool(a.get("synthetic", True)),
        )
    return post, acc


NORMALIZERS = {
    "x": normalize_x,
    "telegram": normalize_telegram,
    "reddit": normalize_reddit,
    "youtube": normalize_youtube,
    "synthetic": normalize_synthetic,
}


def normalize(raw: RawRecord) -> tuple[Post, Account | None]:
    if raw.collector_id == "replay" or is_canonical_payload(raw.payload):
        return normalize_synthetic(raw)
    fn = NORMALIZERS.get(raw.platform) or normalize_synthetic
    return fn(raw)
