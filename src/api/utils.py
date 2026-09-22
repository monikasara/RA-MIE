from sqlalchemy.orm import Session
from src.api.models import AccessLog, ActionEnum, StatusEnum
import mimetypes

def log_action(db: Session, user_id: int, action: ActionEnum, resource_type: str, resource_id: int, status: StatusEnum):
    log_entry = AccessLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status
    )
    db.add(log_entry)
    db.commit()

def validate_image_file(filename: str, content_type: str) -> bool:
    allowed_mimes = ["image/jpeg", "image/png", "image/dicom", "application/dicom"]
    if content_type not in allowed_mimes:
        return False
        
    ext = filename.split('.')[-1].lower()
    allowed_exts = ["jpg", "jpeg", "png", "dcm"]
    if ext not in allowed_exts:
        return False
        
    return True
