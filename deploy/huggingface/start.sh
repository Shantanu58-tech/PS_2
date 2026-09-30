#!/usr/bin/env bash
# Download the private demo bundle (analysed DB, ledger keys, caches) and start the app.
# Space secrets: HF_TOKEN (read access to the bundle repo), GEMINI_API_KEY (optional).
# Optional variable: BUNDLE_REPO.
set -euo pipefail
cd /home/user/app
python - <<'PY'
import os, tarfile
from huggingface_hub import hf_hub_download
path = hf_hub_download(repo_id=os.environ.get("BUNDLE_REPO", "ZOROxJODD/deepastambha-bundle"),
                       repo_type="dataset", filename="bundle.tar.gz", token=os.environ["HF_TOKEN"])
tarfile.open(path).extractall(".", filter="data")
print("bundle extracted", flush=True)
PY
cd backend
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 7860 --proxy-headers --forwarded-allow-ips='*'
