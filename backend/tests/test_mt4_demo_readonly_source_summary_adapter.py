from __future__ import annotations

import copy
from pathlib import Path

import pytest

from app.services import mt4_demo_readonly_source_summary_adapter as adapter
from app.services.mt4_demo_readonly_schema_validator import (
    ACCOUNT_SNAPSHOT_FILE,
    MARKET_SYMBOL_FILE,
    POSITIONS_ORDER_HISTORY_FILE,
)


FORBIDDEN_OUTPUT_KEYS = {
    "payload",
    "raw_payload",
    "suggested_lot",
    "final_lot",
    "buy",
    "sell",
    "open",
    "close",
    "ea_command",
    "trade_signal",
    "trading_action",
    "trade_plan",
    "can_trade",
    "allow_trade",
    "should_buy",
    "should_sell",
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


def _valid_payloads() -> dict[str, dict[str, object]]:
    return {
        ACCOUNT_SNAPSHOT_FILE: _valid_account_snapshot_payload(),
        POSITIONS_ORDER_HISTORY_FILE: _valid_positions_order_history_payload(),
        MARKET_SYMBOL_FILE: _valid_market_symbol_payload(),
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


def _assert_component_safety_fields(component_status: dict[str, object]) -> None:
    assert component_status["read_only"] is True
    assert component_status["demo_only"] is True
    assert component_status["is_tradable"] is False
    assert component_status["can_execute"] is False


def _assert_no_forbidden_output_keys(result: dict[str, object]) -> None:
    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(result)
    for component_status in result["component_statuses"]:
        assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(component_status)
    for validation_status in result["validation_statuses"]:
        assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(validation_status)


def _assert_blocked(result: dict[str, object]) -> None:
    assert result["passed"] is False
    assert result["status_code"] != adapter.MT4_DEMO_READONLY_SOURCE_SUMMARY_READY
    assert result["block_reasons"]
    _assert_safety_fields(result)
    _assert_no_forbidden_output_keys(result)


def test_get_required_mt4_demo_readonly_source_filenames_returns_three_files() -> None:
    assert adapter.get_required_mt4_demo_readonly_source_filenames() == (
        ACCOUNT_SNAPSHOT_FILE,
        POSITIONS_ORDER_HISTORY_FILE,
        MARKET_SYMBOL_FILE,
    )


def test_valid_three_payloads_return_ready_summary() -> None:
    result = adapter.build_mt4_demo_readonly_source_summary(_valid_payloads())

    assert result["passed"] is True
    assert result["status_code"] == adapter.MT4_DEMO_READONLY_SOURCE_SUMMARY_READY
    assert result["source_mode"] == "mt4_demo_readonly_file_bridge_enabled"
    assert result["source_scope"] == "mt4_demo_readonly_validated_payloads_only"
    assert result["summary_version"] == "1.0"
    assert result["missing_components"] == []
    assert result["unexpected_components"] == []
    assert result["block_reasons"] == []
    assert result["warning_reasons"] == []
    assert len(result["component_statuses"]) == 3
    assert len(result["validation_statuses"]) == 3
    _assert_safety_fields(result)
    _assert_no_forbidden_output_keys(result)


def test_ready_summary_keeps_component_names_and_safe_summaries() -> None:
    result = adapter.build_mt4_demo_readonly_source_summary(_valid_payloads())

    component_names = {
        status["component_name"] for status in result["component_statuses"]
    }
    assert component_names == {
        "account_snapshot",
        "positions_order_history",
        "market_symbol",
    }
    for component_status in result["component_statuses"]:
        assert component_status["passed"] is True
        assert "schema validation passed" in component_status["safe_summary"]
        assert "raw" not in component_status["safe_summary"].lower()
        _assert_component_safety_fields(component_status)


def test_payloads_by_filename_not_dict_is_blocked() -> None:
    result = adapter.build_mt4_demo_readonly_source_summary(["not", "a", "dict"])

    _assert_blocked(result)
    assert (
        result["status_code"]
        == adapter.MT4_DEMO_READONLY_SOURCE_SUMMARY_INPUT_INVALID
    )
    assert result["missing_components"] == [
        ACCOUNT_SNAPSHOT_FILE,
        POSITIONS_ORDER_HISTORY_FILE,
        MARKET_SYMBOL_FILE,
    ]


@pytest.mark.parametrize(
    "missing_filename",
    [ACCOUNT_SNAPSHOT_FILE, POSITIONS_ORDER_HISTORY_FILE, MARKET_SYMBOL_FILE],
)
def test_missing_required_component_is_blocked(missing_filename: str) -> None:
    payloads = _valid_payloads()
    payloads.pop(missing_filename)

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    _assert_blocked(result)
    assert (
        result["status_code"]
        == adapter.MT4_DEMO_READONLY_SOURCE_SUMMARY_MISSING_COMPONENTS
    )
    assert result["missing_components"] == [missing_filename]


def test_unexpected_filename_is_blocked() -> None:
    payloads = _valid_payloads()
    payloads["extra.json"] = _valid_account_snapshot_payload()

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    _assert_blocked(result)
    assert (
        result["status_code"]
        == adapter.MT4_DEMO_READONLY_SOURCE_SUMMARY_UNEXPECTED_COMPONENTS
    )
    assert result["unexpected_components"] == ["extra.json"]


def test_forbidden_filename_is_blocked_without_leaking_path_text() -> None:
    payloads = _valid_payloads()
    payloads["../secret/account_snapshot.json"] = _valid_account_snapshot_payload()

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    _assert_blocked(result)
    assert result["unexpected_components"] == ["<rejected_filename>"]
    assert "../secret" not in str(result)


@pytest.mark.parametrize(
    ("filename", "field_name", "replacement"),
    [
        (ACCOUNT_SNAPSHOT_FILE, "equity", "not a number"),
        (POSITIONS_ORDER_HISTORY_FILE, "open_positions", "not a list"),
        (MARKET_SYMBOL_FILE, "ask", "not a number"),
    ],
)
def test_component_validation_failure_blocks_summary(
    filename: str,
    field_name: str,
    replacement: object,
) -> None:
    payloads = _valid_payloads()
    payloads[filename][field_name] = replacement

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    _assert_blocked(result)
    assert (
        result["status_code"]
        == adapter.MT4_DEMO_READONLY_SOURCE_SUMMARY_VALIDATION_FAILED
    )
    assert any(
        status["filename"] == filename and status["passed"] is False
        for status in result["validation_statuses"]
    )


@pytest.mark.parametrize(
    ("filename", "field_name", "replacement"),
    [
        (ACCOUNT_SNAPSHOT_FILE, "password", "SUPER_SECRET_PASSWORD"),
        (POSITIONS_ORDER_HISTORY_FILE, "ticket", "RAW_TICKET_12345"),
        (MARKET_SYMBOL_FILE, "buy_now", "EXECUTE_BUY_NOW"),
    ],
)
def test_forbidden_payload_fields_block_summary_without_leaking_values(
    filename: str,
    field_name: str,
    replacement: object,
) -> None:
    payloads = _valid_payloads()
    payloads[filename][field_name] = replacement

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    _assert_blocked(result)
    assert (
        result["status_code"]
        == adapter.MT4_DEMO_READONLY_SOURCE_SUMMARY_SAFETY_BLOCKED
    )
    assert str(replacement) not in str(result)
    assert any("forbidden field detected" in reason for reason in result["block_reasons"])


def test_nested_forbidden_payload_field_blocks_summary_without_leaking_value() -> None:
    payloads = _valid_payloads()
    payloads[POSITIONS_ORDER_HISTORY_FILE]["open_positions"][0][
        "order_id"
    ] = "RAW_ORDER_ID_999"

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    _assert_blocked(result)
    assert "RAW_ORDER_ID_999" not in str(result)
    assert "open_positions.order_id" in str(result["validation_statuses"])


def test_unknown_field_blocks_summary() -> None:
    payloads = _valid_payloads()
    payloads[MARKET_SYMBOL_FILE]["unknown_extra_field"] = "not allowed"

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    _assert_blocked(result)
    assert "unknown_extra_field" in str(result["validation_statuses"])
    assert "not allowed" not in str(result)


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("read_only", False),
        ("demo_only", False),
        ("can_execute", True),
        ("is_tradable", True),
        ("is_trading_permission", True),
        ("is_execution_instruction", True),
        ("allowed_to_call_ea", True),
        ("allowed_to_modify_risk", True),
    ],
)
def test_safety_flag_violations_block_summary(
    field_name: str,
    replacement: bool,
) -> None:
    payloads = _valid_payloads()
    payloads[ACCOUNT_SNAPSHOT_FILE][field_name] = replacement

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    _assert_blocked(result)
    assert (
        result["status_code"]
        == adapter.MT4_DEMO_READONLY_SOURCE_SUMMARY_SAFETY_BLOCKED
    )
    _assert_safety_fields(result)


