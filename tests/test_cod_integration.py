"""Phase 3 integration tests: COD signals wired into surrounding subsystems.

* ``FraudAgent`` scoring Pakistani phone signals
* Cart recovery WhatsApp nudge (template, sanitization, failure isolation)
* ``_send_sms`` routed through the messaging provider instead of a stub
* Roman Urdu / English recovery template rendering
"""

import os
from typing import Any

import pytest

os.environ["ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["API_KEY"] = "test-key"
os.environ["DEEPSEEK_API_KEY"] = "sk-test-key"

from ecommerce_ops.agents.cart_recovery.agent import AbandonedCartAgent
from ecommerce_ops.agents.cart_recovery.models import (
    CustomerProfile,
    RecoveryStrategy,
)
from ecommerce_ops.agents.fraud import (
    PHONE_INVALID_PENALTY,
    PHONE_STEP_UP_PENALTY,
    FraudAgent,
)
from ecommerce_ops.api.cart_recovery import (
    RecoveryActionRequest,
    _execute_recovery,
    _send_recovery_whatsapp,
)
from ecommerce_ops.cod.messaging import (
    Channel,
    DeliveryResult,
    OutboundMessage,
)
from ecommerce_ops.cod.templates import (
    Language,
    Template,
    render_recovery,
)
from ecommerce_ops.tools.definitions import _send_sms

CLEAN_PHONE = "03214567890"
SUSPICIOUS_PHONE = "03000000000"
INVALID_PHONE = "12345"


def _capture_deliver(monkeypatch, result: DeliveryResult | None = None, raise_exc=None):
    """Replace the cart-recovery module's ``deliver`` and record its calls."""
    calls: list[OutboundMessage] = []

    async def fake(message: OutboundMessage):
        if raise_exc is not None:
            raise raise_exc
        calls.append(message)
        return result or DeliveryResult(
            delivered=True,
            provider="test",
            channel=message.channel,
            message_id=f"m{len(calls)}",
        )

    monkeypatch.setattr("ecommerce_ops.api.cart_recovery.deliver", fake)
    return calls


# ── FraudAgent phone signals ────────────────────────────────────────────


def test_invalid_phone_adds_invalid_number_factor():
    score, factors = FraudAgent()._assess_risk({"id": "o_new", "phone": INVALID_PHONE})
    assert score == 50 + PHONE_INVALID_PENALTY
    assert "invalid_phone_number" in factors


def test_suspicious_phone_adds_step_up_factor():
    score, factors = FraudAgent()._assess_risk({"id": "o_new", "phone": SUSPICIOUS_PHONE})
    assert score == 50 + PHONE_STEP_UP_PENALTY
    assert "suspicious_phone_number" in factors


def test_clean_phone_leaves_score_untouched():
    score, factors = FraudAgent()._assess_risk({"id": "o_new", "phone": CLEAN_PHONE})
    assert score == 50
    assert factors == ["standard_check"]


def test_absent_phone_leaves_score_untouched():
    score, factors = FraudAgent()._assess_risk({"id": "o_new"})
    assert score == 50
    assert factors == ["standard_check"]


def test_phone_is_found_on_customer_object():
    order = {"id": "o_new", "customer": {"email": "a@b.c", "phone": INVALID_PHONE}}
    score, factors = FraudAgent()._assess_risk(order)
    assert score == 50 + PHONE_INVALID_PENALTY
    assert "invalid_phone_number" in factors


def test_phone_is_found_on_shipping_address():
    order = {"id": "o_new", "shipping_address": {"phone": INVALID_PHONE}}
    score, _factors = FraudAgent()._assess_risk(order)
    assert score == 50 + PHONE_INVALID_PENALTY


def test_blank_phone_string_is_treated_as_absent():
    order = {"id": "o_new", "phone": "   "}
    score, factors = FraudAgent()._assess_risk(order)
    assert score == 50
    assert factors == ["standard_check"]


def test_known_fixture_rules_still_short_circuit():
    score, factors = FraudAgent()._assess_risk({"id": "o_suspicious", "phone": INVALID_PHONE})
    assert score == 85
    assert factors == ["ip_shipping_mismatch", "velocity_threshold_breached"]


def test_amount_and_phone_signals_compose_and_cap_at_100():
    order = {
        "id": "o_new",
        "phone": INVALID_PHONE,
        "order_total": 5000,
        "line_items": [{} for _ in range(11)],
    }
    score, factors = FraudAgent()._assess_risk(order)
    assert score == 100  # 50 + 20 + 10 + 40
    assert "invalid_phone_number" in factors
    assert "amount_above_threshold" in factors
    assert "bulk_order" in factors


@pytest.mark.asyncio
async def test_run_emits_hold_decision_for_invalid_phone():
    state: dict[str, Any] = {
        "active_orders": [{"id": "o_cod", "phone": INVALID_PHONE}],
        "decisions": [],
    }
    out = await FraudAgent().run(state)

    assert len(out["decisions"]) == 1
    decision = out["decisions"][0]
    assert decision.action_type == "HOLD_ORDER"
    assert decision.action_data["risk_score"] == 50 + PHONE_INVALID_PENALTY
    assert "invalid_phone_number" in decision.action_data["risk_factors"]
    # 90 >= 70, so a human must approve before release.
    assert decision.requires_approval is True


@pytest.mark.asyncio
async def test_run_does_not_flag_clean_phone():
    state = {"active_orders": [{"id": "o_cod", "phone": CLEAN_PHONE}], "decisions": []}
    out = await FraudAgent().run(state)
    assert out["decisions"] == []


# ── Cart recovery WhatsApp nudge ────────────────────────────────────────


@pytest.mark.asyncio
async def test_recovery_whatsapp_sends_for_valid_number(monkeypatch):
    calls = _capture_deliver(monkeypatch)

    sent = await _send_recovery_whatsapp(
        CLEAN_PHONE, "SAVE10", "https://shop.example/checkout", Language.ENGLISH
    )

    assert sent is True
    assert len(calls) == 1
    message = calls[0]
    assert message.channel is Channel.WHATSAPP
    assert message.purpose == "cart_recovery"
    assert message.to == "+923214567890"
    assert "SAVE10" in message.body
    assert "https://shop.example/checkout" in message.body


@pytest.mark.asyncio
async def test_recovery_whatsapp_skips_invalid_number(monkeypatch):
    calls = _capture_deliver(monkeypatch)

    sent = await _send_recovery_whatsapp(INVALID_PHONE, "SAVE10", "https://x", Language.ENGLISH)

    assert sent is False
    assert calls == []


@pytest.mark.asyncio
async def test_recovery_whatsapp_reports_provider_failure(monkeypatch):
    calls = _capture_deliver(
        monkeypatch,
        result=DeliveryResult(
            delivered=False, provider="test", channel=Channel.WHATSAPP, error="quota"
        ),
    )

    sent = await _send_recovery_whatsapp(CLEAN_PHONE, "SAVE10", "https://x", Language.ENGLISH)

    assert sent is False
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_execute_recovery_triggers_whatsapp_with_phone(monkeypatch):
    calls = _capture_deliver(monkeypatch)

    await _execute_recovery(
        "cart-1",
        RecoveryStrategy.DISCOUNT_PERCENT,
        "SAVE10",
        10.0,
        phone=CLEAN_PHONE,
        checkout_url="https://shop.example/checkout",
        language=Language.ROMAN_URDU,
    )

    assert len(calls) == 1
    assert "SAVE10" in calls[0].body


@pytest.mark.asyncio
async def test_execute_recovery_without_phone_sends_nothing(monkeypatch):
    # The batch recovery path still calls this with positional args only.
    calls = _capture_deliver(monkeypatch)

    await _execute_recovery("cart-1", RecoveryStrategy.DISCOUNT_PERCENT, "SAVE10", 10.0)

    assert calls == []


@pytest.mark.asyncio
async def test_execute_recovery_survives_provider_exception(monkeypatch):
    _capture_deliver(monkeypatch, raise_exc=RuntimeError("provider down"))

    await _execute_recovery(
        "cart-1",
        RecoveryStrategy.DISCOUNT_PERCENT,
        "SAVE10",
        10.0,
        phone=CLEAN_PHONE,
        checkout_url="https://x",
    )


def test_recovery_request_accepts_cod_fields():
    req = RecoveryActionRequest(
        cart_id="c1",
        strategy=RecoveryStrategy.DISCOUNT_PERCENT,
        phone=CLEAN_PHONE,
        checkout_url="https://shop.example/checkout",
        language="ur",
    )
    assert req.phone == CLEAN_PHONE
    assert req.language is Language.ROMAN_URDU


def test_recovery_request_defaults_leave_phone_unset():
    req = RecoveryActionRequest(cart_id="c1", strategy=RecoveryStrategy.URGENCY)
    assert req.phone is None
    assert req.language is Language.ENGLISH


# ── CustomerProfile.phone plumbing ──────────────────────────────────────


def test_customer_profile_carries_phone():
    assert CustomerProfile().phone is None
    assert CustomerProfile(phone=CLEAN_PHONE).phone == CLEAN_PHONE


def test_agent_parses_customer_phone():
    cart = AbandonedCartAgent()._parse_cart(
        {
            "id": "c1",
            "shop_domain": "demo.myshopify.com",
            "customer": {"email": "a@b.c", "phone": CLEAN_PHONE},
            "items": [],
        }
    )
    assert cart.customer is not None
    assert cart.customer.phone == CLEAN_PHONE


# ── _send_sms routed through the provider ───────────────────────────────


@pytest.mark.asyncio
async def test_send_sms_succeeds_through_provider():
    result = await _send_sms("+1234567890", "Hello")

    assert result["success"] is True
    assert result["channel"] == "sms"
    assert result["outcome"] == "delivered"
    assert result["provider"]
    assert result["message_id"]


@pytest.mark.asyncio
async def test_send_sms_reports_provider_failure(monkeypatch):
    async def fake(message):
        return DeliveryResult(
            delivered=False, provider="test", channel=Channel.SMS, error="carrier reject"
        )

    monkeypatch.setattr("ecommerce_ops.tools.definitions.deliver", fake)

    result = await _send_sms("+1234567890", "Hello")

    assert result["success"] is False
    assert result["outcome"] == "failed"
    assert result["error"] == "carrier reject"


@pytest.mark.asyncio
async def test_send_sms_never_raises(monkeypatch):
    async def fake(message):
        raise RuntimeError("messaging exploded")

    monkeypatch.setattr("ecommerce_ops.tools.definitions.deliver", fake)

    result = await _send_sms("+1234567890", "Hello")

    assert result["success"] is False
    assert "messaging exploded" in result["error"]


# ── Recovery template ───────────────────────────────────────────────────


def test_render_recovery_english_includes_code_and_link():
    body = render_recovery("SAVE10", "https://shop.example/checkout", Language.ENGLISH)
    assert "SAVE10" in body
    assert "https://shop.example/checkout" in body


def test_render_recovery_roman_urdu_includes_code_and_link():
    body = render_recovery("SAVE10", "https://shop.example/checkout", Language.ROMAN_URDU)
    assert "SAVE10" in body
    assert "https://shop.example/checkout" in body


def test_recovery_template_differs_by_language():
    english = render_recovery("SAVE10", "https://x", Language.ENGLISH)
    urdu = render_recovery("SAVE10", "https://x", Language.ROMAN_URDU)
    assert english != urdu


def test_recovery_template_has_both_languages_registered():
    from ecommerce_ops.cod.templates import _TEMPLATES

    entry = _TEMPLATES[Template.RECOVERY]
    assert set(entry) == {Language.ENGLISH, Language.ROMAN_URDU}
