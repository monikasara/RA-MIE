import os
import io
import json
import zipfile
import cv2
import numpy as np
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_api_roundtrip():
    print("Testing Personal Mode /encrypt and /decrypt pixel-perfect roundtrip...")
    
    img_path = os.path.abspath("sample_images/mri/1 no.jpeg")
    
    # Read original via cv2 to compare later
    orig_bgr = cv2.imread(img_path)
    
    with open(img_path, "rb") as f:
        img_data = f.read()
    
    # Hack the adaptive_encryption locally to force a HIGH region just for this test
    import src.adaptive_encryption as ae
    original_generate = ae.generate_risk_map
    def mock_generate(*args, **kwargs):
        res = original_generate(*args, **kwargs)
        res['level_matrix'][1, 1] = 'HIGH' # Force HIGH risk
        res['level_matrix'][2, 2] = 'MEDIUM'
        return res
    ae.generate_risk_map = mock_generate
    
    # 1. Encrypt
    resp = client.post(
        "/api/images/encrypt",
        files={"image": ("1 no.jpeg", img_data, "image/jpeg")},
        data={"passphrase": "secretpassword"}
    )
    
    ae.generate_risk_map = original_generate # Restore
    
    assert resp.status_code == 200, f"Encrypt failed: {resp.text}"
    
    zip_bytes = resp.content
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        enc_data = z.read("encrypted.png")
        meta_data = z.read("metadata.json")
    
    # 2. Decrypt
    dec_resp = client.post(
        "/api/images/decrypt",
        files={
            "encrypted_image": ("encrypted.png", enc_data, "image/png"),
            "metadata_file": ("metadata.json", meta_data, "application/json")
        },
        data={"passphrase": "secretpassword"}
    )
    
    assert dec_resp.status_code == 200, f"Decrypt failed: {dec_resp.text}"
    
    # Load decrypted image bytes
    dec_bytes = dec_resp.content
    dec_arr = np.frombuffer(dec_bytes, np.uint8)
    dec_bgr = cv2.imdecode(dec_arr, cv2.IMREAD_COLOR)
    
    is_exact = np.array_equal(orig_bgr, dec_bgr)
    print(f"API Roundtrip Pixel-perfect match? {is_exact}")
    
    if not is_exact:
        diff = np.abs(orig_bgr.astype(int) - dec_bgr.astype(int))
        print(f"Max difference: {np.max(diff)}")
        print("API Roundtrip failed pixel-perfect match.")
        
        # Let's save the decrypted image to inspect
        cv2.imwrite("failed_api_decrypt.png", dec_bgr)

if __name__ == '__main__':
    test_api_roundtrip()
