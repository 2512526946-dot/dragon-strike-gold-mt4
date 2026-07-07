from __future__ import annotations

import math
from typing import Any

from app.services.mt4_demo_readonly_path_guard import (
    MT4_DEMO_READONLY_INPUT_INVALID,
    validate_mt4_demo_readonly_filename,
)


MT4_DEMO_READONLY_SCHEMA_VALID = "MT4_DEMO_READONLY_SCHEMA_VALID"
MT4_DEMO_READONLY_SCHEMA_INVALID = "MT4_DEMO_READONLY_SCHEMA_INVALID"
MT4_DEMO_READONLY_SCHEMA_INPUT_INVALID = "MT4_DEMO_READONLY_SCHEMA_INPUT_INVALID"
MT4_DEMO_READONLY_SCHEMA_VERSION_UNSUPPORTED = (
    "MT4_DEMO_READONLY_SCHEMA_VERSION_UNSUPPORTED"
)
MT4_DEMO_READONLY_SOURCE_MODE_REJECTED = "MT4_DEMO_READONLY_SOURCE_MODE_REJECTED"
MT4_DEMO_READONLY_SAFETY_FIELD_VIOLATION = (
    "MT4_DEMO_READONLY_SAFETY_FIELD_VIOLATION"
)
MT4_DEMO_READONLY_FORBIDDEN_FIELD_DETECTED = (
    "MT4_DEMO_READONLY_FORBIDDEN_FIELD_DETECTED"
)
MT4_DEMO_READONLY_FILENAME_REJECTED = "MT4_DEMO_READONLY_FILENAME_REJECTED"

SUPPORTED_SCHEMA_VERSION = "1.0"
ALLOWED_SOURCE_MODE = "mt4_demo_readonly_file_bridge_enabled"

ACCOUNT_SNAPSHOT_FILE = "account_snapshot.json"
POSITIONS_ORDER_HISTORY_FILE = "positions_order_history.json"
MARKET_SYMBOL_FILE = "market_symbol.json"

ACCOUNT_SNAPSHOT_KIND = "account_snapshot"
POSITIONS_ORDER_HISTORY_KIND = "positions_order_history"
MARKET_SYMBOL_KIND = "market_symbol"

_SAFETY_FIELDS: dict[str, bool] = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}

_GLOBAL_REQUIRED_FIELDS = (
    "schema_version",
    "generated_at",
    "source_mode",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)

_FORBIDDEN_FIELDS = frozenset(
    {
        "password",
        "credential",
        "token",
        "secret",
        "api_key",
        "login",
        "account_number",
        "raw_payload",
        "ticket",
        "order_id",
        "order_send",
        "order_close",
        "order_modify",
        "order_delete",
        "ea_command",
        "execute_trade",
        "can_trade",
        "allow_trade",
        "should_buy",
        "should_sell",
        "buy_now",
        "sell_now",
        "open_position",
        "close_position",
        "suggested_lot",
        "final_lot",
        "trade_signal",
        "trading_action",
        "override_risk",
        "bypass_gate",
    }
)

_ACCOUNT_ALLOWED_FIELDS = frozenset(
    {
        *_GLOBAL_REQUIRED_FIELDS,
        "terminal_name",
        "server_name_masked",
        "account_type",
        "currency",
        "balance",
        "equity",
        "margin",
        "free_margin",
        "margin_level",
        "leverage",
        "positions_count",
        "orders_count",
        "data_quality_notes",
    }
)

_POSITIONS_TOP_ALLOWED_FIELDS = frozenset(
    {
        *_GLOBAL_REQUIRED_FIELDS,
        "open_positions",
        "recent_closed_orders",
        "pending_orders_summary",
        "data_quality_notes",
    }
)

_OPEN_POSITION_ALLOWED_FIELDS = frozenset(
    {
        "position_ref",
        "symbol",
        "side_masked",
        "volume",
        "open_time",
        "open_price",
        "current_price",
        "floating_pnl",
        "swap",
        "commission",
        "age_minutes",
        "read_only_note",
    }
)

_RECENT_CLOSED_ORDER_ALLOWED_FIELDS = frozenset(
    {
        "order_ref",
        "symbol",
        "side_masked",
        "volume",
        "open_time",
        "close_time",
        "open_price",
        "close_price",
        "realized_pnl",
        "swap",
        "commission",
        "duration_minutes",
        "read_only_note",
    }
)

_PENDING_ORDERS_SUMMARY_ALLOWED_FIELDS = frozenset(
    {
        "count",
        "symbols",
        "read_only_note",
    }
)

