# Installation & Deployment Checklist

Use this checklist to verify your installation is complete and working correctly.

## ✅ Pre-Installation

- [ ] Running Fedora Linux (or compatible)
- [ ] Have Python 3.10+ installed (`python3 --version`)
- [ ] Have Node.js 16+ installed (`node --version`)
- [ ] Have npm 8+ installed (`npm --version`)
- [ ] Have 4GB+ RAM available
- [ ] Have 10GB+ free disk space
- [ ] User `ashu` is your current user

## ✅ Directory Structure

After setup, verify these directories exist:

```
/home/ashu/RnD/research_agent/
├── backend/
│   ├── main.py ✓
│   ├── tools.py ✓
│   ├── requirements.txt ✓
│   ├── .env.example ✓
│   ├── venv/ ✓
│   └── __pycache__/ (auto-created)
├── frontend/
│   ├── src/
│   │   ├── App.jsx ✓
│   │   ├── index.js ✓
│   │   ├── index.css ✓
│   │   └── components/
│   │       ├── LeftSidebar.jsx ✓
│   │       ├── CenterPanel.jsx ✓
│   │       ├── RightSidebar.jsx ✓
│   │       └── SmartChildAvatar.jsx ✓
│   ├── public/
│   │   └── index.html ✓
│   ├── package.json ✓
│   ├── .env ✓
│   └── node_modules/ (auto-created)
├── research_notes/ ✓ (created during setup)
├── setup.sh ✓
├── start-all.sh ✓ (created during setup)
├── start-backend.sh ✓ (created during setup)
├── start-frontend.sh ✓ (created during setup)
├── docker-compose.yml ✓
├── Dockerfile.backend ✓
├── frontend/Dockerfile ✓
├── README.md ✓
├── QUICKSTART.md ✓
├── ARCHITECTURE.md ✓
├── API.md ✓
├── DEPLOYMENT.md ✓
├── PROJECT_SUMMARY.md ✓
└── .gitignore ✓
```

## ✅ Installation Steps

- [ ] Navigated to `/home/ashu/RnD/research_agent`
- [ ] Made `setup.sh` executable: `chmod +x setup.sh`
- [ ] Ran setup script: `./setup.sh`
  - [ ] System packages updated
  - [ ] Python dependencies installed
  - [ ] Node dependencies installed
  - [ ] Ollama installed
  - [ ] Models downloaded (deepseek-r1:7b, gemma2:2b)
  - [ ] Directories created
  - [ ] Startup scripts generated

## ✅ Environment & Configuration

- [ ] Backend `.env` file exists or configured
- [ ] Frontend `.env` file exists with correct API URL
- [ ] Ollama is running: `curl http://localhost:11434/api/tags`
- [ ] Models are available: `ollama list`
- [ ] `/home/ashu/research_notes/` directory exists
- [ ] File permissions are correct (755 for dirs, 644 for files)

## ✅ Backend Verification

- [ ] Python virtual environment activated: `source backend/venv/bin/activate`
- [ ] All dependencies installed: `pip list | grep fastapi`
- [ ] Backend starts without errors: `python backend/main.py`
- [ ] Backend listens on port 8000
- [ ] Health check works: `curl http://localhost:8000/api/health`
- [ ] API documentation loads: `open http://localhost:8000/docs`

## ✅ Frontend Verification

- [ ] Node modules installed: `ls frontend/node_modules/ | head -5`
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] Frontend starts: `npm start` (listens on port 3000)
- [ ] React app loads at `http://localhost:3000`
- [ ] No console errors in browser (F12)
- [ ] UI components render correctly

## ✅ Integrated System Check

- [ ] Both services running:
  ```bash
  curl http://localhost:8000/api/health   # Should return JSON
  curl http://localhost:3000              # Should return HTML
  ```
- [ ] Frontend connects to backend
- [ ] System stats update in sidebar
- [ ] Avatar appears in top-right corner
- [ ] Chat input field is visible

## ✅ Research Test

Try a research query:
- [ ] Type "What is machine learning?" in chat
- [ ] Press Enter or click Send
- [ ] Avatar shows thinking indicator
- [ ] Progress bar appears and increases
- [ ] Sources panel populates
- [ ] Response starts streaming
- [ ] Research completes successfully
- [ ] Session saved to history

## ✅ Features Verification

- [ ] Chain of Thought displays when available
- [ ] System Monitor shows CPU/Memory usage
- [ ] Sources show in right sidebar with links
- [ ] Progress bar fills during research
- [ ] Message content can be copied
- [ ] Export buttons work
- [ ] New session button creates blank session
- [ ] Session history shows previous queries

## ✅ File Operations

- [ ] Research file created: `ls /home/ashu/research_notes/`
- [ ] File contains markdown with query + response
- [ ] File has sources listed
- [ ] File permissions are correct

## ✅ Optional: Docker Deployment

