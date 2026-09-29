from app.analytics.burst import kleinberg_bursts, burstiness, norm_entropy


def test_burstiness_regular():
    assert abs(burstiness([1.0] * 100)) < 0.05


def test_burstiness_bursty():
    import random
    rng = random.Random(42)
    gaps = [rng.expovariate(1/10) for _ in range(50)] + [rng.expovariate(1/0.1) for _ in range(50)]
    assert burstiness(gaps) > 0


def test_norm_entropy_concentrated():
    assert norm_entropy([60.0] * 100) < 0.5


def test_norm_entropy_order():
    import random
    rng = random.Random(42)
    u = [rng.uniform(1, 86400) for _ in range(200)]
    assert norm_entropy(u) > norm_entropy([60.0] * 200)


def test_kleinberg_detects_burst():
    base = list(range(0, 10000, 200))
    burst = list(range(5000, 5000 + 20 * 5, 5))
    ts = sorted(base + burst)
    results = kleinberg_bursts([float(t) for t in ts], gamma=0.5)
    assert len(results) > 0
    assert max(r.level for r in results) >= 1


def test_kleinberg_no_burst_poisson():
    import random
    rng = random.Random(42)
    ts = []
    t = 0.0
    for _ in range(200):
        t += rng.expovariate(1/300)
        ts.append(t)
    results = kleinberg_bursts(ts, gamma=2.0)
    assert len(results) == 0 or all(r.level <= 2 for r in results)
