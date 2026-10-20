"""COD verification API routes.

Exposes the Phase 1/2 COD module to callers:

* ``POST /cod/phone/validate`` - sanitize + risk-score a checkout phone number.
* ``POST /cod/otp/request``    - issue a step-up OTP (WhatsApp-first).
* ``POST /cod/otp/verify``     - consume an OTP and write the verified marker.
* ``GET  /cod/health``         - provider / config readiness.

Security notes
--------------
* Every route is RBAC-protected by the dedicated ``cod:*`` permissions rather
  than reusing ``cart_recovery:*``: these endpoints address arbitrary phone
  numbers, so message-send rights must not follow from campaign rights.
* Responses never include the issued code - only ``OTPRequestResult.to_dict``
  metadata. The code exists solely in the outbound body and the TTL store.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ecommerce_ops.cod.messaging import Channel, build_provider, whatsapp_configured
from ecommerce_ops.cod.otp import (
    OTPPurpose,
    OTPRequestResult,
    OTPService,
    OTPVerification,
    build_service,
)
from ecommerce_ops.cod.phone import sanitize_phone
from ecommerce_ops.cod.templates import Language
from ecommerce_ops.config import settings
from ecommerce_ops.security.auth import require_permission
from ecommerce_ops.security.models import Permission, User

logger = logging.getLogger("ecommerce_ops.api.cod")

router = APIRouter(prefix="/cod", tags=["cod-verification"])


def get_otp_service() -> OTPService:
    """Lazily wire the default OTP service.

    Lazy so import never opens a Redis pool, and so tests can swap it via
    ``app.dependency_overrides[get_otp_service]``.
    """
    return build_service()


# ── Request models ──────────────────────────────────────────────────────


class PhoneValidateRequest(BaseModel):
    phone: str = Field(..., description="Phone exactly as entered at checkout")
    context: str | None = Field(default=None, description="Where it was captured, e.g. 'checkout'")


class OTPRequestPayload(BaseModel):
    phone: str = Field(..., description="Checkout phone (any supported format)")
    channel: Channel = Field(
        default=Channel.WHATSAPP,
        description="Delivery channel; WhatsApp is the priority path",
    )
    language: Language = Field(
        default=Language.ENGLISH,
        description="Template language: 'en' (English) or 'ur' (Roman Urdu)",
    )
    purpose: OTPPurpose = OTPPurpose.COD_VERIFICATION


class OTPVerifyPayload(BaseModel):
    phone: str = Field(..., description="Checkout phone (any supported format)")
    code: str = Field(..., min_length=1, max_length=16, description="Submitted OTP")
    purpose: OTPPurpose = OTPPurpose.COD_VERIFICATION


# ── Response models ─────────────────────────────────────────────────────


class PhoneValidationResponse(BaseModel):
    raw: str
    normalized: str
    e164: str
    operator: str
    is_valid: bool
    risk_signals: list[str]
    risk_level: str
    action: str


class OTPRequestResponse(BaseModel):
    sent: bool
    phone: str
    channel: str
    provider: str
    purpose: str
    expires_in: int
    resend_after: int
    attempts_allowed: int
    reason: str
    request_id: str


class OTPVerifyResponse(BaseModel):
    verified: bool
    phone: str
    purpose: str
    attempts_remaining: int
    reason: str


class CodHealthResponse(BaseModel):
    whatsapp_configured: bool
    provider: str
    channel: str
    otp_ttl_seconds: int
    otp_max_attempts: int
    otp_rate_limit_per_window: int
    storage_backend: str


# ── Routes ──────────────────────────────────────────────────────────────


@router.post(
    "/phone/validate",
    response_model=PhoneValidationResponse,
    summary="Sanitize and risk-score a checkout phone number",
)
async def validate_phone(
    req: PhoneValidateRequest,
    _: User = Depends(require_permission(Permission.COD_VIEW)),
) -> Dict[str, Any]:
    phone = sanitize_phone(req.phone)
    logger.info(
        "Phone validated (context=%s) valid=%s signals=%s action=%s",
        req.context or "-",
        phone.is_valid,
        list(phone.risk_signals),
        phone.action.value,
    )
    # Unpacking through the response model is deliberate: if PhonePhone.to_dict()
    # ever drifts from the documented contract this fails loudly instead of
    # silently shipping a shape the frontend cannot read.
    return PhoneValidationResponse(**phone.to_dict())


@router.post(
    "/otp/request",
    response_model=OTPRequestResponse,
    summary="Issue a step-up OTP for a checkout phone number",
)
async def request_otp(
    req: OTPRequestPayload,
    otp: OTPService = Depends(get_otp_service),
    _: User = Depends(require_permission(Permission.COD_EXECUTE)),
) -> Dict[str, Any]:
    result: OTPRequestResult = await otp.request(
        req.phone,
        channel=req.channel,
        language=req.language,
        purpose=req.purpose,
    )
    if not result.sent:
        logger.info("OTP not issued reason=%s phone=%s", result.reason, result.phone)
    # OTPRequestResult.to_dict() intentionally excludes the code itself.
    return OTPRequestResponse(**result.to_dict())


@router.post(
    "/otp/verify",
    response_model=OTPVerifyResponse,
    summary="Verify a step-up OTP and mark the phone as verified",
)
async def verify_otp(
    req: OTPVerifyPayload,
    otp: OTPService = Depends(get_otp_service),
    _: User = Depends(require_permission(Permission.COD_EXECUTE)),
) -> Dict[str, Any]:
    result: OTPVerification = await otp.verify(req.phone, req.code, purpose=req.purpose)
    if not result.verified:
        logger.info(
            "OTP rejected reason=%s phone=%s attempts_left=%d",
            result.reason,
            result.phone,
            result.attempts_remaining,
        )
    return OTPVerifyResponse(**result.to_dict())


@router.get(
    "/health",
    response_model=CodHealthResponse,
    summary="COD messaging and OTP configuration readiness",
)
async def cod_health(
    otp: OTPService = Depends(get_otp_service),
    _: User = Depends(require_permission(Permission.COD_VIEW)),
) -> Dict[str, Any]:
    provider = build_provider()
    return CodHealthResponse(
        whatsapp_configured=whatsapp_configured(),
        provider=provider.name,
        channel=provider.channel.value,
        otp_ttl_seconds=settings.OTP_TTL_SECONDS,
        otp_max_attempts=settings.OTP_MAX_ATTEMPTS,
        otp_rate_limit_per_window=settings.OTP_RATE_LIMIT_MAX_REQUESTS,
        storage_backend=otp.storage_backend,
    )
