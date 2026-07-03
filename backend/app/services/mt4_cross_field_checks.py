from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.mt4_numeric_ranges import (
    Mt4FileNumericRangesStatus,
    Mt4SnapshotNumericRangesStatus,
)
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
    Mt4SnapshotReadResult,
)


ASK_GTE_BID = "ask_gte_bid"
MAX_LOT_GTE_MIN_LOT = "max_lot_gte_min_lot"
LOT_STEP_LTE_MAX_LOT = "lot_step_lte_max_lot"
MAX_DAILY_LOSS_PCT_GTE_MAX_SINGLE_TRADE_LOSS_PCT = (
    "max_daily_loss_pct_gte_max_single_trade_loss_pct"
)

CROSS_FIELD_CHECKS_OK = "CROSS_FIELD_CHECKS_OK"
NUMERIC_RANGES_NOT_READY = "NUMERIC_RANGES_NOT_READY"
CROSS_FIELD_RULE_VIOLATION = "CROSS_FIELD_RULE_VIOLATION"
NO_CROSS_FIELD_RULES = "NO_CROSS_FIELD_RULES"

ALL_CROSS_FIELD_CHECKS_VALID = "ALL_CROSS_FIELD_CHECKS_VALID"
SOME_NUMERIC_RANGES_NOT_READY = "SOME_NUMERIC_RANGES_NOT_READY"
SOME_CROSS_FIELD_CHECKS_INVALID = "SOME_CROSS_FIELD_CHECKS_INVALID"
MULTIPLE_CROSS_FIELD_ISSUES = "MULTIPLE_CROSS_FIELD_ISSUES"

CROSS_FIELD_NOTE = (
    "Cross field checks are not trading permission. "
    "They do not generate trading signals."
)


@dataclass(frozen=True)
class Mt4CrossFieldIssue:
    rule_name: str
    field_paths: list[str]
    actual_values: dict[str, float | int | str | bool | None]
    message: str


@dataclass(frozen=True)
class Mt4FileCrossFieldStatus:
    file_name: str
    checked_rules: list[str]
    violated_rules: list[str]
    cross_field_issues: list[Mt4CrossFieldIssue]
    all_cross_field_checks_valid: bool
    can_proceed_to_data_quality_gate_finalization: bool
    status_code: str
    error_codes: list[str]


@dataclass(frozen=True)
class Mt4SnapshotCrossFieldStatus:
    live_tick: Mt4FileCrossFieldStatus
    latest_bars: Mt4FileCrossFieldStatus
    symbol_spec: Mt4FileCrossFieldStatus
    account_snapshot: Mt4FileCrossFieldStatus
    all_cross_field_checks_valid: bool
    can_proceed_to_data_quality_gate_finalization: bool
    status_code: str
    reasons: list[str]
    is_tradable: bool
    note: str


def check_cross_fields_for_object(
    file_name: str,
    data: dict[str, Any],
) -> Mt4FileCrossFieldStatus:
    if file_name == LIVE_TICK_FILE:
        return _check_live_tick(data)
    if file_name == LATEST_BARS_FILE:
        return _no_cross_field_rules(file_name)
    if file_name == SYMBOL_SPEC_FILE:
        return _check_symbol_spec(data)
    if file_name == ACCOUNT_SNAPSHOT_FILE:
        return _check_account_snapshot(data)

    return _no_cross_field_rules(file_name)


