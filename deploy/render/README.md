# SATYA-NET on Render (free)

Docker web service built from this repo (`render.yaml` blueprint,
`deploy/render/Dockerfile`, context = repo root). At start-up `start.sh`
downloads the private demo bundle from the Hugging Face dataset
`ZOROxJODD/satyanet-bundle` (analysed demo DB + ledger signing key).

Secrets (Render environment): `HF_TOKEN` (read access to the bundle),
`GEMINI_API_KEY` (optional, LLM summaries). Health check: `/healthz`.
Free services sleep after ~15 idle minutes; `deploy/keepalive` (Cloudflare
cron Worker) pings every 10 minutes so the site never sleeps.