If using Docker:
- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker-compose --version`
- [ ] Images built: `docker-compose build`
- [ ] Services start: `docker-compose up -d`
- [ ] All containers running: `docker-compose ps`
- [ ] Backend responds: `curl http://localhost:8000/api/health`
- [ ] Frontend loads: `curl http://localhost:3000`

## ✅ Monitoring

- [ ] CPU usage below 80% during research
- [ ] RAM usage below 6GB
- [ ] No errors in backend logs
- [ ] No errors in browser console
- [ ] Services restart properly after crash

## ✅ System Integration

- [ ] `start-all.sh` starts both services
  ```bash
  ./start-all.sh
  # Both services should start, URLs should display
  ```

- [ ] Services respond to Ctrl+C gracefully
- [ ] Can restart without errors
- [ ] No port conflicts

## ✅ Troubleshooting Verification

Try these commands for verification:

```bash
# Check Ollama
sudo systemctl status ollama
ollama list

# Check backends
curl http://localhost:8000/api/health
curl http://localhost:3000

# Check processes
ps aux | grep python
ps aux | grep node

# Check disk usage
df -h | grep /
du -sh /tmp/chroma/

# Check memory
free -h
```

## ✅ Security Checklist

- [ ] Ollama port 11434 not exposed (if localhost only)
- [ ] Research files have correct permissions
- [ ] Environment files don't contain secrets
- [ ] API keys (if any) not in source control
- [ ] `.gitignore` prevents credential leaks

## ✅ Documentation Review

- [ ] Read `QUICKSTART.md` for quick reference
- [ ] Review `README.md` for full features
- [ ] Check `ARCHITECTURE.md` for system design
- [ ] Study `API.md` for endpoint details
- [ ] Read `DEPLOYMENT.md` for hosting options

## ✅ Performance Baseline

Document your system stats for reference:

```
System Information:
- CPU: [e.g., Intel i5]
- RAM: [e.g., 8GB]
- Storage: [e.g., SSD 256GB]

Baseline Times:
- First research: ___ seconds
- Subsequent research: ___ seconds
- Model load time: ___ seconds
- Average response: ___ seconds

Resource Usage:
- Idle RAM: ___ GB
- During research RAM: ___ GB
- Peak CPU: ___ %
```

## ✅ Backup & Recovery

- [ ] Backup script created for research files
  ```bash
  tar czf backup-research.tar.gz /home/ashu/research_notes/
  ```

- [ ] Backup script for ChromaDB
  ```bash
  tar czf backup-chroma.tar.gz /tmp/chroma/
  ```

- [ ] Backups stored in safe location
- [ ] Tested restore procedure

## ✅ Next Steps

After verification:

1. **Learn the System**
   - [ ] Read all documentation files
   - [ ] Explore the API endpoints
   - [ ] Test different research queries

2. **Customize**
   - [ ] Modify default models in `.env`
   - [ ] Add API keys (Tavily, etc.)
   - [ ] Adjust system parameters

3. **Extend**
   - [ ] Add new tools in `backend/tools.py`
   - [ ] Modify UI components
   - [ ] Add custom prompts
   - [ ] Integrate external services

4. **Deploy**
   - [ ] Set up Docker deployment
   - [ ] Configure nginx proxy
   - [ ] Add SSL certificates
   - [ ] Set up monitoring

5. **Maintain**
   - [ ] Schedule regular backups
   - [ ] Monitor system health
   - [ ] Update models periodically
   - [ ] Review logs

## 📊 Installation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend | ✓ Complete | FastAPI server running |
| Frontend | ✓ Complete | React app loaded |
| Ollama | ✓ Complete | Models downloaded |
| Documentation | ✓ Complete | All guides included |
| Docker | ✓ Complete | Ready to deploy |
| Tests | ✓ Manual | Research query tested |

## 🎯 Success Criteria

Your installation is complete when:

✓ Both backend and frontend are running
✓ You can perform a research query
✓ Avatar shows thinking/research progress
✓ Sources appear and populate
✓ Response streams in real-time
✓ Session is saved to history
✓ Research file is created locally
✓ System monitor shows live stats
✓ No major errors or warnings
✓ All documentation is readable

## 📞 Support

If something isn't working:

1. **Check Logs**
   ```bash
   # Backend logs (in terminal running main.py)
   # Frontend logs (browser console F12)
   ```

2. **Verify Services**
   ```bash
   curl http://localhost:8000/api/health
   curl http://localhost:3000
   ```

3. **Restart Services**
   ```bash
   ./start-all.sh
   ```

4. **Read Documentation**
   - README.md for features
   - DEPLOYMENT.md for troubleshooting
   - API.md for endpoint issues

5. **Check System Resources**
   ```bash
   htop
   df -h
   free -h
   ```

---

**Version: 1.0.0 | Date: January 2024**

Mark off each item as you complete them. When all items are checked, you have a fully functional Research Student AI Agent! 🎉
