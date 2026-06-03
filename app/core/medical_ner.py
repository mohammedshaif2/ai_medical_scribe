"""
Medical Named Entity Recognition using dslim/bert-base-NER
Works with torch 2.4.0
"""

from typing import List, Dict, Any, Optional
from transformers import pipeline
import torch
from loguru import logger

class MedicalNER:
    """Extract medical entities using a lightweight NER model"""
    
    def __init__(self, model_name: str = "dslim/bert-base-NER", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.ner_pipeline = None
        self._load_pipeline()
    
    def _load_pipeline(self):
        logger.info(f"Loading NER model: {self.model_name}")
        try:
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model_name,
                tokenizer=self.model_name,
                device=0 if (self.device == "cuda" and torch.cuda.is_available()) else -1,
                aggregation_strategy="simple"
            )
            logger.info("NER pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NER model: {e}")
            self.ner_pipeline = None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        if self.ner_pipeline is None:
            logger.warning("NER pipeline not available")
            return []
        try:
            if len(text) > 5000:
                text = text[:5000]
            entities = self.ner_pipeline(text)
            results = []
            for ent in entities:
                results.append({
                    "term": ent["word"].replace("##", ""),
                    "type": ent["entity_group"],
                    "confidence": round(ent["score"], 3),
                    "start": ent["start"],
                    "end": ent["end"]
                })
            # Remove duplicates (keep highest confidence)
            unique = {}
            for e in results:
                term = e["term"].lower()
                if term not in unique or e["confidence"] > unique[term]["confidence"]:
                    unique[term] = e
            return list(unique.values())
        except Exception as e:
            logger.error(f"NER extraction failed: {e}")
            return []
    
    def get_medications(self, text: str) -> List[str]:
        ents = self.extract_entities(text)
        return [e["term"] for e in ents if e["type"] in ("CHEMICAL", "MEDICATION")]
    
    def get_symptoms(self, text: str) -> List[str]:
        ents = self.extract_entities(text)
        symptom_keywords = ["pain", "ache", "cough", "fever", "nausea", "fatigue"]
        symptoms = []
        for e in ents:
            term = e["term"].lower()
            if any(kw in term for kw in symptom_keywords):
                symptoms.append(e["term"])
        return symptoms
    
    def get_diagnoses(self, text: str) -> List[str]:
        ents = self.extract_entities(text)
        return [e["term"] for e in ents if e["type"] == "DISEASE"]