from __future__ import annotations

from typing import Any


DOCS_FIXTURE_ONLY_SOURCE_MODE = "docs_fixture_only"
MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE = (
    "mt4_demo_readonly_file_bridge_enabled"
)

MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY = (
    "MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY"
)
MT4_DEMO_READONLY_SOURCE_CONFIG_READY = "MT4_DEMO_READONLY_SOURCE_CONFIG_READY"
MT4_DEMO_READONLY_SOURCE_CONFIG_BLOCKED = "MT4_DEMO_READONLY_SOURCE_CONFIG_BLOCKED"
MT4_DEMO_READONLY_SOURCE_CONFIG_INPUT_INVALID = (
    "MT4_DEMO_READONLY_SOURCE_CONFIG_INPUT_INVALID"
)
MT4_DEMO_READONLY_SOURCE_MODE_REJECTED = "MT4_DEMO_READONLY_SOURCE_MODE_REJECTED"
MT4_DEMO_READONLY_BRIDGE_DIR_REJECTED = "MT4_DEMO_READONLY_BRIDGE_DIR_REJECTED"
MT4_DEMO_READONLY_REQUEST_OVERRIDE_REJECTED = (
    "MT4_DEMO_READONLY_REQUEST_OVERRIDE_REJECTED"
)
MT4_DEMO_READONLY_SOURCE_CONFIG_SAFETY_BLOCKED = (
    "MT4_DEMO_READONLY_SOURCE_CONFIG_SAFETY_BLOCKED"
)

_ALLOWED_SOURCE_MODES = (
    DOCS_FIXTURE_ONLY_SOURCE_MODE,
    MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
)

_ALLOWED_CONFIG_FIELDS = frozenset(
    {
        "source_mode",
        "mt4_demo_readonly_file_bridge_enabled",
        "mt4_demo_readonly_bridge_dir",
        "allow_request_override",
    }
)

_FORBIDDEN_SOURCE_MODES = frozenset(
    {
        "any_execution_source",
        "auto_trade",
        "demo_execution",
        "execution",
        "live",
        "mt4_demo_execution",
        "mt4_live_execution",
        "mt4_live_readonly",
        "order_execution",
        "raw_terminal_export",
        "real_account",
        "unknown_live_source",
    }
)

_REJECTED_BRIDGE_DIR_PARTS = frozenset(
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
    }
)

_REJECTED_BRIDGE_DIR_FRAGMENTS = frozenset(
    {
        "credential",
        "execution",
        "live_account",
        "login",
        "order_send",
        "password",
        "real_account",
        "secret",
        "token",
        "trade_plan",
    }
)

_REJECTED_PRIVATE_PATH_OR_TRACE_FRAGMENTS = (
    "c:/users/",
    "/home/",
    "/root/",
    "traceback",
    "stack trace",
    "stack_trace",
    ".py",
)

