from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re
from typing import Any

from app.services.demo_readonly_canonical_diagnostics_pipeline import (
    build_demo_readonly_canonical_diagnostics_summary,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_ROOT = _REPOSITORY_ROOT / "docs" / "architecture" / "fixtures"
_FIXTURE_BUNDLE_DIR = (
    _FIXTURE_ROOT / "canonical-mt4-demo-readonly-bundle-v1"
)
_FIXTURE_REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)

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
_SAFETY_FIELDS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}
_STATUS_SAFETY_FIELDS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
}
_SOURCE_SCOPE = "canonical_mt4_demo_readonly_data_quality_summary_only"
_VALIDATION_STAGE = "canonical_bundle_v1_diagnostics_summary_adapter"
_FIXTURE_SOURCE = "canonical_bundle_v1_data_quality_gate_result"
_SUMMARY_READY = "CANONICAL_DIAGNOSTICS_SUMMARY_READY"
_SUMMARY_READY_WITH_WARNINGS = "CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS"
_SUMMARY_BLOCKED = "CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED"
_SUMMARY_INPUT_INVALID = "CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID"
_SUMMARY_SAFE_FAILURE = "CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE"
_SUMMARY_STATUS_CODES = frozenset(
    {
        _SUMMARY_READY,
        _SUMMARY_READY_WITH_WARNINGS,
        _SUMMARY_BLOCKED,
        _SUMMARY_INPUT_INVALID,
        _SUMMARY_SAFE_FAILURE,
    }
)
_SOURCE_PASSED = "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED"
_SOURCE_PASSED_WITH_WARNINGS = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS"
)
_SOURCE_UNAVAILABLE = "CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE"
_SOURCE_INPUT_INVALID = "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID"
_SOURCE_POLICY_INVALID = "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID"
_SOURCE_REJECTED = "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED"
_BLOCKED_STATUS_REASON_CODES = {
    _SOURCE_INPUT_INVALID: frozenset(
        {
            "DATA_QUALITY_INPUT_NOT_OBJECT",
            "DATA_QUALITY_REQUIRED_READER_KEY_MISSING",
            "DATA_QUALITY_UNEXPECTED_READER_KEY",
            "DATA_QUALITY_READER_FIELD_TYPE_INVALID",
            "DATA_QUALITY_COMPONENT_STATUS_INVALID",
        }
    ),
    _SOURCE_POLICY_INVALID: frozenset({"DATA_QUALITY_POLICY_INVALID"}),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED": frozenset(
        {
            "READER_SAFETY_ENVELOPE_INVALID",
            "READER_RESULT_INCONSISTENT",
            "READER_WARNING_CODES_INVALID",
        }
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED": frozenset(
        {"READER_MIXED_GENERATION_BLOCKED"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED": frozenset(
        {"READER_INTEGRITY_INVALID"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED": frozenset(
        {"READER_DATA_STALE"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED": frozenset(
        {"READER_STRUCTURE_INVALID"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED": frozenset(
        {"READER_VALUE_INVALID"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED": frozenset(
        {"READER_BLOCKED"}
    ),
    _SOURCE_REJECTED: frozenset({"UPSTREAM_WARNINGS_REJECTED_BY_POLICY"}),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE": frozenset(
        {"DATA_QUALITY_GATE_EXCEPTION_SANITIZED"}
    ),
}
_WARNING_CODES = frozenset({"IDEMPOTENT_REPEAT", "SEQUENCE_GAP"})
_INPUT_INVALID_REASON = "CANONICAL_DATA_QUALITY_RESULT_INVALID"
_SAFE_FAILURE_REASON = "CANONICAL_DIAGNOSTICS_ADAPTER_EXCEPTION_SANITIZED"
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
_SUCCESS_NEXT_ALLOWED_STAGE = ("demo_readonly_diagnostics_response_integration",)
_SUCCESS_NEXT_BLOCKED_STAGE = ("api_reader_activation", "execution_chain")
_BLOCKED_NEXT_STAGE = (
    "demo_readonly_diagnostics_response_integration",
    "api_reader_activation",
    "readonly_analysis",
    "execution_chain",
)
_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


def build_demo_readonly_canonical_docs_fixture_diagnostics_summary() -> dict[
    str, Any
]:
    """Build the canonical summary from the fixed repository docs fixture."""

    try:
        result = build_demo_readonly_canonical_diagnostics_summary(
            allowed_root=_FIXTURE_ROOT,
            bundle_dir=_FIXTURE_BUNDLE_DIR,
            now_utc=_FIXTURE_REFERENCE_TIME,
        )
        return result if _is_safe_summary(result) else {}
    except Exception:
        return {}


def _is_safe_summary(value_to_parse: object) -> bool:
    if not _has_exact_plain_dict_keys(value_to_parse, _SUMMARY_KEYS):
        return False
    if type(value_to_parse["passed"]) is not bool:
        return False
    if any(
        type(value_to_parse[field]) is not str
        for field in ("status_code", "source_scope", "validation_stage", "fixture_source")
    ):
        return False
    if (
        value_to_parse["source_scope"] != _SOURCE_SCOPE
        or value_to_parse["validation_stage"] != _VALIDATION_STAGE
        or value_to_parse["fixture_source"] != _FIXTURE_SOURCE
        or value_to_parse["status_code"] not in _SUMMARY_STATUS_CODES
    ):
        return False
    if any(
        value_to_parse[field] is not expected
        for field, expected in _SAFETY_FIELDS.items()
    ):
        return False

    lists: dict[str, tuple[str, ...]] = {}
    for field in _STRING_LIST_FIELDS:
        parsed = _strict_string_list(value_to_parse[field])
        if parsed is None:
            return False
        lists[field] = parsed

    bundle_status = _parse_status(value_to_parse["bundle_validation_status"])
    components = value_to_parse["component_statuses"]
    if (
        bundle_status is None
        or not _has_exact_plain_dict_keys(
            components,
            frozenset({"canonical_data_quality_gate"}),
        )
    ):
        return False
    component_status = _parse_status(components["canonical_data_quality_gate"])
    if component_status is None or component_status != bundle_status:
        return False

    passed, source_status, block_reasons, warning_reasons = bundle_status
    if (
        value_to_parse["passed"] is not passed
        or lists["block_reasons"] != block_reasons
        or lists["warning_reasons"] != warning_reasons
        or not _codes_are_safe(block_reasons)
        or not _warnings_are_safe(warning_reasons)
    ):
        return False

    return _state_is_consistent(
        passed=passed,
        summary_status=value_to_parse["status_code"],
        source_status=source_status,
        block_reasons=block_reasons,
        warning_reasons=warning_reasons,
        readiness_notes=lists["readiness_notes"],
        next_allowed_stage=lists["next_allowed_stage"],
        next_blocked_stage=lists["next_blocked_stage"],
    )


def _parse_status(
    value_to_parse: object,
) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]] | None:
    if not _has_exact_plain_dict_keys(value_to_parse, _STATUS_KEYS):
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
    return (
        value_to_parse["passed"],
        value_to_parse["status_code"],
        block_reasons,
        warning_reasons,
    )


def _has_exact_plain_dict_keys(
    value_to_parse: object,
    expected_keys: frozenset[str],
) -> bool:
    if type(value_to_parse) is not dict:
        return False
    keys = tuple(value_to_parse)
    if any(type(key) is not str for key in keys):
        return False
    return frozenset(keys) == expected_keys


def _strict_string_list(value_to_parse: object) -> tuple[str, ...] | None:
    if type(value_to_parse) is not list:
        return None
    if any(type(item) is not str for item in value_to_parse):
        return None
    parsed = tuple(value_to_parse)
    return parsed if len(parsed) == len(set(parsed)) else None


def _codes_are_safe(codes: tuple[str, ...]) -> bool:
    return all(_CODE_PATTERN.fullmatch(code) is not None for code in codes)


def _warnings_are_safe(codes: tuple[str, ...]) -> bool:
    return all(code in _WARNING_CODES for code in codes)


def _state_is_consistent(
    *,
    passed: bool,
    summary_status: str,
    source_status: str,
    block_reasons: tuple[str, ...],
    warning_reasons: tuple[str, ...],
    readiness_notes: tuple[str, ...],
    next_allowed_stage: tuple[str, ...],
    next_blocked_stage: tuple[str, ...],
) -> bool:
    if passed:
        if block_reasons or readiness_notes != _READY_NOTES:
            return False
        if next_allowed_stage != _SUCCESS_NEXT_ALLOWED_STAGE:
            return False
        if next_blocked_stage != _SUCCESS_NEXT_BLOCKED_STAGE:
            return False
        if summary_status == _SUMMARY_READY:
            return source_status == _SOURCE_PASSED and not warning_reasons
        return (
            summary_status == _SUMMARY_READY_WITH_WARNINGS
            and source_status == _SOURCE_PASSED_WITH_WARNINGS
            and bool(warning_reasons)
        )

    if (
        readiness_notes != _BLOCKED_NOTES
        or next_allowed_stage
        or next_blocked_stage != _BLOCKED_NEXT_STAGE
        or len(block_reasons) != 1
    ):
        return False
    if summary_status == _SUMMARY_INPUT_INVALID:
        return (
            source_status == _SOURCE_UNAVAILABLE
            and block_reasons == (_INPUT_INVALID_REASON,)
            and not warning_reasons
        )
    if summary_status == _SUMMARY_SAFE_FAILURE:
        return (
            source_status == _SOURCE_UNAVAILABLE
            and block_reasons == (_SAFE_FAILURE_REASON,)
            and not warning_reasons
        )
    expected_reasons = _BLOCKED_STATUS_REASON_CODES.get(source_status)
    if (
        summary_status != _SUMMARY_BLOCKED
        or expected_reasons is None
        or block_reasons[0] not in expected_reasons
    ):
        return False
    if source_status in {_SOURCE_INPUT_INVALID, _SOURCE_POLICY_INVALID}:
        return not warning_reasons
    if source_status == _SOURCE_REJECTED:
        return bool(warning_reasons)
    return True
