from datetime import UTC, datetime

from app.services.data_quality_gate import (
    BLOCKED_BY_FRESHNESS,
    BLOCKED_BY_METADATA,
    BLOCKED_BY_MULTIPLE_REASONS,
    BLOCKED_BY_READ_STATUS,
    DATA_QUALITY_GATE_V0_STAGE,
    READY_FOR_SCHEMA_CHECKS,
    DataQualityGateV0Result,
    evaluate_data_quality_gate_v0,
)
from app.services.mt4_snapshot_freshness import (
    ALL_FILES_FRESH,
    FRESHNESS_OK,
    SOME_FILES_STALE,
    Mt4FileFreshnessStatus,
    Mt4SnapshotFreshnessStatus,
)
from app.services.mt4_snapshot_metadata import (
    ACCOUNT_SNAPSHOT_FILE_TYPE,
    ALL_METADATA_OK,
    LATEST_BARS_FILE_TYPE,
    LIVE_TICK_FILE_TYPE,
    METADATA_OK,
    SOME_METADATA_MISSING,
    SYMBOL_SPEC_FILE_TYPE,
    Mt4FileMetadataStatus,
    Mt4SnapshotMetadataStatus,
)
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
)
from app.services.mt4_snapshot_status import (
    ALL_FILES_READABLE_OBJECTS,
    SOME_FILES_MISSING,
    Mt4SnapshotReadSummary,
)


NOW_UTC = datetime(2026, 7, 3, 10, 15, 30, tzinfo=UTC)


def _read_summary(*, can_proceed: bool = True) -> Mt4SnapshotReadSummary:
    return Mt4SnapshotReadSummary(
        total_files=4,
        present_file_count=4 if can_proceed else 3,
        readable_object_count=4 if can_proceed else 3,
        missing_files=[] if can_proceed else [LIVE_TICK_FILE],
        not_file_paths=[],
        invalid_json_files=[],
        not_object_files=[],
        read_error_files=[],
        all_files_present=can_proceed,
        all_json_valid=can_proceed,
        all_objects=can_proceed,
        can_proceed_to_metadata_checks=can_proceed,
        status_code=ALL_FILES_READABLE_OBJECTS if can_proceed else SOME_FILES_MISSING,
    )


def _file_metadata(
    file_name: str,
    expected_file_type: str,
    *,
    can_proceed: bool = True,
) -> Mt4FileMetadataStatus:
    return Mt4FileMetadataStatus(
        file_name=file_name,
        expected_file_type=expected_file_type,
        actual_file_type=expected_file_type if can_proceed else None,
        schema_version="1.0",
        source="mt4_file_bridge",
        generated_at="2026-07-03T10:15:25Z",
        has_schema_version=True,
        has_file_type=can_proceed,
        has_source=True,
        has_generated_at=True,
        file_type_matches=can_proceed,
        source_matches=True,
        can_proceed_to_freshness_checks=can_proceed,
        status_code=METADATA_OK if can_proceed else SOME_METADATA_MISSING,
        error_codes=[] if can_proceed else ["MISSING_FILE_TYPE"],
    )


def _metadata_status(*, can_proceed: bool = True) -> Mt4SnapshotMetadataStatus:
    return Mt4SnapshotMetadataStatus(
        live_tick=_file_metadata(
            LIVE_TICK_FILE, LIVE_TICK_FILE_TYPE, can_proceed=can_proceed
        ),
        latest_bars=_file_metadata(
            LATEST_BARS_FILE, LATEST_BARS_FILE_TYPE, can_proceed=can_proceed
        ),
        symbol_spec=_file_metadata(
            SYMBOL_SPEC_FILE, SYMBOL_SPEC_FILE_TYPE, can_proceed=can_proceed
        ),
        account_snapshot=_file_metadata(
            ACCOUNT_SNAPSHOT_FILE,
            ACCOUNT_SNAPSHOT_FILE_TYPE,
            can_proceed=can_proceed,
        ),
        all_metadata_present=can_proceed,
        all_file_types_match=can_proceed,
        all_sources_match=True,
        can_proceed_to_freshness_checks=can_proceed,
        status_code=ALL_METADATA_OK if can_proceed else SOME_METADATA_MISSING,
    )


def _file_freshness(file_name: str, *, can_proceed: bool = True) -> Mt4FileFreshnessStatus:
    return Mt4FileFreshnessStatus(
        file_name=file_name,
        generated_at="2026-07-03T10:15:25Z",
        parsed_generated_at_utc=NOW_UTC,
        age_seconds=5 if can_proceed else 120,
        max_age_seconds=10,
        max_future_skew_seconds=5,
        is_parseable=True,
        is_fresh=can_proceed,
        is_stale=not can_proceed,
        is_from_future=False,
        can_proceed_to_data_quality_gate=can_proceed,
        status_code=FRESHNESS_OK if can_proceed else SOME_FILES_STALE,
        error_codes=[] if can_proceed else ["GENERATED_AT_STALE"],
    )


