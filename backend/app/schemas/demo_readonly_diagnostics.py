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

_FORBIDDEN_RESPONSE_KEYS = {
    "order_id",
    "ticket",
    "execute_trade",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
    "auto_trade",
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
    "override_risk",
    "bypass_gate",
    "ea_command",
    "account_number",
    "password",
    "credential",
    "token",
    "secret",
    "login",
    "raw_payload",
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
}

_REDACTED_UNSAFE_TEXT = "[redacted unsafe content]"


class DemoReadonlyDiagnosticsResponse(BaseModel):
    api_version: str
    endpoint: str
    generated_at: str
    passed: bool
    status_code: str
    source_scope: str
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
) -> DemoReadonlyDiagnosticsResponse:
    safety_reasons = _safety_violation_reasons(summary)
    passed = _bool_value(summary, "passed", default=False)

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


def _safe_component_statuses(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}

    safe_components = {}
    for component_name, component_status in value.items():
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
