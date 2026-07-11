from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_DIRECTORY_REJECTED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_ROOT_REJECTED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CANONICAL_MT4_BUNDLE_V1_ACCOUNT_SNAPSHOT_INVALID,
    CANONICAL_MT4_BUNDLE_V1_CROSS_PAYLOAD_INVALID,
    CANONICAL_MT4_BUNDLE_V1_DATA_STALE,
    CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID,
    CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID,
    CANONICAL_MT4_BUNDLE_V1_MANIFEST_TIME_INVALID,
    CANONICAL_MT4_BUNDLE_V1_READ_POLICY_INVALID,
    CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID,
    CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_FROM_FUTURE,
    CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID,
    CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID,
    CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS,
)

from app.services.mt4_cross_field_checks import Mt4SnapshotCrossFieldStatus
from app.services.mt4_field_types import Mt4SnapshotFieldTypesStatus
from app.services.mt4_numeric_ranges import Mt4SnapshotNumericRangesStatus
from app.services.mt4_required_fields import Mt4SnapshotRequiredFieldsStatus
from app.services.mt4_snapshot_freshness import Mt4SnapshotFreshnessStatus
from app.services.mt4_snapshot_metadata import Mt4SnapshotMetadataStatus
from app.services.mt4_snapshot_status import Mt4SnapshotReadSummary


DATA_QUALITY_GATE_V0_STAGE = "data_quality_gate_v0"

READY_FOR_SCHEMA_CHECKS = "READY_FOR_SCHEMA_CHECKS"
BLOCKED_BY_READ_STATUS = "BLOCKED_BY_READ_STATUS"
BLOCKED_BY_METADATA = "BLOCKED_BY_METADATA"
BLOCKED_BY_FRESHNESS = "BLOCKED_BY_FRESHNESS"
BLOCKED_BY_MULTIPLE_REASONS = "BLOCKED_BY_MULTIPLE_REASONS"

DATA_QUALITY_GATE_V0_NOTE = (
    "DataQualityGate v0 is not a trading permission. "
    "It does not generate trading signals."
)

DATA_QUALITY_GATE_V1_STAGE = "data_quality_gate_v1"

DATA_QUALITY_PASSED = "DATA_QUALITY_PASSED"
BLOCKED_BY_GATE_V0 = "BLOCKED_BY_GATE_V0"
BLOCKED_BY_REQUIRED_FIELDS = "BLOCKED_BY_REQUIRED_FIELDS"
BLOCKED_BY_FIELD_TYPES = "BLOCKED_BY_FIELD_TYPES"
BLOCKED_BY_NUMERIC_RANGES = "BLOCKED_BY_NUMERIC_RANGES"
BLOCKED_BY_CROSS_FIELD_CHECKS = "BLOCKED_BY_CROSS_FIELD_CHECKS"

DATA_QUALITY_GATE_V1_NOTE = (
    "DataQualityGate v1 is not a trading permission. "
    "It does not generate trading signals. "
    "It only allows proceeding to read-only analysis."
)

CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STAGE = (
    "canonical_bundle_v1_data_quality_gate"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_CONTRACT_VERSION = "1.0"

CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED"
)
CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE"
)

DATA_QUALITY_INPUT_NOT_OBJECT = "DATA_QUALITY_INPUT_NOT_OBJECT"
DATA_QUALITY_REQUIRED_READER_KEY_MISSING = (
    "DATA_QUALITY_REQUIRED_READER_KEY_MISSING"
)
DATA_QUALITY_UNEXPECTED_READER_KEY = "DATA_QUALITY_UNEXPECTED_READER_KEY"
DATA_QUALITY_READER_FIELD_TYPE_INVALID = (
    "DATA_QUALITY_READER_FIELD_TYPE_INVALID"
)
DATA_QUALITY_COMPONENT_STATUS_INVALID = "DATA_QUALITY_COMPONENT_STATUS_INVALID"
DATA_QUALITY_POLICY_INVALID = "DATA_QUALITY_POLICY_INVALID"
READER_SAFETY_ENVELOPE_INVALID = "READER_SAFETY_ENVELOPE_INVALID"
READER_RESULT_INCONSISTENT = "READER_RESULT_INCONSISTENT"
READER_WARNING_CODES_INVALID = "READER_WARNING_CODES_INVALID"
READER_MIXED_GENERATION_BLOCKED = "READER_MIXED_GENERATION_BLOCKED"
READER_INTEGRITY_INVALID = "READER_INTEGRITY_INVALID"
READER_DATA_STALE = "READER_DATA_STALE"
READER_STRUCTURE_INVALID = "READER_STRUCTURE_INVALID"
READER_VALUE_INVALID = "READER_VALUE_INVALID"
READER_BLOCKED = "READER_BLOCKED"
UPSTREAM_WARNINGS_REJECTED_BY_POLICY = (
    "UPSTREAM_WARNINGS_REJECTED_BY_POLICY"
)
DATA_QUALITY_GATE_EXCEPTION_SANITIZED = "DATA_QUALITY_GATE_EXCEPTION_SANITIZED"

