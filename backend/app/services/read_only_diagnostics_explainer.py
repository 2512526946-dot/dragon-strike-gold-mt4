from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.services import demo_readonly_docs_fixture_validation_summary as summary_service


READONLY_EXPLANATION_READY = "READONLY_EXPLANATION_READY"
READONLY_EXPLANATION_BLOCKED = "READONLY_EXPLANATION_BLOCKED"
READONLY_EXPLANATION_INPUT_INVALID = "READONLY_EXPLANATION_INPUT_INVALID"
READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION = (
    "READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION"
)

REPORT_VERSION = "1.0"
REPORT_TYPE = "read_only_explanation_report"
EXPLANATION_SCOPE = "demo_readonly_diagnostics_summary_only"
DEFAULT_SOURCE_SCOPE = "demo_readonly_diagnostics_api"

KNOWN_COMPONENTS = (
    "account_snapshot",
    "positions_order_history",
    "market_symbol",
    "bundle_validation",
    "diagnostics_api",
    "frontend_dashboard_safety",
)

REQUIRED_FIELDS = (
    "passed",
    "status_code",
    "source_scope",
    "component_statuses",
    "block_reasons",
    "warning_reasons",
    "readiness_notes",
    "next_allowed_stage",
    "next_blocked_stage",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
)

REQUIRED_SAFETY_VALUES = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
}

OPTIONAL_SAFETY_VALUES = {
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}

SAFE_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}

FORBIDDEN_FIELDS = {
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
    "order_id",
    "ticket",
    "buy",
    "sell",
    "buy_now",
    "sell_now",
    "should_buy",
    "should_sell",
    "open_position",
    "close_position",
    "execute_trade",
    "can_trade",
    "allow_trade",
    "suggested_lot",
    "final_lot",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
    "ea_command",
    "auto_trade",
    "trade_signal",
    "trading_action",
    "override_risk",
    "bypass_gate",
}

FORBIDDEN_TEXT_MARKERS = FORBIDDEN_FIELDS | {
    "traceback",
    "stack trace",
    ".env",
    "c:\\",
    "\\users\\",
    "/users/",
    "建议手数",
    "可以交易",
    "允许交易",
    "自动下单",
    "执行交易",
    "下单指令",
    "风控放行",
    "绕过风控",
}

SAFE_NEXT_STEPS = [
    "查看只读诊断",
    "刷新只读诊断",
    "检查数据校验状态",
    "查看阻断原因",
    "查看警告原因",
    "等待下一阶段开发",
    "进行文档审查",
    "进行安全回归检查",
    "进行 Dashboard 展示检查",
]

FORBIDDEN_ACTIONS = [
    "任何交易性操作仍被禁止",
    "任何执行链路仍被禁止",
    "任何 MT4 或 EA 操作入口仍被禁止",
    "任何真实账户或模拟账号连接仍被禁止",
    "任何风控、仓位或计划生成入口仍被禁止",
]


class _MissingType:
    pass


_Missing = _MissingType()


def explain_readonly_diagnostics_summary(summary: dict[str, Any] | Any) -> dict[str, Any]:
    missing_fields = _missing_fields(summary)
    if missing_fields:
        return _base_report(
            passed=False,
            status_code=READONLY_EXPLANATION_INPUT_INVALID,
            summary=summary,
            unknowns=[f"Missing required summary field: {field}." for field in missing_fields],
            block_reasons=["Diagnostics summary is incomplete for read-only explanation."],
            overall_explanation=(
                "当前只读诊断摘要缺少关键字段，只能返回安全失败解释。"
            ),
            status_explanation=(
                "输入摘要不完整；解释层不会补全、读取底层数据或进入执行链路。"
            ),
        )

    safety_reasons = _safety_violation_reasons(summary)
    if safety_reasons:
        safe_input_block_reasons = _safe_text_list(_value(summary, "block_reasons"))
        return _base_report(
            passed=False,
            status_code=READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION,
            summary=summary,
            block_reasons=[*safe_input_block_reasons, *safety_reasons],
            overall_explanation=(
                "输入摘要包含不安全安全字段，解释层已强制回到只读安全状态。"
            ),
            status_explanation=(
                "安全字段异常只会阻断解释输出，不会生成交易许可或执行指令。"
            ),
        )

    input_passed = _bool_value(summary, "passed")
    if input_passed:
        return _base_report(
            passed=True,
            status_code=READONLY_EXPLANATION_READY,
            summary=summary,
            block_reasons=[],
            overall_explanation=(
                "当前只读诊断摘要可解释；这不是交易许可，不是执行指令，"
                "交易能力禁用，执行能力禁用，当前仍不能进入任何交易或执行链路。"
            ),
            status_explanation=(
                "passed=true 只代表只读诊断摘要可用于展示和解释，不代表任何操作许可。"
            ),
        )

    block_reasons = _safe_text_list(_value(summary, "block_reasons"))
    return _base_report(
        passed=False,
        status_code=READONLY_EXPLANATION_BLOCKED,
        summary=summary,
        block_reasons=block_reasons,
        overall_explanation=(
            "当前只读诊断存在阻断；阻断只影响诊断、展示和流程。"
        ),
        status_explanation=(
            "阻断不是交易指令，不能据此进行任何交易或执行操作。"
        ),
    )


