"""COD (Cash-on-Delivery) operations module.

* **Phase 1** (`phone`): Pakistani mobile number sanitization, operator
  detection, and explainable fake-number heuristics - pure Python, zero
  external dependencies.
* **Phase 2** (`messaging`, `otp`, `templates`): WhatsApp-first delivery via
  the Meta Cloud API with a LogProvider credential fallback, plus a Redis/TTL
  backed one-time-passcode lifecycle for the ``NEEDS_OTP_VERIFICATION``
  step-up challenge.
"""

from ecommerce_ops.cod.messaging import (
    Channel,
    DeliveryResult,
    LogProvider,
    MessagingProvider,
    MetaCloudWhatsAppProvider,
    OutboundMessage,
    build_provider,
    deliver,
    whatsapp_configured,
)
from ecommerce_ops.cod.otp import (
    MemoryOTPStore,
    OTPPurpose,
    OTPRequestResult,
    OTPService,
    OTPStorageError,
    OTPStore,
    OTPVerification,
    RedisOTPStore,
    build_service,
    build_store,
    generate_code,
)
from ecommerce_ops.cod.phone import (
    Operator,
    PakistanPhone,
    PhoneAction,
    RiskSignal,
    is_suspicious,
    operator_of,
    recommend_action,
    risk_level,
    sanitize_phone,
)
from ecommerce_ops.cod.templates import (
    Language,
    Template,
    render,
    render_otp,
    render_recovery,
    render_welcome,
)

__all__ = [
    "Channel",
    "DeliveryResult",
    "Language",
    "LogProvider",
    "MemoryOTPStore",
    "MessagingProvider",
    "MetaCloudWhatsAppProvider",
    "OTPPurpose",
    "OTPRequestResult",
    "OTPService",
    "OTPStorageError",
    "OTPStore",
    "OTPVerification",
    "Operator",
    "OutboundMessage",
    "PakistanPhone",
    "PhoneAction",
    "RedisOTPStore",
    "RiskSignal",
    "Template",
    "build_provider",
    "build_service",
    "build_store",
    "deliver",
    "generate_code",
    "is_suspicious",
    "operator_of",
    "recommend_action",
    "render",
    "render_otp",
    "render_recovery",
    "render_welcome",
    "risk_level",
    "sanitize_phone",
    "whatsapp_configured",
]