_MARKET_ALLOWED_FIELDS = frozenset(
    {
        *_GLOBAL_REQUIRED_FIELDS,
        "symbol",
        "bid",
        "ask",
        "spread_points",
        "digits",
        "point",
        "tick_size",
        "tick_value",
        "contract_size",
        "trade_mode_readonly_label",
        "session_status_readonly_label",
        "last_tick_time",
        "data_age_seconds",
        "data_quality_notes",
    }
)

_FILENAME_TO_KIND = {
    ACCOUNT_SNAPSHOT_FILE: ACCOUNT_SNAPSHOT_KIND,
    POSITIONS_ORDER_HISTORY_FILE: POSITIONS_ORDER_HISTORY_KIND,
    MARKET_SYMBOL_FILE: MARKET_SYMBOL_KIND,
}


def validate_account_snapshot_payload(payload: object) -> dict[str, Any]:
    return _validate_schema(
        file_kind=ACCOUNT_SNAPSHOT_KIND,
        payload=payload,
        allowed_fields=_ACCOUNT_ALLOWED_FIELDS,
        validate_kind_fields=_validate_account_snapshot_fields,
    )


def validate_positions_order_history_payload(payload: object) -> dict[str, Any]:
    return _validate_schema(
        file_kind=POSITIONS_ORDER_HISTORY_KIND,
        payload=payload,
        allowed_fields=_POSITIONS_TOP_ALLOWED_FIELDS,
        validate_kind_fields=_validate_positions_order_history_fields,
    )


def validate_market_symbol_payload(payload: object) -> dict[str, Any]:
    return _validate_schema(
        file_kind=MARKET_SYMBOL_KIND,
        payload=payload,
        allowed_fields=_MARKET_ALLOWED_FIELDS,
        validate_kind_fields=_validate_market_symbol_fields,
    )


def validate_mt4_demo_readonly_payload(
    filename: object,
    payload: object,
) -> dict[str, Any]:
    filename_result = validate_mt4_demo_readonly_filename(filename)
    if filename_result["passed"] is not True:
        return _build_result(
            passed=False,
            status_code=(
                MT4_DEMO_READONLY_SCHEMA_INPUT_INVALID
                if filename_result["status_code"] == MT4_DEMO_READONLY_INPUT_INVALID
                else MT4_DEMO_READONLY_FILENAME_REJECTED
            ),
            file_kind=None,
            schema_version=None,
            source_mode=None,
            reason_codes=["FILENAME_REJECTED"],
            missing_fields=[],
            invalid_fields=[],
            blocked_fields=[],
        )

    file_kind = _FILENAME_TO_KIND[str(filename_result["safe_filename"])]
    if file_kind == ACCOUNT_SNAPSHOT_KIND:
        return validate_account_snapshot_payload(payload)
    if file_kind == POSITIONS_ORDER_HISTORY_KIND:
        return validate_positions_order_history_payload(payload)
    return validate_market_symbol_payload(payload)


def _validate_schema(
    *,
    file_kind: str,
    payload: object,
    allowed_fields: frozenset[str],
    validate_kind_fields: Any,
) -> dict[str, Any]:
    context = _ValidationContext()
    if not isinstance(payload, dict):
        context.reason("PAYLOAD_NOT_DICT")
        return _build_result(
            passed=False,
            status_code=MT4_DEMO_READONLY_SCHEMA_INPUT_INVALID,
            file_kind=file_kind,
            schema_version=None,
            source_mode=None,
            reason_codes=context.reason_codes,
            missing_fields=context.missing_fields,
            invalid_fields=context.invalid_fields,
            blocked_fields=context.blocked_fields,
        )

    _collect_forbidden_fields(payload, context)
    _validate_unknown_fields(payload, allowed_fields, context)
    _validate_global_fields(payload, context)
    validate_kind_fields(payload, context)

    passed = not (
        context.reason_codes
        or context.missing_fields
        or context.invalid_fields
        or context.blocked_fields
    )

    return _build_result(
        passed=passed,
        status_code=(
            MT4_DEMO_READONLY_SCHEMA_VALID
            if passed
            else _status_code_for_context(context)
        ),
        file_kind=file_kind,
        schema_version=payload.get("schema_version")
        if payload.get("schema_version") == SUPPORTED_SCHEMA_VERSION
        else None,
        source_mode=payload.get("source_mode")
        if payload.get("source_mode") == ALLOWED_SOURCE_MODE
        else None,
        reason_codes=context.reason_codes,
        missing_fields=context.missing_fields,
        invalid_fields=context.invalid_fields,
        blocked_fields=context.blocked_fields,
    )


