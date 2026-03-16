
# Quick Start Guide - Research Student AI Agent

## For the Impatient 🚀

### Prerequisites Check
```bash
# Check if you have these
python3 --version  # Need 3.10+
node --version     # Need 16+
npm --version      # Need 8+
```

### Step 1: Run Setup (5-10 minutes)
```bash
cd /home/ashu/RnD/research_agent
chmod +x setup.sh
./setup.sh
```

**What this does:**
- Installs all dependencies
- Installs Ollama
- Downloads AI models (this takes time!)
- Sets up directories

### Step 2: Start Everything (1 minute)
```bash
cd /home/ashu/RnD/research_agent
./start-all.sh
```

**What to expect:**
- Backend server starts on http://localhost:8000
- Frontend loads on http://localhost:3000
- Avatar appears in the top-right corner
- You'll see "Ready" status

### Step 3: Try It! (1 minute)
1. Open http://localhost:3000 in your browser
2. Click in the chat box
3. Type: "What is machine learning?"
4. Press Enter or click Send
5. Watch the avatar think! 💡

---

## Detailed Setup

### Option A: Do It Yourself (Advanced)

**1. Backend Setup**
```bash
cd research_agent/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Frontend Setup**
```bash
cd ../frontend
npm install
```

**3. Start Services**
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Frontend
cd frontend && npm start
```

### Option B: Docker (Easiest)
```bash
cd research_agent
docker-compose up
```

---

## First Research Tips

### Good Questions to Try

1. **"What are attention mechanisms in transformers?"**
   - Tests: Web search, markdown formatting, source retrieval

2. **"Latest breakthroughs in AI 2024"**
   - Tests: Multi-source research, summarization

3. **"How does Ollama work?"**
   - Tests: Thinking process, technical explanation

4. **"Best practices for Python development"**
   - Tests: Comprehensive answer, source validation

### What to Expect

**First research (1-2 minutes):**
- Slow because models are loading
- You'll see the progress bar fill up
- Smart avatar shows thinking process
- Chain of Thought reveals AI's reasoning

**Subsequent research (30-60 seconds):**
- Faster because models stay in RAM
- Same quality results
- Progress bar fills quicker

---

## Troubleshooting

### Problem: "OllamaConnectionError"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running:
sudo systemctl start ollama
sudo systemctl status ollama
```

### Problem: Frontend shows "Cannot connect to backend"
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# If not, start it
cd backend && source venv/bin/activate && python main.py
```

### Problem: "Models not found"
```bash
# Download models manually
ollama pull deepseek-r1:7b
ollama pull gemma2:2b
```

### Problem: High CPU/Memory usage
- This is normal during research
- Check right sidebar monitor
- Close other apps if needed
- Models unload automatically after 5 minutes of inactivity

---

## File Locations

Your research gets saved here:
```
/home/ashu/research_notes/
```

### How to Access Research Files
1. Each research is saved as a markdown file
2. Includes query, response, sources, and date
3. Export to PDF directly from the UI

---

## Stop Services

```bash
# If using start-all.sh, press Ctrl+C

# If running separately:
# Terminal 1: Ctrl+C (stops backend)
# Terminal 2: Ctrl+C (stops frontend)

# Stop Ollama (optional):
sudo systemctl stop ollama
```

---

## Advanced Usage

### Change Models

Edit `backend/.env`:
```env
OLLAMA_PRIMARY_MODEL=mistral:latest  # For thinking
OLLAMA_FALLBACK_MODEL=neural-chat    # For responses
```

Then restart backend.

### Add API Keys

If you have Tavily API key:
```env
TAVILY_API_KEY=your_key_here
```

This provides better web search results.

### Monitor System

Watch the right sidebar:
- **CPU**: Should stay below 80% for comfortable use
- **Memory**: Green if < 70%, yellow if 70-85%, red if > 85%
- **Progress**: Shows what the AI is currently doing

---

## Performance Tips for Low-End PC

1. **Close Heavy Apps**: Chrome, VS Code, etc.
2. **Monitor Resources**: Check right sidebar before research
3. **Keep Ollama Warm**: Frequent research = better performance
4. **Use Smaller Models**: Can switch to other models in `.env`
5. **Export Regular**: Save important research to PDF

---

## Next Steps

Ready to dive deeper? Check out:
- `README.md` - Full documentation
- `ARCHITECTURE.md` - Technical details
- `API.md` - API reference
- `DEVELOPMENT.md` - How to extend

---

## Need Help?

1. Check the troubleshooting section above
2. Look at logs:
   ```bash
   # Backend logs (in terminal running main.py)
   # Frontend logs (in browser console, F12)
   ```
3. Read detailed README.md

---

**You're all set! Happy researching! 🔬**
