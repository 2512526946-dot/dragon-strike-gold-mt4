from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.services.demo_account_readonly_validator import (
    validate_demo_account_readonly_snapshot,
)
from app.services.demo_market_symbol_readonly_validator import (
    validate_demo_market_symbol_readonly,
)
from app.services.demo_positions_order_history_validator import (
    validate_demo_positions_order_history,
)
from app.services.demo_readonly_docs_fixture_reader import (
    ACCOUNT_SNAPSHOT,
    MARKET_SYMBOL,
    POSITIONS_ORDER_HISTORY,
    DemoReadOnlyDocsFixturesReadAllResult,
    read_all_demo_readonly_docs_fixtures,
)


COMPONENT_VALIDATION_OK = "COMPONENT_VALIDATION_OK"
COMPONENT_VALIDATION_READER_FAILED = "COMPONENT_VALIDATION_READER_FAILED"
COMPONENT_VALIDATION_FAILED = "COMPONENT_VALIDATION_FAILED"


@dataclass(frozen=True)
class DemoReadOnlyDocsFixtureComponentValidationResult:
    passed: bool
    status_code: str
    reader_result: dict[str, Any]
    component_results: dict[str, dict[str, Any] | None]
    account_snapshot_validation: dict[str, Any] | None
    positions_order_history_validation: dict[str, Any] | None
    market_symbol_validation: dict[str, Any] | None
    block_reasons: list[str]
    warning_reasons: list[str]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool


def validate_demo_readonly_docs_fixture_components() -> (
    DemoReadOnlyDocsFixtureComponentValidationResult
):
    reader_result = read_all_demo_readonly_docs_fixtures()
    reader_summary = _reader_result_summary(reader_result)

    if not reader_result.passed:
        return DemoReadOnlyDocsFixtureComponentValidationResult(
            passed=False,
            status_code=COMPONENT_VALIDATION_READER_FAILED,
            reader_result=reader_summary,
            component_results={},
            account_snapshot_validation=None,
            positions_order_history_validation=None,
            market_symbol_validation=None,
            block_reasons=[
                f"fixture reader failed: {reason}"
                for reason in reader_result.block_reasons
            ],
            warning_reasons=list(reader_result.warning_reasons),
            read_only=True,
            demo_only=True,
            is_tradable=False,
            can_execute=False,
        )

    component_results: dict[str, dict[str, Any] | None] = {
        ACCOUNT_SNAPSHOT: None,
        POSITIONS_ORDER_HISTORY: None,
        MARKET_SYMBOL: None,
    }
    block_reasons: list[str] = []
    warning_reasons: list[str] = []

    account_snapshot_validation = _validate_component(
        ACCOUNT_SNAPSHOT,
        reader_result.account_snapshot,
        validate_demo_account_readonly_snapshot,
        component_results,
        block_reasons,
        warning_reasons,
    )
    positions_order_history_validation = _validate_component(
        POSITIONS_ORDER_HISTORY,
        reader_result.positions_order_history,
        validate_demo_positions_order_history,
        component_results,
        block_reasons,
        warning_reasons,
    )
    market_symbol_validation = _validate_component(
        MARKET_SYMBOL,
        reader_result.market_symbol,
        validate_demo_market_symbol_readonly,
        component_results,
        block_reasons,
        warning_reasons,
    )

    passed = not block_reasons

    return DemoReadOnlyDocsFixtureComponentValidationResult(
        passed=passed,
        status_code=COMPONENT_VALIDATION_OK if passed else COMPONENT_VALIDATION_FAILED,
        reader_result=reader_summary,
        component_results=component_results,
        account_snapshot_validation=account_snapshot_validation,
        positions_order_history_validation=positions_order_history_validation,
        market_symbol_validation=market_symbol_validation,
        block_reasons=block_reasons,
        warning_reasons=warning_reasons,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


def _validate_component(
    component_name: str,
    payload: dict[str, Any] | None,
    validator: Any,
    component_results: dict[str, dict[str, Any] | None],
    block_reasons: list[str],
    warning_reasons: list[str],
) -> dict[str, Any] | None:
    if payload is None:
        block_reasons.append(f"{component_name} fixture payload is missing")
        return None

    validation_result = validator(payload)
    validation_result_dict = asdict(validation_result)
    component_results[component_name] = validation_result_dict

    for reason in validation_result.warning_reasons:
        warning_reasons.append(f"{component_name} validator warning: {reason}")

    if validation_result.passed:
        return validation_result_dict

    if validation_result.block_reasons:
        for reason in validation_result.block_reasons:
            block_reasons.append(f"{component_name} validator failed: {reason}")
    else:
        block_reasons.append(
            f"{component_name} validator failed: {validation_result.status_code}"
        )

    return validation_result_dict


def _reader_result_summary(
    reader_result: DemoReadOnlyDocsFixturesReadAllResult,
) -> dict[str, Any]:
    return {
        "passed": reader_result.passed,
        "status_code": reader_result.status_code,
        "fixtures": {
            component_name: _fixture_result_summary(fixture_result)
            for component_name, fixture_result in reader_result.fixtures.items()
        },
        "block_reasons": list(reader_result.block_reasons),
        "warning_reasons": list(reader_result.warning_reasons),
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }


def _fixture_result_summary(fixture_result: dict[str, Any]) -> dict[str, Any]:
    summary_fields = [
        "passed",
        "status_code",
        "relative_path",
        "resolved_path",
        "block_reasons",
        "warning_reasons",
        "read_only",
        "demo_only",
        "is_tradable",
        "can_execute",
    ]
    return {
        field_name: fixture_result[field_name]
        for field_name in summary_fields
        if field_name in fixture_result
    }
