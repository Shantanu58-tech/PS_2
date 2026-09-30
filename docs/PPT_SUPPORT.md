# DEEPASTAMBHA: idea PPT support (SIH26152)

This is the source content for the six-slide SIH idea deck. Every factual claim traces back to `docs/research/RESEARCH_REPORT.md`, where the citation numbers in brackets point. **Nothing on these slides claims a measured DEEPASTAMBHA result yet.** The metrics are shown as the *evaluation plan* and the *published baselines we must beat*. Say it that way on stage; it is part of our credibility.

---

## Slide 1: Title
- **DEEPASTAMBHA**: *Narrative forensics, not surveillance.*
- Subtitle: compliance-first detection of coordinated narratives across Telegram and X, in Hinglish.
- SIH26152 · Social Media Analytics · NTRO
- Team MOGGERS, VIT Pune · Team Leader: **Om Soma** · (member names)
- Theme: Blockchain & Cybersecurity (the audit ledger) / Smart Automation

**Speaker line:** "We detect when a narrative is being pushed, by which coordinated clusters, across Telegram and X, in Hinglish, with measured accuracy, without building a surveillance database."

---

## Slide 2: Proposed solution

**The problem, told with a real case**
- In Q3 2023, Meta removed a China-origin network aimed at India's Arunachal Pradesh discourse. Its fictitious personas posed as journalists, lawyers and human-rights activists on Facebook and X, and about 1,400 accounts joined one of its Groups. In the same report, part of a separate 4,789-account network switched from posing as Americans to posing as India-based. [81]
- Could India catch this **in Hinglish, across Telegram and X, without surveilling citizens?**

**What DEEPASTAMBHA does**, with components A–E read as an influence-operations workflow:

| PS component | DEEPASTAMBHA answer |
|---|---|
| A. Collection | Official APIs plus a curated public-channel allowlist, with a provenance tag on every event (LIVE / REPLAY / IMPORT / SYNTHETIC) |
| B. Nuanced affect | Hinglish-first multi-head model (sentiment, stance, emotion, sarcasm) with **calibrated confidence and abstention** |
| C. Audience | **Aggregate-only** language, state, interests and age bands, with k-suppression and differential privacy |
| D. Trends and prediction | Narrative clusters, burst detection, and a 6–24 h growth forecast measured against a baseline |
| E. Network and spread | Coordination graphs with a **statistical null model**, temporal KOLs, and **cross-platform cascade lineage** |

**Four things no public SIH26152 repo does** (we reviewed 9 public repos [43–53]):
1. Publish measured Hinglish accuracy with abstention.
2. Test coordination against a null model, with p-values.
3. Trace narratives from Telegram to X over time.
4. Enforce privacy in the architecture itself, including a query audit ledger and refusal by design.

---

## Slide 3: Technical approach

**Architecture** (draw as a left-to-right pipeline):
```
X API · Telegram (read-only allowlist) · YouTube · Reddit · Replay datasets
      → Canonical event (UTC, provenance, content hash)
      → Privacy gate (HMAC-SHA256 pseudonyms, PII dropped, Telegram train_allowed = false)
      → Postgres + immutable Parquet archive + Redis Streams (real time)
      → NLP │ Trends │ Graph │ Aggregate demographics
      → Evidence & alert engine (every alert links posts, method, confidence)
      → FastAPI gateway (RBAC + Merkle-anchored query ledger) → Analyst console
```

**Stack:**
- Backend: Python 3.11, FastAPI, PostgreSQL 16, Redis Streams, Parquet.
- NLP: MuRIL / XLM-R multi-head, served through ONNX int8.
- Topics and graphs: BERTopic, NetworkX + igraph (Leiden).
- Console: Next.js, Sigma.js.