CANONICAL_MT4_BUNDLE_V1_WARNING_CODES = frozenset(
    {"IDEMPOTENT_REPEAT", "SEQUENCE_GAP"}
)

_CANONICAL_READER_STAGE = "canonical_bundle_v1_isolated_filesystem_reader"
_CANONICAL_CONTRACT_VERSION = "1.0"
_CANONICAL_SOURCE_NEXT_ALLOWED_STAGE = (
    "canonical_data_quality_gate_integration",
)
_CANONICAL_SOURCE_NEXT_BLOCKED_STAGE = (
    "api_reader_activation",
    "readonly_analysis",
    "execution_chain",
)
_CANONICAL_SUCCESS_NEXT_ALLOWED_STAGE = (
    "canonical_diagnostics_integration",
)
_CANONICAL_SUCCESS_NEXT_BLOCKED_STAGE = (
    "api_reader_activation",
    "execution_chain",
)
_CANONICAL_BLOCKED_NEXT_STAGE = (
    "canonical_diagnostics_integration",
    "api_reader_activation",
    "readonly_analysis",
    "execution_chain",
)

_CANONICAL_READER_RESULT_KEYS = frozenset(
    {
        "passed",
        "status_code",
        "validation_stage",
        "contract_version",
        "reader_status",
        "reason_codes",
        "warning_codes",
        "component_statuses",
        "manifest_consistency_checked",
        "manifest_consistency_passed",
        "checksum_checked",
        "checksum_passed",
        "upstream_value_passed",
        "upstream_value_status_code",
        "ready_for_readonly_analysis",
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
_CANONICAL_COMPONENT_KEYS = frozenset(
    {
        "component_name",
        "passed",
        "status_code",
        "reason_codes",
        "warning_codes",
    }
)
_CANONICAL_COMPONENT_NAMES = (
    "filesystem_boundary",
    "snapshot_manifest",
    "live_tick",
    "latest_bars",
    "symbol_spec",
    "account_snapshot",
    "manifest_consistency",
    "checksum",
    "upstream_value_validation",
)
_CANONICAL_BOOL_FIELDS = (
    "passed",
    "manifest_consistency_checked",
    "manifest_consistency_passed",
    "checksum_checked",
    "checksum_passed",
    "upstream_value_passed",
    "ready_for_readonly_analysis",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
_CANONICAL_STRING_FIELDS = (
    "status_code",
    "validation_stage",
    "contract_version",
    "reader_status",
)
_CANONICAL_STRING_LIST_FIELDS = (
    "reason_codes",
    "warning_codes",
    "next_allowed_stage",
    "next_blocked_stage",
)
_SAFE_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")

_CANONICAL_READER_STATUS_CODES = frozenset(
    {
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_ROOT_REJECTED,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_DIRECTORY_REJECTED,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE,
    }
)
_CANONICAL_VALUE_STATUS_CODES = frozenset(
    {
        CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
        CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS,
        CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID,
        CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED,
        CANONICAL_MT4_BUNDLE_V1_READ_POLICY_INVALID,
        CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID,
        CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_FROM_FUTURE,
        CANONICAL_MT4_BUNDLE_V1_DATA_STALE,
        CANONICAL_MT4_BUNDLE_V1_MANIFEST_TIME_INVALID,
        CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID,
        CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID,
        CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID,
        CANONICAL_MT4_BUNDLE_V1_ACCOUNT_SNAPSHOT_INVALID,
        CANONICAL_MT4_BUNDLE_V1_CROSS_PAYLOAD_INVALID,
    }
)
_CANONICAL_VALUE_INVALID_STATUS_CODES = _CANONICAL_VALUE_STATUS_CODES - {
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS,
    CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_DATA_STALE,
}
_CANONICAL_STRUCTURE_READER_STATUS_CODES = frozenset(
    {
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT,
    }
)


@dataclass(frozen=True)
class CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy:
    allow_upstream_warnings: bool = True


@dataclass(frozen=True)
class _CanonicalReaderEnvelope:
    passed: bool
    status_code: str
    validation_stage: str
    contract_version: str
    reader_status: str
    reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    component_warning_codes: tuple[str, ...]
    component_result_inconsistent: bool
    manifest_consistency_checked: bool
    manifest_consistency_passed: bool
    checksum_checked: bool
    checksum_passed: bool
    upstream_value_passed: bool
    upstream_value_status_code: str | None
    ready_for_readonly_analysis: bool
    next_allowed_stage: tuple[str, ...]
    next_blocked_stage: tuple[str, ...]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool


@dataclass(frozen=True)
class DataQualityGateV0Result:
    stage: str
    status_code: str
    can_proceed_to_schema_checks: bool
    blocked_by_read_status: bool
    blocked_by_metadata: bool
    blocked_by_freshness: bool
    reasons: list[str]
    source_read_status_code: str | None
    source_metadata_status_code: str | None
    source_freshness_status_code: str | None
    is_tradable: bool
    note: str


@dataclass(frozen=True)
class DataQualityGateV1Result:
    stage: str
    status_code: str
    data_quality_passed: bool
    can_proceed_to_read_only_analysis: bool
    blocked_by_gate_v0: bool
    blocked_by_required_fields: bool
    blocked_by_field_types: bool
    blocked_by_numeric_ranges: bool
    blocked_by_cross_field_checks: bool
    reasons: list[str]
    source_gate_v0_status_code: str | None
    source_required_fields_status_code: str | None
    source_field_types_status_code: str | None
    source_numeric_ranges_status_code: str | None
    source_cross_field_status_code: str | None
    is_tradable: bool
    note: str


def evaluate_data_quality_gate_v0(
    read_summary: Mt4SnapshotReadSummary,
    metadata_status: Mt4SnapshotMetadataStatus,
    freshness_status: Mt4SnapshotFreshnessStatus,
) -> DataQualityGateV0Result:
    blocked_by_read_status = not read_summary.can_proceed_to_metadata_checks
    blocked_by_metadata = not metadata_status.can_proceed_to_freshness_checks
    blocked_by_freshness = not freshness_status.can_proceed_to_data_quality_gate

    reasons = _reasons(
        blocked_by_read_status=blocked_by_read_status,
        blocked_by_metadata=blocked_by_metadata,
        blocked_by_freshness=blocked_by_freshness,
        read_summary=read_summary,
        metadata_status=metadata_status,
        freshness_status=freshness_status,
    )

    return DataQualityGateV0Result(
        stage=DATA_QUALITY_GATE_V0_STAGE,
        status_code=_status_code(
            blocked_by_read_status=blocked_by_read_status,
            blocked_by_metadata=blocked_by_metadata,
            blocked_by_freshness=blocked_by_freshness,
        ),
        can_proceed_to_schema_checks=len(reasons) == 0,
        blocked_by_read_status=blocked_by_read_status,
        blocked_by_metadata=blocked_by_metadata,
        blocked_by_freshness=blocked_by_freshness,
        reasons=reasons,
        source_read_status_code=read_summary.status_code,
        source_metadata_status_code=metadata_status.status_code,
        source_freshness_status_code=freshness_status.status_code,
        is_tradable=False,
        note=DATA_QUALITY_GATE_V0_NOTE,
    )


def evaluate_data_quality_gate_v1(
    gate_v0_result: DataQualityGateV0Result,
    required_fields_status: Mt4SnapshotRequiredFieldsStatus,
    field_types_status: Mt4SnapshotFieldTypesStatus,
    numeric_ranges_status: Mt4SnapshotNumericRangesStatus,
    cross_field_status: Mt4SnapshotCrossFieldStatus,
) -> DataQualityGateV1Result:
    blocked_by_gate_v0 = not gate_v0_result.can_proceed_to_schema_checks
    blocked_by_required_fields = not required_fields_status.can_proceed_to_value_checks
    blocked_by_field_types = not field_types_status.can_proceed_to_value_checks
    blocked_by_numeric_ranges = (
        not numeric_ranges_status.can_proceed_to_cross_field_checks
    )
    blocked_by_cross_field_checks = (
        not cross_field_status.can_proceed_to_data_quality_gate_finalization
    )

    reasons = _v1_reasons(
        blocked_by_gate_v0=blocked_by_gate_v0,
        blocked_by_required_fields=blocked_by_required_fields,
        blocked_by_field_types=blocked_by_field_types,
        blocked_by_numeric_ranges=blocked_by_numeric_ranges,
        blocked_by_cross_field_checks=blocked_by_cross_field_checks,
        gate_v0_result=gate_v0_result,
        required_fields_status=required_fields_status,
        field_types_status=field_types_status,
        numeric_ranges_status=numeric_ranges_status,
        cross_field_status=cross_field_status,
    )
    data_quality_passed = len(reasons) == 0

    return DataQualityGateV1Result(
        stage=DATA_QUALITY_GATE_V1_STAGE,
        status_code=_v1_status_code(
            blocked_by_gate_v0=blocked_by_gate_v0,
            blocked_by_required_fields=blocked_by_required_fields,
            blocked_by_field_types=blocked_by_field_types,
            blocked_by_numeric_ranges=blocked_by_numeric_ranges,
            blocked_by_cross_field_checks=blocked_by_cross_field_checks,
        ),
        data_quality_passed=data_quality_passed,
        can_proceed_to_read_only_analysis=data_quality_passed,
        blocked_by_gate_v0=blocked_by_gate_v0,
        blocked_by_required_fields=blocked_by_required_fields,
        blocked_by_field_types=blocked_by_field_types,
        blocked_by_numeric_ranges=blocked_by_numeric_ranges,
        blocked_by_cross_field_checks=blocked_by_cross_field_checks,
        reasons=reasons,
        source_gate_v0_status_code=gate_v0_result.status_code,
        source_required_fields_status_code=required_fields_status.status_code,
        source_field_types_status_code=field_types_status.status_code,
        source_numeric_ranges_status_code=numeric_ranges_status.status_code,
        source_cross_field_status_code=cross_field_status.status_code,
        is_tradable=False,
        note=DATA_QUALITY_GATE_V1_NOTE,
    )


def _reasons(
    *,
    blocked_by_read_status: bool,
    blocked_by_metadata: bool,
    blocked_by_freshness: bool,
    read_summary: Mt4SnapshotReadSummary,
    metadata_status: Mt4SnapshotMetadataStatus,
    freshness_status: Mt4SnapshotFreshnessStatus,
) -> list[str]:
    reasons: list[str] = []
    if blocked_by_read_status:
        reasons.append(f"read_status:{read_summary.status_code}")
    if blocked_by_metadata:
        reasons.append(f"metadata:{metadata_status.status_code}")
    if blocked_by_freshness:
        reasons.append(f"freshness:{freshness_status.status_code}")
    return reasons


def _v1_reasons(
    *,
    blocked_by_gate_v0: bool,
    blocked_by_required_fields: bool,
    blocked_by_field_types: bool,
    blocked_by_numeric_ranges: bool,
    blocked_by_cross_field_checks: bool,
    gate_v0_result: DataQualityGateV0Result,
    required_fields_status: Mt4SnapshotRequiredFieldsStatus,
    field_types_status: Mt4SnapshotFieldTypesStatus,
    numeric_ranges_status: Mt4SnapshotNumericRangesStatus,
    cross_field_status: Mt4SnapshotCrossFieldStatus,
) -> list[str]:
    reasons: list[str] = []
    if blocked_by_gate_v0:
        reasons.append(f"gate_v0:{gate_v0_result.status_code}")
    if blocked_by_required_fields:
        reasons.append(f"required_fields:{required_fields_status.status_code}")
    if blocked_by_field_types:
        reasons.append(f"field_types:{field_types_status.status_code}")
    if blocked_by_numeric_ranges:
        reasons.append(f"numeric_ranges:{numeric_ranges_status.status_code}")
    if blocked_by_cross_field_checks:
        reasons.append(f"cross_field_checks:{cross_field_status.status_code}")
    return reasons


def _status_code(
    *,
    blocked_by_read_status: bool,
    blocked_by_metadata: bool,
    blocked_by_freshness: bool,
) -> str:
    blocked_count = sum(
        (blocked_by_read_status, blocked_by_metadata, blocked_by_freshness)
    )

    if blocked_count == 0:
        return READY_FOR_SCHEMA_CHECKS
    if blocked_count > 1:
        return BLOCKED_BY_MULTIPLE_REASONS
    if blocked_by_read_status:
        return BLOCKED_BY_READ_STATUS
    if blocked_by_metadata:
        return BLOCKED_BY_METADATA
    return BLOCKED_BY_FRESHNESS


def _v1_status_code(
    *,
    blocked_by_gate_v0: bool,
    blocked_by_required_fields: bool,
    blocked_by_field_types: bool,
    blocked_by_numeric_ranges: bool,
    blocked_by_cross_field_checks: bool,
) -> str:
    blocked_count = sum(
        (
            blocked_by_gate_v0,
            blocked_by_required_fields,
            blocked_by_field_types,
            blocked_by_numeric_ranges,
            blocked_by_cross_field_checks,
        )
    )

    if blocked_count == 0:
        return DATA_QUALITY_PASSED
    if blocked_count > 1:
        return BLOCKED_BY_MULTIPLE_REASONS
    if blocked_by_gate_v0:
        return BLOCKED_BY_GATE_V0
    if blocked_by_required_fields:
        return BLOCKED_BY_REQUIRED_FIELDS
    if blocked_by_field_types:
        return BLOCKED_BY_FIELD_TYPES
    if blocked_by_numeric_ranges:
        return BLOCKED_BY_NUMERIC_RANGES
    return BLOCKED_BY_CROSS_FIELD_CHECKS


def evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate(
    *,
    reader_result: object,
    policy: CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy | None = None,
) -> dict[str, Any]:
    safe_source_reader_status: str | None = None
    safe_source_upstream_status: str | None = None

    try:
        envelope, input_reason = _parse_canonical_reader_envelope(reader_result)
        if envelope is None:
            return _canonical_data_quality_result(
                status_code=CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
                reason_code=input_reason or DATA_QUALITY_READER_FIELD_TYPE_INVALID,
            )

        effective_policy = _canonical_data_quality_policy(policy)
        if effective_policy is None:
            return _canonical_data_quality_result(
                status_code=CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID,
                reason_code=DATA_QUALITY_POLICY_INVALID,
            )

        if envelope.status_code in _CANONICAL_READER_STATUS_CODES:
            safe_source_reader_status = envelope.status_code
        if (
            envelope.upstream_value_status_code is None
            or envelope.upstream_value_status_code in _CANONICAL_VALUE_STATUS_CODES
        ):
            safe_source_upstream_status = envelope.upstream_value_status_code

        warnings_are_safe = (
            envelope.warning_codes == envelope.component_warning_codes
            and len(envelope.warning_codes) == len(set(envelope.warning_codes))
            and all(
                warning_code in CANONICAL_MT4_BUNDLE_V1_WARNING_CODES
                for warning_code in envelope.warning_codes
            )
        )
        safe_warnings = envelope.warning_codes if warnings_are_safe else ()

        safety_reason = _canonical_reader_safety_reason(
            envelope,
            warnings_are_safe=warnings_are_safe,
        )
        if safety_reason is not None:
            return _canonical_data_quality_result(
                status_code=CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
                reason_code=safety_reason,
                source_reader_status_code=safe_source_reader_status,
                source_upstream_value_status_code=safe_source_upstream_status,
                warning_codes=safe_warnings,
            )

        blocked_status = _canonical_upstream_blocked_status(envelope)
        if blocked_status is not None:
            status_code, reason_code = blocked_status
            return _canonical_data_quality_result(
                status_code=status_code,
                reason_code=reason_code,
                source_reader_status_code=safe_source_reader_status,
                source_upstream_value_status_code=safe_source_upstream_status,
                warning_codes=safe_warnings,
            )

        if envelope.warning_codes and not effective_policy.allow_upstream_warnings:
            return _canonical_data_quality_result(
                status_code=CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED,
                reason_code=UPSTREAM_WARNINGS_REJECTED_BY_POLICY,
                source_reader_status_code=safe_source_reader_status,
                source_upstream_value_status_code=safe_source_upstream_status,
                warning_codes=safe_warnings,
            )

        has_warnings = bool(envelope.warning_codes)
        return _canonical_data_quality_result(
            status_code=(
                CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
                if has_warnings
                else CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED
            ),
            passed=True,
            data_quality_status=(
                "passed_with_warnings" if has_warnings else "passed"
            ),
            source_reader_status_code=safe_source_reader_status,
            source_upstream_value_status_code=safe_source_upstream_status,
            warning_codes=safe_warnings,
        )
    except Exception:
        return _canonical_data_quality_result(
            status_code=CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE,
            reason_code=DATA_QUALITY_GATE_EXCEPTION_SANITIZED,
            source_reader_status_code=safe_source_reader_status,
            source_upstream_value_status_code=safe_source_upstream_status,
        )


def _parse_canonical_reader_envelope(
    reader_result: object,
) -> tuple[_CanonicalReaderEnvelope | None, str | None]:
    if type(reader_result) is not dict:
        return None, DATA_QUALITY_INPUT_NOT_OBJECT

    reader_keys = set(reader_result)
    if _CANONICAL_READER_RESULT_KEYS - reader_keys:
        return None, DATA_QUALITY_REQUIRED_READER_KEY_MISSING
    if reader_keys - _CANONICAL_READER_RESULT_KEYS:
        return None, DATA_QUALITY_UNEXPECTED_READER_KEY

    if any(type(reader_result[field]) is not bool for field in _CANONICAL_BOOL_FIELDS):
        return None, DATA_QUALITY_READER_FIELD_TYPE_INVALID
    if any(
        type(reader_result[field]) is not str for field in _CANONICAL_STRING_FIELDS
    ):
        return None, DATA_QUALITY_READER_FIELD_TYPE_INVALID

    string_lists: dict[str, tuple[str, ...]] = {}
    for field in _CANONICAL_STRING_LIST_FIELDS:
        converted = _strict_string_list(reader_result[field])
        if converted is None:
            return None, DATA_QUALITY_READER_FIELD_TYPE_INVALID
        string_lists[field] = converted

    upstream_status = reader_result["upstream_value_status_code"]
    if upstream_status is not None and type(upstream_status) is not str:
        return None, DATA_QUALITY_READER_FIELD_TYPE_INVALID

    if not _safe_code_list(string_lists["reason_codes"]):
        return None, DATA_QUALITY_READER_FIELD_TYPE_INVALID

    component_summary = _parse_canonical_component_statuses(
        reader_result["component_statuses"]
    )
    if component_summary is None:
        return None, DATA_QUALITY_COMPONENT_STATUS_INVALID
    component_warnings, component_result_inconsistent = component_summary

    return (
        _CanonicalReaderEnvelope(
            passed=reader_result["passed"],
            status_code=reader_result["status_code"],
            validation_stage=reader_result["validation_stage"],
            contract_version=reader_result["contract_version"],
            reader_status=reader_result["reader_status"],
            reason_codes=string_lists["reason_codes"],
            warning_codes=string_lists["warning_codes"],
            component_warning_codes=component_warnings,
            component_result_inconsistent=component_result_inconsistent,
            manifest_consistency_checked=reader_result[
                "manifest_consistency_checked"
            ],
            manifest_consistency_passed=reader_result[
                "manifest_consistency_passed"
            ],
            checksum_checked=reader_result["checksum_checked"],
            checksum_passed=reader_result["checksum_passed"],
            upstream_value_passed=reader_result["upstream_value_passed"],
            upstream_value_status_code=upstream_status,
            ready_for_readonly_analysis=reader_result[
                "ready_for_readonly_analysis"
            ],
            next_allowed_stage=string_lists["next_allowed_stage"],
            next_blocked_stage=string_lists["next_blocked_stage"],
            read_only=reader_result["read_only"],
            demo_only=reader_result["demo_only"],
            is_tradable=reader_result["is_tradable"],
            can_execute=reader_result["can_execute"],
            is_trading_permission=reader_result["is_trading_permission"],
            is_execution_instruction=reader_result["is_execution_instruction"],
            allowed_to_call_ea=reader_result["allowed_to_call_ea"],
            allowed_to_modify_risk=reader_result["allowed_to_modify_risk"],
        ),
        None,
    )


def _parse_canonical_component_statuses(
    component_statuses: object,
) -> tuple[tuple[str, ...], bool] | None:
    if type(component_statuses) is not list:
        return None
    if len(component_statuses) != len(_CANONICAL_COMPONENT_NAMES):
        return None

    ordered_warnings: list[str] = []
    result_inconsistent = False
    for expected_name, component in zip(
        _CANONICAL_COMPONENT_NAMES,
        component_statuses,
        strict=True,
    ):
        if type(component) is not dict or set(component) != _CANONICAL_COMPONENT_KEYS:
            return None
        if type(component["component_name"]) is not str:
            return None
        if component["component_name"] != expected_name:
            return None
        if type(component["passed"]) is not bool:
            return None
        if type(component["status_code"]) is not str:
            return None
        if not component["status_code"].startswith(
            "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_"
        ) or _SAFE_CODE_PATTERN.fullmatch(component["status_code"]) is None:
            return None

        reason_codes = _strict_string_list(component["reason_codes"])
        warning_codes = _strict_string_list(component["warning_codes"])
        if reason_codes is None or warning_codes is None:
            return None
        if not _safe_code_list(reason_codes):
            return None
        if len(warning_codes) != len(set(warning_codes)):
            return None
        if component["passed"] and reason_codes:
            result_inconsistent = True
        for warning_code in warning_codes:
            if warning_code not in ordered_warnings:
                ordered_warnings.append(warning_code)

    return tuple(ordered_warnings), result_inconsistent


def _canonical_data_quality_policy(
    policy: CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy | None,
) -> CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy | None:
    if policy is None:
        return CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy()
    if type(policy) is not CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy:
        return None
    if type(policy.allow_upstream_warnings) is not bool:
        return None
    return policy


def _canonical_reader_safety_reason(
    envelope: _CanonicalReaderEnvelope,
    *,
    warnings_are_safe: bool,
) -> str | None:
    if (
        envelope.validation_stage != _CANONICAL_READER_STAGE
        or envelope.contract_version != _CANONICAL_CONTRACT_VERSION
    ):
        return READER_SAFETY_ENVELOPE_INVALID
    if envelope.status_code not in _CANONICAL_READER_STATUS_CODES:
        return READER_SAFETY_ENVELOPE_INVALID
    if (
        envelope.upstream_value_status_code is not None
        and envelope.upstream_value_status_code not in _CANONICAL_VALUE_STATUS_CODES
    ):
        return READER_SAFETY_ENVELOPE_INVALID
    if envelope.reader_status not in {"validated_isolated", "blocked"}:
        return READER_SAFETY_ENVELOPE_INVALID
    if not warnings_are_safe:
        return READER_WARNING_CODES_INVALID
    if envelope.component_result_inconsistent:
        return READER_RESULT_INCONSISTENT
    if not _canonical_fixed_safety_flags(envelope):
        return READER_SAFETY_ENVELOPE_INVALID
    if (
        not envelope.manifest_consistency_checked
        and envelope.manifest_consistency_passed
    ):
        return READER_RESULT_INCONSISTENT
    if not _canonical_upstream_status_consistent(envelope):
        return READER_RESULT_INCONSISTENT

    if envelope.status_code == CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID:
        return _canonical_success_consistency_reason(envelope, with_warnings=False)
    if (
        envelope.status_code
        == CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS
    ):
        return _canonical_success_consistency_reason(envelope, with_warnings=True)

    if (
        envelope.passed
        or envelope.reader_status != "blocked"
        or not envelope.reason_codes
        or envelope.ready_for_readonly_analysis
        or envelope.next_allowed_stage
        or envelope.next_blocked_stage != _CANONICAL_SOURCE_NEXT_BLOCKED_STAGE
    ):
        return READER_RESULT_INCONSISTENT
    if (
        envelope.status_code
        == CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE
        and (
            not envelope.manifest_consistency_checked
            or envelope.manifest_consistency_passed
        )
    ):
        return READER_RESULT_INCONSISTENT
    if (
        envelope.status_code
        == CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH
        and (not envelope.checksum_checked or envelope.checksum_passed)
    ):
        return READER_RESULT_INCONSISTENT
    if (
        envelope.status_code
        != CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH
        and envelope.checksum_checked
        and not envelope.checksum_passed
    ):
        return READER_RESULT_INCONSISTENT
    return None


def _canonical_success_consistency_reason(
    envelope: _CanonicalReaderEnvelope,
    *,
    with_warnings: bool,
) -> str | None:
    expected_upstream_status = (
        CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS
        if with_warnings
        else CANONICAL_MT4_BUNDLE_V1_VALUE_VALID
    )
    if (
        not envelope.passed
        or envelope.reader_status != "validated_isolated"
        or envelope.reason_codes
        or bool(envelope.warning_codes) is not with_warnings
        or not envelope.manifest_consistency_checked
        or not envelope.manifest_consistency_passed
        or not envelope.checksum_passed
        or not envelope.upstream_value_passed
        or envelope.upstream_value_status_code != expected_upstream_status
        or envelope.ready_for_readonly_analysis
        or envelope.next_allowed_stage != _CANONICAL_SOURCE_NEXT_ALLOWED_STAGE
        or envelope.next_blocked_stage != _CANONICAL_SOURCE_NEXT_BLOCKED_STAGE
    ):
        return READER_RESULT_INCONSISTENT
    return None


def _canonical_upstream_status_consistent(
    envelope: _CanonicalReaderEnvelope,
) -> bool:
    upstream_status = envelope.upstream_value_status_code
    if upstream_status is None:
        return not envelope.upstream_value_passed
    if upstream_status in {
        CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
        CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS,
    }:
        if not envelope.upstream_value_passed:
            return False
        if upstream_status == CANONICAL_MT4_BUNDLE_V1_VALUE_VALID:
            return not envelope.warning_codes
        return bool(envelope.warning_codes)
    return not envelope.upstream_value_passed


def _canonical_fixed_safety_flags(envelope: _CanonicalReaderEnvelope) -> bool:
    return (
        envelope.read_only
        and envelope.demo_only
        and not envelope.is_tradable
        and not envelope.can_execute
        and not envelope.is_trading_permission
        and not envelope.is_execution_instruction
        and not envelope.allowed_to_call_ea
        and not envelope.allowed_to_modify_risk
    )


def _canonical_upstream_blocked_status(
    envelope: _CanonicalReaderEnvelope,
) -> tuple[str, str] | None:
    if envelope.status_code in {
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS,
    }:
        return None
    if (
        envelope.status_code
        == CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE
    ):
        return (
            CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED,
            READER_MIXED_GENERATION_BLOCKED,
        )
    if (
        envelope.status_code
        == CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH
    ):
        return (
            CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED,
            READER_INTEGRITY_INVALID,
        )
    if envelope.upstream_value_status_code == CANONICAL_MT4_BUNDLE_V1_DATA_STALE:
        return (
            CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED,
            READER_DATA_STALE,
        )
    if (
        envelope.status_code in _CANONICAL_STRUCTURE_READER_STATUS_CODES
        or envelope.upstream_value_status_code
        == CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED
    ):
        return (
            CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED,
            READER_STRUCTURE_INVALID,
        )
    if envelope.upstream_value_status_code in _CANONICAL_VALUE_INVALID_STATUS_CODES:
        return (
            CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED,
            READER_VALUE_INVALID,
        )
    return (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED,
        READER_BLOCKED,
    )


def _canonical_data_quality_result(
    *,
    status_code: str,
    passed: bool = False,
    data_quality_status: str = "blocked",
    reason_code: str | None = None,
    source_reader_status_code: str | None = None,
    source_upstream_value_status_code: str | None = None,
    warning_codes: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "passed": passed,
        "status_code": status_code,
        "validation_stage": CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STAGE,
        "contract_version": CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_CONTRACT_VERSION,
        "reader_status": "validated_isolated" if passed else "blocked",
        "source_reader_status_code": source_reader_status_code,
        "source_upstream_value_status_code": source_upstream_value_status_code,
        "data_quality_status": data_quality_status,
        "reason_codes": [reason_code] if reason_code is not None else [],
        "warning_codes": list(warning_codes),
        "ready_for_readonly_analysis": passed,
        "next_allowed_stage": (
            list(_CANONICAL_SUCCESS_NEXT_ALLOWED_STAGE) if passed else []
        ),
        "next_blocked_stage": list(
            _CANONICAL_SUCCESS_NEXT_BLOCKED_STAGE
            if passed
            else _CANONICAL_BLOCKED_NEXT_STAGE
        ),
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }


def _strict_string_list(value: object) -> tuple[str, ...] | None:
    if type(value) is not list:
        return None
    if any(type(item) is not str for item in value):
        return None
    return tuple(value)


def _safe_code_list(values: tuple[str, ...]) -> bool:
    return (
        len(values) == len(set(values))
        and all(_SAFE_CODE_PATTERN.fullmatch(value) is not None for value in values)
    )
