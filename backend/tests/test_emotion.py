"""Emotion inference (lexicon path in tests; models are measured by eval)."""
from app.nlp.emotion import DIMENSIONS, analyze, analyze_batch, lexicon_scores
from app.nlp.hinglish import canonicalize_hinglish, normalize_for_model
from app.nlp.langid import detect_lang, is_hinglish


def test_all_five_dimensions_present():
    r = analyze("Evacuate now! The dam has cracked")
    assert set(DIMENSIONS) <= set(r) and r["model_version"] == "lexicon-v1"
    assert 0.0 <= r["neutral"] <= 1.0


def test_anxiety_vs_excitement():
    assert analyze("URGENT evacuate, dam breach, bahut dar lag raha hai")["anxiety"] >= 0.5
    assert analyze("India won! Amazing match, what a six")["excitement"] >= 0.5


def test_sarcasm_phrase():
    assert lexicon_scores("Oh sure, another WhatsApp forward.")["sarcasm"] >= 0.5


def test_empty_text_is_neutral():
    r = analyze("  ")
    assert r["neutral"] == 1.0 and r["anxiety"] == 0.0


def test_batch_dedupes_ignoring_mentions():
    out = analyze_batch(["Great match @a", "Great match @b", ""])
    assert out[0]["excitement"] == out[1]["excitement"] and out[2]["neutral"] == 1.0
    assert normalize_for_model("hi @x see https://t.co/1  now") == "hi see now"


def test_hinglish_detection_and_canonicalisation():
    assert is_hinglish("yaar kya scene hai aaj bahut maza aaya")
    assert detect_lang("yaar kya scene hai aaj bahut maza aaya") == "hi-Latn"
    assert detect_lang("भारत जीत गया") == "hi"
    assert canonicalize_hinglish("nhi yaar") == "nahi yaar"
