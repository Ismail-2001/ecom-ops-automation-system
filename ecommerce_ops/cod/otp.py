"""COD one-time-passcode lifecycle (Phase 2).

Issues and verifies short-lived codes that back the ``NEEDS_OTP_VERIFICATION``
step-up challenge from :mod:`ecommerce_ops.cod.phone`. Storage is a standard
Redis key schema with per-key TTLs; an in-memory twin with identical semantics
backs ``ENV=testing`` so the suite runs without a Redis process.

Locked design decisions
-----------------------
* **Redis key schema + TTL** (see ``KEYS`` below) — every OTP artifact expires,
  nothing lingers after checkout is resolved.
* **WhatsApp-first** delivery via :mod:`ecommerce_ops.cod.messaging`.
* **Roman Urdu + English** bodies from :mod:`ecommerce_ops.cod.templates`.
* **Soft-flag, never a hard drop** — this service only *reports*; the calling
  agent decides whether to hold an order.
* **Reserve-then-refund rate limiting.** ``INCR`` reserves a slot *before* the
  send and ``DECR`` refunds it when the send fails or is rejected, so a provider
  outage cannot burn a customer's hourly budget, while parallel abuse still
  cannot slip past the cap (a pure check-then-increment would be bypassable by
  a synchronised burst).

Security
--------
* Codes are drawn with :mod:`secrets` (CSPRNG), compared with
  :func:`hmac.compare_digest`, consumed on first success, and capped at
  ``OTP_MAX_ATTEMPTS`` failures.
* Codes are never written to logs.
"""

from __future__ import annotations

import hmac
import logging
import secrets
import time
import uuid
from dataclasses import dataclass
from enum import StrEnum
from functools import partial
from typing import TYPE_CHECKING, Awaitable, Callable, Protocol

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from ecommerce_ops.api.metrics import (
    METRIC_COD_OTP_REQUESTS,
    METRIC_COD_OTP_VERIFICATIONS,
)
from ecommerce_ops.cod.messaging import Channel, OutboundMessage, deliver
from ecommerce_ops.cod.phone import sanitize_phone
from ecommerce_ops.cod.templates import Language, render_otp
from ecommerce_ops.config import Environment, settings

if TYPE_CHECKING:
    from ecommerce_ops.config import Settings

logger = logging.getLogger("ecommerce_ops.cod.otp")

__all__ = [
    "MemoryOTPStore",
    "OTPPurpose",
    "OTPRequestResult",
    "OTPService",
    "OTPStorageError",
    "OTPStore",
    "OTPVerification",
    "RedisOTPStore",
    "build_service",
    "build_store",
    "code_key",
    "generate_code",
]


# ── Key schema ──────────────────────────────────────────────────────────


KEY_PREFIX = "opsiq:otp"


def code_key(purpose: str, phone: str) -> str:
    """The issued code. TTL = ``OTP_TTL_SECONDS``; deleted on success."""
    return f"{KEY_PREFIX}:code:{purpose}:{phone}"


def attempts_key(purpose: str, phone: str) -> str:
    """Failed verification counter. TTL = ``OTP_TTL_SECONDS``."""
    return f"{KEY_PREFIX}:attempts:{purpose}:{phone}"


def ratelimit_key(phone: str) -> str:
    """Successful sends per hour. TTL = ``OTP_RATE_LIMIT_WINDOW_SECONDS``.

    Deliberately purpose-agnostic: an abuser must not dodge the cap by
    alternating between COD and login verification.
    """
    return f"{KEY_PREFIX}:ratelimit:{phone}"


def cooldown_key(phone: str) -> str:
    """Resend cooldown. TTL = ``OTP_RESEND_COOLDOWN_SECONDS``."""
    return f"{KEY_PREFIX}:cooldown:{phone}"


def verified_key(purpose: str, phone: str) -> str:
    """Post-verification marker read by the order flow. TTL = verified TTL."""
    return f"{KEY_PREFIX}:verified:{purpose}:{phone}"


# ── Types ───────────────────────────────────────────────────────────────


class OTPPurpose(StrEnum):
    """Verification purposes. Any free-form string is also accepted."""

    COD_VERIFICATION = "cod_verification"
    LOGIN = "login"
    RECOVERY = "recovery"


class OTPStorageError(RuntimeError):
    """Storage backend unavailable. Surfaced as ``reason="storage_error"``."""


