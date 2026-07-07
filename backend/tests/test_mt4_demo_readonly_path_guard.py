from __future__ import annotations

from pathlib import Path

import pytest

from app.services.mt4_demo_readonly_path_guard import (
    MT4_DEMO_READONLY_FILENAME_ALLOWED,
    MT4_DEMO_READONLY_FILENAME_REJECTED,
    MT4_DEMO_READONLY_INPUT_INVALID,
    MT4_DEMO_READONLY_PATH_ALLOWED,
    MT4_DEMO_READONLY_PATH_REJECTED,
    build_mt4_demo_readonly_candidate_path,
    get_allowed_mt4_demo_readonly_filenames,
    is_allowed_mt4_demo_readonly_filename,
    validate_mt4_demo_readonly_filename,
)


ALLOWED_FILENAMES = (
    "account_snapshot.json",
    "positions_order_history.json",
    "market_symbol.json",
)

FORBIDDEN_FILENAMES = (
    "orders_to_send.json",
    "trade_plan.json",
    "execution_command.json",
    "ea_command.json",
    "risk_override.json",
    "position_sizing.json",
    "credentials.json",
    "login.json",
    "password.json",
    ".env",
    ".env.example",
    "account_snapshot.exe",
    "account_snapshot.json.exe",
    "account_snapshot.jsonl",
    "account_snapshot.txt",
    "../account_snapshot.json",
    r"..\account_snapshot.json",
    "/account_snapshot.json",
    r"C:\account_snapshot.json",
    "subdir/account_snapshot.json",
    r"subdir\account_snapshot.json",
)

FORBIDDEN_RESULT_FIELDS = {
    "suggested_lot",
    "final_lot",
    "buy",
    "sell",
    "open",
    "close",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
    "ea_command",
    "trade_signal",
    "trading_action",
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


def _assert_no_trading_or_execution_fields(result: dict[str, object]) -> None:
    assert FORBIDDEN_RESULT_FIELDS.isdisjoint(result)


def test_allowed_filename_tuple_contains_only_three_demo_readonly_files() -> None:
    assert get_allowed_mt4_demo_readonly_filenames() == ALLOWED_FILENAMES


@pytest.mark.parametrize("filename", ALLOWED_FILENAMES)
def test_allowed_filenames_pass(filename: str) -> None:
    result = validate_mt4_demo_readonly_filename(filename)

    assert is_allowed_mt4_demo_readonly_filename(filename) is True
    assert result["passed"] is True
    assert result["status_code"] == MT4_DEMO_READONLY_FILENAME_ALLOWED
    assert result["safe_filename"] == filename
    assert result["reason_code"] is None
    _assert_safety_fields(result)
    _assert_no_trading_or_execution_fields(result)


@pytest.mark.parametrize("filename", FORBIDDEN_FILENAMES)
def test_forbidden_filenames_are_rejected(filename: str) -> None:
    result = validate_mt4_demo_readonly_filename(filename)

    assert is_allowed_mt4_demo_readonly_filename(filename) is False
    assert result["passed"] is False
    assert result["status_code"] == MT4_DEMO_READONLY_FILENAME_REJECTED
    assert result["safe_filename"] is None
    assert result["reason_code"] is not None
    _assert_safety_fields(result)
    _assert_no_trading_or_execution_fields(result)


@pytest.mark.parametrize(
    "filename",
    [
        "../account_snapshot.json",
        r"..\account_snapshot.json",
        "safe..account_snapshot.json",
    ],
)
def test_path_traversal_is_rejected(filename: str) -> None:
    result = validate_mt4_demo_readonly_filename(filename)

    assert result["passed"] is False
    assert result["reason_code"] == "FILENAME_CONTAINS_PATH_TRAVERSAL"
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "filename",
    [
        "/account_snapshot.json",
        r"C:\account_snapshot.json",
        r"\\server\share\account_snapshot.json",
    ],
)
def test_absolute_paths_are_rejected(filename: str) -> None:
    result = validate_mt4_demo_readonly_filename(filename)

    assert result["passed"] is False
    assert result["reason_code"] == "FILENAME_IS_ABSOLUTE_PATH"
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "filename",
    [
        "subdir/account_snapshot.json",
        r"subdir\account_snapshot.json",
    ],
)
def test_path_separators_are_rejected(filename: str) -> None:
    result = validate_mt4_demo_readonly_filename(filename)

    assert result["passed"] is False
    assert result["reason_code"] == "FILENAME_CONTAINS_PATH_SEPARATOR"
    _assert_safety_fields(result)


