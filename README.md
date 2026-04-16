# 🎓 Emotion-Aware Tutoring Agent

A real-time AI tutoring system that adapts learning content based on a learner’s **facial emotions** and **behavioral responses**.

---

## 🚀 Overview

This project implements a **closed-loop adaptive learning system**:

```
Emotion Detection → Pedagogical Decision → Content Adaptation → Feedback → Loop
```

It continuously monitors the learner and adjusts difficulty, hints, and explanations in real time.

---

## 🧠 Features

* 🎥 **Facial Emotion Detection** (MediaPipe FaceMesh)
* ⌨️ **Behavior Analysis** (answer correctness + response time)
* 🔀 **Multimodal Fusion** (face + behavior → final emotion)
* 🎯 **Adaptive Tutoring** (dynamic difficulty & hints)
* 📊 **Engagement Timeline Graph**
* ⚡ **Latency Tracking (<100ms target concept)**
* 📈 **Tutor Response Score**

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Frontend:** HTML, JavaScript
* **Computer Vision:** MediaPipe, OpenCV
* **Visualization:** Chart.js

---

## 📂 Project Structure

```
backend/
  app.py
  emotion.py
  logic.py
  behavior.py
  fusion.py

frontend/
  index.html
  script.js
```

---

## ▶️ How to Run

```bash
pip install -r requirements.txt
python backend/app.py
```

Open in browser:

```
http://127.0.0.1:5000/
```

---

## 🎯 Demo Flow

1. System detects learner emotion via webcam
2. User answers a question
3. Behavior + emotion are fused
4. Tutor adapts difficulty/hints
5. Engagement is tracked over time

---

## 📊 Evaluation Focus

* Emotion detection responsiveness
* Adaptation quality
* Engagement improvement (timeline)
* System latency

---

## 🏁 Status

✔ Multimodal closed-loop system implemented
✔ Real-time adaptation working
⚠ Future: LLM-based explanations, cognitive load scoring

---

## 👥 Team

Hackathon Project – Adaptive Learning AI
