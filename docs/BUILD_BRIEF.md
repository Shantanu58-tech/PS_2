# BUILD BRIEF: DEEPASTAMBHA (working name)
## SIH26152 Social Media Analytics (NTRO) | Team MOGGERS, VIT Pune | Team Leader: Om Soma

> Read this whole file before writing any code. It is the master instruction set.
> Companion file: `docs/research/RESEARCH_REPORT.md` (the evidence map, coverage matrix, gaps and competitor recon). Every design choice here traces back to a gap in that report. If the two ever conflict, this brief wins for *how to build*, the report wins for *facts and citations*.

---

## 0. Mission

Build a **compliance-first narrative forensics engine for India's code-mixed information space**.

One sentence the judges must remember:
**"We detect when a narrative is being pushed, by which coordinated clusters, across Telegram and X, in Hinglish, with measured accuracy, without building a surveillance database."**

We do not win by claiming more features than the nine public SIH26152 repos. They all claim A to E on six platforms. We win by **proving** each component with numbers, ground truth and evidence, and by doing four things none of them do:

1. **Measured Hinglish affect** with calibrated confidence and abstention, shown on a public evaluation card.
2. **Coordination detection with a statistical null model**, not a "bot score", tested against injected synthetic campaigns with known ground truth.
3. **Cross-platform cascade lineage** (Telegram to X to YouTube/Reddit) with first-seen timestamps per platform and community.
4. **Privacy that is enforced by architecture**: aggregate-only demographics, k-suppression, differential privacy noise, no per-user endpoint exists, no under-18 analytics, Telegram data never used for training, and a tamper-evident ledger of every analyst query.

Then we also match every table-stakes feature competitors show, so there is nothing we are "missing".

---

## 1. Environment and constraints (read carefully)

| Item | Value |
|---|---|
| OS | Windows (use PowerShell commands, Windows paths) |
| GPU | RTX 3050, 6 GB VRAM. Train with fp16, seq len 128, batch 16 with gradient accumulation. No model larger than ~300M params for fine-tuning. |
| Disk | D: has ~70 GB free. Put datasets and model checkpoints under `D:\PRAHARI_DATA` (not in the repo). |
| Local project path | `D:\PRAHARI` (create it). Do not modify anything inside `D:\SIH`. |
| Previous project for reference | `D:\SIH` contains our previous problem statement (TRIVENI, SIH26027) and how it was hosted. **Read only.** |
| Cloud GPU (optional) | Google Colab. Om may give access. Use it for heavier training runs (see 1.1). |
| Budget | Near zero. X API is pay-per-use (~$0.005 per post read). Hard budget guard required (see 5.1). |
| Timeline | Idea PPT due before 30 Sept 2026. Prototype continues after that for later rounds. Build in phases so something demoable exists at the end of every phase. |

### 1.1 Training on Google Colab (when available)
Om may give you access to Google Colab. If you have access, or Om can run notebooks for you, use Colab for any training run that is slow or does not fit in 6 GB VRAM (for example a larger encoder, longer sequences, multiple seeds, or hyperparameter sweeps). Otherwise train locally on the 3050.

Rules for Colab:
- Keep all training code in `ml/training/` as normal Python modules. Generate thin notebooks in `ml/colab/` that only clone or upload the code, install requirements, run the training script and download artifacts. The notebook must not contain logic that is missing from the repo.
- Detect the GPU at runtime (`torch.cuda.get_device_name`) and pick batch size and precision to match (fp16 on T4, bf16 where supported).
- Save checkpoints to Google Drive every epoch so a disconnected session can resume. Log the Colab GPU type, runtime, seed and dataset hashes into the eval card so results are reproducible.
- Upload only datasets with `train_allowed = True`. **Never upload Telegram-sourced data to Colab**, and never upload `.env`, API keys or Telethon session files.
- After training, export to ONNX int8 on Colab or locally, copy the final model into `D:\PRAHARI_DATA\models`, and record its hash in `docs/EVAL_CARD.md`.
- If you cannot access Colab directly, give Om the ready notebook plus a short list of steps (under 10 lines) to run it, and tell him which files to send back.

