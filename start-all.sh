#!/bin/bash

# Research Student AI Agent - Start All Services
# This script starts both the backend FastAPI server and frontend React dev server

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "=========================================="
echo "Starting Research Student AI Agent"
echo "=========================================="
echo ""

# Check if Ollama is running
echo "[1/3] Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running on port 11434"
else
    echo "⚠ Ollama is not responding on port 11434"
fi
echo ""

# Start Backend
echo "[2/3] Starting FastAPI backend..."
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    echo "Error: Python virtual environment not found at $BACKEND_DIR/venv"
    echo "Run ./setup.sh first to create the environment"
    exit 1
fi

source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  Logs: tail -f /tmp/backend.log"
echo ""

# Start Frontend
echo "[3/3] Starting React frontend..."
cd "$FRONTEND_DIR"
npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend starting (PID: $FRONTEND_PID)"
echo "  Logs: tail -f /tmp/frontend.log"
echo ""

echo "=========================================="
echo "Services Started!"
echo "=========================================="
echo ""
echo "Backend API:    http://localhost:8000"
echo "Frontend UI:    http://localhost:3000"
echo "Ollama:         http://localhost:11434"
echo ""
echo "Backend PID:    $BACKEND_PID"
echo "Frontend PID:   $FRONTEND_PID"
echo ""
echo "To stop services:"
echo "  kill $BACKEND_PID  # Stop backend"
echo "  kill $FRONTEND_PID # Stop frontend"
echo ""
echo "View logs:"
echo "  tail -f /tmp/backend.log"
echo "  tail -f /tmp/frontend.log"
echo ""

# Wait for services
wait
