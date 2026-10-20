"""Unit tests for the Phase 2 WhatsApp-first messaging abstraction.

Everything runs against ``httpx.MockTransport`` — zero network access. The
suite pins the two properties the rest of the COD flow depends on:

1. **WhatsApp-first resolution** — real Meta Cloud API when a complete
   credential pair exists, ``LogProvider`` otherwise.
2. **Failures are honest** — LogProvider masks *missing credentials* only;
   real transport/HTTP failures always surface as ``delivered=False`` so the
   OTP layer never persists a code nobody received.
"""

import json

import httpx
import pytest
from pydantic import ValidationError

from ecommerce_ops.cod import messaging
from ecommerce_ops.cod.messaging import (
    Channel,
    DeliveryResult,
    LogProvider,
    MetaCloudWhatsAppProvider,
    OutboundMessage,
    build_payload,
    build_provider,
    deliver,
    to_recipient,
    whatsapp_configured,
)
from ecommerce_ops.config import Settings


def make_config(**overrides) -> Settings:
    """Hermetic Settings: no .env file, explicit WhatsApp credentials."""
    return Settings(_env_file=None, **overrides)


WHATSAPP_OK = {
    "WHATSAPP_ACCESS_TOKEN": "test-token",
    "WHATSAPP_PHONE_NUMBER_ID": "111222333444555",
}

# ── Data model ──────────────────────────────────────────────────────────


def test_channel_enum():
    assert Channel.WHATSAPP.value == "whatsapp"
    assert Channel.SMS.value == "sms"


def test_outbound_message_defaults_to_whatsapp_cod():
    msg = OutboundMessage(to="+923214567890", body="hello")
    assert msg.channel == Channel.WHATSAPP
    assert msg.purpose == "cod_verification"
    assert msg.template_name is None
    assert msg.template_params == ()


def test_delivery_result_outcome_property():
    ok = DeliveryResult(delivered=True, provider="log", channel=Channel.WHATSAPP)
    bad = DeliveryResult(delivered=False, provider="log", channel=Channel.WHATSAPP)
    assert ok.outcome == "delivered"
    assert bad.outcome == "failed"


# ── Recipient / payload building ────────────────────────────────────────


@pytest.mark.parametrize(
    ("e164", "expected"),
    [
        ("+923214567890", "923214567890"),
        ("923214567890", "923214567890"),
        ("  +92 321 4567890 ", "92 321 4567890"),
    ],
)
def test_to_recipient_strips_plus(e164, expected):
    assert to_recipient(e164) == expected


def test_build_payload_text_message():
    msg = OutboundMessage(to="+923214567890", body="Your code is 123456")
    payload = build_payload(msg, "923214567890")
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "923214567890"
    assert payload["type"] == "text"
    assert payload["text"]["body"] == "Your code is 123456"
    assert payload["text"]["preview_url"] is False
    assert "template" not in payload


def test_build_payload_template_message():
    msg = OutboundMessage(
        to="+923214567890",
        body="fallback",
        template_name="opsiq_otp",
        template_language="ur",
        template_params=("123456",),
    )
    payload = build_payload(msg, "923214567890")
    assert payload["type"] == "template"
    assert payload["template"]["name"] == "opsiq_otp"
    assert payload["template"]["language"] == {"code": "ur"}
    assert payload["template"]["components"] == [
        {
            "type": "body",
            "parameters": [{"type": "text", "text": "123456"}],
        }
    ]


def test_build_payload_template_without_params_omits_components():
    msg = OutboundMessage(
        to="+923214567890",
        body="b",
        template_name="opsiq_otp",
        template_language="en_US",
    )
    payload = build_payload(msg, "923214567890")
    assert payload["template"]["name"] == "opsiq_otp"
    assert "components" not in payload["template"]


# ── Credential resolution (WhatsApp-first) ──────────────────────────────


