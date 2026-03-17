# Deployment

## Local Development

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
npm --prefix frontend run build
npm --prefix frontend start
```

## Docker

Use the provided compose setup:

```bash
cd /home/ashu/RnD/AI_Agent
docker-compose up --build
```

## Environment

Backend key config supports both:

- runtime key set through `POST /api/config/gemini-key`,
- persisted key in `backend/.env`.

## Readiness Checklist

- `GET /api/health` returns `healthy`.
- Frontend build succeeds.
- A sample `POST /api/research` returns streamed events.
- Saving API key through settings succeeds.
