"""Phase 3 API tests for the COD verification router.

Covers route registration (legacy + v1), the ``cod:*`` RBAC boundary, phone
sanitization over the wire, and the full OTP request -> verify lifecycle
exercised through the real ``OTPService`` with an injected sender.

Async tests carry explicit ``@pytest.mark.asyncio`` markers: the repo's
``[tool.pytest-asyncio] mode = "auto"`` table is not the key pytest-asyncio
reads, so auto mode is not actually active for this suite.
"""

import os
import re
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["API_KEY"] = "test-key"
os.environ["DEEPSEEK_API_KEY"] = "sk-test-key"

from ecommerce_ops.api.app import app
from ecommerce_ops.api.cod import get_otp_service
from ecommerce_ops.cod.messaging import DeliveryResult
from ecommerce_ops.cod.otp import MemoryOTPStore, OTPService
from ecommerce_ops.config import settings as app_settings
from ecommerce_ops.security import auth as auth_mod
from ecommerce_ops.security.models import Role, User

TEST_API_KEY = "test-key"
AUTH_HEADER = {"Authorization": f"Bearer {TEST_API_KEY}"}

CLEAN_PHONE = "03214567890"  # jazz, valid, no heuristics
SUSPICIOUS_PHONE = "03000000000"  # valid but all_same_digit -> step-up
INVALID_PHONE = "12345"  # too short -> review

CODE_PATTERN = re.compile(r"code (?:is|hai): (\d+)")

# Routers whose legacy path is the exact v1 path with "/api/v1" prepended.
# Each of these previously doubled its segment under v1
# (e.g. /api/v1/support/support/tickets).
MIRRORED_ROUTES = [
    "/support/tickets",
    "/support/health",
    "/shopify/orders",
    "/cart-recovery/health",
    "/cart-recovery/analyze",
    "/memory/health",
    "/security/roles",
    "/observability/traces",
    "/cod/health",
    "/cod/phone/validate",
]


@pytest.fixture(autouse=True)
def _patch_settings_for_testing():
    with (
        patch.object(app_settings, "ENV", "testing"),
        patch.object(app_settings, "API_KEY", MagicMock(get_secret_value=lambda: TEST_API_KEY)),
    ):
        yield


@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADER
    ) as c:
        yield c


@pytest_asyncio.fixture()
async def anon_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture()
def otp_service():
    """Real OTPService over a memory store with a sender that records bodies."""
    captured: list = []

    async def sender(message):
        captured.append(message)
        return DeliveryResult(
            delivered=True,
            provider="test",
            channel=message.channel,
            message_id=f"m{len(captured)}",
        )

    svc = OTPService(store=MemoryOTPStore(), sender=sender)
    app.dependency_overrides[get_otp_service] = lambda: svc
    svc.captured = captured
    yield svc
    app.dependency_overrides.pop(get_otp_service, None)


def _installed_paths() -> set:
    return set(app.openapi()["paths"])


async def _issue_code(client, otp_service, phone=CLEAN_PHONE):
    await client.post("/cod/otp/request", json={"phone": phone})
    body = otp_service.captured[-1].body
    return CODE_PATTERN.search(body).group(1)


# ── Registration ────────────────────────────────────────────────────────


def test_cod_routes_registered_on_both_versions():
    expected = {
        "/cod/phone/validate",
        "/cod/otp/request",
        "/cod/otp/verify",
        "/cod/health",
        "/api/v1/cod/phone/validate",
        "/api/v1/cod/otp/request",
        "/api/v1/cod/otp/verify",
        "/api/v1/cod/health",
    }
    missing = expected - _installed_paths()
    assert not missing, f"missing routes: {sorted(missing)}"


