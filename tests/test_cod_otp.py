"""Unit tests for the Phase 2 COD OTP lifecycle.

Hermetic: no Redis process, no network. Storage runs on ``MemoryOTPStore``
with an injectable fake clock (so TTLs are exercised without sleeping), and
delivery goes through an injected fake sender.

The suite pins the security and abuse-protection properties the step-up
challenge relies on:

* single-use codes consumed on first success,
* attempt capping that destroys the code,
* expiry,
* **rate-limit reserve-then-refund** - a provider outage must not burn a
  customer's hourly budget, while a parallel burst still cannot slip past.
"""

import re
from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from ecommerce_ops.cod.messaging import Channel, DeliveryResult
from ecommerce_ops.cod.otp import (
    MemoryOTPStore,
    OTPPurpose,
    OTPService,
    OTPStorageError,
    RedisOTPStore,
    attempts_key,
    build_store,
    code_key,
    cooldown_key,
    generate_code,
    ratelimit_key,
    verified_key,
)
from ecommerce_ops.cod.templates import Language
from ecommerce_ops.config import Settings

PHONE = "03214567890"
E164 = "+923214567890"
INVALID_PHONE = "031234567"  # 9 digits -> structurally invalid
PURPOSE = OTPPurpose.COD_VERIFICATION

_CODE_RE = re.compile(r"(\d+)$")


