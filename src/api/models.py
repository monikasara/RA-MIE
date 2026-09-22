import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.api.database import Base

class RoleEnum(str, enum.Enum):
    Admin = "Admin"
    Doctor = "Doctor"
    Patient = "Patient"
    Hospital = "Hospital"

class ActionEnum(str, enum.Enum):
    UPLOAD = "UPLOAD"
    ENCRYPT = "ENCRYPT"
    DECRYPT = "DECRYPT"
    VIEW = "VIEW"
    LOGIN = "LOGIN"

class StatusEnum(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    
    patient_profile = relationship("Patient", back_populates="user", uselist=False)
    access_logs = relationship("AccessLog", back_populates="user")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hospital_id = Column(String, index=True, nullable=True) # E.g., 'HOSP-001'
    dob = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    
    user = relationship("User", back_populates="patient_profile")
    images = relationship("MedicalImage", back_populates="patient")

class MedicalImage(Base):
    __tablename__ = "medical_images"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    secure_storage_path = Column(String, nullable=False) # Path to encrypted file
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    patient = relationship("Patient", back_populates="images")
    risk_analysis = relationship("RiskAnalysis", back_populates="image", uselist=False)
    encryption_record = relationship("EncryptionRecord", back_populates="image", uselist=False)

class RiskAnalysis(Base):
    __tablename__ = "risk_analysis"
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("medical_images.id"), nullable=False)
    low_risk_pct = Column(Float, nullable=False)
    med_risk_pct = Column(Float, nullable=False)
    high_risk_pct = Column(Float, nullable=False)
    risk_map_path = Column(String, nullable=True)
    
    image = relationship("MedicalImage", back_populates="risk_analysis")

class EncryptionRecord(Base):
    __tablename__ = "encryption_records"
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("medical_images.id"), nullable=False)
    encryption_method = Column(String, default="RA-MIE")
    crypto_metadata_json = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    image = relationship("MedicalImage", back_populates="encryption_record")

class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(Enum(ActionEnum), nullable=False)
    resource_type = Column(String, nullable=False) # e.g., 'MedicalImage'
    resource_id = Column(Integer, nullable=True)
    status = Column(Enum(StatusEnum), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="access_logs")
