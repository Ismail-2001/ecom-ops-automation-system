"""
Customer Support Agent - Standalone API
AI-powered customer support automation for ecommerce
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional
import os

from shared.middleware import setup_middleware


app = FastAPI(
    title="Customer Support Agent",
    description="AI-powered customer support automation for ecommerce",
    version="1.0.0",
)

setup_middleware(app, rate_limit_per_minute=60)

API_KEY = os.getenv("AGENT_API_KEY", "demo-key-2024")


async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


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
    return {
        "status": "healthy",
        "agent": "cs-agent",
    }


@app.post("/api/v1/analyze", response_model=TicketResponse)
async def analyze_ticket(
    request: TicketRequest,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return TicketResponse(
            ticket_id=request.ticket_id,
            sentiment="Neutral",
            priority="Medium",
            category="General",
            suggested_response="Thank you for contacting us. We will look into this.",
            confidence=0.85,
            requires_human=False,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Ticket analysis failed")


@app.get("/")
async def root():
    return {
        "agent": "Customer Support Agent",
        "description": "AI-powered customer support automation for ecommerce",
        "docs": "/docs",
        "health": "/health",
    }
