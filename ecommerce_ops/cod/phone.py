"""Pakistani mobile number sanitization and COD fraud heuristics.

Phase 1 of the COD (Cash-on-Delivery) module: **pure Python logic with zero
external API or database dependencies**.

Responsibilities
----------------
* Normalize Pakistani mobile numbers to canonical local (``03XXXXXXXXX``) and
  E.164 (``+923XXXXXXXXX``) forms.
* Validate format, length, and operator prefix (PTA allocation, 2026).
* Flag suspicious / fake numbers with explainable heuristics.
* Recommend a **soft-flag step-up action** (``NEEDS_OTP_VERIFICATION``) instead
  of a hard drop.

Locked design decisions
-----------------------
* Scope: pure Python, no external calls, no DB migrations.
* Risk handling: soft-flag with a step-up challenge, never a hard drop.
* Mobile Number Portability (MNP) means the prefix reflects the *original*
  allocation, not the current network — it is a soft signal only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "Operator",
    "PakistanPhone",
    "PhoneAction",
    "RiskSignal",
    "is_suspicious",
    "operator_of",
    "recommend_action",
    "risk_level",
    "sanitize_phone",
]

# ── Constants ──────────────────────────────────────────────────

#: Canonical local format length (``03XXXXXXXXX``).
LOCAL_LENGTH = 11
#: National significant number length (``3XXXXXXXXX``).
NATIONAL_LENGTH = 10
#: Pakistan country calling code.
COUNTRY_CODE = "92"
#: Local trunk prefix.
TRUNK_PREFIX = "0"
#: Mobile access code (all Pakistani mobiles start with 3).
MOBILE_ACCESS_CODE = "3"

#: Valid Pakistani mobile prefix ranges (3-digit national prefix).
#: PTA allocation (2026):
#: * Jazz      - 300-309 (Mobilink), 320-329 (ex-Warid), 350-359
#: * Zong      - 310-319, 370-379
#: * Ufone     - 330-339, 360-369
#: * Telenor   - 340-349
#: * SCOM      - 355 (AJK / Gilgit-Baltistan)
#: * Onic      - 339 (PTCL digital brand)
VALID_PREFIX_RANGES: tuple[tuple[int, int], ...] = (
    (300, 309),
    (310, 319),
    (320, 329),
    (330, 339),
    (340, 349),
    (350, 359),
    (360, 369),
    (370, 379),
)

#: Placeholder / test numbers that are never real customers.
KNOWN_TEST_NUMBERS: frozenset[str] = frozenset(
    {
        "00000000000",
        "0000000000",
        "11111111111",
        "12345678901",
        "1234567890",
        "09876543210",
        "99999999999",
    }
)

#: Characters stripped during sanitization.
_FORMATTING_RE = re.compile(r"[\s\-\.\(\)\[\]\{\}/,]")
#: Accepted country-code prefixes (longest first).
_COUNTRY_CODE_PREFIXES = ("0092", "92")
#: Minimum distinct digits for a number to not be flagged as low-entropy.
_MIN_UNIQUE_DIGITS = 4


# ── Enums ──────────────────────────────────────────────────────


class Operator(StrEnum):
    """Pakistani mobile operator inferred from the prefix (soft signal: MNP)."""

    JAZZ = "jazz"
    ZONG = "zong"
    UFONE = "ufone"
    TELENOR = "telenor"
    SCOM = "scom"
    ONIC = "onic"
    UNKNOWN = "unknown"


class PhoneAction(StrEnum):
    """Step-up challenge decision for a COD order (soft-flag, never hard drop)."""

    ALLOW = "allow"
    NEEDS_OTP_VERIFICATION = "needs_otp_verification"
    REVIEW = "review"


class RiskSignal(StrEnum):
    """Explainable fake-number heuristics."""

    ALL_SAME_DIGIT = "all_same_digit"
    SEQUENTIAL_ASCENDING = "sequential_ascending"
    SEQUENTIAL_DESCENDING = "sequential_descending"
    REPEATING_BLOCK = "repeating_block"
    LOW_ENTROPY = "low_entropy"
    INCOMPLETE = "incomplete"
    INVALID_PREFIX = "invalid_prefix"
    KNOWN_TEST_NUMBER = "known_test_number"
    INVALID_FORMAT = "invalid_format"


# ── Data model ─────────────────────────────────────────────────


@dataclass(frozen=True)
class PakistanPhone:
    """Sanitized Pakistani mobile number with validation and risk signals."""

    raw: str
    normalized: str = ""
    e164: str = ""
    operator: Operator = Operator.UNKNOWN
    is_valid: bool = False
    risk_signals: tuple[str, ...] = ()

    @property
    def is_suspicious(self) -> bool:
        """True when at least one heuristic fired."""
        return bool(self.risk_signals)

    @property
    def action(self) -> PhoneAction:
        """Recommended step-up action.

        * ``ALLOW``                  — structurally valid, no heuristics fired.
        * ``NEEDS_OTP_VERIFICATION`` — structurally valid but suspicious.
        * ``REVIEW``                 — structurally invalid, cannot verify.
        """
        if not self.is_valid:
            return PhoneAction.REVIEW
        if self.risk_signals:
            return PhoneAction.NEEDS_OTP_VERIFICATION
        return PhoneAction.ALLOW

    @property
    def risk_level(self) -> str:
        """Coarse risk band: ``low`` / ``medium`` / ``high``."""
        if not self.is_valid:
            return "high"
        if len(self.risk_signals) >= 2:
            return "high"
        if self.risk_signals:
            return "medium"
        return "low"

    def to_dict(self) -> dict:
        """JSON-serializable representation (stable shape for APIs)."""
        return {
            "raw": self.raw,
            "normalized": self.normalized,
            "e164": self.e164,
            "operator": self.operator.value,
            "is_valid": self.is_valid,
            "risk_signals": list(self.risk_signals),
            "risk_level": self.risk_level,
            "action": self.action.value,
        }


# ── Public API ─────────────────────────────────────────────────


def sanitize_phone(raw: str | None) -> PakistanPhone:
    """Sanitize and validate a Pakistani mobile number.

    Accepts local (``0300 1234567``), national (``3001234567``) and
    international (``+92 300 1234567`` / ``0092 300 1234567``) forms.
    """
    raw_input = "" if raw is None else str(raw)
    signals: list[str] = []

    # 1. Strip formatting and a leading '+' sign.
    cleaned = _FORMATTING_RE.sub("", raw_input).lstrip("+")

    # 2. Strip an international country code if present.
    for cc in _COUNTRY_CODE_PREFIXES:
        if cleaned.startswith(cc) and len(cleaned) > NATIONAL_LENGTH:
            cleaned = cleaned[len(cc) :]
            break

    # 3. Strip the local trunk prefix (0) -> national significant number.
    if cleaned.startswith(TRUNK_PREFIX):
        cleaned = cleaned[1:]

    # 4. Must be digits only.
    if not cleaned.isdigit():
        signals.append(RiskSignal.INVALID_FORMAT.value)
        return _build(raw_input, "", "", Operator.UNKNOWN, False, signals)

    # 5. Length must be a full national significant number.
    if len(cleaned) != NATIONAL_LENGTH:
        signals.append(RiskSignal.INCOMPLETE.value)
        normalized = f"{TRUNK_PREFIX}{cleaned}" if cleaned else ""
        return _build(raw_input, normalized, "", Operator.UNKNOWN, False, signals)

    normalized = f"{TRUNK_PREFIX}{cleaned}"
    e164 = f"+{COUNTRY_CODE}{cleaned}"

    # 6. Known placeholder / test numbers (checked before the prefix so a
    #    test number that also has a bad prefix reports both signals).
    if normalized in KNOWN_TEST_NUMBERS or cleaned in KNOWN_TEST_NUMBERS:
        signals.append(RiskSignal.KNOWN_TEST_NUMBER.value)

    # 7. Prefix must be a valid Pakistani mobile prefix.
    prefix3 = int(cleaned[:3])
    if not _prefix_valid(prefix3):
        signals.append(RiskSignal.INVALID_PREFIX.value)
        return _build(raw_input, normalized, e164, Operator.UNKNOWN, False, signals)

    # 8. Fake-number heuristics.
    signals.extend(_heuristic_signals(cleaned))

    return _build(raw_input, normalized, e164, _operator(prefix3), True, signals)


def is_suspicious(phone: PakistanPhone | str | None) -> bool:
    """Convenience wrapper: does this number carry any risk signal?"""
    return _coerce(phone).is_suspicious


def risk_level(phone: PakistanPhone | str | None) -> str:
    """Convenience wrapper: coarse risk band for a number."""
    return _coerce(phone).risk_level


def recommend_action(phone: PakistanPhone | str | None) -> PhoneAction:
    """Convenience wrapper: recommended step-up action for a number."""
    return _coerce(phone).action


def operator_of(phone: PakistanPhone | str | None) -> Operator:
    """Convenience wrapper: operator inferred from the prefix."""
    return _coerce(phone).operator


# ── Internal helpers ───────────────────────────────────────────


def _coerce(phone: PakistanPhone | str | None) -> PakistanPhone:
    return phone if isinstance(phone, PakistanPhone) else sanitize_phone(phone)


def _build(
    raw: str,
    normalized: str,
    e164: str,
    operator: Operator,
    is_valid: bool,
    signals: list[str],
) -> PakistanPhone:
    """Assemble a ``PakistanPhone`` with order-preserving, de-duplicated signals."""
    seen: set[str] = set()
    unique: list[str] = []
    for signal in signals:
        if signal not in seen:
            seen.add(signal)
            unique.append(signal)
    return PakistanPhone(
        raw=raw,
        normalized=normalized,
        e164=e164,
        operator=operator,
        is_valid=is_valid,
        risk_signals=tuple(unique),
    )


def _prefix_valid(prefix3: int) -> bool:
    return any(low <= prefix3 <= high for low, high in VALID_PREFIX_RANGES)


def _operator(prefix3: int) -> Operator:
    """Map a 3-digit national prefix to an operator (MNP is a soft signal)."""
    if 300 <= prefix3 <= 309:
        return Operator.JAZZ
    if 310 <= prefix3 <= 319:
        return Operator.ZONG
    if 320 <= prefix3 <= 329:
        return Operator.JAZZ
    if 330 <= prefix3 <= 339:
        return Operator.ONIC if prefix3 == 339 else Operator.UFONE
    if 340 <= prefix3 <= 349:
        return Operator.TELENOR
    if 350 <= prefix3 <= 359:
        return Operator.SCOM if prefix3 == 355 else Operator.JAZZ
    if 360 <= prefix3 <= 369:
        return Operator.UFONE
    if 370 <= prefix3 <= 379:
        return Operator.ZONG
    return Operator.UNKNOWN


def _heuristic_signals(national: str) -> list[str]:
    """Run the seven fake-number heuristics over a valid-length national number."""
    signals: list[str] = []
    subscriber = national[3:]

    if len(set(subscriber)) == 1:
        signals.append(RiskSignal.ALL_SAME_DIGIT.value)

    if _is_sequential(subscriber, ascending=True):
        signals.append(RiskSignal.SEQUENTIAL_ASCENDING.value)

    if _is_sequential(subscriber, ascending=False):
        signals.append(RiskSignal.SEQUENTIAL_DESCENDING.value)

    if _has_repeating_block(national) or _has_repeating_block(subscriber):
        signals.append(RiskSignal.REPEATING_BLOCK.value)

    if len(set(national)) < _MIN_UNIQUE_DIGITS:
        signals.append(RiskSignal.LOW_ENTROPY.value)

    return signals


def _is_sequential(digits: str, ascending: bool) -> bool:
    """True when every digit steps by exactly ±1 from the previous one."""
    if len(digits) < 2:
        return False
    step = 1 if ascending else -1
    return all(int(digits[i]) == int(digits[i - 1]) + step for i in range(1, len(digits)))


def _has_repeating_block(value: str) -> bool:
    """True when ``value`` is a block repeated two or more times (e.g. 3001230012)."""
    length = len(value)
    for block_len in range(2, length // 2 + 1):
        if length % block_len != 0:
            continue
        block = value[:block_len]
        if block * (length // block_len) == value:
            return True
    return False
