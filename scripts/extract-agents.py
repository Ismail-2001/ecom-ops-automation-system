#!/usr/bin/env python3
"""
Extract individual agents from OpsIQ as standalone packages.
Run this script from the project root.
"""
import os
import shutil
from pathlib import Path

# Source directories
SOURCE_AGENTS = "ecommerce_ops/agents"
SOURCE_API = "ecommerce_ops/api"
SOURCE_SHARED = "ecommerce_ops"

# Agent definitions
AGENTS = {
    "cs-agent": {
        "name": "Customer Support Agent",
        "description": "AI-powered customer support automation for ecommerce",
        "files": ["customer_support.py"],
        "api_files": ["customer_support.py"],
        "port": 8001,
        "tagline": "Replace 60-80% of support tickets with AI",
    },
    "inventory-agent": {
        "name": "Inventory Management Agent",
        "description": "AI demand forecasting and inventory optimization",
        "files": ["inventory_llm.py"],
        "api_files": [],
        "port": 8002,
        "tagline": "Predict demand, prevent stockouts",
    },
    "pricing-agent": {
        "name": "Price Optimization Agent",
        "description": "Dynamic pricing based on competitor analysis",
        "files": ["pricing.py"],
        "api_files": [],
        "port": 8003,
        "tagline": "Maximize profit with AI-driven pricing",
    },
    "reviews-agent": {
        "name": "Review Moderation Agent",
        "description": "Sentiment analysis and automated review responses",
        "files": ["reviews.py"],
        "api_files": [],
        "port": 8004,
        "tagline": "Analyze sentiment, draft responses instantly",
    },
    "marketing-agent": {
        "name": "Marketing Automation Agent",
        "description": "AI campaign creation and audience segmentation",
        "files": ["marketing_llm.py"],
        "api_files": [],
        "port": 8005,
        "tagline": "Create campaigns that convert",
    },
    "cart-recovery-agent": {
        "name": "Cart Recovery Agent",
        "description": "Abandoned cart recovery with personalized sequences",
        "files": ["cart_recovery.py"],
        "api_files": ["cart_recovery.py"],
        "port": 8006,
        "tagline": "Recover 8-12% of abandoned carts",
    },
    "fraud-agent": {
        "name": "Fraud Detection Agent",
        "description": "Real-time transaction fraud detection",
        "files": ["fraud_llm.py"],
        "api_files": [],
        "port": 8007,
        "tagline": "Catch fraud before it costs you money",
    },
}


def create_agent_package(agent_id, config):
    """Create a standalone agent package."""
    agent_dir = Path(agent_id)
    agent_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (agent_dir / "agent").mkdir(exist_ok=True)
    (agent_dir / "api").mkdir(exist_ok=True)

    # Copy agent files
    for filename in config["files"]:
        src = Path(SOURCE_AGENTS) / filename
        if src.exists():
            shutil.copy(src, agent_dir / "agent" / filename)
            print(f"  Copied {filename}")

    # Copy API files
    for filename in config["api_files"]:
        src = Path(SOURCE_API) / filename
        if src.exists():
            shutil.copy(src, agent_dir / "api" / filename)
            print(f"  Copied API: {filename}")

    # Copy shared files
    for filename in ["_base.py", "cost_tracker.py", "config.py"]:
        src = Path(SOURCE_AGENTS) / filename
        if src.exists():
            shutil.copy(src, agent_dir / "agent" / filename)

    # Create __init__.py files
    (agent_dir / "agent" / "__init__.py").write_text("")
    (agent_dir / "api" / "__init__.py").write_text("")

    # Create main.py (FastAPI server)
    create_main_py(agent_dir, agent_id, config)

    # Create requirements.txt
    create_requirements(agent_dir)

    # Create Dockerfile
    create_dockerfile(agent_dir, config["port"])

    # Create docker-compose.yml
    create_docker_compose(agent_dir, agent_id, config["port"])

    # Create .env.example
    create_env_example(agent_dir)

    # Create README.md
    create_readme(agent_dir, agent_id, config)

    # Create .gitignore
    create_gitignore(agent_dir)

    print(f"  Created {agent_id}/")


