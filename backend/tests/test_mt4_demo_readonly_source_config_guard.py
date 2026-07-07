from __future__ import annotations

from pathlib import Path

import pytest

from app.services import mt4_demo_readonly_reader
from app.services import mt4_demo_readonly_source_config_guard as guard


SAFE_BRIDGE_DIR = "mt4_demo_readonly_bridge"

FORBIDDEN_OUTPUT_KEYS = {
    "account_number",
    "allow_trade",
    "api_key",
    "base_dir",
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
    "raw_payload",
    "real_account",
    "secret",
    "sell",
    "sell_now",
    "should_buy",
    "should_sell",
    "suggested_lot",
    "system_path",
    "ticket",
    "token",
    "traceback",
    "trade_plan",
    "trade_signal",
    "trading_action",
}


def _validate(config: object) -> dict[str, object]:
    return guard.validate_demo_readonly_source_config(config)


def _assert_safety_fields(result: dict[str, object]) -> None:
    assert result["read_only"] is True
    assert result["demo_only"] is True
    assert result["is_tradable"] is False
    assert result["can_execute"] is False
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["allowed_to_call_ea"] is False
    assert result["allowed_to_modify_risk"] is False


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


def _assert_no_forbidden_output_keys(result: dict[str, object]) -> None:
    assert not _contains_forbidden_key_recursive(result)


def _assert_no_raw_config_leak(result: dict[str, object], raw_value: object) -> None:
    if isinstance(raw_value, str) and raw_value:
        assert raw_value not in str(result)


def _assert_common_output_shape(result: dict[str, object]) -> None:
    assert "passed" in result
    assert "status_code" in result
    assert "selected_source_mode" in result
    assert "default_source_mode" in result
    assert "source_status" in result
    assert "bridge_dir_status" in result
    assert "request_override_allowed" in result
    assert "block_reasons" in result
    assert "warning_reasons" in result
    assert "notes" in result
    assert result["request_override_allowed"] is False
    assert result["default_source_mode"] == "docs_fixture_only"
    _assert_safety_fields(result)
    _assert_no_forbidden_output_keys(result)


def _assert_blocked(result: dict[str, object]) -> None:
    assert result["passed"] is False
    assert result["block_reasons"]
    _assert_common_output_shape(result)


def _safe_mt4_config(bridge_dir: object = SAFE_BRIDGE_DIR) -> dict[str, object]:
    return {
        "source_mode": "mt4_demo_readonly_file_bridge_enabled",
        "mt4_demo_readonly_file_bridge_enabled": True,
        "mt4_demo_readonly_bridge_dir": bridge_dir,
    }


def test_default_source_mode_function_returns_docs_fixture_only() -> None:
    assert guard.get_demo_readonly_default_source_mode() == "docs_fixture_only"


def test_allowed_source_modes_are_docs_fixture_and_mt4_demo_readonly_only() -> None:
    assert guard.get_demo_readonly_allowed_source_modes() == (
        "docs_fixture_only",
        "mt4_demo_readonly_file_bridge_enabled",
    )


def test_empty_config_returns_docs_fixture_only_ready() -> None:
    result = _validate({})

    assert result["passed"] is True
    assert (
        result["status_code"]
        == guard.MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY
    )
    assert result["selected_source_mode"] == "docs_fixture_only"
    assert result["source_status"] == "docs_fixture_only_ready"
    assert result["bridge_dir_status"] == "not_required"
    _assert_common_output_shape(result)


def test_none_config_safely_defaults_to_docs_fixture_only() -> None:
    result = _validate(None)

    assert result["passed"] is True
    assert result["selected_source_mode"] == "docs_fixture_only"
    assert "CONFIG_MISSING_DEFAULTED_TO_DOCS_FIXTURE_ONLY" in result["warning_reasons"]
    _assert_common_output_shape(result)


@pytest.mark.parametrize("config", ["docs_fixture_only", 123, [], object()])
def test_non_dict_config_is_blocked(config: object) -> None:
    result = _validate(config)

    _assert_blocked(result)
    assert (
        result["status_code"]
        == guard.MT4_DEMO_READONLY_SOURCE_CONFIG_INPUT_INVALID
    )
    assert result["selected_source_mode"] == "docs_fixture_only"


def test_missing_source_mode_defaults_to_docs_fixture_only() -> None:
    result = _validate({"mt4_demo_readonly_file_bridge_enabled": False})

    assert result["passed"] is True
    assert result["selected_source_mode"] == "docs_fixture_only"
    assert result["bridge_dir_status"] == "not_required"
    _assert_common_output_shape(result)


