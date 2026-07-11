from __future__ import annotations

import builtins
import glob
import json
import os
import socket
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import app.api.demo_readonly as demo_readonly_api
from app.main import app
from app.schemas.demo_readonly_diagnostics import (
    DEMO_READONLY_DIAGNOSTICS_BLOCKED,
    DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
    DEMO_READONLY_DIAGNOSTICS_READY,
    DEMO_READONLY_INTERNAL_ERROR,
    DEMO_READONLY_SAFETY_FIELD_VIOLATION,
)
from app.services import demo_readonly_canonical_diagnostics_summary_adapter as adapter
from app.services import mt4_demo_readonly_reader as legacy_reader
from app.services.data_quality_gate import (
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED,
    READER_BLOCKED,
)


MT4_SOURCE_MODE = "mt4_demo_readonly_file_bridge_enabled"
SAFE_BRIDGE_DIR = "mt4_demo_readonly_bridge"

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
    "bridge_dir",
    "base_dir",
    "candidate_path",
    "raw_payload",
    "password",
    "credential",
    "token",
    "secret",
    "api_key",
    "login",
    "account_number",
    "ticket",
    "order_id",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
    "suggested_lot",
    "final_lot",
    "buy_now",
    "sell_now",
    "should_buy",
    "should_sell",
    "open_position",
    "close_position",
    "trade_signal",
    "trading_action",
    "ea_command",
    "execute_trade",
    "can_trade",
    "allow_trade",
    "override_risk",
    "bypass_gate",
    "stack_trace",
    "traceback",
    "system_path",
    "api_key",
    r"c:\\",
    "\\users\\",
    "/home/",
    ".env",
    "SECRET_EXCEPTION_SHOULD_NOT_LEAK",
}


def test_default_diagnostics_does_not_call_reader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_safe_summary(monkeypatch)
    _install_pipeline_that_must_not_be_called(monkeypatch)
    _install_legacy_reader_that_must_not_be_called(monkeypatch)
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "docs_fixture_only_ready"
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "not_called"
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == "READER_NOT_CALLED"
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_server_config_enabled_diagnostics_calls_canonical_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_pipeline(**kwargs: object) -> dict[str, Any]:
        calls.append(kwargs)
        return _safe_canonical_summary(passed=True)

    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        fake_pipeline,
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    _assert_pipeline_calls(calls)
    data = response.json()
    assert data["passed"] is True
    assert data["status_code"] == DEMO_READONLY_DIAGNOSTICS_READY
    assert data["source_mode"] == MT4_SOURCE_MODE
    assert data["source_status"] == "mt4_demo_readonly_file_bridge_ready"
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "ready"
    assert data["reader_passed"] is True
    assert data["reader_status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY
    assert data["readiness_notes"]
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_request_values_cannot_override_server_reader_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_pipeline(**kwargs: object) -> dict[str, Any]:
        calls.append(kwargs)
        return _safe_canonical_summary(passed=True)

    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        fake_pipeline,
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
            },
            headers={
                "X-Source-Mode": MT4_SOURCE_MODE,
                "X-Bridge-Dir": r"C:\Users\hidden\bridge",
            },
            json={
                "source_mode": MT4_SOURCE_MODE,
                "bridge_dir": r"C:\Users\hidden\bridge",
                "raw_payload": {"password": "hidden"},
            },
        )

    assert response.status_code == 200
    _assert_pipeline_calls(calls)
    data = response.json()
    assert data["source_mode"] == MT4_SOURCE_MODE
    assert data["reader_status"] == "ready"
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_canonical_pipeline_blocked_summary_is_returned_as_safe_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **_kwargs: _safe_canonical_summary(passed=False),
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_DIAGNOSTICS_BLOCKED
    assert data["source_mode"] == MT4_SOURCE_MODE
    assert data["reader_status"] == "blocked"
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
    assert "READER_BLOCKED" in data["block_reasons"]
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_pipeline_exception_is_sanitized_without_path_or_secret_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raising_pipeline(**_kwargs: object) -> dict[str, Any]:
        raise RuntimeError(
            r"SECRET_EXCEPTION_SHOULD_NOT_LEAK C:\Users\hidden\password.py"
        )

    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        raising_pipeline,
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 500
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_INTERNAL_ERROR
    assert data["reader_status"] == "not_called"
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == "READER_NOT_CALLED"
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