def check_mt4_snapshot_cross_fields(
    snapshot: Mt4SnapshotReadResult,
    numeric_ranges_status: Mt4SnapshotNumericRangesStatus,
) -> Mt4SnapshotCrossFieldStatus:
    live_tick = _check_file_cross_fields(
        LIVE_TICK_FILE,
        snapshot.live_tick.data,
        numeric_ranges_status.live_tick,
    )
    latest_bars = _check_file_cross_fields(
        LATEST_BARS_FILE,
        snapshot.latest_bars.data,
        numeric_ranges_status.latest_bars,
    )
    symbol_spec = _check_file_cross_fields(
        SYMBOL_SPEC_FILE,
        snapshot.symbol_spec.data,
        numeric_ranges_status.symbol_spec,
    )
    account_snapshot = _check_file_cross_fields(
        ACCOUNT_SNAPSHOT_FILE,
        snapshot.account_snapshot.data,
        numeric_ranges_status.account_snapshot,
    )

    file_statuses = (live_tick, latest_bars, symbol_spec, account_snapshot)
    all_cross_field_checks_valid = all(
        status.all_cross_field_checks_valid for status in file_statuses
    )

    return Mt4SnapshotCrossFieldStatus(
        live_tick=live_tick,
        latest_bars=latest_bars,
        symbol_spec=symbol_spec,
        account_snapshot=account_snapshot,
        all_cross_field_checks_valid=all_cross_field_checks_valid,
        can_proceed_to_data_quality_gate_finalization=all_cross_field_checks_valid,
        status_code=_snapshot_status_code(file_statuses),
        reasons=_snapshot_reasons(file_statuses),
        is_tradable=False,
        note=CROSS_FIELD_NOTE,
    )


def _check_file_cross_fields(
    file_name: str,
    data: dict[str, Any] | None,
    numeric_status: Mt4FileNumericRangesStatus,
) -> Mt4FileCrossFieldStatus:
    if not numeric_status.can_proceed_to_cross_field_checks or data is None:
        return Mt4FileCrossFieldStatus(
            file_name=file_name,
            checked_rules=[],
            violated_rules=[],
            cross_field_issues=[],
            all_cross_field_checks_valid=False,
            can_proceed_to_data_quality_gate_finalization=False,
            status_code=NUMERIC_RANGES_NOT_READY,
            error_codes=[NUMERIC_RANGES_NOT_READY],
        )

    return check_cross_fields_for_object(file_name, data)


def _check_live_tick(data: dict[str, Any]) -> Mt4FileCrossFieldStatus:
    issues: list[Mt4CrossFieldIssue] = []
    bid = _as_number(_field_value(data, "bid"))
    ask = _as_number(_field_value(data, "ask"))

    if ask is None or bid is None or ask < bid:
        issues.append(
            Mt4CrossFieldIssue(
                rule_name=ASK_GTE_BID,
                field_paths=["ask", "bid"],
                actual_values={"ask": ask, "bid": bid},
                message="live_tick.ask must be greater than or equal to live_tick.bid.",
            )
        )

    return _status_from_issues(LIVE_TICK_FILE, [ASK_GTE_BID], issues)


def _check_symbol_spec(data: dict[str, Any]) -> Mt4FileCrossFieldStatus:
    issues: list[Mt4CrossFieldIssue] = []
    min_lot = _as_number(_field_value(data, "min_lot"))
    lot_step = _as_number(_field_value(data, "lot_step"))
    max_lot = _as_number(_field_value(data, "max_lot"))

    if max_lot is None or min_lot is None or max_lot < min_lot:
        issues.append(
            Mt4CrossFieldIssue(
                rule_name=MAX_LOT_GTE_MIN_LOT,
                field_paths=["max_lot", "min_lot"],
                actual_values={"max_lot": max_lot, "min_lot": min_lot},
                message="symbol_spec.max_lot must be greater than or equal to symbol_spec.min_lot.",
            )
        )

    if lot_step is None or max_lot is None or lot_step > max_lot:
        issues.append(
            Mt4CrossFieldIssue(
                rule_name=LOT_STEP_LTE_MAX_LOT,
                field_paths=["lot_step", "max_lot"],
                actual_values={"lot_step": lot_step, "max_lot": max_lot},
                message="symbol_spec.lot_step must be less than or equal to symbol_spec.max_lot.",
            )
        )

    return _status_from_issues(
        SYMBOL_SPEC_FILE,
        [MAX_LOT_GTE_MIN_LOT, LOT_STEP_LTE_MAX_LOT],
        issues,
    )


