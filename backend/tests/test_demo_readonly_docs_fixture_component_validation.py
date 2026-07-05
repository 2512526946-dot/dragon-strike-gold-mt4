from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pytest

from app.services.demo_readonly_docs_fixture_reader import (
    ACCOUNT_SNAPSHOT,
    MARKET_SYMBOL,
    POSITIONS_ORDER_HISTORY,
    DemoReadOnlyDocsFixturesReadAllResult,
    read_all_demo_readonly_docs_fixtures,
)
from app.services.demo_readonly_docs_fixture_component_validation import (
    COMPONENT_VALIDATION_FAILED,
    COMPONENT_VALIDATION_OK,
    COMPONENT_VALIDATION_READER_FAILED,
    DemoReadOnlyDocsFixtureComponentValidationResult,
    validate_demo_readonly_docs_fixture_components,
)


FORBIDDEN_RESULT_FIELDS = {
    "can_trade",
    "allow_trade",
    "should_buy",
    "should_sell",
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


@dataclass(frozen=True)
class FakeValidationResult:
    passed: bool
    status_code: str
    block_reasons: list[str]
    warning_reasons: list[str]
    is_tradable: bool
    can_execute: bool
    note: str


def _fake_validation_result(
    *,
    passed: bool = True,
    status_code: str = "FAKE_VALID",
    block_reasons: list[str] | None = None,
    warning_reasons: list[str] | None = None,
    is_tradable: bool = False,
    can_execute: bool = False,
) -> FakeValidationResult:
    return FakeValidationResult(
        passed=passed,
        status_code=status_code,
        block_reasons=block_reasons or [],
        warning_reasons=warning_reasons or [],
        is_tradable=is_tradable,
        can_execute=can_execute,
        note=(
            "Fake validation is read-only, not trading permission, "
            "and does not generate trading signals."
        ),
    )


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


def _reader_success() -> DemoReadOnlyDocsFixturesReadAllResult:
    return read_all_demo_readonly_docs_fixtures()


def _assert_safety_fields(
    result: DemoReadOnlyDocsFixtureComponentValidationResult,
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


def test_docs_fixtures_pass_component_validation() -> None:
    result = validate_demo_readonly_docs_fixture_components()

    assert isinstance(result, DemoReadOnlyDocsFixtureComponentValidationResult)
    assert result.passed is True
    assert result.status_code == COMPONENT_VALIDATION_OK
    assert result.reader_result["passed"] is True
    assert result.reader_result["status_code"] == "DEMO_READONLY_FIXTURES_READ_OK"
    assert set(result.component_results) == {
        ACCOUNT_SNAPSHOT,
        POSITIONS_ORDER_HISTORY,
        MARKET_SYMBOL,
    }
    assert result.account_snapshot_validation is not None
    assert result.positions_order_history_validation is not None
    assert result.market_symbol_validation is not None
    assert result.account_snapshot_validation["passed"] is True
    assert result.positions_order_history_validation["passed"] is True
    assert result.market_symbol_validation["passed"] is True
    assert result.block_reasons == []
    _assert_safety_fields(result)


def test_reader_failure_returns_failure_without_calling_validators(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("component validators must not run when reader fails")

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_component_validation.read_all_demo_readonly_docs_fixtures",
        _reader_failure,
    )
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_component_validation.validate_demo_account_readonly_snapshot",
        fail_if_called,
    )
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_component_validation.validate_demo_positions_order_history",
        fail_if_called,
    )
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_component_validation.validate_demo_market_symbol_readonly",
        fail_if_called,
    )

    result = validate_demo_readonly_docs_fixture_components()

    assert result.passed is False
    assert result.status_code == COMPONENT_VALIDATION_READER_FAILED
    assert result.component_results == {}
    assert result.account_snapshot_validation is None
    assert result.positions_order_history_validation is None
    assert result.market_symbol_validation is None
    assert (
        "fixture reader failed: docs fixture reader blocked by test"
        in result.block_reasons
    )
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    ("component_name", "validator_name"),
    [
        (ACCOUNT_SNAPSHOT, "validate_demo_account_readonly_snapshot"),
        (POSITIONS_ORDER_HISTORY, "validate_demo_positions_order_history"),
        (MARKET_SYMBOL, "validate_demo_market_symbol_readonly"),
    ],
)
def test_each_component_validator_failure_blocks_result(
    component_name: str,
    validator_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_validator(payload: dict[str, Any]) -> FakeValidationResult:
        return _fake_validation_result(
            passed=False,
            status_code="FAKE_INVALID",
            block_reasons=["forced component failure"],
        )

    monkeypatch.setattr(
        f"app.services.demo_readonly_docs_fixture_component_validation.{validator_name}",
        failing_validator,
    )

    result = validate_demo_readonly_docs_fixture_components()

    assert result.passed is False
    assert result.status_code == COMPONENT_VALIDATION_FAILED
    assert any(
        reason == f"{component_name} validator failed: forced component failure"
        for reason in result.block_reasons
    )
    assert result.component_results[component_name] is not None
    assert result.component_results[component_name]["passed"] is False
    _assert_safety_fields(result)


def test_component_warnings_do_not_enable_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def warning_validator(payload: dict[str, Any]) -> FakeValidationResult:
        return _fake_validation_result(
            warning_reasons=["test warning"],
            is_tradable=True,
            can_execute=True,
        )

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_component_validation.validate_demo_account_readonly_snapshot",
        warning_validator,
    )

    result = validate_demo_readonly_docs_fixture_components()

    assert result.passed is True
    assert "account_snapshot validator warning: test warning" in result.warning_reasons
    assert result.account_snapshot_validation is not None
    assert result.account_snapshot_validation["can_execute"] is True
    assert result.can_execute is False
    assert result.is_tradable is False