**The three technical cores:**
1. **Calibrated Hinglish affect.**
   - Pipeline: token-level language ID → transliteration normalisation → shared encoder with 4 heads.
   - Temperature scaling, reported as ECE before and after.
   - The model outputs **UNCERTAIN** instead of guessing, and sarcasm-aware re-scoring handles sarcasm.
   - Training data: SentiMix, the Hinglish sarcasm corpora, Joshi 2016, HOT, and a **team-annotated gold set of 500+ posts** (two annotators, Cohen's kappa).
2. **Coordination with a null model.**
   - Signals: co-retweet within 60 s (X), co-forward within Δt (Telegram), MinHash near-duplicate text (Jaccard > 0.8), and shared-URL bursts. [22]
   - Each cluster is compared with 200 within-account time-shuffles and reported only above the 99th percentile, with a p-value.
   - This answers the literature's warning that coordination signals often capture organic partisanship. [4][23]
3. **Cross-platform cascade lineage.**
   - Items are linked by URL, content hash, MinHash and time order.
   - Output is a directed temporal graph of narrative jumps, worded as "earliest observed", never "origin".

**Evaluation plan** (what the eval card will report):

| Measure | Reference point we must beat or match |
|---|---|
| Hinglish 3-class sentiment, weighted F1 | SemEval-2020 SentiMix best: **75.0%**; top 15 teams between 75% and 68.6% [Patwa et al.] |
| Sarcasm F1 | Swami et al. 2018: 78.4% on about 5K tweets with 10% sarcastic [7]; Aggarwal et al. 2020: 79.4% [8] |
| Baselines shown side by side | VADER (used by competitors [51]) and TF-IDF logistic regression |
| Calibration | ECE before and after temperature scaling, plus the abstention rate |
| Coordination | Precision, recall and **detection latency** on injected synthetic campaigns with known ground truth |
| Forecast | Lift over a naive persistence baseline |

---

## Slide 4: Feasibility and viability

**Platform access in 2026** (from the report's "Practical reality"):

| Platform | Access route | Limit / cost | Our handling |
|---|---|---|---|
| X | Official API v2, pay-per-use (since 6 Feb 2026) | about $0.005 per post read; 10K posts ≈ $50 [58] | Hard budget guard (default cap $20/month); falls back to replay |
| Telegram | MTProto (Telethon), read-only, curated public channels | Undocumented FLOOD_WAIT; **ToS 1.5 bans using data for AI/ML** [56] | Rule-based and graph analytics plus inference only; **never trained on**, enforced in code |
| YouTube | Data API v3 | 10,000 units/day; commentThreads costs 1 unit [71][73] | Quota tracker |
| Reddit | Official OAuth, non-commercial | 100 queries per minute [70] | Rate limiter |
| Instagram / Facebook | Graph API Hashtag Search | 30 hashtags per 7 days; App Review required [66] | Compliant connector stub; no scraping |

**Why it is buildable:**
- Everything trains on one RTX 3050 (6 GB): fp16, sequence length 128, models ≤ 300M params. Google Colab handles heavier runs.
- Serving uses ONNX int8 on CPU, so the hosted demo runs on free tiers.
- **Replay mode:** the hosted demo streams historical datasets (Pushshift Telegram, TGDataset, SentiMix [26][27]) and synthetic campaigns through the same pipeline. It costs nothing and cannot break.
- The team has a proven hosting track record from TRIVENI (SIH26027): Docker, a cold-start keep-alive, and a warm-up UI.

**Compliance design:**
- DPDP Act 2023 and Rules 2025: aggregate-only outputs, pseudonyms, retention limits, and no children's data (s.9). [76–80]
- This avoids the fate of the 2018 SMCH, withdrawn after the Supreme Court said it would be "like creating a surveillance state". [42]

---

## Slide 5: Impact and benefits
- **Earlier warning on cross-border influence operations.** Narratives are caught while still jumping from Telegram to X, not after they trend.
- **Fewer false accusations.** Calibrated abstention and null-model p-values mean the system says "not sure" rather than labelling citizens. It says "coordinated cluster", never "bot".
- **Evidence-grade output.** Every alert carries its posts, method, parameters, confidence and a reproducibility hash, ready to justify action. Existing state tooling such as Sahyog automates takedowns, but has no analytic layer that justifies them. [5]
- **Auditable, lawful use.** Every analyst query is hash-chained with hourly Merkle roots, and profiling a single account is refused *and logged*. This answers the SMCH lesson directly.
- **Built for India's languages.** Hinglish and Devanagari are handled natively instead of translated then analysed, which loses code-mixed nuance (the weakness of commercial tools such as Logically [33]).
- **Sovereign and low-cost.** It runs on commodity hardware, with no dependence on opaque foreign scoring products. [28][32]

---

## Slide 6: Research and references
- Patwa et al., SemEval-2020 Task 9 SentiMix (Hinglish sentiment benchmark)
- Swami et al. 2018; Aggarwal et al. 2020, Hinglish sarcasm [7][8]
- Wang et al., M3 Inference, WWW 2019 (age F1 0.522; why we refuse per-user demographics) [1][13]
- Coordination Network Toolkit, J. Comput. Soc. Sci. 2024 [22]
- CIB on TikTok, arXiv 2505.10867 (false-positive warning) [23]
- Pushshift Telegram Dataset, ICWSM 2020; TGDataset [26][27]
- Meta Adversarial Threat Report Q3 2023 [81]
- Telegram API Terms of Service §1.5 [56]
- DPDP Act 2023 s.3(c)(ii); DPDP Rules 2025 (G.S.R. 846(E)) [76][79]
- Mahua Moitra v. Union of India (2018), the SMCH withdrawal [42]

---

## Break-test questions a judge may ask (keep ready)
1. *Show a sarcastic Hinglish post handled correctly, and one where the model abstains.* This is the eval card plus a live demo.
2. *Trace one narrative from a Telegram channel to X, with timestamps.* This is the lineage graph.
3. *Can I get one person's profile?* The request is refused by design and appears in the audit ledger.
4. *How is this different from the SMCH?* It is aggregate-only, k-suppressed, uses DP, has no minors, and every query is audited.
5. *Isn't Telethon against Telegram's terms?* We follow ToS 1.5: read-only access to a curated public allowlist, and the data is never used for training.

*Prepared for Team MOGGERS, VIT Pune. Team Leader: Om Soma.*
