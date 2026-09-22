import os
import io
import zipfile
import cv2
import numpy as np
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_api_roundtrip():
    # 1. Select a test image
    test_img_path = "sample_images/mri/1 no.jpeg"
    assert os.path.exists(test_img_path), "Test image not found"
    
    orig_bgr = cv2.imread(test_img_path)
    
    # 2. Test /encrypt
    with open(test_img_path, "rb") as f:
        enc_resp = client.post(
            "/encrypt",
            files={"image": ("test.jpg", f, "image/jpeg")},
            data={"passphrase": "api_test_password"}
        )
        
    assert enc_resp.status_code == 200
    assert enc_resp.headers["content-type"] == "application/zip"
    
    # 3. Extract the ZIP
    zip_bytes = io.BytesIO(enc_resp.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        enc_img_bytes = zf.read("encrypted.png")
        metadata_bytes = zf.read("metadata.json")
        info_bytes = zf.read("info.json")
        
    import json
    info = json.loads(info_bytes.decode('utf-8'))
    image_id = info['image_id']
    
    # 4. Test /risk-map/{id}
    rm_resp = client.get(f"/risk-map/{image_id}")
    assert rm_resp.status_code == 200
    assert rm_resp.headers["content-type"] == "image/png"
    
    # 5. Test /decrypt
    dec_resp = client.post(
        "/decrypt",
        files={
            "encrypted_image": ("encrypted.png", enc_img_bytes, "image/png"),
            "metadata_file": ("metadata.json", metadata_bytes, "application/json")
        },
        data={"passphrase": "api_test_password"}
    )
    
    assert dec_resp.status_code == 200
    assert dec_resp.headers["content-type"] == "image/png"
    
    # 6. Verify lossless decryption
    dec_np_arr = np.frombuffer(dec_resp.content, np.uint8)
    dec_bgr = cv2.imdecode(dec_np_arr, cv2.IMREAD_COLOR)
    
    assert dec_bgr is not None
    assert np.array_equal(orig_bgr, dec_bgr), "API decryption was not lossless!"
    print("API Round-trip test passed successfully!")

if __name__ == "__main__":
    test_api_roundtrip()
