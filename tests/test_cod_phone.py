"""Unit tests for the Pakistani phone sanitizer and COD fake-number heuristics.

Phase 1 of the COD module is pure Python with no external dependencies, so
these tests are fast, hermetic, and cover the full behaviour contract:

* format sanitization (spaces, dashes, parentheses, ``+92`` / ``92`` / ``0092``)
* 11-digit local length validation
* PTA operator prefix boundaries (Jazz, Zong, Ufone, Telenor, SCOM, Onic)
* the seven explainable fake-number heuristics
* the soft-flag step-up decision (``NEEDS_OTP_VERIFICATION``, never a hard drop)
"""

import dataclasses

import pytest

from ecommerce_ops.cod.phone import (
    COUNTRY_CODE,
    KNOWN_TEST_NUMBERS,
    LOCAL_LENGTH,
    NATIONAL_LENGTH,
    VALID_PREFIX_RANGES,
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

# ── Realistic, heuristically-clean numbers (asserted ALLOW / low) ──────
CLEAN_JAZZ = "03214567890"
CLEAN_ZONG = "03132435467"
CLEAN_TELENOR = "03461234098"
CLEAN_ALT = "03219876054"


# ══ 1. Format sanitization ═════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "03214567890",
        "0321-4567890",
        "0321 4567890",
        "0321.4567890",
        "0321/4567890",
        "0321,4567890",
        "0321[4567890]",
        "0321{4567890}",
        "(0321) 4567890",
        "0321 4567 890",
        "0321\t4567890",
        "0321\n4567890",
        " 03214567890 ",
        "0 3 2 1 4 5 6 7 8 9 0",
    ],
)
def test_local_format_variants_normalize_identically(raw):
    phone = sanitize_phone(raw)
    assert phone.normalized == CLEAN_JAZZ
    assert phone.is_valid is True


@pytest.mark.parametrize(
    "raw",
    [
        "+92 321 4567890",
        "+923214567890",
        "+92-321-4567890",
        "+92 321 4567 890",
        "0092 321 4567890",
        "00923214567890",
        "92 321 4567890",
        "923214567890",
    ],
)
def test_international_formats_normalize_identically(raw):
    phone = sanitize_phone(raw)
    assert phone.normalized == CLEAN_JAZZ
    assert phone.e164 == f"+{COUNTRY_CODE}3214567890"
    assert phone.is_valid is True


@pytest.mark.parametrize(
    "raw",
    [
        "3214567890",
        "321 4567 890",
        "321-456-7890",
    ],
)
def test_national_format_drops_trunk_prefix(raw):
    phone = sanitize_phone(raw)
    assert phone.normalized == CLEAN_JAZZ
    assert phone.is_valid is True


def test_e164_is_always_country_plus_national():
    phone = sanitize_phone(CLEAN_JAZZ)
    assert phone.e164 == "+923214567890"
    assert phone.e164.startswith(f"+{COUNTRY_CODE}")
    assert len(phone.e164) == len(f"+{COUNTRY_CODE}") + NATIONAL_LENGTH


def test_local_length_constant_is_11():
    assert LOCAL_LENGTH == 11
    assert len(CLEAN_JAZZ) == LOCAL_LENGTH


def test_national_length_constant_is_10():
    assert NATIONAL_LENGTH == 10


def test_country_code_is_pakistan():
    assert COUNTRY_CODE == "92"


def test_plus_sign_in_middle_is_rejected_as_invalid_format():
    phone = sanitize_phone("0321+4567890")
    assert phone.is_valid is False
    assert RiskSignal.INVALID_FORMAT.value in phone.risk_signals


def test_raw_is_preserved_verbatim():
    raw = "+92 321 4567890"
    phone = sanitize_phone(raw)
    assert phone.raw == raw


def test_raw_for_local_input_is_preserved_verbatim():
    phone = sanitize_phone("0321-4567890")
    assert phone.raw == "0321-4567890"


# ══ 2. Prefix boundaries & operator detection ══════════════════════════