def explain_demo_readonly_docs_fixture_diagnostics() -> dict[str, Any]:
    try:
        summary = summary_service.summarize_demo_readonly_docs_fixture_validation()
    except Exception:
        return _base_report(
            passed=False,
            status_code=READONLY_EXPLANATION_INPUT_INVALID,
            summary={},
            unknowns=["Summary service failed safely."],
            block_reasons=["Summary service failed safely."],
            overall_explanation=(
                "只读诊断摘要服务失败，解释层返回安全失败说明。"
            ),
            status_explanation=(
                "解释层不会泄漏异常细节，不会读取日志或数据库，也不会进入执行链路。"
            ),
        )

    return explain_readonly_diagnostics_summary(summary)


def _base_report(
    *,
    passed: bool,
    status_code: str,
    summary: Any,
    block_reasons: list[str] | None = None,
    unknowns: list[str] | None = None,
    overall_explanation: str,
    status_explanation: str,
) -> dict[str, Any]:
    safe_block_reasons = _safe_text_list(block_reasons or [])
    safe_warning_reasons = _safe_text_list(_value(summary, "warning_reasons"))
    safe_unknowns = _safe_text_list(unknowns or [])
    source_scope = _safe_text(_str_value(summary, "source_scope", DEFAULT_SOURCE_SCOPE))
    input_status_code = _safe_text(_str_value(summary, "status_code", "STATUS_UNAVAILABLE"))
    input_passed = _bool_value(summary, "passed")
    component_explanations = _component_explanations(summary)

    return {
        "passed": passed,
        "status_code": status_code,
        "report_version": REPORT_VERSION,
        "report_type": REPORT_TYPE,
        "generated_at": _generated_at(),
        "source_scope": source_scope,
        "input_status_code": input_status_code,
        "input_passed": input_passed,
        "explanation_scope": EXPLANATION_SCOPE,
        "overall_explanation": overall_explanation,
        "status_explanation": status_explanation,
        "component_explanations": component_explanations,
        "blocker_explanations": _explain_reasons(
            safe_block_reasons,
            empty_text="当前没有可展示的阻断原因。",
            prefix="阻断原因",
        ),
        "warning_explanations": _explain_reasons(
            safe_warning_reasons,
            empty_text="当前没有可展示的警告原因。",
            prefix="警告原因",
        ),
        "readiness_explanation": _readiness_explanation(summary),
        "next_allowed_stage_explanation": _next_allowed_stage_explanation(summary),
        "next_blocked_stage_explanation": _next_blocked_stage_explanation(summary),
        "user_safe_next_steps": list(SAFE_NEXT_STEPS),
        "user_forbidden_actions": list(FORBIDDEN_ACTIONS),
        "unknowns": safe_unknowns,
        "safety_flags": dict(SAFE_FLAGS),
        "block_reasons": safe_block_reasons,
        "warning_reasons": safe_warning_reasons,
        **SAFE_FLAGS,
        "notes": [
            "只读诊断解释层只解释安全摘要。",
            "非交易许可，非执行指令。",
            "交易能力禁用，执行能力禁用。",
        ],
    }


def _component_explanations(summary: Any) -> list[dict[str, Any]]:
    components = _value(summary, "component_statuses")
    bundle_status = _value(summary, "bundle_validation_status")

    result = []
    for component_name in KNOWN_COMPONENTS:
        if component_name == "bundle_validation":
            component_status = bundle_status
        elif component_name == "diagnostics_api":
            component_status = {
                "passed": _bool_value(summary, "passed"),
                "status_code": _str_value(summary, "status_code", "STATUS_UNAVAILABLE"),
                "block_reasons": _value(summary, "block_reasons"),
                "warning_reasons": _value(summary, "warning_reasons"),
            }
        elif component_name == "frontend_dashboard_safety":
            component_status = {
                "passed": True,
                "status_code": "FRONTEND_DASHBOARD_SAFETY_BOUNDARY_DOCUMENTED",
                "block_reasons": [],
                "warning_reasons": [],
            }
        elif isinstance(components, dict):
            component_status = components.get(component_name)
        else:
            component_status = None

        result.append(_component_explanation(component_name, component_status))
    return result


