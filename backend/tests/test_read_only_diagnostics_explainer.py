from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import app.services.read_only_diagnostics_explainer as explainer_module
from app.services.read_only_diagnostics_explainer import (
    READONLY_EXPLANATION_BLOCKED,
    READONLY_EXPLANATION_INPUT_INVALID,
    READONLY_EXPLANATION_READY,
    READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION,
    explain_demo_readonly_docs_fixture_diagnostics,
    explain_readonly_diagnostics_summary,
)


FORBIDDEN_KEYS = {
    "account_number",
    "login",
    "password",
    "credential",
    "token",
    "secret",
    "raw_payload",
    "suggested_lot",
    "final_lot",
    "buy_now",
    "sell_now",
    "should_buy",
    "should_sell",
    "open_position",
    "close_position",
    "order_id",
    "ticket",
    "ea_command",
}

FORBIDDEN_TEXT = {
    "suggested_lot",
    "final_lot",
    "buy_now",
    "sell_now",
    "should_buy",
    "should_sell",
    "open_position",
    "close_position",
    "ea_command",
}


def test_summary_passed_returns_ready_explanation() -> None:
    result = explain_readonly_diagnostics_summary(_summary(passed=True))

    assert result["passed"] is True
    assert result["status_code"] == READONLY_EXPLANATION_READY
    assert "当前只读诊断摘要可解释" in result["overall_explanation"]
    _assert_safety_fields(result)


def test_summary_blocked_returns_blocked_explanation() -> None:
    result = explain_readonly_diagnostics_summary(
        _summary(passed=False, block_reasons=["bundle validation failed"]),
    )

    assert result["passed"] is False
    assert result["status_code"] == READONLY_EXPLANATION_BLOCKED
    assert result["block_reasons"] == ["bundle validation failed"]
    assert any("bundle validation failed" in item for item in result["blocker_explanations"])
    _assert_safety_fields(result)


