"""
End-to-End Integration Tests
Tests full pipeline: API → Supervisor → Agents → DB → Response
"""

import pytest
import uuid
import time
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from httpx import AsyncClient, ASGITransport


# ── Test Client Fixture ───────────────────────────────────


@pytest.fixture
def transport():
    from ecommerce_ops.api.app import app
    return ASGITransport(app=app)


@pytest.fixture
def client(transport):
    return AsyncClient(transport=transport, base_url="http://test", follow_redirects=True)


# ── Health & Readiness Tests ──────────────────────────────


@pytest.mark.asyncio
async def test_health_endpoint_returns_200_or_503(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/health")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "dependencies" in data
        assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_liveness_always_alive(client):
    resp = await client.get("/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_returns_ok(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/ready")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data


# ── Agent Status Tests ────────────────────────────────────


@pytest.mark.asyncio
async def test_agents_status_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/agents/status")
        assert resp.status_code == 200


# ── Settings Tests ────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_settings(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/settings")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_settings_validation(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.patch("/api/settings", json={"fraud_threshold": 150})
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_settings_po_limit_negative(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.patch("/api/settings", json={"po_limit": -100})
        assert resp.status_code == 400


# ── Approvals Tests ───────────────────────────────────────


@pytest.mark.asyncio
async def test_approvals_list(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/approvals")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_approvals_with_filter(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/approvals?status=pending&agent=FraudAgent")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_approval_not_found(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/approvals/nonexistent-id")
        assert resp.status_code == 404


# ── Audit Logs Tests ──────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_logs_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_audit_logs_with_filter(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/audit?agent=FraudAgent&decision=approved")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_audit_export_csv(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/audit/export?format=csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_audit_export_json(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/audit/export?format=json")
        assert resp.status_code == 200


# ── Analytics Tests ───────────────────────────────────────


@pytest.mark.asyncio
async def test_analytics_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        resp = await client.get("/api/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "graduation" in data
        assert "risk_distribution" in data


# ── Observability Tests ───────────────────────────────────


@pytest.mark.asyncio
async def test_observability_traces(client):
    resp = await client.get("/observability/traces")
    assert resp.status_code == 200
    data = resp.json()
    assert data["traces"] == []


@pytest.mark.asyncio
async def test_observability_health(client):
    resp = await client.get("/observability/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_observability_metrics_summary(client):
    resp = await client.get("/observability/metrics/summary")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_observability_agent_metrics(client):
    resp = await client.get("/observability/metrics/agents")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_observability_cost_metrics(client):
    resp = await client.get("/observability/metrics/costs")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_observability_trace_not_found(client):
    resp = await client.get("/observability/traces/nonexistent")
    assert resp.status_code == 404


# ── Security API Tests ────────────────────────────────────


@pytest.mark.asyncio
async def test_security_health(client):
    resp = await client.get("/security/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_security_roles(client):
    resp = await client.get("/security/roles")
    assert resp.status_code == 200


# ── Memory API Tests ──────────────────────────────────────


@pytest.mark.asyncio
async def test_memory_health(client):
    with patch("ecommerce_ops.api.memory.vector_store") as mock_store:
        mock_store.get_stats.return_value = MagicMock(total_memories=0)
        with patch("ecommerce_ops.api.memory.session_manager") as mock_sess:
            mock_sess.get_stats.return_value = {"total_sessions": 0, "active_sessions": 0}
            resp = await client.get("/memory/health")
            assert resp.status_code == 200


@pytest.mark.asyncio
async def test_memory_list_memories(client):
    with patch("ecommerce_ops.api.memory.vector_store") as mock_store:
        mock_store._filter_memories.return_value = []
        resp = await client.get("/memory/memories")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_memory_list_sessions(client):
    with patch("ecommerce_ops.api.memory.session_manager") as mock_sess:
        mock_sess.get_active_sessions.return_value = []
        resp = await client.get("/memory/sessions")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_memory_get_nonexistent(client):
    resp = await client.get("/memory/memories/nonexistent-id")
    assert resp.status_code == 404


# ── Task Queue Tests ──────────────────────────────────────


@pytest.mark.asyncio
async def test_task_status_not_found(client):
    resp = await client.get("/api/tasks/nonexistent-id")
    assert resp.status_code == 404


# ── Pipeline Trigger Tests ────────────────────────────────


@pytest.mark.asyncio
async def test_trigger_run_creates_task(client):
    with patch("ecommerce_ops.api.app.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = MagicMock(
            shadow_mode=True, fraud_threshold=70,
            po_limit=1000.0, pricing_limit=5.0, reviews_rating_threshold=4,
        )
        mock_session.execute.return_value = mock_result
        mock_db.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch("ecommerce_ops.api.app.ws_manager") as mock_ws:
            mock_ws.broadcast = AsyncMock()
            with patch("ecommerce_ops.api.app.run_pipeline_task") as mock_task:
                resp = await client.post("/api/run")
                assert resp.status_code == 200
                data = resp.json()
                assert "run_id" in data


# ── WebSocket Tests ───────────────────────────────────────


@pytest.mark.asyncio
async def test_websocket_connect(client):
    with patch("ecommerce_ops.api.app.ws_manager") as mock_ws:
        mock_ws.connect = AsyncMock()
        mock_ws.disconnect = AsyncMock()
        resp = await client.get("/ws/queue")
        assert resp.status_code in (101, 200, 403)


# ── Login Tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_invalid_key(client):
    resp = await client.post("/api/auth/login", json={"api_key": "wrong-key"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_no_api_key_configured(client):
    with patch("ecommerce_ops.api.app.app_settings") as mock_settings:
        mock_settings.API_KEY = None
        resp = await client.post("/api/auth/login", json={"api_key": "any-key"})
        assert resp.status_code == 401


# ── Prometheus Metrics Tests ──────────────────────────────


@pytest.mark.asyncio
async def test_metrics_endpoint_prometheus(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("content-type", "")
