from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import bcrypt
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from app.database.mongodb import doctors_collection

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

# ----- Pydantic models -----
class DoctorRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    license_number: str
    specialty: str

class DoctorLogin(BaseModel):
    email: EmailStr
    password: str

class DoctorResponse(BaseModel):
    id: str
    full_name: str
    email: str
    license_number: str
    specialty: str

# ----- Helper functions -----
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_doctor(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    doctor = doctors_collection.find_one({"email": email})
    if not doctor:
        raise HTTPException(status_code=401, detail="Doctor not found")
    doctor["_id"] = str(doctor["_id"])
    return doctor

# ----- Endpoints -----
@auth_router.post("/register")
def register(doctor: DoctorRegister):
    if doctors_collection.find_one({"email": doctor.email}):
        raise HTTPException(400, "Email already registered")
    if doctors_collection.find_one({"license_number": doctor.license_number}):
        raise HTTPException(400, "License number already registered")

    doctor_dict = doctor.dict()
    doctor_dict["password"] = hash_password(doctor.password)
    doctor_dict["verified"] = True
    doctor_dict["created_at"] = datetime.utcnow().isoformat()
    result = doctors_collection.insert_one(doctor_dict)
    return {"message": "Doctor registered successfully", "id": str(result.inserted_id)}

@auth_router.post("/login")
def login(doctor: DoctorLogin):
    db_doctor = doctors_collection.find_one({"email": doctor.email})
    if not db_doctor or not verify_password(doctor.password, db_doctor["password"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": db_doctor["email"]})
    return {
        "token": token,
        "doctor": {
            "id": str(db_doctor["_id"]),
            "full_name": db_doctor["full_name"],
            "email": db_doctor["email"],
            "license_number": db_doctor["license_number"],
            "specialty": db_doctor["specialty"]
        }
    }