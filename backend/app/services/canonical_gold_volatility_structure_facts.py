from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import (
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Overflow,
    ROUND_HALF_EVEN,
    Rounded,
    Underflow,
)
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
class CanonicalGoldBarPairVolatilityStructureFactsV1:
    previous_open_time_utc: str
    current_open_time_utc: str
    previous_range_decimal: str
    current_range_decimal: str
    true_range_decimal: str
    body_signed_decimal: str
    body_absolute_decimal: str
    upper_wick_decimal: str
    lower_wick_decimal: str
    close_change_decimal: str
    high_change_decimal: str
    low_change_decimal: str
    direction_code: str
    range_relation_code: str
    range_containment_code: str
    current_high_vs_previous_high_code: str
    current_low_vs_previous_low_code: str
    current_close_vs_previous_range_code: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldTimeframeVolatilityStructureFactsV1:
    timeframe: str
    period_seconds: int
    source_bar_count: int
    pair_count: int
    bar_pairs: tuple[CanonicalGoldBarPairVolatilityStructureFactsV1, ...]


@dataclass(frozen=True, slots=True)
class CanonicalGoldVolatilityStructureFactsV1:
    contract_version: str
    facts_profile_version: str
    passed: bool
    status_code: str
    reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    identity_available: bool
    source_contract_version: str | None
    bundle_schema_version: str | None
    bundle_id: str | None
    sequence: int | None
    canonical_symbol: str | None
    broker_symbol: str | None
    reference_time_utc: str | None
    timeframes: tuple[CanonicalGoldTimeframeVolatilityStructureFactsV1, ...]
    total_pair_count: int
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool


__all__ = (
    "CanonicalGoldVolatilityStructureFactsV1",
    "CanonicalGoldTimeframeVolatilityStructureFactsV1",
    "CanonicalGoldBarPairVolatilityStructureFactsV1",
    "build_canonical_gold_volatility_structure_facts_v1",
)


_CONTRACT_VERSION = "1.0"
_FACTS_PROFILE_VERSION = "canonical_gold_volatility_structure_profile_v1"
_READY_STATUS = "CANONICAL_GOLD_VOLATILITY_STRUCTURE_READY"
_INPUT_INVALID_STATUS = "CANONICAL_GOLD_VOLATILITY_STRUCTURE_INPUT_INVALID"
_UPSTREAM_BLOCKED_STATUS = "CANONICAL_GOLD_VOLATILITY_STRUCTURE_UPSTREAM_BLOCKED"
_IDENTITY_INVALID_STATUS = "CANONICAL_GOLD_VOLATILITY_STRUCTURE_IDENTITY_INVALID"
_TIMEFRAME_INVALID_STATUS = "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID"
_HISTORY_INSUFFICIENT_STATUS = (
    "CANONICAL_GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT"
)
_DECIMAL_INVALID_STATUS = "CANONICAL_GOLD_VOLATILITY_STRUCTURE_DECIMAL_INVALID"
_RESULT_INVALID_STATUS = "CANONICAL_GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID"
_SAFE_FAILURE_STATUS = "CANONICAL_GOLD_VOLATILITY_STRUCTURE_SAFE_FAILURE"

_INPUT_TYPE_INVALID = "GOLD_VOLATILITY_STRUCTURE_INPUT_TYPE_INVALID"
_SNAPSHOT_NOT_READY = "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_NOT_READY"
_SNAPSHOT_IDENTITY_INVALID = "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_IDENTITY_INVALID"
_TIMEFRAME_INPUT_INVALID = "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID"
_HISTORY_INSUFFICIENT = "GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT"
_DECIMAL_INPUT_INVALID = "GOLD_VOLATILITY_STRUCTURE_DECIMAL_INPUT_INVALID"
_RESULT_INVALID = "GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID"
_EXCEPTION_SANITIZED = "GOLD_VOLATILITY_STRUCTURE_EXCEPTION_SANITIZED"

