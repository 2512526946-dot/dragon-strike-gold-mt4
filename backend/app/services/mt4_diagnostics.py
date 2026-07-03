from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.services.data_quality_gate import (
    DataQualityGateV0Result,
    DataQualityGateV1Result,
    evaluate_data_quality_gate_v0,
    evaluate_data_quality_gate_v1,
)
from app.services.mt4_cross_field_checks import (
    Mt4SnapshotCrossFieldStatus,
    check_mt4_snapshot_cross_fields,
)
from app.services.mt4_field_types import (
    Mt4SnapshotFieldTypesStatus,
    check_mt4_snapshot_field_types,
)
from app.services.mt4_numeric_ranges import (
    Mt4SnapshotNumericRangesStatus,
    check_mt4_snapshot_numeric_ranges,
)
from app.services.mt4_required_fields import (
    Mt4SnapshotRequiredFieldsStatus,
    check_mt4_snapshot_required_fields,
)
from app.services.mt4_snapshot_freshness import (
    Mt4SnapshotFreshnessStatus,
    check_mt4_snapshot_freshness,
)
from app.services.mt4_snapshot_metadata import (
    Mt4SnapshotMetadataStatus,
    check_mt4_snapshot_metadata,
)
from app.services.mt4_snapshot_reader import read_mt4_snapshot_files
from app.services.mt4_snapshot_status import (
    Mt4SnapshotReadSummary,
    summarize_mt4_snapshot_read_result,
)


MT4_DIAGNOSTICS_STAGE = "mt4_diagnostics_v1"
MT4_DIAGNOSTICS_NOTE = (
    "Diagnostics are read-only. "
    "Diagnostics are not trading permission. "
    "Diagnostics do not generate trading signals."
)


@dataclass(frozen=True)
class Mt4DiagnosticsResult:
    stage: str
    status_code: str
    data_quality_passed: bool
    can_proceed_to_read_only_analysis: bool
    read_summary: Mt4SnapshotReadSummary
    metadata_status: Mt4SnapshotMetadataStatus
    freshness_status: Mt4SnapshotFreshnessStatus
    gate_v0_result: DataQualityGateV0Result
    required_fields_status: Mt4SnapshotRequiredFieldsStatus
    field_types_status: Mt4SnapshotFieldTypesStatus
    numeric_ranges_status: Mt4SnapshotNumericRangesStatus
    cross_field_status: Mt4SnapshotCrossFieldStatus
    gate_v1_result: DataQualityGateV1Result
    is_tradable: bool
    note: str


def build_mt4_diagnostics(
    base_dir: Path | str,
    now_utc: datetime,
) -> Mt4DiagnosticsResult:
    snapshot = read_mt4_snapshot_files(base_dir)
    read_summary = summarize_mt4_snapshot_read_result(snapshot)
    metadata_status = check_mt4_snapshot_metadata(snapshot)
    freshness_status = check_mt4_snapshot_freshness(metadata_status, now_utc)
    gate_v0_result = evaluate_data_quality_gate_v0(
        read_summary,
        metadata_status,
        freshness_status,
    )
    required_fields_status = check_mt4_snapshot_required_fields(snapshot)
    field_types_status = check_mt4_snapshot_field_types(
        snapshot,
        required_fields_status,
    )
    numeric_ranges_status = check_mt4_snapshot_numeric_ranges(
        snapshot,
        field_types_status,
    )
    cross_field_status = check_mt4_snapshot_cross_fields(
        snapshot,
        numeric_ranges_status,
    )
    gate_v1_result = evaluate_data_quality_gate_v1(
        gate_v0_result,
        required_fields_status,
        field_types_status,
        numeric_ranges_status,
        cross_field_status,
    )

    return Mt4DiagnosticsResult(
        stage=MT4_DIAGNOSTICS_STAGE,
        status_code=gate_v1_result.status_code,
        data_quality_passed=gate_v1_result.data_quality_passed,
        can_proceed_to_read_only_analysis=(
            gate_v1_result.can_proceed_to_read_only_analysis
        ),
        read_summary=read_summary,
        metadata_status=metadata_status,
        freshness_status=freshness_status,
        gate_v0_result=gate_v0_result,
        required_fields_status=required_fields_status,
        field_types_status=field_types_status,
        numeric_ranges_status=numeric_ranges_status,
        cross_field_status=cross_field_status,
        gate_v1_result=gate_v1_result,
        is_tradable=False,
        note=MT4_DIAGNOSTICS_NOTE,
    )
