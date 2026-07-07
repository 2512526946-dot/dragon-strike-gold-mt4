from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.services import mt4_demo_readonly_reader as reader
from app.services.mt4_demo_readonly_schema_validator import (
    ACCOUNT_SNAPSHOT_FILE,
    MARKET_SYMBOL_FILE,
    POSITIONS_ORDER_HISTORY_FILE,
)


FORBIDDEN_OUTPUT_KEYS = {
    "account_number",
    "allow_trade",
    "api_key",
    "buy",
    "buy_now",
    "candidate_path",
    "can_trade",
    "close",
    "close_position",
    "credential",
    "ea_command",
    "execute_trade",
    "final_lot",
    "login",
    "open",
    "open_position",
    "order_close",
    "order_delete",
    "order_id",
    "order_modify",
    "order_send",
    "password",
    "payload",
    "raw_account_snapshot",
    "raw_market_symbol",
    "raw_payload",
    "raw_positions_order_history",
    "secret",
    "sell",
    "sell_now",
    "should_buy",
    "should_sell",
    "stack_trace",
    "suggested_lot",
    "system_path",
    "ticket",
    "token",
    "traceback",
    "trade_plan",
    "trade_signal",
    "trading_action",
}

REQUIRED_FILENAMES = (
    ACCOUNT_SNAPSHOT_FILE,
    POSITIONS_ORDER_HISTORY_FILE,
    MARKET_SYMBOL_FILE,
)


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


def _write_payloads(base_dir: Path, payloads: dict[str, object] | None = None) -> None:
    selected_payloads = payloads or _valid_payloads()
    base_dir.mkdir(exist_ok=True)
    for filename, payload in selected_payloads.items():
        (base_dir / filename).write_text(
            json.dumps(payload),
            encoding="utf-8",
        )


def _read(base_dir: object) -> dict[str, object]:
    return reader.read_mt4_demo_readonly_source_summary_from_dir(base_dir)


def _assert_safety_fields(result: dict[str, object]) -> None:
    assert result["read_only"] is True
    assert result["demo_only"] is True
    assert result["is_tradable"] is False
    assert result["can_execute"] is False
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["allowed_to_call_ea"] is False
    assert result["allowed_to_modify_risk"] is False


def _assert_no_forbidden_output_keys(result: dict[str, object]) -> None:
    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(result)
    assert not _contains_forbidden_key_recursive(result)


def _contains_forbidden_key_recursive(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key in FORBIDDEN_OUTPUT_KEYS or _contains_forbidden_key_recursive(child)
            for key, child in value.items()
            if isinstance(key, str)
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key_recursive(item) for item in value)
    return False


def _assert_no_forbidden_text(result: dict[str, object]) -> None:
    result_text = str(result)
    forbidden_fragments = [
        "PASSWORD_SHOULD_NOT_LEAK",
        "TOKEN_SHOULD_NOT_LEAK",
        "SECRET_SHOULD_NOT_LEAK",
        "LOGIN_SHOULD_NOT_LEAK",
        "ACCOUNT_NUMBER_SHOULD_NOT_LEAK",
        "TICKET_SHOULD_NOT_LEAK",
        "ORDER_ID_SHOULD_NOT_LEAK",
        "LOT_SHOULD_NOT_LEAK",
        "BUY_NOW_SHOULD_NOT_LEAK",
        "SELL_NOW_SHOULD_NOT_LEAK",
        "EA_COMMAND_SHOULD_NOT_LEAK",
        "DO_NOT_LEAK_EXCEPTION",
        "C:\\Users\\86135",
        "/home/user",
        "Traceback",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in result_text


def _assert_blocked(result: dict[str, object]) -> None:
    assert result["passed"] is False
    assert result["status_code"] != reader.MT4_DEMO_READONLY_READER_READY
    assert result["reader_status"] == "blocked"
    assert result["reader_block_reasons"]
    _assert_safety_fields(result)
    _assert_no_forbidden_output_keys(result)
    _assert_no_forbidden_text(result)


def test_required_filenames_are_three_whitelisted_json_files() -> None:
    assert reader.get_mt4_demo_readonly_reader_required_filenames() == REQUIRED_FILENAMES


def test_valid_three_json_files_return_ready(tmp_path: Path) -> None:
    _write_payloads(tmp_path)

    result = _read(str(tmp_path))

    assert result["passed"] is True
    assert result["status_code"] == reader.MT4_DEMO_READONLY_READER_READY
    assert result["reader_status"] == "ready"
    assert result["reader_block_reasons"] == []
    assert result["missing_components"] == []
    assert result["unexpected_components"] == []
    assert len(result["component_statuses"]) == 3
    assert len(result["validation_statuses"]) == 3
    _assert_safety_fields(result)
    _assert_no_forbidden_output_keys(result)


def test_reader_only_opens_three_whitelisted_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_payloads(tmp_path)
    opened_filenames: list[str] = []
    original_open = Path.open

    def tracking_open(self: Path, *args: object, **kwargs: object) -> object:
        opened_filenames.append(self.name)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracking_open)

    result = _read(str(tmp_path))

    assert result["passed"] is True
    assert opened_filenames == list(REQUIRED_FILENAMES)


