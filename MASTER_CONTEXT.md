# DEEPASTAMBHA: Master Context (final)

**दीपस्तम्भ, "pillar of light"**: the temple lamp tower that keeps a light burning through the night.
**Team MOGGERS · VIT Pune · Smart India Hackathon 2026**
**Problem Statement 26152 "Social Media Analytics" · NTRO · Category: Software · Theme: Blockchain & Cybersecurity**

- **Live demo:** https://deepastambha.onrender.com (the URL keeps the old project name; see §13)
- **Code:** https://github.com/Shantanu58-tech/PS_2
- **Walkthrough and video script:** shared doc "DEEPASTAMBHA — Demo Walkthrough & Video Script"
- **Screen-recorded demo:** `demo_video/deepastambha_demo.mp4` (captioned, about 3 min; not in git)

> This is the single reference for the team: what we built, how it works, what we
> measured, how to demo it and how to pitch it.
>
> - **Evaluation numbers** (§6) come only from `eval/reports/summary.json`
>   (generated 2026-09-30). Never put a number on a slide that isn't in that file.
> - **Numbers labelled "on the live demo"** are what the demo database shows on screen.
>
> More detail: `docs/DECISIONS.md` (every design decision, D-01…D-39), `eval/reports/*.md`
> (every measurement), `docs/DIAGRAMS.md` (Mermaid diagrams and references).

---

## 1. One-liner, name and thesis

**One-liner.** DEEPASTAMBHA is a national situation room for social media. At a glance it shows:
- what is happening across India;
- which narratives are being pushed, and by which coordinated groups and accounts;
- the impact, by sector and by state.

From that overview the analyst investigates who is behind a narrative and where it started, then
secures the evidence in a tamper-evident, independently verifiable ledger.

**Name and logo.** A *deepastambha* keeps a light burning all night: a watch that never sleeps. The
emblem is a lamp tower inside a round seal:
- **six lamps** on three tiers stand for the **six platforms** we watch;
- the **saffron flame** with listening arcs is the watch;
- a **green base line** completes the tricolour.

We chose a name no one else uses: common "guard/sentinel" names are taken by several government apps
and by other SIH 2026 teams. A search found no product named Deepastambha.

**Thesis: coordination-adjusted analytics.** Every team will build the five PS components. We tie
them together with one idea: **every view can be shown as all activity or organic only**, with
coordinated accounts removed. The analyst then sees how much a campaign distorts trends, audience
and influence.

Around this sits an evidence pipeline:
- hash chain;
- signed Merkle checkpoints;
- Bitcoin time-anchoring (OpenTimestamps);
- tamper simulation;
- analyst decisions recorded in the chain;
- a draft BSA §63 certificate.

**Primary user:** an NTRO cyber-intelligence analyst.

**Pain points solved:**
- **Alert fatigue:** a few ranked, explained signals instead of many alarms.
- **Organic vs astroturf:** the coordination detector plus the organic-only switch.
- **Cross-platform tracing:** lineage.
- **Evidence that holds up:** the ledger plus the case pack.

---

## 2. Problem statement mapping (what the jury checks)