_G175_READY_STATUS = "CANONICAL_GOLD_MARKET_FACTS_READY"
_TIMEFRAME_PERIODS = (("M15", 900), ("H1", 3600), ("H4", 14400), ("D1", 86400))
_BUNDLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{16,64}$", re.ASCII)
_SAFE_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$", re.ASCII)
_UTC_Z_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$",
    re.ASCII,
)
_POSITIVE_DECIMAL_PATTERN = re.compile(
    r"^(?:[1-9][0-9]*|(?:0|[1-9][0-9]*)\.[0-9]*[1-9])$",
    re.ASCII,
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
_RESULT_FIELDS = (
    "contract_version",
    "facts_profile_version",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
    "identity_available",
    "source_contract_version",
    "bundle_schema_version",
    "bundle_id",
    "sequence",
    "canonical_symbol",
    "broker_symbol",
    "reference_time_utc",
    "timeframes",
    "total_pair_count",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
_RESULT_TIMEFRAME_FIELDS = (
    "timeframe",
    "period_seconds",
    "source_bar_count",
    "pair_count",
    "bar_pairs",
)
_RESULT_PAIR_FIELDS = (
    "previous_open_time_utc",
    "current_open_time_utc",
    "previous_range_decimal",
    "current_range_decimal",
    "true_range_decimal",
    "body_signed_decimal",
    "body_absolute_decimal",
    "upper_wick_decimal",
    "lower_wick_decimal",
    "close_change_decimal",
    "high_change_decimal",
    "low_change_decimal",
    "direction_code",
    "range_relation_code",
    "range_containment_code",
    "current_high_vs_previous_high_code",
    "current_low_vs_previous_low_code",
    "current_close_vs_previous_range_code",
)


@dataclass(frozen=True, slots=True)
class _DecimalInput:
    digits: int
    context: Context
    bar_values: tuple[tuple[tuple[Decimal, Decimal, Decimal, Decimal], ...], ...]


class _DecimalInvalid(Exception):
    pass


def build_canonical_gold_volatility_structure_facts_v1(
    *,
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,
) -> CanonicalGoldVolatilityStructureFactsV1:
    try:
        if not _has_exact_input_shape(market_facts_snapshot):
            return _failure(_INPUT_INVALID_STATUS, _INPUT_TYPE_INVALID)
        if not _has_ready_authority(market_facts_snapshot):
            return _failure(_UPSTREAM_BLOCKED_STATUS, _SNAPSHOT_NOT_READY)
        if not _has_valid_identity(market_facts_snapshot):
            return _failure(_IDENTITY_INVALID_STATUS, _SNAPSHOT_IDENTITY_INVALID)
        if not _has_valid_timeframes(market_facts_snapshot):
            return _failure(_TIMEFRAME_INVALID_STATUS, _TIMEFRAME_INPUT_INVALID)
        if any(len(timeframe.bars) < 2 for timeframe in market_facts_snapshot.timeframes):
            return _failure(_HISTORY_INSUFFICIENT_STATUS, _HISTORY_INSUFFICIENT)
        decimal_input = _validate_decimal_input(market_facts_snapshot)
        if decimal_input is None:
            return _failure(_DECIMAL_INVALID_STATUS, _DECIMAL_INPUT_INVALID)
        try:
            timeframes = _build_timeframes(market_facts_snapshot, decimal_input)
        except _DecimalInvalid:
            return _failure(_DECIMAL_INVALID_STATUS, _DECIMAL_INPUT_INVALID)
        result = _ready_result(market_facts_snapshot, timeframes)
        if not _is_valid_ready_result(result, market_facts_snapshot, timeframes):
            return _failure(_RESULT_INVALID_STATUS, _RESULT_INVALID)
        return result
    except Exception:
        return _failure(_SAFE_FAILURE_STATUS, _EXCEPTION_SANITIZED)


def _has_exact_input_shape(value: object) -> bool:
    try:
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
            and type(snapshot.quote) is CanonicalGoldQuoteFactsV1
            and type(snapshot.timeframes) is tuple
            and type(snapshot.symbol_spec) is CanonicalGoldSymbolFactsV1
            and type(snapshot.freshness) is CanonicalGoldFreshnessFactsV1
            and type(snapshot.read_only) is bool
            and type(snapshot.demo_only) is bool
            and type(snapshot.is_tradable) is bool
            and type(snapshot.can_execute) is bool
            and type(snapshot.is_trading_permission) is bool
            and type(snapshot.is_execution_instruction) is bool
            and type(snapshot.allowed_to_call_ea) is bool
            and type(snapshot.allowed_to_modify_risk) is bool
            and _has_exact_quote_shape(snapshot.quote)
            and _has_exact_symbol_shape(snapshot.symbol_spec)
            and _has_exact_freshness_shape(snapshot.freshness)
        ):
            return False
        return all(_has_exact_timeframe_shape(timeframe) for timeframe in snapshot.timeframes)
    except (AttributeError, TypeError):
        return False


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
    return _is_exact_record(value, CanonicalGoldTimeframeFactsV1, _TIMEFRAME_FIELDS) and (
        type(value.timeframe) is str
        and type(value.period_seconds) is int
        and type(value.bars) is tuple
        and all(_has_exact_bar_shape(bar) for bar in value.bars)
    )


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
    symbol = snapshot.symbol_spec
    return (
        snapshot.contract_version == _CONTRACT_VERSION
        and snapshot.passed is True
        and snapshot.status_code == _G175_READY_STATUS
        and snapshot.reason_codes == ()
        and snapshot.warning_codes == ()
        and snapshot.identity_available is True
        and snapshot.read_only is True
        and snapshot.demo_only is True
        and snapshot.is_tradable is False
        and snapshot.can_execute is False
        and snapshot.is_trading_permission is False
        and snapshot.is_execution_instruction is False
        and snapshot.allowed_to_call_ea is False
        and snapshot.allowed_to_modify_risk is False
        and symbol.base_currency == "XAU"
        and symbol.profit_currency == "USD"
        and _is_safe_label(symbol.margin_currency)
        and _is_safe_label(symbol.trade_mode_readonly_label)
        and _is_safe_label(symbol.session_status_readonly_label)
    )


def _has_valid_identity(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
    return (
        snapshot.bundle_schema_version == "1.0"
        and type(snapshot.bundle_id) is str
        and snapshot.bundle_id.isascii()
        and _BUNDLE_ID_PATTERN.fullmatch(snapshot.bundle_id) is not None
        and type(snapshot.sequence) is int
        and snapshot.sequence > 0
        and snapshot.canonical_symbol == "XAUUSD"
        and snapshot.broker_symbol == "GOLD"
        and type(snapshot.reference_time_utc) is str
        and _parse_utc_z(snapshot.reference_time_utc) is not None
    )


def _has_valid_timeframes(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
    reference_time = _parse_utc_z(snapshot.reference_time_utc)
    quote = snapshot.quote
    symbol = snapshot.symbol_spec
    freshness = snapshot.freshness
    if reference_time is None or len(snapshot.timeframes) != 4:
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
    except OverflowError:
        return False

    pattern = _source_price_pattern(quote.digits) if 0 <= quote.digits <= 8 else None
    for timeframe, expected in zip(snapshot.timeframes, _TIMEFRAME_PERIODS, strict=True):
        if (
            (timeframe.timeframe, timeframe.period_seconds) != expected
            or not 1 <= len(timeframe.bars) <= 500
        ):
            return False
        previous_time: datetime | None = None
        for bar in timeframe.bars:
            bar_time = _parse_utc_z(bar.open_time_utc)
            if bar_time is None or (previous_time is not None and bar_time <= previous_time):
                return False
            previous_time = bar_time
            try:
                if bar_time + timedelta(seconds=timeframe.period_seconds) > bars_payload_time:
                    return False
            except OverflowError:
                return False
            if bar.tick_volume < 0 or bar.spread_points < 0:
                return False
            if pattern is not None:
                values = tuple(
                    _parse_source_price(text, pattern)
                    for text in (
                        bar.open_decimal,
                        bar.high_decimal,
                        bar.low_decimal,
                        bar.close_decimal,
                    )
                )
                if all(value is not None for value in values):
                    open_value, high_value, low_value, close_value = values
                    if any(value <= 0 for value in values):
                        return False
                    if high_value < max(open_value, close_value):
                        return False
                    if low_value > min(open_value, close_value):
                        return False
    return True


def _validate_decimal_input(
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
) -> _DecimalInput | None:
    quote = snapshot.quote
    symbol = snapshot.symbol_spec
    digits = quote.digits
    if not 0 <= digits <= 8 or symbol.digits != digits:
        return None
    pattern = _source_price_pattern(digits)
    price_texts = [
        quote.bid_decimal,
        quote.ask_decimal,
        quote.spread_decimal,
        quote.point_decimal,
        symbol.point_decimal,
        symbol.tick_size_decimal,
    ]
    for timeframe in snapshot.timeframes:
        for bar in timeframe.bars:
            price_texts.extend(
                (bar.open_decimal, bar.high_decimal, bar.low_decimal, bar.close_decimal)
            )
    parsed = tuple(_parse_source_price(text, pattern) for text in price_texts)
    if any(value is None for value in parsed):
        return None
    values = tuple(value for value in parsed if value is not None)
    bid, ask, spread, point, symbol_point, tick_size = values[:6]
    quantum = Decimal((0, (1,), -digits))
    positive_values = tuple(
        _parse_positive_decimal(text)
        for text in (
            symbol.tick_value_decimal,
            symbol.contract_size_decimal,
            symbol.min_lot_decimal,
            symbol.lot_step_decimal,
            symbol.max_lot_decimal,
        )
    )
    if any(value is None for value in positive_values):
        return None
    tick_value, contract_size, min_lot, lot_step, max_lot = positive_values
    if not (
        tick_value > 0
        and contract_size > 0
        and min_lot > 0
        and lot_step > 0
        and max_lot > 0
        and min_lot <= max_lot
        and lot_step <= max_lot
    ):
        return None

    coefficient_digits = max(len(value.as_tuple().digits) for value in values)
    context = Context(prec=coefficient_digits + 2, rounding=ROUND_HALF_EVEN)
    for signal in (
        InvalidOperation,
        DivisionByZero,
        Overflow,
        Underflow,
        Inexact,
        Rounded,
    ):
        context.traps[signal] = True
    try:
        spread_from_prices = context.subtract(ask, bid)
        spread_from_points = context.multiply(Decimal(quote.spread_points), point)
    except DecimalException:
        return None
    if not (
        bid > 0
        and ask > 0
        and ask >= bid
        and spread >= 0
        and point == symbol_point == quantum
        and tick_size > 0
        and quote.spread_points >= 0
        and spread_from_prices == spread
        and spread_from_points == spread
    ):
        return None

    offset = 6
    bar_values: list[tuple[tuple[Decimal, Decimal, Decimal, Decimal], ...]] = []
    for timeframe in snapshot.timeframes:
        timeframe_values: list[tuple[Decimal, Decimal, Decimal, Decimal]] = []
        for _bar in timeframe.bars:
            bar_tuple = values[offset : offset + 4]
            if len(bar_tuple) != 4:
                return None
            timeframe_values.append((bar_tuple[0], bar_tuple[1], bar_tuple[2], bar_tuple[3]))
            offset += 4
        bar_values.append(tuple(timeframe_values))
    if offset != len(values):
        return None
    return _DecimalInput(digits=digits, context=context, bar_values=tuple(bar_values))


def _build_timeframes(
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
    decimal_input: _DecimalInput,
) -> tuple[CanonicalGoldTimeframeVolatilityStructureFactsV1, ...]:
    output: list[CanonicalGoldTimeframeVolatilityStructureFactsV1] = []
    for timeframe, values in zip(
        snapshot.timeframes,
        decimal_input.bar_values,
        strict=True,
    ):
        pairs = tuple(
            _build_pair(
                timeframe.bars[index],
                timeframe.bars[index + 1],
                values[index],
                values[index + 1],
                decimal_input.digits,
                decimal_input.context,
            )
            for index in range(len(timeframe.bars) - 1)
        )
        output.append(
            CanonicalGoldTimeframeVolatilityStructureFactsV1(
                timeframe=timeframe.timeframe,
                period_seconds=timeframe.period_seconds,
                source_bar_count=len(timeframe.bars),
                pair_count=len(pairs),
                bar_pairs=pairs,
            )
        )
    return tuple(output)


def _build_pair(
    previous_bar: CanonicalGoldBarFactsV1,
    current_bar: CanonicalGoldBarFactsV1,
    previous: tuple[Decimal, Decimal, Decimal, Decimal],
    current: tuple[Decimal, Decimal, Decimal, Decimal],
    digits: int,
    context: Context,
) -> CanonicalGoldBarPairVolatilityStructureFactsV1:
    try:
        _, previous_high, previous_low, previous_close = previous
        current_open, current_high, current_low, current_close = current
        previous_range = context.subtract(previous_high, previous_low)
        current_range = context.subtract(current_high, current_low)
        high_gap = context.copy_abs(context.subtract(current_high, previous_close))
        low_gap = context.copy_abs(context.subtract(current_low, previous_close))
        true_range = max(current_range, high_gap, low_gap)
        body_signed = context.subtract(current_close, current_open)
        body_absolute = context.copy_abs(body_signed)
        upper_wick = context.subtract(current_high, max(current_open, current_close))
        lower_wick = context.subtract(min(current_open, current_close), current_low)
        close_change = context.subtract(current_close, previous_close)
        high_change = context.subtract(current_high, previous_high)
        low_change = context.subtract(current_low, previous_low)
    except DecimalException as exc:
        raise _DecimalInvalid from exc
    unsigned = tuple(
        _render_derived(value, digits, signed=False)
        for value in (
            previous_range,
            current_range,
            true_range,
            body_absolute,
            upper_wick,
            lower_wick,
        )
    )
    signed = tuple(
        _render_derived(value, digits, signed=True)
        for value in (body_signed, close_change, high_change, low_change)
    )
    return CanonicalGoldBarPairVolatilityStructureFactsV1(
        previous_open_time_utc=previous_bar.open_time_utc,
        current_open_time_utc=current_bar.open_time_utc,
        previous_range_decimal=unsigned[0],
        current_range_decimal=unsigned[1],
        true_range_decimal=unsigned[2],
        body_signed_decimal=signed[0],
        body_absolute_decimal=unsigned[3],
        upper_wick_decimal=unsigned[4],
        lower_wick_decimal=unsigned[5],
        close_change_decimal=signed[1],
        high_change_decimal=signed[2],
        low_change_decimal=signed[3],
        direction_code=_direction_code(current_open, current_close),
        range_relation_code=_range_relation_code(previous_range, current_range),
        range_containment_code=_range_containment_code(
            previous_high, previous_low, current_high, current_low
        ),
        current_high_vs_previous_high_code=_high_relation_code(
            previous_high, current_high
        ),
        current_low_vs_previous_low_code=_low_relation_code(previous_low, current_low),
        current_close_vs_previous_range_code=_close_relation_code(
            previous_high, previous_low, current_close
        ),
    )


def _ready_result(
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
    timeframes: tuple[CanonicalGoldTimeframeVolatilityStructureFactsV1, ...],
) -> CanonicalGoldVolatilityStructureFactsV1:
    return CanonicalGoldVolatilityStructureFactsV1(
        contract_version=_CONTRACT_VERSION,
        facts_profile_version=_FACTS_PROFILE_VERSION,
        passed=True,
        status_code=_READY_STATUS,
        reason_codes=(),
        warning_codes=(),
        identity_available=True,
        source_contract_version=snapshot.contract_version,
        bundle_schema_version=snapshot.bundle_schema_version,
        bundle_id=snapshot.bundle_id,
        sequence=snapshot.sequence,
        canonical_symbol=snapshot.canonical_symbol,
        broker_symbol=snapshot.broker_symbol,
        reference_time_utc=snapshot.reference_time_utc,
        timeframes=timeframes,
        total_pair_count=sum(timeframe.pair_count for timeframe in timeframes),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


def _is_valid_ready_result(
    result: object,
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
    expected_timeframes: tuple[CanonicalGoldTimeframeVolatilityStructureFactsV1, ...],
) -> bool:
    try:
        if not _is_exact_record(result, CanonicalGoldVolatilityStructureFactsV1, _RESULT_FIELDS):
            return False
        if not (
            type(result.contract_version) is str
            and type(result.facts_profile_version) is str
            and type(result.passed) is bool
            and type(result.status_code) is str
            and _is_string_tuple(result.reason_codes)
            and _is_string_tuple(result.warning_codes)
            and type(result.identity_available) is bool
            and _is_optional_str(result.source_contract_version)
            and _is_optional_str(result.bundle_schema_version)
            and _is_optional_str(result.bundle_id)
            and _is_optional_int(result.sequence)
            and _is_optional_str(result.canonical_symbol)
            and _is_optional_str(result.broker_symbol)
            and _is_optional_str(result.reference_time_utc)
            and type(result.timeframes) is tuple
            and type(result.total_pair_count) is int
            and type(result.read_only) is bool
            and type(result.demo_only) is bool
            and type(result.is_tradable) is bool
            and type(result.can_execute) is bool
            and type(result.is_trading_permission) is bool
            and type(result.is_execution_instruction) is bool
            and type(result.allowed_to_call_ea) is bool
            and type(result.allowed_to_modify_risk) is bool
        ):
            return False
        if (
            result.contract_version != _CONTRACT_VERSION
            or result.facts_profile_version != _FACTS_PROFILE_VERSION
            or result.passed is not True
            or result.status_code != _READY_STATUS
            or result.reason_codes != ()
            or result.warning_codes != ()
            or result.identity_available is not True
            or result.source_contract_version != snapshot.contract_version
            or result.bundle_schema_version != snapshot.bundle_schema_version
            or result.bundle_id != snapshot.bundle_id
            or result.sequence != snapshot.sequence
            or result.canonical_symbol != snapshot.canonical_symbol
            or result.broker_symbol != snapshot.broker_symbol
            or result.reference_time_utc != snapshot.reference_time_utc
            or len(result.timeframes) != 4
            or result.timeframes != expected_timeframes
            or not _has_safety_flags(result)
        ):
            return False
        expected_total = 0
        for output, source, authority in zip(
            result.timeframes, snapshot.timeframes, _TIMEFRAME_PERIODS, strict=True
        ):
            if not _is_exact_record(
                output,
                CanonicalGoldTimeframeVolatilityStructureFactsV1,
                _RESULT_TIMEFRAME_FIELDS,
            ):
                return False
            if not (
                type(output.timeframe) is str
                and type(output.period_seconds) is int
                and type(output.source_bar_count) is int
                and type(output.pair_count) is int
                and type(output.bar_pairs) is tuple
                and (output.timeframe, output.period_seconds) == authority
                and output.source_bar_count == len(source.bars)
                and output.pair_count == len(source.bars) - 1
                and len(output.bar_pairs) == output.pair_count
            ):
                return False
            for index, pair in enumerate(output.bar_pairs):
                if not _is_valid_pair(pair, source.bars[index], source.bars[index + 1]):
                    return False
            expected_total += output.pair_count
        return result.total_pair_count == expected_total
    except (AttributeError, TypeError):
        return False


def _is_valid_pair(
    pair: object,
    previous_bar: CanonicalGoldBarFactsV1,
    current_bar: CanonicalGoldBarFactsV1,
) -> bool:
    if not _is_exact_record(
        pair, CanonicalGoldBarPairVolatilityStructureFactsV1, _RESULT_PAIR_FIELDS
    ):
        return False
    if not all(type(getattr(pair, field)) is str for field in _RESULT_PAIR_FIELDS):
        return False
    return (
        pair.previous_open_time_utc == previous_bar.open_time_utc
        and pair.current_open_time_utc == current_bar.open_time_utc
        and pair.direction_code in ("UP", "DOWN", "FLAT")
        and pair.range_relation_code in ("EXPANDED", "CONTRACTED", "EQUAL")
        and pair.range_containment_code
        in ("EXACT_MATCH", "INSIDE", "OUTSIDE", "SHIFTED_UP", "SHIFTED_DOWN")
        and pair.current_high_vs_previous_high_code
        in ("ABOVE_PREVIOUS_HIGH", "BELOW_PREVIOUS_HIGH", "AT_PREVIOUS_HIGH")
        and pair.current_low_vs_previous_low_code
        in ("ABOVE_PREVIOUS_LOW", "BELOW_PREVIOUS_LOW", "AT_PREVIOUS_LOW")
        and pair.current_close_vs_previous_range_code
        in (
            "ABOVE_PREVIOUS_HIGH",
            "AT_PREVIOUS_HIGH",
            "INSIDE_PREVIOUS_RANGE",
            "AT_PREVIOUS_LOW",
            "BELOW_PREVIOUS_LOW",
        )
    )


def _failure(status: str, reason: str) -> CanonicalGoldVolatilityStructureFactsV1:
    return CanonicalGoldVolatilityStructureFactsV1(
        contract_version=_CONTRACT_VERSION,
        facts_profile_version=_FACTS_PROFILE_VERSION,
        passed=False,
        status_code=status,
        reason_codes=(reason,),
        warning_codes=(),
        identity_available=False,
        source_contract_version=None,
        bundle_schema_version=None,
        bundle_id=None,
        sequence=None,
        canonical_symbol=None,
        broker_symbol=None,
        reference_time_utc=None,
        timeframes=(),
        total_pair_count=0,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


def _source_price_pattern(digits: int) -> re.Pattern[str]:
    if digits == 0:
        return re.compile(r"^(?:0|[1-9][0-9]*)$", re.ASCII)
    return re.compile(rf"^(?:0|[1-9][0-9]*)\.[0-9]{{{digits}}}$", re.ASCII)


def _derived_pattern(digits: int, *, signed: bool) -> re.Pattern[str]:
    sign = "-?" if signed else ""
    if digits == 0:
        return re.compile(rf"^{sign}(?:0|[1-9][0-9]*)$", re.ASCII)
    return re.compile(
        rf"^{sign}(?:0|[1-9][0-9]*)\.[0-9]{{{digits}}}$",
        re.ASCII,
    )


def _parse_source_price(value: str, pattern: re.Pattern[str]) -> Decimal | None:
    if not value.isascii() or pattern.fullmatch(value) is None:
        return None
    try:
        parsed = Decimal(value)
    except (DecimalException, ValueError, OverflowError):
        return None
    return parsed if parsed.is_finite() else None


def _parse_positive_decimal(value: str) -> Decimal | None:
    if not value.isascii() or _POSITIVE_DECIMAL_PATTERN.fullmatch(value) is None:
        return None
    try:
        parsed = Decimal(value)
    except (DecimalException, ValueError, OverflowError):
        return None
    return parsed if parsed.is_finite() and parsed > 0 else None


def _render_derived(value: Decimal, digits: int, *, signed: bool) -> str:
    if not value.is_finite() or (not signed and value < 0):
        raise _DecimalInvalid
    exponent = value.as_tuple().exponent
    if type(exponent) is not int or exponent != -digits:
        raise _DecimalInvalid
    if value == 0:
        rendered = "0" if digits == 0 else "0." + ("0" * digits)
    else:
        rendered = format(value, f".{digits}f")
    if _derived_pattern(digits, signed=signed).fullmatch(rendered) is None:
        raise _DecimalInvalid
    if rendered.startswith("-") and Decimal(rendered) == 0:
        raise _DecimalInvalid
    if Decimal(rendered) != value:
        raise _DecimalInvalid
    return rendered


def _direction_code(open_value: Decimal, close_value: Decimal) -> str:
    if close_value > open_value:
        return "UP"
    if close_value < open_value:
        return "DOWN"
    return "FLAT"


def _range_relation_code(previous: Decimal, current: Decimal) -> str:
    if current > previous:
        return "EXPANDED"
    if current < previous:
        return "CONTRACTED"
    return "EQUAL"


def _range_containment_code(
    previous_high: Decimal,
    previous_low: Decimal,
    current_high: Decimal,
    current_low: Decimal,
) -> str:
    if current_high == previous_high and current_low == previous_low:
        return "EXACT_MATCH"
    if current_high <= previous_high and current_low >= previous_low:
        return "INSIDE"
    if current_high >= previous_high and current_low <= previous_low:
        return "OUTSIDE"
    if current_high > previous_high and current_low > previous_low:
        return "SHIFTED_UP"
    if current_high < previous_high and current_low < previous_low:
        return "SHIFTED_DOWN"
    raise _DecimalInvalid


def _high_relation_code(previous_high: Decimal, current_high: Decimal) -> str:
    if current_high > previous_high:
        return "ABOVE_PREVIOUS_HIGH"
    if current_high < previous_high:
        return "BELOW_PREVIOUS_HIGH"
    return "AT_PREVIOUS_HIGH"


def _low_relation_code(previous_low: Decimal, current_low: Decimal) -> str:
    if current_low > previous_low:
        return "ABOVE_PREVIOUS_LOW"
    if current_low < previous_low:
        return "BELOW_PREVIOUS_LOW"
    return "AT_PREVIOUS_LOW"


def _close_relation_code(
    previous_high: Decimal,
    previous_low: Decimal,
    current_close: Decimal,
) -> str:
    if current_close > previous_high:
        return "ABOVE_PREVIOUS_HIGH"
    if current_close == previous_high:
        return "AT_PREVIOUS_HIGH"
    if current_close > previous_low:
        return "INSIDE_PREVIOUS_RANGE"
    if current_close == previous_low:
        return "AT_PREVIOUS_LOW"
    return "BELOW_PREVIOUS_LOW"


def _parse_utc_z(value: str | None) -> datetime | None:
    if (
        type(value) is not str
        or not value.isascii()
        or _UTC_Z_PATTERN.fullmatch(value) is None
    ):
        return None
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        return None
    return parsed.astimezone(UTC)


def _microseconds_between(later: datetime, earlier: datetime) -> int:
    delta = later - earlier
    return ((delta.days * 86400) + delta.seconds) * 1_000_000 + delta.microseconds


def _is_safe_label(value: str) -> bool:
    return value.isascii() and _SAFE_LABEL_PATTERN.fullmatch(value) is not None


def _has_safety_flags(result: CanonicalGoldVolatilityStructureFactsV1) -> bool:
    return (
        result.read_only is True
        and result.demo_only is True
        and result.is_tradable is False
        and result.can_execute is False
        and result.is_trading_permission is False
        and result.is_execution_instruction is False
        and result.allowed_to_call_ea is False
        and result.allowed_to_modify_risk is False
    )
