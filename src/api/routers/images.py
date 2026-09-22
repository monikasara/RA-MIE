import os
import io
import json
import base64
import zipfile
import cv2
import numpy as np
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
import uuid

from src.api.database import get_db
from src.api.models import User, Patient, MedicalImage, RiskAnalysis, EncryptionRecord, RoleEnum, ActionEnum, StatusEnum
from src.api.auth import get_current_user, require_role
from src.preprocessing import preprocess_image
from src.api.utils import log_action, validate_image_file
from src.adaptive_encryption import encrypt_adaptive, decrypt_adaptive
from src.risk_analysis.risk_map import generate_risk_map

router = APIRouter(prefix="/api/images", tags=["Images"])

SECURE_STORAGE = "results/secure_storage"
CACHE_DIR = "results/api_cache/risk_maps"
os.makedirs(SECURE_STORAGE, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

@router.post("/encrypt")
async def encrypt_single(image: UploadFile = File(...), passphrase: str = Form(...)):
    # Legacy personal mode without DB requirement
    if not validate_image_file(image.filename, image.content_type):
        raise HTTPException(status_code=400, detail="Invalid image file format")
        
    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid image file format")
        
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_rgb = preprocess_image(img_rgb, target_size=(512, 512))
    enc_img, metadata = encrypt_adaptive(img_rgb, passphrase, grid_size=(4, 4))
    
    image_id = str(uuid.uuid4())
    generate_risk_map(img_rgb, grid_size=(4, 4), save_dir=CACHE_DIR)
    
    default_rm = os.path.join(CACHE_DIR, "risk_map.png")
    target_rm = os.path.join(CACHE_DIR, f"{image_id}.png")
    if os.path.exists(default_rm):
        os.replace(default_rm, target_rm)
        
    enc_bgr = cv2.cvtColor(enc_img, cv2.COLOR_RGB2BGR)
    _, enc_buffer = cv2.imencode('.png', enc_bgr)
    
    levels = metadata['level_matrix']
    total = levels.size
    low_pct = f"{(np.sum(levels == 'LOW') / total * 100):.2f}"
    med_pct = f"{(np.sum(levels == 'MEDIUM') / total * 100):.2f}"
    high_pct = f"{(np.sum(levels == 'HIGH') / total * 100):.2f}"
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        zf.writestr('encrypted.png', enc_buffer.tobytes())
        zf.writestr('metadata.json', json.dumps(serialize_metadata(metadata)))
        zf.writestr('info.json', json.dumps({"image_id": image_id}))
        
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip", 
        headers={
            "Content-Disposition": f"attachment; filename=ramie_encrypted_{image_id}.zip",
            "X-Image-ID": image_id,
            "X-Risk-Low": low_pct,
            "X-Risk-Medium": med_pct,
            "X-Risk-High": high_pct,
            "Access-Control-Expose-Headers": "X-Image-ID, X-Risk-Low, X-Risk-Medium, X-Risk-High"
        }
    )

@router.get("/risk-map/{image_id}")
async def get_risk_map(image_id: str):
    target_rm = os.path.join(CACHE_DIR, f"{image_id}.png")
    if not os.path.exists(target_rm):
        raise HTTPException(status_code=404, detail="Risk map not found")
    return FileResponse(target_rm, media_type="image/png")

def serialize_metadata(metadata):
    return {
        'image_hash': base64.b64encode(metadata['image_hash']).decode('utf-8'),
        'level_matrix': metadata['level_matrix'].tolist(),
        'y_splits': metadata['y_splits'].tolist(),
        'x_splits': metadata['x_splits'].tolist(),
        'grid_size': list(metadata['grid_size'])
    }

def deserialize_metadata(data):
    return {
        'image_hash': base64.b64decode(data['image_hash']),
        'level_matrix': np.array(data['level_matrix'], dtype=object),
        'y_splits': np.array(data['y_splits'], dtype=int),
        'x_splits': np.array(data['x_splits'], dtype=int),
        'grid_size': tuple(data['grid_size'])
    }

