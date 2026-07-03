from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.mt4_field_types import (
    Mt4FileFieldTypesStatus,
    Mt4SnapshotFieldTypesStatus,
)
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
    Mt4SnapshotReadResult,
)


GT_0 = "gt_0"
GTE_0 = "gte_0"

NUMERIC_RANGES_OK = "NUMERIC_RANGES_OK"
FIELD_TYPES_NOT_READY = "FIELD_TYPES_NOT_READY"
NUMERIC_RANGE_VIOLATION = "NUMERIC_RANGE_VIOLATION"
NO_NUMERIC_RANGE_RULES = "NO_NUMERIC_RANGE_RULES"

ALL_NUMERIC_RANGES_VALID = "ALL_NUMERIC_RANGES_VALID"
SOME_FIELD_TYPES_NOT_READY = "SOME_FIELD_TYPES_NOT_READY"
SOME_NUMERIC_RANGES_INVALID = "SOME_NUMERIC_RANGES_INVALID"
MULTIPLE_NUMERIC_RANGE_ISSUES = "MULTIPLE_NUMERIC_RANGE_ISSUES"

NUMERIC_RANGE_NOTE = (
    "Numeric range checks are not trading permission. "
    "They do not generate trading signals."
)

LIVE_TICK_NUMERIC_RANGE_RULES = {
    "bid": GT_0,
    "ask": GT_0,
    "spread": GTE_0,
}

LATEST_BARS_NUMERIC_RANGE_RULES: dict[str, str] = {}

SYMBOL_SPEC_NUMERIC_RANGE_RULES = {
    "tick_size": GT_0,
    "tick_value": GT_0,
    "lot_size": GT_0,
    "min_lot": GT_0,
    "lot_step": GT_0,
    "max_lot": GT_0,
}

ACCOUNT_SNAPSHOT_NUMERIC_RANGE_RULES = {
    "balance": GTE_0,
    "equity": GTE_0,
    "free_margin": GTE_0,
    "daily_loss_pct": GTE_0,
    "risk_limits.max_single_trade_loss_pct": GT_0,
    "risk_limits.max_daily_loss_pct": GT_0,
}


@dataclass(frozen=True)
class Mt4NumericRangeIssue:
    field_path: str
    rule: str
    actual_value: float


@dataclass(frozen=True)
class Mt4FileNumericRangesStatus:
    file_name: str
    checked_fields: list[str]
    invalid_fields: list[str]
    range_issues: list[Mt4NumericRangeIssue]
    all_numeric_ranges_valid: bool
    can_proceed_to_cross_field_checks: bool
    status_code: str
    error_codes: list[str]


@dataclass(frozen=True)
class Mt4SnapshotNumericRangesStatus:
    live_tick: Mt4FileNumericRangesStatus
    latest_bars: Mt4FileNumericRangesStatus
    symbol_spec: Mt4FileNumericRangesStatus
    account_snapshot: Mt4FileNumericRangesStatus
    all_numeric_ranges_valid: bool
    can_proceed_to_cross_field_checks: bool
    status_code: str
    reasons: list[str]
    is_tradable: bool
    note: str


def check_numeric_ranges_for_object(
    file_name: str,
    data: dict[str, Any],
    range_rules: dict[str, str],
) -> Mt4FileNumericRangesStatus:
    if not range_rules:
        return Mt4FileNumericRangesStatus(
            file_name=file_name,
            checked_fields=[],
            invalid_fields=[],
            range_issues=[],
            all_numeric_ranges_valid=True,
            can_proceed_to_cross_field_checks=True,
            status_code=NO_NUMERIC_RANGE_RULES,
            error_codes=[],
        )

    range_issues: list[Mt4NumericRangeIssue] = []

    for field_path, rule in range_rules.items():
        value = _field_value(data, field_path)
        numeric_value = _as_float(value)
        if numeric_value is None or not _matches_rule(numeric_value, rule):
            range_issues.append(
                Mt4NumericRangeIssue(
                    field_path=field_path,
                    rule=rule,
                    actual_value=numeric_value if numeric_value is not None else float("nan"),
                )
            )

    error_codes = [NUMERIC_RANGE_VIOLATION] if range_issues else []

    return Mt4FileNumericRangesStatus(
        file_name=file_name,
        checked_fields=list(range_rules.keys()),
        invalid_fields=[issue.field_path for issue in range_issues],
        range_issues=range_issues,
        all_numeric_ranges_valid=len(range_issues) == 0,
        can_proceed_to_cross_field_checks=len(range_issues) == 0,
        status_code=_file_status_code(error_codes),
        error_codes=error_codes,
    )


