"""
SATYA-NET Scenario Generator
Generates synthetic social-media posts (marked synthetic=true) for replay testing.

Usage:
    python -m scenario.generate --seed 7 --output replay/scenario_v1.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Content pools
# ---------------------------------------------------------------------------

PLATFORMS = ["x", "telegram", "reddit", "youtube"]

ORGANIC_BIOS = [
    "Software developer at a startup",
    "Student, UPSC aspirant from UP",
    "Journalist covering politics in Delhi",
    "Professor, IIT alumna, researcher",
    "Cricket fan and sports enthusiast",
    "Retired IAS officer",
    "Business entrepreneur, investor",
    "PhD researcher in AI/ML",
    "B.Tech 2nd yr student",
    "Government officer, ministry",
]

ORGANIC_LOCATIONS = [
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata",
    "Pune", "Hyderabad", "Ahmedabad", "Jaipur", "Lucknow",
]

ORGANIC_TOPICS = [
    "New infrastructure project announced in Maharashtra",
    "Cricket match results today",
    "Monsoon update: heavy rains expected in Kerala",
    "Budget session parliament highlights",
    "Startup ecosystem growing rapidly in Bengaluru",
    "University exam results declared",
    "Film review: latest Bollywood release",
    "Agriculture policy changes affect farmers",
    "Tech conference highlights from Pune",
    "Cultural festival celebrated across India",
]

COORD_TOPIC = "BREAKING: Viral political controversy spreading fast"
COORD_HASHTAGS = ["#BreakingNews", "#TrendingNow", "#MustShare"]


def _make_account(rng: random.Random, prefix: str, idx: int, platform: str,
                  bio: str | None = None, location: str | None = None) -> dict:
    return {
        "account_id": f"{prefix}_{idx:04d}",
        "platform": platform,
        "handle": f"{prefix}{idx}",
        "display_name": f"{prefix.title()} User {idx}",
        "bio": bio or rng.choice(ORGANIC_BIOS),
        "location_text": location or rng.choice(ORGANIC_LOCATIONS),
        "followers": rng.randint(50, 5000),
        "following": rng.randint(30, 3000),
        "verified": False,
        "synthetic": True,
    }


def _ts(base: datetime, offset_seconds: float) -> str:
    return (base + timedelta(seconds=offset_seconds)).isoformat()


def generate_scenario(seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    records: list[dict] = []
    base_time = datetime(2026, 9, 1, 6, 0, 0, tzinfo=timezone.utc)

    # ------------------------------------------------------------------
    # 1. Organic posts — 150 posts across platforms over 24 hours
    # ------------------------------------------------------------------
    n_organic_accounts = 30
    organic_accounts = [
        _make_account(rng, "organic", i, rng.choice(PLATFORMS))
        for i in range(n_organic_accounts)
    ]

    for i in range(150):
        acc = rng.choice(organic_accounts)
        # Organic: Poisson-like arrival (mean gap ~576 s over 86400 s / 150 posts)
        offset = rng.uniform(0, 86400)
        topic = rng.choice(ORGANIC_TOPICS)
        hashtags = []
        if rng.random() < 0.3:
            hashtags = [rng.choice(["#India", "#News", "#Tech", "#Sports", "#Bollywood"])]
        records.append({
            "platform": acc["platform"],
            "post_id": f"org_{i:04d}",
            "author_id": acc["account_id"],
            "kind": rng.choice(["post", "reply", "repost"]),
            "text": topic,
            "created_at": _ts(base_time, offset),
            "collected_at": _ts(base_time, offset + rng.uniform(1, 60)),
            "hashtags": hashtags,
            "metrics": {"likes": rng.randint(0, 500), "reposts": rng.randint(0, 100)},
            "lang": "en",
            "synthetic": True,
            # embed account info for replay collector
            "_account": acc,
        })

    # ------------------------------------------------------------------
    # 2. Coordinated inauthentic burst — 40 bot accounts, 200 near-identical
    #    posts in a 5-minute window (300 s) starting at T+5 h
    # ------------------------------------------------------------------
    burst_start = 5 * 3600  # 5 hours in
    n_coord = 40
    coord_accounts = [
        _make_account(rng, "coord", i, rng.choice(["x", "telegram"]),
                      bio="Sharing important updates",
                      location="Unknown")
        for i in range(n_coord)
    ]

    for i in range(200):
        acc = coord_accounts[i % n_coord]
        # Very tight burst: gaps of ~1.5 s on average (300 s / 200 posts)
        offset = burst_start + rng.uniform(0, 300)
        slight_variation = rng.choice([
            COORD_TOPIC,
            COORD_TOPIC + " Share NOW!",
            "RT: " + COORD_TOPIC,
            COORD_TOPIC + " #Viral",
        ])
        records.append({
            "platform": acc["platform"],
            "post_id": f"coord_{i:04d}",
            "author_id": acc["account_id"],
            "kind": "post" if i % 5 != 0 else "repost",
            "text": slight_variation,
            "created_at": _ts(base_time, offset),
            "collected_at": _ts(base_time, offset + rng.uniform(0.5, 5)),
            "hashtags": COORD_HASHTAGS,
            "metrics": {"likes": rng.randint(0, 20), "reposts": rng.randint(0, 50)},
            "lang": "en",
            "synthetic": True,
            "_account": acc,
        })

    # ------------------------------------------------------------------
    # 3. Sort by created_at
    # ------------------------------------------------------------------
    records.sort(key=lambda r: r["created_at"])
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="SATYA-NET scenario generator")
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    parser.add_argument("--output", type=str, default="replay/scenario_v1.jsonl",
                        help="Output JSONL path")
    args = parser.parse_args()

    records = generate_scenario(seed=args.seed)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Generated {len(records)} synthetic posts -> {out_path}")
    n_organic = sum(1 for r in records if r["post_id"].startswith("org_"))
    n_coord = sum(1 for r in records if r["post_id"].startswith("coord_"))
    print(f"  organic: {n_organic}, coordinated burst: {n_coord}")


if __name__ == "__main__":
    main()
