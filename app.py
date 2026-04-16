from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import cv2

from emotion import get_emotion
from logic import get_next_question

app = Flask(__name__, static_folder="../frontend")
CORS(app)

# Serve frontend
@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

# Main API
@app.route("/get_state")
def get_state():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        return jsonify({"error": "Camera not accessible"})

    ret, frame = cap.read()
    cap.release()

    print("RET:", ret)

    if not ret:
        return jsonify({"error": "Camera read failed"})

    emotion = get_emotion(frame)
    action, question = get_next_question(emotion)

    print("Emotion:", emotion)

    return jsonify({
        "emotion": emotion or "No Face",
        "action": action or "Waiting",
        "question": question or "No question"
    })

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)