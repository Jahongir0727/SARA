import whisper
import requests
from gtts import gTTS

# Gemini configuration
GEMINI_API_KEY = "AIzaSyCOHVB8AzJgHU7TA9uVLV0Cqo6HiNroPxE"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Load Whisper model (tiny for speed)
model = whisper.load_model("tiny")

def transcribe_audio_file(filepath):
    print("[INFO] Transcribing audio using Whisper...")
    try:
        result = model.transcribe(filepath, language="en")
        return result["text"]
    except Exception as e:
        print("[ERROR] Whisper failed:", e)
        return "[ASR failed]"

def call_gemini(prompt):
    system_prompt = (
        "You are SARA (Smart Audio-Recognition Assistant), who can converse with the user by recognizing their speech."
        "Answer concisely:"
    )
    full_prompt = f"{system_prompt}\n{prompt}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }]
    }
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        if "candidates" in result and result["candidates"]:
            parts = result["candidates"][0].get("content", {}).get("parts", [])
            if parts and isinstance(parts[0], dict):
                return parts[0].get("text", "[No response text found]")
        return "[No output provided]"
    except Exception as e:
        return f"[Gemini Error] {e}"

def speak(text, filename="response.mp3"):
    print("[INFO] Generating TTS for text:", text)
    try:
        tts = gTTS(text=text, lang="en")
        tts.save(filename)
    except Exception as e:
        print("[ERROR] TTS failed:", e)
