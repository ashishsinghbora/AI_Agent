# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER'S COMPUTER                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          FRONTEND (React + Tailwind)                 │   │
│  │                                                       │   │
│  │  ┌────────────┬──────────────┬──────────────┐        │   │
│  │  │   Left     │    Center    │    Right     │        │   │
│  │  │  Sidebar   │    Panel     │   Sidebar    │        │   │
│  │  │ (Sessions) │ (Chat + CoT) │  (Monitor)   │        │   │
│  │  └────────────┴──────────────┴──────────────┘        │   │
│  │                                                       │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │ HTTP/SSE                              │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │      BACKEND (FastAPI + Agent Loop)                 │   │
│  │                                                       │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  Router (Main Orchestrator)                  │   │   │
│  │  │  - POST /api/research                        │   │   │
│  │  │  - GET /api/sessions                         │   │   │
│  │  │  - GET /api/system-stats                     │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                     │                               │   │
│  │  ┌──────────────────┼──────────────────────────┐   │   │
│  │  │  Agent Loop  │   │                          │   │   │
│  │  ├──────────────┴───────────────────────────┤  │   │   │
│  │  │                                            │  │   │   │
│  │  │  1. Thinking (deepseek-r1)                │  │   │   │
│  │  │  2. Web Research (DuckDuckGo)             │  │   │   │
│  │  │  3. Vector Store (ChromaDB)               │  │   │   │
│  │  │  4. Response Generation (gemma2)          │  │   │   │
│  │  │  5. Export & Storage                      │  │   │   │
│  │  │                                            │  │   │   │
│  │  └────────────────────────────────────────────┘  │   │   │
│  │                                                       │   │
│  └───┬────────────┬────────────────┬──────────────────┘   │
│      │            │                │                      │
│      ▼            ▼                ▼                      │
│  ┌────────┐  ┌────────────┐  ┌──────────┐               │
│  │ Ollama │  │ ChromaDB   │  │  File    │               │
│  │ (Local │  │ (Vector    │  │ System   │               │
│  │  LLM)  │  │  Store)    │  │ (/home/) │               │
│  └────────┘  └────────────┘  └──────────┘               │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │         External Services (Optional)              │   │
│  │  - Tavily API (for better web search)             │   │
│  │  - DuckDuckGo (free web search)                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend Architecture

```
App.jsx (Root)
├── State Management
│   ├── sessions: Research session history
│   ├── chatMessages: Current conversation
│   ├── systemStats: CPU/RAM monitoring
│   └── researchProgress: Progress tracking
│
├── LeftSidebar
│   ├── Session List
│   ├── Search Bar
│   └── Statistics
│
├── CenterPanel
│   ├── Welcome Screen
│   ├── Message Display
│   ├── Chain of Thought
│   ├── Progress Bar
│   └── Input Field
│
├── RightSidebar
│   ├── System Monitor
│   │   ├── CPU Usage
│   │   └── Memory Usage
│   ├── Research Progress
│   └── Sources Panel
│
└── SmartChildAvatar
    ├── Animated Face
    ├── Thinking Indicator
    └── Status Text
```

### Backend Architecture

```
main.py (FastAPI Application)
│
├── Middleware
│   └── CORS Configuration
│
├── Routes
│   ├── POST /api/research
│   ├── GET /api/sessions
│   ├── GET /api/system-stats
│   ├── POST /api/export/{id}
│   ├── POST /api/execute
│   └── GET /api/health
│
├── Agent Loop (Streaming Generator)
│   ├── 1. Thinking Phase
│   │   └── deepseek-r1:7b (with streaming)
│   │
│   ├── 2. Research Phase
│   │   ├── Web Search (Tavily/DuckDuckGo)
│   │   └── Content Extraction
│   │
│   ├── 3. Storage Phase
│   │   └── ChromaDB Vector Store
│   │
│   ├── 4. Response Phase
│   │   └── gemma2:2b (with streaming)
│   │
│   └── 5. Export Phase
│       └── Markdown/PDF Generation
│
└── Session Management
    └── In-Memory Store (ResearchSession objects)

tools.py (Utility Modules)
│
├── OllamaManager
│   ├── Model Switching
│   ├── Streaming Generation
│   └── Fallback Handling
│
├── VectorStore (ChromaDB)
│   ├── add_document()
│   └── search() - Semantic Search
│
├── WebResearcher
│   ├── DuckDuckGo Search
│   ├── Tavily API Integration
│   └── Page Content Extraction
│
├── FileManager
│   ├── Create/Read/Update Files
│   └── Save Research
│
├── TerminalExecutor
│   ├── Safe Command Execution
│   └── Command Whitelist
│
└── ResearchSummarizer
    ├── PDF Generation
    └── Export Formatting
```