PREFIX_OPERATOR_TABLE = [
    ("0300", Operator.JAZZ),
    ("0305", Operator.JAZZ),
    ("0309", Operator.JAZZ),
    ("0310", Operator.ZONG),
    ("0315", Operator.ZONG),
    ("0319", Operator.ZONG),
    ("0320", Operator.JAZZ),  # ex-Warid
    ("0325", Operator.JAZZ),
    ("0329", Operator.JAZZ),
    ("0330", Operator.UFONE),
    ("0335", Operator.UFONE),
    ("0338", Operator.UFONE),
    ("0339", Operator.ONIC),  # PTCL digital brand
    ("0340", Operator.TELENOR),
    ("0345", Operator.TELENOR),
    ("0349", Operator.TELENOR),
    ("0350", Operator.JAZZ),
    ("0354", Operator.JAZZ),
    ("0355", Operator.SCOM),  # AJK / Gilgit-Baltistan
    ("0356", Operator.JAZZ),
    ("0359", Operator.JAZZ),
    ("0360", Operator.UFONE),
    ("0365", Operator.UFONE),
    ("0369", Operator.UFONE),
    ("0370", Operator.ZONG),
    ("0375", Operator.ZONG),
    ("0379", Operator.ZONG),
]


@pytest.mark.parametrize(("prefix", "expected"), PREFIX_OPERATOR_TABLE)
def test_operator_detected_from_prefix(prefix, expected):
    phone = sanitize_phone(f"{prefix}1234567")
    assert phone.operator == expected
    assert phone.is_valid is True


@pytest.mark.parametrize(
    "invalid",
    [
        "03801234567",  # 380 — unallocated
        "03901234567",  # 390 — unallocated
        "03891234567",
        "03991234567",
        "02101234567",  # 21 — Karachi landline, not mobile
        "04212345678",  # 42 — Lahore landline
        "05112345678",  # 51 — Islamabad landline
    ],
)
def test_invalid_prefix_rejected(invalid):
    phone = sanitize_phone(invalid)
    assert phone.is_valid is False
    assert phone.operator == Operator.UNKNOWN
    assert RiskSignal.INVALID_PREFIX.value in phone.risk_signals


def test_prefix_range_table_is_contiguous_and_sane():
    assert VALID_PREFIX_RANGES[0] == (300, 309)
    assert VALID_PREFIX_RANGES[-1] == (370, 379)
    assert len(VALID_PREFIX_RANGES) == 8
    for low, high in VALID_PREFIX_RANGES:
        assert low <= high
        assert 300 <= low <= 379


def test_operator_of_convenience_wrapper_accepts_string():
    assert operator_of(CLEAN_JAZZ) == Operator.JAZZ
    assert operator_of("03132435467") == Operator.ZONG


def test_operator_mnp_is_soft_signal_documented():
    """MNP means the prefix is the original allocation, not the live network.

    The sanitizer must still resolve a concrete operator (never UNKNOWN) for a
    structurally valid number, because downstream OTP routing treats it as a
    hint only.
    """
    phone = sanitize_phone(CLEAN_JAZZ)
    assert phone.is_valid is True
    assert phone.operator == Operator.JAZZ


# ══ 3. The seven fake-number heuristics ════════════════════════════════


def test_all_same_digit():
    phone = sanitize_phone("03000000000")
    assert RiskSignal.ALL_SAME_DIGIT.value in phone.risk_signals
    assert phone.is_valid is True


def test_all_same_digit_alternate():
    phone = sanitize_phone("03111111111")
    assert RiskSignal.ALL_SAME_DIGIT.value in phone.risk_signals


def test_sequential_ascending_example_from_brief():
    """The brief's canonical fake: 03123456789."""
    phone = sanitize_phone("03123456789")
    assert RiskSignal.SEQUENTIAL_ASCENDING.value in phone.risk_signals
    assert phone.is_valid is True
    assert phone.operator == Operator.ZONG


