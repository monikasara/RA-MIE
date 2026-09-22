import numpy as np
import pytest
from src.metrics import calculate_entropy, calculate_npcr, calculate_uaci, calculate_correlation, plot_histogram
from src.cipher import encrypt

def test_entropy():
    # A completely random image should have entropy close to 8.0
    image = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    entropy = calculate_entropy(image)
    assert 7.9 < entropy <= 8.0

def test_npcr_uaci():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Encrypt original
    encrypted1 = encrypt(image, "password")
    
    # Modify one pixel
    image_modified = image.copy()
    image_modified[0, 0, 0] = 1
    
    # Encrypt modified
    encrypted2 = encrypt(image_modified, "password")
    
    # Calculate NPCR and UACI
    npcr = calculate_npcr(np.asarray(encrypted1), np.asarray(encrypted2))
    uaci = calculate_uaci(np.asarray(encrypted1), np.asarray(encrypted2))
    
    # NPCR should be close to 99.6%
    assert npcr > 95.0
    
    # UACI should be close to 33.4%
    assert 20.0 < uaci < 45.0

def test_correlation():
    # A flat image has correlation NaN or 0 (handled as 0 in our code)
    # A gradient image has high correlation
    gradient = np.tile(np.arange(256), (256, 1)).astype(np.uint8)
    corr_h = calculate_correlation(gradient, 'horizontal')
    assert corr_h > 0.9
    
    # A random image has correlation close to 0
    random_img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    corr_rand = calculate_correlation(random_img, 'horizontal')
    assert abs(corr_rand) < 0.1

def test_plot_histogram():
    image = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
    encrypted = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
    
    buf = plot_histogram(image, encrypted)
    
    assert buf is not None
    buf.seek(0)
    header = buf.read(4)
    # PNG magic number
    assert header == b'\x89PNG'
