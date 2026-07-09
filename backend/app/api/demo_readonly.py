from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.demo_readonly_diagnostics import (
    DemoReadonlyDiagnosticsResponse,
    demo_readonly_diagnostics_internal_error_response,
    demo_readonly_diagnostics_response,
)
from app.services.demo_readonly_docs_fixture_validation_summary import (
    summarize_demo_readonly_docs_fixture_validation,
)
from app.services.mt4_demo_readonly_source_config_guard import (
    validate_demo_readonly_source_config,
)
from app.services.mt4_demo_readonly_reader import (
    read_mt4_demo_readonly_source_summary_from_dir,
)
from app.services.read_only_diagnostics_explainer import (
    READONLY_EXPLANATION_BLOCKED,
    READONLY_EXPLANATION_INPUT_INVALID,
    READONLY_EXPLANATION_READY,
    READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION,
    READONLY_EXPLANATION_SOURCE_ERROR,
    explain_demo_readonly_docs_fixture_diagnostics,
)


router = APIRouter(prefix="/api/demo-readonly", tags=["demo-readonly"])

DEMO_READONLY_EXPLANATION_ENDPOINT = "/api/demo-readonly/explanation"
READONLY_EXPLANATION_API_ERROR = "READONLY_EXPLANATION_API_ERROR"
MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE = (
    "mt4_demo_readonly_file_bridge_enabled"
)
MT4_DEMO_READONLY_FILE_BRIDGE_READY = "mt4_demo_readonly_file_bridge_ready"
MT4_DEMO_READONLY_BRIDGE_DIR_CONFIG_KEY = "mt4_demo_readonly_bridge_dir"
_SERVER_SIDE_DEMO_READONLY_SOURCE_CONFIG: dict[str, object] = {}
_SAFE_SOURCE_CONFIG_GUARD_EXCEPTION_RESULT: dict[str, object] = {
    "passed": False,
    "status_code": "SOURCE_CONFIG_GUARD_EXCEPTION_SANITIZED",
    "selected_source_mode": "docs_fixture_only",
    "source_status": "source_config_safety_blocked",
    "block_reasons": ["source_config_guard_exception_sanitized"],
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
_SAFE_SOURCE_CONFIG_SERVER_MISMATCH_RESULT: dict[str, object] = {
    "passed": False,
    "status_code": "SOURCE_CONFIG_SERVER_MISMATCH_BLOCKED",
    "selected_source_mode": "docs_fixture_only",
    "source_status": "source_config_safety_blocked",
    "block_reasons": ["source_config_server_mismatch_blocked"],
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

_ALLOWED_EXPLANATION_STATUS_CODES = {
    READONLY_EXPLANATION_READY,
    READONLY_EXPLANATION_BLOCKED,
    READONLY_EXPLANATION_INPUT_INVALID,
    READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION,
    READONLY_EXPLANATION_SOURCE_ERROR,
    READONLY_EXPLANATION_API_ERROR,
}

_EXPLANATION_RESPONSE_FIELDS = (
    "passed",
    "status_code",
    "report_version",
    "report_type",
    "generated_at",
    "source_scope",
    "input_status_code",
    "input_passed",
    "explanation_scope",
    "overall_explanation",
    "status_explanation",
    "component_explanations",
    "blocker_explanations",
    "warning_explanations",
    "readiness_explanation",
    "next_allowed_stage_explanation",
    "next_blocked_stage_explanation",
    "user_safe_next_steps",
    "user_forbidden_actions",
    "unknowns",
    "safety_flags",
    "block_reasons",
    "warning_reasons",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
    "notes",
)

_SAFE_EXPLANATION_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}

_FORBIDDEN_EXPLANATION_KEYS = {
    "raw_payload",
    "account_snapshot",
    "positions_order_history",
    "market_symbol",
    "raw_account_snapshot",
    "raw_positions_order_history",
    "raw_market_symbol",
    "account_number",
    "login",
    "password",
    "credential",
    "token",
    "secret",
    "api_key",
    "key",
    "traceback",
    "stack_trace",
    "system_path",
    "order_id",
    "ticket",
    "buy",
    "sell",
    "open",
    "close",
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
    "trade_signal",
    "trading_action",
}

_FORBIDDEN_EXPLANATION_TEXT_MARKERS = {
    "raw_payload",
    "raw_account_snapshot",
    "raw_positions_order_history",
    "raw_market_symbol",
    "account_number",
    "login",
    "password",
    "credential",
    "token",
    "secret",
    "api_key",
    "key",
    "traceback",
    "stack_trace",
    "system_path",
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
    "trade_signal",
    "trading_action",
    "traceback",
    "stack trace",
    "raw payload",
    ".env",
    "c:\\",
    "\\users\\",
    "/users/",
    "/home/",
    ".py",
    "site-packages",
    "买入",
    "卖出",
    "开仓",
    "平仓",
    "建议手数",
    "可以交易",
    "允许交易",
    "自动下单",
    "自动交易",
    "执行交易",
    "下单指令",
    "风控放行",
    "绕过风控",
    "should buy",
    "should sell",
    "buy",
    "sell",
    "open position",
    "close position",
    "execute trade",
    "allow trade",
    "can trade",
    "suggested lot",
}

_REDACTED_EXPLANATION_TEXT = "存在不适合展示的原始内容，API 层已隐藏。"


@router.get("/diagnostics", response_model=DemoReadonlyDiagnosticsResponse)
def get_demo_readonly_diagnostics() -> (
    DemoReadonlyDiagnosticsResponse | JSONResponse
):
    server_source_config = _get_demo_readonly_server_source_config()
    source_config_guard_result = _safe_source_config_guard_result(
        server_source_config
    )
    source_config_guard_result = _safe_source_config_guard_result_for_server_config(
        source_config_guard_result=source_config_guard_result,
        server_source_config=server_source_config,
    )

    try:
        summary = _demo_readonly_diagnostics_summary(
            source_config_guard_result=source_config_guard_result,
            server_source_config=server_source_config,
        )
    except Exception:
        safe_response = demo_readonly_diagnostics_internal_error_response()
        return JSONResponse(
            status_code=500,
            content=safe_response.model_dump(),
        )

    return demo_readonly_diagnostics_response(
        summary,
        source_config_guard_result=source_config_guard_result,
    )


@router.get("/explanation")
def get_demo_readonly_explanation() -> dict[str, Any]:
    try:
        report = explain_demo_readonly_docs_fixture_diagnostics()
    except Exception:
        return _safe_explanation_api_error_response()

    return _safe_explanation_response(report)


def _get_demo_readonly_server_source_config() -> dict[str, object]:
    return dict(_SERVER_SIDE_DEMO_READONLY_SOURCE_CONFIG)


def _safe_source_config_guard_result(
    server_source_config: dict[str, object],
) -> dict[str, object]:
    try:
        return validate_demo_readonly_source_config(server_source_config)
    except Exception:
        return dict(_SAFE_SOURCE_CONFIG_GUARD_EXCEPTION_RESULT)


def _safe_source_config_guard_result_for_server_config(
    *,
    source_config_guard_result: dict[str, object],
    server_source_config: dict[str, object],
) -> dict[str, object]:
    if (
        source_config_guard_result.get("selected_source_mode")
        != MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE
    ):
        return source_config_guard_result
    if _server_config_explicitly_selects_reader(server_source_config):
        return source_config_guard_result
    return dict(_SAFE_SOURCE_CONFIG_SERVER_MISMATCH_RESULT)


def _demo_readonly_diagnostics_summary(
    *,
    source_config_guard_result: dict[str, object],
    server_source_config: dict[str, object],
) -> Any:
    if not _should_call_mt4_demo_readonly_reader(
        source_config_guard_result=source_config_guard_result,
        server_source_config=server_source_config,
    ):
        return summarize_demo_readonly_docs_fixture_validation()

    bridge_dir = server_source_config.get(MT4_DEMO_READONLY_BRIDGE_DIR_CONFIG_KEY)
    try:
        return read_mt4_demo_readonly_source_summary_from_dir(bridge_dir)
    except Exception:
        return _safe_mt4_demo_readonly_reader_exception_summary()


def _should_call_mt4_demo_readonly_reader(
    *,
    source_config_guard_result: dict[str, object],
    server_source_config: dict[str, object],
) -> bool:
    return (
        source_config_guard_result.get("passed") is True
        and source_config_guard_result.get("selected_source_mode")
        == MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE
        and source_config_guard_result.get("source_status")
        == MT4_DEMO_READONLY_FILE_BRIDGE_READY
        and source_config_guard_result.get("read_only") is True
        and source_config_guard_result.get("demo_only") is True
        and source_config_guard_result.get("is_tradable") is False
        and source_config_guard_result.get("can_execute") is False
        and source_config_guard_result.get("is_trading_permission") is False
        and source_config_guard_result.get("is_execution_instruction") is False
        and source_config_guard_result.get("allowed_to_call_ea") is False
        and source_config_guard_result.get("allowed_to_modify_risk") is False
        and _server_config_explicitly_selects_reader(server_source_config)
    )


def _server_config_explicitly_selects_reader(
    server_source_config: dict[str, object],
) -> bool:
    return (
        server_source_config.get("source_mode")
        == MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE
        and server_source_config.get("mt4_demo_readonly_file_bridge_enabled") is True
        and server_source_config.get("allow_request_override", False) is False
        and isinstance(
            server_source_config.get(MT4_DEMO_READONLY_BRIDGE_DIR_CONFIG_KEY),
            str,
        )
    )


def _safe_mt4_demo_readonly_reader_exception_summary() -> dict[str, Any]:
    return {
        "passed": False,
        "status_code": "MT4_DEMO_READONLY_READER_EXCEPTION_SAFE",
        "source_mode": MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
        "source_scope": "mt4_demo_readonly_reader_safe_summary_only",
        "validation_stage": "demo_readonly_diagnostics_reader",
        "fixture_source": "mt4_demo_readonly_file_bridge",
        "reader_status": "error_safe",
        "reader_block_reasons": ["READER_EXCEPTION_SANITIZED"],
        "reader_warning_reasons": [],
        "bundle_validation_status": {
            "passed": False,
            "status_code": "MT4_DEMO_READONLY_READER_EXCEPTION_SAFE",
            "block_reasons": ["READER_EXCEPTION_SANITIZED"],
            "warning_reasons": [],
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
        },
        "component_statuses": {},
        "block_reasons": ["reader exception sanitized"],
        "warning_reasons": [],
        "readiness_notes": [
            "Reader failed safely.",
            "Diagnostics remain read-only.",
            "Diagnostics are not trading permission.",
            "Diagnostics do not generate trading signals.",
        ],
        "next_allowed_stage": [],
        "next_blocked_stage": ["execution_chain"],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }


def _safe_explanation_response(report: Any) -> dict[str, Any]:
    safety_reasons = _explanation_safety_violation_reasons(report)
    safe_report = _safe_explanation_output_value(report)
    response = _default_explanation_response()

    if isinstance(safe_report, dict):
        for field_name in _EXPLANATION_RESPONSE_FIELDS:
            if field_name in safe_report:
                response[field_name] = safe_report[field_name]

    response["passed"] = response.get("passed") is True
    status_code = str(response.get("status_code") or "")
    if status_code not in _ALLOWED_EXPLANATION_STATUS_CODES:
        safety_reasons.append("Unsafe explanation status code was blocked.")

    if safety_reasons:
        response["passed"] = False
        response["status_code"] = READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION
        response["block_reasons"] = [
            *_safe_explanation_list(response.get("block_reasons")),
            *safety_reasons,
        ]

    response.update(_SAFE_EXPLANATION_FLAGS)
    response["safety_flags"] = dict(_SAFE_EXPLANATION_FLAGS)

    return _safe_explanation_output_value(response)


def _safe_explanation_api_error_response() -> dict[str, Any]:
    response = _default_explanation_response()
    response["passed"] = False
    response["status_code"] = READONLY_EXPLANATION_API_ERROR
    response["overall_explanation"] = (
        "只读解释 API 发生安全失败，未暴露内部细节。"
    )
    response["status_explanation"] = (
        "当前仍是 demo-only / read-only 状态，非交易许可，非执行指令。"
    )
    response["block_reasons"] = ["Explanation API failed safely."]
    response["blocker_explanations"] = ["只读解释 API 安全失败。"]
    response["notes"] = [
        "只读解释 API 只返回安全失败摘要。",
        "非交易许可，非执行指令。",
        "交易能力禁用，执行能力禁用。",
    ]
    response.update(_SAFE_EXPLANATION_FLAGS)
    response["safety_flags"] = dict(_SAFE_EXPLANATION_FLAGS)
    return response


def _default_explanation_response() -> dict[str, Any]:
    response: dict[str, Any] = {
        "passed": False,
        "status_code": READONLY_EXPLANATION_INPUT_INVALID,
        "report_version": "1.0",
        "report_type": "read_only_explanation_report",
        "generated_at": _generated_at(),
        "source_scope": "demo_readonly_diagnostics_api",
        "input_status_code": "STATUS_UNAVAILABLE",
        "input_passed": False,
        "explanation_scope": "demo_readonly_diagnostics_summary_only",
        "overall_explanation": "当前只读解释不可用，API 返回安全失败摘要。",
        "status_explanation": "解释 API 不会进入任何交易或执行链路。",
        "component_explanations": [],
        "blocker_explanations": ["当前没有可展示的阻断原因。"],
        "warning_explanations": ["当前没有可展示的警告原因。"],
        "readiness_explanation": ["当前没有可展示的 readiness 说明。"],
        "next_allowed_stage_explanation": [
            "当前没有可展示的下一阶段流程提示。"
        ],
        "next_blocked_stage_explanation": [
            "当前没有可展示的后续阶段限制。"
        ],
        "user_safe_next_steps": [
            "查看只读解释",
            "查看只读诊断",
            "查看阻断原因",
            "查看警告原因",
            "进行安全回归检查",
        ],
        "user_forbidden_actions": [
            "任何交易性操作仍被禁止",
            "任何执行链路仍被禁止",
            "任何 MT4 或 EA 操作入口仍被禁止",
        ],
        "unknowns": [],
        "safety_flags": dict(_SAFE_EXPLANATION_FLAGS),
        "block_reasons": [],
        "warning_reasons": [],
        "notes": [
            "只读解释 API 只解释安全摘要。",
            "非交易许可，非执行指令。",
            "交易能力禁用，执行能力禁用。",
        ],
    }
    response.update(_SAFE_EXPLANATION_FLAGS)
    return response


def _explanation_safety_violation_reasons(report: Any) -> list[str]:
    reasons = []
    if not isinstance(report, dict):
        reasons.append("Explanation report was not a JSON object.")
        return reasons

    for field_name, expected_value in _SAFE_EXPLANATION_FLAGS.items():
        if report.get(field_name) is not expected_value:
            reasons.append(f"Unsafe safety field value: {field_name}.")

    safety_flags = report.get("safety_flags")
    if isinstance(safety_flags, dict):
        for field_name, expected_value in _SAFE_EXPLANATION_FLAGS.items():
            if safety_flags.get(field_name) is not expected_value:
                reasons.append(f"Unsafe safety_flags value: {field_name}.")

    if _contains_explanation_forbidden_content(report):
        reasons.append("Unsafe explanation response content was blocked.")

    return reasons


def _safe_explanation_output_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _safe_explanation_output_value(child)
            for key, child in value.items()
            if not _is_forbidden_explanation_key(key)
        }
    if isinstance(value, list):
        return [_safe_explanation_output_value(child) for child in value]
    if isinstance(value, tuple):
        return [_safe_explanation_output_value(child) for child in value]
    if isinstance(value, str):
        return _safe_explanation_text(value)
    return value


