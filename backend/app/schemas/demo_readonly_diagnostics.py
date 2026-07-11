from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


API_VERSION = "1.0"
DEMO_READONLY_DIAGNOSTICS_ENDPOINT = "/api/demo-readonly/diagnostics"

DEMO_READONLY_DIAGNOSTICS_READY = "DEMO_READONLY_DIAGNOSTICS_READY"
DEMO_READONLY_DIAGNOSTICS_BLOCKED = "DEMO_READONLY_DIAGNOSTICS_BLOCKED"
DEMO_READONLY_INTERNAL_ERROR = "DEMO_READONLY_INTERNAL_ERROR"
DEMO_READONLY_SAFETY_FIELD_VIOLATION = (
    "DEMO_READONLY_SAFETY_FIELD_VIOLATION"
)

SOURCE_SCOPE = "docs_fixture_only"
VALIDATION_STAGE = "demo_readonly_docs_fixture_validation_summary"
SOURCE_STATUS_DEFAULT_READY = "docs_fixture_only_ready"
SOURCE_STATUS_BLOCKED = "source_mode_blocked"
SOURCE_STATUS_SAFETY_BLOCKED = "source_config_safety_blocked"
SOURCE_CONFIG_STATUS_UNAVAILABLE = "SOURCE_CONFIG_STATUS_UNAVAILABLE"
SOURCE_CONFIG_STATUS_DEFAULT_READY = "MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY"
SOURCE_CONFIG_STATUS_SAFETY_BLOCKED = "SOURCE_CONFIG_SAFETY_BLOCKED"
MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE = (
    "mt4_demo_readonly_file_bridge_enabled"
)
MT4_DEMO_READONLY_READER_SOURCE_SCOPE = (
    "mt4_demo_readonly_reader_safe_summary_only"
)
CANONICAL_MT4_DEMO_READONLY_DATA_QUALITY_SOURCE_SCOPE = (
    "canonical_mt4_demo_readonly_data_quality_summary_only"
)
CANONICAL_SUMMARY_ENVELOPE_INVALID_REASON = (
    "Canonical diagnostics summary envelope is inconsistent."
)
SUMMARY_SOURCE_CONFIG_MISMATCH_REASON = (
    "Reader summary does not match safe server source configuration."
)
_READER_SUMMARY_SOURCE_SCOPES = frozenset(
    {
        MT4_DEMO_READONLY_READER_SOURCE_SCOPE,
        CANONICAL_MT4_DEMO_READONLY_DATA_QUALITY_SOURCE_SCOPE,
    }
)
READER_STATUS_NOT_CALLED = "not_called"
READER_STATUS_READY = "ready"
READER_STATUS_BLOCKED = "blocked"
READER_STATUS_ERROR_SAFE = "error_safe"
READER_STATUS_SAFETY_BLOCKED = "safety_blocked"
READER_STATUS_CODE_NOT_CALLED = "READER_NOT_CALLED"
READER_STATUS_CODE_UNAVAILABLE = "READER_STATUS_UNAVAILABLE"
READER_STATUS_CODE_SAFETY_BLOCKED = "READER_OUTPUT_SAFETY_BLOCKED"
READER_EXCEPTION_SAFE_STATUS_CODE = "MT4_DEMO_READONLY_READER_EXCEPTION_SAFE"
_ALLOWED_SOURCE_MODES = {
    SOURCE_SCOPE,
    MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
}

_REQUIRED_SUMMARY_SAFETY_FIELDS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
}

_OPTIONAL_FALSE_SUMMARY_SAFETY_FIELDS = {
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}

