from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import cv2

from emotion import get_emotion
from logic import get_next_question, get_current_answer
from behavior import evaluate_answer
from fusion import fuse_emotions
import time

# store timeline
timeline = []

app = Flask(__name__, static_folder="../frontend")
CORS(app)

@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

# 👉 GET STATE (emotion loop)
@app.route("/get_state")
def get_state():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        return jsonify({"error": "Camera not accessible"})

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({"error": "Camera read failed"})

    emotion = get_emotion(frame)
    action, question = get_next_question(emotion)

    return jsonify({
        "emotion": emotion,
        "action": action,
        "question": question
    })

# 👉 NEW: ANSWER SUBMISSION
@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    data = request.json
    user_answer = data.get("answer")

    correct_answer = get_current_answer()

    behavior_emotion = evaluate_answer(user_answer, correct_answer)

    return jsonify({
        "result": "Correct" if user_answer == correct_answer else "Wrong",
        "behavior_emotion": behavior_emotion
    })

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
