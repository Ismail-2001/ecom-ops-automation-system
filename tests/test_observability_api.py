"""Tests for Observability API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Observability Endpoint Tests ──────────────────────────


@pytest.mark.asyncio
async def test_traces_list_empty():
    from ecommerce_ops.api.observability import list_traces
    result = await list_traces()
    assert result["traces"] == []
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_metrics_summary_zeros():
    from ecommerce_ops.api.observability import get_metrics_summary
    result = await get_metrics_summary(days=7)
    assert result.total_traces == 0
    assert result.total_cost_usd == 0.0


@pytest.mark.asyncio
async def test_agent_metrics_empty():
    from ecommerce_ops.api.observability import get_agent_metrics
    result = await get_agent_metrics()
    assert result["agents"] == []


@pytest.mark.asyncio
async def test_cost_metrics_zeros():
    from ecommerce_ops.api.observability import get_cost_metrics
    result = await get_cost_metrics(days=30)
    assert result["total_cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_evaluation_history_empty():
    from ecommerce_ops.api.observability import get_evaluation_history
    result = await get_evaluation_history()
    assert result["evaluations"] == []
    assert result["total"] == 0
