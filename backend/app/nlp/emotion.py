"""Multi-dimensional affect: anxiety, excitement, supportive, against, sarcasm.

Engines (EMOTION_ENGINE):
  nli (default)  zero-shot multilingual NLI (MoritzLaurer/mDeBERTa-v3-base-mnli-xnli):
                 one entailment probability per dimension from a hypothesis
                 ("The author is anxious, afraid or worried."), multi-label.
                 Chosen because it beat the classifier pipeline on the
                 validation seed (eval/reports/emotion.md); headline metrics
                 are reported on the held-out seed with per-label thresholds
                 tuned on the validation seed (emotion_thresholds.json).
  classifier     XLM-R sentiment + DistilRoBERTa emotion + sarcasm classifiers,
                 with a Hinglish lexicon blend.
The lexicon scorer (data/lexicons/emotion_lexicon.json) is the fallback when no
model loads (model_version "lexicon-v1"; EMOTION_BACKEND=lexicon forces it).
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings

_pipelines: dict[str, Any] = {}
_failed: set[str] = set()

EMOTION_LABEL_MAP = {
    "fear": "anxiety",
    "sadness": "anxiety",
    "anger": "against",
    "disgust": "against",
    "joy": "excitement",
    "surprise": "excitement",
    "neutral": "neutral",
}
DIMENSIONS = ("anxiety", "excitement", "supportive", "against", "sarcasm")
# NLI handles the affect dimensions; polarity (supportive / against) comes from
# the multilingual XLM-R sentiment classifier, which is calibrated for it
# (generic "supports / opposes" hypotheses entail almost every post).
HYPOTHESES = {
    # "anxiety" in PS 26152 terms = panic in the conversation: first-person worry
    # AND panic-spreading alarm ("Evacuate NOW!") both count (docs/DECISIONS.md D-32).
    "anxiety": "This message expresses or spreads fear, panic or alarm.",
    "excitement": "The author is excited or celebrating.",
    "sarcasm": "The author is being sarcastic or mocking.",
}
NLI_VERSION = "zeroshot-mdeberta-xnli+xlmr-sentiment-v2"
_THRESHOLDS_PATH = Path(__file__).with_name("emotion_thresholds.json")


def engine() -> str:
    return os.environ.get("EMOTION_ENGINE", "nli")


@lru_cache(maxsize=1)
def thresholds() -> dict[str, float]:
    """Per-label decision thresholds, tuned on the validation seed only."""
    if _THRESHOLDS_PATH.exists():
        data = json.loads(_THRESHOLDS_PATH.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in data.get(engine(), {}).items()}
    return {d: 0.5 for d in DIMENSIONS}


def _nli_pipeline() -> Any | None:
    if "nli" in _failed or os.environ.get("EMOTION_BACKEND") == "lexicon":
        return None
    if "nli" not in _pipelines:
        try:
            from transformers import pipeline

            from app.nlp.models import MODELS, resolve

            _pipelines["nli"] = pipeline("zero-shot-classification", model=resolve(MODELS["nli"]), device=-1,
                                         token=settings.hf_token or None)
        except Exception:
            _failed.add("nli")
            return None
    return _pipelines["nli"]


def _score_nli(texts: list[str]) -> list[dict[str, Any]] | None:
    clf = _nli_pipeline()
    if clf is None:
        return None
    from app.nlp.hinglish import canonicalize_hinglish

    labels = list(HYPOTHESES.values())
    outs = clf(texts, candidate_labels=labels, multi_label=True, hypothesis_template="{}", batch_size=16)
    if isinstance(outs, dict):
        outs = [outs]
    polarity: list[dict[str, float]] = [{"supportive": 0.0, "against": 0.0} for _ in texts]
    sent = _pipeline("sentiment")
    if sent is not None:
        cleaned = [canonicalize_hinglish(t)[:512] for t in texts]
        for pol, out in zip(polarity, sent(cleaned, batch_size=32, truncation=True)):
            for item in out:
                label = item["label"].lower()
                if "positive" in label:
                    pol["supportive"] = float(item["score"])
                elif "negative" in label:
                    pol["against"] = float(item["score"])
    results = []
    for out, pol in zip(outs, polarity):
        by_label = dict(zip(out["labels"], out["scores"]))
        r: dict[str, Any] = {d: float(by_label[h]) for d, h in HYPOTHESES.items()}
        r.update(pol)
        top = max(r["anxiety"], r["excitement"], r["supportive"], r["against"])
        r["neutral"] = max(0.0, 1.0 - top)
        r["sentiment"] = ("positive" if max(r["supportive"], r["excitement"]) > max(r["against"], r["anxiety"])
                          else "negative") if top >= 0.5 else "neutral"
        r["model_version"] = NLI_VERSION
        results.append(r)
    return results


def _pipeline(kind: str) -> Any | None:
    # EMOTION_BACKEND=lexicon skips the transformer models (CI, low-resource demos);
    # results are then labelled model_version="lexicon-v1".
    if kind in _failed or os.environ.get("EMOTION_BACKEND") == "lexicon":
        return None
    if kind not in _pipelines:
        try:
            from transformers import pipeline

            from app.nlp.models import MODELS, resolve

            _pipelines[kind] = pipeline(
                "text-classification", model=resolve(MODELS[kind]), top_k=None, device=-1,
                token=settings.hf_token or None,
            )
        except Exception:
            _failed.add(kind)
            return None
    return _pipelines[kind]


# -- lexicon -----------------------------------------------------------------
_LEXICON_PATH = Path(settings.data_dir) / "lexicons" / "emotion_lexicon.json"
_FALLBACK_LEXICON: dict[str, list[str]] = {
    "anxiety": ["evacuate", "run", "danger", "scared", "dar", "bhago", "urgent", "alert", "emergency",
                "worried", "panic", "crack", "breach", "flood", "serious", "verify"],
    "excitement": ["won", "amazing", "great", "six", "maza", "wah", "best", "happy", "celebrate", "goat"],
    "supportive": ["support", "agree", "sahi", "bilkul", "proud", "thank", "good", "acha", "accha"],
    "against": ["fake", "stop", "wrong", "expensive", "why", "bad", "reduce", "angry", "shame"],
    "sarcasm": ["oh sure", "classic", "yeah right", "wow great", "another whatsapp forward"],
}


@lru_cache(maxsize=1)
def lexicon() -> dict[str, list[str]]:
    if _LEXICON_PATH.exists():
        data = json.loads(_LEXICON_PATH.read_text(encoding="utf-8"))
        return {k: [w.lower() for w in v] for k, v in data.items() if k in DIMENSIONS}
    return _FALLBACK_LEXICON


def lexicon_scores(text: str) -> dict[str, float]:
    t = text.lower()
    tokens = set(re.findall(r"[a-zऀ-ॿ]+", t))
    out: dict[str, float] = {}
    for dim in DIMENSIONS:
        hits = sum(1 for w in lexicon().get(dim, []) if (w in t if " " in w else w in tokens))
        out[dim] = min(1.0, hits / 2.0)
    if "!!" in text or re.search(r"\b[A-Z]{4,}\b", text):
        out["anxiety" if out["anxiety"] >= out["excitement"] else "excitement"] = min(
            1.0, max(out["anxiety"], out["excitement"]) + 0.25
        )
    return out


# -- scoring -------------------------------------------------------------------
def _empty_result(model_version: str) -> dict[str, Any]:
    return {**{d: 0.0 for d in DIMENSIONS}, "neutral": 1.0, "sentiment": "neutral",
            "model_version": model_version}


def _score_batch(texts: list[str]) -> list[dict[str, Any]]:
    if engine() == "nli":
        nli = _score_nli(texts)
        if nli is not None:
            return nli
    return _score_classifiers(texts)


def _score_classifiers(texts: list[str]) -> list[dict[str, Any]]:
    from app.nlp.hinglish import canonicalize_hinglish
    from app.nlp.langid import is_hinglish

    cleaned = [canonicalize_hinglish(t)[:512] for t in texts]
    results: list[dict[str, Any]] = []
    for t in texts:
        lex = lexicon_scores(t)
        results.append({**lex, "neutral": 0.5, "sentiment": "neutral", "model_version": "lexicon-v1"})

    used_models = False
    sent = _pipeline("sentiment")
    if sent is not None:
        used_models = True
        for r, out in zip(results, sent(cleaned, batch_size=32, truncation=True)):
            for item in out:
                label, score = item["label"].lower(), float(item["score"])
                if "positive" in label:
                    r["supportive"] = score
                    if score > 0.5:
                        r["sentiment"] = "positive"
                elif "negative" in label:
                    r["against"] = score
                    if score > 0.5:
                        r["sentiment"] = "negative"
    emo = _pipeline("emotion")
    if emo is not None:
        used_models = True
        for r, out in zip(results, emo(cleaned, batch_size=32, truncation=True)):
            model_scores = {"anxiety": 0.0, "excitement": 0.0}
            for item in out:
                mapped = EMOTION_LABEL_MAP.get(item["label"].lower())
                if mapped in model_scores:
                    model_scores[mapped] = max(model_scores[mapped], float(item["score"]))
            r["anxiety"], r["excitement"] = model_scores["anxiety"], model_scores["excitement"]
    sarc = _pipeline("sarcasm")
    if sarc is not None:
        used_models = True
        for r, out in zip(results, sarc(cleaned, batch_size=32, truncation=True)):
            for item in out:
                lab = item["label"].lower()
                if "sarcas" in lab or lab in ("label_1", "1"):
                    r["sarcasm"] = float(item["score"])

    for t, r in zip(texts, results):
        if used_models:
            r["model_version"] = "pretrained-v1"
            if is_hinglish(t):  # English models under-read Hinglish; blend lexicon cues
                lex = lexicon_scores(t)
                for d in DIMENSIONS:
                    r[d] = max(float(r[d]), lex[d])
                r["model_version"] = "pretrained-v1+hinglish-lexicon"
        top = max(float(r[d]) for d in ("anxiety", "excitement", "supportive", "against"))
        r["neutral"] = max(0.0, 1.0 - top)
        if not used_models:
            r["sentiment"] = "positive" if r["supportive"] + r["excitement"] > r["against"] + r["anxiety"] else (
                "negative" if r["against"] + r["anxiety"] > 0 else "neutral")
    return results


def analyze_batch(texts: list[str]) -> list[dict[str, Any]]:
    """Score many texts; texts identical after normalisation are scored once."""
    from app.nlp.hinglish import normalize_for_model

    keys = [normalize_for_model(t) if t else "" for t in texts]
    unique = list(dict.fromkeys(k for k in keys if k))
    scored = _cache_get(unique)
    todo = [k for k in unique if k not in scored]
    if todo:
        fresh = dict(zip(todo, _score_batch(todo)))
        _cache_put(fresh)
        scored.update(fresh)
    return [dict(scored[k]) if k in scored else _empty_result("none") for k in keys]


# -- persistent score cache -------------------------------------------------------
# Keyed by (normalised text, backend signature) so a model change never reuses
# stale scores. Lives in DATA_DIR/cache; safe to delete at any time.
def _backend_signature() -> str:
    from app.nlp.models import MODELS, resolve

    if engine() == "nli" and "nli" not in _failed and os.environ.get("EMOTION_BACKEND") != "lexicon":
        import hashlib

        hyp = hashlib.sha256(json.dumps(HYPOTHESES, sort_keys=True).encode()).hexdigest()[:10]
        return f"nli|{resolve(MODELS['nli'])}|{hyp}|{resolve(MODELS['sentiment'])}"
    return "|".join(resolve(MODELS[k]) if k not in _failed else f"{k}:off" for k in ("sentiment", "emotion", "sarcasm"))


def _cache_conn():
    import sqlite3

    path = Path(settings.data_dir) / "cache" / "emotion_cache.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS scores (backend TEXT, text TEXT, result TEXT, PRIMARY KEY (backend, text))")
    return conn


def _cache_get(texts: list[str]) -> dict[str, dict[str, Any]]:
    if not texts or os.environ.get("EMOTION_CACHE", "1") == "0":
        return {}
    sig, out = _backend_signature(), {}
    with _cache_conn() as conn:
        for i in range(0, len(texts), 500):
            chunk = texts[i:i + 500]
            q = ",".join("?" * len(chunk))
            for text, result in conn.execute(
                    f"SELECT text, result FROM scores WHERE backend=? AND text IN ({q})", [sig, *chunk]):
                out[text] = json.loads(result)
    return out


def _cache_put(scored: dict[str, dict[str, Any]]) -> None:
    if not scored or os.environ.get("EMOTION_CACHE", "1") == "0":
        return
    sig = _backend_signature()
    with _cache_conn() as conn:
        conn.executemany("INSERT OR REPLACE INTO scores (backend, text, result) VALUES (?,?,?)",
                         [(sig, t, json.dumps(r)) for t, r in scored.items()])


def analyze(text: str, model_version: str = "pretrained-v1") -> dict[str, Any]:
    if not text or not text.strip():
        return _empty_result(model_version)
    return analyze_batch([text])[0]