def _check_account_snapshot(data: dict[str, Any]) -> Mt4FileCrossFieldStatus:
    issues: list[Mt4CrossFieldIssue] = []
    max_single_trade_loss_pct = _as_number(
        _field_value(data, "risk_limits.max_single_trade_loss_pct")
    )
    max_daily_loss_pct = _as_number(
        _field_value(data, "risk_limits.max_daily_loss_pct")
    )

    if (
        max_daily_loss_pct is None
        or max_single_trade_loss_pct is None
        or max_daily_loss_pct < max_single_trade_loss_pct
    ):
        issues.append(
            Mt4CrossFieldIssue(
                rule_name=MAX_DAILY_LOSS_PCT_GTE_MAX_SINGLE_TRADE_LOSS_PCT,
                field_paths=[
                    "risk_limits.max_daily_loss_pct",
                    "risk_limits.max_single_trade_loss_pct",
                ],
                actual_values={
                    "risk_limits.max_daily_loss_pct": max_daily_loss_pct,
                    "risk_limits.max_single_trade_loss_pct": max_single_trade_loss_pct,
                },
                message=(
                    "account_snapshot.risk_limits.max_daily_loss_pct must be greater "
                    "than or equal to account_snapshot.risk_limits.max_single_trade_loss_pct."
                ),
            )
        )

    return _status_from_issues(
        ACCOUNT_SNAPSHOT_FILE,
        [MAX_DAILY_LOSS_PCT_GTE_MAX_SINGLE_TRADE_LOSS_PCT],
        issues,
    )


def _no_cross_field_rules(file_name: str) -> Mt4FileCrossFieldStatus:
    return Mt4FileCrossFieldStatus(
        file_name=file_name,
        checked_rules=[],
        violated_rules=[],
        cross_field_issues=[],
        all_cross_field_checks_valid=True,
        can_proceed_to_data_quality_gate_finalization=True,
        status_code=NO_CROSS_FIELD_RULES,
        error_codes=[],
    )


def _status_from_issues(
    file_name: str,
    checked_rules: list[str],
    issues: list[Mt4CrossFieldIssue],
) -> Mt4FileCrossFieldStatus:
    error_codes = [CROSS_FIELD_RULE_VIOLATION] if issues else []

    return Mt4FileCrossFieldStatus(
        file_name=file_name,
        checked_rules=checked_rules,
        violated_rules=[issue.rule_name for issue in issues],
        cross_field_issues=issues,
        all_cross_field_checks_valid=len(issues) == 0,
        can_proceed_to_data_quality_gate_finalization=len(issues) == 0,
        status_code=_file_status_code(error_codes),
        error_codes=error_codes,
    )


def _field_value(data: dict[str, Any], field_path: str) -> Any:
    current_value: Any = data
    for part in field_path.split("."):
        if not isinstance(current_value, dict) or part not in current_value:
            return None
        current_value = current_value[part]
    return current_value


def _as_number(value: Any) -> float | int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _file_status_code(error_codes: list[str]) -> str:
    if not error_codes:
        return CROSS_FIELD_CHECKS_OK
    return error_codes[0]


def _snapshot_status_code(
    file_statuses: tuple[Mt4FileCrossFieldStatus, ...],
) -> str:
    issue_types = {
        error_code
        for status in file_statuses
        for error_code in status.error_codes
    }

    if not issue_types:
        return ALL_CROSS_FIELD_CHECKS_VALID
    if len(issue_types) > 1:
        return MULTIPLE_CROSS_FIELD_ISSUES
    if NUMERIC_RANGES_NOT_READY in issue_types:
        return SOME_NUMERIC_RANGES_NOT_READY
    return SOME_CROSS_FIELD_CHECKS_INVALID


def _snapshot_reasons(
    file_statuses: tuple[Mt4FileCrossFieldStatus, ...],
) -> list[str]:
    reasons: list[str] = []
    for status in file_statuses:
        if status.status_code == NUMERIC_RANGES_NOT_READY:
            reasons.append(f"{status.file_name}:{NUMERIC_RANGES_NOT_READY}")
        if status.cross_field_issues:
            reasons.append(
                f"{status.file_name}:{CROSS_FIELD_RULE_VIOLATION}:"
                f"{','.join(status.violated_rules)}"
            )
    return reasons
