"""Regenerate the README metrics table from eval/reports/summary.json.

Replaces the block between <!-- METRICS:START --> and <!-- METRICS:END -->.
Numbers are only ever copied from summary.json (CLAUDE.md rule 3); anything
missing is written as "not yet measured".
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NM = "not yet measured"


def get(d: dict, path: str):
    cur = d
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def fmt(v, pct: bool = False) -> str:
    if v is None:
        return NM
    if isinstance(v, float) and pct:
        return f"{v * 100:.1f}%"
    return str(v)


def table(s: dict) -> str:
    rows = [
        ("A", "Pipeline throughput (replay -> ledger -> DB)", f"{fmt(get(s, 'pipeline.records_per_second'))} records/s over {fmt(get(s, 'pipeline.records'))} records"),
        ("B", f"Emotion macro-F1, held-out seed {fmt(get(s, 'emotion.evaluated_seed'))}, synthetic template labels (not a gold set)",
         f"{fmt(get(s, 'emotion.macro_f1'))} vs zero-shot NLI baseline {fmt(get(s, 'emotion.baseline_zero_shot_nli_macro_f1'))} "
         f"(team lexicon {fmt(get(s, 'emotion.baseline_lexicon_macro_f1'))} is leaky: written with the templates)"),
        ("B", "Raw vs organic-only anxiety share, rumour window (ratio < 1: models under-read panic broadcasts, see emotion.md)", f"{fmt(get(s, 'emotion.distortion.raw_anxiety_share'), True)} vs {fmt(get(s, 'emotion.distortion.organic_anxiety_share'), True)} (x{fmt(get(s, 'emotion.distortion.distortion_ratio'))})"),
        ("B", "Emotion macro-F1 on human-audited gold set", NM),
        ("C", "Geography extraction accuracy / coverage", f"{fmt(get(s, 'demographics.geo_accuracy'), True)} / {fmt(get(s, 'demographics.geo_coverage'), True)}"),
        ("C", "Released buckets below k", fmt(get(s, "demographics.released_buckets_below_k"))),
        ("D", "Planted rumour alerted at high priority / decoy high-priority alerts", f"{fmt(get(s, 'burst.injected_event_recall'))} / {fmt(get(s, 'burst.decoy_high_priority_alerts'))}"),
        ("D", "Lead time vs naive keyword-volume baseline", f"{fmt(get(s, 'burst.lead_time_minutes'))} min"),
        ("D", "Alerts/day: ours (high priority) vs naive", f"{fmt(get(s, 'burst.high_priority_alerts_per_day'))} vs {fmt(get(s, 'burst.naive_alerts_per_day'))}"),
        ("D", "Forecast MAE (6 h): naive / GBR / Hawkes", f"{fmt(get(s, 'forecast.mae_naive'))} / {fmt(get(s, 'forecast.mae_gbr'))} / {fmt(get(s, 'forecast.mae_hawkes'))}"),
        ("E", "Planted bridge account rank (bridge score)", fmt(get(s, "graph.bridge_rank"))),
        ("E", "Coordinated accounts in top-20 KOLs: raw -> organic-only", f"{fmt(get(s, 'graph.coordinated_in_top20_raw'))} -> {fmt(get(s, 'graph.coordinated_in_top20_organic'))}"),
        ("V2", "Coordination P / R / F1 (held-out seed)", f"{fmt(get(s, 'coordination.precision'))} / {fmt(get(s, 'coordination.recall'))} / {fmt(get(s, 'coordination.f1'))}"),
        ("V2", "Baselines F1: age/ratio heuristic / exact-duplicate", f"{fmt(get(s, 'coordination.baseline_age_ratio_f1'))} / {fmt(get(s, 'coordination.baseline_exact_duplicate_f1'))}"),
        ("V2", "Decoy (cricket + fan-club) accounts flagged", fmt(get(s, "coordination.decoy_accounts_flagged"))),
        ("V3", "Scenario origin found / Telegram -> X migration", f"{fmt(get(s, 'lineage.origin_found'))} / {fmt(get(s, 'lineage.telegram_to_x_minutes'))} min"),
        ("V3", "pHash recall / FPR at chosen threshold", f"{fmt(get(s, 'phash.recall_at_chosen'), True)} / {fmt(get(s, 'phash.fpr_at_chosen'), True)} (T={fmt(get(s, 'phash.chosen_threshold'))})"),
        ("Theme", "Tamper detection (single-char mutations)", f"{fmt(get(s, 'ledger.tamper_detection_rate'), True)} of {fmt(get(s, 'ledger.tamper_trials'))} trials"),
        ("Theme", "Full verification time, 100k records", f"{fmt(get(s, 'ledger.verify_100k_seconds'))} s"),
    ]
    head = f"_Generated from `eval/reports/summary.json` ({s.get('generated_at', NM)}). Scenario data is synthetic._\n\n"
    lines = ["| PS | Metric | Measured |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return head + "\n".join(lines)


def main() -> None:
    summary_path = ROOT / "eval" / "reports" / "summary.json"
    s = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    block = f"<!-- METRICS:START -->\n{table(s)}\n<!-- METRICS:END -->"
    new = re.sub(r"<!-- METRICS:START -->.*?<!-- METRICS:END -->", lambda _: block, text, flags=re.S)
    readme.write_text(new, encoding="utf-8")
    print("README metrics updated" if new != text else "README unchanged")


if __name__ == "__main__":
    main()
