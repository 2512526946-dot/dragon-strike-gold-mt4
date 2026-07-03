from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.mt4_file_reader import (
    FILE_NOT_FOUND,
    INVALID_JSON,
    JSON_NOT_OBJECT,
    NOT_A_FILE,
    READ_ERROR,
    Mt4JsonReadResult,
)
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
    Mt4SnapshotReadResult,
    read_mt4_snapshot_files,
)


ALL_FILES_READABLE_OBJECTS = "ALL_FILES_READABLE_OBJECTS"
SOME_FILES_MISSING = "SOME_FILES_MISSING"
SOME_FILES_INVALID_JSON = "SOME_FILES_INVALID_JSON"
SOME_FILES_NOT_OBJECT = "SOME_FILES_NOT_OBJECT"
SOME_PATHS_NOT_FILES = "SOME_PATHS_NOT_FILES"
SOME_FILES_READ_ERROR = "SOME_FILES_READ_ERROR"


@dataclass(frozen=True)
class Mt4SnapshotReadSummary:
    total_files: int
    present_file_count: int
    readable_object_count: int
    missing_files: list[str]
    not_file_paths: list[str]
    invalid_json_files: list[str]
    not_object_files: list[str]
    read_error_files: list[str]
    all_files_present: bool
    all_json_valid: bool
    all_objects: bool
    can_proceed_to_metadata_checks: bool
    status_code: str


def summarize_mt4_snapshot_read_result(
    snapshot: Mt4SnapshotReadResult,
) -> Mt4SnapshotReadSummary:
    named_results = _named_results(snapshot)
    total_files = len(named_results)

    missing_files = _files_with_error(named_results, FILE_NOT_FOUND)
    not_file_paths = _files_with_error(named_results, NOT_A_FILE)
    invalid_json_files = _files_with_error(named_results, INVALID_JSON)
    not_object_files = _files_with_error(named_results, JSON_NOT_OBJECT)
    read_error_files = _files_with_error(named_results, READ_ERROR)

    all_files_present = len(missing_files) == 0
    all_json_valid = all(result.is_json_valid for _, result in named_results)
    all_objects = all(result.is_object for _, result in named_results)
    can_proceed_to_metadata_checks = (
        all_files_present
        and all_json_valid
        and all_objects
        and not not_file_paths
        and not read_error_files
    )

    return Mt4SnapshotReadSummary(
        total_files=total_files,
        present_file_count=sum(1 for _, result in named_results if result.exists),
        readable_object_count=sum(1 for _, result in named_results if result.is_object),
        missing_files=missing_files,
        not_file_paths=not_file_paths,
        invalid_json_files=invalid_json_files,
        not_object_files=not_object_files,
        read_error_files=read_error_files,
        all_files_present=all_files_present,
        all_json_valid=all_json_valid,
        all_objects=all_objects,
        can_proceed_to_metadata_checks=can_proceed_to_metadata_checks,
        status_code=_status_code(
            missing_files=missing_files,
            not_file_paths=not_file_paths,
            invalid_json_files=invalid_json_files,
            not_object_files=not_object_files,
            read_error_files=read_error_files,
        ),
    )


def read_and_summarize_mt4_snapshot_files(base_dir: Path | str) -> Mt4SnapshotReadSummary:
    return summarize_mt4_snapshot_read_result(read_mt4_snapshot_files(base_dir))


def _named_results(
    snapshot: Mt4SnapshotReadResult,
) -> tuple[tuple[str, Mt4JsonReadResult], ...]:
    return (
        (LIVE_TICK_FILE, snapshot.live_tick),
        (LATEST_BARS_FILE, snapshot.latest_bars),
        (SYMBOL_SPEC_FILE, snapshot.symbol_spec),
        (ACCOUNT_SNAPSHOT_FILE, snapshot.account_snapshot),
    )


def _files_with_error(
    named_results: tuple[tuple[str, Mt4JsonReadResult], ...],
    error_code: str,
) -> list[str]:
    return [
        filename for filename, result in named_results if result.error_code == error_code
    ]


def _status_code(
    *,
    missing_files: list[str],
    not_file_paths: list[str],
    invalid_json_files: list[str],
    not_object_files: list[str],
    read_error_files: list[str],
) -> str:
    if missing_files:
        return SOME_FILES_MISSING
    if not_file_paths:
        return SOME_PATHS_NOT_FILES
    if invalid_json_files:
        return SOME_FILES_INVALID_JSON
    if not_object_files:
        return SOME_FILES_NOT_OBJECT
    if read_error_files:
        return SOME_FILES_READ_ERROR
    return ALL_FILES_READABLE_OBJECTS
