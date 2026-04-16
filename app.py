from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import cv2
import time

from emotion import get_emotion
from logic import get_next_question, get_current_answer
from behavior import evaluate_answer
from fusion import fuse_emotions, tutor_score

app = Flask(__name__, static_folder="../frontend")
CORS(app)

# GLOBAL STATE
last_behavior = "Engaged"
timeline = []

@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

# 👉 MAIN LOOP
@app.route("/get_state")
def get_state():
    global last_behavior

    start_time = time.time()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        return jsonify({"error": "Camera not accessible"})

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({"error": "Camera read failed"})

    face_emotion = get_emotion(frame)

    # 🔥 FUSION
    final_emotion = fuse_emotions(face_emotion, last_behavior)

    action, question = get_next_question(final_emotion)

    # 📊 Timeline
    timeline.append({
        "time": time.time(),
        "emotion": final_emotion
    })

    if len(timeline) > 20:
        timeline.pop(0)

    # ⚡ Latency
    latency = round((time.time() - start_time) * 1000, 2)

    # 🎯 Tutor score
    score = tutor_score(face_emotion, final_emotion)

    return jsonify({
        "emotion": final_emotion,
        "action": action,
        "question": question,
        "timeline": timeline,
        "latency": latency,
        "score": score
    })

# 👉 ANSWER
@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    global last_behavior

    data = request.json
    user_answer = data.get("answer")

    correct_answer = get_current_answer()

    behavior_emotion = evaluate_answer(user_answer, correct_answer)

    last_behavior = behavior_emotion  # 🔥 store globally

    return jsonify({
        "result": "Correct" if user_answer == correct_answer else "Wrong",
        "behavior_emotion": behavior_emotion
    })

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
