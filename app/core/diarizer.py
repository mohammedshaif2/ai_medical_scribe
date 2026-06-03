"""
Speaker diarization module using PyAnnote (works with token parameter)
"""

from typing import List, Dict, Any, Optional
import torch
from pyannote.audio import Pipeline
from loguru import logger

class SpeakerDiarizer:
    """Handles speaker identification and diarization"""
    
    def __init__(self, model_name: str = "pyannote/speaker-diarization-3.1",
                 device: str = "cpu", hf_token: Optional[str] = None):
        self.model_name = model_name
        self.device = device
        self.hf_token = hf_token
        self.pipeline = None
        self._load_pipeline()
    
    def _load_pipeline(self):
        logger.info(f"Loading diarization model: {self.model_name}")
        if not self.hf_token:
            logger.error("HF_TOKEN not provided")
            self.pipeline = None
            return
        try:
            # Use 'token' (works with pyannote.audio 3.1.1)
            self.pipeline = Pipeline.from_pretrained(
                self.model_name,
                use_auth_token=self.hf_token
            )
            self.pipeline.to(torch.device(self.device))
            logger.info("Diarization pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load diarization pipeline: {e}")
            self.pipeline = None
    
    def diarize(self, audio_path: str) -> Dict[str, Any]:
        if self.pipeline is None:
            return {"success": False, "error": "Pipeline not loaded", "segments": []}
        logger.info(f"Starting diarization: {audio_path}")
        try:
            diarization = self.pipeline(audio_path)
            segments = []
            speakers = set()
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "speaker": speaker,
                    "start": turn.start,
                    "end": turn.end,
                    "duration": turn.end - turn.start
                })
                speakers.add(speaker)
            total_duration = segments[-1]["end"] if segments else 0
            speaker_summary = {}
            for spk in speakers:
                spk_segs = [s for s in segments if s["speaker"] == spk]
                total = sum(s["duration"] for s in spk_segs)
                speaker_summary[spk] = {
                    "segments": len(spk_segs),
                    "total_duration": total,
                    "percentage": (total / total_duration * 100) if total_duration else 0
                }
            return {
                "success": True,
                "segments": segments,
                "num_speakers": len(speakers),
                "speakers": list(speakers),
                "speaker_summary": speaker_summary,
                "total_duration": total_duration
            }
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return {"success": False, "error": str(e), "segments": []}
    
    def align_with_transcript(self, transcript_segments: List[Dict], diarization_segments: List[Dict]) -> List[Dict]:
        aligned = []
        for trans in transcript_segments:
            trans_start, trans_end = trans["start"], trans["end"]
            votes = {}
            for diar in diarization_segments:
                overlap_start = max(trans_start, diar["start"])
                overlap_end = min(trans_end, diar["end"])
                if overlap_end > overlap_start:
                    duration = overlap_end - overlap_start
                    speaker = diar["speaker"]
                    votes[speaker] = votes.get(speaker, 0) + duration
            assigned = max(votes, key=votes.get) if votes else "UNKNOWN"
            new_seg = trans.copy()
            new_seg["speaker"] = assigned
            aligned.append(new_seg)
        return aligned