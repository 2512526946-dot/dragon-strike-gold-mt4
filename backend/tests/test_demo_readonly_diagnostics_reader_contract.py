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
    SOURCE_SCOPE,
)
from app.services import mt4_demo_readonly_reader


EXPLANATION_ENDPOINT = demo_readonly_api.DEMO_READONLY_EXPLANATION_ENDPOINT
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

FORBIDDEN_RESPONSE_KEYS = {
    "raw_payload",
    "bridge_dir",
    "base_dir",
    "candidate_path",
    "system_path",
    "traceback",
    "stack_trace",
    "password",
    "credential",
    "token",
    "secret",
    "api_key",
    "login",
    "account_number",
    "ticket",
    "order_id",
    "suggested_lot",
    "final_lot",
    "buy_now",
    "sell_now",
    "should_buy",
    "should_sell",
    "open_position",
    "close_position",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
    "ea_command",
    "trade_signal",
    "trading_action",
    "override_risk",
    "bypass_gate",
}

FORBIDDEN_TEXT_MARKERS = FORBIDDEN_RESPONSE_KEYS | {
    MT4_SOURCE_MODE,
    "c:\\",
    "\\users\\",
    "/home/",
    ".env",
    "raw payload",
    "stack trace",
    "OrderSend",
    "OrderClose",
    "OrderModify",
    "OrderDelete",
}


@pytest.fixture()
def reader_contract_harness(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, list[object]]:
    source_config_calls: list[object] = []

    def safe_source_config_guard(config: object) -> dict[str, Any]:
        source_config_calls.append(config)
        assert config == {}
        return _safe_source_config_guard_result()

    _install_no_reader_guard(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "validate_demo_readonly_source_config",
        safe_source_config_guard,
        raising=False,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        _safe_diagnostics_summary,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        _safe_explanation_report,
    )
    return TestClient(app), source_config_calls


def test_diagnostics_api_default_reader_contract_is_not_called(
    reader_contract_harness: tuple[TestClient, list[object]],
) -> None:
    client, source_config_calls = reader_contract_harness

    response = _guarded_request(client, DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    assert source_config_calls == [{}]
    data = response.json()
    assert data["source_scope"] == SOURCE_SCOPE
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "docs_fixture_only_ready"
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "not_called"
    _assert_response_safe(data)


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {
            "params": {
                "source_mode": MT4_SOURCE_MODE,
            }
        },
        {
            "params": {
                "bridge_dir": r"C:\Users\hidden\bridge",
                "base_dir": "/home/hidden/base",
                "candidate_path": "/home/hidden/candidate.py",
            }
        },
        {
            "headers": {
                "X-Source-Mode": MT4_SOURCE_MODE,
                "X-Bridge-Dir": r"C:\Users\hidden\bridge",
            }
        },
        {
            "headers": {
                "X-Base-Dir": "/home/hidden/base",
                "X-Candidate-Path": "/home/hidden/candidate.py",
            }
        },
        {
            "json": {
                "source_mode": MT4_SOURCE_MODE,
                "bridge_dir": r"C:\Users\hidden\bridge",
                "base_dir": "/home/hidden/base",
                "candidate_path": "/home/hidden/candidate.py",
                "raw_payload": {"password": "hidden"},
            }
        },
    ],
)
def test_diagnostics_api_request_overrides_cannot_enable_reader(
    reader_contract_harness: tuple[TestClient, list[object]],
    request_kwargs: dict[str, Any],
) -> None:
    client, source_config_calls = reader_contract_harness

    response = _guarded_request(
        client,
        DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
        **request_kwargs,
    )

    assert response.status_code == 200
    assert source_config_calls == [{}]
    data = response.json()
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "docs_fixture_only_ready"
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "not_called"
    _assert_response_safe(data)


