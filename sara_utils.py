import whisper
import requests
from google.cloud import texttospeech
import os
import re

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "optical-pillar-456208-b7-f11a787d3a82.json"

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

def call_gemini(chat_history, user_input):
    system_prompt = (
        "You are SARA (Smart Audio-Recognition Assistant). Keep responses to 5 sentences max. "
        "Analyze the emotional context and add a tone marker at the end:\n"
        "Options: [tone:professional], [tone:friendly], [tone:sad], [tone:happy]\n"
        "Examples:\n"
        "User: I lost my job -> [tone:sad]\n"
        "User: Got promoted! -> [tone:happy]\n"
        "User: Explain quantum physics -> [tone:professional]\n"
        "Now respond to this:\n"
    )
    
    # Format history
    history_str = ""
    for msg in chat_history:
        if msg['role'] == 'user':
            history_str += f"User: {msg['parts'][0]['text']}\n"
        elif msg['role'] == 'model':
            history_str += f"SARA: {msg['parts'][0]['text']}\n"
    
    full_prompt = f"{system_prompt}{history_str}User: {user_input}\nSARA:"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "role": "user",
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
                reply_text = parts[0].get("text", "[No response text found]")
                
                # Extract tone and clean response
                tone_match = re.search(r'\[tone:(\w+)\]', reply_text)
                tone = tone_match.group(1).lower() if tone_match else "professional"
                clean_reply = re.sub(r'\s*\[tone:\w+\]\s*$', '', reply_text).strip()
                
                # Enforce 3 sentence limit
                sentences = clean_reply.split('. ')
                if len(sentences) > 3:
                    clean_reply = '. '.join(sentences[:3]) + '.'
                elif clean_reply.count('.') < 2:
                    clean_reply = clean_reply[:500]
                
                return clean_reply, tone
        return "[No output provided]", "professional"
    except Exception as e:
        return f"[Gemini Error] {e}", "professional"

def speak(text, filename="static/response.mp3", tone="professional"):
    print(f"[INFO] Generating TTS with tone: {tone}")
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-C",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        # Tone-based audio configurations
        tone_settings = {
            "professional": {"speaking_rate": 1.0, "pitch": 0.0},
            "friendly": {"speaking_rate": 1.1, "pitch": 2.0},
            "sad": {"speaking_rate": 0.8, "pitch": -3.0},
            "happy": {"speaking_rate": 1.2, "pitch": 4.0}
        }

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=tone_settings[tone]["speaking_rate"],
            pitch=tone_settings[tone]["pitch"]
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        with open(filename, "wb") as out:
            out.write(response.audio_content)
        print(f"[INFO] Audio saved to {filename}")
    except Exception as e:
        print("[ERROR] Google Cloud TTS failed:", e)