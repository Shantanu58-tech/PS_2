# ADR 0003: Local infrastructure and time-series storage

- Status: Accepted
- Date: 2026-09-29
- Owner: architect
- Approved by: Om Soma ("whichever option will help us host this website in future")

## Context
Docker is not installed on the development machine. The brief's Phase 0 gate is `docker compose up`. Production runs as Docker containers with managed Postgres and Redis (ADR 0002).

## Decision
1. **Local stack:** Docker Desktop with the WSL2 backend, running `docker-compose.yml` with three services:
   - `postgres` (postgres:16-alpine)
   - `redis` (redis:7-alpine, AOF on)
   - `api` (the same Dockerfile the host uses)
2. **Python outside Docker:** Python development also works outside Docker (`py -3.11` with a uv venv) against the Compose Postgres and Redis. Unit tests that don't need a live database run with no services at all.
3. **No TimescaleDB.** `events` uses plain Postgres declarative range partitioning by month on `created_at_utc`. Hosts differ in extension support, and partitioning is enough at demo scale.

## Consequences
- Om installs Docker Desktop once (admin rights plus a reboot). Until then, all the non-database work continues.
- Local containers match production, so "works locally, fails hosted" risk is low.
- Hourly and daily rollups are built as materialised aggregate tables in Phase 2 instead of Timescale continuous aggregates.
