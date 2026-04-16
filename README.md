# ⚽ Player Impact Engine (MVP Board)

Real-time football player ranking engine inspired by Dota 2 net worth bars.

## 🚀 Features
- Live player impact ranking (22 players)
- Mixed team leaderboard (Spain vs France)
- Real-time simulation engine
- Player flags:
  - ⭐ Captain
  - 🧤 Goalkeeper
  - ⚽ Goals
  - 🟨 Yellow card
  - 🟥 Red card
- “Watch this player” feature

## 🧱 Tech Stack
- Python (FastAPI)
- REST API
- Simulated event engine
- Vanilla JS frontend

## ▶️ Run locally

```bash
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:
http://127.0.0.1:8000/static/index.html

## 🧠 Concept

A real-time “player impact score” calculated from live match events:
- passes
- shots
- goals
- cards

Designed to simulate live match intelligence for the FIFA World Cup 2026.

## 🔮 Next Steps
- Match scoreboard (Spain 1–0 France)
- Live timer
- Momentum indicators
- Real sports API integration
- MySQL persistence