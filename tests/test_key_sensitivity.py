import numpy as np
import pytest
from src.cipher import encrypt, decrypt

def test_key_sensitivity_decrypt():
    image = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
    passphrase1 = "password123"
    passphrase2 = "password124" # Changed by one character
    
    encrypted = encrypt(image, passphrase1)
    
    # Decrypting with wrong passphrase
    decrypted_wrong = decrypt(encrypted, passphrase2)
    
    # Should not match original image at all
    assert not np.array_equal(image, decrypted_wrong)
    
    # Check that a large portion is different
    diff_pixels = np.sum(image != decrypted_wrong)
    total_pixels = image.size
    assert diff_pixels / total_pixels > 0.95 # >95% of byte values should differ
