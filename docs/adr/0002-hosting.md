# ADR 0002: Hosting approach

- Status: Accepted (target topology); the final choice of URL layout is made at Phase 5
- Date: 2026-09-29
- Owner: architect
- Approved by: Om Soma

## Context
TRIVENI ran on Render's free tier (Docker, 512 MB, 0.1 CPU). The code bundle was pulled from a private Hugging Face repo at boot, a Cloudflare keep-alive Worker hit the service, and a warm-up screen covered cold starts (`docs/HOSTING_NOTES.md`). What hurt: cold starts, too little RAM, the database resetting on every restart, and manual bundling.

DEEPASTAMBHA adds needs TRIVENI did not have:
- An ONNX int8 transformer, roughly 250 to 300 MB in memory.
- Postgres that persists across restarts.
- A Redis Streams bus.

## Decision
1. **API and inference:** a Hugging Face **Docker Space** (free CPU tier, far more RAM than Render free).
   - The Dockerfile follows TRIVENI's pattern: `python:3.11-slim`, a non-root user, `MALLOC_ARENA_MAX=2`, a pinned runtime requirements file.
   - Render free stays as the documented fallback. If Render is used, inference moves to a separate Space.
2. **Postgres:** Neon free tier, which persists and so ends the reset-on-restart pain.
3. **Redis:** Upstash (Redis Streams supported).
4. **Frontend:** Next.js on Vercel. The API has a locked CORS allowlist. The alternative, a static export served by the API from one URL (TRIVENI's pattern), gets re-evaluated at Phase 5 and a follow-up ADR records the choice.
5. **Warmth:** a Cloudflare Worker cron pings `/healthz` every 10 minutes, and the console shows a "starting up" state while it polls `/healthz`.
6. **Mode:** the hosted mode is `MODE=replay`, with SYNTHETIC injection. Live connectors need explicit env flags and are never enabled on the public demo.
7. **Secrets:** only in host env settings. Never in the repo, the docs or the bundle.

## Consequences
- The local Docker Compose stack (ADR 0003) mirrors this topology: API container, Postgres 16 and Redis 7.
- `docs/DEPLOY.md` will list every env var and every step. It is written in Phase 5.
- The Hugging Face Space's RAM and CPU limits must be re-checked at deploy time, because free tiers change.
