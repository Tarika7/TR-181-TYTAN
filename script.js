async function update() {
    try {
        const res = await fetch("/get_state");
        const data = await res.json();

        console.log("API:", data);

        if (data.error) {
            document.getElementById("emotion").innerText =
                "Emotion: Camera Error";

            document.getElementById("decision").innerText =
                "System Action: Waiting...";

            document.getElementById("question").innerText =
                "Question: Check camera";

            return;
        }

        document.getElementById("emotion").innerText =
            "Emotion: " + data.emotion;

        document.getElementById("decision").innerText =
            "System Action: " + data.action;

        document.getElementById("question").innerText =
            "Question: " + data.question;

    } catch (err) {
        console.error(err);
    }
}

// Auto loop every 3 seconds (stable)
setInterval(update, 3000);

// Run immediately
update();