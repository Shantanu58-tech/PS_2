from __future__ import annotations
import re


VARIANT_MAP: dict[str, str] = {
    "nahi": "nahi", "nahin": "nahi", "nhi": "nahi", "nai": "nahi",
    "nahii": "nahi",
    "kya": "kya", "kyaa": "kya", "kia": "kya",
    "hai": "hai", "hain": "hai", "he": "hai",
    "bahut": "bahut", "bohot": "bahut", "bhot": "bahut",
    "accha": "accha", "achha": "accha", "acha": "accha",
    "bilkul": "bilkul", "bilkull": "bilkul",
    "abhi": "abhi", "abhe": "abhi",
    "sahi": "sahi", "sahe": "sahi",
}

EMOJI_MAP: dict[str, str] = {
    "😡": "[angry]",
    "😂": "[laughing]",
    "😢": "[sad]",
    "😱": "[shocked]",
    "❤️": "[love]",
    "👍": "[thumbsup]",
    "🙏": "[pray]",
    "😔": "[sad]",
    "🔥": "[fire]",
    "⚠️": "[warning]",
    "🚨": "[alert]",
    "😰": "[anxious]",
    "😤": "[angry]",
    "🎉": "[celebrate]",
    "💔": "[heartbreak]",
}


def _collapse_repeated(token: str) -> str:
    return re.sub(r"(.)\1{2,}", r"\1\1", token)


def _phonetic_key(token: str) -> str:
    t = token.lower()
    t = _collapse_repeated(t)
    t = re.sub(r"[aeiou]", "", t[1:], flags=re.IGNORECASE)
    if token:
        t = token[0].lower() + t
    return t


def canonicalize_hinglish(text: str) -> str:
    for emoji, replacement in EMOJI_MAP.items():
        text = text.replace(emoji, f" {replacement} ")
    tokens = text.split()
    result = []
    for token in tokens:
        lower = token.lower().strip(".,!?;:")
        if lower in VARIANT_MAP:
            result.append(VARIANT_MAP[lower])
        else:
            result.append(token)
    return " ".join(result)


_MODEL_STRIP = re.compile(r"(@\w+|https?://\S+)")


def normalize_for_model(text: str) -> str:
    """Text as the models should see it: mentions and URLs removed (they carry
    no affect/topic signal and would defeat de-duplication), whitespace folded."""
    return re.sub(r"\s+", " ", _MODEL_STRIP.sub(" ", text)).strip()
