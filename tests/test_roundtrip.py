import numpy as np
import pytest
from src.cipher import encrypt, decrypt

def test_cipher_roundtrip():
    # Use a small test image
    image = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
    passphrase = "super_secret_password_123"
    
    # Encrypt
    encrypted = encrypt(image, passphrase)
    
    # Decrypt
    decrypted = decrypt(encrypted, passphrase)
    
    # Check that they match exactly
    np.testing.assert_array_equal(image, decrypted)
    
    # Check that ciphertext is different from plaintext
    assert not np.array_equal(image, encrypted)
