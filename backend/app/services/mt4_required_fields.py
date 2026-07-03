from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.mt4_file_reader import Mt4JsonReadResult
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
    Mt4SnapshotReadResult,
)


REQUIRED_FIELDS_OK = "REQUIRED_FIELDS_OK"
READ_RESULT_NOT_READY = "READ_RESULT_NOT_READY"
MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
NULL_REQUIRED_FIELDS = "NULL_REQUIRED_FIELDS"

ALL_REQUIRED_FIELDS_PRESENT = "ALL_REQUIRED_FIELDS_PRESENT"
SOME_FILES_NOT_READY = "SOME_FILES_NOT_READY"
SOME_REQUIRED_FIELDS_MISSING = "SOME_REQUIRED_FIELDS_MISSING"
SOME_REQUIRED_FIELDS_NULL = "SOME_REQUIRED_FIELDS_NULL"
MULTIPLE_REQUIRED_FIELD_ISSUES = "MULTIPLE_REQUIRED_FIELD_ISSUES"

REQUIRED_FIELD_NOTE = (
    "Required field presence checks are not trading permission. "
    "They do not generate trading signals."
)

LIVE_TICK_REQUIRED_FIELDS = [
    "symbol",
    "bid",
    "ask",
    "spread",
    "is_tradable",
]

LATEST_BARS_REQUIRED_FIELDS = [
    "symbol",
    "timeframes",
    "timeframes.M15",
    "timeframes.H1",
    "timeframes.H4",
    "timeframes.D1",
    "is_tradable",
]

SYMBOL_SPEC_REQUIRED_FIELDS = [
    "symbol",
    "tick_size",
    "tick_value",
    "lot_size",
    "min_lot",
    "lot_step",
    "max_lot",
    "is_tradable",
]

ACCOUNT_SNAPSHOT_REQUIRED_FIELDS = [
    "account_currency",
    "balance",
    "equity",
    "free_margin",
    "daily_loss_pct",
    "risk_limits",
    "risk_limits.max_single_trade_loss_pct",
    "risk_limits.max_daily_loss_pct",
    "risk_limits.no_overnight",
    "is_tradable",
]


@dataclass(frozen=True)
class Mt4FileRequiredFieldsStatus:
    file_name: str
    required_fields: list[str]
    present_fields: list[str]
    missing_fields: list[str]
    null_fields: list[str]
    all_required_fields_present: bool
    can_proceed_to_value_checks: bool
    status_code: str
    error_codes: list[str]


@dataclass(frozen=True)
class Mt4SnapshotRequiredFieldsStatus:
    live_tick: Mt4FileRequiredFieldsStatus
    latest_bars: Mt4FileRequiredFieldsStatus
    symbol_spec: Mt4FileRequiredFieldsStatus
    account_snapshot: Mt4FileRequiredFieldsStatus
    all_required_fields_present: bool
    can_proceed_to_value_checks: bool
    status_code: str
    reasons: list[str]
    is_tradable: bool
    note: str


def check_required_fields_for_object(
    file_name: str,
    data: dict[str, Any],
    required_fields: list[str],
) -> Mt4FileRequiredFieldsStatus:
    present_fields: list[str] = []
    missing_fields: list[str] = []
    null_fields: list[str] = []

    for field_path in required_fields:
        field_state = _field_state(data, field_path)
        if field_state == "present":
            present_fields.append(field_path)
        elif field_state == "null":
            null_fields.append(field_path)
        else:
            missing_fields.append(field_path)

    error_codes = _file_error_codes(
        missing_fields=missing_fields,
        null_fields=null_fields,
    )

    return Mt4FileRequiredFieldsStatus(
        file_name=file_name,
        required_fields=required_fields,
        present_fields=present_fields,
        missing_fields=missing_fields,
        null_fields=null_fields,
        all_required_fields_present=len(error_codes) == 0,
        can_proceed_to_value_checks=len(error_codes) == 0,
        status_code=_file_status_code(error_codes),
        error_codes=error_codes,
    )