@pytest.mark.parametrize(
    "base_dir",
    [
        None,
        123,
        "",
        "   ",
        "demo\x00readonly",
        "../demo-readonly",
        r"..\demo-readonly",
        ".env",
        "logs",
        "database",
        "cache",
        "data",
        "Desktop",
        "Downloads",
        "Documents",
        "account_snapshot.json",
        "payload",
    ],
)
def test_invalid_base_dir_is_blocked(base_dir: object) -> None:
    result = _read(base_dir)

    _assert_blocked(result)
    assert result["status_code"] in {
        reader.MT4_DEMO_READONLY_READER_INPUT_INVALID,
        reader.MT4_DEMO_READONLY_READER_BASE_DIR_REJECTED,
    }


@pytest.mark.parametrize("missing_filename", REQUIRED_FILENAMES)
def test_missing_file_is_blocked(tmp_path: Path, missing_filename: str) -> None:
    _write_payloads(tmp_path)
    (tmp_path / missing_filename).unlink()

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert result["status_code"] == reader.MT4_DEMO_READONLY_READER_FILE_MISSING
    assert result["missing_components"] == [missing_filename]
    assert str(tmp_path) not in str(result)


@pytest.mark.parametrize("invalid_filename", REQUIRED_FILENAMES)
def test_invalid_json_is_blocked(tmp_path: Path, invalid_filename: str) -> None:
    _write_payloads(tmp_path)
    (tmp_path / invalid_filename).write_text("{not valid json", encoding="utf-8")

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert result["status_code"] == reader.MT4_DEMO_READONLY_READER_JSON_INVALID
    assert "{not valid json" not in str(result)


@pytest.mark.parametrize("payload", [[], "not an object", 123])
def test_json_must_be_object(tmp_path: Path, payload: object) -> None:
    _write_payloads(tmp_path)
    (tmp_path / ACCOUNT_SNAPSHOT_FILE).write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert result["status_code"] == reader.MT4_DEMO_READONLY_READER_JSON_NOT_OBJECT


def test_unreadable_file_is_blocked_without_path_leak(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_payloads(tmp_path)

    original_open = Path.open

    def tracking_open(self: Path, *args: object, **kwargs: object) -> object:
        if self.name == ACCOUNT_SNAPSHOT_FILE:
            raise OSError("DO_NOT_LEAK_EXCEPTION C:\\Users\\86135\\secret.py")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracking_open)

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert result["status_code"] == reader.MT4_DEMO_READONLY_READER_FILE_UNREADABLE


