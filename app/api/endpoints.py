# app/api/endpoints.py
import shutil
import time
import json
from pathlib import Path
from datetime import datetime
from bson.objectid import ObjectId

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.core.pipeline import MedicalScribePipeline
from app.config import settings
from app.utils.report_generator import ReportGenerator
from app.database.mongodb import patients_collection, consultations_collection

router = APIRouter()
pipeline = MedicalScribePipeline()
report_gen = ReportGenerator()

DEFAULT_DOCTOR_EMAIL = "demo@doctor.com"
DEFAULT_DOCTOR_NAME = "Demo Doctor"

def get_or_create_patient(patient_id: str = None, doctor_email: str = DEFAULT_DOCTOR_EMAIL):
    if patient_id:
        patient = patients_collection.find_one({"_id": ObjectId(patient_id), "doctor_email": doctor_email})
        if patient:
            return patient
    new_patient = {
        "first_name": "Unknown",
        "last_name": "Patient",
        "doctor_email": doctor_email,
        "created_at": datetime.utcnow().isoformat()
    }
    result = patients_collection.insert_one(new_patient)
    new_patient["_id"] = result.inserted_id
    return new_patient

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    patient_id: str = None,
    background_tasks: BackgroundTasks = None
):
    allowed_types = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/m4a", "audio/flac"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Unsupported file type. Allowed: {allowed_types}")

    file_path = settings.UPLOAD_DIR / f"{int(time.time())}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        results = pipeline.process_file(str(file_path))
        if not results["success"]:
            raise HTTPException(500, f"Processing failed: {results.get('error')}")

        patient = get_or_create_patient(patient_id, DEFAULT_DOCTOR_EMAIL)
        patient_id = str(patient["_id"])

        consultation_doc = {
            "patient_id": patient_id,
            "doctor_email": DEFAULT_DOCTOR_EMAIL,
            "doctor_name": DEFAULT_DOCTOR_NAME,
            "audio_filename": file.filename,
            "transcript": results["transcription"].get("text", ""),
            "original_soap_json": json.dumps(results["soap_note"].get("soap_parsed", {})),
            "edited_soap_json": None,
            "pdf_path": results["report_path"],
            "duration_minutes": results["audio_info"].get("duration_minutes", 0),
            "created_at": datetime.utcnow().isoformat()
        }
        consultations_collection.insert_one(consultation_doc)

        report_filename = Path(results['report_path']).name
        response = {
            "success": True,
            "audio_info": results["audio_info"],
            "num_speakers": results["diarization"].get("num_speakers", 0),
            "medical_entities_count": len(results["medical_entities"]),
            "soap_note": results["soap_note"].get("soap_parsed", {}),
            "report_url": f"/api/v1/download/{report_filename}",
            "processing_time": results["processing_time"],
            "patient": {
                "id": patient_id,
                "name": f"{patient.get('first_name', 'Unknown')} {patient.get('last_name', '')}"
            }
        }

        if background_tasks:
            background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

        return response

    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(500, str(e))

@router.post("/process-text")
async def process_text(text: str):
    try:
        results = pipeline.process_text(text)
        if not results["success"]:
            raise HTTPException(500, f"Processing failed: {results.get('error')}")
        report_filename = Path(results['report_path']).name
        return {
            "success": True,
            "medical_entities_count": len(results["medical_entities"]),
            "soap_note": results["soap_note"].get("soap_parsed", {}),
            "report_url": f"/api/v1/download/{report_filename}"
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/download/{filename}")
async def download_report(filename: str):
    file_path = settings.REPORT_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, f"Report not found at {file_path}")
    return FileResponse(path=file_path, filename=filename, media_type='application/pdf')

@router.get("/dashboard/stats")
def get_dashboard_stats():
    doctor_email = DEFAULT_DOCTOR_EMAIL
    total_patients = patients_collection.count_documents({"doctor_email": doctor_email})
    total_consultations = consultations_collection.count_documents({"doctor_email": doctor_email})

    recent = list(consultations_collection.find({"doctor_email": doctor_email})
                  .sort("created_at", -1).limit(10))
    recent_list = []
    for c in recent:
        patient = patients_collection.find_one({"_id": ObjectId(c["patient_id"])})
        patient_name = f"{patient.get('first_name', 'Unknown')} {patient.get('last_name', '')}" if patient else "Unknown"
        recent_list.append({
            "patient_name": patient_name,
            "date": c["created_at"],
            "duration": c["duration_minutes"]
        })
    return {
        "total_patients": total_patients,
        "total_consultations": total_consultations,
        "recent_consultations": recent_list
    }

@router.get("/dashboard/patients")
def list_patients():
    patients = list(patients_collection.find({"doctor_email": DEFAULT_DOCTOR_EMAIL}))
    for p in patients:
        p["id"] = str(p["_id"])
        p.pop("_id")
    return patients

@router.post("/dashboard/patients")
def create_patient(patient_data: dict):
    required_fields = ["first_name", "last_name"]
    for field in required_fields:
        if not patient_data.get(field):
            raise HTTPException(400, f"Missing required field: {field}")
    patient_data["doctor_email"] = DEFAULT_DOCTOR_EMAIL
    patient_data["created_at"] = datetime.utcnow().isoformat()
    result = patients_collection.insert_one(patient_data)
    return {"id": str(result.inserted_id), "message": "Patient added"}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}