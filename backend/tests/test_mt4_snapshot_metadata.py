import json

from app.services.mt4_snapshot_metadata import (
    ACCOUNT_SNAPSHOT_FILE_TYPE,
    ALL_METADATA_OK,
    LATEST_BARS_FILE_TYPE,
    LIVE_TICK_FILE_TYPE,
    METADATA_OK,
    MISSING_FILE_TYPE,
    MISSING_GENERATED_AT,
    MISSING_SCHEMA_VERSION,
    MISSING_SOURCE,
    MT4_FILE_BRIDGE_SOURCE,
    READ_RESULT_NOT_READY,
    SOME_FILES_NOT_READY,
    SOME_FILE_TYPES_UNEXPECTED,
    SOME_METADATA_MISSING,
    SOME_SOURCES_UNEXPECTED,
    SYMBOL_SPEC_FILE_TYPE,
    UNEXPECTED_FILE_TYPE,
    UNEXPECTED_SOURCE,
    Mt4FileMetadataStatus,
    Mt4SnapshotMetadataStatus,
    read_and_check_mt4_snapshot_metadata,
)
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
)


EXPECTED_TYPES = {
    LIVE_TICK_FILE: LIVE_TICK_FILE_TYPE,
    LATEST_BARS_FILE: LATEST_BARS_FILE_TYPE,
    SYMBOL_SPEC_FILE: SYMBOL_SPEC_FILE_TYPE,
    ACCOUNT_SNAPSHOT_FILE: ACCOUNT_SNAPSHOT_FILE_TYPE,
}


def _metadata_payload(file_type: str) -> dict[str, str]:
    return {
        "schema_version": "1.0",
        "file_type": file_type,
        "source": MT4_FILE_BRIDGE_SOURCE,
        "generated_at": "not-a-parsed-time-but-present",
    }


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_all_metadata(base_dir) -> None:
    for filename, file_type in EXPECTED_TYPES.items():
        _write_json(base_dir / filename, _metadata_payload(file_type))


def test_metadata_all_files_ok(tmp_path) -> None:
    _write_all_metadata(tmp_path)

    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert isinstance(status, Mt4SnapshotMetadataStatus)
    assert isinstance(status.live_tick, Mt4FileMetadataStatus)
    assert status.all_metadata_present is True
    assert status.all_file_types_match is True
    assert status.all_sources_match is True
    assert status.can_proceed_to_freshness_checks is True
    assert status.status_code == ALL_METADATA_OK
    assert status.live_tick.status_code == METADATA_OK
    assert status.live_tick.error_codes == []


def test_metadata_missing_file_type(tmp_path) -> None:
    _write_all_metadata(tmp_path)
    payload = _metadata_payload(LIVE_TICK_FILE_TYPE)
    payload.pop("file_type")
    _write_json(tmp_path / LIVE_TICK_FILE, payload)

    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert status.live_tick.has_file_type is False
    assert status.live_tick.file_type_matches is False
    assert MISSING_FILE_TYPE in status.live_tick.error_codes
    assert status.live_tick.status_code == MISSING_FILE_TYPE
    assert status.can_proceed_to_freshness_checks is False
    assert status.status_code == SOME_METADATA_MISSING


def test_metadata_unexpected_file_type(tmp_path) -> None:
    _write_all_metadata(tmp_path)
    payload = _metadata_payload("wrong_type")
    _write_json(tmp_path / LATEST_BARS_FILE, payload)

    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert status.latest_bars.actual_file_type == "wrong_type"
    assert status.latest_bars.file_type_matches is False
    assert UNEXPECTED_FILE_TYPE in status.latest_bars.error_codes
    assert status.latest_bars.status_code == UNEXPECTED_FILE_TYPE
    assert status.can_proceed_to_freshness_checks is False
    assert status.status_code == SOME_FILE_TYPES_UNEXPECTED


