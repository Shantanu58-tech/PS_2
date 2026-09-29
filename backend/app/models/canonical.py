from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class Media(BaseModel):
    media_id: str
    kind: Literal["image", "video", "gif"]
    url: str | None = None
    local_path: str | None = None
    sha256: str
    phash: str | None = None
    ocr_text: str | None = None


class Post(BaseModel):
    platform: Literal["x", "telegram", "reddit", "youtube", "instagram", "facebook", "synthetic"]
    post_id: str
    author_id: str
    kind: Literal["post", "reply", "repost", "quote", "forward", "comment"]
    text: str
    created_at: datetime
    collected_at: datetime
    parent_post_id: str | None = None
    root_post_id: str | None = None
    origin_post_id: str | None = None
    channel_or_community: str | None = None
    lang: str | None = None
    hashtags: list[str] = []
    mentions: list[str] = []
    urls: list[str] = []
    media: list[Media] = []
    metrics: dict = {}
    synthetic: bool = False
    ledger_seq: int | None = None


class Account(BaseModel):
    platform: Literal["x", "telegram", "reddit", "youtube", "instagram", "facebook", "synthetic"]
    account_id: str
    handle: str | None = None
    display_name: str | None = None
    bio: str | None = None
    location_text: str | None = None
    created_at: datetime | None = None
    followers: int | None = None
    following: int | None = None
    verified: bool | None = None
    synthetic: bool = False


class RawRecord(BaseModel):
    platform: str
    collector_id: str
    collected_at: datetime
    payload: dict
    media_bytes: bytes | None = None