def test_sequential_ascending_partial_run_is_not_flagged():
    phone = sanitize_phone("03001234568")
    assert RiskSignal.SEQUENTIAL_ASCENDING.value not in phone.risk_signals


def test_sequential_descending_with_valid_prefix():
    phone = sanitize_phone("03498765432")
    assert RiskSignal.SEQUENTIAL_DESCENDING.value in phone.risk_signals
    assert phone.is_valid is True
    assert phone.operator == Operator.TELENOR


def test_sequential_descending_subscriber_only():
    phone = sanitize_phone("03009876543")
    assert RiskSignal.SEQUENTIAL_DESCENDING.value in phone.risk_signals


def test_repeating_block_example_from_brief():
    """The brief's canonical fake: 03001230012 ('30012' x2)."""
    phone = sanitize_phone("03001230012")
    assert RiskSignal.REPEATING_BLOCK.value in phone.risk_signals
    assert phone.is_valid is True


def test_repeating_block_detected_on_national_number():
    """A 7-digit subscriber has prime length, so a repeating block can only be
    detected on the 10-digit national form ('3434343434' = '34' x5)."""
    phone = sanitize_phone("03434343434")
    assert RiskSignal.REPEATING_BLOCK.value in phone.risk_signals
    assert phone.is_valid is True


def test_repeating_block_not_flagged_for_random_number():
    phone = sanitize_phone(CLEAN_JAZZ)
    assert RiskSignal.REPEATING_BLOCK.value not in phone.risk_signals


def test_low_entropy_threshold_is_four_unique_digits():
    phone = sanitize_phone("03001111111")
    assert RiskSignal.LOW_ENTROPY.value in phone.risk_signals
    assert len(set(phone.normalized)) < 4


def test_low_entropy_not_flagged_when_enough_unique_digits():
    phone = sanitize_phone(CLEAN_JAZZ)
    assert RiskSignal.LOW_ENTROPY.value not in phone.risk_signals
    assert len(set(phone.normalized)) >= 4


def test_incomplete_nine_digit_local_number():
    """The brief's third case: incomplete 9-digit numbers."""
    phone = sanitize_phone("031234567")
    assert RiskSignal.INCOMPLETE.value in phone.risk_signals
    assert phone.is_valid is False


def test_incomplete_flagged_for_overlong_numbers():
    phone = sanitize_phone("031234567890")
    assert RiskSignal.INCOMPLETE.value in phone.risk_signals
    assert phone.is_valid is False


def test_incomplete_for_ten_digit_local_with_trunk():
    phone = sanitize_phone("0312345678")
    assert RiskSignal.INCOMPLETE.value in phone.risk_signals
    assert phone.is_valid is False


def test_invalid_prefix_is_a_signal():
    phone = sanitize_phone("03801234567")
    assert RiskSignal.INVALID_PREFIX.value in phone.risk_signals


def test_known_test_number_signal_fires():
    phone = sanitize_phone("1234567890")
    assert RiskSignal.KNOWN_TEST_NUMBER.value in phone.risk_signals


def test_known_test_number_constant_is_frozen():
    assert isinstance(KNOWN_TEST_NUMBERS, frozenset)
    assert "00000000000" in KNOWN_TEST_NUMBERS
    assert "1234567890" in KNOWN_TEST_NUMBERS


@pytest.mark.parametrize(
    "raw",
    [
        "abc",
        "",
        "   ",
        None,
        "0321-12a4-567",
        "0321!4567890",
        "+92 321 456789a",
        "0321@4567890",
    ],
)
def test_invalid_format_rejected(raw):
    phone = sanitize_phone(raw)
    assert phone.is_valid is False
    assert RiskSignal.INVALID_FORMAT.value in phone.risk_signals


def test_empty_string_and_none_produce_identical_shape():
    from_none = sanitize_phone(None)
    from_empty = sanitize_phone("")
    assert from_none.normalized == from_empty.normalized == ""
    assert from_none.e164 == from_empty.e164 == ""
    assert from_none.is_valid is False and from_empty.is_valid is False


