from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import random
import threading
import time
import asyncio

app = FastAPI()

# -------------------------
# STATIC FRONTEND (FIXED)
# -------------------------
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def root():
    return FileResponse("frontend/index.html")


@app.get("/whatsapp")
def whatsapp():
    return FileResponse("frontend/whatsapp.html")


# -------------------------
# LOAD PLAYERS
# -------------------------
def load_players():
    with open("data/players.json", "r") as f:
        return json.load(f)

all_players = load_players()

# -------------------------
# MATCH SETUP
# -------------------------
def generate_match():
    teams = list(set([p["team"] for p in all_players]))
    home, away = random.sample(teams, 2)
    match_players = [p for p in all_players if p["team"] in [home, away]]
    return home, away, match_players

HOME_TEAM, AWAY_TEAM, players = generate_match()

# -------------------------
# STATE
# -------------------------
MATCH_MINUTE = 0
HALF = 1

score = {HOME_TEAM: 0, AWAY_TEAM: 0}

impact = {p["id"]: 0 for p in players}
momentum = {p["id"]: 0 for p in players}

stats = {"shots": 0, "fouls": 0, "goals": 0}
events_feed = []

# -------------------------
# COACHES
# -------------------------
COACHES = {
    "Spain": "De La Fuente",
    "France": "Deschamps",
    "Argentina": "Scaloni",
    "Brazil": "Diniz",
    "Germany": "Nagelsmann"
}

# -------------------------
# FLAGS
# -------------------------
def get_flag(team):
    return {
        "Spain": "🇪🇸",
        "France": "🇫🇷",
        "Argentina": "🇦🇷",
        "Brazil": "🇧🇷",
        "Germany": "🇩🇪"
    }.get(team, "🏳️")

# -------------------------
# EVENTS
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
        list(EVENT_DISTRIBUTION.values())
    )[0]

# -------------------------
# FEED
# -------------------------
def log_event(player, event):
    events_feed.insert(0, {
        "minute": MATCH_MINUTE,
        "event": event,
        "player": player["name"],
        "team": player["team"]
    })

    if event == "goal":
        stats["goals"] += 1
        score[player["team"]] += 1
    elif event == "shot":
        stats["shots"] += 1
    elif event == "foul":
        stats["fouls"] += 1

    if len(events_feed) > 30:
        events_feed.pop()

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
# WEBSOCKET MANAGER
# -------------------------
class ConnectionManager:
    def __init__(self):
        self.clients = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.clients:
            self.clients.remove(ws)

    async def broadcast(self, msg):
        dead = []
        for ws in self.clients:
            try:
                await ws.send_json(msg)
            except:
                dead.append(ws)
        for d in dead:
            self.disconnect(d)

manager = ConnectionManager()

# -------------------------
# SIMULATION ENGINE (FIXED)
# -------------------------
def simulate():
    global MATCH_MINUTE, HALF

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def broadcast(payload):
        await manager.broadcast(payload)

    while MATCH_MINUTE < 90:

        player = random.choice(players)
        pid = player["id"]
        team = player["team"]

        event = pick_event()

        # impact logic
        if event == "goal":
            score[team] += 1
            impact[pid] += 10
            momentum[pid] += 5

        elif event == "shot":
            impact[pid] += 2

        elif event == "pass":
            impact[pid] += 0.3

        elif event == "foul":
            impact[pid] -= 1

        elif event == "miss":
            impact[pid] -= 0.5

        if event in ["goal", "shot", "foul", "miss"]:
            log_event(player, event)

        payload = {
            "minute": MATCH_MINUTE,
            "score": f"{score[HOME_TEAM]} - {score[AWAY_TEAM]}",
            "event": event,
            "feed": events_feed[:5]
        }

        loop.run_until_complete(broadcast(payload))

        if MATCH_MINUTE == 45:
            time.sleep(2)
            HALF = 2

        MATCH_MINUTE += 1
        time.sleep(0.5)

# -------------------------
# API
# -------------------------
@app.get("/match/1/status")
def status():
    return {
        "home": f"{HOME_TEAM} ({COACHES.get(HOME_TEAM,'Coach')})",
        "away": f"{AWAY_TEAM} ({COACHES.get(AWAY_TEAM,'Coach')})",
        "score": f"{score[HOME_TEAM]} - {score[AWAY_TEAM]}",
        "minute": MATCH_MINUTE,
        "half": HALF,
        "status": "LIVE" if MATCH_MINUTE < 90 else "FT"
    }


@app.get("/match/1/impact")
def impact_board():
    result = []

    for p in players:
        result.append({
            "id": p["id"],
            "number": p.get("number", 0),
            "name": p["name"],
            "team": p["team"],
            "flag": get_flag(p["team"]),
            "position": p.get("position"),
            "impact_score": round(impact[p["id"]], 2),
            "icons": icons(p)
        })

    return {
        "players": sorted(result, key=lambda x: x["impact_score"], reverse=True)
    }


@app.get("/match/1/feed")
def feed():
    return events_feed


@app.get("/match/1/stats")
def get_stats():
    return stats


# -------------------------
# WEBSOCKET
# -------------------------
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# -------------------------
# START
# -------------------------
@app.on_event("startup")
def start():
    threading.Thread(target=simulate, daemon=True).start()