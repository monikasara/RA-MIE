import numpy as np
import pytest
from src.diffusion import diffuse, inverse_diffuse

def test_diffusion_roundtrip():
    image = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
    x0, mu = 0.35, 3.85
    
    diffused = diffuse(image, x0, mu)
    
    # Should not be identical
    assert not np.array_equal(image, diffused)
    assert image.shape == diffused.shape
    
    restored = inverse_diffuse(diffused, x0, mu)
    
    np.testing.assert_array_equal(image, restored)

def test_diffusion_avalanche_effect():
    image1 = np.zeros((10, 10), dtype=np.uint8)
    image2 = np.zeros((10, 10), dtype=np.uint8)
    image2[0, 0] = 1 # Change one pixel
    
    x0, mu = 0.35, 3.85
    
    diffused1 = diffuse(image1, x0, mu)
    diffused2 = diffuse(image2, x0, mu)
    
    # Because of CBC style, changing the first byte should cascade and change many bytes
    difference = np.sum(diffused1 != diffused2)
    assert difference > 50 # At least half the image should change
