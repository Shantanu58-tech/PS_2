"""Hawkes MLE recovers parameters on simulated data; GBR forecast shape."""
import math
import random
from datetime import datetime, timedelta, timezone

import numpy as np

from app.analytics.forecast import fit_hawkes, gbr_forecast, hawkes_expected_counts


def simulate_hawkes(mu: float, alpha: float, beta: float, T: float, seed: int = 1) -> np.ndarray:
    """Ogata thinning."""
    rng = random.Random(seed)
    t, events = 0.0, []
    while t < T:
        lam_bar = mu + sum(alpha * math.exp(-beta * (t - s)) for s in events[-200:]) + alpha
        t += rng.expovariate(lam_bar)
        lam_t = mu + sum(alpha * math.exp(-beta * (t - s)) for s in events[-200:])
        if t < T and rng.random() <= lam_t / lam_bar:
            events.append(t)
    return np.array(events)


def test_hawkes_mle_recovers_branching_ratio():
    ev = simulate_hawkes(mu=2.0, alpha=1.2, beta=2.0, T=300)
    fit = fit_hawkes(ev, 300)
    assert 0.35 <= fit.branching_ratio <= 0.85  # true 0.6
    assert 1.0 <= fit.mu <= 3.2  # true 2.0
    pred = hawkes_expected_counts(fit, ev, 300, 3)
    assert all(p > 0 for p in pred)


def test_gbr_forecast_shape_and_band():
    times = [datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=h) for h in range(72)]
    y = np.array([10 + 5 * math.sin(2 * math.pi * h / 24) for h in range(72)])
    f = gbr_forecast(times, y, horizon=6)
    assert len(f["pred"]) == 6
    assert all(lo <= p <= hi for lo, p, hi in zip(f["lower"], f["pred"], f["upper"]))
    assert abs(f["pred"][0] - (10 + 5 * math.sin(2 * math.pi * 72 / 24))) < 3