def test_whatsapp_configured_requires_pair():
    assert whatsapp_configured(make_config(**WHATSAPP_OK)) is True
    assert whatsapp_configured(make_config()) is False


def test_settings_reject_half_configured_whatsapp_pair():
    """Fail closed at startup.

    A half pair would otherwise boot and silently resolve to LogProvider,
    turning the COD step-up challenge into a flow that logs instead of sending.
    """
    with pytest.raises(ValidationError, match="must be set together"):
        make_config(WHATSAPP_ACCESS_TOKEN="t")
    with pytest.raises(ValidationError, match="must be set together"):
        make_config(WHATSAPP_PHONE_NUMBER_ID="123")


def test_whatsapp_configured_defends_against_half_pair():
    """Defence in depth: the guard holds even if a non-Settings object is passed."""

    class _HalfPair:
        WHATSAPP_ACCESS_TOKEN = "t"
        WHATSAPP_PHONE_NUMBER_ID = None

    assert whatsapp_configured(_HalfPair()) is False


def test_build_provider_prefers_meta_cloud_when_configured():
    provider = build_provider(make_config(**WHATSAPP_OK))
    assert isinstance(provider, MetaCloudWhatsAppProvider)
    assert provider.is_configured() is True


def test_build_provider_falls_back_to_log_without_credentials():
    provider = build_provider(make_config())
    assert isinstance(provider, LogProvider)


def test_build_provider_sms_resolves_to_log():
    provider = build_provider(make_config(**WHATSAPP_OK), Channel.SMS)
    assert isinstance(provider, LogProvider)
    assert provider.channel == Channel.SMS


def test_from_settings_raises_without_credentials():
    with pytest.raises(ValueError, match="not configured"):
        MetaCloudWhatsAppProvider.from_settings(make_config())


# ── LogProvider ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_provider_succeeds_without_credentials():
    provider = LogProvider()
    result = await provider.send(OutboundMessage(to="+923214567890", body="hi"))
    assert result.delivered is True
    assert result.provider == "log"
    assert result.message_id.startswith("log-")
    assert result.error is None


@pytest.mark.asyncio
async def test_log_provider_reports_sms_channel():
    provider = LogProvider(Channel.SMS)
    result = await provider.send(
        OutboundMessage(to="+923214567890", body="hi", channel=Channel.SMS)
    )
    assert result.channel == Channel.SMS


# ── MetaCloudWhatsAppProvider over MockTransport ────────────────────────


def _provider(handler, **overrides) -> MetaCloudWhatsAppProvider:
    return MetaCloudWhatsAppProvider(
        access_token="test-token",
        phone_number_id="111222333444555",
        transport=httpx.MockTransport(handler),
        **overrides,
    )


@pytest.mark.asyncio
async def test_meta_cloud_successful_send():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("Authorization")
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"messages": [{"id": "wamid.ABC123"}]})

    provider = _provider(handler)
    result = await provider.send(
        OutboundMessage(to="+923214567890", body="Your code is 123456")
    )

    assert result.delivered is True
    assert result.message_id == "wamid.ABC123"
    assert result.provider == "meta_cloud"
    assert result.error is None
    assert seen["auth"] == "Bearer test-token"
    assert "/111222333444555/messages" in seen["url"]
    assert seen["payload"]["to"] == "923214567890"
    assert seen["payload"]["type"] == "text"


@pytest.mark.asyncio
async def test_meta_cloud_sends_template_payload_when_configured():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"messages": [{"id": "wamid.TPL"}]})

    provider = _provider(handler)
    result = await provider.send(
        OutboundMessage(
            to="+923214567890",
            body="fallback",
            template_name="opsiq_otp",
            template_language="ur",
            template_params=("654321",),
        )
    )
    assert result.delivered is True
    assert seen["payload"]["type"] == "template"
    assert seen["payload"]["template"]["language"] == {"code": "ur"}
    assert seen["payload"]["template"]["components"][0]["parameters"][0]["text"] == "654321"