def test_source_config_passed_and_reader_status_are_not_execution_permission(
    reader_contract_harness: tuple[TestClient, list[object]],
) -> None:
    client, _source_config_calls = reader_contract_harness

    response = _guarded_request(client, DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "not_called"
    assert data["is_tradable"] is False
    assert data["can_execute"] is False
    assert data["is_trading_permission"] is False
    assert data["is_execution_instruction"] is False
    assert data["allowed_to_call_ea"] is False
    assert data["allowed_to_modify_risk"] is False
    _assert_response_safe(data)


def test_explanation_api_still_does_not_call_reader_or_source_config_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_source_config_guard(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("explanation API must not call source config guard")

    _install_no_reader_guard(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "validate_demo_readonly_source_config",
        fail_source_config_guard,
        raising=False,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        _safe_explanation_report,
    )
    client = TestClient(app)

    response = _guarded_request(client, EXPLANATION_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert "source_mode" not in data
    assert "reader_status" not in data
    _assert_response_safe(data)


def _install_no_reader_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("diagnostics reader contract must not call reader")

    monkeypatch.setattr(
        mt4_demo_readonly_reader,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fail_if_called,
    )
    monkeypatch.setattr(
        mt4_demo_readonly_reader,
        "get_mt4_demo_readonly_reader_required_filenames",
        fail_if_called,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fail_if_called,
        raising=False,
    )


def _guarded_request(
    client: TestClient,
    endpoint: str,
    **kwargs: Any,
) -> Any:
    with _external_state_guard_context():
        return client.request("GET", endpoint, **kwargs)


def _external_state_guard_context() -> ExitStack:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(
            "diagnostics reader contract must not touch files, env, or network"
        )

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
    stack.enter_context(patch.object(socket, "create_connection", fail_if_called))
    return stack


def _safe_diagnostics_summary() -> SimpleNamespace:
    safe_status = _safe_component_status()
    return SimpleNamespace(
        passed=True,
        status_code="SUMMARY_READY",
        source_scope=SOURCE_SCOPE,
        validation_stage="diagnostics_reader_contract",
        fixture_source="docs_fixture_only",
        bundle_validation_status=safe_status,
        component_statuses={"reader_contract": safe_status},
        block_reasons=[],
        warning_reasons=[],
        readiness_notes=[
            "Diagnostics API remains docs fixture only.",
            "Diagnostics API is not trading permission.",
            "Diagnostics API does not generate trading signals.",
        ],
        next_allowed_stage=["diagnostics_reader_contract_review"],
        next_blocked_stage=["mt4_reader_source_mode_integration"],
        **SAFE_FLAGS,
    )


def _safe_component_status() -> dict[str, Any]:
    return {
        "passed": True,
        "status_code": "CONTRACT_SAFE",
        "block_reasons": [],
        "warning_reasons": [],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }


def _safe_source_config_guard_result() -> dict[str, Any]:
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
        "overall_explanation": "Read-only explanation keeps the safe summary.",
        "status_explanation": "Current explanation is not trading permission or an execution instruction.",
        "component_explanations": [
            {
                "component_name": "reader_contract",
                "status": "passed",
                "status_code": "CONTRACT_SAFE",
                "plain_language_summary": "Reader remains disconnected.",
                "block_reasons_explained": ["No displayable block reasons."],
                "warning_reasons_explained": ["No displayable warning reasons."],
                "user_impact": "Only read-only diagnostics display is affected.",
                "safe_next_step": "Review read-only diagnostics.",
                "forbidden_interpretation": "Do not interpret this as trading permission or an execution instruction.",
            }
        ],
        "blocker_explanations": ["No displayable block reasons."],
        "warning_explanations": ["No displayable warning reasons."],
        "readiness_explanation": ["Read-only explanation keeps the safe summary."],
        "next_allowed_stage_explanation": [
            "Reader contract review is a test-stage hint, not trading permission."
        ],
        "next_blocked_stage_explanation": [
            "Future reader integration remains disabled, and this is not an execution instruction."
        ],
        "user_safe_next_steps": ["Review read-only diagnostics"],
        "user_forbidden_actions": ["Any trading operation remains forbidden."],
        "unknowns": [],
        "safety_flags": dict(SAFE_FLAGS),
        "block_reasons": [],
        "warning_reasons": [],
        "notes": [
            "Reader contract tests do not enable the reader.",
            "Not trading permission and not an execution instruction.",
        ],
        **SAFE_FLAGS,
    }


def _assert_response_safe(data: dict[str, Any]) -> None:
    _assert_safe_flags(data)
    _assert_forbidden_keys_absent(data)
    _assert_forbidden_text_absent(data)
    serialized = json.dumps(data, ensure_ascii=False)
    assert MT4_SOURCE_MODE not in serialized


def _assert_safe_flags(data: dict[str, Any]) -> None:
    for field_name, expected_value in SAFE_FLAGS.items():
        assert data[field_name] is expected_value
    if isinstance(data.get("safety_flags"), dict):
        for field_name, expected_value in SAFE_FLAGS.items():
            assert data["safety_flags"][field_name] is expected_value


def _assert_forbidden_keys_absent(data: dict[str, Any]) -> None:
    keys = _collect_keys(data)
    for forbidden_key in FORBIDDEN_RESPONSE_KEYS:
        assert forbidden_key not in keys


def _assert_forbidden_text_absent(data: dict[str, Any]) -> None:
    serialized = json.dumps(data, ensure_ascii=False).casefold()
    for forbidden_text in FORBIDDEN_TEXT_MARKERS:
        assert forbidden_text.casefold() not in serialized


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys: set[str] = set(value)
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()