def test_explicit_docs_fixture_only_source_mode_passes() -> None:
    result = _validate({"source_mode": "docs_fixture_only"})

    assert result["passed"] is True
    assert result["selected_source_mode"] == "docs_fixture_only"
    assert result["source_status"] == "docs_fixture_only_ready"
    _assert_common_output_shape(result)


def test_mt4_demo_readonly_source_mode_requires_explicit_enable() -> None:
    result = _validate({"source_mode": "mt4_demo_readonly_file_bridge_enabled"})

    _assert_blocked(result)
    assert (
        result["status_code"] == guard.MT4_DEMO_READONLY_SOURCE_CONFIG_BLOCKED
    )
    assert result["selected_source_mode"] == "mt4_demo_readonly_file_bridge_enabled"
    assert "MT4_DEMO_READONLY_FILE_BRIDGE_DISABLED" in result["block_reasons"]


def test_mt4_demo_readonly_source_mode_requires_bridge_dir() -> None:
    result = _validate(
        {
            "source_mode": "mt4_demo_readonly_file_bridge_enabled",
            "mt4_demo_readonly_file_bridge_enabled": True,
        }
    )

    _assert_blocked(result)
    assert result["status_code"] == guard.MT4_DEMO_READONLY_BRIDGE_DIR_REJECTED
    assert result["bridge_dir_status"] == "rejected"
    assert "BRIDGE_DIR_INPUT_NOT_STR" in result["block_reasons"]


def test_mt4_demo_readonly_source_mode_with_safe_bridge_dir_passes() -> None:
    result = _validate(_safe_mt4_config())

    assert result["passed"] is True
    assert result["status_code"] == guard.MT4_DEMO_READONLY_SOURCE_CONFIG_READY
    assert result["selected_source_mode"] == "mt4_demo_readonly_file_bridge_enabled"
    assert result["source_status"] == "mt4_demo_readonly_file_bridge_ready"
    assert result["bridge_dir_status"] == "safe_configured"
    assert SAFE_BRIDGE_DIR not in str(result)
    _assert_common_output_shape(result)


@pytest.mark.parametrize(
    "source_mode",
    [
        "unknown_source",
        "mt4_live_readonly",
        "mt4_live_execution",
        "mt4_demo_execution",
        "raw_terminal_export",
        "unknown_live_source",
        "any_execution_source",
        "live",
        "execution",
        "auto_trade",
        "order_execution",
        "real_account",
        "demo_execution",
    ],
)
def test_forbidden_or_unknown_source_modes_are_blocked(source_mode: str) -> None:
    result = _validate({"source_mode": source_mode})

    _assert_blocked(result)
    assert result["status_code"] == guard.MT4_DEMO_READONLY_SOURCE_MODE_REJECTED
    assert result["selected_source_mode"] == "docs_fixture_only"
    assert result["selected_source_mode"] != source_mode
    assert source_mode not in result["block_reasons"]
    assert source_mode not in result["warning_reasons"]
    assert source_mode not in result["notes"]


@pytest.mark.parametrize("source_mode", ["", "   ", 123, None])
def test_invalid_source_mode_values_are_blocked(source_mode: object) -> None:
    result = _validate({"source_mode": source_mode})

    _assert_blocked(result)
    assert result["status_code"] == guard.MT4_DEMO_READONLY_SOURCE_MODE_REJECTED
    assert result["selected_source_mode"] == "docs_fixture_only"


@pytest.mark.parametrize("override_value", [True, "true", 1])
def test_request_override_is_rejected(override_value: object) -> None:
    result = _validate({"allow_request_override": override_value})

    _assert_blocked(result)
    assert (
        result["status_code"] == guard.MT4_DEMO_READONLY_REQUEST_OVERRIDE_REJECTED
    )
    assert "REQUEST_OVERRIDE_REJECTED" in result["block_reasons"]


def test_unexpected_config_fields_are_blocked_without_value_leak() -> None:
    result = _validate({"password": "PASSWORD_SHOULD_NOT_LEAK"})

    _assert_blocked(result)
    assert (
        result["status_code"]
        == guard.MT4_DEMO_READONLY_SOURCE_CONFIG_SAFETY_BLOCKED
    )
    assert "PASSWORD_SHOULD_NOT_LEAK" not in str(result)


@pytest.mark.parametrize("bridge_dir", [123, None, [], object()])
def test_bridge_dir_must_be_string(bridge_dir: object) -> None:
    result = _validate(_safe_mt4_config(bridge_dir))

    _assert_blocked(result)
    assert result["status_code"] == guard.MT4_DEMO_READONLY_BRIDGE_DIR_REJECTED
    assert "BRIDGE_DIR_INPUT_NOT_STR" in result["block_reasons"]


