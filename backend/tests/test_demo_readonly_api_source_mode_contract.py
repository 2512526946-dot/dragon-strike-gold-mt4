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
from app.services import mt4_demo_readonly_source_config_guard


EXPLANATION_ENDPOINT = demo_readonly_api.DEMO_READONLY_EXPLANATION_ENDPOINT
MT4_SOURCE_MODE = "mt4_demo_readonly_file_bridge_enabled"

FORBIDDEN_RESPONSE_KEYS = {
    "account_number",
    "api_key",
    "base_dir",
    "bridge_dir",
    "buy_now",
    "bypass_gate",
    "candidate_path",
    "close_position",
    "credential",
    "ea_command",
    "final_lot",
    "login",
    "open_position",
    "order_close",
    "order_delete",
    "order_id",
    "order_modify",
    "order_send",
    "override_risk",
    "password",
    "raw_payload",
    "secret",
    "sell_now",
    "should_buy",
    "should_sell",
    "stack_trace",
    "suggested_lot",
    "system_path",
    "ticket",
    "token",
    "traceback",
    "trade_signal",
    "trading_action",
}

FORBIDDEN_TEXT_MARKERS = {
    MT4_SOURCE_MODE,
    "account_number",
    "api_key",
    "base_dir",
    "bridge_dir",
    "buy_now",
    "bypass_gate",
    "candidate_path",
    "close_position",
    "credential",
    "ea_command",
    "final_lot",
    "login",
    "open_position",
    "order_close",
    "order_delete",
    "order_id",
    "order_modify",
    "order_send",
    "override_risk",
    "password",
    "raw_payload",
    "secret",
    "sell_now",
    "should_buy",
    "should_sell",
    "stack_trace",
    "suggested_lot",
    "system_path",
    "ticket",
    "token",
    "traceback",
    "trade_signal",
    "trading_action",
    "c:\\",
    "\\users\\",
    "/home/",
    ".env",
}

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


@pytest.fixture()
def guarded_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    _install_no_reader_or_source_config_guard(monkeypatch)
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
    return TestClient(app)


