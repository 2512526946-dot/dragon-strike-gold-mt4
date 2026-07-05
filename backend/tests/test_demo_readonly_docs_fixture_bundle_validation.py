from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from app.services.demo_readonly_docs_fixture_bundle_validation import (
    BUNDLE_VALIDATION_FAILED,
    BUNDLE_VALIDATION_OK,
    BUNDLE_VALIDATION_READER_FAILED,
    DemoReadOnlyDocsFixtureBundleValidationResult,
    validate_demo_readonly_docs_fixture_bundle,
)
from app.services.demo_readonly_docs_fixture_reader import (
    ACCOUNT_SNAPSHOT,
    MARKET_SYMBOL,
    POSITIONS_ORDER_HISTORY,
    DemoReadOnlyDocsFixturesReadAllResult,
    read_all_demo_readonly_docs_fixtures,
)
from app.services.demo_readonly_validation_bundle import (
    DEMO_READONLY_BUNDLE_INVALID,
    DEMO_READONLY_BUNDLE_VALID,
    DemoReadOnlyValidationBundleResult,
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


def _reader_failure() -> DemoReadOnlyDocsFixturesReadAllResult:
    return DemoReadOnlyDocsFixturesReadAllResult(
        passed=False,
        status_code="DEMO_READONLY_FIXTURES_READ_FAILED",
        fixtures={},
        account_snapshot=None,
        positions_order_history=None,
        market_symbol=None,
        block_reasons=["docs fixture reader blocked by test"],
        warning_reasons=[],
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


def _bundle_result(
    *,
    passed: bool = True,
    status_code: str = DEMO_READONLY_BUNDLE_VALID,
    block_reasons: list[str] | None = None,
    warning_reasons: list[str] | None = None,
    is_tradable: bool = False,
    can_execute: bool = False,
) -> DemoReadOnlyValidationBundleResult:
    return DemoReadOnlyValidationBundleResult(
        passed=passed,
        status_code=status_code,
        block_reasons=block_reasons or [],
        warning_reasons=warning_reasons or [],
        component_results={
            ACCOUNT_SNAPSHOT: {"passed": True},
            POSITIONS_ORDER_HISTORY: {"passed": True},
            MARKET_SYMBOL: {"passed": True},
        },
        cross_checks={
            "demo_only_consistent": True,
            "live_account_absent": True,
            "password_absent": True,
            "credentials_absent": True,
            "can_execute": False,
            "can_execute_absent": True,
            "is_tradable": False,
            "is_tradable_absent": True,
            "symbol_consistent": True,
            "account_alias_consistent": True,
        },
        is_tradable=is_tradable,
        can_execute=can_execute,
    )


def _assert_safety_fields(
    result: DemoReadOnlyDocsFixtureBundleValidationResult,
) -> None:
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


def test_docs_fixtures_pass_bundle_validation() -> None:
    result = validate_demo_readonly_docs_fixture_bundle()

    assert isinstance(result, DemoReadOnlyDocsFixtureBundleValidationResult)
    assert result.passed is True
    assert result.status_code == BUNDLE_VALIDATION_OK
    assert result.reader_result["passed"] is True
    assert result.bundle_result is not None
    assert result.bundle_result["passed"] is True
    assert result.bundle_result["status_code"] == DEMO_READONLY_BUNDLE_VALID
    assert isinstance(result.account_snapshot, dict)
    assert isinstance(result.positions_order_history, dict)
    assert isinstance(result.market_symbol, dict)
    assert result.block_reasons == []
    _assert_safety_fields(result)


def test_success_calls_bundle_with_three_docs_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_bundle: dict[str, Any] = {}

    def fake_bundle_validator(bundle: dict[str, Any]) -> DemoReadOnlyValidationBundleResult:
        captured_bundle.update(bundle)
        return _bundle_result()

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_bundle_validation.validate_demo_readonly_bundle",
        fake_bundle_validator,
    )

    result = validate_demo_readonly_docs_fixture_bundle()

    assert result.passed is True
    assert set(captured_bundle) == {
        ACCOUNT_SNAPSHOT,
        POSITIONS_ORDER_HISTORY,
        MARKET_SYMBOL,
    }
    assert captured_bundle[ACCOUNT_SNAPSHOT] == result.account_snapshot
    assert captured_bundle[POSITIONS_ORDER_HISTORY] == result.positions_order_history
    assert captured_bundle[MARKET_SYMBOL] == result.market_symbol
    _assert_safety_fields(result)


def test_reader_failure_returns_failure_without_calling_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("bundle validation must not run when reader fails")

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_bundle_validation.read_all_demo_readonly_docs_fixtures",
        _reader_failure,
    )
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_bundle_validation.validate_demo_readonly_bundle",
        fail_if_called,
    )

    result = validate_demo_readonly_docs_fixture_bundle()

    assert result.passed is False
    assert result.status_code == BUNDLE_VALIDATION_READER_FAILED
    assert result.bundle_result is None
    assert result.account_snapshot is None
    assert result.positions_order_history is None
    assert result.market_symbol is None
    assert (
        "fixture reader failed: docs fixture reader blocked by test"
        in result.block_reasons
    )
    _assert_safety_fields(result)


