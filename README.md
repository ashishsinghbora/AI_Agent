# AI Agent

A lightweight research assistant with a React frontend and FastAPI backend.

## What It Does

- Streams research responses in real time.
- Tracks session history.
- Shows system stats in the UI.
- Supports Gemini API key setup from the Settings panel.
- Exports completed sessions.

## Project Structure

```
AI_Agent/
├── backend/            # FastAPI app and orchestration
├── frontend/           # React app
├── docs/               # Documentation
├── docker-compose.yml
├── setup.sh
├── start-all.sh
├── start-backend.sh
└── start-frontend.sh
```

## Quick Start

### Backend

```bash
cd /home/ashu/RnD/AI_Agent
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=. python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd /home/ashu/RnD/AI_Agent
npm --prefix frontend install
npm --prefix frontend start
```

Open `http://localhost:3000`.

## Docs

- `docs/README.md`
- `docs/QUICKSTART.md`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/DEPLOYMENT.md`

## Notes

- Start backend from repo root with `PYTHONPATH=.`.
- Running backend without `--reload` avoids Linux file watch limit issues.
