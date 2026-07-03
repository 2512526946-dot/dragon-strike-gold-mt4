from __future__ import annotations

from dataclasses import dataclass

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
