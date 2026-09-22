import numpy as np
from src.cipher import encrypt_selective, decrypt

def test_selective_encryption_roundtrip():
    # Use a small test image
    image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    passphrase = "super_secret_password_123"
    
    # Encrypt
    encrypted = encrypt_selective(image, passphrase)
    
    # Decrypt
    decrypted = decrypt(encrypted, passphrase)
    
    # Check that they match exactly
    np.testing.assert_array_equal(image, decrypted)
