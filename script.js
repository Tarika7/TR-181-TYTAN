// Global state
let currentState = {
    uploaded_topic_data: null,
    uploaded_questions: null,
    session_duration: 15,
    session_active: false,
    current_emotion: 'Engaged',
    interaction_count: 0,
    correct_count: 0,
    distraction_count: 0,
    current_topic_id: null,
    question_start_time: null,
    chart: null,
    emotion_history: [],
    session_id: null
};

// ============================================================================
// PAGE MANAGEMENT
// ============================================================================

function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(pageName).classList.add('active');
}

function goToUpload() {
    showPage('uploadPage');
    resetUploadUI();
}

function goToSessionConfig() {
    showPage('sessionPage');
    document.getElementById('topicCount').textContent = currentState.uploaded_topic_data.topics.length;
    initCameraPreview();
}

function goToLearning() {
    showPage('learningPage');
    initChart();
    initWebcam();
    startLearningLoop();
}

function goToSummary() {
    showPage('summaryPage');
    displaySessionSummary();
}

// ============================================================================
// FILE UPLOAD & PDF PROCESSING
// ============================================================================

function resetUploadUI() {
    document.getElementById('uploadStatus').classList.add('hidden');
    document.getElementById('uploadError').classList.add('hidden');
    document.getElementById('uploadSuccess').classList.add('hidden');
    document.getElementById('dropZone').style.display = 'block';
}

const dropZone = document.getElementById('dropZone');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.background = '#f0f0f0';
});

dropZone.addEventListener('dragleave', () => {
    dropZone.style.background = '';
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.background = '';
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadPDF(files[0]);
    }
});

document.getElementById('pdfInput').addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadPDF(e.target.files[0]);
    }
});

async function uploadPDF(file) {
    // Check file extension (more reliable than file.type)
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showError('Please upload a PDF file');
        return;
    }

    console.log('📤 Uploading file:', file.name, file.size, 'bytes');
    showStateLoading('uploadStatus', 'Uploading and processing PDF...');

    const formData = new FormData();
    formData.append('file', file);

    try {
        console.log('Sending fetch request to /upload_pdf');
        const response = await fetch('/upload_pdf', {
            method: 'POST',
            body: formData
        });

        console.log('Response received:', response.status, response.statusText);

        if (!response.ok) {
            let errorMsg = 'Upload failed';
            try {
                const error = await response.json();
                errorMsg = error.error || errorMsg;
            } catch (e) {
                errorMsg = `Server error: ${response.status}`;
            }
            throw new Error(errorMsg);
        }

        const data = await response.json();
        console.log('✅ PDF processed successfully. Topics:', data.topics);

        currentState.uploaded_topic_data = data.topic_data;
        currentState.uploaded_questions = data.questions;

        showStateSuccess('uploadSuccess', `
            <h3>✅ Content Loaded Successfully!</h3>
            <div class="topic-details">
                <p><strong>Main Topic:</strong> ${data.main_topic}</p>
                <p><strong>Topics Found:</strong> ${data.topics}</p>
                <p><strong>Estimated Duration:</strong> ${data.estimated_duration} minutes</p>
                <div class="objectives">
                    <strong>Learning Objectives:</strong>
                    <ul>${data.learning_objectives.map(obj => `<li>${obj}</li>`).join('')}</ul>
                </div>
            </div>
        `);

        document.getElementById('dropZone').style.display = 'none';

    } catch (error) {
        console.error('❌ Upload error:', error);
        showError(error.message || 'Failed to process PDF');
    }
}

function showStateLoading(elementId, message) {
    document.getElementById('uploadStatus').classList.remove('hidden');
    document.getElementById('uploadError').classList.add('hidden');
    document.getElementById('uploadSuccess').classList.add('hidden');
    document.getElementById('statusText').textContent = message;
}

function showStateSuccess(elementId, html) {
    document.getElementById('uploadStatus').classList.add('hidden');
    document.getElementById('uploadError').classList.add('hidden');
    document.getElementById(elementId).classList.remove('hidden');
    document.getElementById('topicDetails').innerHTML = html;
}

function showError(message) {
    document.getElementById('uploadStatus').classList.add('hidden');
    document.getElementById('uploadSuccess').classList.add('hidden');
    document.getElementById('uploadError').classList.remove('hidden');
    document.getElementById('errorText').textContent = '❌ ' + message;
}

// ============================================================================
// SESSION CONFIGURATION
// ============================================================================

function updateDuration(minutes) {
    currentState.session_duration = minutes;
    document.getElementById('durationDisplay').textContent = minutes + ' min';
}

let cameraStream;

async function initCameraPreview() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = document.getElementById('cameraPreview');
        video.srcObject = cameraStream;
        document.getElementById('cameraStatus').textContent = '✅ Camera ready';
    } catch (error) {
        document.getElementById('cameraStatus').textContent = '❌ Camera access denied';
    }
}

