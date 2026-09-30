"""Synthetic Instagram and Facebook export CSVs for the demo scenario.

Neither platform offers a free live API for public posts, so DEEPASTAMBHA ingests
them from analyst-supplied exports (Meta Content Library style CSV). This
script writes a fictional sample in that format covering the same week as the
replay scenario, including the Varunapur dam rumour reaching a Facebook
residents' group and Instagram screenshots. Every row has synthetic=true.

    python scenario/meta_export_sample.py --out data/samples
"""
from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = datetime(2024, 11, 4, tzinfo=timezone.utc)
RUMOUR = datetime(2024, 11, 7, 16, 40, tzinfo=timezone.utc)

IG_POSTS = {
    "cricket": ["What a catch!! #INDvsAUS #TeamIndia", "Stadium vibes tonight #Cricket", "Kohli fans assemble #TeamIndia",
                "Match day outfit ready #INDvsAUS", "Yeh six dekha kya? #Cricket"],
    "festival": ["Diwali lights at home #Diwali #Festival", "Rangoli done! #Diwali", "Festive sweets haul #Festival",
                 "Family time this Diwali #Diwali"],
    "film": ["Movie night with the gang #Bollywood", "That climax though #NewRelease", "First day first show #Bollywood"],
    "weather": ["Monsoon mood #Rain", "Clouds over the city #Monsoon", "Rainy chai time #Rain"],
    "food": ["Street food crawl #Foodie", "Homemade biryani #Foodie", "Best vada pav in town #Foodie"],
}
IG_COMMENTS = ["So pretty!", "Love this", "Amazing", "Where is this?", "Bahut badhiya", "Need this", "Wow",
               "Great shot", "Haha so true", "Same here"]
IG_RUMOUR = ["Is this real?? Varunapur dam crack news everywhere #VarunapurDam",
             "Saw this on my feed, praying for Varunapur #VarunapurDam",
             "Screenshot from Telegram: dam crack?! Anyone confirm? #FloodAlert"]
IG_RUMOUR_COMMENTS = ["Scary, my relatives live there", "Please verify before sharing", "Dar lag raha hai yaar",
                      "Is this confirmed?", "Officials said it's fake", "Praying for everyone"]

FB_POSTS = {
    "cricket": ["Who else watched the match today? #INDvsAUS", "Proud of Team India #TeamIndia"],
    "fuel": ["Petrol price went up again in our area #PetrolPrice", "Diesel costlier this week #DieselPrice"],
    "weather": ["Heavy rain in our colony, roads flooded #Monsoon", "Power cut since morning due to storm #Rain"],
    "festival": ["Society Diwali celebration photos #Diwali", "Festival market is so crowded #Festival"],
    "traffic": ["Avoid the highway, huge jam #TrafficJam", "Metro is faster than road today #DelhiTraffic"],
}
FB_COMMENTS = ["Agreed", "True", "Thanks for sharing", "Same in our area", "Very nice", "Sahi baat",
               "Hope it improves", "Happy Diwali to all"]
FB_RUMOUR_SHARE = ("URGENT - forwarded: Varunapur Dam has cracked, evacuate now! Share with everyone in the group "
                   "#VarunapurDam #Emergency")
FB_RUMOUR_COMMENTS = ["Oh god is this true? Calling my family", "Please share, this is serious", "Kya sach mein?",
                      "My parents live downstream, very worried", "Someone confirm with the collector office",
                      "Packing bags just in case", "Stop spreading panic, check official news",
                      "Dam officials say it is safe, this is fake"]
FB_DEBUNK = ("District Administration Varunapur: The Varunapur Dam is safe. Reports of a crack are false. "
             "Please do not forward unverified messages. #VarunapurDam #FactCheck")


def _ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _row(pid: str, author: str, kind: str, text: str, dt: datetime, parent: str = "", likes: int = 0,
         comments: int = 0, shares: int = 0) -> dict:
    return {"id": pid, "username": author, "type": kind, "text": text, "created_time": _ts(dt),
            "parent_id": parent, "likes": likes, "comments": comments, "shares": shares, "synthetic": "true"}