### Code style rules from Om (non-negotiable)
- **No code comments** anywhere in code. Use clear names, docstring-free small functions, and put explanations in `docs/` instead.
- Give full files when editing, never truncated snippets with "..." placeholders.
- Om Soma's name must appear in final project documents (README, docs site footer, PPT support docs, LICENSE owner line).
- Explanations to Om in chat: short and condensed.

---

## 2. How to work: agents, phases, memory files

### 2.1 Working method
Use **phases with gates** and **specialised subagents**. Each phase ends with a runnable demo and passing tests. Do not start phase N+1 until phase N's gate checklist passes, unless Om says otherwise.

### 2.2 Subagents to create in `.claude/agents/`
Create one markdown file per agent with a focused system prompt:

| Agent | Owns | Must never |
|---|---|---|
| `architect` | Overall design, ADRs, interface contracts, phase planning | Write feature code without an ADR for major choices |
| `ingestion-engineer` | Connectors, canonical schema, replay engine, budget guard, provenance | Store raw user handles or profile images |
| `nlp-ml-engineer` | Language ID, normalisation, affect model, calibration, eval card | Train on Telegram-sourced data |
| `graph-analyst` | Interaction graphs, coordination detection, null models, KOLs, cascades | Label anyone "bot" or "inauthentic"; use "coordinated cluster" |
| `privacy-officer` | Pseudonymisation, k-suppression, DP, audit ledger, DPDP mapping | Allow any endpoint returning individual-level inference |
| `frontend-engineer` | Analyst UI, evidence drawer, eval card page, audit page | Show raw handles, show demographics below k |
| `red-team-qa` | Break tests, synthetic campaign injection, adversarial inputs, security scan | Mark a phase done if any break test fails |
| `research-integrator` | Triage of new research from Om's teammate into ADRs and backlog | Change the current phase scope mid-phase |

Run agents in parallel where work is independent (for example ingestion and NLP in Phase 2), and always have `red-team-qa` review before a phase gate.

### 2.3 Memory and tracking files (create in Phase 0)
- `CLAUDE.md`: condensed version of this brief (rules, stack, commands, current phase). Keep under 200 lines.
- `docs/PLAN.md`: phase checklist with status.
- `docs/PROGRESS.md`: dated log of what was done, what broke, what is next.
- `docs/adr/NNNN-title.md`: architecture decision records.
- `docs/BACKLOG.md`: ideas not in current scope.
- `docs/SCORECARD_MAP.md`: how each feature maps to the SIH judging criteria (Problem Understanding, Innovation, Feasibility, Impact, Clarity).

### 2.4 Late research from Om's teammate
Om's teammate is doing parallel research that may arrive mid-build. Protocol:
1. New material goes into `research/inbox/` (any format).
2. `research-integrator` reads it, writes `research/triage/YYYY-MM-DD.md` classifying each item as: **Adopt now** (small, fits current phase), **Adopt next phase**, **Backlog**, or **Reject** (with reason and citation).
3. Anything that changes architecture needs an ADR and Om's approval.
4. Merge happens at phase boundaries, never in the middle of a phase, so the build is never destabilised.
5. If new research contradicts `RESEARCH_REPORT.md`, record both sources and flag it to Om in one short message.

---

## 3. Architecture

