from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import (
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    ROUND_HALF_EVEN,
    localcontext,
)
import math
import re
from typing import Callable, TypeVar


@dataclass(frozen=True, slots=True)
class CanonicalGoldMarketFactsSourceV1:
    contract_version: str
    bundle_schema_version: str
    bundle_id: str
    sequence: int
    canonical_symbol: str
    broker_symbol: str
    reference_time_utc: str
    policy_profile_version: str
    upstream_evidence: CanonicalGoldUpstreamEvidenceV1
    live_tick: CanonicalGoldTickSourceV1
    bars_generated_at_utc: str
    timeframes: tuple[CanonicalGoldTimeframeSourceV1, ...]
    symbol_spec: CanonicalGoldSymbolSpecSourceV1


@dataclass(frozen=True, slots=True)
class CanonicalGoldUpstreamEvidenceV1:
    reader_passed: bool
    reader_status_code: str
    value_status_code: str
    data_quality_passed: bool
    data_quality_status_code: str
    ready_for_readonly_analysis: bool
    warning_codes: tuple[str, ...]
    same_attempt_identity_bound: bool


@dataclass(frozen=True, slots=True)
class CanonicalGoldTickSourceV1:
    bid: int | float
    ask: int | float
    spread: int | float
    spread_points: int
    digits: int
    point: int | float
    tick_time_utc: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldTimeframeSourceV1:
    timeframe: str
    period_seconds: int
    bars: tuple[CanonicalGoldBarSourceV1, ...]


@dataclass(frozen=True, slots=True)
class CanonicalGoldBarSourceV1:
    open_time_utc: str
    open: int | float
    high: int | float
    low: int | float
    close: int | float
    tick_volume: int
    spread_points: int


@dataclass(frozen=True, slots=True)
class CanonicalGoldSymbolSpecSourceV1:
    spec_time_utc: str
    digits: int
    point: int | float
    tick_size: int | float
    tick_value: int | float
    contract_size: int | float
    min_lot: int | float
    lot_step: int | float
    max_lot: int | float
    base_currency: str
    profit_currency: str
    margin_currency: str
    trade_mode_readonly_label: str
    session_status_readonly_label: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldMarketFactsSnapshotV1:
    contract_version: str
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
    quote: CanonicalGoldQuoteFactsV1 | None
    timeframes: tuple[CanonicalGoldTimeframeFactsV1, ...]
    symbol_spec: CanonicalGoldSymbolFactsV1 | None
    freshness: CanonicalGoldFreshnessFactsV1 | None
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool


@dataclass(frozen=True, slots=True)
class CanonicalGoldQuoteFactsV1:
    bid_decimal: str
    ask_decimal: str
    spread_decimal: str
    spread_points: int
    digits: int
    point_decimal: str
    tick_time_utc: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldTimeframeFactsV1:
    timeframe: str
    period_seconds: int
    bars: tuple[CanonicalGoldBarFactsV1, ...]


@dataclass(frozen=True, slots=True)
class CanonicalGoldBarFactsV1:
    open_time_utc: str
    open_decimal: str
    high_decimal: str
    low_decimal: str
    close_decimal: str
    tick_volume: int
    spread_points: int


@dataclass(frozen=True, slots=True)
class CanonicalGoldSymbolFactsV1:
    spec_time_utc: str
    digits: int
    point_decimal: str
    tick_size_decimal: str
    tick_value_decimal: str
    contract_size_decimal: str
    min_lot_decimal: str
    lot_step_decimal: str
    max_lot_decimal: str
    base_currency: str
    profit_currency: str
    margin_currency: str
    trade_mode_readonly_label: str
    session_status_readonly_label: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldFreshnessFactsV1:
    tick_age_microseconds: int
    bars_payload_age_microseconds: int
    symbol_spec_age_microseconds: int


_CONTRACT_VERSION = "1.0"
_BUNDLE_SCHEMA_VERSION = "1.0"
_CANONICAL_SYMBOL = "XAUUSD"
_BROKER_SYMBOL = "GOLD"
_POLICY_PROFILE_VERSION = "canonical_gold_market_facts_policy_v1"

