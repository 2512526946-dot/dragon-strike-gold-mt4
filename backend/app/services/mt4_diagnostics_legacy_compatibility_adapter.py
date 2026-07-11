from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services import data_quality_gate as gate
from app.services import (
    demo_readonly_canonical_diagnostics_summary_adapter as canonical_summary,
)


LEGACY_STAGE = "mt4_diagnostics_v1"
LEGACY_NOTE = (
    "Diagnostics are read-only. "
    "Diagnostics are not trading permission. "
    "Diagnostics do not generate trading signals."
)

_SUMMARY_KEYS = frozenset(
    {
        "passed",
        "status_code",
        "source_scope",
        "validation_stage",
        "fixture_source",
        "bundle_validation_status",
        "component_statuses",
        "block_reasons",
        "warning_reasons",
        "readiness_notes",
        "next_allowed_stage",
        "next_blocked_stage",
        "read_only",
        "demo_only",
        "is_tradable",
        "can_execute",
        "is_trading_permission",
        "is_execution_instruction",
        "allowed_to_call_ea",
        "allowed_to_modify_risk",
    }
)
_STATUS_KEYS = frozenset(
    {
        "passed",
        "status_code",
        "block_reasons",
        "warning_reasons",
        "read_only",
        "demo_only",
        "is_tradable",
        "can_execute",
    }
)
_STRING_LIST_FIELDS = (
    "block_reasons",
    "warning_reasons",
    "readiness_notes",
    "next_allowed_stage",
    "next_blocked_stage",
)
_SAFETY_FIELDS: dict[str, bool] = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}
_STATUS_SAFETY_FIELDS: dict[str, bool] = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
}

_SUCCESS_NEXT_ALLOWED_STAGE = (
    "demo_readonly_diagnostics_response_integration",
)
_SUCCESS_NEXT_BLOCKED_STAGE = ("api_reader_activation", "execution_chain")
_BLOCKED_NEXT_STAGE = (
    "demo_readonly_diagnostics_response_integration",
    "api_reader_activation",
    "readonly_analysis",
    "execution_chain",
)
_READY_NOTES = (
    "Canonical DataQualityGate passed for read-only diagnostics adaptation.",
    "Readiness is not trading permission.",
    "This summary is read-only and cannot execute orders.",
)
_BLOCKED_NOTES = (
    "Canonical DataQualityGate blocked read-only diagnostics adaptation.",
    "Readiness is not trading permission.",
    "This summary is read-only and cannot execute orders.",
)
_UNAVAILABLE_SOURCE_STATUS = "CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE"
_INPUT_INVALID_REASON = "CANONICAL_DATA_QUALITY_RESULT_INVALID"
_SAFE_FAILURE_REASON = "CANONICAL_DIAGNOSTICS_ADAPTER_EXCEPTION_SANITIZED"

