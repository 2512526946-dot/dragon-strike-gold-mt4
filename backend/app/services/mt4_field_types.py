from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.mt4_required_fields import (
    Mt4FileRequiredFieldsStatus,
    Mt4SnapshotRequiredFieldsStatus,
)
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
    Mt4SnapshotReadResult,
)


STRING_TYPE = "string"
NUMBER_TYPE = "number"
BOOLEAN_TYPE = "boolean"
OBJECT_TYPE = "object"

FIELD_TYPES_OK = "FIELD_TYPES_OK"
REQUIRED_FIELDS_NOT_READY = "REQUIRED_FIELDS_NOT_READY"
FIELD_TYPE_MISMATCH = "FIELD_TYPE_MISMATCH"

ALL_FIELD_TYPES_VALID = "ALL_FIELD_TYPES_VALID"
SOME_REQUIRED_FIELDS_NOT_READY = "SOME_REQUIRED_FIELDS_NOT_READY"
SOME_FIELD_TYPES_INVALID = "SOME_FIELD_TYPES_INVALID"
MULTIPLE_FIELD_TYPE_ISSUES = "MULTIPLE_FIELD_TYPE_ISSUES"

FIELD_TYPE_NOTE = (
    "Field type checks are not trading permission. "
    "They do not generate trading signals."
)

LIVE_TICK_FIELD_TYPES = {
    "symbol": STRING_TYPE,
    "bid": NUMBER_TYPE,
    "ask": NUMBER_TYPE,
    "spread": NUMBER_TYPE,
    "is_tradable": BOOLEAN_TYPE,
}

LATEST_BARS_FIELD_TYPES = {
    "symbol": STRING_TYPE,
    "timeframes": OBJECT_TYPE,
    "timeframes.M15": OBJECT_TYPE,
    "timeframes.H1": OBJECT_TYPE,
    "timeframes.H4": OBJECT_TYPE,
    "timeframes.D1": OBJECT_TYPE,
    "is_tradable": BOOLEAN_TYPE,
}

SYMBOL_SPEC_FIELD_TYPES = {
    "symbol": STRING_TYPE,
    "tick_size": NUMBER_TYPE,
    "tick_value": NUMBER_TYPE,
    "lot_size": NUMBER_TYPE,
    "min_lot": NUMBER_TYPE,
    "lot_step": NUMBER_TYPE,
    "max_lot": NUMBER_TYPE,
    "is_tradable": BOOLEAN_TYPE,
}

ACCOUNT_SNAPSHOT_FIELD_TYPES = {
    "account_currency": STRING_TYPE,
    "balance": NUMBER_TYPE,
    "equity": NUMBER_TYPE,
    "free_margin": NUMBER_TYPE,
    "daily_loss_pct": NUMBER_TYPE,
    "risk_limits": OBJECT_TYPE,
    "risk_limits.max_single_trade_loss_pct": NUMBER_TYPE,
    "risk_limits.max_daily_loss_pct": NUMBER_TYPE,
    "risk_limits.no_overnight": BOOLEAN_TYPE,
    "is_tradable": BOOLEAN_TYPE,
}


@dataclass(frozen=True)
class Mt4FieldTypeIssue:
    field_path: str
    expected_type: str
    actual_type: str


@dataclass(frozen=True)
class Mt4FileFieldTypesStatus:
    file_name: str
    expected_field_types: dict[str, str]
    valid_type_fields: list[str]
    wrong_type_fields: list[str]
    type_issues: list[Mt4FieldTypeIssue]
    all_field_types_valid: bool
    can_proceed_to_value_checks: bool
    status_code: str
    error_codes: list[str]


@dataclass(frozen=True)
class Mt4SnapshotFieldTypesStatus:
    live_tick: Mt4FileFieldTypesStatus
    latest_bars: Mt4FileFieldTypesStatus
    symbol_spec: Mt4FileFieldTypesStatus
    account_snapshot: Mt4FileFieldTypesStatus
    all_field_types_valid: bool
    can_proceed_to_value_checks: bool
    status_code: str
    reasons: list[str]
    is_tradable: bool
    note: str


def check_field_types_for_object(
    file_name: str,
    data: dict[str, Any],
    expected_field_types: dict[str, str],
) -> Mt4FileFieldTypesStatus:
    valid_type_fields: list[str] = []
    type_issues: list[Mt4FieldTypeIssue] = []

    for field_path, expected_type in expected_field_types.items():
        value = _field_value(data, field_path)
        actual_type = _actual_type_name(value)
        if _matches_expected_type(value, expected_type):
            valid_type_fields.append(field_path)
        else:
            type_issues.append(
                Mt4FieldTypeIssue(
                    field_path=field_path,
                    expected_type=expected_type,
                    actual_type=actual_type,
                )
            )

    error_codes = [FIELD_TYPE_MISMATCH] if type_issues else []

    return Mt4FileFieldTypesStatus(
        file_name=file_name,
        expected_field_types=expected_field_types,
        valid_type_fields=valid_type_fields,
        wrong_type_fields=[issue.field_path for issue in type_issues],
        type_issues=type_issues,
        all_field_types_valid=len(type_issues) == 0,
        can_proceed_to_value_checks=len(type_issues) == 0,
        status_code=_file_status_code(error_codes),
        error_codes=error_codes,
    )