| PS | Requirement (abridged) | What we built | Where |
|---|---|---|---|
| **A** | Multi-platform ingestion of live posts, interactions and comments, with a time-stamped history. Essential: X, Telegram. Desirable: Instagram, Facebook. Appreciable: Reddit, YouTube | Collectors for **X (twscrape), Telegram (Telethon, connected and live), Reddit (PRAW), YouTube (Data API v3, incl. replies)**. **Instagram/Facebook** arrive via their official data export (CSV) through the same pipeline; the demo includes a synthetic IG/FB export sample. Backoff, circuit breaker and health checks. UTC timeline, reply threads, dedup. **Platforms page:** activity, mood, topics, accounts and source status for all six. **Live Telegram feed:** real posts fetched right now from public news channels | `backend/app/collectors/`, `app/pipeline/`, `/api/platforms`, `/api/live/telegram` |
| **B** | NLP for nuanced emotions (sarcasm, anxiety, excitement, supportive, against) over the timeline | Five dimensions per post from zero-shot multilingual NLI plus multilingual sentiment; Hinglish handling. Hourly or daily timeline, all activity vs organic, **filterable by platform and by posts vs comment threads** | `app/nlp/`, `/api/timeline/*` |
| **C** | Aggregate, anonymised demographics (age brackets, geography, language, professional interests) | Cohort-only counts: 36-state/UT gazetteer, bio-cue age brackets (minors excluded), interests, language. **k-anonymity (K=10) plus Laplace noise.** No per-account endpoint. **State-level impact map** on the first page, also k-anonymous | `app/analytics/demographics.py`, `app/analytics/situation.py` |
| **D** | Identify, rank and **predict** rising trends and viral keywords over time | Windowed topic clustering with centroid matching; **Kleinberg bursts**; **rise score**; **gradient-boosting and Hawkes forecasts**; ranked signals; **viral hashtags** (peak hour vs usual rate); **hot topics**; **sector-wise impact** (9 sectors) | `app/analytics/{topics,trends,burst,forecast,signals,situation}.py` |
| **E** | Map relationships, find key opinion leaders, show spread between segments over time | Interaction graph across apps, coloured by platform. **"Play the week"** time-lapse. Account panel with followers, activity per platform and connected accounts. KOLs by **cascade influence**, PageRank and betweenness; bridges; communities. **Segment-to-segment spread** with anxiety per segment. Rank changes in organic-only view | `app/analytics/graph*.py`, `/api/graph*` |
| **Theme** | Blockchain & Cybersecurity | **SHA-256 hash chain, Ed25519-signed Merkle checkpoints, inclusion proofs, OpenTimestamps (Bitcoin) anchoring, tamper simulation.** Every analyst action (review decisions, cases, verification) is **written into the chain**. Draft §63 certificate | `app/ledger/`, `app/analytics/cases.py` |

---

## 3. Architecture

```
            ┌──────────── Collectors ─────────────────┐
            │ X · Telegram (live) · Reddit · YouTube  │  backoff+jitter, circuit breaker,
            │ IG/FB official-export CSV · Replay      │  health at /api/collectors
            └──────────────┬──────────────────────────┘
                           │ RawRecord
                           ▼
   SECURE  ledger writer: canonical JSON → SHA-256 → chained entry hash → raw_records (append-only)
           every 100 entries: Merkle root, signed with Ed25519 → ledger_checkpoints → OpenTimestamps
                           ▼
   PREPARE normaliser → SQLite (WAL, FTS5): posts · accounts · edges (account→account) · media (sha256+pHash)
                           ▼
   ANALYSE (each stage an idempotent recompute):
     emotions → edges → topics → coordination → series & Kleinberg bursts → manufactured/organic
     → demographics (all + organic) → behaviour → influence (KOLs) → segments → forecasts → signals → OTS
                           ▼
   ALL ACTIVITY vs ORGANIC → PRIORITY SCORE → high? ALERT : lower in the queue
                           ▼
   ANALYST REVIEW: approve → CASE (evidence pack + draft certificate) · watchlist · dismiss
                   (every decision written into the hash chain)
                           ▼
   FastAPI (REST + SSE live updates) ──► React console:
   1 Situation Room → 2 Detect → 3 Investigate → 4 Evidence
```

**Checks on the team's architecture diagram** (it is correct apart from these):
1. Add "Trends & bursts" to the Analyse box.
2. Signals below the threshold stay lower in the queue; "Watchlist" and "Dismiss" are analyst decisions.
3. The evidence pack and the draft certificate are produced together when a case opens. Counsel
   review is a human step after that.
4. Only raw records (at Secure) and analyst actions are written to the Trust Layer, not priority scores.

**Stack.**
- Backend: Python 3.11, FastAPI, SQLite (Postgres-portable schema), NetworkX (Neo4j via the
  `GraphStore` interface), PyTorch CPU and Hugging Face models.
- Frontend: React, Vite, TypeScript, Recharts, react-force-graph.
- Packaging: one Docker image.
- CI (GitHub Actions): pytest, ruff, mypy, gitleaks, build, Playwright.

**Prototype → production** (slide 4):

| Prototype | Production |
|---|---|
| SQLite | Postgres / TimescaleDB |
| asyncio queue | Kafka |
| NetworkX | Neo4j (already behind an interface) |
| FTS5 | Elasticsearch |
| Embeddings | Milvus |
| Hash-chain ledger | Hyperledger Fabric |
| Research collectors | Licensed feeds |