```
Sources                Ingestion              Core store                 Analytics                      Serving
-------                ---------              ----------                 ---------                      -------
X API (pay-per-use) -> connector_x   -\
Telegram (Telethon) -> connector_tg  --\
YouTube Data API    -> connector_yt  ---> canonical event -> privacy gate -> Postgres (events, aggregates)
Reddit API          -> connector_rd  --/   (UTC, provenance,  (HMAC ids,     Parquet (immutable raw, D:)
Replay datasets     -> replay_engine -/     platform, hash)    drop PII)      Redis Streams (live bus)
                                                                                   |
                          +------------------------+------------------+-----------+-----------+
                          |                        |                  |                       |
                     NLP service              Trend service      Graph service          Demographics service
                     lang id, normalise       embeddings,        interaction + co-      aggregate only,
                     affect multi-head,       narrative clusters, ordination layers,    k-suppress, DP noise,
                     calibration, abstain     burst, forecast    null model, KOLs,      poststratify, CI
                                                                 cascade lineage
                          +------------------------+------------------+-----------------------+
                                                   |
                                        Evidence and alert engine (every alert links posts, method, confidence)
                                                   |
                                        FastAPI gateway (auth, RBAC, query audit ledger with Merkle anchoring)
                                                   |
                                        Next.js analyst console
```

### 3.1 Stack
| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11 backend, TypeScript frontend | Team familiarity, ML ecosystem |
| API | FastAPI + Pydantic v2 | Typed contracts, OpenAPI for free |
| Bus | Redis Streams | Real-time without Kafka's weight; Upstash for hosting |
| DB | PostgreSQL 16 (+ TimescaleDB if the host supports it, else plain partitions) | Time-series queries, one DB to host |
| Raw archive | Parquet on local disk (`D:\PRAHARI_DATA\raw`) | Immutable, replayable |
| Graph | NetworkX + python-igraph for compute, edges persisted in Postgres | No extra hosted service needed; Neo4j optional later |
| NLP | Hugging Face Transformers, MuRIL or XLM-R base, sentence-transformers (LaBSE or multilingual MiniLM) | Best Indic code-mixed support that fits 6 GB |
| Topics | BERTopic with custom embedding model | Dynamic topics, documented method |
| Serving models | ONNX Runtime with int8 quantisation | Runs on CPU hosts with little RAM |
| Frontend | Next.js 14 (App Router), Tailwind, Recharts, Sigma.js or Cytoscape for graphs | Vercel-native, fast graph rendering |
| Tests | pytest, hypothesis, Playwright | Break tests and UI e2e |
| Packaging | uv or pip-tools, Docker Compose for local stack | Reproducible |

If `D:\SIH` shows a stack that worked well for hosting, prefer consistency with it where it does not weaken the design, and record that in an ADR.

### 3.2 Repository layout
```
DEEPASTAMBHA/
  CLAUDE.md
  README.md
  LICENSE
  .env.example
  docker-compose.yml
  .claude/agents/
  docs/
    research/RESEARCH_REPORT.md
    adr/
    PLAN.md  PROGRESS.md  BACKLOG.md  SCORECARD_MAP.md
    COMPLIANCE.md  EVAL_CARD.md  HOSTING_NOTES.md  DEMO_SCRIPT.md
  research/inbox/  research/triage/
  backend/
    app/api/  app/auth/  app/audit/
    ingest/connectors/  ingest/replay/  ingest/schema.py  ingest/budget.py
    privacy/pseudonym.py  privacy/ksuppress.py  privacy/dp.py  privacy/policy.py
    nlp/langid.py  nlp/normalise.py  nlp/affect/  nlp/calibrate.py  nlp/explain.py
    trends/embed.py  trends/narratives.py  trends/burst.py  trends/forecast.py
    graph/build.py  graph/coordination.py  graph/nullmodel.py  graph/kol.py  graph/lineage.py
    demographics/estimate.py  demographics/poststratify.py
    alerts/engine.py  alerts/evidence.py
    synth/campaign_injector.py
    tests/
  ml/
    datasets/  training/  eval/  export_onnx/
  frontend/
  scripts/
  infra/
```

---

## 4. Canonical data model

Every source is converted to one schema before anything else touches it.

