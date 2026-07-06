from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api.demo_readonly as demo_readonly_api
from app.main import app
from app.services.read_only_diagnostics_explainer import (
    READONLY_EXPLANATION_BLOCKED,
    READONLY_EXPLANATION_INPUT_INVALID,
    READONLY_EXPLANATION_READY,
    READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION,
    READONLY_EXPLANATION_SOURCE_ERROR,
)


ENDPOINT = demo_readonly_api.DEMO_READONLY_EXPLANATION_ENDPOINT

ALLOWED_STATUS_CODES = {
    READONLY_EXPLANATION_READY,
    READONLY_EXPLANATION_BLOCKED,
    READONLY_EXPLANATION_INPUT_INVALID,
    READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION,
    READONLY_EXPLANATION_SOURCE_ERROR,
    demo_readonly_api.READONLY_EXPLANATION_API_ERROR,
}

REQUIRED_RESPONSE_FIELDS = {
    "passed",
    "status_code",
    "report_version",
    "report_type",
    "generated_at",
    "source_scope",
    "input_status_code",
    "input_passed",
    "explanation_scope",
    "overall_explanation",
    "status_explanation",
    "component_explanations",
    "blocker_explanations",
    "warning_explanations",
    "readiness_explanation",
    "next_allowed_stage_explanation",
    "next_blocked_stage_explanation",
    "user_safe_next_steps",
    "user_forbidden_actions",
    "unknowns",
    "safety_flags",
    "block_reasons",
    "warning_reasons",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
    "notes",
}

FORBIDDEN_RESPONSE_KEYS = {
    "raw_payload",
    "account_snapshot",
    "positions_order_history",
    "market_symbol",
    "raw_account_snapshot",
    "raw_positions_order_history",
    "raw_market_symbol",
    "account_number",
    "login",
    "password",
    "credential",
    "token",
    "secret",
    "api_key",
    "key",
    "traceback",
    "stack_trace",
    "system_path",
    "order_id",
    "ticket",
    "buy",
    "sell",
    "open",
    "close",
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
    "trade_signal",
    "trading_action",
}

FORBIDDEN_TEXT = {
    "raw_payload",
    "raw_account_snapshot",
    "raw_positions_order_history",
    "raw_market_symbol",
    "account_number",
    "login",
    "password",
    "credential",
    "token",
    "secret",
    "api_key",
    "traceback",
    "stack trace",
    "raw payload",
    "system_path",
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
    "buy",
    "sell",
    "buy_now",
    "sell_now",
    "open_position",
    "close_position",
    "suggested_lot",
    "final_lot",
    "override_risk",
    "bypass_gate",
    "ea_command",
    "trade_signal",
    "trading_action",
    "c:\\",
    "\\users\\",
    "/users/",
    "/home/",
    ".env",
    ".py",
}

FORBIDDEN_PAGE_ACTION_TEXT = {
    "买入",
    "卖出",
    "开仓",
    "平仓",
    "建议手数",
    "可以交易",
    "允许交易",
    "自动下单",
    "自动交易",
    "执行交易",
    "下单指令",
    "风控放行",
    "绕过风控",
    "should buy",
    "should sell",
    "buy",
    "sell",
    "open position",
    "close position",
    "execute trade",
    "allow trade",
    "can trade",
    "suggested lot",
}


def test_demo_readonly_explanation_api_returns_safe_contract() -> None:
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    data = response.json()
    assert REQUIRED_RESPONSE_FIELDS.issubset(set(data))
    assert data["status_code"] in ALLOWED_STATUS_CODES
    assert data["report_type"] == "read_only_explanation_report"
    assert data["explanation_scope"] == "demo_readonly_diagnostics_summary_only"
    assert data["passed"] is True
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)
    _assert_no_forbidden_text(data)
    _assert_no_page_action_suggestions(data)


def test_demo_readonly_explanation_api_contains_readonly_non_permission_copy() -> None:
    client = TestClient(app)

    data = client.get(ENDPOINT).json()

    assert any(
        "不是交易许可" in item
        for item in data["next_allowed_stage_explanation"]
    )
    assert any(
        "不是执行指令" in item
        for item in data["next_blocked_stage_explanation"]
    )
    serialized = json.dumps(data, ensure_ascii=False)
    assert "非交易许可" in serialized or "不是交易许可" in serialized
    assert "非执行指令" in serialized or "不是执行指令" in serialized
    _assert_required_safe_flags(data)


