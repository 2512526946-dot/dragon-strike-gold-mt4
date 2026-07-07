from __future__ import annotations

from typing import Any

from app.services import mt4_demo_readonly_path_guard as path_guard
from app.services import mt4_demo_readonly_schema_validator as schema_validator


MT4_DEMO_READONLY_SOURCE_SUMMARY_READY = "MT4_DEMO_READONLY_SOURCE_SUMMARY_READY"
MT4_DEMO_READONLY_SOURCE_SUMMARY_BLOCKED = "MT4_DEMO_READONLY_SOURCE_SUMMARY_BLOCKED"
MT4_DEMO_READONLY_SOURCE_SUMMARY_INPUT_INVALID = (
    "MT4_DEMO_READONLY_SOURCE_SUMMARY_INPUT_INVALID"
)
MT4_DEMO_READONLY_SOURCE_SUMMARY_MISSING_COMPONENTS = (
    "MT4_DEMO_READONLY_SOURCE_SUMMARY_MISSING_COMPONENTS"
)
MT4_DEMO_READONLY_SOURCE_SUMMARY_UNEXPECTED_COMPONENTS = (
    "MT4_DEMO_READONLY_SOURCE_SUMMARY_UNEXPECTED_COMPONENTS"
)
MT4_DEMO_READONLY_SOURCE_SUMMARY_VALIDATION_FAILED = (
    "MT4_DEMO_READONLY_SOURCE_SUMMARY_VALIDATION_FAILED"
)
MT4_DEMO_READONLY_SOURCE_SUMMARY_SAFETY_BLOCKED = (
    "MT4_DEMO_READONLY_SOURCE_SUMMARY_SAFETY_BLOCKED"
)

SUMMARY_VERSION = "1.0"
SOURCE_MODE = schema_validator.ALLOWED_SOURCE_MODE
SOURCE_SCOPE = "mt4_demo_readonly_validated_payloads_only"

ACCOUNT_SNAPSHOT_COMPONENT = "account_snapshot"
POSITIONS_ORDER_HISTORY_COMPONENT = "positions_order_history"
MARKET_SYMBOL_COMPONENT = "market_symbol"

_REQUIRED_FILENAMES = (
    schema_validator.ACCOUNT_SNAPSHOT_FILE,
    schema_validator.POSITIONS_ORDER_HISTORY_FILE,
    schema_validator.MARKET_SYMBOL_FILE,
)

