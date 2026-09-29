"""PS 26152 requirement -> module -> test -> measured metric.

Status is computed, not asserted: a row is "built" only if its module and
test files exist; the metric comes from eval/reports/summary.json or reads
"not yet measured".
"""
import json
from pathlib import Path

from fastapi import APIRouter

from app.config import BACKEND_DIR, settings

router = APIRouter()

TRACEABILITY = [
    {"ps": "A", "requirement": "Continuous multi-platform collection & timeline",
     "component": "Collectors X, Telegram (essential), Reddit, YouTube (appreciable), IG/FB CSV import "
                  "(desirable); append-only time-stamped DB",
     "modules": ["app/collectors/x_twscrape.py", "app/collectors/telegram_telethon.py",
                 "app/collectors/reddit_praw.py", "app/collectors/youtube_api.py",
                 "app/collectors/import_csv.py", "app/collectors/replay.py"],
     "tests": ["tests/test_collectors.py", "tests/test_normalizers.py", "tests/test_pipeline.py"],
     "metric": ("pipeline", "records_per_second"), "page": "/sources"},
    {"ps": "B", "requirement": "Multi-dimensional sentiment over time",
     "component": "Pre-trained XLM-R sentiment + DistilRoBERTa emotion + sarcasm model, Hinglish lexicon "
                  "blend; anxiety/excitement/supportive/against/sarcasm timeline",
     "modules": ["app/nlp/emotion.py", "app/nlp/hinglish.py", "app/nlp/langid.py"],
     "tests": ["tests/test_emotion.py"], "metric": ("emotion", "macro_f1"), "page": "/timeline"},
    {"ps": "C", "requirement": "Aggregate anonymized demographics",
     "component": "Cohort-only age/geography/language/interests; k-anonymity + Laplace noise",
     "modules": ["app/analytics/demographics.py"], "tests": ["tests/test_demographics.py"],
     "metric": ("demographics", "geo_accuracy"), "page": "/audience"},
    {"ps": "D", "requirement": "Real-time trend & topic detection, ranking, prediction",
     "component": "Windowed topic clustering + centroid matching, Kleinberg bursts, rise score, forecasts",
     "modules": ["app/analytics/topics.py", "app/analytics/burst.py", "app/analytics/trends.py",
                 "app/analytics/forecast.py"],
     "tests": ["tests/test_burst.py", "tests/test_topics.py", "tests/test_forecast.py"],
     "metric": ("burst", "lead_time_minutes"), "page": "/trends"},
    {"ps": "E", "requirement": "Link analysis, KOLs, spread over time",
     "component": "Interaction graph, PageRank/cascade KOLs, bridges, communities, spread frames",
     "modules": ["app/analytics/graph.py", "app/analytics/graph_store.py"],
     "tests": ["tests/test_graph.py"], "metric": ("graph", "bridge_rank"), "page": "/network"},
    {"ps": "Theme", "requirement": "Blockchain & Cybersecurity",
     "component": "SHA-256 hash chain, signed Merkle checkpoints (Ed25519), OpenTimestamps, tamper demo, "
                  "audit trail, draft BSA s.63 certificate",
     "modules": ["app/ledger/chain.py", "app/ledger/verify.py", "app/ledger/ots.py", "app/ledger/proof.py"],
     "tests": ["tests/test_ledger.py", "tests/test_ots.py"],
     "metric": ("ledger", "tamper_detection_rate"), "page": "/ledger"},
    {"ps": "V2", "requirement": "Coordination detector (value feature)",
     "component": "Timing/entropy/duplicate cluster test + per-account attribution; organic-only views",
     "modules": ["app/analytics/coordination.py"], "tests": ["tests/test_coordination.py"],
     "metric": ("coordination", "f1"), "page": "/network"},
]


def _summary() -> dict:
    path = Path(settings.eval_dir) / "summary.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


@router.get("/traceability")
async def get_traceability():
    summary = _summary()
    rows = []
    for req in TRACEABILITY:
        modules_ok = all((BACKEND_DIR / m).exists() for m in req["modules"])
        tests = {t: (BACKEND_DIR / t).exists() for t in req["tests"]}
        section, key = req["metric"]
        value = (summary.get(section) or {}).get(key)
        rows.append({
            "ps": req["ps"], "requirement": req["requirement"], "component": req["component"],
            "module": ", ".join(req["modules"]), "test": ", ".join(req["tests"]),
            "modules_present": modules_ok, "tests_present": tests,
            "status": "built" if modules_ok and all(tests.values()) else "partial",
            "metric_name": f"{section}.{key}",
            "metric_value": value if value is not None else "not yet measured",
            "page": req["page"],
        })
    return {"requirements": rows, "eval_generated_at": summary.get("generated_at")}
