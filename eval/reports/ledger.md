# Evidence ledger evaluation

Single-character mutations of one random field of one random record, 1000 trials (scratch copy; append-only triggers dropped on the copy only).

| trials | detected | detection_rate | localized_at_seq_rate |
|---|---|---|---|
| 1000 | 1000 | 1.0 | 1.0 |

| field | detected/trials |
|---|---|
| payload_canonical | 184/184 |
| record_hash | 170/170 |
| entry_hash | 147/147 |
| prev_entry_hash | 175/175 |
| collected_at | 160/160 |
| collector_id | 164/164 |

## Verification time

| records | write_seconds | verify_seconds | status |
|---|---|---|---|
| 10000 | 0.29 | 0.09 | PASS |
| 100000 | 3.26 | 1.33 | PASS |
