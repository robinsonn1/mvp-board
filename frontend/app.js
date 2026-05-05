async function updateStatus() {
    const res = await fetch("/match/1/status");
    const data = await res.json();

    document.getElementById("score").innerText = data.score;
    document.getElementById("minute").innerText = data.minute + "'";
}

async function updateImpact() {
    const res = await fetch("/match/1/impact");
    const data = await res.json();

    const container = document.getElementById("players");
    const top3 = document.getElementById("top3");

    container.innerHTML = "";
    top3.innerHTML = "";

    const max = Math.max(...data.map(p => p.impact_score)) || 1;

    data.forEach((p, index) => {
        const width = (p.impact_score / max) * 100;

        const div = document.createElement("div");
        div.className = `player ${p.team}`;

        div.innerHTML = `
            <div class="name">${p.icons || ""} ${p.name}</div>
            <div style="flex:1; margin:0 10px;">
                <div class="bar" style="width:${width}%; background:${p.team === "Spain" ? "red" : "blue"}"></div>
            </div>
            <div class="scoreval">${p.impact_score}</div>
        `;

        container.appendChild(div);

        if (index < 3) {
            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = `
                <div class="avatar"></div>
                <div>${p.name}</div>
                <div class="pos">${p.position}</div>
                <div>🔥 ${p.impact_score}</div>
            `;
            top3.appendChild(card);
        }
    });
}

async function updateFeed() {
    const res = await fetch("/match/1/feed");
    const data = await res.json();

    const feed = document.getElementById("feed");
    feed.innerHTML = "";

    data.forEach(e => {
        const div = document.createElement("div");
        div.className = "feed-item";
        div.innerText = `${e.minute}' - ${e.event.toUpperCase()} - ${e.player} (${e.team})`;
        feed.appendChild(div);
    });
}

async function updateStats() {
    const res = await fetch("/match/1/stats");
    const data = await res.json();

    document.getElementById("shots").innerText = data.shots;
    document.getElementById("goals").innerText = data.goals;
    document.getElementById("fouls").innerText = data.fouls;
}

function loop() {
    updateStatus();
    updateImpact();
    updateFeed();
    updateStats();
}

setInterval(loop, 2000);
loop();

const ws = new WebSocket("ws://127.0.0.1:8000/ws");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    console.log("LIVE UPDATE:", data);

    // optional: instant UI update trigger
    updateStatus();
    updateImpact();
    updateFeed();
    updateStats();
};