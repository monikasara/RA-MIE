import os
import io
import zipfile
import json
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_hospital_flow():
    # 1. Register a hospital user
    reg_resp = client.post("/register", data={
        "username": "dr_smith",
        "password": "securepassword",
        "role": "hospital_staff",
        "hospital_id": "HOSP-001"
    })
    assert reg_resp.status_code in [200, 400] # 400 if already exists, which is fine
    
    # 2. Login
    login_resp = client.post("/login", data={
        "username": "dr_smith",
        "password": "securepassword"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Batch Encrypt
    img1_path = "sample_images/mri/1 no.jpeg"
    img2_path = "sample_images/xray/chest_xray_01.jpg"
    
    with open(img1_path, "rb") as f1, open(img2_path, "rb") as f2:
        batch_resp = client.post(
            "/hospital/batch-encrypt",
            headers=headers,
            files=[
                ("images", ("img1.jpg", f1, "image/jpeg")),
                ("images", ("img2.jpg", f2, "image/jpeg"))
            ],
            data={
                "patient_ids": "PAT-101, PAT-102",
                "passphrase": "hospital_secure_key"
            }
        )
        
    assert batch_resp.status_code == 200
    assert batch_resp.headers["content-type"] == "application/zip"
    
    # Verify ZIP contents
    zip_bytes = io.BytesIO(batch_resp.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        namelist = zf.namelist()
        assert "PAT-101_0_encrypted.png" in namelist
        assert "PAT-101_0_metadata.json" in namelist
        assert "PAT-102_1_encrypted.png" in namelist
        assert "PAT-102_1_metadata.json" in namelist
        
    # 4. Check Dashboard
    dash_resp = client.get("/hospital/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    
    dash_data = dash_resp.json()
    assert dash_data["hospital_id"] == "HOSP-001"
    assert dash_data["total_images"] >= 2
    assert len(dash_data["recent_activity"]) >= 2
    print("Hospital flow test passed successfully!")

if __name__ == "__main__":
    test_hospital_flow()