@pytest.mark.parametrize("filename", [".env", ".env.example", ".hidden.json"])
def test_hidden_filenames_are_rejected(filename: str) -> None:
    result = validate_mt4_demo_readonly_filename(filename)

    assert result["passed"] is False
    assert result["reason_code"] == "FILENAME_IS_HIDDEN"
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "filename",
    [
        " account_snapshot.json",
        "account_snapshot.json ",
        "\taccount_snapshot.json",
    ],
)
def test_surrounding_whitespace_is_rejected(filename: str) -> None:
    result = validate_mt4_demo_readonly_filename(filename)

    assert result["passed"] is False
    assert result["reason_code"] == "FILENAME_HAS_SURROUNDING_WHITESPACE"
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "filename",
    [
        "Account_snapshot.json",
        "ACCOUNT_SNAPSHOT.JSON",
        "Market_Symbol.json",
    ],
)
def test_case_variants_are_rejected(filename: str) -> None:
    result = validate_mt4_demo_readonly_filename(filename)

    assert result["passed"] is False
    assert result["reason_code"] == "FILENAME_EXTENSION_NOT_ALLOWED" or result[
        "reason_code"
    ] == "FILENAME_NOT_IN_WHITELIST"
    _assert_safety_fields(result)


@pytest.mark.parametrize("filename", [None, 123, object(), Path("account_snapshot.json")])
def test_non_string_filename_is_input_invalid(filename: object) -> None:
    result = validate_mt4_demo_readonly_filename(filename)

    assert result["passed"] is False
    assert result["status_code"] == MT4_DEMO_READONLY_INPUT_INVALID
    assert result["reason_code"] == "FILENAME_INPUT_NOT_STR"
    _assert_safety_fields(result)


@pytest.mark.parametrize("filename", ALLOWED_FILENAMES)
def test_build_candidate_path_allows_whitelisted_files(filename: str) -> None:
    result = build_mt4_demo_readonly_candidate_path("demo_readonly_input", filename)

    assert result["passed"] is True
    assert result["status_code"] == MT4_DEMO_READONLY_PATH_ALLOWED
    assert result["safe_filename"] == filename
    assert result["candidate_path"] is not None
    assert str(result["candidate_path"]).endswith(filename)
    assert result["reason_code"] is None
    _assert_safety_fields(result)
    _assert_no_trading_or_execution_fields(result)


@pytest.mark.parametrize("filename", FORBIDDEN_FILENAMES)
def test_build_candidate_path_blocks_forbidden_filename(filename: str) -> None:
    result = build_mt4_demo_readonly_candidate_path("demo_readonly_input", filename)

    assert result["passed"] is False
    assert result["status_code"] == MT4_DEMO_READONLY_PATH_REJECTED
    assert result["safe_filename"] is None
    assert result["candidate_path"] is None
    assert result["reason_code"] is not None
    _assert_safety_fields(result)
    _assert_no_trading_or_execution_fields(result)


@pytest.mark.parametrize("base_dir", [None, 123, object(), "", " demo", "demo "])
def test_build_candidate_path_rejects_invalid_base_dir(base_dir: object) -> None:
    result = build_mt4_demo_readonly_candidate_path(base_dir, "account_snapshot.json")

    assert result["passed"] is False
    assert result["status_code"] == MT4_DEMO_READONLY_INPUT_INVALID
    assert result["candidate_path"] is None
    assert result["safe_filename"] is None
    assert result["reason_code"] is not None
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "malicious_filename",
    [
        r"C:\Users\someone\secret\password.json",
        "/home/user/.env",
    ],
)
def test_error_result_does_not_leak_malicious_raw_path(malicious_filename: str) -> None:
    result = build_mt4_demo_readonly_candidate_path(
        "demo_readonly_input",
        malicious_filename,
    )

    assert result["passed"] is False
    assert result["candidate_path"] is None
    assert result["safe_filename"] is None
    assert malicious_filename not in str(result)
    _assert_safety_fields(result)


def test_build_candidate_path_does_not_call_filesystem_or_network(monkeypatch: pytest.MonkeyPatch) -> None:
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

    result = build_mt4_demo_readonly_candidate_path(
        "demo_readonly_input",
        "account_snapshot.json",
    )

    assert result["passed"] is True
    assert result["status_code"] == MT4_DEMO_READONLY_PATH_ALLOWED
    _assert_safety_fields(result)


def test_module_does_not_need_file_to_exist(tmp_path: Path) -> None:
    missing_base_dir = tmp_path / "not_created"
    candidate_file = missing_base_dir / "account_snapshot.json"
    assert missing_base_dir.exists() is False
    assert candidate_file.exists() is False

    result = build_mt4_demo_readonly_candidate_path(
        str(missing_base_dir),
        "account_snapshot.json",
    )

    assert result["passed"] is True
    assert result["candidate_path"] == str(candidate_file)
    assert missing_base_dir.exists() is False
    assert candidate_file.exists() is False
    _assert_safety_fields(result)