_READY_STATUS = "CANONICAL_GOLD_MARKET_FACTS_READY"
_INPUT_INVALID_STATUS = "CANONICAL_GOLD_MARKET_FACTS_INPUT_INVALID"
_AUTHORITY_INVALID_STATUS = "CANONICAL_GOLD_MARKET_FACTS_AUTHORITY_INVALID"
_UPSTREAM_BLOCKED_STATUS = "CANONICAL_GOLD_MARKET_FACTS_UPSTREAM_BLOCKED"
_IDENTITY_INVALID_STATUS = "CANONICAL_GOLD_MARKET_FACTS_IDENTITY_INVALID"
_VALUE_INVALID_STATUS = "CANONICAL_GOLD_MARKET_FACTS_VALUE_INVALID"
_SAFE_FAILURE_STATUS = "CANONICAL_GOLD_MARKET_FACTS_SAFE_FAILURE"

_SOURCE_TYPE_INVALID = "GOLD_MARKET_FACTS_SOURCE_TYPE_INVALID"
_SOURCE_AUTHORITY_INVALID = "GOLD_MARKET_FACTS_SOURCE_AUTHORITY_INVALID"
_UPSTREAM_NOT_READY = "GOLD_MARKET_FACTS_UPSTREAM_NOT_READY"
_UPSTREAM_WARNINGS_REJECTED = "GOLD_MARKET_FACTS_UPSTREAM_WARNINGS_REJECTED"
_IDENTITY_INVALID = "GOLD_MARKET_FACTS_IDENTITY_INVALID"
_TICK_INVALID = "GOLD_MARKET_FACTS_TICK_INVALID"
_BARS_INVALID = "GOLD_MARKET_FACTS_BARS_INVALID"
_SYMBOL_SPEC_INVALID = "GOLD_MARKET_FACTS_SYMBOL_SPEC_INVALID"
_FRESHNESS_INVALID = "GOLD_MARKET_FACTS_FRESHNESS_INVALID"
_EXCEPTION_SANITIZED = "GOLD_MARKET_FACTS_EXCEPTION_SANITIZED"

_READER_VALID = "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID"
_VALUE_VALID = "CANONICAL_MT4_BUNDLE_V1_VALUE_VALID"
_DATA_QUALITY_VALID = "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED"

_TIMEFRAME_PERIODS = (
    ("M15", 900),
    ("H1", 3600),
    ("H4", 14400),
    ("D1", 86400),
)
_BUNDLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_SAFE_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
_UTC_Z_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)

_T = TypeVar("_T")


class _ProjectionInvalid(Exception):
    pass


def build_canonical_gold_market_facts_snapshot_v1(
    *,
    validated_source: CanonicalGoldMarketFactsSourceV1,
) -> CanonicalGoldMarketFactsSnapshotV1:
    try:
        if not _has_exact_source_shape(validated_source):
            return _failure(_INPUT_INVALID_STATUS, _SOURCE_TYPE_INVALID)
        if not _has_valid_authority(validated_source):
            return _failure(_AUTHORITY_INVALID_STATUS, _SOURCE_AUTHORITY_INVALID)
        if not _is_upstream_ready(validated_source.upstream_evidence):
            return _failure(_UPSTREAM_BLOCKED_STATUS, _UPSTREAM_NOT_READY)
        if validated_source.upstream_evidence.warning_codes:
            return _failure(_UPSTREAM_BLOCKED_STATUS, _UPSTREAM_WARNINGS_REJECTED)
        if not _has_valid_identity(validated_source):
            return _failure(_IDENTITY_INVALID_STATUS, _IDENTITY_INVALID)

        reference_time = _parse_utc_z(validated_source.reference_time_utc)
        bars_generated_time = _parse_utc_z(validated_source.bars_generated_at_utc)
        context = _new_decimal_context()
        with localcontext(context) as active_context:
            quote = _project_quote(validated_source.live_tick, active_context)
            if quote is None:
                return _failure(_VALUE_INVALID_STATUS, _TICK_INVALID)

            timeframe_facts = _project_timeframes(
                validated_source.timeframes,
                digits=validated_source.live_tick.digits,
                bars_generated_time=bars_generated_time,
                context=active_context,
            )
            if timeframe_facts is None:
                return _failure(_VALUE_INVALID_STATUS, _BARS_INVALID)

            symbol_facts = _project_symbol(
                validated_source.symbol_spec,
                live_tick=validated_source.live_tick,
                context=active_context,
            )
            if symbol_facts is None:
                return _failure(_VALUE_INVALID_STATUS, _SYMBOL_SPEC_INVALID)

        freshness = _project_freshness(
            reference_time=reference_time,
            tick_time=_parse_utc_z(validated_source.live_tick.tick_time_utc),
            bars_generated_time=bars_generated_time,
            symbol_spec_time=_parse_utc_z(validated_source.symbol_spec.spec_time_utc),
        )
        if freshness is None:
            return _failure(_VALUE_INVALID_STATUS, _FRESHNESS_INVALID)

        return CanonicalGoldMarketFactsSnapshotV1(
            contract_version=_CONTRACT_VERSION,
            passed=True,
            status_code=_READY_STATUS,
            reason_codes=(),
            warning_codes=(),
            identity_available=True,
            bundle_schema_version=validated_source.bundle_schema_version,
            bundle_id=validated_source.bundle_id,
            sequence=validated_source.sequence,
            canonical_symbol=validated_source.canonical_symbol,
            broker_symbol=validated_source.broker_symbol,
            reference_time_utc=validated_source.reference_time_utc,
            quote=quote,
            timeframes=timeframe_facts,
            symbol_spec=symbol_facts,
            freshness=freshness,
            read_only=True,
            demo_only=True,
            is_tradable=False,
            can_execute=False,
            is_trading_permission=False,
            is_execution_instruction=False,
            allowed_to_call_ea=False,
            allowed_to_modify_risk=False,
        )
    except Exception:
        return _failure(_SAFE_FAILURE_STATUS, _EXCEPTION_SANITIZED)


