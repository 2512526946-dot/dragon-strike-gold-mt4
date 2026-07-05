from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

import app.api.demo_readonly as demo_readonly_api
from app.main import app
from app.schemas.demo_readonly_diagnostics import (
    DEMO_READONLY_DIAGNOSTICS_BLOCKED,
    DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
    DEMO_READONLY_DIAGNOSTICS_READY,
    DEMO_READONLY_INTERNAL_ERROR,
    DEMO_READONLY_SAFETY_FIELD_VIOLATION,
    SOURCE_SCOPE,
)


FORBIDDEN_RESPONSE_KEYS = {
    "order_id",
    "ticket",
    "execute_trade",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
    "auto_trade",
    "can_trade",
    "allow_trade",
    "should_buy",
    "should_sell",
    "buy_now",
    "sell_now",
    "open_position",
    "close_position",
    "suggested_lot",
    "final_lot",
    "override_risk",
    "bypass_gate",
    "ea_command",
    "account_number",
    "password",
    "credential",
    "token",
    "secret",
    "login",
    "raw_payload",
    "raw_account_snapshot",
    "raw_positions_order_history",
    "raw_market_symbol",
}


def test_demo_readonly_diagnostics_api_returns_safe_contract() -> None:
    client = TestClient(app)

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["api_version"] == "1.0"
    assert data["endpoint"] == DEMO_READONLY_DIAGNOSTICS_ENDPOINT
    assert data["source_scope"] == SOURCE_SCOPE
    assert data["validation_stage"]
    assert isinstance(data["component_statuses"], dict)
    assert isinstance(data["readiness_notes"], list)
    assert isinstance(data["next_allowed_stage"], list)
    assert isinstance(data["next_blocked_stage"], list)
    assert data["status_code"] == DEMO_READONLY_DIAGNOSTICS_READY
    assert data["passed"] is True
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)


def test_demo_readonly_diagnostics_api_returns_200_for_summary_blocked(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        lambda: _summary(passed=False, block_reasons=["fixture validation failed"]),
    )
    client = TestClient(app)

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_DIAGNOSTICS_BLOCKED
    assert data["block_reasons"] == ["fixture validation failed"]
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)


def test_demo_readonly_diagnostics_api_handles_summary_exception_safely(
    monkeypatch,
) -> None:
    def raise_summary_error() -> None:
        raise RuntimeError("Traceback C:\\secret\\password should not leak")

    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        raise_summary_error,
    )
    client = TestClient(app)

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 500
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_INTERNAL_ERROR
    _assert_required_safe_flags(data)
    serialized = json.dumps(data)
    assert "Traceback" not in serialized
    assert "C:\\" not in serialized
    assert "password should not leak" not in serialized
    _assert_forbidden_keys_absent(data)


def test_demo_readonly_diagnostics_api_blocks_unsafe_can_execute(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        lambda: _summary(can_execute=True),
    )
    client = TestClient(app)

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_SAFETY_FIELD_VIOLATION
    assert data["can_execute"] is False
    assert "Unsafe safety field value: can_execute." in data["block_reasons"]
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)


def test_demo_readonly_diagnostics_api_blocks_unsafe_is_tradable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        lambda: _summary(is_tradable=True),
    )
    client = TestClient(app)

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_SAFETY_FIELD_VIOLATION
    assert data["is_tradable"] is False
    assert "Unsafe safety field value: is_tradable." in data["block_reasons"]
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)


def test_demo_readonly_diagnostics_api_blocks_missing_safety_field(
    monkeypatch,
) -> None:
    unsafe_summary = _summary()
    delattr(unsafe_summary, "can_execute")
    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        lambda: unsafe_summary,
    )
    client = TestClient(app)

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_SAFETY_FIELD_VIOLATION
    assert "Missing safety field: can_execute." in data["block_reasons"]
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)


def test_demo_readonly_diagnostics_api_sanitizes_raw_payload_fields(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        lambda: _summary(
            bundle_validation_status={
                "passed": True,
                "status_code": "OK",
                "block_reasons": [],
                "warning_reasons": [],
                "read_only": True,
                "demo_only": True,
                "is_tradable": False,
                "can_execute": False,
                "raw_account_snapshot": {"account_number": "demo"},
            },
            component_statuses={
                "account_snapshot": {
                    "passed": True,
                    "status_code": "OK",
                    "block_reasons": [],
                    "warning_reasons": [],
                    "read_only": True,
                    "demo_only": True,
                    "is_tradable": False,
                    "can_execute": False,
                    "order_id": "hidden",
                    "ticket": "hidden",
                    "suggested_lot": 1.0,
                    "raw_payload": {"secret": "hidden"},
                },
                "positions_order_history": {
                    "passed": True,
                    "status_code": "OK",
                    "raw_positions_order_history": [],
                    "ea_command": "hidden",
                },
                "market_symbol": {
                    "passed": True,
                    "status_code": "OK",
                    "raw_market_symbol": {"login": "hidden"},
                    "should_buy": True,
                },
            },
        ),
    )
    client = TestClient(app)

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)


def test_demo_readonly_diagnostics_api_calls_summary_once(monkeypatch) -> None:
    calls = 0

    def fake_summary() -> SimpleNamespace:
        nonlocal calls
        calls += 1
        return _summary()

    monkeypatch.setattr(
        demo_readonly_api,
        "summarize_demo_readonly_docs_fixture_validation",
        fake_summary,
    )
    client = TestClient(app)

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    assert calls == 1
    _assert_required_safe_flags(response.json())


def _summary(**overrides: Any) -> SimpleNamespace:
    values = {
        "passed": True,
        "status_code": "SUMMARY_READY",
        "source_scope": SOURCE_SCOPE,
        "validation_stage": "docs_fixture_bundle_summary",
        "fixture_source": "docs example fixtures only",
        "bundle_validation_status": {
            "passed": True,
            "status_code": "BUNDLE_VALID",
            "block_reasons": [],
            "warning_reasons": [],
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
        },
        "component_statuses": {
            "account_snapshot": {
                "passed": True,
                "status_code": "COMPONENT_VALID",
                "block_reasons": [],
                "warning_reasons": [],
                "read_only": True,
                "demo_only": True,
                "is_tradable": False,
                "can_execute": False,
            }
        },
        "block_reasons": [],
        "warning_reasons": [],
        "readiness_notes": [
            "Diagnostics are read-only.",
            "Diagnostics are not trading permission.",
            "Diagnostics do not generate trading signals.",
        ],
        "next_allowed_stage": ["1P-3 API safety tests"],
        "next_blocked_stage": ["execution_chain"],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _assert_required_safe_flags(data: dict[str, Any]) -> None:
    assert data["read_only"] is True
    assert data["demo_only"] is True
    assert data["is_tradable"] is False
    assert data["can_execute"] is False
    assert data["is_trading_permission"] is False
    assert data["is_execution_instruction"] is False
    assert data["allowed_to_call_ea"] is False
    assert data["allowed_to_modify_risk"] is False


def _assert_forbidden_keys_absent(data: dict[str, Any]) -> None:
    keys = _collect_keys(data)
    for forbidden_key in FORBIDDEN_RESPONSE_KEYS:
        assert forbidden_key not in keys


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
