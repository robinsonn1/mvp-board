# ⚽ MVP Board V2 – Football Simulation Engine

A real-time football match simulation engine with live impact scoring, WebSocket updates, and WhatsApp-style match previews.

---

## 🚀 Features

- Live match simulation (0–90 minutes)
- Real-time WebSocket updates
- Player impact ranking (22 players)
- Match feed (events)
- Stats tracking (goals, shots, fouls)
- WhatsApp message simulator
- Coach + flag system
- Emoji-based player state system

---

## 🧠 Engine Logic

- Pass: +0.3 impact
- Shot: +2 impact
- Goal: +10 impact
- Foul: -1 impact
- Miss: -0.5 impact

🔥 Bonus states:
- ⭐ Captain
- 🧤 Goalkeeper
- 🔥 Hot form (impact > 15)

---

## ▶️ How to Run

### 1. Install dependencies
```bash
pip install fastapi uvicorn