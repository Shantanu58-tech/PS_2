# DEEPASTAMBHA on Render (free)

Live: https://deepastambha.onrender.com · keepalive: https://deepastambha-keepalive.triveni-moggers.workers.dev

Docker web service built from this repo (`render.yaml` blueprint,
`deploy/render/Dockerfile`, context = repo root). At start-up `start.sh`
downloads the private demo bundle from the Hugging Face dataset
`ZOROxJODD/deepastambha-bundle` (analysed demo DB + ledger signing key).

Secrets (Render environment): `HF_TOKEN` (read access to the bundle),
`GEMINI_API_KEY` (optional, LLM summaries). Health check: `/healthz`.
Free services sleep after ~15 idle minutes; `deploy/keepalive` (Cloudflare
cron Worker) pings every 10 minutes so the site never sleeps.

## Deployment
The Render service builds from a private deployment mirror that always holds
exactly the same commits as the canonical repository,
https://github.com/Shantanu58-tech/PS_2 (both are updated by the same push).
