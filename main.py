from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import json
import random
import threading
import time
import asyncio

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend", html=True), name="frontend")

# -------------------------
# LOAD PLAYERS
# -------------------------
def load_players():
    with open("data/players.json", "r") as f:
        return json.load(f)

all_players = load_players()

# -------------------------
# MATCH SELECTION
# -------------------------
def generate_match():
    teams = list(set([p["team"] for p in all_players]))
    home, away = random.sample(teams, 2)
    match_players = [p for p in all_players if p["team"] in [home, away]]
    return home, away, match_players

HOME_TEAM, AWAY_TEAM, players = generate_match()

# -------------------------
# MATCH STATE
# -------------------------
MATCH_MINUTE = 0
HALF = 1

score = {HOME_TEAM: 0, AWAY_TEAM: 0}
impact = {p["id"]: 0 for p in players}
momentum = {p["id"]: 0 for p in players}

# NEW: stats
stats = {
    "shots": 0,
    "fouls": 0,
    "goals": 0
}

# -------------------------
# MATCH FEED
# -------------------------
events_feed = []

def log_event(player, event_type):
    global stats

    events_feed.insert(0, {
        "minute": MATCH_MINUTE,
        "event": event_type,
        "player": player["name"],
        "team": player["team"]
    })

    # stats update
    if event_type == "goal":
        stats["goals"] += 1
    elif event_type == "shot":
        stats["shots"] += 1
    elif event_type == "foul":
        stats["fouls"] += 1

    if len(events_feed) > 30:
        events_feed.pop()

# -------------------------
# EVENT SYSTEM
# -------------------------
EVENT_DISTRIBUTION = {
    "pass": 0.70,
    "shot": 0.18,
    "goal": 0.03,
    "foul": 0.06,
    "miss": 0.03
}

def pick_event():
    return random.choices(
        list(EVENT_DISTRIBUTION.keys()),
        list(EVENT_DISTRIBUTION.values()),
        k=1
    )[0]

# -------------------------
# WEBSOCKET MANAGER 🔥
# -------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

# -------------------------
# SIMULATION ENGINE
# -------------------------
def simulate():
    global MATCH_MINUTE, HALF

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while MATCH_MINUTE < 90:

        player = random.choice(players)
        pid = player["id"]
        team = player["team"]

        event = pick_event()

        if event == "goal":
            score[team] += 1
            impact[pid] += 10
            momentum[pid] += 5
            log_event(player, "goal")

        elif event == "shot":
            impact[pid] += 2
            momentum[pid] += 1
            log_event(player, "shot")

        elif event == "pass":
            impact[pid] += 0.3

        elif event == "foul":
            impact[pid] -= 1
            log_event(player, "foul")

        elif event == "miss":
            impact[pid] -= 0.5
            log_event(player, "miss")

        # broadcast update 🔥
        data = {
            "minute": MATCH_MINUTE,
            "score": score,
            "event": event,
            "feed": events_feed[:5]
        }

        loop.run_until_complete(manager.broadcast(data))

        # halftime
        if MATCH_MINUTE == 45:
            time.sleep(3)
            HALF = 2

        MATCH_MINUTE += 1
        time.sleep(0.5)

# -------------------------
# ICONS
# -------------------------
def icons(p):
    i = ""
    if p.get("is_captain"):
        i += "⭐ "
    if p.get("position") == "GK":
        i += "🧤 "
    if impact[p["id"]] > 15:
        i += "🔥 "
    return i.strip()

# -------------------------
# API: STATUS
# -------------------------
@app.get("/match/1/status")
def status():
    return {
        "home": HOME_TEAM,
        "away": AWAY_TEAM,
        "score": f"{score[HOME_TEAM]} - {score[AWAY_TEAM]}",
        "minute": MATCH_MINUTE,
        "half": HALF,
        "status": "LIVE" if MATCH_MINUTE < 90 else "FULL TIME"
    }

# -------------------------
# API: IMPACT
# -------------------------
@app.get("/match/1/impact")
def impact_board():
    result = []

    for p in players:
        result.append({
            "player_id": p["id"],
            "name": p["name"],
            "team": p["team"],
            "position": p.get("position"),
            "impact_score": round(impact[p["id"]], 2),
            "momentum": round(momentum[p["id"]], 2),
            "icons": icons(p)
        })

    return sorted(result, key=lambda x: x["impact_score"], reverse=True)

# -------------------------
# API: FEED
# -------------------------
@app.get("/match/1/feed")
def feed():
    return events_feed

# -------------------------
# API: STATS (NEW 🔥)
# -------------------------
@app.get("/match/1/stats")
def get_stats():
    return stats

# -------------------------
# API: EXPLAIN PLAYER 🔥
# -------------------------
@app.get("/player/{player_id}/explain")
def explain(player_id: int):
    return {
        "player_id": player_id,
        "impact": impact[player_id],
        "breakdown": {
            "goals": impact[player_id] // 10,
            "shots": impact[player_id] // 2
        }
    }

# -------------------------
# WEBSOCKET ENDPOINT 🔥
# -------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# -------------------------
# STARTUP
# -------------------------
@app.on_event("startup")
def start():
    threading.Thread(target=simulate, daemon=True).start()