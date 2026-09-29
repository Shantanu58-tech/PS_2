from __future__ import annotations
import argparse
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


ORGANIC_TOPICS = [
    ("cricket", ["#cricket", "#INDvsAUS", "#TeamIndia"], ["Great match!", "What a six!", "India plays well today", "Cricket fever is real"]),
    ("exam", ["#NEET", "#JEE", "#BoardExams"], ["Results out soon", "Studied all night", "Board exam stress is real", "Best of luck everyone"]),
    ("fuel", ["#PetrolPrice", "#DieselPrice"], ["Fuel prices rising again", "Why is petrol so expensive", "Government should reduce taxes"]),
    ("weather", ["#Monsoon", "#Rain", "#Delhi"], ["Heavy rain today", "Roads flooded", "Power cut due to storm"]),
    ("film", ["#Bollywood", "#NewRelease"], ["Watched the new movie", "Amazing film releasing Friday", "Box office collection"]),
    ("traffic", ["#TrafficJam", "#DelhiTraffic"], ["Stuck in traffic for 2 hrs", "Metro is better", "Roads need repair"]),
    ("tech", ["#AI", "#Tech", "#Startup"], ["AI is changing everything", "New app launched", "Tech stocks up"]),
    ("festival", ["#Diwali", "#Holi", "#Festival"], ["Happy Diwali", "Festival season is here", "Celebrations across India"]),
]

HINGLISH_ORGANIC = [
    "Yaar kya scene hai aaj",
    "Bhai sach mein acha laga",
    "Arey yaar bahut maza aaya",
    "Sahi baat hai",
    "Bilkul sahi kaha",
    "Main bhi yahi soch raha tha",
    "Haan bhai agree",
    "Kya baat hai wah",
]

RUMOUR_TEMPLATES = [
    "BREAKING: Varunapur Dam has cracked! Evacuate immediately! #VarunapurDam #Emergency",
    "ALERT: Dam wall cracking in Varunapur - residents must evacuate NOW! #FloodAlert",
    "Varunapur dam crack confirmed by officials - RUN! #VarunapurCrisis",
    "dam crack varunapur confirm ho gaya - bhago! #VarunapurDam",
    "Varunapur Dam toot raha hai - turant nikal jao! #Emergency #FloodWarning",
    "WARNING: Varunapur reservoir showing structural failure - evacuate all downstream! #DamCrack",
    "URGENT: Varunapur dam breach imminent - downstream areas EVACUATE #Breaking",
    "abhi abhi news aai - Varunapur dam crack - please share karo #FloodAlert",
]

SARCASM_DEBUNK = [
    "Oh sure, another WhatsApp forward. Varunapur dam is fine, checked official sources. #FakeNews",
    "Yaar ye forward mat karo, dam bilkul theek hai. Stop spreading panic.",
    "Stop sharing this rumour. No dam crack in Varunapur. Verified.",
    "Classic panic chain. Dam is intact, checked on news. #Debunked",
]

ANXIOUS_ORGANIC_REPLIES = [
    "Oh god, my family lives near there, calling them now",
    "Please share this is serious!",
    "Is this real? Someone verify please",
    "Yaar sach hai kya? Bahut dar lag raha hai",
    "My cousin is in Varunapur district, trying to reach them",
    "Should we trust this? Sharing just in case",
]

CRICKET_FAN_POSTS = [
    "INDIA WON!!! Amazing match!!! #INDvsAUS #Cricket",
    "What a six by Rohit! #CricketMania",
    "India all the way #TeamIndia",
    "Best cricket match ever watched! #INDvsAUS",
    "Kohli is the GOAT #Cricket",
    "India India India!!! #INDvsAUS",
]