def make_config(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


class FakeClock:
    """Deterministic monotonic clock so TTLs advance without sleeping."""

    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeSender:
    """Injected sender; records messages and can be flipped to fail."""

    def __init__(self, delivered: bool = True, error: str | None = None) -> None:
        self.delivered = delivered
        self.error = error
        self.provider = "meta_cloud"
        self.messages = []

    async def __call__(self, message) -> DeliveryResult:
        self.messages.append(message)
        return DeliveryResult(
            delivered=self.delivered,
            provider=self.provider,
            channel=message.channel,
            message_id="wamid.1" if self.delivered else None,
            error=None if self.delivered else (self.error or "http_500:boom"),
        )


class Harness:
    def __init__(self, sender: FakeSender | None = None, config: Settings | None = None):
        self.clock = FakeClock()
        self.store = MemoryOTPStore(clock=self.clock)
        self.sender = sender if sender is not None else FakeSender()
        self.config = config or make_config()
        self.service = OTPService(
            store=self.store, sender=self.sender, config=self.config
        )

    @property
    def last_code(self) -> str:
        return _CODE_RE.search(self.sender.messages[-1].body).group(1)

    async def issue(self, raw_phone: str = PHONE, **kwargs):
        return await self.service.request(raw_phone, **kwargs)


def wrong_code(code: str) -> str:
    """Deterministically derive a non-matching code (no 1-in-a-million flakes)."""
    flipped = "0" if code[0] != "0" else "1"
    return flipped + code[1:]


class BrokenStore:
    """Full OTPStore implementation whose every operation fails.

    Deliberately complete: a store missing a method would raise AttributeError
    and mask the storage-failure path we are trying to observe.
    """

    async def get(self, key):
        raise OTPStorageError("redis down")

    async def set(self, key, value, ttl):
        raise OTPStorageError("redis down")

    async def delete(self, *keys):
        raise OTPStorageError("redis down")

    async def incr(self, key, ttl):
        raise OTPStorageError("redis down")

    async def decr(self, key):
        raise OTPStorageError("redis down")

    async def ttl(self, key):
        raise OTPStorageError("redis down")


# ══ generate_code ══════════════════════════════════════════════════════


def test_generate_code_default_length_six():
    assert len(generate_code()) == 6


def test_generate_code_is_all_digits():
    assert generate_code(8).isdigit()
    assert len(generate_code(8)) == 8


def test_generate_code_uses_csprng_and_varies():
    codes = {generate_code() for _ in range(50)}
    assert len(codes) > 1


def test_generate_code_preserves_leading_zeroes(monkeypatch):
    monkeypatch.setattr("ecommerce_ops.cod.otp.secrets.randbelow", lambda n: 0)
    assert generate_code(6) == "000000"


def test_generate_code_rejects_non_positive_length():
    with pytest.raises(ValueError, match="positive"):
        generate_code(0)


# ══ Key schema ═════════════════════════════════════════════════════════


def test_key_schema_shapes():
    assert code_key("cod_verification", PHONE) == (
        "opsiq:otp:code:cod_verification:03214567890"
    )
    assert attempts_key("cod_verification", PHONE).startswith("opsiq:otp:attempts:")
    assert ratelimit_key(PHONE) == "opsiq:otp:ratelimit:03214567890"
    assert cooldown_key(PHONE) == "opsiq:otp:cooldown:03214567890"
    assert verified_key("cod_verification", PHONE).startswith("opsiq:otp:verified:")


def test_ratelimit_key_is_purpose_agnostic():
    """Anti-bombing: alternating purposes must not dodge the hourly cap."""
    assert ratelimit_key(PHONE) == f"opsiq:otp:ratelimit:{PHONE}"
    assert "cod_verification" not in ratelimit_key(PHONE)


def test_attempt_and_code_keys_are_purpose_scoped():
    assert code_key("login", PHONE) != code_key("cod_verification", PHONE)
    assert attempts_key("login", PHONE) != attempts_key("cod_verification", PHONE)


# ══ MemoryOTPStore semantics ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_memory_store_set_get_delete():
    store = MemoryOTPStore(clock=FakeClock())
    await store.set("k", "v", 100)
    assert await store.get("k") == "v"
    await store.delete("k")
    assert await store.get("k") is None


@pytest.mark.asyncio
async def test_memory_store_delete_missing_key_is_safe():
    store = MemoryOTPStore(clock=FakeClock())
    await store.delete("never", "existed")
    assert await store.get("never") is None


@pytest.mark.asyncio
async def test_memory_store_expires_after_ttl():
    clock = FakeClock()
    store = MemoryOTPStore(clock=clock)
    await store.set("k", "v", 10)
    clock.advance(9)
    assert await store.get("k") == "v"
    clock.advance(2)
    assert await store.get("k") is None


@pytest.mark.asyncio
async def test_memory_store_ttl_floors_at_zero():
    clock = FakeClock()
    store = MemoryOTPStore(clock=clock)
    assert await store.ttl("missing") == 0
    await store.set("k", "v", 30)
    assert await store.ttl("k") == 30
    clock.advance(30)
    assert await store.ttl("k") == 0


@pytest.mark.asyncio
async def test_memory_store_incr_creates_with_ttl():
    clock = FakeClock()
    store = MemoryOTPStore(clock=clock)
    assert await store.incr("k", 60) == 1
    assert await store.ttl("k") == 60
    assert await store.incr("k", 60) == 2


@pytest.mark.asyncio
async def test_memory_store_incr_preserves_existing_ttl():
    """The window is anchored on first use and must NOT slide forward."""
    clock = FakeClock()
    store = MemoryOTPStore(clock=clock)
    await store.set("k", "0", 100)

    clock.advance(50)
    assert await store.incr("k", 100) == 1
    assert await store.ttl("k") == 50  # preserved, not reset to 100

    clock.advance(60)  # 110 > 100 -> expired
    assert await store.get("k") is None


@pytest.mark.asyncio
async def test_memory_store_decr_preserves_ttl_and_sign():
    clock = FakeClock()
    store = MemoryOTPStore(clock=clock)
    await store.set("k", "3", 100)
    clock.advance(40)
    assert await store.decr("k") == 2
    assert await store.ttl("k") == 60


@pytest.mark.asyncio
async def test_memory_store_keys_lists_live_keys_only():
    clock = FakeClock()
    store = MemoryOTPStore(clock=clock)
    await store.set("a", "1", 100)
    await store.set("b", "1", 10)
    clock.advance(20)
    assert store.keys() == ["a"]


# ══ RedisOTPStore semantics (mocked client) ═════════════════════════════


def _redis_store() -> tuple[RedisOTPStore, AsyncMock]:
    client = AsyncMock()
    return RedisOTPStore(client), client


@pytest.mark.asyncio
async def test_redis_incr_anchors_ttl_when_key_has_none():
    """INCR created the key (TTL -1) -> window must be anchored."""
    store, client = _redis_store()
    client.incr = AsyncMock(return_value=1)
    client.ttl = AsyncMock(return_value=-1)
    client.expire = AsyncMock()

    assert await store.incr("k", 3600) == 1
    client.expire.assert_awaited_once_with("k", 3600)


@pytest.mark.asyncio
async def test_redis_incr_does_not_reanchor_existing_ttl():
    """A pre-seeded `attempts` key already has a TTL; re-anchoring would
    restart the failure window on its very first increment."""
    store, client = _redis_store()
    client.incr = AsyncMock(return_value=1)
    client.ttl = AsyncMock(return_value=300)
    client.expire = AsyncMock()

    assert await store.incr("k", 3600) == 1
    client.expire.assert_not_awaited()


@pytest.mark.asyncio
async def test_redis_errors_become_otp_storage_error():
    store, client = _redis_store()
    client.get = AsyncMock(side_effect=RedisConnectionError("down"))
    with pytest.raises(OTPStorageError, match="redis GET failed"):
        await store.get("k")


@pytest.mark.asyncio
async def test_redis_ttl_floors_at_zero():
    store, client = _redis_store()
    client.ttl = AsyncMock(return_value=-2)  # Redis: key missing
    assert await store.ttl("k") == 0
    client.ttl = AsyncMock(return_value=-1)  # Redis: no expiry
    assert await store.ttl("k") == 0
    client.ttl = AsyncMock(return_value=42)
    assert await store.ttl("k") == 42


@pytest.mark.asyncio
async def test_redis_delete_noop_for_empty_keys():
    store, client = _redis_store()
    client.delete = AsyncMock()
    await store.delete()
    client.delete.assert_not_awaited()


# ══ Store selection ════════════════════════════════════════════════════


def test_build_store_uses_memory_under_testing():
    assert isinstance(build_store(make_config(ENV="testing")), MemoryOTPStore)


def test_build_store_uses_redis_outside_testing():
    assert isinstance(build_store(make_config(ENV="development")), RedisOTPStore)


# ══ OTPService.request ═════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_request_success_persists_code_and_state():
    h = Harness()
    result = await h.issue()

    assert result.sent is True
    assert result.reason == "ok"
    assert result.phone == PHONE
    assert result.channel == Channel.WHATSAPP
    assert result.provider == "meta_cloud"
    assert result.expires_in == 300
    assert result.resend_after == 60
    assert result.attempts_allowed == 5
    assert result.request_id

    assert len(h.sender.messages) == 1
    msg = h.sender.messages[0]
    assert msg.to == E164
    assert msg.purpose == "cod_verification"

    code = h.last_code
    assert await h.store.get(code_key("cod_verification", PHONE)) == code
    assert await h.store.get(attempts_key("cod_verification", PHONE)) == "0"
    assert await h.store.ttl(cooldown_key(PHONE)) == 60
    assert await h.store.ttl(ratelimit_key(PHONE)) == 3600


@pytest.mark.asyncio
async def test_request_uses_roman_urdu_template():
    h = Harness()
    result = await h.issue(language=Language.ROMAN_URDU)
    assert result.sent is True
    assert h.sender.messages[-1].body.startswith("Aap ka OpsIQ verification code hai:")


@pytest.mark.asyncio
async def test_request_uses_english_by_default():
    h = Harness()
    await h.issue()
    assert h.sender.messages[-1].body.startswith("Your OpsIQ verification code is:")


@pytest.mark.asyncio
async def test_request_passes_code_as_template_param_when_configured():
    config = make_config(WHATSAPP_OTP_TEMPLATE_NAME="opsiq_otp")
    h = Harness(config=config)
    await h.issue()
    msg = h.sender.messages[-1]
    assert msg.template_name == "opsiq_otp"
    assert msg.template_params == (h.last_code,)


@pytest.mark.asyncio
async def test_request_omits_template_when_not_configured():
    h = Harness()
    await h.issue()
    msg = h.sender.messages[-1]
    assert msg.template_name is None
    assert msg.template_params == ()


@pytest.mark.asyncio
async def test_request_rejects_structurally_invalid_phone():
    """A 9-digit number cannot receive an OTP: no send, no state written."""
    h = Harness()
    result = await h.issue(INVALID_PHONE)

    assert result.sent is False
    assert result.reason == "invalid_phone"
    assert result.provider == "none"
    assert h.sender.messages == []
    assert h.store.keys() == []


@pytest.mark.asyncio
async def test_request_allows_structurally_valid_suspicious_phone():
    """Soft-flag design: suspicious numbers are exactly who OTP must reach."""
    from ecommerce_ops.cod.phone import sanitize_phone

    suspicious = "03000000000"
    assert sanitize_phone(suspicious).is_suspicious is True

    h = Harness()
    result = await h.issue(suspicious)
    assert result.sent is True
    assert result.phone == suspicious


@pytest.mark.asyncio
async def test_request_blocks_within_resend_cooldown():
    h = Harness()
    assert (await h.issue()).sent is True

    blocked = await h.issue()
    assert blocked.sent is False
    assert blocked.reason == "cooldown_active"
    assert 0 < blocked.resend_after <= 60

    h.clock.advance(61)
    assert (await h.issue()).sent is True


@pytest.mark.asyncio
async def test_request_rate_limits_after_hourly_budget():
    h = Harness()
    for i in range(3):
        h.clock.advance(61)
        result = await h.issue()
        assert result.sent is True, f"send {i} should succeed"

    h.clock.advance(61)
    limited = await h.issue()
    assert limited.sent is False
    assert limited.reason == "rate_limited"
    assert limited.resend_after > 0
    assert len(h.sender.messages) == 3


@pytest.mark.asyncio
async def test_rate_limit_refunded_when_provider_fails():
    """An outage must not consume the customer's hourly budget."""
    h = Harness(sender=FakeSender(delivered=False, error="http_503:down"))

    for _ in range(5):
        result = await h.issue()
        assert result.reason == "provider_error"
        h.clock.advance(61)

    # Counter refunded to zero (budget intact) and no code/cooldown state left
    # behind; the ratelimit key itself stays harmlessly until its window ends.
    assert await h.store.get(ratelimit_key(PHONE)) == "0"
    assert await h.store.get(code_key("cod_verification", PHONE)) is None
    assert await h.store.get(cooldown_key(PHONE)) is None

    # Provider recovers -> budget is fully intact.
    h.sender.delivered = True
    result = await h.issue()
    assert result.sent is True
    assert result.reason == "ok"


@pytest.mark.asyncio
async def test_no_code_persisted_when_delivery_fails():
    h = Harness(sender=FakeSender(delivered=False))
    result = await h.issue()
    assert result.sent is False

    assert await h.store.get(code_key("cod_verification", PHONE)) is None
    verification = await h.service.verify(PHONE, "123456")
    assert verification.reason == "not_found"


@pytest.mark.asyncio
async def test_request_reports_storage_error():
    service = OTPService(
        store=BrokenStore(), sender=FakeSender(), config=make_config()
    )
    result = await service.request(PHONE)
    assert result.sent is False
    assert result.reason == "storage_error"


@pytest.mark.asyncio
async def test_request_serializes_to_dict():
    h = Harness()
    payload = (await h.issue()).to_dict()
    assert set(payload) == {
        "sent", "phone", "channel", "provider", "purpose",
        "expires_in", "resend_after", "attempts_allowed", "reason", "request_id",
    }
    assert payload["channel"] == "whatsapp"
    assert isinstance(payload["sent"], bool)


# ══ OTPService.verify ══════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_verify_success_is_single_use():
    h = Harness()
    await h.issue()
    code = h.last_code

    first = await h.service.verify(PHONE, code)
    assert first.verified is True
    assert first.reason == "ok"
    assert first.attempts_remaining == 0

    second = await h.service.verify(PHONE, code)
    assert second.verified is False
    assert second.reason == "not_found"


@pytest.mark.asyncio
async def test_verify_sets_marker_read_by_order_flow():
    h = Harness()
    assert await h.service.is_verified(PHONE) is False

    await h.issue()
    await h.service.verify(PHONE, h.last_code)

    assert await h.service.is_verified(PHONE) is True
    assert await h.service.is_verified(INVALID_PHONE) is False


@pytest.mark.asyncio
async def test_verify_marker_expires():
    h = Harness()
    await h.issue()
    await h.service.verify(PHONE, h.last_code)
    h.clock.advance(901)  # beyond OTP_VERIFIED_TTL_SECONDS
    assert await h.service.is_verified(PHONE) is False


@pytest.mark.asyncio
async def test_wrong_code_decrements_attempts():
    h = Harness()
    await h.issue()
    code = h.last_code

    result = await h.service.verify(PHONE, wrong_code(code))
    assert result.verified is False
    assert result.reason == "invalid_code"
    assert result.attempts_remaining == 4  # 5 - 1


@pytest.mark.asyncio
async def test_exhausted_attempts_destroy_the_code():
    h = Harness()
    await h.issue()
    code = h.last_code

    for i in range(4):
        result = await h.service.verify(PHONE, wrong_code(code))
        assert result.reason == "invalid_code"
        assert result.attempts_remaining == 4 - i

    final = await h.service.verify(PHONE, wrong_code(code))
    assert final.reason == "too_many_attempts"
    assert final.attempts_remaining == 0

    # Code destroyed: even the correct code can no longer verify.
    assert await h.store.get(code_key("cod_verification", PHONE)) is None
    assert (await h.service.verify(PHONE, code)).reason == "not_found"


@pytest.mark.asyncio
async def test_verify_expires_after_ttl():
    h = Harness()
    await h.issue()
    code = h.last_code

    h.clock.advance(301)
    result = await h.service.verify(PHONE, code)
    assert result.verified is False
    assert result.reason == "not_found"


@pytest.mark.asyncio
async def test_verify_without_prior_issue_is_not_found():
    h = Harness()
    result = await h.service.verify(PHONE, "123456")
    assert result.reason == "not_found"
    assert result.verified is False


@pytest.mark.asyncio
async def test_verify_is_purpose_scoped():
    h = Harness()
    await h.issue()
    code = h.last_code

    result = await h.service.verify(PHONE, code, purpose=OTPPurpose.LOGIN)
    assert result.reason == "not_found"

    assert (await h.service.verify(PHONE, code)).verified is True


@pytest.mark.asyncio
async def test_verify_rejects_invalid_phone():
    h = Harness()
    result = await h.service.verify(INVALID_PHONE, "123456")
    assert result.reason == "invalid_phone"
    assert result.verified is False


@pytest.mark.asyncio
async def test_verify_accepts_none_code_without_crashing():
    h = Harness()
    await h.issue()
    result = await h.service.verify(PHONE, None)
    assert result.verified is False
    assert result.reason == "invalid_code"


@pytest.mark.asyncio
async def test_verify_serializes_to_dict():
    h = Harness()
    payload = (await h.service.verify(PHONE, "123456")).to_dict()
    assert set(payload) == {
        "verified", "phone", "purpose", "attempts_remaining", "reason"
    }


@pytest.mark.asyncio
async def test_verify_reports_storage_error():
    service = OTPService(
        store=BrokenStore(), sender=FakeSender(), config=make_config()
    )
    result = await service.verify(PHONE, "123456")
    assert result.verified is False
    assert result.reason == "storage_error"


# ══ invalidate ═════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_invalidate_burns_outstanding_code():
    h = Harness()
    await h.issue()
    code = h.last_code

    await h.service.invalidate(PHONE)

    assert (await h.service.verify(PHONE, code)).reason == "not_found"
    assert await h.store.get(code_key("cod_verification", PHONE)) is None


@pytest.mark.asyncio
async def test_invalidate_clears_verified_marker():
    h = Harness()
    await h.issue()
    await h.service.verify(PHONE, h.last_code)
    assert await h.service.is_verified(PHONE) is True

    await h.service.invalidate(PHONE)
    assert await h.service.is_verified(PHONE) is False


@pytest.mark.asyncio
async def test_invalidate_on_invalid_phone_is_noop():
    h = Harness()
    await h.service.invalidate(INVALID_PHONE)  # must not raise
    assert h.store.keys() == []


@pytest.mark.asyncio
async def test_invalidate_is_purpose_scoped():
    h = Harness()
    await h.issue()
    await h.service.invalidate(PHONE, purpose=OTPPurpose.LOGIN)
    # COD issue is untouched by a login-scoped invalidation.
    assert await h.store.get(code_key("cod_verification", PHONE)) is not None


# ══ Observability ══════════════════════════════════════════════════════


class _FakeMetric:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def labels(self, **kwargs):
        self.calls.append(kwargs)
        return self

    def inc(self) -> None:
        return None


@pytest.mark.asyncio
async def test_request_records_metric_outcome(monkeypatch):
    from ecommerce_ops.cod import otp as otp_module

    metric = _FakeMetric()
    monkeypatch.setattr(otp_module, "METRIC_COD_OTP_REQUESTS", metric)

    h = Harness()
    await h.issue()
    await h.issue(INVALID_PHONE)
    assert [c["outcome"] for c in metric.calls] == ["ok", "invalid_phone"]


@pytest.mark.asyncio
async def test_verify_records_metric_outcome(monkeypatch):
    from ecommerce_ops.cod import otp as otp_module

    metric = _FakeMetric()
    monkeypatch.setattr(otp_module, "METRIC_COD_OTP_VERIFICATIONS", metric)

    h = Harness()
    await h.issue()
    code = h.last_code
    await h.service.verify(PHONE, code)
    # Already consumed, so any submitted code reports not_found.
    await h.service.verify(PHONE, wrong_code(code))

    assert [c["outcome"] for c in metric.calls] == ["ok", "not_found"]


# ══ End-to-end soft-flag flow ══════════════════════════════════════════


@pytest.mark.asyncio
async def test_full_step_up_challenge_round_trip():
    """sanitize -> issue -> verify -> marker, exactly as the order flow sees it."""
    from ecommerce_ops.cod.phone import PhoneAction, recommend_action

    assert recommend_action(PHONE) == PhoneAction.ALLOW
    assert recommend_action("03000000000") == PhoneAction.NEEDS_OTP_VERIFICATION

    h = Harness()
    issued = await h.issue("03000000000")
    assert issued.sent is True

    code = h.last_code
    assert (await h.service.verify("03000000000", wrong_code(code))).reason == (
        "invalid_code"
    )
    assert (await h.service.verify("03000000000", code)).verified is True
    assert await h.service.is_verified("03000000000") is True

    # Once verified, the code cannot be replayed.
    assert (await h.service.verify("03000000000", code)).reason == "not_found"
