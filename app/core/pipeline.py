"""
Main orchestration pipeline
Connects all modules into a single workflow
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import time
import json
from loguru import logger

from app.config import settings
from app.core.audio_processor import AudioProcessor
from app.core.transcriber import MedicalTranscriber
from app.core.diarizer import SpeakerDiarizer
from app.core.llm_generator import SOAPNoteGenerator
from app.core.medical_ner import MedicalNER
from app.utils.report_generator import ReportGenerator

class MedicalScribePipeline:
    """Main pipeline orchestrating all components"""
    
    def __init__(self):
        """Initialize all pipeline components"""
        logger.info("Initializing Medical Scribe Pipeline...")
        
        # Initialize components
        self.audio_processor = AudioProcessor(sample_rate=16000)
        
        self.transcriber = MedicalTranscriber(
            model_size=settings.WHISPER_MODEL_SIZE,
            device=settings.DEVICE
        )
        
        self.diarizer = SpeakerDiarizer(
            model_name=settings.DIARIZATION_MODEL,
            device=settings.DEVICE,
            hf_token=settings.HF_TOKEN
        )
        
        self.llm_generator = SOAPNoteGenerator(
            model_name=settings.LLM_MODEL
        )
        
        self.medical_ner = MedicalNER(
            device=settings.DEVICE
        )
        
        self.report_generator = ReportGenerator()
        
        logger.info("Pipeline initialization complete")
    
    def process_file(self, audio_path: str) -> Dict[str, Any]:
        """
        Process audio file through entire pipeline
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Complete pipeline results
        """
        start_time = time.time()
        results = {
            "success": False,
            "audio_info": {},
            "transcription": {},
            "diarization": {},
            "medical_entities": [],
            "soap_note": {},
            "report_path": None,
            "processing_time": {},
            "error": None
        }
        
        try:
            # Step 1: Get audio info
            logger.info("Step 1: Analyzing audio file")
            audio_info = self.audio_processor.get_audio_info(audio_path)
            results["audio_info"] = audio_info
            results["processing_time"]["audio_info"] = time.time() - start_time
            
            # Step 2: Preprocess audio
            logger.info("Step 2: Preprocessing audio")
            audio, sr = self.audio_processor.load_audio(audio_path)
            audio_processed = self.audio_processor.preprocess_audio(audio, sr)
            
            # Save processed audio temporarily
            temp_audio_path = str(settings.TEMP_DIR / f"processed_{Path(audio_path).name}")
            import soundfile as sf
            sf.write(temp_audio_path, audio_processed, sr)
            
            results["processing_time"]["preprocessing"] = time.time() - start_time
            
            # Step 3: Transcribe
            logger.info("Step 3: Transcribing audio")
            transcribe_start = time.time()
            transcription = self.transcriber.transcribe(temp_audio_path)
            results["transcription"] = transcription
            results["processing_time"]["transcription"] = time.time() - transcribe_start
            
            if not transcription.get("success", False):
                raise Exception(f"Transcription failed: {transcription.get('error')}")
            
            # Step 4: Speaker diarization
            logger.info("Step 4: Identifying speakers")
            diarize_start = time.time()
            diarization = self.diarizer.diarize(temp_audio_path)
            results["diarization"] = diarization
            results["processing_time"]["diarization"] = time.time() - diarize_start
            
            # Step 5: Align speakers with transcript
            logger.info("Step 5: Aligning speakers")
            if diarization.get("success", False) and transcription.get("segments"):
                aligned_segments = self.diarizer.align_with_transcript(
                    transcription["segments"],
                    diarization["segments"]
                )
                
                # Build conversation with speaker labels
                conversation_with_speakers = []
                for seg in aligned_segments:
                    speaker = seg.get("speaker", "UNKNOWN")
                    text = seg.get("text", "")
                    conversation_with_speakers.append(f"{speaker}: {text}")
                
                conversation_text = "\n".join(conversation_with_speakers)
            else:
                conversation_text = transcription.get("text", "")
            
            # Step 6: Extract medical entities
            logger.info("Step 6: Extracting medical entities")
            ner_start = time.time()
            # medical_entities = self.medical_ner.extract_entities(transcription.get("text", ""))
            medical_entities = []  # Temporary empty list
            results["medical_entities"] = medical_entities
            results["processing_time"]["ner"] = time.time() - ner_start
            
            # Step 7: Generate SOAP note
            logger.info("Step 7: Generating SOAP note")
            soap_start = time.time()
            soap_result = self.llm_generator.generate_soap(
                transcript=transcription.get("text", ""),
                conversation_with_speakers=conversation_text if 'conversation_text' in locals() else None,
                medical_terms=medical_entities
            )
            results["soap_note"] = soap_result
            results["processing_time"]["soap"] = time.time() - soap_start
            
            # Step 8: Generate PDF report
            logger.info("Step 8: Generating PDF report")
            report_start = time.time()
            
            report_data = {
                "audio_file": Path(audio_path).name,
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": audio_info.get("duration_minutes", 0),
                "transcript": transcription.get("text", ""),
                "conversation": conversation_text if 'conversation_text' in locals() else transcription.get("text", ""),
                "soap_note": soap_result.get("soap_parsed", {}),
                "medical_entities": medical_entities,
                "num_speakers": diarization.get("num_speakers", 1)
            }
            
            report_path = self.report_generator.generate_pdf(report_data)
            results["report_path"] = report_path
            results["processing_time"]["report"] = time.time() - report_start
            
            # Clean up temp file
            Path(temp_audio_path).unlink(missing_ok=True)
            
            # Final success
            results["success"] = True
            results["total_time"] = time.time() - start_time
            results["processing_time"]["total"] = results["total_time"]
            
            logger.info(f"Pipeline completed successfully in {results['total_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text input directly (no audio)
        
        Args:
            text: Clinical conversation text
            
        Returns:
            Pipeline results (skipping audio steps)
        """
        start_time = time.time()
        results = {
            "success": False,
            "medical_entities": [],
            "soap_note": {},
            "report_path": None,
            "processing_time": {}
        }
        
        try:
            # Step 1: Extract medical entities
            logger.info("Step 1: Extracting medical entities")
            ner_start = time.time()
            medical_entities = self.medical_ner.extract_entities(text)
            results["medical_entities"] = medical_entities
            results["processing_time"]["ner"] = time.time() - ner_start
            
            # Step 2: Generate SOAP note
            logger.info("Step 2: Generating SOAP note")
            soap_start = time.time()
            soap_result = self.llm_generator.generate_soap(
                transcript=text,
                medical_terms=medical_entities
            )
            results["soap_note"] = soap_result
            results["processing_time"]["soap"] = time.time() - soap_start
            
            # Step 3: Generate PDF report
            logger.info("Step 3: Generating PDF report")
            report_start = time.time()
            
            report_data = {
                "audio_file": "text_input.txt",
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": 0,
                "transcript": text,
                "conversation": text,
                "soap_note": soap_result.get("soap_parsed", {}),
                "medical_entities": medical_entities,
                "num_speakers": 2  # Assume doctor + patient
            }
            
            report_path = self.report_generator.generate_pdf(report_data)
            results["report_path"] = report_path
            results["processing_time"]["report"] = time.time() - report_start
            
            results["success"] = True
            results["total_time"] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            results["error"] = str(e)
        
        return results