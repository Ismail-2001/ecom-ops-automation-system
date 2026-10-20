"""WhatsApp-first outbound messaging for COD verification.

Phase 2 of the COD module: the transport behind the step-up challenge. Bodies
are rendered upstream by :mod:`ecommerce_ops.cod.templates` (Roman Urdu +
English); this layer only decides *who delivers them* and *how failures look*.

Locked design decisions
-----------------------
* **WhatsApp-first priority.** When Meta Cloud API credentials are present the
  real provider is used; otherwise delivery degrades to ``LogProvider`` so
  development and unprovisioned environments keep working.
* **LogProvider masks missing credentials, never real failures.** A transport
  error or non-2xx from Meta surfaces as ``DeliveryResult.delivered = False``
  so the OTP layer can refuse to persist a code nobody actually received.
* **Injected transport.** ``httpx.AsyncClient`` / ``transport`` are injectable,
  so the provider is unit-testable with ``httpx.MockTransport`` and zero
  network access.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol

import httpx

from ecommerce_ops.api.metrics import METRIC_COD_MESSAGES_SENT
from ecommerce_ops.config import settings

if TYPE_CHECKING:
    from ecommerce_ops.config import Settings

logger = logging.getLogger("ecommerce_ops.cod.messaging")

__all__ = [
    "Channel",
    "DeliveryResult",
    "LogProvider",
    "MessagingProvider",
    "MetaCloudWhatsAppProvider",
    "OutboundMessage",
    "build_payload",
    "build_provider",
    "deliver",
    "whatsapp_configured",
]


class Channel(StrEnum):
    """Delivery channel. WhatsApp is the priority channel for COD."""

    WHATSAPP = "whatsapp"
    SMS = "sms"


@dataclass(frozen=True)
class OutboundMessage:
    """A single outbound message, already rendered to text.

    ``template_name`` / ``template_params`` are optional: when present the
    provider sends a pre-approved WhatsApp template (the production path for
    OTP volume), otherwise it sends a free-form text message inside Meta's
    24-hour customer-service window.
    """

    to: str
    body: str
    channel: Channel = Channel.WHATSAPP
    purpose: str = "cod_verification"
    template_name: str | None = None
    template_language: str | None = None
    template_params: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeliveryResult:
    """Outcome of one delivery attempt.

    ``delivered=False`` always carries ``error`` so callers can distinguish a
    provider outage from an intentional no-op.
    """

    delivered: bool
    provider: str
    channel: Channel
    message_id: str | None = None
    error: str | None = None
    latency_ms: int = 0

    @property
    def outcome(self) -> str:
        return "delivered" if self.delivered else "failed"


class MessagingProvider(Protocol):
    """Structural contract for every outbound provider."""

    name: str
    channel: Channel

    def is_configured(self) -> bool:
        """True when real credentials are present (LogProvider is always True)."""
        ...

    async def send(self, message: OutboundMessage) -> DeliveryResult:
        """Attempt delivery. Never raises — failures come back as results."""
        ...


# ── Provider: log-only fallback ─────────────────────────────────────────


class LogProvider:
    """Log-only provider used when real credentials are not configured.

    It reports ``delivered=True`` because there is no external dependency that
    can fail — but the body is only written to logs, never to a handset. This
    is the documented fallback for development and ``ENV=testing``.
    """

    name = "log"
    channel = Channel.WHATSAPP

    def __init__(self, channel: Channel = Channel.WHATSAPP) -> None:
        self.channel = channel

    def is_configured(self) -> bool:
        return True

    async def send(self, message: OutboundMessage) -> DeliveryResult:
        logger.info(
            "[COD:%s] to=%s purpose=%s template=%s body=%r",
            message.channel.value,
            message.to,
            message.purpose,
            message.template_name or "-",
            message.body,
        )
        return DeliveryResult(
            delivered=True,
            provider=self.name,
            channel=message.channel,
            message_id=f"log-{uuid.uuid4().hex[:16]}",
        )


# ── Provider: Meta WhatsApp Cloud API ───────────────────────────────────


def build_payload(message: OutboundMessage, recipient: str) -> dict[str, Any]:
    """Build the Meta Cloud API ``/messages`` body.

    Exposed as a module function so payload shape is unit-testable without a
    network round trip. ``recipient`` must already be digits-only international
    format (``923214567890``), never ``+``-prefixed or local ``0``-prefixed.
    """
    payload: dict[str, Any] = {"messaging_product": "whatsapp", "to": recipient}

    if message.template_name:
        template: dict[str, Any] = {
            "name": message.template_name,
            "language": {"code": message.template_language or "en_US"},
        }
        if message.template_params:
            template["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(param)} for param in message.template_params
                    ],
                }
            ]
        payload["type"] = "template"
        payload["template"] = template
    else:
        payload["type"] = "text"
        payload["text"] = {"preview_url": False, "body": message.body}

    return payload


def to_recipient(e164: str) -> str:
    """Strip ``+`` for Meta's ``to`` field (``+92321...`` -> ``92321...``)."""
    return e164.strip().lstrip("+")


def whatsapp_configured(config: Settings | None = None) -> bool:
    """True when a complete Meta Cloud API credential pair is present."""
    cfg = config or settings
    return bool(cfg.WHATSAPP_ACCESS_TOKEN and cfg.WHATSAPP_PHONE_NUMBER_ID)