def test_summary_missing_required_field_returns_input_invalid() -> None:
    summary = _summary()
    del summary["passed"]

    result = explain_readonly_diagnostics_summary(summary)

    assert result["passed"] is False
    assert result["status_code"] == READONLY_EXPLANATION_INPUT_INVALID
    assert "Missing required summary field: passed." in result["unknowns"]
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "field_name",
    [
        "can_execute",
        "is_tradable",
        "is_trading_permission",
        "is_execution_instruction",
        "allowed_to_call_ea",
        "allowed_to_modify_risk",
    ],
)
def test_unsafe_true_safety_fields_return_safety_violation(field_name: str) -> None:
    result = explain_readonly_diagnostics_summary(_summary(**{field_name: True}))

    assert result["passed"] is False
    assert result["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    assert f"Unsafe safety field value: {field_name}." in result["block_reasons"]
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    [
        ("read_only", False),
        ("demo_only", False),
    ],
)
def test_unsafe_false_safety_fields_return_safety_violation(
    field_name: str,
    unsafe_value: bool,
) -> None:
    result = explain_readonly_diagnostics_summary(
        _summary(**{field_name: unsafe_value}),
    )

    assert result["passed"] is False
    assert result["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    assert f"Unsafe safety field value: {field_name}." in result["block_reasons"]
    _assert_safety_fields(result)


def test_output_contains_required_report_sections() -> None:
    result = explain_readonly_diagnostics_summary(_summary())

    for key in (
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
        "notes",
    ):
        assert key in result


def test_component_explanations_cover_expected_components() -> None:
    result = explain_readonly_diagnostics_summary(_summary())

    component_names = {
        component["component_name"]
        for component in result["component_explanations"]
    }
    assert component_names == {
        "account_snapshot",
        "positions_order_history",
        "market_symbol",
        "bundle_validation",
        "diagnostics_api",
        "frontend_dashboard_safety",
    }
    for component in result["component_explanations"]:
        assert "plain_language_summary" in component
        assert "block_reasons_explained" in component
        assert "warning_reasons_explained" in component
        assert "user_impact" in component
        assert "safe_next_step" in component
        assert "forbidden_interpretation" in component
        assert "展示" in component["user_impact"] or "诊断" in component["user_impact"]
        assert "交易许可" in component["forbidden_interpretation"]


def test_safe_next_steps_are_non_executing_review_actions() -> None:
    result = explain_readonly_diagnostics_summary(_summary())

    assert "查看只读诊断" in result["user_safe_next_steps"]
    assert "刷新只读诊断" in result["user_safe_next_steps"]
    assert "进行安全回归检查" in result["user_safe_next_steps"]
    serialized_steps = json.dumps(result["user_safe_next_steps"], ensure_ascii=False)
    for unsafe_text in ("建议手数", "自动下单", "执行交易", "下单指令"):
        assert unsafe_text not in serialized_steps


def test_forbidden_actions_are_safe_limit_descriptions() -> None:
    result = explain_readonly_diagnostics_summary(_summary())

    assert result["user_forbidden_actions"]
    assert all("禁止" in action for action in result["user_forbidden_actions"])
    serialized_actions = json.dumps(result["user_forbidden_actions"], ensure_ascii=False)
    for unsafe_text in ("建议手数", "自动下单", "执行交易", "下单指令"):
        assert unsafe_text not in serialized_actions


def test_output_does_not_expose_raw_payload_or_sensitive_fields() -> None:
    result = explain_readonly_diagnostics_summary(
        _summary(
            component_statuses={
                "account_snapshot": {
                    "passed": True,
                    "status_code": "OK",
                    "block_reasons": [],
                    "warning_reasons": [],
                    "raw_payload": {"account_number": "hidden"},
                    "password": "hidden",
                    "suggested_lot": 1.0,
                    "ea_command": "hidden",
                }
            }
        ),
    )

    assert result["status_code"] == READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
    _assert_forbidden_keys_absent(result)
    _assert_forbidden_text_absent(result)


def test_output_redacts_forbidden_text_in_reason_lists() -> None:
    result = explain_readonly_diagnostics_summary(
        _summary(
            warning_reasons=["should_buy must not leak"],
            block_reasons=["ea_command must not leak"],
        ),
    )

    assert "[redacted unsafe content]" in result["block_reasons"]
    assert "[redacted unsafe content]" in result["warning_reasons"]
    _assert_forbidden_text_absent(result)


def test_next_allowed_stage_is_not_trading_permission() -> None:
    result = explain_readonly_diagnostics_summary(_summary())

    assert all(
        "不是交易许可" in explanation
        for explanation in result["next_allowed_stage_explanation"]
    )


def test_next_blocked_stage_is_not_execution_instruction() -> None:
    result = explain_readonly_diagnostics_summary(_summary())

    assert all(
        "不是执行指令" in explanation
        for explanation in result["next_blocked_stage_explanation"]
    )


def test_explain_demo_readonly_docs_fixture_diagnostics_calls_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_summary() -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return _summary()

    monkeypatch.setattr(
        explainer_module.summary_service,
        "summarize_demo_readonly_docs_fixture_validation",
        fake_summary,
    )

    result = explain_demo_readonly_docs_fixture_diagnostics()

    assert calls == 1
    assert result["status_code"] == READONLY_EXPLANATION_READY
    _assert_safety_fields(result)


def test_explain_demo_readonly_docs_fixture_diagnostics_handles_summary_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_summary_error() -> None:
        raise RuntimeError("Traceback C:\\secret\\password must not leak")

    monkeypatch.setattr(
        explainer_module.summary_service,
        "summarize_demo_readonly_docs_fixture_validation",
        raise_summary_error,
    )

    result = explain_demo_readonly_docs_fixture_diagnostics()

    assert result["passed"] is False
    assert result["status_code"] == READONLY_EXPLANATION_INPUT_INVALID
    assert "Summary service failed safely." in result["block_reasons"]
    _assert_safety_fields(result)
    serialized = json.dumps(result)
    assert "Traceback" not in serialized
    assert "password must not leak" not in serialized
    assert "C:\\" not in serialized


def test_explainer_does_not_write_files(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("explainer must not write files")

    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "touch", fail_if_called)

    result = explain_readonly_diagnostics_summary(_summary())

    assert result["status_code"] == READONLY_EXPLANATION_READY


def test_explainer_does_not_return_runtime_data_paths() -> None:
    result = explain_readonly_diagnostics_summary(_summary())
    serialized = json.dumps(result).casefold()

    assert "data/mt4" not in serialized
    assert ".env" not in serialized
    assert "placeholder_signals.jsonl" not in serialized


def test_explainer_does_not_call_llm_network_or_mt4(monkeypatch: pytest.MonkeyPatch) -> None:
    forbidden_calls: list[str] = []

    def record_forbidden_call(*args: object, **kwargs: object) -> None:
        forbidden_calls.append("called")

    monkeypatch.setattr(Path, "read_text", record_forbidden_call)

    result = explain_readonly_diagnostics_summary(_summary())

    assert result["status_code"] == READONLY_EXPLANATION_READY
    assert forbidden_calls == []
    serialized = json.dumps(result).casefold()
    assert "llm" not in serialized
    assert "prompt executor" not in serialized
    assert "mt4 command" not in serialized


def _summary(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "passed": True,
        "status_code": "SUMMARY_READY",
        "source_scope": "docs_fixture_only",
        "component_statuses": {
            "account_snapshot": {
                "passed": True,
                "status_code": "ACCOUNT_VALID",
                "block_reasons": [],
                "warning_reasons": [],
                "read_only": True,
                "demo_only": True,
                "is_tradable": False,
                "can_execute": False,
            },
            "positions_order_history": {
                "passed": True,
                "status_code": "POSITIONS_VALID",
                "block_reasons": [],
                "warning_reasons": [],
                "read_only": True,
                "demo_only": True,
                "is_tradable": False,
                "can_execute": False,
            },
            "market_symbol": {
                "passed": True,
                "status_code": "MARKET_VALID",
                "block_reasons": [],
                "warning_reasons": [],
                "read_only": True,
                "demo_only": True,
                "is_tradable": False,
                "can_execute": False,
            },
        },
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
        "block_reasons": [],
        "warning_reasons": [],
        "readiness_notes": [
            "Diagnostics are read-only.",
            "Diagnostics are not trading permission.",
        ],
        "next_allowed_stage": ["readonly_explainer_review"],
        "next_blocked_stage": ["execution_chain"],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }
    values.update(overrides)
    return values


def _assert_safety_fields(result: dict[str, Any]) -> None:
    assert result["read_only"] is True
    assert result["demo_only"] is True
    assert result["is_tradable"] is False
    assert result["can_execute"] is False
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["allowed_to_call_ea"] is False
    assert result["allowed_to_modify_risk"] is False
    assert result["safety_flags"] == {
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
    for forbidden_key in FORBIDDEN_KEYS:
        assert forbidden_key not in keys


def _assert_forbidden_text_absent(value: Any) -> None:
    serialized = json.dumps(value).casefold()
    for forbidden_text in FORBIDDEN_TEXT:
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
