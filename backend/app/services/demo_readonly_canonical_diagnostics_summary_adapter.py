from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services import canonical_mt4_demo_readonly_bundle_v1_filesystem_reader as reader
from app.services import canonical_mt4_demo_readonly_bundle_v1_value_validator as value
from app.services import data_quality_gate as gate


CANONICAL_DIAGNOSTICS_SUMMARY_READY = "CANONICAL_DIAGNOSTICS_SUMMARY_READY"
CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS = (
    "CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS"
)
CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED = "CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED"
CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID = (
    "CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID"
)
CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE = (
    "CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE"
)

VALIDATION_STAGE = "canonical_bundle_v1_diagnostics_summary_adapter"
SOURCE_SCOPE = "canonical_mt4_demo_readonly_data_quality_summary_only"
FIXTURE_SOURCE = "canonical_bundle_v1_data_quality_gate_result"

_NEXT_ALLOWED_STAGE = ["demo_readonly_diagnostics_response_integration"]
_SUCCESS_BLOCKED_STAGES = ["api_reader_activation", "execution_chain"]
_BLOCKED_STAGES = [
    "demo_readonly_diagnostics_response_integration",
    "api_reader_activation",
    "readonly_analysis",
    "execution_chain",
]

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

_DATA_QUALITY_RESULT_KEYS = frozenset(
    {
        "passed",
        "status_code",
        "validation_stage",
        "contract_version",
        "reader_status",
        "source_reader_status_code",
        "source_upstream_value_status_code",
        "data_quality_status",
        "reason_codes",
        "warning_codes",
        "ready_for_readonly_analysis",
        "next_allowed_stage",
        "next_blocked_stage",
        *_SAFETY_FIELDS,
    }
)
_BOOL_FIELDS = (
    "passed",
    "ready_for_readonly_analysis",
    *_SAFETY_FIELDS,
)
_STRING_FIELDS = (
    "status_code",
    "validation_stage",
    "contract_version",
    "reader_status",
    "data_quality_status",
)
_STRING_LIST_FIELDS = (
    "reason_codes",
    "warning_codes",
    "next_allowed_stage",
    "next_blocked_stage",
)

_SUCCESS_STATUS_CODES = frozenset(
    {
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS,
    }
)
_DATA_QUALITY_STATUS_CODES = _SUCCESS_STATUS_CODES | frozenset(
    {
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE,
    }
)
_DATA_QUALITY_REASON_CODES = frozenset(
    {
        gate.DATA_QUALITY_INPUT_NOT_OBJECT,
        gate.DATA_QUALITY_REQUIRED_READER_KEY_MISSING,
        gate.DATA_QUALITY_UNEXPECTED_READER_KEY,
        gate.DATA_QUALITY_READER_FIELD_TYPE_INVALID,
        gate.DATA_QUALITY_COMPONENT_STATUS_INVALID,
        gate.DATA_QUALITY_POLICY_INVALID,
        gate.READER_SAFETY_ENVELOPE_INVALID,
        gate.READER_RESULT_INCONSISTENT,
        gate.READER_WARNING_CODES_INVALID,
        gate.READER_MIXED_GENERATION_BLOCKED,
        gate.READER_INTEGRITY_INVALID,
        gate.READER_DATA_STALE,
        gate.READER_STRUCTURE_INVALID,
        gate.READER_VALUE_INVALID,
        gate.READER_BLOCKED,
        gate.UPSTREAM_WARNINGS_REJECTED_BY_POLICY,
        gate.DATA_QUALITY_GATE_EXCEPTION_SANITIZED,
    }
)
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
_READER_STATUS_CODES = frozenset(
    {
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_ROOT_REJECTED,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_DIRECTORY_REJECTED,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED,
        reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE,
    }
)
_VALUE_STATUS_CODES = frozenset(
    {
        value.CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
        value.CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS,
        value.CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID,
        value.CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED,
        value.CANONICAL_MT4_BUNDLE_V1_READ_POLICY_INVALID,
        value.CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID,
        value.CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_FROM_FUTURE,
        value.CANONICAL_MT4_BUNDLE_V1_DATA_STALE,
        value.CANONICAL_MT4_BUNDLE_V1_MANIFEST_TIME_INVALID,
        value.CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID,
        value.CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID,
        value.CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID,
        value.CANONICAL_MT4_BUNDLE_V1_ACCOUNT_SNAPSHOT_INVALID,
        value.CANONICAL_MT4_BUNDLE_V1_CROSS_PAYLOAD_INVALID,
    }
)


