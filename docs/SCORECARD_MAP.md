# Scorecard map

This file does two things. It maps SIH judging criteria to PRAHARI features, with proof links. It also traces each problem-statement requirement through the code to where it shows up in the UI. Paths are filled in as each phase lands; a row is "done" only when its test or proof link exists.

## Judging criteria

| Criterion | What we show | Proof (file / test / page) | Status |
|---|---|---|---|
| Problem Understanding | Components A–E read as an influence-operations workflow; the SMCH 2018 lesson; Telegram ToS 1.5 | `docs/research/RESEARCH_REPORT.md`, `docs/PPT_SUPPORT.md` | In progress |
| Innovation | Null-model coordination with p-values; calibrated Hinglish affect with abstention; cross-platform lineage; a query audit ledger | Phases 2–3 | Planned |
| Feasibility | Platform access table with 2026 costs; replay mode; budget guard; runs on a 6 GB GPU | `docs/adr/`, `backend/ingest/budget.py` | Planned |
| Impact | Earlier warning on cross-border influence operations; fewer false accusations; auditable use | `docs/DEMO_SCRIPT.md` | Planned |
| Clarity | Eval card, evidence drawer, method tooltips, 5-minute demo | `/eval`, `docs/EVAL_CARD.md` | Planned |

## Requirement → code → UI traceability

| PS requirement | Backend module | Test | UI page | Status |
|---|---|---|---|---|
| A. Multi-platform ingestion | `backend/ingest/connectors/*`, `ingest/replay/` | `tests/test_connectors_*.py` | Sources & compliance | Planned |
| A. Historical database | `backend/ingest/archive.py`, Postgres `events` | `tests/test_archive.py` | Overview | Planned |
| B. Nuanced affect (supportive, against, anxiety, excitement, sarcasm, neutral) | `backend/nlp/affect/` | `tests/test_affect_*.py` | Narrative detail, Eval card | Planned |
| B. Affect over time | `backend/nlp/` + aggregates | | Narrative detail | Planned |
| C. Demographics (aggregate) | `backend/demographics/` | `tests/test_route_scan.py` | Audience | Planned |
| D. Trend emergence | `backend/trends/` | | Overview | Planned |
| D. Prediction | `backend/trends/forecast.py` | | Narrative detail | Planned |
| E. Network / KOLs | `backend/graph/kol.py` | | Network | Planned |
| E. Coordination | `backend/graph/coordination.py`, `nullmodel.py` | `tests/test_coordination_*.py` | Coordination explorer | Planned |
| E. Spread across segments and platforms | `backend/graph/lineage.py` | | Narrative detail, Network | Planned |
| Governance | `backend/app/audit/` | `tests/test_ledger_*.py` | Audit | Planned |

Team MOGGERS, VIT Pune. Team Leader: Om Soma.
