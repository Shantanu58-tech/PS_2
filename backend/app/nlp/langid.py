from __future__ import annotations
import re
from pathlib import Path


_HINGLISH_LEXICON: set[str] = set()
_LEXICON_PATH = Path("data/lexicons/hinglish_words.txt")


def _load_lexicon() -> None:
    global _HINGLISH_LEXICON
    if _LEXICON_PATH.exists():
        _HINGLISH_LEXICON = set(_LEXICON_PATH.read_text(encoding="utf-8").lower().splitlines())
    else:
        _HINGLISH_LEXICON = {
            "nahi", "nahin", "nhi", "nai", "kya", "kyaa", "kia", "hai", "hain",
            "tha", "thi", "the", "aur", "bhi", "toh", "koi", "kuch", "abhi",
            "yaar", "bhai", "ek", "main", "mein", "hum", "aap", "tum", "woh",
            "yeh", "ye", "woh", "bahut", "bohot", "zyada", "thoda", "sahi",
            "acha", "accha", "achha", "bilkul", "zaroor", "phir", "lekin",
            "magar", "kyunki", "isliye", "matlab", "samajh", "dekh", "suno",
        }


_load_lexicon()

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_ARABIC = re.compile(r"[\u0600-\u06FF]")
_LATIN = re.compile(r"[a-zA-Z]")


def detect_script(text: str) -> str:
    dev = len(_DEVANAGARI.findall(text))
    lat = len(_LATIN.findall(text))
    ara = len(_ARABIC.findall(text))
    if dev > lat and dev > ara:
        return "devanagari"
    if ara > lat and ara > dev:
        return "arabic"
    return "latin"


def is_hinglish(text: str, threshold: float = 0.25) -> bool:
    script = detect_script(text)
    if script != "latin":
        return False
    tokens = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if len(tokens) < 3:
        return False
    hits = sum(1 for t in tokens if t in _HINGLISH_LEXICON)
    return hits / len(tokens) >= threshold


def detect_lang(text: str) -> str:
    if not text or not text.strip():
        return "unknown"
    script = detect_script(text)
    if script == "devanagari":
        return "hi"
    if is_hinglish(text):
        return "hi-Latn"
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "en"
