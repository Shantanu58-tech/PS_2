# PRAHARI: Project Status

**Team MOGGERS · VIT Pune · SIH 2026 · PS 26152 (NTRO)**
_Last verified: 2026-09-30. Every claim below was checked by running the code. Metrics come from `eval/reports/summary.json`._

## Legend
| Symbol | Meaning |
|---|---|
| ✅ | Built, tested, and wired into the API/UI |
| ⚠️ | Built but with a known limitation, or waiting on a human input |
| ❌ | Not built |

---

**Live demo:** https://prahari-h849.onrender.com · **Code:** https://github.com/Shantanu58-tech/PS_2

## 1. Verified health

| Check | Result |
|---|---|
| Backend tests (`pytest`) | **135 passed** (115 functional + 20 native-import smoke) |
| Lint / types | ruff clean, mypy clean (75 source files) |
| Frontend | `tsc --noEmit` clean, `npm run build` OK |
| Browser smoke (Playwright, single-URL server) | **11/11** routes and ledger flow pass |
| Full eval (`make eval`) | complete; about 35 min on CPU; reports in `eval/reports/` |
| Replay of the demo scenario | 37,353 records → ledger → analytics |
| Hosted demo | https://prahari-h849.onrender.com: live smoke test passes (all pages, APIs, verify, tamper-sim, case brief, Gemini, read-only guard) |

## 2. What the previous status report got wrong (corrected)
- "25/26 tests pass": no Python environment had the dependencies, so **no tests could run**.
- "test_norm_entropy_uniform fails": that test didn't exist.
- "Routers / run_all.py / summary.json missing": they existed. But the pipeline itself was
  disconnected. Ingestion **never wrote the ledger**, replayed posts collapsed to
  `post_id="unknown"`, and **no analytics stage was ever called**, so every page was empty.
- The PS letters in the README were mis-mapped (B/C/D). Fixed.
- The ledger private key was not gitignored, and **it is present in this repo's first
  commit** (see §6).

Every fix is recorded in `docs/DECISIONS.md` (D-01 … D-32).

## 3. PS 26152 coverage

| PS | Status | What exists | Measured (held-out where applicable) |
|---|---|---|---|
| A: collection and timeline | ✅/⚠️ | X, Telegram, Reddit, YouTube collectors with backoff and circuit breaker; IG/FB CSV import; replay; UTC timeline, threads | 544 records/s. Live runs **need credentials** |
| B: multi-dimensional sentiment | ⚠️ | Zero-shot mDeBERTa NLI + XLM-R sentiment; 5 dimensions; timeline raw/organic | macro-F1 **0.63** (synthetic labels, seed 11); sarcasm 0.17; panic distortion inverted (0.69) |
| C: aggregate demographics | ✅ | Geography (36-state gazetteer), interests, age (bio cues), language; k-anon K=10 + Laplace DP | geo accuracy 100%, coverage 86%; 0 released buckets below k |
| D: trends, ranking, prediction | ✅ | Windowed topics + centroid matching, Kleinberg bursts, rise score, GBR + Hawkes forecasts, Signal Cards | rumour P=72.9 (high); decoy max 61.7; **5 min** ahead of naive; 0.14 vs 35 alerts/day; forecast MAE 1.41 vs naive 3.51 |
| E: link analysis | ✅ | Interaction graph, cascade-influence KOLs, PageRank, bridges, communities, spread frames, organic-only ranks; NetworkX/Neo4j interface | planted bridge ranked **#1** |
| Theme: blockchain & cybersecurity | ✅ | Hash chain, Ed25519 Merkle checkpoints, verify, inclusion proofs, OpenTimestamps (Bitcoin) stamp/upgrade/verify, audit trail in the chain, tamper simulation, case brief + draft §63 certificate | **1000/1000** tampers caught; 100k records verified in 1.33 s |
| V2: coordination detector | ⚠️ | Narrative clusters, per-account attribution, organic-only views | held-out P **0.71** / R **1.00** / F1 **0.83**; FPs = fan-club swarm (25); baselines F1 0.01 / 0.21 |
| V3: lineage | ✅ | Earliest observed per platform, chains, pHash variants | origin found (Telegram), +12.1 min to X, 4/4 variants; pHash recall 98.2% @ 0.9% FPR |
| B4: LLM summaries | ⚠️ | Gemini, with prompt-injection defences and break tests | disabled until `GEMINI_API_KEY` is set |

## 4. Remaining work

### Needs a human (ask-when-needed)
| # | Item | Notes |
|---|---|---|
| H1 | ~~X cookies~~ | done: live pull verified |
| H2 | Telegram one-time phone login | api_id/hash stored; run `scripts/telegram_login.py` interactively to create TG_SESSION_STRING |
| H3 | Reddit script-app id/secret | optional (appreciable) |
| H4 | ~~YouTube Data API key~~ | done: live pull verified |
| H5 | ~~`GEMINI_API_KEY`~~ | done: summaries live |
| H6 | Decide: rewrite repo history to purge the leaked ledger key | see §6 |
| H7 | Approve deletion of the Next.js scaffold leftovers | `frontend/src/app/`, `Sidebar.tsx`, `EngineStatus.tsx`, `SectionPlaceholder.tsx`, `ProvenanceBadge.tsx`, `lib/api.ts`, `lib/nav.ts`, `frontend/AGENTS.md`, `frontend/CLAUDE.md`, `next.config.ts`, `postcss.config.mjs`, top-level `scenario/` (duplicate) |
| H8 | Emotion gold set + MuRIL fine-tune (PRD §11) | needs a GPU and 400 human-audited items; this is the fix for B's weaknesses |
| H9 | Legal review of the §63 draft template | |

### Engineering (next)
| # | Item | Priority |
|---|---|---|
| E1 | **UI/UX overhaul** (graph visualisation, time slider, "why fired" panels, design system) | High; waiting for team go-ahead |
| E2 | Emotion: fine-tuned model; CUSUM sentiment shift in Signal Cards | High (after H8) |
| E3 | Coordination: reduce fan-swarm false positives (evaluate on a fresh held-out seed) | Medium |
| E4 | JWT login, rate limiting, CSP headers | Before any non-demo deployment |
| E5 | OCR + CLIP image search (P1), ONNX int8 export (P1) | Medium |
| E6 | Holt damped-trend forecast (PRD 8.D), zero-shot interest classification | Low |

## 5. How to run
```bash
make setup && cp .env.example backend/.env && make models && make scenario && make demo   # http://localhost:8000
make test | make eval | make verify | make check-collectors
```
Windows: `scripts\dev.ps1 <target>`. Docker: `docker compose up --build`.

## 6. Security notice
`backend/keys/ledger_ed25519` (a private Ed25519 ledger key) was committed in the first commit
of `Shantanu58-tech/PS_2`. It is no longer tracked, and the system now signs with a new key in
`data/keys/`, which is gitignored. The old key remains in git history. Treat it as compromised:
it must not sign anything. Purging it needs a history rewrite and force-push (team decision H6).