```python
class CanonicalEvent(BaseModel):
    event_id: str
    platform: Literal["x", "telegram", "youtube", "reddit", "instagram", "facebook"]
    provenance: Literal["LIVE", "REPLAY", "IMPORT", "SYNTHETIC"]
    source_ref: str
    author_pid: str
    community_pid: str | None
    created_at_utc: datetime
    ingested_at_utc: datetime
    text: str
    lang_hint: str | None
    reply_to: str | None
    forward_of: str | None
    quote_of: str | None
    urls: list[str]
    hashtags: list[str]
    mentions_pid: list[str]
    metrics: dict[str, int]
    content_hash: str
    train_allowed: bool
    retention_until: datetime
```

Rules:
- `author_pid`, `community_pid`, `mentions_pid` are **HMAC-SHA256** of the platform id with a per-deployment secret key from `.env`. Raw handles and ids are never persisted. Public channel names may be kept in a separate `sources` table because they are organisational, not personal, but only for channels on the curated list.
- `train_allowed` is `False` for every Telegram event, always. The training pipeline must assert this and fail loudly otherwise.
- `provenance = SYNTHETIC` marks injected test campaigns so the UI can show them with a badge.
- Profile images are never downloaded. Bios are processed in memory for aggregate interest topics and then discarded; only the derived topic id is kept.

---

## 5. Component specs

### 5.1 A. Ingestion
- **X**: official API v2 pay-per-use. `ingest/budget.py` keeps a spend ledger and refuses calls once the configured monthly cap (default $20) is reached. Query plans are keyword and hashtag based, recent search only.
- **Telegram**: Telethon, read-only, on a curated allowlist of public channels in `config/telegram_channels.yaml`. No auto-joining of arbitrary channels. Respect FLOOD_WAIT with exponential backoff. Data used only for rule-based analytics, graphs, and inference with models trained elsewhere.
- **YouTube**: Data API v3, commentThreads for a curated video list; quota tracker (10,000 units per day).
- **Reddit**: official OAuth API, non-commercial, under 100 queries per minute.
- **Instagram / Facebook**: implement the connector interface and a Graph API Hashtag Search stub respecting the 30 hashtags per 7 days limit. Mark as "requires Meta App Review" in the UI. Do not scrape.
- **Replay engine**: streams historical datasets (Pushshift Telegram, TGDataset, SentiMix, our own recorded captures) through the same bus at configurable speed. The hosted demo runs in replay mode by default so it costs nothing and never breaks.
- **Historical DB**: every event is time-stamped and immutable in Parquet; Postgres holds the queryable projection.

### 5.2 B. Affect over time (Hinglish-first)
Pipeline: language ID per token (script + code-mixed LID), transliteration normalisation (romanised Hindi variants), then a **multi-head classifier** on a shared MuRIL or XLM-R encoder:
- Head 1 sentiment: positive, negative, neutral
- Head 2 stance: supportive, against, neutral (towards a target narrative)
- Head 3 emotion: anxiety, excitement, anger, hope, neutral
- Head 4 sarcasm: sarcastic, not sarcastic

Requirements:
- **Calibration** by temperature scaling on a held-out set. Report ECE before and after.
- **Abstention**: if max calibrated probability is below a threshold chosen on validation, output `UNCERTAIN`. Show abstention rate and accuracy on non-abstained items.
- **Sarcasm flips**: when sarcasm is detected with high confidence, sentiment is re-scored using the sarcasm-aware head, and both raw and adjusted are stored.
- **Explanation**: top contributing tokens per prediction (integrated gradients or attention rollout), shown in the evidence drawer.
- **Time series**: affect aggregated per narrative, platform, community segment and hour/day.
- **Baselines** in the eval card: VADER, a TF-IDF logistic regression, and our model. Competitors mostly use VADER; the card must show why that fails on Hinglish.
- **Gold set**: team hand-labels at least 500 Hinglish posts from X/YouTube/Reddit (not Telegram) with two annotators and reports Cohen's kappa. This is our own contribution and a strong slide.
- Training data: SentiMix Hinglish, Hinglish sarcasm corpora, Joshi 2016, HOT offensive, plus the gold set. Check each licence and record it in `ml/datasets/LICENSES.md`.