@pytest.mark.parametrize(
    ("bridge_dir", "reason_code"),
    [
        ("", "BRIDGE_DIR_EMPTY"),
        ("   ", "BRIDGE_DIR_EMPTY"),
        (" safe_bridge", "BRIDGE_DIR_HAS_SURROUNDING_WHITESPACE"),
        ("safe_bridge ", "BRIDGE_DIR_HAS_SURROUNDING_WHITESPACE"),
        ("safe\x00bridge", "BRIDGE_DIR_CONTAINS_NUL"),
        ("../bridge", "BRIDGE_DIR_CONTAINS_PATH_TRAVERSAL"),
        (r"..\bridge", "BRIDGE_DIR_CONTAINS_PATH_TRAVERSAL"),
        ("bridge/../secret", "BRIDGE_DIR_CONTAINS_PATH_TRAVERSAL"),
        (".env", "BRIDGE_DIR_POINTS_TO_ENV"),
        ("safe/.env", "BRIDGE_DIR_POINTS_TO_ENV"),
        ("logs/bridge", "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"),
        ("log/bridge", "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"),
        ("database/bridge", "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"),
        ("db/bridge", "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"),
        ("cache/bridge", "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"),
        ("data/mt4", "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"),
        ("Desktop/bridge", "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"),
        ("Downloads/bridge", "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"),
        ("Documents/bridge", "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"),
        ("mt4_password_bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
        ("mt4/token/bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
        ("secret_bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
        ("credential_bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
        ("login_bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
        ("live_account_bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
        ("real_account_bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
        ("execution_bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
        ("order_send_bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
        ("trade_plan_bridge", "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"),
    ],
)
def test_unsafe_bridge_dir_values_are_blocked_without_raw_value_leak(
    bridge_dir: str,
    reason_code: str,
) -> None:
    result = _validate(_safe_mt4_config(bridge_dir))

    _assert_blocked(result)
    assert result["status_code"] == guard.MT4_DEMO_READONLY_BRIDGE_DIR_REJECTED
    assert reason_code in result["block_reasons"]
    _assert_no_raw_config_leak(result, bridge_dir)


def test_output_does_not_return_bridge_dir_base_dir_candidate_path_or_system_path() -> None:
    result = _validate(_safe_mt4_config())

    assert "mt4_demo_readonly_bridge" not in str(result)
    assert "base_dir" not in result
    assert "candidate_path" not in result
    assert "system_path" not in result
    _assert_common_output_shape(result)


def test_output_does_not_return_sensitive_trading_or_execution_values() -> None:
    result = _validate(
        _safe_mt4_config("password_token_secret_login_live_account_execution")
    )

    _assert_blocked(result)
    result_text = str(result)
    for fragment in [
        "password_token_secret_login_live_account_execution",
        "PASSWORD_SHOULD_NOT_LEAK",
        "TOKEN_SHOULD_NOT_LEAK",
        "SECRET_SHOULD_NOT_LEAK",
        "suggested_lot",
        "final_lot",
        "buy_now",
        "sell_now",
        "order_send",
        "trade_plan",
    ]:
        assert fragment not in result_text


def test_safety_flags_stay_safe_even_when_config_attempts_to_override_them() -> None:
    result = _validate({"read_only": False, "can_execute": True})

    _assert_blocked(result)
    _assert_safety_fields(result)
    assert "read_only" in result
    assert "can_execute" in result


def test_source_mode_ready_is_not_trading_permission() -> None:
    result = _validate(_safe_mt4_config())

    assert result["passed"] is True
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["can_execute"] is False
    assert "source_mode readiness is not a trading permission" in result["notes"]


def test_guard_does_not_touch_env_files_network_reader_or_path_scanning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("source config guard must not touch external state")

    class FailingEnviron(dict[str, str]):
        def __getitem__(self, key: str) -> str:
            raise AssertionError(f"os.environ read is not allowed: {key}")

        def get(self, key: str, default: object = None) -> object:
            raise AssertionError(f"os.environ.get is not allowed: {key}")

    monkeypatch.setattr("builtins.open", fail_if_called)
    monkeypatch.setattr("os.getenv", fail_if_called)
    monkeypatch.setattr("os.environ", FailingEnviron())
    monkeypatch.setattr("glob.glob", fail_if_called)
    monkeypatch.setattr("os.walk", fail_if_called)
    monkeypatch.setattr("socket.create_connection", fail_if_called)
    monkeypatch.setattr(Path, "exists", fail_if_called)
    monkeypatch.setattr(Path, "is_file", fail_if_called)
    monkeypatch.setattr(Path, "iterdir", fail_if_called)
    monkeypatch.setattr(Path, "read_text", fail_if_called)
    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(
        mt4_demo_readonly_reader,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fail_if_called,
    )

    result = _validate(_safe_mt4_config())

    assert result["passed"] is True
    _assert_common_output_shape(result)
