from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEMO_ACCOUNT_READONLY_VALID = "DEMO_ACCOUNT_READONLY_VALID"
DEMO_ACCOUNT_READONLY_INVALID = "DEMO_ACCOUNT_READONLY_INVALID"

DEMO_ACCOUNT_READONLY_NOTE = (
    "DemoAccountReadOnlySnapshot validation is read-only. "
    "It is not trading permission and does not generate trading signals."
)


@dataclass(frozen=True)
class DemoAccountReadOnlyValidationResult:
    passed: bool
    status_code: str
    block_reasons: list[str]
    warning_reasons: list[str]
    is_tradable: bool
    can_execute: bool
    note: str


def validate_demo_account_readonly_snapshot(
    payload: dict[str, Any],
) -> DemoAccountReadOnlyValidationResult:
    block_reasons: list[str] = []

    _expect_equal(
        payload,
        "record_type",
        "demo_account_readonly_snapshot",
        "record_type must be demo_account_readonly_snapshot",
        block_reasons,
    )
    _expect_equal(
        payload,
        "account_mode",
        "demo_only",
        "account_mode must be demo_only",
        block_reasons,
    )
    _expect_equal(
        payload,
        "demo_account.is_demo_account",
        True,
        "demo_account.is_demo_account must be true",
        block_reasons,
    )
    _expect_equal(
        payload,
        "demo_account.is_live_account",
        False,
        "demo_account.is_live_account must be false",
        block_reasons,
    )
    _expect_equal(
        payload,
        "demo_account.account_number",
        None,
        "demo_account.account_number must be null",
        block_reasons,
    )
    _expect_equal(
        payload,
        "safety_flags.demo_only",
        True,
        "safety_flags.demo_only must be true",
        block_reasons,
    )
    _expect_equal(
        payload,
        "safety_flags.is_tradable",
        False,
        "safety_flags.is_tradable must be false",
        block_reasons,
    )
    _expect_equal(
        payload,
        "safety_flags.can_execute",
        False,
        "safety_flags.can_execute must be false",
        block_reasons,
    )
    _expect_equal(
        payload,
        "safety_flags.contains_credentials",
        False,
        "safety_flags.contains_credentials must be false",
        block_reasons,
    )
    _expect_equal(
        payload,
        "safety_flags.contains_password",
        False,
        "safety_flags.contains_password must be false",
        block_reasons,
    )
    _expect_equal(
        payload,
        "safety_flags.contains_live_account",
        False,
        "safety_flags.contains_live_account must be false",
        block_reasons,
    )
    _expect_equal(
        payload,
        "bridge_status.read_only",
        True,
        "bridge_status.read_only must be true",
        block_reasons,
    )
    _expect_present(
        payload,
        "generated_at",
        "generated_at must exist",
        block_reasons,
    )
    _expect_number(
        payload,
        "demo_account.equity",
        "demo_account.equity must be a number",
        block_reasons,
    )
    _expect_equal(
        payload,
        "symbol_snapshot.symbol",
        "XAUUSD",
        "symbol_snapshot.symbol must be XAUUSD",
        block_reasons,
    )
    _expect_number(
        payload,
        "symbol_snapshot.bid",
        "symbol_snapshot.bid must be a number",
        block_reasons,
    )
    _expect_number(
        payload,
        "symbol_snapshot.ask",
        "symbol_snapshot.ask must be a number",
        block_reasons,
    )
    _expect_ask_not_below_bid(payload, block_reasons)
    _expect_non_negative_number(
        payload,
        "symbol_snapshot.spread",
        "symbol_snapshot.spread must be greater than or equal to 0",
        block_reasons,
    )
    _expect_safe_note(payload, block_reasons)

    passed = len(block_reasons) == 0

    return DemoAccountReadOnlyValidationResult(
        passed=passed,
        status_code=(
            DEMO_ACCOUNT_READONLY_VALID
            if passed
            else DEMO_ACCOUNT_READONLY_INVALID
        ),
        block_reasons=block_reasons,
        warning_reasons=[],
        is_tradable=False,
        can_execute=False,
        note=DEMO_ACCOUNT_READONLY_NOTE,
    )


def _expect_equal(
    payload: dict[str, Any],
    field_path: str,
    expected_value: Any,
    reason: str,
    block_reasons: list[str],
) -> None:
    if _field_value(payload, field_path) != expected_value:
        block_reasons.append(reason)


def _expect_present(
    payload: dict[str, Any],
    field_path: str,
    reason: str,
    block_reasons: list[str],
) -> None:
    if _field_value(payload, field_path) is _MissingField:
        block_reasons.append(reason)


def _expect_number(
    payload: dict[str, Any],
    field_path: str,
    reason: str,
    block_reasons: list[str],
) -> None:
    value = _field_value(payload, field_path)
    if not _is_number(value):
        block_reasons.append(reason)


def _expect_non_negative_number(
    payload: dict[str, Any],
    field_path: str,
    reason: str,
    block_reasons: list[str],
) -> None:
    value = _field_value(payload, field_path)
    if not _is_number(value) or value < 0:
        block_reasons.append(reason)


def _expect_ask_not_below_bid(
    payload: dict[str, Any],
    block_reasons: list[str],
) -> None:
    bid = _field_value(payload, "symbol_snapshot.bid")
    ask = _field_value(payload, "symbol_snapshot.ask")

    if _is_number(bid) and _is_number(ask) and ask < bid:
        block_reasons.append("symbol_snapshot.ask must be greater than or equal to bid")


def _expect_safe_note(
    payload: dict[str, Any],
    block_reasons: list[str],
) -> None:
    note = _field_value(payload, "note")
    if not isinstance(note, str) or not note.strip():
        block_reasons.append("note must exist")
        return

    normalized_note = note.lower()
    required_phrases = [
        "read-only",
        "not trading advice",
        "not trading permission",
    ]
    for phrase in required_phrases:
        if phrase not in normalized_note:
            block_reasons.append(f"note must mention {phrase}")


def _field_value(payload: dict[str, Any], field_path: str) -> Any:
    current_value: Any = payload
    for part in field_path.split("."):
        if not isinstance(current_value, dict) or part not in current_value:
            return _MissingField
        current_value = current_value[part]
    return current_value


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class _MissingField:
    pass