def check_mt4_snapshot_numeric_ranges(
    snapshot: Mt4SnapshotReadResult,
    field_types_status: Mt4SnapshotFieldTypesStatus,
) -> Mt4SnapshotNumericRangesStatus:
    live_tick = _check_file_numeric_ranges(
        LIVE_TICK_FILE,
        snapshot.live_tick.data,
        field_types_status.live_tick,
        LIVE_TICK_NUMERIC_RANGE_RULES,
    )
    latest_bars = _check_file_numeric_ranges(
        LATEST_BARS_FILE,
        snapshot.latest_bars.data,
        field_types_status.latest_bars,
        LATEST_BARS_NUMERIC_RANGE_RULES,
    )
    symbol_spec = _check_file_numeric_ranges(
        SYMBOL_SPEC_FILE,
        snapshot.symbol_spec.data,
        field_types_status.symbol_spec,
        SYMBOL_SPEC_NUMERIC_RANGE_RULES,
    )
    account_snapshot = _check_file_numeric_ranges(
        ACCOUNT_SNAPSHOT_FILE,
        snapshot.account_snapshot.data,
        field_types_status.account_snapshot,
        ACCOUNT_SNAPSHOT_NUMERIC_RANGE_RULES,
    )

    file_statuses = (live_tick, latest_bars, symbol_spec, account_snapshot)
    all_numeric_ranges_valid = all(
        status.all_numeric_ranges_valid for status in file_statuses
    )

    return Mt4SnapshotNumericRangesStatus(
        live_tick=live_tick,
        latest_bars=latest_bars,
        symbol_spec=symbol_spec,
        account_snapshot=account_snapshot,
        all_numeric_ranges_valid=all_numeric_ranges_valid,
        can_proceed_to_cross_field_checks=all_numeric_ranges_valid,
        status_code=_snapshot_status_code(file_statuses),
        reasons=_snapshot_reasons(file_statuses),
        is_tradable=False,
        note=NUMERIC_RANGE_NOTE,
    )


def _check_file_numeric_ranges(
    file_name: str,
    data: dict[str, Any] | None,
    field_types_status: Mt4FileFieldTypesStatus,
    range_rules: dict[str, str],
) -> Mt4FileNumericRangesStatus:
    if not field_types_status.can_proceed_to_value_checks or data is None:
        return Mt4FileNumericRangesStatus(
            file_name=file_name,
            checked_fields=[],
            invalid_fields=[],
            range_issues=[],
            all_numeric_ranges_valid=False,
            can_proceed_to_cross_field_checks=False,
            status_code=FIELD_TYPES_NOT_READY,
            error_codes=[FIELD_TYPES_NOT_READY],
        )

    return check_numeric_ranges_for_object(
        file_name=file_name,
        data=data,
        range_rules=range_rules,
    )


def _field_value(data: dict[str, Any], field_path: str) -> Any:
    current_value: Any = data
    for part in field_path.split("."):
        if not isinstance(current_value, dict) or part not in current_value:
            return None
        current_value = current_value[part]
    return current_value


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _matches_rule(value: float, rule: str) -> bool:
    if rule == GT_0:
        return value > 0
    if rule == GTE_0:
        return value >= 0
    return False


def _file_status_code(error_codes: list[str]) -> str:
    if not error_codes:
        return NUMERIC_RANGES_OK
    return error_codes[0]


def _snapshot_status_code(
    file_statuses: tuple[Mt4FileNumericRangesStatus, ...],
) -> str:
    issue_types = {
        error_code
        for status in file_statuses
        for error_code in status.error_codes
    }

    if not issue_types:
        return ALL_NUMERIC_RANGES_VALID
    if len(issue_types) > 1:
        return MULTIPLE_NUMERIC_RANGE_ISSUES
    if FIELD_TYPES_NOT_READY in issue_types:
        return SOME_FIELD_TYPES_NOT_READY
    return SOME_NUMERIC_RANGES_INVALID


def _snapshot_reasons(
    file_statuses: tuple[Mt4FileNumericRangesStatus, ...],
) -> list[str]:
    reasons: list[str] = []
    for status in file_statuses:
        if status.status_code == FIELD_TYPES_NOT_READY:
            reasons.append(f"{status.file_name}:{FIELD_TYPES_NOT_READY}")
        if status.range_issues:
            reasons.append(
                f"{status.file_name}:{NUMERIC_RANGE_VIOLATION}:"
                f"{','.join(status.invalid_fields)}"
            )
    return reasons
