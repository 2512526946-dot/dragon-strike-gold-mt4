from __future__ import annotations

from pathlib import PurePath, PurePosixPath, PureWindowsPath
from typing import Any


MT4_DEMO_READONLY_FILENAME_ALLOWED = "MT4_DEMO_READONLY_FILENAME_ALLOWED"
MT4_DEMO_READONLY_FILENAME_REJECTED = "MT4_DEMO_READONLY_FILENAME_REJECTED"
MT4_DEMO_READONLY_PATH_ALLOWED = "MT4_DEMO_READONLY_PATH_ALLOWED"
MT4_DEMO_READONLY_PATH_REJECTED = "MT4_DEMO_READONLY_PATH_REJECTED"
MT4_DEMO_READONLY_INPUT_INVALID = "MT4_DEMO_READONLY_INPUT_INVALID"

ALLOWED_MT4_DEMO_READONLY_FILENAMES = (
    "account_snapshot.json",
    "positions_order_history.json",
    "market_symbol.json",
)

_ALLOWED_FILENAME_SET = frozenset(ALLOWED_MT4_DEMO_READONLY_FILENAMES)

_SAFETY_FIELDS: dict[str, bool] = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}


def get_allowed_mt4_demo_readonly_filenames() -> tuple[str, ...]:
    return ALLOWED_MT4_DEMO_READONLY_FILENAMES


def is_allowed_mt4_demo_readonly_filename(filename: object) -> bool:
    return validate_mt4_demo_readonly_filename(filename)["passed"] is True


def validate_mt4_demo_readonly_filename(filename: object) -> dict[str, Any]:
    reason_code = _filename_rejection_reason(filename)
    if reason_code is not None:
        return _filename_result(
            passed=False,
            status_code=(
                MT4_DEMO_READONLY_INPUT_INVALID
                if reason_code == "FILENAME_INPUT_NOT_STR"
                else MT4_DEMO_READONLY_FILENAME_REJECTED
            ),
            safe_filename=None,
            reason_code=reason_code,
        )

    return _filename_result(
        passed=True,
        status_code=MT4_DEMO_READONLY_FILENAME_ALLOWED,
        safe_filename=filename,
        reason_code=None,
    )


def build_mt4_demo_readonly_candidate_path(
    base_dir: object,
    filename: object,
) -> dict[str, Any]:
    base_reason_code = _base_dir_rejection_reason(base_dir)
    if base_reason_code is not None:
        return _path_result(
            passed=False,
            status_code=MT4_DEMO_READONLY_INPUT_INVALID,
            safe_filename=None,
            candidate_path=None,
            reason_code=base_reason_code,
        )

    filename_result = validate_mt4_demo_readonly_filename(filename)
    if filename_result["passed"] is not True:
        return _path_result(
            passed=False,
            status_code=(
                MT4_DEMO_READONLY_INPUT_INVALID
                if filename_result["status_code"] == MT4_DEMO_READONLY_INPUT_INVALID
                else MT4_DEMO_READONLY_PATH_REJECTED
            ),
            safe_filename=None,
            candidate_path=None,
            reason_code=str(filename_result["reason_code"]),
        )

    safe_filename = str(filename_result["safe_filename"])
    candidate_path = str(PurePath(str(base_dir)) / safe_filename)

    return _path_result(
        passed=True,
        status_code=MT4_DEMO_READONLY_PATH_ALLOWED,
        safe_filename=safe_filename,
        candidate_path=candidate_path,
        reason_code=None,
    )


def _filename_result(
    *,
    passed: bool,
    status_code: str,
    safe_filename: object,
    reason_code: str | None,
) -> dict[str, Any]:
    return {
        "passed": passed,
        "status_code": status_code,
        "safe_filename": safe_filename,
        "reason_code": reason_code,
        **_SAFETY_FIELDS,
    }


def _path_result(
    *,
    passed: bool,
    status_code: str,
    safe_filename: str | None,
    candidate_path: str | None,
    reason_code: str | None,
) -> dict[str, Any]:
    return {
        "passed": passed,
        "status_code": status_code,
        "safe_filename": safe_filename,
        "candidate_path": candidate_path,
        "reason_code": reason_code,
        **_SAFETY_FIELDS,
    }


def _filename_rejection_reason(filename: object) -> str | None:
    if not isinstance(filename, str):
        return "FILENAME_INPUT_NOT_STR"

    if not filename:
        return "FILENAME_EMPTY"

    if filename != filename.strip():
        return "FILENAME_HAS_SURROUNDING_WHITESPACE"

    if _is_absolute_path_text(filename):
        return "FILENAME_IS_ABSOLUTE_PATH"

    if ".." in filename:
        return "FILENAME_CONTAINS_PATH_TRAVERSAL"

    if "/" in filename or "\\" in filename:
        return "FILENAME_CONTAINS_PATH_SEPARATOR"

    if filename.startswith("."):
        return "FILENAME_IS_HIDDEN"

    if filename.count(".") > 1:
        return "FILENAME_HAS_DOUBLE_EXTENSION"

    if not filename.endswith(".json"):
        return "FILENAME_EXTENSION_NOT_ALLOWED"

    if filename not in _ALLOWED_FILENAME_SET:
        return "FILENAME_NOT_IN_WHITELIST"

    return None


def _base_dir_rejection_reason(base_dir: object) -> str | None:
    if not isinstance(base_dir, str):
        return "BASE_DIR_INPUT_NOT_STR"

    if not base_dir:
        return "BASE_DIR_EMPTY"

    if base_dir != base_dir.strip():
        return "BASE_DIR_HAS_SURROUNDING_WHITESPACE"

    return None


def _is_absolute_path_text(path_text: str) -> bool:
    windows_path = PureWindowsPath(path_text)
    posix_path = PurePosixPath(path_text)
    return (
        windows_path.is_absolute()
        or bool(windows_path.drive)
        or posix_path.is_absolute()
        or path_text.startswith("\\\\")
    )