def _freshness_status(*, can_proceed: bool = True) -> Mt4SnapshotFreshnessStatus:
    return Mt4SnapshotFreshnessStatus(
        live_tick=_file_freshness(LIVE_TICK_FILE, can_proceed=can_proceed),
        latest_bars=_file_freshness(LATEST_BARS_FILE, can_proceed=can_proceed),
        symbol_spec=_file_freshness(SYMBOL_SPEC_FILE, can_proceed=can_proceed),
        account_snapshot=_file_freshness(
            ACCOUNT_SNAPSHOT_FILE, can_proceed=can_proceed
        ),
        all_generated_at_parseable=True,
        all_files_fresh=can_proceed,
        any_file_stale=not can_proceed,
        any_file_from_future=False,
        can_proceed_to_data_quality_gate=can_proceed,
        status_code=ALL_FILES_FRESH if can_proceed else SOME_FILES_STALE,
    )


def test_data_quality_gate_v0_ready_for_schema_checks() -> None:
    result = evaluate_data_quality_gate_v0(
        _read_summary(),
        _metadata_status(),
        _freshness_status(),
    )

    assert isinstance(result, DataQualityGateV0Result)
    assert result.stage == DATA_QUALITY_GATE_V0_STAGE
    assert result.status_code == READY_FOR_SCHEMA_CHECKS
    assert result.can_proceed_to_schema_checks is True
    assert result.blocked_by_read_status is False
    assert result.blocked_by_metadata is False
    assert result.blocked_by_freshness is False
    assert result.reasons == []
    assert result.is_tradable is False


def test_data_quality_gate_v0_blocked_by_read_summary() -> None:
    result = evaluate_data_quality_gate_v0(
        _read_summary(can_proceed=False),
        _metadata_status(),
        _freshness_status(),
    )

    assert result.blocked_by_read_status is True
    assert result.blocked_by_metadata is False
    assert result.blocked_by_freshness is False
    assert result.status_code == BLOCKED_BY_READ_STATUS
    assert result.can_proceed_to_schema_checks is False
    assert result.reasons == [f"read_status:{SOME_FILES_MISSING}"]
    assert result.source_read_status_code == SOME_FILES_MISSING


def test_data_quality_gate_v0_blocked_by_metadata() -> None:
    result = evaluate_data_quality_gate_v0(
        _read_summary(),
        _metadata_status(can_proceed=False),
        _freshness_status(),
    )

    assert result.blocked_by_metadata is True
    assert result.status_code == BLOCKED_BY_METADATA
    assert result.can_proceed_to_schema_checks is False
    assert result.reasons == [f"metadata:{SOME_METADATA_MISSING}"]
    assert result.source_metadata_status_code == SOME_METADATA_MISSING


def test_data_quality_gate_v0_blocked_by_freshness() -> None:
    result = evaluate_data_quality_gate_v0(
        _read_summary(),
        _metadata_status(),
        _freshness_status(can_proceed=False),
    )

    assert result.blocked_by_freshness is True
    assert result.status_code == BLOCKED_BY_FRESHNESS
    assert result.can_proceed_to_schema_checks is False
    assert result.reasons == [f"freshness:{SOME_FILES_STALE}"]
    assert result.source_freshness_status_code == SOME_FILES_STALE


def test_data_quality_gate_v0_blocked_by_multiple_reasons() -> None:
    result = evaluate_data_quality_gate_v0(
        _read_summary(can_proceed=False),
        _metadata_status(can_proceed=False),
        _freshness_status(can_proceed=False),
    )

    assert result.status_code == BLOCKED_BY_MULTIPLE_REASONS
    assert result.can_proceed_to_schema_checks is False
    assert result.blocked_by_read_status is True
    assert result.blocked_by_metadata is True
    assert result.blocked_by_freshness is True
    assert result.reasons == [
        f"read_status:{SOME_FILES_MISSING}",
        f"metadata:{SOME_METADATA_MISSING}",
        f"freshness:{SOME_FILES_STALE}",
    ]


def test_data_quality_gate_v0_note_and_tradable_boundary() -> None:
    result = evaluate_data_quality_gate_v0(
        _read_summary(),
        _metadata_status(),
        _freshness_status(),
    )

    assert result.is_tradable is False
    assert "DataQualityGate v0 is not a trading permission." in result.note
    assert "It does not generate trading signals." in result.note


def test_data_quality_gate_v0_uses_constructed_results_only(tmp_path) -> None:
    result = evaluate_data_quality_gate_v0(
        _read_summary(),
        _metadata_status(),
        _freshness_status(),
    )

    assert result.status_code == READY_FOR_SCHEMA_CHECKS
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")
