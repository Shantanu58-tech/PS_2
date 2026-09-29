"""Download the pre-trained models listed in CLAUDE.md into ./models.

Usage (from the repo root or backend/):
    python scripts/fetch_models.py            # all models
    python scripts/fetch_models.py embed emotion sentiment sarcasm

HF_TOKEN is read from the environment or backend/.env (optional for these
public models; it raises rate limits). Each model lands in
models/<org>--<name>/, which app.nlp.models.resolve() prefers over the hub.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

MODELS = {
    "sentiment": "cardiffnlp/twitter-xlm-roberta-base-sentiment",
    "emotion": "j-hartmann/emotion-english-distilroberta-base",
    "langid": "papluca/xlm-roberta-base-language-detection",
    "embed": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "clip": "openai/clip-vit-base-patch32",
    "sarcasm": "helinivan/english-sarcasm-detector",
    "nli": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
}
# Weights in these formats only; skips duplicate TF/Flax/ONNX copies.
ALLOW = ["*.json", "*.txt", "*.model", "*.safetensors", "*.bin", "*.py", "sentencepiece*",
         "1_Pooling/*", "*.md"]
IGNORE = ["onnx/*", "openvino/*", "*.onnx", "tf_model.h5", "flax_model.msgpack", "*.ot",
          "training_args.bin"]


def _token() -> str | None:
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    env = ROOT / "backend" / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("HF_TOKEN=") and line.split("=", 1)[1].strip():
                return line.split("=", 1)[1].strip()
    return None


def main(names: list[str]) -> int:
    from huggingface_hub import snapshot_download

    out = ROOT / "models"
    out.mkdir(exist_ok=True)
    token = _token()
    failed = []
    for name in names or list(MODELS):
        repo = MODELS[name]
        target = out / repo.replace("/", "--")
        print(f"-> {name}: {repo}")
        try:
            snapshot_download(repo, local_dir=str(target), token=token, allow_patterns=ALLOW,
                              ignore_patterns=IGNORE)
            # prefer safetensors: drop a duplicate pytorch_model.bin if both exist
            if (target / "model.safetensors").exists() and (target / "pytorch_model.bin").exists():
                (target / "pytorch_model.bin").unlink()
        except Exception as exc:  # report and continue with the others
            print(f"   FAILED: {exc}")
            failed.append(name)
    print("done" if not failed else f"failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