_BLOCKED_STATUS_REASON_CODES = {
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID: frozenset(
        {
            gate.DATA_QUALITY_INPUT_NOT_OBJECT,
            gate.DATA_QUALITY_REQUIRED_READER_KEY_MISSING,
            gate.DATA_QUALITY_UNEXPECTED_READER_KEY,
            gate.DATA_QUALITY_READER_FIELD_TYPE_INVALID,
            gate.DATA_QUALITY_COMPONENT_STATUS_INVALID,
        }
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID: frozenset(
        {gate.DATA_QUALITY_POLICY_INVALID}
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED: frozenset(
        {
            gate.READER_SAFETY_ENVELOPE_INVALID,
            gate.READER_RESULT_INCONSISTENT,
            gate.READER_WARNING_CODES_INVALID,
        }
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED: frozenset(
        {gate.READER_MIXED_GENERATION_BLOCKED}
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED: frozenset(
        {gate.READER_INTEGRITY_INVALID}
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED: frozenset(
        {gate.READER_DATA_STALE}
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED: frozenset(
        {gate.READER_STRUCTURE_INVALID}
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED: frozenset(
        {gate.READER_VALUE_INVALID}
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED: frozenset(
        {gate.READER_BLOCKED}
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED: frozenset(
        {gate.UPSTREAM_WARNINGS_REJECTED_BY_POLICY}
    ),
    gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE: frozenset(
        {gate.DATA_QUALITY_GATE_EXCEPTION_SANITIZED}
    ),
}


@dataclass(frozen=True)
class _CanonicalSummaryEnvelope:
    passed: bool
    status_code: str
    source_status_code: str
    block_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]


def adapt_canonical_summary_to_legacy_mt4_diagnostics_response(
    *,
    canonical_summary: object,
) -> dict[str, Any]:
    """Map a validated G151 summary into the fixed legacy response envelope."""

    try:
        envelope = _parse_summary(canonical_summary)
        if envelope is None:
            return _legacy_result(passed=False, warning_reasons=[])
        return _legacy_result(
            passed=envelope.passed,
            warning_reasons=list(envelope.warning_reasons),
        )
    except Exception:
        return _legacy_result(passed=False, warning_reasons=[])


def _parse_summary(value_to_parse: object) -> _CanonicalSummaryEnvelope | None:
    if type(value_to_parse) is not dict:
        return None
    if set(value_to_parse) != _SUMMARY_KEYS:
        return None
    if type(value_to_parse["passed"]) is not bool:
        return None
    if any(
        type(value_to_parse[field]) is not str
        for field in (
            "status_code",
            "source_scope",
            "validation_stage",
            "fixture_source",
        )
    ):
        return None
    if value_to_parse["source_scope"] != canonical_summary.SOURCE_SCOPE:
        return None
    if value_to_parse["validation_stage"] != canonical_summary.VALIDATION_STAGE:
        return None
    if value_to_parse["fixture_source"] != canonical_summary.FIXTURE_SOURCE:
        return None
    if any(
        value_to_parse[field] is not expected
        for field, expected in _SAFETY_FIELDS.items()
    ):
        return None

    parsed_lists: dict[str, tuple[str, ...]] = {}
    for field in _STRING_LIST_FIELDS:
        parsed = _strict_string_list(value_to_parse[field])
        if parsed is None:
            return None
        parsed_lists[field] = parsed

    bundle_status = _parse_status(value_to_parse["bundle_validation_status"])
    if bundle_status is None:
        return None
    component_statuses = value_to_parse["component_statuses"]
    if type(component_statuses) is not dict:
        return None
    if set(component_statuses) != {"canonical_data_quality_gate"}:
        return None
    component_status = _parse_status(component_statuses["canonical_data_quality_gate"])
    if component_status is None or component_status != bundle_status:
        return None

    envelope = _CanonicalSummaryEnvelope(
        passed=value_to_parse["passed"],
        status_code=value_to_parse["status_code"],
        source_status_code=bundle_status.status_code,
        block_reasons=parsed_lists["block_reasons"],
        warning_reasons=parsed_lists["warning_reasons"],
    )
    if bundle_status.passed is not envelope.passed:
        return None
    if bundle_status.block_reasons != envelope.block_reasons:
        return None
    if bundle_status.warning_reasons != envelope.warning_reasons:
        return None
    if not _envelope_is_consistent(
        envelope,
        readiness_notes=parsed_lists["readiness_notes"],
        next_allowed_stage=parsed_lists["next_allowed_stage"],
        next_blocked_stage=parsed_lists["next_blocked_stage"],
    ):
        return None
    return envelope


@dataclass(frozen=True)
class _SafeStatus:
    passed: bool
    status_code: str
    block_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]


def _parse_status(value_to_parse: object) -> _SafeStatus | None:
    if type(value_to_parse) is not dict:
        return None
    if set(value_to_parse) != _STATUS_KEYS:
        return None
    if type(value_to_parse["passed"]) is not bool:
        return None
    if type(value_to_parse["status_code"]) is not str:
        return None
    if any(
        value_to_parse[field] is not expected
        for field, expected in _STATUS_SAFETY_FIELDS.items()
    ):
        return None
    block_reasons = _strict_string_list(value_to_parse["block_reasons"])
    warning_reasons = _strict_string_list(value_to_parse["warning_reasons"])
    if block_reasons is None or warning_reasons is None:
        return None
    return _SafeStatus(
        passed=value_to_parse["passed"],
        status_code=value_to_parse["status_code"],
        block_reasons=block_reasons,
        warning_reasons=warning_reasons,
    )


def _envelope_is_consistent(
    envelope: _CanonicalSummaryEnvelope,
    *,
    readiness_notes: tuple[str, ...],
    next_allowed_stage: tuple[str, ...],
    next_blocked_stage: tuple[str, ...],
) -> bool:
    if not _warnings_are_allowed(envelope.warning_reasons):
        return False

    if envelope.status_code == canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY:
        return (
            envelope.passed
            and envelope.source_status_code
            == gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED
            and not envelope.block_reasons
            and not envelope.warning_reasons
            and readiness_notes == _READY_NOTES
            and next_allowed_stage == _SUCCESS_NEXT_ALLOWED_STAGE
            and next_blocked_stage == _SUCCESS_NEXT_BLOCKED_STAGE
        )

    if (
        envelope.status_code
        == canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS
    ):
        return (
            envelope.passed
            and envelope.source_status_code
            == gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
            and not envelope.block_reasons
            and bool(envelope.warning_reasons)
            and readiness_notes == _READY_NOTES
            and next_allowed_stage == _SUCCESS_NEXT_ALLOWED_STAGE
            and next_blocked_stage == _SUCCESS_NEXT_BLOCKED_STAGE
        )

    if envelope.status_code == canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED:
        expected_reasons = _BLOCKED_STATUS_REASON_CODES.get(
            envelope.source_status_code
        )
        if expected_reasons is None or len(envelope.block_reasons) != 1:
            return False
        if envelope.block_reasons[0] not in expected_reasons:
            return False
        if envelope.source_status_code in {
            gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
            gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID,
        } and envelope.warning_reasons:
            return False
        if (
            envelope.source_status_code
            == gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED
            and not envelope.warning_reasons
        ):
            return False
        return (
            not envelope.passed
            and readiness_notes == _BLOCKED_NOTES
            and not next_allowed_stage
            and next_blocked_stage == _BLOCKED_NEXT_STAGE
        )

    if (
        envelope.status_code
        == canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID
    ):
        return (
            not envelope.passed
            and envelope.source_status_code == _UNAVAILABLE_SOURCE_STATUS
            and envelope.block_reasons == (_INPUT_INVALID_REASON,)
            and not envelope.warning_reasons
            and readiness_notes == _BLOCKED_NOTES
            and not next_allowed_stage
            and next_blocked_stage == _BLOCKED_NEXT_STAGE
        )

    if (
        envelope.status_code
        == canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE
    ):
        return (
            not envelope.passed
            and envelope.source_status_code == _UNAVAILABLE_SOURCE_STATUS
            and envelope.block_reasons == (_SAFE_FAILURE_REASON,)
            and not envelope.warning_reasons
            and readiness_notes == _BLOCKED_NOTES
            and not next_allowed_stage
            and next_blocked_stage == _BLOCKED_NEXT_STAGE
        )

    return False


def _legacy_result(
    *,
    passed: bool,
    warning_reasons: list[str],
) -> dict[str, Any]:
    details = {
        key: _unavailable_detail()
        for key in (
            "read_summary",
            "metadata_status",
            "freshness_status",
            "gate_v0_result",
            "required_fields_status",
            "field_types_status",
            "numeric_ranges_status",
            "cross_field_status",
            "gate_v1_result",
        )
    }
    details["gate_v1_result"]["warning_reasons"] = list(warning_reasons)
    return {
        "stage": LEGACY_STAGE,
        "status_code": (
            gate.DATA_QUALITY_PASSED if passed else gate.BLOCKED_BY_GATE_V0
        ),
        "data_quality_passed": passed,
        "can_proceed_to_read_only_analysis": passed,
        "is_tradable": False,
        "note": LEGACY_NOTE,
        **details,
    }


def _unavailable_detail() -> dict[str, Any]:
    return {
        "available": False,
        "status": "unavailable",
        "passed": False,
    }


def _strict_string_list(value_to_parse: object) -> tuple[str, ...] | None:
    if type(value_to_parse) is not list:
        return None
    if any(type(item) is not str for item in value_to_parse):
        return None
    values = tuple(value_to_parse)
    return values if len(values) == len(set(values)) else None


def _warnings_are_allowed(warnings: tuple[str, ...]) -> bool:
    return all(
        warning in gate.CANONICAL_MT4_BUNDLE_V1_WARNING_CODES
        for warning in warnings
    )