def test_diagnostics_api_default_response_stays_docs_fixture_only_and_safe(
    guarded_client: TestClient,
) -> None:
    response = _guarded_request(guarded_client, DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["source_scope"] == SOURCE_SCOPE
    _assert_contract_response_safe(data)


def test_explanation_api_default_response_stays_docs_fixture_only_and_safe(
    guarded_client: TestClient,
) -> None:
    response = _guarded_request(guarded_client, EXPLANATION_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["source_scope"] == "demo_readonly_diagnostics_api"
    _assert_contract_response_safe(data)


@pytest.mark.parametrize(
    "endpoint",
    [DEMO_READONLY_DIAGNOSTICS_ENDPOINT, EXPLANATION_ENDPOINT],
)
def test_query_source_mode_cannot_enable_mt4_reader(
    guarded_client: TestClient,
    endpoint: str,
) -> None:
    response = _guarded_request(
        guarded_client,
        endpoint,
        params={
            "source_mode": MT4_SOURCE_MODE,
            "bridge_dir": r"C:\Users\hidden\mt4",
        },
    )

    assert response.status_code == 200
    _assert_contract_response_safe(response.json())


@pytest.mark.parametrize(
    "endpoint",
    [DEMO_READONLY_DIAGNOSTICS_ENDPOINT, EXPLANATION_ENDPOINT],
)
def test_path_query_values_are_not_returned(
    guarded_client: TestClient,
    endpoint: str,
) -> None:
    response = _guarded_request(
        guarded_client,
        endpoint,
        params={
            "bridge_dir": r"C:\Users\hidden\bridge",
            "base_dir": "/home/hidden/base",
            "candidate_path": "/home/hidden/secret.py",
        },
    )

    assert response.status_code == 200
    _assert_contract_response_safe(response.json())


@pytest.mark.parametrize(
    "endpoint",
    [DEMO_READONLY_DIAGNOSTICS_ENDPOINT, EXPLANATION_ENDPOINT],
)
def test_source_mode_header_cannot_enable_mt4_reader(
    guarded_client: TestClient,
    endpoint: str,
) -> None:
    response = _guarded_request(
        guarded_client,
        endpoint,
        headers={
            "X-Source-Mode": MT4_SOURCE_MODE,
            "X-Bridge-Dir": r"C:\Users\hidden\bridge",
        },
    )

    assert response.status_code == 200
    _assert_contract_response_safe(response.json())


@pytest.mark.parametrize(
    "endpoint",
    [DEMO_READONLY_DIAGNOSTICS_ENDPOINT, EXPLANATION_ENDPOINT],
)
def test_get_request_body_cannot_enable_mt4_reader(
    guarded_client: TestClient,
    endpoint: str,
) -> None:
    response = _guarded_request(
        guarded_client,
        endpoint,
        json={
            "source_mode": MT4_SOURCE_MODE,
            "bridge_dir": r"C:\Users\hidden\bridge",
            "raw_payload": {"password": "hidden"},
        },
    )

    assert response.status_code == 200
    _assert_contract_response_safe(response.json())


def _install_no_reader_or_source_config_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(
            "demo-readonly API source_mode contract must not call reader or source config guard"
        )

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
    monkeypatch.setattr(
        mt4_demo_readonly_source_config_guard,
        "validate_demo_readonly_source_config",
        fail_if_called,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "validate_demo_readonly_source_config",
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
            "demo-readonly API source_mode contract must not touch external state"
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


def _safe_diagnostics_summary() -> SimpleNamespace:
    safe_status = _safe_component_status()
    return SimpleNamespace(
        passed=True,
        status_code="SUMMARY_READY",
        source_scope=SOURCE_SCOPE,
        validation_stage="demo_readonly_api_source_mode_contract",
        fixture_source="docs_fixture_only",
        bundle_validation_status=safe_status,
        component_statuses={"contract": safe_status},
        block_reasons=[],
        warning_reasons=[],
        readiness_notes=[
            "Diagnostics API remains docs fixture only.",
            "Diagnostics API is not trading permission.",
            "Diagnostics API does not generate trading signals.",
        ],
        next_allowed_stage=["api_source_mode_contract_review"],
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


def _safe_explanation_report() -> dict[str, Any]:
    return {
        "passed": True,
        "status_code": "READONLY_EXPLANATION_READY",
        "report_version": "1.0",
        "report_type": "read_only_explanation_report",
        "generated_at": "2026-07-08T00:00:00Z",
        "source_scope": "demo_readonly_diagnostics_api",
        "input_status_code": "DEMO_READONLY_DIAGNOSTICS_READY",
        "input_passed": True,
        "explanation_scope": "demo_readonly_diagnostics_summary_only",
        "overall_explanation": "Read-only explanation API keeps the docs fixture contract.",
        "status_explanation": "Current explanation is not trading permission or an execution instruction.",
        "component_explanations": [
            {
                "component_name": "contract",
                "status": "passed",
                "status_code": "CONTRACT_SAFE",
                "plain_language_summary": "API still keeps the read-only contract boundary.",
                "block_reasons_explained": ["No displayable block reasons."],
                "warning_reasons_explained": ["No displayable warning reasons."],
                "user_impact": "Only read-only diagnostics display is affected.",
                "safe_next_step": "Continue reviewing the read-only contract.",
                "forbidden_interpretation": "Do not interpret this as trading permission or an execution instruction.",
            }
        ],
        "blocker_explanations": ["No displayable block reasons."],
        "warning_explanations": ["No displayable warning reasons."],
        "readiness_explanation": ["Read-only explanation keeps the safe summary."],
        "next_allowed_stage_explanation": [
            "api_source_mode_contract_review is a test-stage hint, not trading permission."
        ],
        "next_blocked_stage_explanation": [
            "Future source mode integration remains disabled, and this is not an execution instruction."
        ],
        "user_safe_next_steps": ["Review read-only diagnostics", "Review read-only explanation"],
        "user_forbidden_actions": ["Any trading operation remains forbidden."],
        "unknowns": [],
        "safety_flags": dict(SAFE_FLAGS),
        "block_reasons": [],
        "warning_reasons": [],
        "notes": [
            "API source mode contract tests do not enable MT4 reader.",
            "Not trading permission and not an execution instruction.",
        ],
        **SAFE_FLAGS,
    }


def _assert_contract_response_safe(data: dict[str, Any]) -> None:
    _assert_safe_flags(data)
    _assert_source_mode_not_enabled(data)
    _assert_forbidden_keys_absent(data)
    _assert_forbidden_text_absent(data)


def _assert_safe_flags(data: dict[str, Any]) -> None:
    for field_name, expected_value in SAFE_FLAGS.items():
        assert data[field_name] is expected_value
    if isinstance(data.get("safety_flags"), dict):
        for field_name, expected_value in SAFE_FLAGS.items():
            assert data["safety_flags"][field_name] is expected_value


def _assert_source_mode_not_enabled(data: dict[str, Any]) -> None:
    serialized = json.dumps(data, ensure_ascii=False)
    assert MT4_SOURCE_MODE not in serialized
    for source_mode in _collect_values_for_key(data, "source_mode"):
        assert source_mode == "docs_fixture_only"
    for source_scope in _collect_values_for_key(data, "source_scope"):
        assert source_scope in {"docs_fixture_only", "demo_readonly_diagnostics_api"}


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


def _collect_values_for_key(value: Any, target_key: str) -> list[Any]:
    if isinstance(value, dict):
        values = [child for key, child in value.items() if key == target_key]
        for child in value.values():
            values.extend(_collect_values_for_key(child, target_key))
        return values
    if isinstance(value, list):
        values: list[Any] = []
        for child in value:
            values.extend(_collect_values_for_key(child, target_key))
        return values
    return []
