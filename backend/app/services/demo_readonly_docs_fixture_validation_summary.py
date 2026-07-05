from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.demo_readonly_docs_fixture_bundle_validation import (
    validate_demo_readonly_docs_fixture_bundle,
)
from app.services.demo_readonly_docs_fixture_reader import (
    ACCOUNT_SNAPSHOT,
    MARKET_SYMBOL,
    POSITIONS_ORDER_HISTORY,
)


SUMMARY_READY = "SUMMARY_READY"
SUMMARY_VALIDATION_FAILED = "SUMMARY_VALIDATION_FAILED"

SOURCE_SCOPE = "docs_fixture_only"
VALIDATION_STAGE = "docs_fixture_bundle_summary"
FIXTURE_SOURCE_NOTE = (
    "Summary is derived only from docs example fixtures. It is not real demo "
    "account data and not real MT4 data."
)

NEXT_ALLOWED_STAGE = [
    "demo_readonly_fixture_summary_review",
    "demo_readonly_api_planning",
]
NEXT_BLOCKED_STAGE = [
    "real_mt4_connection",
    "demo_account_connection",
    "live_account_connection",
    "auto_trading",
    "execution_api",
    "risk_gate_execution",
    "position_sizing_execution",
    "execution_gate_execution",
]
READINESS_NOTES = [
    "Current output is only a docs fixture summary.",
    "It is not a backend API.",
    "It is not frontend display.",
    "It is not trading permission.",
    "It is not execution permission.",
    "It cannot place orders automatically.",
    "It cannot connect to a real account.",
    "It cannot connect to a demo account.",
]


@dataclass(frozen=True)
class DemoReadOnlyDocsFixtureValidationSummary:
    passed: bool
    status_code: str
    source_scope: str
    validation_stage: str
    fixture_source: str
    bundle_validation_status: dict[str, Any]
    component_statuses: dict[str, dict[str, Any]]
    block_reasons: list[str]
    warning_reasons: list[str]
    readiness_notes: list[str]
    next_allowed_stage: list[str]
    next_blocked_stage: list[str]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool


def summarize_demo_readonly_docs_fixture_validation() -> (
    DemoReadOnlyDocsFixtureValidationSummary
):
    bundle_validation = validate_demo_readonly_docs_fixture_bundle()
    passed = bundle_validation.passed

    return DemoReadOnlyDocsFixtureValidationSummary(
        passed=passed,
        status_code=SUMMARY_READY if passed else SUMMARY_VALIDATION_FAILED,
        source_scope=SOURCE_SCOPE,
        validation_stage=VALIDATION_STAGE,
        fixture_source=FIXTURE_SOURCE_NOTE,
        bundle_validation_status=_bundle_validation_status(bundle_validation),
        component_statuses=_component_statuses(bundle_validation.bundle_result),
        block_reasons=list(bundle_validation.block_reasons),
        warning_reasons=list(bundle_validation.warning_reasons),
        readiness_notes=list(READINESS_NOTES),
        next_allowed_stage=list(NEXT_ALLOWED_STAGE),
        next_blocked_stage=list(NEXT_BLOCKED_STAGE),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


def _bundle_validation_status(bundle_validation: Any) -> dict[str, Any]:
    return {
        "passed": bundle_validation.passed,
        "status_code": bundle_validation.status_code,
        "block_reasons": list(bundle_validation.block_reasons),
        "warning_reasons": list(bundle_validation.warning_reasons),
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }


def _component_statuses(
    bundle_result: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    component_results = {}
    if bundle_result is not None:
        maybe_component_results = bundle_result.get("component_results")
        if isinstance(maybe_component_results, dict):
            component_results = maybe_component_results

    return {
        component_name: _component_status(component_results.get(component_name))
        for component_name in (
            ACCOUNT_SNAPSHOT,
            POSITIONS_ORDER_HISTORY,
            MARKET_SYMBOL,
        )
    }


def _component_status(component_result: Any) -> dict[str, Any]:
    if not isinstance(component_result, dict):
        return {
            "passed": False,
            "status_code": "COMPONENT_STATUS_UNAVAILABLE",
            "block_reasons": [],
            "warning_reasons": [],
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
        }

    return {
        "passed": component_result.get("passed") is True,
        "status_code": component_result.get("status_code"),
        "block_reasons": list(component_result.get("block_reasons") or []),
        "warning_reasons": list(component_result.get("warning_reasons") or []),
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }
