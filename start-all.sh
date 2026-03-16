#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Research Agent..."
echo ""
echo "Starting Backend (FastAPI)..."
cd "${PROJECT_DIR}/backend"
source venv/bin/activate
python main.py &
BACKEND_PID=$!

echo ""
echo "Waiting for backend to start..."
sleep 3

echo ""
echo "Starting Frontend (React)..."
cd "${PROJECT_DIR}/frontend"
npm start &
FRONTEND_PID=$!

echo ""
echo -e "\033[0;32m=================================\033[0m"
echo -e "\033[0;32mResearch Agent is starting!\033[0m"
echo -e "\033[0;32m=================================\033[0m"
echo ""
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8000"
echo "Ollama:    http://localhost:11434"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Wait for both processes
wait
