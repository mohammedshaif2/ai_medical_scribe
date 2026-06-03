"""Database models for patient records and consultations"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

from app.config import settings

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medical_scribe.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    consultations = relationship("Consultation", back_populates="patient")

class Consultation(Base):
    __tablename__ = "consultations"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_name = Column(String, nullable=False)
    doctor_email = Column(String, nullable=True) 
    audio_filename = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    original_soap_json = Column(Text, nullable=True)  # JSON string
    edited_soap_json = Column(Text, nullable=True)   # JSON string
    pdf_path = Column(String, nullable=True)
    duration_minutes = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="consultations")

class DoctorStat(Base):
    __tablename__ = "doctor_stats"
    
    id = Column(Integer, primary_key=True)
    doctor_name = Column(String, unique=True, nullable=False)
    total_time_saved_minutes = Column(Float, default=0)  # based on consultation duration
    last_updated = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()