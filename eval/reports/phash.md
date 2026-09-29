# Perceptual-hash lineage: transformation suite

200 generated base images x 6 transforms = 1200 positive pairs; 2000 unrelated pairs. Threshold chosen = highest recall with FPR <= 1%.

| T | recall | fpr |
|---|---|---|
| 0 | 0.5433 | 0.0 |
| 2 | 0.7675 | 0.0 |
| 4 | 0.8317 | 0.0 |
| 6 | 0.8567 | 0.0 |
| 8 | 0.8825 | 0.0 |
| 10 | 0.9042 | 0.0 |
| 12 | 0.9283 | 0.0 |
| 14 | 0.9483 | 0.0015 |
| 16 | 0.9667 | 0.0015 |
| 18 | 0.9758 | 0.0045 |
| 20 | 0.9825 | 0.0085 |
| 22 | 0.9908 | 0.022 |
| 24 | 0.995 | 0.0605 |
| 26 | 0.9983 | 0.142 |
| 28 | 1.0 | 0.28 |
| 30 | 1.0 | 0.4515 |
| 32 | 1.0 | 0.6445 |

Chosen T = 20: recall 0.9825, FPR 0.0085.

| transform | recall |
|---|---|
| blur | 1.0 |
| crop | 0.895 |
| jpeg | 1.0 |
| resize | 1.0 |
| screenshot | 1.0 |
| watermark | 1.0 |
