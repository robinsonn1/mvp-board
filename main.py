from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import random
import time
from datetime import datetime
import threading

app = FastAPI()

# -------------------------
# SERVE FRONTEND
# -------------------------
app.mount("/static", StaticFiles(directory="frontend", html=True), name="frontend")

# -------------------------
# CREATE PLAYERS (22 TOTAL)
# -------------------------
players = []

def create_players():
    pid = 1
    for team in ["Spain", "France"]:
        for i in range(1, 12):
            players.append({
                "id": pid,
                "name": f"{team[:2]} Player {i}",
                "team": team,
                "position": "GK" if i == 1 else "FW",
                "is_captain": i == 2
            })
            pid += 1

create_players()

# -------------------------
# DATA STORAGE
# -------------------------
events = []
impact_cache = {}
player_stats = {}

# initialize stats
for p in players:
    player_stats[p["id"]] = {
        "goals": 0,
        "yellow": False,
        "red": False
    }

EVENT_TYPES = ["pass", "shot", "goal", "yellow", "red"]

# -------------------------
# SIMULATOR
# -------------------------
def generate_event():
    player = random.choice(players)
    event_type = random.choice(EVENT_TYPES)

    event = {
        "player_id": player["id"],
        "team": player["team"],
        "event_type": event_type,
        "outcome": random.choice(["success", "fail"]),
        "timestamp": datetime.utcnow()
    }

    # update stats
    if event_type == "goal":
        player_stats[player["id"]]["goals"] += 1
    elif event_type == "yellow":
        player_stats[player["id"]]["yellow"] = True
    elif event_type == "red":
        player_stats[player["id"]]["red"] = True

    events.append(event)

# -------------------------
# IMPACT ENGINE
# -------------------------
def calculate_impact(player_id):
    score = 0
    player_events = [e for e in events if e["player_id"] == player_id]

    for e in player_events:
        if e["event_type"] == "pass" and e["outcome"] == "success":
            score += 0.5
        elif e["event_type"] == "shot":
            score += 2
        elif e["event_type"] == "goal":
            score += 10
        elif e["event_type"] == "yellow":
            score -= 2
        elif e["event_type"] == "red":
            score -= 5
        elif e["event_type"] == "pass" and e["outcome"] == "fail":
            score -= 0.3

    return round(score, 2)

# -------------------------
# BACKGROUND LOOP
# -------------------------
def run_simulation():
    while True:
        generate_event()

        for p in players:
            impact_cache[p["id"]] = calculate_impact(p["id"])

        time.sleep(2)

# -------------------------
# RESPONSE MODEL
# -------------------------
class PlayerResponse(BaseModel):
    player_id: int
    name: str
    team: str
    impact_score: float
    icons: str

# -------------------------
# ICON BUILDER
# -------------------------
def build_icons(player, stats):
    icons = ""

    if player["is_captain"]:
        icons += "⭐ "
    if player["position"] == "GK":
        icons += "🧤 "
    if stats["yellow"]:
        icons += "🟨 "
    if stats["red"]:
        icons += "🟥 "
    if stats["goals"] > 0:
        icons += "⚽ "

    return icons.strip()

# -------------------------
# API ENDPOINTS
# -------------------------
@app.get("/match/1/impact", response_model=List[PlayerResponse])
def get_impact():
    result = []

    for p in players:
        stats = player_stats[p["id"]]

        result.append({
            "player_id": p["id"],
            "name": p["name"],
            "team": p["team"],
            "impact_score": impact_cache.get(p["id"], 0),
            "icons": build_icons(p, stats)
        })

    # 🔥 GLOBAL SORT (mixed teams)
    return sorted(result, key=lambda x: x["impact_score"], reverse=True)


@app.get("/match/1/watch")
def watch_player():
    impacts = get_impact()

    if not impacts:
        return {"message": "No data"}

    top = impacts[0]

    return {
        "watch_player": top["name"],
        "impact_score": top["impact_score"],
        "reason": "Top impact player"
    }

# -------------------------
# START SIMULATION
# -------------------------
@app.on_event("startup")
def startup():
    thread = threading.Thread(target=run_simulation, daemon=True)
    thread.start()