# frontend/gradio_app.py
import gradio as gr
import requests
import tempfile
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"

# ----------------------------------------------------------------------
# Scribing functions (audio + text)
# ----------------------------------------------------------------------
def transcribe_audio(audio_file):
    if audio_file is None:
        return "Please upload an audio file", "", None
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': (Path(audio_file).name, f, 'audio/wav')}
            response = requests.post(f"{API_BASE}/transcribe", files=files)
        if response.status_code == 200:
            result = response.json()
            soap = result.get('soap_note', {})
            output = f"""
            # MEDICAL REPORT
            ## SUBJECTIVE
            {soap.get('subjective', 'N/A')}
            ## OBJECTIVE
            {soap.get('objective', 'N/A')}
            ## ASSESSMENT
            {soap.get('assessment', 'N/A')}
            ## PLAN
            {soap.get('plan', 'N/A')}
            ---
            **Duration:** {result.get('audio_info', {}).get('duration_minutes', 0)} min
            **Speakers:** {result.get('num_speakers', 0)}
            **Processing Time:** {result.get('processing_time', {}).get('total', 0):.2f}s
            """
            report_url = result.get('report_url')
            pdf_path = None
            if report_url:
                pdf_response = requests.get(f"http://localhost:8000{report_url}")
                pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_response.content)
            return output, result, pdf_path
        else:
            return f"Error: {response.text}", "", None
    except Exception as e:
        return f"Error: {str(e)}", "", None

def process_text(text):
    if not text.strip():
        return "Please enter some text", "", None
    try:
        response = requests.post(f"{API_BASE}/process-text", params={"text": text})
        if response.status_code == 200:
            result = response.json()
            soap = result.get('soap_note', {})
            output = f"""
            # MEDICAL REPORT (Text Input)
            ## SUBJECTIVE
            {soap.get('subjective', 'N/A')}
            ## OBJECTIVE
            {soap.get('objective', 'N/A')}
            ## ASSESSMENT
            {soap.get('assessment', 'N/A')}
            ## PLAN
            {soap.get('plan', 'N/A')}
            ---
            **Medical Terms Found:** {result.get('medical_entities_count', 0)}
            """
            report_url = result.get('report_url')
            pdf_path = None
            if report_url:
                pdf_response = requests.get(f"http://localhost:8000{report_url}")
                pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_response.content)
            return output, result, pdf_path
        else:
            return f"Error: {response.text}", "", None
    except Exception as e:
        return f"Error: {str(e)}", "", None

# ----------------------------------------------------------------------
# Dashboard functions (fetch stats, patients, add patient)
# ----------------------------------------------------------------------
def get_dashboard_stats():
    try:
        resp = requests.get(f"{API_BASE}/dashboard/stats")
        if resp.status_code == 200:
            stats = resp.json()
            return f"""
            ### 📊 Practice Overview
            - **Total Patients:** {stats['total_patients']}
            - **Total Consultations:** {stats['total_consultations']}
            """
        else:
            return "⚠️ Could not load statistics."
    except:
        return "⚠️ Could not connect to backend."

def get_recent_consultations():
    try:
        resp = requests.get(f"{API_BASE}/dashboard/stats")
        if resp.status_code == 200:
            stats = resp.json()
            recent = stats['recent_consultations']
            if not recent:
                return "No consultations yet."
            table = "| Patient | Date | Duration (min) |\n|--------|------|----------------|\n"
            for cons in recent:
                date = cons['date'][:16] if cons['date'] else "Unknown"
                duration = cons['duration']
                patient = cons['patient_name']
                table += f"| {patient} | {date} | {duration} |\n"
            return table
        else:
            return "Error fetching consultations"
    except:
        return "Could not connect to backend"

def get_patient_list():
    try:
        resp = requests.get(f"{API_BASE}/dashboard/patients")
        if resp.status_code == 200:
            patients = resp.json()
            if not patients:
                return "No patients found."
            table = "| ID | Name | Phone | Email |\n|----|------|-------|-------|\n"
            for p in patients:
                name = f"{p.get('first_name', '')} {p.get('last_name', '')}"
                phone = p.get('phone', '') or '-'
                email = p.get('email', '') or '-'
                table += f"| {p['id']} | {name} | {phone} | {email} |\n"
            return table
        else:
            return "Error fetching patients"
    except:
        return "Could not connect to backend"

