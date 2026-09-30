# DEEPASTAMBHA: current approach, end to end (interim)

> Snapshot for team context and PPT prep, written mid-build (2026-09-30).
> Numbers marked **interim** come from the latest `eval/reports/` run and may change
> after the final evaluation. The final, complete brief will be `MASTER_CONTEXT.md`.
> Rule: slides may only quote numbers that appear in `eval/reports/summary.json`.

---

## 1. The problem (PS 26152, NTRO, Blockchain & Cybersecurity theme)
Build an AI social-media analytics framework covering:
- **A.** Multi-platform collection and a time-stamped history: X and Telegram (must-have), Instagram and Facebook (desirable), Reddit and YouTube (appreciable).
- **B.** Nuanced sentiment over time: sarcasm, anxiety, excitement, supportive, against.
- **C.** Aggregate, anonymised demographics: age, geography, language, interests.
- **D.** Real-time trend and topic detection, ranking and prediction.
- **E.** Link analysis: key opinion leaders (KOLs) and how narratives spread between segments.

## 2. Our thesis: coordination-adjusted analytics
Every team will build A–E. What makes us different: **every view can be shown raw or
"organic-only"**, with coordinated accounts removed. This shows an analyst how much a
campaign distorts sentiment, trends, demographics and influence. It is wrapped in an
evidence-grade pipeline, where every collected record is hash-chained and signed,
optionally anchored to Bitcoin via OpenTimestamps.

Analyst story in one line: *what narrative is spreading, where it was first seen, who is
amplifying it, whether that amplification is organic or coordinated, how the real
public feels, and what evidence can be handed over.*

## 3. Architecture (as built)
```
Collectors (X, Telegram, Reddit, YouTube; IG/FB export import; Replay)
  -> RawRecord
  -> Ledger writer: canonical JSON -> SHA-256 record hash -> chained entry hash
                    -> every 100 entries: Merkle root signed with Ed25519
  -> Normaliser -> SQLite (WAL + FTS5): posts, accounts, interaction edges, media (sha256 + pHash)
  -> Analytics pipeline (idempotent stages):
       emotions -> edge resolution -> topics -> coordination -> series & bursts
       -> topic classification -> demographics -> behaviour -> forecasts
       -> Signal Cards -> OpenTimestamps anchor
  -> FastAPI (REST + SSE live progress) -> React console (served from the same URL)
```
Stack: Python 3.11, FastAPI, SQLite, NetworkX (Neo4j optional through the GraphStore
interface), PyTorch CPU, Hugging Face models, React + Vite + Recharts. Docker is a single
image. Every component sits behind an interface, so a production swap
(Postgres, Kafka, Neo4j, Milvus) is a config change.

## 4. Component by component

### A. Collection and timeline
- Live collectors: **twscrape** (X, using burner-account cookies), **Telethon** (Telegram,
  keeps forward headers for lineage), **PRAW** (Reddit), **YouTube Data API v3**
  (comments plus replies).
- Resilience: exponential backoff with jitter, a circuit breaker per collector, and
  health shown at `/api/collectors`.
- Instagram/Facebook: CSV export import (no free live API; stated openly).
- Replay collector: streams the seeded scenario through **the same** pipeline.
- Chronology: UTC stored, IST shown. Reply threads resolve, or are flagged as orphans.
- Credentials are needed for live runs: X cookies, Telegram api_id/hash, Reddit
  script app, YouTube key.

### B. Sentiment and emotion (pre-trained, no training)
- **Engine:** zero-shot multilingual NLI (`mDeBERTa-v3-base-mnli-xnli`) for anxiety,
  excitement and sarcasm, plus the multilingual **XLM-R sentiment** model for supportive
  and against. Per-label thresholds are tuned on the validation seed; the headline is
  reported on the held-out seed.
- **Interim, held-out seed:** macro-F1 **0.63**. That beats the old English classifier
  pipeline (0.28) and the zero-shot baseline (0.57). Anxiety F1 is 0.80, excitement 0.92,
  and sarcasm only 0.17.
- Hinglish handling: script detection, a Hinglish lexicon, spelling-variant
  canonicalisation, emoji-to-token mapping. Scores are cached, so re-runs are fast.
