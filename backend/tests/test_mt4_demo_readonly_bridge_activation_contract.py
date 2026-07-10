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

FORBIDDEN_RESPONSE_KEYS = {
    "account_number",
    "account_path",
    "allow_trade",
    "auto_trade_enabled",
    "base_dir",
    "bridge_dir",
    "buy_signal",
    "can_trade",
    "candidate_path",
    "ea_command",
    "entry_price",
    "execution_allowed",
    "execution_plan",
    "live_trade_enabled",
    "login",
    "lot_size",
    "order_allowed",
    "password",
    "position_size",
    "profile_path",
    "raw_payload",
    "sell_signal",
    "server",
    "stop_loss",
    "system_path",
    "take_profit",
    "terminal_path",
    "token",
    "traceback",
    "trade_allowed",
    "trade_plan",
}

FORBIDDEN_TEXT_MARKERS = (FORBIDDEN_RESPONSE_KEYS - {"server"}) | {
    r"c:\\",
    "\\users\\",
    "/home/",
    "/users/",
    "/var/",
    ".env",
    "stack trace",
    "raw payload",
    "OrderSend",
    "OrderClose",
    "OrderModify",
    "OrderDelete",
    "should_buy",
    "should_sell",
    "suggested_lot",
}


@pytest.fixture()
def activation_contract_harness(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, list[object]]:
    source_config_calls: list[object] = []

    def safe_source_config_guard(config: object) -> dict[str, Any]:
        source_config_calls.append(config)
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
        _safe_docs_fixture_summary,
    )
    return TestClient(app), source_config_calls


def test_default_diagnostics_keeps_docs_fixture_reader_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_no_reader_guard(monkeypatch)
    client = TestClient(app)

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "docs_fixture_only_ready"
    assert data["source_config_passed"] is True
    assert data["reader_status"] == "not_called"
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == "READER_NOT_CALLED"
    _assert_not_trading_permission(data)
    _assert_bridge_activation_output_safe(data)


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {
            "params": {
                "source_mode": MT4_SOURCE_MODE,
                "mt4_demo_readonly_file_bridge_enabled": "true",
                "bridge_dir": r"C:\Users\hidden\TradeMax\bridge",
                "base_dir": "/home/hidden/bridge",
                "candidate_path": "/home/hidden/account_snapshot.json",
            },
        },
        {
            "headers": {
                "X-Source-Mode": MT4_SOURCE_MODE,
                "X-MT4-Demo-Readonly-File-Bridge-Enabled": "true",
                "X-Bridge-Dir": r"C:\Users\hidden\TradeMax\bridge",
                "X-Base-Dir": "/home/hidden/bridge",
                "X-Candidate-Path": "/home/hidden/account_snapshot.json",
            },
        },
        {
            "json": {
                "source_mode": MT4_SOURCE_MODE,
                "mt4_demo_readonly_file_bridge_enabled": True,
                "bridge_dir": r"C:\Users\hidden\TradeMax\bridge",
                "base_dir": "/home/hidden/bridge",
                "candidate_path": "/home/hidden/account_snapshot.json",
                "raw_payload": {"password": "hidden"},
            },
        },
    ],
)
def test_client_input_cannot_activate_reader_or_change_source_config(
    activation_contract_harness: tuple[TestClient, list[object]],
    request_kwargs: dict[str, Any],
) -> None:
    client, source_config_calls = activation_contract_harness

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
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == "READER_NOT_CALLED"
    _assert_not_trading_permission(data)
    _assert_bridge_activation_output_safe(data)


def test_bridge_path_and_account_details_are_never_exposed(
    activation_contract_harness: tuple[TestClient, list[object]],
) -> None:
    client, _source_config_calls = activation_contract_harness

    response = _guarded_request(
        client,
        DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
        params={
            "bridge_dir": r"C:\Users\86135\AppData\Roaming\MetaQuotes\Terminal",
            "base_dir": "/Users/hidden/MetaTrader",
            "candidate_path": "/home/hidden/terminal/account_snapshot.json",
            "account_number": "123456",
            "login": "demo-login",
            "password": "demo-password",
            "server": "TradeMax-Demo",
        },
    )

    assert response.status_code == 200
    _assert_bridge_activation_output_safe(response.json())