def test_whitespace_only_input():
    phone = sanitize_phone("   \t  ")
    assert phone.is_valid is False
    assert RiskSignal.INVALID_FORMAT.value in phone.risk_signals


def test_signals_are_deduplicated():
    phone = sanitize_phone("03000000000")
    assert len(phone.risk_signals) == len(set(phone.risk_signals))


def test_signals_are_stable_tuple_not_list():
    phone = sanitize_phone("03000000000")
    assert isinstance(phone.risk_signals, tuple)


# ══ 4. Risk level & step-up action ═════════════════════════════════════


def test_clean_number_is_low_risk_and_allowed():
    phone = sanitize_phone(CLEAN_JAZZ)
    assert phone.risk_signals == ()
    assert phone.is_suspicious is False
    assert phone.risk_level == "low"
    assert phone.action == PhoneAction.ALLOW


@pytest.mark.parametrize("raw", [CLEAN_JAZZ, CLEAN_ZONG, CLEAN_TELENOR, CLEAN_ALT])
def test_all_clean_numbers_allow(raw):
    phone = sanitize_phone(raw)
    assert phone.action == PhoneAction.ALLOW
    assert phone.risk_level == "low"


def test_single_signal_is_medium_and_needs_otp():
    """Soft-flag, never a hard drop: valid but suspicious -> step-up OTP."""
    phone = sanitize_phone("03123456789")
    assert phone.is_valid is True
    assert len(phone.risk_signals) == 1
    assert phone.risk_level == "medium"
    assert phone.action == PhoneAction.NEEDS_OTP_VERIFICATION


def test_two_signals_are_high_risk():
    phone = sanitize_phone("03000000000")
    assert len(phone.risk_signals) >= 2
    assert phone.risk_level == "high"
    assert phone.action == PhoneAction.NEEDS_OTP_VERIFICATION


def test_structurally_invalid_is_review_not_drop():
    """Incomplete / bad-prefix numbers are REVIEW, never silently dropped."""
    phone = sanitize_phone("031234567")
    assert phone.is_valid is False
    assert phone.action == PhoneAction.REVIEW
    assert phone.risk_level == "high"


def test_phone_action_enum_values():
    assert PhoneAction.ALLOW.value == "allow"
    assert PhoneAction.NEEDS_OTP_VERIFICATION.value == "needs_otp_verification"
    assert PhoneAction.REVIEW.value == "review"


def test_never_hard_drops_any_number():
    """No input may produce a terminal 'reject'/'block' action."""
    for raw in ["03000000000", "031234567", "abc", "03801234567", CLEAN_JAZZ]:
        assert sanitize_phone(raw).action in {
            PhoneAction.ALLOW,
            PhoneAction.NEEDS_OTP_VERIFICATION,
            PhoneAction.REVIEW,
        }


def test_brief_fake_numbers_all_trigger_step_up_or_review():
    """The exact numbers from the brief must never be ALLOW."""
    for raw in ["03000000000", "03123456789", "031234567"]:
        phone = sanitize_phone(raw)
        assert phone.action != PhoneAction.ALLOW, raw


# ══ 5. Convenience wrappers ════════════════════════════════════════════


def test_is_suspicious_wrapper_on_string():
    assert is_suspicious("03000000000") is True
    assert is_suspicious(CLEAN_JAZZ) is False


def test_risk_level_wrapper_on_string():
    assert risk_level(CLEAN_JAZZ) == "low"
    assert risk_level("03123456789") == "medium"
    assert risk_level("031234567") == "high"


def test_recommend_action_wrapper_on_string():
    assert recommend_action(CLEAN_JAZZ) == PhoneAction.ALLOW
    assert recommend_action("03123456789") == PhoneAction.NEEDS_OTP_VERIFICATION
    assert recommend_action("031234567") == PhoneAction.REVIEW


