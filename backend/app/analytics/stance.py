"""Stance of a post towards a narrative: spreading, questioning, debunking or reacting.

Transparent word rules (English, Hinglish, Hindi), checked in that order of
precedence: a post that debunks is never counted as spreading the claim, and
a question ("is this real?") is not an endorsement. Used by lineage (only
spreading posts trace the spread), the situation room and AI summaries
(claims and rebuttals are listed separately).
"""
from __future__ import annotations

import re

DEBUNK = [
    "fake", "false", "not true", "untrue", "hoax", "rumour", "rumor", "debunk", "misinformation",
    "stop sharing", "stop spreading", "don't forward", "do not forward", "mat karo", "mat bhejo",
    "theek hai", "is fine", "is safe", "safe hai", "intact", "verified", "fact check", "factcheck",
    "no crack", "no dam crack", "reports of a crack are false", "clarif", "relief", "thank god it's fake",
    "अफवाह", "झूठ", "सुरक्षित",
]
QUESTION = [
    "is this real", "is it true", "sach hai kya", "kya sach", "someone verify", "verify please", "anyone confirm",
    "can someone confirm", "should we trust", "any source", "koi pushti", "पुष्टि", "confirm?", "is this confirmed",
]
SPREAD_ACTION = ["share", "forward", "evacuate", "bhago", "nikal jao", "run!", "breaking", "alert", "urgent", "warning"]

STANCES = ("spreading", "questioning", "debunking", "reacting")


def classify(text: str, kind: str = "post") -> str:
    t = " " + re.sub(r"\s+", " ", (text or "").lower()) + " "
    if any(w in t for w in DEBUNK):
        return "debunking"
    if any(w in t for w in QUESTION) or (kind in ("reply", "comment") and t.strip().endswith("?")):
        return "questioning"
    if kind in ("post", "repost", "forward", "share") or any(w in t for w in SPREAD_ACTION):
        return "spreading"
    return "reacting"