_FILENAME_TO_COMPONENT = {
    schema_validator.ACCOUNT_SNAPSHOT_FILE: ACCOUNT_SNAPSHOT_COMPONENT,
    schema_validator.POSITIONS_ORDER_HISTORY_FILE: POSITIONS_ORDER_HISTORY_COMPONENT,
    schema_validator.MARKET_SYMBOL_FILE: MARKET_SYMBOL_COMPONENT,
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

_FORBIDDEN_RESULT_FIELDS = frozenset(
    {
        "password",
        "credential",
        "token",
        "secret",
        "api_key",
        "login",
        "account_number",
        "raw_payload",
        "raw_account_snapshot",
        "raw_positions_order_history",
        "raw_market_symbol",
        "payload",
        "ticket",
        "order_id",
        "order_send",
        "order_close",
        "order_modify",
        "order_delete",
        "ea_command",
        "execute_trade",
        "can_trade",
        "allow_trade",
        "should_buy",
        "should_sell",
        "buy_now",
        "sell_now",
        "open_position",
        "close_position",
        "suggested_lot",
        "final_lot",
        "trade_signal",
        "trading_action",
        "override_risk",
        "bypass_gate",
        "traceback",
        "stack_trace",
        "system_path",
        "trade_plan",
    }
)

_VALIDATION_STATUS_CODES = frozenset(
    {
        schema_validator.MT4_DEMO_READONLY_SCHEMA_VALID,
        schema_validator.MT4_DEMO_READONLY_SCHEMA_INVALID,
        schema_validator.MT4_DEMO_READONLY_SCHEMA_INPUT_INVALID,
        schema_validator.MT4_DEMO_READONLY_SCHEMA_VERSION_UNSUPPORTED,
        schema_validator.MT4_DEMO_READONLY_SOURCE_MODE_REJECTED,
        schema_validator.MT4_DEMO_READONLY_SAFETY_FIELD_VIOLATION,
        schema_validator.MT4_DEMO_READONLY_FORBIDDEN_FIELD_DETECTED,
        schema_validator.MT4_DEMO_READONLY_FILENAME_REJECTED,
    }
)

_SAFE_REASON_CODES = frozenset(
    {
        "PAYLOAD_NOT_DICT",
        "FILENAME_REJECTED",
        "REQUIRED_FIELD_MISSING",
        "UNKNOWN_FIELD_DETECTED",
        "FIELD_TYPE_INVALID",
        "FIELD_VALUE_INVALID",
        "SCHEMA_VERSION_UNSUPPORTED",
        "SOURCE_MODE_REJECTED",
        "SAFETY_FIELD_VIOLATION",
        "FORBIDDEN_FIELD_DETECTED",
        "VALIDATOR_OUTPUT_SANITIZED",
        "UNSAFE_VALIDATOR_OUTPUT_BLOCKED",
        "VALIDATOR_EXCEPTION_SANITIZED",
        "UNEXPECTED_COMPONENT",
    }
)

_SANITIZED_REASON_CODE = "VALIDATOR_OUTPUT_SANITIZED"
_UNSAFE_VALIDATOR_OUTPUT_REASON_CODE = "UNSAFE_VALIDATOR_OUTPUT_BLOCKED"
_VALIDATOR_EXCEPTION_REASON_CODE = "VALIDATOR_EXCEPTION_SANITIZED"


def get_required_mt4_demo_readonly_source_filenames() -> tuple[str, ...]:
    return _REQUIRED_FILENAMES


def build_mt4_demo_readonly_source_summary(
    payloads_by_filename: object,
) -> dict[str, Any]:
    if not isinstance(payloads_by_filename, dict):
        return _build_summary_result(
            passed=False,
            status_code=MT4_DEMO_READONLY_SOURCE_SUMMARY_INPUT_INVALID,
            component_statuses=_missing_component_statuses(
                set(_REQUIRED_FILENAMES),
                reason="input is not a payload mapping",
            ),
            validation_statuses=[],
            missing_components=list(_REQUIRED_FILENAMES),
            unexpected_components=[],
            block_reasons=["payloads_by_filename must be a dict"],
            warning_reasons=[],
        )

    filename_results = {
        filename: path_guard.validate_mt4_demo_readonly_filename(filename)
        for filename in payloads_by_filename
    }
    safe_input_filenames = {
        str(result["safe_filename"])
        for result in filename_results.values()
        if result["passed"] is True
    }

    missing_components = [
        filename for filename in _REQUIRED_FILENAMES if filename not in payloads_by_filename
    ]
    unexpected_components = [
        _safe_unexpected_component_label(filename, result)
        for filename, result in filename_results.items()
        if result["passed"] is not True
        or str(result["safe_filename"]) not in _REQUIRED_FILENAMES
    ]

    component_statuses: list[dict[str, Any]] = []
    validation_statuses: list[dict[str, Any]] = []
    block_reasons: list[str] = []

    for filename in _REQUIRED_FILENAMES:
        if filename not in payloads_by_filename:
            component_statuses.append(
                _missing_component_status(filename, reason="missing required component")
            )
            block_reasons.append(f"missing component: {filename}")
            continue

        try:
            raw_validation_result = schema_validator.validate_mt4_demo_readonly_payload(
                filename,
                payloads_by_filename[filename],
            )
        except Exception:
            raw_validation_result = _validator_exception_result()

        validation_result = _sanitize_validation_result(raw_validation_result)
        component_statuses.append(
            _component_status_from_validation(filename, validation_result)
        )
        validation_statuses.append(
            _validation_status_from_result(filename, validation_result)
        )
        if validation_result["passed"] is not True:
            block_reasons.extend(
                _block_reasons_from_validation(filename, validation_result)
            )

    if unexpected_components:
        block_reasons.append("unexpected component detected")
        for filename, result in filename_results.items():
            if result["passed"] is not True:
                validation_statuses.append(
                    _filename_rejection_validation_status(filename, result)
                )
                continue
            safe_filename = str(result["safe_filename"])
            if safe_filename not in _REQUIRED_FILENAMES:
                validation_statuses.append(
                    _unexpected_component_validation_status(safe_filename)
                )

    all_validations_passed = all(
        status["passed"] is True for status in validation_statuses
    )
    passed = (
        not missing_components
        and not unexpected_components
        and all_validations_passed
        and safe_input_filenames == set(_REQUIRED_FILENAMES)
    )

    return _build_summary_result(
        passed=passed,
        status_code=(
            MT4_DEMO_READONLY_SOURCE_SUMMARY_READY
            if passed
            else _blocked_status_code(
                missing_components=missing_components,
                unexpected_components=unexpected_components,
                validation_statuses=validation_statuses,
            )
        ),
        component_statuses=component_statuses,
        validation_statuses=validation_statuses,
        missing_components=missing_components,
        unexpected_components=unexpected_components,
        block_reasons=block_reasons if block_reasons else [],
        warning_reasons=[],
    )


def _build_summary_result(
    *,
    passed: bool,
    status_code: str,
    component_statuses: list[dict[str, Any]],
    validation_statuses: list[dict[str, Any]],
    missing_components: list[str],
    unexpected_components: list[str],
    block_reasons: list[str],
    warning_reasons: list[str],
) -> dict[str, Any]:
    data_quality_notes = (
        ["all required demo readonly payloads passed schema validation"]
        if passed
        else ["source summary adapter blocked incomplete or unsafe payloads"]
    )
    return {
        "passed": passed,
        "status_code": status_code,
        "source_mode": SOURCE_MODE,
        "source_scope": SOURCE_SCOPE,
        "summary_version": SUMMARY_VERSION,
        "component_statuses": component_statuses,
        "validation_statuses": validation_statuses,
        "missing_components": list(dict.fromkeys(missing_components)),
        "unexpected_components": list(dict.fromkeys(unexpected_components)),
        "block_reasons": list(dict.fromkeys(block_reasons)),
        "warning_reasons": list(dict.fromkeys(warning_reasons)),
        "data_quality_notes": data_quality_notes,
        "next_allowed_stage": (
            "read_only_source_summary_available_for_internal_diagnostics"
            if passed
            else "fix_demo_readonly_source_inputs_before_summary"
        ),
        "next_blocked_stage": "execution_and_trading_remain_blocked",
        **_SAFETY_FIELDS,
        "notes": [
            "Adapter summarizes caller-provided in-memory payloads only.",
            "This does not enable API source mode, MT4 connection, Dashboard integration, or trading permission.",
        ],
    }


def _missing_component_statuses(
    missing_filenames: set[str],
    *,
    reason: str,
) -> list[dict[str, Any]]:
    return [
        _missing_component_status(filename, reason=reason)
        for filename in _REQUIRED_FILENAMES
        if filename in missing_filenames
    ]


def _missing_component_status(filename: str, *, reason: str) -> dict[str, Any]:
    component_name = _FILENAME_TO_COMPONENT[filename]
    return {
        "component_name": component_name,
        "filename": filename,
        "passed": False,
        "status_code": MT4_DEMO_READONLY_SOURCE_SUMMARY_MISSING_COMPONENTS,
        "safe_summary": f"{component_name} is missing from in-memory demo readonly inputs.",
        "block_reasons": [reason],
        "warning_reasons": [],
        "data_quality_notes": ["required demo readonly component missing"],
        **_component_safety_fields(),
    }


def _component_status_from_validation(
    filename: str,
    validation_result: dict[str, Any],
) -> dict[str, Any]:
    component_name = _FILENAME_TO_COMPONENT[filename]
    passed = validation_result["passed"] is True
    return {
        "component_name": component_name,
        "filename": filename,
        "passed": passed,
        "status_code": _safe_status_code(validation_result.get("status_code")),
        "safe_summary": (
            f"{component_name} schema validation passed."
            if passed
            else f"{component_name} schema validation blocked."
        ),
        "block_reasons": (
            []
            if passed
            else _block_reasons_from_validation(filename, validation_result)
        ),
        "warning_reasons": [],
        "data_quality_notes": (
            ["schema validation passed"]
            if passed
            else ["schema validation failed without exposing payload values"]
        ),
        **_component_safety_fields(),
    }


def _validation_status_from_result(
    filename: str,
    validation_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "filename": filename,
        "passed": validation_result["passed"] is True,
        "status_code": _safe_status_code(validation_result.get("status_code")),
        "reason_codes": _safe_reason_codes(validation_result.get("reason_codes")),
        "missing_fields": _safe_field_paths(validation_result.get("missing_fields")),
        "invalid_fields": _safe_field_paths(validation_result.get("invalid_fields")),
        "blocked_fields": _safe_field_paths(validation_result.get("blocked_fields")),
    }


def _filename_rejection_validation_status(
    filename: object,
    filename_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "filename": _safe_unexpected_component_label(filename, filename_result),
        "passed": False,
        "status_code": MT4_DEMO_READONLY_SOURCE_SUMMARY_UNEXPECTED_COMPONENTS,
        "reason_codes": ["FILENAME_REJECTED"],
        "missing_fields": [],
        "invalid_fields": [],
        "blocked_fields": [],
    }


def _unexpected_component_validation_status(filename: str) -> dict[str, Any]:
    return {
        "filename": filename,
        "passed": False,
        "status_code": MT4_DEMO_READONLY_SOURCE_SUMMARY_UNEXPECTED_COMPONENTS,
        "reason_codes": ["UNEXPECTED_COMPONENT"],
        "missing_fields": [],
        "invalid_fields": [],
        "blocked_fields": [],
    }


def _block_reasons_from_validation(
    filename: str,
    validation_result: dict[str, Any],
) -> list[str]:
    component_name = _FILENAME_TO_COMPONENT[filename]
    reasons = [f"schema validation failed: {component_name}"]
    reason_codes = set(_safe_reason_codes(validation_result.get("reason_codes")))
    if "FORBIDDEN_FIELD_DETECTED" in reason_codes:
        reasons.append(f"forbidden field detected: {component_name}")
    if "SAFETY_FIELD_VIOLATION" in reason_codes:
        reasons.append(f"safety field violation: {component_name}")
    return reasons


def _blocked_status_code(
    *,
    missing_components: list[str],
    unexpected_components: list[str],
    validation_statuses: list[dict[str, Any]],
) -> str:
    if unexpected_components:
        return MT4_DEMO_READONLY_SOURCE_SUMMARY_UNEXPECTED_COMPONENTS
    if missing_components:
        return MT4_DEMO_READONLY_SOURCE_SUMMARY_MISSING_COMPONENTS

    reason_codes = {
        reason
        for status in validation_statuses
        for reason in _safe_reason_codes(status.get("reason_codes"))
    }
    if reason_codes.intersection(
        {
            "SAFETY_FIELD_VIOLATION",
            "FORBIDDEN_FIELD_DETECTED",
            _UNSAFE_VALIDATOR_OUTPUT_REASON_CODE,
            _VALIDATOR_EXCEPTION_REASON_CODE,
        }
    ):
        return MT4_DEMO_READONLY_SOURCE_SUMMARY_SAFETY_BLOCKED
    if any(status["passed"] is not True for status in validation_statuses):
        return MT4_DEMO_READONLY_SOURCE_SUMMARY_VALIDATION_FAILED
    return MT4_DEMO_READONLY_SOURCE_SUMMARY_BLOCKED


def _safe_unexpected_component_label(
    filename: object,
    filename_result: dict[str, Any],
) -> str:
    if filename_result["passed"] is True:
        return str(filename_result["safe_filename"])
    if not isinstance(filename, str):
        return "<rejected_filename>"
    if (
        filename
        and filename == filename.strip()
        and "/" not in filename
        and "\\" not in filename
        and ".." not in filename
        and len(filename) <= 80
    ):
        return filename
    return "<rejected_filename>"


def _validator_exception_result() -> dict[str, Any]:
    return {
        "passed": False,
        "status_code": MT4_DEMO_READONLY_SOURCE_SUMMARY_SAFETY_BLOCKED,
        "reason_codes": [_VALIDATOR_EXCEPTION_REASON_CODE],
        "missing_fields": [],
        "invalid_fields": [],
        "blocked_fields": [],
    }


def _sanitize_validation_result(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return _unsafe_validation_result()

    unsafe_output = _contains_forbidden_result_key(value) or _has_unsafe_safety_flags(value)

    reason_codes = _safe_reason_codes(value.get("reason_codes"))
    missing_fields = _safe_field_paths(value.get("missing_fields"))
    invalid_fields = _safe_field_paths(value.get("invalid_fields"))
    blocked_fields = _safe_field_paths(value.get("blocked_fields"))

    sanitized = {
        "passed": value.get("passed") is True and not unsafe_output,
        "status_code": _safe_status_code(value.get("status_code")),
        "reason_codes": reason_codes,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "blocked_fields": blocked_fields,
    }

    if unsafe_output:
        sanitized["passed"] = False
        sanitized["status_code"] = schema_validator.MT4_DEMO_READONLY_SAFETY_FIELD_VIOLATION
        sanitized["reason_codes"] = list(
            dict.fromkeys(
                [
                    *reason_codes,
                    _SANITIZED_REASON_CODE,
                    _UNSAFE_VALIDATOR_OUTPUT_REASON_CODE,
                ]
            )
        )

    return sanitized


def _unsafe_validation_result() -> dict[str, Any]:
    return {
        "passed": False,
        "status_code": schema_validator.MT4_DEMO_READONLY_SAFETY_FIELD_VIOLATION,
        "reason_codes": [
            _SANITIZED_REASON_CODE,
            _UNSAFE_VALIDATOR_OUTPUT_REASON_CODE,
        ],
        "missing_fields": [],
        "invalid_fields": [],
        "blocked_fields": [],
    }


def _safe_status_code(value: object) -> str:
    if isinstance(value, str) and value in _VALIDATION_STATUS_CODES:
        return value
    if value == MT4_DEMO_READONLY_SOURCE_SUMMARY_SAFETY_BLOCKED:
        return MT4_DEMO_READONLY_SOURCE_SUMMARY_SAFETY_BLOCKED
    return "VALIDATOR_STATUS_SANITIZED"


def _safe_reason_codes(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    reason_codes: list[str] = []
    for item in value:
        if item in _SAFE_REASON_CODES:
            reason_codes.append(item)
        elif isinstance(item, str):
            reason_codes.append(_SANITIZED_REASON_CODE)
    return list(dict.fromkeys(reason_codes))


def _safe_field_paths(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    field_paths: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        sanitized_path = _safe_field_path(item)
        if sanitized_path is not None:
            field_paths.append(sanitized_path)
    return list(dict.fromkeys(field_paths))


def _safe_field_path(field_path: str) -> str | None:
    parts = [part for part in field_path.split(".") if part]
    if not parts:
        return None
    lower_field_path = field_path.lower()
    lower_parts = [part.lower() for part in parts]
    if field_path != lower_field_path:
        return "validator_output_sanitized"
    if _looks_like_path_or_trace(field_path):
        return "validator_output_sanitized"
    if any(part in _FORBIDDEN_RESULT_FIELDS for part in lower_parts):
        return "forbidden_field_detected"
    if any(forbidden_key in lower_field_path for forbidden_key in _FORBIDDEN_RESULT_FIELDS):
        return "forbidden_field_detected"
    if any(not _is_safe_field_name_part(part) for part in parts):
        return "validator_output_sanitized"
    return ".".join(parts)


def _is_safe_field_name_part(value: str) -> bool:
    return value.replace("_", "").isalnum()


def _contains_forbidden_result_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, child_value in value.items():
            if isinstance(key, str) and key in _FORBIDDEN_RESULT_FIELDS:
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


def _component_safety_fields() -> dict[str, bool]:
    return {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }


def _assert_no_forbidden_result_keys(result: dict[str, Any]) -> None:
    if _FORBIDDEN_RESULT_FIELDS.intersection(result):
        raise AssertionError("source summary result contains forbidden keys")
