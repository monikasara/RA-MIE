import cv2
import numpy as np
import os
import json
from src.adaptive_encryption import encrypt_adaptive, decrypt_adaptive
from src.api.routers.images import serialize_metadata, deserialize_metadata

def test_roundtrip():
    # Load sample image
    img_path = os.path.abspath("sample_images/mri/1 no.jpeg")
    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        print("Failed to load sample image.")
        return
        
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    passphrase = "test_passphrase_123!"
    
    print("Encrypting image...")
    # Hack the adaptive_encryption locally to force a HIGH region just for this test
    import src.adaptive_encryption as ae
    original_generate = ae.generate_risk_map
    def mock_generate(*args, **kwargs):
        res = original_generate(*args, **kwargs)
        res['level_matrix'][1, 1] = 'HIGH' # Force HIGH risk
        res['level_matrix'][2, 2] = 'MEDIUM'
        return res
    ae.generate_risk_map = mock_generate
    
    enc_img, metadata = encrypt_adaptive(img_rgb, passphrase, grid_size=(4, 4))
    
    ae.generate_risk_map = original_generate # Restore
    
    print("Decrypting immediately with raw metadata...")
    dec_img = decrypt_adaptive(enc_img, metadata, passphrase)
    
    # Compare
    is_exact = np.array_equal(img_rgb, dec_img)
    print(f"Step 1 (Raw Metadata) Pixel-perfect match? {is_exact}")
    
    if not is_exact:
        print("Core crypto logic has a bug. Step 1 failed.")
        diff = np.abs(img_rgb.astype(int) - dec_img.astype(int))
        print(f"Max difference: {np.max(diff)}")
        return
        
    print("\nStep 1 passed! Core crypto is fine.")
    print("Testing Step 2: Serialization/Deserialization...")
    
    # Serialize to dict (simulating what goes into JSON)
    meta_serialized = serialize_metadata(metadata)
    
    # Simulate saving to and reading from JSON
    json_str = json.dumps(meta_serialized)
    meta_loaded_dict = json.loads(json_str)
    
    # Deserialize back to numpy structures
    metadata_restored = deserialize_metadata(meta_loaded_dict)
    
    print("Decrypting with restored metadata...")
    dec_img_restored = decrypt_adaptive(enc_img, metadata_restored, passphrase)
    
    is_exact_restored = np.array_equal(img_rgb, dec_img_restored)
    print(f"Step 2 (Restored Metadata) Pixel-perfect match? {is_exact_restored}")
    
    if True: # Always print the arrays as requested by the user
        print("\n--- METADATA DIFF ANALYSIS ---")
        for key in metadata:
            orig = metadata[key]
            rest = metadata_restored[key]
            
            if isinstance(orig, np.ndarray):
                match = np.array_equal(orig, rest)
                print(f"\nKey '{key}': ndarray match? {match}")
                print(f"  Original ({orig.dtype}):\n{orig}")
                print(f"  Restored ({rest.dtype}):\n{rest}")
            else:
                match = (orig == rest)
                print(f"\nKey '{key}': value match? {match}")
                print(f"  Original: {orig}")
                print(f"  Restored: {rest}")
        print("------------------------------\n")
        
    if not is_exact_restored:
        print("Serialization/Deserialization logic has a bug. Step 2 failed.")
    else:
        print("Step 2 passed. Metadata serialization is fine.")

if __name__ == "__main__":
    test_roundtrip()
