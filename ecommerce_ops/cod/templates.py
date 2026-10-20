"""Roman Urdu + English message templates for COD verification.

Phase 1 ships the template *data* and pure string rendering. The WhatsApp/SMS
provider abstraction that delivers these lands in Phase 2.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "Language",
    "Template",
    "render",
    "render_otp",
    "render_welcome",
]


class Language(StrEnum):
    """Supported template languages."""

    ENGLISH = "en"
    ROMAN_URDU = "ur"


class Template(StrEnum):
    """Template keys."""

    OTP = "otp"
    WELCOME = "welcome"
    ORDER_CONFIRMED = "order_confirmed"
    RECOVERY = "recovery"


_TEMPLATES: dict[Template, dict[Language, str]] = {
    Template.OTP: {
        Language.ENGLISH: "Your OpsIQ verification code is: {code}",
        Language.ROMAN_URDU: "Aap ka OpsIQ verification code hai: {code}",
    },
    Template.WELCOME: {
        Language.ENGLISH: "Welcome to {store}! Your order is confirmed.",
        Language.ROMAN_URDU: "{store} mein khush aamdeed! Aap ka order confirm ho gaya hai.",
    },
    Template.ORDER_CONFIRMED: {
        Language.ENGLISH: "Order {order_id} confirmed. Track it here: {tracking_url}",
        Language.ROMAN_URDU: "Order {order_id} confirm ho gaya hai. Tracking yahan: {tracking_url}",
    },
    Template.RECOVERY: {
        Language.ENGLISH: (
            "You left something in your cart. Use code {discount_code} to "
            "complete your order: {checkout_url}"
        ),
        Language.ROMAN_URDU: (
            "Aap ka cart mein kuch reh gaya hai. Order mukammal karne ke liye "
            "code {discount_code} istemal karein: {checkout_url}"
        ),
    },
}


def render(template: Template, language: Language = Language.ENGLISH, **params) -> str:
    """Render a template in the requested language with ``params``."""
    return _TEMPLATES[template][language].format(**params)


def render_otp(code: str, language: Language = Language.ENGLISH) -> str:
    """Render an OTP message."""
    return render(Template.OTP, language, code=code)


def render_welcome(store: str, language: Language = Language.ENGLISH) -> str:
    """Render a welcome / order-confirmation message."""
    return render(Template.WELCOME, language, store=store)


def render_recovery(
    discount_code: str, checkout_url: str, language: Language = Language.ENGLISH
) -> str:
    """Render an abandoned-cart recovery message."""
    return render(
        Template.RECOVERY, language, discount_code=discount_code, checkout_url=checkout_url
    )