class MetaCloudWhatsAppProvider:
    """Meta WhatsApp Cloud API sender (``POST /{phone-number-id}/messages``)."""

    name = "meta_cloud"
    channel = Channel.WHATSAPP

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        *,
        api_version: str = "v21.0",
        base_url: str = "https://graph.facebook.com",
        timeout: float = 15.0,
        transport: httpx.AsyncBaseTransport | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._access_token = access_token
        self._phone_number_id = phone_number_id
        self._api_version = api_version
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._transport = transport
        self._client = client

    @classmethod
    def from_settings(
        cls,
        config: Settings | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> MetaCloudWhatsAppProvider:
        """Build from ``Settings``. Requires ``whatsapp_configured()`` first."""
        cfg = config or settings
        token = cfg.WHATSAPP_ACCESS_TOKEN
        if not token or not cfg.WHATSAPP_PHONE_NUMBER_ID:
            raise ValueError("Meta Cloud API credentials are not configured")
        return cls(
            access_token=token.get_secret_value(),
            phone_number_id=cfg.WHATSAPP_PHONE_NUMBER_ID,
            api_version=cfg.WHATSAPP_API_VERSION,
            base_url=cfg.WHATSAPP_API_BASE_URL,
            timeout=cfg.WHATSAPP_TIMEOUT_SECONDS,
            transport=transport,
        )

    def is_configured(self) -> bool:
        return bool(self._access_token and self._phone_number_id)

    @property
    def endpoint(self) -> str:
        return f"{self._base_url}/{self._api_version}/{self._phone_number_id}/messages"

    async def send(self, message: OutboundMessage) -> DeliveryResult:
        if not self.is_configured():
            return DeliveryResult(
                delivered=False,
                provider=self.name,
                channel=message.channel,
                error="not_configured",
            )

        payload = build_payload(message, to_recipient(message.to))
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        started = time.monotonic()

        try:
            if self._client is not None:
                client, owns_client = self._client, False
            else:
                client = httpx.AsyncClient(timeout=self._timeout, transport=self._transport)
                owns_client = True
            try:
                resp = await client.post(self.endpoint, json=payload, headers=headers)
            finally:
                if owns_client:
                    await client.aclose()
        except Exception as exc:
            latency = int((time.monotonic() - started) * 1000)
            logger.warning("WhatsApp send failed to %s: %s", message.to, exc)
            return DeliveryResult(
                delivered=False,
                provider=self.name,
                channel=message.channel,
                error=f"transport_error:{type(exc).__name__}",
                latency_ms=latency,
            )

        latency = int((time.monotonic() - started) * 1000)
        data = _safe_json(resp)

        if resp.status_code >= 300:
            detail = _error_detail(data) or resp.text[:200]
            logger.warning(
                "WhatsApp API rejected message to %s: status=%s detail=%s",
                message.to,
                resp.status_code,
                detail,
            )
            return DeliveryResult(
                delivered=False,
                provider=self.name,
                channel=message.channel,
                error=f"http_{resp.status_code}:{detail}",
                latency_ms=latency,
            )

        message_id = _extract_message_id(data)
        logger.info(
            "WhatsApp message delivered to %s via %s id=%s latency_ms=%d",
            message.to,
            self.name,
            message_id,
            latency,
        )
        return DeliveryResult(
            delivered=True,
            provider=self.name,
            channel=message.channel,
            message_id=message_id,
            latency_ms=latency,
        )


# ── Helpers ─────────────────────────────────────────────────────────────


def _safe_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return None


def _error_detail(data: Any) -> str | None:
    """Extract Meta's ``{"error": {"message": ...}}`` when present."""
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])[:200]
        if isinstance(error, str):
            return error[:200]
    return None


def _extract_message_id(data: Any) -> str | None:
    if isinstance(data, dict):
        messages = data.get("messages")
        if isinstance(messages, list) and messages:
            first = messages[0]
            if isinstance(first, dict):
                return first.get("id")
    return None


# ── Resolution (WhatsApp-first) ─────────────────────────────────────────


def build_provider(
    config: Settings | None = None,
    channel: Channel = Channel.WHATSAPP,
) -> MessagingProvider:
    """Resolve the provider for ``channel``.

    WhatsApp-first: real Meta Cloud API when credentials exist, ``LogProvider``
    otherwise. Any other channel currently resolves to ``LogProvider`` — SMS
    providers land when a PTA sender ID is provisioned.
    """
    if channel == Channel.WHATSAPP and whatsapp_configured(config):
        return MetaCloudWhatsAppProvider.from_settings(config)
    return LogProvider(channel)


async def deliver(message: OutboundMessage, config: Settings | None = None) -> DeliveryResult:
    """Resolve the provider for ``message.channel`` and send, recording metrics."""
    provider = build_provider(config, message.channel)
    result = await provider.send(message)
    METRIC_COD_MESSAGES_SENT.labels(
        channel=result.channel.value,
        provider=result.provider,
        outcome=result.outcome,
    ).inc()
    if not result.delivered:
        logger.warning(
            "COD message not delivered to %s via %s: %s",
            message.to,
            result.provider,
            result.error,
        )
    return result
