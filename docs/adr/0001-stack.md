# ADR 0001: Technology stack

- Status: Accepted
- Date: 2026-09-29
- Owner: architect
- Approved by: Om Soma

## Context
PRAHARI has to ingest from four live platforms plus replay datasets. It needs to run Hinglish NLP on a 6 GB RTX 3050, compute temporal coordination graphs, and serve an analyst console. The hosted demo must run for free. The brief (§3.1) proposes a stack. TRIVENI (`docs/HOSTING_NOTES.md`) showed what worked for this team and what hurt.

## Decision

| Layer | Choice | Version pin (at decision time) |
|---|---|---|
| Backend language | Python 3.11 (`py -3.11`; the machine default is 3.14, which is not used) | 3.11 |
| Package / lock | `uv` with `pyproject.toml` and `uv.lock` | uv 0.12 |
| API | FastAPI with Pydantic v2 and pydantic-settings | fastapi 0.141, pydantic 2.13 |
| ORM / migrations | SQLAlchemy 2 with Alembic, driver psycopg 3 | sqlalchemy 2.1 |
| Database | PostgreSQL 16 | 16 |
| Bus | Redis Streams (redis-py), consumer groups | Redis 7 |
| Raw archive | Parquet through pyarrow, under `D:\PRAHARI_DATA\raw` | |
| Graph compute | NetworkX plus python-igraph (Leiden); edges persisted in Postgres | |
| NLP | Transformers, MuRIL or XLM-R base, sentence-transformers (LaBSE or multilingual MiniLM) | |
| Topics | BERTopic with the custom embedder | |
| Serving models | ONNX Runtime, int8 | |
| Frontend | Next.js (App Router), TypeScript, Tailwind, Recharts, Sigma.js | next 16, tailwind 4 |
| Tests | pytest, hypothesis, Playwright | |
| Lint | ruff (Python), ESLint (TS) | |

## Consequences
- Following TRIVENI, the Python version stays at 3.11 so the Docker base image (`python:3.11-slim`) matches local development.
- The brief says Next.js 14. We take the current stable major (16) instead, because 14 is two majors behind and would miss security fixes. The App Router model is the same.
- TRIVENI used Vite with React. We move to Next.js because the brief specifies it, and because it deploys natively on Vercel. Server components also help the eight-page console. Recorded here per brief §3.1.
- Code is modular, one package per component, which avoids TRIVENI's 2,000-line `main.py`.
- There are no code comments anywhere (Om's rule). Explanations live in `docs/`.
