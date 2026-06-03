"""
Transcription module using faster-whisper
Converts audio to text with word-level timestamps
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import time
from faster_whisper import WhisperModel
from loguru import logger

class MedicalTranscriber:
    """Handles speech-to-text conversion using Whisper"""
    
    def __init__(self, model_size: str = "base", device: str = "cpu", 
                 compute_type: str = "int8"):
        """
        Initialize Whisper model
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: cpu or cuda
            compute_type: int8, float16, etc.
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Load the Whisper model"""
        logger.info(f"Loading Whisper model: {self.model_size} on {self.device}")
        start_time = time.time()
        
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=None  # Download to cache
            )
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe(self, audio_path: str, language: str = "en", 
                  task: str = "transcribe", word_timestamps: bool = True,
                  beam_size: int = 5, best_of: int = 5) -> Dict[str, Any]:
        """
        Transcribe audio file
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., "en", "es")
            task: "transcribe" or "translate"
            word_timestamps: Include word-level timestamps
            beam_size: Beam size for decoding
            best_of: Number of candidates for non-beam decoding
            
        Returns:
            Dictionary with transcription results
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        logger.info(f"Starting transcription: {audio_path}")
        start_time = time.time()
        
        try:
            # Run transcription
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                beam_size=beam_size,
                best_of=best_of,
                word_timestamps=word_timestamps,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(
                    threshold=0.5,
                    min_speech_duration_ms=250,
                    min_silence_duration_ms=100
                )
            )
            
            # Process segments
            all_segments = []
            full_text = []
            
            for segment in segments:
                segment_dict = {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": []
                }
                
                # Add word-level details if available
                if word_timestamps and segment.words:
                    for word in segment.words:
                        segment_dict["words"].append({
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability
                        })
                
                all_segments.append(segment_dict)
                full_text.append(segment.text)
            
            processing_time = time.time() - start_time
            audio_duration = info.duration
            
            result = {
                "success": True,
                "text": " ".join(full_text),
                "segments": all_segments,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": audio_duration,
                "processing_time": processing_time,
                "real_time_factor": processing_time / audio_duration if audio_duration else 0
            }
            
            logger.info(f"Transcription completed in {processing_time:.2f}s "
                       f"(RTF: {result['real_time_factor']:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def transcribe_streaming(self, audio_chunk_generator):
        """
        Transcribe streaming audio (for future implementation)
        """
        raise NotImplementedError("Streaming not implemented in this version")
    
    def get_medical_vocabulary_boost(self) -> List[str]:
        """
        Return common medical terms for vocabulary boosting
        """
        return [
            "hypertension", "diabetes", "metformin", "lisinopril",
            "systolic", "diastolic", "cardiovascular", "respiratory",
            "gastrointestinal", "neurological", "musculoskeletal",
            "psychiatric", "medication", "allergies", "symptoms",
            "diagnosis", "prognosis", "treatment", "follow-up",
            "blood pressure", "heart rate", "temperature", "respiratory rate",
            "myocardial infarction", "congestive heart failure",
            "chronic obstructive pulmonary disease", "deep vein thrombosis",
            "pulmonary embolism", "cerebrovascular accident"
        ]