async function startLearning() {
    if (!currentState.uploaded_topic_data) {
        alert('Please upload a PDF first');
        return;
    }

    // Create session
    try {
        const response = await fetch('/create_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic_data: currentState.uploaded_topic_data,
                questions: currentState.uploaded_questions,
                time_minutes: currentState.session_duration
            })
        });

        if (!response.ok) throw new Error('Failed to create session');

        const data = await response.json();
        currentState.session_id = data.session_id;
        currentState.session_active = true;

        // Get first topic
        const topics = currentState.uploaded_topic_data.topics;
        if (topics.length > 0) {
            currentState.current_topic_id = topics[0].id;
        }

        goToLearning();

    } catch (error) {
        alert('Failed to start session: ' + error.message);
    }
}

// ============================================================================
// LEARNING SESSION
// ============================================================================

let webcamStream;
let learningInterval;
let timerInterval;

async function initWebcam() {
    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
        document.getElementById('webcam').srcObject = webcamStream;
        document.getElementById('webcamStatus').textContent = 'Camera active ✅';
    } catch (error) {
        document.getElementById('webcamStatus').textContent = 'Camera failed ❌';
    }
}

function initChart() {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    currentState.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Emotion Level',
                data: [],
                fill: true,
                borderColor: 'rgba(102, 126, 234, 1)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 4,
                    ticks: {
                        callback: (value) => {
                            const emotions = ['', 'Bored', 'Frustrated', 'Confused', 'Engaged'];
                            return emotions[value] || '';
                        }
                    }
                }
            }
        }
    });
}

function emotionToNumber(emotion) {
    const map = { 'Bored': 1, 'Frustrated': 2, 'Confused': 3, 'Engaged': 4 };
    return map[emotion] || 2;
}

function startLearningLoop() {
    startSessionTimer();

    learningInterval = setInterval(async () => {
        if (!currentState.session_active) {
            clearInterval(learningInterval);
            return;
        }

        try {
            const response = await fetch('/get_state_advanced', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic_id: currentState.current_topic_id
                })
            });

            const data = await response.json();

            // Handle distraction block
            if (data.blocked) {
                showDistractionBlock(data);
                return;
            }

            currentState.current_emotion = data.emotion;
            
            // Update UI
            updateEmotionDisplay(data.emotion);
            document.getElementById('strategyText').textContent = 
                data.teaching_strategy.name + ': ' + data.teaching_strategy.description;
            document.getElementById('latencyValue').textContent = data.latency_ms + 'ms';

            // Show question
            if (data.question) {
                document.getElementById('questionBox').style.display = 'block';
                document.getElementById('questionText').textContent = data.question;
                document.getElementById('answer').value = '';
                currentState.question_start_time = Date.now();
            }

            // Update chart
            currentState.emotion_history.push(data.emotion);
            if (currentState.chart) {
                currentState.chart.data.labels = currentState.emotion_history.map((_, i) => i);
                currentState.chart.data.datasets[0].data = currentState.emotion_history.map(emotionToNumber);
                currentState.chart.update();
            }

            // Handle distraction warning
            if (data.has_distractions) {
                currentState.distraction_count++;
                updateDistractionCounter();
            }

        } catch (error) {
            console.error('Error:', error);
        }

    }, 3000); // Update every 3 seconds
}

function showDistractionBlock(data) {
    document.getElementById('blockingOverlay').style.display = 'flex';
    document.getElementById('blockingMessage').textContent = data.message;

    const timeRemaining = Math.ceil(data.time_remaining || 5);
    let countdown = timeRemaining;

    const countdownInterval = setInterval(() => {
        document.getElementById('blockingTimer').textContent = countdown;
        countdown--;

        if (countdown < 0) {
            clearInterval(countdownInterval);
            document.getElementById('blockingOverlay').style.display = 'none';
        }
    }, 1000);
}

function updateEmotionDisplay(emotion) {
    const emotionMap = {
        'Engaged': '😊',
        'Confused': '🤔',
        'Frustrated': '😞',
        'Bored': '😴',
        'Distracted': '📱'
    };

    document.getElementById('emotionCircle').textContent = emotionMap[emotion] || '😐';
    document.getElementById('emotionName').textContent = emotion;
}

function updateDistractionCounter() {
    document.getElementById('distractionCount').textContent = currentState.distraction_count;
}

function handleKeyDown(event) {
    if (event.key === 'Enter') {
        submitAnswer();
    }
}

