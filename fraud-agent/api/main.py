"""
Fraud Detection Agent - API Server
Run: uvicorn api.main:app --reload --port 8007
"""

from fastapi import FastAPI, HTTPException, Header, Depends
import os

from agent.fraud_agent import agent, Order, FraudAnalysis, BulkFraudRequest, BulkFraudResponse
from shared.middleware import setup_middleware


app = FastAPI(
    title="Fraud Detection Agent",
    description="AI-powered real-time fraud detection, risk scoring, and transaction analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

setup_middleware(app, rate_limit_per_minute=60)

API_KEY = os.getenv("AGENT_API_KEY", "demo-key-2024")


async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@app.on_event("shutdown")
async def shutdown():
    await agent.close()


@app.get("/")
async def root():
    return {
        "agent": "Fraud Detection Agent",
        "version": "1.0.0",
        "status": "active",
        "capabilities": [
            "Single Order Analysis",
            "Bulk Order Analysis",
            "Real-time Risk Scoring",
            "Fraud Pattern Detection",
            "Velocity Analysis",
            "Rule + LLM Hybrid Detection",
        ],
        "endpoints": {
            "analyze": "POST /api/v1/analyze",
            "bulk": "POST /api/v1/bulk",
            "health": "GET /health",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "fraud-detection",
        "version": "1.0.0",
        "provider": "gemini" if os.getenv("GOOGLE_API_KEY") else "rule-based",
    }


@app.post("/api/v1/analyze", response_model=FraudAnalysis)
async def analyze_order(
    order: Order,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.analyze(order)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Fraud analysis failed")


@app.post("/api/v1/bulk", response_model=BulkFraudResponse)
async def analyze_bulk(
    request: BulkFraudRequest,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.analyze_bulk(request)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Bulk analysis failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
