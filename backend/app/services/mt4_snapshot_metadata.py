from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.mt4_file_reader import Mt4JsonReadResult
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
    Mt4SnapshotReadResult,
    read_mt4_snapshot_files,
)


MT4_FILE_BRIDGE_SOURCE = "mt4_file_bridge"

LIVE_TICK_FILE_TYPE = "live_tick"
LATEST_BARS_FILE_TYPE = "latest_bars"
SYMBOL_SPEC_FILE_TYPE = "symbol_spec"
ACCOUNT_SNAPSHOT_FILE_TYPE = "account_snapshot"

METADATA_OK = "METADATA_OK"
READ_RESULT_NOT_READY = "READ_RESULT_NOT_READY"
MISSING_SCHEMA_VERSION = "MISSING_SCHEMA_VERSION"
MISSING_FILE_TYPE = "MISSING_FILE_TYPE"
UNEXPECTED_FILE_TYPE = "UNEXPECTED_FILE_TYPE"
MISSING_SOURCE = "MISSING_SOURCE"
UNEXPECTED_SOURCE = "UNEXPECTED_SOURCE"
MISSING_GENERATED_AT = "MISSING_GENERATED_AT"

ALL_METADATA_OK = "ALL_METADATA_OK"
SOME_METADATA_MISSING = "SOME_METADATA_MISSING"
SOME_FILE_TYPES_UNEXPECTED = "SOME_FILE_TYPES_UNEXPECTED"
SOME_SOURCES_UNEXPECTED = "SOME_SOURCES_UNEXPECTED"
SOME_FILES_NOT_READY = "SOME_FILES_NOT_READY"


@dataclass(frozen=True)
class Mt4FileMetadataStatus:
    file_name: str
    expected_file_type: str
    actual_file_type: str | None
    schema_version: str | None
    source: str | None
    generated_at: str | None
    has_schema_version: bool
    has_file_type: bool
    has_source: bool
    has_generated_at: bool
    file_type_matches: bool
    source_matches: bool
    can_proceed_to_freshness_checks: bool
    status_code: str
    error_codes: list[str]


@dataclass(frozen=True)
class Mt4SnapshotMetadataStatus:
    live_tick: Mt4FileMetadataStatus
    latest_bars: Mt4FileMetadataStatus
    symbol_spec: Mt4FileMetadataStatus
    account_snapshot: Mt4FileMetadataStatus
    all_metadata_present: bool
    all_file_types_match: bool
    all_sources_match: bool
    can_proceed_to_freshness_checks: bool
    status_code: str


def check_mt4_file_metadata(
    file_name: str,
    read_result: Mt4JsonReadResult,
    expected_file_type: str,
) -> Mt4FileMetadataStatus:
    if not read_result.is_object or read_result.data is None:
        return Mt4FileMetadataStatus(
            file_name=file_name,
            expected_file_type=expected_file_type,
            actual_file_type=None,
            schema_version=None,
            source=None,
            generated_at=None,
            has_schema_version=False,
            has_file_type=False,
            has_source=False,
            has_generated_at=False,
            file_type_matches=False,
            source_matches=False,
            can_proceed_to_freshness_checks=False,
            status_code=READ_RESULT_NOT_READY,
            error_codes=[READ_RESULT_NOT_READY],
        )

    data = read_result.data
    schema_version = _string_metadata(data, "schema_version")
    actual_file_type = _string_metadata(data, "file_type")
    source = _string_metadata(data, "source")
    generated_at = _string_metadata(data, "generated_at")

    error_codes: list[str] = []

    if schema_version is None:
        error_codes.append(MISSING_SCHEMA_VERSION)
    if actual_file_type is None:
        error_codes.append(MISSING_FILE_TYPE)
    elif actual_file_type != expected_file_type:
        error_codes.append(UNEXPECTED_FILE_TYPE)
    if source is None:
        error_codes.append(MISSING_SOURCE)
    elif source != MT4_FILE_BRIDGE_SOURCE:
        error_codes.append(UNEXPECTED_SOURCE)
    if generated_at is None:
        error_codes.append(MISSING_GENERATED_AT)

    return Mt4FileMetadataStatus(
        file_name=file_name,
        expected_file_type=expected_file_type,
        actual_file_type=actual_file_type,
        schema_version=schema_version,
        source=source,
        generated_at=generated_at,
        has_schema_version=schema_version is not None,
        has_file_type=actual_file_type is not None,
        has_source=source is not None,
        has_generated_at=generated_at is not None,
        file_type_matches=actual_file_type == expected_file_type,
        source_matches=source == MT4_FILE_BRIDGE_SOURCE,
        can_proceed_to_freshness_checks=len(error_codes) == 0,
        status_code=_file_status_code(error_codes),
        error_codes=error_codes,
    )


def check_mt4_snapshot_metadata(
    snapshot: Mt4SnapshotReadResult,
) -> Mt4SnapshotMetadataStatus:
    live_tick = check_mt4_file_metadata(
        LIVE_TICK_FILE,
        snapshot.live_tick,
        LIVE_TICK_FILE_TYPE,
    )
    latest_bars = check_mt4_file_metadata(
        LATEST_BARS_FILE,
        snapshot.latest_bars,
        LATEST_BARS_FILE_TYPE,
    )
    symbol_spec = check_mt4_file_metadata(
        SYMBOL_SPEC_FILE,
        snapshot.symbol_spec,
        SYMBOL_SPEC_FILE_TYPE,
    )
    account_snapshot = check_mt4_file_metadata(
        ACCOUNT_SNAPSHOT_FILE,
        snapshot.account_snapshot,
        ACCOUNT_SNAPSHOT_FILE_TYPE,
    )

    file_statuses = (live_tick, latest_bars, symbol_spec, account_snapshot)

    return Mt4SnapshotMetadataStatus(
        live_tick=live_tick,
        latest_bars=latest_bars,
        symbol_spec=symbol_spec,
        account_snapshot=account_snapshot,
        all_metadata_present=all(_has_all_metadata(status) for status in file_statuses),
        all_file_types_match=all(status.file_type_matches for status in file_statuses),
        all_sources_match=all(status.source_matches for status in file_statuses),
        can_proceed_to_freshness_checks=all(
            status.can_proceed_to_freshness_checks for status in file_statuses
        ),
        status_code=_snapshot_status_code(file_statuses),
    )


def read_and_check_mt4_snapshot_metadata(
    base_dir: Path | str,
) -> Mt4SnapshotMetadataStatus:
    return check_mt4_snapshot_metadata(read_mt4_snapshot_files(base_dir))


def _string_metadata(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _file_status_code(error_codes: list[str]) -> str:
    if not error_codes:
        return METADATA_OK
    return error_codes[0]


def _has_all_metadata(status: Mt4FileMetadataStatus) -> bool:
    return (
        status.has_schema_version
        and status.has_file_type
        and status.has_source
        and status.has_generated_at
    )


def _snapshot_status_code(
    file_statuses: tuple[Mt4FileMetadataStatus, ...],
) -> str:
    all_errors = [error for status in file_statuses for error in status.error_codes]

    if READ_RESULT_NOT_READY in all_errors:
        return SOME_FILES_NOT_READY
    if UNEXPECTED_FILE_TYPE in all_errors:
        return SOME_FILE_TYPES_UNEXPECTED
    if UNEXPECTED_SOURCE in all_errors:
        return SOME_SOURCES_UNEXPECTED
    if all_errors:
        return SOME_METADATA_MISSING
    return ALL_METADATA_OK
