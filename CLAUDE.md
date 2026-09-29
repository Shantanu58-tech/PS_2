# SATYA-NET — instructions for Claude Code

You are building the system in PRD sections 5–14 of SATYANET_PRD_and_Dev_Handoff.md.

## Rules
1. Build milestone by milestone (PRD §15). After each milestone: run `make test`, then report what passed and what didn't. Do not start the next milestone with failing tests.
2. Implement the CORRECTED algorithms (Kleinberg with γ·ln(n) up-transition costs, binned normalized entropy, Goh–Barabási burstiness, windowed topic re-clustering with centroid matching, cohort-only demographics).
3. Never fabricate metrics. Any number shown in UI, README or docs must come from `eval/reports/summary.json` produced by `make eval`. If a metric is missing, show "not yet measured".
4. Privacy: never add an endpoint or field that exposes per-account inferred demographics. Enforce k-anonymity (K_ANON env).
5. The ledger is append-only. Never write UPDATE/DELETE on `raw_records`. Tamper simulation runs only on a scratch copy.
6. Use interfaces for every swappable component (Collector, Queue, VectorStore, GraphStore, Ledger) so production swaps are config changes.
7. All timestamps are UTC internally, IST in UI. Mark every synthetic object `synthetic=true` and show the SIMULATED banner in replay mode.
8. Secrets only in .env; never commit keys, cookies or session files.
9. Prefer simple, tested code. Type hints everywhere; ruff + mypy clean; pytest for every module; golden fixtures for collectors.
10. When a library API differs from the PRD (e.g. twscrape field names), adapt, note it in docs/DECISIONS.md, and add a test.
11. Ask the human for anything only a human can do (PRD §20) instead of stubbing silently. Stubs must be flagged in code and README.

## Pre-trained models used (no training required)
- Emotion/Sentiment: `cardiffnlp/twitter-xlm-roberta-base-sentiment` via HF Inference API or local pipeline
- Multi-emotion: `j-hartmann/emotion-english-distilroberta-base` (anxiety/excitement/anger/joy/fear/disgust/neutral)
- Language ID: `papluca/xlm-roberta-base-language-detection`
- Embeddings: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- CLIP (image-text): `openai/clip-vit-base-patch32`
- Sarcasm: `helinivan/english-sarcasm-detector`
- Zero-shot NLI for topics/demographics: `facebook/bart-large-mnli` or `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`

## Definition of done for any task
Code + tests + docs line + (if user-visible) UI wired + acceptance criteria in the PRD met.
