# SATYA-NET — Project Status Report
**Team MOGGERS · VIT Pune · SIH 2026 · PS 26152 (NTRO)**
_Last audited: 2026-09-29 | Do not modify files listed under "Do Not Harm"_

---

## Legend
| Symbol | Meaning |
|--------|---------|
| ✅ | Complete — file exists, logic implemented, tests pass |
| ⚠️ | Partial — file exists but feature is stubbed, incomplete, or has a known failing test |
| ❌ | Missing — file/feature not yet created |
| 🔒 | Do Not Harm — fully working, do not touch without a clear reason |

---

## 1. DO NOT HARM — Fully Working Files

These files are complete, tested, and must not be modified without a specific bug fix or milestone reason.

### Backend Core
| File | What it does | Test coverage |
|------|-------------|---------------|
| 🔒 `backend/app/config.py` | Pydantic-settings config; loads all `.env` keys cleanly | `test_health.py::test_config_loads` ✅ |
| 🔒 `backend/app/version.py` | Single-source version string `0.1.0` | — |
| 🔒 `backend/app/main.py` | FastAPI app wiring: lifespan, CORS, all routers, static mount | — |
| 🔒 `backend/app/db/schema.sql` | SQLite DDL: `raw_records`, `posts`, `accounts`, `edges`, `cases`, `alerts` tables with triggers | `test_health.py::test_db_init_creates_tables` ✅ |
| 🔒 `backend/app/db/session.py` | `init_db_sync()` runs schema.sql on startup | `test_health.py::test_schema_sql_exists` ✅ |
| 🔒 `backend/app/db/repo.py` | `upsert_post()`, `upsert_account()` insert-or-ignore DB helpers | — |

### Analytics
| File | What it does | Test coverage |
|------|-------------|---------------|
| 🔒 `backend/app/analytics/burst.py` | Kleinberg burst detector (gamma·ln(n) up-transition cost), Goh-Barabasi burstiness, binned normalised entropy | `test_burst.py` 6/7 pass ✅ (1 failing — see R1) |
| 🔒 `backend/app/analytics/coordination.py` | Temporal sync scoring, norm-entropy coordination signal | Covered via ledger tests ✅ |
| 🔒 `backend/app/analytics/demographics.py` | Cohort-only demographics; k-anonymity suppression (K=10); no per-account exposure | `test_demographics.py` 4/4 pass ✅ |
| 🔒 `backend/app/analytics/graph.py` | NetworkX in-memory graph; degree/community compute | — |
| 🔒 `backend/app/analytics/lineage.py` | Cross-platform narrative lineage tracing | — |
| 🔒 `backend/app/analytics/signals.py` | Alert signal generation | — |
| 🔒 `backend/app/analytics/topics.py` | Topic clustering with windowed re-clustering + centroid matching | — |
| 🔒 `backend/app/analytics/cases.py` | Case brief generation (Jinja2 HTML); tamper-evident export | — |

### Ledger
| File | What it does | Test coverage |
|------|-------------|---------------|
| 🔒 `backend/app/ledger/canonical.py` | Deterministic canonical JSON serialisation | `test_ledger.py::test_canonical_json_deterministic` ✅ |
| 🔒 `backend/app/ledger/chain.py` | Append-only HMAC chain over `raw_records` | `test_ledger.py::test_ledger_chain_and_verify` ✅ |
| 🔒 `backend/app/ledger/merkle.py` | Merkle tree checkpoints | `test_ledger.py::test_merkle_root_changes_on_tamper` ✅ |
| 🔒 `backend/app/ledger/verify.py` | `verify_chain()` full chain integrity check | `test_ledger.py::test_tamper_detection` ✅ |
| 🔒 `backend/app/ledger/sign.py` | Ed25519 signing of Merkle roots | — |
| ⚠️ `backend/app/ledger/ots.py` | OpenTimestamps — STUB ONLY; returns placeholder until Bitcoin node available | — |

