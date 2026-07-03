from app.services.mt4_file_reader import (
    FILE_NOT_FOUND,
    INVALID_JSON,
    JSON_NOT_OBJECT,
    NOT_A_FILE,
    read_json_object_file,
)


def test_read_json_object_file_missing_file(tmp_path) -> None:
    result = read_json_object_file(tmp_path / "missing.json")

    assert result.exists is False
    assert result.is_file is False
    assert result.is_json_valid is False
    assert result.is_object is False
    assert result.data is None
    assert result.error_code == FILE_NOT_FOUND
    assert result.error_message is not None


def test_read_json_object_file_path_is_directory(tmp_path) -> None:
    result = read_json_object_file(tmp_path)

    assert result.exists is True
    assert result.is_file is False
    assert result.is_json_valid is False
    assert result.is_object is False
    assert result.data is None
    assert result.error_code == NOT_A_FILE
    assert result.error_message is not None


def test_read_json_object_file_invalid_json(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{not-valid-json", encoding="utf-8")

    result = read_json_object_file(path)

    assert result.exists is True
    assert result.is_file is True
    assert result.is_json_valid is False
    assert result.is_object is False
    assert result.data is None
    assert result.error_code == INVALID_JSON
    assert result.error_message is not None


def test_read_json_object_file_json_array_is_not_object(tmp_path) -> None:
    path = tmp_path / "array.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    result = read_json_object_file(path)

    assert result.exists is True
    assert result.is_file is True
    assert result.is_json_valid is True
    assert result.is_object is False
    assert result.data is None
    assert result.error_code == JSON_NOT_OBJECT
    assert result.error_message is not None


def test_read_json_object_file_valid_object(tmp_path) -> None:
    path = tmp_path / "object.json"
    path.write_text('{"file_type": "live_tick", "source": "test"}', encoding="utf-8")

    result = read_json_object_file(path)

    assert result.exists is True
    assert result.is_file is True
    assert result.is_json_valid is True
    assert result.is_object is True
    assert result.data == {"file_type": "live_tick", "source": "test"}
    assert result.error_code is None
    assert result.error_message is None
