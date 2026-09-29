"""Pipeline throughput, demographics accuracy/coverage, graph (bridge rank,
organic-only demotion), scenario lineage, forecast backtest."""
from __future__ import annotations

from datetime import datetime

from eval.common import connect, md_table, write_report


def pipeline(built: dict) -> dict:
    rec, ing, ana = built["records"], built["ingest_seconds"], built["analytics_seconds"]
    return {"records": rec, "ingest_seconds": ing, "records_per_second": round(rec / ing, 1) if ing else None,
            "analytics_seconds": ana, "end_to_end_seconds": round(ing + ana, 1),
            "stage_seconds": built.get("stage_seconds")}


GEO_TRUTH = {"Delhi": "delhi", "Mumbai": "maharashtra", "Bangalore": "karnataka", "Pune": "maharashtra",
             "Hyderabad": "telangana", "Chennai": "tamil nadu", "Kolkata": "west bengal", "Jaipur": "rajasthan",
             "Lucknow": "uttar pradesh", "Ahmedabad": "gujarat", "Patna": "bihar", "Bhopal": "madhya pradesh",
             "Kochi": "kerala", "Guwahati": "assam", "Chandigarh": "chandigarh"}


def demographics(built: dict) -> dict:
    from app.analytics.demographics import _infer_age_bracket, _infer_state

    with connect(built["db"]) as c:
        accts = c.execute("SELECT location_text, bio FROM accounts").fetchall()
        rows = c.execute("SELECT dimension, bucket, count FROM demo_aggregates WHERE organic_only=0").fetchall()
    geo_known = [a for a in accts if a["location_text"] in GEO_TRUTH]
    geo_acc = sum(1 for a in geo_known if _infer_state(a["location_text"]) == GEO_TRUTH[a["location_text"]])
    age_cov = sum(1 for a in accts if _infer_age_bracket(a["bio"]))
    suppressed = [r for r in rows if r["bucket"] == "suppressed"]
    below_k = [r for r in rows if r["bucket"] != "suppressed" and r["count"] < 10]
    return {"geo_accuracy": round(geo_acc / len(geo_known), 4) if geo_known else None,
            "geo_coverage": round(len(geo_known) / len(accts), 4) if accts else None,
            "age_coverage": round(age_cov / len(accts), 4) if accts else None,
            "released_buckets": len(rows) - len(suppressed), "suppressed_buckets": len(suppressed),
            "released_buckets_below_k": len(below_k)}


def graph(built: dict) -> dict:
    from app.analytics.graph import bridge_accounts, build_graph, compute_kols

    db, truth = built["db"], built["truth"]
    G = build_graph(db)
    bridges = bridge_accounts(G, top_n=20)
    rank = next((i + 1 for i, b in enumerate(bridges) if b["account_id"] == truth["bridge_account_id"]), None)
    coord = set(truth["coordinated_account_ids"])
    raw_top = [k["account_id"] for k in compute_kols(G, top_n=20)]
    org_top = [k["account_id"] for k in compute_kols(build_graph(db, organic_only=True), top_n=20)]
    return {"nodes": G.number_of_nodes(), "edges": G.number_of_edges(), "bridge_rank": rank,
            "coordinated_in_top20_raw": sum(1 for a in raw_top if a in coord),
            "coordinated_in_top20_organic": sum(1 for a in org_top if a in coord)}


def lineage(built: dict) -> dict:
    from app.analytics.lineage import find_near_duplicate_images, topic_lineage

    db, truth = built["db"], built["truth"]
    with connect(db) as c:
        tid = c.execute(
            "SELECT ta.topic_id FROM topic_assign ta WHERE ta.post_id LIKE 'rumour_x_%' "
            "GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
    lin = topic_lineage(db, tid[0]) if tid else {"platforms": []}
    first = lin["platforms"][0] if lin["platforms"] else {}
    by_platform = {p["platform"]: p["first_seen"] for p in lin["platforms"]}
    migration = None
    if "telegram" in by_platform and "x" in by_platform:
        migration = (datetime.fromisoformat(by_platform["x"]) - datetime.fromisoformat(by_platform["telegram"])).total_seconds() / 60
    matches = find_near_duplicate_images(db)
    variants = set(truth.get("image_variant_media_ids", {}))
    linked = {m["media_id_b"] for m in matches if m["media_id_a"] == "img_dam_original"} | \
             {m["media_id_a"] for m in matches if m["media_id_b"] == "img_dam_original"}
    return {"earliest_platform": first.get("platform"), "origin_found": first.get("first_post_id") == truth["origin_post_id"],
            "telegram_to_x_minutes": round(migration, 1) if migration is not None else None,
            "image_variants_linked": f"{len(linked & variants)}/{len(variants)}" if variants else None}


def forecast(built: dict) -> dict:
    from app.analytics.forecast import backtest

    return backtest(built["db"])


def evaluate(built: dict) -> dict:
    out = {"pipeline": pipeline(built), "demographics": demographics(built), "graph": graph(built),
           "lineage": lineage(built), "forecast": forecast(built)}
    lines = []
    for k, v in out.items():
        lines += [f"## {k}", "", *md_table([{"metric": m, "value": x} for m, x in v.items()], ["metric", "value"]), ""]
    write_report("components", "Pipeline, demographics, graph, lineage, forecast", lines)
    return out