def _safe_explanation_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_safe_explanation_text(str(item)) for item in value]


def _safe_explanation_text(value: str) -> str:
    if _is_unsafe_explanation_text(value):
        return _REDACTED_EXPLANATION_TEXT
    return value


def _contains_explanation_forbidden_content(value: Any) -> bool:
    if isinstance(value, str):
        return _is_unsafe_explanation_text(value)
    if isinstance(value, dict):
        for key, child in value.items():
            if _is_forbidden_explanation_key(key):
                return True
            if _contains_explanation_forbidden_content(child):
                return True
        return False
    if isinstance(value, list | tuple | set):
        return any(_contains_explanation_forbidden_content(child) for child in value)
    if isinstance(value, bool | int | float | type(None)):
        return False

    value_dict = getattr(value, "__dict__", None)
    if isinstance(value_dict, dict):
        return _contains_explanation_forbidden_content(value_dict)
    return False


def _is_forbidden_explanation_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.casefold() in {item.casefold() for item in _FORBIDDEN_EXPLANATION_KEYS}


def _is_unsafe_explanation_text(value: str) -> bool:
    normalized = value.casefold()
    return any(
        marker.casefold() in normalized
        for marker in _FORBIDDEN_EXPLANATION_TEXT_MARKERS
    )


def _generated_at() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
