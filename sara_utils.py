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

# Global accent state
CURRENT_ACCENT = "american"

def transcribe_audio_file(filepath):
    print("[INFO] Transcribing audio using Whisper...")
    try:
        result = model.transcribe(filepath, language="en")
        return result["text"]
    except Exception as e:
        print("[ERROR] Whisper failed:", e)
        return "[ASR failed]"

def call_gemini(chat_history, user_input):
    global CURRENT_ACCENT

    system_prompt = (
        "You are SARA (Smart Audio-Recognition Assistant) who can switch accents in 4 different ways and change the tone of the speaking. "
        "Keep responses to 5 sentences max. Don't put tone brackets.\n"
        "Analyze the emotional context and add markers:\n"
        "1. Tone: [tone:professional], [tone:friendly], [tone:sad], [tone:happy], [tone:angry]\n"
        "2. Accent (ONLY when explicitly requested): [accent:british], [accent:australian], [accent:indian], [accent:american]\n"
        "3. Never include the markers in your actual response text.\n"
        "Examples:\n"
        "User: I lost my job -> [tone:sad]\n"
        "User: Switch to British accent -> [accent:british]\n"
        "User: Got promoted! -> [tone:happy]\n"
        "User: Explain quantum physics -> [tone:professional]\n"
        "User: You are useless! -> [tone:angry]\n"
        "Now respond to this in 5 sentences max. (You are encouraged to add emoji into your response):\n"
    )

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

                tone_match = re.search(r'\[tone:(\w+)\]', reply_text)
                accent_match = re.search(r'\[accent:(\w+)\]', reply_text)

                tone = tone_match.group(1).lower() if tone_match else "professional"
                if accent_match:
                    CURRENT_ACCENT = accent_match.group(1).lower()

                clean_reply = re.sub(r'\s*\[(tone|accent):\w+\]\s*', '', reply_text).strip()

                # Enforce sentence limit
                sentences = clean_reply.split('. ')
                if len(sentences) > 3:
                    clean_reply = '. '.join(sentences[:3]) + '.'
                elif clean_reply.count('.') < 2:
                    clean_reply = clean_reply[:500]

                return clean_reply, tone, CURRENT_ACCENT
        return "[No output provided]", "professional", CURRENT_ACCENT
    except Exception as e:
        return f"[Gemini Error] {e}", "professional", CURRENT_ACCENT

def speak(text, filename="static/response.mp3", tone="professional", accent="american"):
    print(f"[INFO] Generating TTS | Tone: {tone} | Accent: {accent}")
    try:
        filtered_text = re.sub(r'\[\w+\]', '', text).strip()
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\u2600-\u26FF"
            u"\u2700-\u27BF"
            u"\U0001F900-\U0001F9FF"
            "]+", flags=re.UNICODE)
        filtered_text = emoji_pattern.sub(r'', filtered_text)
        print(f"[INFO] Filtered text for TTS: '{filtered_text}'")

        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=filtered_text)

        voice_config = {
            "american": "en-US-Chirp3-HD-Achernar",
            "british": "en-GB-Standard-F",
            "australian": "en-AU-Wavenet-A",
            "indian": "en-IN-Wavenet-A"
        }
        voice_name = voice_config.get(accent, "en-US-Chirp3-HD-Achernar")

        tone_settings = {
            "professional": {"speaking_rate": 1.0, "pitch": 0.0},
            "friendly": {"speaking_rate": 1.1, "pitch": 2.0},
            "sad": {"speaking_rate": 0.93, "pitch": -2.0},
            "happy": {"speaking_rate": 1.15, "pitch": 4.0},
            "angry": {"speaking_rate": 1.2, "pitch": 2.5}
        }

        voice_params = texttospeech.VoiceSelectionParams(
            language_code="en-GB" if accent == "british" else
                          "en-AU" if accent == "australian" else
                          "en-IN" if accent == "indian" else "en-US",
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        if voice_name == "en-US-Chirp3-HD-Achernar":
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=tone_settings[tone]["speaking_rate"]
            )
        else:
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=tone_settings[tone]["speaking_rate"],
                pitch=tone_settings[tone]["pitch"]
            )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )

        with open(filename, "wb") as out:
            out.write(response.audio_content)
        print(f"[INFO] Audio saved to {filename}")
    except Exception as e:
        print("[ERROR] Google Cloud TTS failed:", e)