def test_readiness_and_source_status_are_not_trading_permission(
    activation_contract_harness: tuple[TestClient, list[object]],
) -> None:
    client, _source_config_calls = activation_contract_harness

    response = _guarded_request(client, DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["source_config_passed"] is True
    assert data["reader_passed"] is False
    assert data["reader_status"] == "not_called"
    _assert_not_trading_permission(data)
    _assert_bridge_activation_output_safe(data)


def test_unsafe_reader_guard_selection_without_server_config_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_no_reader_guard(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "validate_demo_readonly_source_config",
        lambda _config: {
            **_safe_source_config_guard_result(),
            "passed": True,
            "status_code": "MT4_DEMO_READONLY_SOURCE_CONFIG_READY",
            "selected_source_mode": MT4_SOURCE_MODE,
            "source_status": "mt4_demo_readonly_file_bridge_ready",
        },
        raising=False,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        _safe_docs_fixture_summary,
    )
    client = TestClient(app)

    response = _guarded_request(client, DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "source_config_safety_blocked"
    assert data["source_config_passed"] is False
    assert data["reader_status"] == "not_called"
    assert "source_config_server_mismatch_blocked" in data["block_reasons"]
    _assert_not_trading_permission(data)
    _assert_bridge_activation_output_safe(data)


def _install_no_reader_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("bridge activation contract must not call reader")

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
            "bridge activation contract must not touch files, env, or network"
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


def _safe_docs_fixture_summary() -> SimpleNamespace:
    safe_status = {
        "passed": True,
        "status_code": "BRIDGE_ACTIVATION_CONTRACT_SAFE",
        "block_reasons": [],
        "warning_reasons": [],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }
    return SimpleNamespace(
        passed=True,
        status_code="SUMMARY_READY",
        source_scope="docs_fixture_only",
        validation_stage="bridge_activation_contract",
        fixture_source="docs_fixture_only",
        bundle_validation_status=safe_status,
        component_statuses={"bridge_activation_contract": safe_status},
        block_reasons=[],
        warning_reasons=[],
        readiness_notes=[
            "Diagnostics remain docs fixture only by default.",
            "Readiness is not trading permission.",
            "Diagnostics do not generate trading signals.",
        ],
        next_allowed_stage=["read_only_contract_review"],
        next_blocked_stage=["execution_chain"],
        **SAFE_FLAGS,
    )


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
            "Server-side source config keeps the docs fixture default.",
            "Source readiness is not trading permission.",
        ],
        **SAFE_FLAGS,
    }


def _assert_not_trading_permission(data: dict[str, Any]) -> None:
    for field_name, expected_value in SAFE_FLAGS.items():
        assert data[field_name] is expected_value

    forbidden_keys = _collect_keys(data)
    for forbidden_key in {
        "can_trade",
        "trade_allowed",
        "order_allowed",
        "execution_allowed",
        "auto_trade_enabled",
        "live_trade_enabled",
        "buy_signal",
        "sell_signal",
        "position_size",
        "stop_loss",
        "take_profit",
        "lot_size",
        "entry_price",
        "trade_plan",
        "execution_plan",
    }:
        assert forbidden_key not in forbidden_keys


def _assert_bridge_activation_output_safe(data: dict[str, Any]) -> None:
    serialized = json.dumps(data, ensure_ascii=False).casefold()
    keys = _collect_keys(data)

    for forbidden_key in FORBIDDEN_RESPONSE_KEYS:
        assert forbidden_key.casefold() not in keys

    for forbidden_marker in FORBIDDEN_TEXT_MARKERS:
        assert forbidden_marker.casefold() not in serialized


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = {key.casefold() for key in value}
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()
