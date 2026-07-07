from __future__ import annotations

import copy
import math
from pathlib import Path

import pytest

from app.services.mt4_demo_readonly_schema_validator import (
    ACCOUNT_SNAPSHOT_FILE,
    MARKET_SYMBOL_FILE,
    MT4_DEMO_READONLY_FILENAME_REJECTED,
    MT4_DEMO_READONLY_FORBIDDEN_FIELD_DETECTED,
    MT4_DEMO_READONLY_SCHEMA_INPUT_INVALID,
    MT4_DEMO_READONLY_SCHEMA_VALID,
    POSITIONS_ORDER_HISTORY_FILE,
    validate_account_snapshot_payload,
    validate_market_symbol_payload,
    validate_mt4_demo_readonly_payload,
    validate_positions_order_history_payload,
)


FORBIDDEN_RESULT_FIELDS = {
    "payload",
    "raw_payload",
    "password",
    "credential",
    "token",
    "secret",
    "login",
    "account_number",
    "ticket",
    "order_id",
    "suggested_lot",
    "final_lot",
    "buy",
    "sell",
    "open",
    "close",
    "ea_command",
    "trade_signal",
    "trading_action",
}


def _global_fields() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "generated_at": "2026-07-07T10:00:00Z",
        "source_mode": "mt4_demo_readonly_file_bridge_enabled",
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }


def _valid_account_snapshot_payload() -> dict[str, object]:
    return {
        **_global_fields(),
        "terminal_name": "MT4 Demo Terminal",
        "server_name_masked": "Demo-Server-***",
        "account_type": "demo",
        "currency": "USD",
        "balance": 10000.0,
        "equity": 10010.5,
        "margin": 120.0,
        "free_margin": 9890.5,
        "margin_level": 8334.0,
        "leverage": 100,
        "positions_count": 1,
        "orders_count": 2,
        "data_quality_notes": ["demo readonly account snapshot"],
    }


def _valid_positions_order_history_payload() -> dict[str, object]:
    return {
        **_global_fields(),
        "open_positions": [
            {
                "position_ref": "pos-demo-001",
                "symbol": "XAUUSD",
                "side_masked": "readonly_side_1",
                "volume": 0.01,
                "open_time": "2026-07-07T09:30:00Z",
                "open_price": 2350.1,
                "current_price": 2351.3,
                "floating_pnl": 1.2,
                "swap": 0.0,
                "commission": -0.1,
                "age_minutes": 30,
                "read_only_note": "readonly position summary",
            }
        ],
        "recent_closed_orders": [
            {
                "order_ref": "order-demo-001",
                "symbol": "XAUUSD",
                "side_masked": "readonly_side_2",
                "volume": 0.02,
                "open_time": "2026-07-06T09:30:00Z",
                "close_time": "2026-07-06T10:30:00Z",
                "open_price": 2340.0,
                "close_price": 2342.0,
                "realized_pnl": 4.0,
                "swap": 0.0,
                "commission": -0.2,
                "duration_minutes": 60,
                "read_only_note": "readonly closed order summary",
            }
        ],
        "pending_orders_summary": {
            "count": 0,
            "symbols": ["XAUUSD"],
            "read_only_note": "readonly pending order summary",
        },
        "data_quality_notes": ["demo readonly positions order history"],
    }


def _valid_market_symbol_payload() -> dict[str, object]:
    return {
        **_global_fields(),
        "symbol": "XAUUSD",
        "bid": 2350.1,
        "ask": 2350.4,
        "spread_points": 30,
        "digits": 2,
        "point": 0.01,
        "tick_size": 0.01,
        "tick_value": 1.0,
        "contract_size": 100.0,
        "trade_mode_readonly_label": "readonly-demo-observed",
        "session_status_readonly_label": "readonly-session-observed",
        "last_tick_time": "2026-07-07T10:00:00Z",
        "data_age_seconds": 1.0,
        "data_quality_notes": ["demo readonly market symbol"],
    }


def _assert_safety_fields(result: dict[str, object]) -> None:
    assert result["read_only"] is True
    assert result["demo_only"] is True
    assert result["is_tradable"] is False
    assert result["can_execute"] is False
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["allowed_to_call_ea"] is False
    assert result["allowed_to_modify_risk"] is False


