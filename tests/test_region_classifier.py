from src.risk_analysis.region_classifier import classify_risk_score

def test_classify_risk_score_low():
    assert classify_risk_score(0.0) == "LOW"
    assert classify_risk_score(0.33) == "LOW"
    assert classify_risk_score(0.2) == "LOW"

def test_classify_risk_score_medium():
    assert classify_risk_score(0.34) == "MEDIUM"
    assert classify_risk_score(0.66) == "MEDIUM"
    assert classify_risk_score(0.5) == "MEDIUM"

def test_classify_risk_score_high():
    assert classify_risk_score(0.67) == "HIGH"
    assert classify_risk_score(1.0) == "HIGH"
    assert classify_risk_score(0.8) == "HIGH"

def test_classify_risk_score_out_of_bounds():
    # Defensive testing
    assert classify_risk_score(-0.1) == "LOW"
    assert classify_risk_score(1.1) == "HIGH"
