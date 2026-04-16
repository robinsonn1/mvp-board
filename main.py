from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import json
import random
import threading
import time

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

score = {
    HOME_TEAM: 0,
    AWAY_TEAM: 0
}

impact = {p["id"]: 0 for p in players}
momentum = {p["id"]: 0 for p in players}

# -------------------------
# MATCH FEED (NEW 🔥)
# -------------------------
events_feed = []

def log_event(player, event_type):
    events_feed.insert(0, {
        "minute": MATCH_MINUTE,
        "text": f"{event_type.upper()} - {player['name']} ({player['team']})"
    })

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
# SIMULATION ENGINE
# -------------------------
def simulate():
    global MATCH_MINUTE, HALF

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

        # halftime logic
        if MATCH_MINUTE == 45:
            time.sleep(3)
            HALF = 2

        MATCH_MINUTE += 1
        time.sleep(0.5)

# -------------------------
# ICONS SYSTEM
# -------------------------
def icons(p):
    i = ""
    if p["is_captain"]:
        i += "⭐ "
    if p["position"] == "GK":
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
# API: IMPACT BOARD
# -------------------------
@app.get("/match/1/impact")
def impact_board():
    result = []

    for p in players:
        result.append({
            "player_id": p["id"],
            "name": p["name"],
            "team": p["team"],
            "position": p["position"],
            "impact_score": round(impact[p["id"]], 2),
            "momentum": round(momentum[p["id"]], 2),
            "icons": icons(p)
        })

    return sorted(result, key=lambda x: x["impact_score"], reverse=True)

# -------------------------
# API: MATCH FEED (NEW 🔥)
# -------------------------
@app.get("/match/1/feed")
def feed():
    return events_feed

# -------------------------
# API: ENGINE INFO (for UI "about section")
# -------------------------
@app.get("/match/1/info")
def info():
    return {
        "engine": "FIFA 2026 Simulation Engine",
        "version": "1.0",
        "rules": {
            "pass": "+0.3 impact",
            "shot": "+2 impact",
            "goal": "+10 impact",
            "foul": "-1 impact",
            "miss": "-0.5 impact"
        },
        "emojis": {
            "⭐": "Captain",
            "🧤": "Goalkeeper",
            "🔥": "Hot form (impact > 15)"
        }
    }

# -------------------------
# STARTUP
# -------------------------
@app.on_event("startup")
def start():
    threading.Thread(target=simulate, daemon=True).start()