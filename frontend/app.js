async function updateStatus() {
    const res = await fetch("/match/1/status");
    const data = await res.json();

    document.getElementById("score").innerText = data.score;
    document.getElementById("minute").innerText = data.minute + "'";
    document.getElementById("teams").innerText = `${data.home} vs ${data.away}`;
}

async function updateImpact() {
    const res = await fetch("/match/1/impact");
    const data = await res.json();

    const players = data.players || [];

    const container = document.getElementById("players");
    const top3 = document.getElementById("top3");

    container.innerHTML = "";
    top3.innerHTML = "";

    const max = Math.max(...players.map(p => p.impact_score)) || 1;

    players.forEach((p, i) => {

        const width = (p.impact_score / max) * 100;

        const div = document.createElement("div");
        div.className = `player ${p.team}`;

        div.innerHTML = `
            <div class="name">
                ${i+1}. #${p.number} ${p.flag} ${p.name} ${p.icons || ""}
            </div>

            <div style="flex:1; margin:0 10px;">
                <div class="bar" style="width:${width}%"></div>
            </div>

            <div class="scoreval">${p.impact_score.toFixed(1)}</div>
        `;

        container.appendChild(div);

        if (i < 3) {
            const card = document.createElement("div");
            card.className = "card";

            card.innerHTML = `
                <div class="avatar"></div>
                <div>${p.name}</div>
                <div>${p.position}</div>
                <div>🔥 ${p.impact_score.toFixed(1)}</div>
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
        div.innerText = `${e.minute}' - ${e.event.toUpperCase()} - ${e.player}`;
        feed.appendChild(div);
    });
}

async function updateStats() {
    const res = await fetch("/match/1/stats");
    const data = await res.json();

    document.getElementById("goals").innerText = data.goals;
    document.getElementById("shots").innerText = data.shots;
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

ws.onmessage = () => {
    loop();
};