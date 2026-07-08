from __future__ import annotations

import builtins
import glob
import json
import os
import socket
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import app.api.demo_readonly as demo_readonly_api
from app.main import app
from app.schemas.demo_readonly_diagnostics import (
    DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
    DEMO_READONLY_SAFETY_FIELD_VIOLATION,
)
from app.services import mt4_demo_readonly_reader


MT4_SOURCE_MODE = "mt4_demo_readonly_file_bridge_enabled"
SAFE_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}
FORBIDDEN_RESPONSE_TEXT = {
    MT4_SOURCE_MODE,
    "BRIDGE_DIR_SHOULD_NOT_LEAK",
    "BASE_DIR_SHOULD_NOT_LEAK",
    "CANDIDATE_PATH_SHOULD_NOT_LEAK",
    "PASSWORD_SHOULD_NOT_LEAK",
    "TOKEN_SHOULD_NOT_LEAK",
    "ACCOUNT_SHOULD_NOT_LEAK",
    "ORDER_SHOULD_NOT_LEAK",
    "LOT_SHOULD_NOT_LEAK",
    "EA_COMMAND_SHOULD_NOT_LEAK",
    "TRACEBACK_SHOULD_NOT_LEAK",
    "SECRET_EXCEPTION_SHOULD_NOT_LEAK",
    "bridge_dir",
    "base_dir",
    "candidate_path",
    "raw_payload",
    "password",
    "credential",
    "token",
    "secret",
    "account_number",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
    "OrderSend",
    "OrderClose",
    "OrderModify",
    "OrderDelete",
    "suggested_lot",
    "final_lot",
    "trade_signal",
    "trading_action",
    "ea_command",
    "override_risk",
    "bypass_gate",
    "stack_trace",
    "traceback",
    "system_path",
    "api_key",
    "c:\\",
    "\\users\\",
    "/home/",
    ".env",
}


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("bridge_dir", "BRIDGE_DIR_SHOULD_NOT_LEAK"),
        ("base_dir", r"C:\Users\hidden\BASE_DIR_SHOULD_NOT_LEAK.py"),
        ("candidate_path", "/home/hidden/CANDIDATE_PATH_SHOULD_NOT_LEAK.py"),
        ("raw_payload", {"password": "PASSWORD_SHOULD_NOT_LEAK"}),
        ("system_path", r"C:\Users\hidden\SYSTEM_PATH_SHOULD_NOT_LEAK.py"),
        ("traceback", "TRACEBACK_SHOULD_NOT_LEAK"),
        ("stack_trace", "TRACEBACK_SHOULD_NOT_LEAK"),
        ("api_key", "TOKEN_SHOULD_NOT_LEAK"),
        ("token", "TOKEN_SHOULD_NOT_LEAK"),
        ("secret", "TOKEN_SHOULD_NOT_LEAK"),
        ("account_number", "ACCOUNT_SHOULD_NOT_LEAK"),
        ("order_id", "ORDER_SHOULD_NOT_LEAK"),
        ("OrderSend", "ORDER_SHOULD_NOT_LEAK"),
        ("OrderClose", "ORDER_SHOULD_NOT_LEAK"),
        ("OrderModify", "ORDER_SHOULD_NOT_LEAK"),
        ("OrderDelete", "ORDER_SHOULD_NOT_LEAK"),
        ("suggested_lot", "LOT_SHOULD_NOT_LEAK"),
        ("final_lot", "LOT_SHOULD_NOT_LEAK"),
        ("trade_signal", "ORDER_SHOULD_NOT_LEAK"),
        ("trading_action", "ORDER_SHOULD_NOT_LEAK"),
        ("ea_command", "EA_COMMAND_SHOULD_NOT_LEAK"),
        ("override_risk", True),
        ("bypass_gate", True),
    ],
)
def test_diagnostics_api_sanitizes_polluted_source_config_guard_output(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    field_value: Any,
) -> None:
    result = _docs_fixture_source_config_result()
    result[field_name] = field_value

    data = _diagnostics_response_for_guard_result(monkeypatch, result)

    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_SAFETY_FIELD_VIOLATION
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "source_config_safety_blocked"
    assert data["source_config_status_code"] == "SOURCE_CONFIG_SAFETY_BLOCKED"
    assert data["source_config_passed"] is False
    assert data["reader_status"] == "not_called"
    assert "source_config_output_sanitized" in data["block_reasons"]
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    [
        ("read_only", False),
        ("demo_only", False),
        ("is_tradable", True),
        ("can_execute", True),
        ("is_trading_permission", True),
        ("is_execution_instruction", True),
        ("allowed_to_call_ea", True),
        ("allowed_to_modify_risk", True),
    ],
)
def test_diagnostics_api_sanitizes_unsafe_source_config_safety_flags(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    unsafe_value: bool,
) -> None:
    result = _docs_fixture_source_config_result()
    result[field_name] = unsafe_value

    data = _diagnostics_response_for_guard_result(monkeypatch, result)

    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_SAFETY_FIELD_VIOLATION
    assert data["source_config_passed"] is False
    assert data["source_status"] == "source_config_safety_blocked"
    assert "source_config_output_sanitized" in data["block_reasons"]
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_diagnostics_api_handles_source_config_guard_exception_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raising_guard(config: object) -> dict[str, Any]:
        assert config == {}
        raise RuntimeError(
            r"TRACEBACK_SHOULD_NOT_LEAK C:\Users\hidden\SECRET_EXCEPTION_SHOULD_NOT_LEAK.py"
        )

    _install_no_reader_guard(monkeypatch)
    _install_safe_summary(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "validate_demo_readonly_source_config",
        raising_guard,
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_SAFETY_FIELD_VIOLATION
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "source_config_safety_blocked"
    assert data["source_config_status_code"] == (
        "SOURCE_CONFIG_GUARD_EXCEPTION_SANITIZED"
    )
    assert data["source_config_passed"] is False
    assert data["reader_status"] == "not_called"
    assert "source_config_guard_exception_sanitized" in data["block_reasons"]
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_diagnostics_api_ignores_request_source_config_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def fake_guard(config: object) -> dict[str, Any]:
        calls.append(config)
        return _docs_fixture_source_config_result()

    _install_no_reader_guard(monkeypatch)
    _install_safe_summary(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "validate_demo_readonly_source_config",
        fake_guard,
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.request(
            "GET",
            DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
            params={
                "source_mode": MT4_SOURCE_MODE,
                "bridge_dir": r"C:\Users\hidden\bridge",
                "base_dir": "/home/hidden/base",
                "candidate_path": "/home/hidden/candidate.py",
            },
            headers={
                "X-Source-Mode": MT4_SOURCE_MODE,
                "X-Bridge-Dir": r"C:\Users\hidden\bridge",
            },
            json={
                "source_mode": MT4_SOURCE_MODE,
                "raw_payload": {"password": "PASSWORD_SHOULD_NOT_LEAK"},
            },
        )

    assert response.status_code == 200
    assert calls == [{}]
    data = response.json()
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "docs_fixture_only_ready"
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "not_called"
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def _diagnostics_response_for_guard_result(
    monkeypatch: pytest.MonkeyPatch,
    guard_result: dict[str, Any],
) -> dict[str, Any]:
    _install_no_reader_guard(monkeypatch)
    _install_safe_summary(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "validate_demo_readonly_source_config",
        lambda config: guard_result if config == {} else {},
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    return response.json()


def _docs_fixture_source_config_result() -> dict[str, Any]:
    return {
        "passed": True,
        "status_code": "MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY",
        "selected_source_mode": "docs_fixture_only",
        "default_source_mode": "docs_fixture_only",
        "source_status": "docs_fixture_only_ready",
        "request_override_allowed": False,
        "block_reasons": [],
        "warning_reasons": [],
        "notes": [
            "source config guard validates caller-provided server-side config only",
            "source_mode readiness is not a trading permission",
        ],
        **SAFE_FLAGS,
    }


def _install_no_reader_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("diagnostics source config safety must not call reader")

    monkeypatch.setattr(
        mt4_demo_readonly_reader,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fail_if_called,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fail_if_called,
        raising=False,
    )


def _install_safe_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        lambda: SimpleNamespace(
            passed=True,
            status_code="SUMMARY_READY",
            source_scope="docs_fixture_only",
            validation_stage="diagnostics_source_config_safety",
            fixture_source="docs_fixture_only",
            bundle_validation_status={
                "passed": True,
                "status_code": "BUNDLE_VALID",
                "block_reasons": [],
                "warning_reasons": [],
                "read_only": True,
                "demo_only": True,
                "is_tradable": False,
                "can_execute": False,
            },
            component_statuses={},
            block_reasons=[],
            warning_reasons=[],
            readiness_notes=[
                "Diagnostics API remains docs fixture only.",
                "Diagnostics API is not trading permission.",
                "Diagnostics API does not generate trading signals.",
            ],
            next_allowed_stage=["diagnostics_source_config_safety"],
            next_blocked_stage=["mt4_reader_source_mode_integration"],
            **SAFE_FLAGS,
        ),
    )


def _external_state_guard_context() -> ExitStack:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(
            "diagnostics source config safety test must not touch external state"
        )

    stack = ExitStack()
    stack.enter_context(patch.object(builtins, "open", fail_if_called))
    stack.enter_context(patch.object(glob, "glob", fail_if_called))
    stack.enter_context(patch.object(os, "walk", fail_if_called))
    stack.enter_context(patch.object(Path, "iterdir", fail_if_called))
    stack.enter_context(patch.object(Path, "open", fail_if_called))
    stack.enter_context(patch.object(Path, "read_text", fail_if_called))
    stack.enter_context(patch.object(Path, "read_bytes", fail_if_called))
    stack.enter_context(patch.object(socket, "create_connection", fail_if_called))
    return stack


def _assert_safe_flags(data: dict[str, Any]) -> None:
    for field_name, expected_value in SAFE_FLAGS.items():
        assert data[field_name] is expected_value


def _assert_forbidden_text_absent(data: dict[str, Any]) -> None:
    serialized = json.dumps(data, ensure_ascii=False).casefold()
    for forbidden_text in FORBIDDEN_RESPONSE_TEXT:
        assert forbidden_text.casefold() not in serialized
