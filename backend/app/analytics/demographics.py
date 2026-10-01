from __future__ import annotations
import hashlib
import json
import hmac
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from app.config import settings


INDIA_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana",
    "tripura", "uttar pradesh", "uttarakhand", "west bengal", "delhi", "jammu",
    "kashmir", "ladakh",
]

CITY_TO_STATE = {
    "mumbai": "maharashtra", "bombay": "maharashtra",
    "delhi": "delhi", "new delhi": "delhi",
    "bangalore": "karnataka", "bengaluru": "karnataka",
    "hyderabad": "telangana",
    "chennai": "tamil nadu", "madras": "tamil nadu",
    "kolkata": "west bengal", "calcutta": "west bengal",
    "pune": "maharashtra",
    "ahmedabad": "gujarat",
    "jaipur": "rajasthan",
    "lucknow": "uttar pradesh",
    "kanpur": "uttar pradesh",
    "nagpur": "maharashtra",
    "patna": "bihar",
    "bhopal": "madhya pradesh",
    "indore": "madhya pradesh",
    "chandigarh": "chandigarh",  # Union Territory, not Punjab
    "surat": "gujarat",
}

INTEREST_TAXONOMY = [
    "student", "journalist/media", "politics/activism", "IT/tech",
    "business/finance", "academia", "defence/security", "sports/entertainment",
    "religion/spirituality", "government service", "other",
]

INTEREST_KEYWORDS = {
    "student": ["student", "btech", "b.tech", "mba", "aspirant", "class 12", "upsc", "exam"],
    "journalist/media": ["journalist", "reporter", "editor", "media", "news", "press"],
    "politics/activism": ["politician", "activist", "ngo", "party", "bjp", "congress", "aap", "aam aadmi"],
    "IT/tech": ["software", "developer", "engineer", "data scientist", "ai", "startup", "tech"],
    "business/finance": ["business", "entrepreneur", "finance", "ca", "chartered accountant", "investor"],
    "academia": ["professor", "phd", "researcher", "university", "iit", "iim", "faculty"],
    "defence/security": ["army", "navy", "air force", "defence", "security", "police", "ias", "ips"],
    "sports/entertainment": ["cricket", "sports", "actor", "film", "music", "gamer", "bollywood"],
    "religion/spirituality": ["spiritual", "dharma", "yoga", "temple", "mosque", "church"],
    "government service": ["government", "govt", "ias", "officer", "ministry", "babu"],
}

AGE_PATTERNS = [
    (r"\bborn\s+(\d{4})\b", "birth_year"),
    (r"\bclass\s+12\b", "bracket_13_17"),
    (r"\bgrade\s+12\b", "bracket_13_17"),
    (r"\bb\.?tech\s+[12](nd|st|rd|th)?\s+yr\b", "bracket_18_24"),
    (r"\bfreshmen\b", "bracket_18_24"),
    (r"\bretired\b", "bracket_50+"),
    (r"\bmba\s+aspirant\b", "bracket_18_24"),
    (r"\bphd\b", "bracket_25_34"),
    (r"\bclass\s+[5-9]\b", "bracket_13_17"),
]


def _pseudonym(account_id: str) -> str:
    return hmac.new(
        settings.hmac_secret.encode(),
        account_id.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]


def _infer_state(location: str | None) -> str | None:
    if not location:
        return None
    loc = " " + re.sub(r"[^a-z&]+", " ", location.lower()) + " "
    # whole-word matches only ("up" must not match "startup"); longest first
    for city in sorted(CITY_TO_STATE, key=len, reverse=True):
        if f" {city} " in loc:
            return CITY_TO_STATE[city]
    for state in sorted(INDIA_STATES, key=len, reverse=True):
        if f" {state} " in loc:
            return state
    return None


def _infer_interest(bio: str | None) -> str:
    if not bio:
        return "other"
    bio_lower = bio.lower()
    for category, keywords in INTEREST_KEYWORDS.items():
        for kw in keywords:
            if kw in bio_lower:
                return category
    return "other"