def test_bundle_failure_blocks_total_result(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_bundle_validator(
        bundle: dict[str, Any],
    ) -> DemoReadOnlyValidationBundleResult:
        return _bundle_result(
            passed=False,
            status_code=DEMO_READONLY_BUNDLE_INVALID,
            block_reasons=["forced bundle failure"],
        )

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_bundle_validation.validate_demo_readonly_bundle",
        failing_bundle_validator,
    )

    result = validate_demo_readonly_docs_fixture_bundle()

    assert result.passed is False
    assert result.status_code == BUNDLE_VALIDATION_FAILED
    assert "bundle validation failed: forced bundle failure" in result.block_reasons
    assert result.bundle_result is not None
    assert result.bundle_result["passed"] is False
    _assert_safety_fields(result)


def test_bundle_warning_does_not_enable_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def warning_bundle_validator(
        bundle: dict[str, Any],
    ) -> DemoReadOnlyValidationBundleResult:
        return _bundle_result(
            warning_reasons=["review-only warning"],
            is_tradable=True,
            can_execute=True,
        )

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_bundle_validation.validate_demo_readonly_bundle",
        warning_bundle_validator,
    )

    result = validate_demo_readonly_docs_fixture_bundle()

    assert result.passed is True
    assert "bundle validation warning: review-only warning" in result.warning_reasons
    assert result.bundle_result is not None
    assert result.bundle_result["can_execute"] is True
    assert result.bundle_result["is_tradable"] is True
    assert result.can_execute is False
    assert result.is_tradable is False


def test_result_does_not_return_forbidden_trade_fields() -> None:
    result = validate_demo_readonly_docs_fixture_bundle()

    _assert_no_forbidden_result_fields(asdict(result))


def test_bundle_validation_reads_docs_fixtures_not_runtime_data() -> None:
    result = validate_demo_readonly_docs_fixture_bundle()

    assert result.passed is True
    for fixture_summary in result.reader_result["fixtures"].values():
        normalized_path = fixture_summary["relative_path"].replace("\\", "/")
        assert normalized_path.startswith("docs/implementation_plans/")
        assert "data/" not in normalized_path


def test_bundle_validation_does_not_write_files_or_access_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("bundle fixture validation must not write or use network")

    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "touch", fail_if_called)

    result = validate_demo_readonly_docs_fixture_bundle()

    assert result.passed is True
    _assert_safety_fields(result)


def test_bundle_failure_can_be_triggered_without_modifying_docs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader_result = read_all_demo_readonly_docs_fixtures()
    assert reader_result.account_snapshot is not None
    reader_result.account_snapshot["account_mode"] = "live"

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_bundle_validation.read_all_demo_readonly_docs_fixtures",
        lambda: reader_result,
    )

    result = validate_demo_readonly_docs_fixture_bundle()

    assert result.passed is False
    assert result.status_code == BUNDLE_VALIDATION_FAILED
    assert any(
        "bundle validation failed:" in reason
        for reason in result.block_reasons
    )
    _assert_safety_fields(result)
