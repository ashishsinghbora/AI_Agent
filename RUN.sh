#!/bin/bash
# Research Student AI Agent - Quick Start Guide

echo "=========================================="
echo "  Research Student AI Agent"
echo "  Quick Start Guide"
echo "=========================================="
echo ""

# Check if dependencies are installed
echo "Checking dependencies..."
python_check=$(/home/ashu/RnD/research_agent/backend/venv/bin/pip list | wc -l)
npm_check=$(ls /home/ashu/RnD/research_agent/frontend/node_modules 2>/dev/null | wc -l)

if [ "$python_check" -lt 50 ]; then
    echo "❌ Python dependencies not fully installed"
    exit 1
fi

if [ "$npm_check" -lt 1 ]; then
    echo "❌ npm dependencies not installed"
    exit 1
fi

echo "✓ All dependencies installed"
echo ""

# Check Ollama
echo "Checking Ollama service..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not installed"
    echo "   Install: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

echo "✓ Ollama found"
echo ""

# Start instructions
echo "=========================================="
echo "  Starting Research Agent"
echo "=========================================="
echo ""
echo "Step 1: Start Ollama (in a new terminal):"
echo "  $ ollama serve"
echo ""
echo "Step 2: Wait for Ollama to start, then run:"
echo "  $ cd /home/ashu/RnD/research_agent"
echo "  $ ./start-all.sh"
echo ""
echo "Step 3: Open your browser:"
echo "  http://localhost:3000"
echo ""
echo "=========================================="
echo ""
echo "First time tip: Models need to download on first use"
echo "  - deepseek-r1:7b (~5GB) for thinking"
echo "  - gemma2:2b (~1.5GB) for responses"
echo ""
echo "For more details, see: README.md or QUICKSTART.md"
echo ""