def test_reader_exception_is_safely_blocked_without_exception_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_payloads(tmp_path)

    def exploding_open(self: Path, *_args: object, **_kwargs: object) -> object:
        raise RuntimeError("DO_NOT_LEAK_EXCEPTION C:\\Users\\86135\\secret.py Traceback")

    monkeypatch.setattr(Path, "open", exploding_open)

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert result["status_code"] == reader.MT4_DEMO_READONLY_READER_SAFETY_BLOCKED


def test_schema_validation_failure_blocks_reader(tmp_path: Path) -> None:
    payloads = _valid_payloads()
    payloads[ACCOUNT_SNAPSHOT_FILE].pop("equity")
    _write_payloads(tmp_path, payloads)

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert (
        result["status_code"]
        == reader.MT4_DEMO_READONLY_READER_SOURCE_SUMMARY_BLOCKED
    )
    assert "SOURCE_SUMMARY_BLOCKED" in result["reader_block_reasons"]


def test_source_summary_blocked_blocks_reader(tmp_path: Path) -> None:
    payloads = _valid_payloads()
    payloads[MARKET_SYMBOL_FILE]["read_only"] = False
    _write_payloads(tmp_path, payloads)

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert (
        result["status_code"]
        == reader.MT4_DEMO_READONLY_READER_SOURCE_SUMMARY_BLOCKED
    )


@pytest.mark.parametrize(
    ("filename", "field_name", "secret_value"),
    [
        (ACCOUNT_SNAPSHOT_FILE, "password", "PASSWORD_SHOULD_NOT_LEAK"),
        (ACCOUNT_SNAPSHOT_FILE, "token", "TOKEN_SHOULD_NOT_LEAK"),
        (ACCOUNT_SNAPSHOT_FILE, "account_number", "ACCOUNT_NUMBER_SHOULD_NOT_LEAK"),
        (POSITIONS_ORDER_HISTORY_FILE, "ticket", "TICKET_SHOULD_NOT_LEAK"),
        (POSITIONS_ORDER_HISTORY_FILE, "order_id", "ORDER_ID_SHOULD_NOT_LEAK"),
        (MARKET_SYMBOL_FILE, "buy_now", "BUY_NOW_SHOULD_NOT_LEAK"),
        (MARKET_SYMBOL_FILE, "sell_now", "SELL_NOW_SHOULD_NOT_LEAK"),
        (MARKET_SYMBOL_FILE, "suggested_lot", "LOT_SHOULD_NOT_LEAK"),
        (MARKET_SYMBOL_FILE, "final_lot", "LOT_SHOULD_NOT_LEAK"),
        (MARKET_SYMBOL_FILE, "ea_command", "EA_COMMAND_SHOULD_NOT_LEAK"),
    ],
)
def test_forbidden_fields_are_blocked_without_value_leak(
    tmp_path: Path,
    filename: str,
    field_name: str,
    secret_value: str,
) -> None:
    payloads = _valid_payloads()
    payloads[filename][field_name] = secret_value
    _write_payloads(tmp_path, payloads)

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert (
        result["status_code"]
        == reader.MT4_DEMO_READONLY_READER_SOURCE_SUMMARY_BLOCKED
    )
    assert secret_value not in str(result)


def test_nested_forbidden_fields_are_blocked_without_value_leak(tmp_path: Path) -> None:
    payloads = _valid_payloads()
    payloads[POSITIONS_ORDER_HISTORY_FILE]["open_positions"][0][
        "ticket"
    ] = "TICKET_SHOULD_NOT_LEAK"
    payloads[POSITIONS_ORDER_HISTORY_FILE]["recent_closed_orders"][0][
        "order_id"
    ] = "ORDER_ID_SHOULD_NOT_LEAK"
    _write_payloads(tmp_path, payloads)

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert "TICKET_SHOULD_NOT_LEAK" not in str(result)
    assert "ORDER_ID_SHOULD_NOT_LEAK" not in str(result)


