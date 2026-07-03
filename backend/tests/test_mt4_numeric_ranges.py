from app.services.mt4_field_types import check_mt4_snapshot_field_types
from app.services.mt4_file_reader import Mt4JsonReadResult
from app.services.mt4_numeric_ranges import (
    ALL_NUMERIC_RANGES_VALID,
    FIELD_TYPES_NOT_READY,
    GT_0,
    GTE_0,
    MULTIPLE_NUMERIC_RANGE_ISSUES,
    NO_NUMERIC_RANGE_RULES,
    NUMERIC_RANGE_VIOLATION,
    NUMERIC_RANGES_OK,
    SOME_FIELD_TYPES_NOT_READY,
    SOME_NUMERIC_RANGES_INVALID,
    Mt4FileNumericRangesStatus,
    Mt4NumericRangeIssue,
    Mt4SnapshotNumericRangesStatus,
    check_mt4_snapshot_numeric_ranges,
)
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


def _check(snapshot: Mt4SnapshotReadResult) -> Mt4SnapshotNumericRangesStatus:
    required_fields_status = check_mt4_snapshot_required_fields(snapshot)
    field_types_status = check_mt4_snapshot_field_types(
        snapshot,
        required_fields_status,
    )
    return check_mt4_snapshot_numeric_ranges(snapshot, field_types_status)


def test_numeric_ranges_all_files_valid() -> None:
    status = _check(_snapshot())

    assert isinstance(status, Mt4SnapshotNumericRangesStatus)
    assert isinstance(status.live_tick, Mt4FileNumericRangesStatus)
    assert status.all_numeric_ranges_valid is True
    assert status.can_proceed_to_cross_field_checks is True
    assert status.status_code == ALL_NUMERIC_RANGES_VALID
    assert status.is_tradable is False
    assert status.live_tick.status_code == NUMERIC_RANGES_OK
    assert status.latest_bars.status_code == NO_NUMERIC_RANGE_RULES
    assert status.symbol_spec.status_code == NUMERIC_RANGES_OK
    assert status.account_snapshot.status_code == NUMERIC_RANGES_OK
    assert status.reasons == []


def test_numeric_ranges_live_tick_bid_zero_violates_gt_0() -> None:
    payload = _live_tick_payload()
    payload["bid"] = 0

    status = _check(_snapshot(live_tick=payload))

    assert "bid" in status.live_tick.invalid_fields
    assert status.live_tick.range_issues == [
        Mt4NumericRangeIssue(field_path="bid", rule=GT_0, actual_value=0.0)
    ]
    assert status.live_tick.status_code == NUMERIC_RANGE_VIOLATION
    assert status.can_proceed_to_cross_field_checks is False
    assert status.status_code == SOME_NUMERIC_RANGES_INVALID


def test_numeric_ranges_live_tick_spread_negative_violates_gte_0() -> None:
    payload = _live_tick_payload()
    payload["spread"] = -1

    status = _check(_snapshot(live_tick=payload))

    assert "spread" in status.live_tick.invalid_fields
    assert status.live_tick.range_issues[0].rule == GTE_0
    assert status.live_tick.range_issues[0].actual_value == -1.0


def test_numeric_ranges_symbol_spec_tick_size_zero_violates_gt_0() -> None:
    payload = _symbol_spec_payload()
    payload["tick_size"] = 0

    status = _check(_snapshot(symbol_spec=payload))

    assert "tick_size" in status.symbol_spec.invalid_fields
    assert status.symbol_spec.range_issues[0].rule == GT_0
    assert status.status_code == SOME_NUMERIC_RANGES_INVALID


def test_numeric_ranges_symbol_spec_min_lot_negative_is_invalid() -> None:
    payload = _symbol_spec_payload()
    payload["min_lot"] = -0.01

    status = _check(_snapshot(symbol_spec=payload))

    assert "min_lot" in status.symbol_spec.invalid_fields
    assert status.symbol_spec.range_issues[0].rule == GT_0


def test_numeric_ranges_account_balance_negative_violates_gte_0() -> None:
    payload = _account_snapshot_payload()
    payload["balance"] = -1

    status = _check(_snapshot(account_snapshot=payload))

    assert "balance" in status.account_snapshot.invalid_fields
    assert status.account_snapshot.range_issues[0].rule == GTE_0
    assert status.account_snapshot.range_issues[0].actual_value == -1.0


def test_numeric_ranges_account_max_daily_loss_zero_violates_gt_0() -> None:
    payload = _account_snapshot_payload()
    payload["risk_limits"]["max_daily_loss_pct"] = 0

    status = _check(_snapshot(account_snapshot=payload))

    assert (
        "risk_limits.max_daily_loss_pct"
        in status.account_snapshot.invalid_fields
    )
    assert status.account_snapshot.range_issues[0].rule == GT_0
    assert status.account_snapshot.range_issues[0].actual_value == 0.0


def test_numeric_ranges_latest_bars_has_no_numeric_rules() -> None:
    status = _check(_snapshot())

    assert status.latest_bars.status_code == NO_NUMERIC_RANGE_RULES
    assert status.latest_bars.checked_fields == []
    assert status.latest_bars.can_proceed_to_cross_field_checks is True
    assert status.latest_bars.all_numeric_ranges_valid is True


def test_numeric_ranges_field_types_not_ready_blocks_file() -> None:
    payload = _live_tick_payload()
    payload["bid"] = "2030.12"

    status = _check(_snapshot(live_tick=payload))

    assert status.live_tick.status_code == FIELD_TYPES_NOT_READY
    assert status.live_tick.error_codes == [FIELD_TYPES_NOT_READY]
    assert status.live_tick.can_proceed_to_cross_field_checks is False
    assert status.status_code == SOME_FIELD_TYPES_NOT_READY


def test_numeric_ranges_multiple_issue_types() -> None:
    live_tick = _live_tick_payload()
    live_tick["bid"] = "2030.12"
    symbol_spec = _symbol_spec_payload()
    symbol_spec["tick_size"] = 0

    status = _check(_snapshot(live_tick=live_tick, symbol_spec=symbol_spec))

    assert status.live_tick.status_code == FIELD_TYPES_NOT_READY
    assert "tick_size" in status.symbol_spec.invalid_fields
    assert status.status_code == MULTIPLE_NUMERIC_RANGE_ISSUES
    assert status.can_proceed_to_cross_field_checks is False


def test_numeric_ranges_note_and_tradable_boundary() -> None:
    status = _check(_snapshot())

    assert status.is_tradable is False
    assert "Numeric range checks are not trading permission." in status.note
    assert "They do not generate trading signals." in status.note


def test_numeric_ranges_uses_constructed_results_only(tmp_path) -> None:
    status = _check(_snapshot())

    assert status.status_code == ALL_NUMERIC_RANGES_VALID
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")
    assert status.live_tick.file_name == LIVE_TICK_FILE
    assert status.latest_bars.file_name == LATEST_BARS_FILE
    assert status.symbol_spec.file_name == SYMBOL_SPEC_FILE
    assert status.account_snapshot.file_name == ACCOUNT_SNAPSHOT_FILE