### NLP
| File | What it does | Test coverage |
|------|-------------|---------------|
| 🔒 `backend/app/nlp/embed.py` | Sentence embeddings via `paraphrase-multilingual-MiniLM-L12-v2` | — |
| 🔒 `backend/app/nlp/emotion.py` | Sentiment/emotion via `twitter-xlm-roberta-base-sentiment` + `emotion-english-distilroberta-base` | — |
| 🔒 `backend/app/nlp/langid.py` | Language detection via `xlm-roberta-base-language-detection` | — |
| 🔒 `backend/app/nlp/hinglish.py` | Hinglish-specific affect handling | — |

### Pipeline
| File | What it does | Test coverage |
|------|-------------|---------------|
| 🔒 `backend/app/pipeline/normalize.py` | Platform normalizers: X, Telegram, Reddit, YouTube, synthetic | `test_normalizers.py` 4/4 pass ✅ |
| 🔒 `backend/app/pipeline/queue.py` | Async `IngestQueue` backed by `asyncio.Queue` | — |
| 🔒 `backend/app/pipeline/workers.py` | `ingest_record()`: normalize → upsert post/account → write edges | — |

### Collectors
| File | What it does | Status |
|------|-------------|--------|
| 🔒 `backend/app/collectors/base.py` | Abstract `Collector` interface | ✅ |
| ⚠️ `backend/app/collectors/x_twscrape.py` | X/Twitter collector — requires `X_AUTH_TOKEN`, `X_CT0` in `.env` | Needs credentials |
| ⚠️ `backend/app/collectors/telegram_telethon.py` | Telegram collector — requires `TG_API_ID`, `TG_API_HASH` | Needs credentials |
| ⚠️ `backend/app/collectors/reddit_praw.py` | Reddit collector — requires `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | Needs credentials |
| ⚠️ `backend/app/collectors/youtube_api.py` | YouTube collector — requires `YT_API_KEY` | Needs credentials |
| 🔒 `backend/app/collectors/replay.py` | Replay collector — reads `.jsonl` scenario file; works out-of-box | ✅ |

### API Layer
| File | What it does | Status |
|------|-------------|--------|
| 🔒 `backend/app/api/health.py` | `/healthz` endpoint | ✅ |
| ⚠️ `backend/app/api/routers/` | All router files imported in `main.py` (`posts`, `timeline`, `topics`, `graph`, `coordination`, `lineage`, `demographics`, `alerts`, `cases`, `ledger_router`, `stream`, `collectors`, `search`, `eval_router`, `replay_router`, `traceability`) — must verify these files exist under `app/api/routers/` | Verify existence |

### Scenario & Eval
| File | What it does | Status |
|------|-------------|--------|
| 🔒 `scenario/generate.py` | Generates synthetic JSONL scenario (seed 7); organic + coordinated burst posts; `synthetic=true` flagged | ✅ |
| 🔒 `scenario/truth_schema.json` | Ground-truth schema for eval comparison | ✅ |
| 🔒 `scenario/__init__.py` | Package init | ✅ |
| ❌ `backend/eval/run_all.py` | Main eval runner — directory exists but `run_all.py` is missing | NOT CREATED |
| ❌ `eval/reports/summary.json` | Required output of `make eval` — does not exist | NOT CREATED |

### Tests
| Test file | Tests | Status |
|-----------|-------|--------|
| 🔒 `tests/test_burst.py` | 7 tests | 6 pass ✅ / 1 fail ⚠️ (`test_norm_entropy_uniform`) |
| 🔒 `tests/test_demographics.py` | 4 tests | All 4 pass ✅ |
| 🔒 `tests/test_health.py` | 5 tests | All 5 pass ✅ |
| 🔒 `tests/test_ledger.py` | 6 tests | All 6 pass ✅ |
| 🔒 `tests/test_normalizers.py` | 4 tests | All 4 pass ✅ |

### Config & Infrastructure
| File | Status |
|------|--------|
| 🔒 `.env.example` | All keys documented; no secrets committed ✅ |
| 🔒 `docker-compose.yml` | Backend service; volumes for `data/`, `models/`, `replay/` ✅ |
| 🔒 `Makefile` | `setup`, `demo`, `live`, `test`, `eval`, `verify`, `scenario`, `lint` targets ✅ |
| 🔒 `backend/Dockerfile` | Container for backend ✅ |
| 🔒 `backend/pyproject.toml` | All deps pinned; `uv.lock` committed ✅ |
| 🔒 `.gitignore` / `.gitattributes` / `.gitleaksignore` | Secrets excluded ✅ |

### Frontend — Working Components
| File | What it does | Status |
|------|-------------|--------|
| 🔒 `frontend/src/main.tsx` | React root; QueryClient + BrowserRouter | ✅ |
| 🔒 `frontend/src/components/Layout.tsx` | App shell layout with sidebar | ✅ |
| 🔒 `frontend/src/components/Sidebar.tsx` | Navigation sidebar | ✅ |
| 🔒 `frontend/src/components/EngineStatus.tsx` | Engine/collector status panel | ✅ |
| 🔒 `frontend/src/components/ProvenanceBadge.tsx` | SIMULATED / LIVE badge | ✅ |
| 🔒 `frontend/src/components/SectionPlaceholder.tsx` | Placeholder for unimplemented pages | ✅ |
| 🔒 `frontend/src/lib/api.ts` | API client base | ✅ |
| 🔒 `frontend/src/lib/nav.ts` | Navigation config | ✅ |
| 🔒 `frontend/src/hooks/useApi.ts` | React Query hooks for API calls | ✅ |
| 🔒 `frontend/src/store/app.ts` | Zustand app state store | ✅ |
| 🔒 `frontend/src/pages/CommandCenter.tsx` | Main dashboard with guided tour | ✅ |
| 🔒 `frontend/src/pages/Ledger.tsx` | Ledger verify + tamper-sim UI | ✅ |
| 🔒 `frontend/src/pages/Network.tsx` | Network graph view | ✅ |
| 🔒 `frontend/src/pages/TimelineEmotions.tsx` | Emotion timeline | ✅ |
| 🔒 `frontend/src/pages/Compliance.tsx` | PS 26152 traceability panel | ✅ |
| 🔒 `frontend/src/pages/CaseFile.tsx` | Case file / brief viewer | ✅ |
| 🔒 `frontend/src/pages/Audience.tsx` | Cohort demographics viewer | ✅ |
| 🔒 `frontend/src/pages/Lineage.tsx` | Narrative lineage view | ✅ |
| 🔒 `frontend/src/pages/Search.tsx` | Post search UI | ✅ |
| 🔒 `frontend/src/pages/Trends.tsx` | Topic trends view | ✅ |

### Docs
| File | Status |
|------|--------|
| 🔒 `docs/BUILD_BRIEF.md` | Full project build brief ✅ |
| 🔒 `docs/BACKLOG.md` | Future work backlog ✅ |
| 🔒 `docs/PLAN.md` | Phase plan ✅ |
| 🔒 `docs/HOSTING_NOTES.md` | Deployment/hosting notes ✅ |
| 🔒 `docs/PPT_SUPPORT.md` | Presentation support material ✅ |
| 🔒 `docs/PROGRESS.md` | Progress tracker ✅ |
| 🔒 `docs/SCORECARD_MAP.md` | SIH scorecard to code traceability ✅ |
| 🔒 `docs/adr/0001-stack.md` | ADR: Technology stack ✅ |
| 🔒 `docs/adr/0002-*.md` | ADR: Hosting ✅ |
| 🔒 `docs/adr/0004-windows-smart-app-control.md` | ADR: Windows Smart App Control workaround ✅ |
| ❌ `docs/DECISIONS.md` | Required by CLAUDE.md rule 10 — does NOT exist |

---

## 2. REMAINING WORK — What Still Needs to Be Done

### Critical / Blocking (fix before any milestone advance)

| # | Task | Location | Why it blocks |
|---|------|----------|--------------|
| R1 | **Fix `test_norm_entropy_uniform` failure** | `backend/app/analytics/burst.py` → `norm_entropy()` | `make test` cannot be clean until this passes; CLAUDE.md rule 1 forbids advancing milestones with failing tests |
| R2 | **Verify / create all API router files** | `backend/app/api/routers/` — need: `posts.py`, `timeline.py`, `topics.py`, `graph.py`, `coordination.py`, `lineage.py`, `demographics.py`, `alerts.py`, `cases.py`, `ledger_router.py`, `stream.py`, `collectors.py`, `search.py`, `eval_router.py`, `replay_router.py`, `traceability.py` | `main.py` imports all 16; if any are missing the server crashes on startup |
| R3 | **Create `backend/eval/run_all.py`** | `backend/eval/run_all.py` | `make eval` calls `python -m eval.run_all`; the file does not exist; no metrics can be measured |
| R4 | **Produce `eval/reports/summary.json`** | Run `make eval` after R3 is done | All metrics in README say "not yet measured"; CLAUDE.md rule 3 forbids showing numbers not from this file |
| R5 | **Create `docs/DECISIONS.md`** | `docs/DECISIONS.md` | CLAUDE.md rule 10 requires every library API adaptation to be documented here; the file is missing |

### Important / Pre-demo

| # | Task | Location | Notes |
|---|------|----------|-------|
| R6 | **Wire frontend app-router pages to real components** | `frontend/src/app/audience/page.tsx`, `audit/page.tsx`, `coordination/page.tsx`, `eval/page.tsx`, `narratives/page.tsx`, `network/page.tsx`, `sources/page.tsx` | All 7 use `<SectionPlaceholder>` — they should render the corresponding `pages/` components |
| R7 | **OpenTimestamps stub — document or implement** | `backend/app/ledger/ots.py` | Flagged in README as stubbed; document in `DECISIONS.md` if kept as stub |
| R8 | **Generate replay scenario file** | `replay/scenario_v1.jsonl` | Run `make scenario`; directory is empty; Docker volume mounts this path |
| R9 | **Download or document HuggingFace models** | `models/` directory | Empty; NLP pipelines expect models here or via HF_TOKEN; document the fetch process |
| R10 | **Populate data sub-directories** | `data/gazetteer/`, `data/lexicons/`, `data/media/` | All three are empty; demographics and NLP modules likely depend on these files |
| R11 | **Test live collectors end-to-end** | `backend/app/collectors/x_twscrape.py` etc. | After credentials are added (see H1-H4 below), each collector should be run and verified at least once |
| R12 | **GitHub Actions CI** | `.github/workflows/` | Backlog item 6; pytest + ruff + gitleaks + Playwright pipeline not set up |

### Low Priority / Post-Demo Backlog

| # | Task | Notes |
|---|------|-------|
| B1 | Hawkes-process intensity forecast | After gradient-boosting baseline is proven (Backlog #1) |
| B2 | Neo4j swap for graph store | Postgres edges are enough at demo scale (Backlog #2) |
| B3 | Experimental account-behaviour likelihood | Must be labelled "experimental"; never call it "bot" in UI (Backlog #3) |
| B4 | LLM-assisted narrative summaries | Requires prompt-injection break test first (Backlog #4) |
| B5 | Static-export console from single URL | Alternative to Vercel + CORS (Backlog #5) |

---

## 3. Complete File Tree with Status

```
MOGGERS_V2-main/
├── .env.example                          🔒 Complete
├── .gitignore                            🔒 Complete
├── .gitattributes                        🔒 Complete
├── .gitleaksignore                       🔒 Complete
├── CLAUDE.md                             🔒 Complete (project rules)
├── docker-compose.yml                    🔒 Complete
├── LICENSE                               🔒 Complete
├── Makefile                              🔒 Complete
├── README.md                             🔒 Complete (metrics show "not yet measured" until eval runs)
│
├── .claude/agents/                       🔒 All 8 agent role files present
│   ├── architect.md
│   ├── frontend-engineer.md
│   ├── graph-analyst.md
│   ├── ingestion-engineer.md
│   ├── nlp-ml-engineer.md
│   ├── privacy-officer.md
│   ├── red-team-qa.md
│   └── research-integrator.md
│
├── backend/
│   ├── Dockerfile                        🔒 Complete
│   ├── pyproject.toml                    🔒 Complete
│   ├── uv.lock                           🔒 Complete
│   ├── app/
│   │   ├── config.py                     🔒 Complete
│   │   ├── main.py                       🔒 Complete
│   │   ├── version.py                    🔒 Complete
│   │   ├── __init__.py                   🔒 Complete
│   │   ├── analytics/
│   │   │   ├── burst.py                  ⚠️  1 failing test (test_norm_entropy_uniform)
│   │   │   ├── cases.py                  🔒 Complete
│   │   │   ├── coordination.py           🔒 Complete
│   │   │   ├── demographics.py           🔒 Complete
│   │   │   ├── graph.py                  🔒 Complete
│   │   │   ├── lineage.py                🔒 Complete
│   │   │   ├── signals.py                🔒 Complete
│   │   │   ├── topics.py                 🔒 Complete
│   │   │   └── __init__.py               🔒 Complete
│   │   ├── api/
│   │   │   ├── health.py                 🔒 Complete
│   │   │   ├── __init__.py               🔒 Complete
│   │   │   └── routers/                  ❌ Sub-package must contain 16 router files
│   │   ├── collectors/
│   │   │   ├── base.py                   🔒 Complete
│   │   │   ├── replay.py                 🔒 Complete (works without credentials)
│   │   │   ├── x_twscrape.py             ⚠️  Needs X credentials in .env
│   │   │   ├── telegram_telethon.py      ⚠️  Needs Telegram credentials in .env
│   │   │   ├── reddit_praw.py            ⚠️  Needs Reddit credentials in .env
│   │   │   ├── youtube_api.py            ⚠️  Needs YouTube API key in .env
│   │   │   └── __init__.py               🔒 Complete
│   │   ├── db/
│   │   │   ├── repo.py                   🔒 Complete
│   │   │   ├── schema.sql                🔒 Complete
│   │   │   ├── session.py                🔒 Complete
│   │   │   └── __init__.py               🔒 Complete
│   │   ├── ledger/
│   │   │   ├── canonical.py              🔒 Complete
│   │   │   ├── chain.py                  🔒 Complete
│   │   │   ├── merkle.py                 🔒 Complete
│   │   │   ├── ots.py                    ⚠️  Stub — placeholder until real OTS available
│   │   │   ├── sign.py                   🔒 Complete
│   │   │   ├── verify.py                 🔒 Complete
│   │   │   └── __init__.py               🔒 Complete
│   │   ├── models/
│   │   │   ├── canonical.py              🔒 Complete
│   │   │   └── __init__.py               🔒 Complete
│   │   ├── nlp/
│   │   │   ├── embed.py                  🔒 Complete
│   │   │   ├── emotion.py                🔒 Complete
│   │   │   ├── hinglish.py               🔒 Complete
│   │   │   ├── langid.py                 🔒 Complete
│   │   │   └── __init__.py               🔒 Complete
│   │   └── pipeline/
│   │       ├── normalize.py              🔒 Complete
│   │       ├── queue.py                  🔒 Complete
│   │       ├── workers.py                🔒 Complete
│   │       └── __init__.py               🔒 Complete
│   ├── eval/                             ❌ run_all.py is missing
│   ├── replay/                           (populated at runtime by `make scenario`)
│   ├── scenario/
│   │   ├── generate.py                   🔒 Complete
│   │   ├── truth_schema.json             🔒 Complete
│   │   └── __init__.py                   🔒 Complete
│   └── tests/
│       ├── test_burst.py                 ⚠️  6/7 pass — 1 failing
│       ├── test_demographics.py          🔒 4/4 pass
│       ├── test_health.py                🔒 5/5 pass
│       ├── test_ledger.py                🔒 6/6 pass
│       ├── test_normalizers.py           🔒 4/4 pass
│       └── __init__.py                   🔒 Complete
│
├── data/
│   ├── gazetteer/                        ❌ Empty — needed for demographics
│   ├── lexicons/                         ❌ Empty — needed for NLP
│   └── media/                            ❌ Empty
│
├── docs/
│   ├── BUILD_BRIEF.md                    🔒 Complete
│   ├── BACKLOG.md                        🔒 Complete
│   ├── PLAN.md                           🔒 Complete
│   ├── HOSTING_NOTES.md                  🔒 Complete
│   ├── PPT_SUPPORT.md                    🔒 Complete
│   ├── PROGRESS.md                       🔒 Complete
│   ├── SCORECARD_MAP.md                  🔒 Complete
│   ├── DECISIONS.md                      ❌ Missing — required by CLAUDE.md rule 10
│   ├── adr/
│   │   ├── 0001-stack.md                 🔒 Complete
│   │   ├── 0002-*.md                     🔒 Complete
│   │   └── 0004-windows-smart-app-control.md 🔒 Complete
│   └── research/                         🔒 Research files present
│
├── eval/
│   └── reports/
│       └── summary.json                  ❌ Does not exist — produce with `make eval`
│
├── frontend/
│   ├── index.html                        🔒 Complete
│   ├── vite.config.ts                    🔒 Complete
│   ├── tsconfig.json                     🔒 Complete
│   ├── package.json                      🔒 Complete
│   ├── tailwind.config.js                🔒 Complete
│   ├── postcss.config.js                 🔒 Complete
│   ├── eslint.config.mjs                 🔒 Complete
│   ├── Dockerfile                        🔒 Complete
│   └── src/
│       ├── main.tsx                      🔒 Complete
│       ├── app/
│       │   ├── layout.tsx                🔒 Complete
│       │   ├── page.tsx                  🔒 Complete (root)
│       │   ├── audience/page.tsx         ⚠️  SectionPlaceholder — not wired to Audience.tsx
│       │   ├── audit/page.tsx            ⚠️  SectionPlaceholder — not wired to real component
│       │   ├── coordination/page.tsx     ⚠️  SectionPlaceholder — not wired to real component
│       │   ├── eval/page.tsx             ⚠️  SectionPlaceholder — not wired to real component
│       │   ├── narratives/page.tsx       ⚠️  SectionPlaceholder — not wired to real component
│       │   ├── network/page.tsx          ⚠️  SectionPlaceholder — not wired to Network.tsx
│       │   └── sources/page.tsx          ⚠️  SectionPlaceholder — not wired to real component
│       ├── components/
│       │   ├── EngineStatus.tsx          🔒 Complete
│       │   ├── Layout.tsx                🔒 Complete
│       │   ├── ProvenanceBadge.tsx       🔒 Complete
│       │   ├── SectionPlaceholder.tsx    🔒 Complete
│       │   └── Sidebar.tsx               🔒 Complete
│       ├── hooks/
│       │   └── useApi.ts                 🔒 Complete
│       ├── lib/
│       │   ├── api.ts                    🔒 Complete
│       │   └── nav.ts                    🔒 Complete
│       ├── pages/
│       │   ├── Audience.tsx              🔒 Complete
│       │   ├── CaseFile.tsx              🔒 Complete
│       │   ├── CommandCenter.tsx         🔒 Complete (includes guided tour)
│       │   ├── Compliance.tsx            🔒 Complete
│       │   ├── Ledger.tsx                🔒 Complete
│       │   ├── Lineage.tsx               🔒 Complete
│       │   ├── Network.tsx               🔒 Complete
│       │   ├── Search.tsx                🔒 Complete
│       │   ├── TimelineEmotions.tsx      🔒 Complete
│       │   └── Trends.tsx                🔒 Complete
│       └── store/
│           └── app.ts                    🔒 Complete
│
├── models/                               ❌ Empty — HF models not downloaded
├── replay/                               ❌ Empty — run `make scenario` to populate
├── scenario/                             🔒 Complete (top-level copy mirrors backend/scenario)
└── training/                             ❌ Empty (intentional — no training needed per CLAUDE.md)
```

---

## 4. Action Priority Queue

Run these in order. Do not skip a step while the previous has failing tests.

```powershell
# STEP 1: Diagnose the failing burst test
cd D:\MOGGERS_V2-main\MOGGERS_V2-main\backend
python -m pytest tests/test_burst.py::test_norm_entropy_uniform -v --tb=long