---

## 4. The console: one connected flow

The numbered bar under the masthead drives everything: **1 Situation Room → 2 Detect →
3 Investigate → 4 Evidence**. The sidebar is grouped by the same four stages and shows live
counts, every page is headed "Step n", and each page ends with a "Next in the flow" card.
Every element on the first page is one click from its detail.

The look follows the team's reference build: espresso masthead with a tricolour strip, sand
canvas, copper accent. It is structured like a government portal but modern. Light is the default
and dark is one click away.

| Step | Page | What it shows |
|---|---|---|
| 1 | **Situation Room** | Auto-written situation report and a "How it travelled" strip. Four KPIs: posts secured, priority alerts, coordinated accounts, manufactured trends. **India state map** (exposure to pushed narratives, anxiety or posts; click a state). **Narratives being pushed**, with the coordinated group and its amplifiers. **Sector-wise impact matrix.** **Signals for analyst review** (Approve → case, Watchlist, Dismiss). **Live from Telegram.** Hot topics. Activity and amplification gap |
| 2 | Platforms | All six sources with their status (Connected / API ready / official export) and per-platform activity, mood, topics, accounts and posts; the Telegram page shows the full live feed |
| 2 | Trends | Topics marked manufactured or organic, burst bands, forecast, top posts, AI summary, viral hashtags; opens pre-filtered from a sector or topic |
| 2 | Emotions | Five emotions over time, all activity vs organic, filtered by platform and by posts or comments |
| 3 | Coordination | Why a group was flagged (posting in sync, predictable timing, clock-like rhythm, copy-paste text, robotic cadence), timing chart, accounts, sample posts |
| 3 | Network | Interaction map across apps, platform filters, time-lapse, account panel, top influencers, bridges, spread between groups, reach over time |
| 3 | Lineage | First seen per platform, hand-offs, image copies (pHash) |
| 3 | Audience | Region, language, interests and age as group counts only |
| 4 | Cases | Evidence pack (brief) and draft §63 certificate |
| 4 | Evidence ledger | Verify integrity, tamper test, signed seals, proof of inclusion, activity log |

**On the live demo** (from the demo database):
- The situation report reads: "Dam Varunapur Evacuate", Critical Infrastructure, 93% of 347 posts
  from a group of 72 accounts acting in sync.
- It started on Telegram and went X (+12 min) → YouTube → Facebook → Reddit → Instagram.
- 223 real users reacted with 59% anxiety, mostly in Maharashtra and Telangana.
- Critical Infrastructure is the only CRITICAL sector. The bigger cricket surge is organic.
- The live Telegram feed shows about 45–50 real posts from The Indian Express, Hindustan Times,
  Mint and Moneycontrol, refreshed every few minutes.

---

## 5. Algorithms (for slide 3 and jury questions)

### 5.1 Ledger (Theme)
- `record_hash = SHA256(canonical_json(payload))` (sorted keys, UTF-8, no whitespace).
- `entry_hash_n = SHA256(prev_entry_hash ‖ record_hash ‖ collected_at ‖ collector_id ‖ seq)`; the genesis hash is 64 zeros.
- Every 100 entries, a Merkle root over the entry hashes is **signed with Ed25519**.
- `verify` recomputes every record hash, chain link, **Merkle root** and signature.
- **Inclusion proof:** a Merkle path plus the signed root. Anyone with the public key can verify one record.
- **OpenTimestamps:** the newest checkpoint root is stamped on public calendars and later upgraded
  to a Bitcoin attestation. Because entries are chained, one anchor covers all earlier records.
- SQLite triggers enforce append-only. The tamper simulation runs only on a temporary copy.
- Analyst actions are written into the chain: signal review decisions, case creation, verify and
  tamper runs.

### 5.2 Emotion (B)
- **Anxiety, excitement, sarcasm:** zero-shot NLI with `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`,
  which is multilingual.