def _has_exact_source_shape(source: object) -> bool:
    if type(source) is not CanonicalGoldMarketFactsSourceV1:
        return False
    if not (
        type(source.contract_version) is str
        and type(source.bundle_schema_version) is str
        and type(source.bundle_id) is str
        and type(source.sequence) is int
        and type(source.canonical_symbol) is str
        and type(source.broker_symbol) is str
        and type(source.reference_time_utc) is str
        and type(source.policy_profile_version) is str
        and type(source.upstream_evidence) is CanonicalGoldUpstreamEvidenceV1
        and type(source.live_tick) is CanonicalGoldTickSourceV1
        and type(source.bars_generated_at_utc) is str
        and type(source.timeframes) is tuple
        and type(source.symbol_spec) is CanonicalGoldSymbolSpecSourceV1
    ):
        return False

    evidence = source.upstream_evidence
    if not (
        type(evidence.reader_passed) is bool
        and type(evidence.reader_status_code) is str
        and type(evidence.value_status_code) is str
        and type(evidence.data_quality_passed) is bool
        and type(evidence.data_quality_status_code) is str
        and type(evidence.ready_for_readonly_analysis) is bool
        and type(evidence.warning_codes) is tuple
        and all(type(code) is str for code in evidence.warning_codes)
        and type(evidence.same_attempt_identity_bound) is bool
    ):
        return False

    tick = source.live_tick
    if not (
        _is_exact_number(tick.bid)
        and _is_exact_number(tick.ask)
        and _is_exact_number(tick.spread)
        and type(tick.spread_points) is int
        and type(tick.digits) is int
        and _is_exact_number(tick.point)
        and type(tick.tick_time_utc) is str
    ):
        return False

    if len(source.timeframes) != len(_TIMEFRAME_PERIODS):
        return False
    for timeframe in source.timeframes:
        if not (
            type(timeframe) is CanonicalGoldTimeframeSourceV1
            and type(timeframe.timeframe) is str
            and type(timeframe.period_seconds) is int
            and type(timeframe.bars) is tuple
        ):
            return False
        for bar in timeframe.bars:
            if not (
                type(bar) is CanonicalGoldBarSourceV1
                and type(bar.open_time_utc) is str
                and _is_exact_number(bar.open)
                and _is_exact_number(bar.high)
                and _is_exact_number(bar.low)
                and _is_exact_number(bar.close)
                and type(bar.tick_volume) is int
                and type(bar.spread_points) is int
            ):
                return False

    spec = source.symbol_spec
    return (
        type(spec.spec_time_utc) is str
        and type(spec.digits) is int
        and _is_exact_number(spec.point)
        and _is_exact_number(spec.tick_size)
        and _is_exact_number(spec.tick_value)
        and _is_exact_number(spec.contract_size)
        and _is_exact_number(spec.min_lot)
        and _is_exact_number(spec.lot_step)
        and _is_exact_number(spec.max_lot)
        and type(spec.base_currency) is str
        and type(spec.profit_currency) is str
        and type(spec.margin_currency) is str
        and type(spec.trade_mode_readonly_label) is str
        and type(spec.session_status_readonly_label) is str
    )


