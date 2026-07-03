from app.services.mt4_field_types import (
    ALL_FIELD_TYPES_VALID,
    FIELD_TYPE_MISMATCH,
    FIELD_TYPES_OK,
    MULTIPLE_FIELD_TYPE_ISSUES,
    REQUIRED_FIELDS_NOT_READY,
    SOME_FIELD_TYPES_INVALID,
    SOME_REQUIRED_FIELDS_NOT_READY,
    Mt4FieldTypeIssue,
    Mt4FileFieldTypesStatus,
    Mt4SnapshotFieldTypesStatus,
    check_mt4_snapshot_field_types,
)
from app.services.mt4_file_reader import Mt4JsonReadResult
from app.services.mt4_required_fields import check_mt4_snapshot_required_fields
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
    Mt4SnapshotReadResult,
)


def _read_object(data: dict) -> Mt4JsonReadResult:
    return Mt4JsonReadResult(
        exists=True,
        is_file=True,
        is_json_valid=True,
        is_object=True,
        data=data,
    )


def _live_tick_payload() -> dict:
    return {
        "symbol": "XAUUSD",
        "bid": 2030.12,
        "ask": 2030.42,
        "spread": 0.30,
        "is_tradable": False,
    }


def _latest_bars_payload() -> dict:
    return {
        "symbol": "XAUUSD",
        "timeframes": {
            "M15": {},
            "H1": {},
            "H4": {},
            "D1": {},
        },
        "is_tradable": False,
    }


def _symbol_spec_payload() -> dict:
    return {
        "symbol": "XAUUSD",
        "tick_size": 0.01,
        "tick_value": 1.0,
        "lot_size": 100,
        "min_lot": 0.01,
        "lot_step": 0.01,
        "max_lot": 50,
        "is_tradable": False,
    }


def _account_snapshot_payload() -> dict:
    return {
        "account_currency": "USD",
        "balance": 10000,
        "equity": 10000,
        "free_margin": 9000,
        "daily_loss_pct": 0,
        "risk_limits": {
            "max_single_trade_loss_pct": 1.0,
            "max_daily_loss_pct": 3.0,
            "no_overnight": True,
        },
        "is_tradable": False,
    }


def _snapshot(
    *,
    live_tick: dict | None = None,
    latest_bars: dict | None = None,
    symbol_spec: dict | None = None,
    account_snapshot: dict | None = None,
) -> Mt4SnapshotReadResult:
    return Mt4SnapshotReadResult(
        live_tick=_read_object(live_tick or _live_tick_payload()),
        latest_bars=_read_object(latest_bars or _latest_bars_payload()),
        symbol_spec=_read_object(symbol_spec or _symbol_spec_payload()),
        account_snapshot=_read_object(account_snapshot or _account_snapshot_payload()),
    )


def _check(snapshot: Mt4SnapshotReadResult) -> Mt4SnapshotFieldTypesStatus:
    return check_mt4_snapshot_field_types(
        snapshot,
        check_mt4_snapshot_required_fields(snapshot),
    )


def test_field_types_all_files_valid() -> None:
    status = _check(_snapshot())

    assert isinstance(status, Mt4SnapshotFieldTypesStatus)
    assert isinstance(status.live_tick, Mt4FileFieldTypesStatus)
    assert status.all_field_types_valid is True
    assert status.can_proceed_to_value_checks is True
    assert status.status_code == ALL_FIELD_TYPES_VALID
    assert status.is_tradable is False
    assert status.live_tick.status_code == FIELD_TYPES_OK
    assert status.latest_bars.status_code == FIELD_TYPES_OK
    assert status.symbol_spec.status_code == FIELD_TYPES_OK
    assert status.account_snapshot.status_code == FIELD_TYPES_OK
    assert status.reasons == []


def test_field_types_live_tick_bid_string_is_wrong_type() -> None:
    payload = _live_tick_payload()
    payload["bid"] = "2030.12"

    status = _check(_snapshot(live_tick=payload))

    assert "bid" in status.live_tick.wrong_type_fields
    assert status.live_tick.type_issues == [
        Mt4FieldTypeIssue(
            field_path="bid",
            expected_type="number",
            actual_type="string",
        )
    ]
    assert status.live_tick.status_code == FIELD_TYPE_MISMATCH
    assert status.can_proceed_to_value_checks is False
    assert status.status_code == SOME_FIELD_TYPES_INVALID


