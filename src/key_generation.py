import hashlib
import numpy as np

def generate_keys(passphrase: str, image: np.ndarray):
    """
    Generates chaotic parameters based on a passphrase and the plaintext image.
    
    Args:
        passphrase (str): User-provided passphrase.
        image (np.ndarray): Plaintext image array.
        
    Returns:
        tuple: (x0_perm, mu_perm, x0_diff, mu_diff)
    """
    # 1. Hash the passphrase
    hash_pass = hashlib.sha256(passphrase.encode('utf-8')).digest()
    
    # 2. Hash the raw image bytes
    hash_img = hashlib.sha256(image.tobytes()).digest()
    
    # 3. Combine both hashes (XOR)
    combined_hash = bytes(a ^ b for a, b in zip(hash_pass, hash_img))
    
    # 4. Split into 4 chunks of 8 bytes (64 bits) each
    chunk1 = combined_hash[0:8]
    chunk2 = combined_hash[8:16]
    chunk3 = combined_hash[16:24]
    chunk4 = combined_hash[24:32]
    
    # 5. Convert to valid chaotic parameters
    def bytes_to_float_0_1(b):
        # Convert 8 bytes to uint64
        val = int.from_bytes(b, byteorder='big', signed=False)
        # Map to (0, 1) exclusively
        return (val + 1) / ((1 << 64) + 1)
        
    def bytes_to_float_mu(b):
        # Map to [3.57, 4.0]
        val = int.from_bytes(b, byteorder='big', signed=False)
        # Use (1 << 64) - 1 to allow reaching exactly 4.0 if val is max
        return 3.57 + 0.43 * (val / ((1 << 64) - 1))

    x0_perm = bytes_to_float_0_1(chunk1)
    mu_perm = bytes_to_float_mu(chunk2)
    x0_diff = bytes_to_float_0_1(chunk3)
    mu_diff = bytes_to_float_mu(chunk4)
    
    return x0_perm, mu_perm, x0_diff, mu_diff

def generate_adaptive_keys(passphrase: str, image_hash: bytes, risk_map_hash: bytes, region_idx: int, round_idx: int):
    """
    Generates chaotic parameters for a specific region and encryption round in RA-MIE.
    Uses SHA-256 on (passphrase + image_hash + risk_map_hash + region_idx + round_idx).
    """
    key_material = (
        passphrase.encode('utf-8') + 
        image_hash + 
        risk_map_hash + 
        str(region_idx).encode('utf-8') + 
        str(round_idx).encode('utf-8')
    )
    
    combined_hash = hashlib.sha256(key_material).digest()
    
    chunk1 = combined_hash[0:8]
    chunk2 = combined_hash[8:16]
    chunk3 = combined_hash[16:24]
    chunk4 = combined_hash[24:32]
    
    def bytes_to_float_0_1(b):
        val = int.from_bytes(b, byteorder='big', signed=False)
        return (val + 1) / ((1 << 64) + 1)
        
    def bytes_to_float_mu(b):
        val = int.from_bytes(b, byteorder='big', signed=False)
        return 3.57 + 0.43 * (val / ((1 << 64) - 1))

    x0_perm = bytes_to_float_0_1(chunk1)
    mu_perm = bytes_to_float_mu(chunk2)
    x0_diff = bytes_to_float_0_1(chunk3)
    mu_diff = bytes_to_float_mu(chunk4)
    
    return x0_perm, mu_perm, x0_diff, mu_diff