def _has_valid_authority(source: CanonicalGoldMarketFactsSourceV1) -> bool:
    return (
        source.contract_version == _CONTRACT_VERSION
        and source.bundle_schema_version == _BUNDLE_SCHEMA_VERSION
        and source.canonical_symbol == _CANONICAL_SYMBOL
        and source.broker_symbol == _BROKER_SYMBOL
        and source.policy_profile_version == _POLICY_PROFILE_VERSION
        and source.upstream_evidence.same_attempt_identity_bound is True
    )


def _is_upstream_ready(evidence: CanonicalGoldUpstreamEvidenceV1) -> bool:
    return (
        evidence.reader_passed is True
        and evidence.reader_status_code == _READER_VALID
        and evidence.value_status_code == _VALUE_VALID
        and evidence.data_quality_passed is True
        and evidence.data_quality_status_code == _DATA_QUALITY_VALID
        and evidence.ready_for_readonly_analysis is True
    )


def _has_valid_identity(source: CanonicalGoldMarketFactsSourceV1) -> bool:
    return (
        16 <= len(source.bundle_id) <= 64
        and source.bundle_id.isascii()
        and _BUNDLE_ID_PATTERN.fullmatch(source.bundle_id) is not None
        and source.sequence > 0
    )


def _project_quote(
    tick: CanonicalGoldTickSourceV1,
    context: Context,
) -> CanonicalGoldQuoteFactsV1 | None:
    try:
        if not (0 <= tick.digits <= 8 and tick.spread_points >= 0):
            return None
        if _parse_utc_z(tick.tick_time_utc) is None:
            return None

        bid = _decimal_from_source(tick.bid, context)
        ask = _decimal_from_source(tick.ask, context)
        spread = _decimal_from_source(tick.spread, context)
        point = _decimal_from_source(tick.point, context)
        quantum = _price_quantum(tick.digits, context)
        if not (
            bid > 0
            and ask > 0
            and spread >= 0
            and point > 0
            and ask >= bid
            and point == quantum
        ):
            return None
        for value in (bid, ask, spread, point):
            if not _is_price_representable(value, tick.digits):
                return None

        spread_from_prices = _checked_decimal_operation(
            context, lambda: context.subtract(ask, bid)
        )
        spread_points_decimal = Decimal(str(tick.spread_points))
        spread_from_points = _checked_decimal_operation(
            context, lambda: context.multiply(spread_points_decimal, point)
        )
        if spread != spread_from_prices or spread != spread_from_points:
            return None

        return CanonicalGoldQuoteFactsV1(
            bid_decimal=_format_price(bid, tick.digits),
            ask_decimal=_format_price(ask, tick.digits),
            spread_decimal=_format_price(spread, tick.digits),
            spread_points=tick.spread_points,
            digits=tick.digits,
            point_decimal=_format_price(point, tick.digits),
            tick_time_utc=tick.tick_time_utc,
        )
    except (_ProjectionInvalid, DecimalException, ValueError, OverflowError):
        return None