def test_ready_summary_safety_fields_remain_strictly_readonly() -> None:
    result = adapter.build_mt4_demo_readonly_source_summary(_valid_payloads())

    _assert_safety_fields(result)
    for component_status in result["component_statuses"]:
        _assert_component_safety_fields(component_status)
    assert result["next_allowed_stage"] != "trading_permission"
    assert "trading_remain_blocked" in result["next_blocked_stage"]


def test_validation_statuses_do_not_include_raw_payload_or_values() -> None:
    payloads = _valid_payloads()
    payloads[ACCOUNT_SNAPSHOT_FILE]["password"] = "DO_NOT_LEAK_PASSWORD"
    payloads[MARKET_SYMBOL_FILE]["token"] = "DO_NOT_LEAK_TOKEN"
    payloads[POSITIONS_ORDER_HISTORY_FILE]["pending_orders_summary"][
        "secret"
    ] = "DO_NOT_LEAK_SECRET"

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    assert "DO_NOT_LEAK_PASSWORD" not in str(result)
    assert "DO_NOT_LEAK_TOKEN" not in str(result)
    assert "DO_NOT_LEAK_SECRET" not in str(result)
    assert "raw_payload" not in result
    _assert_no_forbidden_output_keys(result)


def test_output_does_not_leak_account_number_ticket_order_id_values() -> None:
    payloads = _valid_payloads()
    payloads[ACCOUNT_SNAPSHOT_FILE]["account_number"] = "123456789"
    payloads[POSITIONS_ORDER_HISTORY_FILE]["open_positions"][0][
        "ticket"
    ] = "ticket-raw-123"
    payloads[POSITIONS_ORDER_HISTORY_FILE]["recent_closed_orders"][0][
        "order_id"
    ] = "order-raw-456"

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    assert "123456789" not in str(result)
    assert "ticket-raw-123" not in str(result)
    assert "order-raw-456" not in str(result)


