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
        "raw_payload",
        "payload",
        "suggested_lot",
        "final_lot",
        "buy",
        "sell",
        "open",
        "close",
        "ea_command",
        "trade_signal",
        "trading_action",
        "trade_plan",
        "can_trade",
        "allow_trade",
        "should_buy",
        "should_sell",
    }
)


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

        validation_result = schema_validator.validate_mt4_demo_readonly_payload(
            filename,
            payloads_by_filename[filename],
        )
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
        "status_code": str(validation_result["status_code"]),
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
        "status_code": str(validation_result["status_code"]),
        "reason_codes": _safe_string_list(validation_result.get("reason_codes")),
        "missing_fields": _safe_string_list(validation_result.get("missing_fields")),
        "invalid_fields": _safe_string_list(validation_result.get("invalid_fields")),
        "blocked_fields": _safe_string_list(validation_result.get("blocked_fields")),
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
    reason_codes = set(_safe_string_list(validation_result.get("reason_codes")))
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
        for reason in _safe_string_list(status.get("reason_codes"))
    }
    if reason_codes.intersection(
        {"SAFETY_FIELD_VIOLATION", "FORBIDDEN_FIELD_DETECTED"}
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


def _safe_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


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