def test_metadata_missing_schema_version(tmp_path) -> None:
    _write_all_metadata(tmp_path)
    payload = _metadata_payload(SYMBOL_SPEC_FILE_TYPE)
    payload.pop("schema_version")
    _write_json(tmp_path / SYMBOL_SPEC_FILE, payload)

    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert status.symbol_spec.has_schema_version is False
    assert MISSING_SCHEMA_VERSION in status.symbol_spec.error_codes
    assert status.symbol_spec.status_code == MISSING_SCHEMA_VERSION
    assert status.all_metadata_present is False
    assert status.can_proceed_to_freshness_checks is False
    assert status.status_code == SOME_METADATA_MISSING


def test_metadata_missing_source(tmp_path) -> None:
    _write_all_metadata(tmp_path)
    payload = _metadata_payload(ACCOUNT_SNAPSHOT_FILE_TYPE)
    payload.pop("source")
    _write_json(tmp_path / ACCOUNT_SNAPSHOT_FILE, payload)

    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert status.account_snapshot.has_source is False
    assert status.account_snapshot.source_matches is False
    assert MISSING_SOURCE in status.account_snapshot.error_codes
    assert status.account_snapshot.status_code == MISSING_SOURCE
    assert status.can_proceed_to_freshness_checks is False
    assert status.status_code == SOME_METADATA_MISSING


def test_metadata_unexpected_source(tmp_path) -> None:
    _write_all_metadata(tmp_path)
    payload = _metadata_payload(LIVE_TICK_FILE_TYPE)
    payload["source"] = "manual_file"
    _write_json(tmp_path / LIVE_TICK_FILE, payload)

    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert status.live_tick.source == "manual_file"
    assert status.live_tick.source_matches is False
    assert UNEXPECTED_SOURCE in status.live_tick.error_codes
    assert status.live_tick.status_code == UNEXPECTED_SOURCE
    assert status.can_proceed_to_freshness_checks is False
    assert status.status_code == SOME_SOURCES_UNEXPECTED


def test_metadata_missing_generated_at(tmp_path) -> None:
    _write_all_metadata(tmp_path)
    payload = _metadata_payload(LATEST_BARS_FILE_TYPE)
    payload.pop("generated_at")
    _write_json(tmp_path / LATEST_BARS_FILE, payload)

    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert status.latest_bars.has_generated_at is False
    assert MISSING_GENERATED_AT in status.latest_bars.error_codes
    assert status.latest_bars.status_code == MISSING_GENERATED_AT
    assert status.can_proceed_to_freshness_checks is False
    assert status.status_code == SOME_METADATA_MISSING


def test_metadata_read_result_not_ready(tmp_path) -> None:
    _write_all_metadata(tmp_path)
    (tmp_path / SYMBOL_SPEC_FILE).write_text("{bad-json", encoding="utf-8")

    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert status.symbol_spec.status_code == READ_RESULT_NOT_READY
    assert status.symbol_spec.error_codes == [READ_RESULT_NOT_READY]
    assert status.symbol_spec.can_proceed_to_freshness_checks is False
    assert status.can_proceed_to_freshness_checks is False
    assert status.status_code == SOME_FILES_NOT_READY
    assert status.live_tick.status_code == METADATA_OK


def test_metadata_generated_at_is_presence_only(tmp_path) -> None:
    _write_all_metadata(tmp_path)
    payload = _metadata_payload(ACCOUNT_SNAPSHOT_FILE_TYPE)
    payload["generated_at"] = "definitely-not-a-timestamp"
    _write_json(tmp_path / ACCOUNT_SNAPSHOT_FILE, payload)

    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert status.account_snapshot.generated_at == "definitely-not-a-timestamp"
    assert status.account_snapshot.has_generated_at is True
    assert MISSING_GENERATED_AT not in status.account_snapshot.error_codes
    assert status.status_code == ALL_METADATA_OK
    assert status.can_proceed_to_freshness_checks is True


def test_metadata_uses_test_directory_only(tmp_path) -> None:
    status = read_and_check_mt4_snapshot_metadata(tmp_path)

    assert status.status_code == SOME_FILES_NOT_READY
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")