- **Honest finding, and our weakest part:** the model reacts to *words* like "panic" rather
  than to meaning. A debunk saying "stop spreading panic" scores higher anxiety than the
  rumour "Evacuate immediately!". So the raw-vs-organic anxiety distortion is currently
  **inverted** (42% raw vs 61% organic, ratio 0.69), and the "bots made it look more
  panicked" claim **cannot be made yet**. The fix is the PRD §11 MuRIL fine-tune
  (it needs a GPU and a 400-item audited set).
- Labels come from synthetic templates (about a dozen distinct texts), not a human gold set.

### C. Demographics (aggregate only)
- Geography from a 36-state/UT gazetteer (whole-word matching). Interests from bio
  keywords. Age bracket from bio cues (minors excluded). Language from posts.
- Privacy: **k-anonymity (K=10)**, so buckets under K are withheld. **Laplace noise** is
  added (DP, ε=1). Account IDs are HMAC-pseudonymised, and there is **no per-account
  endpoint** (tested).
- **Interim:** geography accuracy 100% on known-location profiles (an earlier 93.5% exposed a
  Chandigarh→Punjab bug, now fixed), coverage 86%, age coverage 21%.

### D. Trends, bursts, prediction
- Topics: 24 h windows over post time, clustered with multilingual sentence embeddings
  (agglomerative, deterministic), with centroid matching to keep topic identity across
  windows. Labels from c-TF-IDF.
- **Kleinberg burst detection**, as corrected in the PRD (γ·ln n up-transition cost).
- Rise score: z-scored burst level, acceleration, novelty and unique-account growth.
- Forecast: gradient boosting on lagged hourly counts plus an **exponential-kernel Hawkes
  process** (MLE). **Interim** 6 h backtest MAE: GBR 1.41, Hawkes 1.83, naive 3.51.
- Signal Cards: priority = 35% burst + 30% coordinated share + 20% anxiety shift + 15% reach,
  one card per topic, with "why it fired" evidence.
- **Interim:** the planted rumour is flagged at high priority (**72.9/100**; the high-priority
  threshold is 70). The cricket decoy peaks at **61.7**, so it gets **no** high-priority alert. Our online detector flags the rumour **5 min earlier** than a
  naive keyword-volume baseline. High-priority alerts: 0.14/day vs 35/day naive.

### E. Network and influence
- An account-to-account interaction graph (reply, repost, quote, forward, mention).
- KOLs ranked by **cascade influence** (50%) + PageRank (30%) + betweenness (20%), with
  originator vs amplifier roles. The ranking is recomputed organic-only to show "who
  actually influences vs who is pumped".
- Bridge accounts, communities, and spread frames over time.
- **Interim:** the planted bridge account ranks **#1** on bridge score.

### Value feature: coordination detector
- Unit of analysis: **narrative clusters**, which are connected posts sharing near-identical
  text (same hour), a hashtag (same 30 min window) or a repost chain. This makes detection
  robust even when topic modelling fragments a campaign.
- Cluster test: synchrony, binned normalised entropy of gaps, Goh–Barabási burstiness,
  cross-account duplicate ratio, and the share of accounts with scripted cadence.
- **Per-account** attribution, so that people who merely reply to a campaign are not flagged.
- Protocol: weights set on scenario seed 7, headline reported on **held-out seed 11**.
- **Interim** (held-out): recall **1.00**, precision **0.71**, F1 **0.83**. All false positives
  are the planted **fan-club swarm** (legitimate fans posting together at match moments),
  which the PRD itself calls the hard case. On the validation seed: P = R = 1.0.
  Baselines F1: age/follower heuristic 0.01, exact-duplicate detector 0.21.
- Guardrails: never labelled "bot"; the wording is "behaviour consistent with scripted amplification".

### Value feature: narrative lineage
- Earliest *observed* post per platform, platform hand-offs, repost/forward chains,
  and image variants matched by perceptual hash.
- **Interim:** origin found (Telegram), migration Telegram→X in **12.1 min**, **4/4** image
  variants linked. On a 200-image transformation suite, pHash recall is **98.3% at 0.85% FPR**
  (T=20).