@dataclass(frozen=True)
class _DataQualityEnvelope:
    passed: bool
    status_code: str
    reader_status: str
    source_reader_status_code: str | None
    source_upstream_value_status_code: str | None
    data_quality_status: str
    reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    ready_for_readonly_analysis: bool
    next_allowed_stage: tuple[str, ...]
    next_blocked_stage: tuple[str, ...]


def adapt_canonical_data_quality_gate_to_demo_readonly_diagnostics_summary(
    *,
    data_quality_result: object,
) -> dict[str, Any]:
    try:
        envelope = _parse_data_quality_result(data_quality_result)
        if envelope is None:
            return _summary_result(
                passed=False,
                status_code=CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID,
                source_status_code="CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE",
                block_reasons=["CANONICAL_DATA_QUALITY_RESULT_INVALID"],
                warning_reasons=[],
            )

        passed = envelope.passed
        return _summary_result(
            passed=passed,
            status_code=_summary_status_code(envelope),
            source_status_code=envelope.status_code,
            block_reasons=[] if passed else list(envelope.reason_codes),
            warning_reasons=list(envelope.warning_codes),
        )
    except Exception:
        return _summary_result(
            passed=False,
            status_code=CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE,
            source_status_code="CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE",
            block_reasons=["CANONICAL_DIAGNOSTICS_ADAPTER_EXCEPTION_SANITIZED"],
            warning_reasons=[],
        )


def _parse_data_quality_result(value_to_parse: object) -> _DataQualityEnvelope | None:
    if type(value_to_parse) is not dict:
        return None
    if set(value_to_parse) != _DATA_QUALITY_RESULT_KEYS:
        return None
    if any(type(value_to_parse[field]) is not bool for field in _BOOL_FIELDS):
        return None
    if any(type(value_to_parse[field]) is not str for field in _STRING_FIELDS):
        return None

    lists: dict[str, tuple[str, ...]] = {}
    for field in _STRING_LIST_FIELDS:
        parsed = _strict_string_list(value_to_parse[field])
        if parsed is None:
            return None
        lists[field] = parsed

    source_reader_status = value_to_parse["source_reader_status_code"]
    source_upstream_status = value_to_parse["source_upstream_value_status_code"]
    if source_reader_status is not None and type(source_reader_status) is not str:
        return None
    if source_upstream_status is not None and type(source_upstream_status) is not str:
        return None
    if source_reader_status is not None and source_reader_status not in _READER_STATUS_CODES:
        return None
    if source_upstream_status is not None and source_upstream_status not in _VALUE_STATUS_CODES:
        return None

    if value_to_parse["validation_stage"] != gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STAGE:
        return None
    if value_to_parse["contract_version"] != gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_CONTRACT_VERSION:
        return None
    if value_to_parse["status_code"] not in _DATA_QUALITY_STATUS_CODES:
        return None
    if any(value_to_parse[field] is not expected for field, expected in _SAFETY_FIELDS.items()):
        return None
    if not _codes_are_allowed(lists["reason_codes"], _DATA_QUALITY_REASON_CODES):
        return None
    if not _codes_are_allowed(lists["warning_codes"], gate.CANONICAL_MT4_BUNDLE_V1_WARNING_CODES):
        return None

    envelope = _DataQualityEnvelope(
        passed=value_to_parse["passed"],
        status_code=value_to_parse["status_code"],
        reader_status=value_to_parse["reader_status"],
        source_reader_status_code=source_reader_status,
        source_upstream_value_status_code=source_upstream_status,
        data_quality_status=value_to_parse["data_quality_status"],
        reason_codes=lists["reason_codes"],
        warning_codes=lists["warning_codes"],
        ready_for_readonly_analysis=value_to_parse["ready_for_readonly_analysis"],
        next_allowed_stage=lists["next_allowed_stage"],
        next_blocked_stage=lists["next_blocked_stage"],
    )
    return envelope if _envelope_is_consistent(envelope) else None


