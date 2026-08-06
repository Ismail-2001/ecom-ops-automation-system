"""
Review Moderation Agent - API Server
Run: uvicorn api.main:app --reload --port 8004
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from typing import List
import os

from agent.reviews_agent import agent, Review, ReviewAnalysis, BulkReviewRequest, BulkReviewResponse, ReviewTrend
from shared.middleware import setup_middleware


app = FastAPI(
    title="Review Moderation Agent",
    description="AI-powered review analysis, sentiment detection, and automated response drafting",
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
        "agent": "Review Moderation Agent",
        "version": "1.0.0",
        "status": "active",
        "capabilities": [
            "Single Review Analysis",
            "Bulk Review Analysis",
            "Sentiment Detection",
            "Theme Extraction",
            "Auto Response Drafting",
            "Fake Review Detection",
            "Trend Analysis",
        ],
        "endpoints": {
            "analyze": "POST /api/v1/analyze",
            "bulk": "POST /api/v1/bulk",
            "trends": "POST /api/v1/trends",
            "fake-detect": "POST /api/v1/fake-detect",
            "health": "GET /health",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "review-moderation",
        "version": "1.0.0",
        "provider": "gemini" if os.getenv("GOOGLE_API_KEY") else "mock",
    }


@app.post("/api/v1/analyze", response_model=ReviewAnalysis)
async def analyze_review(
    review: Review,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.analyze(review)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Review analysis failed")


@app.post("/api/v1/bulk", response_model=BulkReviewResponse)
async def analyze_bulk(
    request: BulkReviewRequest,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.analyze_bulk(request)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Bulk analysis failed")


@app.post("/api/v1/trends")
async def get_trends(
    reviews: List[Review],
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.get_trends(reviews)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Trend analysis failed")


@app.post("/api/v1/fake-detect")
async def detect_fake(
    review: Review,
    x_api_key: str = Depends(verify_api_key),
):
    try:
        return await agent.detect_fake_review(review)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Fake detection failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