@pytest.mark.parametrize("method_name", ["post", "put", "patch", "delete"])
def test_demo_readonly_explanation_api_rejects_write_methods(
    method_name: str,
) -> None:
    client = TestClient(app)

    response = getattr(client, method_name)(ENDPOINT)

    assert response.status_code == 405


def test_demo_readonly_explanation_api_does_not_register_websocket_route() -> None:
    websocket_routes = [
        route
        for route in app.routes
        if getattr(route, "path", None) == ENDPOINT
        and getattr(route, "methods", None) is None
    ]

    assert websocket_routes == []


def test_demo_readonly_explanation_api_calls_explainer_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_explainer() -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return _safe_report()

    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        fake_explainer,
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    assert calls == 1
    assert response.json()["status_code"] == READONLY_EXPLANATION_READY


def test_demo_readonly_explanation_api_handles_explainer_exception_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_explainer_error() -> None:
        raise RuntimeError("Traceback C:\\Users\\secret\\password.py should not leak")

    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        raise_explainer_error,
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == demo_readonly_api.READONLY_EXPLANATION_API_ERROR
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)
    _assert_no_forbidden_text(data)


def test_demo_readonly_explanation_api_blocks_unsafe_payload_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(
            raw_payload={
                "account_number": "hidden",
                "password": "hidden",
            },
            component_explanations=[
                {
                    "component_name": "account_snapshot",
                    "status": "passed",
                    "raw_account_snapshot": {"token": "hidden"},
                    "suggested_lot": 1.0,
                }
            ],
        ),
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    assert "Unsafe explanation response content was blocked." in data["block_reasons"]
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)
    _assert_no_forbidden_text(data)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("raw_payload", {"secret": "hidden"}),
        ("account_snapshot", {"equity": 1000}),
        ("positions_order_history", [{"ticket": "hidden"}]),
        ("market_symbol", {"symbol": "XAUUSD"}),
        ("raw_account_snapshot", {"account_number": "hidden"}),
        ("raw_positions_order_history", [{"order_id": "hidden"}]),
        ("raw_market_symbol", {"login": "hidden"}),
        ("account_number", "hidden"),
        ("login", "hidden"),
        ("password", "hidden"),
        ("credential", "hidden"),
        ("token", "hidden"),
        ("secret", "hidden"),
        ("api_key", "hidden"),
        ("key", "hidden"),
        ("traceback", "hidden"),
        ("stack_trace", "hidden"),
        ("system_path", "C:\\Users\\hidden\\secret.py"),
        ("order_id", "hidden"),
        ("ticket", "hidden"),
        ("buy", True),
        ("sell", True),
        ("open", True),
        ("close", True),
        ("execute_trade", True),
        ("order_send", True),
        ("order_close", True),
        ("order_modify", True),
        ("order_delete", True),
        ("auto_trade", True),
        ("can_trade", True),
        ("allow_trade", True),
        ("should_buy", True),
        ("should_sell", True),
        ("buy_now", True),
        ("sell_now", True),
        ("open_position", True),
        ("close_position", True),
        ("suggested_lot", 1.0),
        ("final_lot", 1.0),
        ("override_risk", True),
        ("bypass_gate", True),
        ("ea_command", "hidden"),
        ("trade_signal", "hidden"),
        ("trading_action", "hidden"),
    ],
)
def test_demo_readonly_explanation_api_removes_each_forbidden_field(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    field_value: Any,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(
            component_explanations=[
                {
                    "component_name": "account_snapshot",
                    "status": "passed",
                    "user_impact": "只影响只读诊断展示。",
                    field_name: field_value,
                }
            ],
        ),
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    assert "Unsafe explanation response content was blocked." in data["block_reasons"]
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)
    _assert_no_forbidden_text(data)
    _assert_no_page_action_suggestions(data)


