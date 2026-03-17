# Architecture

## Overview

The project is a two-tier app:

- React frontend (`frontend/`) for chat, streaming UI, sessions, and settings.
- FastAPI backend (`backend/`) for orchestration, web fetch, synthesis, storage, and exports.

## High-Level Flow

1. User submits a prompt in frontend.
2. Frontend calls `POST /api/research` and consumes NDJSON stream.
3. Backend orchestrator performs:
	- optional reasoning phase,
	- web/source fetch,
	- synthesis,
	- persistence.
4. Streamed events update UI in real time.
5. Session metadata is stored and listed via session endpoints.

## Backend Modules

- `backend/main.py`: HTTP routes and app wiring.
- `backend/core/orchestrator.py`: research flow coordination.
- `backend/core/fetcher.py`: source acquisition.
- `backend/core/synthesizer.py`: response synthesis.
- `backend/core/persistence.py`: session persistence.
- `backend/tools.py`: tool adapters (Gemini stream manager, search helpers, exports).

## Frontend Modules

- `frontend/src/App.jsx`: top-level layout and state boundaries.
- `frontend/src/context/ResearchContext.jsx`: global research state and actions.
- `frontend/src/hooks/useResearch.js`: research request + stream handling.
- `frontend/src/components/CenterPanel.jsx`: prompt input and output view.
- `frontend/src/components/RightSidebar.jsx`: settings and runtime monitor.

## Runtime Notes

- Backend startup should use `PYTHONPATH=.` from repository root.
- Frontend dev server proxies API to backend (`frontend/package.json` proxy).