def _assert_no_forbidden_result_fields(result: dict[str, object]) -> None:
    assert FORBIDDEN_RESULT_FIELDS.isdisjoint(result)
    assert "payload" not in result
    assert "raw_payload" not in result


def _assert_blocked(result: dict[str, object]) -> None:
    assert result["passed"] is False
    assert result["status_code"] != MT4_DEMO_READONLY_SCHEMA_VALID
    _assert_safety_fields(result)
    _assert_no_forbidden_result_fields(result)


@pytest.mark.parametrize(
    ("filename", "payload_factory"),
    [
        (ACCOUNT_SNAPSHOT_FILE, _valid_account_snapshot_payload),
        (POSITIONS_ORDER_HISTORY_FILE, _valid_positions_order_history_payload),
        (MARKET_SYMBOL_FILE, _valid_market_symbol_payload),
    ],
)
def test_valid_payloads_pass(filename: str, payload_factory: object) -> None:
    payload = payload_factory()

    result = validate_mt4_demo_readonly_payload(filename, payload)

    assert result["passed"] is True
    assert result["status_code"] == MT4_DEMO_READONLY_SCHEMA_VALID
    assert result["schema_version"] == "1.0"
    assert result["source_mode"] == "mt4_demo_readonly_file_bridge_enabled"
    assert result["reason_codes"] == []
    assert result["missing_fields"] == []
    assert result["invalid_fields"] == []
    assert result["blocked_fields"] == []
    _assert_safety_fields(result)
    _assert_no_forbidden_result_fields(result)


def test_direct_validators_pass_valid_payloads() -> None:
    assert validate_account_snapshot_payload(_valid_account_snapshot_payload())["passed"] is True
    assert (
        validate_positions_order_history_payload(
            _valid_positions_order_history_payload()
        )["passed"]
        is True
    )
    assert validate_market_symbol_payload(_valid_market_symbol_payload())["passed"] is True


def test_filename_not_in_whitelist_is_blocked() -> None:
    result = validate_mt4_demo_readonly_payload(
        "orders_to_send.json",
        _valid_account_snapshot_payload(),
    )

    assert result["passed"] is False
    assert result["status_code"] == MT4_DEMO_READONLY_FILENAME_REJECTED
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    ("validator", "payload"),
    [
        (validate_account_snapshot_payload, None),
        (validate_positions_order_history_payload, []),
        (validate_market_symbol_payload, "not a dict"),
    ],
)
def test_payload_not_dict_is_blocked(validator: object, payload: object) -> None:
    result = validator(payload)

    assert result["passed"] is False
    assert result["status_code"] == MT4_DEMO_READONLY_SCHEMA_INPUT_INVALID
    assert "PAYLOAD_NOT_DICT" in result["reason_codes"]
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    ("field_name", "replacement", "expected_reason"),
    [
        ("schema_version", None, "REQUIRED_FIELD_MISSING"),
        ("schema_version", "2.0", "SCHEMA_VERSION_UNSUPPORTED"),
        ("source_mode", None, "REQUIRED_FIELD_MISSING"),
        ("source_mode", "mt4_live_readonly", "SOURCE_MODE_REJECTED"),
        ("read_only", None, "REQUIRED_FIELD_MISSING"),
        ("read_only", False, "SAFETY_FIELD_VIOLATION"),
        ("read_only", "true", "SAFETY_FIELD_VIOLATION"),
        ("demo_only", False, "SAFETY_FIELD_VIOLATION"),
        ("is_tradable", True, "SAFETY_FIELD_VIOLATION"),
        ("can_execute", True, "SAFETY_FIELD_VIOLATION"),
        ("is_trading_permission", True, "SAFETY_FIELD_VIOLATION"),
        ("is_execution_instruction", True, "SAFETY_FIELD_VIOLATION"),
        ("allowed_to_call_ea", True, "SAFETY_FIELD_VIOLATION"),
        ("allowed_to_modify_risk", True, "SAFETY_FIELD_VIOLATION"),
    ],
)
def test_global_field_violations_are_blocked(
    field_name: str,
    replacement: object,
    expected_reason: str,
) -> None:
    payload = _valid_account_snapshot_payload()
    if replacement is None:
        payload.pop(field_name)
    else:
        payload[field_name] = replacement

    result = validate_account_snapshot_payload(payload)

    _assert_blocked(result)
    assert expected_reason in result["reason_codes"]


