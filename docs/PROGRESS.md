# Progress log

## 2026-09-29: Phase 0 started

**Done**
- Read the build brief and the research report. The Phase 0 and Phase 1 plan was approved by Om.
- Repo decision: build in `D:\SIH_P2` (not `D:\DEEPASTAMBHA`); the project name stays DEEPASTAMBHA.
- Initialised git on `main`. Moved the docs to `docs/BUILD_BRIEF.md` and `docs/research/RESEARCH_REPORT.md`. Created the `D:\DEEPASTAMBHA_DATA` tree.
- Read `D:\SIH` (read-only) and wrote `docs/HOSTING_NOTES.md`.
- ADRs 0001 (stack), 0002 (hosting), 0003 (local infra), 0004 (Smart App Control).
- Wrote `CLAUDE.md`, `PLAN.md`, `BACKLOG.md`, `SCORECARD_MAP.md` and the eight agents in `.claude/agents/`.
- Backend skeleton: FastAPI `/healthz`, typed settings, a Dockerfile and `docker-compose.yml`. 2 tests pass and ruff is clean.
- Next.js 16 console skeleton: dark theme, 8 routes, an engine warm-up indicator, provenance badges and the credit footer. It builds and lints clean.
- Smoke test: the API `/healthz` returns 200 and every console route returns 200. CORS allows `localhost:3000` and rejects other origins.
- `docs/PPT_SUPPORT.md` written for the idea PPT.

**What broke**
- Windows Smart App Control blocked the newest native wheels (`pyarrow 25`, `orjson 3.12`). The fix was a uv `exclude-newer` cutoff (ADR 0004); `orjson` was dropped.
- Starlette deprecated `httpx` in its test client, so `httpx2` was added as a dev dependency.

**Blocked**
- The Phase 0 gate needs `docker compose up`, and Docker Desktop is not installed yet.
- The gitleaks scan will run through its release binary or Docker image.

**Next**
- Docker Desktop install (Om), then the compose gate and gitleaks, then tag `phase-0`.
- Phase 1: the data spine.