Output `docs/EVAL_CARD.md` and an `/eval` page in the UI with per-class precision, recall, F1, macro-F1, confusion matrices, ECE, abstention rate, and known failure cases.

### 5.3 C. Demographics (aggregate only)
- **No function or endpoint may return a demographic estimate for a single account.** Enforced by the policy layer and by a test that scans all routes.
- Signals: language mix from text, state-level geography from self-declared location strings mapped with a gazetteer of Indian states and major cities, professional interest topics from bios, age band only as a **poststratified aggregate** with confidence intervals (adapt the poststratification method from the research report; use Indian census-style marginals where available, otherwise report unadjusted with a warning).
- **k-suppression**: any cell with fewer than k accounts (default 20) is shown as "suppressed".
- **Differential privacy**: Laplace noise on published counts with a configurable epsilon; epsilon shown in the UI.
- **Minors**: accounts predicted under 18 are excluded before any aggregation; no under-18 bucket is ever displayed.
- Every demographic panel shows sample size, method and uncertainty.

### 5.4 D. Trends and prediction
- Multilingual sentence embeddings, then **narratives** = clusters of semantically similar claims (BERTopic with the custom embedder, online updates per time window).
- Label each narrative with top keywords plus a short representative post (pseudonymised).
- **Burst detection**: rolling z-score and Kleinberg bursts per narrative.
- **Ranking**: velocity, acceleration, cross-platform spread count, coordination share, affect intensity.
- **Prediction**: short-horizon (6 to 24 h) growth forecast using features from early cascade shape (first-hour velocity, number of distinct communities, coordination share). Start with gradient boosting on cascade features; compare against a naive persistence baseline and report the lift. Optional later: Hawkes-process intensity.
- Every trend alert states why it fired.

### 5.5 E. Network, coordination, KOLs, spread
Two graph layers:
1. **Interaction layer**: reply, forward, retweet, quote, mention edges with timestamps.
2. **Coordination layer**: edges between accounts that repeatedly
   - co-retweet the same post within 60 s (X),
   - co-forward the same message within Δt (Telegram, Δt configurable, default 60 s),
   - post near-duplicate text (MinHash LSH, Jaccard above 0.8) within a window,
   - share the same URL in a burst.

**Null model (key differentiator)**: for every detected cluster, recompute coordination scores on time-shuffled data (permute timestamps within each account, 200 runs). Only report clusters whose edge weights exceed the 99th percentile of the null distribution. Show the p-value. This directly addresses the literature warning that coordination signals often capture organic partisanship.

**KOLs**: rank by temporal influence, not static PageRank alone:
- time-to-amplification (how fast others pick up their posts),
- unique downstream communities reached,
- share of cascade volume attributable to them,
- plus PageRank and betweenness for parity with competitors.

**Cascade lineage (cross-platform)**: link items across platforms by URL, content hash, MinHash similarity and time ordering. Build a directed temporal graph of narrative jumps: first-seen on Telegram channel cluster, then X, then YouTube comments. Use "earliest observed" wording, never "origin".

**Segment spread**: communities via Leiden (igraph), then show how affect and narratives move between communities over time (Sankey or streamgraph).

Language rule: the system says **"coordinated cluster"**, never "bot" or "fake". An optional bot-likelihood feature may exist but must be labelled as experimental, with its limits stated.

### 5.6 Evidence and alerts
Every alert object contains: type, narrative id, time window, confidence, method name and version, parameters used, list of evidence event ids (pseudonymised display), a reproducibility hash of the query, and a plain-language explanation. An analyst can click through to the exact posts that produced it.

