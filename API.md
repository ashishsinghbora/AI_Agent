# API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Research Query

**Endpoint:** `POST /api/research`

**Purpose:** Initiate an autonomous research query with streaming responses

**Request:**
```json
{
  "query": "What are transformer architectures in deep learning?",
  "max_sources": 5,
  "use_thinking_model": true,
  "chat_history": [
    {
      "role": "user",
      "content": "Previous question",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Response:** Server-Sent Events (streaming NDJSON)

**Event Types:**

```json
// 1. Thinking Start
{
  "type": "thinking_start",
  "timestamp": "2024-01-15T10:30:00Z"
}

// 2. Thinking Content (streamed)
{
  "type": "thinking",
  "content": "chunk of AI reasoning..."
}

// 3. Thinking End
{
  "type": "thinking_end",
  "timestamp": "2024-01-15T10:30:05Z"
}

// 4. Research Start
{
  "type": "research_start",
  "message": "Searching the web for relevant information...",
  "progress": 0
}

// 5. Sources Found
{
  "type": "sources_found",
  "sources": [
    {
      "title": "Page Title",
      "url": "https://example.com",
      "content": "Extracted content...",
      "snippet": "Short description..."
    }
  ],
  "count": 5,
  "progress": 30
}

// 6. Status Updates
{
  "type": "status",
  "message": "Processing and storing research findings...",
  "progress": 50
}

// 7. Response Start
{
  "type": "response_start",
  "progress": 75
}

// 8. Response Content (streamed)
{
  "type": "response",
  "content": "chunk of markdown response..."
}

// 9. Research Complete
{
  "type": "research_complete",
  "message": "Research complete!",
  "summary": {
    "query": "...",
    "response_length": 2500,
    "sources_count": 5,
    "key_sources": [
      {"title": "...", "url": "..."}
    ],
    "created_at": "2024-01-15T10:35:00Z"
  },
  "progress": 100,
  "session_id": "unique-session-id",
  "timestamp": "2024-01-15T10:35:00Z"
}