@router.post("/hospital/batch-encrypt")
async def batch_encrypt(
    images: List[UploadFile] = File(...), 
    patient_ids: str = Form(...), # Comma separated
    passphrase: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.Doctor, RoleEnum.Hospital, RoleEnum.Admin]))
):
    pid_list = [pid.strip() for pid in patient_ids.split(',')]
    if len(pid_list) != len(images):
        raise HTTPException(status_code=400, detail="Number of patient IDs must match number of images")
        
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for idx, (img_file, pid_str) in enumerate(zip(images, pid_list)):
            if not validate_image_file(img_file.filename, img_file.content_type):
                continue
                
            contents = await img_file.read()
            # Enforce size limit (e.g. 50MB)
            if len(contents) > 50 * 1024 * 1024:
                continue
                
            np_arr = np.frombuffer(contents, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                continue
                
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            
            # Resolve Patient ID (Create if doesn't exist for Hospital workflow)
            try:
                pid = int(pid_str)
                patient = db.query(Patient).filter(Patient.id == pid).first()
            except ValueError:
                patient = None
                
            if not patient:
                raise HTTPException(status_code=404, detail=f"Patient ID {pid_str} not found")
            
            # 1. Store Original Image Record
            secure_filename = f"{pid}_{img_file.filename}"
            secure_path = os.path.join(SECURE_STORAGE, secure_filename)
            
            med_img = MedicalImage(
                patient_id=patient.id,
                uploaded_by=current_user.id,
                original_filename=img_file.filename,
                mime_type=img_file.content_type,
                file_size=len(contents),
                secure_storage_path=secure_path
            )
            db.add(med_img)
            db.flush() # get med_img.id
            log_action(db, current_user.id, ActionEnum.UPLOAD, "MedicalImage", med_img.id, StatusEnum.SUCCESS)
            
            # 2. Risk Analysis & Encryption
            img_rgb = preprocess_image(img_rgb, target_size=(512, 512))
            enc_img, metadata = encrypt_adaptive(img_rgb, passphrase, grid_size=(4, 4))
            
            levels = metadata['level_matrix']
            total = levels.size
            low = float(np.sum(levels == 'LOW') / total * 100)
            med = float(np.sum(levels == 'MEDIUM') / total * 100)
            high = float(np.sum(levels == 'HIGH') / total * 100)
            
            risk_record = RiskAnalysis(
                image_id=med_img.id,
                low_risk_pct=low,
                med_risk_pct=med,
                high_risk_pct=high
            )
            db.add(risk_record)
            
            # 3. Encryption Record
            enc_record = EncryptionRecord(
                image_id=med_img.id,
                encryption_method="RA-MIE",
                crypto_metadata_json=json.dumps(serialize_metadata(metadata))
            )
            db.add(enc_record)
            log_action(db, current_user.id, ActionEnum.ENCRYPT, "MedicalImage", med_img.id, StatusEnum.SUCCESS)
            
            # Add to ZIP
            enc_bgr = cv2.cvtColor(enc_img, cv2.COLOR_RGB2BGR)
            _, enc_buffer = cv2.imencode('.png', enc_bgr)
            
            # Save physically to secure storage (mock secure storage)
            with open(secure_path, "wb") as sf:
                sf.write(enc_buffer.tobytes())
                
            zf.writestr(f'{pid}_{idx}_encrypted.png', enc_buffer.tobytes())
            zf.writestr(f'{pid}_{idx}_metadata.json', enc_record.crypto_metadata_json)

    db.commit()
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip", 
        headers={"Content-Disposition": "attachment; filename=hospital_batch_encrypted.zip"}
    )

@router.post("/decrypt")
async def decrypt_image(
    encrypted_image: UploadFile = File(...), 
    metadata_file: UploadFile = File(...), 
    passphrase: str = Form(...)
):
    # Personal mode unauthenticated decryption
    img_contents = await encrypted_image.read()
    np_arr = np.frombuffer(img_contents, np.uint8)
    enc_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if enc_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid encrypted image file format")
        
    enc_rgb = cv2.cvtColor(enc_bgr, cv2.COLOR_BGR2RGB)
    
    meta_contents = await metadata_file.read()
    try:
        meta_dict = json.loads(meta_contents.decode('utf-8'))
        metadata = deserialize_metadata(meta_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {str(e)}")
        
    # Decrypt
    try:
        dec_img = decrypt_adaptive(enc_rgb, metadata, passphrase)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Decryption failed (wrong passphrase or corrupted data)")
    
    dec_bgr = cv2.cvtColor(dec_img, cv2.COLOR_RGB2BGR)
    _, dec_buffer = cv2.imencode('.png', dec_bgr)
    
    return StreamingResponse(
        io.BytesIO(dec_buffer.tobytes()), 
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=ramie_decrypted.png"}
    )
