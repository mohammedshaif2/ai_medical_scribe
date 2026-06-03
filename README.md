ai-medical-scribe/
├── app/
│   ├── api/                  # FastAPI endpoints
│   ├── core/                 # AI pipeline modules
│   ├── database/             # MongoDB connection
│   ├── utils/                # PDF generation, helpers
│   ├── config.py
│   └── main.py
├── data/
│   ├── audio/                # Uploaded audio files
│   ├── reports/              # Generated PDFs
│   └── temp/                 # Temporary processed audio
├── frontend/
│   └── gradio_app.py         # Main UI
├── .env
├── requirements.txt
├── generate_test_audio.py
└── README.mdAcknowledgements
OpenAI Whisper
PyAnnote
Hugging Face Transformers
Ollama
FastAPI
Gradio
python test_audio_pipeline.py


fastapi==0.136.1
uvicorn==0.46.0
pydantic==2.13.4
pydantic-settings==2.14.1
python-dotenv==1.2.2
python-multipart==0.0.28
sqlalchemy==2.0.49
alembic==1.18.4
pymongo==4.17.0
requests==2.34.1
httpx==0.28.1
pandas==2.3.3
numpy==1.26.4
scikit-learn==1.7.2
scipy==1.15.3
matplotlib==3.10.9
fpdf==1.7.2
gradio==6.14.0
torch==2.4.0+cpu
torchaudio==2.4.0+cpu
transformers==4.41.2
faster-whisper==1.2.1
pyannote.audio==3.1.1
librosa==0.11.0
soundfile==0.13.1
speechbrain==0.5.16
huggingface_hub==0.36.2
onnxruntime==1.23.2
onnxruntime-gpu==1.23.2
tensorboard==2.20.0
tqdm==4.67.3
PyYAML==6.0.3
Jinja2==3.1.6
orjson==3.11.9


# ============================================
# AI MEDICAL SCRIBE – COMMANDS (PowerShell)
# ============================================

# 1. Navigate to your project folder
cd D:\final year\ai-medical-scribe

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. (First time only) Install dependencies
pip install -r requirements.txt

# 4. Start MongoDB (if not running as a service)
#    Open a new terminal and run:
mongod

# 5. Start Ollama (if not already running)
#    Open a new terminal and run:
ollama serve

# 6. Generate a test audio file (if you don't have one)
python generate_test_audio.py

# 7. Start FastAPI Backend (keep this terminal open)
python -m app.main
# Backend will be available at: http://localhost:8000
# API docs: http://localhost:8000/docs

# 8. Open a NEW PowerShell terminal and start Gradio Frontend
cd D:\final year\ai-medical-scribe
.\venv\Scripts\Activate.ps1
python frontend\gradio_app.py
# Gradio UI will be at: http://localhost:7860

# 9. Test the application
#    - Open browser to http://localhost:7860
#    - Register / Login
#    - Add a patient in the Dashboard tab
#    - Upload test_consultation.wav in Audio Upload tab
#    - Click "Generate Report"

# 10. (Optional) Test audio processing directly with curl
curl -X POST http://localhost:8000/api/v1/process-text -d "text=Doctor: Hello%0APatient: I have a headache"

# 11. Stop all servers: Press Ctrl+C in each terminal













































































