- **Supportive / against:** polarity from `cardiffnlp/twitter-xlm-roberta-base-sentiment`.
- Per-label thresholds are tuned on the validation seed; the headline number is on the held-out seed.
- Hinglish: script detection, a Hinglish lexicon, spelling-variant canonicalisation and emoji tokens.
- The live Telegram feed uses the fast lexicon scorer (`lexicon-v1`) because the free server has no GPU.

### 5.3 Demographics and states (C)
- **Geography:** a whole-word gazetteer match on profile location or bio (36 states/UTs).
- **Interests:** a keyword taxonomy over bios.
- **Age:** bio cues mapped to brackets; **minors are excluded**.
- **Language:** each account's dominant language.
- **Privacy:**
  - buckets or states backed by fewer than K=10 accounts are withheld;
  - released counts get Laplace noise (ε=1);
  - IDs are HMAC-pseudonymised;
  - **no per-account endpoint exists**, and a test enforces that.
- **State impact:** share of a state's posts that are **in a manufactured narrative or reply to
  one**. Replies count because the coordinated accounts give no location, and the public reacts
  through replies.

### 5.4 Trends, sectors and signals (D)
- **Topics:** 24 h windows; multilingual sentence embeddings (paraphrase-multilingual-MiniLM-L12-v2);
  agglomerative clustering. A new cluster is matched to an existing topic when centroid cosine is
  ≥ 0.80. Labels come from c-TF-IDF.
- **Kleinberg bursts (corrected form):** αᵢ = sⁱ/ĝ; σ(i,x) = −ln αᵢ + αᵢx; τ = (j−i)·γ·ln n; solved
  by Viterbi.
- **Rise score** = 0.35·z(burst) + 0.25·z(acceleration) + 0.20·z(novelty) + 0.20·z(unique-account growth).
- **Forecast:** gradient boosting on lagged hourly counts (80% band), plus an exponential-kernel
  **Hawkes process** fitted by maximum likelihood.
- **Priority** P = 100·(0.35·B + 0.30·C + 0.20·S + 0.15·R): burst level, coordinated share, anxiety
  shift, reach. P ≥ 70 is high priority.
- **Sectors:** each topic is assigned to one of 9 sectors by transparent keyword evidence. Levels:

  | Level | Rule |
  |---|---|
  | Critical | A manufactured topic with a high-priority signal |
  | Elevated | A manufactured topic, or ≥ 10% coordinated |
  | Watch | ≥ 2% coordinated, or burst level ≥ 3 |
  | Quiet | No posts |

- **Hot topics / viral hashtags:** the busiest hour divided by the usual hourly rate over the whole window.

### 5.5 Network (E)
- Directed interaction graph, account → account. Edge weights: reply 1.0, forward 0.9, repost 0.8,
  mention 0.3.
- **KOL influence** = 0.5·cascade + 0.3·PageRank + 0.2·betweenness, each normalised.
- **Bridges:** high betweenness among accounts that touch more than one community.
- **Segments:** segment 0 is the coordinated group; segments 1–4 are the largest greedy-modularity
  communities of everyone else. For a narrative we show when each segment was reached and its
  anxiety.
- **Account panel:** public profile fields, activity per platform, topics, and connected accounts in
  both directions. No inferred demographics.

### 5.6 Coordination detector
- **Unit = narrative cluster:** posts linked by near-identical text (cosine ≥ 0.90, same hour), a
  shared hashtag (same 30 min) or a repost/forward chain.
- **Cluster test:** logistic combination of
  - synchrony;
  - (1 − normalised entropy of log-binned gaps);
  - max(0, −B), where B is Goh–Barabási burstiness;
  - the cross-account duplicate ratio;
  - the share of posts from accounts with scripted cadence.
- **Per-account score:** co-posting, regularity of the account's own timing, repetition. An account
  is flagged at ≥ 0.7.
- Wording guardrail: "behaviour consistent with scripted amplification". **Never "bot".**

### 5.7 Lineage and LLM summaries
- **Lineage:** earliest *observed* post per platform, hand-offs, Telegram forward chains, image
  copies by perceptual hash.
- **AI summaries (Gemini):** posts are treated as untrusted data. They are fenced with a nonce,
  output must match a JSON schema, and output must be grounded in the source posts. 11 injection
  break tests; the feature is disabled without a key.

---

## 6. Measured results (eval harness, `eval/reports/summary.json`)

