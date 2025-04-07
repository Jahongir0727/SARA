# SARA: Smart Audio-Recognition Assistant

SARA is a smart voice assistant that leverages state-of-the-art open-source technologies to provide a seamless conversational experience through a web-based user interface. It integrates:

- **ASR (Automatic Speech Recognition):** Uses [Whisper](https://github.com/openai/whisper) to transcribe spoken language into text.
- **Conversational AI:** Calls the Gemini 2.0 Flash API to generate brief, intelligent responses based on user input. A system prompt is included with every request to remind Gemini of SARA’s identity.
- **TTS (Text-to-Speech):** Uses Google TTS (gTTS) to convert Gemini's responses into audible speech, which is played back via the web interface.

## Features

- **Real Voice Input:**  
  Users can click the “Voice Input” button to record speech from their computer's microphone. When they click “Finish,” the audio is sent to the backend where Whisper transcribes it.

- **Dynamic Text Input:**  
  Users can also type their messages. The text input field auto-grows in height as more text is entered, while the buttons maintain a fixed height.

- **Intuitive Chat UI:**

  - The home page displays a pleasant greeting (with an emoji and a pastel gradient background).
  - Once a message is sent (via text or voice), the greeting is replaced by a centered chat box.
  - All user messages are right-aligned and all Gemini responses are left-aligned, similar to popular messaging apps.
  - Message bubbles dynamically adjust their width based on the content.

- **Real-Time Transcription & TTS Response:**  
  After transcribing the user’s speech, SARA queries the Gemini API (with a system prompt) and displays the response in the chat. The Gemini response is converted to speech via Google TTS and played back automatically.

## Installation

1. **Install Dependencies**

   ```
   pip install -r requirements.txt
   ```

2. **Install System Dependencies**

   PortAudio (for PyAudio):

   - On macOS:
     ```
     brew install portaudio
     ```
   - On Ubuntu:
     ```
     sudo apt-get install portaudio19-dev
     ```

   FFmpeg (for Whisper):

   - On macOS:
     ```
     brew install ffmpeg
     ```
   - On Ubuntu:
     ```
     sudo apt-get install ffmpeg
     ```
   - On Windows, download and install FFmpeg from ffmpeg.org and add it to your PATH.

## File Structure

```
csci3280-project/
├── app.py                # Flask backend for the web UI
├── sara_utils.py         # Utility functions: ASR (Whisper), Gemini API call, and TTS (gTTS)
├── templates/
│   └── index.html        # HTML for the user interface
└── static/
    ├── style.css         # CSS styling for the UI
    └── script.js         # JavaScript for UI interactions and audio recording
```

## Usage

1. **Run the Flask Backend:**

```
python app.py
```

The server will start (by default on http://127.0.0.1:5000).

2. **Open the Web UI:** Open your browser and navigate to http://127.0.0.1:5000.

Home page: displays a welcoming message.

Chat page: The input field and buttons are fixed at the bottom. Once the user sends a message (typed or voice), the greeting is replaced by the chat box. User messages appear on the right, and Gemini responses appear on the left. The text input field auto-grows, and the chat box height adjusts so its bottom is near the input area.

3. **Interact with SARA:**

- Text Input: Type your message and press Submit. The message will be displayed and SARA’s response will be shown and played.

- Voice Input: Click Voice Input to start recording, then click Finish to stop recording and send the audio. The transcribed text and SARA’s response will be displayed and played.

4. **Exit:** Press Ctrl+C in the terminal to stop the Flask server.
