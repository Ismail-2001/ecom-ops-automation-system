import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from ecommerce_ops.api.app import app
from ecommerce_ops.config import settings as app_settings


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        response = await client.get("/health")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data
        assert "dependencies" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_approvals_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        response = await client.get("/api/approvals")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_agents_status_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        response = await client.get("/api/agents/status")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_analytics_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        response = await client.get("/api/analytics")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_audit_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        response = await client.get("/api/audit")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_settings_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        response = await client.get("/api/settings")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_run_endpoint(client):
    with patch("ecommerce_ops.api.app.get_db_session"):
        response = await client.post("/api/run")
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