@pytest.mark.parametrize(
    ("field_name", "unsafe_text"),
    [
        ("blocker_explanations", "Traceback C:\\Users\\hidden\\secret.py"),
        ("warning_explanations", "stack trace from /home/hidden/app.py"),
        ("readiness_explanation", "raw payload contains password"),
        ("next_allowed_stage_explanation", "可以交易 should buy now"),
        ("next_blocked_stage_explanation", "execute trade after bypass_gate"),
        ("user_safe_next_steps", "自动下单"),
        ("user_forbidden_actions", "建议手数"),
        ("unknowns", "token=hidden api_key=hidden"),
        ("notes", "buy sell open position close position suggested lot"),
    ],
)
def test_demo_readonly_explanation_api_redacts_unsafe_user_visible_text(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    unsafe_text: str,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(**{field_name: [unsafe_text]}),
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)
    _assert_no_forbidden_text(data)
    _assert_no_page_action_suggestions(data)


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "买入",
        "卖出",
        "开仓",
        "平仓",
        "建议手数",
        "可以交易",
        "允许交易",
        "自动下单",
        "自动交易",
        "执行交易",
        "下单指令",
        "风控放行",
        "绕过风控",
        "buy",
        "sell",
        "should buy",
        "should sell",
        "open position",
        "close position",
        "execute trade",
        "allow trade",
        "can trade",
        "suggested lot",
    ],
)
def test_demo_readonly_explanation_api_redacts_actionable_trading_text(
    monkeypatch: pytest.MonkeyPatch,
    unsafe_text: str,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(status_explanation=unsafe_text),
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    _assert_required_safe_flags(data)
    _assert_no_forbidden_text(data)
    _assert_no_page_action_suggestions(data)


def test_demo_readonly_explanation_api_component_explanations_stay_summary_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(
            component_explanations=[
                {
                    "component_name": "market_symbol",
                    "status": "blocked",
                    "plain_language_summary": "组件处于只读诊断状态。",
                    "user_impact": "只影响只读诊断展示和流程提示。",
                    "account_snapshot": {"account_number": "hidden"},
                    "positions_order_history": [{"ticket": "hidden"}],
                    "market_symbol": {"raw_payload": "hidden"},
                }
            ],
        ),
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    serialized_components = json.dumps(
        data["component_explanations"],
        ensure_ascii=False,
    )
    assert "只读诊断展示" in serialized_components
    assert "account_number" not in serialized_components
    assert "ticket" not in serialized_components
    assert "raw_payload" not in serialized_components
    _assert_required_safe_flags(data)
    _assert_forbidden_keys_absent(data)
    _assert_no_forbidden_text(data)


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
def test_demo_readonly_explanation_api_forces_safety_fields(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    unsafe_value: bool,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(**{field_name: unsafe_value}),
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    assert f"Unsafe safety field value: {field_name}." in data["block_reasons"]
    _assert_required_safe_flags(data)


def test_demo_readonly_explanation_api_blocks_unsafe_safety_flags_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(
            safety_flags={
                "read_only": True,
                "demo_only": True,
                "is_tradable": False,
                "can_execute": True,
                "is_trading_permission": False,
                "is_execution_instruction": False,
                "allowed_to_call_ea": False,
                "allowed_to_modify_risk": False,
            },
        ),
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    assert "Unsafe safety_flags value: can_execute." in data["block_reasons"]
    _assert_required_safe_flags(data)


def test_demo_readonly_explanation_api_blocks_unknown_status_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(status_code="READY_TO_TRADE"),
    )
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    assert "Unsafe explanation status code was blocked." in data["block_reasons"]
    _assert_required_safe_flags(data)


def test_demo_readonly_explanation_api_does_not_write_runtime_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("explanation API must not write runtime files")

    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(),
    )
    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "touch", fail_if_called)
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    assert response.json()["status_code"] == READONLY_EXPLANATION_READY


def test_demo_readonly_explanation_api_does_not_open_runtime_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("explanation API must not open runtime files")

    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(),
    )
    monkeypatch.setattr(Path, "open", fail_if_called)
    monkeypatch.setattr(Path, "read_text", fail_if_called)
    monkeypatch.setattr(Path, "read_bytes", fail_if_called)
    client = TestClient(app)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    assert response.json()["status_code"] == READONLY_EXPLANATION_READY