def test_output_does_not_leak_trade_instruction_values() -> None:
    payloads = _valid_payloads()
    payloads[MARKET_SYMBOL_FILE]["suggested_lot"] = "LOT_VALUE_SHOULD_NOT_LEAK"
    payloads[MARKET_SYMBOL_FILE]["final_lot"] = "FINAL_LOT_SHOULD_NOT_LEAK"
    payloads[MARKET_SYMBOL_FILE]["trade_signal"] = "BUY_SIGNAL_SHOULD_NOT_LEAK"
    payloads[MARKET_SYMBOL_FILE]["trading_action"] = "OPEN_NOW_SHOULD_NOT_LEAK"
    payloads[MARKET_SYMBOL_FILE]["ea_command"] = "EA_COMMAND_SHOULD_NOT_LEAK"

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    result_text = str(result)
    assert "LOT_VALUE_SHOULD_NOT_LEAK" not in result_text
    assert "FINAL_LOT_SHOULD_NOT_LEAK" not in result_text
    assert "BUY_SIGNAL_SHOULD_NOT_LEAK" not in result_text
    assert "OPEN_NOW_SHOULD_NOT_LEAK" not in result_text
    assert "EA_COMMAND_SHOULD_NOT_LEAK" not in result_text


def test_adapter_does_not_call_filesystem_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    result = adapter.build_mt4_demo_readonly_source_summary(_valid_payloads())

    assert result["passed"] is True


def test_adapter_calls_schema_validator_for_each_required_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_validate(filename: object, _payload: object) -> dict[str, object]:
        calls.append(str(filename))
        return {
            "passed": True,
            "status_code": "MT4_DEMO_READONLY_SCHEMA_VALID",
            "reason_codes": [],
            "missing_fields": [],
            "invalid_fields": [],
            "blocked_fields": [],
        }

    monkeypatch.setattr(
        adapter.schema_validator,
        "validate_mt4_demo_readonly_payload",
        fake_validate,
    )

    result = adapter.build_mt4_demo_readonly_source_summary(_valid_payloads())

    assert result["passed"] is True
    assert calls == [
        ACCOUNT_SNAPSHOT_FILE,
        POSITIONS_ORDER_HISTORY_FILE,
        MARKET_SYMBOL_FILE,
    ]


def test_filename_whitelist_is_checked_for_all_input_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    original_validate = adapter.path_guard.validate_mt4_demo_readonly_filename

    def tracking_validate(filename: object) -> dict[str, object]:
        calls.append(filename)
        return original_validate(filename)

    monkeypatch.setattr(
        adapter.path_guard,
        "validate_mt4_demo_readonly_filename",
        tracking_validate,
    )

    payloads = _valid_payloads()
    payloads["extra.json"] = _valid_account_snapshot_payload()
    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    _assert_blocked(result)
    assert calls == [
        ACCOUNT_SNAPSHOT_FILE,
        POSITIONS_ORDER_HISTORY_FILE,
        MARKET_SYMBOL_FILE,
        "extra.json",
    ]


def test_source_mode_notes_do_not_claim_api_dashboard_or_trading_enabled() -> None:
    result = adapter.build_mt4_demo_readonly_source_summary(_valid_payloads())

    assert result["source_scope"] == "mt4_demo_readonly_validated_payloads_only"
    joined_notes = " ".join(result["notes"])
    assert "does not enable API source mode" in joined_notes
    assert "Dashboard integration" in joined_notes
    assert "trading permission" in joined_notes


def test_adapter_does_not_mutate_input_payloads() -> None:
    payloads = _valid_payloads()
    original = copy.deepcopy(payloads)

    result = adapter.build_mt4_demo_readonly_source_summary(payloads)

    assert result["passed"] is True
    assert payloads == original