def test_wrappers_accept_pre_sanitized_object():
    phone = sanitize_phone(CLEAN_JAZZ)
    assert is_suspicious(phone) is phone.is_suspicious
    assert recommend_action(phone) is phone.action
    assert operator_of(phone) is phone.operator


def test_wrappers_treat_none_as_invalid():
    assert is_suspicious(None) is True
    assert recommend_action(None) == PhoneAction.REVIEW
    assert operator_of(None) == Operator.UNKNOWN


# ══ 6. Data model guarantees ═══════════════════════════════════════════


def test_to_dict_has_stable_api_shape():
    d = sanitize_phone(CLEAN_JAZZ).to_dict()
    assert set(d) == {
        "raw",
        "normalized",
        "e164",
        "operator",
        "is_valid",
        "risk_signals",
        "risk_level",
        "action",
    }
    assert d["operator"] == "jazz"
    assert d["action"] == "allow"
    assert isinstance(d["risk_signals"], list)


def test_to_dict_serializes_enums_to_strings():
    d = sanitize_phone("03000000000").to_dict()
    assert isinstance(d["operator"], str)
    assert isinstance(d["action"], str)
    assert all(isinstance(s, str) for s in d["risk_signals"])


def test_frozen_dataclass_is_immutable():
    phone = sanitize_phone(CLEAN_JAZZ)
    with pytest.raises(dataclasses.FrozenInstanceError):
        phone.normalized = "03000000000"


def test_dataclass_type_annotations():
    phone = sanitize_phone(CLEAN_JAZZ)
    assert isinstance(phone, PakistanPhone)
    assert isinstance(phone.is_valid, bool)
    assert isinstance(phone.operator, Operator)


def test_equality_includes_raw_input():
    """Frozen dataclass equality compares every field, including ``raw``.

    Two different raw spellings of the same number are therefore distinct
    objects even though they sanitize identically.
    """
    assert sanitize_phone(CLEAN_JAZZ) == sanitize_phone(CLEAN_JAZZ)
    assert sanitize_phone("03214567890") != sanitize_phone("0321-4567890")


def test_distinct_numbers_are_not_equal():
    assert sanitize_phone(CLEAN_JAZZ) != sanitize_phone(CLEAN_ZONG)


# ══ 7. RiskSignal enum contract ════════════════════════════════════════


def test_risk_signal_enum_covers_all_seven_heuristics_plus_format():
    values = {s.value for s in RiskSignal}
    assert {
        "all_same_digit",
        "sequential_ascending",
        "sequential_descending",
        "repeating_block",
        "low_entropy",
        "incomplete",
        "invalid_prefix",
        "known_test_number",
    } <= values
    assert "invalid_format" in values


def test_operator_enum_has_all_pakistani_operators():
    values = {o.value for o in Operator}
    assert {"jazz", "zong", "ufone", "telenor", "scom", "onic", "unknown"} <= values


# ══ 8. Idempotency / composition ═══════════════════════════════════════


def test_sanitize_is_idempotent_on_normalized_output():
    once = sanitize_phone("0321 4567890")
    twice = sanitize_phone(once.normalized)
    assert once.normalized == twice.normalized
    assert once.e164 == twice.e164
    assert once.operator == twice.operator


def test_sanitizing_e164_output_is_stable():
    phone = sanitize_phone(CLEAN_JAZZ)
    again = sanitize_phone(phone.e164)
    assert again.normalized == phone.normalized
    assert again.is_valid is True


def test_mixed_punctuation_and_country_code_compose():
    phone = sanitize_phone("+92 (321) 4567.890")
    assert phone.normalized == CLEAN_JAZZ
    assert phone.is_valid is True


def test_many_numbers_in_sequence_do_not_leak_state():
    """Sanitizer is stateless; a suspicious number must not taint the next."""
    bad = sanitize_phone("03000000000")
    good = sanitize_phone(CLEAN_JAZZ)
    assert bad.is_suspicious is True
    assert good.risk_signals == ()
    assert good.action == PhoneAction.ALLOW