def check_mt4_snapshot_field_types(
    snapshot: Mt4SnapshotReadResult,
    required_fields_status: Mt4SnapshotRequiredFieldsStatus,
) -> Mt4SnapshotFieldTypesStatus:
    live_tick = _check_file_field_types(
        LIVE_TICK_FILE,
        snapshot.live_tick.data,
        required_fields_status.live_tick,
        LIVE_TICK_FIELD_TYPES,
    )
    latest_bars = _check_file_field_types(
        LATEST_BARS_FILE,
        snapshot.latest_bars.data,
        required_fields_status.latest_bars,
        LATEST_BARS_FIELD_TYPES,
    )
    symbol_spec = _check_file_field_types(
        SYMBOL_SPEC_FILE,
        snapshot.symbol_spec.data,
        required_fields_status.symbol_spec,
        SYMBOL_SPEC_FIELD_TYPES,
    )
    account_snapshot = _check_file_field_types(
        ACCOUNT_SNAPSHOT_FILE,
        snapshot.account_snapshot.data,
        required_fields_status.account_snapshot,
        ACCOUNT_SNAPSHOT_FIELD_TYPES,
    )

    file_statuses = (live_tick, latest_bars, symbol_spec, account_snapshot)
    all_field_types_valid = all(
        status.all_field_types_valid for status in file_statuses
    )

    return Mt4SnapshotFieldTypesStatus(
        live_tick=live_tick,
        latest_bars=latest_bars,
        symbol_spec=symbol_spec,
        account_snapshot=account_snapshot,
        all_field_types_valid=all_field_types_valid,
        can_proceed_to_value_checks=all_field_types_valid,
        status_code=_snapshot_status_code(file_statuses),
        reasons=_snapshot_reasons(file_statuses),
        is_tradable=False,
        note=FIELD_TYPE_NOTE,
    )


def _check_file_field_types(
    file_name: str,
    data: dict[str, Any] | None,
    required_status: Mt4FileRequiredFieldsStatus,
    expected_field_types: dict[str, str],
) -> Mt4FileFieldTypesStatus:
    if not required_status.can_proceed_to_value_checks or data is None:
        return Mt4FileFieldTypesStatus(
            file_name=file_name,
            expected_field_types=expected_field_types,
            valid_type_fields=[],
            wrong_type_fields=[],
            type_issues=[],
            all_field_types_valid=False,
            can_proceed_to_value_checks=False,
            status_code=REQUIRED_FIELDS_NOT_READY,
            error_codes=[REQUIRED_FIELDS_NOT_READY],
        )

    return check_field_types_for_object(
        file_name=file_name,
        data=data,
        expected_field_types=expected_field_types,
    )


def _field_value(data: dict[str, Any], field_path: str) -> Any:
    current_value: Any = data
    for part in field_path.split("."):
        if not isinstance(current_value, dict) or part not in current_value:
            return _MissingField
        current_value = current_value[part]
    return current_value


class _MissingField:
    pass


def _matches_expected_type(value: Any, expected_type: str) -> bool:
    if expected_type == STRING_TYPE:
        return isinstance(value, str)
    if expected_type == NUMBER_TYPE:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == BOOLEAN_TYPE:
        return isinstance(value, bool)
    if expected_type == OBJECT_TYPE:
        return isinstance(value, dict)
    return False


def _actual_type_name(value: Any) -> str:
    if value is _MissingField:
        return "missing"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return BOOLEAN_TYPE
    if isinstance(value, str):
        return STRING_TYPE
    if isinstance(value, (int, float)):
        return NUMBER_TYPE
    if isinstance(value, dict):
        return OBJECT_TYPE
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def _file_status_code(error_codes: list[str]) -> str:
    if not error_codes:
        return FIELD_TYPES_OK
    return error_codes[0]


def _snapshot_status_code(
    file_statuses: tuple[Mt4FileFieldTypesStatus, ...],
) -> str:
    issue_types = {
        error_code
        for status in file_statuses
        for error_code in status.error_codes
    }

    if not issue_types:
        return ALL_FIELD_TYPES_VALID
    if len(issue_types) > 1:
        return MULTIPLE_FIELD_TYPE_ISSUES
    if REQUIRED_FIELDS_NOT_READY in issue_types:
        return SOME_REQUIRED_FIELDS_NOT_READY
    return SOME_FIELD_TYPES_INVALID


def _snapshot_reasons(
    file_statuses: tuple[Mt4FileFieldTypesStatus, ...],
) -> list[str]:
    reasons: list[str] = []
    for status in file_statuses:
        if status.status_code == REQUIRED_FIELDS_NOT_READY:
            reasons.append(f"{status.file_name}:{REQUIRED_FIELDS_NOT_READY}")
        if status.type_issues:
            reasons.append(
                f"{status.file_name}:{FIELD_TYPE_MISMATCH}:"
                f"{','.join(status.wrong_type_fields)}"
            )
    return reasons