### Theme: evidence ledger (Blockchain & Cybersecurity)
- Append-only (DB triggers), SHA-256 hash chain, and Ed25519-signed Merkle checkpoints
  every 100 records. Merkle inclusion proofs let anyone verify a record with only the
  public key.
- **OpenTimestamps**: the newest checkpoint root is stamped on public calendars, then
  upgraded to a Bitcoin attestation and verified against the block header.
- Tamper simulation runs on a scratch copy and fails at the exact sequence number.
  Analyst actions (verify, tamper-sim, case creation) are themselves written into the chain.
- **Interim:** **1000/1000** single-character tampers detected. Verifying 37k records with
  374 signed checkpoints takes about 0.6 s.
- Case files: a brief (evidence index with ledger seq and hashes, checkpoints, lineage, raw
  vs organic affect, coordination stats) plus a **draft** BSA §63 certificate for counsel review.

### Optional: LLM narrative summaries
- Google Gemini (`GEMINI_API_KEY`), with prompt-injection defences: nonce-fenced input,
  a JSON schema check, grounding checks and a canary check. It fails closed and is disabled without a key.

## 5. The demo scenario (fully synthetic)
- 7 days, about 37k posts, 3,000 accounts, IST daily rhythm, English / Hinglish / Devanagari
  (plus a little Tamil and Bengali), with reply trees and mentions.
- Planted rumour: "Varunapur Dam has cracked", seeded as a meme on a Telegram channel at
  day 4 22:10 IST, forwarded on Telegram, then amplified on X 12 min later by
  **60 coordinated accounts** posting every ~90 s (10 of them "aged" accounts).
- Organic pickup (anxious replies plus sarcastic debunks), a **cricket-win decoy** with a
  legitimate fan-club swarm, and a planted **bridge** account.
- `replay/truth.json` holds the ground truth used by the eval harness.

## 6. How we measure (eval harness)
`make eval` builds two scenario seeds (7 = validation, 11 = held-out) and writes
`eval/reports/*.md` + `summary.json`. It covers: coordination P/R/F1 with baselines and a
per-signal ablation; alerts vs a naive baseline, with online lead time; emotion vs a
zero-shot baseline; a pHash ROC; 1000 ledger tamper trials plus verify time at 100k records;
demographics accuracy and coverage; the bridge rank; a forecast backtest; pipeline throughput.

## 7. Demo flow (about 3 min)
1. Mission Briefing, then **Start Replay** (live progress over SSE).
2. Command Center: the "Manufactured surge" Signal Card for the dam rumour; the cricket
   decoy stays low priority.
3. Timeline: flip **Organic only** to show the raw vs organic views. Do not claim a
   panic distortion until the fine-tuned emotion model exists.
4. Lineage: Telegram origin, then X at +12 min, plus the matched image variants.
5. Network: bridge account, KOLs, coordinated accounts marked.
6. Ledger: **Verify** passes; **Tamper Simulation** fails at the exact record.
7. Case: brief plus the draft §63 certificate. Compliance page: A–E with measured metrics.

## 8. Honest limitations (say them before the jury does)
- The demo data is synthetic. Collectors are live-capable but need credentials.
- Emotion is the weakest part: synthetic labels, no gold set, weak sarcasm, and an inverted
  panic distortion (the zero-shot model keys on words, not meaning).
- The coordination detector flags a legitimate fan swarm on the held-out seed.
- "Earliest observed" is not the true origin. The §63 certificate is a draft. Age coverage is low.
- Not yet built: JWT login and rate limiting, OCR, CLIP image search, ONNX export, the
  UI/UX overhaul (planned next, with the team's go-ahead).

## 9. Where things are
- Live demo: https://deepastambha.onrender.com (read-only, synthetic data). Code: https://github.com/Shantanu58-tech/PS_2
- Code: `backend/app/` (collectors, pipeline, nlp, analytics, ledger, api), `frontend/src/`.
- Evidence: `eval/reports/`. Decisions and deviations: `docs/DECISIONS.md`.
- Run: `make setup && make models && make scenario && make demo` (Windows: `scripts\dev.ps1`).
