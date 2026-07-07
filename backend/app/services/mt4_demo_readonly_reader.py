from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services import mt4_demo_readonly_path_guard as path_guard
from app.services import mt4_demo_readonly_source_summary_adapter as source_summary_adapter
from app.services.mt4_demo_readonly_schema_validator import (
    ACCOUNT_SNAPSHOT_FILE,
    MARKET_SYMBOL_FILE,
    POSITIONS_ORDER_HISTORY_FILE,
)


MT4_DEMO_READONLY_READER_READY = "MT4_DEMO_READONLY_READER_READY"
MT4_DEMO_READONLY_READER_BLOCKED = "MT4_DEMO_READONLY_READER_BLOCKED"
MT4_DEMO_READONLY_READER_INPUT_INVALID = "MT4_DEMO_READONLY_READER_INPUT_INVALID"
MT4_DEMO_READONLY_READER_BASE_DIR_REJECTED = (
    "MT4_DEMO_READONLY_READER_BASE_DIR_REJECTED"
)
MT4_DEMO_READONLY_READER_FILE_MISSING = "MT4_DEMO_READONLY_READER_FILE_MISSING"
MT4_DEMO_READONLY_READER_FILE_UNREADABLE = "MT4_DEMO_READONLY_READER_FILE_UNREADABLE"
MT4_DEMO_READONLY_READER_JSON_INVALID = "MT4_DEMO_READONLY_READER_JSON_INVALID"
MT4_DEMO_READONLY_READER_JSON_NOT_OBJECT = "MT4_DEMO_READONLY_READER_JSON_NOT_OBJECT"
MT4_DEMO_READONLY_READER_SOURCE_SUMMARY_BLOCKED = (
    "MT4_DEMO_READONLY_READER_SOURCE_SUMMARY_BLOCKED"
)
MT4_DEMO_READONLY_READER_SAFETY_BLOCKED = "MT4_DEMO_READONLY_READER_SAFETY_BLOCKED"

_REQUIRED_FILENAMES = (
    ACCOUNT_SNAPSHOT_FILE,
    POSITIONS_ORDER_HISTORY_FILE,
    MARKET_SYMBOL_FILE,
)

_FILENAME_TO_COMPONENT = {
    ACCOUNT_SNAPSHOT_FILE: "account_snapshot",
    POSITIONS_ORDER_HISTORY_FILE: "positions_order_history",
    MARKET_SYMBOL_FILE: "market_symbol",
}

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

_REJECTED_BASE_DIR_PARTS = frozenset(
    {
        ".env",
        "cache",
        "data",
        "database",
        "databases",
        "db",
        "desktop",
        "documents",
        "downloads",
        "log",
        "logs",
        "payload",
        "request_body",
        "api_request_body",
    }
)

_FORBIDDEN_RESULT_KEYS = frozenset(
    {
        "account_number",
        "allow_trade",
        "api_key",
        "buy",
        "buy_now",
        "candidate_path",
        "can_trade",
        "close",
        "close_position",
        "credential",
        "ea_command",
        "execute_trade",
        "final_lot",
        "login",
        "open",
        "open_position",
        "order_close",
        "order_delete",
        "order_id",
        "order_modify",
        "order_send",
        "password",
        "payload",
        "raw_account_snapshot",
        "raw_market_symbol",
        "raw_payload",
        "raw_positions_order_history",
        "secret",
        "sell",
        "sell_now",
        "should_buy",
        "should_sell",
        "stack_trace",
        "suggested_lot",
        "system_path",
        "ticket",
        "token",
        "traceback",
        "trade_plan",
        "trade_signal",
        "trading_action",
    }
)


def get_mt4_demo_readonly_reader_required_filenames() -> tuple[str, ...]:
    return _REQUIRED_FILENAMES


