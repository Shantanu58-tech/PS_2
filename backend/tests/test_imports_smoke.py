"""ADR 0004 rule 4: import every native dependency so a blocked DLL (Windows
Smart App Control raises ImportError "DLL load failed") fails loudly.
A package that is simply not installed is skipped, not failed."""
import importlib
import importlib.util

import pytest

NATIVE = ["numpy", "scipy", "sklearn.ensemble", "sklearn.cluster", "pandas", "cryptography.hazmat.primitives.asymmetric.ed25519",
          "PIL.Image", "imagehash", "networkx", "pydantic_core", "torch", "transformers", "sentence_transformers",
          "umap", "hdbscan", "faiss", "cv2", "bertopic", "sentencepiece", "opentimestamps.core.timestamp"]


@pytest.mark.parametrize("module", NATIVE)
def test_native_import(module):
    if importlib.util.find_spec(module.split(".")[0]) is None:
        pytest.skip(f"{module} not installed")
    importlib.import_module(module)
