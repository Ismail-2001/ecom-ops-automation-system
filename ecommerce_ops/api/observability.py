"""
Observability API Routes
Endpoints for traces, evaluations, and metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ecommerce_ops.config import settings
from ecommerce_ops.observability.evaluation import (
    AgentEvaluation,
    EvaluationFramework,
    evaluation_framework,
)
from ecommerce_ops.observability.langfuse_client import langfuse_client
from ecommerce_ops.observability.trace_models import (
    StoredTrace,
    TraceAggregation,
    TraceStatus,
)

logger = logging.getLogger("ecommerce_ops.api.observability")

router = APIRouter(prefix="/observability", tags=["observability"])


class EvaluationRequest(BaseModel):
    agent_name: str
    decision_id: str
    decision: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None


class BatchEvaluationRequest(BaseModel):
    evaluations: List[EvaluationRequest]


# ── Traces ─────────────────────────────────────────────────


@router.get("/traces")
async def list_traces(
    status: Optional[TraceStatus] = None,
    agent_name: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
):
    """List recent traces."""
    # In production: query Langfuse or local storage
    return {
        "traces": [
            {
                "id": "trace_001",
                "name": "pipeline.run",
                "status": "completed",
                "duration_ms": 1250.5,
                "span_count": 8,
                "average_score": 0.85,
                "total_tokens": 2500,
                "total_cost_usd": 0.025,
                "tags": ["pipeline"],
                "start_time": datetime.utcnow().isoformat(),
            },
            {
                "id": "trace_002",
                "name": "agent.FraudAgent.run",
                "status": "completed",
                "duration_ms": 320.2,
                "span_count": 3,
                "average_score": 0.92,
                "total_tokens": 800,
                "total_cost_usd": 0.008,
                "tags": ["FraudAgent"],
                "start_time": datetime.utcnow().isoformat(),
            },
        ],
        "total": 2,
    }


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get trace details."""
    # In production: query Langfuse or local storage
    return {
        "id": trace_id,
        "name": "pipeline.run",
        "status": "completed",
        "user_id": None,
        "session_id": None,
        "tags": ["pipeline"],
        "metadata": {"run_id": "test-123"},
        "start_time": datetime.utcnow().isoformat(),
        "end_time": datetime.utcnow().isoformat(),
        "duration_ms": 1250.5,
        "spans": [
            {
                "id": "span_001",
                "name": "supervisor.run",
                "span_type": "agent",
                "duration_ms": 800.0,
                "status": "completed",
            },
            {
                "id": "span_002",
                "name": "FraudAgent.run",
                "span_type": "agent",
                "duration_ms": 320.2,
                "status": "completed",
            },
        ],
        "scores": [
            {"name": "pipeline_success", "value": 1.0},
            {"name": "FraudAgent.quality", "value": 0.92},
        ],
        "total_tokens": 2500,
        "total_cost_usd": 0.025,
    }


@router.get("/traces/{trace_id}/spans")
async def get_trace_spans(trace_id: str):
    """Get spans for a trace."""
    return {
        "trace_id": trace_id,
        "spans": [
            {
                "id": "span_001",
                "trace_id": trace_id,
                "name": "supervisor.run",
                "span_type": "agent",
                "input": {"decisions": []},
                "output": {"decisions": 5},
                "duration_ms": 800.0,
                "status": "completed",
                "start_time": datetime.utcnow().isoformat(),
            },
        ],
    }


@router.get("/traces/{trace_id}/scores")
async def get_trace_scores(trace_id: str):
    """Get scores for a trace."""
    return {
        "trace_id": trace_id,
        "scores": [
            {"name": "pipeline_success", "value": 1.0, "comment": "Pipeline completed"},
            {"name": "FraudAgent.quality", "value": 0.92, "comment": "High quality decisions"},
            {"name": "InventoryAgent.quality", "value": 0.88, "comment": "Good decisions"},
        ],
    }


@router.get("/traces/{trace_id}/url")
async def get_trace_url(trace_id: str):
    """Get Langfuse dashboard URL for a trace."""
    url = langfuse_client.get_trace_url(trace_id)
    return {"trace_id": trace_id, "url": url}


# ── Evaluations ────────────────────────────────────────────


@router.post("/evaluate")
async def evaluate_decision(req: EvaluationRequest):
    """Evaluate a single decision."""
    result = evaluation_framework.evaluate_decision(
        agent_name=req.agent_name,
        decision_id=req.decision_id,
        decision=req.decision,
        context=req.context,
        trace_id=req.trace_id,
    )

    return result.score_breakdown


@router.post("/evaluate/batch")
async def evaluate_batch(req: BatchEvaluationRequest):
    """Evaluate multiple decisions."""
    evaluation_items = [
        {
            "agent_name": e.agent_name,
            "decision_id": e.decision_id,
            "dimension": e.decision,
            "context": e.context,
            "trace_id": e.trace_id,
        }
        for e in req.evaluations
    ]

    result = evaluation_framework.evaluate_batch(evaluation_items)
    return result