def read_mt4_demo_readonly_source_summary_from_dir(base_dir: object) -> dict[str, Any]:
    base_dir_reason = _base_dir_rejection_reason(base_dir)
    if base_dir_reason is not None:
        return _blocked_result(
            status_code=(
                MT4_DEMO_READONLY_READER_INPUT_INVALID
                if base_dir_reason in {"BASE_DIR_INPUT_NOT_STR", "BASE_DIR_EMPTY"}
                else MT4_DEMO_READONLY_READER_BASE_DIR_REJECTED
            ),
            reader_block_reasons=[base_dir_reason],
        )

    payloads_by_filename: dict[str, dict[str, Any]] = {}
    for filename in _REQUIRED_FILENAMES:
        path_result = path_guard.build_mt4_demo_readonly_candidate_path(
            base_dir,
            filename,
        )
        if path_result["passed"] is not True:
            return _blocked_result(
                status_code=MT4_DEMO_READONLY_READER_BASE_DIR_REJECTED,
                reader_block_reasons=["PATH_GUARD_REJECTED"],
            )

        candidate_path = path_result.get("candidate_path")
        if not isinstance(candidate_path, str):
            return _blocked_result(
                status_code=MT4_DEMO_READONLY_READER_SAFETY_BLOCKED,
                reader_block_reasons=["PATH_GUARD_OUTPUT_SANITIZED"],
            )

        loaded_payload = _read_json_object(Path(candidate_path), filename)
        if loaded_payload["passed"] is not True:
            return _blocked_result(
                status_code=str(loaded_payload["status_code"]),
                reader_block_reasons=list(loaded_payload["reader_block_reasons"]),
                component_statuses=[
                    _reader_component_status(
                        filename=filename,
                        passed=False,
                        status_code=str(loaded_payload["status_code"]),
                        block_reasons=list(loaded_payload["reader_block_reasons"]),
                    )
                ],
                missing_components=(
                    [filename]
                    if loaded_payload["status_code"]
                    == MT4_DEMO_READONLY_READER_FILE_MISSING
                    else []
                ),
            )

        payloads_by_filename[filename] = loaded_payload["data"]

    try:
        summary = source_summary_adapter.build_mt4_demo_readonly_source_summary(
            payloads_by_filename,
        )
    except Exception:
        return _blocked_result(
            status_code=MT4_DEMO_READONLY_READER_SAFETY_BLOCKED,
            reader_block_reasons=["SOURCE_SUMMARY_ADAPTER_EXCEPTION_SANITIZED"],
        )

    if not isinstance(summary, dict) or _contains_forbidden_result_key(summary):
        return _blocked_result(
            status_code=MT4_DEMO_READONLY_READER_SAFETY_BLOCKED,
            reader_block_reasons=["SOURCE_SUMMARY_OUTPUT_SANITIZED"],
        )

    if _has_unsafe_safety_flags(summary):
        return _blocked_result(
            status_code=MT4_DEMO_READONLY_READER_SAFETY_BLOCKED,
            reader_block_reasons=["SOURCE_SUMMARY_SAFETY_FIELD_VIOLATION"],
        )

    if summary.get("passed") is not True:
        blocked_summary = dict(summary)
        adapter_block_reasons = summary.get("block_reasons", [])
        if not isinstance(adapter_block_reasons, list):
            adapter_block_reasons = []
        blocked_summary["status_code"] = MT4_DEMO_READONLY_READER_SOURCE_SUMMARY_BLOCKED
        blocked_summary["reader_status"] = "blocked"
        blocked_summary["reader_block_reasons"] = [
            "SOURCE_SUMMARY_BLOCKED",
            *adapter_block_reasons,
        ]
        blocked_summary["reader_warning_reasons"] = []
        blocked_summary.update(_SAFETY_FIELDS)
        return blocked_summary

    ready_summary = dict(summary)
    ready_summary["status_code"] = MT4_DEMO_READONLY_READER_READY
    ready_summary["reader_status"] = "ready"
    ready_summary["reader_block_reasons"] = []
    ready_summary["reader_warning_reasons"] = []
    ready_summary.update(_SAFETY_FIELDS)
    return ready_summary


