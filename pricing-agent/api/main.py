"""
Price Optimization Agent - API Server
Run: uvicorn api.main:app --reload --port 8003
"""

from fastapi import FastAPI, HTTPException, Header, Depends
import os

from agent.pricing_agent import agent, Product, PriceRecommendation, BulkPriceRequest, BulkPriceResponse
from shared.middleware import setup_middleware


app = FastAPI(
    title="Price Optimization Agent",
    description="AI-powered dynamic pricing, competitor analysis, and profit maximization",
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
        "agent": "Price Optimization Agent",
        "version": "1.0.0",
        "status": "active",
        "capabilities": [
            "Single Product Pricing",
            "Bulk Pricing Analysis",
            "Competitor Price Insight",
            "Profit Impact Forecasting",
            "Strategy Recommendations",
        ],
        "endpoints": {
            "analyze": "POST /api/v1/analyze",
            "bulk": "POST /api/v1/bulk",
            "competitor": "POST /api/v1/competitor-insight",
            "health": "GET /health",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "price-optimization",
        "version": "1.0.0",
        "provider": "gemini" if os.getenv("GOOGLE_API_KEY") else "mock",
    }


@app.post("/api/v1/analyze", response_model=PriceRecommendation)
async def analyze_price(
    product: Product,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.analyze(product)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Price analysis failed")


@app.post("/api/v1/bulk", response_model=BulkPriceResponse)
async def analyze_bulk(
    request: BulkPriceRequest,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.analyze_bulk(request)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Bulk analysis failed")


@app.post("/api/v1/competitor-insight")
async def competitor_insight(
    product: Product,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.get_competitor_insight(product)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Competitor insight failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
