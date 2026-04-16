from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import cv2
import time
import sys
import os
import uuid
import base64
import numpy as np
from werkzeug.utils import secure_filename

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from emotion import get_emotion
from logic import get_next_question, get_current_answer
from claude import generate_dynamic_lesson
from cognitive import cognitive_score
from fusion import fuse_emotions, tutor_score

# Try to import optional modules; they'll be needed for full functionality
try:
    from pdf_processor import process_pdf_to_topic_graph
except ImportError as e:
    print(f"Warning: PDF processor not available: {e}")
    process_pdf_to_topic_graph = None

try:
    from distraction_detector import detector
except ImportError as e:
    print(f"Warning: Distraction detector not available (ultralytics still installing): {e}")
    detector = None

from session_manager import session_manager
from fusion_advanced import fuse_emotions as fuse_emotions_advanced, get_intervention_message
from challenge_quiz import ChallengeQuizGenerator

app = Flask(__name__, static_folder="../frontend")
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global state
last_behavior = "Engaged"
timeline = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================================
# ORIGINAL ENDPOINTS (backward compatible)
# ============================================================================

@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route("/get_state")
def get_state():
    """Legacy: emotion detection without session"""
    global last_behavior
    start = time.time()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({"error": "Camera failed"})

    face_emotion = get_emotion(frame)
    final_emotion = fuse_emotions(face_emotion, last_behavior)
    action, question = get_next_question(final_emotion)

    timeline.append({"time": time.time(), "emotion": final_emotion})
    if len(timeline) > 20:
        timeline.pop(0)

    latency = round((time.time() - start)*1000, 2)
    score = tutor_score(face_emotion, final_emotion)

    return jsonify({
        "emotion": final_emotion,
        "action": action,
        "question": question,
        "timeline": timeline,
        "latency": latency,
        "score": score
    })

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    """Legacy: answer submission"""
    global last_behavior
    data = request.json
    user_answer = data.get("answer")
    current_emotion = data.get("emotion", "Engaged")
    correct = get_current_answer()

    behavior_emotion = cognitive_score(user_answer, correct, current_emotion)
    last_behavior = behavior_emotion

    return jsonify({
        "result": "Correct" if user_answer == correct else "Wrong",
        "behavior_emotion": behavior_emotion
    })

@app.route("/get_analytics")
def get_analytics():
    """Analytics endpoint"""
    from logic import learner_history

    if not learner_history:
        return jsonify({
            "total_sessions": 0,
            "emotion_distribution": {},
            "average_correctness": 0,
            "average_time": 0,
            "topic_performance": {}
        })

    total_sessions = len(learner_history)
    emotion_counts = {}
    correct_count = 0
    total_time = 0
    topic_performance = {}

    for entry in learner_history:
        emotion = entry["emotion"]
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        if entry["correct"]:
            correct_count += 1
        total_time += entry["time_taken"]
        topic = entry["topic"]
        if topic not in topic_performance:
            topic_performance[topic] = {"correct": 0, "total": 0}
        topic_performance[topic]["total"] += 1
        if entry["correct"]:
            topic_performance[topic]["correct"] += 1

    for topic in topic_performance:
        correct = topic_performance[topic]["correct"]
        total = topic_performance[topic]["total"]
        topic_performance[topic]["percentage"] = round(correct / total * 100, 1) if total > 0 else 0

    return jsonify({
        "total_sessions": total_sessions,
        "emotion_distribution": emotion_counts,
        "average_correctness": round(correct_count / total_sessions * 100, 1) if total_sessions > 0 else 0,
        "average_time": round(total_time / total_sessions, 2) if total_sessions > 0 else 0,
        "topic_performance": topic_performance
    })

# ============================================================================
# NEW ENDPOINTS (PDF-based adaptive learning with distraction detection)
# ============================================================================

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    """Upload PDF and extract topics"""
    try:
        print(f"📤 Received upload request")
        print(f"Files in request: {list(request.files.keys())}")
        
        if 'file' not in request.files:
            print("❌ No file in request")
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        print(f"📄 File received: {file.filename}, size: {len(file.read())} bytes")
        file.seek(0)  # Reset file pointer
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF files allowed"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"💾 Saving file to: {filepath}")
        file.save(filepath)
        print(f"✅ File saved")

        print(f"🔍 Checking if processor available: {process_pdf_to_topic_graph is not None}")
        
        if process_pdf_to_topic_graph is None:
            print("❌ PDF processor not available")
            return jsonify({
                "error": "PDF processing not available (dependencies still installing). Please try again in a moment."
            }), 503
        
        print(f"🔄 Processing PDF: {filename}")
        topic_data = process_pdf_to_topic_graph(filepath, subject="mathematics")
        print(f"✅ Extracted {len(topic_data.get('topics', []))} topics")

        return jsonify({
            "status": "success",
            "filename": filename,
            "main_topic": topic_data.get("main_topic", "Unknown"),
            "topics": len(topic_data.get("topics", [])),
            "learning_objectives": topic_data.get("learning_objectives", []),
            "estimated_duration": topic_data.get("estimated_duration_minutes", 45),
            "topic_data": topic_data,
            "questions": {} # Send empty dict to keep frontend format compatible temporarily
        })

    except Exception as e:
        print(f"❌ ERROR in upload_pdf: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/create_session", methods=["POST"])
