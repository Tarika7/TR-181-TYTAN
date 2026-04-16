let chart;

function initChart() {
    const ctx = document.getElementById("chart").getContext("2d");

    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Emotion",
                data: [],
                fill: false
            }]
        }
    });
}

function emotionToNumber(e) {
    if (e === "Engaged") return 4;
    if (e === "Confused") return 3;
    if (e === "Frustrated") return 2;
    if (e === "Bored") return 1;
    return 0;
}

async function update() {
    const res = await fetch("/get_state");
    const data = await res.json();

    if (data.error) return;

    document.getElementById("emotion").innerText =
        "Emotion: " + data.emotion;

    document.getElementById("decision").innerText =
        "System Action: " + data.action;

    document.getElementById("question").innerText =
        "Question: " + data.question;

    // 📊 update chart
    const labels = data.timeline.map((_, i) => i);
    const values = data.timeline.map(t => emotionToNumber(t.emotion));

    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();
}

// submit answer
async function submitAnswer() {
    const answer = document.getElementById("answer").value;

    const res = await fetch("/submit_answer", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ answer })
    });

    const data = await res.json();

    document.getElementById("result").innerText =
        "Result: " + data.result;

    document.getElementById("behavior").innerText =
        "Behavior Emotion: " + data.behavior_emotion;
}

// init
initChart();
setInterval(update, 3000);
update();
