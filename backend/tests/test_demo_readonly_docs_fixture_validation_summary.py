from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from app.services.demo_readonly_docs_fixture_bundle_validation import (
    BUNDLE_VALIDATION_FAILED,
    BUNDLE_VALIDATION_OK,
    DemoReadOnlyDocsFixtureBundleValidationResult,
)
from app.services.demo_readonly_docs_fixture_reader import (
    ACCOUNT_SNAPSHOT,
    MARKET_SYMBOL,
    POSITIONS_ORDER_HISTORY,
)
from app.services.demo_readonly_docs_fixture_validation_summary import (
    SOURCE_SCOPE,
    SUMMARY_READY,
    SUMMARY_VALIDATION_FAILED,
    VALIDATION_STAGE,
    DemoReadOnlyDocsFixtureValidationSummary,
    summarize_demo_readonly_docs_fixture_validation,
)


FORBIDDEN_RESULT_FIELDS = {
    "can_trade",
    "allow_trade",
    "execution_permission",
    "suggested_lot",
    "final_lot",
    "buy",
    "sell",
    "open",
    "close",
    "ea_command",
    "OrderSend",
    "OrderClose",
    "OrderModify",
    "OrderDelete",
}


def _bundle_validation_result(
    *,
    passed: bool = True,
    status_code: str = BUNDLE_VALIDATION_OK,
    block_reasons: list[str] | None = None,
    warning_reasons: list[str] | None = None,
    bundle_result: dict[str, Any] | None = None,
) -> DemoReadOnlyDocsFixtureBundleValidationResult:
    if bundle_result is None:
        bundle_result = {
            "passed": passed,
            "status_code": "DEMO_READONLY_BUNDLE_VALID" if passed else "DEMO_READONLY_BUNDLE_INVALID",
            "block_reasons": block_reasons or [],
            "warning_reasons": warning_reasons or [],
            "component_results": {
                ACCOUNT_SNAPSHOT: {
                    "passed": passed,
                    "status_code": "ACCOUNT_STATUS",
                    "block_reasons": block_reasons or [],
                    "warning_reasons": [],
                    "is_tradable": False,
                    "can_execute": False,
                },
                POSITIONS_ORDER_HISTORY: {
                    "passed": True,
                    "status_code": "POSITIONS_STATUS",
                    "block_reasons": [],
                    "warning_reasons": [],
                    "is_tradable": False,
                    "can_execute": False,
                },
                MARKET_SYMBOL: {
                    "passed": True,
                    "status_code": "MARKET_STATUS",
                    "block_reasons": [],
                    "warning_reasons": [],
                    "is_tradable": False,
                    "can_execute": False,
                },
            },
            "cross_checks": {},
            "is_tradable": False,
            "can_execute": False,
        }

    return DemoReadOnlyDocsFixtureBundleValidationResult(
        passed=passed,
        status_code=status_code,
        reader_result={"passed": True, "status_code": "READER_OK"},
        bundle_result=bundle_result,
        account_snapshot={"raw": "must not be exposed"},
        positions_order_history={"raw": "must not be exposed"},
        market_symbol={"raw": "must not be exposed"},
        block_reasons=block_reasons or [],
        warning_reasons=warning_reasons or [],
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


def _assert_safety_fields(result: DemoReadOnlyDocsFixtureValidationSummary) -> None:
    assert result.read_only is True
    assert result.demo_only is True
    assert result.is_tradable is False
    assert result.can_execute is False


def _assert_no_forbidden_result_fields(value: Any) -> None:
    if isinstance(value, dict):
        assert FORBIDDEN_RESULT_FIELDS.isdisjoint(value)
        for child_value in value.values():
            _assert_no_forbidden_result_fields(child_value)
        return

    if isinstance(value, list):
        for child_value in value:
            _assert_no_forbidden_result_fields(child_value)


def test_summary_calls_bundle_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"bundle": False}

    def fake_bundle_validation() -> DemoReadOnlyDocsFixtureBundleValidationResult:
        called["bundle"] = True
        return _bundle_validation_result()

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_validation_summary.validate_demo_readonly_docs_fixture_bundle",
        fake_bundle_validation,
    )

    result = summarize_demo_readonly_docs_fixture_validation()

    assert called["bundle"] is True
    assert result.passed is True