def test_result_does_not_return_forbidden_trade_fields() -> None:
    result = validate_demo_readonly_docs_fixture_components()

    _assert_no_forbidden_result_fields(asdict(result))
    assert "payload" not in result.reader_result
    assert "account_snapshot" not in result.reader_result
    assert "positions_order_history" not in result.reader_result
    assert "market_symbol" not in result.reader_result


def test_component_validation_does_not_call_validation_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("component validation must not call bundle validation")

    monkeypatch.setattr(
        "app.services.demo_readonly_validation_bundle.validate_demo_readonly_bundle",
        fail_if_called,
    )

    result = validate_demo_readonly_docs_fixture_components()

    assert result.passed is True
    _assert_safety_fields(result)


def test_component_validation_does_not_do_cross_component_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader_result = _reader_success()
    assert reader_result.account_snapshot is not None
    assert reader_result.positions_order_history is not None
    assert reader_result.market_symbol is not None

    reader_result.account_snapshot["demo_account"]["account_alias"] = "account-a"
    reader_result.positions_order_history["demo_account"]["account_alias"] = "account-b"
    reader_result.market_symbol["symbol"] = "EURUSD"

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_component_validation.read_all_demo_readonly_docs_fixtures",
        lambda: reader_result,
    )
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_component_validation.validate_demo_account_readonly_snapshot",
        lambda payload: _fake_validation_result(),
    )
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_component_validation.validate_demo_positions_order_history",
        lambda payload: _fake_validation_result(),
    )
    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_component_validation.validate_demo_market_symbol_readonly",
        lambda payload: _fake_validation_result(),
    )

    result = validate_demo_readonly_docs_fixture_components()

    assert result.passed is True
    assert result.block_reasons == []
    _assert_safety_fields(result)


def test_component_validation_does_not_write_files_or_use_runtime_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("component validation must not write files")

    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "touch", fail_if_called)

    result = validate_demo_readonly_docs_fixture_components()

    assert result.passed is True
    for fixture_summary in result.reader_result["fixtures"].values():
        normalized_path = fixture_summary["relative_path"].replace("\\", "/")
        assert normalized_path.startswith("docs/implementation_plans/")
        assert "data/" not in normalized_path
    _assert_safety_fields(result)
