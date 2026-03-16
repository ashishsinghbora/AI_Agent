#!/bin/bash

# Research Student AI Agent - Docker Compose Start
# Simple one-command startup using Docker Compose

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Starting Research Student AI Agent with Docker"
echo "=========================================="
echo ""

cd "$PROJECT_DIR"

# Check if docker and docker-compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🚀 Starting services with Docker Compose..."
echo "This may take a few minutes to download images and start services."
echo ""

docker-compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "🤖 Ollama: http://localhost:11434"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo ""
echo "The application will be ready in 1-2 minutes."