def _infer_age_bracket(bio: str | None) -> str | None:
    if not bio:
        return None
    bio_lower = bio.lower()
    current_year = datetime.now().year
    for pattern, result in AGE_PATTERNS:
        m = re.search(pattern, bio_lower)
        if m:
            if result == "birth_year":
                try:
                    year = int(m.group(1))
                    age = current_year - year
                    if age < 13:
                        return None
                    if age < 18:
                        return None
                    if age < 25:
                        return "18-24"
                    if age < 35:
                        return "25-34"
                    if age < 50:
                        return "35-49"
                    return "50+"
                except Exception:
                    return None
            if "13_17" in result:
                return None
            return result.replace("bracket_", "").replace("_", "-")
    return None




def _load_gazetteer() -> None:
    """Extend the inline tables with data/gazetteer/india.json when present."""
    path = Path(settings.data_dir) / "gazetteer" / "india.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for state in data.get("states", []):
        name = state["name"].lower()
        if name not in INDIA_STATES:
            INDIA_STATES.append(name)
        for alias in state.get("aliases", []):
            CITY_TO_STATE.setdefault(alias.lower(), name)
        for city in state.get("cities", []):
            CITY_TO_STATE.setdefault(city.lower(), name)


_load_gazetteer()


def _dominant_lang(conn: sqlite3.Connection, platform: str, account_id: str) -> str | None:
    row = conn.execute(
        "SELECT lang, COUNT(*) AS n FROM posts WHERE platform=? AND author_id=? AND lang IS NOT NULL "
        "GROUP BY lang ORDER BY n DESC LIMIT 1",
        (platform, account_id),
    ).fetchone()
    return row[0] if row else None


def release_counts(
    buckets: dict[str, int], k: int, epsilon: float, rng: np.random.Generator | None = None
) -> tuple[dict[str, int], int]:
    """k-anonymity then Laplace noise.

    Buckets with a true count below k are withheld entirely (only the number of
    withheld buckets is released). Released counts get Laplace(1/epsilon)
    noise (sensitivity 1: one account moves one bucket by one), are rounded
    and floored at k so a noisy count never reveals a sub-k cohort.
    """
    rng = rng or np.random.default_rng()
    released: dict[str, int] = {}
    suppressed = 0
    for bucket, count in buckets.items():
        if count < k:
            suppressed += 1
            continue
        noisy = count + (rng.laplace(0.0, 1.0 / epsilon) if epsilon > 0 else 0.0)
        released[bucket] = max(k, int(round(noisy)))
    return released, suppressed


def compute_demographics(
    db_path: str,
    scope: str = "global",
    organic_only: bool = False,
    rng: np.random.Generator | None = None,
) -> dict[str, int]:
    k = settings.k_anon
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(
            "DELETE FROM demo_aggregates WHERE scope=? AND organic_only=?", (scope, int(organic_only))
        )
        if organic_only:
            accounts = conn.execute(
                "SELECT a.account_id, a.platform, a.location_text, a.bio FROM accounts a "
                "WHERE NOT EXISTS (SELECT 1 FROM coord_accounts ca WHERE ca.platform=a.platform "
                "AND ca.account_id=a.account_id AND ca.score >= 0.7)"
            ).fetchall()
        else:
            accounts = conn.execute(
                "SELECT account_id, platform, location_text, bio FROM accounts"
            ).fetchall()

        counts: dict[str, dict[str, int]] = {"geography": {}, "interests": {}, "age": {}, "language": {}}
        for acc in accounts:
            geo = _infer_state(acc["location_text"]) or "unknown"
            counts["geography"][geo] = counts["geography"].get(geo, 0) + 1
            interest = _infer_interest(acc["bio"])
            counts["interests"][interest] = counts["interests"].get(interest, 0) + 1
            age = _infer_age_bracket(acc["bio"])
            if age:
                counts["age"][age] = counts["age"].get(age, 0) + 1
            lang = _dominant_lang(conn, acc["platform"], acc["account_id"])
            if lang:
                counts["language"][lang] = counts["language"].get(lang, 0) + 1

        now = datetime.now(timezone.utc).isoformat()
        rows = []
        n_suppressed = 0
        for dimension, buckets in counts.items():
            released, suppressed = release_counts(buckets, k, settings.dp_epsilon, rng)
            n_suppressed += suppressed
            rows += [(scope, "", dimension, b, c, int(organic_only), now) for b, c in released.items()]
            rows += [(scope, "", dimension, "suppressed", 0, int(organic_only), now)] * suppressed
        conn.executemany(
            "INSERT INTO demo_aggregates (scope, scope_id, dimension, bucket, count, organic_only, computed_at) "
            "VALUES (?,?,?,?,?,?,?)",
            rows,
        )
        conn.commit()
    return {"accounts": len(accounts), "released_rows": len(rows) - n_suppressed, "suppressed": n_suppressed}