def create_session():
    """Create learning session"""
    try:
        data = request.json
        topic_data = data.get("topic_data")
        time_minutes = int(data.get("time_minutes", 15))

        if not topic_data:
            return jsonify({"error": "Missing topic_data"}), 400
        
        # questions is now empty dict by default - lessons are generated dynamically
        questions = data.get("questions", {})

        session_id = str(uuid.uuid4())[:8]
        result = session_manager.create_session(
            session_id=session_id,
            topic_data=topic_data,
            questions=questions,
            subject="mathematics",
            time_minutes=time_minutes
        )

        return jsonify({**result, "message": f"Session {session_id} created"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/session_info", methods=["GET"])
def get_sess_info():
    """Get session info"""
    info = session_manager.get_session_info()
    return jsonify(info)

@app.route("/get_state_advanced", methods=["POST"])
def get_state_advanced():
    """Real-time emotion + distraction detection"""
    try:
        data = request.json
        topic_id = data.get("topic_id", "unknown")
        frame_b64 = data.get("frame")

        start = time.time()
        
        if frame_b64:
            try:
                # Handle raw base64 or data uri protocol cleanly
                if ',' in frame_b64:
                    img_data = base64.b64decode(frame_b64.split(',')[1])
                else:
                    img_data = base64.b64decode(frame_b64)
                    
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                ret = True if frame is not None else False
            except Exception:
                ret = False
                frame = None
        else:
            ret = False
            frame = None

        has_distractions = False
        critical_distraction = False
        distractions = []
        
        if not ret or frame is None:
            # Drop frame gracefully without returning 400 error breaking the loop
            face_emotion = "Engaged"
        else:
            # Emotion detection
            face_emotion = get_emotion(frame)
    
            # Distraction detection (optional feature if ultralytics available)
            if detector is not None:
                distraction_result = detector.detect_distractions(frame)
                has_distractions = distraction_result['has_distractions']
                critical_distraction = distraction_result['critical_distraction']
                distractions = distraction_result['distractions']

        # Check distraction block
        block_status = session_manager.check_distraction_block()
        if block_status['blocked']:
            return jsonify({
                "blocked": True,
                "message": block_status['message'],
                "time_remaining": block_status.get('time_remaining', 0)
            })

        # Fuse emotions
        final_emotion, teaching_strategy, intervention_needed = fuse_emotions_advanced(
            face_emotion, last_behavior, has_distractions, critical_distraction
        )

        # Hard block if critical distraction
        if critical_distraction and detector is not None:
            block_result = session_manager.block_distraction(duration_seconds=5)
            distraction_msg = detector.get_distraction_message(distractions) if detector else "Distraction detected"
            return jsonify({
                "blocked": True,
                "reason": "critical_distraction",
                "message": distraction_msg,
                "distractions": distractions,
                **block_result
            })

        session_info = session_manager.get_session_info()
        mastery = session_manager.metrics.topic_mastery.get(topic_id, {})

        timeline.append({
            "timestamp": time.time(),
            "emotion": final_emotion,
            "topic": topic_id,
            "has_distractions": has_distractions
        })
        if len(timeline) > 50:
            timeline.pop(0)

        latency = round((time.time() - start) * 1000, 2)
        intervention_msg = get_intervention_message(final_emotion, has_distractions, distractions)
        strategy = teaching_strategy

        return jsonify({
            "status": "success",
            "emotion": final_emotion,
            "face_emotion": face_emotion,
            "teaching_strategy": strategy,
            "intervention_message": intervention_msg,
            "intervention_needed": intervention_needed,
            "distractions": distractions,
            "has_distractions": has_distractions,
            "latency_ms": latency,
            "session_info": session_info,
            "topic_mastery": mastery,
            "timeline": timeline[-10:]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/get_next_lesson", methods=["POST"])
def get_next_lesson():
    """Dynamically generate tailored teachings and questions"""
    try:
        data = request.json
        topic_id = data.get("topic_id")
        emotion = data.get("emotion", "Engaged")
        
        session_info = session_manager.get_session_info()
        topics = session_info.get("topic_data", {}).get("topics", [])
        
        topic_data = next((t for t in topics if t.get("id") == topic_id), None)
        if not topic_data:
            return jsonify({"error": "Topic not found"}), 404
            
        print(f"Generating lesson for {topic_id} adapted to {emotion}")
        lesson_data = generate_dynamic_lesson(topic_data, emotion)
        
        if topic_id not in session_manager.metrics.topic_mastery:
            session_manager.metrics.topic_mastery[topic_id] = {
                'questions_asked': 0, 'correct_answers': 0, 'mastery_score': 0.0, 
                'difficulty_level': 1, 'current_q_index': 0, 'expected_answer': ''
            }
            
        session_manager.metrics.topic_mastery[topic_id]['expected_answer'] = lesson_data.get('answer', '')
        
        return jsonify(lesson_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/submit_answer_advanced", methods=["POST"])
def submit_answer_advanced():
    """Submit answer with full tracking"""
    try:
        global last_behavior
        data = request.json
        user_answer = data.get("answer")
        topic_id = data.get("topic_id", "unknown")
        current_emotion = data.get("emotion", "Engaged")
        time_taken = data.get("time_taken", 0)

        expected = session_manager.metrics.topic_mastery.get(topic_id, {}).get('expected_answer', '')
        if not expected:
            # No expected answer stored - treat as open ended, always correct
            is_correct = True
        else:
            # Fuzzy matching: check if any word from expected answer appears in user answer
            user_words = set(str(user_answer).strip().lower().split())
            expected_words = set(str(expected).strip().lower().split())
            # Exact match or at least 1 meaningful word overlap (excluding stopwords)
            stopwords = {'the','a','an','is','are','was','were','of','in','to','and','or','for','it','this','that'}
            meaningful_expected = expected_words - stopwords
            meaningful_user = user_words - stopwords
            exact = str(user_answer).strip().lower() == str(expected).strip().lower()
            overlap = len(meaningful_expected & meaningful_user) >= 1 if meaningful_expected else True
            is_correct = exact or overlap

        behavior_emotion = cognitive_score(user_answer, expected, current_emotion)
        last_behavior = behavior_emotion

        has_distraction = data.get("has_distraction", False)
        session_manager.record_interaction(
            topic_id=topic_id,
            correct=is_correct,
            emotion=current_emotion,
            time_taken=time_taken,
            distraction_detected=has_distraction
        )

        # Check for challenge quiz
        mastery = session_manager.metrics.topic_mastery.get(topic_id, {})
        offer_challenge = False
        challenge_question = None

        if mastery.get('correct_answers', 0) >= 2 and is_correct and current_emotion == "Engaged":
            offer_challenge = True
            topic_data = session_manager.current_session.topic_data
            topics = topic_data.get('topics', [])
            current_topic = next((t for t in topics if t['id'] == topic_id), None)

            if current_topic:
                challenge_question = ChallengeQuizGenerator.generate_challenge_question(current_topic)

        return jsonify({
            "status": "success",
            "result": "Correct ✓" if is_correct else "Not quite - keep trying!",
            "is_correct": is_correct,
            "behavior_emotion": behavior_emotion,
            "expected_answer": expected,
            "offer_challenge": offer_challenge,
            "challenge_question": challenge_question,
            "mastery_update": mastery,
            "emotion_adaptation": f"Lesson adapted to your current mood: {current_emotion}" if current_emotion != "Engaged" else None
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_challenge", methods=["POST"])
def get_challenge():
    """Get challenge question"""
    try:
        data = request.json
        topic_id = data.get("topic_id")

        if not session_manager.current_session:
            return jsonify({"error": "No session"}), 400

        topic_data = session_manager.current_session.topic_data
        topics = topic_data.get('topics', [])
        current_topic = next((t for t in topics if t['id'] == topic_id), None)

        if not current_topic:
            return jsonify({"error": "Topic not found"}), 404

        challenge = ChallengeQuizGenerator.generate_challenge_question(current_topic)

        return jsonify({
            "status": "success",
            "challenge": challenge,
            "topic_title": current_topic.get('title')
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/end_session", methods=["POST"])
def end_session():
    """End session and get summary"""
    try:
        summary = session_manager.get_session_summary()
        return jsonify({"status": "success", "summary": summary})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Emotion-Aware Tutoring Agent Starting...")
    print("📊 Ready for PDF-based adaptive learning")
    print("🌐 Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