_FORBIDDEN_OUTPUT_KEYS = frozenset(
    {
        "account_number",
        "allow_trade",
        "api_key",
        "base_dir",
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
        "order",
        "order_close",
        "order_delete",
        "order_id",
        "order_modify",
        "order_send",
        "password",
        "raw_payload",
        "real_account",
        "secret",
        "sell",
        "sell_now",
        "should_buy",
        "should_sell",
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

_FORBIDDEN_OUTPUT_TEXT_FRAGMENTS = frozenset(
    {
        "account_number",
        "allow_trade",
        "api_key",
        "base_dir",
        "buy_now",
        "candidate_path",
        "can_trade",
        "credential",
        "ea_command",
        "execute_trade",
        "final_lot",
        "live_account",
        "login",
        "open_position",
        "order_close",
        "order_delete",
        "order_modify",
        "order_send",
        "password",
        "raw_payload",
        "real_account",
        "secret",
        "sell_now",
        "should_buy",
        "should_sell",
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


def get_demo_readonly_default_source_mode() -> str:
    return DOCS_FIXTURE_ONLY_SOURCE_MODE


def get_demo_readonly_allowed_source_modes() -> tuple[str, ...]:
    return _ALLOWED_SOURCE_MODES


def validate_demo_readonly_source_config(config: object) -> dict[str, Any]:
    try:
        result = _validate_demo_readonly_source_config(config)
    except Exception:
        return _safety_blocked_result(
            block_reasons=["SOURCE_CONFIG_GUARD_EXCEPTION_SANITIZED"]
        )

    if (
        not isinstance(result, dict)
        or _has_unsafe_safety_flags(result)
        or _contains_forbidden_output_content(result)
    ):
        return _safety_blocked_result(
            block_reasons=["SOURCE_CONFIG_GUARD_OUTPUT_SANITIZED"]
        )

    return result


def _validate_demo_readonly_source_config(config: object) -> dict[str, Any]:
    if config is None:
        return _result(
            passed=True,
            status_code=MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY,
            selected_source_mode=DOCS_FIXTURE_ONLY_SOURCE_MODE,
            source_status="docs_fixture_only_ready",
            bridge_dir_status="not_required",
            block_reasons=[],
            warning_reasons=["CONFIG_MISSING_DEFAULTED_TO_DOCS_FIXTURE_ONLY"],
        )

    if not isinstance(config, dict):
        return _blocked_result(
            status_code=MT4_DEMO_READONLY_SOURCE_CONFIG_INPUT_INVALID,
            block_reasons=["CONFIG_INPUT_NOT_DICT"],
        )

    unexpected_config_fields = set(config) - _ALLOWED_CONFIG_FIELDS
    if unexpected_config_fields:
        return _blocked_result(
            status_code=MT4_DEMO_READONLY_SOURCE_CONFIG_SAFETY_BLOCKED,
            block_reasons=["CONFIG_FIELD_NOT_ALLOWED"],
        )

    if config.get("allow_request_override", False) is not False:
        return _blocked_result(
            status_code=MT4_DEMO_READONLY_REQUEST_OVERRIDE_REJECTED,
            block_reasons=["REQUEST_OVERRIDE_REJECTED"],
        )

    source_mode = config.get("source_mode", DOCS_FIXTURE_ONLY_SOURCE_MODE)
    if "source_mode" not in config and not config:
        return _result(
            passed=True,
            status_code=MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY,
            selected_source_mode=DOCS_FIXTURE_ONLY_SOURCE_MODE,
            source_status="docs_fixture_only_ready",
            bridge_dir_status="not_required",
            block_reasons=[],
            warning_reasons=[],
        )

    if source_mode == DOCS_FIXTURE_ONLY_SOURCE_MODE:
        return _result(
            passed=True,
            status_code=MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY,
            selected_source_mode=DOCS_FIXTURE_ONLY_SOURCE_MODE,
            source_status="docs_fixture_only_ready",
            bridge_dir_status="not_required",
            block_reasons=[],
            warning_reasons=[],
        )

    if not isinstance(source_mode, str) or not source_mode.strip():
        return _blocked_result(
            status_code=MT4_DEMO_READONLY_SOURCE_MODE_REJECTED,
            block_reasons=["SOURCE_MODE_REJECTED"],
        )

    if source_mode in _FORBIDDEN_SOURCE_MODES or source_mode not in _ALLOWED_SOURCE_MODES:
        return _blocked_result(
            status_code=MT4_DEMO_READONLY_SOURCE_MODE_REJECTED,
            block_reasons=["SOURCE_MODE_REJECTED"],
        )

    if source_mode == MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE:
        if config.get("mt4_demo_readonly_file_bridge_enabled") is not True:
            return _result(
                passed=False,
                status_code=MT4_DEMO_READONLY_SOURCE_CONFIG_BLOCKED,
                selected_source_mode=MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
                source_status="source_mode_blocked",
                bridge_dir_status="not_evaluated",
                block_reasons=["MT4_DEMO_READONLY_FILE_BRIDGE_DISABLED"],
                warning_reasons=[],
            )

        bridge_dir_reason = _bridge_dir_rejection_reason(
            config.get("mt4_demo_readonly_bridge_dir")
        )
        if bridge_dir_reason is not None:
            return _result(
                passed=False,
                status_code=MT4_DEMO_READONLY_BRIDGE_DIR_REJECTED,
                selected_source_mode=MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
                source_status="source_mode_blocked",
                bridge_dir_status="rejected",
                block_reasons=[bridge_dir_reason],
                warning_reasons=[],
            )

        return _result(
            passed=True,
            status_code=MT4_DEMO_READONLY_SOURCE_CONFIG_READY,
            selected_source_mode=MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
            source_status="mt4_demo_readonly_file_bridge_ready",
            bridge_dir_status="safe_configured",
            block_reasons=[],
            warning_reasons=[],
        )

    return _blocked_result(
        status_code=MT4_DEMO_READONLY_SOURCE_CONFIG_SAFETY_BLOCKED,
        block_reasons=["SOURCE_CONFIG_GUARD_FELL_THROUGH"],
    )


def _safety_blocked_result(*, block_reasons: list[str]) -> dict[str, Any]:
    return {
        "passed": False,
        "status_code": MT4_DEMO_READONLY_SOURCE_CONFIG_SAFETY_BLOCKED,
        "selected_source_mode": DOCS_FIXTURE_ONLY_SOURCE_MODE,
        "default_source_mode": DOCS_FIXTURE_ONLY_SOURCE_MODE,
        "source_status": "source_mode_blocked",
        "bridge_dir_status": "not_evaluated",
        "request_override_allowed": False,
        "block_reasons": list(dict.fromkeys(block_reasons)),
        "warning_reasons": [],
        "notes": [
            "source config guard validates caller-provided server-side config only",
            "source_mode readiness is not a trading permission",
        ],
        **_SAFETY_FIELDS,
    }


def _blocked_result(*, status_code: str, block_reasons: list[str]) -> dict[str, Any]:
    return _result(
        passed=False,
        status_code=status_code,
        selected_source_mode=DOCS_FIXTURE_ONLY_SOURCE_MODE,
        source_status="source_mode_blocked",
        bridge_dir_status="not_evaluated",
        block_reasons=block_reasons,
        warning_reasons=[],
    )


def _result(
    *,
    passed: bool,
    status_code: str,
    selected_source_mode: str,
    source_status: str,
    bridge_dir_status: str,
    block_reasons: list[str],
    warning_reasons: list[str],
) -> dict[str, Any]:
    return {
        "passed": passed,
        "status_code": status_code,
        "selected_source_mode": selected_source_mode,
        "default_source_mode": DOCS_FIXTURE_ONLY_SOURCE_MODE,
        "source_status": source_status,
        "bridge_dir_status": bridge_dir_status,
        "request_override_allowed": False,
        "block_reasons": list(dict.fromkeys(block_reasons)),
        "warning_reasons": list(dict.fromkeys(warning_reasons)),
        "notes": [
            "source config guard validates caller-provided server-side config only",
            "source_mode readiness is not a trading permission",
        ],
        **_SAFETY_FIELDS,
    }


def _has_unsafe_safety_flags(result: dict[str, Any]) -> bool:
    return any(result.get(key) is not expected for key, expected in _SAFETY_FIELDS.items())


def _contains_forbidden_output_content(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            (
                isinstance(key, str)
                and key.lower() in _FORBIDDEN_OUTPUT_KEYS
            )
            or _contains_forbidden_output_content(child)
            for key, child in value.items()
        )

    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_output_content(item) for item in value)

    if isinstance(value, str):
        return _contains_forbidden_output_text(value)

    return False


def _contains_forbidden_output_text(value: str) -> bool:
    lower_value = value.lower()
    normalized_value = lower_value.replace("\\", "/")
    return any(
        fragment in lower_value for fragment in _FORBIDDEN_OUTPUT_TEXT_FRAGMENTS
    ) or any(
        fragment in normalized_value
        for fragment in _REJECTED_PRIVATE_PATH_OR_TRACE_FRAGMENTS
    )


def _bridge_dir_rejection_reason(value: object) -> str | None:
    if not isinstance(value, str):
        return "BRIDGE_DIR_INPUT_NOT_STR"

    if not value or not value.strip():
        return "BRIDGE_DIR_EMPTY"

    if value != value.strip():
        return "BRIDGE_DIR_HAS_SURROUNDING_WHITESPACE"

    if "\x00" in value:
        return "BRIDGE_DIR_CONTAINS_NUL"

    normalized = value.replace("\\", "/")
    lower_normalized = normalized.lower()
    parts = [part.lower() for part in normalized.split("/") if part]

    if any(
        fragment in lower_normalized
        for fragment in _REJECTED_PRIVATE_PATH_OR_TRACE_FRAGMENTS
    ):
        return "BRIDGE_DIR_CONTAINS_UNSAFE_PATH_TEXT"

    if ".." in parts or "../" in normalized or "..\\" in value:
        return "BRIDGE_DIR_CONTAINS_PATH_TRAVERSAL"

    if ".env" in parts or ".env" in lower_normalized:
        return "BRIDGE_DIR_POINTS_TO_ENV"

    if any(part in _REJECTED_BRIDGE_DIR_PARTS for part in parts):
        return "BRIDGE_DIR_POINTS_TO_REJECTED_LOCATION"

    if any(fragment in lower_normalized for fragment in _REJECTED_BRIDGE_DIR_FRAGMENTS):
        return "BRIDGE_DIR_CONTAINS_FORBIDDEN_FRAGMENT"

    return None
