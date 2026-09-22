from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.models import User, MedicalImage, RiskAnalysis, Patient, RoleEnum, AccessLog
from src.api.auth import require_role

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/")
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.Doctor, RoleEnum.Hospital, RoleEnum.Admin, RoleEnum.Patient]))):
    # Only get patients for this doctor/hospital
    if current_user.role == RoleEnum.Admin:
        images = db.query(MedicalImage).all()
        logs = db.query(AccessLog).order_by(AccessLog.timestamp.desc()).limit(20).all()
    else:
        images = db.query(MedicalImage).filter(MedicalImage.uploaded_by == current_user.id).all()
        logs = db.query(AccessLog).filter(AccessLog.user_id == current_user.id).order_by(AccessLog.timestamp.desc()).limit(20).all()
        
    total_images = len(images)
    avg_low, avg_med, avg_high = 0.0, 0.0, 0.0
    
    recent_activity = []
    
    if total_images > 0:
        for img in images:
            risk = db.query(RiskAnalysis).filter(RiskAnalysis.image_id == img.id).first()
            if risk:
                avg_low += risk.low_risk_pct
                avg_med += risk.med_risk_pct
                avg_high += risk.high_risk_pct
                
        avg_low /= total_images
        avg_med /= total_images
        avg_high /= total_images
        
        recent_images = sorted(images, key=lambda x: str(x.timestamp), reverse=True)[:5]
        for img in recent_images:
            recent_activity.append({
                "patient_id": img.patient_id,
                "filename": img.original_filename,
                "timestamp": str(img.timestamp)
            })
            
    audit_logs = [{
        "action": log.action.value,
        "resource_type": log.resource_type,
        "status": log.status.value,
        "timestamp": str(log.timestamp)
    } for log in logs]
            
    return {
        "user": {
            "username": current_user.username,
            "role": current_user.role.value
        },
        "total_images": total_images,
        "average_risk_levels": {
            "LOW": round(avg_low, 2),
            "MEDIUM": round(avg_med, 2),
            "HIGH": round(avg_high, 2)
        },
        "recent_activity": recent_activity,
        "audit_logs": audit_logs
    }