def test_bundle_passed_returns_ready_summary() -> None:
    result = summarize_demo_readonly_docs_fixture_validation()

    assert isinstance(result, DemoReadOnlyDocsFixtureValidationSummary)
    assert result.passed is True
    assert result.status_code == SUMMARY_READY
    assert result.source_scope == SOURCE_SCOPE
    assert result.validation_stage == VALIDATION_STAGE
    assert "docs example fixtures" in result.fixture_source
    assert "not real demo account" in result.fixture_source
    assert "not real MT4 data" in result.fixture_source
    assert result.bundle_validation_status["passed"] is True
    assert set(result.component_statuses) == {
        ACCOUNT_SNAPSHOT,
        POSITIONS_ORDER_HISTORY,
        MARKET_SYMBOL,
    }
    assert result.block_reasons == []
    _assert_safety_fields(result)


def test_bundle_failure_returns_blocked_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_validation_summary.validate_demo_readonly_docs_fixture_bundle",
        lambda: _bundle_validation_result(
            passed=False,
            status_code=BUNDLE_VALIDATION_FAILED,
            block_reasons=["bundle validation failed: symbols must be consistent"],
        ),
    )

    result = summarize_demo_readonly_docs_fixture_validation()

    assert result.passed is False
    assert result.status_code == SUMMARY_VALIDATION_FAILED
    assert (
        "bundle validation failed: symbols must be consistent"
        in result.block_reasons
    )
    assert result.bundle_validation_status["passed"] is False
    _assert_safety_fields(result)


def test_summary_contains_readiness_and_next_stage_notes() -> None:
    result = summarize_demo_readonly_docs_fixture_validation()

    assert result.readiness_notes
    assert any("docs fixture summary" in note for note in result.readiness_notes)
    assert any("not a backend API" in note for note in result.readiness_notes)
    assert any("not frontend display" in note for note in result.readiness_notes)
    assert any("not trading permission" in note for note in result.readiness_notes)
    assert any("not execution permission" in note for note in result.readiness_notes)
    assert any("cannot place orders automatically" in note for note in result.readiness_notes)
    assert any("cannot connect to a real account" in note for note in result.readiness_notes)
    assert any("cannot connect to a demo account" in note for note in result.readiness_notes)
    assert "demo_readonly_fixture_summary_review" in result.next_allowed_stage
    assert "demo_readonly_api_planning" in result.next_allowed_stage
    assert "real_mt4_connection" in result.next_blocked_stage
    assert "demo_account_connection" in result.next_blocked_stage
    assert "live_account_connection" in result.next_blocked_stage
    assert "auto_trading" in result.next_blocked_stage
    assert "execution_api" in result.next_blocked_stage


def test_summary_does_not_return_raw_payloads_or_trade_fields() -> None:
    result = summarize_demo_readonly_docs_fixture_validation()
    result_dict = asdict(result)

    _assert_no_forbidden_result_fields(result_dict)
    assert "account_snapshot" not in result_dict
    assert "positions_order_history" not in result_dict
    assert "market_symbol" not in result_dict
    serialized = repr(result_dict)
    assert "must not be exposed" not in serialized
    assert "symbol_snapshot" not in serialized
    assert "open_positions" not in serialized
    assert "quote" not in serialized


def test_warning_does_not_enable_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_validation_summary.validate_demo_readonly_docs_fixture_bundle",
        lambda: _bundle_validation_result(
            warning_reasons=["summary warning only"],
        ),
    )

    result = summarize_demo_readonly_docs_fixture_validation()

    assert result.passed is True
    assert "summary warning only" in result.warning_reasons
    assert result.bundle_validation_status["warning_reasons"] == [
        "summary warning only"
    ]
    _assert_safety_fields(result)


def test_unavailable_component_statuses_are_not_treated_as_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_validation_summary.validate_demo_readonly_docs_fixture_bundle",
        lambda: _bundle_validation_result(bundle_result={}),
    )

    result = summarize_demo_readonly_docs_fixture_validation()

    assert set(result.component_statuses) == {
        ACCOUNT_SNAPSHOT,
        POSITIONS_ORDER_HISTORY,
        MARKET_SYMBOL,
    }
    for component_status in result.component_statuses.values():
        assert component_status["read_only"] is True
        assert component_status["demo_only"] is True
        assert component_status["is_tradable"] is False
        assert component_status["can_execute"] is False
    _assert_safety_fields(result)


def test_summary_does_not_write_files_or_access_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("summary must not write files or access network")

    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "touch", fail_if_called)

    result = summarize_demo_readonly_docs_fixture_validation()

    assert result.passed is True
    _assert_safety_fields(result)


def test_summary_does_not_expose_fixture_paths_as_data_runtime_paths() -> None:
    result = summarize_demo_readonly_docs_fixture_validation()
    result_text = repr(asdict(result))

    assert "data/mt4" not in result_text
    assert ".env" not in result_text
    assert "placeholder_signals.jsonl" not in result_text
