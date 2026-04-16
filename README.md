# MVP Board – Player Impact Engine ⚽

Real-time simulated player impact dashboard inspired by Dota 2 net worth bars.

## Tech Stack
- Python
- FastAPI
- REST API
- Simulated live events

## Features
- Live player ranking
- Impact score calculation
- “Watch this player” logic
- Background event simulation

## Run locally

```bash
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:
http://127.0.0.1:8000/docs