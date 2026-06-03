try:
    from gtts import gTTS
except ImportError:
    print("Error: gtts library is not installed. Please install it using 'pip install gtts'")
    exit(1)

try:
    from pydub import AudioSegment
except ImportError:
    print("Error: pydub library is not installed. Please install it using 'pip install pydub'")
    print("Note: ffmpeg is also required. Install with: 'choco install ffmpeg' (Windows) or 'brew install ffmpeg' (Mac)")
    exit(1)

import os

def create_test_audio():
    # List of dialogue lines (alternating Doctor/Patient)
    dialogue = [
         "Doctor: Good morning. Please come in and have a seat.",
    "Patient: Good morning, doctor.",
    "Doctor: What brings you here today?",
    "Patient: I have been having a fever and cough for the last three days.",
    "Doctor: Do you also have a sore throat?",
    "Patient: Yes, my throat hurts while swallowing.",
    "Doctor: Are you experiencing body pain or headache?",
    "Patient: Yes, especially in my back and legs.",
    "Doctor: What about breathing difficulty?",
    "Patient: No, breathing is normal.",
    "Doctor: Have you checked your temperature?",
    "Patient: Yes, it was around 101°F yesterday night.",
    "Doctor: Did you take any medicine?",
    "Patient: I took paracetamol twice.",
    "Doctor: Did it help reduce the fever?",
    "Patient: Yes, but the fever comes back after some time.",
    "Doctor: Do you have any allergies?",
    "Patient: No, doctor.",
    "Doctor: Are you diabetic or do you have high blood pressure?",
    "Patient: No, I don’t have any medical conditions.",
    "Doctor: Are you eating properly?",
    "Patient: My appetite is low since yesterday.",
    "Doctor: Are you drinking enough water?",
    "Patient: I am trying to, but my throat hurts.",
    "Doctor: I understand. Let me check your throat and chest.",
    "Patient: Okay, doctor.",
    "Doctor: Please open your mouth wide.",
    "Patient: Like this?",
    "Doctor: Yes. Your throat looks slightly red. Now take a deep breath.",
    "Patient: Breathes deeply",
    "Doctor: Your chest sounds clear. It looks like a viral infection.",
    "Patient: Is it serious?",
    "Doctor: No, it should improve in a few days with rest and medication.",
    "Patient: Okay, doctor.",
    "Doctor: I will prescribe medicine for fever, cough, and throat pain.",
    "Patient: Thank you.",
    "Doctor: Avoid cold drinks and oily food for a few days.",
    "Patient: Sure, doctor.",
    "Doctor: Drink warm water and take enough rest.",
    "Patient: I will follow that.",
    "Doctor: If the fever continues for more than five days, come back for tests.",
    "Patient: Alright.",
    "Doctor: Do you have any other symptoms?",
    "Patient: Sometimes I feel tired and weak.",
    "Doctor: That is common with viral fever.",
    "Patient: Okay.",
    "Doctor: Are you working or studying?",
    "Patient: I am a college student.",
    "Doctor: Then avoid going to college for two or three days.",
    "Patient: Okay, I will stay home."
    ]
    
    segments = []
    for i, line in enumerate(dialogue):
        tts = gTTS(text=line, lang='en')
        temp_file = f"temp_{i}.mp3"
        tts.save(temp_file)
        segment = AudioSegment.from_mp3(temp_file)
        silence = AudioSegment.silent(duration=700)  # 0.7 sec pause
        segments.append(segment)
        segments.append(silence)
        os.remove(temp_file)
    
    # Combine all segments
    final = AudioSegment.empty()
    for seg in segments:
        final += seg
    
    # Export as WAV
    output_file = "test_consultation.wav"
    final.export(output_file, format="wav")
    print(f"✅ Test audio file created: {output_file}")

if __name__ == "__main__":
    create_test_audio()