"""Live smoke run: pull a few records from each collector whose credentials
are configured, show the normalised result, and (with --ingest) push them
through the ledger pipeline. Collectors without credentials are skipped.

    python scripts/check_collectors.py                       # all configured
    python scripts/check_collectors.py telegram --target @somechannel
    python scripts/check_collectors.py x --target narendramodi --record

--record saves raw payloads to backend/tests/fixtures/recorded/<platform>.json
(golden fixtures from real traffic). Telegram's first run asks for your phone
number and login code interactively; run it in a terminal you can type into.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

DEFAULT_TARGETS = {"x": "PIB_India", "telegram": "@durov", "reddit": "india", "youtube": "jNQXAC9IVRw"}


async def check(name: str, target: str, limit: int, record: bool, ingest: bool) -> dict:
    from app.collectors.reddit_praw import RedditCollector
    from app.collectors.telegram_telethon import TelegramCollector
    from app.collectors.x_twscrape import XCollector
    from app.collectors.youtube_api import YouTubeCollector
    from app.pipeline.normalize import normalize

    collector = {"x": XCollector, "telegram": TelegramCollector, "reddit": RedditCollector,
                 "youtube": YouTubeCollector}[name]()
    records = []
    async for raw in collector.backfill(target, limit):
        records.append(raw)
        if len(records) >= limit:
            break
    status = collector.health.state
    if status == "credentials_missing":
        return {"collector": name, "status": "skipped (credentials not provided)"}
    sample = []
    for raw in records[:3]:
        post, acc = normalize(raw)
        sample.append({"post_id": post.post_id, "author": post.author_id, "kind": post.kind,
                       "created_at": post.created_at.isoformat(), "text": post.text[:80]})
    if record and records:
        out = ROOT / "backend" / "tests" / "fixtures" / "recorded"
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{name}.json").write_text(json.dumps([r.payload for r in records[:5]], indent=2, default=str),
                                          encoding="utf-8")
    if ingest and records:
        from app.db.session import init_db_sync
        from app.pipeline.workers import get_ingestor

        init_db_sync()
        get_ingestor().ingest_many(records)
    return {"collector": name, "target": target, "status": status, "records": len(records),
            "errors": collector.health.errors, "last_error": collector.health.last_error, "sample": sample}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("collectors", nargs="*", default=list(DEFAULT_TARGETS))
    ap.add_argument("--target")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--ingest", action="store_true")
    args = ap.parse_args()
    for name in args.collectors:
        try:
            res = asyncio.run(check(name, args.target or DEFAULT_TARGETS[name], args.limit, args.record, args.ingest))
        except Exception as exc:  # report and continue
            res = {"collector": name, "status": "error", "error": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
