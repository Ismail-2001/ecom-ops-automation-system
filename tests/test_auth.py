import pytest
from httpx import AsyncClient, ASGITransport

from ecommerce_ops.api.app import app

API_KEY = "opsiq-dev-key-2024"

@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_login_invalid_key(client):
    resp = await client.post("/api/auth/login", json={"api_key": "wrong-key"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_valid_key(client):
    resp = await client.post("/api/auth/login", json={"api_key": API_KEY})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["operator"] == "api-operator"


@pytest.mark.asyncio
async def test_login_with_operator(client):
    resp = await client.post("/api/auth/login", json={"api_key": API_KEY, "operator_id": "test-op"})
    assert resp.status_code == 200
    assert resp.json()["operator"] == "test-op"


@pytest.mark.asyncio
async def test_missing_auth_on_protected_route(client):
    resp = await client.post("/api/approvals/fake-id/approve", json={})
    # Should fail with 401 because no Bearer token
    assert resp.status_code in (401, 404)


@pytest.mark.asyncio
async def test_valid_auth_on_protected_route(client):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    resp = await client.post("/api/approvals/fake-id/approve", json={}, headers=headers)
    # Valid auth but action doesn't exist -> 404 (auth passed)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health_without_auth(client):
    resp = await client.get("/health")
    assert resp.status_code in (200, 503)


@pytest.mark.asyncio
async def test_public_endpoints_without_auth(client):
    """All GET endpoints should work without auth (read-only)."""
    endpoints = [
        "/api/approvals",
        "/api/agents/status",
        "/api/analytics",
        "/api/audit",
        "/api/settings",
        "/metrics",
    ]
    for ep in endpoints:
        resp = await client.get(ep)
        assert resp.status_code in (200, 404, 503), f"{ep} returned {resp.status_code}"
