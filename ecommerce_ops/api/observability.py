"""
Observability API Routes
Endpoints for traces, evaluations, and metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
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
    return {
        "traces": [],
        "total": 0,
        "note": "Traces will appear after pipeline runs",
    }


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get trace details."""
    raise HTTPException(status_code=404, detail="Trace not found")


@router.get("/traces/{trace_id}/spans")
async def get_trace_spans(trace_id: str):
    """Get spans for a trace."""
    raise HTTPException(status_code=404, detail="Trace not found")


@router.get("/traces/{trace_id}/scores")
async def get_trace_scores(trace_id: str):
    """Get scores for a trace."""
    raise HTTPException(status_code=404, detail="Trace not found")


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
    return {
        "evaluations": [],
        "total": 0,
        "period_days": days,
        "note": "Evaluations will appear after agent runs",
    }


# ── Aggregations ───────────────────────────────────────────


@router.get("/metrics/summary")
async def get_metrics_summary(
    days: int = Query(7, ge=1, le=90),
):
    """Get aggregated metrics summary."""
    return TraceAggregation(
        total_traces=0,
        successful_traces=0,
        failed_traces=0,
        avg_duration_ms=0.0,
        p50_duration_ms=0.0,
        p95_duration_ms=0.0,
        p99_duration_ms=0.0,
        total_tokens=0,
        total_cost_usd=0.0,
        avg_score=0.0,
        traces_by_status={},
        traces_by_name={},
        cost_by_model={},
        daily_volume=[],
    )


@router.get("/metrics/agents")
async def get_agent_metrics():
    """Get per-agent metrics."""
    return {
        "agents": [],
        "note": "Agent metrics will appear after pipeline runs",
    }


@router.get("/metrics/costs")
async def get_cost_metrics(
    days: int = Query(30, ge=1, le=90),
):
    """Get cost breakdown metrics."""
    return {
        "period_days": days,
        "total_cost_usd": 0.0,
        "cost_by_model": {},
        "cost_by_agent": {},
        "daily_costs": [],
        "note": "Cost metrics will appear after LLM usage",
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