def _build_result(
    *,
    passed: bool,
    status_code: str,
    file_kind: str | None,
    schema_version: str | None,
    source_mode: str | None,
    reason_codes: list[str],
    missing_fields: list[str],
    invalid_fields: list[str],
    blocked_fields: list[str],
) -> dict[str, Any]:
    return {
        "passed": passed,
        "status_code": status_code,
        "file_kind": file_kind,
        "schema_version": schema_version,
        "source_mode": source_mode,
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "missing_fields": sorted(set(missing_fields)),
        "invalid_fields": sorted(set(invalid_fields)),
        "blocked_fields": sorted(set(blocked_fields)),
        "data_quality_notes": [],
        **_SAFETY_FIELDS,
    }


def _status_code_for_context(context: "_ValidationContext") -> str:
    if context.blocked_fields:
        return MT4_DEMO_READONLY_FORBIDDEN_FIELD_DETECTED
    if "SCHEMA_VERSION_UNSUPPORTED" in context.reason_codes:
        return MT4_DEMO_READONLY_SCHEMA_VERSION_UNSUPPORTED
    if "SOURCE_MODE_REJECTED" in context.reason_codes:
        return MT4_DEMO_READONLY_SOURCE_MODE_REJECTED
    if "SAFETY_FIELD_VIOLATION" in context.reason_codes:
        return MT4_DEMO_READONLY_SAFETY_FIELD_VIOLATION
    return MT4_DEMO_READONLY_SCHEMA_INVALID


def _validate_global_fields(
    payload: dict[str, Any],
    context: "_ValidationContext",
) -> None:
    for field_name in _GLOBAL_REQUIRED_FIELDS:
        _require_field(payload, field_name, context)

    _expect_equal(
        payload,
        "schema_version",
        SUPPORTED_SCHEMA_VERSION,
        context,
        reason_code="SCHEMA_VERSION_UNSUPPORTED",
    )
    _expect_equal(
        payload,
        "source_mode",
        ALLOWED_SOURCE_MODE,
        context,
        reason_code="SOURCE_MODE_REJECTED",
    )
    for field_name, expected_value in _SAFETY_FIELDS.items():
        _expect_equal(
            payload,
            field_name,
            expected_value,
            context,
            reason_code="SAFETY_FIELD_VIOLATION",
        )

    _expect_string(payload, "generated_at", context)


def _validate_account_snapshot_fields(
    payload: dict[str, Any],
    context: "_ValidationContext",
) -> None:
    required_fields = _ACCOUNT_ALLOWED_FIELDS - set(_GLOBAL_REQUIRED_FIELDS)
    for field_name in required_fields:
        _require_field(payload, field_name, context)

    for field_name in (
        "terminal_name",
        "server_name_masked",
        "account_type",
        "currency",
    ):
        _expect_string(payload, field_name, context)

    for field_name in (
        "balance",
        "equity",
        "margin",
        "free_margin",
        "margin_level",
        "leverage",
    ):
        _expect_number(payload, field_name, context)

    for field_name in ("positions_count", "orders_count"):
        _expect_non_negative_integer(payload, field_name, context)

    _expect_string_list(payload, "data_quality_notes", context)


def _validate_positions_order_history_fields(
    payload: dict[str, Any],
    context: "_ValidationContext",
) -> None:
    required_fields = _POSITIONS_TOP_ALLOWED_FIELDS - set(_GLOBAL_REQUIRED_FIELDS)
    for field_name in required_fields:
        _require_field(payload, field_name, context)

    _validate_open_positions(payload, context)
    _validate_recent_closed_orders(payload, context)
    _validate_pending_orders_summary(payload, context)
    _expect_string_list(payload, "data_quality_notes", context)


def _validate_market_symbol_fields(
    payload: dict[str, Any],
    context: "_ValidationContext",
) -> None:
    required_fields = _MARKET_ALLOWED_FIELDS - set(_GLOBAL_REQUIRED_FIELDS)
    for field_name in required_fields:
        _require_field(payload, field_name, context)

    for field_name in (
        "symbol",
        "trade_mode_readonly_label",
        "session_status_readonly_label",
        "last_tick_time",
    ):
        _expect_string(payload, field_name, context)

    for field_name in (
        "bid",
        "ask",
        "spread_points",
        "point",
        "tick_size",
        "tick_value",
        "contract_size",
    ):
        _expect_number(payload, field_name, context)

    _expect_non_negative_integer(payload, "digits", context)
    _expect_non_negative_number(payload, "data_age_seconds", context)
    _expect_string_list(payload, "data_quality_notes", context)


