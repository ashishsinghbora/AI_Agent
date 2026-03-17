# Quick Start

## Prerequisites

- Python 3.10+
- Node.js 16+
- npm

## 1. Start Backend

```bash
cd /home/ashu/RnD/AI_Agent
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=. python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl -sS http://127.0.0.1:8000/api/health
```

## 2. Start Frontend

Open another terminal:

```bash
cd /home/ashu/RnD/AI_Agent
npm --prefix frontend install
npm --prefix frontend start
```

Open `http://localhost:3000`.

## 3. Run a Query

1. Enter a query in the center panel.
2. Open `Settings` and set `GEMINI_API_KEY` if required.
3. Submit and monitor streamed progress.

## Troubleshooting

- Backend import errors: start backend from repo root with `PYTHONPATH=.`.
- API key errors: save key in `Settings` and retry.
- Watch limit errors on Linux: run without `--reload`.
