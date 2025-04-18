import os
import re
import datetime
import subprocess
import webbrowser
import platform

import whisper
import requests
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from google.cloud import texttospeech

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "optical-pillar-456208-b7-f11a787d3a82.json"

# Gemini configuration
GEMINI_API_KEY = "AIzaSyCOHVB8AzJgHU7TA9uVLV0Cqo6HiNroPxE"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
)

# Load Whisper model (tiny for speed)
model = whisper.load_model("tiny")

# Keep track of the current accent
CURRENT_ACCENT = "american"


def transcribe_audio_file(filepath):
    """Run Whisper ASR on a saved .wav file."""
    print("[INFO] Transcribing audio using Whisper...")
    try:
        result = model.transcribe(filepath, language="en")
        return result["text"]
    except Exception as e:
        print("[ERROR] Whisper failed:", e)
        return "[ASR failed]"


def call_gemini(chat_history, user_input):
    """
    Send the full prompt (system + history + user_input) to Gemini
    and extract tone/accent markers and the clean reply.
    """
    global CURRENT_ACCENT
    system_prompt = (
        "You are SARA (Smart Audio-Recognition Assistant) who can switch accents in 4 "
        "different ways and change the tone of the speaking. Keep responses to 5 sentences max. "
        "Don't include markers in the final text.\n"
        "Markers:\n"
        " • Tone: [tone:professional], [tone:friendly], [tone:sad], [tone:happy], [tone:angry]\n"
        " • Accent (when requested): [accent:british], [accent:australian], [accent:indian], "
        "[accent:american]\n"
        "Examples:\n"
        " User: I lost my job -> [tone:sad]\n"
        " User: Switch to British accent -> [accent:british]\n"
        " User: Got promoted! -> [tone:happy]\n"
        "Now respond:\n"
    )
    # Build history string
    history_str = ""
    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "SARA"
        history_str += f"{role}: {msg['parts'][0]['text']}\n"

    full_prompt = f"{system_prompt}{history_str}User: {user_input}\nSARA:"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"role": "user", "parts": [{"text": full_prompt}]}]}

    try:
        resp = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return "[No output provided]", "professional", CURRENT_ACCENT

        raw = candidates[0].get("content", {}).get("parts", [])[0].get("text", "")
        # Extract markers
        tone_m = re.search(r"\[tone:(\w+)\]", raw)
        accent_m = re.search(r"\[accent:(\w+)\]", raw)
        tone = tone_m.group(1).lower() if tone_m else "professional"
        if accent_m:
            CURRENT_ACCENT = accent_m.group(1).lower()

        # Clean out all markers
        clean = re.sub(r"\s*\[(tone|accent):\w+\]\s*", "", raw).strip()
        # Enforce up to 3 sentences
        parts = clean.split(". ")
        if len(parts) > 3:
            clean = ". ".join(parts[:3]) + "."

        return clean, tone, CURRENT_ACCENT

    except Exception as e:
        return f"[Gemini Error] {e}", "professional", CURRENT_ACCENT


def speak(text, filename="static/response.mp3", tone="professional", accent="american"):
    """Call Google Cloud TTS with tone & accent settings and write MP3 to disk."""
    print(f"[INFO] Generating TTS | Tone: {tone} | Accent: {accent}")
    # Strip out any leftover markers or emojis
    filtered = re.sub(r"\[\w+\]", "", text).strip()
    emoji_re = re.compile(
        "[" 
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\u2600-\u27BF"          # misc & dingbats
        u"\U0001F900-\U0001F9FF"  # supplemental
        u"\U0001FA70-\U0001FAFF"  # extended (e.g., 🪅)
        "]+",
        flags=re.UNICODE,
    )
    filtered = emoji_re.sub("", filtered)
    print(f"[INFO] Filtered text for TTS: '{filtered}'")

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=filtered)

    # Choose voice by accent
    voice_map = {
        "american": ("en-US", "en-US-Chirp3-HD-Achernar"),
        "british": ("en-GB", "en-GB-Standard-F"),
        "australian": ("en-AU", "en-AU-Wavenet-A"),
        "indian": ("en-IN", "en-IN-Wavenet-A"),
    }
    lang_code, name = voice_map.get(accent, voice_map["american"])
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=lang_code, name=name, ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )

    # Speaking rate & pitch per tone
    tone_cfg = {
        "professional": {"speaking_rate": 1.0, "pitch": 0.0},
        "friendly": {"speaking_rate": 1.1, "pitch": 2.0},
        "sad": {"speaking_rate": 0.7, "pitch": -5.0},
        "happy": {"speaking_rate": 1.15, "pitch": 4.0},
        "angry": {"speaking_rate": 1.2, "pitch": 2.5},
        "flirty": {"speaking_rate": 1.05, "pitch": 3.5},
    }
    cfg = tone_cfg.get(tone, tone_cfg["professional"])

    audio_cfg = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=cfg["speaking_rate"],
        pitch=cfg["pitch"],
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice_params, audio_config=audio_cfg
    )
    with open(filename, "wb") as out:
        out.write(response.audio_content)
    print(f"[INFO] Audio saved to {filename}")


