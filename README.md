# SARA: Smart Audio-Recognition Assistant

SARA is a smart voice assistant that leverages state-of-the-art open-source technologies to provide a seamless conversational experience. It integrates:

- **ASR (Automatic Speech Recognition):** Uses [Whisper](https://github.com/openai/whisper) to transcribe spoken language into text.
- **Conversational AI:** Calls the Gemini 2.0 Flash API to generate intelligent responses based on user input.
- **TTS (Text-to-Speech):** Uses Google TTS (gTTS) to convert Gemini's responses into audible speech.

## Features

- **Dynamic Voice Activity Detection (VAD):**  
  SARA starts recording only when speech is detected and ends the segment after 3 seconds of silence.
- **Real-Time Transcription & Response:**  
  Uses Whisper to transcribe speech in near real-time and then queries the Gemini API with a system prompt that reminds the model of SARA’s identity.

- **Audible Feedback:**  
  Converts the Gemini response into speech using Google TTS and plays it back to the user using pygame.

## Installation

1. **Install Dependencies**
   `pip install -r requirements.txt`
2. **Install System Dependencies**

   PortAudio (for PyAudio):
   - On macOS: `brew install portaudio`
   - On Ubuntu: `sudo apt-get install portaudio19-dev`
   
   FFmpeg (for Whisper):
   - On macOS: `brew install ffmpeg`
   - On Ubuntu: `sudo apt-get install ffmpeg`
   - On Windows, download and install FFmpeg from ffmpeg.org and add it to your PATH.

## Usage

Simply run the sara.py script:

```
python sara.py
```

Speak naturally into your microphone. SARA will detect your speech, transcribe it, send it to the Gemini API (with a system prompt reminding the assistant of its identity), and then use Google TTS to read out the response.

Press Ctrl+C to exit the application.