def rand_account(seed_base: int, synthetic: bool = False, aged: bool = False) -> dict:
    rng = random.Random(seed_base)
    platforms = ["x", "telegram", "reddit", "youtube"]
    platform = rng.choice(platforms)
    handle = f"user_{seed_base}_{rng.randint(100, 999)}"
    followers = rng.randint(50, 5000)
    if aged:
        followers = rng.randint(1000, 20000)
    created_year = rng.randint(2018, 2023) if aged else rng.randint(2020, 2024)
    return {
        "account_id": f"acc_{seed_base}",
        "platform": platform,
        "handle": handle,
        "display_name": handle.replace("_", " ").title(),
        "bio": rng.choice(["Tech enthusiast", "News addict", "Sports fan", "Student", "Journalist", ""]),
        "location_text": rng.choice(["Delhi", "Mumbai", "Bangalore", "Pune", "Hyderabad", "Chennai", ""]),
        "followers": followers,
        "following": rng.randint(100, 1000),
        "created_at": f"{created_year}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T00:00:00Z",
        "synthetic": synthetic,
    }


def rand_datetime(base: datetime, spread_hours: float, rng: random.Random) -> datetime:
    offset_seconds = rng.gauss(0, spread_hours * 1800)
    return base + timedelta(seconds=offset_seconds)