def create_main_py(agent_dir, agent_id, config):
    """Create the FastAPI main.py file."""
    class_name = config["files"][0].replace(".py", "").replace("_", " ").title().replace(" ", "")

    content = f'''"""
{config['name']} - Standalone API
{config['description']}
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os

app = FastAPI(
    title="{config['name']}",
    description="{config['description']}",
    version="1.0.0",
)


class TicketRequest(BaseModel):
    ticket_id: str
    customer_email: str
    subject: str
    body: str
    order_id: Optional[str] = None


class TicketResponse(BaseModel):
    ticket_id: str
    sentiment: str
    priority: str
    category: str
    suggested_response: str
    confidence: float
    requires_human: bool


@app.get("/health")
async def health():
    return {{"status": "healthy", "agent": "{agent_id}"}}


@app.post("/api/v1/analyze", response_model=TicketResponse)
async def analyze_ticket(request: TicketRequest):
    """Analyze a support ticket and generate response."""
    # TODO: Integrate your LLM agent here
    return TicketResponse(
        ticket_id=request.ticket_id,
        sentiment="Neutral",
        priority="Medium",
        category="General",
        suggested_response="Thank you for contacting us. We will look into this.",
        confidence=0.85,
        requires_human=False,
    )


@app.get("/")
async def root():
    return {{
        "agent": "{config['name']}",
        "description": "{config['description']}",
        "docs": "/docs",
        "health": "/health",
    }}
'''
    (agent_dir / "api" / "main.py").write_text(content)


def create_requirements(agent_dir):
    """Create requirements.txt."""
    content = """fastapi==0.115.0
uvicorn==0.30.0
pydantic==2.9.0
langchain-google-genai==2.0.0
langchain-openai==0.2.0
python-dotenv==1.0.0
httpx==0.27.0
"""
    (agent_dir / "requirements.txt").write_text(content)


def create_dockerfile(agent_dir, port):
    """Create Dockerfile."""
    content = f"""FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {port}

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "{port}"]
"""
    (agent_dir / "Dockerfile").write_text(content)


def create_docker_compose(agent_dir, agent_id, port):
    """Create docker-compose.yml."""
    content = f"""services:
  {agent_id}:
    build: .
    ports:
      - "{port}:{port}"
    environment:
      - GOOGLE_API_KEY=${{GOOGLE_API_KEY}}
      - OPENAI_API_KEY=${{OPENAI_API_KEY}}
    restart: unless-stopped
"""
    (agent_dir / "docker-compose.yml").write_text(content)


def create_env_example(agent_dir):
    """Create .env.example."""
    content = """# LLM Provider (choose one)
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-api-key

# Optional: Custom settings
# MODEL_NAME=gemini-2.0-flash
# TEMPERATURE=0.7
"""
    (agent_dir / ".env.example").write_text(content)


def create_readme(agent_dir, agent_id, config):
    """Create README.md."""
    content = f"""# {config['name']}

{config['description']}

## Features

- {config['tagline']}
- REST API with OpenAPI docs
- Docker support
- Easy integration

## Quick Start

### 1. Clone and setup

```bash
git clone https://github.com/YOUR_USERNAME/{agent_id}.git
cd {agent_id}
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run with Docker

```bash
docker compose up -d
```

### 3. Or run locally

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port {config['port']}
```

### 4. Test the API

```bash
curl http://localhost:{config['port']}/health

curl -X POST http://localhost:{config['port']}/api/v1/analyze \\
  -H "Content-Type: application/json" \\
  -d '{{
    "ticket_id": "T-1234",
    "customer_email": "user@example.com",
    "subject": "Order not received",
    "body": "I ordered 5 days ago and haven\\'t received it yet."
  }}'
```

## API Documentation

Once running, visit: `http://localhost:{config['port']}/docs`

## Pricing

| Plan | Price | Includes |
|------|-------|----------|
| Starter | $1,500 setup | 1 agent, basic integration |
| Growth | $3,000 setup + $1,000/mo | Full integration, support |
| Enterprise | Custom | Multi-agent, SLA |

## Contact

- Email: your@email.com
- LinkedIn: your-linkedin
"""
    (agent_dir / "README.md").write_text(content)


def create_gitignore(agent_dir):
    """Create .gitignore."""
    content = """__pycache__/
*.pyc
.env
.venv/
venv/
*.egg-info/
dist/
build/
.DS_Store
"""
    (agent_dir / ".gitignore").write_text(content)


def main():
    print("=" * 60)
    print("OpsIQ Agent Extractor")
    print("=" * 60)

    for agent_id, config in AGENTS.items():
        print(f"\nExtracting: {config['name']}...")
        create_agent_package(agent_id, config)

    print("\n" + "=" * 60)
    print("DONE! Created 7 standalone agent packages.")
    print("=" * 60)
    print("\nNext steps:")
    print("1. cd into each agent folder")
    print("2. Create a GitHub repo")
    print("3. Push the code")
    print("4. Deploy to Railway/Render (free)")
    print("\nExample:")
    print("  cd cs-agent")
    print("  git init")
    print("  git add .")
    print('  git commit -m "Initial commit"')
    print("  git remote add origin https://github.com/YOUR_USERNAME/cs-agent.git")
    print("  git push -u origin main")


if __name__ == "__main__":
    main()
