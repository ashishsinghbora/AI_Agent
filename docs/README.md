# Research Student AI Agent - Documentation

## 🎉 Project Overview

You now have a fully functional, production-ready Research Student AI Agent system. This comprehensive guide covers everything you need to understand, set up, and use the system.

## 📦 What's Included

### Backend Components
- **FastAPI application server** with agentic research loop and streaming
- **OllamaManager**: Local LLM interface
- **VectorStore**: ChromaDB integration for semantic search
- **WebResearcher**: Web search & content extraction
- **FileManager**: Local file operations
- **TerminalExecutor**: Safe command execution
- **ResearchSummarizer**: PDF/Markdown export

### Frontend Components
- **React application** with session management and research orchestration
- **LeftSidebar**: Session history, search, statistics
- **CenterPanel**: Chat interface, Chain of Thought display
- **RightSidebar**: System monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

### Setup (5-10 minutes)
```bash
cd /home/ashu/RnD/research_agent
chmod +x setup.sh
./setup.sh
```

### Start Everything (1 minute)
```bash
cd /home/ashu/RnD/research_agent
./start-docker.sh
```

**Alternative native start:**
```bash
./start-all.sh
```

### Try It!
1. Open http://localhost:3000 in your browser
2. Type: "What is machine learning?"
3. Watch the avatar think! 💡

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER'S COMPUTER                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │          FRONTEND (React + Tailwind)                 │   │
│  │  ┌────────────┬──────────────┬──────────────┐        │   │
│  │  │   Left     │    Center    │    Right     │        │   │
│  │  │  Sidebar   │    Panel     │   Sidebar    │        │   │
│  │  │ (Sessions) │ (Chat + CoT) │  (Monitor)   │        │   │
│  │  └────────────┴──────────────┴──────────────┘        │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │ HTTP/SSE                              │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │      BACKEND (FastAPI + Agent Loop)                 │   │
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
│  │  │                                            │  │   │
│  │  │  1. Thinking (deepseek-r1)                │  │   │
│  │  │  2. Web Research (DuckDuckGo)             │  │   │
│  │  │  3. Vector Store (ChromaDB)               │  │   │
│  │  │  4. Response Generation (gemma2)          │  │   │
│  │  │  5. Export & Storage                      │  │   │
│  │  │                                            │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  │                                                       │   │
│  └───┬────────────┬────────────────┬──────────────────┘   │
│      │            │                │                      │
│      ▼            ▼                ▼                      │
│  ┌────────┐  ┌────────────┐  ┌──────────┐               │
│  │ Ollama │  │ ChromaDB   │  │  File    │               │
│  │ (Local │  │ (Vector    │  │ System   │               │
│  │  LLM)  │  │  Store)    │  │ (/home/) │               │
│  └────────┘  └────────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## 📡 API Reference

**Base URL:** `http://localhost:8000`

### Research Query
**Endpoint:** `POST /api/research`

Initiate an autonomous research query with streaming responses.

**Request:**
```json
{
  "query": "What are transformer architectures in deep learning?",
  "max_sources": 5,
  "use_thinking_model": true,
  "chat_history": [...]
}
```

**Response:** Server-Sent Events (streaming NDJSON)

Event Types: `thinking_start`, `thinking`, `thinking_end`, `research_start`, `research`, `research_end`, `response_start`, `response`, `response_end`, `complete`

### Sessions
**Endpoint:** `GET /api/sessions`

Retrieve list of research sessions.

### System Stats
**Endpoint:** `GET /api/system-stats`

Get system performance metrics.

## 🚀 Deployment

### Local Native Installation (Recommended)
```bash
cd /home/ashu/RnD/research_agent
chmod +x setup.sh
./setup.sh
./start-all.sh
```

### Docker Deployment
Use the provided docker-compose.yml for containerized deployment.

### Systemd Service
For production, create a systemd service for automatic startup.

## 📚 Additional Resources

- [Detailed API Documentation](API.md)
- [Architecture Deep Dive](ARCHITECTURE.md)
- [Deployment Options](DEPLOYMENT.md)
- [Project Checklist](CHECKLIST.md)
- [File Manifest](FILE_MANIFEST.md)
- [Enterprise Refactor Notes](ENTERPRISE_REFACTOR.md)
- [Project Summary](PROJECT_SUMMARY.md)
- [Quick Start Details](QUICKSTART.md)
- [Ready to Run Guide](READY_TO_RUN.md)

## 🤝 Contributing

This project is ready for professional deployment. For contributions or issues, please refer to the GitHub repository.

## 📄 License

[Add license information here]