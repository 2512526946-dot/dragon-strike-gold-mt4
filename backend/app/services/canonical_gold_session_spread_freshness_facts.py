from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re

from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldBarFactsV1,
    CanonicalGoldFreshnessFactsV1,
    CanonicalGoldMarketFactsSnapshotV1,
    CanonicalGoldQuoteFactsV1,
    CanonicalGoldSymbolFactsV1,
    CanonicalGoldTimeframeFactsV1,
)


@dataclass(frozen=True, slots=True)
class CanonicalGoldSessionFactsV1:
    utc_weekday_code: str
    utc_second_of_day: int
    session_bucket_code: str
    window_start_second_utc: int
    window_end_second_utc: int
    seconds_since_window_start: int
    seconds_until_window_end: int
    observed_writer_session_status_label: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldSpreadFactsV1:
    bid_decimal: str
    ask_decimal: str
    mid_decimal: str
    spread_decimal: str
    spread_points: int
    digits: int
    point_decimal: str
    spread_to_mid_ppm_decimal: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldSourceFreshnessFactsV1:
    tick_age_microseconds: int
    bars_payload_age_microseconds: int
    symbol_spec_age_microseconds: int
    maximum_source_age_microseconds: int
    oldest_source_component_code: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldSessionSpreadFreshnessFactsV1:
    contract_version: str
    facts_profile_version: str
    passed: bool
    status_code: str
    reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    identity_available: bool
    bundle_schema_version: str | None
    bundle_id: str | None
    sequence: int | None
    canonical_symbol: str | None
    broker_symbol: str | None
    reference_time_utc: str | None
    session: CanonicalGoldSessionFactsV1 | None
    spread: CanonicalGoldSpreadFactsV1 | None
    freshness: CanonicalGoldSourceFreshnessFactsV1 | None
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool


__all__ = (
    "CanonicalGoldSessionSpreadFreshnessFactsV1",
    "CanonicalGoldSessionFactsV1",
    "CanonicalGoldSpreadFactsV1",
    "CanonicalGoldSourceFreshnessFactsV1",
    "build_canonical_gold_session_spread_freshness_facts_v1",
)


_CONTRACT_VERSION = "1.0"
_FACTS_PROFILE_VERSION = "canonical_gold_session_spread_freshness_profile_v1"
_READY_STATUS = "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_READY"
_INPUT_INVALID_STATUS = "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID"
_UPSTREAM_BLOCKED_STATUS = "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_UPSTREAM_BLOCKED"
_IDENTITY_INVALID_STATUS = "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_IDENTITY_INVALID"
_SESSION_INVALID_STATUS = "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID"
_SPREAD_INVALID_STATUS = "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID"
_FRESHNESS_INVALID_STATUS = "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID"
_SAFE_FAILURE_STATUS = "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SAFE_FAILURE"

_INPUT_TYPE_INVALID = "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID"
_SNAPSHOT_NOT_READY = "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_NOT_READY"
_SNAPSHOT_IDENTITY_INVALID = "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_IDENTITY_INVALID"
_SESSION_INVALID = "GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID"
_SPREAD_INVALID = "GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID"
_FRESHNESS_INVALID = "GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID"
_EXCEPTION_SANITIZED = "GOLD_SESSION_SPREAD_FRESHNESS_EXCEPTION_SANITIZED"

_G175_READY_STATUS = "CANONICAL_GOLD_MARKET_FACTS_READY"
_BUNDLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{16,64}$", re.ASCII)
_SAFE_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$", re.ASCII)
_UTC_Z_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$",
    re.ASCII,
)
_TIMEFRAME_PERIODS = (("M15", 900), ("H1", 3600), ("H4", 14400), ("D1", 86400))
_SESSION_WINDOWS = (
    ("ASIA_UTC", 0, 28800),
    ("LONDON_UTC", 28800, 46800),
    ("LONDON_NEW_YORK_OVERLAP_UTC", 46800, 57600),
    ("NEW_YORK_UTC", 57600, 79200),
    ("OFF_HOURS_UTC", 79200, 86400),
)
_WEEKDAY_CODES = (
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
)

