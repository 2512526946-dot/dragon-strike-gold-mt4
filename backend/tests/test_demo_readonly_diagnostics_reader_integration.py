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
    DEMO_READONLY_DIAGNOSTICS_BLOCKED,
    DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
    DEMO_READONLY_DIAGNOSTICS_READY,
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
    "account_number",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
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
    _install_reader_that_must_not_be_called(monkeypatch)
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


def test_server_config_enabled_diagnostics_calls_reader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def fake_reader(base_dir: object) -> dict[str, Any]:
        calls.append(base_dir)
        return _safe_reader_summary(passed=True)

    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fake_reader,
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    assert calls == [SAFE_BRIDGE_DIR]
    data = response.json()
    assert data["passed"] is True
    assert data["status_code"] == DEMO_READONLY_DIAGNOSTICS_READY
    assert data["source_mode"] == MT4_SOURCE_MODE
    assert data["source_status"] == "mt4_demo_readonly_file_bridge_ready"
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "ready"
    assert data["reader_passed"] is True
    assert data["reader_status_code"] == "MT4_DEMO_READONLY_READER_READY"
    assert data["readiness_notes"]
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_request_values_cannot_override_server_reader_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def fake_reader(base_dir: object) -> dict[str, Any]:
        calls.append(base_dir)
        return _safe_reader_summary(passed=True)

    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fake_reader,
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
    assert calls == [SAFE_BRIDGE_DIR]
    data = response.json()
    assert data["source_mode"] == MT4_SOURCE_MODE
    assert data["reader_status"] == "ready"
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_reader_blocked_summary_is_returned_as_safe_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "read_mt4_demo_readonly_source_summary_from_dir",
        lambda _base_dir: _safe_reader_summary(passed=False),
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
    assert data["reader_status_code"] == "MT4_DEMO_READONLY_READER_BLOCKED"
    assert "reader blocked safely" in data["block_reasons"]
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_reader_exception_is_sanitized_without_path_or_secret_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raising_reader(_base_dir: object) -> dict[str, Any]:
        raise RuntimeError(
            r"SECRET_EXCEPTION_SHOULD_NOT_LEAK C:\Users\hidden\password.py"
        )

    _install_server_config(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "read_mt4_demo_readonly_source_summary_from_dir",
        raising_reader,
        raising=False,
    )
    client = TestClient(app)

    with _external_state_guard_context():
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["reader_status"] == "error_safe"
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == "MT4_DEMO_READONLY_READER_EXCEPTION_SAFE"
    assert "reader exception sanitized" in data["block_reasons"]
    _assert_safe_flags(data)
    _assert_forbidden_text_absent(data)


def test_explanation_api_does_not_call_server_config_or_reader(
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
        "read_mt4_demo_readonly_source_summary_from_dir",
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


def _install_reader_that_must_not_be_called(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("reader must remain not_called by default")

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


def _safe_reader_summary(*, passed: bool) -> dict[str, Any]:
    return {
        "passed": passed,
        "status_code": (
            "MT4_DEMO_READONLY_READER_READY"
            if passed
            else "MT4_DEMO_READONLY_READER_BLOCKED"
        ),
        "source_mode": MT4_SOURCE_MODE,
        "source_scope": "mt4_demo_readonly_reader_safe_summary_only",
        "validation_stage": "demo_readonly_diagnostics_reader",
        "fixture_source": "mt4_demo_readonly_file_bridge",
        "reader_status": "ready" if passed else "blocked",
        "reader_block_reasons": [] if passed else ["READER_BLOCKED"],
        "reader_warning_reasons": [],
        "bundle_validation_status": _safe_status(passed=passed),
        "component_statuses": [
            {
                "component_name": "account_snapshot",
                "passed": passed,
                "status_code": "COMPONENT_READY" if passed else "COMPONENT_BLOCKED",
                "block_reasons": [] if passed else ["reader blocked safely"],
                "warning_reasons": [],
                "read_only": True,
                "demo_only": True,
                "is_tradable": False,
                "can_execute": False,
            }
        ],
        "block_reasons": [] if passed else ["reader blocked safely"],
        "warning_reasons": [],
        "readiness_notes": [
            "Reader summary is read-only.",
            "Reader summary is not trading permission.",
            "Reader summary does not generate trading signals.",
        ],
        "next_allowed_stage": ["read_only_diagnostics_review"] if passed else [],
        "next_blocked_stage": ["execution_chain"],
        **SAFE_FLAGS,
    }


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