@router.get("/evaluate/metrics")
async def get_metric_definitions():
    """Get available evaluation metrics."""
    metrics = {}
    for dim, metric in evaluation_framework._metrics.items():
        metrics[dim.value] = {
            "name": metric.name,
            "dimension": metric.dimension.value,
            "metric_type": metric.metric_type.value,
            "description": metric.description,
            "min_value": metric.min_value,
            "max_value": metric.max_value,
            "weight": metric.weight,
        }
    return {"metrics": metrics}


@router.get("/evaluate/history")
async def get_evaluation_history(
    agent_name: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
):
    """Get evaluation history."""
    # In production: query database
    return {
        "evaluations": [
            {
                "id": "eval_001",
                "agent_name": "FraudAgent",
                "decision_id": "dec_001",
                "overall_score": 0.92,
                "passed": True,
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "id": "eval_002",
                "agent_name": "InventoryAgent",
                "decision_id": "dec_002",
                "overall_score": 0.85,
                "passed": True,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ],
        "total": 2,
        "period_days": days,
    }


# ── Aggregations ───────────────────────────────────────────


@router.get("/metrics/summary")
async def get_metrics_summary(
    days: int = Query(7, ge=1, le=90),
):
    """Get aggregated metrics summary."""
    return TraceAggregation(
        total_traces=1250,
        successful_traces=1200,
        failed_traces=50,
        avg_duration_ms=850.0,
        p50_duration_ms=650.0,
        p95_duration_ms=2100.0,
        p99_duration_ms=4500.0,
        total_tokens=250000,
        total_cost_usd=2.50,
        avg_score=0.87,
        traces_by_status={
            "completed": 1200,
            "failed": 50,
        },
        traces_by_name={
            "pipeline.run": 100,
            "agent.FraudAgent.run": 350,
            "agent.InventoryAgent.run": 350,
            "agent.PricingAgent.run": 250,
        },
        cost_by_model={
            "deepseek-chat": 1.50,
            "gemini-2.0-flash": 1.00,
        },
        daily_volume=[
            {"date": "2024-01-01", "traces": 180, "cost": 0.35},
            {"date": "2024-01-02", "traces": 195, "cost": 0.38},
            {"date": "2024-01-03", "traces": 175, "cost": 0.33},
        ],
    )


@router.get("/metrics/agents")
async def get_agent_metrics():
    """Get per-agent metrics."""
    return {
        "agents": [
            {
                "agent_name": "FraudAgent",
                "total_runs": 350,
                "avg_duration_ms": 320.0,
                "avg_score": 0.92,
                "pass_rate": 0.95,
                "total_tokens": 80000,
                "total_cost_usd": 0.80,
            },
            {
                "agent_name": "InventoryAgent",
                "total_runs": 350,
                "avg_duration_ms": 280.0,
                "avg_score": 0.88,
                "pass_rate": 0.92,
                "total_tokens": 75000,
                "total_cost_usd": 0.75,
            },
            {
                "agent_name": "PricingAgent",
                "total_runs": 250,
                "avg_duration_ms": 450.0,
                "avg_score": 0.85,
                "pass_rate": 0.88,
                "total_tokens": 60000,
                "total_cost_usd": 0.60,
            },
            {
                "agent_name": "AbandonedCartAgent",
                "total_runs": 150,
                "avg_duration_ms": 200.0,
                "avg_score": 0.90,
                "pass_rate": 0.94,
                "total_tokens": 20000,
                "total_cost_usd": 0.20,
            },
            {
                "agent_name": "CustomerSupportAgent",
                "total_runs": 150,
                "avg_duration_ms": 350.0,
                "avg_score": 0.87,
                "pass_rate": 0.90,
                "total_tokens": 15000,
                "total_cost_usd": 0.15,
            },
        ],
    }


@router.get("/metrics/costs")
async def get_cost_metrics(
    days: int = Query(30, ge=1, le=90),
):
    """Get cost breakdown metrics."""
    return {
        "period_days": days,
        "total_cost_usd": 2.50,
        "cost_by_model": {
            "deepseek-chat": {"calls": 1200, "tokens": 180000, "cost": 1.50},
            "gemini-2.0-flash": {"calls": 800, "tokens": 70000, "cost": 1.00},
        },
        "cost_by_agent": {
            "FraudAgent": 0.80,
            "InventoryAgent": 0.75,
            "PricingAgent": 0.60,
            "AbandonedCartAgent": 0.20,
            "CustomerSupportAgent": 0.15,
        },
        "daily_costs": [
            {"date": "2024-01-01", "cost": 0.08},
            {"date": "2024-01-02", "cost": 0.09},
            {"date": "2024-01-03", "cost": 0.07},
        ],
    }


# ── Health ─────────────────────────────────────────────────


@router.get("/health")
async def observability_health():
    """Health check for observability service."""
    return {
        "status": "healthy",
        "langfuse_enabled": langfuse_client.is_enabled,
        "evaluation_framework": "loaded",
        "timestamp": datetime.utcnow().isoformat(),
    }
