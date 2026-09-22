import numpy as np
import pytest
from src.chaotic_engine import generate_logistic_sequence

def test_logistic_sequence_length():
    seq = generate_logistic_sequence(0.5, 3.9, 1000)
    assert len(seq) == 1000

def test_logistic_sequence_bounds():
    seq = generate_logistic_sequence(0.5, 3.9, 1000)
    assert np.all((seq > 0) & (seq < 1))

def test_logistic_sequence_reproducibility():
    seq1 = generate_logistic_sequence(0.5, 3.9, 1000)
    seq2 = generate_logistic_sequence(0.5, 3.9, 1000)
    np.testing.assert_array_equal(seq1, seq2)

def test_logistic_sequence_non_repeating():
    # In chaotic range, the sequence should not be periodic with small period
    # Let's test that all elements are unique (or at least mostly unique)
    seq = generate_logistic_sequence(0.5, 3.99, 1000)
    unique_elements = np.unique(seq)
    assert len(unique_elements) > 990 # Allow for tiny floating point collisions, but it should be chaotic

def test_invalid_parameters():
    with pytest.raises(ValueError):
        generate_logistic_sequence(0.0, 3.9, 100) # x0 <= 0
    with pytest.raises(ValueError):
        generate_logistic_sequence(1.0, 3.9, 100) # x0 >= 1
    with pytest.raises(ValueError):
        generate_logistic_sequence(0.5, 3.5, 100) # mu < 3.57
    with pytest.raises(ValueError):
        generate_logistic_sequence(0.5, 4.1, 100) # mu > 4.0
