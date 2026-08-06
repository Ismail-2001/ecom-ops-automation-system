"""
Marketing Automation Agent - API Server
Run: uvicorn api.main:app --reload --port 8005
"""

from fastapi import FastAPI, HTTPException, Header, Depends
import os

from agent.marketing_agent import agent, CampaignRequest, Campaign, BulkCampaignRequest, BulkCampaignResponse
from shared.middleware import setup_middleware


app = FastAPI(
    title="Marketing Automation Agent",
    description="AI-powered campaign creation, audience segmentation, content optimization, and A/B testing",
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
        "agent": "Marketing Automation Agent",
        "version": "1.0.0",
        "status": "active",
        "capabilities": [
            "Campaign Creation",
            "Audience Segmentation",
            "Content Generation",
            "A/B Test Design",
            "ROI Estimation",
            "Bulk Campaign Creation",
        ],
        "triggers": ["manual", "cart_abandonment", "post_purchase", "re_engagement", "seasonal", "product_launch"],
        "audience_segments": ["vip", "high_value", "at_risk", "new", "lapsed", "cart_abandoner"],
        "endpoints": {
            "create": "POST /api/v1/campaign/create",
            "bulk": "POST /api/v1/campaign/bulk",
            "health": "GET /health",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "marketing-automation",
        "version": "1.0.0",
        "provider": "gemini" if os.getenv("GOOGLE_API_KEY") else "rule-based",
    }


@app.post("/api/v1/campaign/create", response_model=Campaign)
async def create_campaign(
    request: CampaignRequest,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.create_campaign(request)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Campaign creation failed")


@app.post("/api/v1/campaign/bulk", response_model=BulkCampaignResponse)
async def create_bulk(
    request: BulkCampaignRequest,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.create_bulk(request)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Bulk campaign creation failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
