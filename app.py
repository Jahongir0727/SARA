from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from sara_utils import transcribe_audio_file, call_gemini, speak
from collections import deque

app = Flask(__name__)
CHAT_HISTORY_MAX_LENGTH = 6  # Stores 3 exchanges (user + assistant)
chat_history = deque(maxlen=CHAT_HISTORY_MAX_LENGTH)

# Ensure static directory exists
if not os.path.exists("static"):
    os.makedirs("static")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/text', methods=['POST'])
def handle_text():
    user_input = request.json.get('message', '')
    print(f"[User] {user_input}")
    reply, tone = call_gemini(list(chat_history), user_input)
    print(f"[SARA] {reply} (Tone: {tone})")
    chat_history.append({'role': 'user', 'parts': [{'text': user_input}]})
    chat_history.append({'role': 'model', 'parts': [{'text': reply}]})
    speak(reply, "static/response.mp3", tone)
    return jsonify({"response": reply})

@app.route('/audio', methods=['POST'])
def audio_input():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio part in request"}), 400

        audio_file = request.files['audio']
        audio_path = "temp_audio.wav"
        audio_file.save(audio_path)

        transcription = transcribe_audio_file(audio_path)
        print(f"[Transcription] {transcription}")

        if transcription.strip() == "":
            return jsonify({"response": "[No speech detected]"}), 200

        reply, tone = call_gemini(list(chat_history), transcription)
        print(f"[SARA] {reply} (Tone: {tone})")
        chat_history.append({'role': 'user', 'parts': [{'text': transcription}]})
        chat_history.append({'role': 'model', 'parts': [{'text': reply}]})
        speak(reply, "static/response.mp3", tone)
        return jsonify({"transcription": transcription, "response": reply})
    except Exception as e:
        print("[ERROR]", e)
        return jsonify({"error": str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)