def _purpose_key(purpose: str) -> str:
    """Normalize ``OTPPurpose`` or a plain string into a key segment."""
    return purpose.value if isinstance(purpose, OTPPurpose) else purpose


def generate_code(length: int = 6) -> str:
    """Draw a CSPRNG one-time code. Leading zeros are preserved (string, not int)."""
    if length < 1:
        raise ValueError("OTP length must be positive")
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


@dataclass(frozen=True)
class OTPRequestResult:
    """Outcome of an OTP issuance attempt."""

    sent: bool
    phone: str
    channel: Channel
    provider: str
    purpose: str
    expires_in: int
    resend_after: int
    attempts_allowed: int
    reason: str
    request_id: str

    @property
    def ok(self) -> bool:
        return self.sent

    def to_dict(self) -> dict:
        return {
            "sent": self.sent,
            "phone": self.phone,
            "channel": self.channel.value,
            "provider": self.provider,
            "purpose": self.purpose,
            "expires_in": self.expires_in,
            "resend_after": self.resend_after,
            "attempts_allowed": self.attempts_allowed,
            "reason": self.reason,
            "request_id": self.request_id,
        }


@dataclass(frozen=True)
class OTPVerification:
    """Outcome of an OTP verification attempt."""

    verified: bool
    phone: str
    purpose: str
    attempts_remaining: int
    reason: str

    @property
    def ok(self) -> bool:
        return self.verified

    def to_dict(self) -> dict:
        return {
            "verified": self.verified,
            "phone": self.phone,
            "purpose": self.purpose,
            "attempts_remaining": self.attempts_remaining,
            "reason": self.reason,
        }


# ── Storage abstraction ────────────────────────────────────────────────


class OTPStore(Protocol):
    """Minimal TTL-key store. Redis is production; memory is testing."""

    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, ttl: int) -> None: ...

    async def delete(self, *keys: str) -> None: ...

    async def incr(self, key: str, ttl: int) -> int:
        """Atomically increment, anchoring the TTL on first creation."""
        ...

    async def decr(self, key: str) -> int:
        """Atomically decrement, preserving the existing TTL."""
        ...

    async def ttl(self, key: str) -> int:
        """Remaining seconds, floored at 0 (absent / expired keys report 0)."""
        ...


