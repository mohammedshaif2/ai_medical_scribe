"""
Test audio processing pipeline step by step
Run this to identify exactly where the failure occurs
"""

import os
import sys

def test_step1_ffmpeg():
    """Test if FFmpeg is available"""
    print("\n=== Step 1: Testing FFmpeg ===")
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
        else:
            print("❌ FFmpeg not found. Please install FFmpeg.")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH. Please install FFmpeg.")
        return False

def test_step2_audio_loading():
    """Test if we can load an audio file"""
    print("\n=== Step 2: Testing Audio Loading ===")
    try:
        import librosa
        print("✅ librosa imported")
        
        # Try to load a sample file if exists
        test_file = "test_consultation.wav"
        if os.path.exists(test_file):
            audio, sr = librosa.load(test_file, sr=16000)
            print(f"✅ Successfully loaded {test_file}: {len(audio)} samples at {sr}Hz")
            return True
        else:
            print(f"⚠️ Test file {test_file} not found. Run generate_test_audio.py first.")
            return False
    except Exception as e:
        print(f"❌ Audio loading failed: {e}")
        return False

def test_step3_whisper():
    """Test if Whisper model loads"""
    print("\n=== Step 3: Testing Whisper ===")
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        print("✅ Whisper model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Whisper failed: {e}")
        return False

def test_step4_pyannote():
    """Test if PyAnnote can load with token"""
    print("\n=== Step 4: Testing PyAnnote ===")
    try:
        from pyannote.audio import Pipeline
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        token = os.getenv("HF_TOKEN")
        
        if not token:
            print("❌ HF_TOKEN not found in .env file")
            return False
        
        print("Attempting to load PyAnnote pipeline...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=token
        )
        print("✅ PyAnnote pipeline loaded successfully")
        return True
    except Exception as e:
        print(f"❌ PyAnnote failed: {e}")
        return False

def test_step5_ollama():
    """Test if Ollama is running"""
    print("\n=== Step 5: Testing Ollama ===")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            return True
        else:
            print("❌ Ollama not responding")
            return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("AUDIO PIPELINE DIAGNOSTIC TEST")
    print("="*50)
    
    results = []
    results.append(("FFmpeg", test_step1_ffmpeg()))
    results.append(("Audio Loading", test_step2_audio_loading()))
    results.append(("Whisper", test_step3_whisper()))
    results.append(("PyAnnote", test_step4_pyannote()))
    results.append(("Ollama", test_step5_ollama()))
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    if not results[0][1]:
        print("\n🔧 ACTION REQUIRED: Install FFmpeg (see step 2 above)")
    if not results[3][1]:
        print("\n🔧 ACTION REQUIRED: Check HF_TOKEN in .env and accept PyAnnote licenses at huggingface.co")