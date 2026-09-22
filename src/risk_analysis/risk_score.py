import numpy as np
import cv2
from src.metrics import calculate_entropy

def calculate_diagnostic_importance(region):
    """
    Calculates diagnostic importance based on edge density (variance of Laplacian).
    This is an explainable image-derived feature for the prototype.
    Returns a normalized value in [0, 1].
    """
    if len(region.shape) == 3:
        gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
    else:
        gray = region
        
    laplacian_var = np.var(cv2.Laplacian(gray, cv2.CV_64F))
    # Normalize with an empirical max threshold of 1000 (values > 1000 clamped to 1.0)
    return min(laplacian_var / 1000.0, 1.0)

def calculate_uncertainty(region):
    """
    Calculates uncertainty based on the Shannon entropy of the region.
    Returns a normalized value in [0, 1].
    """
    if len(region.shape) == 3:
        gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
    else:
        gray = region
    
    entropy = calculate_entropy(gray)
    return min(entropy / 8.0, 1.0)

def calculate_security_threat(region):
    """
    Calculates security threat based on local contrast (standard deviation).
    Regions with high contrast might contain textual data (like patient info).
    Returns a normalized value in [0, 1].
    """
    std_dev = np.std(region)
    # Max possible std dev for 8-bit image is ~127.5
    return min(std_dev / 128.0, 1.0)

def calculate_risk_score(region):
    """
    Calculates the combined normalized risk score [0, 1] for a given region.
    
    Risk Score = 0.5 * Diagnostic Importance + 0.3 * Uncertainty + 0.2 * Security Threat
    
    NOTE: This is an AI-assisted/image-analysis prototype and not a 
    clinically validated diagnostic model.
    """
    diagnostic = calculate_diagnostic_importance(region)
    uncertainty = calculate_uncertainty(region)
    threat = calculate_security_threat(region)
    
    score = 0.5 * diagnostic + 0.3 * uncertainty + 0.2 * threat
    
    return np.clip(score, 0.0, 1.0)