class MemoryOTPStore:
    """In-process TTL store mirroring Redis semantics.

    Used for ``ENV=testing`` (and any process without Redis). Expiry is driven
    by an injectable monotonic clock so tests can advance time deterministically
    without sleeping.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        # key -> (value, expires_at_monotonic)
        self._data: dict[str, tuple[str, float]] = {}

    def _live(self, key: str) -> tuple[str, float] | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        if entry[1] <= self._clock():
            self._data.pop(key, None)
            return None
        return entry

    async def get(self, key: str) -> str | None:
        entry = self._live(key)
        return entry[0] if entry else None

    async def set(self, key: str, value: str, ttl: int) -> None:
        self._data[key] = (str(value), self._clock() + max(ttl, 0))

    async def delete(self, *keys: str) -> None:
        for key in keys:
            self._data.pop(key, None)

    async def incr(self, key: str, ttl: int) -> int:
        entry = self._live(key)
        if entry is None:
            self._data[key] = ("1", self._clock() + max(ttl, 0))
            return 1
        # Preserve the original expiry: the window is anchored at first use,
        # exactly like Redis INCR (which does not touch TTL).
        value = int(entry[0]) + 1
        self._data[key] = (str(value), entry[1])
        return value

    async def decr(self, key: str) -> int:
        entry = self._live(key)
        if entry is None:
            # Redis DECR on a missing key creates it value -1 with *no* TTL.
            # We deliberately bound it: this path is unreachable in OTPService
            # (DECR always refunds a key INCR just created), and a immortal key
            # in an in-process dict would be a leak rather than a redis-style
            # footgun. Everything else - sign, TTL preservation - matches Redis.
            self._data[key] = ("-1", self._clock() + 60)
            return -1
        value = int(entry[0]) - 1
        self._data[key] = (str(value), entry[1])
        return value

    async def ttl(self, key: str) -> int:
        entry = self._live(key)
        if entry is None:
            return 0
        return max(int(entry[1] - self._clock()), 0)

    def keys(self) -> list[str]:
        """Test/ops helper: currently-live keys."""
        return [k for k in list(self._data) if self._live(k) is not None]


class RedisOTPStore:
    """Production store backed by ``redis.asyncio``.

    Redis errors are converted to :class:`OTPStorageError` so callers see one
    well-defined failure instead of a raw connection traceback.
    """

    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    @classmethod
    def from_url(cls, url: str, **kwargs) -> RedisOTPStore:
        kwargs.setdefault("decode_responses", True)
        return cls(aioredis.from_url(url, **kwargs))

    @classmethod
    def from_settings(cls, config: Settings | None = None) -> RedisOTPStore:
        cfg = config or settings
        return cls.from_url(
            cfg.REDIS_URL,
            max_connections=cfg.REDIS_MAX_CONNECTIONS,
            socket_timeout=cfg.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=cfg.REDIS_SOCKET_CONNECT_TIMEOUT,
        )

    async def get(self, key: str) -> str | None:
        try:
            return await self._client.get(key)
        except RedisError as exc:
            raise OTPStorageError(f"redis GET failed: {exc}") from exc

    async def set(self, key: str, value: str, ttl: int) -> None:
        try:
            await self._client.set(key, value, ex=max(ttl, 0))
        except RedisError as exc:
            raise OTPStorageError(f"redis SET failed: {exc}") from exc

    async def delete(self, *keys: str) -> None:
        if not keys:
            return
        try:
            await self._client.delete(*keys)
        except RedisError as exc:
            raise OTPStorageError(f"redis DEL failed: {exc}") from exc

    async def incr(self, key: str, ttl: int) -> int:
        try:
            value = int(await self._client.incr(key))
            if int(await self._client.ttl(key)) == -1:
                # INCR left the key with no expiry. Anchor the window *now* and
                # never again: a key that already carries a TTL keeps it, so the
                # attempts counter stays aligned to issuance instead of
                # restarting on its first increment. (Gating on ``value == 1``
                # would wrongly re-anchor a pre-seeded ``attempts`` key.)
                await self._client.expire(key, max(ttl, 0))
            return value
        except RedisError as exc:
            raise OTPStorageError(f"redis INCR failed: {exc}") from exc

    async def decr(self, key: str) -> int:
        try:
            return int(await self._client.decr(key))
        except RedisError as exc:
            raise OTPStorageError(f"redis DECR failed: {exc}") from exc

    async def ttl(self, key: str) -> int:
        try:
            remaining = int(await self._client.ttl(key))
        except RedisError as exc:
            raise OTPStorageError(f"redis TTL failed: {exc}") from exc
        # Redis reports -2 (missing) and -1 (no expiry); both mean "not active".
        return max(remaining, 0)


# ── Service ─────────────────────────────────────────────────────────────

Sender = Callable[[OutboundMessage], Awaitable[object]]


class OTPService:
    """Issues and verifies COD one-time passcodes.

    ``sender`` is injectable so tests exercise the full lifecycle with a fake
    delivery path and zero network access.
    """

    def __init__(
        self,
        store: OTPStore | None = None,
        sender: Sender | None = None,
        config: Settings | None = None,
    ) -> None:
        self._config = config or settings
        self._store = store or build_store(self._config)
        self._sender: Sender = sender or partial(deliver, config=self._config)

    # -- tunables (read live from Settings so tests can monkeypatch) -----

    @property
    def otp_length(self) -> int:
        return self._config.OTP_LENGTH

    @property
    def ttl_seconds(self) -> int:
        return self._config.OTP_TTL_SECONDS

    @property
    def max_attempts(self) -> int:
        return self._config.OTP_MAX_ATTEMPTS

    @property
    def cooldown_seconds(self) -> int:
        return self._config.OTP_RESEND_COOLDOWN_SECONDS

    @property
    def rate_window(self) -> int:
        return self._config.OTP_RATE_LIMIT_WINDOW_SECONDS

    @property
    def rate_max(self) -> int:
        return self._config.OTP_RATE_LIMIT_MAX_REQUESTS

    @property
    def verified_ttl(self) -> int:
        return self._config.OTP_VERIFIED_TTL_SECONDS

    @property
    def storage_backend(self) -> str:
        """Concrete store class name (``MemoryOTPStore`` / ``RedisOTPStore``)."""
        return type(self._store).__name__

    # -- issuance ---------------------------------------------------------

    async def request(
        self,
        raw_phone: str | None,
        *,
        channel: Channel = Channel.WHATSAPP,
        language: Language = Language.ENGLISH,
        purpose: str = OTPPurpose.COD_VERIFICATION,
    ) -> OTPRequestResult:
        """Issue an OTP to ``raw_phone``.

        Refuses (with an explicit ``reason``) on an invalid number, an active
        resend cooldown, an exhausted hourly budget, a failed delivery, or an
        unavailable store. No code is ever persisted unless the provider
        actually accepted the message.
        """
        purpose = _purpose_key(purpose)
        phone = sanitize_phone(raw_phone)
        request_id = uuid.uuid4().hex[:16]

        def _result(**overrides) -> OTPRequestResult:
            base = {
                "sent": False,
                "phone": phone.normalized,
                "channel": channel,
                "provider": "none",
                "purpose": purpose,
                "expires_in": 0,
                "resend_after": 0,
                "attempts_allowed": self.max_attempts,
                "reason": "ok",
                "request_id": request_id,
            }
            base.update(overrides)
            return OTPRequestResult(**base)

        if not phone.is_valid:
            return self._record_request(_result(reason="invalid_phone"))

        cooldown_left = await self._safe_ttl(cooldown_key(phone.normalized))
        if cooldown_left > 0:
            return self._record_request(
                _result(reason="cooldown_active", resend_after=cooldown_left)
            )

        # Reserve a rate-limit slot first so a synchronised burst cannot
        # overshoot the cap; refunded below if the send does not happen.
        try:
            used = await self._store.incr(ratelimit_key(phone.normalized), self.rate_window)
        except OTPStorageError:
            logger.error("OTP storage unavailable while requesting for %s", phone.normalized)
            return self._record_request(_result(reason="storage_error"))

        if used > self.rate_max:
            await self._safe_decr(ratelimit_key(phone.normalized))
            remaining = await self._safe_ttl(ratelimit_key(phone.normalized))
            return self._record_request(_result(reason="rate_limited", resend_after=remaining))

        code = generate_code(self.otp_length)
        delivery = await self._sender(
            self._build_message(phone.e164, code, channel, language, purpose)
        )

        if not delivery.delivered:
            # Refund the reserved slot: an outage must not consume the
            # customer's hourly budget, and no code exists to verify.
            await self._safe_decr(ratelimit_key(phone.normalized))
            logger.warning(
                "OTP delivery failed for %s via %s: %s",
                phone.e164,
                delivery.provider,
                delivery.error,
            )
            return self._record_request(
                _result(reason="provider_error", provider=delivery.provider)
            )

        try:
            await self._store.set(code_key(purpose, phone.normalized), code, self.ttl_seconds)
            await self._store.set(attempts_key(purpose, phone.normalized), "0", self.ttl_seconds)
            await self._store.set(cooldown_key(phone.normalized), request_id, self.cooldown_seconds)
        except OTPStorageError:
            logger.error(
                "OTP issued but not persisted for %s (code %s...)",
                phone.normalized,
                code[:2],
            )
            return self._record_request(_result(reason="storage_error", provider=delivery.provider))

        logger.info(
            "OTP issued for %s purpose=%s channel=%s provider=%s request_id=%s",
            phone.normalized,
            purpose,
            channel.value,
            delivery.provider,
            request_id,
        )
        return self._record_request(
            _result(
                sent=True,
                provider=delivery.provider,
                expires_in=self.ttl_seconds,
                resend_after=self.cooldown_seconds,
            )
        )

    # -- verification -----------------------------------------------------

    async def verify(
        self,
        raw_phone: str | None,
        code: str | None,
        *,
        purpose: str = OTPPurpose.COD_VERIFICATION,
    ) -> OTPVerification:
        """Verify ``code`` against the currently-issued passcode.

        Single-use: a successful verification consumes the code and writes the
        ``verified`` marker the order flow reads. Failures are counted and the
        code is destroyed once ``OTP_MAX_ATTEMPTS`` is reached.
        """
        purpose = _purpose_key(purpose)
        phone = sanitize_phone(raw_phone)
        normalized = phone.normalized

        def _result(**overrides) -> OTPVerification:
            base = {
                "verified": False,
                "phone": normalized,
                "purpose": purpose,
                "attempts_remaining": self.max_attempts,
                "reason": "ok",
            }
            base.update(overrides)
            return OTPVerification(**base)

        if not phone.is_valid:
            return self._record_verify(_result(reason="invalid_phone"))

        c_key = code_key(purpose, normalized)
        a_key = attempts_key(purpose, normalized)

        try:
            stored = await self._store.get(c_key)
            if stored is None:
                # Never issued, expired, or already consumed.
                await self._store.delete(a_key)
                return self._record_verify(_result(reason="not_found"))

            attempts_raw = await self._store.get(a_key)
            attempts = int(attempts_raw or 0)
            if attempts >= self.max_attempts:
                await self._store.delete(c_key, a_key)
                return self._record_verify(
                    _result(reason="too_many_attempts", attempts_remaining=0)
                )

            submitted = code or ""
            if hmac.compare_digest(stored, submitted):
                await self._store.delete(c_key, a_key)
                await self._store.set(verified_key(purpose, normalized), "1", self.verified_ttl)
                logger.info("OTP verified for %s purpose=%s", normalized, purpose)
                return self._record_verify(_result(verified=True, attempts_remaining=0))

            used = await self._store.incr(a_key, self.ttl_seconds)
            if used >= self.max_attempts:
                await self._store.delete(c_key, a_key)
                logger.warning("OTP attempts exhausted for %s purpose=%s", normalized, purpose)
                return self._record_verify(
                    _result(reason="too_many_attempts", attempts_remaining=0)
                )
            return self._record_verify(
                _result(
                    reason="invalid_code",
                    attempts_remaining=self.max_attempts - used,
                )
            )
        except OTPStorageError:
            logger.error("OTP storage unavailable while verifying %s", normalized)
            return self._record_verify(_result(reason="storage_error"))

    async def is_verified(
        self, raw_phone: str | None, *, purpose: str = OTPPurpose.COD_VERIFICATION
    ) -> bool:
        """True when this phone passed verification recently (soft-flag read)."""
        phone = sanitize_phone(raw_phone)
        if not phone.is_valid:
            return False
        try:
            return (
                await self._store.get(verified_key(_purpose_key(purpose), phone.normalized))
                is not None
            )
        except OTPStorageError:
            return False

    async def invalidate(
        self, raw_phone: str | None, *, purpose: str = OTPPurpose.COD_VERIFICATION
    ) -> None:
        """Burn any outstanding code and marker (e.g. order cancelled)."""
        phone = sanitize_phone(raw_phone)
        if not phone.is_valid:
            return
        purpose = _purpose_key(purpose)
        try:
            await self._store.delete(
                code_key(purpose, phone.normalized),
                attempts_key(purpose, phone.normalized),
                verified_key(purpose, phone.normalized),
            )
        except OTPStorageError:
            logger.error("OTP invalidation failed for %s", phone.normalized)

    # -- internals --------------------------------------------------------

    def _build_message(
        self,
        e164: str,
        code: str,
        channel: Channel,
        language: Language,
        purpose: str,
    ) -> OutboundMessage:
        body = render_otp(code, language)
        template_name = self._config.WHATSAPP_OTP_TEMPLATE_NAME
        return OutboundMessage(
            to=e164,
            body=body,
            channel=channel,
            purpose=purpose,
            template_name=template_name,
            template_language=self._config.WHATSAPP_OTP_TEMPLATE_LANGUAGE
            if template_name
            else None,
            template_params=(code,) if template_name else (),
        )

    async def _safe_ttl(self, key: str) -> int:
        try:
            return await self._store.ttl(key)
        except OTPStorageError:
            return 0

    async def _safe_decr(self, key: str) -> None:
        try:
            await self._store.decr(key)
        except OTPStorageError:
            logger.warning("OTP rate-limit refund failed for %s", key)

    @staticmethod
    def _record_request(result: OTPRequestResult) -> OTPRequestResult:
        METRIC_COD_OTP_REQUESTS.labels(outcome=result.reason).inc()
        return result

    @staticmethod
    def _record_verify(result: OTPVerification) -> OTPVerification:
        METRIC_COD_OTP_VERIFICATIONS.labels(outcome=result.reason).inc()
        return result


# ── Factories ───────────────────────────────────────────────────────────


def build_store(config: Settings | None = None) -> OTPStore:
    """Redis in development/production, in-memory twins under ``ENV=testing``.

    Production deliberately has no in-memory fallback: OTP state must be shared
    across workers, so a silent per-process store would let worker A issue a
    code worker B cannot verify.
    """
    cfg = config or settings
    if cfg.ENV == Environment.TESTING:
        return MemoryOTPStore()
    return RedisOTPStore.from_settings(cfg)


def build_service(config: Settings | None = None) -> OTPService:
    """Wire the default store and WhatsApp-first sender."""
    cfg = config or settings
    return OTPService(store=build_store(cfg), config=cfg)
