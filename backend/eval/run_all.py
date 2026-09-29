from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone


def run_burst_eval() -> dict:
    from app.analytics.burst import kleinberg_bursts, burstiness, norm_entropy
    import random
    rng = random.Random(42)
    base = list(range(0, 10000, 200))
    burst = list(range(5000, 5000 + 20 * 5, 5))
    ts = sorted(base + burst)
    results = kleinberg_bursts([float(t) for t in ts])
    detected = len(results) > 0
    return {
        "burst_detected": detected,
        "burst_count": len(results),
        "status": "PASS" if detected else "FAIL",
    }


def run_ledger_eval(db_path: str = "data/satya.db") -> dict:
    from pathlib import Path as P
    if not P(db_path).exists():
        return {"status": "SKIP", "reason": "DB not found"}
    from app.ledger.verify import verify_chain
    return verify_chain(db_path)


def run_coordination_eval() -> dict:
    from app.analytics.burst import burstiness, norm_entropy
    scripted_gaps = [60.0 + i * 0.1 for i in range(100)]
    organic_gaps = [abs(300 + 200 * (i % 7 - 3)) for i in range(100)]
    B_scripted = burstiness(scripted_gaps)
    B_organic = burstiness(organic_gaps)
    Hn_scripted = norm_entropy(scripted_gaps)
    Hn_organic = norm_entropy(organic_gaps)
    return {
        "scripted_burstiness": B_scripted,
        "organic_burstiness": B_organic,
        "scripted_entropy": Hn_scripted,
        "organic_entropy": Hn_organic,
        "status": "PASS" if Hn_organic > Hn_scripted else "FAIL",
    }


def main() -> None:
    reports_dir = Path("eval/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "burst": run_burst_eval(),
        "ledger": run_ledger_eval(),
        "coordination": run_coordination_eval(),
        "emotion": {"status": "not_yet_measured", "message": "Run with real data"},
        "demographics": {"status": "not_yet_measured", "message": "Run with real data"},
        "pipeline": {"status": "not_yet_measured", "message": "Run replay scenario"},
    }

    summary_path = reports_dir / "summary.json"
    summary_path.write_text(json.dumps(results, indent=2))
    print(f"Eval complete. Results at {summary_path}")
    for k, v in results.items():
        if isinstance(v, dict):
            status = v.get("status", "?")
            print(f"  {k}: {status}")


if __name__ == "__main__":
    main()
