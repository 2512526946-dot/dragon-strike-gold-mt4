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
    DEMO_READONLY_DIAGNOSTICS_READY,
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


def test_diagnostics_api_calls_source_config_guard_with_server_side_empty_config(
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
        response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    assert calls == [{}]
    data = response.json()
    assert data["status_code"] == DEMO_READONLY_DIAGNOSTICS_READY
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "docs_fixture_only_ready"
    assert data["source_config_status_code"] == (
        "MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY"
    )
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "not_called"
    _assert_safe_flags(data)
    _assert_no_forbidden_source_values(data)


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {
            "params": {
                "source_mode": MT4_SOURCE_MODE,
                "bridge_dir": r"C:\Users\hidden\mt4",
            }
        },
        {
            "headers": {
                "X-Source-Mode": MT4_SOURCE_MODE,
                "X-Bridge-Dir": r"C:\Users\hidden\bridge",
            }
        },
        {
            "json": {
                "source_mode": MT4_SOURCE_MODE,
                "bridge_dir": r"C:\Users\hidden\bridge",
                "raw_payload": {"password": "hidden"},
            }
        },
    ],
)
def test_diagnostics_api_request_values_cannot_switch_source_config(
    monkeypatch: pytest.MonkeyPatch,
    request_kwargs: dict[str, Any],
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
            **request_kwargs,
        )

    assert response.status_code == 200
    assert calls == [{}]
    data = response.json()
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "docs_fixture_only_ready"
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "not_called"
    _assert_safe_flags(data)
    _assert_no_forbidden_source_values(data)


def test_diagnostics_api_blocks_reader_guard_result_without_server_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_no_reader_guard(monkeypatch)
    _install_safe_summary(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "validate_demo_readonly_source_config",
        lambda _config: {
            **_docs_fixture_source_config_result(),
            "passed": True,
            "status_code": "MT4_DEMO_READONLY_SOURCE_CONFIG_READY",
            "selected_source_mode": MT4_SOURCE_MODE,
            "source_status": "mt4_demo_readonly_file_bridge_ready",
        },
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
    assert data["source_config_status_code"] == "SOURCE_CONFIG_SERVER_MISMATCH_BLOCKED"
    assert data["source_config_passed"] is False
    assert data["reader_status"] == "not_called"
    assert "source_config_server_mismatch_blocked" in data["block_reasons"]
    _assert_safe_flags(data)
    _assert_no_forbidden_source_values(data)


def test_explanation_api_does_not_call_source_config_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("explanation API must not call source config guard")

    monkeypatch.setattr(
        demo_readonly_api,
        "validate_demo_readonly_source_config",
        fail_if_called,
        raising=False,
    )
    client = TestClient(app)

    response = client.get(demo_readonly_api.DEMO_READONLY_EXPLANATION_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert "source_mode" not in data
    assert "reader_status" not in data
    _assert_safe_flags(data)


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
        raise AssertionError("diagnostics source config guard must not call reader")

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
            validation_stage="diagnostics_source_config_guard_contract",
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
            next_allowed_stage=["diagnostics_source_config_guard_contract"],
            next_blocked_stage=["mt4_reader_source_mode_integration"],
            **SAFE_FLAGS,
        ),
    )


def _external_state_guard_context() -> ExitStack:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(
            "diagnostics source config guard API test must not touch external state"
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


def _assert_no_forbidden_source_values(data: dict[str, Any]) -> None:
    serialized = json.dumps(data, ensure_ascii=False).casefold()
    for forbidden_text in [
        MT4_SOURCE_MODE,
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
        "trade_signal",
        "trading_action",
        r"c:\\",
        "\\users\\",
        "/home/",
        ".env",
    ]:
        assert forbidden_text.casefold() not in serialized