def _project_timeframes(
    timeframes: tuple[CanonicalGoldTimeframeSourceV1, ...],
    *,
    digits: int,
    bars_generated_time: datetime | None,
    context: Context,
) -> tuple[CanonicalGoldTimeframeFactsV1, ...] | None:
    try:
        if bars_generated_time is None:
            return None
        projected_timeframes: list[CanonicalGoldTimeframeFactsV1] = []
        for source_timeframe, expected in zip(
            timeframes,
            _TIMEFRAME_PERIODS,
            strict=True,
        ):
            if (
                (source_timeframe.timeframe, source_timeframe.period_seconds) != expected
                or not 1 <= len(source_timeframe.bars) <= 500
            ):
                return None

            projected_bars: list[CanonicalGoldBarFactsV1] = []
            previous_open_time: datetime | None = None
            for source_bar in source_timeframe.bars:
                open_time = _parse_utc_z(source_bar.open_time_utc)
                if open_time is None:
                    return None
                if previous_open_time is not None and open_time <= previous_open_time:
                    return None
                previous_open_time = open_time
                try:
                    if (
                        open_time + timedelta(seconds=expected[1])
                        > bars_generated_time
                    ):
                        return None
                except OverflowError:
                    return None
                if source_bar.tick_volume < 0 or source_bar.spread_points < 0:
                    return None

                open_value = _decimal_from_source(source_bar.open, context)
                high_value = _decimal_from_source(source_bar.high, context)
                low_value = _decimal_from_source(source_bar.low, context)
                close_value = _decimal_from_source(source_bar.close, context)
                prices = (open_value, high_value, low_value, close_value)
                if not all(
                    value > 0 and _is_price_representable(value, digits)
                    for value in prices
                ):
                    return None
                if high_value < max(open_value, low_value, close_value):
                    return None
                if low_value > min(open_value, high_value, close_value):
                    return None

                projected_bars.append(
                    CanonicalGoldBarFactsV1(
                        open_time_utc=source_bar.open_time_utc,
                        open_decimal=_format_price(open_value, digits),
                        high_decimal=_format_price(high_value, digits),
                        low_decimal=_format_price(low_value, digits),
                        close_decimal=_format_price(close_value, digits),
                        tick_volume=source_bar.tick_volume,
                        spread_points=source_bar.spread_points,
                    )
                )

            projected_timeframes.append(
                CanonicalGoldTimeframeFactsV1(
                    timeframe=source_timeframe.timeframe,
                    period_seconds=source_timeframe.period_seconds,
                    bars=tuple(projected_bars),
                )
            )
        return tuple(projected_timeframes)
    except (_ProjectionInvalid, DecimalException, ValueError, OverflowError):
        return None


def _project_symbol(
    spec: CanonicalGoldSymbolSpecSourceV1,
    *,
    live_tick: CanonicalGoldTickSourceV1,
    context: Context,
) -> CanonicalGoldSymbolFactsV1 | None:
    try:
        if _parse_utc_z(spec.spec_time_utc) is None:
            return None
        if not (0 <= spec.digits <= 8 and spec.digits == live_tick.digits):
            return None
        if not (
            spec.base_currency == "XAU"
            and spec.profit_currency == "USD"
            and _is_safe_label(spec.margin_currency)
            and _is_safe_label(spec.trade_mode_readonly_label)
            and _is_safe_label(spec.session_status_readonly_label)
        ):
            return None

        point = _decimal_from_source(spec.point, context)
        tick_size = _decimal_from_source(spec.tick_size, context)
        tick_value = _decimal_from_source(spec.tick_value, context)
        contract_size = _decimal_from_source(spec.contract_size, context)
        min_lot = _decimal_from_source(spec.min_lot, context)
        lot_step = _decimal_from_source(spec.lot_step, context)
        max_lot = _decimal_from_source(spec.max_lot, context)
        tick_point = _decimal_from_source(live_tick.point, context)
        quantum = _price_quantum(spec.digits, context)

        if not all(
            value > 0
            for value in (
                point,
                tick_size,
                tick_value,
                contract_size,
                min_lot,
                lot_step,
                max_lot,
            )
        ):
            return None
        if not (point == tick_point == quantum):
            return None
        if not (
            _is_price_representable(point, spec.digits)
            and _is_price_representable(tick_size, spec.digits)
        ):
            return None
        if min_lot > max_lot or lot_step > max_lot:
            return None

        return CanonicalGoldSymbolFactsV1(
            spec_time_utc=spec.spec_time_utc,
            digits=spec.digits,
            point_decimal=_format_price(point, spec.digits),
            tick_size_decimal=_format_price(tick_size, spec.digits),
            tick_value_decimal=_format_non_price(tick_value),
            contract_size_decimal=_format_non_price(contract_size),
            min_lot_decimal=_format_non_price(min_lot),
            lot_step_decimal=_format_non_price(lot_step),
            max_lot_decimal=_format_non_price(max_lot),
            base_currency=spec.base_currency,
            profit_currency=spec.profit_currency,
            margin_currency=spec.margin_currency,
            trade_mode_readonly_label=spec.trade_mode_readonly_label,
            session_status_readonly_label=spec.session_status_readonly_label,
        )
    except (_ProjectionInvalid, DecimalException, ValueError, OverflowError):
        return None


