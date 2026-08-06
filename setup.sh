#!/bin/bash
# ============================================
# AI Agents Deployment Script for Oracle Cloud
# Run this on your Oracle Cloud VM
# ============================================

set -e

echo "=========================================="
echo "  AI Agents Deployment - Oracle Cloud"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Update system
echo -e "${YELLOW}[1/8] Updating system...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install Docker
echo -e "${YELLOW}[2/8] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed successfully!"
else
    echo "Docker already installed."
fi

# Step 3: Install Docker Compose
echo -e "${YELLOW}[3/8] Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo apt install docker-compose -y
    echo "Docker Compose installed!"
else
    echo "Docker Compose already installed."
fi

# Step 4: Clone repos
echo -e "${YELLOW}[4/8] Cloning agent repos...${NC}"
mkdir -p ~/ai-agents && cd ~/ai-agents

if [ ! -d "cs-agent" ]; then
    git clone https://github.com/Ismail-2001/cs-agent.git
    git clone https://github.com/Ismail-2001/inventory-agent.git
    git clone https://github.com/Ismail-2001/price-optimization-agent.git
    git clone https://github.com/Ismail-2001/review-moderation-agent.git
    git clone https://github.com/Ismail-2001/marketing-automation-agent.git
    git clone https://github.com/Ismail-2001/cart-recovery-agent.git
    git clone https://github.com/Ismail-2001/fraud-detection-agent.git
    echo "All repos cloned!"
else
    echo "Repos already exist."
fi

# Step 5: Create environment file
echo -e "${YELLOW}[5/8] Creating environment file...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Get your API key from: https://aistudio.google.com/apikey
GOOGLE_API_KEY=your-google-api-key-here

# Or use OpenAI
OPENAI_API_KEY=

# API Authentication
AGENT_API_KEY=demo-key-2024
EOF
    echo "Created .env file - PLEASE ADD YOUR API KEY!"
    echo "Edit with: nano .env"
else
    echo ".env already exists."
fi

# Step 6: Create docker-compose.yml
echo -e "${YELLOW}[6/8] Creating docker-compose.yml...${NC}"
cat > docker-compose.yml << 'COMPOSE'
version: '3.8'

services:
  cs-agent:
    build: ./cs-agent
    ports:
      - "8001:8001"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AGENT_API_KEY=${AGENT_API_KEY:-demo-key-2024}
    restart: unless-stopped

  inventory-agent:
    build: ./inventory-agent
    ports:
      - "8002:8002"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AGENT_API_KEY=${AGENT_API_KEY:-demo-key-2024}
    restart: unless-stopped

  pricing-agent:
    build: ./pricing-agent
    ports:
      - "8003:8003"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AGENT_API_KEY=${AGENT_API_KEY:-demo-key-2024}
    restart: unless-stopped

  reviews-agent:
    build: ./reviews-agent
    ports:
      - "8004:8004"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AGENT_API_KEY=${AGENT_API_KEY:-demo-key-2024}
    restart: unless-stopped

  marketing-agent:
    build: ./marketing-agent
    ports:
      - "8005:8005"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AGENT_API_KEY=${AGENT_API_KEY:-demo-key-2024}
    restart: unless-stopped

  cart-recovery-agent:
    build: ./cart-recovery-agent
    ports:
      - "8006:8006"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AGENT_API_KEY=${AGENT_API_KEY:-demo-key-2024}
    restart: unless-stopped

  fraud-agent:
    build: ./fraud-agent
    ports:
      - "8007:8007"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AGENT_API_KEY=${AGENT_API_KEY:-demo-key-2024}
    restart: unless-stopped
COMPOSE

# Step 7: Build and start
echo -e "${YELLOW}[7/8] Building and starting agents...${NC}"
docker-compose up -d --build

# Step 8: Wait and test
echo -e "${YELLOW}[8/8] Testing agents...${NC}"
sleep 10

echo ""
echo "=========================================="
echo "  DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Your AI Agents are live at:"
echo ""
echo -e "${GREEN}http://$(curl -s ifconfig.me):8001${NC}  - Customer Support Agent"
echo -e "${GREEN}http://$(curl -s ifconfig.me):8002${NC}  - Inventory Agent"
echo -e "${GREEN}http://$(curl -s ifconfig.me):8003${NC}  - Price Optimization Agent"
echo -e "${GREEN}http://$(curl -s ifconfig.me):8004${NC}  - Review Moderation Agent"
echo -e "${GREEN}http://$(curl -s ifconfig.me):8005${NC}  - Marketing Automation Agent"
echo -e "${GREEN}http://$(curl -s ifconfig.me):8006${NC}  - Cart Recovery Agent"
echo -e "${GREEN}http://$(curl -s ifconfig.me):8007${NC}  - Fraud Detection Agent"
echo ""
echo "Test command:"
echo "  curl http://localhost:8001/health"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop all:"
echo "  docker-compose down"
echo ""
echo "=========================================="
