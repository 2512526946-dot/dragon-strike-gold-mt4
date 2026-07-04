from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEMO_POSITIONS_ORDER_HISTORY_VALID = "DEMO_POSITIONS_ORDER_HISTORY_VALID"
DEMO_POSITIONS_ORDER_HISTORY_INVALID = "DEMO_POSITIONS_ORDER_HISTORY_INVALID"

DEMO_POSITIONS_ORDER_HISTORY_NOTE = (
    "DemoPositionsOrderHistory validation is read-only. "
    "It is not trading permission and does not generate trading signals."
)

ALLOWED_DIRECTIONS = {"long", "short"}


@dataclass(frozen=True)
class DemoPositionsOrderHistoryValidationResult:
    passed: bool
    status_code: str
    block_reasons: list[str]
    warning_reasons: list[str]
    is_tradable: bool
    can_execute: bool
    note: str


def validate_demo_positions_order_history(
    payload: dict[str, Any],
) -> DemoPositionsOrderHistoryValidationResult:
    block_reasons: list[str] = []

    _expect_equal(
        payload,
        "record_type",
        "demo_positions_order_history",
        "record_type must be demo_positions_order_history",
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
        "safety_flags.is_order_instruction",
        False,
        "safety_flags.is_order_instruction must be false",
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
    _expect_non_negative_integer(
        payload,
        "open_positions_summary.open_positions_count",
        "open_positions_summary.open_positions_count must be a non-negative integer",
        block_reasons,
    )
    _expect_non_negative_number(
        payload,
        "open_positions_summary.total_lots",
        "open_positions_summary.total_lots must be a non-negative number",
        block_reasons,
    )
    _expect_non_negative_integer(
        payload,
        "order_history_summary.orders_count",
        "order_history_summary.orders_count must be a non-negative integer",
        block_reasons,
    )
    _expect_non_negative_integer(
        payload,
        "order_history_summary.closed_orders_count",
        "order_history_summary.closed_orders_count must be a non-negative integer",
        block_reasons,
    )
    _expect_non_negative_integer(
        payload,
        "order_history_summary.consecutive_losses",
        "order_history_summary.consecutive_losses must be a non-negative integer",
        block_reasons,
    )
    _validate_open_positions(payload, block_reasons)
    _validate_closed_orders(payload, block_reasons)
    _expect_safe_note(payload, block_reasons)

    passed = len(block_reasons) == 0

    return DemoPositionsOrderHistoryValidationResult(
        passed=passed,
        status_code=(
            DEMO_POSITIONS_ORDER_HISTORY_VALID
            if passed
            else DEMO_POSITIONS_ORDER_HISTORY_INVALID
        ),
        block_reasons=block_reasons,
        warning_reasons=[],
        is_tradable=False,
        can_execute=False,
        note=DEMO_POSITIONS_ORDER_HISTORY_NOTE,
    )


def _validate_open_positions(
    payload: dict[str, Any],
    block_reasons: list[str],
) -> None:
    open_positions = _field_value(payload, "open_positions")
    if not isinstance(open_positions, list):
        block_reasons.append("open_positions must be a list")
        return

    open_positions_count = _field_value(
        payload,
        "open_positions_summary.open_positions_count",
    )
    if _is_non_negative_integer(open_positions_count) and (
        open_positions_count != len(open_positions)
    ):
        block_reasons.append(
            "open_positions_summary.open_positions_count must equal open_positions count"
        )

    for index, position in enumerate(open_positions):
        _validate_open_position(index, position, block_reasons)


def _validate_open_position(
    index: int,
    position: Any,
    block_reasons: list[str],
) -> None:
    prefix = f"open_positions[{index}]"
    if not isinstance(position, dict):
        block_reasons.append(f"{prefix} must be an object")
        return

    _expect_equal(
        position,
        "symbol",
        "XAUUSD",
        f"{prefix}.symbol must be XAUUSD",
        block_reasons,
    )
    _expect_direction(position, f"{prefix}.direction", block_reasons)
    _expect_positive_number(
        position,
        "lot",
        f"{prefix}.lot must be greater than 0",
        block_reasons,
    )
    _expect_present_not_null(
        position,
        "stop_loss",
        f"{prefix}.stop_loss must exist and not be null",
        block_reasons,
    )


def _validate_closed_orders(
    payload: dict[str, Any],
    block_reasons: list[str],
) -> None:
    closed_orders = _field_value(payload, "closed_orders")
    if not isinstance(closed_orders, list):
        block_reasons.append("closed_orders must be a list")
        return

    closed_orders_count = _field_value(
        payload,
        "order_history_summary.closed_orders_count",
    )
    if _is_non_negative_integer(closed_orders_count) and (
        closed_orders_count != len(closed_orders)
    ):
        block_reasons.append(
            "order_history_summary.closed_orders_count must equal closed_orders count"
        )

    for index, order in enumerate(closed_orders):
        _validate_closed_order(index, order, block_reasons)


def _validate_closed_order(
    index: int,
    order: Any,
    block_reasons: list[str],
) -> None:
    prefix = f"closed_orders[{index}]"
    if not isinstance(order, dict):
        block_reasons.append(f"{prefix} must be an object")
        return

    _expect_equal(
        order,
        "symbol",
        "XAUUSD",
        f"{prefix}.symbol must be XAUUSD",
        block_reasons,
    )
    _expect_direction(order, f"{prefix}.direction", block_reasons)
    _expect_positive_number(
        order,
        "lot",
        f"{prefix}.lot must be greater than 0",
        block_reasons,
    )
    _expect_number(
        order,
        "closed_pnl",
        f"{prefix}.closed_pnl must be a number",
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


def _expect_present_not_null(
    payload: dict[str, Any],
    field_path: str,
    reason: str,
    block_reasons: list[str],
) -> None:
    value = _field_value(payload, field_path)
    if value is _MissingField or value is None:
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


def _expect_direction(
    payload: dict[str, Any],
    rendered_field_path: str,
    block_reasons: list[str],
) -> None:
    value = _field_value(payload, "direction")
    if value not in ALLOWED_DIRECTIONS:
        block_reasons.append(f"{rendered_field_path} must be long or short")


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
