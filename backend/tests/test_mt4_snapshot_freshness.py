from datetime import UTC, datetime

from app.services.mt4_snapshot_freshness import (
    ACCOUNT_SNAPSHOT_FILE,
    ALL_FILES_FRESH,
    FRESHNESS_OK,
    GENERATED_AT_FROM_FUTURE,
    GENERATED_AT_STALE,
    INVALID_GENERATED_AT,
    METADATA_NOT_READY,
    MISSING_GENERATED_AT,
    SOME_FILES_FROM_FUTURE,
    SOME_FILES_STALE,
    SOME_GENERATED_AT_INVALID,
    SOME_GENERATED_AT_MISSING,
    SOME_METADATA_NOT_READY,
    Mt4FileFreshnessStatus,
    Mt4SnapshotFreshnessStatus,
    check_mt4_file_freshness,
    check_mt4_snapshot_freshness,
)
from app.services.mt4_snapshot_metadata import (
    ACCOUNT_SNAPSHOT_FILE_TYPE,
    LATEST_BARS_FILE_TYPE,
    LIVE_TICK_FILE_TYPE,
    METADATA_OK,
    MISSING_FILE_TYPE,
    MT4_FILE_BRIDGE_SOURCE,
    SYMBOL_SPEC_FILE_TYPE,
    Mt4FileMetadataStatus,
    Mt4SnapshotMetadataStatus,
)
from app.services.mt4_snapshot_reader import (
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
)


NOW_UTC = datetime(2026, 7, 3, 10, 15, 30, tzinfo=UTC)


def _metadata_status(
    *,
    file_name: str,
    expected_file_type: str,
    generated_at: str | None,
    can_proceed: bool = True,
    status_code: str = METADATA_OK,
    error_codes: list[str] | None = None,
) -> Mt4FileMetadataStatus:
    has_generated_at = generated_at is not None
    return Mt4FileMetadataStatus(
        file_name=file_name,
        expected_file_type=expected_file_type,
        actual_file_type=expected_file_type,
        schema_version="1.0",
        source=MT4_FILE_BRIDGE_SOURCE,
        generated_at=generated_at,
        has_schema_version=True,
        has_file_type=True,
        has_source=True,
        has_generated_at=has_generated_at,
        file_type_matches=True,
        source_matches=True,
        can_proceed_to_freshness_checks=can_proceed,
        status_code=status_code,
        error_codes=error_codes or [],
    )


def _fresh_metadata_snapshot(
    *,
    live_tick_generated_at: str = "2026-07-03T10:15:25Z",
    latest_bars_generated_at: str = "2026-07-03T10:14:50Z",
    symbol_spec_generated_at: str = "2026-07-02T10:15:30Z",
    account_snapshot_generated_at: str = "2026-07-03T10:15:05Z",
) -> Mt4SnapshotMetadataStatus:
    live_tick = _metadata_status(
        file_name=LIVE_TICK_FILE,
        expected_file_type=LIVE_TICK_FILE_TYPE,
        generated_at=live_tick_generated_at,
    )
    latest_bars = _metadata_status(
        file_name=LATEST_BARS_FILE,
        expected_file_type=LATEST_BARS_FILE_TYPE,
        generated_at=latest_bars_generated_at,
    )
    symbol_spec = _metadata_status(
        file_name=SYMBOL_SPEC_FILE,
        expected_file_type=SYMBOL_SPEC_FILE_TYPE,
        generated_at=symbol_spec_generated_at,
    )
    account_snapshot = _metadata_status(
        file_name=ACCOUNT_SNAPSHOT_FILE,
        expected_file_type=ACCOUNT_SNAPSHOT_FILE_TYPE,
        generated_at=account_snapshot_generated_at,
    )
    return Mt4SnapshotMetadataStatus(
        live_tick=live_tick,
        latest_bars=latest_bars,
        symbol_spec=symbol_spec,
        account_snapshot=account_snapshot,
        all_metadata_present=True,
        all_file_types_match=True,
        all_sources_match=True,
        can_proceed_to_freshness_checks=True,
        status_code=METADATA_OK,
    )


def test_freshness_all_files_fresh() -> None:
    status = check_mt4_snapshot_freshness(_fresh_metadata_snapshot(), NOW_UTC)

    assert isinstance(status, Mt4SnapshotFreshnessStatus)
    assert isinstance(status.live_tick, Mt4FileFreshnessStatus)
    assert status.all_generated_at_parseable is True
    assert status.all_files_fresh is True
    assert status.can_proceed_to_data_quality_gate is True
    assert status.status_code == ALL_FILES_FRESH
    assert status.live_tick.status_code == FRESHNESS_OK
    assert status.live_tick.age_seconds == 5


def test_freshness_live_tick_stale() -> None:
    status = check_mt4_snapshot_freshness(
        _fresh_metadata_snapshot(live_tick_generated_at="2026-07-03T10:15:19Z"),
        NOW_UTC,
    )

    assert status.live_tick.is_stale is True
    assert status.live_tick.error_codes == [GENERATED_AT_STALE]
    assert status.live_tick.status_code == GENERATED_AT_STALE
    assert status.can_proceed_to_data_quality_gate is False
    assert status.status_code == SOME_FILES_STALE