def test_output_does_not_include_raw_payload_paths_or_execution_fields(
    tmp_path: Path,
) -> None:
    _write_payloads(tmp_path)

    result = _read(str(tmp_path))

    result_text = str(result)
    assert "raw_payload" not in result_text
    assert "candidate_path" not in result_text
    assert "system_path" not in result_text
    assert "traceback" not in result_text.lower()
    assert str(tmp_path) not in result_text
    _assert_no_forbidden_output_keys(result)


def test_reader_calls_source_summary_adapter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_payloads(tmp_path)
    calls: list[object] = []

    def fake_summary(payloads_by_filename: object) -> dict[str, object]:
        calls.append(payloads_by_filename)
        return {
            "passed": True,
            "status_code": "MT4_DEMO_READONLY_SOURCE_SUMMARY_READY",
            "source_mode": "mt4_demo_readonly_file_bridge_enabled",
            "source_scope": "mt4_demo_readonly_validated_payloads_only",
            "component_statuses": [],
            "validation_statuses": [],
            "missing_components": [],
            "unexpected_components": [],
            "block_reasons": [],
            "warning_reasons": [],
            "data_quality_notes": [],
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
            "is_trading_permission": False,
            "is_execution_instruction": False,
            "allowed_to_call_ea": False,
            "allowed_to_modify_risk": False,
        }

    monkeypatch.setattr(
        reader.source_summary_adapter,
        "build_mt4_demo_readonly_source_summary",
        fake_summary,
    )

    result = _read(str(tmp_path))

    assert result["passed"] is True
    assert len(calls) == 1
    assert set(calls[0]) == set(REQUIRED_FILENAMES)


def test_reader_blocks_unsafe_source_summary_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_payloads(tmp_path)

    def unsafe_summary(_payloads_by_filename: object) -> dict[str, object]:
        return {
            "passed": True,
            "raw_payload": {"password": "PASSWORD_SHOULD_NOT_LEAK"},
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
            "is_trading_permission": False,
            "is_execution_instruction": False,
            "allowed_to_call_ea": False,
            "allowed_to_modify_risk": False,
        }

    monkeypatch.setattr(
        reader.source_summary_adapter,
        "build_mt4_demo_readonly_source_summary",
        unsafe_summary,
    )

    result = _read(str(tmp_path))

    _assert_blocked(result)
    assert result["status_code"] == reader.MT4_DEMO_READONLY_READER_SAFETY_BLOCKED


def test_reader_calls_path_guard_for_each_required_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_payloads(tmp_path)
    calls: list[tuple[object, object]] = []
    original_build = reader.path_guard.build_mt4_demo_readonly_candidate_path

    def tracking_build(base_dir: object, filename: object) -> dict[str, object]:
        calls.append((base_dir, filename))
        return original_build(base_dir, filename)

    monkeypatch.setattr(
        reader.path_guard,
        "build_mt4_demo_readonly_candidate_path",
        tracking_build,
    )

    result = _read(str(tmp_path))

    assert result["passed"] is True
    assert [filename for _base_dir, filename in calls] == list(REQUIRED_FILENAMES)


def test_reader_does_not_glob_walk_iterdir_write_or_use_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_payloads(tmp_path)

    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("forbidden side effect")

    monkeypatch.setattr("glob.glob", fail_if_called)
    monkeypatch.setattr("os.walk", fail_if_called)
    monkeypatch.setattr("socket.create_connection", fail_if_called)
    monkeypatch.setattr(Path, "iterdir", fail_if_called)
    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "unlink", fail_if_called)
    monkeypatch.setattr(Path, "mkdir", fail_if_called)

    result = _read(str(tmp_path))

    assert result["passed"] is True


def test_reader_does_not_generate_trade_plan_or_execution_permission(
    tmp_path: Path,
) -> None:
    _write_payloads(tmp_path)

    result = _read(str(tmp_path))

    assert "trade_plan" not in str(result).lower()
    assert "suggested_lot" not in str(result).lower()
    assert "final_lot" not in str(result).lower()
    assert "ea_command" not in str(result).lower()
    _assert_safety_fields(result)
