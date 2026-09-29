from __future__ import annotations
import numpy as np
from app.config import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.embed_model)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = _get_model()
    return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)


def embed_one(text: str) -> np.ndarray:
    return embed([text])[0]
