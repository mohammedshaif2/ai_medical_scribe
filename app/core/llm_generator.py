"""
LLM integration for SOAP note generation
Uses Ollama for local LLM inference
"""

from typing import Dict, Any, List, Optional
import json
import requests
import time
from loguru import logger

class SOAPNoteGenerator:
    """Generate structured SOAP notes using local LLM"""
    
    def __init__(self, model_name: str = "phi3:mini", 
                 ollama_host: str = "http://localhost:11434"):
        """
        Initialize LLM generator
        
        Args:
            model_name: Model name in Ollama (meditron, llama3, etc.)
            ollama_host: Ollama API host
        """
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.api_url = f"{ollama_host}/api/generate"
        
        # Check if model is available
        self._check_model()
    
    def _check_model(self):
        """Check if model is available in Ollama"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [m["name"] for m in models]
                
                if self.model_name not in available_models:
                    logger.warning(f"Model {self.model_name} not found in Ollama")
                    logger.info(f"Pull it with: ollama pull {self.model_name}")
                else:
                    logger.info(f"Model {self.model_name} is available")
            else:
                logger.warning("Could not check model availability")
        except Exception as e:
            logger.error(f"Error checking Ollama: {e}")
            logger.info("Make sure Ollama is running: 'ollama serve'")
    
    def generate_soap(self, transcript: str, 
                      conversation_with_speakers: Optional[str] = None,
                      medical_terms: Optional[List] = None) -> Dict[str, Any]:
        """
        Generate SOAP note from transcript
        
        Args:
            transcript: Raw transcript text
            conversation_with_speakers: Transcript with speaker labels
            medical_terms: Extracted medical terms (optional)
            
        Returns:
            Dictionary with SOAP note sections
        """
        # Use conversation with speakers if available
        input_text = conversation_with_speakers if conversation_with_speakers else transcript
        
        # Build prompt
        prompt = self._build_soap_prompt(input_text, medical_terms)
        
        logger.info("Generating SOAP note with LLM")
        start_time = time.time()
        
        try:
            # Call Ollama API
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,  # Lower temperature for more consistent output
                    "max_tokens": 1500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                soap_text = result.get("response", "")
                
                # Parse the SOAP note
                soap_parsed = self._parse_soap_response(soap_text)
                
                processing_time = time.time() - start_time
                logger.info(f"SOAP generation completed in {processing_time:.2f}s")
                
                return {
                    "success": True,
                    "soap_text": soap_text,
                    "soap_parsed": soap_parsed,
                    "processing_time": processing_time
                }
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "soap_text": "",
                    "soap_parsed": {}
                }
                
        except Exception as e:
            logger.error(f"SOAP generation failed: {e}")
            
            # Fallback to template-based generation
            logger.info("Using fallback template-based generation")
            return self._generate_fallback_soap(input_text, medical_terms)
    
    def _build_soap_prompt(self, conversation: str, 
                          medical_terms: Optional[List] = None) -> str:
        """Build prompt for SOAP note generation"""
        
        prompt = f"""You are a clinical documentation assistant. Convert the following doctor-patient conversation into a structured SOAP note.

Follow this EXACT format with clear section headers:

SUBJECTIVE:
- Chief Complaint (CC): [One sentence]
- History of Present Illness (HPI): [Detailed paragraph]
- Past Medical History: [List relevant conditions]
- Medications: [List current medications]
- Allergies: [List allergies]
- Review of Systems: [Mention any systems discussed]

OBJECTIVE:
- Vital Signs: [Mention if available]
- Physical Exam: [Relevant findings from conversation]
- Observations: [General appearance, etc.]

ASSESSMENT:
- Diagnosis: [Primary diagnosis]
- Differential Diagnoses: [List if mentioned]

PLAN:
- Medications: [Prescribed or adjusted medications]
- Tests/Imaging: [Ordered tests]
- Follow-up: [Follow-up instructions]
- Patient Education: [Key points discussed]

CONVERSATION:
{conversation}

"""
        
        if medical_terms:
            prompt += f"\nMEDICAL TERMS IDENTIFIED: {', '.join([t.get('term', '') for t in medical_terms[:10]])}\n"
        
        prompt += "\nGenerate the SOAP note now:"
        
        return prompt
    
    def _parse_soap_response(self, soap_text: str) -> Dict[str, str]:
        """Parse LLM response into structured sections"""
        
        sections = {
            "subjective": "",
            "objective": "",
            "assessment": "",
            "plan": ""
        }
        
        current_section = None
        section_content = []
        
        for line in soap_text.split('\n'):
            line_lower = line.lower()
            
            # Check for section headers
            if "subjective" in line_lower and ":" in line_lower[:20]:
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = "subjective"
                section_content = [line]
            elif "objective" in line_lower and ":" in line_lower[:20]:
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = "objective"
                section_content = [line]
            elif "assessment" in line_lower and ":" in line_lower[:20]:
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = "assessment"
                section_content = [line]
            elif "plan" in line_lower and ":" in line_lower[:20]:
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = "plan"
                section_content = [line]
            else:
                if current_section:
                    section_content.append(line)
        
        # Add last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        return sections
    
    def _generate_fallback_soap(self, conversation: str, 
                               medical_terms: Optional[List] = None) -> Dict[str, Any]:
        """Fallback template-based SOAP generation"""
        
        # Extract key phrases (simplified)
        words = conversation.lower().split()
        
        # Simple keyword extraction
        symptoms = []
        medications = []
        
        symptom_keywords = ["pain", "cough", "fever", "headache", "nausea", "fatigue"]
        med_keywords = ["lisinopril", "metformin", "ibuprofen", "aspirin"]
        
        for word in words:
            if word in symptom_keywords and word not in symptoms:
                symptoms.append(word)
            if word in med_keywords and word not in medications:
                medications.append(word)
        
        soap_text = f"""
SUBJECTIVE:
- Chief Complaint: Patient reports {', '.join(symptoms) if symptoms else 'various symptoms'}.
- History of Present Illness: {conversation[:200]}...
- Medications: {', '.join(medications) if medications else 'Not specified'}

OBJECTIVE:
- Vital Signs: Not available in audio.
- Physical Exam: Based on conversation.

ASSESSMENT:
- Diagnosis: Under evaluation based on symptoms.

PLAN:
- Follow-up: As discussed with patient.
- Education: Reviewed treatment options.

NOTE: This is a template-based fallback. Install Ollama for AI-generated notes.
"""
        
        return {
            "success": False,
            "error": "Used fallback template (LLM unavailable)",
            "soap_text": soap_text,
            "soap_parsed": self._parse_soap_response(soap_text)
        }