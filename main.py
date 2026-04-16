# =========================
# Player Impact Engine - Starter Project
# Backend: FastAPI + SQLite (easy to swap to MySQL)
# =========================

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import random
import time
from datetime import datetime

app = FastAPI()

# -------------------------
# In-memory storage (MVP)
# -------------------------
players = [
    {"id": 1, "name": "Pedri", "team": "Spain"},
    {"id": 2, "name": "Morata", "team": "Spain"},
    {"id": 3, "name": "Mbappe", "team": "France"},
    {"id": 4, "name": "Griezmann", "team": "France"},
]

matches = {
    1: {
        "id": 1,
        "home_team": "Spain",
        "away_team": "France",
        "minute": 1
    }
}

events = []
impact_cache = {}

# -------------------------
# Event Generator (Simulator)
# -------------------------
EVENT_TYPES = ["pass", "shot", "goal", "foul"]


def generate_event(match_id):
    player = random.choice(players)

    event = {
        "match_id": match_id,
        "player_id": player["id"],
        "team": player["team"],
        "event_type": random.choice(EVENT_TYPES),
        "outcome": random.choice(["success", "fail"]),
        "timestamp": datetime.utcnow()
    }

    events.append(event)
    return event

# -------------------------
# Impact Calculation
# -------------------------

def calculate_impact(player_id):
    score = 0
    recent_events = [e for e in events if e["player_id"] == player_id]

    for e in recent_events:
        if e["event_type"] == "pass" and e["outcome"] == "success":
            score += 0.5
        elif e["event_type"] == "shot":
            score += 2
        elif e["event_type"] == "goal":
            score += 10
        elif e["event_type"] == "pass" and e["outcome"] == "fail":
            score -= 0.3

    return round(score, 2)

# -------------------------
# Background Simulation Loop
# -------------------------

def run_simulation():
    while True:
        generate_event(1)

        # update impact cache
        for p in players:
            impact_cache[p["id"]] = calculate_impact(p["id"])

        time.sleep(3)

# -------------------------
# API Schemas
# -------------------------

class PlayerImpact(BaseModel):
    player_id: int
    name: str
    team: str
    impact_score: float

# -------------------------
# API Endpoints
# -------------------------

@app.get("/")
def root():
    return {"message": "Player Impact Engine running"}


@app.get("/match/{match_id}/impact", response_model=List[PlayerImpact])
def get_impact(match_id: int):
    result = []

    for p in players:
        result.append({
            "player_id": p["id"],
            "name": p["name"],
            "team": p["team"],
            "impact_score": impact_cache.get(p["id"], 0)
        })

    # sort descending
    return sorted(result, key=lambda x: x["impact_score"], reverse=True)


@app.get("/match/{match_id}/watch")
def watch_player(match_id: int):
    impacts = get_impact(match_id)

    if not impacts:
        return {"message": "No data"}

    top = impacts[0]

    return {
        "watch_player": top["name"],
        "impact_score": top["impact_score"],
        "reason": "Highest impact score"
    }

# -------------------------
# Run simulator in background
# -------------------------

import threading

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=run_simulation, daemon=True)
    thread.start()

# -------------------------
# To run:
# uvicorn main:app --reload
# -------------------------
