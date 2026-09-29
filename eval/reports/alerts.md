# Signal Cards and burst detection

Seed 7; 7.0 days. High priority = P >= 70.0.

| metric | value |
|---|---|
| alerts/day (ours, all) | 10.58 |
| alerts/day (ours, high priority) | 0.14 |
| alerts/day (naive keyword z>3) | 35.04 |
| injected rumour alerted at high priority | 1.0 |
| decoy high-priority alerts (ours) | 0 |
| decoy alerts (naive) | 4 |
| our first flag (online Kleinberg, 5-min steps) | 2024-11-07T16:55:00+00:00 |
| naive first flag (end of hourly bucket) | 2024-11-07T17:00:00+00:00 |
| lead time vs naive (min) | 5.0 |

## Gamma sensitivity (larger gamma = fewer bursts)

| gamma | bursts_level>=1 |
|---|---|
| 0.5 | 421 |
| 1.0 | 258 |
| 2.0 | 75 |
| 4.0 | 13 |

Note: topic assignment is computed on the full replay; the online test re-runs Kleinberg on growing prefixes of the rumour topic's timestamps.
