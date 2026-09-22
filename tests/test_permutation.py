import numpy as np
import pytest
from src.permutation import permute, inverse_permute

def test_permutation_roundtrip_color():
    image = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
    x0, mu = 0.45, 3.8
    
    permuted = permute(image, x0, mu)
    
    # Should not be identically equal to the original
    assert not np.array_equal(image, permuted)
    
    # Should have the same shape and elements (just shuffled)
    assert image.shape == permuted.shape
    assert np.array_equal(np.sort(image, axis=None), np.sort(permuted, axis=None))
    
    restored = inverse_permute(permuted, x0, mu)
    
    # Should be perfectly restored
    np.testing.assert_array_equal(image, restored)

def test_permutation_roundtrip_grayscale():
    image = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
    x0, mu = 0.55, 3.9
    
    permuted = permute(image, x0, mu)
    assert not np.array_equal(image, permuted)
    
    restored = inverse_permute(permuted, x0, mu)
    np.testing.assert_array_equal(image, restored)
