# PRAHARI phase plan

Legend: `[x]` done, `[~]` in progress, `[ ]` not started, `[!]` blocked (reason given)

## Phase 0: Setup and reconnaissance
- [x] Repo at `D:\SIH_P2` with git and `.gitignore`/`.gitattributes`/`.env.example`
- [x] Brief and research report moved to `docs/BUILD_BRIEF.md` and `docs/research/RESEARCH_REPORT.md`
- [x] `D:\PRAHARI_DATA` tree created
- [x] `docs/HOSTING_NOTES.md` from the read-only review of `D:\SIH`
- [x] ADR 0001 (stack), 0002 (hosting), 0003 (local infra)
- [x] `CLAUDE.md`, PLAN, PROGRESS, BACKLOG, SCORECARD_MAP
- [x] Eight agents in `.claude/agents/`
- [x] Backend skeleton with `/healthz`, config and tests
- [x] Dockerfile and `docker-compose.yml` (Postgres 16, Redis 7, API)
- [x] Next.js console skeleton (dark theme, placeholder Overview)
- [x] README and LICENSE (Om Soma credited)
- [x] `docs/PPT_SUPPORT.md` for the idea PPT
- [!] **Gate:** `docker compose up` works and `/healthz` returns 200. Blocked until Docker Desktop is installed.
- [x] **Gate:** gitleaks is clean on the full history
- [ ] Tag `phase-0`

## Phase 1: Data spine
- [ ] `CanonicalEvent` schema with validators
- [ ] Privacy gate: HMAC pseudonyms with key version, PII drop policy
- [ ] Parquet archive and Postgres projection (Alembic, monthly partitions)
- [ ] Redis Streams bus and canonicaliser worker
- [ ] Replay engine: SentiMix and a Pushshift Telegram sample
- [ ] Connectors: Telegram, YouTube, Reddit, X (budget guard), Instagram/Facebook stubs
- [ ] Training loader guard (crashes on Telegram)
- [ ] Synthetic campaign injector v1 with a ground-truth manifest
- [ ] **Gate:** 100k events replayed end to end
- [ ] **Gate:** zero raw ids in the database (automated scan)
- [ ] **Gate:** every Telegram event has `train_allowed = False`
- [ ] **Gate:** budget guard tests pass
- [ ] red-team-qa review, then tag `phase-1`

## Phase 2: Intelligence core
The NLP multi-head model with calibration, abstention and ONNX; trends; the graph layers with the null model; KOLs; the eval card. Planned in detail at the Phase 1 boundary.

## Phase 3: Lineage, demographics, alerts, governance
Planned at the Phase 2 boundary.

## Phase 4: Console and demo
Planned at the Phase 3 boundary.

## Phase 5: Hardening, GitHub, hosting
Planned at the Phase 4 boundary.

## Phase 6: Break-test loop
Runs continuously from Phase 2 onwards.