def _validate_open_positions(
    payload: dict[str, Any],
    context: "_ValidationContext",
) -> None:
    field_name = "open_positions"
    positions = payload.get(field_name)
    if not isinstance(positions, list):
        context.invalid(field_name, "FIELD_TYPE_INVALID")
        return

    for index, item in enumerate(positions):
        prefix = f"{field_name}[{index}]"
        if not isinstance(item, dict):
            context.invalid(prefix, "NESTED_ITEM_NOT_OBJECT")
            continue
        _validate_unknown_fields_for_object(
            item,
            _OPEN_POSITION_ALLOWED_FIELDS,
            prefix,
            context,
        )
        _validate_open_position_item(item, prefix, context)


def _validate_open_position_item(
    item: dict[str, Any],
    prefix: str,
    context: "_ValidationContext",
) -> None:
    for field_name in _OPEN_POSITION_ALLOWED_FIELDS:
        _require_field(item, field_name, context, prefix=prefix)

    for field_name in ("position_ref", "symbol", "side_masked", "open_time", "read_only_note"):
        _expect_string(item, field_name, context, prefix=prefix)

    if item.get("position_ref") in {"ticket", "order_id"}:
        context.invalid(f"{prefix}.position_ref", "EXECUTABLE_REFERENCE_REJECTED")

    for field_name in (
        "volume",
        "open_price",
        "current_price",
        "floating_pnl",
        "swap",
        "commission",
    ):
        _expect_number(item, field_name, context, prefix=prefix)

    _expect_non_negative_number(item, "age_minutes", context, prefix=prefix)


def _validate_recent_closed_orders(
    payload: dict[str, Any],
    context: "_ValidationContext",
) -> None:
    field_name = "recent_closed_orders"
    orders = payload.get(field_name)
    if not isinstance(orders, list):
        context.invalid(field_name, "FIELD_TYPE_INVALID")
        return

    for index, item in enumerate(orders):
        prefix = f"{field_name}[{index}]"
        if not isinstance(item, dict):
            context.invalid(prefix, "NESTED_ITEM_NOT_OBJECT")
            continue
        _validate_unknown_fields_for_object(
            item,
            _RECENT_CLOSED_ORDER_ALLOWED_FIELDS,
            prefix,
            context,
        )
        _validate_recent_closed_order_item(item, prefix, context)


def _validate_recent_closed_order_item(
    item: dict[str, Any],
    prefix: str,
    context: "_ValidationContext",
) -> None:
    for field_name in _RECENT_CLOSED_ORDER_ALLOWED_FIELDS:
        _require_field(item, field_name, context, prefix=prefix)

    for field_name in (
        "order_ref",
        "symbol",
        "side_masked",
        "open_time",
        "close_time",
        "read_only_note",
    ):
        _expect_string(item, field_name, context, prefix=prefix)

    if item.get("order_ref") in {"ticket", "order_id"}:
        context.invalid(f"{prefix}.order_ref", "EXECUTABLE_REFERENCE_REJECTED")

    for field_name in (
        "volume",
        "open_price",
        "close_price",
        "realized_pnl",
        "swap",
        "commission",
    ):
        _expect_number(item, field_name, context, prefix=prefix)

    _expect_non_negative_number(item, "duration_minutes", context, prefix=prefix)


def _validate_pending_orders_summary(
    payload: dict[str, Any],
    context: "_ValidationContext",
) -> None:
    field_name = "pending_orders_summary"
    summary = payload.get(field_name)
    if not isinstance(summary, dict):
        context.invalid(field_name, "FIELD_TYPE_INVALID")
        return

    _validate_unknown_fields_for_object(
        summary,
        _PENDING_ORDERS_SUMMARY_ALLOWED_FIELDS,
        field_name,
        context,
    )
    for child_field in _PENDING_ORDERS_SUMMARY_ALLOWED_FIELDS:
        _require_field(summary, child_field, context, prefix=field_name)

    _expect_non_negative_integer(summary, "count", context, prefix=field_name)
    _expect_string_list(summary, "symbols", context, prefix=field_name)
    _expect_string(summary, "read_only_note", context, prefix=field_name)