### 5.7 Governance and audit
- **Query audit ledger**: every analyst query (who, when, what filters, which result ids) is appended to a hash chain; hourly, a Merkle root of the last hour is computed and stored. `/audit` page shows the chain and lets anyone verify integrity. This is our Blockchain and Cybersecurity theme fit, done properly.
- **RBAC**: roles `analyst`, `supervisor`, `auditor`. Auditor can see the ledger but not content.
- **Refusal by design**: a query that tries to profile one account (for example filter by a single author_pid and request demographics) returns a structured refusal and is itself logged. This is a demo moment.
- `docs/COMPLIANCE.md` maps each control to DPDP Act 2023 sections, DPDP Rules 2025, platform terms (Telegram ToS 1.5, Meta, X, Reddit, YouTube), and the 2018 Social Media Communication Hub lesson.

### 5.8 Synthetic campaign injector (our ground truth)
`backend/synth/campaign_injector.py` injects configurable fake campaigns into replay streams: N accounts, posting pattern (burst, staggered, relay chain), Telegram-first then X, text templates in Hinglish with paraphrase noise, mixed with organic background. Tagged `SYNTHETIC`.
Use it to measure coordination precision, recall and detection latency, and to run the live demo ("watch the system catch this campaign in under X minutes"). Report results in the eval card.

---

## 6. Analyst console (frontend)

Pages:
1. **Overview**: live or replay clock, top narratives with velocity, coordination share and affect sparkline.
2. **Narrative detail**: timeline, affect over time by platform, representative posts, cascade lineage graph across platforms, forecast band.
3. **Coordination explorer**: clusters with p-values, evidence posts, timing heatmap (who posted within seconds of whom).
4. **Network**: interactive graph (Sigma.js), KOL table with temporal metrics, community Sankey.
5. **Audience (aggregate)**: language, state map of India, interest topics, age bands with CIs, suppressed cells visible as suppressed, epsilon shown.
6. **Eval card**: model metrics, baselines, calibration plot, failure examples.
7. **Audit**: query ledger, Merkle roots, verify button, refused queries.
8. **Sources and compliance**: which connectors are live, budget used, provenance mix, ToS notes.

Design: dark, serious, intelligence-console look. Every chart has a "method" tooltip. No raw handles anywhere. Provenance badge (LIVE, REPLAY, IMPORT, SYNTHETIC) on every item.

---

## 7. Phases and gates

### Phase 0: Setup and reconnaissance
- Create `D:\PRAHARI`, git init locally, `.gitignore` (env files, data, checkpoints, sessions such as `*.session`), `.env.example`.
- Copy the research report to `docs/research/RESEARCH_REPORT.md`.
- **Read `D:\SIH` read-only**: find its deployment configs (Dockerfiles, `vercel.json`, `render.yaml`, Procfiles, env examples, CI workflows, README deploy notes). Write `docs/HOSTING_NOTES.md` summarising exactly how TRIVENI was hosted, what worked, what hurt. Do not copy secrets.
- Create agents, `CLAUDE.md`, `PLAN.md`, ADR 0001 (stack), ADR 0002 (hosting approach based on D:\SIH findings).
- Docker Compose with Postgres and Redis running locally.
- **Gate**: `docker compose up` works, health endpoint returns 200, docs exist, no secrets in git history.

### Phase 1: Data spine
- Canonical schema, privacy gate (HMAC pseudonyms), Parquet archive, Postgres projection.
- Replay engine with SentiMix and a Pushshift Telegram sample.
- Connectors: Telegram (Telethon read-only allowlist), YouTube, Reddit; X with budget guard (can stay disabled until Om adds keys).
- Synthetic campaign injector v1.
- **Gate**: replay of 100k events end to end, zero raw ids in DB (automated scan), Telegram events all `train_allowed = False`, budget guard unit tests pass.

