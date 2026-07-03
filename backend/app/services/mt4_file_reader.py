from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any


FILE_NOT_FOUND = "FILE_NOT_FOUND"
NOT_A_FILE = "NOT_A_FILE"
INVALID_JSON = "INVALID_JSON"
JSON_NOT_OBJECT = "JSON_NOT_OBJECT"
READ_ERROR = "READ_ERROR"


@dataclass(frozen=True)
class Mt4JsonReadResult:
    exists: bool
    is_file: bool
    is_json_valid: bool
    is_object: bool
    data: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None


def read_json_object_file(path: Path | str) -> Mt4JsonReadResult:
    file_path = Path(path)

    try:
        exists = file_path.exists()
    except OSError as exc:
        return Mt4JsonReadResult(
            exists=False,
            is_file=False,
            is_json_valid=False,
            is_object=False,
            error_code=READ_ERROR,
            error_message=str(exc),
        )

    if not exists:
        return Mt4JsonReadResult(
            exists=False,
            is_file=False,
            is_json_valid=False,
            is_object=False,
            error_code=FILE_NOT_FOUND,
            error_message=f"File does not exist: {file_path}",
        )

    try:
        is_file = file_path.is_file()
    except OSError as exc:
        return Mt4JsonReadResult(
            exists=True,
            is_file=False,
            is_json_valid=False,
            is_object=False,
            error_code=READ_ERROR,
            error_message=str(exc),
        )

    if not is_file:
        return Mt4JsonReadResult(
            exists=True,
            is_file=False,
            is_json_valid=False,
            is_object=False,
            error_code=NOT_A_FILE,
            error_message=f"Path is not a file: {file_path}",
        )

    try:
        parsed = json.loads(file_path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        return Mt4JsonReadResult(
            exists=True,
            is_file=True,
            is_json_valid=False,
            is_object=False,
            error_code=INVALID_JSON,
            error_message=str(exc),
        )
    except (OSError, UnicodeDecodeError) as exc:
        return Mt4JsonReadResult(
            exists=True,
            is_file=True,
            is_json_valid=False,
            is_object=False,
            error_code=READ_ERROR,
            error_message=str(exc),
        )

    if not isinstance(parsed, dict):
        return Mt4JsonReadResult(
            exists=True,
            is_file=True,
            is_json_valid=True,
            is_object=False,
            error_code=JSON_NOT_OBJECT,
            error_message="JSON payload is not an object.",
        )

    return Mt4JsonReadResult(
        exists=True,
        is_file=True,
        is_json_valid=True,
        is_object=True,
        data=parsed,
    )