@pytest.mark.parametrize(
    ("polluted_key", "polluted_value"),
    [
        ("raw_payload", {"password": "PASSWORD_SHOULD_NOT_LEAK"}),
        ("bridge_dir", "BRIDGE_DIR_SHOULD_NOT_LEAK"),
        ("base_dir", "BASE_DIR_SHOULD_NOT_LEAK"),
        ("candidate_path", "C:\\Users\\hidden\\CANDIDATE_PATH_SHOULD_NOT_LEAK.py"),
        ("system_path", "C:\\Users\\hidden\\SYSTEM_PATH_SHOULD_NOT_LEAK.py"),
        ("traceback", "TRACEBACK_SHOULD_NOT_LEAK"),
        ("stack_trace", "STACK_TRACE_SHOULD_NOT_LEAK"),
        ("password", "PASSWORD_SHOULD_NOT_LEAK"),
        ("credential", "CREDENTIAL_SHOULD_NOT_LEAK"),
        ("token", "TOKEN_SHOULD_NOT_LEAK"),
        ("secret", "SECRET_SHOULD_NOT_LEAK"),
        ("api_key", "API_KEY_SHOULD_NOT_LEAK"),
        ("login", "LOGIN_SHOULD_NOT_LEAK"),
        ("account_number", "ACCOUNT_NUMBER_SHOULD_NOT_LEAK"),
        ("ticket", "TICKET_SHOULD_NOT_LEAK"),
        ("order_id", "ORDER_ID_SHOULD_NOT_LEAK"),
        ("suggested_lot", "LOT_SHOULD_NOT_LEAK"),
        ("final_lot", "LOT_SHOULD_NOT_LEAK"),
        ("buy_now", "BUY_NOW_SHOULD_NOT_LEAK"),
        ("sell_now", "SELL_NOW_SHOULD_NOT_LEAK"),
        ("should_buy", "SHOULD_BUY_SHOULD_NOT_LEAK"),
        ("should_sell", "SHOULD_SELL_SHOULD_NOT_LEAK"),
        ("open_position", "OPEN_POSITION_SHOULD_NOT_LEAK"),
        ("close_position", "CLOSE_POSITION_SHOULD_NOT_LEAK"),
        ("order_send", "ORDER_SEND_SHOULD_NOT_LEAK"),
        ("order_close", "ORDER_CLOSE_SHOULD_NOT_LEAK"),
        ("order_modify", "ORDER_MODIFY_SHOULD_NOT_LEAK"),
        ("order_delete", "ORDER_DELETE_SHOULD_NOT_LEAK"),
        ("ea_command", "EA_COMMAND_SHOULD_NOT_LEAK"),
        ("trade_signal", "TRADE_SIGNAL_SHOULD_NOT_LEAK"),
        ("trading_action", "TRADING_ACTION_SHOULD_NOT_LEAK"),
        ("override_risk", True),
        ("bypass_gate", True),
        ("execute_trade", "EXECUTE_TRADE_SHOULD_NOT_LEAK"),
        ("can_trade", True),
        ("allow_trade", True),
    ],
)
def test_pipeline_polluted_output_is_safety_blocked_and_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    polluted_key: str,
    polluted_value: Any,
) -> None:
    summary = _safe_canonical_summary(passed=True)
    summary[polluted_key] = polluted_value

    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **_kwargs: summary,
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_SAFETY_FIELD_VIOLATION
    assert data["reader_status"] == "safety_blocked"
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == "READER_OUTPUT_SAFETY_BLOCKED"
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)
    assert str(polluted_value) not in json.dumps(data, ensure_ascii=False)


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
def test_pipeline_unsafe_safety_flags_are_forced_safe_and_downgraded(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    unsafe_value: bool,
) -> None:
    summary = _safe_canonical_summary(passed=True)
    summary[field_name] = unsafe_value

    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **_kwargs: summary,
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_SAFETY_FIELD_VIOLATION
    assert data["reader_status"] == "safety_blocked"
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == "READER_OUTPUT_SAFETY_BLOCKED"
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_pipeline_unexpected_structure_does_not_crash_or_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **_kwargs: [
            "raw_payload",
            "PASSWORD_SHOULD_NOT_LEAK",
            r"C:\Users\hidden\traceback.py",
        ],
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_SAFETY_FIELD_VIOLATION
    assert data["reader_status"] == "blocked"
    assert data["reader_passed"] is False
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_explanation_api_does_not_call_server_config_or_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("explanation API must not call source config or reader")

    monkeypatch.setattr(
        demo_readonly_api,
        "_get_demo_readonly_server_source_config",
        fail_if_called,
        raising=False,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        fail_if_called,
        raising=False,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        _safe_explanation_report,
    )
    client = TestClient(app)

    response = client.get(demo_readonly_api.DEMO_READONLY_EXPLANATION_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert "source_mode" not in data
    assert "reader_status" not in data
    _assert_safe_flags(data)


def _install_server_config(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_legacy_reader_that_must_not_be_called(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "_get_demo_readonly_server_source_config",
        lambda: {
            "source_mode": MT4_SOURCE_MODE,
            "mt4_demo_readonly_file_bridge_enabled": True,
            "mt4_demo_readonly_bridge_dir": SAFE_BRIDGE_DIR,
            "allow_request_override": False,
        },
        raising=False,
    )


def _install_pipeline_that_must_not_be_called(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("canonical pipeline must remain not_called by default")

    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        fail_if_called,
        raising=False,
    )


def _install_legacy_reader_that_must_not_be_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("legacy reader must not be called by canonical diagnostics")

    monkeypatch.setattr(
        legacy_reader,
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
            validation_stage="diagnostics_reader_default_off",
            fixture_source="docs_fixture_only",
            bundle_validation_status=_safe_status(),
            component_statuses={"reader_default_off": _safe_status()},
            block_reasons=[],
            warning_reasons=[],
            readiness_notes=[
                "Diagnostics API remains docs fixture only by default.",
                "Diagnostics API is not trading permission.",
                "Diagnostics API does not generate trading signals.",
            ],
            next_allowed_stage=["diagnostics_reader_default_off_review"],
            next_blocked_stage=["execution_chain"],
            **SAFE_FLAGS,
        ),
    )


def _safe_canonical_summary(*, passed: bool) -> dict[str, Any]:
    source_status_code = (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED
        if passed
        else CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED
    )
    block_reasons = [] if passed else [READER_BLOCKED]
    status = {
        "passed": passed,
        "status_code": source_status_code,
        "block_reasons": list(block_reasons),
        "warning_reasons": [],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }
    return {
        "passed": passed,
        "status_code": (
            adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY
            if passed
            else adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
        ),
        "source_scope": adapter.SOURCE_SCOPE,
        "validation_stage": adapter.VALIDATION_STAGE,
        "fixture_source": adapter.FIXTURE_SOURCE,
        "bundle_validation_status": dict(status),
        "component_statuses": {"canonical_data_quality_gate": dict(status)},
        "block_reasons": list(block_reasons),
        "warning_reasons": [],
        "readiness_notes": [
            "Canonical diagnostics summary is read-only.",
            "Readiness is not trading permission.",
            "This summary cannot execute orders.",
        ],
        "next_allowed_stage": (
            ["demo_readonly_diagnostics_response_integration"] if passed else []
        ),
        "next_blocked_stage": (
            ["api_reader_activation", "execution_chain"]
            if passed
            else [
                "demo_readonly_diagnostics_response_integration",
                "api_reader_activation",
                "readonly_analysis",
                "execution_chain",
            ]
        ),
        **SAFE_FLAGS,
    }


def _assert_pipeline_calls(calls: list[dict[str, object]]) -> None:
    assert len(calls) == 1
    call = calls[0]
    assert set(call) == {"allowed_root", "bundle_dir", "now_utc"}
    assert call["allowed_root"] == Path(SAFE_BRIDGE_DIR).parent
    assert call["bundle_dir"] == Path(SAFE_BRIDGE_DIR)
    assert isinstance(call["now_utc"], datetime)
    assert call["now_utc"].tzinfo is UTC


def _safe_status(*, passed: bool = True) -> dict[str, Any]:
    return {
        "passed": passed,
        "status_code": "SAFE_STATUS_READY" if passed else "SAFE_STATUS_BLOCKED",
        "block_reasons": [] if passed else ["reader blocked safely"],
        "warning_reasons": [],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }


def _safe_explanation_report() -> dict[str, Any]:
    return {
        "passed": True,
        "status_code": "READONLY_EXPLANATION_READY",
        "report_version": "1.0",
        "report_type": "read_only_explanation_report",
        "generated_at": "2026-07-09T00:00:00Z",
        "source_scope": "demo_readonly_diagnostics_api",
        "input_status_code": "DEMO_READONLY_DIAGNOSTICS_READY",
        "input_passed": True,
        "explanation_scope": "demo_readonly_diagnostics_summary_only",
        "overall_explanation": "Read-only explanation remains docs fixture scoped.",
        "status_explanation": "This is not trading permission or an execution instruction.",
        "component_explanations": [],
        "blocker_explanations": ["No displayable block reasons."],
        "warning_explanations": ["No displayable warning reasons."],
        "readiness_explanation": ["Read-only explanation remains safe."],
        "next_allowed_stage_explanation": [
            "Review read-only diagnostics only."
        ],
        "next_blocked_stage_explanation": [
            "Execution and trading remain blocked."
        ],
        "user_safe_next_steps": ["Review read-only diagnostics"],
        "user_forbidden_actions": ["Any trading operation remains forbidden."],
        "unknowns": [],
        "safety_flags": dict(SAFE_FLAGS),
        "block_reasons": [],
        "warning_reasons": [],
        "notes": ["Explanation API does not call reader."],
        **SAFE_FLAGS,
    }


def _external_state_guard_context() -> ExitStack:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("diagnostics reader integration test must not touch files")

    allowed_runtime_env_keys = {"PYDANTIC_DISABLE_PLUGINS", "PYTHONASYNCIODEBUG"}

    def guarded_getenv(key: str, default: Any = None) -> Any:
        if key in allowed_runtime_env_keys:
            return default
        raise AssertionError(f"os.getenv read is not allowed: {key}")

    class FailingEnviron(dict[str, str]):
        def __getitem__(self, key: str) -> str:
            if key in allowed_runtime_env_keys:
                raise KeyError(key)
            raise AssertionError(f"os.environ read is not allowed: {key}")

        def get(self, key: str, default: Any = None) -> Any:
            if key in allowed_runtime_env_keys:
                return default
            raise AssertionError(f"os.environ.get is not allowed: {key}")

    stack = ExitStack()
    stack.enter_context(patch.object(builtins, "open", fail_if_called))
    stack.enter_context(patch.object(glob, "glob", fail_if_called))
    stack.enter_context(patch.object(os, "walk", fail_if_called))
    stack.enter_context(patch.object(os, "getenv", guarded_getenv))
    stack.enter_context(patch.object(os, "environ", FailingEnviron()))
    stack.enter_context(patch.object(Path, "iterdir", fail_if_called))
    stack.enter_context(patch.object(Path, "open", fail_if_called))
    stack.enter_context(patch.object(Path, "read_text", fail_if_called))
    stack.enter_context(patch.object(Path, "read_bytes", fail_if_called))
    stack.enter_context(socket_no_network_context())
    return stack


def socket_no_network_context() -> Any:
    return patch.object(
        socket,
        "create_connection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("network is not allowed")
        ),
    )


def _assert_safe_flags(data: dict[str, Any]) -> None:
    for field_name, expected_value in SAFE_FLAGS.items():
        assert data[field_name] is expected_value
    if isinstance(data.get("safety_flags"), dict):
        for field_name, expected_value in SAFE_FLAGS.items():
            assert data["safety_flags"][field_name] is expected_value


def _assert_forbidden_text_absent(data: dict[str, Any]) -> None:
    serialized = json.dumps(data, ensure_ascii=False).casefold()
    for forbidden_text in FORBIDDEN_RESPONSE_TEXT:
        assert forbidden_text.casefold() not in serialized
