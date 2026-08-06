#!/usr/bin/env bash
# Push each agent to GitHub
# Usage: bash push-all.sh YOUR_GITHUB_USERNAME

USERNAME=${1:-"Ismail-2001"}
GIT_PATH="/c/Program Files/Git/cmd/git.exe"

AGENTS=(
    "cs-agent"
    "inventory-agent"
    "pricing-agent"
    "reviews-agent"
    "marketing-agent"
    "cart-recovery-agent"
    "fraud-agent"
)

echo "=========================================="
echo "Pushing 7 Agents to GitHub"
echo "=========================================="
echo "Username: $USERNAME"
echo ""

for AGENT in "${AGENTS[@]}"; do
    echo "------------------------------------------"
    echo "Processing: $AGENT"
    echo "------------------------------------------"
    
    cd "$AGENT" 2>/dev/null || { echo "ERROR: Directory $AGENT not found"; continue; }
    
    # Init git
    "$GIT_PATH" init
    
    # Create .gitignore if not exists
    if [ ! -f .gitignore ]; then
        echo "__pycache__/" > .gitignore
        echo "*.pyc" >> .gitignore
        echo ".env" >> .gitignore
        echo ".venv/" >> .gitignore
        echo "venv/" >> .gitignore
        echo "*.egg-info/" >> .gitignore
        echo "dist/" >> .gitignore
        echo "build/" >> .gitignore
        echo ".DS_Store" >> .gitignore
    fi
    
    # Stage and commit
    "$GIT_PATH" add .
    "$GIT_PATH" commit -m "Initial commit: $AGENT standalone package"
    
    # Create repo on GitHub (requires gh CLI)
    if command -v gh &> /dev/null; then
        gh repo create "$USERNAME/$AGENT" --public --source=. --push 2>/dev/null || {
            echo "  Setting remote manually..."
            "$GIT_PATH" remote add origin "https://github.com/$USERNAME/$AGENT.git" 2>/dev/null
            "$GIT_PATH" branch -M main
            "$GIT_PATH" push -u origin main
        }
    else
        # Manual push - create repo on GitHub first, then:
        "$GIT_PATH" remote add origin "https://github.com/$USERNAME/$AGENT.git" 2>/dev/null || \
            "$GIT_PATH" remote set-url origin "https://github.com/$USERNAME/$AGENT.git"
        "$GIT_PATH" branch -M main
        "$GIT_PATH" push -u origin main
    fi
    
    echo "  Pushed: https://github.com/$USERNAME/$AGENT"
    
    cd ..
done

echo ""
echo "=========================================="
echo "DONE! All 7 agents pushed to GitHub"
echo "=========================================="
