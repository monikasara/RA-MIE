def classify_risk_score(score):
    """
    Classifies a risk score [0, 1] into a risk level string.
    
    0.00 - 0.33 = LOW
    0.34 - 0.66 = MEDIUM
    0.67 - 1.00 = HIGH
    """
    if score < 0.0:
        return "LOW"
    elif score <= 0.33:
        return "LOW"
    elif score <= 0.66:
        return "MEDIUM"
    else:
        return "HIGH"