### Phase 2: Intelligence core (run agents in parallel)
- NLP: langid, normalisation, affect multi-head training on the local GPU or Google Colab (section 1.1), calibration, abstention, ONNX int8 export.
- Trends: embeddings, narratives, burst, ranking.
- Graph: both layers, coordination detection, null model, KOL temporal metrics.
- **Gate**: eval card generated with real numbers and baselines; synthetic campaign detected with reported precision and recall; null model p-values computed; all break tests for this phase pass.

### Phase 3: Lineage, demographics, alerts, governance
- Cross-platform cascade lineage.
- Aggregate demographics with k-suppression, DP, poststratification, minors exclusion.
- Alert engine with evidence.
- Audit ledger with Merkle anchoring, RBAC, refusal by design.
- Forecasting with baseline comparison.
- **Gate**: the route-scan test proves no per-user demographic output; refusal demo works; ledger verification passes and fails correctly when tampered.

### Phase 4: Console and demo
- All frontend pages from section 6.
- `docs/DEMO_SCRIPT.md`: a 5 minute jury walkthrough (see section 10).
- Playwright e2e on the demo path.
- **Gate**: full demo runs in replay mode from a clean machine with one command.

### Phase 5: Hardening, GitHub, hosting
- Security: gitleaks scan, dependency audit, rate limiting, auth on all routes, CORS locked.
- Push to GitHub **only when Om says so** (see section 8).
- Deploy following `HOSTING_NOTES.md` (see section 9).
- **Gate**: hosted URL works in replay mode, secrets only in host env settings, README has setup, architecture, eval card link, compliance link, team credits with Om Soma as team leader.

### Phase 6: Break-test loop (continuous)
Om's method: find gaps, fill gaps, repeat until nothing breaks. `red-team-qa` maintains `docs/BREAK_TESTS.md` and adds a test for every failure found. Seed list:
- Sarcastic Hinglish praise that is actually criticism is classified correctly, or the model abstains.
- Pure Devanagari, pure romanised Hindi, and mixed script all go through without crashing.
- Organic viral event (many real users, no coordination) is **not** flagged as a coordinated cluster.
- Injected campaign with staggered timing (not all in 60 s) is still caught; report detection latency.
- Attempt to get demographics for one account is refused and logged.
- Cell with 19 accounts is suppressed.
- Telegram-sourced event reaching the training loader crashes the loader with a clear error.
- Tampering with one ledger row breaks verification.
- X budget exhausted: system degrades to replay gracefully, UI shows it.
- Emoji-only, URL-only, empty and 4,000-character posts are all handled.
- Prompt-injection style text inside posts does not affect any LLM-assisted summary (if an LLM summariser is added later).

---

## 8. Git and GitHub workflow
- Local repo from day one. Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Branches: `main` (stable, gate-passed), `dev`, and short `feat/*` branches per agent task.
- Tag each passed gate: `phase-0`, `phase-1`, and so on.
- **Do not create a remote or push until Om explicitly says "push now"**. When he does: run gitleaks on full history, confirm `.env`, `*.session` (Telethon sessions), datasets and checkpoints are excluded, then create the repo (private first), push, and ask Om before making it public.
- Lesson from competitor recon: one public SIH26152 repo leaked what look like real Telegram API credentials in its README. Never put keys in docs or code.

---

## 9. Hosting
1. **First choice: mirror our previous approach** documented in `docs/HOSTING_NOTES.md` from `D:\SIH`, adapted to this stack.
2. **Fallback / default plan**:
   - Frontend: Vercel (Next.js).
   - API: Render web service (Docker).
   - Postgres: Render Postgres or Neon free tier.
   - Redis: Upstash.
   - Model inference: ONNX int8 inside the API container if memory allows; otherwise a Hugging Face Space serving the model, called by the API.
   - Hosted mode runs **REPLAY + SYNTHETIC** by default. Live connectors are enabled only locally or with explicit env flags, so the public demo never burns API budget or touches ToS limits.