def handle_command(user_input):
    """
    Detect and execute built‑in commands before falling
    back to Gemini. Returns (result, tone, accent) or (None, None, None).
    """
    global CURRENT_ACCENT
    txt = user_input.lower().strip()
    system = platform.system().lower()
    is_wsl = "microsoft" in platform.uname().release.lower()

    # Simple map for common abbreviations
    LOCATION_MAP = {
        "hk": "Hong Kong",
        "usa": "Washington, D.C.",
        "us": "Washington, D.C.",
        "uk": "London",
        "nyc": "New York City",
        "la": "Los Angeles",
        "sf": "San Francisco",
    }

    # 1) Search
    m = re.search(r"\bsearch for (.+)", txt)
    if m:
        q = re.sub(r"\b(for me|please|now|in browser)\b", "", m.group(1), flags=re.IGNORECASE).strip().rstrip(".?!")
        url = f"https://www.google.com/search?q={requests.utils.quote(q)}"
        try:
            if is_wsl:
                subprocess.run(["cmd.exe", "/c", "start", url], check=True)
            elif system == "windows":
                subprocess.Popen(f"start {url}", shell=True)
            elif system == "darwin":
                subprocess.Popen(["open", url])
            else:
                webbrowser.open_new_tab(url)
            return f"Searching for \"{q}\".", "professional", CURRENT_ACCENT
        except Exception as e:
            return f"Search failed: {e}", "professional", CURRENT_ACCENT

    # 2) Time
    # Only match when user is asking for the time
    if re.search(r"\b(?:what(?:'s| is) the time|current time|time in)\b", txt):
        # First, do “time in <location>” if present
        m2 = re.search(r"time in ([a-z\s]+)", txt)
        if m2:
            raw = re.sub(r"\b(now|today)\b", "", m2.group(1), flags=re.IGNORECASE).strip()
            city = LOCATION_MAP.get(raw, raw.title())
            try:
                geo = Nominatim(user_agent="tz_app").geocode(city, exactly_one=True)
                tf = TimezoneFinder()
                tzstr = tf.timezone_at(lat=geo.latitude, lng=geo.longitude)
                tz = pytz.timezone(tzstr)
                now_t = datetime.datetime.now(tz).strftime("%I:%M %p")
                disp = tzstr.split("/")[-1].replace("_", " ")
                return f"The current time in {disp} is {now_t}.", "professional", CURRENT_ACCENT
            except Exception:
                fallback = datetime.datetime.now().strftime("%I:%M %p")
                return f"The current time in {city} is {fallback}.", "professional", CURRENT_ACCENT

        # Otherwise handle generic “what’s the time” or “current time”
        now_local = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is {now_local}.", "professional", CURRENT_ACCENT


    # 3) Take a note
    m3 = re.match(r"^\s*take a note[,:]?\s*(.+)$", user_input, flags=re.IGNORECASE)
    if m3:
        note = re.sub(r"^(?:take a note|for me)[,:]?\s*", "", m3.group(1), flags=re.IGNORECASE).strip()
        path = os.path.expanduser("~/notes.txt")
        try:
            with open(path, "a", encoding="utf-8") as f:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                f.write(f"{ts}: {note}\n")
            return f"Your note has been saved to {path}.", "professional", CURRENT_ACCENT
        except Exception as e:
            return f"Note failed: {e}", "professional", CURRENT_ACCENT

    # 4) Play music
    if "play music" in txt:
        try:
            if is_wsl:
                subprocess.run(["cmd.exe", "/c", "start", "spotify:"])
            elif system == "windows":
                subprocess.Popen(["start", "spotify:"], shell=True)
            elif system == "darwin":
                subprocess.Popen(["open", "-a", "Spotify"])
            else:
                subprocess.Popen(["flatpak", "run", "com.spotify.Client"])
        except:
            webbrowser.open("https://music.youtube.com")
        return "Opening Spotify for you...", "friendly", CURRENT_ACCENT

    # 5) Weather
    if "weather in" in txt:
        m4 = re.search(r"weather in\s+([a-z\s]+)", txt)
        if m4:
            loc = re.sub(r"\b(now|today)\b.*$", "", m4.group(1), flags=re.IGNORECASE).strip()
            city = LOCATION_MAP.get(loc, loc.title())
            key = "d32f275d3b4d46fec855b7e37f40eb41"
            url = (f"http://api.openweathermap.org/data/2.5/weather"
                   f"?q={requests.utils.quote(city)}"
                   f"&appid={key}&units=metric")
            jr = requests.get(url).json()
            if jr.get("cod") == 200:
                d = jr["weather"][0]["description"]
                t = jr["main"]["temp"]
                return f"Weather in {city}: {d}, {t}°C.", "professional", CURRENT_ACCENT
            return f"Weather unavailable for {city}.", "professional", CURRENT_ACCENT
        return "Specify location (e.g., 'weather in London').", "professional", CURRENT_ACCENT

    return None, None, None
