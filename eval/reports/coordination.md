# Coordination detector evaluation

Threshold: account score >= 0.7. Weights set on seed 7; headline = held-out seed 11.

## Account-level detection

| seed | method | precision | recall | f1 | tp | fp | fn |
|---|---|---|---|---|---|---|---|
| 7 | ours | 1.0 | 1.0 | 1.0 | 60 | 0 | 0 |
| 7 | baseline_age_ratio | 0.0273 | 0.1333 | 0.0453 | 8 | 285 | 52 |
| 7 | baseline_exact_duplicate | 0.1105 | 1.0 | 0.199 | 60 | 483 | 0 |
| 11 | ours | 0.7059 | 1.0 | 0.8276 | 60 | 25 | 0 |
| 11 | baseline_age_ratio | 0.0059 | 0.0333 | 0.01 | 2 | 337 | 58 |
| 11 | baseline_exact_duplicate | 0.1163 | 1.0 | 0.2083 | 60 | 456 | 0 |

Decoy (cricket + fan-club) accounts flagged on held-out seed: 25 (fan-club: 25)

## Ablation (held-out seed; one weight zeroed at a time)

| variant | precision | recall | f1 | tp | fp | fn |
|---|---|---|---|---|---|---|
| full model | 0.7059 | 1.0 | 0.8276 | 60 | 25 | 0 |
| cluster -sync | 1.0 | 1.0 | 1.0 | 60 | 0 | 0 |
| cluster -1-Hn | 1.0 | 1.0 | 1.0 | 60 | 0 | 0 |
| cluster -max(0,-B) | 0.7059 | 1.0 | 0.8276 | 60 | 25 | 0 |
| cluster -cross_account_dup | 1.0 | 1.0 | 1.0 | 60 | 0 | 0 |
| cluster -regular_share | 0.0 | 0.0 | 0.0 | 0 | 0 | 60 |
| account -co_sync | 1.0 | 0.8167 | 0.8991 | 49 | 0 | 11 |
| account -regularity | 0.7143 | 1.0 | 0.8333 | 60 | 24 | 0 |
| account -repetition | 0.7407 | 1.0 | 0.8511 | 60 | 21 | 0 |
| account -cluster_dup | 0.7059 | 1.0 | 0.8276 | 60 | 25 | 0 |

Limitations: scenario is synthetic; scripted accounts follow one template family. Real campaigns vary cadence and content; expect lower recall on real data.