def add_patient(first_name, last_name, phone, email, dob):
    if not first_name or not last_name:
        return "❌ First name and last name are required."
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone or "",
        "email": email or "",
        "date_of_birth": dob or ""
    }
    try:
        resp = requests.post(f"{API_BASE}/dashboard/patients", json=data)
        if resp.status_code == 200:
            return f"✅ Patient {first_name} {last_name} added successfully."
        else:
            return f"❌ Error: {resp.text}"
    except Exception as e:
        return f"❌ Connection error: {e}"

# ----------------------------------------------------------------------
# Gradio UI (combined scribing + dashboard)
# ----------------------------------------------------------------------
with gr.Blocks(title="AI Medical Scribe", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏥 AI Medical Scribe")
    gr.Markdown("Generate SOAP notes from doctor-patient conversations and manage patients.")

    with gr.Tabs():
        with gr.TabItem("🎙️ Audio Upload"):
            with gr.Row():
                with gr.Column():
                    audio_input = gr.Audio(type="filepath", label="Upload Consultation Audio", sources=["upload", "microphone"])
                    submit_audio = gr.Button("Generate Report", variant="primary")
                with gr.Column():
                    audio_output = gr.Markdown(label="Medical Report")
            with gr.Row():
                audio_api_response = gr.JSON(label="API Response")
                audio_pdf = gr.File(label="Download PDF Report")
            submit_audio.click(transcribe_audio, inputs=audio_input, outputs=[audio_output, audio_api_response, audio_pdf])

        with gr.TabItem("📝 Text Input"):
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(lines=12, label="Paste Conversation Transcript", placeholder="Doctor: Good morning. How are you feeling?\nPatient: I've had a headache for three days...")
                    submit_text = gr.Button("Process Text", variant="primary")
                with gr.Column():
                    text_output = gr.Markdown(label="Medical Report")
            with gr.Row():
                text_api_response = gr.JSON(label="API Response")
                text_pdf = gr.File(label="Download PDF Report")
            submit_text.click(process_text, inputs=text_input, outputs=[text_output, text_api_response, text_pdf])

        with gr.TabItem("📊 Dashboard"):
            gr.Markdown("## Dashboard Overview")
            stats_output = gr.Markdown()
            gr.Markdown("### Recent Consultations")
            recent_output = gr.Markdown()
            gr.Markdown("### Patient List")
            patient_table = gr.Markdown()
            refresh_btn = gr.Button("🔄 Refresh Dashboard")
            refresh_btn.click(get_dashboard_stats, outputs=stats_output)
            refresh_btn.click(get_recent_consultations, outputs=recent_output)
            refresh_btn.click(get_patient_list, outputs=patient_table)

            gr.Markdown("---")
            gr.Markdown("### ➕ Add New Patient")
            with gr.Row():
                p_first = gr.Textbox(label="First Name *")
                p_last = gr.Textbox(label="Last Name *")
            with gr.Row():
                p_phone = gr.Textbox(label="Phone")
                p_email = gr.Textbox(label="Email")
                p_dob = gr.Textbox(label="Date of Birth (YYYY-MM-DD)")
            add_btn = gr.Button("Add Patient", variant="primary")
            add_result = gr.Textbox(label="Result", interactive=False)
            add_btn.click(add_patient, inputs=[p_first, p_last, p_phone, p_email, p_dob], outputs=add_result)
            # Load initial data when dashboard tab is selected
            demo.load(get_dashboard_stats, outputs=stats_output)
            demo.load(get_recent_consultations, outputs=recent_output)
            demo.load(get_patient_list, outputs=patient_table)

    gr.Markdown("---\n### ⚠️ Disclaimer\nThis is an AI-generated draft for educational purposes. Must be reviewed by a qualified healthcare professional.")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)