def _component_explanation(
    component_name: str,
    component_status: Any,
) -> dict[str, Any]:
    status = _component_status_label(component_status)
    block_reasons = _safe_text_list(_value(component_status, "block_reasons"))
    warning_reasons = _safe_text_list(_value(component_status, "warning_reasons"))
    status_code = _safe_text(_str_value(component_status, "status_code", "STATUS_UNAVAILABLE"))

    return {
        "component_name": component_name,
        "status": status,
        "status_code": status_code,
        "plain_language_summary": (
            f"{component_name} 当前处于 {status} 只读诊断状态。"
        ),
        "block_reasons_explained": _explain_reasons(
            block_reasons,
            empty_text="该组件没有可展示的阻断原因。",
            prefix=f"{component_name} 阻断原因",
        ),
        "warning_reasons_explained": _explain_reasons(
            warning_reasons,
            empty_text="该组件没有可展示的警告原因。",
            prefix=f"{component_name} 警告原因",
        ),
        "user_impact": "只影响只读诊断展示和阶段流程，不影响任何执行能力。",
        "safe_next_step": "查看只读诊断或进行安全回归检查。",
        "forbidden_interpretation": (
            "不能把该组件状态解释成交易许可或执行指令。"
        ),
    }


def _component_status_label(component_status: Any) -> str:
    if not isinstance(component_status, dict):
        return "unknown"
    if component_status.get("passed") is True:
        warning_reasons = _safe_text_list(component_status.get("warning_reasons"))
        return "warning" if warning_reasons else "passed"
    block_reasons = _safe_text_list(component_status.get("block_reasons"))
    return "blocked" if block_reasons else "unknown"


def _explain_reasons(
    reasons: list[str],
    *,
    empty_text: str,
    prefix: str,
) -> list[str]:
    if not reasons:
        return [empty_text]
    return [f"{prefix}: {reason}" for reason in reasons]


def _readiness_explanation(summary: Any) -> list[str]:
    readiness_notes = _safe_text_list(_value(summary, "readiness_notes"))
    if not readiness_notes:
        return ["当前没有可展示的 readiness 说明。"]
    return [
        f"只读 readiness 说明：{note}" for note in readiness_notes
    ]


def _next_allowed_stage_explanation(summary: Any) -> list[str]:
    stages = _safe_text_list(_value(summary, "next_allowed_stage"))
    if not stages:
        return ["当前没有可展示的下一阶段流程提示。"]
    return [
        f"{stage} 是流程提示，不是交易许可。"
        for stage in stages
    ]


def _next_blocked_stage_explanation(summary: Any) -> list[str]:
    stages = _safe_text_list(_value(summary, "next_blocked_stage"))
    if not stages:
        return ["当前没有可展示的后续阶段限制。"]
    return [
        f"仍存在后续阶段限制：{stage}。这不是执行指令。"
        for stage in stages
    ]


def _missing_fields(summary: Any) -> list[str]:
    return [
        field_name
        for field_name in REQUIRED_FIELDS
        if _value(summary, field_name, _Missing) is _Missing
    ]


def _safety_violation_reasons(summary: Any) -> list[str]:
    reasons = []
    for field_name, expected_value in REQUIRED_SAFETY_VALUES.items():
        actual_value = _value(summary, field_name, _Missing)
        if actual_value is not expected_value:
            reasons.append(f"Unsafe safety field value: {field_name}.")

    for field_name, expected_value in OPTIONAL_SAFETY_VALUES.items():
        actual_value = _value(summary, field_name, _Missing)
        if actual_value is not _Missing and actual_value is not expected_value:
            reasons.append(f"Unsafe safety field value: {field_name}.")

    if _contains_forbidden_content(summary):
        reasons.append("Unsafe summary content was blocked.")

    return reasons


def _safe_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_safe_text(str(item)) for item in value]


def _safe_text(value: str) -> str:
    if _is_unsafe_text(value):
        return "[redacted unsafe content]"
    return value


def _is_unsafe_text(value: str) -> bool:
    normalized = value.casefold()
    return any(marker.casefold() in normalized for marker in FORBIDDEN_TEXT_MARKERS)


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


def _bool_value(value: Any, field_name: str) -> bool:
    return _value(value, field_name) is True


def _str_value(value: Any, field_name: str, default: str) -> str:
    field_value = _value(value, field_name, default)
    if field_value is None:
        return default
    return str(field_value)


def _value(value: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _generated_at() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
