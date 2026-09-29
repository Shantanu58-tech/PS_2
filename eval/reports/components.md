# Pipeline, demographics, graph, lineage, forecast

## pipeline

| metric | value |
|---|---|
| records | 37353 |
| ingest_seconds | 68.7 |
| records_per_second | 543.7 |
| analytics_seconds | 323.0 |
| end_to_end_seconds | 391.7 |
| stage_seconds | {'emotions': 133.44, 'edges': 0.06, 'topics': 71.28, 'coordination': 101.93, 'trends': 3.22, 'classify': 0.53, 'demographics': 1.12, 'behaviour': 0.51, 'forecast': 10.18, 'signals': 0.73, 'ots': 0.0} |

## demographics

| metric | value |
|---|---|
| geo_accuracy | 1.0 |
| geo_coverage | 0.8642 |
| age_coverage | 0.2081 |
| released_buckets | 32 |
| suppressed_buckets | 5 |
| released_buckets_below_k | 0 |

## graph

| metric | value |
|---|---|
| nodes | 3275 |
| edges | 12144 |
| bridge_rank | 1 |
| coordinated_in_top20_raw | 0 |
| coordinated_in_top20_organic | 0 |

## lineage

| metric | value |
|---|---|
| earliest_platform | telegram |
| origin_found | True |
| telegram_to_x_minutes | 12.1 |
| image_variants_linked | 4/4 |

## forecast

| metric | value |
|---|---|
| horizon_hours | 6 |
| n_points | 396 |
| mae_naive | 3.513 |
| mae_gbr | 1.414 |
| mae_hawkes | 1.826 |

