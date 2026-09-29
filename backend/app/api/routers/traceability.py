from fastapi import APIRouter

router = APIRouter()

TRACEABILITY = [
    {"ps": "A", "component": "Multi-platform collection + timeline", "module": "app/collectors/", "test": "tests/test_collectors.py", "status": "built"},
    {"ps": "B", "component": "Multi-dimensional emotion inference", "module": "app/nlp/emotion.py", "test": "tests/test_emotion.py", "status": "built"},
    {"ps": "C", "component": "Aggregate demographics (k-anon)", "module": "app/analytics/demographics.py", "test": "tests/test_demographics.py", "status": "built"},
    {"ps": "D", "component": "Trend detection, burst, forecast", "module": "app/analytics/topics.py + burst.py", "test": "tests/test_burst.py", "status": "built"},
    {"ps": "E", "component": "Network graph, KOLs, spread", "module": "app/analytics/graph.py", "test": "tests/test_graph.py", "status": "built"},
    {"ps": "Theme", "component": "Hash-chain ledger + Ed25519 + tamper demo", "module": "app/ledger/", "test": "tests/test_ledger.py", "status": "built"},
]


@router.get("/traceability")
async def get_traceability():
    return {"requirements": TRACEABILITY}
