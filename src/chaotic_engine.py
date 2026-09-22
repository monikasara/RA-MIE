import numpy as np

def generate_logistic_sequence(x0, mu, length, transient=500):
    """
    Generates a chaotic sequence using the logistic map.
    
    Args:
        x0 (float): Initial value, 0 < x0 < 1.
        mu (float): Control parameter, 3.57 <= mu <= 4.0.
        length (int): Desired length of the output sequence.
        transient (int): Number of initial iterations to discard.
        
    Returns:
        np.ndarray: A 1D numpy array of the chaotic sequence.
    """
    if not (0 < x0 < 1):
        raise ValueError("Initial value x0 must be in range (0, 1).")
    if not (3.57 <= mu <= 4.0):
        raise ValueError("Parameter mu must be in range [3.57, 4.0].")
    if length <= 0:
        raise ValueError("Length must be a positive integer.")

    total_length = length + transient
    # Pre-allocate list for massive speedup over numpy array indexing in pure Python loops
    sequence = [0.0] * total_length
    sequence[0] = x0
    x = x0
    
    for i in range(1, total_length):
        x = mu * x * (1.0 - x)
        sequence[i] = x
        
    return np.array(sequence[transient:], dtype=np.float64)