## Data Flow

### Research Query Flow

```
User Input
    │
    ▼
POST /api/research
    │
    ▼
Agent Loop Start
    │
    ├─► THINKING PHASE
    │   │ "What should I research and how?"
    │   ├─ deepseek-r1:7b reasoning
    │   └─► STREAM: thinking chunks to frontend
    │
    ├─► RESEARCH PHASE
    │   │ "Find relevant sources"
    │   ├─ DuckDuckGo search (3-5 sources)
    │   ├─ Fetch page content
    │   └─► STREAM: sources_found event
    │
    ├─► STORAGE PHASE
    │   │ "Store for future reference"
    │   ├─ ChromaDB vector embedding
    │   ├─ Store with metadata (URL, title, time)
    │   └─► STREAM: status update
    │
    ├─► RESPONSE PHASE
    │   │ "Answer based on research"
    │   ├─ Retrieve context from vector store
    │   ├─ Build prompt with sources
    │   ├─ gemma2:2b generation
    │   └─► STREAM: response chunks
    │
    ├─► EXPORT PHASE
    │   │ "Save for record"
    │   ├─ Markdown file creation
    │   ├─ Add metadata
    │   └─► STREAM: research_complete event
    │
    └─► FRONTEND
        ├─ Display thinking process
        ├─ Show sources
        ├─ Stream response
        ├─ Update progress bar
        └─ Show smart avatar animation
```

## Data Storage

### File Structure

```
/home/ashu/research_notes/
├── research_2024-01-15T10-30-45.md
│   ├── Query: "What is..."
│   ├── Response: "Full markdown response..."
│   └── Sources: "Links with titles..."
│
├── research_2024-01-15T11-45-20.md
└── ...

/tmp/chroma/
├── Vector database files
└── Embeddings for semantic search
```

### Session Storage

```
In-Memory (ResearchSession objects)
├── session_id: Unique identifier
├── query: Original user query
├── started_at: Timestamp
├── chat_history: Message list
├── findings: Research results
└── sources: Web sources used
```

## Performance Characteristics

### Model Loading & Execution

**First Query:**
- deepseek-r1 load: 20-40s (first time only)
- gemma2 load: 5-10s (first time only)
- Research: 30-60s
- Total: ~60-90s

**Subsequent Queries:**
- Model load: 0s (in RAM)
- Research: 30-60s
- Total: ~30-60s

### Resource Usage

```
Idle State:
- RAM: 100-200 MB
- CPU: <1%

During Thinking:
- RAM: 3-5 GB (deepseek-r1)
- CPU: 80-100%

During Response:
- RAM: 1-2 GB (gemma2)
- CPU: 60-80%

Post-Research (models in RAM):
- RAM: 3-5 GB
- CPU: <1%
```

### Smart Unloading

Ollama automatically unloads models after:
- 5 minutes of inactivity
- When switching models
- Manual unload command

## API Contracts

### Stream Event Types

```json
// Thinking event
{
  "type": "thinking",
  "content": "chunk of text"
}

// Research found sources
{
  "type": "sources_found",
  "sources": [...],
  "progress": 30
}

// Response chunk
{
  "type": "response",
  "content": "chunk of markdown"
}

// Complete
{
  "type": "research_complete",
  "session_id": "...",
  "summary": {...}
}

// Error
{
  "type": "error",
  "error": "error message"
}
```

## Security Considerations

1. **Local Processing**: All data stays on-device
2. **No External APIs**: Uses free DuckDuckGo by default
3. **Command Whitelist**: Only safe commands allowed
4. **Input Validation**: All user inputs validated
5. **Error Handling**: Graceful fallbacks for failures

## Scalability Limitations

Current design is for **single-user, local installation**:
- Single Ollama instance
- In-memory session storage (max ~100 sessions)
- Single FastAPI worker process
- Local vector store (fine for ~1000 embeddings)

To scale:
- Add database backend (PostgreSQL + pgvector)
- Use distributed caching (Redis)
- Deploy multiple backend workers
- Use Milvus or Weaviate for vector store

## Future Enhancements

### Planned
- WebSocket for real-time updates
- Database persistence
- User authentication
- Multi-model support
- Custom model fine-tuning
- Research paper indexing

### Considerations
- GPU acceleration for faster inference
- Distributed processing
- Advanced caching strategies
- Full-text search integration
- Citation management

---

**Architecture designed for single-user research with focus on autonomy, privacy, and local processing.**