def test_v1_paths_mirror_their_legacy_paths():
    paths = _installed_paths()
    problems = [p for p in MIRRORED_ROUTES if "/api/v1" + p not in paths]
    assert not problems, f"legacy routes without a v1 twin: {problems}"

    # Regression guards for the doubled segment create_v1_router() used to emit
    # by re-adding a prefix each feature router already declares.
    for doubled in (
        "/api/v1/support/support/tickets",
        "/api/v1/shopify/shopify/orders",
        "/api/v1/cart-recovery/cart-recovery/health",
        "/api/v1/cod/cod/health",
    ):
        assert doubled not in paths, f"duplicated prefix still present: {doubled}"


# ── Auth boundary ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_request_is_rejected(anon_client):
    resp = await anon_client.post("/cod/phone/validate", json={"phone": CLEAN_PHONE})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_otp_request_is_rejected(anon_client):
    resp = await anon_client.post("/cod/otp/request", json={"phone": CLEAN_PHONE})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_viewer_can_validate_but_cannot_request_otp(client, monkeypatch):
    viewer = User(id="v1", email="viewer@x", role=Role.VIEWER, is_active=True)

    async def fake_auth(request):
        return viewer

    monkeypatch.setattr(auth_mod, "get_authenticated_user", fake_auth)

    allowed = await client.post("/cod/phone/validate", json={"phone": CLEAN_PHONE})
    assert allowed.status_code == 200

    denied = await client.post("/cod/otp/request", json={"phone": CLEAN_PHONE})
    assert denied.status_code == 403
    assert "cod:execute" in denied.json()["detail"]


@pytest.mark.asyncio
async def test_api_only_role_can_request_but_cannot_validate(client, monkeypatch):
    api_only = User(id="k1", email="svc@x", role=Role.API_ONLY, is_active=True)

    async def fake_auth(request):
        return api_only

    monkeypatch.setattr(auth_mod, "get_authenticated_user", fake_auth)

    allowed = await client.post("/cod/otp/request", json={"phone": CLEAN_PHONE})
    assert allowed.status_code == 200

    denied = await client.post("/cod/phone/validate", json={"phone": CLEAN_PHONE})
    assert denied.status_code == 403
    assert "cod:view" in denied.json()["detail"]


# ── POST /cod/phone/validate ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_normalizes_clean_number(client):
    resp = await client.post("/cod/phone/validate", json={"phone": CLEAN_PHONE})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["normalized"] == CLEAN_PHONE
    assert data["e164"] == "+923214567890"
    assert data["operator"] == "jazz"
    assert data["action"] == "allow"
    assert data["risk_signals"] == []
    assert data["risk_level"] == "low"


@pytest.mark.asyncio
async def test_validate_accepts_e164_and_separated_forms(client):
    for raw in ("+923214567890", "0321-4567890"):
        resp = await client.post("/cod/phone/validate", json={"phone": raw})
        assert resp.status_code == 200
        assert resp.json()["e164"] == "+923214567890"


@pytest.mark.asyncio
async def test_validate_flags_malformed_number_for_review(client):
    resp = await client.post("/cod/phone/validate", json={"phone": INVALID_PHONE})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is False
    assert data["action"] == "review"
    assert data["risk_level"] == "high"
    assert "incomplete" in data["risk_signals"]


@pytest.mark.asyncio
async def test_validate_recommends_step_up_for_suspicious_number(client):
    resp = await client.post("/cod/phone/validate", json={"phone": SUSPICIOUS_PHONE})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["action"] == "needs_otp_verification"
    assert set(data["risk_signals"]) >= {"all_same_digit", "low_entropy"}


@pytest.mark.asyncio
async def test_validate_response_matches_documented_contract(client):
    resp = await client.post("/cod/phone/validate", json={"phone": CLEAN_PHONE})
    assert set(resp.json()) == {
        "raw",
        "normalized",
        "e164",
        "operator",
        "is_valid",
        "risk_signals",
        "risk_level",
        "action",
    }