@pytest.mark.asyncio
async def test_meta_cloud_http_error_surfaces_meta_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": "Invalid parameter", "type": "OAuthException"}},
        )

    result = await _provider(handler).send(OutboundMessage(to="+9231", body="x"))
    assert result.delivered is False
    assert result.message_id is None
    assert result.error is not None
    assert "http_400" in result.error
    assert "Invalid parameter" in result.error


@pytest.mark.asyncio
async def test_meta_cloud_transport_error_becomes_result():
    def handler(request: httpx.Request) -> httpx.Response:
        raise RuntimeError("connection refused")

    result = await _provider(handler).send(OutboundMessage(to="+9231", body="x"))
    assert result.delivered is False
    assert result.error == "transport_error:RuntimeError"


@pytest.mark.asyncio
async def test_meta_cloud_non_json_body_still_reports_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="<html>unavailable</html>")

    result = await _provider(handler).send(OutboundMessage(to="+9231", body="x"))
    assert result.delivered is False
    assert "http_503" in result.error


@pytest.mark.asyncio
async def test_meta_cloud_not_configured_short_circuits():
    provider = MetaCloudWhatsAppProvider(
        access_token="", phone_number_id="123",
        transport=httpx.MockTransport(lambda r: httpx.Response(200)),
    )
    result = await provider.send(OutboundMessage(to="+9231", body="x"))
    assert result.delivered is False
    assert result.error == "not_configured"


@pytest.mark.asyncio
async def test_meta_cloud_endpoint_construction():
    provider = MetaCloudWhatsAppProvider(
        access_token="t", phone_number_id="999", api_version="v20.0"
    )
    assert provider.endpoint == "https://graph.facebook.com/v20.0/999/messages"
    assert provider.channel == Channel.WHATSAPP
    assert provider.name == "meta_cloud"


# ── deliver() choke point ───────────────────────────────────────────────


class _FakeMetric:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def labels(self, **kwargs):
        self.calls.append(kwargs)
        return self

    def inc(self) -> None:
        return None


@pytest.mark.asyncio
async def test_deliver_records_metric_with_log_provider(monkeypatch):
    fake = _FakeMetric()
    monkeypatch.setattr(messaging, "METRIC_COD_MESSAGES_SENT", fake)

    result = await deliver(OutboundMessage(to="+923214567890", body="hi"), make_config())

    assert result.delivered is True
    assert fake.calls == [
        {"channel": "whatsapp", "provider": "log", "outcome": "delivered"}
    ]


@pytest.mark.asyncio
async def test_deliver_records_failed_outcome(monkeypatch):
    fake = _FakeMetric()
    monkeypatch.setattr(messaging, "METRIC_COD_MESSAGES_SENT", fake)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "boom"}})

    config = make_config(**WHATSAPP_OK)
    provider = MetaCloudWhatsAppProvider.from_settings(
        config, transport=httpx.MockTransport(handler)
    )
    monkeypatch.setattr(messaging, "build_provider", lambda cfg, ch: provider)

    result = await deliver(OutboundMessage(to="+9231", body="x"), config)

    assert result.delivered is False
    assert fake.calls == [
        {"channel": "whatsapp", "provider": "meta_cloud", "outcome": "failed"}
    ]


@pytest.mark.asyncio
async def test_deliver_uses_meta_cloud_when_configured(monkeypatch):
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"messages": [{"id": "wamid.X"}]})

    config = make_config(**WHATSAPP_OK)
    provider = MetaCloudWhatsAppProvider.from_settings(
        config, transport=httpx.MockTransport(handler)
    )
    monkeypatch.setattr(messaging, "build_provider", lambda cfg, ch: provider)

    result = await deliver(OutboundMessage(to="+923214567890", body="hi"), config)

    assert result.delivered is True
    assert seen["auth"] == "Bearer test-token"
