# SATYA-NET: Master Context

**Team MOGGERS · VIT Pune · Smart India Hackathon 2026**
**Problem Statement 26152 "Social Media Analytics" · NTRO · Category: Software · Theme: Blockchain & Cybersecurity**

> The single reference for the team: what we built, how it works, what we measured,
> how to demo it and how to pitch it. **Every number here comes from
> `eval/reports/summary.json` (generated 2026-09-30).** Never put a number on a
> slide that isn't in that file. Details: `docs/DECISIONS.md` (all design decisions),
> `eval/reports/*.md` (all measurements), `PROJECT_STATUS.md` (what's left).

---

## 1. One-liner and thesis

**One-liner:** SATYA-NET turns raw multi-platform social streams into evidence-grade
intelligence. It shows what narrative is spreading, where it was first seen, who is
amplifying it, whether that amplification is organic or coordinated, and it keeps every
collected record in a tamper-evident, independently verifiable ledger.

**Thesis: coordination-adjusted analytics.** Every team will build the five PS
components (collection, sentiment, demographics, trends, network). We tie them together
with one idea: **every view can be shown raw or organic-only**, with coordinated
accounts removed, so the analyst sees how much a campaign distorts trends, audience and
influence. Around it sits an evidence pipeline: hash chain, signed Merkle checkpoints,
Bitcoin time-anchoring (OpenTimestamps), tamper simulation, and a draft BSA §63 certificate.

**Primary user:** an NTRO cyber-intelligence analyst.
**Pain points solved:** alert fatigue (few, explained Signal Cards); organic vs
astroturf (coordination detector + organic-only toggle); cross-platform tracing
(lineage); evidence that holds up (ledger + case brief).

---

## 2. Problem statement mapping (what the jury checks)

| PS | Requirement (abridged) | What we built | Where |
|---|---|---|---|
| **A** | Multi-platform ingestion of live posts, interactions and comments; structured time-stamped history. Essential: X, Telegram. Desirable: Instagram, Facebook. Appreciable: Reddit, YouTube | Live collectors for **X (twscrape), Telegram (Telethon), Reddit (PRAW), YouTube (Data API v3, incl. replies)**; **IG/FB via export CSV import**; replay; backoff + circuit breaker + health; UTC timeline, reply threads, dedup | `backend/app/collectors/`, `app/pipeline/` |
| **B** | NLP for nuanced emotions (sarcasm, anxiety, excitement, supportive, against) over the timeline | Five dimensions per post; zero-shot multilingual NLI + multilingual sentiment; Hinglish handling; hourly/daily timeline, raw vs organic | `app/nlp/`, `/api/timeline/*` |
| **C** | Aggregate, anonymised demographics (age brackets, geography, language, professional interests) | Cohort-only counts; 36-state/UT gazetteer; bio-cue age brackets (minors excluded); interests; language; **k-anonymity K=10 + Laplace noise**; no per-account endpoint | `app/analytics/demographics.py` |
| **D** | Identify, rank and **predict** rising trends and viral keywords chronologically | Windowed topic clustering with centroid matching; **Kleinberg bursts**; **rise score**; **gradient-boosting + Hawkes forecasts**; Signal Cards | `app/analytics/{topics,trends,burst,forecast,signals}.py` |
| **E** | Map relationships, find key opinion leaders, visualise spread between segments over time | Interaction graph; KOLs by **cascade influence** + PageRank + betweenness; bridge accounts; communities; spread frames; organic-only rank changes | `app/analytics/graph*.py` |
| **Theme** | Blockchain & Cybersecurity | **SHA-256 hash chain, Ed25519-signed Merkle checkpoints, inclusion proofs, OpenTimestamps (Bitcoin) anchoring, tamper simulation, audit trail inside the chain, draft §63 certificate** | `app/ledger/`, `app/analytics/cases.py` |

---

## 3. Architecture

```
            ┌──────────── Collectors ────────────┐
            │ X · Telegram · Reddit · YouTube    │  backoff+jitter, circuit breaker,
            │ IG/FB CSV import · Replay          │  health at /api/collectors
            └──────────────┬─────────────────────┘
                           │ RawRecord
                           ▼
   Ledger writer: canonical JSON → SHA-256 → chained entry hash → raw_records (append-only)
                  every 100 entries: Merkle root, signed with Ed25519 → ledger_checkpoints
                           │
                           ▼
   Normaliser → SQLite (WAL, FTS5): posts · accounts · edges (account→account) · media (sha256+pHash)
                           │
                           ▼
   Analytics pipeline (each stage an idempotent recompute):
     emotions → edge resolution → topics → coordination → series & bursts → topic classification
     → demographics (raw + organic) → behaviour (experimental) → forecasts → Signal Cards → OTS anchor
                           │
                           ▼
   FastAPI (REST + SSE live progress)  ──►  React console (served from the same URL)
```

**Stack:** Python 3.11, FastAPI, SQLite (Postgres-portable schema), NetworkX (Neo4j via
the `GraphStore` interface), PyTorch CPU + Hugging Face models, React + Vite + TypeScript +
Recharts, Docker single image, GitHub Actions CI (pytest, ruff, mypy, gitleaks, build,
Playwright).

**Prototype → production** (slide 4): SQLite → Postgres/TimescaleDB; asyncio queue →
Kafka; NetworkX → Neo4j (already behind an interface); FTS5 → Elasticsearch; embeddings →
Milvus; hash-chain ledger → Hyperledger Fabric; research collectors → licensed feeds.

---

## 4. Algorithms (for slide 3 and jury questions)

### 4.1 Ledger (Theme)
- `record_hash = SHA256(canonical_json(payload))` (sorted keys, UTF-8, no whitespace)
- `entry_hash_n = SHA256(prev_entry_hash ‖ record_hash ‖ collected_at ‖ collector_id ‖ seq)`, genesis = 64 zeros
- Every 100 entries: Merkle root over the entry hashes, **signed with Ed25519**
- `verify` recomputes every record hash, chain link, **Merkle root** and signature
- **Inclusion proof:** a Merkle path plus the signed root. Anyone with the public key can verify one record.
- **OpenTimestamps:** the newest checkpoint root is submitted to public calendars, then
  `upgrade` fetches the Bitcoin attestation and `verify` checks it against the block
  header. Anchoring the newest root timestamps the whole ledger up to that point, because
  the entries are chained.
- Append-only is enforced by SQLite triggers. The tamper simulation runs only on a
  temporary copy. Analyst actions are written into the chain.

### 4.2 Emotion (B)
- **Anxiety, excitement, sarcasm:** zero-shot NLI with `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`
  (multilingual), using hypotheses such as "This message expresses or spreads fear, panic or alarm."
- **Supportive / against:** `cardiffnlp/twitter-xlm-roberta-base-sentiment` (multilingual) polarity.
- Per-label thresholds are tuned on the validation scenario seed; the headline is on the held-out seed.
- Hinglish: script detection, a Hinglish lexicon (`data/lexicons/hinglish_words.txt`),
  spelling-variant canonicalisation (nahi/nahin/nhi), emoji tokens.
- Language: script rules + Hinglish detector + langdetect (seeded).

### 4.3 Demographics (C)
- Geography: whole-word gazetteer match on location/bio (36 states/UTs with cities and aliases).
  Interests: keyword taxonomy over bios. Age: bio cues (for example "B.Tech 2nd yr",
  "retired", "born 1990") mapped to brackets; **minors are excluded**. Language: each
  account's dominant post language.
- **Privacy:** buckets with fewer than K=10 accounts are withheld (only the number of
  withheld buckets is shown). Released counts get **Laplace(1/ε) noise**, ε=1, floored at
  K. IDs are HMAC-pseudonymised. **No per-account endpoint exists** (tested).

### 4.4 Trends (D)
- **Topics:** 24 h windows (by post time). Multilingual sentence embeddings
  (paraphrase-multilingual-MiniLM-L12-v2) → agglomerative clustering (cosine,
  deterministic). A new cluster joins an existing topic if centroid cosine ≥ 0.80, which
  keeps topic identity across windows. Posts join if cosine to the centroid ≥ 0.55.
  Labels come from c-TF-IDF.
- **Kleinberg bursts (corrected form):** states i with rate αᵢ = sⁱ/ĝ; emission
  σ(i,x) = −ln αᵢ + αᵢx; up-transition cost τ = (j−i)·γ·ln n; solved by Viterbi. γ is
  the false-alarm control.
- **Rise score** = 0.35·z(burst level) + 0.25·z(acceleration) + 0.20·z(novelty) + 0.20·z(unique-account growth).
- **Forecast:** gradient boosting on lagged hourly counts, with an 80% band, plus an
  **exponential-kernel Hawkes process** λ(t) = μ + Σα·e^(−β(t−tᵢ)) fitted by maximum
  likelihood.
- **Signal Card priority** P = 100·(0.35·B + 0.30·C + 0.20·S + 0.15·R): burst level, coordinated
  share, anxiety shift, reach percentile. P ≥ 70 is high priority.

### 4.5 Network (E)
- Directed interaction graph account→account (reply 1.0, forward 0.9, repost 0.8, mention 0.3).
- **KOL influence** = 0.5·cascade (accounts who replied to, reposted or forwarded you, directly
  or indirectly) + 0.3·PageRank + 0.2·betweenness, each normalised; plus an
  originator/amplifier role.
- Bridges: betweenness among nodes touching more than one community (greedy modularity).
- Organic-only recompute shows rank changes ("who really influences vs who is pumped").

### 4.6 Coordination detector (value feature V2)
- **Unit = narrative cluster:** posts linked by near-identical text (cosine ≥ 0.90, same
  hour), a shared hashtag (same 30 min window) or a repost/forward chain. This is robust even
  when topic modelling fragments a campaign.
- **Cluster test:** logistic combination of synchrony S, (1 − normalised entropy Hn of
  log-binned gaps), max(0, −B) with Goh–Barabási burstiness B = (σ−μ)/(σ+μ), the
  cross-account duplicate ratio, and the share of posts from accounts with scripted cadence.
- **Per-account score:** co-posting (near-duplicate by a different account within 60 s),
  regularity of the account's own gaps, repetition, and cluster duplication. Flag at ≥ 0.7.
  Every signal is stored for the "why" panel.
- Wording guardrail: "behaviour consistent with scripted amplification". **Never "bot".**

### 4.7 Lineage (V3)
- Earliest *observed* post per platform, platform hand-offs, repost/forward chains
  (Telegram forward headers), and image variants by **perceptual hash** (Hamming distance).

### 4.8 LLM summaries (optional, B4)
- Google Gemini. Posts are untrusted data: sanitised, fenced with a random nonce, JSON
  schema enforced, and URLs/handles/hashtags must appear in the source posts. Known
  injection phrases fail closed. There are 11 break tests. Disabled without a key.

---

## 5. Demo scenario (fully synthetic, labelled SIMULATED)
- 7 days (Nov 4–11 2024), **37,353 posts**, 3,000 background accounts, IST daily rhythm,
  bursty human timing; English, Hinglish, Devanagari Hindi, a little Tamil and Bengali;
  reply trees and mentions; 8 everyday topics.
- **Planted rumour:** "Varunapur Dam has cracked, evacuate", a meme with a Hinglish overlay
  posted on a Telegram channel at **day 4, 22:10 IST**, forwarded in Telegram, then amplified
  on X **12 min later** by **60 coordinated accounts** posting template variants every
  ~90 s ± 5 s (10 of them "aged" accounts that fool naive age/follower heuristics).
- **Organic pickup:** 300 anxious replies and sarcastic debunks.
- **Decoy:** a bigger cricket-win surge from genuine accounts plus a **legitimate fan-club
  swarm** posting together at match moments (the hard false-positive test).
- **Bridge:** one account linking the rumour and cricket communities.
- **Image variants:** resize 60%, JPEG q30, crop 10%, watermark.
- Ground truth: `replay/truth.json`. Seed 7 = demo/validation; seed 11 = held-out evaluation.

---

## 6. Measured results (eval harness, `eval/reports/`)

Protocol: weights and thresholds are set on **seed 7**; headline numbers are on
**held-out seed 11** where tuning was involved. The data is synthetic.

| Area | Metric | Result |
|---|---|---|
| A | Ingest throughput (replay → ledger → DB) | **544 records/s** (37,353 records) |
| B | Emotion macro-F1, held-out, synthetic labels | **0.63** (zero-shot NLI baseline 0.57; old classifier pipeline 0.28) |
| B | Per label (held-out) | anxiety **0.80**, excitement **0.92**, sarcasm 0.17 |
| B | Raw vs organic anxiety share, rumour window | 42.0% vs 60.8% (**×0.69, inverted; do not claim a panic distortion**) |
| C | Geography extraction accuracy / coverage | **100%** / 86.4% |
| C | Released buckets below k | **0** |
| D | Planted rumour alerted at high priority | **yes** (P = 72.9); decoy max P = 61.7 → **0 decoy high-priority alerts** |
| D | Lead time vs naive keyword-volume baseline (online) | **5 min earlier** |
| D | High-priority alerts/day: ours vs naive | **0.14 vs 35.0** |
| D | 6 h forecast MAE: naive / GBR / Hawkes | 3.51 / **1.41** / 1.83 |
| E | Planted bridge account rank | **#1** |
| V2 | Coordination, held-out: precision / recall / F1 | **0.71 / 1.00 / 0.83** |
| V2 | Baselines F1: age-follower heuristic / exact-duplicate | 0.01 / 0.21 |
| V2 | Validation seed (for reference) | P = R = F1 = 1.00 |
| V2 | Decoy accounts flagged (held-out) | 25, all from the fan-club swarm |
| V3 | Origin / migration | earliest observed = **Telegram**, X after **12.1 min** |
| V3 | Image variants linked in scenario | **4/4** |
| V3 | pHash suite (200 images × 6 transforms, 2,000 negatives) | recall **98.2%** at FPR **0.9%** (T=20) |
| Theme | Single-character tamper detection | **1000 / 1000 (100%)** |
| Theme | Full verification time, 100k records | **1.33 s** |

**Ablation (coordination, held-out):** removing the scripted-cadence share drops recall to
0 (it is the key signal). Removing synchrony, entropy or cross-account duplication removes
the fan-club false positives (precision 1.0), which shows the detector over-weights
co-posting for synchronized but genuine groups.

---

## 7. What to say, and what not to say

**Say:**
- "Coordination-adjusted analytics: every view raw or organic-only."
- "Detector found all 60 planted accounts on a held-out scenario; simple baselines score F1 0.01 and 0.21."
- "The planted rumour fires a high-priority card 5 minutes before a volume alarm; the bigger organic cricket surge doesn't."
- "1000 out of 1000 tampers caught; 100k records verified in 1.3 s; checkpoints anchored to Bitcoin via OpenTimestamps."
- "Lineage finds the Telegram origin and the 12-minute jump to X, including edited image copies."
- "Every number comes from our eval harness; limitations are listed in the app."

**Don't say:**
- "Bots made it look X× more panicked." Our current pre-trained models measure 0.69 (inverted).
- "Legally admissible." Say "designed to support BSA §63 documentation (draft for signature)".
- "Bot detection." Say "behaviour consistent with scripted amplification".
- "Accuracy on real data." All metrics are on synthetic scenarios with ground truth.
- Any number that isn't in `summary.json`.

---

## 8. PPT: 6 slides (PRD §18.1; confirm against the official SIH template)

**Slide 1: Title and hook.** PS 26152 · NTRO · Team MOGGERS · members. Headline: *"From
noisy streams to evidence-grade intelligence, and who's really behind the noise."* Chips:
"5/5 PS components live" · "Coordination-adjusted analytics" · "Every record
hash-chained". Buttons: live prototype · demo video · GitHub. Screenshot: Command Center
with the "Manufactured surge" Signal Card.

**Slide 2: Solution in one picture.** Left: A→E + ledger strip. Middle: the traceability
table with one measured number per row (§6). Right: a detection before/after, e.g.
"volume alarm: 35 alerts/day, decoy triggered · ours: 0.14/day, rumour caught 5 min
earlier, decoy ignored". Footer: "Scenario simulated; collectors live-capable."

**Slide 3: Technical approach.** Pipeline diagram (§3); Kleinberg and Goh–Barabási
formulas; the ledger flow (hash → chain → Merkle → Ed25519 → Bitcoin); the models used.

**Slide 4: Feasibility.** Zero-cost stack; risks and mitigations (API breakage → replay
plus pluggable collectors; ToS → official feeds in production; privacy → k-anon + DP;
legal → draft + counsel); scaling path (§3).

**Slide 5: Impact.** Alert fatigue cut (0.14 vs 35 alerts/day on the scenario);
earlier detection (5 min); evidence readiness (verify, proofs, §63 draft); use cases:
public-order rumours, influence operations; India-first multilingual design.

**Slide 6: References.** Kleinberg 2002 (bursts); Goh & Barabási 2008 (burstiness);
Hawkes 1971; mDeBERTa-v3 / XNLI; XLM-R (Conneau et al. 2020); Sentence-BERT; Merkle 1987;
Ed25519 (Bernstein et al.); OpenTimestamps; perceptual hashing (pHash); BSA 2023 §63;
k-anonymity (Sweeney 2002); differential privacy (Dwork 2006).

---

## 9. Demo script (about 3.5 min)
1. **(0:00)** Mission Briefing. Say the problem in one sentence. Open the PS 26152 Compliance page for 3 s.
2. **(0:20)** Command Center → **Start Replay**; progress streams live; analytics run.
3. **(0:50)** The top Signal Card, "Manufactured surge: Varunapur dam…". Open it: burst level,
   coordinated share, platforms. Point out the cricket surge is bigger but stays low priority.
4. **(1:20)** Trends: "Manufactured trend" vs "Organic" badges. Network: the bridge account,
   coordinated accounts marked, organic-only rank changes.
5. **(2:00)** Lineage: Telegram origin at 22:10 IST → X at +12 min; image variants with Hamming distances.
6. **(2:30)** Ledger: **Verify** passes (37k records, 374 signed checkpoints) → **Tamper
   Simulation** fails at the exact sequence number, on a copy.
7. **(3:00)** Case: create from the alert → brief (evidence index with ledger seqs and
   hashes) → **§63 DRAFT** certificate.
8. **(3:20)** Eval scoreboard, limitations, links.

---

## 10. Likely jury questions (with answers)
- **"Is the data real?"** The demo is synthetic so that we have ground truth to measure
  against. The collectors are real (`scripts/check_collectors.py`) and run once credentials
  are supplied.
- **"How do you know it's a bot?"** We don't label bots. We score behaviour: synchronized
  near-duplicate posting plus scripted cadence, and every factor is shown. Held-out: all 60
  planted accounts found; precision 0.71, because a legitimate fan swarm looks coordinated
  (listed as a limitation).
- **"Why is sentiment weak?"** Pre-trained models misread Hinglish panic content; a debunk
  saying "stop spreading panic" scores more anxious than the rumour. The fix is our planned
  MuRIL fine-tune with an audited gold set. We report this rather than hide it.
- **"What makes it blockchain?"** A hash-chained append-only log with Ed25519-signed Merkle
  checkpoints and optional Bitcoin anchoring via OpenTimestamps. There's no token or
  consensus network; production could swap in Hyperledger Fabric behind the same interface.
- **"Privacy?"** Aggregate cohorts only, k=10, Laplace noise, no per-account demographics
  anywhere in the API (tested), and pseudonymised IDs.
- **"Scale?"** SQLite and NetworkX for the prototype; each piece sits behind an interface
  for Postgres, Kafka, Neo4j and Milvus. Verifying 100k records takes 1.3 s.
- **"Instagram/Facebook?"** No free live API; we import official exports through the same
  evidence pipeline, and say so openly.

---

## 11. Limitations (shown in the app too)
1. The demo data is synthetic; live collectors need credentials.
2. Emotion: synthetic labels (about a dozen distinct texts), no gold set; sarcasm F1 0.17;
   the panic distortion is inverted with pre-trained models.
3. Coordination flags a legitimate fan swarm on the held-out seed (precision 0.71).
4. Lineage gives the *earliest observed* origin, not necessarily the true one.
5. Age coverage is low (bio cues only).
6. The §63 certificate is a draft for counsel; no admissibility is claimed.
7. Not built yet: JWT login, rate limiting, OCR, CLIP image search, ONNX, the UI overhaul.
8. The old ledger private key is in the repo's first commit (treat it as compromised; see PROJECT_STATUS §6).

---

## 12. Repository map
```
backend/app/collectors/   X, Telegram, Reddit, YouTube, CSV import, replay, health (backoff/breaker)
backend/app/pipeline/     normalise, ingest (ledger first), analytics orchestrator, events (SSE), live scheduler
backend/app/nlp/          emotion (NLI + sentiment), embeddings, language id, Hinglish
backend/app/analytics/    topics, trends, burst, forecast, signals, coordination, graph(+store), lineage,
                          demographics, behaviour (experimental), cases, summarize (Gemini)
backend/app/ledger/       canonical, chain, merkle, sign, verify, proof, audit, ots
backend/app/api/routers/  REST endpoints (see README / openapi at /docs)
backend/eval/             eval harness (make eval) + calibration
backend/scenario/         synthetic scenario generator
backend/tests/            135 tests
frontend/src/             React console; frontend/tests = Playwright smoke
data/                     gazetteer, lexicons, public ledger key (secrets and DBs are gitignored)
eval/reports/             summary.json + reports (the source of every number)
docs/                     DECISIONS.md, APPROACH.md, ADRs, PRD notes
scripts/                  fetch_models, check_collectors, update_readme_metrics, dev.ps1
```

## 13. How to run
```bash
make setup && cp .env.example backend/.env
make models        # ~3 GB of pre-trained models into ./models
make scenario      # synthetic scenario
make demo          # http://localhost:8000 → Start Replay
make test / make eval / make verify / make check-collectors
```
Windows: `scripts\dev.ps1 <target>`. Docker: `docker compose up --build`.

## 14. Glossary
- **Organic-only:** metrics recomputed without accounts whose coordination score is ≥ 0.7.
- **Signal Card:** a ranked, explained alert (one per topic).
- **Kleinberg burst:** a period where a stream's best-fit rate state is elevated.
- **Burstiness B:** −1 for clock-like posting, about 0 for random (Poisson), toward +1 for very bursty posting.
- **Normalised entropy Hn:** how spread out the inter-post gaps are across time scales (low = scheduled).
- **Cascade influence:** the number of accounts that directly or indirectly re-shared or replied to you.
- **Merkle checkpoint:** one hash summarising 100 ledger entries, signed so no one can alter them later.
- **OpenTimestamps:** free proof that a hash existed at a time, anchored in Bitcoin.
- **pHash:** a perceptual image fingerprint; a small Hamming distance means the same image after edits.
- **k-anonymity / DP:** no group smaller than k is released; counts carry calibrated noise.