def check_mt4_snapshot_required_fields(
    snapshot: Mt4SnapshotReadResult,
) -> Mt4SnapshotRequiredFieldsStatus:
    live_tick = _check_file_read_result(
        LIVE_TICK_FILE,
        snapshot.live_tick,
        LIVE_TICK_REQUIRED_FIELDS,
    )
    latest_bars = _check_file_read_result(
        LATEST_BARS_FILE,
        snapshot.latest_bars,
        LATEST_BARS_REQUIRED_FIELDS,
    )
    symbol_spec = _check_file_read_result(
        SYMBOL_SPEC_FILE,
        snapshot.symbol_spec,
        SYMBOL_SPEC_REQUIRED_FIELDS,
    )
    account_snapshot = _check_file_read_result(
        ACCOUNT_SNAPSHOT_FILE,
        snapshot.account_snapshot,
        ACCOUNT_SNAPSHOT_REQUIRED_FIELDS,
    )

    file_statuses = (live_tick, latest_bars, symbol_spec, account_snapshot)
    all_required_fields_present = all(
        status.all_required_fields_present for status in file_statuses
    )

    return Mt4SnapshotRequiredFieldsStatus(
        live_tick=live_tick,
        latest_bars=latest_bars,
        symbol_spec=symbol_spec,
        account_snapshot=account_snapshot,
        all_required_fields_present=all_required_fields_present,
        can_proceed_to_value_checks=all_required_fields_present,
        status_code=_snapshot_status_code(file_statuses),
        reasons=_snapshot_reasons(file_statuses),
        is_tradable=False,
        note=REQUIRED_FIELD_NOTE,
    )


def _check_file_read_result(
    file_name: str,
    read_result: Mt4JsonReadResult,
    required_fields: list[str],
) -> Mt4FileRequiredFieldsStatus:
    if not read_result.is_object or read_result.data is None:
        return Mt4FileRequiredFieldsStatus(
            file_name=file_name,
            required_fields=required_fields,
            present_fields=[],
            missing_fields=[],
            null_fields=[],
            all_required_fields_present=False,
            can_proceed_to_value_checks=False,
            status_code=READ_RESULT_NOT_READY,
            error_codes=[READ_RESULT_NOT_READY],
        )

    return check_required_fields_for_object(
        file_name=file_name,
        data=read_result.data,
        required_fields=required_fields,
    )


def _field_state(data: dict[str, Any], field_path: str) -> str:
    current_value: Any = data

    for part in field_path.split("."):
        if not isinstance(current_value, dict) or part not in current_value:
            return "missing"
        current_value = current_value[part]
        if current_value is None:
            return "null"

    return "present"


def _file_error_codes(
    *,
    missing_fields: list[str],
    null_fields: list[str],
) -> list[str]:
    error_codes: list[str] = []
    if missing_fields:
        error_codes.append(MISSING_REQUIRED_FIELDS)
    if null_fields:
        error_codes.append(NULL_REQUIRED_FIELDS)
    return error_codes


def _file_status_code(error_codes: list[str]) -> str:
    if not error_codes:
        return REQUIRED_FIELDS_OK
    return error_codes[0]


def _snapshot_status_code(
    file_statuses: tuple[Mt4FileRequiredFieldsStatus, ...],
) -> str:
    issue_types = {
        status_code
        for status in file_statuses
        for status_code in status.error_codes
    }

    if not issue_types:
        return ALL_REQUIRED_FIELDS_PRESENT
    if len(issue_types) > 1:
        return MULTIPLE_REQUIRED_FIELD_ISSUES
    if READ_RESULT_NOT_READY in issue_types:
        return SOME_FILES_NOT_READY
    if MISSING_REQUIRED_FIELDS in issue_types:
        return SOME_REQUIRED_FIELDS_MISSING
    return SOME_REQUIRED_FIELDS_NULL


def _snapshot_reasons(
    file_statuses: tuple[Mt4FileRequiredFieldsStatus, ...],
) -> list[str]:
    reasons: list[str] = []
    for status in file_statuses:
        if status.status_code == READ_RESULT_NOT_READY:
            reasons.append(f"{status.file_name}:{READ_RESULT_NOT_READY}")
        if status.missing_fields:
            reasons.append(
                f"{status.file_name}:{MISSING_REQUIRED_FIELDS}:"
                f"{','.join(status.missing_fields)}"
            )
        if status.null_fields:
            reasons.append(
                f"{status.file_name}:{NULL_REQUIRED_FIELDS}:"
                f"{','.join(status.null_fields)}"
            )
    return reasons