def generate_scenario(seed: int, output_path: str) -> dict:
    rng = random.Random(seed)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    base_time = datetime(2024, 11, 4, 0, 0, 0, tzinfo=timezone.utc)
    rumour_start = base_time + timedelta(days=3, hours=16, minutes=40)

    posts: list[dict] = []
    accounts: dict[str, dict] = {}
    truth: dict = {
        "coordinated_account_ids": [],
        "rumour_post_ids": [],
        "origin_post_id": None,
        "decoy_topic": "cricket",
        "bridge_account_id": "acc_bridge_1",
        "scenario_seed": seed,
    }

    for i in range(3000):
        acc = rand_account(i, synthetic=True)
        accounts[acc["account_id"]] = acc

    bridge_acc = {
        "account_id": "acc_bridge_1",
        "platform": "x",
        "handle": "bridge_user_1",
        "display_name": "Bridge User",
        "bio": "Connects communities",
        "followers": 5000,
        "following": 2000,
        "synthetic": True,
    }
    accounts["acc_bridge_1"] = bridge_acc

    for day in range(7):
        for hour in range(24):
            bucket_time = base_time + timedelta(days=day, hours=hour)
            n_posts = int(rng.gauss(80, 20))
            for _ in range(max(10, n_posts)):
                topic = rng.choice(ORGANIC_TOPICS)
                acc_id = f"acc_{rng.randint(0, 2999)}"
                acc = accounts.get(acc_id, rand_account(rng.randint(0, 9999), synthetic=True))
                text = rng.choice(topic[2])
                if rng.random() < 0.3:
                    text += " " + rng.choice(HINGLISH_ORGANIC)
                if topic[1]:
                    text += " " + rng.choice(topic[1])
                dt = rand_datetime(bucket_time, 0.5, rng)
                post_id = f"org_{day}_{hour}_{rng.randint(10000,99999)}"
                posts.append({
                    "platform": acc.get("platform", "x"),
                    "post_id": post_id,
                    "author_id": acc["account_id"],
                    "kind": "post",
                    "text": text,
                    "created_at": dt.isoformat(),
                    "hashtags": topic[1],
                    "synthetic": True,
                    "account": acc,
                })

    for i in range(60):
        is_aged = i < 10
        acc_id = f"acc_coord_{i}"
        acc = rand_account(10000 + i, synthetic=True, aged=is_aged)
        acc["account_id"] = acc_id
        acc["platform"] = "x"
        accounts[acc_id] = acc
        truth["coordinated_account_ids"].append(acc_id)

    origin_id = "rumour_origin_telegram_001"
    origin_post = {
        "platform": "telegram",
        "post_id": origin_id,
        "author_id": "acc_coord_0",
        "kind": "post",
        "text": RUMOUR_TEMPLATES[0] + " [image attached - dam crack]",
        "created_at": rumour_start.isoformat(),
        "hashtags": ["#VarunapurDam", "#Emergency"],
        "synthetic": True,
        "account": accounts["acc_coord_0"],
        "has_image": True,
    }
    posts.append(origin_post)
    truth["origin_post_id"] = origin_id
    truth["rumour_post_ids"].append(origin_id)

    for i in range(60):
        acc_id = f"acc_coord_{i}"
        for j in range(rng.randint(3, 8)):
            delay_seconds = 90 * j + rng.gauss(0, 5)
            post_time = rumour_start + timedelta(seconds=delay_seconds)
            tmpl = rng.choice(RUMOUR_TEMPLATES)
            post_id = f"rumour_x_{i}_{j}"
            posts.append({
                "platform": "x",
                "post_id": post_id,
                "author_id": acc_id,
                "kind": "repost" if j > 0 else "post",
                "text": tmpl,
                "created_at": post_time.isoformat(),
                "hashtags": ["#VarunapurDam", "#Emergency", "#FloodAlert"],
                "synthetic": True,
                "origin_post_id": origin_id if j == 0 else f"rumour_x_{i}_{j-1}",
                "account": accounts[acc_id],
            })
            truth["rumour_post_ids"].append(post_id)

    for i in range(300):
        acc_id = f"acc_{rng.randint(0, 2999)}"
        acc = accounts.get(acc_id, rand_account(rng.randint(0, 9999), synthetic=True))
        delay = rng.expovariate(1 / 1800)
        post_time = rumour_start + timedelta(seconds=delay)
        text = rng.choice(ANXIOUS_ORGANIC_REPLIES)
        if rng.random() < 0.15:
            text = rng.choice(SARCASM_DEBUNK)
        post_id = f"organic_react_{i}"
        posts.append({
            "platform": rng.choice(["x", "reddit", "youtube"]),
            "post_id": post_id,
            "author_id": acc_id,
            "kind": "reply",
            "text": text,
            "created_at": post_time.isoformat(),
            "parent_post_id": rng.choice(truth["rumour_post_ids"][:10]),
            "synthetic": True,
            "account": acc,
        })

    cricket_start = base_time + timedelta(days=4, hours=14)
    cricket_accounts = [f"acc_cricket_{i}" for i in range(200)]
    for i, acc_id in enumerate(cricket_accounts):
        acc = rand_account(20000 + i, synthetic=True)
        acc["account_id"] = acc_id
        accounts[acc_id] = acc
    fan_accounts = [f"acc_fan_{i}" for i in range(50)]
    for i, acc_id in enumerate(fan_accounts):
        acc = rand_account(25000 + i, synthetic=True)
        acc["account_id"] = acc_id
        accounts[acc_id] = acc

    for i in range(500):
        acc_id = rng.choice(cricket_accounts + fan_accounts)
        delay = rng.expovariate(1 / 300)
        if acc_id.startswith("acc_fan_"):
            delay = rng.uniform(0, 120)
        post_time = cricket_start + timedelta(seconds=delay * i / 10)
        post_id = f"cricket_{i}"
        posts.append({
            "platform": rng.choice(["x", "reddit"]),
            "post_id": post_id,
            "author_id": acc_id,
            "kind": "post",
            "text": rng.choice(CRICKET_FAN_POSTS),
            "created_at": post_time.isoformat(),
            "hashtags": ["#cricket", "#INDvsAUS", "#TeamIndia"],
            "synthetic": True,
            "account": accounts[acc_id],
        })

    for i in range(20):
        acc_id = "acc_bridge_1"
        half = i < 10
        other_acc = f"acc_coord_{i}" if half else f"acc_cricket_{i}"
        post_time = base_time + timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 23))
        post_id = f"bridge_{i}"
        posts.append({
            "platform": "x",
            "post_id": post_id,
            "author_id": acc_id,
            "kind": "reply",
            "text": rng.choice(ORGANIC_TOPICS[0][2]),
            "created_at": post_time.isoformat(),
            "parent_post_id": other_acc,
            "synthetic": True,
            "account": accounts[acc_id],
        })

    posts.sort(key=lambda p: p["created_at"])

    with open(out_path, "w", encoding="utf-8") as f:
        for post in posts:
            f.write(json.dumps(post, ensure_ascii=False, default=str) + "\n")

    truth_path = out_path.parent / "truth.json"
    with open(truth_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2)

    print(f"Generated {len(posts)} posts, truth at {truth_path}")
    return truth


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", default="replay/scenario_v1.jsonl")
    args = parser.parse_args()
    generate_scenario(args.seed, args.output)
