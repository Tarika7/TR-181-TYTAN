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
}

// 🔥 Submit answer
async function submitAnswer() {
    const answer = document.getElementById("answer").value;

    const res = await fetch("/submit_answer", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ answer })
    });

    const data = await res.json();

    document.getElementById("result").innerText =
        "Result: " + data.result;

    document.getElementById("behavior").innerText =
        "Behavior Emotion: " + data.behavior_emotion;
}

// Auto update
setInterval(update, 3000);
update();
