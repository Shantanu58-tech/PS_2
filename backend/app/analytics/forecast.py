"""Topic volume forecasting (Backlog B1).

* gbr   - gradient-boosting regressor on lagged hourly counts (lags 1,2,3,6,24
          + hour of day), recursive multi-step, 80% band from residual quantiles.
* hawkes - univariate Hawkes process with exponential kernel
          lambda(t) = mu + sum_i alpha * exp(-beta (t - t_i)), fitted by MLE
          (O(n) recursive likelihood, scipy L-BFGS-B, branching ratio < 1).
          Expected counts come from the fitted intensity: decaying excitation
          of observed events plus the stationary background mu / (1 - n*).

backtest() holds out the last `horizon` hours and reports MAE of both models
against a naive last-value baseline; the eval harness records it.
"""
from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

HORIZON = 6
LAGS = (1, 2, 3, 6, 24)


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))


# -- series ------------------------------------------------------------------
def hourly_series(conn: sqlite3.Connection, topic_id: int) -> tuple[list[datetime], np.ndarray]:
    rows = conn.execute(
        "SELECT bucket_start, count_all FROM topic_series WHERE topic_id=? ORDER BY bucket_start",
        (topic_id,),
    ).fetchall()
    if not rows:
        return [], np.zeros(0)
    counts = {_parse(r[0]): r[1] for r in rows}
    start, end = min(counts), max(counts)
    hours = int((end - start).total_seconds() // 3600) + 1
    idx = [start + timedelta(hours=h) for h in range(hours)]
    return idx, np.array([counts.get(t, 0) for t in idx], dtype=float)


# -- gradient boosting baseline --------------------------------------------------
def _features(y: np.ndarray, t: int, hour: int) -> list[float]:
    return [y[t - lag] if t - lag >= 0 else 0.0 for lag in LAGS] + [
        math.sin(2 * math.pi * hour / 24), math.cos(2 * math.pi * hour / 24)
    ]


def gbr_forecast(times: list[datetime], y: np.ndarray, horizon: int = HORIZON) -> dict:
    from sklearn.ensemble import GradientBoostingRegressor

    if len(y) < 12:
        last = float(y[-1]) if len(y) else 0.0
        return {"pred": [last] * horizon, "lower": [last] * horizon, "upper": [last] * horizon}
    X = [_features(y, t, times[t].hour) for t in range(1, len(y))]
    target = y[1:]
    model = GradientBoostingRegressor(n_estimators=150, max_depth=3, learning_rate=0.05, random_state=7)
    model.fit(X, target)
    resid = target - model.predict(X)
    lo_q, hi_q = np.quantile(resid, [0.1, 0.9])
    hist = list(y)
    preds: list[float] = []
    for h in range(horizon):
        t = len(hist)
        hour = (times[-1] + timedelta(hours=h + 1)).hour
        p = max(0.0, float(model.predict([_features(np.array(hist), t, hour)])[0]))
        preds.append(p)
        hist.append(p)
    return {
        "pred": preds,
        "lower": [max(0.0, p + lo_q) for p in preds],
        "upper": [p + hi_q for p in preds],
    }


# -- Hawkes ----------------------------------------------------------------------
@dataclass
class HawkesFit:
    mu: float
    alpha: float
    beta: float
    loglik: float

    @property
    def branching_ratio(self) -> float:
        return self.alpha / self.beta


def _neg_loglik(params: np.ndarray, t: np.ndarray, T: float) -> float:
    mu, alpha, beta = params
    if mu <= 0 or alpha < 0 or beta <= 0 or alpha >= beta:
        return 1e18
    A = 0.0
    ll = 0.0
    for i in range(len(t)):
        if i > 0:
            A = math.exp(-beta * (t[i] - t[i - 1])) * (1.0 + A)
        ll += math.log(mu + alpha * A)
    ll -= mu * T + (alpha / beta) * float(np.sum(1.0 - np.exp(-beta * (T - t))))
    return -ll


def fit_hawkes(event_hours: np.ndarray, T: float) -> HawkesFit:
    from scipy.optimize import minimize

    t = np.sort(np.asarray(event_hours, dtype=float))
    n = len(t)
    mu0 = max(n / max(T, 1e-6) * 0.5, 1e-3)
    best: HawkesFit | None = None
    for beta0 in (0.5, 2.0, 10.0):
        res = minimize(
            _neg_loglik, x0=np.array([mu0, 0.5 * beta0, beta0]), args=(t, T), method="L-BFGS-B",
            bounds=[(1e-6, None), (0.0, None), (1e-3, 200.0)],
        )
        mu, alpha, beta = res.x
        if alpha >= beta:
            alpha = 0.99 * beta
        fit = HawkesFit(float(mu), float(alpha), float(beta), float(-res.fun))
        if best is None or fit.loglik > best.loglik:
            best = fit
    assert best is not None
    return best


def hawkes_expected_counts(fit: HawkesFit, event_hours: np.ndarray, T: float, horizon: int) -> list[float]:
    t = np.asarray(event_hours, dtype=float)
    n_star = min(fit.branching_ratio, 0.99)
    out = []
    for h in range(horizon):
        a, b = T + h, T + h + 1
        excite = (fit.alpha / fit.beta) * float(
            np.sum(np.exp(-fit.beta * (a - t)) - np.exp(-fit.beta * (b - t)))
        )
        out.append(fit.mu / (1.0 - n_star) + excite)
    return out


def _event_hours(conn: sqlite3.Connection, topic_id: int, t0: datetime) -> np.ndarray:
    rows = conn.execute(
        "SELECT p.created_at FROM topic_assign ta JOIN posts p "
        "ON p.platform=ta.platform AND p.post_id=ta.post_id WHERE ta.topic_id=? ORDER BY p.created_at",
        (topic_id,),
    ).fetchall()
    return np.array([(_parse(r[0]) - t0).total_seconds() / 3600 for r in rows])


def compute_forecasts(db_path: str, horizon: int = HORIZON) -> dict[str, int]:
    now = datetime.now(timezone.utc).isoformat()
    n = 0
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM forecasts")
        for (tid,) in conn.execute("SELECT topic_id FROM topics").fetchall():
            times, y = hourly_series(conn, tid)
            if len(y) == 0:
                continue
            future = [times[-1] + timedelta(hours=h + 1) for h in range(horizon)]
            g = gbr_forecast(times, y, horizon)
            rows = [(tid, "gbr", f.isoformat(), p, lo, hi, now)
                    for f, p, lo, hi in zip(future, g["pred"], g["lower"], g["upper"])]
            ev = _event_hours(conn, tid, times[0])
            if len(ev) >= 10:
                T = float(len(y))
                fit = fit_hawkes(ev, T)
                for f, p in zip(future, hawkes_expected_counts(fit, ev, T, horizon)):
                    rows.append((tid, "hawkes", f.isoformat(), p, None, None, now))
            conn.executemany(
                "INSERT INTO forecasts (topic_id, model, bucket_start, predicted, lower, upper, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                rows,
            )
            n += 1
        conn.commit()
    return {"topics_forecast": n}


def backtest(db_path: str, horizon: int = HORIZON, min_hours: int = 48) -> dict:
    """Hold out the last `horizon` hours of every topic with enough history."""
    errs: dict[str, list[float]] = {"naive": [], "gbr": [], "hawkes": []}
    with sqlite3.connect(db_path) as conn:
        for (tid,) in conn.execute("SELECT topic_id FROM topics").fetchall():
            times, y = hourly_series(conn, tid)
            if len(y) < min_hours + horizon:
                continue
            train_t, train_y, test_y = times[:-horizon], y[:-horizon], y[-horizon:]
            errs["naive"] += list(np.abs(test_y - train_y[-1]))
            errs["gbr"] += list(np.abs(test_y - np.array(gbr_forecast(train_t, train_y, horizon)["pred"])))
            ev = _event_hours(conn, tid, times[0])
            T = float(len(train_y))
            ev_train = ev[ev < T]
            if len(ev_train) >= 10:
                fit = fit_hawkes(ev_train, T)
                errs["hawkes"] += list(np.abs(test_y - np.array(hawkes_expected_counts(fit, ev_train, T, horizon))))
    return {
        "horizon_hours": horizon,
        "n_points": len(errs["naive"]),
        **{f"mae_{k}": (round(float(np.mean(v)), 3) if v else None) for k, v in errs.items()},
    }
