import json

from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
    read_mt4_snapshot_files,
)
from app.services.mt4_snapshot_status import (
    ALL_FILES_READABLE_OBJECTS,
    SOME_FILES_INVALID_JSON,
    SOME_FILES_MISSING,
    SOME_FILES_NOT_OBJECT,
    SOME_PATHS_NOT_FILES,
    Mt4SnapshotReadSummary,
    read_and_summarize_mt4_snapshot_files,
    summarize_mt4_snapshot_read_result,
)


ALL_FILES = (
    LIVE_TICK_FILE,
    LATEST_BARS_FILE,
    SYMBOL_SPEC_FILE,
    ACCOUNT_SNAPSHOT_FILE,
)


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_all_objects(base_dir) -> None:
    for filename in ALL_FILES:
        _write_json(base_dir / filename, {"name": filename})


def test_summary_all_files_readable_objects(tmp_path) -> None:
    _write_all_objects(tmp_path)

    summary = summarize_mt4_snapshot_read_result(read_mt4_snapshot_files(tmp_path))

    assert isinstance(summary, Mt4SnapshotReadSummary)
    assert summary.total_files == 4
    assert summary.present_file_count == 4
    assert summary.readable_object_count == 4
    assert summary.missing_files == []
    assert summary.not_file_paths == []
    assert summary.invalid_json_files == []
    assert summary.not_object_files == []
    assert summary.read_error_files == []
    assert summary.all_files_present is True
    assert summary.all_json_valid is True
    assert summary.all_objects is True
    assert summary.can_proceed_to_metadata_checks is True
    assert summary.status_code == ALL_FILES_READABLE_OBJECTS


def test_summary_all_files_missing(tmp_path) -> None:
    summary = read_and_summarize_mt4_snapshot_files(tmp_path)

    assert summary.total_files == 4
    assert summary.present_file_count == 0
    assert summary.readable_object_count == 0
    assert summary.missing_files == list(ALL_FILES)
    assert summary.all_files_present is False
    assert summary.can_proceed_to_metadata_checks is False
    assert summary.status_code == SOME_FILES_MISSING


def test_summary_partial_missing(tmp_path) -> None:
    _write_json(tmp_path / LIVE_TICK_FILE, {"name": "live"})
    _write_json(tmp_path / SYMBOL_SPEC_FILE, {"name": "spec"})

    summary = read_and_summarize_mt4_snapshot_files(tmp_path)

    assert summary.present_file_count == 2
    assert summary.readable_object_count == 2
    assert summary.missing_files == [LATEST_BARS_FILE, ACCOUNT_SNAPSHOT_FILE]
    assert summary.invalid_json_files == []
    assert summary.can_proceed_to_metadata_checks is False
    assert summary.status_code == SOME_FILES_MISSING


def test_summary_invalid_json_does_not_affect_other_files(tmp_path) -> None:
    _write_json(tmp_path / LIVE_TICK_FILE, {"name": "live"})
    (tmp_path / LATEST_BARS_FILE).write_text("{bad-json", encoding="utf-8")
    _write_json(tmp_path / SYMBOL_SPEC_FILE, {"name": "spec"})
    _write_json(tmp_path / ACCOUNT_SNAPSHOT_FILE, {"name": "account"})

    summary = read_and_summarize_mt4_snapshot_files(tmp_path)

    assert summary.present_file_count == 4
    assert summary.readable_object_count == 3
    assert summary.invalid_json_files == [LATEST_BARS_FILE]
    assert summary.missing_files == []
    assert summary.can_proceed_to_metadata_checks is False
    assert summary.status_code == SOME_FILES_INVALID_JSON


def test_summary_json_valid_but_not_object(tmp_path) -> None:
    _write_all_objects(tmp_path)
    _write_json(tmp_path / SYMBOL_SPEC_FILE, ["not", "object"])

    summary = read_and_summarize_mt4_snapshot_files(tmp_path)

    assert summary.present_file_count == 4
    assert summary.readable_object_count == 3
    assert summary.not_object_files == [SYMBOL_SPEC_FILE]
    assert summary.all_json_valid is True
    assert summary.can_proceed_to_metadata_checks is False
    assert summary.status_code == SOME_FILES_NOT_OBJECT


def test_summary_path_is_directory_not_file(tmp_path) -> None:
    _write_all_objects(tmp_path)
    (tmp_path / ACCOUNT_SNAPSHOT_FILE).unlink()
    (tmp_path / ACCOUNT_SNAPSHOT_FILE).mkdir()

    summary = read_and_summarize_mt4_snapshot_files(tmp_path)

    assert summary.present_file_count == 4
    assert summary.readable_object_count == 3
    assert summary.not_file_paths == [ACCOUNT_SNAPSHOT_FILE]
    assert summary.can_proceed_to_metadata_checks is False
    assert summary.status_code == SOME_PATHS_NOT_FILES


def test_summary_uses_test_directory_only(tmp_path) -> None:
    summary = read_and_summarize_mt4_snapshot_files(tmp_path)

    assert summary.missing_files == list(ALL_FILES)
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")