def _project_freshness(
    *,
    reference_time: datetime | None,
    tick_time: datetime | None,
    bars_generated_time: datetime | None,
    symbol_spec_time: datetime | None,
) -> CanonicalGoldFreshnessFactsV1 | None:
    if any(
        value is None
        for value in (reference_time, tick_time, bars_generated_time, symbol_spec_time)
    ):
        return None
    try:
        return CanonicalGoldFreshnessFactsV1(
            tick_age_microseconds=_age_microseconds(reference_time, tick_time),
            bars_payload_age_microseconds=_age_microseconds(
                reference_time, bars_generated_time
            ),
            symbol_spec_age_microseconds=_age_microseconds(reference_time, symbol_spec_time),
        )
    except (_ProjectionInvalid, OverflowError):
        return None


def _failure(
    status_code: str,
    reason_code: str,
) -> CanonicalGoldMarketFactsSnapshotV1:
    return CanonicalGoldMarketFactsSnapshotV1(
        contract_version=_CONTRACT_VERSION,
        passed=False,
        status_code=status_code,
        reason_codes=(reason_code,),
        warning_codes=(),
        identity_available=False,
        bundle_schema_version=None,
        bundle_id=None,
        sequence=None,
        canonical_symbol=None,
        broker_symbol=None,
        reference_time_utc=None,
        quote=None,
        timeframes=(),
        symbol_spec=None,
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


def _new_decimal_context() -> Context:
    context = Context(
        prec=64,
        rounding=ROUND_HALF_EVEN,
        Emin=-999999,
        Emax=999999,
        capitals=1,
        clamp=0,
    )
    for signal in context.traps:
        context.traps[signal] = False
    for signal in (InvalidOperation, DivisionByZero, Overflow):
        context.traps[signal] = True
    context.clear_flags()
    return context


def _decimal_from_source(value: int | float, context: Context) -> Decimal:
    if not _is_exact_number(value):
        raise _ProjectionInvalid
    if type(value) is float and not math.isfinite(value):
        raise _ProjectionInvalid
    decimal_value = Decimal(str(value))
    if not decimal_value.is_finite() or (
        decimal_value.is_zero() and decimal_value.is_signed()
    ):
        raise _ProjectionInvalid
    checked = _checked_decimal_operation(context, lambda: context.plus(decimal_value))
    if checked != decimal_value:
        raise _ProjectionInvalid
    return decimal_value


def _price_quantum(digits: int, context: Context) -> Decimal:
    return _checked_decimal_operation(
        context,
        lambda: Decimal(1).scaleb(-digits, context=context),
    )


def _checked_decimal_operation(context: Context, operation: Callable[[], _T]) -> _T:
    context.clear_flags()
    try:
        value = operation()
    except DecimalException as exc:
        raise _ProjectionInvalid from exc
    if any(context.flags.values()):
        raise _ProjectionInvalid
    return value


def _is_price_representable(value: Decimal, digits: int) -> bool:
    exponent = value.as_tuple().exponent
    return type(exponent) is int and exponent >= -digits


def _format_price(value: Decimal, digits: int) -> str:
    formatted = format(value, f".{digits}f")
    if "E" in formatted or "e" in formatted or formatted.startswith("+"):
        raise _ProjectionInvalid
    if digits == 0:
        if "." in formatted:
            raise _ProjectionInvalid
    elif len(formatted.rpartition(".")[2]) != digits:
        raise _ProjectionInvalid
    return formatted


def _format_non_price(value: Decimal) -> str:
    if value.is_zero():
        return "0"
    formatted = format(value, "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    if (
        not formatted
        or "E" in formatted
        or "e" in formatted
        or formatted.startswith("+")
    ):
        raise _ProjectionInvalid
    return formatted


def _parse_utc_z(value: str) -> datetime | None:
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


def _age_microseconds(reference_time: datetime, observed_time: datetime) -> int:
    if observed_time > reference_time:
        raise _ProjectionInvalid
    delta = reference_time - observed_time
    return ((delta.days * 86400) + delta.seconds) * 1_000_000 + delta.microseconds


def _is_exact_number(value: object) -> bool:
    return type(value) is int or type(value) is float


def _is_safe_label(value: str) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value.isascii()
        and _SAFE_LABEL_PATTERN.fullmatch(value) is not None
    )