# ── POST /cod/otp/request ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_issues_code_without_leaking_it(client, otp_service):
    resp = await client.post("/cod/otp/request", json={"phone": CLEAN_PHONE})
    assert resp.status_code == 200
    data = resp.json()

    assert data["sent"] is True
    assert data["expires_in"] == app_settings.OTP_TTL_SECONDS
    assert data["resend_after"] == app_settings.OTP_RESEND_COOLDOWN_SECONDS
    assert data["attempts_allowed"] == app_settings.OTP_MAX_ATTEMPTS
    assert data["reason"] == "ok"

    # The code never appears in the response body - only in the outbound message.
    assert "code" not in data
    assert len(data["request_id"]) > 0

    assert len(otp_service.captured) == 1
    match = CODE_PATTERN.search(otp_service.captured[0].body)
    assert match, f"OTP body did not contain a code: {otp_service.captured[0].body!r}"
    assert len(match.group(1)) == app_settings.OTP_LENGTH


@pytest.mark.asyncio
async def test_request_refuses_malformed_number(client, otp_service):
    resp = await client.post("/cod/otp/request", json={"phone": INVALID_PHONE})
    assert resp.status_code == 200
    assert resp.json()["sent"] is False
    assert resp.json()["reason"] == "invalid_phone"
    assert otp_service.captured == []


@pytest.mark.asyncio
async def test_request_enforces_resend_cooldown(client, otp_service):
    first = await client.post("/cod/otp/request", json={"phone": CLEAN_PHONE})
    second = await client.post("/cod/otp/request", json={"phone": CLEAN_PHONE})

    assert first.json()["sent"] is True
    assert second.json()["sent"] is False
    assert second.json()["reason"] == "cooldown_active"
    assert second.json()["resend_after"] > 0
    assert len(otp_service.captured) == 1


@pytest.mark.asyncio
async def test_request_enforces_hourly_rate_limit(client):
    """The hourly cap is per phone, so it needs a controllable clock.

    A resend is otherwise blocked by the 60s cooldown long before the 3/hour
    budget can be reached, so time is advanced between sends.
    """
    now = {"t": 0.0}
    store = MemoryOTPStore(clock=lambda: now["t"])

    async def sender(message):
        return DeliveryResult(
            delivered=True, provider="test", channel=message.channel, message_id="m"
        )

    svc = OTPService(store=store, sender=sender)
    app.dependency_overrides[get_otp_service] = lambda: svc
    try:
        for _ in range(app_settings.OTP_RATE_LIMIT_MAX_REQUESTS):
            resp = await client.post("/cod/otp/request", json={"phone": CLEAN_PHONE})
            assert resp.json()["sent"] is True, resp.json()
            now["t"] += 61.0

        resp = await client.post("/cod/otp/request", json={"phone": CLEAN_PHONE})
        data = resp.json()
        assert data["sent"] is False
        assert data["reason"] == "rate_limited"
        assert data["resend_after"] > 0
    finally:
        app.dependency_overrides.pop(get_otp_service, None)


@pytest.mark.asyncio
async def test_request_roman_urdu_renders_roman_urdu_body(client, otp_service):
    resp = await client.post("/cod/otp/request", json={"phone": CLEAN_PHONE, "language": "ur"})
    assert resp.json()["sent"] is True
    body = otp_service.captured[0].body
    assert "code hai" in body
    assert CODE_PATTERN.search(body)


@pytest.mark.asyncio
async def test_failed_delivery_issues_no_code(client):
    """A provider outage must neither persist a code nor burn the rate budget."""

    async def sender(message):
        return DeliveryResult(
            delivered=False,
            provider="test",
            channel=message.channel,
            error="upstream down",
        )

    svc = OTPService(store=MemoryOTPStore(), sender=sender)
    app.dependency_overrides[get_otp_service] = lambda: svc
    try:
        resp = await client.post("/cod/otp/request", json={"phone": CLEAN_PHONE})
        assert resp.json()["sent"] is False
        assert resp.json()["reason"] == "provider_error"

        verify = await client.post(
            "/cod/otp/verify", json={"phone": CLEAN_PHONE, "code": "123456"}
        )
        assert verify.json()["verified"] is False
        assert verify.json()["reason"] == "not_found"
    finally:
        app.dependency_overrides.pop(get_otp_service, None)


