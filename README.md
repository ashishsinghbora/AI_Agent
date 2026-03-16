
# Research Student AI Agent

![AI Agent](https://github.com/user-attachments/assets/692049aa-176f-4e7f-a003-a62bec447013)

A sophisticated, locally-hosted AI research assistant with a ChatGPT-style interface for autonomous web research, analysis, and knowledge management.

## 🎯 Features

- **Local Brain**: Powered by Ollama with deep-thinking models (deepseek-r1:7b) and fast response models (gemma2:2b)
- **Autonomous Web Research**: Search the web, crawl relevant pages, and extract information automatically
- **Vector Store**: ChromaDB-backed local knowledge base for fast retrieval of past findings
- **Real-time Streaming**: See the AI's thinking process and research progress in real-time
- **Professional Dashboard**: Three-column ChatGPT-style interface
  - Left: Session history and research management
  - Center: Chat interface with Chain of Thought display
  - Right: System monitor and research sources
- **Markdown & LaTeX Support**: Rich text formatting and mathematical equation rendering
- **Export Capabilities**: Save research as PDF or Markdown
- **Smart Avatar**: Animated avatar showing thinking and progress status (bottom-right)
- **Resource-Optimized**: Designed for low-end PCs with async I/O and smart model management
- **Containerized Deployment**: Docker support for easy deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+
- Docker & Docker Compose (recommended)
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

### One-Command Start (Recommended)
```bash
git clone <repository-url>
cd research_agent
./start-docker.sh
```

**Alternative native start:**
```bash
./setup.sh
./start-all.sh
```

Then open http://localhost:3000 in your browser.

## 📚 Documentation

For detailed documentation, see the [docs/](docs/) folder:

- [Complete Documentation](docs/README.md)
- [API Reference](docs/API.md)
- [Architecture Details](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Quick Start Details](docs/QUICKSTART.md)

## 🏗️ Architecture

```
research_agent/
├── backend/              # FastAPI server & agentic loop
├── frontend/             # React application
├── docs/                 # Comprehensive documentation
├── research_notes/       # Local storage for findings
├── docker-compose.yml    # Container orchestration
├── setup.sh             # Installation script
├── start-docker.sh      # Docker startup script
└── start-all.sh         # Native startup script
```

## 📋 Requirements

- **OS**: Linux (Fedora recommended) or macOS/Windows with Docker
- **Python**: 3.10+ (for native installation)
- **Node.js**: 16+ (for native installation)
- **Docker**: For containerized deployment (recommended)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB free space

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
git clone <repository-url>
cd research_agent
./start-docker.sh
```

### Option 2: Native Installation

```bash
git clone <repository-url>
cd research_agent
chmod +x setup.sh
./setup.sh
./start-all.sh
```

Then open http://localhost:3000 in your browser.

### 3. Start the Application

**Option A: Docker (Recommended)**
```bash
./start-docker.sh
```

**Option B: Native Start All Services**
```bash
./start-all.sh
```

**Option C: Start Services Separately**

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Frontend:
```bash
cd frontend
npm start
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🧠 How It Works

### Research Loop

1. **User Input**: You ask a research question
2. **Thinking Phase**: AI uses deepseek-r1:7b to reason about the query and plan research strategy
3. **Web Research**: System searches multiple sources and crawls relevant pages
4. **Vector Store**: Findings are stored in ChromaDB for semantic search
5. **Response Generation**: AI synthesizes findings using gemma2:2b for fast, coherent responses
6. **Storage**: Research is saved locally as Markdown/PDF for future reference

### UI Components

- **Chain of Thought Display**: See the AI's internal reasoning in real-time
- **Progress Bar**: Visualizes research progress (thinking → searching → processing → finalizing)
- **Smart Avatar**: Animated child character showing:
  - Thinking indicator (light bulb glow)
  - Progress percentage
  - Status messages
- **System Monitor**: Live CPU/RAM usage to ensure your low-end PC isn't overloaded
- **Sources Panel**: Shows all web sources the AI is referencing

## ⚙️ Configuration

### Backend (.env)

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_PRIMARY_MODEL=deepseek-r1:7b
OLLAMA_FALLBACK_MODEL=gemma2:2b

# Web Research APIs (Optional)
TAVILY_API_KEY=your_api_key_here

# Paths
RESEARCH_NOTES_PATH=/home/ashu/research_notes
CHROMA_PERSIST_DIR=/tmp/chroma

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

### Frontend (.env)

```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## 🛠️ API Endpoints

### `/api/research` (POST)
Initiate a research query with streaming responses

**Request:**
```json
{
  "query": "What are the latest advances in deep learning?",
  "max_sources": 5,
  "use_thinking_model": true,
  "chat_history": []
}
```

**Response**: Server-Sent Events stream with events like:
- `thinking`: Chain of thought content
- `sources_found`: Web sources discovered
- `response`: Generated response
- `research_complete`: Final summary and metadata

### `/api/system-stats` (GET)
Get real-time system statistics

### `/api/sessions` (GET)
List all research sessions

### `/api/sessions/{session_id}` (GET)
Get specific session details

### `/api/export/{session_id}` (POST)
Export session as PDF or Markdown

### `/api/execute` (POST)
Execute safe terminal commands

### `/api/health` (GET)
Health check endpoint

## 🎓 Example Usage

### Question: "What is Transformer Architecture in Deep Learning?"

1. Type the question in the input box
2. Watch the Smart Avatar thinking indicator
3. See real-time progress:
   - "Thinking..." (deepseek-r1 reasoning)
   - "Searching..." (web queries)
   - "Processing..." (storing findings)
   - "Finalizing..." (generating response)
4. Read the Chain of Thought to see the AI's reasoning
5. Review sources in the right sidebar
6. Export as PDF for later reference

## 📊 Performance Optimization

### For Low-End PCs

- **Async Operations**: All I/O uses asyncio to avoid blocking
- **Model Offloading**: Ollama unloads models from RAM after 5 minutes (configurable)
- **Streaming Responses**: UI updates incrementally instead of waiting for full response
- **Smart Model Selection**: Uses fast gemma2:2b for responses after thinking phase
- **Vector Search**: Only searches relevant documents, not the entire web
- **Component-Level Rendering**: React only re-renders changed components

### Tips for Your System

1. Close unnecessary applications before research
2. Ensure Ollama has enough RAM (4GB minimum, 8GB recommended)
3. Monitor system stats in the right sidebar
4. First research might be slow as models load
5. Subsequent queries will be faster (keep Ollama warm)

## 🔐 Security

- **Local Processing**: All research and data stays on your machine
- **Command Restrictions**: Only safe terminal commands allowed
- **No Data Tracking**: No telemetry or external data sharing
- **Sandboxed Execution**: Terminal commands limited to read-only operations

## 🎨 UI/UX Features

- **Dark Mode**: Easy on the eyes, optimized for focus
- **Lucide Icons**: Clean, professional thin-line icons
- **Smooth Animations**: Polished transitions and interactions
- **Responsive Design**: Works on different screen sizes
- **Real-time Updates**: WebSocket/SSE for live updates
- **Copy to Clipboard**: Easy sharing of AI responses

## 📝 File Structure

### Backend Files

**main.py**: Core FastAPI application
- Research agent loop
- API endpoints
- Session management
- Streaming response handlers

**tools.py**: Tools and utilities
- OllamaManager: Model interaction
- VectorStore: ChromaDB integration
- WebResearcher: Web search and crawling
- FileManager: Local file operations
- TerminalExecutor: Safe command execution
- ResearchSummarizer: PDF/Markdown export

### Frontend Files

**App.jsx**: Main application
- Session management
- Research orchestration
- State management

**Components**:
- **LeftSidebar.jsx**: Chat sessions and history
- **CenterPanel.jsx**: Main chat interface
- **RightSidebar.jsx**: System monitor and sources
- **SmartChildAvatar.jsx**: Animated avatar

## 🐛 Troubleshooting

### Ollama not starting
```bash
sudo systemctl start ollama
sudo systemctl status ollama
```

### Models not downloading
```bash
ollama pull deepseek-r1:7b
ollama pull gemma2:2b
```

### Backend connection errors
```bash
# Check if backend is running
curl http://localhost:8000/api/health
```

### Frontend fails to start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### High CPU/RAM usage
- Close other applications
- Check system stats in right sidebar
- Restart Ollama if needed

## 📚 Learning Resources

- [Ollama Documentation](https://ollama.ai)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [ChromaDB Documentation](https://docs.trychroma.com)
- [LangChain Documentation](https://python.langchain.com)

## 🤝 Contributing

This is a research project. Feel free to:
- Modify models and parameters
- Add new tools and capabilities
- Improve UI/UX
- Optimize performance
- Add new research features

## 📄 License

This project is for educational and research purposes.

## 🎯 Future Enhancements

- [ ] Multi-language support
- [ ] Custom model fine-tuning
- [ ] Collaborative research sessions
- [ ] Advanced data visualization
- [ ] Integration with external services
- [ ] Voice input/output
- [ ] Mobile app version
- [ ] Database backend for history
- [ ] Research paper PDF parsing
- [ ] Citation management integration

## 💡 Tips & Tricks

1. **Complex Queries**: Break down complex research into multiple queries for better results
2. **Follow-ups**: Use chat history context by asking follow-up questions
3. **Source Validation**: Always verify sources in right sidebar
4. **Exports**: Regular exports to maintain research backups
5. **Model Switching**: Modify `.env` to use different Ollama models

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section
2. Verify all services are running
3. Check browser console for frontend errors
4. Check backend logs for API errors
5. Ensure Ollama has sufficient resources

---

**Happy Researching! 🚀**

Built with ❤️ for autonomous learning and research.
