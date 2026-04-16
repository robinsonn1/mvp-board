from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import json
import random
import threading
import time

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend", html=True), name="frontend")

# -------------------------
# LOAD TEAMS
# -------------------------
def load_teams():
    with open("data/teams.json", "r") as f:
        return json.load(f)

teams_list = load_teams()

# -------------------------
# GENERATE PLAYERS (REALISTIC WORLD CUP STYLE)
# -------------------------
positions = ["GK", "DF", "DF", "DF", "DF", "MF", "MF", "MF", "FW", "FW", "FW"]

players = []
pid = 1

for team in teams_list:
    for i in range(11):  # starting XI
        players.append({
            "id": pid,
            "name": f"{team['name']} Player {i+1}",
            "team": team["name"],
            "position": positions[i],
            "is_captain": i == 1  # simple captain rule
        })
        pid += 1

# -------------------------
# MATCH STATE
# -------------------------
MATCH_MINUTE = 0

team_score = {t["name"]: 0 for t in teams_list}

impact = {p["id"]: 0 for p in players}
momentum = {p["id"]: 0 for p in players}

EVENTS = ["pass", "shot", "goal", "yellow", "red"]

# -------------------------
# SIMULATION
# -------------------------
def simulate():
    while True:
        p = random.choice(players)
        pid = p["id"]
        team = p["team"]

        event = random.choice(EVENTS)

        if event == "goal":
            team_score[team] += 1
            impact[pid] += 10
            momentum[pid] += 5

        elif event == "shot":
            impact[pid] += 2
            momentum[pid] += 1.2

        elif event == "pass":
            impact[pid] += 0.4

        elif event == "yellow":
            impact[pid] -= 2

        elif event == "red":
            impact[pid] -= 5

        time.sleep(1.5)

# -------------------------
# TIMER
# -------------------------
def timer():
    global MATCH_MINUTE
    while True:
        time.sleep(5)
        MATCH_MINUTE += 1

# -------------------------
# ICONS
# -------------------------
def icons(p):
    i = ""
    if p["is_captain"]:
        i += "⭐ "
    if p["position"] == "GK":
        i += "🧤 "
    if impact[p["id"]] > 20:
        i += "🔥 "
    return i.strip()

# -------------------------
# API
# -------------------------
@app.get("/match/1/status")
def status():
    teams = list(team_score.keys())
    return {
        "home": teams[0],
        "away": teams[1],
        "score": f"{team_score[teams[0]]} - {team_score[teams[1]]}",
        "minute": MATCH_MINUTE
    }

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
# START
# -------------------------
@app.on_event("startup")
def start():
    threading.Thread(target=simulate, daemon=True).start()
    threading.Thread(target=timer, daemon=True).start()