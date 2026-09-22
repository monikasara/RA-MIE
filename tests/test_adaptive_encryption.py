import numpy as np
import pytest
import hashlib
from src.adaptive_encryption import encrypt_adaptive, decrypt_adaptive, get_encryption_rounds, get_deterministic_risk_map_hash
from src.key_generation import generate_adaptive_keys

def test_get_encryption_rounds():
    assert get_encryption_rounds("LOW") == 1
    assert get_encryption_rounds("MEDIUM") == 2
    assert get_encryption_rounds("HIGH") == 3
    assert get_encryption_rounds("UNKNOWN") == 3 # Default secure fallback

def test_adaptive_encryption_roundtrip_rgb():
    image = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    passphrase = "medical_password"
    
    encrypted, metadata = encrypt_adaptive(image, passphrase, grid_size=(2, 2))
    
    # 4. All regions encrypted / 5. Encryption changes the image
    assert not np.array_equal(image, encrypted)
    diff_pixels = np.sum(image != encrypted)
    assert diff_pixels / image.size > 0.5 # Substantial change
    
    # 6. Correct password decrypts / 10. Encryption -> decryption returns original
    decrypted = decrypt_adaptive(encrypted, metadata, passphrase)
    np.testing.assert_array_equal(image, decrypted)

def test_adaptive_encryption_roundtrip_grayscale():
    image = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
    passphrase = "medical_password"
    
    encrypted, metadata = encrypt_adaptive(image, passphrase, grid_size=(2, 2))
    assert not np.array_equal(image, encrypted)
    
    decrypted = decrypt_adaptive(encrypted, metadata, passphrase)
    np.testing.assert_array_equal(image, decrypted)

def test_wrong_password_fails():
    image = np.random.randint(0, 256, (32, 32), dtype=np.uint8)
    passphrase1 = "correct_password"
    passphrase2 = "wrong_password"
    
    encrypted, metadata = encrypt_adaptive(image, passphrase1)
    decrypted_wrong = decrypt_adaptive(encrypted, metadata, passphrase2)
    
    # 7. Wrong password fails (does not return original image)
    assert not np.array_equal(image, decrypted_wrong)

def test_key_sensitivity_inputs():
    image1_hash = hashlib.sha256(b"image1").digest()
    image2_hash = hashlib.sha256(b"image2").digest()
    
    risk_map1 = np.array([["LOW", "HIGH"], ["MEDIUM", "LOW"]], dtype=object)
    risk_map2 = np.array([["LOW", "LOW"], ["MEDIUM", "LOW"]], dtype=object)
    
    rm_hash1 = get_deterministic_risk_map_hash(risk_map1)
    rm_hash2 = get_deterministic_risk_map_hash(risk_map2)
    
    # Base Keys
    keys1 = generate_adaptive_keys("pass1", image1_hash, rm_hash1, 0, 0)
    
    # Password A -> Key A, Password B -> Key B
    keys2 = generate_adaptive_keys("pass2", image1_hash, rm_hash1, 0, 0)
    assert keys1 != keys2
    
    # Image A -> Key A, Image B -> Key B
    keys3 = generate_adaptive_keys("pass1", image2_hash, rm_hash1, 0, 0)
    assert keys1 != keys3
    
    # Risk Map A -> Key A, Risk Map B -> Key B
    keys4 = generate_adaptive_keys("pass1", image1_hash, rm_hash2, 0, 0)
    assert keys1 != keys4
