import numpy as np
import hashlib
from src.risk_analysis.risk_map import generate_risk_map
from src.key_generation import generate_adaptive_keys
from src.permutation import permute, inverse_permute
from src.diffusion import diffuse, inverse_diffuse

def get_encryption_rounds(risk_level):
    """
    Returns the number of encryption rounds for a given risk level.
    """
    rounds = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3
    }
    return rounds.get(risk_level, 3) # default to highly secure if unknown

def get_deterministic_risk_map_hash(level_matrix):
    """
    Generates a deterministic SHA-256 hash of the risk map levels.
    """
    matrix_str = "".join("".join(row) for row in level_matrix)
    return hashlib.sha256(matrix_str.encode('utf-8')).digest()

def encrypt_adaptive(image, passphrase, grid_size=(4, 4)):
    """
    Encrypts a medical image using Risk-Adaptive Medical Image Encryption (RA-MIE).
    
    Returns a tuple: (encrypted_image_array, metadata)
    - encrypted_image_array: The raw numpy array of the encrypted image.
    - metadata: A dictionary containing non-sensitive data required for decryption.
    """
    # 1. Generate Risk Map
    risk_data = generate_risk_map(image, grid_size=grid_size)
    level_matrix = risk_data['level_matrix']
    y_splits = risk_data['y_splits']
    x_splits = risk_data['x_splits']
    
    # 2. Extract hashes for key derivation
    image_hash = hashlib.sha256(image.tobytes()).digest()
    risk_map_hash = get_deterministic_risk_map_hash(level_matrix)
    
    encrypted_full = image.copy()
    
    rows, cols = grid_size
    region_idx = 0
    
    for i in range(rows):
        for j in range(cols):
            y_start, y_end = y_splits[i], y_splits[i+1]
            x_start, x_end = x_splits[j], x_splits[j+1]
            
            crop = image[y_start:y_end, x_start:x_end].copy()
            
            if crop.size == 0:
                region_idx += 1
                continue
                
            risk_level = level_matrix[i, j]
            rounds = get_encryption_rounds(risk_level)
            
            for r in range(rounds):
                # Generate specific keys for this region and this round
                x0_perm, mu_perm, x0_diff, mu_diff = generate_adaptive_keys(
                    passphrase, image_hash, risk_map_hash, region_idx, r
                )
                
                # Permutation
                crop = permute(crop, x0_perm, mu_perm)
                
                # Diffusion
                crop = diffuse(crop, x0_diff, mu_diff)
                
            encrypted_full[y_start:y_end, x_start:x_end] = crop
            region_idx += 1
            
    # Compile metadata clearly separated from ciphertext
    metadata = {
        'image_hash': image_hash,
        'level_matrix': level_matrix,
        'y_splits': y_splits,
        'x_splits': x_splits,
        'grid_size': grid_size
    }
    
    return encrypted_full, metadata

def decrypt_adaptive(encrypted_image, metadata, passphrase):
    """
    Decrypts a RA-MIE encrypted image using the provided non-sensitive metadata.
    """
    image_hash = metadata['image_hash']
    level_matrix = metadata['level_matrix']
    y_splits = metadata['y_splits']
    x_splits = metadata['x_splits']
    grid_size = metadata['grid_size']
    
    risk_map_hash = get_deterministic_risk_map_hash(level_matrix)
    
    decrypted_full = encrypted_image.copy()
    
    rows, cols = grid_size
    region_idx = 0
    
    for i in range(rows):
        for j in range(cols):
            y_start, y_end = y_splits[i], y_splits[i+1]
            x_start, x_end = x_splits[j], x_splits[j+1]
            
            crop = encrypted_image[y_start:y_end, x_start:x_end].copy()
            
            if crop.size == 0:
                region_idx += 1
                continue
                
            risk_level = level_matrix[i, j]
            rounds = get_encryption_rounds(risk_level)
            
            # Decryption must proceed in reverse order of rounds
            for r in reversed(range(rounds)):
                x0_perm, mu_perm, x0_diff, mu_diff = generate_adaptive_keys(
                    passphrase, image_hash, risk_map_hash, region_idx, r
                )
                
                # Inverse Diffusion
                crop = inverse_diffuse(crop, x0_diff, mu_diff)
                
                # Inverse Permutation
                crop = inverse_permute(crop, x0_perm, mu_perm)
                
            decrypted_full[y_start:y_end, x_start:x_end] = crop
            region_idx += 1
            
    return decrypted_full
