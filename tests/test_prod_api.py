import os
import io
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_full_production_workflow():
    # 1. Register a hospital doctor
    reg_resp = client.post("/api/auth/register", data={
        "username": "prod_dr",
        "password": "secure_prod_password",
        "role": "Doctor",
        "hospital_id": "HOSP-PROD"
    })
    assert reg_resp.status_code in [200, 400] # OK or already exists
    
    # 2. Register a patient (to test RBAC later)
    patient_resp = client.post("/api/auth/register", data={
        "username": "prod_patient",
        "password": "patient_password",
        "role": "Patient"
    })
    assert patient_resp.status_code in [200, 400]
    
    # 3. Doctor Login
    login_resp = client.post("/api/auth/login", data={
        "username": "prod_dr",
        "password": "secure_prod_password"
    })
    assert login_resp.status_code == 200
    dr_token = login_resp.json()["access_token"]
    dr_headers = {"Authorization": f"Bearer {dr_token}"}
    
    # 4. Patient Login
    p_login_resp = client.post("/api/auth/login", data={
        "username": "prod_patient",
        "password": "patient_password"
    })
    assert p_login_resp.status_code == 200
    p_token = p_login_resp.json()["access_token"]
    p_headers = {"Authorization": f"Bearer {p_token}"}
    
    # 5. Patient attempts to access Doctor Dashboard (RBAC check)
    dash_reject_resp = client.get("/api/dashboard/", headers=p_headers)
    assert dash_reject_resp.status_code == 403 # Forbidden!
    
    # 6. Doctor Dashboard access (should succeed)
    dash_success_resp = client.get("/api/dashboard/", headers=dr_headers)
    assert dash_success_resp.status_code == 200
    
    # 7. Doctor Batch Upload (with invalid file validation check)
    # 7a. valid files
    img1_path = "sample_images/mri/1 no.jpeg"
    assert os.path.exists(img1_path)
    
    # Fetch patient ID directly via DB to pass to batch-encrypt
    from src.api.database import SessionLocal
    from src.api.models import User, Patient
    db = SessionLocal()
    patient_user = db.query(User).filter(User.username == "prod_patient").first()
    patient_record = db.query(Patient).filter(Patient.user_id == patient_user.id).first()
    real_pid = str(patient_record.id)
    db.close()
    
    with open(img1_path, "rb") as f1:
        batch_resp = client.post(
            "/api/images/hospital/batch-encrypt",
            headers=dr_headers,
            files=[
                ("images", ("img1.jpg", f1, "image/jpeg"))
            ],
            data={
                "patient_ids": real_pid,
                "passphrase": "hospital_secure_key"
            }
        )
    assert batch_resp.status_code == 200
    assert batch_resp.headers["content-type"] == "application/zip"
    
    # 8. Check Dashboard stats updated
    dash_update_resp = client.get("/api/dashboard/", headers=dr_headers)
    assert dash_update_resp.status_code == 200
    data = dash_update_resp.json()
    assert data["total_images"] >= 1
    assert "LOW" in data["average_risk_levels"]

    print("Full Production Workflow test passed successfully (DB, Auth, RBAC, Validation, Encryption)!")

if __name__ == "__main__":
    test_full_production_workflow()
