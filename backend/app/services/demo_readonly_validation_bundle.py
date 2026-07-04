from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.services.demo_account_readonly_validator import (
    validate_demo_account_readonly_snapshot,
)
from app.services.demo_market_symbol_readonly_validator import (
    validate_demo_market_symbol_readonly,
)
from app.services.demo_positions_order_history_validator import (
    validate_demo_positions_order_history,
)


DEMO_READONLY_BUNDLE_VALID = "DEMO_READONLY_BUNDLE_VALID"
DEMO_READONLY_BUNDLE_INVALID = "DEMO_READONLY_BUNDLE_INVALID"

ACCOUNT_SNAPSHOT = "account_snapshot"
POSITIONS_ORDER_HISTORY = "positions_order_history"
MARKET_SYMBOL = "market_symbol"

COMPONENT_KEYS = (
    ACCOUNT_SNAPSHOT,
    POSITIONS_ORDER_HISTORY,
    MARKET_SYMBOL,
)


@dataclass(frozen=True)
class DemoReadOnlyValidationBundleResult:
    passed: bool
    status_code: str
    block_reasons: list[str]
    warning_reasons: list[str]
    component_results: dict[str, dict[str, Any] | None]
    cross_checks: dict[str, bool]
    is_tradable: bool
    can_execute: bool


def validate_demo_readonly_bundle(
    bundle: dict[str, Any],
) -> DemoReadOnlyValidationBundleResult:
    block_reasons: list[str] = []
    component_results: dict[str, dict[str, Any] | None] = {
        ACCOUNT_SNAPSHOT: None,
        POSITIONS_ORDER_HISTORY: None,
        MARKET_SYMBOL: None,
    }
    component_payloads = _extract_component_payloads(bundle, block_reasons)

    _validate_components(component_payloads, component_results, block_reasons)
    cross_checks = _build_cross_checks(component_payloads)
    _append_cross_check_failures(cross_checks, block_reasons)

    passed = len(block_reasons) == 0

    return DemoReadOnlyValidationBundleResult(
        passed=passed,
        status_code=DEMO_READONLY_BUNDLE_VALID
        if passed
        else DEMO_READONLY_BUNDLE_INVALID,
        block_reasons=block_reasons,
        warning_reasons=[],
        component_results=component_results,
        cross_checks=cross_checks,
        is_tradable=False,
        can_execute=False,
    )


def _extract_component_payloads(
    bundle: dict[str, Any],
    block_reasons: list[str],
) -> dict[str, dict[str, Any]]:
    component_payloads: dict[str, dict[str, Any]] = {}

    for component_key in COMPONENT_KEYS:
        if component_key not in bundle:
            block_reasons.append(f"{component_key} must exist")
            continue

        component_payload = bundle[component_key]
        if not isinstance(component_payload, dict):
            block_reasons.append(f"{component_key} must be an object")
            continue

        component_payloads[component_key] = component_payload

    return component_payloads


def _validate_components(
    component_payloads: dict[str, dict[str, Any]],
    component_results: dict[str, dict[str, Any] | None],
    block_reasons: list[str],
) -> None:
    validators = {
        ACCOUNT_SNAPSHOT: validate_demo_account_readonly_snapshot,
        POSITIONS_ORDER_HISTORY: validate_demo_positions_order_history,
        MARKET_SYMBOL: validate_demo_market_symbol_readonly,
    }

    for component_key, validator in validators.items():
        component_payload = component_payloads.get(component_key)
        if component_payload is None:
            continue

        result = validator(component_payload)
        result_dict = asdict(result)
        component_results[component_key] = result_dict

        if result.passed:
            continue

        for reason in result.block_reasons:
            block_reasons.append(f"{component_key} validator failed: {reason}")


