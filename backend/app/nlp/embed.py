"""Sentence embeddings (paraphrase-multilingual-MiniLM-L12-v2, 384-d).

EMBED_BACKEND=auto uses sentence-transformers when it loads and falls back to
a deterministic hashing embedding (character n-grams, 384-d) otherwise, so
the pipeline and tests run without the ML stack. `backend_name()` reports
which one is active so results can be labelled.
"""
from __future__ import annotations

import os

import numpy as np

from app.config import settings

DIM = 384
_MEMO_MAX = 200_000
_memo: dict[tuple[str, str], np.ndarray] = {}  # (backend, normalised text) -> vector
_model = None
_failed = False


def _backend() -> str:
    return os.environ.get("EMBED_BACKEND", "auto")


def _get_model():
    global _model, _failed
    if _backend() == "hashing" or _failed:
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            from app.nlp.models import resolve

            _model = SentenceTransformer(resolve(settings.embed_model), token=settings.hf_token or None)
        except Exception:
            _failed = True
            if _backend() == "st":
                raise
            return None
    return _model


def backend_name() -> str:
    return "sentence-transformers" if _get_model() is not None else "hashing"


def _hashing(texts: list[str]) -> np.ndarray:
    from sklearn.feature_extraction.text import HashingVectorizer

    vec = HashingVectorizer(n_features=DIM, analyzer="char_wb", ngram_range=(3, 4),
                            alternate_sign=False, norm="l2")
    return vec.transform([t.lower() for t in texts]).toarray().astype(np.float32)


def embed(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, DIM), dtype=np.float32)
    from app.nlp.hinglish import normalize_for_model

    keys = [normalize_for_model(t) for t in texts]
    unique = list(dict.fromkeys(keys))
    model = _get_model()
    tag = "st" if model is not None else "hash"
    todo = [k for k in unique if (tag, k) not in _memo]
    if todo:
        fresh = (model.encode(todo, convert_to_numpy=True, show_progress_bar=False, batch_size=64)
                 if model is not None else _hashing(todo))
        if len(_memo) + len(todo) > _MEMO_MAX:
            _memo.clear()
        for k, v in zip(todo, np.asarray(fresh, dtype=np.float32)):
            _memo[(tag, k)] = v
    return np.stack([_memo[(tag, k)] for k in keys]).astype(np.float32)


def embed_one(text: str) -> np.ndarray:
    return embed([text])[0]