@pytest.mark.parametrize(
    "forbidden_field",
    [
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
        "suggested_lot",
        "final_lot",
        "buy_now",
        "sell_now",
        "should_buy",
        "should_sell",
        "open_position",
        "close_position",
        "execute_trade",
        "can_trade",
        "allow_trade",
        "trade_signal",
        "trading_action",
        "override_risk",
        "bypass_gate",
    ],
)
def test_top_level_forbidden_fields_are_blocked(forbidden_field: str) -> None:
    payload = _valid_account_snapshot_payload()
    payload[forbidden_field] = "DO_NOT_LEAK_SECRET_VALUE"

    result = validate_account_snapshot_payload(payload)

    assert result["status_code"] == MT4_DEMO_READONLY_FORBIDDEN_FIELD_DETECTED
    assert forbidden_field in result["blocked_fields"]
    assert "DO_NOT_LEAK_SECRET_VALUE" not in str(result)
    _assert_blocked(result)


def test_unknown_field_is_blocked() -> None:
    payload = _valid_market_symbol_payload()
    payload["unexpected_field"] = "safe but not allowed"

    result = validate_market_symbol_payload(payload)

    _assert_blocked(result)
    assert "UNKNOWN_FIELD_DETECTED" in result["reason_codes"]
    assert "unexpected_field" in result["invalid_fields"]


@pytest.mark.parametrize(
    ("container_name", "forbidden_field"),
    [
        ("open_positions", "ticket"),
        ("open_positions", "password"),
        ("recent_closed_orders", "order_id"),
        ("recent_closed_orders", "secret"),
    ],
)
def test_nested_forbidden_fields_in_position_arrays_are_blocked(
    container_name: str,
    forbidden_field: str,
) -> None:
    payload = _valid_positions_order_history_payload()
    payload[container_name][0][forbidden_field] = "NEVER_LEAK_THIS_VALUE"

    result = validate_positions_order_history_payload(payload)

    assert result["status_code"] == MT4_DEMO_READONLY_FORBIDDEN_FIELD_DETECTED
    assert any(forbidden_field in field for field in result["blocked_fields"])
    assert "NEVER_LEAK_THIS_VALUE" not in str(result)
    _assert_blocked(result)


def test_nested_forbidden_field_in_pending_orders_summary_is_blocked() -> None:
    payload = _valid_positions_order_history_payload()
    payload["pending_orders_summary"]["ea_command"] = "NEVER_LEAK_THIS_VALUE"

    result = validate_positions_order_history_payload(payload)

    assert result["status_code"] == MT4_DEMO_READONLY_FORBIDDEN_FIELD_DETECTED
    assert "pending_orders_summary.ea_command" in result["blocked_fields"]
    assert "NEVER_LEAK_THIS_VALUE" not in str(result)
    _assert_blocked(result)


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("balance", "10000"),
        ("equity", "10000"),
        ("margin", "1"),
        ("free_margin", "1"),
        ("margin_level", "1"),
        ("leverage", "100"),
        ("positions_count", -1),
        ("orders_count", -1),
        ("data_quality_notes", "not a list"),
    ],
)
def test_invalid_account_snapshot_types_or_values_are_blocked(
    field_name: str,
    replacement: object,
) -> None:
    payload = _valid_account_snapshot_payload()
    payload[field_name] = replacement

    result = validate_account_snapshot_payload(payload)

    _assert_blocked(result)
    assert field_name in result["invalid_fields"]


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("open_positions", "not a list"),
        ("recent_closed_orders", "not a list"),
        ("pending_orders_summary", []),
        ("data_quality_notes", ["ok", 1]),
    ],
)
def test_invalid_positions_top_level_types_are_blocked(
    field_name: str,
    replacement: object,
) -> None:
    payload = _valid_positions_order_history_payload()
    payload[field_name] = replacement

    result = validate_positions_order_history_payload(payload)

    _assert_blocked(result)
    assert field_name in result["invalid_fields"]


@pytest.mark.parametrize("container_name", ["open_positions", "recent_closed_orders"])
def test_invalid_positions_item_type_is_blocked(container_name: str) -> None:
    payload = _valid_positions_order_history_payload()
    payload[container_name][0] = "not an object"

    result = validate_positions_order_history_payload(payload)

    _assert_blocked(result)
    assert f"{container_name}[0]" in result["invalid_fields"]


