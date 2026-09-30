#!/usr/bin/env bash
# Fetch the private demo bundle (analysed DB + ledger keys) and start DEEPASTAMBHA.
# Env (Render secrets): HF_TOKEN (read access to the bundle), GEMINI_API_KEY (optional).
# Optional: BUNDLE_REPO. Render provides PORT.
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
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}" --proxy-headers --forwarded-allow-ips='*'