def test_freshness_account_snapshot_stale() -> None:
    status = check_mt4_snapshot_freshness(
        _fresh_metadata_snapshot(
            account_snapshot_generated_at="2026-07-03T10:14:59Z"
        ),
        NOW_UTC,
    )

    assert status.account_snapshot.is_stale is True
    assert status.account_snapshot.error_codes == [GENERATED_AT_STALE]
    assert status.can_proceed_to_data_quality_gate is False
    assert status.status_code == SOME_FILES_STALE


def test_freshness_generated_at_missing() -> None:
    metadata_status = _metadata_status(
        file_name=LIVE_TICK_FILE,
        expected_file_type=LIVE_TICK_FILE_TYPE,
        generated_at=None,
        can_proceed=False,
    )

    status = check_mt4_file_freshness(metadata_status, NOW_UTC, max_age_seconds=10)

    assert status.generated_at is None
    assert status.is_parseable is False
    assert status.error_codes == [MISSING_GENERATED_AT]
    assert status.status_code == MISSING_GENERATED_AT

    snapshot_status = check_mt4_snapshot_freshness(
        _fresh_metadata_snapshot(live_tick_generated_at=None),
        NOW_UTC,
    )
    assert snapshot_status.status_code == SOME_GENERATED_AT_MISSING


def test_freshness_generated_at_invalid() -> None:
    status = check_mt4_snapshot_freshness(
        _fresh_metadata_snapshot(latest_bars_generated_at="not-a-time"),
        NOW_UTC,
    )

    assert status.latest_bars.is_parseable is False
    assert status.latest_bars.error_codes == [INVALID_GENERATED_AT]
    assert status.latest_bars.status_code == INVALID_GENERATED_AT
    assert status.status_code == SOME_GENERATED_AT_INVALID
    assert status.can_proceed_to_data_quality_gate is False


def test_freshness_generated_at_from_future() -> None:
    status = check_mt4_snapshot_freshness(
        _fresh_metadata_snapshot(live_tick_generated_at="2026-07-03T10:15:40Z"),
        NOW_UTC,
    )

    assert status.live_tick.is_from_future is True
    assert status.live_tick.error_codes == [GENERATED_AT_FROM_FUTURE]
    assert status.live_tick.status_code == GENERATED_AT_FROM_FUTURE
    assert status.status_code == SOME_FILES_FROM_FUTURE
    assert status.can_proceed_to_data_quality_gate is False


def test_freshness_metadata_not_ready() -> None:
    metadata_status = _metadata_status(
        file_name=LIVE_TICK_FILE,
        expected_file_type=LIVE_TICK_FILE_TYPE,
        generated_at="2026-07-03T10:15:25Z",
        can_proceed=False,
        status_code=MISSING_FILE_TYPE,
        error_codes=[MISSING_FILE_TYPE],
    )
    snapshot = _fresh_metadata_snapshot()
    snapshot = Mt4SnapshotMetadataStatus(
        live_tick=metadata_status,
        latest_bars=snapshot.latest_bars,
        symbol_spec=snapshot.symbol_spec,
        account_snapshot=snapshot.account_snapshot,
        all_metadata_present=False,
        all_file_types_match=False,
        all_sources_match=True,
        can_proceed_to_freshness_checks=False,
        status_code=MISSING_FILE_TYPE,
    )

    status = check_mt4_snapshot_freshness(snapshot, NOW_UTC)

    assert status.live_tick.status_code == METADATA_NOT_READY
    assert status.live_tick.error_codes == [METADATA_NOT_READY]
    assert status.status_code == SOME_METADATA_NOT_READY
    assert status.can_proceed_to_data_quality_gate is False


def test_freshness_supports_z_suffix_utc() -> None:
    metadata_status = _metadata_status(
        file_name=LIVE_TICK_FILE,
        expected_file_type=LIVE_TICK_FILE_TYPE,
        generated_at="2026-07-03T10:15:20Z",
    )

    status = check_mt4_file_freshness(metadata_status, NOW_UTC, max_age_seconds=10)

    assert status.parsed_generated_at_utc == datetime(
        2026, 7, 3, 10, 15, 20, tzinfo=UTC
    )
    assert status.age_seconds == 10
    assert status.status_code == FRESHNESS_OK


def test_freshness_supports_timezone_offset() -> None:
    status = check_mt4_snapshot_freshness(
        _fresh_metadata_snapshot(
            account_snapshot_generated_at="2026-07-03T18:15:20+08:00"
        ),
        NOW_UTC,
    )

    assert status.account_snapshot.parsed_generated_at_utc == datetime(
        2026, 7, 3, 10, 15, 20, tzinfo=UTC
    )
    assert status.account_snapshot.age_seconds == 10
    assert status.account_snapshot.status_code == FRESHNESS_OK


def test_freshness_thresholds_can_be_overridden() -> None:
    status = check_mt4_snapshot_freshness(
        _fresh_metadata_snapshot(live_tick_generated_at="2026-07-03T10:15:19Z"),
        NOW_UTC,
        thresholds_seconds={LIVE_TICK_FILE: 15},
    )

    assert status.live_tick.max_age_seconds == 15
    assert status.live_tick.is_stale is False
    assert status.status_code == ALL_FILES_FRESH


def test_freshness_uses_constructed_results_only(tmp_path) -> None:
    status = check_mt4_snapshot_freshness(_fresh_metadata_snapshot(), NOW_UTC)

    assert status.status_code == ALL_FILES_FRESH
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")
