from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEMO_MARKET_SYMBOL_READONLY_VALID = "DEMO_MARKET_SYMBOL_READONLY_VALID"
DEMO_MARKET_SYMBOL_READONLY_INVALID = "DEMO_MARKET_SYMBOL_READONLY_INVALID"

DEMO_MARKET_SYMBOL_READONLY_NOTE = (
    "DemoMarketSymbolReadOnly validation is read-only. "
    "It is not trading permission and does not generate trading signals."
)


@dataclass(frozen=True)
class DemoMarketSymbolReadOnlyValidationResult:
    passed: bool
    status_code: str
    block_reasons: list[str]
    warning_reasons: list[str]
    is_tradable: bool
    can_execute: bool
    note: str


def validate_demo_market_symbol_readonly(
    payload: dict[str, Any],
) -> DemoMarketSymbolReadOnlyValidationResult:
    block_reasons: list[str] = []

    _expect_equal(
        payload,
        "record_type",
        "demo_market_symbol_readonly",
        "record_type must be demo_market_symbol_readonly",
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
        "symbol",
        "XAUUSD",
        "symbol must be XAUUSD",
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
        "safety_flags.is_trade_signal",
        False,
        "safety_flags.is_trade_signal must be false",
        block_reasons,
    )
    _expect_equal(
        payload,
        "safety_flags.is_trade_plan",
        False,
        "safety_flags.is_trade_plan must be false",
        block_reasons,
    )
    _expect_equal(
        payload,
        "safety_flags.is_execution_permission",
        False,
        "safety_flags.is_execution_permission must be false",
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

    _validate_quote(payload, block_reasons)
    _validate_symbol_spec(payload, block_reasons)
    _validate_market_session(payload, block_reasons)
    _expect_safe_note(payload, block_reasons)

    passed = len(block_reasons) == 0

    return DemoMarketSymbolReadOnlyValidationResult(
        passed=passed,
        status_code=(
            DEMO_MARKET_SYMBOL_READONLY_VALID
            if passed
            else DEMO_MARKET_SYMBOL_READONLY_INVALID
        ),
        block_reasons=block_reasons,
        warning_reasons=[],
        is_tradable=False,
        can_execute=False,
        note=DEMO_MARKET_SYMBOL_READONLY_NOTE,
    )


def _validate_quote(
    payload: dict[str, Any],
    block_reasons: list[str],
) -> None:
    _expect_number(
        payload,
        "quote.bid",
        "quote.bid must be a number",
        block_reasons,
    )
    _expect_number(
        payload,
        "quote.ask",
        "quote.ask must be a number",
        block_reasons,
    )
    _expect_ask_not_below_bid(payload, block_reasons)
    _expect_non_negative_number(
        payload,
        "quote.spread",
        "quote.spread must be greater than or equal to 0",
        block_reasons,
    )
    _expect_non_negative_number(
        payload,
        "quote.spread_points",
        "quote.spread_points must be greater than or equal to 0",
        block_reasons,
    )
    _expect_present(
        payload,
        "quote.last_tick_time",
        "quote.last_tick_time must exist",
        block_reasons,
    )
    _expect_non_negative_number(
        payload,
        "quote.last_update_age_seconds",
        "quote.last_update_age_seconds must be greater than or equal to 0",
        block_reasons,
    )


def _validate_symbol_spec(
    payload: dict[str, Any],
    block_reasons: list[str],
) -> None:
    _expect_non_negative_integer(
        payload,
        "symbol_spec.digits",
        "symbol_spec.digits must be a non-negative integer",
        block_reasons,
    )
    _expect_positive_number(
        payload,
        "symbol_spec.point",
        "symbol_spec.point must be greater than 0",
        block_reasons,
    )
    _expect_positive_number(
        payload,
        "symbol_spec.tick_size",
        "symbol_spec.tick_size must be greater than 0",
        block_reasons,
    )
    _expect_positive_number(
        payload,
        "symbol_spec.tick_value",
        "symbol_spec.tick_value must be greater than 0",
        block_reasons,
    )
    _expect_positive_number(
        payload,
        "symbol_spec.contract_size",
        "symbol_spec.contract_size must be greater than 0",
        block_reasons,
    )
    _expect_positive_number(
        payload,
        "symbol_spec.min_lot",
        "symbol_spec.min_lot must be greater than 0",
        block_reasons,
    )
    _expect_max_lot_not_below_min_lot(payload, block_reasons)
    _expect_positive_number(
        payload,
        "symbol_spec.lot_step",
        "symbol_spec.lot_step must be greater than 0",
        block_reasons,
    )
    _expect_non_negative_number(
        payload,
        "symbol_spec.stop_level_points",
        "symbol_spec.stop_level_points must be greater than or equal to 0",
        block_reasons,
    )
    _expect_non_negative_number(
        payload,
        "symbol_spec.freeze_level_points",
        "symbol_spec.freeze_level_points must be greater than or equal to 0",
        block_reasons,
    )


def _validate_market_session(
    payload: dict[str, Any],
    block_reasons: list[str],
) -> None:
    _expect_bool(
        payload,
        "market_session.market_open",
        "market_session.market_open must be boolean",
        block_reasons,
    )
    _expect_bool(
        payload,
        "market_session.trade_allowed_by_broker",
        "market_session.trade_allowed_by_broker must be boolean",
        block_reasons,
    )
    _expect_bool(
        payload,
        "market_session.is_major_news_window",
        "market_session.is_major_news_window must be boolean",
        block_reasons,
    )
    _expect_bool(
        payload,
        "market_session.is_rollover_window",
        "market_session.is_rollover_window must be boolean",
        block_reasons,
    )
    _expect_bool(
        payload,
        "market_session.is_weekend",
        "market_session.is_weekend must be boolean",
        block_reasons,
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


def _expect_non_negative_integer(
    payload: dict[str, Any],
    field_path: str,
    reason: str,
    block_reasons: list[str],
) -> None:
    value = _field_value(payload, field_path)
    if not _is_non_negative_integer(value):
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


def _expect_positive_number(
    payload: dict[str, Any],
    field_path: str,
    reason: str,
    block_reasons: list[str],
) -> None:
    value = _field_value(payload, field_path)
    if not _is_number(value) or value <= 0:
        block_reasons.append(reason)


def _expect_bool(
    payload: dict[str, Any],
    field_path: str,
    reason: str,
    block_reasons: list[str],
) -> None:
    if not isinstance(_field_value(payload, field_path), bool):
        block_reasons.append(reason)


def _expect_ask_not_below_bid(
    payload: dict[str, Any],
    block_reasons: list[str],
) -> None:
    bid = _field_value(payload, "quote.bid")
    ask = _field_value(payload, "quote.ask")

    if _is_number(bid) and _is_number(ask) and ask < bid:
        block_reasons.append("quote.ask must be greater than or equal to bid")


def _expect_max_lot_not_below_min_lot(
    payload: dict[str, Any],
    block_reasons: list[str],
) -> None:
    min_lot = _field_value(payload, "symbol_spec.min_lot")
    max_lot = _field_value(payload, "symbol_spec.max_lot")

    if not _is_number(max_lot):
        block_reasons.append("symbol_spec.max_lot must be greater than or equal to min_lot")
        return

    if _is_number(min_lot) and max_lot < min_lot:
        block_reasons.append("symbol_spec.max_lot must be greater than or equal to min_lot")


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


def _is_non_negative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


class _MissingField:
    pass