def _require_field(
    payload: dict[str, Any],
    field_name: str,
    context: "_ValidationContext",
    *,
    prefix: str | None = None,
) -> None:
    if field_name not in payload:
        context.missing(_field_path(field_name, prefix))


def _expect_equal(
    payload: dict[str, Any],
    field_name: str,
    expected_value: object,
    context: "_ValidationContext",
    *,
    reason_code: str,
    prefix: str | None = None,
) -> None:
    if field_name not in payload:
        return
    if payload[field_name] != expected_value or type(payload[field_name]) is not type(expected_value):
        context.invalid(_field_path(field_name, prefix), reason_code)


def _expect_string(
    payload: dict[str, Any],
    field_name: str,
    context: "_ValidationContext",
    *,
    prefix: str | None = None,
) -> None:
    if field_name not in payload:
        return
    if not isinstance(payload[field_name], str):
        context.invalid(_field_path(field_name, prefix), "FIELD_TYPE_INVALID")


def _expect_number(
    payload: dict[str, Any],
    field_name: str,
    context: "_ValidationContext",
    *,
    prefix: str | None = None,
) -> None:
    if field_name not in payload:
        return
    if not _is_finite_number(payload[field_name]):
        context.invalid(_field_path(field_name, prefix), "FIELD_NUMBER_INVALID")


def _expect_non_negative_number(
    payload: dict[str, Any],
    field_name: str,
    context: "_ValidationContext",
    *,
    prefix: str | None = None,
) -> None:
    if field_name not in payload:
        return
    value = payload[field_name]
    if not _is_finite_number(value) or value < 0:
        context.invalid(_field_path(field_name, prefix), "FIELD_NON_NEGATIVE_NUMBER_INVALID")


def _expect_non_negative_integer(
    payload: dict[str, Any],
    field_name: str,
    context: "_ValidationContext",
    *,
    prefix: str | None = None,
) -> None:
    if field_name not in payload:
        return
    value = payload[field_name]
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        context.invalid(_field_path(field_name, prefix), "FIELD_NON_NEGATIVE_INTEGER_INVALID")


def _expect_string_list(
    payload: dict[str, Any],
    field_name: str,
    context: "_ValidationContext",
    *,
    prefix: str | None = None,
) -> None:
    if field_name not in payload:
        return
    value = payload[field_name]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        context.invalid(_field_path(field_name, prefix), "FIELD_STRING_LIST_INVALID")


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _validate_unknown_fields(
    payload: dict[str, Any],
    allowed_fields: frozenset[str],
    context: "_ValidationContext",
) -> None:
    _validate_unknown_fields_for_object(payload, allowed_fields, None, context)


def _validate_unknown_fields_for_object(
    payload: dict[str, Any],
    allowed_fields: frozenset[str],
    prefix: str | None,
    context: "_ValidationContext",
) -> None:
    for field_name in payload:
        if field_name not in allowed_fields and field_name not in _FORBIDDEN_FIELDS:
            context.invalid(_field_path(field_name, prefix), "UNKNOWN_FIELD_DETECTED")


def _collect_forbidden_fields(
    value: object,
    context: "_ValidationContext",
    *,
    prefix: str | None = None,
) -> None:
    if isinstance(value, dict):
        for field_name, child_value in value.items():
            child_path = _field_path(field_name, prefix)
            if field_name in _FORBIDDEN_FIELDS:
                context.blocked(child_path)
            _collect_forbidden_fields(child_value, context, prefix=child_path)
        return

    if isinstance(value, list):
        for item in value:
            _collect_forbidden_fields(item, context, prefix=prefix)


def _field_path(field_name: str, prefix: str | None = None) -> str:
    if prefix:
        return f"{prefix}.{field_name}"
    return field_name


class _ValidationContext:
    def __init__(self) -> None:
        self.reason_codes: list[str] = []
        self.missing_fields: list[str] = []
        self.invalid_fields: list[str] = []
        self.blocked_fields: list[str] = []

    def reason(self, reason_code: str) -> None:
        self.reason_codes.append(reason_code)

    def missing(self, field_path: str) -> None:
        self.missing_fields.append(field_path)
        self.reason("REQUIRED_FIELD_MISSING")

    def invalid(self, field_path: str, reason_code: str) -> None:
        self.invalid_fields.append(field_path)
        self.reason(reason_code)

    def blocked(self, field_path: str) -> None:
        self.blocked_fields.append(field_path)
        self.reason("FORBIDDEN_FIELD_DETECTED")
