import time
import whisper
import pyaudio
import webrtcvad
import numpy as np
import requests
import pygame
from gtts import gTTS

# ------------------------------
# Configuration and Parameters
# ------------------------------
RATE = 16000
FRAME_DURATION_MS = 30
FRAME_SIZE = int(RATE * FRAME_DURATION_MS / 1000)
CHUNK_DURATION_MS = 1000
FRAMES_PER_CHUNK = int(CHUNK_DURATION_MS / FRAME_DURATION_MS)

VAD_MODE = 2
SILENCE_THRESHOLD_CHUNKS = 3

GEMINI_API_KEY = "AIzaSyCOHVB8AzJgHU7TA9uVLV0Cqo6HiNroPxE"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# ------------------------------
# Utility Functions
# ------------------------------
def int16_to_float32(audio_bytes):
    audio_data = np.frombuffer(audio_bytes, np.int16).astype(np.float32) / 32768.0
    return audio_data

def transcribe_audio_buffer(model, audio_buffer):
    audio_bytes = b"".join(audio_buffer)
    audio_np = int16_to_float32(audio_bytes)
    result = model.transcribe(audio_np, language="en", fp16=False)
    return result["text"]

def call_gemini(prompt):
    system_prompt = "You are SARA (Smart Audio-Recognition Assistant), who converses with the user by recognizing their speech. Answer in one paragraph."
    # Combine system prompt with user input (prompt)
    full_prompt = f"{system_prompt} {prompt}"

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
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            if parts and isinstance(parts[0], dict):
                return parts[0].get("text", "[No response text found]")
        return "[No output provided]"
    except Exception as e:
        return f"[Error calling Gemini]: {e}"

# ------------------------------
# Main Loop
# ------------------------------
def main():
    print("Initializing microphone stream and VAD...")
    vad = webrtcvad.Vad(VAD_MODE)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=RATE,
                     input=True,
                     frames_per_buffer=FRAME_SIZE)

    print("Loading Whisper model (tiny for speed)...")
    model = whisper.load_model("tiny")

    print("\n=== SARA: Smart Audio-Recognition Assistant ===")
    print("Speak naturally. A segment starts only when speech is detected and ends after 3 seconds of silence.")
    print("Press Ctrl+C to exit.\n")

    current_buffer = None
    silence_counter = 0

    pygame.mixer.init()

    try:
        while True:
            chunk_frames = [stream.read(FRAME_SIZE, exception_on_overflow=False)
                            for _ in range(FRAMES_PER_CHUNK)]

            speech_frames = sum(1 for frame in chunk_frames if vad.is_speech(frame, RATE))

            if speech_frames >= (FRAMES_PER_CHUNK * 0.5):
                if current_buffer is None:
                    current_buffer = []
                    silence_counter = 0
                    print("\n--- Speech detected: starting new segment ---")
                current_buffer.extend(chunk_frames)
            else:
                if current_buffer is not None:
                    silence_counter += 1
                    current_buffer.extend(chunk_frames)
                    if silence_counter >= SILENCE_THRESHOLD_CHUNKS:
                        print("\n--- Silence detected for 3 seconds: ending segment ---")
                        transcription = transcribe_audio_buffer(model, current_buffer)
                        if transcription.strip():
                            print("Transcription:", transcription)

                            print("\n--- Calling Gemini 2.0 Flash ---")
                            gemini_response = call_gemini(transcription)
                            print("Gemini Response:", gemini_response)

                            print("\n--- Playing Gemini Response via Google TTS ---")
                            tts = gTTS(text=gemini_response, lang="en")
                            filename = "voice.mp3"
                            tts.save(filename)

                            pygame.mixer.music.load(filename)
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.1)
                        else:
                            print("Segment had no transcribable speech.")
                        current_buffer = None
                        silence_counter = 0
                        print("\n--- Listening for new segment ---")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting SARA...")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

if __name__ == "__main__":
    main()