Weights and thresholds are set on **seed 7**; headline numbers are on **held-out seed 11** wherever
tuning was involved. The evaluation data is synthetic, with ground truth.

| Area | Metric | Result |
|---|---|---|
| A | Ingest throughput (replay → ledger → DB) | **544 records/s** |
| B | Emotion macro-F1, held-out, synthetic labels | **0.63** (zero-shot baseline 0.57) |
| B | Per label (held-out) | anxiety **0.80**, excitement **0.92**, sarcasm 0.17 |
| B | All vs organic anxiety share, rumour window | 42.0% vs 60.8% (×0.69, **inverted: do not claim a panic distortion**) |
| C | Geography extraction accuracy / coverage | **100%** / 86.4% |
| C | Released buckets below k | **0** |
| D | Planted rumour alerted at high priority | **yes** (P = 72.9); decoy max P = 61.7 → **0 decoy high-priority alerts** |
| D | Lead time vs naive keyword-volume alarm | **5 min earlier** |
| D | High-priority alerts per day: ours vs naive | **0.14 vs 35.0** |
| D | 6 h forecast MAE: naive / GBR / Hawkes | 3.51 / **1.41** / 1.83 |
| E | Planted bridge account rank | **#1** |
| Coord | Held-out precision / recall / F1 | **0.71 / 1.00 / 0.83** |
| Coord | Baselines F1: age-follower heuristic / exact duplicate | 0.01 / 0.21 |
| Lineage | Origin / migration | earliest = **Telegram**, X after **12.1 min** |
| Lineage | pHash suite (200 images × 6 transforms, 2,000 negatives) | recall **98.2%** at FPR **0.9%** |
| Theme | Single-character tamper detection | **1000 / 1000** |
| Theme | Full verification, 100k records | **1.33 s** |

**Ablation (coordination, held-out).** Removing the scripted-cadence share drops recall to 0; it is
the key signal. Removing synchrony, entropy or cross-account duplication removes the fan-club false
positives: the detector over-weights co-posting for synchronized but genuine groups.

---

## 7. Demo data
- **Scenario (for ground truth).** 7 days (Nov 4–11 2024) on X, Telegram, Reddit and YouTube, plus
  a synthetic Instagram/Facebook official-export sample loaded through the real import path.
  Records carry `synthetic=true`; the site does not display it, and we say it in the pitch.
- **The planted story:**
  - **Rumour:** "Varunapur Dam has cracked, evacuate", first posted by a Telegram channel at
    22:10 IST on day 4.
  - **Amplification:** 60 coordinated X accounts posting every ~90 s ± 5 s.
  - **Real reaction:** anxious replies and debunks, and a Facebook residents' group share. The
    district administration's debunk follows.
  - **Decoy:** a bigger, genuine cricket surge with a legitimate fan-club swarm.
  - **Bridge:** one account linking both communities.
  - **Image copies:** resized, compressed, cropped and watermarked versions of the rumour photo.
- **Real data:** the **live Telegram feed** fetches real posts from The Indian Express, Hindustan
  Times, Mint and Moneycontrol through our connected account. They are scored live and refreshed
  every few minutes. They are shown alongside the scenario, not mixed into its timeline.

---

## 8. What to say, and what not to say

**Say:**
- "One national picture: what is being pushed, by whom, and where it lands, then investigate, then evidence."
- "Every view as all activity or organic only."
- "Our Telegram collector is live: these are real posts from public news channels, fetched just now."
- "The detector found all 60 planted accounts on a held-out scenario; simple baselines score F1 0.01 and 0.21."
- "The rumour fires a high-priority signal 5 minutes before a volume alarm; the bigger organic cricket surge doesn't."
- "1000 out of 1000 tampers caught; 100k records verified in 1.3 s; checkpoints anchored to Bitcoin."
- "Every analyst decision is sealed in the same chain as the evidence."

**Don't say:**
- "Bots made it look X× more panicked." The measured ratio is inverted (0.69).
- "Legally admissible." Say "designed to support BSA §63 documentation (draft for signature)".
- "Bot detection." Say "behaviour consistent with scripted amplification".
- "Accuracy on real data." Every metric is on synthetic scenarios with ground truth.
- Any number that isn't in `summary.json`, except the on-screen demo facts in §4.

