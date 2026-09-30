"""
DEEPASTAMBHA scenario generator v2 (PRD section 10.1). Fully fictional; every
object carries synthetic=true and the UI shows a SIMULATED banner.

7 days, ~40k posts:
  * Organic background: 3,000 accounts, IST diurnal activity, gamma-distributed
    (bursty) inter-arrival times, 8 everyday topics in English, Hinglish,
    Devanagari Hindi and a small Tamil/Bengali share; reply trees and mentions.
  * Planted narrative: "Varunapur Dam has cracked" - a meme image with Hinglish
    overlay posted in a Telegram channel at T0 = day 4 22:10 IST, forwarded in
    Telegram, then amplified on X +12 min by 60 coordinated accounts posting
    template variants every ~90 s +/- 5 s (10 of them "aged" accounts).
  * Organic pickup: 300 accounts reply anxiously; sarcastic debunks included.
  * Organic decoy: a cricket-win surge (bigger than the rumour) from genuine
    accounts plus a legitimate fan-club swarm posting near-simultaneously -
    it must NOT produce a high-priority alert.
  * Bridge: one account linking the rumour and cricket communities.
  * Image variants of the meme: resize, JPEG q30, crop 10%, watermark.
Ground truth goes to truth.json next to the scenario file.

Usage:
    python -m scenario.generate --seed 7          # demo / validation seed
    python -m scenario.generate --seed 11 --output replay/scenario_seed11.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_TIME = datetime(2024, 11, 4, 0, 0, 0, tzinfo=timezone.utc)
T0 = BASE_TIME + timedelta(days=3, hours=16, minutes=40)  # day 4, 22:10 IST
N_ACCOUNTS = 3000
TARGET_ORGANIC = 36000

# topic -> hashtags, {lang: templates}
TOPICS: dict[str, tuple[list[str], dict[str, list[str]]]] = {
    "cricket": (["#cricket", "#INDvsAUS", "#TeamIndia"], {
        "en": ["Great match today!", "What a six!", "India plays well today", "Cricket fever is real",
               "That catch was unbelievable", "Bowling attack looks sharp"],
        "hi-Latn": ["Kya match tha yaar", "Bhai kya shot maara", "Aaj toh India jeetega pakka"],
        "hi": ["क्या शानदार मैच था", "भारत आज जरूर जीतेगा", "क्या छक्का मारा"],
        "ta": ["அருமையான போட்டி இன்று"], "bn": ["দারুণ ম্যাচ আজ"],
    }),
    "exam": (["#NEET", "#JEE", "#BoardExams"], {
        "en": ["Results out soon", "Studied all night", "Board exam stress is real", "Best of luck everyone",
               "Paper was tougher than expected"],
        "hi-Latn": ["Exam ka tension bahut hai", "Result kab aayega yaar", "Padhai karte karte thak gaya"],
        "hi": ["परीक्षा का तनाव बहुत है", "परिणाम जल्द आएगा"],
        "ta": ["தேர்வு முடிவுகள் விரைவில்"], "bn": ["পরীক্ষার ফলাফল শীঘ্রই"],
    }),
    "fuel": (["#PetrolPrice", "#DieselPrice"], {
        "en": ["Fuel prices rising again", "Why is petrol so expensive", "Government should reduce taxes",
               "Diesel hike will push up prices"],
        "hi-Latn": ["Petrol phir se mehenga ho gaya", "Itna mehenga petrol kyun hai"],
        "hi": ["पेट्रोल फिर महंगा हो गया", "सरकार को टैक्स कम करना चाहिए"],
        "ta": ["பெட்ரோல் விலை மீண்டும் உயர்வு"], "bn": ["পেট্রোলের দাম আবার বাড়ল"],
    }),
    "weather": (["#Monsoon", "#Rain", "#Delhi"], {
        "en": ["Heavy rain today", "Roads flooded near my area", "Power cut due to storm",
               "Lovely weather this evening"],
        "hi-Latn": ["Aaj bahut baarish ho rahi hai", "Sadak pe paani bhar gaya"],
        "hi": ["आज बहुत बारिश हो रही है", "सड़कों पर पानी भर गया"],
        "ta": ["இன்று கனமழை"], "bn": ["আজ প্রচুর বৃষ্টি"],
    }),
    "film": (["#Bollywood", "#NewRelease"], {
        "en": ["Watched the new movie", "Amazing film releasing Friday", "Box office collection looks huge",
               "Songs in this film are great"],
        "hi-Latn": ["Movie ekdum mast thi", "Picture dekh ke maza aa gaya"],
        "hi": ["फिल्म बहुत अच्छी थी", "नई फिल्म शुक्रवार को आ रही है"],
        "ta": ["புதிய படம் அருமை"], "bn": ["নতুন সিনেমাটা দারুণ"],
    }),
    "traffic": (["#TrafficJam", "#DelhiTraffic"], {
        "en": ["Stuck in traffic for 2 hrs", "Metro is better than driving", "Roads need repair",
               "Signal not working at the junction"],
        "hi-Latn": ["Traffic mein phas gaya yaar", "Metro hi best hai"],
        "hi": ["ट्रैफिक में दो घंटे फंसा रहा", "मेट्रो ही सबसे अच्छी है"],
        "ta": ["போக்குவரத்து நெரிசல் அதிகம்"], "bn": ["যানজটে আটকে আছি"],
    }),
    "tech": (["#AI", "#Tech", "#Startup"], {
        "en": ["AI is changing everything", "New app launched today", "Tech stocks up this week",
               "Startup funding news is exciting"],
        "hi-Latn": ["Naya app launch hua hai", "AI sab badal raha hai"],
        "hi": ["नया ऐप लॉन्च हुआ है", "एआई सब कुछ बदल रहा है"],
        "ta": ["புதிய செயலி அறிமுகம்"], "bn": ["নতুন অ্যাপ চালু হয়েছে"],
    }),
    "festival": (["#Diwali", "#Festival"], {
        "en": ["Happy Diwali everyone", "Festival season is here", "Celebrations across India tonight",
               "Sweets and lights everywhere"],
        "hi-Latn": ["Diwali ki bahut shubhkamnayein", "Tyohar ka mahaul hai"],
        "hi": ["दिवाली की हार्दिक शुभकामनाएं", "त्योहार का माहौल है"],
        "ta": ["தீபாவளி வாழ்த்துக்கள்"], "bn": ["শুভ দীপাবলি"],
    }),
}
LANG_WEIGHTS = [("en", 0.52), ("hi-Latn", 0.28), ("hi", 0.14), ("ta", 0.03), ("bn", 0.03)]
REPLY_OPENERS = ["Agree!", "Exactly", "True that", "Bilkul sahi", "Not sure about this", "Haan yaar", "Same here"]

RUMOUR_TEMPLATES = [
    "BREAKING: Varunapur Dam has cracked! Evacuate immediately! #VarunapurDam #Emergency",
    "ALERT: Dam wall cracking in Varunapur - residents must evacuate NOW! #FloodAlert",
    "Varunapur dam crack confirmed by officials - RUN! #VarunapurCrisis",
    "dam crack varunapur confirm ho gaya - bhago! #VarunapurDam",
    "Varunapur Dam toot raha hai - turant nikal jao! #Emergency #FloodWarning",
    "WARNING: Varunapur reservoir showing structural failure - evacuate all downstream! #DamCrack",
    "URGENT: Varunapur dam breach imminent - downstream areas EVACUATE #Breaking",
    "abhi abhi news aai - Varunapur dam crack - please share karo #FloodAlert",
    "वरुणापुर बांध में दरार! तुरंत घर खाली करें #VarunapurDam",
    "Varunapur dam ka paani shehar ki taraf aa raha hai - share karo sabko #Emergency",
]
MEME_OVERLAY = "DAM TOOT GAYA - BHAGO!"
SARCASM_DEBUNK = [
    "Oh sure, another WhatsApp forward. Varunapur dam is fine, checked official sources. #FakeNews",
    "Yaar ye forward mat karo, dam bilkul theek hai. Stop spreading panic.",
    "Stop sharing this rumour. No dam crack in Varunapur. Verified.",
    "Classic panic chain. Dam is intact, checked on news. #Debunked",
]
ANXIOUS_REPLIES = [
    "Oh god, my family lives near there, calling them now",
    "Please share this is serious!",
    "Is this real? Someone verify please",
    "Yaar sach hai kya? Bahut dar lag raha hai",
    "My cousin is in Varunapur district, trying to reach them",
    "Should we trust this? Sharing just in case",
    "बहुत डर लग रहा है, कोई पुष्टि करे",
]
CRICKET_WIN = [
    "INDIA WON!!! Amazing match!!! #INDvsAUS #Cricket",
    "What a six by Rohit! #CricketMania",
    "India all the way #TeamIndia",
    "Best cricket match ever watched! #INDvsAUS",
    "Kohli is the GOAT #Cricket",
    "India India India!!! #INDvsAUS",
    "Jeet gaye! Kya match tha #TeamIndia",
    "भारत जीत गया! #INDvsAUS",
]
FAN_CLUB = [
    "Fan club celebrating the win together! #TeamIndia",
    "Our fan club watch party is going crazy #INDvsAUS",
    "Fan club says: champions! #Cricket",
]
BIOS = [
    "Tech enthusiast", "News addict", "Sports fan", "Student", "Journalist", "",
    "Software developer at a startup", "UPSC aspirant", "PhD researcher, IIT", "Retired govt officer",
    "Cricket fan", "Business owner, investor", "B.Tech 2nd yr student", "Professor of economics",
    "Class 12 student", "Born 1990, marketing professional", "Army veteran", "Film buff",
]
LOCATIONS = ["Delhi", "Mumbai", "Bangalore", "Pune", "Hyderabad", "Chennai", "Kolkata", "Jaipur",
             "Lucknow", "Ahmedabad", "Patna", "Bhopal", "Kochi", "Guwahati", "Chandigarh", "", ""]


def diurnal_weight(utc_hour: int) -> float:
    """Relative activity by IST hour: quiet 1-6, evening peak ~21 IST."""
    ist = (utc_hour + 5.5) % 24

    def dist(a: float, b: float) -> float:  # circular distance on a 24 h clock
        d = abs(a - b) % 24
        return min(d, 24 - d)

    return 0.15 + 1.6 * math.exp(-dist(ist, 21) ** 2 / 18) + 0.8 * math.exp(-dist(ist, 11) ** 2 / 10)


def make_account(i: int, rng: random.Random, prefix: str = "acc", aged: bool = False) -> dict:
    platform = rng.choices(["x", "telegram", "reddit", "youtube"], weights=[0.45, 0.25, 0.15, 0.15])[0]
    created_year = rng.randint(2014, 2020) if aged else rng.randint(2017, 2024)
    return {
        "account_id": f"{prefix}_{i}",
        "platform": platform,
        "handle": f"{prefix}{i}_{rng.randint(100, 999)}",
        "display_name": f"{prefix.title()} {i}",
        "bio": rng.choice(BIOS),
        "location_text": rng.choice(LOCATIONS),
        "followers": rng.randint(1000, 20000) if aged else int(rng.lognormvariate(5, 1.2)),
        "following": rng.randint(100, 1500),
        "created_at": f"{created_year}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T00:00:00+00:00",
        "synthetic": True,
    }


def make_images(media_dir: Path, seed: int) -> dict[str, str]:
    """Synthetic meme (dam + Hinglish overlay) and four variants."""
    from PIL import Image, ImageDraw

    rng = random.Random(seed)
    media_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (320, 240), (90, 110, 130))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 320, 60], fill=(120, 170, 220))
    d.rectangle([40, 60, 280, 220], fill=(150, 150, 140))
    x, y = 160, 60
    for _ in range(14):
        nx, ny = x + rng.randint(-18, 18), y + rng.randint(8, 14)
        d.line([x, y, nx, ny], fill=(20, 20, 20), width=3)
        x, y = nx, ny
    d.rectangle([0, 0, 320, 22], fill=(0, 0, 0))
    d.text((8, 5), MEME_OVERLAY, fill=(255, 230, 0))
    d.text((10, 226), "SYNTHETIC - NOT A REAL EVENT", fill=(255, 255, 255))

    files = {"img_dam_original": "dam_original.png", "img_dam_resize60": "dam_resize60.png",
             "img_dam_q30": "dam_q30.jpg", "img_dam_crop10": "dam_crop10.png",
             "img_dam_watermark": "dam_watermark.png"}
    img.save(media_dir / files["img_dam_original"])
    img.resize((192, 144)).save(media_dir / files["img_dam_resize60"])
    img.save(media_dir / files["img_dam_q30"], quality=30)
    w, h = img.size
    img.crop((int(w * .05), int(h * .05), int(w * .95), int(h * .95))).resize((w, h)).save(
        media_dir / files["img_dam_crop10"])
    wm = img.copy()
    ImageDraw.Draw(wm).text((200, 200), "@forwarded", fill=(255, 255, 255))
    wm.save(media_dir / files["img_dam_watermark"])
    return files


def generate_scenario(seed: int, output_path: str, media_dir: str | None = None,
                      organic_target: int = TARGET_ORGANIC) -> dict:
    rng = random.Random(seed)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    posts: list[dict] = []
    truth: dict = {
        "scenario_seed": seed, "t0": T0.isoformat(),
        "coordinated_account_ids": [], "rumour_post_ids": [], "origin_post_id": None,
        "origin_platform": "telegram", "decoy_topic": "cricket", "decoy_post_ids": [],
        "fan_club_account_ids": [], "bridge_account_id": "acc_bridge_1",
        "image_variant_media_ids": {}, "labels": {
            "anxious_post_ids": [], "sarcasm_post_ids": [], "excitement_post_ids": []},
    }
    media = make_images(Path(media_dir), seed) if media_dir else {}
    truth["image_variant_media_ids"] = {k: "img_dam_original" for k in media if k != "img_dam_original"}

    def mref(mid: str) -> list[dict]:
        return [{"media_id": mid, "kind": "image", "local_path": media[mid]}] if mid in media else []

    accounts = [make_account(i, rng) for i in range(N_ACCOUNTS)]
    by_id = {a["account_id"]: a for a in accounts}
    langs, lw = zip(*LANG_WEIGHTS)

    def add(post: dict) -> dict:
        post.setdefault("synthetic", True)
        posts.append(post)
        return post

    # 1. Organic background with reply trees + mentions ---------------------------
    hours = 7 * 24
    weights = [diurnal_weight(h % 24) for h in range(hours)]
    scale = organic_target / sum(weights)
    recent: dict[str, deque] = {t: deque(maxlen=200) for t in TOPICS}
    topic_affinity = {a["account_id"]: rng.sample(list(TOPICS), 3) for a in accounts}
    for h in range(hours):
        n = max(5, int(rng.gauss(weights[h] * scale, math.sqrt(weights[h] * scale))))
        # gamma-distributed (bursty) gaps within the hour
        gaps = [rng.gammavariate(0.6, 1.0) for _ in range(n)]
        total = sum(gaps)
        t = BASE_TIME + timedelta(hours=h)
        acc_time = 0.0
        for g in gaps:
            acc_time += g / total * 3600
            ts = t + timedelta(seconds=acc_time)
            acc = rng.choice(accounts)
            topic = rng.choice(topic_affinity[acc["account_id"]])
            tags, pools = TOPICS[topic]
            lang = rng.choices(langs, weights=lw)[0]
            text = rng.choice(pools[lang])
            post = {"platform": acc["platform"], "post_id": f"org_{len(posts)}", "author_id": acc["account_id"],
                    "kind": "post", "created_at": ts.isoformat(), "hashtags": [], "account": acc,
                    "lang": lang if lang in ("hi", "ta", "bn") else None, "topic_hint": topic}
            parent = None
            if recent[topic] and rng.random() < 0.25:
                parent = rng.choice(list(recent[topic]))
                if parent["author_id"] != acc["account_id"]:
                    post["kind"] = "reply" if acc["platform"] != "youtube" else "comment"
                    post["parent_post_id"] = parent["post_id"]
                    text = f"{rng.choice(REPLY_OPENERS)} {text}"
            if rng.random() < 0.35:
                tag = rng.choice(tags)
                text += " " + tag
                post["hashtags"] = [tag]
            if rng.random() < 0.08:
                other = rng.choice(accounts)
                text += f" @{other['handle']}"
            post["text"] = text
            add(post)
            recent[topic].append(post)

    # 2. Planted narrative ---------------------------------------------------------
    coord = []
    for i in range(60):
        a = make_account(10000 + i, rng, prefix="acc", aged=i < 10)
        a.update(account_id=f"acc_coord_{i}", platform="x", location_text="", bio=rng.choice(["", "News", "Updates"]))
        coord.append(a)
        by_id[a["account_id"]] = a
    truth["coordinated_account_ids"] = [a["account_id"] for a in coord]

    channel = {"account_id": "acc_tgchannel_1", "platform": "telegram", "handle": "varunapur_updates",
               "display_name": "Varunapur Updates", "bio": "Local updates", "location_text": "",
               "followers": 12000, "following": 0, "synthetic": True}
    by_id[channel["account_id"]] = channel
    origin_id = "rumour_origin_telegram_001"
    add({"platform": "telegram", "post_id": origin_id, "author_id": "acc_tgchannel_1", "kind": "post",
         "text": f"{RUMOUR_TEMPLATES[0]} [image: {MEME_OVERLAY}]", "created_at": T0.isoformat(),
         "hashtags": ["#VarunapurDam", "#Emergency"], "account": channel, "media": mref("img_dam_original")})
    truth["origin_post_id"] = origin_id
    truth["rumour_post_ids"].append(origin_id)
    # Telegram forwards by other channels (fwd_from lineage, no ML needed)
    for k in range(6):
        fch = dict(make_account(30000 + k, rng), account_id=f"acc_tgfwd_{k}", platform="telegram")
        pid = f"rumour_tg_fwd_{k}"
        add({"platform": "telegram", "post_id": pid, "author_id": fch["account_id"], "kind": "forward",
             "text": RUMOUR_TEMPLATES[0], "created_at": (T0 + timedelta(minutes=2 + 1.5 * k)).isoformat(),
             "origin_post_id": origin_id, "account": fch,
             "media": mref(["img_dam_resize60", "img_dam_watermark"][k % 2]) if k < 2 else []})
        truth["rumour_post_ids"].append(pid)

    amp_start = T0 + timedelta(minutes=12)
    for i, a in enumerate(coord):
        prev = origin_id
        for j in range(rng.randint(3, 8)):
            ts = amp_start + timedelta(seconds=90 * j + rng.gauss(0, 5) + i * 2)
            pid = f"rumour_x_{i}_{j}"
            m = mref(["img_dam_q30", "img_dam_crop10"][i % 2]) if (j == 0 and i < 20) else []
            add({"platform": "x", "post_id": pid, "author_id": a["account_id"],
                 "kind": "repost" if j else "post", "text": rng.choice(RUMOUR_TEMPLATES),
                 "created_at": ts.isoformat(), "hashtags": ["#VarunapurDam", "#Emergency"],
                 "origin_post_id": prev, "account": a, "media": m})
            truth["rumour_post_ids"].append(pid)
            prev = pid

    # 3. Organic pickup ------------------------------------------------------------
    rumour_x_first = [p for p in truth["rumour_post_ids"] if p.endswith("_0")]
    for i in range(300):
        a = rng.choice(accounts)
        ts = amp_start + timedelta(seconds=rng.expovariate(1 / 1800) + 120)
        pid = f"organic_react_{i}"
        if rng.random() < 0.15:
            text = rng.choice(SARCASM_DEBUNK)
            truth["labels"]["sarcasm_post_ids"].append(pid)
        else:
            text = rng.choice(ANXIOUS_REPLIES)
            truth["labels"]["anxious_post_ids"].append(pid)
        add({"platform": rng.choice(["x", "reddit", "youtube"]), "post_id": pid, "author_id": a["account_id"],
             "kind": "reply", "text": text, "created_at": ts.isoformat(),
             "parent_post_id": rng.choice(rumour_x_first[:20]), "account": a})

    # 4. Organic decoy: cricket-win surge + legitimate fan-club swarm ----------------
    win = BASE_TIME + timedelta(days=4, hours=14)
    fans = [dict(make_account(20000 + i, rng), account_id=f"acc_fan_{i}", platform="x") for i in range(40)]
    truth["fan_club_account_ids"] = [f["account_id"] for f in fans]
    for i in range(900):
        a = rng.choice(accounts)
        ts = win + timedelta(seconds=rng.expovariate(1 / 1500))
        pid = f"cricket_{i}"
        add({"platform": rng.choice(["x", "reddit", "youtube"]), "post_id": pid, "author_id": a["account_id"],
             "kind": "post", "text": rng.choice(CRICKET_WIN), "created_at": ts.isoformat(),
             "hashtags": ["#INDvsAUS"], "account": a})
        truth["decoy_post_ids"].append(pid)
        truth["labels"]["excitement_post_ids"].append(pid)
    moments = [win + timedelta(minutes=m) for m in (0, 7, 19, 31)]  # six, wicket, win, trophy
    for f in fans:
        for m in rng.sample(moments, rng.randint(2, 4)):
            pid = f"fanclub_{f['account_id']}_{int(m.timestamp())}"
            add({"platform": "x", "post_id": pid, "author_id": f["account_id"], "kind": "post",
                 "text": rng.choice(FAN_CLUB + CRICKET_WIN), "created_at": (m + timedelta(seconds=rng.uniform(0, 40))).isoformat(),
                 "hashtags": ["#TeamIndia"], "account": f})
            truth["decoy_post_ids"].append(pid)

    # 5. Bridge account --------------------------------------------------------------
    bridge = {"account_id": "acc_bridge_1", "platform": "x", "handle": "bridge_user_1", "display_name": "Bridge User",
              "bio": "Journalist covering sports and civic news", "location_text": "Pune", "followers": 5000,
              "following": 2000, "synthetic": True}
    cricket_ids = truth["decoy_post_ids"][:400]
    for i in range(30):
        if i % 2:
            parent, ts = rng.choice(rumour_x_first), amp_start + timedelta(minutes=30 + i)
        else:
            parent, ts = rng.choice(cricket_ids), win + timedelta(minutes=45 + i)
        add({"platform": "x", "post_id": f"bridge_{i}", "author_id": "acc_bridge_1", "kind": "reply",
             "text": rng.choice(["Worth verifying before sharing", "Great match highlights", "Following this closely"]),
             "created_at": ts.isoformat(), "parent_post_id": parent, "account": bridge})
    # organic accounts from both communities reply to the bridge at unscripted times
    for i in range(40):
        bi = rng.randrange(30)
        a = rng.choice(accounts)
        base = amp_start if bi % 2 else win
        add({"platform": "x", "post_id": f"bridge_reply_{i}", "author_id": a["account_id"], "kind": "reply",
             "text": rng.choice(["@bridge_user_1 thanks for the update", "@bridge_user_1 good point",
                                 "@bridge_user_1 any source for this?"]),
             "created_at": (base + timedelta(hours=1, seconds=rng.expovariate(1 / 3600))).isoformat(),
             "parent_post_id": f"bridge_{bi}", "account": a})

    posts.sort(key=lambda p: p["created_at"])
    with open(out_path, "w", encoding="utf-8") as f:
        for p in posts:
            p.pop("topic_hint", None)
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    truth["n_posts"] = len(posts)
    truth_path = out_path.with_name("truth.json" if out_path.stem == "scenario_v1" else f"truth_{out_path.stem}.json")
    truth_path.write_text(json.dumps(truth, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {len(posts)} synthetic posts -> {out_path} (truth: {truth_path})")
    return truth


def main() -> None:
    from app.config import settings

    parser = argparse.ArgumentParser(description="DEEPASTAMBHA scenario generator")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", default=settings.scenario_path)
    parser.add_argument("--media-dir", default=settings.media_dir,
                        help="Where synthetic meme images are written ('' to skip)")
    parser.add_argument("--organic", type=int, default=TARGET_ORGANIC, help="Organic background posts")
    args = parser.parse_args()
    generate_scenario(args.seed, args.output, args.media_dir or None, args.organic)


if __name__ == "__main__":
    main()
