"""Dashboard statistics and patient management"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models.database import Patient, Consultation, DoctorStat

class DashboardService:
    
    @staticmethod
    def get_doctor_stats(db: Session, doctor_name: str = "Dr. Smith"):
        """Get dashboard stats for a doctor"""
        # Time saved (assuming each minute of consultation saves 2 minutes of documentation)
        total_consultations = db.query(Consultation).filter(
            Consultation.doctor_name == doctor_name
        ).count()
        
        total_audio_duration = db.query(func.sum(Consultation.duration_minutes)).filter(
            Consultation.doctor_name == doctor_name
        ).scalar() or 0
        
        # Estimate: AI saves 70% documentation time
        time_saved_minutes = total_audio_duration * 0.7
        
        # Patients attended this month
        first_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        monthly_patients = db.query(Consultation.patient_id).filter(
            Consultation.doctor_name == doctor_name,
            Consultation.created_at >= first_of_month
        ).distinct().count()
        
        # Total patient records
        total_patients = db.query(Patient).count()
        
        # Recent consultations
        recent = db.query(Consultation).filter(
            Consultation.doctor_name == doctor_name
        ).order_by(Consultation.created_at.desc()).limit(10).all()
        
        recent_list = []
        for c in recent:
            recent_list.append({
                "id": c.id,
                "patient_name": f"{c.patient.first_name} {c.patient.last_name}" if c.patient else "Unknown",
                "doctor_name": c.doctor_name,
                "date": c.created_at.strftime("%Y-%m-%d %H:%M"),
                "duration": c.duration_minutes
            })
        
        return {
            "doctor_name": doctor_name,
            "time_saved_minutes": round(time_saved_minutes, 1),
            "time_saved_hours": round(time_saved_minutes / 60, 1),
            "monthly_patients": monthly_patients,
            "total_patients": total_patients,
            "total_consultations": total_consultations,
            "recent_consultations": recent_list
        }
    
    @staticmethod
    def get_all_patients(db: Session, skip: int = 0, limit: int = 100):
        patients = db.query(Patient).offset(skip).limit(limit).all()
        return [
            {
                "id": p.id,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "date_of_birth": p.date_of_birth,
                "phone": p.phone,
                "email": p.email,
                "created_at": p.created_at.strftime("%Y-%m-%d")
            }
            for p in patients
        ]
    
    @staticmethod
    def create_patient(db: Session, patient_data: dict):
        patient = Patient(**patient_data)
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient
    
    @staticmethod
    def update_patient(db: Session, patient_id: int, patient_data: dict):
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            for key, value in patient_data.items():
                setattr(patient, key, value)
            db.commit()
            db.refresh(patient)
        return patient
    
    @staticmethod
    def delete_patient(db: Session, patient_id: int):
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            db.delete(patient)
            db.commit()
            return True
        return False