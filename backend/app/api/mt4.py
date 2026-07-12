from typing import Any

from fastapi import APIRouter

from app.schemas.mt4_diagnostics import Mt4DiagnosticsResponse
from app.services.data_quality_gate import (
    BLOCKED_BY_GATE_V0,
    CANONICAL_MT4_BUNDLE_V1_WARNING_CODES,
    DATA_QUALITY_PASSED,
)
from app.services.demo_readonly_canonical_docs_fixture_diagnostics_summary_producer import (
    build_demo_readonly_canonical_docs_fixture_diagnostics_summary,
)
from app.services.mt4_demo_readonly_source_config_guard import (
    DOCS_FIXTURE_ONLY_SOURCE_MODE,
    MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY,
    validate_demo_readonly_source_config,
)
from app.services.mt4_diagnostics_legacy_compatibility_adapter import (
    LEGACY_NOTE,
    LEGACY_STAGE,
    adapt_canonical_summary_to_legacy_mt4_diagnostics_response,
)

router = APIRouter(prefix="/api/mt4", tags=["mt4"])

_SOURCE_CONFIG_GUARD_KEYS = frozenset(
    {
        "passed",
        "status_code",
        "selected_source_mode",
        "default_source_mode",
        "source_status",
        "bridge_dir_status",
        "request_override_allowed",
        "block_reasons",
        "warning_reasons",
        "notes",
        "read_only",
        "demo_only",
        "is_tradable",
        "can_execute",
        "is_trading_permission",
        "is_execution_instruction",
        "allowed_to_call_ea",
        "allowed_to_modify_risk",
    }
)
_SOURCE_CONFIG_SAFETY_FIELDS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}
_SOURCE_CONFIG_NOTES = (
    "source config guard validates caller-provided server-side config only",
    "source_mode readiness is not a trading permission",
)
_LEGACY_RESPONSE_KEYS = frozenset(Mt4DiagnosticsResponse.model_fields)
_LEGACY_DETAIL_FIELDS = (
    "read_summary",
    "metadata_status",
    "freshness_status",
    "gate_v0_result",
    "required_fields_status",
    "field_types_status",
    "numeric_ranges_status",
    "cross_field_status",
)
_UNAVAILABLE_DETAIL = {
    "available": False,
    "status": "unavailable",
    "passed": False,
}


@router.get("/diagnostics", response_model=Mt4DiagnosticsResponse)
def get_mt4_diagnostics() -> Mt4DiagnosticsResponse:
    canonical_summary: object = None
    source_ready = False
    try:
        guard_result = validate_demo_readonly_source_config({})
        if _guard_allows_default_docs_fixture(guard_result):
            canonical_summary = (
                build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
            )
            source_ready = True
        else:
            canonical_summary = guard_result
    except Exception:
        canonical_summary = None

    try:
        legacy_result = adapt_canonical_summary_to_legacy_mt4_diagnostics_response(
            canonical_summary=canonical_summary
        )
        if not _legacy_result_is_safe(
            legacy_result,
            success_allowed=source_ready,
        ):
            return _fixed_blocked_response()
        return Mt4DiagnosticsResponse.model_validate(legacy_result)
    except Exception:
        return _fixed_blocked_response()


def _guard_allows_default_docs_fixture(result: object) -> bool:
    if type(result) is not dict or frozenset(result) != _SOURCE_CONFIG_GUARD_KEYS:
        return False
    if any(type(key) is not str for key in result):
        return False
    if (
        result["passed"] is not True
        or type(result["status_code"]) is not str
        or result["status_code"]
        != MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY
        or type(result["selected_source_mode"]) is not str
        or result["selected_source_mode"] != DOCS_FIXTURE_ONLY_SOURCE_MODE
        or type(result["default_source_mode"]) is not str
        or result["default_source_mode"] != DOCS_FIXTURE_ONLY_SOURCE_MODE
        or type(result["source_status"]) is not str
        or result["source_status"] != "docs_fixture_only_ready"
        or type(result["bridge_dir_status"]) is not str
        or result["bridge_dir_status"] != "not_required"
        or result["request_override_allowed"] is not False
        or type(result["block_reasons"]) is not list
        or bool(result["block_reasons"])
        or type(result["warning_reasons"]) is not list
        or bool(result["warning_reasons"])
        or not _strict_string_list(result["notes"])
        or tuple(result["notes"]) != _SOURCE_CONFIG_NOTES
    ):
        return False
    return all(
        result[field] is expected
        for field, expected in _SOURCE_CONFIG_SAFETY_FIELDS.items()
    )


