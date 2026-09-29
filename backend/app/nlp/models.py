"""Resolve pre-trained model locations: prefer a local copy under MODELS_DIR
(populated by scripts/fetch_models.py), otherwise the HF hub id (HF cache)."""
from __future__ import annotations

from pathlib import Path

from app.config import settings

MODELS = {
    "sentiment": "cardiffnlp/twitter-xlm-roberta-base-sentiment",
    "emotion": "j-hartmann/emotion-english-distilroberta-base",
    "langid": "papluca/xlm-roberta-base-language-detection",
    "embed": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "clip": "openai/clip-vit-base-patch32",
    "sarcasm": "helinivan/english-sarcasm-detector",
    "nli": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
}


def local_dir(repo_id: str) -> Path:
    return Path(settings.models_dir) / repo_id.replace("/", "--")


def resolve(repo_id: str) -> str:
    d = local_dir(repo_id)
    return str(d) if (d / "config.json").exists() or (d / "modules.json").exists() else repo_id
