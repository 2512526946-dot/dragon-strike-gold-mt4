from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.services.demo_readonly_docs_fixture_reader import (
    ACCOUNT_SNAPSHOT,
    MARKET_SYMBOL,
    POSITIONS_ORDER_HISTORY,
    DemoReadOnlyDocsFixturesReadAllResult,
    read_all_demo_readonly_docs_fixtures,
)
from app.services.demo_readonly_validation_bundle import (
    validate_demo_readonly_bundle,
)


BUNDLE_VALIDATION_OK = "BUNDLE_VALIDATION_OK"
BUNDLE_VALIDATION_READER_FAILED = "BUNDLE_VALIDATION_READER_FAILED"
BUNDLE_VALIDATION_FAILED = "BUNDLE_VALIDATION_FAILED"


@dataclass(frozen=True)
class DemoReadOnlyDocsFixtureBundleValidationResult:
    passed: bool
    status_code: str
    reader_result: dict[str, Any]
    bundle_result: dict[str, Any] | None
    account_snapshot: dict[str, Any] | None
    positions_order_history: dict[str, Any] | None
    market_symbol: dict[str, Any] | None
    block_reasons: list[str]
    warning_reasons: list[str]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool


def validate_demo_readonly_docs_fixture_bundle() -> (
    DemoReadOnlyDocsFixtureBundleValidationResult
):
    reader_result = read_all_demo_readonly_docs_fixtures()
    reader_summary = _reader_result_summary(reader_result)

    if not reader_result.passed:
        return DemoReadOnlyDocsFixtureBundleValidationResult(
            passed=False,
            status_code=BUNDLE_VALIDATION_READER_FAILED,
            reader_result=reader_summary,
            bundle_result=None,
            account_snapshot=reader_result.account_snapshot,
            positions_order_history=reader_result.positions_order_history,
            market_symbol=reader_result.market_symbol,
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

    bundle_payload = {
        ACCOUNT_SNAPSHOT: reader_result.account_snapshot,
        POSITIONS_ORDER_HISTORY: reader_result.positions_order_history,
        MARKET_SYMBOL: reader_result.market_symbol,
    }
    bundle_result = validate_demo_readonly_bundle(bundle_payload)
    bundle_result_dict = asdict(bundle_result)

    passed = bundle_result.passed
    block_reasons = (
        []
        if passed
        else [
            f"bundle validation failed: {reason}"
            for reason in bundle_result.block_reasons
        ]
    )
    warning_reasons = [
        f"bundle validation warning: {reason}"
        for reason in bundle_result.warning_reasons
    ]

    return DemoReadOnlyDocsFixtureBundleValidationResult(
        passed=passed,
        status_code=BUNDLE_VALIDATION_OK if passed else BUNDLE_VALIDATION_FAILED,
        reader_result=reader_summary,
        bundle_result=bundle_result_dict,
        account_snapshot=reader_result.account_snapshot,
        positions_order_history=reader_result.positions_order_history,
        market_symbol=reader_result.market_symbol,
        block_reasons=block_reasons,
        warning_reasons=warning_reasons,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


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