// Error Event
{
  "type": "error",
  "error": "Error message",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Example Usage (JavaScript):**
```javascript
async function research(query) {
  const response = await fetch('http://localhost:8000/api/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: query,
      use_thinking_model: true,
      chat_history: []
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value);
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (line) {
        const event = JSON.parse(line);
        console.log('Event:', event.type, event);
        
        // Handle different event types
        switch(event.type) {
          case 'thinking':
            console.log('AI Thinking:', event.content);
            break;
          case 'response':
            console.log('AI Response:', event.content);
            break;
          case 'sources_found':
            console.log('Sources:', event.sources);
            break;
          // ... handle other types
        }
      }
    }
  }
}
```

---

### 2. System Statistics

**Endpoint:** `GET /api/system-stats`

**Purpose:** Get real-time CPU and memory usage

**Response:**
```json
{
  "cpu_percent": 45.2,
  "memory": {
    "used": 4.5,
    "total": 16.0,
    "percent": 28.1
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example Usage:**
```javascript
async function getSystemStats() {
  const response = await fetch('http://localhost:8000/api/system-stats');
  const data = await response.json();
  console.log(`CPU: ${data.cpu_percent}%`);
  console.log(`Memory: ${data.memory.percent}%`);
  return data;
}
```

---

### 3. Get All Sessions

**Endpoint:** `GET /api/sessions`

**Purpose:** Retrieve list of all research sessions

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "2024-01-15T10-30-45.123456",
      "query": "What is machine learning?",
      "started_at": "2024-01-15T10:30:45Z",
      "findings_count": 5
    },
    {
      "session_id": "2024-01-15T11-00-00.654321",
      "query": "Deep learning architectures",
      "started_at": "2024-01-15T11:00:00Z",
      "findings_count": 3
    }
  ]
}
```

**Example Usage:**
```javascript
async function listSessions() {
  const response = await fetch('http://localhost:8000/api/sessions');
  const data = await response.json();
  data.sessions.forEach(session => {
    console.log(`${session.query} (${session.findings_count} findings)`);
  });
  return data.sessions;
}
```

---

### 4. Get Specific Session

**Endpoint:** `GET /api/sessions/{session_id}`

**Purpose:** Retrieve detailed information about a specific session

**Parameters:**
- `session_id` (path): Unique session identifier

**Response:**
```json
{
  "session_id": "2024-01-15T10-30-45.123456",
  "query": "What is machine learning?",
  "started_at": "2024-01-15T10:30:45Z",
  "findings": [
    {
      "title": "Machine Learning - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Machine_learning",
      "content": "Machine learning is a subset of artificial intelligence..."
    }
  ],
  "chat_history": [
    {
      "role": "user",
      "content": "What is machine learning?",
      "timestamp": "2024-01-15T10:30:45Z"
    },
    {
      "role": "assistant",
      "content": "Machine learning is...",
      "timestamp": "2024-01-15T10:35:00Z"
    }
  ]
}
```

---

### 5. Export Session

**Endpoint:** `POST /api/export/{session_id}`

**Purpose:** Export a research session as PDF or Markdown

**Parameters:**
- `session_id` (path): Unique session identifier
- `format` (query): Export format - `markdown` or `pdf`

**Response:**
```json
{
  "path": "/tmp/research_session_id.pdf",
  "format": "pdf"
}
```

**Example Usage:**
```javascript
async function exportSession(sessionId, format = 'markdown') {
  const response = await fetch(
    `http://localhost:8000/api/export/${sessionId}?format=${format}`,
    { method: 'POST' }
  );
  const data = await response.json();
  console.log(`Exported to: ${data.path}`);
  return data;
}
```

---

### 6. Execute Terminal Command

**Endpoint:** `POST /api/execute`

**Purpose:** Safely execute whitelisted terminal commands

**Allowed Commands:**
- File operations: `ls`, `cat`, `grep`, `find`
- System info: `whoami`, `pwd`, `uname`, `date`
- Process monitoring: `ps`, `top`, `free`
- Network: `netstat`, `lsof`

**Request:**
```json
{
  "command": "ls -la /home/ashu/research_notes"
}
```

**Response:**
```json
{
  "success": true,
  "command": "ls -la /home/ashu/research_notes",
  "stdout": "total 48\ndrwxr-xr-x  3 ashu ashu 4096 Jan 15 10:30 .\n...",
  "stderr": "",
  "returncode": 0
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Command 'rm' not allowed",
  "command": "rm -rf /"
}
```

---

### 7. Health Check

**Endpoint:** `GET /api/health`

**Purpose:** Verify backend and Ollama are running

**Response:**
```json
{
  "status": "healthy",
  "ollama": {
    "status": "running",
    "models_available": [
      "deepseek-r1:7b",
      "gemma2:2b"
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Session not found"
}
```

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `403`: Forbidden (disallowed command)
- `404`: Not Found (session/resource doesn't exist)
- `500`: Server Error (internal error)

---

## Rate Limiting

Currently no rate limiting. Recommended:
- Max 10 concurrent research queries
- Max 5 queries per minute per user
- Implement in production

---

## Authentication

Currently no authentication. For production:
- Add JWT tokens
- Implement user roles
- Add API key authentication

---

## Response Format

All endpoints return JSON responses with:
- Success responses: Data object or array
- Error responses: `{ "detail": "error message" }`
- Streaming responses: NDJSON (newline-delimited JSON)

---

## WebSocket Support (Future)

Planned for real-time updates:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);
};
```

---

## cURL Examples

### Basic Research Query
```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is deep learning?",
    "use_thinking_model": true
  }' \
  -N
```

### Get System Stats
```bash
curl http://localhost:8000/api/system-stats
```

### List Sessions
```bash
curl http://localhost:8000/api/sessions
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Execute Command
```bash
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la"}'
```

---

## Rate Limits & Quotas

For low-end PC optimization:

| Resource | Limit | Reason |
|----------|-------|--------|
| Concurrent Researches | 1 | Single Ollama instance |
| Max Sources | 5-10 | Network limits |
| Max Response Length | 10,000 tokens | Memory constraints |
| Session History | 100 | RAM limits |

---

## Timeout Values

| Operation | Timeout |
|-----------|---------|
| Web Search | 30s |
| Model Generation | 300s |
| Vector Store Query | 10s |
| File Operations | 5s |

---

## Development

### Testing the API

```bash
# Install httpie for easier testing
pip install httpie

# Test research endpoint
http POST localhost:8000/api/research query='What is AI?'

# Stream with curl
curl -N http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'
```

---

**API Documentation v1.0 - Last Updated: Jan 2024**