def _envelope_is_consistent(envelope: _DataQualityEnvelope) -> bool:
    if envelope.status_code in _SUCCESS_STATUS_CODES:
        with_warnings = (
            envelope.status_code
            == gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
        )
        return (
            envelope.passed
            and envelope.reader_status == "validated_isolated"
            and envelope.data_quality_status
            == ("passed_with_warnings" if with_warnings else "passed")
            and not envelope.reason_codes
            and bool(envelope.warning_codes) is with_warnings
            and envelope.ready_for_readonly_analysis
            and envelope.next_allowed_stage == ("canonical_diagnostics_integration",)
            and envelope.next_blocked_stage
            == ("api_reader_activation", "execution_chain")
            and envelope.source_reader_status_code
            == (
                reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS
                if with_warnings
                else reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID
            )
            and envelope.source_upstream_value_status_code
            == (
                value.CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS
                if with_warnings
                else value.CANONICAL_MT4_BUNDLE_V1_VALUE_VALID
            )
        )

    expected_reasons = _BLOCKED_STATUS_REASON_CODES.get(envelope.status_code)
    if expected_reasons is None or envelope.reason_codes[0] not in expected_reasons:
        return False
    if envelope.status_code in {
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID,
    } and (
        envelope.source_reader_status_code is not None
        or envelope.source_upstream_value_status_code is not None
        or envelope.warning_codes
    ):
        return False
    if (
        envelope.status_code == gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED
        and not envelope.warning_codes
    ):
        return False

    return (
        not envelope.passed
        and envelope.reader_status == "blocked"
        and envelope.data_quality_status == "blocked"
        and len(envelope.reason_codes) == 1
        and not envelope.ready_for_readonly_analysis
        and not envelope.next_allowed_stage
        and envelope.next_blocked_stage
        == (
            "canonical_diagnostics_integration",
            "api_reader_activation",
            "readonly_analysis",
            "execution_chain",
        )
    )


def _summary_status_code(envelope: _DataQualityEnvelope) -> str:
    if not envelope.passed:
        return CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
    if envelope.warning_codes:
        return CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS
    return CANONICAL_DIAGNOSTICS_SUMMARY_READY


def _summary_result(
    *,
    passed: bool,
    status_code: str,
    source_status_code: str,
    block_reasons: list[str],
    warning_reasons: list[str],
) -> dict[str, Any]:
    status = _safe_status(
        passed=passed,
        status_code=source_status_code,
        block_reasons=block_reasons,
        warning_reasons=warning_reasons,
    )
    return {
        "passed": passed,
        "status_code": status_code,
        "source_scope": SOURCE_SCOPE,
        "validation_stage": VALIDATION_STAGE,
        "fixture_source": FIXTURE_SOURCE,
        "bundle_validation_status": dict(status),
        "component_statuses": {"canonical_data_quality_gate": dict(status)},
        "block_reasons": list(block_reasons),
        "warning_reasons": list(warning_reasons),
        "readiness_notes": [
            (
                "Canonical DataQualityGate passed for read-only diagnostics adaptation."
                if passed
                else "Canonical DataQualityGate blocked read-only diagnostics adaptation."
            ),
            "Readiness is not trading permission.",
            "This summary is read-only and cannot execute orders.",
        ],
        "next_allowed_stage": list(_NEXT_ALLOWED_STAGE) if passed else [],
        "next_blocked_stage": list(
            _SUCCESS_BLOCKED_STAGES if passed else _BLOCKED_STAGES
        ),
        **_SAFETY_FIELDS,
    }


def _safe_status(
    *,
    passed: bool,
    status_code: str,
    block_reasons: list[str],
    warning_reasons: list[str],
) -> dict[str, Any]:
    return {
        "passed": passed,
        "status_code": status_code,
        "block_reasons": list(block_reasons),
        "warning_reasons": list(warning_reasons),
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }


def _strict_string_list(value_to_parse: object) -> tuple[str, ...] | None:
    if type(value_to_parse) is not list:
        return None
    if any(type(item) is not str for item in value_to_parse):
        return None
    return tuple(value_to_parse)


def _codes_are_allowed(values: tuple[str, ...], allowed: frozenset[str]) -> bool:
    return len(values) == len(set(values)) and all(value in allowed for value in values)
