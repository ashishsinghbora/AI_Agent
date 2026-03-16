#!/bin/bash

# Research Student AI Agent - Setup Script for Fedora
# This script handles all dependencies and initial configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="python3"  # Use system default Python
NODE_VERSION="18"
USER_HOME=$(eval echo ~${SUDO_USER})

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Research Student AI Agent - Setup${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if running on Fedora
if ! grep -q "Fedora\|RedHat\|CentOS" /etc/os-release; then
  echo -e "${YELLOW}Warning: This script is optimized for Fedora. You may need to adjust commands.${NC}\n"
fi

# Update system
echo -e "${BLUE}[1/10] Updating system packages...${NC}"
sudo dnf update -y

# Install system dependencies
echo -e "${BLUE}[2/10] Installing system dependencies...${NC}"
sudo dnf install -y \
  git \
  curl \
  wget \
  gcc \
  g++ \
  make \
  python3 \
  python3-devel \
  python3-pip \
  nodejs \
  npm \
  systemd-devel \
  libffi-devel \
  openssl-devel || true

# Create Python virtual environment for backend
echo -e "${BLUE}[3/10] Setting up Python virtual environment...${NC}"
cd "${PROJECT_DIR}/backend"
${PYTHON_CMD} -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo -e "${BLUE}[4/10] Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Install Ollama
echo -e "${BLUE}[5/10] Installing Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.ai/install.sh | sh
  echo -e "${GREEN}Ollama installed successfully${NC}"
else
  echo -e "${GREEN}Ollama is already installed${NC}"
fi

# Configure Ollama service
echo -e "${BLUE}[6/10] Configuring Ollama service...${NC}"
sudo sed -i 's/^OLLAMA_HOST.*/OLLAMA_HOST=0.0.0.0:11434/' /etc/default/ollama 2>/dev/null || true
sudo systemctl daemon-reload 2>/dev/null || true
sudo systemctl enable ollama 2>/dev/null || true
sudo systemctl start ollama 2>/dev/null || true

# Wait for Ollama to start
echo "Waiting for Ollama to start..."
for i in {1..30}; do
  if curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo -e "${GREEN}Ollama is running${NC}"
    break
  fi
  sleep 1
done

# Pull required models
echo -e "${BLUE}[7/10] Pulling required models (this may take a while)...${NC}"
echo "Pulling deepseek-r1:7b for thinking/research..."
ollama pull deepseek-r1:7b || echo -e "${YELLOW}Note: deepseek-r1:7b download in progress or already exists${NC}"

echo "Pulling gemma2:2b for fast responses..."
ollama pull gemma2:2b || echo -e "${YELLOW}Note: gemma2:2b download in progress or already exists${NC}"

# Setup Node.js and npm
echo -e "${BLUE}[8/10] Installing frontend dependencies...${NC}"
cd "${PROJECT_DIR}/frontend"
npm install

# Create environment files if they don't exist
echo -e "${BLUE}[9/10] Setting up environment files...${NC}"
if [ ! -f "${PROJECT_DIR}/backend/.env" ]; then
  cp "${PROJECT_DIR}/backend/.env.example" "${PROJECT_DIR}/backend/.env"
  echo -e "${GREEN}Created .env file from template${NC}"
fi

# Create research_notes directory with proper permissions
echo -e "${BLUE}[10/10] Setting up research notes directory...${NC}"
mkdir -p "${USER_HOME}/research_notes"
chmod 755 "${USER_HOME}/research_notes"

# Create a startup script
echo -e "${BLUE}Creating startup scripts...${NC}"
cat > "${PROJECT_DIR}/start-backend.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
python main.py
EOF

cat > "${PROJECT_DIR}/start-frontend.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/frontend"
npm start
EOF

cat > "${PROJECT_DIR}/start-all.sh" << 'EOF'
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
EOF

chmod +x "${PROJECT_DIR}/start-backend.sh"
chmod +x "${PROJECT_DIR}/start-frontend.sh"
chmod +x "${PROJECT_DIR}/start-all.sh"

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}Quick Start Guide:${NC}"
echo ""
echo "1. Ensure Ollama is running:"
echo "   sudo systemctl status ollama"
echo ""
echo "2. Start the Research Agent:"
echo "   cd ${PROJECT_DIR}"
echo "   ./start-all.sh"
echo ""
echo "3. Or start components separately:"
echo "   Terminal 1: ./start-backend.sh"
echo "   Terminal 2: ./start-frontend.sh"
echo ""
echo -e "${YELLOW}URLs:${NC}"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   Ollama:    http://localhost:11434"
echo ""
echo -e "${YELLOW}Available Models:${NC}"
echo "   Thinking: deepseek-r1:7b"
echo "   Fast:     gemma2:2b"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "   Backend: ${PROJECT_DIR}/backend/.env"
echo "   Frontend: ${PROJECT_DIR}/frontend/.env"
echo "   Research Notes: ${USER_HOME}/research_notes"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "   See files in ${PROJECT_DIR}/ for more information"
echo ""
