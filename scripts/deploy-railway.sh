#!/usr/bin/env bash
# Deploy agent to Railway (free tier: $5/month credit)
# Run this for each agent after pushing to GitHub
#
# Setup once:
#   npm install -g @railway/cli
#   railway login
#
# Usage: bash deploy-railway.sh cs-agent

AGENT=${1:-"cs-agent"}
GIT_PATH="/c/Program Files/Git/cmd/git.exe"

if [ -z "$1" ]; then
    echo "Usage: bash deploy-railway.sh <agent-name>"
    echo ""
    echo "Agents: cs-agent, inventory-agent, pricing-agent, reviews-agent,"
    echo "        marketing-agent, cart-recovery-agent, fraud-agent"
    exit 1
fi

echo "=========================================="
echo "Deploying $AGENT to Railway"
echo "=========================================="
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Railway CLI not found. Installing..."
    npm install -g @railway/cli
    echo ""
    echo "Now run: railway login"
    echo "Then run this script again."
    exit 1
fi

cd "$AGENT" || { echo "ERROR: Directory $AGENT not found"; exit 1; }

# Login check
railway whoami > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Not logged in. Running: railway login"
    railway login
fi

# Init project (if not already)
if [ ! -f "railway.toml" ]; then
    echo "Initializing Railway project..."
    railway init "$AGENT"
fi

# Set environment variables
echo "Setting environment variables..."
railway variables set GOOGLE_API_KEY="$GOOGLE_API_KEY" 2>/dev/null
railway variables set OPENAI_API_KEY="$OPENAI_API_KEY" 2>/dev/null
railway variables set PORT=8000

# Deploy
echo ""
echo "Deploying..."
railway up --service "$AGENT"

# Get domain
echo ""
echo "Getting domain..."
DOMAIN=$(railway domain 2>/dev/null | head -1)
if [ -z "$DOMAIN" ]; then
    DOMAIN=$(railway status 2>/dev/null | grep -i "domain" | awk '{print $NF}')
fi

echo ""
echo "=========================================="
echo "DEPLOYED!"
echo "=========================================="
echo ""
echo "Agent: $AGENT"
echo "URL:   https://$DOMAIN"
echo "Docs:  https://$DOMAIN/docs"
echo "Health: https://$DOMAIN/health"
echo ""
echo "Test it:"
echo "  curl https://$DOMAIN/health"
echo ""