def _read_json_object(path: Path, filename: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file_handle:
            payload = json.load(file_handle)
    except FileNotFoundError:
        return _read_failed_result(
            status_code=MT4_DEMO_READONLY_READER_FILE_MISSING,
            reason_code=f"FILE_MISSING:{filename}",
        )
    except json.JSONDecodeError:
        return _read_failed_result(
            status_code=MT4_DEMO_READONLY_READER_JSON_INVALID,
            reason_code=f"JSON_INVALID:{filename}",
        )
    except OSError:
        return _read_failed_result(
            status_code=MT4_DEMO_READONLY_READER_FILE_UNREADABLE,
            reason_code=f"FILE_UNREADABLE:{filename}",
        )
    except Exception:
        return _read_failed_result(
            status_code=MT4_DEMO_READONLY_READER_SAFETY_BLOCKED,
            reason_code="READER_EXCEPTION_SANITIZED",
        )

    if not isinstance(payload, dict):
        return _read_failed_result(
            status_code=MT4_DEMO_READONLY_READER_JSON_NOT_OBJECT,
            reason_code=f"JSON_NOT_OBJECT:{filename}",
        )

    return {
        "passed": True,
        "status_code": MT4_DEMO_READONLY_READER_READY,
        "reader_block_reasons": [],
        "data": payload,
    }


def _read_failed_result(*, status_code: str, reason_code: str) -> dict[str, Any]:
    return {
        "passed": False,
        "status_code": status_code,
        "reader_block_reasons": [reason_code],
        "data": None,
    }


def _blocked_result(
    *,
    status_code: str,
    reader_block_reasons: list[str],
    component_statuses: list[dict[str, Any]] | None = None,
    missing_components: list[str] | None = None,
) -> dict[str, Any]:
    safe_reasons = list(dict.fromkeys(reader_block_reasons))
    return {
        "passed": False,
        "status_code": status_code,
        "source_mode": source_summary_adapter.SOURCE_MODE,
        "source_scope": "mt4_demo_readonly_reader_safe_summary_only",
        "reader_status": "blocked",
        "reader_block_reasons": safe_reasons,
        "reader_warning_reasons": [],
        "component_statuses": component_statuses or [],
        "validation_statuses": [],
        "missing_components": missing_components or [],
        "unexpected_components": [],
        "block_reasons": safe_reasons,
        "warning_reasons": [],
        "data_quality_notes": ["reader blocked without exposing raw payload or paths"],
        "next_allowed_stage": "fix_demo_readonly_reader_inputs_before_summary",
        "next_blocked_stage": "execution_and_trading_remain_blocked",
        **_SAFETY_FIELDS,
    }


def _reader_component_status(
    *,
    filename: str,
    passed: bool,
    status_code: str,
    block_reasons: list[str],
) -> dict[str, Any]:
    component_name = _FILENAME_TO_COMPONENT[filename]
    return {
        "component_name": component_name,
        "filename": filename,
        "passed": passed,
        "status_code": status_code,
        "safe_summary": (
            f"{component_name} file read passed."
            if passed
            else f"{component_name} file read blocked."
        ),
        "block_reasons": list(dict.fromkeys(block_reasons)),
        "warning_reasons": [],
        "data_quality_notes": ["reader file access stayed within filename whitelist"],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }


def _base_dir_rejection_reason(base_dir: object) -> str | None:
    if not isinstance(base_dir, str):
        return "BASE_DIR_INPUT_NOT_STR"

    if not base_dir or not base_dir.strip():
        return "BASE_DIR_EMPTY"

    if base_dir != base_dir.strip():
        return "BASE_DIR_HAS_SURROUNDING_WHITESPACE"

    if "\x00" in base_dir:
        return "BASE_DIR_CONTAINS_NUL"

    normalized = base_dir.replace("\\", "/")
    lower_normalized = normalized.lower()
    parts = [part.lower() for part in normalized.split("/") if part]

    if ".." in parts or "../" in normalized or "..\\" in base_dir:
        return "BASE_DIR_CONTAINS_PATH_TRAVERSAL"

    if lower_normalized.endswith(".json"):
        return "BASE_DIR_LOOKS_LIKE_FILENAME"

    if ".env" in parts or ".env" in lower_normalized:
        return "BASE_DIR_POINTS_TO_ENV"

    for part in parts:
        if part in _REJECTED_BASE_DIR_PARTS:
            return "BASE_DIR_POINTS_TO_REJECTED_LOCATION"

    return None


def _contains_forbidden_result_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, child_value in value.items():
            if isinstance(key, str) and key in _FORBIDDEN_RESULT_KEYS:
                return True
            if _contains_forbidden_result_key(child_value):
                return True
        return False

    if isinstance(value, list):
        return any(_contains_forbidden_result_key(item) for item in value)

    if isinstance(value, str):
        return _looks_like_path_or_trace(value)

    return False


def _looks_like_path_or_trace(value: str) -> bool:
    lower_value = value.lower()
    return (
        "traceback" in lower_value
        or "stack trace" in lower_value
        or "c:\\users\\" in lower_value
        or "\\appdata\\" in lower_value
        or lower_value.startswith("/home/")
        or ".py" in lower_value
    )


def _has_unsafe_safety_flags(value: dict[str, Any]) -> bool:
    for field_name, expected_value in _SAFETY_FIELDS.items():
        if field_name in value and value[field_name] is not expected_value:
            return True
    return False
