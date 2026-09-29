# Security

## Secrets
- Secrets live only in `backend/.env` (or `.env` at the repo root), which is gitignored,
  as are `*.session`, `data/keys/ledger_ed25519` (the ledger's private signing key) and
  the database files. `.env.example` lists every key with no values.
- The `.gitignore` patterns use `**/` so they also match under `backend/`. Before
  this fix, `backend/keys/ledger_ed25519` was not ignored.
- CI runs gitleaks on the full history.
- **If a key was ever pushed or pasted anywhere public, rotate it.** That covers
  platform cookies/tokens, HF_TOKEN, GEMINI_API_KEY, and the ledger key (a new
  ledger key means re-signing checkpoints in a fresh ledger).

## Evidence integrity
- `raw_records` is append-only (SQLite triggers). The app never issues
  UPDATE/DELETE on it. Tamper simulation runs only on a temporary backup copy.
- Hash chain: SHA-256 over the canonical JSON payload plus the previous entry hash.
  Every 100 entries, a Merkle checkpoint is signed with Ed25519. `verify_chain`
  recomputes every record hash, chain link, Merkle root and signature.
- Optional OpenTimestamps anchoring of checkpoint roots (ENABLE_OTS).
- Analyst actions are written to both `audit_log` and the hash chain.

## Web
- Replay/demo mode is public read-only (CORS `*`). Live mode restricts CORS and
  should be served same-origin (the backend serves the built console).
- Inputs are validated by Pydantic/FastAPI. Search input is converted to a quoted
  FTS5 query, so raw user text is never interpreted as FTS syntax.
- LLM summaries treat posts as untrusted data: nonce-fenced input, schema-checked
  JSON output, and grounding/canary checks (`tests/test_summarize.py`).
- Not yet implemented: JWT analyst login, rate limiting and CSP headers
  (PRD section 17). These are required before any non-demo deployment.

## Reporting
Report security issues privately to the team lead, not through public issues.
