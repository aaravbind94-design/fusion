import os, time, threading
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from dotenv import dotenv_values

# Import your modules
from main_chatbot import ChatBot
from realtime_search import RealtimeSearchEngine
from speech import text_to_speech, stop_speech
from voice import trans_hindi_to_english
import speech_recognition as sr

# ================= Load ENV =================
env = dotenv_values(".env")
Username = env.get("Username", "User")
Assistantname = env.get("Assistantname", "SmartAssistant")

# ================= Chat Logs =================
os.makedirs("Data", exist_ok=True)
CHAT_LOG_FILE = "Data/ChatLog.json"

def load_chat():
    import json
    try:
        with open(CHAT_LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return []

# ================= Flask App =================
app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# --- Global stop flags ---
stream_stop_flag = threading.Event()
listening_flag = threading.Event()  # controls /listen input

@app.route("/")
def root():
    return send_from_directory("static", "index.html")

# --- Normal Chat ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"error":"Empty message"}), 400

    try:
        stop_speech()
        stream_stop_flag.set()   # stop old streams
        stream_stop_flag.clear() # reset for new stream

        if any(k in msg.lower() for k in ["search","google","latest","news","find"]):
            reply = RealtimeSearchEngine(msg)
        else:
            reply = ChatBot(msg)

        # Start TTS in separate thread
        threading.Thread(target=text_to_speech, args=(reply,), daemon=True).start()

        # Stream reply word by word
        words, delay = reply.split(), 0.5
        def generate():
            for w in words:
                if stream_stop_flag.is_set():
                    break
                yield w+" "
                time.sleep(delay)
        return Response(generate(), mimetype="text/plain")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Hindi Voice → English → ChatBot/Search + TTS ---
@app.route("/listen", methods=["POST"])
def listen_hindi():
    try:
        listening_flag.set()
        stop_speech()
        stream_stop_flag.set()
        stream_stop_flag.clear()

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print("🎙 Listening in Hindi...")
            audio = recognizer.listen(source, timeout=10)

            if not listening_flag.is_set():
                return jsonify({"status":"Voice input cancelled"}), 200

            text = recognizer.recognize_google(audio, language="hi-IN")
            english_query = trans_hindi_to_english(text)

        # ✅ Use search engine if keywords are present
        if any(k in english_query.lower() for k in ["search","google","latest","news","find"]):
            reply = RealtimeSearchEngine(english_query)
        else:
            reply = ChatBot(english_query)

        # ✅ Start TTS
        threading.Thread(target=text_to_speech, args=(reply,), daemon=True).start()

        # ✅ Stream back to client
        words, delay = reply.split(), 0.5
        def generate():
            yield f"[You]: {english_query}\n"
            for w in words:
                if stream_stop_flag.is_set():
                    break
                yield w+" "
                time.sleep(delay)
        listening_flag.clear()
        return Response(generate(), mimetype="text/plain")

    except Exception as e:
        listening_flag.clear()
        return jsonify({"error": str(e)}), 500

# --- Chat History ---
@app.route("/history", methods=["GET"])
def history():
    try:
        messages = load_chat()
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Universal Stop ---
@app.route("/stop", methods=["POST"])
def stop_all():
    # Stop TTS and streaming
    stream_stop_flag.set()
    stop_speech()
    listening_flag.clear()  # stop voice input if running
    return jsonify({"status": "stopped"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
