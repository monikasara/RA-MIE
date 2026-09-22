import os
import io
import zipfile
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def run_tests():
    print("Testing unauthenticated Personal Mode /encrypt...")
    
    img_path = os.path.abspath("sample_images/mri/1 no.jpeg")
    with open(img_path, "rb") as f:
        img_data = f.read()
    
    # 1. Encrypt (No Auth headers)
    resp = client.post(
        "/api/images/encrypt",
        files={"image": ("1 no.jpeg", img_data, "image/jpeg")},
        data={"passphrase": "secretpassword"}
    )
    
    print(f"Encrypt Request Sent. Status: {resp.status_code}")
    assert resp.status_code == 200, f"Encrypt failed: {resp.text}"
    
    print("Encrypt succeeded. Reading ZIP...")
    zip_bytes = resp.content
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        enc_data = z.read("encrypted.png")
        meta_data = z.read("metadata.json")
    print("ZIP successfully generated and extracted.")
    
    # 2. Decrypt (No Auth headers)
    print("\nTesting unauthenticated Personal Mode /decrypt...")
    dec_resp = client.post(
        "/api/images/decrypt",
        files={
            "encrypted_image": ("encrypted.png", enc_data, "image/png"),
            "metadata_file": ("metadata.json", meta_data, "application/json")
        },
        data={"passphrase": "secretpassword"}
    )
    
    print(f"Decrypt Request Sent. Status: {dec_resp.status_code}")
    assert dec_resp.status_code == 200, f"Decrypt failed: {dec_resp.text}"
    print("Decrypt succeeded! Unauthenticated requests are functioning correctly.")
    
if __name__ == '__main__':
    run_tests()