@pytest.mark.parametrize(
    ("container_name", "field_name", "replacement"),
    [
        ("open_positions", "volume", "0.01"),
        ("open_positions", "age_minutes", -1),
        ("open_positions", "position_ref", "ticket"),
        ("recent_closed_orders", "realized_pnl", "1.0"),
        ("recent_closed_orders", "duration_minutes", -1),
        ("recent_closed_orders", "order_ref", "order_id"),
    ],
)
def test_invalid_positions_item_values_are_blocked(
    container_name: str,
    field_name: str,
    replacement: object,
) -> None:
    payload = _valid_positions_order_history_payload()
    payload[container_name][0][field_name] = replacement

    result = validate_positions_order_history_payload(payload)

    _assert_blocked(result)
    assert any(field_name in field for field in result["invalid_fields"])


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("count", -1),
        ("symbols", ["XAUUSD", 2]),
        ("read_only_note", 123),
    ],
)
def test_invalid_pending_orders_summary_values_are_blocked(
    field_name: str,
    replacement: object,
) -> None:
    payload = _valid_positions_order_history_payload()
    payload["pending_orders_summary"][field_name] = replacement

    result = validate_positions_order_history_payload(payload)

    _assert_blocked(result)
    assert f"pending_orders_summary.{field_name}" in result["invalid_fields"]


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("symbol", 123),
        ("bid", "2350.1"),
        ("ask", "2350.4"),
        ("spread_points", "30"),
        ("digits", 2.5),
        ("digits", -1),
        ("point", "0.01"),
        ("tick_size", "0.01"),
        ("tick_value", "1"),
        ("contract_size", "100"),
        ("trade_mode_readonly_label", 1),
        ("session_status_readonly_label", 1),
        ("last_tick_time", 123),
        ("data_age_seconds", -1),
        ("data_quality_notes", "not a list"),
    ],
)
def test_invalid_market_symbol_types_or_values_are_blocked(
    field_name: str,
    replacement: object,
) -> None:
    payload = _valid_market_symbol_payload()
    payload[field_name] = replacement

    result = validate_market_symbol_payload(payload)

    _assert_blocked(result)
    assert field_name in result["invalid_fields"]


@pytest.mark.parametrize("bad_number", [math.nan, math.inf, -math.inf])
def test_nan_and_infinity_numbers_are_blocked(bad_number: float) -> None:
    payload = _valid_market_symbol_payload()
    payload["bid"] = bad_number

    result = validate_market_symbol_payload(payload)

    _assert_blocked(result)
    assert "bid" in result["invalid_fields"]


def test_result_never_contains_raw_payload_or_sensitive_values() -> None:
    payload = _valid_account_snapshot_payload()
    payload["password"] = "SUPER_SECRET_PASSWORD"
    payload["token"] = "SUPER_SECRET_TOKEN"

    result = validate_account_snapshot_payload(payload)

    assert "SUPER_SECRET_PASSWORD" not in str(result)
    assert "SUPER_SECRET_TOKEN" not in str(result)
    _assert_no_forbidden_result_fields(result)
    _assert_safety_fields(result)


def test_validator_does_not_call_filesystem_or_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("filesystem or network access is not allowed")

    monkeypatch.setattr("builtins.open", fail_if_called)
    monkeypatch.setattr("glob.glob", fail_if_called)
    monkeypatch.setattr("os.walk", fail_if_called)
    monkeypatch.setattr("socket.create_connection", fail_if_called)
    monkeypatch.setattr(Path, "exists", fail_if_called)
    monkeypatch.setattr(Path, "is_file", fail_if_called)
    monkeypatch.setattr(Path, "iterdir", fail_if_called)
    monkeypatch.setattr(Path, "read_text", fail_if_called)
    monkeypatch.setattr(Path, "write_text", fail_if_called)

    result = validate_mt4_demo_readonly_payload(
        ACCOUNT_SNAPSHOT_FILE,
        _valid_account_snapshot_payload(),
    )

    assert result["passed"] is True
    _assert_safety_fields(result)


def test_payload_is_not_mutated() -> None:
    payload = _valid_positions_order_history_payload()
    original = copy.deepcopy(payload)

    result = validate_positions_order_history_payload(payload)

    assert result["passed"] is True
    assert payload == original