async function submitAnswer() {
    const answer = document.getElementById('answer').value.trim();
    if (!answer) return;

    const time_taken = (Date.now() - currentState.question_start_time) / 1000;

    try {
        const response = await fetch('/submit_answer_advanced', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                answer: answer,
                topic_id: currentState.current_topic_id,
                emotion: currentState.current_emotion,
                time_taken: time_taken,
                has_distraction: currentState.distraction_count > 0
            })
        });

        const data = await response.json();

        currentState.interaction_count++;
        if (data.is_correct) {
            currentState.correct_count++;
            document.getElementById('feedback').innerHTML = '✓ Correct!';
        } else {
            document.getElementById('feedback').innerHTML = `✗ Not quite. Expected: ${data.expected_answer}`;
        }

        // Update stats
        document.getElementById('interactionCount').textContent = currentState.interaction_count;
        const rate = Math.round((currentState.correct_count / currentState.interaction_count) * 100);
        document.getElementById('correctnessRate').textContent = rate + '%';

        // Show challenge if earned
        if (data.offer_challenge && data.challenge_question) {
            showChallenge(data.challenge_question);
        }

    } catch (error) {
        console.error('Error:', error);
    }
}

function showChallenge(challenge) {
    document.getElementById('challengeSection').style.display = 'block';
    document.getElementById('challengeText').textContent = challenge.question;
}

async function submitChallenge() {
    // Similar to submitAnswer but for challenge
    const answer = document.getElementById('challengeAnswer').value.trim();
    if (!answer) return;

    try {
        const response = await fetch('/submit_answer_advanced', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                answer: answer,
                topic_id: currentState.current_topic_id + '_challenge',
                emotion: 'Engaged',
                time_taken: 60,
                has_distraction: false
            })
        });

        document.getElementById('challengeSection').style.display = 'none';

    } catch (error) {
        console.error('Error:', error);
    }
}

function startSessionTimer() {
    let remaining = currentState.session_duration * 60;

    timerInterval = setInterval(() => {
        remaining--;

        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        document.getElementById('timerDisplay').textContent = 
            `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

        const progress = ((currentState.session_duration * 60 - remaining) / (currentState.session_duration * 60)) * 100;
        document.getElementById('progressFill').style.width = progress + '%';
        document.getElementById('progressText').textContent = Math.round(progress) + '% complete';

        if (remaining <= 0) {
            clearInterval(timerInterval);
            currentState.session_active = false;
            endSession();
        }
    }, 1000);
}

// ============================================================================
// SESSION SUMMARY
// ============================================================================

async function endSession() {
    if (learningInterval) clearInterval(learningInterval);
    if (timerInterval) clearInterval(timerInterval);

    try {
        const response = await fetch('/end_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        currentState.summary = data.summary;
        goToSummary();

    } catch (error) {
        alert('Error ending session: ' + error.message);
    }
}

function displaySessionSummary() {
    const summary = currentState.summary;

    document.getElementById('summaryDuration').textContent = 
        Math.floor(summary.duration_seconds / 60) + ':' + 
        String(summary.duration_seconds % 60).padStart(2, '0');

    document.getElementById('summaryAccuracy').textContent = summary.correctness_rate + '%';
    document.getElementById('summaryInteractions').textContent = summary.total_interactions;
    document.getElementById('summaryDistractions').textContent = summary.distraction_events.length;

    // Emotion distribution
    const emotionDist = summary.emotion_distribution;
    let emotionHTML = '<div class="emotion-grid">';
    for (const [emotion, count] of Object.entries(emotionDist)) {
        const percent = Math.round((count / summary.total_interactions) * 100);
        emotionHTML += `
            <div class="emotion-stat">
                <p>${emotion}: ${percent}%</p>
                <div class="bar" style="width: ${percent}%"></div>
            </div>
        `;
    }
    emotionHTML += '</div>';
    document.getElementById('emotionSummary').innerHTML = emotionHTML;

    // Topic mastery
    let topicHTML = '<div class="topic-list">';
    for (const [topic, data] of Object.entries(summary.topic_mastery)) {
        const mastery = data.mastery_score;
        const color = mastery >= 80 ? 'green' : mastery >= 50 ? 'yellow' : 'red';
        topicHTML += `
            <div class="topic-stat">
                <p>${topic}<span class="mastery-${color}">${Math.round(mastery)}%</span></p>
                <div class="progress" style="background: var(--color-${color});" 
                     style="width: ${mastery}%"></div>
            </div>
        `;
    }
    topicHTML += '</div>';
    document.getElementById('topicMastery').innerHTML = topicHTML;

    document.getElementById('recommendation').textContent = summary.recommendation;
}

function newSession() {
    currentState = {
        uploaded_topic_data: null,
        uploaded_questions: null,
        session_duration: 15,
        session_active: false,
        current_emotion: 'Engaged',
        interaction_count: 0,
        correct_count: 0,
        distraction_count: 0,
        current_topic_id: null,
        question_start_time: null,
        chart: null,
        emotion_history: [],
        session_id: null
    };
    goToUpload();
}

function downloadReport() {
    console.log('Report download initiated');
    // Implement PDF generation here
}

// Initialize on page load
window.addEventListener('load', () => {
    showPage('uploadPage');
});
