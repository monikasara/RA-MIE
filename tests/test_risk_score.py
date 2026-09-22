import numpy as np
from src.risk_analysis.risk_score import (
    calculate_diagnostic_importance,
    calculate_uncertainty,
    calculate_security_threat,
    calculate_risk_score
)

def test_diagnostic_importance_bounds():
    region = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
    val = calculate_diagnostic_importance(region)
    assert 0.0 <= val <= 1.0

def test_uncertainty_bounds():
    region = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
    val = calculate_uncertainty(region)
    assert 0.0 <= val <= 1.0

def test_security_threat_bounds():
    region = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
    val = calculate_security_threat(region)
    assert 0.0 <= val <= 1.0

def test_risk_score_bounds():
    region = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
    score = calculate_risk_score(region)
    assert 0.0 <= score <= 1.0
    
def test_risk_score_flat_region():
    # A completely flat region should have low scores
    region = np.zeros((50, 50), dtype=np.uint8)
    score = calculate_risk_score(region)
    assert score == 0.0