def instagram(rng: random.Random) -> list[dict]:
    rows: list[dict] = []
    users = [f"ig_{rng.choice(['priya', 'rahul', 'aditi', 'arjun', 'neha', 'vikram', 'sneha', 'karan'])}_{i}"
             for i in range(320)]
    for day in range(7):
        for _ in range(55):
            topic = rng.choice(list(IG_POSTS))
            dt = BASE + timedelta(days=day, hours=rng.uniform(3, 18))
            pid = f"ig_{day}_{len(rows)}"
            rows.append(_row(pid, rng.choice(users), "reel" if rng.random() < 0.4 else "photo",
                             rng.choice(IG_POSTS[topic]), dt, likes=rng.randint(20, 4000),
                             comments=rng.randint(0, 60), shares=rng.randint(0, 40)))
            for _ in range(rng.randint(0, 3)):
                rows.append(_row(f"{pid}_c{len(rows)}", rng.choice(users), "comment", rng.choice(IG_COMMENTS),
                                 dt + timedelta(minutes=rng.uniform(2, 240)), parent=pid, likes=rng.randint(0, 30)))
    for i in range(14):  # the rumour arrives as Telegram screenshots
        dt = RUMOUR + timedelta(minutes=35 + rng.uniform(0, 150))
        pid = f"ig_rumour_{i}"
        rows.append(_row(pid, rng.choice(users), "photo", rng.choice(IG_RUMOUR), dt, likes=rng.randint(50, 900),
                         comments=rng.randint(5, 40), shares=rng.randint(10, 200)))
        for _ in range(rng.randint(2, 6)):
            rows.append(_row(f"{pid}_c{len(rows)}", rng.choice(users), "comment", rng.choice(IG_RUMOUR_COMMENTS),
                             dt + timedelta(minutes=rng.uniform(1, 90)), parent=pid))
    return rows


def facebook(rng: random.Random) -> list[dict]:
    rows: list[dict] = []
    users = [f"fb_{rng.choice(['sunita', 'rajesh', 'meena', 'anil', 'kavita', 'suresh', 'pooja', 'deepak'])}_{i}"
             for i in range(300)]
    for day in range(7):
        for _ in range(45):
            topic = rng.choice(list(FB_POSTS))
            dt = BASE + timedelta(days=day, hours=rng.uniform(1, 17))
            pid = f"fb_{day}_{len(rows)}"
            rows.append(_row(pid, rng.choice(users), "status", rng.choice(FB_POSTS[topic]), dt,
                             likes=rng.randint(2, 600), comments=rng.randint(0, 40), shares=rng.randint(0, 30)))
            for _ in range(rng.randint(0, 4)):
                rows.append(_row(f"{pid}_c{len(rows)}", rng.choice(users), "comment", rng.choice(FB_COMMENTS),
                                 dt + timedelta(minutes=rng.uniform(2, 300)), parent=pid, likes=rng.randint(0, 20)))
    share_dt = RUMOUR + timedelta(minutes=27)  # forwarded into a residents' group
    rows.append(_row("fb_rumour_share", "fb_varunapur_residents_group", "share", FB_RUMOUR_SHARE, share_dt,
                     likes=410, comments=180, shares=950))
    for i in range(90):
        rows.append(_row(f"fb_rumour_c{i}", rng.choice(users), "comment", rng.choice(FB_RUMOUR_COMMENTS),
                         share_dt + timedelta(minutes=rng.expovariate(1 / 40)), parent="fb_rumour_share"))
    debunk_dt = RUMOUR + timedelta(hours=2, minutes=50)
    rows.append(_row("fb_debunk", "fb_district_admin_varunapur", "status", FB_DEBUNK, debunk_dt,
                     likes=2300, comments=240, shares=3100))
    for i in range(25):
        rows.append(_row(f"fb_debunk_c{i}", rng.choice(users), "comment",
                         rng.choice(["Thank you for clarifying", "Relief!", "People should stop forwarding",
                                     "Thank god it's fake"]),
                         debunk_dt + timedelta(minutes=rng.uniform(1, 120)), parent="fb_debunk"))
    return rows


def write(rows: list[dict], path: Path) -> None:
    rows.sort(key=lambda r: r["created_time"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/samples")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    write(instagram(rng), Path(a.out) / "instagram_export_sample.csv")
    write(facebook(rng), Path(a.out) / "facebook_export_sample.csv")
