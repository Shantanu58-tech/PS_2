# Hosting notes: how TRIVENI (SIH26027) was hosted, and what DEEPASTAMBHA takes from it

Source: a read-only review of `D:\SIH` on 2026-09-29. No secrets were opened or copied. Env var **names** are listed below, never their values.

## 1. What TRIVENI shipped

| Part | What it was |
|---|---|
| Main repo | `D:\SIH\SIH`. It was called RAILSYNC-X before being renamed TRIVENI. |
| Backend | Python 3.11 with FastAPI and uvicorn. The core is one 2,112-line `backend/main.py`, plus routers in `backend/api/`. |
| Database | SQLite (`data/processed/triveni.db`) accessed with raw `sqlite3`. A PostGIS service existed in `docker-compose.yml` but was only ever used locally. |
| Cache / queue | None |
| ML / optimisation | OR-Tools CP-SAT, scikit-learn, XGBoost, SHAP, networkx |
| Frontend | React 19, Vite 8, TypeScript, Tailwind 4, recharts, leaflet, react-force-graph-2d |
| Tests | 70 pytest tests plus one Playwright smoke test |
| CI | None. Deploys were done by hand. |

## 2. Hosting topology

```
Cloudflare Worker (cron */10) --ping /healthz--> Render free web service (Docker, 512 MB, 0.1 CPU)
                                                   start.sh:
                                                     hf_hub_download(private HF repo) -> bundle.tar.gz
                                                       (code + SQLite snapshot + models + built frontend)
                                                     uvicorn backend.main:app --port $PORT --proxy-headers
                                                   FastAPI mounts frontend/dist -> one URL serves API + UI
Vercel (optional) -> SPA only, VITE_API_BASE_URL -> Render
Hugging Face Docker Space (alternative) -> same Dockerfile, app_port 7860
```

- **Dockerfile:** `deploy/render/Dockerfile`. It builds from `python:3.11-slim`, installs `libgomp1`, runs as a non-root user, sets `MALLOC_ARENA_MAX=2`, and uses a pinned `requirements-runtime.txt`.
- **Image contents:** the image holds dependencies only. Code, data and models arrive at boot from a private Hugging Face repo (`BUNDLE_REPO`, authenticated with `HF_TOKEN`). This kept the Render build repo small and private.
- **Tunnels:** there was also a local tunnel option (`deploy/start_hosted.ps1`) using ngrok or Cloudflare Tunnel, with a Google OAuth email allowlist.

### Env var names used
- **Backend:** `HF_TOKEN`, `BUNDLE_REPO`, `PORT`, `TZ`, `TRIVENI_JWT_SECRET`, `TRIVENI_JWT_ALG`, `TRIVENI_JWT_EXP_MINUTES`, `TRIVENI_JWT_ISSUER`, `TRIVENI_ACCESS_KEY`, `TRIVENI_CORS_ORIGIN_REGEX`, `TRIVENI_SOLVE_TIME_SCALE`, `TRIVENI_SOLVER_WORKERS`, `TRIVENI_ADMIN_USERNAME`, `TRIVENI_ADMIN_EMAIL`, `TRIVENI_ADMIN_PASSWORD`, `TRIVENI_BCRYPT_ROUNDS`, `TRIVENI_SEED_DEMO_USERS`, `TRIVENI_MODE`, `TRIVENI_PLANNING_READONLY`, `TRIVENI_PRIORITY_ENGINE`.
- **Frontend:** `VITE_API_BASE_URL`, `VITE_DEMO_MODE`, `VITE_MAP_TILE_URL`, `VITE_MAP_TILE_ATTRIBUTION`.

## 3. What worked
- **One URL for API and UI:** no CORS problems during judging, and just one thing to keep warm.
- **Keep-alive:** a Cloudflare Worker cron hitting `/healthz` every 10 minutes kept the free Render dyno awake. `/healthz` was exempt from the access gate.
- **Warm-up screen:** `EngineWake.tsx` showed a "starting the engine" screen that polled `/healthz`, so judges never saw a broken page on a cold start.
- **Private bundle:** pulling the bundle from Hugging Face at boot kept code and data private and the image small.
- **Honest degradation:** when the solver hit its time limit it returned `no_solution` rather than faking a result.

## 4. What hurt
1. **Cold starts:** Render free sleeps after about 15 idle minutes, and the first load took up to a minute.
2. **Memory and CPU:** 512 MB RAM and 0.1 CPU. The solver had to be limited to 1 worker with scaled-down time limits, a 90 s cap and a low-priority thread.
3. **Resets:** the database reset on every restart, because the SQLite snapshot came back from the bundle.
4. **Redeploys:** changing an env var needed a redeploy, not just a restart.
5. **Manual bundles:** rebuilding the bundle was a manual multi-step process (build SPA → `git archive` + DB + models + dist → upload to HF → restart Render).
6. **Monolith:** the 2,000-line `main.py` was hard to test in parts.
7. **No CI:** nothing caught a broken build before the deploy.

## 5. What DEEPASTAMBHA adopts (decided in ADR 0002)

| TRIVENI lesson | DEEPASTAMBHA decision |
|---|---|
| Docker image, slim, non-root, `MALLOC_ARENA_MAX=2` | Same base, pattern and flags |
| 512 MB was too small | API plus ONNX inference on a **Hugging Face Docker Space** (free CPU tier, far more RAM). Render remains the fallback. |
| Database reset on restart | Persistent managed **Neon Postgres**; Redis Streams on **Upstash** |
| Cold starts | Reuse the Cloudflare keep-alive Worker plus a warm-up screen in the console |
| One URL, no CORS pain | Next.js console on Vercel with a locked CORS allowlist, *or* a static export served by the API. The choice is made at Phase 5 and recorded in an ADR. |
| Manual bundles | A scripted `scripts/build_bundle.ps1` and a GitHub Actions workflow (after "push now") |
| Monolith | Modular packages per component (see `CLAUDE.md` layout) |
| No CI | pytest, ruff and gitleaks in CI from Phase 5 onwards |
| Demo must never break | Hosted mode is **REPLAY + SYNTHETIC** only; live connectors are off by default |

Project: DEEPASTAMBHA, Team MOGGERS, VIT Pune. Team Leader: Om Soma.
