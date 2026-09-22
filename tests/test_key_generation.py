import numpy as np
import pytest
from src.key_generation import generate_keys

def test_key_generation_bounds():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    passphrase = "my_secure_password"
    
    x0_perm, mu_perm, x0_diff, mu_diff = generate_keys(passphrase, image)
    
    assert 0 < x0_perm < 1
    assert 0 < x0_diff < 1
    assert 3.57 <= mu_perm <= 4.0
    assert 3.57 <= mu_diff <= 4.0

def test_key_generation_sensitivity_passphrase():
    image = np.zeros((10, 10), dtype=np.uint8)
    keys1 = generate_keys("pass1", image)
    keys2 = generate_keys("pass2", image)
    
    assert keys1 != keys2

def test_key_generation_sensitivity_image():
    image1 = np.zeros((10, 10), dtype=np.uint8)
    image2 = np.ones((10, 10), dtype=np.uint8)
    passphrase = "password"
    
    keys1 = generate_keys(passphrase, image1)
    keys2 = generate_keys(passphrase, image2)
    
    assert keys1 != keys2
