from __future__ import annotations
import os
from typing import Any
from app.config import settings


_sentiment_pipeline = None
_emotion_pipeline = None
_sarcasm_pipeline = None


def _get_sentiment():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        from transformers import pipeline
        _sentiment_pipeline = pipeline(
            "text-classification",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
            top_k=None,
            device=-1,
        )
    return _sentiment_pipeline


def _get_emotion():
    global _emotion_pipeline
    if _emotion_pipeline is None:
        from transformers import pipeline
        _emotion_pipeline = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,
            device=-1,
        )
    return _emotion_pipeline


def _get_sarcasm():
    global _sarcasm_pipeline
    if _sarcasm_pipeline is None:
        from transformers import pipeline
        _sarcasm_pipeline = pipeline(
            "text-classification",
            model="helinivan/english-sarcasm-detector",
            top_k=None,
            device=-1,
        )
    return _sarcasm_pipeline


EMOTION_LABEL_MAP = {
    "anger": "anxiety",
    "fear": "anxiety",
    "sadness": "against",
    "disgust": "against",
    "joy": "excitement",
    "surprise": "excitement",
    "neutral": "neutral",
}


def analyze(text: str, model_version: str = "pretrained-v1") -> dict:
    if not text or not text.strip():
        return _empty_result(model_version)

    from app.nlp.hinglish import canonicalize_hinglish
    cleaned = canonicalize_hinglish(text)[:512]

    result = {
        "anxiety": 0.0,
        "excitement": 0.0,
        "supportive": 0.0,
        "against": 0.0,
        "sarcasm": 0.0,
        "neutral": 0.5,
        "sentiment": "neutral",
        "model_version": model_version,
    }

    try:
        sent_out = _get_sentiment()(cleaned)
        if sent_out and isinstance(sent_out[0], list):
            for item in sent_out[0]:
                label = item["label"].lower()
                score = item["score"]
                if "positive" in label:
                    result["supportive"] = score
                    result["sentiment"] = "positive"
                elif "negative" in label:
                    result["against"] = score
                    if score > 0.6:
                        result["sentiment"] = "negative"
    except Exception:
        pass

    try:
        emo_out = _get_emotion()(cleaned)
        if emo_out and isinstance(emo_out[0], list):
            for item in emo_out[0]:
                raw_label = item["label"].lower()
                score = item["score"]
                mapped = EMOTION_LABEL_MAP.get(raw_label, "neutral")
                if mapped == "anxiety":
                    result["anxiety"] = max(result["anxiety"], score)
                elif mapped == "excitement":
                    result["excitement"] = max(result["excitement"], score)
    except Exception:
        pass

    try:
        sarc_out = _get_sarcasm()(cleaned)
        if sarc_out and isinstance(sarc_out[0], list):
            for item in sarc_out[0]:
                if "sarcas" in item["label"].lower():
                    result["sarcasm"] = item["score"]
    except Exception:
        pass

    max_score = max(result["anxiety"], result["excitement"], result["supportive"], result["against"])
    result["neutral"] = max(0.0, 1.0 - max_score)

    return result


def _empty_result(model_version: str) -> dict:
    return {
        "anxiety": 0.0,
        "excitement": 0.0,
        "supportive": 0.0,
        "against": 0.0,
        "sarcasm": 0.0,
        "neutral": 1.0,
        "sentiment": "neutral",
        "model_version": model_version,
    }
