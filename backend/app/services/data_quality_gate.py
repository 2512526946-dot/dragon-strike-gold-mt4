from __future__ import annotations

from dataclasses import dataclass

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