# STEP 2: Fix burst.py norm_entropy(), then confirm all tests pass
python -m pytest tests/ -v --tb=short -p no:warnings

# STEP 3: Create docs/DECISIONS.md

# STEP 4: Verify all 16 router files exist under app/api/routers/
#         Create any that are missing

# STEP 5: Create backend/eval/run_all.py

# STEP 6: Generate scenario (populates replay/)
make scenario

# STEP 7: Run eval to produce eval/reports/summary.json
make eval

# STEP 8: Wire 7 frontend placeholder pages to real components

# STEP 9: Run lint
make lint

# STEP 10: Full test + lint green before next milestone
make test
```

---

## 5. Human-Only Blockers (cannot be done by code)

These require action from the operator (Om Soma or team lead):

| # | Blocker | Required from |
|---|---------|--------------|
| H1 | X/Twitter credentials: `X_AUTH_TOKEN`, `X_CT0`, `X_ACCOUNT_USER` | Operator |
| H2 | Telegram API credentials: `TG_API_ID`, `TG_API_HASH`, session file | Operator |
| H3 | Reddit app credentials: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | Operator |
| H4 | YouTube Data API key: `YT_API_KEY` | Operator |
| H5 | HuggingFace token: `HF_TOKEN` (for rate-limited or private models) | Operator |
| H6 | Windows Smart App Control decision — turning it off is one-way (see ADR 0004) | Om only |
| H7 | Bitcoin node or OTS calendar for real OpenTimestamps proofs in `ots.py` | Operator |

---

## 6. Test Health Summary

| Suite | Total | Pass | Fail | Skip |
|-------|-------|------|------|------|
| `test_burst.py` | 7 | 6 | 1 — `test_norm_entropy_uniform` | 0 |
| `test_demographics.py` | 4 | 4 | 0 | 0 |
| `test_health.py` | 5 | 5 | 0 | 0 |
| `test_ledger.py` | 6 | 6 | 0 | 0 |
| `test_normalizers.py` | 4 | 4 | 0 | 0 |
| **Total** | **26** | **25** | **1** | **0** |

Eval metrics (`emotion scoring`, `demographics`, `pipeline end-to-end`) all show **"not yet measured"** because `eval/run_all.py` does not exist yet and `eval/reports/summary.json` has never been produced.

---

## 7. PS 26152 Requirement Traceability

| Req | Description | Backend module | Test | UI page | Status |
|-----|-------------|---------------|------|---------|--------|
| A | Multi-platform collection (X, Telegram, Reddit, YouTube) | `app/collectors/*` | — | Sources | ⚠️ Live collectors need credentials |
| A | Replay / historical mode | `app/collectors/replay.py` | — | — | ✅ Ready |
| B | Coordinated inauthentic behaviour (Kleinberg, Goh-Barabasi, norm-entropy, temporal sync) | `app/analytics/burst.py`, `coordination.py` | `test_burst.py` | Command Center | ⚠️ 1 test failing |
| C | Tamper-evident append-only ledger + Merkle + Ed25519 | `app/ledger/*` | `test_ledger.py` | Ledger page | ✅ Complete |
| D | Privacy-preserving cohort demographics (k-anon >= 10, no per-account exposure) | `app/analytics/demographics.py` | `test_demographics.py` | Audience page | ✅ Complete |
| E | Analyst UI: timeline, alert dashboard, graph view, case certificates, PS traceability panel | `frontend/src/pages/*` | — | All pages | ⚠️ 7 routes use placeholder |
| Theme | Ethical AI: synthetic flagged, SIMULATED banner, secrets in .env only | Throughout | — | ProvenanceBadge | ✅ Complete |

---

_This file is generated from a full codebase audit. Update it after each milestone._
