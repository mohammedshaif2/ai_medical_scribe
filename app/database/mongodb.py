# app/database/mongodb.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "medical_scribe")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
doctors_collection = db["doctors"]
patients_collection = db["patients"]
consultations_collection = db["consultations"]

def init_mongo():
    """
    Create indexes safely.
    - email: unique and required.
    - license_number: unique but only for documents that actually contain a license_number.
      Using sparse=True ignores documents where license_number is missing or null,
      which prevents duplicate key errors from existing null values.
    """
    # Drop the old index if it exists (to avoid conflicts with new definition)
    try:
        doctors_collection.drop_index("license_number_1")
    except Exception:
        pass  # Index may not exist

    # Create indexes
    doctors_collection.create_index("email", unique=True)
    doctors_collection.create_index("license_number", unique=True, sparse=True)

    patients_collection.create_index("doctor_email")
    consultations_collection.create_index("doctor_email")
    consultations_collection.create_index("patient_id")

# Run initialization when module loads
init_mongo()