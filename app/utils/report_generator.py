"""
PDF Report Generation Module
Creates professional medical reports from pipeline results
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import time
from datetime import datetime
from fpdf import FPDF
from loguru import logger

from app.config import settings


def clean_text(text):
    """Remove or replace special characters for PDF compatibility"""
    if not text:
        return ""
    # Replace em dash, en dash with regular dash
    text = text.replace('\u2014', '-').replace('\u2013', '-')
    # Replace smart quotes with straight quotes
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    # Remove other non-ASCII characters
    return text.encode('ascii', 'ignore').decode('ascii')


class PDF(FPDF):
    """Custom PDF class with headers and footers"""
    
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'AI MEDICAL SCRIBE - CLINICAL REPORT', 0, 1, 'L')
        self.set_font('Arial', '', 8)
        # You can add doctor/patient if passed via instance variable
        self.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'L')
        self.ln(5)
        
        # Line
        self.set_draw_color(0, 80, 180)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
    
    def footer(self):
        """Add footer to each page"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def section_title(self, title):
        """Add section title"""
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 80, 180)
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_text_color(0, 0, 0)
        self.ln(2)
    
    def section_body(self, text):
        """Add section body text"""
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, clean_text(text))
        self.ln(5)
    
    def add_key_value(self, key, value):
        """Add key-value pair"""
        self.set_font('Arial', 'B', 10)
        self.cell(50, 6, f"{key}:", 0, 0)
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, clean_text(str(value)))
    
    def add_medical_terms(self, terms: List[Dict]):
        """Add medical terms table"""
        self.set_font('Arial', 'B', 10)
        self.cell(60, 7, 'Term', 1)
        self.cell(40, 7, 'Type', 1)
        self.cell(30, 7, 'Confidence', 1)
        self.ln()
        
        self.set_font('Arial', '', 9)
        for term in terms[:20]:  # Limit to 20 terms
            self.cell(60, 6, term.get('term', '')[:40], 1)
            self.cell(40, 6, term.get('type', ''), 1)
            self.cell(30, 6, str(term.get('confidence', '')), 1)
            self.ln()

class ReportGenerator:
    """Generate PDF medical reports"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir or settings.REPORT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_pdf(self, data: Dict[str, Any], custom_filename: Optional[str] = None) -> str:
        """
        Generate PDF report from pipeline data
        
        Args:
            data: Pipeline results dictionary
            custom_filename: Optional filename for the generated PDF
            
        Returns:
            Path to generated PDF
        """
        if custom_filename:
            filename = custom_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"medical_report_{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF
        pdf = PDF()
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 15, 'MEDICAL CONSULTATION REPORT', 0, 1, 'C')
        pdf.ln(5)
        
        # Metadata
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Patient ID: {data.get('patient_id', 'Not specified')}", 0, 1)
        pdf.cell(0, 6, f"Date of Visit: {data.get('date', datetime.now().strftime('%Y-%m-%d'))}", 0, 1)
        pdf.cell(0, 6, f"Audio File: {data.get('audio_file', 'N/A')}", 0, 1)
        pdf.cell(0, 6, f"Duration: {data.get('duration', 0)} minutes", 0, 1)
        pdf.cell(0, 6, f"Speakers Detected: {data.get('num_speakers', 'N/A')}", 0, 1)
        pdf.ln(5)
        
        # Line
        pdf.set_draw_color(0, 0, 0)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # SOAP Note
        soap = data.get('soap_note', {})
        
        pdf.section_title('SUBJECTIVE')
        pdf.section_body(soap.get('subjective', 'Not available'))
        
        pdf.section_title('OBJECTIVE')
        pdf.section_body(soap.get('objective', 'Not available'))
        
        pdf.section_title('ASSESSMENT')
        pdf.section_body(soap.get('assessment', 'Not available'))
        
        pdf.section_title('PLAN')
        pdf.section_body(soap.get('plan', 'Not available'))
        
        # Medical Terms
        if data.get('medical_entities'):
            pdf.add_page()
            pdf.section_title('MEDICAL TERMS DETECTED')
            pdf.add_medical_terms(data['medical_entities'])
        
        # Conversation Transcript
        if data.get('conversation'):
            pdf.add_page()
            pdf.section_title('CONVERSATION TRANSCRIPT')
            pdf.set_font('Courier', '', 8)  # Monospace for transcript
            pdf.multi_cell(0, 4, clean_text(data['conversation']))
        
        # Disclaimer
        pdf.add_page()
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(100, 100, 100)
        disclaimer = """
        DISCLAIMER: This report was generated by an AI medical scribe system and is for informational and educational purposes only.
        It is not a substitute for professional medical judgment. All information should be reviewed and verified by a qualified healthcare provider before clinical use.
        """
        pdf.multi_cell(0, 4, clean_text(disclaimer))
        
        # Save PDF
        pdf.output(str(filepath))
        logger.info(f"PDF report generated: {filepath}")
        
        return str(filepath)
    
    def generate_json(self, data: Dict[str, Any]) -> str:
        """
        Generate JSON report (FHIR-compatible format)
        
        Args:
            data: Pipeline results
            
        Returns:
            Path to JSON file
        """
        import json
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"medical_report_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Create FHIR-like structure
        fhir_report = {
            "resourceType": "DocumentReference",
            "status": "current",
            "docStatus": "preliminary",
            "date": datetime.now().isoformat(),
            "content": [
                {
                    "attachment": {
                        "contentType": "text/plain",
                        "data": data.get('conversation', '')
                    }
                }
            ],
            "context": {
                "encounter": {
                    "period": {
                        "start": data.get('date', '')
                    }
                }
            },
            "extension": [
                {
                    "url": "http://example.org/fhir/StructureDefinition/soap-note",
                    "valueString": json.dumps(data.get('soap_note', {}))
                },
                {
                    "url": "http://example.org/fhir/StructureDefinition/medical-entities",
                    "valueString": json.dumps(data.get('medical_entities', []))
                }
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(fhir_report, f, indent=2)
        
        logger.info(f"JSON report generated: {filepath}")
        return str(filepath)