---

## 9. PPT: 6 slides (confirm against the official SIH template)
1. **Title and hook.** Deepastambha logo and name (दीपस्तम्भ, "pillar of light"), PS 26152 · NTRO ·
   Team MOGGERS.
   - Headline: *"A national situation room for social media: what is being pushed, by whom, and where
     it lands."*
   - Chips: "5/5 PS components live" · "Telegram live" · "Every record hash-chained".
   - Screenshot: the Situation Room.
2. **Solution in one picture.** The four-step flow (Situation → Detect → Investigate → Evidence).
   Add the traceability table (§2), one measured number per row (§6). Before/after: "volume alarm:
   35 alerts/day, decoy triggered · ours: 0.14/day, rumour caught 5 min earlier, decoy ignored".
3. **Technical approach.**
   - The architecture (§3) or the team's diagram with the four corrections.
   - The Kleinberg and Goh–Barabási formulas.
   - The ledger flow: hash → chain → Merkle → Ed25519 → Bitcoin.
   - The models used.
4. **Feasibility.**
   - Zero-cost stack; free hosting kept awake 24/7.
   - Risks and mitigations: API breakage → replay plus pluggable collectors; terms of service →
     official feeds in production; privacy → k-anonymity and differential privacy; legal → draft
     certificate plus counsel.
   - Scaling path (§3).
5. **Impact.**
   - Alert fatigue cut (0.14 vs 35 per day).
   - Earlier detection (5 min).
   - State- and sector-level situational awareness.
   - Evidence readiness.
   - Use cases: public-order rumours, influence operations, disaster misinformation.
   - India-first multilingual design.
6. **References.**
   - Kleinberg 2002; Goh & Barabási 2008; Hawkes 1971.
   - mDeBERTa-v3 / XNLI; XLM-R; Sentence-BERT.
   - Merkle 1987; Ed25519; OpenTimestamps; pHash.
   - BSA 2023 §63.
   - k-anonymity (Sweeney 2002); differential privacy (Dwork 2006).
   - More in `docs/DIAGRAMS.md`.

---

## 10. Demo (about 3 min)
The captioned screen recording is in `demo_video/`. The click-by-click walkthrough and
voice-over are in the shared doc.
1. **Situation Room:** read the report. Switch the state map to anxiety and click Maharashtra.
   Click the Critical Infrastructure sector card, which opens Trends filtered.
2. **Live from Telegram:** real posts from Indian news channels, fetched now.
3. **Trends:** the manufactured badge and viral hashtags.
4. **Investigate the group** (from the report): Coordination.
5. **Network:** press Play the week, then click the Telegram channel node (12,000 followers,
   forwarded by 66 accounts on X).
6. **Lineage:** Telegram → X +12 min → four more platforms.
7. Back on the Situation Room, press **Approve → case**. The case opens with the evidence pack and
   draft certificate.
8. **Evidence ledger:** Verify integrity, then Run tamper simulation, which is caught at the exact record.

---

## 11. Likely jury questions (with answers)
- **"Is the data real?"** The storyline is a synthetic scenario so that we can measure against
  ground truth. The Telegram collector is live on the site: those posts are real and fetched now.
  X, Reddit and YouTube collectors are built and tested; Instagram and Facebook come through their
  official exports.
- **"How do you know they're bots?"** We don't label bots. We score behaviour (synchronized
  near-duplicate posting plus scripted cadence) and show every factor. Held-out: all 60 accounts
  found; precision 0.71, because a legitimate fan swarm also looks coordinated.
- **"Why is sentiment weak?"** Pre-trained models misread Hinglish panic content. We report it
  openly; the fix is a MuRIL fine-tune on an audited gold set.
- **"What makes it blockchain?"** A hash-chained append-only log with Ed25519-signed Merkle
  checkpoints and Bitcoin anchoring via OpenTimestamps. There's no token; production could swap in
  Hyperledger Fabric behind the same interface.
- **"Privacy?"** Group counts only: k=10, Laplace noise, and no per-account demographics anywhere
  (tested). States are reported only when at least 10 accounts back them.
- **"How is the state map computed?"** Only from the location people write on their public
  profile, aggregated. Impact counts posts in a pushed narrative or replies to one.