3. Cold starts: add a warm-up ping and a "starting up" state in the UI.
4. Write `docs/DEPLOY.md` with exact steps and every env var.

---

## 10. Demo script outline (for DEMO_SCRIPT.md)
1. **Hook (30 s)**: a real, documented pattern from the research report (a foreign network posing as Indian journalists and activists). "Could India catch this in Hinglish, across Telegram and X, without surveilling citizens?"
2. **Live replay (60 s)**: narratives rising on the overview, provenance badges visible.
3. **Catch (90 s)**: a synthetic Telegram-first campaign jumps to X. The coordination explorer flags the cluster with p-value, timing heatmap and evidence posts. The lineage graph shows the jump with timestamps.
4. **Nuance (45 s)**: a sarcastic Hinglish post classified correctly; an ambiguous one where the model says UNCERTAIN. Open the eval card and show numbers against VADER.
5. **Privacy (45 s)**: audience page with suppressed cells and epsilon; try to profile one account and get refused; show that refusal in the audit ledger and verify the chain.
6. **Close (30 s)**: "Measured, explainable, lawful. Built for India's languages."

---

## 11. Parity checklist (so competitors have nothing we lack)
- [ ] Six platform connectors present in the interface (X, Telegram, YouTube, Reddit live; Instagram and Facebook as compliant stubs)
- [ ] Provenance labels on every event
- [ ] Hash-chained audit (ours covers queries and data, theirs only data)
- [ ] Six-class affect taxonomy from the problem statement (supportive, against, anxiety, excitement, sarcasm, neutral) mapped to our heads
- [ ] PageRank and betweenness available alongside temporal influence
- [ ] Real-time mode via Redis Streams
- [ ] Interactive network graph
- [ ] Requirement to code to UI traceability table in `docs/SCORECARD_MAP.md` (one competitor has this; ours must be more complete)

## 12. Differentiator checklist (what makes us win)
- [ ] Eval card with Hinglish metrics, baselines, calibration and abstention
- [ ] Team-built annotated gold set with inter-annotator agreement
- [ ] Coordination detection with a time-shuffled null model and p-values
- [ ] Synthetic ground-truth campaigns with precision, recall and detection latency
- [ ] Cross-platform cascade lineage (Telegram to X to YouTube/Reddit)
- [ ] Aggregate-only demographics with k-suppression, DP, CI and minors exclusion, proven by a route-scan test
- [ ] Telegram never used for training, enforced in code
- [ ] Query audit ledger with Merkle roots and refusal by design
- [ ] Every alert tied to evidence posts and a method explanation
- [ ] Hosted demo that is free to run and cannot break (replay mode)

---

## 13. Definition of done
- Every checklist item in sections 11 and 12 is ticked with a link to the file or test proving it.
- `docs/EVAL_CARD.md`, `docs/COMPLIANCE.md`, `docs/DEMO_SCRIPT.md`, `docs/DEPLOY.md`, `docs/SCORECARD_MAP.md` are complete.
- All break tests pass.
- README credits: Team MOGGERS, VIT Pune, Team Leader Om Soma.

## 14. First actions for Claude Code
1. Read this brief and `docs/research/RESEARCH_REPORT.md` fully.
2. Read `D:\SIH` (read only) and write `docs/HOSTING_NOTES.md`.
3. Propose the Phase 0 and Phase 1 plan to Om in a short message (bullets, under 15 lines) and list any questions. Wait for approval, then execute.
4. Ask Om for: X API keys (optional), Telegram api_id and api_hash (kept in `.env` only), YouTube API key, Reddit app credentials, and the initial Telegram channel allowlist and keyword list.

---
*Prepared for Team MOGGERS, VIT Pune. Team Leader: Om Soma. Problem Statement SIH26152, sponsored by NTRO.*
