"""Run every evaluation and write eval/reports/*.md + summary.json.

    cd backend && python -m eval.run_all [--quick] [--rebuild]

--quick: 100 tamper trials, skip the 100k verify benchmark.
Every number the README / slides / UI shows must come from summary.json.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

from eval.common import HELDOUT_SEED, REPORTS, VALIDATION_SEED, build_db


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--only", default="", help="comma list of sections to recompute, merged into the "
                    "existing summary.json (coordination,burst,emotion,phash,ledger,components)")
    args = ap.parse_args()

    from eval import alerts_eval, components_eval, coordination_eval, emotion_eval, ledger_eval, phash_suite

    t0 = time.perf_counter()
    val = build_db(VALIDATION_SEED, force=args.rebuild)
    held = build_db(HELDOUT_SEED, force=args.rebuild)
    if args.only:
        only = {x.strip() for x in args.only.split(",") if x.strip()}
        path = REPORTS / "summary.json"
        summary = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if "coordination" in only:
            summary["coordination"] = coordination_eval.evaluate(val, held)
        if "burst" in only:
            summary["burst"] = alerts_eval.evaluate(val)
        if "emotion" in only:
            summary["emotion"] = emotion_eval.evaluate(val, held)
        if "phash" in only:
            summary["phash"] = phash_suite.run()
        if "ledger" in only:
            summary["ledger"] = ledger_eval.evaluate(val, trials=100 if args.quick else 1000,
                                                     sizes=(10_000,) if args.quick else (10_000, 100_000))
        if "components" in only:
            summary.update(components_eval.evaluate(val))
        summary["generated_at"] = datetime.now(timezone.utc).isoformat()
        summary.setdefault("partial_updates", []).append({"sections": sorted(only), "at": summary["generated_at"]})
        path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        print(f"Updated {sorted(only)} in {path}")
        return
    comp = components_eval.evaluate(val)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario": {"validation_seed": VALIDATION_SEED, "heldout_seed": HELDOUT_SEED,
                     "records_validation": val["records"], "records_heldout": held["records"],
                     "synthetic": True},
        "coordination": coordination_eval.evaluate(val, held),
        "burst": alerts_eval.evaluate(val),
        "emotion": emotion_eval.evaluate(val, held),
        "phash": phash_suite.run(),
        "ledger": ledger_eval.evaluate(val, trials=100 if args.quick else 1000,
                                      sizes=(10_000,) if args.quick else (10_000, 100_000)),
        **comp,
    }
    summary["runtime_seconds"] = round(time.perf_counter() - t0, 1)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"Eval complete -> {REPORTS / 'summary.json'} ({summary['runtime_seconds']} s)")
    c, b, e, lg = summary["coordination"], summary["burst"], summary["emotion"], summary["ledger"]
    print(f"  coordination (held-out seed {c['heldout_seed']}): P {c['precision']} R {c['recall']} F1 {c['f1']}; "
          f"decoy flagged {c['decoy_accounts_flagged']}")
    print(f"  alerts: rumour recall {b['injected_event_recall']}, decoy high-priority {b['decoy_high_priority_alerts']}, "
          f"lead vs naive {b['lead_time_minutes']} min")
    print(f"  emotion macro-F1 (synthetic labels) {e['macro_f1']} vs lexicon {e['baseline_lexicon_macro_f1']}; "
          f"distortion {e['distortion']['distortion_ratio']}")
    print(f"  phash T={summary['phash']['chosen_threshold']} recall {summary['phash']['recall_at_chosen']} "
          f"FPR {summary['phash']['fpr_at_chosen']}")
    print(f"  ledger tamper detection {lg['tamper_detection_rate']} over {lg['tamper_trials']} trials")


if __name__ == "__main__":
    main()
