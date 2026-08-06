"""
Cart Recovery Agent - API Server
Run: uvicorn api.main:app --reload --port 8006
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from typing import List
import os

from agent.cart_recovery_agent import agent, AbandonedCart, CartAnalysis, BulkCartResponse
from shared.middleware import setup_middleware


app = FastAPI(
    title="Cart Recovery Agent",
    description="AI-powered abandoned cart detection, recovery strategies, and discount code generation",
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
        "agent": "Cart Recovery Agent",
        "version": "1.0.0",
        "status": "active",
        "capabilities": [
            "Single Cart Analysis",
            "Bulk Cart Analysis",
            "Strategy Recommendations",
            "Discount Code Generation",
            "Recovery Email Copy",
            "Revenue Estimation",
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
        "agent": "cart-recovery",
        "version": "1.0.0",
        "provider": "gemini" if os.getenv("GOOGLE_API_KEY") else "mock",
    }


@app.post("/api/v1/analyze", response_model=CartAnalysis)
async def analyze_cart(
    cart: AbandonedCart,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.analyze(cart)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Cart analysis failed")


@app.post("/api/v1/bulk", response_model=BulkCartResponse)
async def analyze_bulk(
    carts: List[AbandonedCart],
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.analyze_bulk(carts)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Bulk analysis failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