_CANONICAL_SUMMARY_VALIDATION_STAGE = (
    "canonical_bundle_v1_diagnostics_summary_adapter"
)
_CANONICAL_SUMMARY_FIXTURE_SOURCE = (
    "canonical_bundle_v1_data_quality_gate_result"
)
_CANONICAL_SUMMARY_READY = "CANONICAL_DIAGNOSTICS_SUMMARY_READY"
_CANONICAL_SUMMARY_READY_WITH_WARNINGS = (
    "CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS"
)
_CANONICAL_SUMMARY_BLOCKED = "CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED"
_CANONICAL_SUMMARY_INPUT_INVALID = (
    "CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID"
)
_CANONICAL_SUMMARY_SAFE_FAILURE = (
    "CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE"
)
_CANONICAL_SUMMARY_WARNING_CODES = frozenset(
    {"IDEMPOTENT_REPEAT", "SEQUENCE_GAP"}
)
_CANONICAL_DATA_QUALITY_PASSED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED"
)
_CANONICAL_DATA_QUALITY_PASSED_WITH_WARNINGS = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS"
)
_CANONICAL_DATA_QUALITY_INPUT_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID"
)
_CANONICAL_DATA_QUALITY_POLICY_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID"
)
_CANONICAL_DATA_QUALITY_REJECTED = (
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED"
)
_CANONICAL_DATA_QUALITY_BLOCKED_REASON_CODES = {
    _CANONICAL_DATA_QUALITY_INPUT_INVALID: frozenset(
        {
            "DATA_QUALITY_INPUT_NOT_OBJECT",
            "DATA_QUALITY_REQUIRED_READER_KEY_MISSING",
            "DATA_QUALITY_UNEXPECTED_READER_KEY",
            "DATA_QUALITY_READER_FIELD_TYPE_INVALID",
            "DATA_QUALITY_COMPONENT_STATUS_INVALID",
        }
    ),
    _CANONICAL_DATA_QUALITY_POLICY_INVALID: frozenset(
        {"DATA_QUALITY_POLICY_INVALID"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED": frozenset(
        {
            "READER_SAFETY_ENVELOPE_INVALID",
            "READER_RESULT_INCONSISTENT",
            "READER_WARNING_CODES_INVALID",
        }
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED": frozenset(
        {"READER_MIXED_GENERATION_BLOCKED"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED": frozenset(
        {"READER_INTEGRITY_INVALID"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED": frozenset(
        {"READER_DATA_STALE"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED": frozenset(
        {"READER_STRUCTURE_INVALID"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED": frozenset(
        {"READER_VALUE_INVALID"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED": frozenset(
        {"READER_BLOCKED"}
    ),
    _CANONICAL_DATA_QUALITY_REJECTED: frozenset(
        {"UPSTREAM_WARNINGS_REJECTED_BY_POLICY"}
    ),
    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE": frozenset(
        {"DATA_QUALITY_GATE_EXCEPTION_SANITIZED"}
    ),
}
_CANONICAL_DATA_QUALITY_NO_WARNING_STATUS_CODES = frozenset(
    {
        _CANONICAL_DATA_QUALITY_INPUT_INVALID,
        _CANONICAL_DATA_QUALITY_POLICY_INVALID,
    }
)
_CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE = (
    "CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE"
)
_CANONICAL_SUMMARY_KEYS = frozenset(
    {
        "passed",
        "status_code",
        "source_scope",
        "validation_stage",
        "fixture_source",
        "bundle_validation_status",
        "component_statuses",
        "block_reasons",
        "warning_reasons",
        "readiness_notes",
        "next_allowed_stage",
        "next_blocked_stage",
        *_REQUIRED_SUMMARY_SAFETY_FIELDS,
        *_OPTIONAL_FALSE_SUMMARY_SAFETY_FIELDS,
    }
)
_CANONICAL_STATUS_KEYS = frozenset(
    {
        "passed",
        "status_code",
        "block_reasons",
        "warning_reasons",
        "read_only",
        "demo_only",
        "is_tradable",
        "can_execute",
    }
)
_CANONICAL_SUCCESS_NEXT_ALLOWED_STAGE = [
    "demo_readonly_diagnostics_response_integration"
]
_CANONICAL_SUCCESS_NEXT_BLOCKED_STAGE = [
    "api_reader_activation",
    "execution_chain",
]
_CANONICAL_BLOCKED_NEXT_BLOCKED_STAGE = [
    "demo_readonly_diagnostics_response_integration",
    "api_reader_activation",
    "readonly_analysis",
    "execution_chain",
]

_FORBIDDEN_RESPONSE_KEYS = {
    "account_number",
    "api_key",
    "base_dir",
    "bridge_dir",
    "bypass_gate",
    "buy",
    "buy_now",
    "candidate_path",
    "checksum",
    "checksum_checked",
    "checksum_passed",
    "close",
    "close_position",
    "credential",
    "ea_command",
    "final_lot",
    "login",
    "open",
    "open_position",
    "order_id",
    "order_close",
    "order_delete",
    "order_modify",
    "order_send",
    "orderclose",
    "orderdelete",
    "ordermodify",
    "ordersend",
    "override_risk",
    "password",
    "raw_payload",
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
    "trade_signal",
    "trading_action",
    "allow_trade",
    "auto_trade",
    "can_trade",
    "execute_trade",
    "raw_account_snapshot",
    "raw_positions_order_history",
    "raw_market_symbol",
}

_FORBIDDEN_TEXT_MARKERS = _FORBIDDEN_RESPONSE_KEYS | {
    "traceback",
    "stack trace",
    ".env",
    "c:\\",
    "\\users\\",
    "/users/",
    "/home/",
    ".py",
    "site-packages",
}

_REDACTED_UNSAFE_TEXT = "[redacted unsafe content]"


class DemoReadonlyDiagnosticsResponse(BaseModel):
    api_version: str
    endpoint: str
    generated_at: str
    passed: bool
    status_code: str
    source_scope: str
    source_mode: str
    source_status: str
    source_config_status_code: str
    source_config_passed: bool
    reader_status: str
    reader_passed: bool
    reader_status_code: str
    validation_stage: str
    fixture_source: str
    bundle_validation_status: dict[str, Any]
    component_statuses: dict[str, dict[str, Any]]
    block_reasons: list[str]
    warning_reasons: list[str]
    readiness_notes: list[str]
    next_allowed_stage: list[str]
    next_blocked_stage: list[str]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool

    model_config = ConfigDict(extra="forbid")


def demo_readonly_diagnostics_response(
    summary: Any,
    source_config_guard_result: Any = None,
) -> DemoReadonlyDiagnosticsResponse:
    is_reader_summary = _is_reader_summary(summary)
    safety_reasons = _safety_violation_reasons(summary)
    safety_reasons.extend(_canonical_summary_consistency_reasons(summary))
    source_config_status = _safe_source_config_status(source_config_guard_result)
    source_config_safety_reasons = _source_config_safety_violation_reasons(
        source_config_status
    )
    safety_reasons.extend(source_config_safety_reasons)
    safety_reasons.extend(
        _summary_source_consistency_reasons(
            source_config_status=source_config_status,
            is_reader_summary=is_reader_summary,
        )
    )

    passed = _bool_value(summary, "passed", default=False)
    reader_safety_blocked = is_reader_summary and bool(safety_reasons)

    status_code = (
        DEMO_READONLY_DIAGNOSTICS_READY
        if passed
        else DEMO_READONLY_DIAGNOSTICS_BLOCKED
    )
    if safety_reasons:
        passed = False
        status_code = DEMO_READONLY_SAFETY_FIELD_VIOLATION

    block_reasons = _safe_list(_value(summary, "block_reasons"))
    block_reasons.extend(safety_reasons)

    return DemoReadonlyDiagnosticsResponse(
        api_version=API_VERSION,
        endpoint=DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
        generated_at=_generated_at(),
        passed=passed,
        status_code=status_code,
        source_scope=_str_value(summary, "source_scope", SOURCE_SCOPE),
        source_mode=_source_mode_from_source_config_status(source_config_status),
        source_status=_source_status_from_source_config_status(source_config_status),
        source_config_status_code=_str_value(
            source_config_status,
            "status_code",
            SOURCE_CONFIG_STATUS_UNAVAILABLE,
        ),
        source_config_passed=_source_config_passed(source_config_status),
        reader_status=_reader_status_from_summary(
            summary,
            source_config_status=source_config_status,
            is_reader_summary=is_reader_summary,
            reader_safety_blocked=reader_safety_blocked,
        ),
        reader_passed=_reader_passed_from_summary(
            summary,
            source_config_status=source_config_status,
            is_reader_summary=is_reader_summary,
            reader_safety_blocked=reader_safety_blocked,
        ),
        reader_status_code=_reader_status_code_from_summary(
            summary,
            source_config_status=source_config_status,
            is_reader_summary=is_reader_summary,
            reader_safety_blocked=reader_safety_blocked,
        ),
        validation_stage=_str_value(
            summary,
            "validation_stage",
            VALIDATION_STAGE,
        ),
        fixture_source=_str_value(summary, "fixture_source", ""),
        bundle_validation_status=_safe_status_dict(
            _value(summary, "bundle_validation_status")
        ),
        component_statuses=_safe_component_statuses(
            _value(summary, "component_statuses")
        ),
        block_reasons=block_reasons,
        warning_reasons=_safe_list(_value(summary, "warning_reasons")),
        readiness_notes=_safe_list(_value(summary, "readiness_notes")),
        next_allowed_stage=_safe_list(_value(summary, "next_allowed_stage")),
        next_blocked_stage=_safe_list(_value(summary, "next_blocked_stage")),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


def demo_readonly_diagnostics_internal_error_response() -> (
    DemoReadonlyDiagnosticsResponse
):
    return DemoReadonlyDiagnosticsResponse(
        api_version=API_VERSION,
        endpoint=DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
        generated_at=_generated_at(),
        passed=False,
        status_code=DEMO_READONLY_INTERNAL_ERROR,
        source_scope=SOURCE_SCOPE,
        source_mode=SOURCE_SCOPE,
        source_status=SOURCE_STATUS_DEFAULT_READY,
        source_config_status_code=SOURCE_CONFIG_STATUS_DEFAULT_READY,
        source_config_passed=True,
        reader_status=READER_STATUS_NOT_CALLED,
        reader_passed=False,
        reader_status_code=READER_STATUS_CODE_NOT_CALLED,
        validation_stage=VALIDATION_STAGE,
        fixture_source="docs_fixture_only",
        bundle_validation_status=_safe_status_dict(None),
        component_statuses={},
        block_reasons=["Summary service failed safely."],
        warning_reasons=[],
        readiness_notes=[
            "Diagnostics are read-only.",
            "Diagnostics are not trading permission.",
            "Diagnostics do not generate trading signals.",
        ],
        next_allowed_stage=[],
        next_blocked_stage=["execution_chain"],
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


def _safety_violation_reasons(summary: Any) -> list[str]:
    reasons = []
    for field_name, expected_value in _REQUIRED_SUMMARY_SAFETY_FIELDS.items():
        actual_value = _value(summary, field_name, _Missing)
        if actual_value is _Missing:
            reasons.append(f"Missing safety field: {field_name}.")
            continue
        if actual_value is not expected_value:
            reasons.append(f"Unsafe safety field value: {field_name}.")
    for field_name, expected_value in _OPTIONAL_FALSE_SUMMARY_SAFETY_FIELDS.items():
        actual_value = _value(summary, field_name, _Missing)
        if actual_value is not _Missing and actual_value is not expected_value:
            reasons.append(f"Unsafe safety field value: {field_name}.")
    if _contains_forbidden_content(summary):
        reasons.append("Unsafe response content was removed.")
    return reasons


def _safe_status_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "passed": False,
            "status_code": "STATUS_UNAVAILABLE",
            "block_reasons": [],
            "warning_reasons": [],
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
        }

    return {
        "passed": value.get("passed") is True,
        "status_code": _safe_scalar(value.get("status_code")),
        "block_reasons": _safe_list(value.get("block_reasons")),
        "warning_reasons": _safe_list(value.get("warning_reasons")),
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }


def _safe_source_config_status(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return _blocked_source_config_status(
            status_code=SOURCE_CONFIG_STATUS_UNAVAILABLE,
            block_reason="source_config_guard_result_unavailable",
        )

    if (
        _source_config_has_unsafe_safety_flags(value)
        or _contains_source_config_forbidden_content(value)
    ):
        return _blocked_source_config_status(
            status_code=SOURCE_CONFIG_STATUS_SAFETY_BLOCKED,
            block_reason="source_config_output_sanitized",
        )

    return {
        "passed": value.get("passed") is True,
        "status_code": _safe_scalar(value.get("status_code"))
        or SOURCE_CONFIG_STATUS_UNAVAILABLE,
        "selected_source_mode": _safe_scalar(value.get("selected_source_mode"))
        or SOURCE_SCOPE,
        "source_status": _safe_scalar(value.get("source_status"))
        or SOURCE_STATUS_BLOCKED,
        "block_reasons": _safe_list(value.get("block_reasons")),
        "warning_reasons": _safe_list(value.get("warning_reasons")),
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }


def _blocked_source_config_status(
    *,
    status_code: str,
    block_reason: str,
) -> dict[str, Any]:
    return {
        "passed": False,
        "status_code": status_code,
        "selected_source_mode": SOURCE_SCOPE,
        "source_status": SOURCE_STATUS_SAFETY_BLOCKED,
        "block_reasons": [block_reason],
        "warning_reasons": [],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }


def _source_config_has_unsafe_safety_flags(value: dict[str, Any]) -> bool:
    required_true_fields = {
        "read_only": True,
        "demo_only": True,
    }
    required_false_fields = {
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }
    return any(
        value.get(field_name) is not expected_value
        for field_name, expected_value in {
            **required_true_fields,
            **required_false_fields,
        }.items()
    )


def _contains_source_config_forbidden_content(value: Any) -> bool:
    if isinstance(value, str):
        return _is_unsafe_text(value)
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and key.casefold() in {
                forbidden_key.casefold()
                for forbidden_key in _FORBIDDEN_RESPONSE_KEYS
            }:
                return True
            if _contains_source_config_forbidden_content(child):
                return True
        return False
    if isinstance(value, list | tuple | set):
        return any(_contains_source_config_forbidden_content(child) for child in value)
    if isinstance(value, bool | int | float | type(None)):
        return False
    value_dict = getattr(value, "__dict__", None)
    if isinstance(value_dict, dict):
        return _contains_source_config_forbidden_content(value_dict)
    return False


def _source_config_safety_violation_reasons(
    source_config_status: dict[str, Any],
) -> list[str]:
    if source_config_status.get("passed") is not True:
        return _safe_list(source_config_status.get("block_reasons")) or [
            "source_config_guard_blocked"
        ]
    if source_config_status.get("selected_source_mode") not in _ALLOWED_SOURCE_MODES:
        return ["Source config guard selected an unsupported source mode."]
    if source_config_status.get("read_only") is not True:
        return ["Unsafe source config safety field value: read_only."]
    if source_config_status.get("demo_only") is not True:
        return ["Unsafe source config safety field value: demo_only."]
    for field_name in (
        "is_tradable",
        "can_execute",
        "is_trading_permission",
        "is_execution_instruction",
        "allowed_to_call_ea",
        "allowed_to_modify_risk",
    ):
        if source_config_status.get(field_name) is not False:
            return [f"Unsafe source config safety field value: {field_name}."]
    return []


def _source_mode_from_source_config_status(
    source_config_status: dict[str, Any],
) -> str:
    selected_source_mode = source_config_status.get("selected_source_mode")
    if selected_source_mode in _ALLOWED_SOURCE_MODES:
        return str(selected_source_mode)
    return SOURCE_SCOPE


def _source_status_from_source_config_status(
    source_config_status: dict[str, Any],
) -> str:
    if source_config_status.get("selected_source_mode") in _ALLOWED_SOURCE_MODES:
        return _str_value(
            source_config_status,
            "source_status",
            SOURCE_STATUS_DEFAULT_READY,
        )
    return SOURCE_STATUS_BLOCKED


def _source_config_passed(source_config_status: dict[str, Any]) -> bool:
    return (
        source_config_status.get("passed") is True
        and source_config_status.get("selected_source_mode") in _ALLOWED_SOURCE_MODES
    )


def _is_reader_summary(summary: Any) -> bool:
    return _strict_source_scope(summary) in _READER_SUMMARY_SOURCE_SCOPES


def _canonical_summary_consistency_reasons(summary: Any) -> list[str]:
    if _strict_source_scope(summary) != (
        CANONICAL_MT4_DEMO_READONLY_DATA_QUALITY_SOURCE_SCOPE
    ):
        return []
    if _canonical_summary_is_consistent(summary):
        return []
    return [CANONICAL_SUMMARY_ENVELOPE_INVALID_REASON]


def _canonical_summary_is_consistent(summary: Any) -> bool:
    if type(summary) is not dict or set(summary) != _CANONICAL_SUMMARY_KEYS:
        return False
    if type(summary["passed"]) is not bool:
        return False
    if any(
        type(summary[field_name]) is not str
        for field_name in (
            "status_code",
            "source_scope",
            "validation_stage",
            "fixture_source",
        )
    ):
        return False
    if any(
        not _is_strict_string_list(summary[field_name])
        for field_name in (
            "block_reasons",
            "warning_reasons",
            "readiness_notes",
            "next_allowed_stage",
            "next_blocked_stage",
        )
    ):
        return False
    if any(
        type(summary[field_name]) is not bool
        or summary[field_name] is not expected_value
        for field_name, expected_value in {
            **_REQUIRED_SUMMARY_SAFETY_FIELDS,
            **_OPTIONAL_FALSE_SUMMARY_SAFETY_FIELDS,
        }.items()
    ):
        return False
    if (
        summary["source_scope"]
        != CANONICAL_MT4_DEMO_READONLY_DATA_QUALITY_SOURCE_SCOPE
        or summary["validation_stage"] != _CANONICAL_SUMMARY_VALIDATION_STAGE
        or summary["fixture_source"] != _CANONICAL_SUMMARY_FIXTURE_SOURCE
    ):
        return False

    passed = summary["passed"]
    block_reasons = summary["block_reasons"]
    warning_reasons = summary["warning_reasons"]
    if not _canonical_summary_status_is_consistent(
        passed=passed,
        status_code=summary["status_code"],
        block_reasons=block_reasons,
        warning_reasons=warning_reasons,
    ):
        return False
    if not _canonical_summary_stages_are_consistent(summary, passed=passed):
        return False
    if not _canonical_status_is_consistent(
        summary["bundle_validation_status"],
        passed=passed,
        summary_status_code=summary["status_code"],
        block_reasons=block_reasons,
        warning_reasons=warning_reasons,
    ):
        return False

    component_statuses = summary["component_statuses"]
    return (
        type(component_statuses) is dict
        and set(component_statuses) == {"canonical_data_quality_gate"}
        and component_statuses["canonical_data_quality_gate"]
        == summary["bundle_validation_status"]
        and _canonical_status_is_consistent(
            component_statuses["canonical_data_quality_gate"],
            passed=passed,
            summary_status_code=summary["status_code"],
            block_reasons=block_reasons,
            warning_reasons=warning_reasons,
        )
    )


def _canonical_summary_status_is_consistent(
    *,
    passed: bool,
    status_code: str,
    block_reasons: list[str],
    warning_reasons: list[str],
) -> bool:
    if any(
        warning not in _CANONICAL_SUMMARY_WARNING_CODES
        for warning in warning_reasons
    ):
        return False
    if status_code == _CANONICAL_SUMMARY_READY:
        return passed and not block_reasons and not warning_reasons
    if status_code == _CANONICAL_SUMMARY_READY_WITH_WARNINGS:
        return passed and not block_reasons and bool(warning_reasons)
    if status_code == _CANONICAL_SUMMARY_BLOCKED:
        return not passed and bool(block_reasons)
    if status_code == _CANONICAL_SUMMARY_INPUT_INVALID:
        return (
            not passed
            and block_reasons == ["CANONICAL_DATA_QUALITY_RESULT_INVALID"]
            and not warning_reasons
        )
    if status_code == _CANONICAL_SUMMARY_SAFE_FAILURE:
        return (
            not passed
            and block_reasons
            == ["CANONICAL_DIAGNOSTICS_ADAPTER_EXCEPTION_SANITIZED"]
            and not warning_reasons
        )
    return False


def _canonical_summary_stages_are_consistent(
    summary: dict[str, Any],
    *,
    passed: bool,
) -> bool:
    if passed:
        return (
            summary["next_allowed_stage"]
            == _CANONICAL_SUCCESS_NEXT_ALLOWED_STAGE
            and summary["next_blocked_stage"]
            == _CANONICAL_SUCCESS_NEXT_BLOCKED_STAGE
        )
    return (
        summary["next_allowed_stage"] == []
        and summary["next_blocked_stage"]
        == _CANONICAL_BLOCKED_NEXT_BLOCKED_STAGE
    )


def _canonical_status_is_consistent(
    status: Any,
    *,
    passed: bool,
    summary_status_code: str,
    block_reasons: list[str],
    warning_reasons: list[str],
) -> bool:
    if type(status) is not dict or set(status) != _CANONICAL_STATUS_KEYS:
        return False
    if type(status["passed"]) is not bool or status["passed"] is not passed:
        return False
    if (
        type(status["status_code"]) is not str
        or not _canonical_source_status_is_consistent(
            summary_status_code=summary_status_code,
            source_status_code=status["status_code"],
        )
    ):
        return False
    if (
        summary_status_code == _CANONICAL_SUMMARY_BLOCKED
        and not _canonical_blocked_source_details_are_consistent(
            source_status_code=status["status_code"],
            block_reasons=block_reasons,
            warning_reasons=warning_reasons,
        )
    ):
        return False
    if (
        not _is_strict_string_list(status["block_reasons"])
        or status["block_reasons"] != block_reasons
        or not _is_strict_string_list(status["warning_reasons"])
        or status["warning_reasons"] != warning_reasons
    ):
        return False
    return all(
        type(status[field_name]) is bool
        and status[field_name] is expected_value
        for field_name, expected_value in {
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
        }.items()
    )


def _canonical_source_status_is_consistent(
    *,
    summary_status_code: str,
    source_status_code: str,
) -> bool:
    if summary_status_code == _CANONICAL_SUMMARY_READY:
        return source_status_code == _CANONICAL_DATA_QUALITY_PASSED
    if summary_status_code == _CANONICAL_SUMMARY_READY_WITH_WARNINGS:
        return source_status_code == _CANONICAL_DATA_QUALITY_PASSED_WITH_WARNINGS
    if summary_status_code == _CANONICAL_SUMMARY_BLOCKED:
        return source_status_code in _CANONICAL_DATA_QUALITY_BLOCKED_REASON_CODES
    if summary_status_code in {
        _CANONICAL_SUMMARY_INPUT_INVALID,
        _CANONICAL_SUMMARY_SAFE_FAILURE,
    }:
        return source_status_code == _CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE
    return False


def _canonical_blocked_source_details_are_consistent(
    *,
    source_status_code: str,
    block_reasons: list[str],
    warning_reasons: list[str],
) -> bool:
    allowed_reasons = _CANONICAL_DATA_QUALITY_BLOCKED_REASON_CODES.get(
        source_status_code
    )
    if (
        allowed_reasons is None
        or len(block_reasons) != 1
        or block_reasons[0] not in allowed_reasons
    ):
        return False
    if source_status_code in _CANONICAL_DATA_QUALITY_NO_WARNING_STATUS_CODES:
        return not warning_reasons
    if source_status_code == _CANONICAL_DATA_QUALITY_REJECTED:
        return bool(warning_reasons)
    return True


def _is_strict_string_list(value: Any) -> bool:
    return type(value) is list and all(type(item) is str for item in value)


def _strict_source_scope(summary: Any) -> str:
    source_scope = _value(summary, "source_scope", "")
    return source_scope if type(source_scope) is str else ""


def _summary_source_consistency_reasons(
    *,
    source_config_status: dict[str, Any],
    is_reader_summary: bool,
) -> list[str]:
    if _source_config_selected_reader(source_config_status) is is_reader_summary:
        return []
    return [SUMMARY_SOURCE_CONFIG_MISMATCH_REASON]


def _reader_status_from_summary(
    summary: Any,
    *,
    source_config_status: dict[str, Any],
    is_reader_summary: bool,
    reader_safety_blocked: bool,
) -> str:
    if not _source_config_selected_reader(source_config_status):
        return READER_STATUS_NOT_CALLED
    if not is_reader_summary:
        return READER_STATUS_BLOCKED
    if reader_safety_blocked:
        return READER_STATUS_SAFETY_BLOCKED
    status_code = _str_value(summary, "status_code", READER_STATUS_CODE_UNAVAILABLE)
    if status_code == READER_EXCEPTION_SAFE_STATUS_CODE:
        return READER_STATUS_ERROR_SAFE
    if _bool_value(summary, "passed", default=False):
        return READER_STATUS_READY
    return READER_STATUS_BLOCKED


def _reader_passed_from_summary(
    summary: Any,
    *,
    source_config_status: dict[str, Any],
    is_reader_summary: bool,
    reader_safety_blocked: bool,
) -> bool:
    return (
        _source_config_selected_reader(source_config_status)
        and is_reader_summary
        and not reader_safety_blocked
        and _bool_value(summary, "passed", default=False)
    )


def _reader_status_code_from_summary(
    summary: Any,
    *,
    source_config_status: dict[str, Any],
    is_reader_summary: bool,
    reader_safety_blocked: bool,
) -> str:
    if not _source_config_selected_reader(source_config_status):
        return READER_STATUS_CODE_NOT_CALLED
    if not is_reader_summary:
        return READER_STATUS_CODE_UNAVAILABLE
    if reader_safety_blocked:
        return READER_STATUS_CODE_SAFETY_BLOCKED
    return _str_value(summary, "status_code", READER_STATUS_CODE_UNAVAILABLE)


def _source_config_selected_reader(source_config_status: dict[str, Any]) -> bool:
    return (
        source_config_status.get("selected_source_mode")
        == MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE
    )


def _safe_component_statuses(value: Any) -> dict[str, dict[str, Any]]:
    safe_components = {}
    if isinstance(value, dict):
        items = value.items()
    elif isinstance(value, list):
        items = (
            (component_status.get("component_name"), component_status)
            for component_status in value
            if isinstance(component_status, dict)
        )
    else:
        return {}

    for component_name, component_status in items:
        if not isinstance(component_name, str):
            continue
        if _is_unsafe_text(component_name):
            continue
        safe_components[component_name] = _safe_status_dict(component_status)
    return safe_components


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_safe_text(str(item)) for item in value]


def _safe_scalar(value: Any) -> str | None:
    if value is None:
        return None
    return _safe_text(str(value))


def _str_value(value: Any, field_name: str, default: str) -> str:
    field_value = _value(value, field_name, default)
    if field_value is None:
        return default
    return _safe_text(str(field_value))


def _bool_value(value: Any, field_name: str, *, default: bool) -> bool:
    field_value = _value(value, field_name, default)
    return field_value is True


def _value(value: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _generated_at() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_text(value: str) -> str:
    if _is_unsafe_text(value):
        return _REDACTED_UNSAFE_TEXT
    return value


def _is_unsafe_text(value: str) -> bool:
    normalized = value.casefold()
    return any(marker in normalized for marker in _FORBIDDEN_TEXT_MARKERS)


def _contains_forbidden_content(value: Any) -> bool:
    if isinstance(value, str):
        return _is_unsafe_text(value)
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and _is_unsafe_text(key):
                return True
            if _contains_forbidden_content(child):
                return True
        return False
    if isinstance(value, list | tuple | set):
        return any(_contains_forbidden_content(child) for child in value)
    if isinstance(value, bool | int | float | type(None)):
        return False
    value_dict = getattr(value, "__dict__", None)
    if isinstance(value_dict, dict):
        return _contains_forbidden_content(value_dict)
    return False


class _MissingType:
    pass


_Missing = _MissingType()
