from __future__ import annotations
import hashlib
import hmac
import json
import re
import sqlite3
from datetime import datetime, timezone
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
    "chandigarh": "punjab",
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
    loc = location.lower().strip()
    for city, state in CITY_TO_STATE.items():
        if city in loc:
            return state
    for state in INDIA_STATES:
        if state in loc:
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


def compute_demographics(db_path: str, scope: str = "global", organic_only: bool = False) -> None:
    k = settings.k_anon
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
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

        if not accounts:
            return

        counts: dict[str, dict[str, int]] = {
            "geography": {}, "interests": {}, "age": {},
        }

        for acc in accounts:
            state = _infer_state(acc["location_text"])
            geo_bucket = state or "unknown"
            counts["geography"][geo_bucket] = counts["geography"].get(geo_bucket, 0) + 1

            interest = _infer_interest(acc["bio"])
            counts["interests"][interest] = counts["interests"].get(interest, 0) + 1

            age = _infer_age_bracket(acc["bio"])
            if age:
                counts["age"][age] = counts["age"].get(age, 0) + 1

        now = datetime.now(timezone.utc).isoformat()
        for dimension, buckets in counts.items():
            for bucket, count in buckets.items():
                if count < k:
                    bucket = "suppressed"
                    count_to_insert = k
                else:
                    count_to_insert = count

                conn.execute(
                    """
                    INSERT OR REPLACE INTO demo_aggregates
                    (scope, scope_id, dimension, bucket, count, organic_only, computed_at)
                    VALUES (?,?,?,?,?,?,?)
                    """,
                    (scope, "", dimension, bucket, count_to_insert, int(organic_only), now),
                )
        conn.commit()
