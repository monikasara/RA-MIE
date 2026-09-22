from fastapi import APIRouter, Depends, HTTPException, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.models import User, Patient, RoleEnum, ActionEnum, StatusEnum
from src.api.auth import get_password_hash, verify_password, create_access_token
from src.api.utils import log_action

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
def register_user(
    username: str = Form(...), 
    password: str = Form(...), 
    role: RoleEnum = Form(...), 
    email: str = Form(None),
    hospital_id: str = Form(None), 
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password, role=role)
    db.add(new_user)
    db.flush() # flush to get new_user.id
    
    if role == RoleEnum.Patient:
        new_patient = Patient(user_id=new_user.id, hospital_id=hospital_id)
        db.add(new_patient)
        
    db.commit()
    
    log_action(db, new_user.id, ActionEnum.LOGIN, "User", new_user.id, StatusEnum.SUCCESS) # Register counts as first action
    return {"message": "User registered successfully"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    if not verify_password(form_data.password, user.password_hash):
        log_action(db, user.id, ActionEnum.LOGIN, "User", user.id, StatusEnum.FAILURE)
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    log_action(db, user.id, ActionEnum.LOGIN, "User", user.id, StatusEnum.SUCCESS)
    
    return {"access_token": access_token, "token_type": "bearer"}