def test_field_types_latest_bars_m15_array_is_wrong_type() -> None:
    payload = _latest_bars_payload()
    payload["timeframes"]["M15"] = []

    status = _check(_snapshot(latest_bars=payload))

    assert "timeframes.M15" in status.latest_bars.wrong_type_fields
    assert status.latest_bars.type_issues[0].expected_type == "object"
    assert status.latest_bars.type_issues[0].actual_type == "array"
    assert status.status_code == SOME_FIELD_TYPES_INVALID


def test_field_types_symbol_spec_tick_value_string_is_wrong_type() -> None:
    payload = _symbol_spec_payload()
    payload["tick_value"] = "1.0"

    status = _check(_snapshot(symbol_spec=payload))

    assert "tick_value" in status.symbol_spec.wrong_type_fields
    assert status.symbol_spec.type_issues[0].expected_type == "number"
    assert status.symbol_spec.type_issues[0].actual_type == "string"
    assert status.status_code == SOME_FIELD_TYPES_INVALID


def test_field_types_account_snapshot_no_overnight_string_is_wrong_type() -> None:
    payload = _account_snapshot_payload()
    payload["risk_limits"]["no_overnight"] = "true"

    status = _check(_snapshot(account_snapshot=payload))

    assert "risk_limits.no_overnight" in status.account_snapshot.wrong_type_fields
    assert status.account_snapshot.type_issues[0].expected_type == "boolean"
    assert status.account_snapshot.type_issues[0].actual_type == "string"
    assert status.status_code == SOME_FIELD_TYPES_INVALID


def test_field_types_number_rejects_bool() -> None:
    payload = _live_tick_payload()
    payload["bid"] = True

    status = _check(_snapshot(live_tick=payload))

    assert "bid" in status.live_tick.wrong_type_fields
    assert status.live_tick.type_issues[0].expected_type == "number"
    assert status.live_tick.type_issues[0].actual_type == "boolean"
    assert status.can_proceed_to_value_checks is False


def test_field_types_required_fields_not_ready_blocks_file() -> None:
    payload = _live_tick_payload()
    payload.pop("bid")
    snapshot = _snapshot(live_tick=payload)

    status = _check(snapshot)

    assert status.live_tick.status_code == REQUIRED_FIELDS_NOT_READY
    assert status.live_tick.error_codes == [REQUIRED_FIELDS_NOT_READY]
    assert status.live_tick.can_proceed_to_value_checks is False
    assert status.latest_bars.status_code == FIELD_TYPES_OK
    assert status.status_code == SOME_REQUIRED_FIELDS_NOT_READY


def test_field_types_multiple_issue_types() -> None:
    live_tick = _live_tick_payload()
    live_tick.pop("bid")
    symbol_spec = _symbol_spec_payload()
    symbol_spec["tick_value"] = "1.0"

    status = _check(_snapshot(live_tick=live_tick, symbol_spec=symbol_spec))

    assert status.live_tick.status_code == REQUIRED_FIELDS_NOT_READY
    assert "tick_value" in status.symbol_spec.wrong_type_fields
    assert status.status_code == MULTIPLE_FIELD_TYPE_ISSUES
    assert status.can_proceed_to_value_checks is False


def test_field_types_note_and_tradable_boundary() -> None:
    status = _check(_snapshot())

    assert status.is_tradable is False
    assert "Field type checks are not trading permission." in status.note
    assert "They do not generate trading signals." in status.note


def test_field_types_uses_constructed_results_only(tmp_path) -> None:
    status = _check(_snapshot())

    assert status.status_code == ALL_FIELD_TYPES_VALID
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")
    assert status.live_tick.file_name == LIVE_TICK_FILE
    assert status.latest_bars.file_name == LATEST_BARS_FILE
    assert status.symbol_spec.file_name == SYMBOL_SPEC_FILE
    assert status.account_snapshot.file_name == ACCOUNT_SNAPSHOT_FILE
