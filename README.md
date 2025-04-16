# SARA: Smart Audio-Recognition Assistant

SARA is a smart voice assistant that leverages cutting-edge open-source technologies to deliver a seamless conversational experience through a modern web-based user interface. SARA integrates multiple modules to enable natural conversation, command execution, and dynamic emotional responses.

## Core Functionalities

- **ASR (Automatic Speech Recognition):**  
  Uses [Whisper](https://github.com/openai/whisper) to transcribe spoken language from your computer’s microphone into text.

- **Conversational AI:**  
  Communicates with the Gemini 2.0 Flash API to generate short, intelligent responses. A detailed system prompt guides responses to be in an appropriate tone (professional, friendly, sad, happy, angry, or even flirty) and optionally switches accents when requested.

- **TTS (Text-to-Speech):**  
  Utilizes Google Cloud’s Text-to-Speech API to convert Gemini's responses into natural-sounding audio, dynamically adjusted by tone and accent.

- **Dynamic UI with Emotion Animation:**  
  SARA’s web interface features a clean, centered chat box where:
  - User messages appear right-aligned.
  - Gemini responses appear left-aligned.
  - An emotion indicator (using Lottie animations) shows a visual cue based on the detected tone of the response.
  - The input field auto-grows as you type.

## Advanced Command Handling

In addition to regular conversation, SARA intelligently detects and executes a variety of commands embedded in natural language. Supported commands include:

- **Search Command:**  
  When the user includes "search for" in their input, SARA extracts the key query—removing extraneous trailing words like "for me", "please", or "now"—and opens your default browser with a Google search.

  _Example:_  
  _User:_ "Can you search for the busiest airports in the world for me?"  
  _Response:_ "Searching for the busiest airports in the world in your browser."

- **Time Command:**  
  SARA can provide the current time. If a location is specified (e.g., "time in New York"), the response includes that location.

  _Example:_  
  _User:_ "What is the time in New York now?"  
  _Response:_ "The current time in New York is 05:00 PM."

- **Weather Command:**  
  When a user asks about the weather (e.g., "weather in Hong Kong"), SARA retrieves real-time weather data from OpenWeatherMap and responds accordingly.

- **Note Command:**  
  Input beginning with "take a note" causes SARA to append the note to a text file.

- **Play Music Command:**  
  If the message contains "play music" anywhere, SARA opens Spotify (on Mac, using the `open` command).

## Installation

1. **Install Dependencies**

   ```
   pip install -r requirements.txt
   ```

2. **Install System Dependencies**

- **PortAudio (for PyAudio):**

  - On macOS:
    ```
    brew install portaudio
    ```
  - On Ubuntu:

    ```
    sudo apt-get install portaudio19-dev
    ```

- **FFmpeg (for Whisper):**

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
├── requirements.txt
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

2. **Open the Web UI:**

- Navigate your browser to http://127.0.0.1:5000.

- The home page will display a welcoming message with a background animation.

- The chat interface (with a fixed-width chat box and a left-side emotion animation indicator) appears once a message is sent.

3. **Interact with SARA:**

- Text Input:  
  Type your message and press Submit. Your text appears right-aligned in the chat box, and SARA’s response (with an appropriate tone and accent) appears on the left, accompanied by a matching emotion animation.

- Voice Input:  
  Click Voice Input to record your speech, then click Finish. SARA transcribes your voice, processes the input, and responds with text and audio.

- Advanced Commands:

  - Ask, "What's the time in New York now?" to get a time response with the location.

  - Say "Search for the busiest airports for me" to trigger a browser search.

  - Ask about the weather or request to play music, and SARA will execute those commands.

4. **Exit:**  
   Press Ctrl+C in the terminal to stop the Flask server.

## Additional Notes

- Emotion Animation:  
  The web UI includes a Lottie-based emotion indicator that dynamically updates based on SARA’s tone.

- Command Handling:  
  SARA uses simple regex-based matching to detect commands within natural language input, making responses more intuitive even when commands are embedded in questions.

- Customization:  
  TTS parameters and Gemini response handling support multiple tones (professional, friendly, sad, happy, angry, flirty) and accents (American, British, Australian, Indian).

## Acknowledgments

[OpenAI Whisper](https://github.com/openai/whisper)

[Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech)

[Gemini 2.0 Flash API](https://ai.google.dev/gemini-api/docs/models)

[LottieFiles](https://lottiefiles.com/)

[PyAudio](https://pypi.org/project/PyAudio/)

[webrtcvad](https://github.com/wiseman/py-webrtcvad)

[Flask](https://github.com/pallets/flask)

[OpenWeatherMap](https://openweathermap.org/)
