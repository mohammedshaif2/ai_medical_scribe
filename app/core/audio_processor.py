"""
Audio processing module
Handles audio loading, preprocessing, and basic operations
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import numpy as np
import soundfile as sf
import librosa
from pydub import AudioSegment
import noisereduce as nr
from loguru import logger

class AudioProcessor:
    """Handle audio file operations and preprocessing"""
    
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac'}
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize audio processor
        
        Args:
            sample_rate: Target sample rate (Whisper expects 16kHz)
        """
        self.sample_rate = sample_rate
        logger.info(f"AudioProcessor initialized with sample rate: {sample_rate}Hz")
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file and convert to numpy array
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (audio_array, sample_rate)
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {file_ext}. Supported: {self.SUPPORTED_FORMATS}")
        
        try:
            # Load with librosa (handles most formats)
            audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            logger.info(f"Loaded audio: {file_path}, duration: {len(audio)/sr:.2f}s")
            return audio, sr
        except Exception as e:
            logger.error(f"Error loading audio with librosa: {e}")
            
            # Fallback to pydub for problematic files
            try:
                audio_segment = AudioSegment.from_file(file_path)
                audio_segment = audio_segment.set_channels(1).set_frame_rate(self.sample_rate)
                samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
                samples = samples / (2**15)  # Convert to float in [-1, 1]
                logger.info(f"Loaded audio with pydub: {file_path}")
                return samples, self.sample_rate
            except Exception as e2:
                logger.error(f"Error loading audio with pydub: {e2}")
                raise RuntimeError(f"Failed to load audio file: {file_path}")
    
    def save_uploaded_file(self, uploaded_file, filename: Optional[str] = None) -> str:
        """
        Save uploaded file to disk
        
        Args:
            uploaded_file: File-like object from upload
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            filename = uploaded_file.name
        
        # Create safe filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        file_path = Path(tempfile.gettempdir()) / safe_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.read())
        
        logger.info(f"Saved uploaded file: {file_path}")
        return str(file_path)
    
    def preprocess_audio(self, audio: np.ndarray, sr: int, 
                        reduce_noise: bool = True) -> np.ndarray:
        """
        Apply preprocessing to improve transcription quality
        
        Args:
            audio: Audio array
            sr: Sample rate
            reduce_noise: Whether to apply noise reduction
            
        Returns:
            Processed audio array
        """
        if reduce_noise:
            # Apply noise reduction
            audio = nr.reduce_noise(y=audio, sr=sr, prop_decrease=0.8)
            logger.info("Applied noise reduction")
        
        # Normalize audio
        if np.abs(audio).max() > 0:
            audio = audio / np.abs(audio).max() * 0.95
        
        return audio
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get audio file metadata
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata
        """
        try:
            audio, sr = self.load_audio(file_path)
            duration = len(audio) / sr
            
            return {
                "filename": Path(file_path).name,
                "duration_seconds": round(duration, 2),
                "duration_minutes": round(duration / 60, 2),
                "sample_rate": sr,
                "samples": len(audio),
                "format": Path(file_path).suffix.lower(),
                "size_bytes": os.path.getsize(file_path)
            }
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return {"error": str(e)}
    
    def split_audio_on_silence(self, audio: np.ndarray, sr: int,
                               min_silence_len: int = 500,
                               silence_thresh: int = -40) -> list:
        """
        Split audio on silence (useful for long recordings)
        
        Args:
            audio: Audio array
            sr: Sample rate
            min_silence_len: Minimum silence length in ms
            silence_thresh: Silence threshold in dB
            
        Returns:
            List of audio segments
        """
        # Convert to pydub for silence detection
        audio_segment = AudioSegment(
            (audio * (2**15)).astype(np.int16).tobytes(),
            frame_rate=sr,
            sample_width=2,
            channels=1
        )
        
        # Split on silence
        chunks = librosa.effects.split(
            audio, 
            top_db=-silence_thresh,
            frame_length=2048,
            hop_length=512
        )
        
        segments = []
        for start, end in chunks:
            segments.append(audio[start:end])
        
        logger.info(f"Split audio into {len(segments)} segments")
        return segments