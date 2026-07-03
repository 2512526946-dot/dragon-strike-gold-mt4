from app.services.mt4_file_reader import FILE_NOT_FOUND, Mt4JsonReadResult
from app.services.mt4_required_fields import (
    ALL_REQUIRED_FIELDS_PRESENT,
    MULTIPLE_REQUIRED_FIELD_ISSUES,
    NULL_REQUIRED_FIELDS,
    READ_RESULT_NOT_READY,
    REQUIRED_FIELDS_OK,
    SOME_FILES_NOT_READY,
    SOME_REQUIRED_FIELDS_MISSING,
    SOME_REQUIRED_FIELDS_NULL,
    Mt4FileRequiredFieldsStatus,
    Mt4SnapshotRequiredFieldsStatus,
    check_mt4_snapshot_required_fields,
)
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


def _not_ready_result() -> Mt4JsonReadResult:
    return Mt4JsonReadResult(
        exists=False,
        is_file=False,
        is_json_valid=False,
        is_object=False,
        data=None,
        error_code=FILE_NOT_FOUND,
        error_message="File does not exist: test-only-path/live_tick.json",
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
            "M15": [],
            "H1": [],
            "H4": [],
            "D1": [],
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
    live_tick: dict | Mt4JsonReadResult | None = None,
    latest_bars: dict | Mt4JsonReadResult | None = None,
    symbol_spec: dict | Mt4JsonReadResult | None = None,
    account_snapshot: dict | Mt4JsonReadResult | None = None,
) -> Mt4SnapshotReadResult:
    return Mt4SnapshotReadResult(
        live_tick=_coerce_result(live_tick, _live_tick_payload()),
        latest_bars=_coerce_result(latest_bars, _latest_bars_payload()),
        symbol_spec=_coerce_result(symbol_spec, _symbol_spec_payload()),
        account_snapshot=_coerce_result(account_snapshot, _account_snapshot_payload()),
    )


def _coerce_result(
    override: dict | Mt4JsonReadResult | None,
    default_payload: dict,
) -> Mt4JsonReadResult:
    if isinstance(override, Mt4JsonReadResult):
        return override
    if override is not None:
        return _read_object(override)
    return _read_object(default_payload)


def test_required_fields_all_files_present() -> None:
    status = check_mt4_snapshot_required_fields(_snapshot())

    assert isinstance(status, Mt4SnapshotRequiredFieldsStatus)
    assert isinstance(status.live_tick, Mt4FileRequiredFieldsStatus)
    assert status.all_required_fields_present is True
    assert status.can_proceed_to_value_checks is True
    assert status.status_code == ALL_REQUIRED_FIELDS_PRESENT
    assert status.is_tradable is False
    assert status.live_tick.status_code == REQUIRED_FIELDS_OK
    assert status.latest_bars.status_code == REQUIRED_FIELDS_OK
    assert status.symbol_spec.status_code == REQUIRED_FIELDS_OK
    assert status.account_snapshot.status_code == REQUIRED_FIELDS_OK
    assert status.reasons == []


def test_required_fields_live_tick_missing_bid() -> None:
    payload = _live_tick_payload()
    payload.pop("bid")

    status = check_mt4_snapshot_required_fields(_snapshot(live_tick=payload))

    assert "bid" in status.live_tick.missing_fields
    assert status.live_tick.can_proceed_to_value_checks is False
    assert status.can_proceed_to_value_checks is False
    assert status.status_code == SOME_REQUIRED_FIELDS_MISSING


def test_required_fields_latest_bars_missing_h1() -> None:
    payload = _latest_bars_payload()
    payload["timeframes"].pop("H1")

    status = check_mt4_snapshot_required_fields(_snapshot(latest_bars=payload))

    assert "timeframes.H1" in status.latest_bars.missing_fields
    assert status.status_code == SOME_REQUIRED_FIELDS_MISSING


def test_required_fields_symbol_spec_missing_tick_value() -> None:
    payload = _symbol_spec_payload()
    payload.pop("tick_value")

    status = check_mt4_snapshot_required_fields(_snapshot(symbol_spec=payload))

    assert "tick_value" in status.symbol_spec.missing_fields
    assert status.status_code == SOME_REQUIRED_FIELDS_MISSING


def test_required_fields_account_snapshot_missing_nested_risk_limit() -> None:
    payload = _account_snapshot_payload()
    payload["risk_limits"].pop("max_daily_loss_pct")

    status = check_mt4_snapshot_required_fields(_snapshot(account_snapshot=payload))

    assert (
        "risk_limits.max_daily_loss_pct"
        in status.account_snapshot.missing_fields
    )
    assert status.status_code == SOME_REQUIRED_FIELDS_MISSING


def test_required_fields_detects_null_field() -> None:
    payload = _live_tick_payload()
    payload["bid"] = None

    status = check_mt4_snapshot_required_fields(_snapshot(live_tick=payload))

    assert "bid" in status.live_tick.null_fields
    assert status.live_tick.status_code == NULL_REQUIRED_FIELDS
    assert status.status_code == SOME_REQUIRED_FIELDS_NULL
    assert status.can_proceed_to_value_checks is False


def test_required_fields_read_result_not_ready() -> None:
    status = check_mt4_snapshot_required_fields(
        _snapshot(live_tick=_not_ready_result())
    )

    assert status.live_tick.status_code == READ_RESULT_NOT_READY
    assert status.live_tick.error_codes == [READ_RESULT_NOT_READY]
    assert status.live_tick.can_proceed_to_value_checks is False
    assert status.status_code == SOME_FILES_NOT_READY
    assert status.latest_bars.status_code == REQUIRED_FIELDS_OK


def test_required_fields_multiple_issue_types() -> None:
    live_tick = _live_tick_payload()
    live_tick.pop("bid")
    symbol_spec = _symbol_spec_payload()
    symbol_spec["tick_value"] = None

    status = check_mt4_snapshot_required_fields(
        _snapshot(live_tick=live_tick, symbol_spec=symbol_spec)
    )

    assert status.live_tick.missing_fields == ["bid"]
    assert status.symbol_spec.null_fields == ["tick_value"]
    assert status.status_code == MULTIPLE_REQUIRED_FIELD_ISSUES
    assert status.can_proceed_to_value_checks is False


def test_required_fields_note_and_tradable_boundary() -> None:
    status = check_mt4_snapshot_required_fields(_snapshot())

    assert status.is_tradable is False
    assert "Required field presence checks are not trading permission." in status.note
    assert "They do not generate trading signals." in status.note


def test_required_fields_uses_constructed_results_only(tmp_path) -> None:
    status = check_mt4_snapshot_required_fields(_snapshot())

    assert status.status_code == ALL_REQUIRED_FIELDS_PRESENT
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")
    assert status.live_tick.file_name == LIVE_TICK_FILE
    assert status.latest_bars.file_name == LATEST_BARS_FILE
    assert status.symbol_spec.file_name == SYMBOL_SPEC_FILE
    assert status.account_snapshot.file_name == ACCOUNT_SNAPSHOT_FILE
