import numpy as np
import hashlib
from src.key_generation import generate_keys
from src.permutation import permute, inverse_permute
from src.diffusion import diffuse, inverse_diffuse

class EncryptedImage(np.ndarray):
    """
    A NumPy array subclass that carries the original image's hash 
    and ROIs for plaintext-dependent decryption.
    """
    def __new__(cls, input_array, image_hash=None, rois=None):
        obj = np.asarray(input_array).view(cls)
        obj.image_hash = image_hash
        obj.rois = rois
        return obj
        
    def __array_finalize__(self, obj):
        if obj is None: return
        self.image_hash = getattr(obj, 'image_hash', None)
        self.rois = getattr(obj, 'rois', None)

def encrypt(image, passphrase):
    """
    Encrypts an image using the ChaosCrypt system.
    """
    # Key generation relies on the plaintext image for chosen-plaintext attack resistance
    x0_perm, mu_perm, x0_diff, mu_diff = generate_keys(passphrase, image)
    
    # 1. Permutation
    permuted = permute(image, x0_perm, mu_perm)
    
    # 2. Diffusion
    diffused = diffuse(permuted, x0_diff, mu_diff)
    
    # Compute hash to store with the encrypted image
    image_hash = hashlib.sha256(image.tobytes()).digest()
    
    return EncryptedImage(diffused, image_hash)

def encrypt_selective(image, passphrase):
    """
    Selectively encrypts faces in an image using ChaosCrypt.
    Leaves the rest of the image unencrypted (or skipped).
    """
    from src.roi_detector import detect_faces
    
    faces = detect_faces(image)
    
    encrypted_full = image.copy()
    image_hash = hashlib.sha256(image.tobytes()).digest()
    
    # We encrypt each region with a slightly different derived passphrase or just the same keys
    # To keep it simple, we generate keys based on the whole image and passphrase,
    # but apply them to the cropped regions.
    # Wait, the lengths are different for each crop, so Chaotic sequence will be generated for the crop size.
    x0_perm, mu_perm, x0_diff, mu_diff = generate_keys(passphrase, image)
    
    for (x, y, w, h) in faces:
        crop = image[y:y+h, x:x+w].copy()
        
        # 1. Permutation
        permuted_crop = permute(crop, x0_perm, mu_perm)
        
        # 2. Diffusion
        diffused_crop = diffuse(permuted_crop, x0_diff, mu_diff)
        
        encrypted_full[y:y+h, x:x+w] = diffused_crop
        
    return EncryptedImage(encrypted_full, image_hash, rois=faces)

def decrypt(encrypted_image, passphrase):
    """
    Decrypts a ChaosCrypt encrypted image.
    """
    if not hasattr(encrypted_image, 'image_hash') or encrypted_image.image_hash is None:
        raise ValueError("Encrypted image does not contain the required plaintext hash.")
        
    image_hash = encrypted_image.image_hash
    
    # We need to bypass the standard generate_keys since we don't have the plaintext image
    # We will compute the hashes manually here as done in key_generation.py
    hash_pass = hashlib.sha256(passphrase.encode('utf-8')).digest()
    combined_hash = bytes(a ^ b for a, b in zip(hash_pass, image_hash))
    
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
    
    rois = getattr(encrypted_image, 'rois', None)
    
    if rois is not None:
        decrypted = np.asarray(encrypted_image).copy()
        for (x, y, w, h) in rois:
            crop = decrypted[y:y+h, x:x+w].copy()
            undiffused_crop = inverse_diffuse(crop, x0_diff, mu_diff)
            decrypted_crop = inverse_permute(undiffused_crop, x0_perm, mu_perm)
            decrypted[y:y+h, x:x+w] = decrypted_crop
        return decrypted
    else:
        # 1. Inverse Diffusion
        undiffused = inverse_diffuse(np.asarray(encrypted_image), x0_diff, mu_diff)
        
        # 2. Inverse Permutation
        decrypted = inverse_permute(undiffused, x0_perm, mu_perm)
        
        return decrypted
