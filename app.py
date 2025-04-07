from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from sara_utils import transcribe_audio_file, call_gemini, speak

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/text', methods=['POST'])
def handle_text():
    user_input = request.json.get('message', '')
    print(f"[User] {user_input}")
    reply = call_gemini(user_input)
    print(f"[SARA] {reply}")
    speak(reply, "static/response.mp3")
    return jsonify({"response": reply})

@app.route('/audio', methods=['POST'])
def audio_input():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio part in request"}), 400

        audio_file = request.files['audio']
        audio_path = "temp_audio.wav"
        audio_file.save(audio_path)

        print("[INFO] Audio file received and saved.")
        transcription = transcribe_audio_file(audio_path)
        print(f"[Transcription] {transcription}")

        if transcription.strip() == "":
            return jsonify({"response": "[No speech detected]"}), 200

        reply = call_gemini(transcription)
        print(f"[SARA] {reply}")
        speak(reply, "static/response.mp3")
        return jsonify({"transcription": transcription, "response": reply})
    except Exception as e:
        print("[ERROR]", e)
        return jsonify({"error": str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)
