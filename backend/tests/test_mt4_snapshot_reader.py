import json

from app.services.mt4_file_reader import FILE_NOT_FOUND, INVALID_JSON
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
    Mt4SnapshotReadResult,
    read_mt4_snapshot_files,
)


ALL_FILES = (
    LIVE_TICK_FILE,
    LATEST_BARS_FILE,
    SYMBOL_SPEC_FILE,
    ACCOUNT_SNAPSHOT_FILE,
)


def _write_json(path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_read_mt4_snapshot_files_all_objects_exist(tmp_path) -> None:
    payloads = {
        LIVE_TICK_FILE: {"name": "live"},
        LATEST_BARS_FILE: {"name": "bars"},
        SYMBOL_SPEC_FILE: {"name": "spec"},
        ACCOUNT_SNAPSHOT_FILE: {"name": "account"},
    }
    for filename, payload in payloads.items():
        _write_json(tmp_path / filename, payload)

    result = read_mt4_snapshot_files(tmp_path)

    assert isinstance(result, Mt4SnapshotReadResult)
    assert result.live_tick.is_json_valid is True
    assert result.latest_bars.is_json_valid is True
    assert result.symbol_spec.is_json_valid is True
    assert result.account_snapshot.is_json_valid is True
    assert result.live_tick.is_object is True
    assert result.latest_bars.is_object is True
    assert result.symbol_spec.is_object is True
    assert result.account_snapshot.is_object is True
    assert result.live_tick.data == payloads[LIVE_TICK_FILE]
    assert result.latest_bars.data == payloads[LATEST_BARS_FILE]
    assert result.symbol_spec.data == payloads[SYMBOL_SPEC_FILE]
    assert result.account_snapshot.data == payloads[ACCOUNT_SNAPSHOT_FILE]


def test_read_mt4_snapshot_files_all_missing(tmp_path) -> None:
    result = read_mt4_snapshot_files(tmp_path)

    assert result.live_tick.error_code == FILE_NOT_FOUND
    assert result.latest_bars.error_code == FILE_NOT_FOUND
    assert result.symbol_spec.error_code == FILE_NOT_FOUND
    assert result.account_snapshot.error_code == FILE_NOT_FOUND


def test_read_mt4_snapshot_files_partial_missing(tmp_path) -> None:
    _write_json(tmp_path / LIVE_TICK_FILE, {"name": "live"})
    _write_json(tmp_path / SYMBOL_SPEC_FILE, {"name": "spec"})

    result = read_mt4_snapshot_files(tmp_path)

    assert result.live_tick.is_object is True
    assert result.live_tick.data == {"name": "live"}
    assert result.latest_bars.error_code == FILE_NOT_FOUND
    assert result.symbol_spec.is_object is True
    assert result.symbol_spec.data == {"name": "spec"}
    assert result.account_snapshot.error_code == FILE_NOT_FOUND


def test_read_mt4_snapshot_files_invalid_json_does_not_affect_others(tmp_path) -> None:
    _write_json(tmp_path / LIVE_TICK_FILE, {"name": "live"})
    (tmp_path / LATEST_BARS_FILE).write_text("{bad-json", encoding="utf-8")
    _write_json(tmp_path / SYMBOL_SPEC_FILE, {"name": "spec"})
    _write_json(tmp_path / ACCOUNT_SNAPSHOT_FILE, {"name": "account"})

    result = read_mt4_snapshot_files(tmp_path)

    assert result.live_tick.is_object is True
    assert result.latest_bars.error_code == INVALID_JSON
    assert result.symbol_spec.is_object is True
    assert result.account_snapshot.is_object is True


def test_mt4_snapshot_reader_uses_test_directory_only(tmp_path) -> None:
    result = read_mt4_snapshot_files(tmp_path)
    messages = " ".join(
        read_result.error_message or ""
        for read_result in (
            result.live_tick,
            result.latest_bars,
            result.symbol_spec,
            result.account_snapshot,
        )
    )

    assert str(tmp_path) in messages
    assert "data/mt4" not in messages.replace("\\", "/")
    for filename in ALL_FILES:
        assert filename in messages