_SNAPSHOT_FIELDS = (
    "contract_version",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
    "identity_available",
    "bundle_schema_version",
    "bundle_id",
    "sequence",
    "canonical_symbol",
    "broker_symbol",
    "reference_time_utc",
    "quote",
    "timeframes",
    "symbol_spec",
    "freshness",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
_QUOTE_FIELDS = (
    "bid_decimal",
    "ask_decimal",
    "spread_decimal",
    "spread_points",
    "digits",
    "point_decimal",
    "tick_time_utc",
)
_TIMEFRAME_FIELDS = ("timeframe", "period_seconds", "bars")
_BAR_FIELDS = (
    "open_time_utc",
    "open_decimal",
    "high_decimal",
    "low_decimal",
    "close_decimal",
    "tick_volume",
    "spread_points",
)
_SYMBOL_FIELDS = (
    "spec_time_utc",
    "digits",
    "point_decimal",
    "tick_size_decimal",
    "tick_value_decimal",
    "contract_size_decimal",
    "min_lot_decimal",
    "lot_step_decimal",
    "max_lot_decimal",
    "base_currency",
    "profit_currency",
    "margin_currency",
    "trade_mode_readonly_label",
    "session_status_readonly_label",
)
_FRESHNESS_FIELDS = (
    "tick_age_microseconds",
    "bars_payload_age_microseconds",
    "symbol_spec_age_microseconds",
)


def build_canonical_gold_session_spread_freshness_facts_v1(
    *,
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,
) -> CanonicalGoldSessionSpreadFreshnessFactsV1:
    try:
        if not _has_exact_input_shape(market_facts_snapshot):
            return _failure(_INPUT_INVALID_STATUS, _INPUT_TYPE_INVALID)
        if not _has_ready_authority(market_facts_snapshot):
            return _failure(_UPSTREAM_BLOCKED_STATUS, _SNAPSHOT_NOT_READY)
        if not _has_valid_upstream_values(market_facts_snapshot):
            return _failure(_UPSTREAM_BLOCKED_STATUS, _SNAPSHOT_NOT_READY)
        if not _has_valid_identity(market_facts_snapshot):
            return _failure(_IDENTITY_INVALID_STATUS, _SNAPSHOT_IDENTITY_INVALID)
        reference_time = _parse_utc_z(market_facts_snapshot.reference_time_utc)
        if reference_time is None or not _has_valid_session_input(market_facts_snapshot):
            return _failure(_SESSION_INVALID_STATUS, _SESSION_INVALID)
        if not _has_valid_spread_input(market_facts_snapshot):
            return _failure(_SPREAD_INVALID_STATUS, _SPREAD_INVALID)
        if not _has_valid_freshness_input(market_facts_snapshot, reference_time):
            return _failure(_FRESHNESS_INVALID_STATUS, _FRESHNESS_INVALID)
        return _ready_result(market_facts_snapshot, reference_time)
    except Exception:
        return _failure(_SAFE_FAILURE_STATUS, _EXCEPTION_SANITIZED)


def _has_exact_input_shape(value: object) -> bool:
    if not _is_exact_record(value, CanonicalGoldMarketFactsSnapshotV1, _SNAPSHOT_FIELDS):
        return False
    snapshot = value
    if not (
        type(snapshot.contract_version) is str
        and type(snapshot.passed) is bool
        and type(snapshot.status_code) is str
        and _is_string_tuple(snapshot.reason_codes)
        and _is_string_tuple(snapshot.warning_codes)
        and type(snapshot.identity_available) is bool
        and _is_optional_str(snapshot.bundle_schema_version)
        and _is_optional_str(snapshot.bundle_id)
        and _is_optional_int(snapshot.sequence)
        and _is_optional_str(snapshot.canonical_symbol)
        and _is_optional_str(snapshot.broker_symbol)
        and _is_optional_str(snapshot.reference_time_utc)
        and type(snapshot.timeframes) is tuple
        and type(snapshot.read_only) is bool
        and type(snapshot.demo_only) is bool
        and type(snapshot.is_tradable) is bool
        and type(snapshot.can_execute) is bool
        and type(snapshot.is_trading_permission) is bool
        and type(snapshot.is_execution_instruction) is bool
        and type(snapshot.allowed_to_call_ea) is bool
        and type(snapshot.allowed_to_modify_risk) is bool
    ):
        return False
    if snapshot.quote is not None and not _has_exact_quote_shape(snapshot.quote):
        return False
    if snapshot.symbol_spec is not None and not _has_exact_symbol_shape(snapshot.symbol_spec):
        return False
    if snapshot.freshness is not None and not _has_exact_freshness_shape(snapshot.freshness):
        return False
    for timeframe in snapshot.timeframes:
        if not _has_exact_timeframe_shape(timeframe):
            return False
    return True


def _has_exact_quote_shape(value: object) -> bool:
    return _is_exact_record(value, CanonicalGoldQuoteFactsV1, _QUOTE_FIELDS) and (
        type(value.bid_decimal) is str
        and type(value.ask_decimal) is str
        and type(value.spread_decimal) is str
        and type(value.spread_points) is int
        and type(value.digits) is int
        and type(value.point_decimal) is str
        and type(value.tick_time_utc) is str
    )


def _has_exact_timeframe_shape(value: object) -> bool:
    if not _is_exact_record(value, CanonicalGoldTimeframeFactsV1, _TIMEFRAME_FIELDS):
        return False
    if not (
        type(value.timeframe) is str
        and type(value.period_seconds) is int
        and type(value.bars) is tuple
    ):
        return False
    return all(_has_exact_bar_shape(bar) for bar in value.bars)


def _has_exact_bar_shape(value: object) -> bool:
    return _is_exact_record(value, CanonicalGoldBarFactsV1, _BAR_FIELDS) and (
        type(value.open_time_utc) is str
        and type(value.open_decimal) is str
        and type(value.high_decimal) is str
        and type(value.low_decimal) is str
        and type(value.close_decimal) is str
        and type(value.tick_volume) is int
        and type(value.spread_points) is int
    )


def _has_exact_symbol_shape(value: object) -> bool:
    return _is_exact_record(value, CanonicalGoldSymbolFactsV1, _SYMBOL_FIELDS) and (
        type(value.spec_time_utc) is str
        and type(value.digits) is int
        and type(value.point_decimal) is str
        and type(value.tick_size_decimal) is str
        and type(value.tick_value_decimal) is str
        and type(value.contract_size_decimal) is str
        and type(value.min_lot_decimal) is str
        and type(value.lot_step_decimal) is str
        and type(value.max_lot_decimal) is str
        and type(value.base_currency) is str
        and type(value.profit_currency) is str
        and type(value.margin_currency) is str
        and type(value.trade_mode_readonly_label) is str
        and type(value.session_status_readonly_label) is str
    )


def _has_exact_freshness_shape(value: object) -> bool:
    return _is_exact_record(value, CanonicalGoldFreshnessFactsV1, _FRESHNESS_FIELDS) and (
        type(value.tick_age_microseconds) is int
        and type(value.bars_payload_age_microseconds) is int
        and type(value.symbol_spec_age_microseconds) is int
    )


def _is_exact_record(value: object, expected_type: type[object], fields: tuple[str, ...]) -> bool:
    return type(value) is expected_type and getattr(type(value), "__slots__", None) == fields


def _is_string_tuple(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _is_optional_str(value: object) -> bool:
    return value is None or type(value) is str


def _is_optional_int(value: object) -> bool:
    return value is None or type(value) is int


def _has_ready_authority(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
    return (
        snapshot.contract_version == _CONTRACT_VERSION
        and snapshot.passed is True
        and snapshot.status_code == _G175_READY_STATUS
        and snapshot.reason_codes == ()
        and snapshot.warning_codes == ()
        and snapshot.identity_available is True
        and type(snapshot.bundle_schema_version) is str
        and type(snapshot.bundle_id) is str
        and type(snapshot.sequence) is int
        and type(snapshot.canonical_symbol) is str
        and type(snapshot.broker_symbol) is str
        and type(snapshot.reference_time_utc) is str
        and type(snapshot.quote) is CanonicalGoldQuoteFactsV1
        and type(snapshot.symbol_spec) is CanonicalGoldSymbolFactsV1
        and type(snapshot.freshness) is CanonicalGoldFreshnessFactsV1
        and len(snapshot.timeframes) == 4
        and all(len(timeframe.bars) > 0 for timeframe in snapshot.timeframes)
        and snapshot.read_only is True
        and snapshot.demo_only is True
        and snapshot.is_tradable is False
        and snapshot.can_execute is False
        and snapshot.is_trading_permission is False
        and snapshot.is_execution_instruction is False
        and snapshot.allowed_to_call_ea is False
        and snapshot.allowed_to_modify_risk is False
    )


def _has_valid_upstream_values(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
    quote = snapshot.quote
    symbol = snapshot.symbol_spec
    if quote is None or symbol is None:
        return False
    digits = quote.digits
    for timeframe, expected in zip(snapshot.timeframes, _TIMEFRAME_PERIODS, strict=True):
        if (timeframe.timeframe, timeframe.period_seconds) != expected:
            return False
        if not 1 <= len(timeframe.bars) <= 500:
            return False
        previous_time: datetime | None = None
        for bar in timeframe.bars:
            bar_time = _parse_utc_z(bar.open_time_utc)
            if bar_time is None or (previous_time is not None and bar_time <= previous_time):
                return False
            previous_time = bar_time
            if bar.tick_volume < 0 or bar.spread_points < 0:
                return False
            if 0 <= digits <= 8:
                prices = tuple(
                    _parse_fixed_price(value, digits)
                    for value in (
                        bar.open_decimal,
                        bar.high_decimal,
                        bar.low_decimal,
                        bar.close_decimal,
                    )
                )
                if any(value is None or value <= 0 for value in prices):
                    return False
                open_value, high_value, low_value, close_value = prices
                if high_value < max(open_value, low_value, close_value):
                    return False
                if low_value > min(open_value, high_value, close_value):
                    return False
    if 0 <= digits <= 8:
        tick_size = _parse_fixed_price(symbol.tick_size_decimal, digits)
        if tick_size is None or tick_size <= 0:
            return False
    non_price_values = tuple(
        _parse_canonical_positive_decimal(value)
        for value in (
            symbol.tick_value_decimal,
            symbol.contract_size_decimal,
            symbol.min_lot_decimal,
            symbol.lot_step_decimal,
            symbol.max_lot_decimal,
        )
    )
    if any(value is None for value in non_price_values):
        return False
    _, _, min_lot, lot_step, max_lot = non_price_values
    if _compare_scaled(min_lot, max_lot) > 0 or _compare_scaled(lot_step, max_lot) > 0:
        return False
    return (
        symbol.base_currency == "XAU"
        and symbol.profit_currency == "USD"
        and _is_safe_label(symbol.margin_currency)
        and _is_safe_label(symbol.trade_mode_readonly_label)
    )


def _has_valid_identity(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
    return (
        snapshot.bundle_schema_version == "1.0"
        and _BUNDLE_ID_PATTERN.fullmatch(snapshot.bundle_id) is not None
        and snapshot.sequence > 0
        and snapshot.canonical_symbol == "XAUUSD"
        and snapshot.broker_symbol == "GOLD"
    )


def _has_valid_session_input(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
    symbol = snapshot.symbol_spec
    return symbol is not None and _is_safe_label(symbol.session_status_readonly_label)


def _has_valid_spread_input(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
    quote = snapshot.quote
    symbol = snapshot.symbol_spec
    if quote is None or symbol is None or not 0 <= quote.digits <= 8:
        return False
    bid = _parse_fixed_price(quote.bid_decimal, quote.digits)
    ask = _parse_fixed_price(quote.ask_decimal, quote.digits)
    spread = _parse_fixed_price(quote.spread_decimal, quote.digits)
    point = _parse_fixed_price(quote.point_decimal, quote.digits)
    if None in (bid, ask, spread, point):
        return False
    if (
        bid <= 0
        or ask <= 0
        or ask < bid
        or spread < 0
        or point != 1
        or quote.spread_points < 0
        or ask - bid != spread
        or quote.spread_points * point != spread
        or _parse_utc_z(quote.tick_time_utc) is None
    ):
        return False
    return (
        symbol.digits == quote.digits
        and symbol.point_decimal == quote.point_decimal
        and _parse_fixed_price(symbol.point_decimal, quote.digits) == 1
    )


def _has_valid_freshness_input(
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
    reference_time: datetime,
) -> bool:
    quote = snapshot.quote
    symbol = snapshot.symbol_spec
    freshness = snapshot.freshness
    if quote is None or symbol is None or freshness is None:
        return False
    ages = (
        freshness.tick_age_microseconds,
        freshness.bars_payload_age_microseconds,
        freshness.symbol_spec_age_microseconds,
    )
    if any(age < 0 for age in ages):
        return False
    tick_time = _parse_utc_z(quote.tick_time_utc)
    spec_time = _parse_utc_z(symbol.spec_time_utc)
    if tick_time is None or spec_time is None:
        return False
    if _microseconds_between(reference_time, tick_time) != ages[0]:
        return False
    if _microseconds_between(reference_time, spec_time) != ages[2]:
        return False
    try:
        bars_payload_time = reference_time - timedelta(microseconds=ages[1])
        for timeframe in snapshot.timeframes:
            for bar in timeframe.bars:
                bar_time = _parse_utc_z(bar.open_time_utc)
                if bar_time is None:
                    return False
                if bar_time + timedelta(seconds=timeframe.period_seconds) > bars_payload_time:
                    return False
    except OverflowError:
        return False
    return True


def _ready_result(
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
    reference_time: datetime,
) -> CanonicalGoldSessionSpreadFreshnessFactsV1:
    quote = snapshot.quote
    freshness = snapshot.freshness
    if quote is None or freshness is None:
        raise RuntimeError("validated snapshot lost required facts")
    return CanonicalGoldSessionSpreadFreshnessFactsV1(
        contract_version=_CONTRACT_VERSION,
        facts_profile_version=_FACTS_PROFILE_VERSION,
        passed=True,
        status_code=_READY_STATUS,
        reason_codes=(),
        warning_codes=(),
        identity_available=True,
        bundle_schema_version=snapshot.bundle_schema_version,
        bundle_id=snapshot.bundle_id,
        sequence=snapshot.sequence,
        canonical_symbol=snapshot.canonical_symbol,
        broker_symbol=snapshot.broker_symbol,
        reference_time_utc=snapshot.reference_time_utc,
        session=_build_session(snapshot, reference_time),
        spread=_build_spread(quote),
        freshness=_build_freshness(freshness),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


def _build_session(
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
    reference_time: datetime,
) -> CanonicalGoldSessionFactsV1:
    second = reference_time.hour * 3600 + reference_time.minute * 60 + reference_time.second
    bucket, start, end = next(
        window for window in _SESSION_WINDOWS if window[1] <= second < window[2]
    )
    symbol = snapshot.symbol_spec
    if symbol is None:
        raise RuntimeError("validated snapshot lost symbol facts")
    return CanonicalGoldSessionFactsV1(
        utc_weekday_code=_WEEKDAY_CODES[reference_time.weekday()],
        utc_second_of_day=second,
        session_bucket_code=bucket,
        window_start_second_utc=start,
        window_end_second_utc=end,
        seconds_since_window_start=second - start,
        seconds_until_window_end=end - second,
        observed_writer_session_status_label=symbol.session_status_readonly_label,
    )


def _build_spread(quote: CanonicalGoldQuoteFactsV1) -> CanonicalGoldSpreadFactsV1:
    bid = _parse_fixed_price(quote.bid_decimal, quote.digits)
    ask = _parse_fixed_price(quote.ask_decimal, quote.digits)
    spread = _parse_fixed_price(quote.spread_decimal, quote.digits)
    if bid is None or ask is None or spread is None:
        raise RuntimeError("validated snapshot lost spread facts")
    midpoint = _format_scaled_integer(5 * (bid + ask), quote.digits + 1)
    numerator = 2 * spread * (10**12)
    denominator = bid + ask
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (
        2 * remainder == denominator and quotient % 2 == 1
    ):
        quotient += 1
    return CanonicalGoldSpreadFactsV1(
        bid_decimal=quote.bid_decimal,
        ask_decimal=quote.ask_decimal,
        mid_decimal=midpoint,
        spread_decimal=quote.spread_decimal,
        spread_points=quote.spread_points,
        digits=quote.digits,
        point_decimal=quote.point_decimal,
        spread_to_mid_ppm_decimal=_format_scaled_integer(quotient, 6),
    )


def _build_freshness(
    value: CanonicalGoldFreshnessFactsV1,
) -> CanonicalGoldSourceFreshnessFactsV1:
    ages = (
        ("TICK", value.tick_age_microseconds),
        ("BARS_PAYLOAD", value.bars_payload_age_microseconds),
        ("SYMBOL_SPEC", value.symbol_spec_age_microseconds),
    )
    maximum = max(age for _, age in ages)
    oldest = next(component for component, age in ages if age == maximum)
    return CanonicalGoldSourceFreshnessFactsV1(
        tick_age_microseconds=value.tick_age_microseconds,
        bars_payload_age_microseconds=value.bars_payload_age_microseconds,
        symbol_spec_age_microseconds=value.symbol_spec_age_microseconds,
        maximum_source_age_microseconds=maximum,
        oldest_source_component_code=oldest,
    )


def _failure(status: str, reason: str) -> CanonicalGoldSessionSpreadFreshnessFactsV1:
    return CanonicalGoldSessionSpreadFreshnessFactsV1(
        contract_version=_CONTRACT_VERSION,
        facts_profile_version=_FACTS_PROFILE_VERSION,
        passed=False,
        status_code=status,
        reason_codes=(reason,),
        warning_codes=(),
        identity_available=False,
        bundle_schema_version=None,
        bundle_id=None,
        sequence=None,
        canonical_symbol=None,
        broker_symbol=None,
        reference_time_utc=None,
        session=None,
        spread=None,
        freshness=None,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


def _parse_utc_z(value: str | None) -> datetime | None:
    if type(value) is not str or _UTC_Z_PATTERN.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError:
        return None
    return parsed if parsed.tzinfo is UTC else None


def _parse_fixed_price(value: str, digits: int) -> int | None:
    if type(value) is not str or type(digits) is not int or not 0 <= digits <= 8:
        return None
    if digits == 0:
        integer_part, fractional_part = value, ""
        if "." in value:
            return None
    else:
        pieces = value.split(".")
        if len(pieces) != 2 or len(pieces[1]) != digits:
            return None
        integer_part, fractional_part = pieces
    if not _is_canonical_unsigned_integer(integer_part):
        return None
    if fractional_part and not _is_ascii_digits(fractional_part):
        return None
    return _digits_to_int(integer_part + fractional_part)


def _parse_canonical_positive_decimal(value: str) -> tuple[int, int] | None:
    if type(value) is not str or value.count(".") > 1:
        return None
    if "." in value:
        integer_part, fractional_part = value.split(".")
        if not fractional_part or fractional_part[-1] == "0":
            return None
    else:
        integer_part, fractional_part = value, ""
    if not _is_canonical_unsigned_integer(integer_part):
        return None
    if fractional_part and not _is_ascii_digits(fractional_part):
        return None
    coefficient = _digits_to_int(integer_part + fractional_part)
    return (coefficient, len(fractional_part)) if coefficient > 0 else None


def _is_canonical_unsigned_integer(value: str) -> bool:
    return bool(value) and _is_ascii_digits(value) and (value == "0" or value[0] != "0")


def _is_ascii_digits(value: str) -> bool:
    return all("0" <= character <= "9" for character in value)


def _digits_to_int(value: str) -> int:
    result = 0
    for start in range(0, len(value), 18):
        chunk = value[start : start + 18]
        result = result * (10 ** len(chunk)) + int(chunk)
    return result


def _compare_scaled(left: tuple[int, int], right: tuple[int, int]) -> int:
    common_scale = max(left[1], right[1])
    left_value = left[0] * (10 ** (common_scale - left[1]))
    right_value = right[0] * (10 ** (common_scale - right[1]))
    return (left_value > right_value) - (left_value < right_value)


def _format_scaled_integer(value: int, scale: int) -> str:
    digits = _int_to_digits(value)
    if scale == 0:
        return digits
    digits = digits.rjust(scale + 1, "0")
    return f"{digits[:-scale]}.{digits[-scale:]}"


def _int_to_digits(value: int) -> str:
    if value == 0:
        return "0"
    chunks: list[int] = []
    while value:
        value, remainder = divmod(value, 10**18)
        chunks.append(remainder)
    return str(chunks[-1]) + "".join(f"{chunk:018d}" for chunk in reversed(chunks[:-1]))


def _microseconds_between(later: datetime, earlier: datetime) -> int:
    delta = later - earlier
    return ((delta.days * 86400) + delta.seconds) * 1_000_000 + delta.microseconds


def _is_safe_label(value: str) -> bool:
    return _SAFE_LABEL_PATTERN.fullmatch(value) is not None
