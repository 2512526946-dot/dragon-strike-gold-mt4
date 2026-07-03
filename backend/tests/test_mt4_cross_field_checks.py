from app.services.mt4_cross_field_checks import (
    ALL_CROSS_FIELD_CHECKS_VALID,
    ASK_GTE_BID,
    CROSS_FIELD_CHECKS_OK,
    CROSS_FIELD_RULE_VIOLATION,
    LOT_STEP_LTE_MAX_LOT,
    MAX_DAILY_LOSS_PCT_GTE_MAX_SINGLE_TRADE_LOSS_PCT,
    MAX_LOT_GTE_MIN_LOT,
    NO_CROSS_FIELD_RULES,
    NUMERIC_RANGES_NOT_READY,
    SOME_CROSS_FIELD_CHECKS_INVALID,
    SOME_NUMERIC_RANGES_NOT_READY,
    Mt4FileCrossFieldStatus,
    Mt4SnapshotCrossFieldStatus,
    check_mt4_snapshot_cross_fields,
)
from app.services.mt4_field_types import check_mt4_snapshot_field_types
from app.services.mt4_file_reader import Mt4JsonReadResult
from app.services.mt4_numeric_ranges import check_mt4_snapshot_numeric_ranges
from app.services.mt4_required_fields import check_mt4_snapshot_required_fields
from app.services.mt4_snapshot_reader import Mt4SnapshotReadResult


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


def _check(snapshot: Mt4SnapshotReadResult) -> Mt4SnapshotCrossFieldStatus:
    required_fields_status = check_mt4_snapshot_required_fields(snapshot)
    field_types_status = check_mt4_snapshot_field_types(
        snapshot,
        required_fields_status,
    )
    numeric_ranges_status = check_mt4_snapshot_numeric_ranges(
        snapshot,
        field_types_status,
    )
    return check_mt4_snapshot_cross_fields(snapshot, numeric_ranges_status)


def test_cross_field_checks_all_files_valid() -> None:
    status = _check(_snapshot())

    assert isinstance(status, Mt4SnapshotCrossFieldStatus)
    assert isinstance(status.live_tick, Mt4FileCrossFieldStatus)
    assert status.status_code == ALL_CROSS_FIELD_CHECKS_VALID
    assert status.all_cross_field_checks_valid is True
    assert status.can_proceed_to_data_quality_gate_finalization is True
    assert status.is_tradable is False
    assert status.live_tick.status_code == CROSS_FIELD_CHECKS_OK
    assert status.latest_bars.status_code == NO_CROSS_FIELD_RULES
    assert status.symbol_spec.status_code == CROSS_FIELD_CHECKS_OK
    assert status.account_snapshot.status_code == CROSS_FIELD_CHECKS_OK
    assert status.reasons == []


def test_cross_field_checks_live_tick_ask_must_be_gte_bid() -> None:
    live_tick = _live_tick_payload()
    live_tick["ask"] = live_tick["bid"] - 0.01

    status = _check(_snapshot(live_tick=live_tick))

    assert status.live_tick.status_code == CROSS_FIELD_RULE_VIOLATION
    assert status.live_tick.violated_rules == [ASK_GTE_BID]
    assert status.live_tick.can_proceed_to_data_quality_gate_finalization is False
    assert status.status_code == SOME_CROSS_FIELD_CHECKS_INVALID
    assert status.can_proceed_to_data_quality_gate_finalization is False


def test_cross_field_checks_symbol_spec_max_lot_must_be_gte_min_lot() -> None:
    symbol_spec = _symbol_spec_payload()
    symbol_spec["min_lot"] = 1.0
    symbol_spec["max_lot"] = 0.5

    status = _check(_snapshot(symbol_spec=symbol_spec))

    assert status.symbol_spec.status_code == CROSS_FIELD_RULE_VIOLATION
    assert MAX_LOT_GTE_MIN_LOT in status.symbol_spec.violated_rules
    assert status.status_code == SOME_CROSS_FIELD_CHECKS_INVALID