- **"Scale?"** Each component sits behind an interface for Postgres, Kafka, Neo4j and Milvus.
  Verifying 100k records takes 1.3 s.

---

## 12. Limitations
1. The storyline is synthetic. Only Telegram is connected live on the hosted demo; X, Reddit and
   YouTube need their credentials there.
2. The live Telegram feed is scored with the lexicon model and is shown, not stored, on the public
   demo.
3. Emotion is measured on synthetic labels with no gold set; sarcasm F1 is 0.17; the panic
   distortion is inverted.
4. Coordination flags a legitimate fan swarm on the held-out seed (precision 0.71).
5. Lineage gives the *earliest observed* origin, not necessarily the true one.
6. Age coverage is low (bio cues only); sectors come from keyword rules.
7. The §63 certificate is a draft for counsel; no admissibility is claimed.
8. Not built yet: login/roles, rate limiting, OCR, CLIP image search, ONNX.
9. An old ledger private key is in the repo's first commit; treat it as compromised.

---

## 13. Deployment and repository
- **Hosting.**
  - Render free web service; the private demo database is downloaded from a Hugging Face bundle at
    start-up.
  - A Cloudflare cron Worker keeps it awake 24/7.
  - Telegram, Gemini and HF credentials are Render secrets.
  - Infrastructure names keep the old name so nothing breaks: `deepastambha.onrender.com`,
    `deepastambha-keepalive`, `ZOROxJODD/deepastambha-bundle`, `data/deepastambha.db`.
  - TRIVENI runs on a separate account and is untouched.
- **Repositories.** `Shantanu58-tech/PS_2` is canonical. `OMEExZORO/PS_2` is the deploy mirror. Both
  always get the same commits.

```
backend/app/collectors/   X, Telegram (+ live_feed), Reddit, YouTube, CSV import, replay, health
backend/app/pipeline/     normalise, ingest (ledger first), analytics orchestrator, SSE events, live scheduler
backend/app/nlp/          emotion (NLI + sentiment + lexicon), embeddings, language id, Hinglish
backend/app/analytics/    topics, trends, burst, forecast, signals, coordination, graph (+store, segments),
                          lineage, demographics, behaviour, situation (sectors/states/narratives), cases, summarize
backend/app/ledger/       canonical, chain, merkle, sign, verify, proof, audit, ots
backend/app/api/routers/  REST endpoints (OpenAPI at /docs)
backend/eval/             eval harness + calibration
backend/tests/            153 tests
frontend/src/             React console (SituationRoom, Platforms, Trends, …); frontend/tests = Playwright
scenario/                 synthetic scenario + IG/FB export sample generator
scripts/                  fetch_models, check_collectors, telegram_login (two-step), dev.ps1
docs/                     DECISIONS.md, DIAGRAMS.md, APPROACH.md, ADRs
eval/reports/             summary.json + reports (the source of every evaluation number)
```

**Run locally:** `make setup && cp .env.example backend/.env`, then `make models`, `make scenario`,
`make demo` (http://localhost:8000 → Load data). Tests and evaluation: `make test`, `make eval`,
`make verify`. On Windows use `scripts\dev.ps1 <target>`. Telegram login:
`python scripts/telegram_login.py --phone …`, then `--code …`.

## 14. Glossary
- **Organic only:** metrics recomputed without accounts whose coordination score is ≥ 0.7.
- **Signal:** a ranked, explained alert (one per topic), reviewed by an analyst.
- **Exposure (state map):** the share of a state's posts that are in, or reply to, a pushed narrative.
- **Kleinberg burst:** a period where a stream's best-fit rate state is elevated.
- **Burstiness B:** −1 clock-like, about 0 random, toward +1 very bursty.
- **Cascade influence:** the accounts that directly or indirectly re-shared or replied to you.
- **Merkle checkpoint / seal:** one signed hash summarising 100 ledger entries.
- **OpenTimestamps:** a free proof that a hash existed at a time, anchored in Bitcoin.
- **pHash:** a perceptual image fingerprint; a small Hamming distance means the same image after edits.
- **k-anonymity / DP:** no group smaller than k is released; counts carry calibrated noise.
