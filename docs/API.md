# API Reference

Base URL: `http://localhost:8000`

## Streaming

`POST /api/research` responds as streamed NDJSON (`application/x-ndjson`).

## Endpoints

### POST `/api/research`

Starts a research run.

Request body:

```json
{
  "query": "What is retrieval-augmented generation?",
  "max_sources": 5,
  "use_thinking_model": true,
  "speed_mode": "fast",
  "output_mode": "quick",
  "thinking_chars": 180,
  "cpu_budget_percent": 80,
  "preferred_domains": [],
  "chat_history": [
    {"role": "user", "content": "previous message"}
  ],
  "gemini_api_key": "optional-runtime-key"
}
```

Important fields:

- `query` (string): research prompt.
- `max_sources` (int): source fetch cap.
- `use_thinking_model` (bool): enable reasoning phase.
- `speed_mode` (string): speed profile.
- `output_mode` (string): response format profile.
- `gemini_api_key` (string): optional key sent per request.

Typical streamed event types:

- `status`
- `thinking_start`
- `thinking`
- `thinking_end`
- `research_start`
- `research`
- `research_end`
- `response_start`
- `response`
- `response_end`
- `complete`

### POST `/api/config/gemini-key`

Sets or clears the Gemini key in runtime and optionally in `backend/.env`.

Request body:

```json
{
  "api_key": "your_key",
  "persist_to_env": true
}
```

Response shape:

```json
{
  "status": "updated",
  "persisted_to_env": true,
  "env_path": "/path/to/backend/.env"
}
```

### GET `/api/system-stats`

Returns CPU and memory usage.

### GET `/api/sessions`

Returns session list.

### GET `/api/sessions/{session_id}`

Returns details for one session.

### DELETE `/api/sessions/{session_id}`

Deletes one session.

### POST `/api/export/{session_id}?format=markdown|pdf|learning-pack`

Exports a session.

### POST `/api/ingest`

Uploads and ingests file content into vector storage.

### POST `/api/execute`

Runs allowlisted shell commands.

### GET `/api/health`

Health endpoint.
