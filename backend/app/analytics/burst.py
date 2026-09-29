from __future__ import annotations
import math
import numpy as np
from dataclasses import dataclass


@dataclass
class BurstResult:
    start_idx: int
    end_idx: int
    level: int
    weight: float


def kleinberg_bursts(
    timestamps: list[float],
    s: float = 2.0,
    gamma: float = 1.0,
) -> list[BurstResult]:
    if len(timestamps) < 3:
        return []
    ts = sorted(set(timestamps))  # deduplicate to avoid zero gaps
    if len(ts) < 3:
        return []
    n = len(ts)
    gaps = [ts[i + 1] - ts[i] for i in range(n - 1)]
    gaps = [max(g, 1e-6) for g in gaps]
    T = ts[-1] - ts[0]
    if T <= 0:
        return []
    g_hat = T / n
    # Use the 5th-percentile gap (robust against near-zero outliers) to
    # determine k, capped at 10 to prevent combinatorial explosion.
    sorted_gaps = sorted(gaps)
    p5_idx = max(0, len(sorted_gaps) // 20)
    min_gap_robust = max(sorted_gaps[p5_idx], 1e-3)
    k = max(2, min(10, math.ceil(math.log(T / min_gap_robust, s)) + 1))

    def alpha(i: int) -> float:
        # Rate for state i: higher states have higher frequency (smaller mean gap).
        # Kleinberg (2002): alpha_i = n / T * s^i = s^i / g_hat
        return (s ** i) / g_hat

    def sigma(i: int, x: float) -> float:
        a = alpha(i)
        return -math.log(a) + a * x

    def tau(i: int, j: int) -> float:
        if j > i:
            return (j - i) * gamma * math.log(n)
        return 0.0

    inf = float("inf")
    cost = [[inf] * k for _ in range(len(gaps))]
    prev_state = [[-1] * k for _ in range(len(gaps))]

    for j in range(k):
        cost[0][j] = sigma(j, gaps[0]) + tau(0, j)

    for t in range(1, len(gaps)):
        for j in range(k):
            best = inf
            best_prev = 0
            for i in range(k):
                c = cost[t - 1][i] + tau(i, j) + sigma(j, gaps[t])
                if c < best:
                    best = c
                    best_prev = i
            cost[t][j] = best
            prev_state[t][j] = best_prev

    last_state = int(np.argmin(cost[-1]))
    states = [0] * len(gaps)
    states[-1] = last_state
    for t in range(len(gaps) - 2, -1, -1):
        states[t] = prev_state[t + 1][states[t + 1]]

    bursts: list[BurstResult] = []
    i = 0
    while i < len(states):
        if states[i] >= 1:
            j = i
            while j < len(states) and states[j] >= 1:
                j += 1
            level = max(states[i:j])
            weight = sum(
                sigma(0, gaps[t]) - sigma(states[t], gaps[t])
                for t in range(i, j)
            ) - sum(tau(states[t], states[t + 1]) for t in range(i, j - 1) if t + 1 < j)
            bursts.append(BurstResult(i, j - 1, level, weight))
            i = j
        else:
            i += 1
    return bursts


def burstiness(gaps: list[float]) -> float:
    arr = np.array(gaps, dtype=float)
    if len(arr) < 2:
        return 0.0
    m = float(np.mean(arr))
    s = float(np.std(arr))
    # Goh-Barabasi: sigma = 0 (perfectly periodic) gives B = -1, not 0.
    denom = s + m
    return (s - m) / denom if denom > 0 else 0.0


def norm_entropy(gaps: list[float], k: int = 12, lo: float = 1.0, hi: float = 86400.0) -> float:
    if len(gaps) < 2:
        return 1.0
    bins = np.logspace(np.log10(lo), np.log10(hi), k + 1)
    arr = np.clip(np.array(gaps, dtype=float), lo, hi)
    p, _ = np.histogram(arr, bins=bins)
    p = p[p > 0].astype(float)
    if p.sum() == 0:
        return 1.0
    p /= p.sum()
    return float(-(p * np.log2(p)).sum() / np.log2(k))