def test_demo_readonly_explanation_api_does_not_create_network_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("explanation API must not access network")

    monkeypatch.setattr(
        demo_readonly_api,
        "explain_demo_readonly_docs_fixture_diagnostics",
        lambda: _safe_report(),
    )
    monkeypatch.setattr(socket, "socket", fail_if_called)

    data = demo_readonly_api.get_demo_readonly_explanation()

    assert data["status_code"] == READONLY_EXPLANATION_READY
    _assert_required_safe_flags(data)


def _safe_report(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "passed": True,
        "status_code": READONLY_EXPLANATION_READY,
        "report_version": "1.0",
        "report_type": "read_only_explanation_report",
        "generated_at": "2026-07-07T00:00:00Z",
        "source_scope": "demo_readonly_diagnostics_api",
        "input_status_code": "DEMO_READONLY_DIAGNOSTICS_READY",
        "input_passed": True,
        "explanation_scope": "demo_readonly_diagnostics_summary_only",
        "overall_explanation": "当前只读诊断摘要可解释，非交易许可，非执行指令。",
        "status_explanation": "当前解释只用于安全展示。",
        "component_explanations": [
            {
                "component_name": "account_snapshot",
                "status": "passed",
                "status_code": "ACCOUNT_VALID",
                "plain_language_summary": "组件处于只读诊断状态。",
                "block_reasons_explained": ["该组件没有可展示的阻断原因。"],
                "warning_reasons_explained": ["该组件没有可展示的警告原因。"],
                "user_impact": "只影响只读诊断展示。",
                "safe_next_step": "查看只读诊断。",
                "forbidden_interpretation": "不能解释成交易许可或执行指令。",
            }
        ],
        "blocker_explanations": ["当前没有可展示的阻断原因。"],
        "warning_explanations": ["当前没有可展示的警告原因。"],
        "readiness_explanation": ["只读 readiness 说明：诊断可展示。"],
        "next_allowed_stage_explanation": [
            "readonly_explainer_review 是流程提示，不是交易许可。"
        ],
        "next_blocked_stage_explanation": [
            "仍存在后续阶段限制：execution_chain。这不是执行指令。"
        ],
        "user_safe_next_steps": ["查看只读解释", "查看只读诊断"],
        "user_forbidden_actions": ["任何交易性操作仍被禁止", "任何执行链路仍被禁止"],
        "unknowns": [],
        "safety_flags": {
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
            "is_trading_permission": False,
            "is_execution_instruction": False,
            "allowed_to_call_ea": False,
            "allowed_to_modify_risk": False,
        },
        "block_reasons": [],
        "warning_reasons": [],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
        "notes": [
            "只读解释 API 只解释安全摘要。",
            "非交易许可，非执行指令。",
            "交易能力禁用，执行能力禁用。",
        ],
    }
    values.update(overrides)
    return values


def _assert_required_safe_flags(data: dict[str, Any]) -> None:
    assert data["read_only"] is True
    assert data["demo_only"] is True
    assert data["is_tradable"] is False
    assert data["can_execute"] is False
    assert data["is_trading_permission"] is False
    assert data["is_execution_instruction"] is False
    assert data["allowed_to_call_ea"] is False
    assert data["allowed_to_modify_risk"] is False
    assert data["safety_flags"] == {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }


def _assert_forbidden_keys_absent(value: Any) -> None:
    keys = _collect_keys(value)
    for forbidden_key in FORBIDDEN_RESPONSE_KEYS:
        assert forbidden_key not in keys


def _assert_no_forbidden_text(value: Any) -> None:
    serialized = json.dumps(value, ensure_ascii=False).casefold()
    for forbidden_text in FORBIDDEN_TEXT:
        assert forbidden_text.casefold() not in serialized


def _assert_no_page_action_suggestions(value: Any) -> None:
    serialized = json.dumps(value, ensure_ascii=False).casefold()
    for forbidden_text in FORBIDDEN_PAGE_ACTION_TEXT:
        assert forbidden_text.casefold() not in serialized


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()