def _strict_string_list(value: object) -> bool:
    return (
        type(value) is list
        and bool(value)
        and all(type(item) is str and bool(item.strip()) for item in value)
        and len(value) == len(set(value))
    )


def _legacy_result_is_safe(
    result: object,
    *,
    success_allowed: bool,
) -> bool:
    if type(result) is not dict or frozenset(result) != _LEGACY_RESPONSE_KEYS:
        return False
    if any(type(key) is not str for key in result):
        return False
    if (
        type(result["stage"]) is not str
        or result["stage"] != LEGACY_STAGE
        or type(result["note"]) is not str
        or result["note"] != LEGACY_NOTE
        or type(result["status_code"]) is not str
        or type(result["data_quality_passed"]) is not bool
        or type(result["can_proceed_to_read_only_analysis"]) is not bool
        or result["is_tradable"] is not False
    ):
        return False

    passed = result["data_quality_passed"]
    if passed and not success_allowed:
        return False
    if result["can_proceed_to_read_only_analysis"] is not passed:
        return False
    if result["status_code"] != (
        DATA_QUALITY_PASSED if passed else BLOCKED_BY_GATE_V0
    ):
        return False
    if any(
        not _is_unavailable_detail(result[field])
        for field in _LEGACY_DETAIL_FIELDS
    ):
        return False

    gate_result = result["gate_v1_result"]
    if type(gate_result) is not dict or frozenset(gate_result) != frozenset(
        {*_UNAVAILABLE_DETAIL, "warning_reasons"}
    ):
        return False
    if any(type(key) is not str for key in gate_result):
        return False
    if not _is_unavailable_detail(
        {key: gate_result[key] for key in _UNAVAILABLE_DETAIL}
    ):
        return False
    warnings = gate_result["warning_reasons"]
    return (
        type(warnings) is list
        and all(
            type(warning) is str
            and warning in CANONICAL_MT4_BUNDLE_V1_WARNING_CODES
            for warning in warnings
        )
        and len(warnings) == len(set(warnings))
        and (passed or not warnings)
    )


def _is_unavailable_detail(value: object) -> bool:
    return (
        type(value) is dict
        and frozenset(value) == frozenset(_UNAVAILABLE_DETAIL)
        and all(type(key) is str for key in value)
        and value["available"] is False
        and type(value["status"]) is str
        and value["status"] == "unavailable"
        and value["passed"] is False
    )


def _fixed_blocked_response() -> Mt4DiagnosticsResponse:
    unavailable = {
        key: _unavailable_detail()
        for key in (
            "read_summary",
            "metadata_status",
            "freshness_status",
            "gate_v0_result",
            "required_fields_status",
            "field_types_status",
            "numeric_ranges_status",
            "cross_field_status",
            "gate_v1_result",
        )
    }
    unavailable["gate_v1_result"]["warning_reasons"] = []
    return Mt4DiagnosticsResponse(
        stage=LEGACY_STAGE,
        status_code=BLOCKED_BY_GATE_V0,
        data_quality_passed=False,
        can_proceed_to_read_only_analysis=False,
        is_tradable=False,
        note=LEGACY_NOTE,
        **unavailable,
    )


def _unavailable_detail() -> dict[str, Any]:
    return {
        "available": False,
        "status": "unavailable",
        "passed": False,
    }
