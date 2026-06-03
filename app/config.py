"""
Configuration module for AI Medical Scribe
Loads settings from environment variables
"""

import os
from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "AI Medical Scribe")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-secret-key-change")
    
    # Model Settings
    WHISPER_MODEL_SIZE: Literal["tiny", "base", "small", "medium", "large"] = \
        os.getenv("WHISPER_MODEL_SIZE", "base")
    DIARIZATION_MODEL: str = os.getenv(
        "DIARIZATION_MODEL", 
        "pyannote/speaker-diarization-community-1"   # Changed from -3.1
    )
    LLM_MODEL: str = os.getenv("LLM_MODEL", "meditron")
    DEVICE: str = os.getenv("DEVICE", "cpu")
    
    # API Keys
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    
    # File Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "audio"
    REPORT_DIR: Path = BASE_DIR / "data" / "reports"
    TEMP_DIR: Path = BASE_DIR / "data" / "temp"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Validate HF_TOKEN is present for diarization
        if not self.HF_TOKEN:
            print("⚠️  WARNING: HF_TOKEN not set. Speaker diarization will fail.")
            print("Get your free token at: https://huggingface.co/settings/tokens")

# Create global settings instance
settings = Settings()  