# ── POST /cod/otp/verify ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_accepts_correct_code(client, otp_service):
    code = await _issue_code(client, otp_service)

    resp = await client.post("/cod/otp/verify", json={"phone": CLEAN_PHONE, "code": code})
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert data["phone"] == CLEAN_PHONE


@pytest.mark.asyncio
async def test_verify_rejects_wrong_code_and_counts_attempt(client, otp_service):
    await _issue_code(client, otp_service)

    wrong = await client.post("/cod/otp/verify", json={"phone": CLEAN_PHONE, "code": "000000"})
    assert wrong.json()["verified"] is False
    assert wrong.json()["reason"] == "invalid_code"
    assert wrong.json()["attempts_remaining"] == app_settings.OTP_MAX_ATTEMPTS - 1


@pytest.mark.asyncio
async def test_verify_is_single_use(client, otp_service):
    code = await _issue_code(client, otp_service)

    first = await client.post("/cod/otp/verify", json={"phone": CLEAN_PHONE, "code": code})
    second = await client.post("/cod/otp/verify", json={"phone": CLEAN_PHONE, "code": code})

    assert first.json()["verified"] is True
    assert second.json()["verified"] is False
    assert second.json()["reason"] == "not_found"


@pytest.mark.asyncio
async def test_verify_without_prior_request_fails_closed(client, otp_service):
    resp = await client.post("/cod/otp/verify", json={"phone": CLEAN_PHONE, "code": "123456"})
    assert resp.json()["verified"] is False
    assert resp.json()["reason"] == "not_found"


@pytest.mark.asyncio
async def test_verify_locks_out_after_max_attempts(client, otp_service):
    code = await _issue_code(client, otp_service)

    last = None
    for _ in range(app_settings.OTP_MAX_ATTEMPTS):
        last = await client.post("/cod/otp/verify", json={"phone": CLEAN_PHONE, "code": "000000"})

    # The final failure destroys the code rather than leaving it attackable.
    assert last.json()["reason"] == "too_many_attempts"
    assert last.json()["attempts_remaining"] == 0

    # The genuine code is now permanently refused: it no longer exists.
    exhausted = await client.post("/cod/otp/verify", json={"phone": CLEAN_PHONE, "code": code})
    assert exhausted.json()["verified"] is False
    assert exhausted.json()["reason"] == "not_found"


@pytest.mark.asyncio
async def test_verified_marker_is_written_after_success(client, otp_service):
    code = await _issue_code(client, otp_service)
    await client.post("/cod/otp/verify", json={"phone": CLEAN_PHONE, "code": code})

    assert await otp_service.is_verified(CLEAN_PHONE) is True


# ── GET /cod/health ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_reports_configured_readiness(client):
    resp = await client.get("/cod/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["whatsapp_configured"] is False
    assert data["provider"] == "log"
    assert data["channel"] == "whatsapp"
    assert data["otp_ttl_seconds"] == app_settings.OTP_TTL_SECONDS
    assert data["otp_max_attempts"] == app_settings.OTP_MAX_ATTEMPTS
    assert data["otp_rate_limit_per_window"] == app_settings.OTP_RATE_LIMIT_MAX_REQUESTS
    assert data["storage_backend"] == "MemoryOTPStore"


@pytest.mark.asyncio
async def test_health_is_reachable_on_versioned_path(client):
    resp = await client.get("/api/v1/cod/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-API-Version") == "1.0"


@pytest.mark.asyncio
async def test_legacy_api_paths_carry_deprecation_headers(client):
    # Health may legitimately report 503 here (no DB in this fixture), but the
    # versioning middleware still stamps every legacy /api/ response.
    resp = await client.get("/api/health")
    assert resp.status_code != 404
    assert resp.headers.get("X-API-Version") == "deprecated"
    assert resp.headers.get("Deprecation") == "true"
    assert "/api/v1/health" in resp.headers.get("Link", "")
