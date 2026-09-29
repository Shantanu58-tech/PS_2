from app.analytics.demographics import _infer_state, _infer_interest, _infer_age_bracket


def test_infer_state_city():
    assert _infer_state("Mumbai, Maharashtra") == "maharashtra"
    assert _infer_state("Bangalore") == "karnataka"
    assert _infer_state("Bengaluru") == "karnataka"
    assert _infer_state("Unknown City XYZ") is None


def test_infer_interest():
    assert _infer_interest("Software developer at a startup") == "IT/tech"
    assert _infer_interest("Student, UPSC aspirant") == "student"
    assert _infer_interest("Journalist covering politics") == "journalist/media"


def test_infer_age_bracket_excludes_minors():
    assert _infer_age_bracket("Class 12 student") is None
    assert _infer_age_bracket("B.Tech 2nd yr student") == "18-24"
    assert _infer_age_bracket("Retired IAS officer") == "50+"


def test_k_suppression():
    # Previously a no-op; now checks withheld buckets and the noise floor.
    import numpy as np

    from app.analytics.demographics import release_counts

    released, suppressed = release_counts({"a": 3, "b": 9, "c": 50, "d": 10}, k=10, epsilon=1.0,
                                          rng=np.random.default_rng(0))
    assert suppressed == 2 and set(released) == {"c", "d"}
    assert all(v >= 10 for v in released.values())  # noise never reveals a sub-k count


def test_dp_noise_is_unbiased_and_scaled():
    import numpy as np

    from app.analytics.demographics import release_counts

    rng = np.random.default_rng(1)
    vals = [release_counts({"x": 500}, k=10, epsilon=0.5, rng=rng)[0]["x"] for _ in range(2000)]
    assert abs(np.mean(vals) - 500) < 0.5 and 2.0 < np.std(vals) < 3.8  # Laplace(b=2): sd ~2.83


def test_no_word_boundary_false_matches():
    assert _infer_state("startup founder") is None  # 'up' alias must not match 'startup'
    assert _infer_state("Lives in Navi Mumbai") == "maharashtra"


def test_aggregates_never_hold_sub_k_counts(analysed_db):
    from tests.conftest import rows

    bad = rows(analysed_db, "SELECT * FROM demo_aggregates WHERE bucket != 'suppressed' AND count < 10")
    assert not bad
    dims = {r[0] for r in rows(analysed_db, "SELECT DISTINCT dimension FROM demo_aggregates")}
    assert {"geography", "interests", "language"} <= dims