def _build_cross_checks(
    component_payloads: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    return {
        "demo_only_consistent": _all_field_equal(
            component_payloads,
            "account_mode",
            "demo_only",
        ),
        "live_account_absent": _all_field_equal(
            component_payloads,
            "demo_account.is_live_account",
            False,
        ),
        "password_absent": _all_field_equal(
            component_payloads,
            "safety_flags.contains_password",
            False,
        ),
        "credentials_absent": _all_field_equal(
            component_payloads,
            "safety_flags.contains_credentials",
            False,
        ),
        "can_execute": False,
        "can_execute_absent": _all_field_equal(
            component_payloads,
            "safety_flags.can_execute",
            False,
        ),
        "is_tradable": False,
        "is_tradable_absent": _all_field_equal(
            component_payloads,
            "safety_flags.is_tradable",
            False,
        ),
        "symbol_consistent": _symbols_are_consistent(component_payloads),
        "account_alias_consistent": _account_aliases_are_consistent(
            component_payloads
        ),
    }


def _append_cross_check_failures(
    cross_checks: dict[str, bool],
    block_reasons: list[str],
) -> None:
    if not cross_checks["demo_only_consistent"]:
        block_reasons.append("all components account_mode must be demo_only")
    if not cross_checks["live_account_absent"]:
        block_reasons.append("all components demo_account.is_live_account must be false")
    if not cross_checks["password_absent"]:
        block_reasons.append("all components must not contain passwords")
    if not cross_checks["credentials_absent"]:
        block_reasons.append("all components must not contain credentials")
    if not cross_checks["can_execute_absent"]:
        block_reasons.append("all components safety_flags.can_execute must be false")
    if not cross_checks["is_tradable_absent"]:
        block_reasons.append("all components safety_flags.is_tradable must be false")
    if not cross_checks["symbol_consistent"]:
        block_reasons.append("symbols must be consistent and XAUUSD")
    if not cross_checks["account_alias_consistent"]:
        block_reasons.append("account_alias must be consistent across components")


def _all_field_equal(
    component_payloads: dict[str, dict[str, Any]],
    field_path: str,
    expected_value: Any,
) -> bool:
    if set(component_payloads) != set(COMPONENT_KEYS):
        return False

    return all(
        _field_value(component_payload, field_path) == expected_value
        for component_payload in component_payloads.values()
    )


def _symbols_are_consistent(
    component_payloads: dict[str, dict[str, Any]],
) -> bool:
    if set(component_payloads) != set(COMPONENT_KEYS):
        return False

    symbols = _collect_symbols(component_payloads)
    return bool(symbols) and all(symbol == "XAUUSD" for symbol in symbols)


def _collect_symbols(
    component_payloads: dict[str, dict[str, Any]],
) -> list[Any]:
    symbols: list[Any] = []

    account_symbol = _field_value(
        component_payloads[ACCOUNT_SNAPSHOT],
        "symbol_snapshot.symbol",
    )
    symbols.append(account_symbol)

    market_symbol = _field_value(component_payloads[MARKET_SYMBOL], "symbol")
    symbols.append(market_symbol)

    positions_payload = component_payloads[POSITIONS_ORDER_HISTORY]
    for position in _safe_list(_field_value(positions_payload, "open_positions")):
        symbols.append(_field_value(position, "symbol"))
    for order in _safe_list(_field_value(positions_payload, "closed_orders")):
        symbols.append(_field_value(order, "symbol"))

    return symbols


def _account_aliases_are_consistent(
    component_payloads: dict[str, dict[str, Any]],
) -> bool:
    if set(component_payloads) != set(COMPONENT_KEYS):
        return False

    aliases = [
        _field_value(component_payload, "demo_account.account_alias")
        for component_payload in component_payloads.values()
    ]
    present_aliases = [
        alias for alias in aliases if alias is not _MissingField and alias is not None
    ]

    return len(set(present_aliases)) <= 1


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _field_value(payload: Any, field_path: str) -> Any:
    current_value = payload
    for part in field_path.split("."):
        if not isinstance(current_value, dict) or part not in current_value:
            return _MissingField
        current_value = current_value[part]
    return current_value


class _MissingField:
    pass
