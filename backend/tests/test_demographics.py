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
    from app.analytics.demographics import compute_demographics
    pass