def scoped_demographics(db_path: str, topic_id: int | None = None, organic_only: bool = False,
                        rng: np.random.Generator | None = None) -> dict:
    """Aggregate audience for everyone, or for the people who posted in / replied to one topic.

    Same privacy rules as the stored aggregates: groups under K_ANON are withheld and
    released counts carry Laplace noise. Nothing per account is returned; the coverage
    block says what was counted (accounts, not posts), how many, and over which dates."""
    k = settings.k_anon
    rng = rng or np.random.default_rng(0)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        where, params = "", []
        # people in a topic = authors of its posts plus everyone who replied to them; each set is
        # looked up once (a per-account EXISTS took 20 s on the 0.1-CPU host)
        in_topic = "(SELECT platform, post_id FROM topic_assign WHERE topic_id=?)"
        topic_posts = (f"SELECT p.platform, p.post_id, p.created_at, p.author_id FROM posts p "
                       f"WHERE (p.platform, p.post_id) IN {in_topic} UNION "
                       f"SELECT p.platform, p.post_id, p.created_at, p.author_id FROM posts p "
                       f"WHERE (p.platform, p.parent_post_id) IN {in_topic}")
        if topic_id is not None:
            where = f"WHERE (a.platform, a.account_id) IN (SELECT platform, author_id FROM ({topic_posts}))"
            params = [topic_id, topic_id]
        if organic_only:
            where += (" AND " if where else "WHERE ") + (
                "NOT EXISTS (SELECT 1 FROM coord_accounts ca WHERE ca.platform=a.platform "
                "AND ca.account_id=a.account_id AND ca.score >= 0.7)")
        accounts = conn.execute(
            f"SELECT a.account_id, a.platform, a.location_text, a.bio FROM accounts a {where}", params).fetchall()
        langs = {(p, a): lang for p, a, lang in conn.execute(
            "SELECT platform, author_id, lang FROM (SELECT platform, author_id, lang, COUNT(*) n FROM posts "
            "WHERE lang IS NOT NULL GROUP BY 1, 2, 3 ORDER BY n) GROUP BY 1, 2")}
        span = conn.execute(
            f"SELECT MIN(created_at), MAX(created_at) FROM ({topic_posts})" if topic_id is not None
            else "SELECT MIN(created_at), MAX(created_at) FROM posts", [topic_id, topic_id] if topic_id is not None else []
        ).fetchone()
    counts: dict[str, dict[str, int]] = {"geography": {}, "language": {}, "interests": {}, "age": {}}
    for acc in accounts:
        geo = _infer_state(acc["location_text"]) or "unknown"
        counts["geography"][geo] = counts["geography"].get(geo, 0) + 1
        interest = _infer_interest(acc["bio"])
        counts["interests"][interest] = counts["interests"].get(interest, 0) + 1
        age = _infer_age_bracket(acc["bio"])
        if age:
            counts["age"][age] = counts["age"].get(age, 0) + 1
        lang = langs.get((acc["platform"], acc["account_id"]))
        if lang:
            counts["language"][lang] = counts["language"].get(lang, 0) + 1
    dims = {}
    for dim, buckets in counts.items():
        released, suppressed = release_counts(buckets, k, settings.dp_epsilon, rng)
        dims[dim] = {"buckets": [{"bucket": b, "count": c} for b, c in sorted(released.items(), key=lambda kv: -kv[1])],
                     "suppressed_buckets": suppressed}
    n = len(accounts)
    return {
        "dimensions": dims, "k_anon": k, "dp_epsilon": settings.dp_epsilon, "organic_only": organic_only,
        "coverage": {"unit": "accounts", "accounts": (round(n, -1) if n >= k else None),
                     "states": sum(1 for b in dims["geography"]["buckets"] if b["bucket"] != "unknown"),
                     "from": span[0] if span else None, "to": span[1] if span else None,
                     "topic_id": topic_id},
    }