def test_cross_field_checks_symbol_spec_lot_step_must_be_lte_max_lot() -> None:
    symbol_spec = _symbol_spec_payload()
    symbol_spec["lot_step"] = 2.0
    symbol_spec["max_lot"] = 1.0

    status = _check(_snapshot(symbol_spec=symbol_spec))

    assert status.symbol_spec.status_code == CROSS_FIELD_RULE_VIOLATION
    assert LOT_STEP_LTE_MAX_LOT in status.symbol_spec.violated_rules
    assert status.status_code == SOME_CROSS_FIELD_CHECKS_INVALID


def test_cross_field_checks_account_daily_limit_must_be_gte_single_limit() -> None:
    account_snapshot = _account_snapshot_payload()
    account_snapshot["risk_limits"]["max_single_trade_loss_pct"] = 3.0
    account_snapshot["risk_limits"]["max_daily_loss_pct"] = 1.0

    status = _check(_snapshot(account_snapshot=account_snapshot))

    assert status.account_snapshot.status_code == CROSS_FIELD_RULE_VIOLATION
    assert (
        MAX_DAILY_LOSS_PCT_GTE_MAX_SINGLE_TRADE_LOSS_PCT
        in status.account_snapshot.violated_rules
    )
    assert status.status_code == SOME_CROSS_FIELD_CHECKS_INVALID


def test_cross_field_checks_latest_bars_has_no_cross_field_rules() -> None:
    status = _check(_snapshot())

    assert status.latest_bars.status_code == NO_CROSS_FIELD_RULES
    assert status.latest_bars.checked_rules == []
    assert status.latest_bars.violated_rules == []
    assert status.latest_bars.all_cross_field_checks_valid is True
    assert (
        status.latest_bars.can_proceed_to_data_quality_gate_finalization
        is True
    )


def test_cross_field_checks_numeric_ranges_not_ready_blocks_file() -> None:
    live_tick = _live_tick_payload()
    live_tick["bid"] = 0

    status = _check(_snapshot(live_tick=live_tick))

    assert status.live_tick.status_code == NUMERIC_RANGES_NOT_READY
    assert status.live_tick.error_codes == [NUMERIC_RANGES_NOT_READY]
    assert status.live_tick.checked_rules == []
    assert status.status_code == SOME_NUMERIC_RANGES_NOT_READY
    assert status.can_proceed_to_data_quality_gate_finalization is False


def test_cross_field_checks_do_not_compare_spread_to_ask_minus_bid() -> None:
    live_tick = _live_tick_payload()
    live_tick["bid"] = 100
    live_tick["ask"] = 101
    live_tick["spread"] = 999

    status = _check(_snapshot(live_tick=live_tick))

    assert status.live_tick.status_code == CROSS_FIELD_CHECKS_OK
    assert status.live_tick.violated_rules == []
    assert status.status_code == ALL_CROSS_FIELD_CHECKS_VALID


def test_cross_field_checks_do_not_validate_latest_bars_price_shape() -> None:
    latest_bars = _latest_bars_payload()
    latest_bars["timeframes"]["M15"] = {
        "open": 100,
        "high": 10,
        "low": 500,
        "close": 200,
    }

    status = _check(_snapshot(latest_bars=latest_bars))

    assert status.latest_bars.status_code == NO_CROSS_FIELD_RULES
    assert status.status_code == ALL_CROSS_FIELD_CHECKS_VALID


def test_cross_field_checks_note_and_tradable_boundary() -> None:
    status = _check(_snapshot())

    assert status.is_tradable is False
    assert "Cross field checks are not trading permission." in status.note
    assert "They do not generate trading signals." in status.note


def test_cross_field_checks_use_constructed_results_only(tmp_path) -> None:
    status = _check(_snapshot())

    assert status.status_code == ALL_CROSS_FIELD_CHECKS_VALID
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")
