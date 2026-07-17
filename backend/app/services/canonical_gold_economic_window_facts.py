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
class CanonicalGoldEconomicCalendarUpstreamEvidenceV1:
    adapter_passed: bool
    adapter_status_code: str
    schema_validated: bool
    identity_validated: bool
    timestamps_normalized: bool
    same_snapshot_bound: bool
    warning_codes: tuple[str, ...]
    raw_payload_discarded: bool


@dataclass(frozen=True, slots=True)
class CanonicalGoldEconomicEventSourceV1:
    event_id: str
    scheduled_at_utc: str
    country_code: str
    currency_code: str
    event_category_code: str
    impact_code: str
    source_revision: int
    event_status_code: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldEconomicCalendarSnapshotV1:
    contract_version: str
    calendar_schema_version: str
    calendar_snapshot_id: str
    source_profile_version: str
    generated_at_utc: str
    coverage_start_utc: str
    coverage_end_utc: str
    events: tuple[CanonicalGoldEconomicEventSourceV1, ...]
    upstream_evidence: CanonicalGoldEconomicCalendarUpstreamEvidenceV1
    read_only: bool
    demo_only: bool
    contains_raw_provider_payload: bool


@dataclass(frozen=True, slots=True)
class CanonicalGoldEconomicEventWindowFactsV1:
    event_id: str
    scheduled_at_utc: str
    country_code: str
    currency_code: str
    event_category_code: str
    impact_code: str
    source_revision: int
    window_start_utc: str
    window_end_utc: str
    event_offset_microseconds: int
    window_start_offset_microseconds: int
    window_end_offset_microseconds: int
    window_relation_code: str
    is_active_observation_window: bool


@dataclass(frozen=True, slots=True)
class CanonicalGoldEconomicWindowSummaryV1:
    calendar_age_microseconds: int
    relevant_event_count: int
    active_window_count: int
    inside_any_observation_window: bool
    active_event_ids: tuple[str, ...]
    nearest_previous_event_id: str | None
    nearest_previous_event_offset_microseconds: int | None
    nearest_next_event_id: str | None
    nearest_next_event_offset_microseconds: int | None
    highest_active_impact_code: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldEconomicWindowFactsV1:
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
    calendar_contract_version: str | None
    calendar_schema_version: str | None
    calendar_snapshot_id: str | None
    calendar_source_profile_version: str | None
    calendar_generated_at_utc: str | None
    calendar_coverage_start_utc: str | None
    calendar_coverage_end_utc: str | None
    event_windows: tuple[CanonicalGoldEconomicEventWindowFactsV1, ...]
    summary: CanonicalGoldEconomicWindowSummaryV1 | None
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool


__all__ = (
    "CanonicalGoldEconomicCalendarSnapshotV1",
    "CanonicalGoldEconomicCalendarUpstreamEvidenceV1",
    "CanonicalGoldEconomicEventSourceV1",
    "CanonicalGoldEconomicWindowFactsV1",
    "CanonicalGoldEconomicEventWindowFactsV1",
    "CanonicalGoldEconomicWindowSummaryV1",
    "build_canonical_gold_economic_window_facts_v1",
)


_CONTRACT_VERSION = "1.0"
_FACTS_PROFILE_VERSION = "canonical_gold_economic_window_profile_v1"
_CALENDAR_SOURCE_PROFILE_VERSION = "canonical_gold_economic_calendar_source_v1"
_CALENDAR_READY_STATUS = "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY"
_MARKET_READY_STATUS = "CANONICAL_GOLD_MARKET_FACTS_READY"
_READY_STATUS = "CANONICAL_GOLD_ECONOMIC_WINDOW_READY"

_FAILURES = (
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_INPUT_INVALID",
        "GOLD_ECONOMIC_WINDOW_INPUT_TYPE_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_UPSTREAM_BLOCKED",
        "GOLD_ECONOMIC_WINDOW_MARKET_SNAPSHOT_NOT_READY",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_MARKET_IDENTITY_INVALID",
        "GOLD_ECONOMIC_WINDOW_MARKET_IDENTITY_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_MARKET_VALUE_INVALID",
        "GOLD_ECONOMIC_WINDOW_MARKET_FACTS_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_AUTHORITY_INVALID",
        "GOLD_ECONOMIC_WINDOW_CALENDAR_AUTHORITY_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_IDENTITY_INVALID",
        "GOLD_ECONOMIC_WINDOW_CALENDAR_IDENTITY_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_FRESHNESS_INVALID",
        "GOLD_ECONOMIC_WINDOW_CALENDAR_FRESHNESS_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_COVERAGE_INVALID",
        "GOLD_ECONOMIC_WINDOW_CALENDAR_COVERAGE_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_EVENT_INVALID",
        "GOLD_ECONOMIC_WINDOW_EVENT_INPUT_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_RESULT_INVALID",
        "GOLD_ECONOMIC_WINDOW_RESULT_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_WINDOW_SAFE_FAILURE",
        "GOLD_ECONOMIC_WINDOW_EXCEPTION_SANITIZED",
    ),
)

_CALENDAR_MAXIMUM_AGE_MICROSECONDS = 300_000_000
_SEARCH_HORIZON_SECONDS = 86_400
_MAXIMUM_CALENDAR_EVENTS = 512
_MAXIMUM_COVERAGE_SPAN_MICROSECONDS = 259_200_000_000
_TIMEFRAME_PERIODS = (("M15", 900), ("H1", 3600), ("H4", 14_400), ("D1", 86_400))
_EVENT_CATEGORIES = (
    "FOMC_RATE_DECISION",
    "FOMC_STATEMENT",
    "FOMC_PRESS_CONFERENCE",
    "US_CPI",
    "US_CORE_CPI",
    "US_PCE",
    "US_CORE_PCE",
    "US_NONFARM_PAYROLLS",
    "US_UNEMPLOYMENT_RATE",
    "US_GDP",
    "US_RETAIL_SALES",
    "US_ISM_MANUFACTURING",
    "US_ISM_SERVICES",
)
_IMPACT_CODES = ("LOW", "MEDIUM", "HIGH")
_EVENT_STATUS_CODES = ("SCHEDULED", "CANCELLED")

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$", re.ASCII)
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
_CALENDAR_FIELDS = (
    "contract_version",
    "calendar_schema_version",
    "calendar_snapshot_id",
    "source_profile_version",
    "generated_at_utc",
    "coverage_start_utc",
    "coverage_end_utc",
    "events",
    "upstream_evidence",
    "read_only",
    "demo_only",
    "contains_raw_provider_payload",
)
_UPSTREAM_FIELDS = (
    "adapter_passed",
    "adapter_status_code",
    "schema_validated",
    "identity_validated",
    "timestamps_normalized",
    "same_snapshot_bound",
    "warning_codes",
    "raw_payload_discarded",
)
_EVENT_FIELDS = (
    "event_id",
    "scheduled_at_utc",
    "country_code",
    "currency_code",
    "event_category_code",
    "impact_code",
    "source_revision",
    "event_status_code",
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
    "calendar_contract_version",
    "calendar_schema_version",
    "calendar_snapshot_id",
    "calendar_source_profile_version",
    "calendar_generated_at_utc",
    "calendar_coverage_start_utc",
    "calendar_coverage_end_utc",
    "event_windows",
    "summary",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
_WINDOW_FIELDS = (
    "event_id",
    "scheduled_at_utc",
    "country_code",
    "currency_code",
    "event_category_code",
    "impact_code",
    "source_revision",
    "window_start_utc",
    "window_end_utc",
    "event_offset_microseconds",
    "window_start_offset_microseconds",
    "window_end_offset_microseconds",
    "window_relation_code",
    "is_active_observation_window",
)
_SUMMARY_FIELDS = (
    "calendar_age_microseconds",
    "relevant_event_count",
    "active_window_count",
    "inside_any_observation_window",
    "active_event_ids",
    "nearest_previous_event_id",
    "nearest_previous_event_offset_microseconds",
    "nearest_next_event_id",
    "nearest_next_event_offset_microseconds",
    "highest_active_impact_code",
)


def build_canonical_gold_economic_window_facts_v1(
    *,
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,
    economic_calendar_snapshot: CanonicalGoldEconomicCalendarSnapshotV1,
) -> CanonicalGoldEconomicWindowFactsV1:
    try:
        if not _has_exact_input_shape(market_facts_snapshot, economic_calendar_snapshot):
            return _failure(*_FAILURES[0])
        if not _has_ready_market_authority(market_facts_snapshot):
            return _failure(*_FAILURES[1])
        if not _has_valid_market_identity(market_facts_snapshot):
            return _failure(*_FAILURES[2])
        if not _has_valid_market_values(market_facts_snapshot):
            return _failure(*_FAILURES[3])
        if not _has_valid_calendar_authority(economic_calendar_snapshot):
            return _failure(*_FAILURES[4])
        if not _has_valid_calendar_identity(economic_calendar_snapshot):
            return _failure(*_FAILURES[5])

        reference_time = _parse_utc_z(market_facts_snapshot.reference_time_utc)
        generated_time = _parse_utc_z(economic_calendar_snapshot.generated_at_utc)
        if (
            reference_time is None
            or generated_time is None
            or not _has_valid_calendar_freshness(reference_time, generated_time)
        ):
            return _failure(*_FAILURES[6])

        coverage_start = _parse_utc_z(economic_calendar_snapshot.coverage_start_utc)
        coverage_end = _parse_utc_z(economic_calendar_snapshot.coverage_end_utc)
        if not _has_valid_calendar_coverage(
            reference_time,
            coverage_start,
            coverage_end,
        ):
            return _failure(*_FAILURES[7])
        if not _has_valid_events(economic_calendar_snapshot, coverage_start, coverage_end):
            return _failure(*_FAILURES[8])

        event_windows = _build_event_windows(economic_calendar_snapshot.events, reference_time)
        summary = _build_summary(event_windows, reference_time, generated_time)
        result = _ready_result(
            market_facts_snapshot,
            economic_calendar_snapshot,
            event_windows,
            summary,
        )
        if not _is_valid_ready_result(
            result,
            market_facts_snapshot,
            economic_calendar_snapshot,
            event_windows,
            summary,
        ):
            return _failure(*_FAILURES[9])
        return result
    except Exception:
        return _failure(*_FAILURES[10])


def _has_exact_input_shape(market: object, calendar: object) -> bool:
    try:
        return _has_exact_market_shape(market) and _has_exact_calendar_shape(calendar)
    except (AttributeError, TypeError):
        return False


def _has_exact_market_shape(value: object) -> bool:
    if not _is_exact_record(value, CanonicalGoldMarketFactsSnapshotV1, _SNAPSHOT_FIELDS):
        return False
    return (
        type(value.contract_version) is str
        and type(value.passed) is bool
        and type(value.status_code) is str
        and _is_string_tuple(value.reason_codes)
        and _is_string_tuple(value.warning_codes)
        and type(value.identity_available) is bool
        and _is_optional_str(value.bundle_schema_version)
        and _is_optional_str(value.bundle_id)
        and _is_optional_int(value.sequence)
        and _is_optional_str(value.canonical_symbol)
        and _is_optional_str(value.broker_symbol)
        and _is_optional_str(value.reference_time_utc)
        and (value.quote is None or _has_exact_quote_shape(value.quote))
        and type(value.timeframes) is tuple
        and all(_has_exact_timeframe_shape(item) for item in value.timeframes)
        and (value.symbol_spec is None or _has_exact_symbol_shape(value.symbol_spec))
        and (value.freshness is None or _has_exact_freshness_shape(value.freshness))
        and type(value.read_only) is bool
        and type(value.demo_only) is bool
        and type(value.is_tradable) is bool
        and type(value.can_execute) is bool
        and type(value.is_trading_permission) is bool
        and type(value.is_execution_instruction) is bool
        and type(value.allowed_to_call_ea) is bool
        and type(value.allowed_to_modify_risk) is bool
    )


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
    return _is_exact_record(value, CanonicalGoldSymbolFactsV1, _SYMBOL_FIELDS) and all(
        type(getattr(value, field)) is (int if field == "digits" else str)
        for field in _SYMBOL_FIELDS
    )


def _has_exact_freshness_shape(value: object) -> bool:
    return _is_exact_record(value, CanonicalGoldFreshnessFactsV1, _FRESHNESS_FIELDS) and all(
        type(getattr(value, field)) is int for field in _FRESHNESS_FIELDS
    )


def _has_exact_calendar_shape(value: object) -> bool:
    if not _is_exact_record(value, CanonicalGoldEconomicCalendarSnapshotV1, _CALENDAR_FIELDS):
        return False
    return (
        all(
            type(getattr(value, field)) is str
            for field in _CALENDAR_FIELDS[:7]
        )
        and type(value.events) is tuple
        and all(_has_exact_event_shape(event) for event in value.events)
        and _has_exact_upstream_shape(value.upstream_evidence)
        and type(value.read_only) is bool
        and type(value.demo_only) is bool
        and type(value.contains_raw_provider_payload) is bool
    )


def _has_exact_upstream_shape(value: object) -> bool:
    if not _is_exact_record(
        value,
        CanonicalGoldEconomicCalendarUpstreamEvidenceV1,
        _UPSTREAM_FIELDS,
    ):
        return False
    return (
        type(value.adapter_passed) is bool
        and type(value.adapter_status_code) is str
        and type(value.schema_validated) is bool
        and type(value.identity_validated) is bool
        and type(value.timestamps_normalized) is bool
        and type(value.same_snapshot_bound) is bool
        and _is_string_tuple(value.warning_codes)
        and type(value.raw_payload_discarded) is bool
    )


def _has_exact_event_shape(value: object) -> bool:
    return _is_exact_record(value, CanonicalGoldEconomicEventSourceV1, _EVENT_FIELDS) and (
        all(type(getattr(value, field)) is str for field in _EVENT_FIELDS[:6])
        and type(value.source_revision) is int
        and type(value.event_status_code) is str
    )


def _is_exact_record(value: object, expected: type[object], fields: tuple[str, ...]) -> bool:
    return type(value) is expected and getattr(type(value), "__slots__", None) == fields


def _is_string_tuple(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _is_optional_str(value: object) -> bool:
    return value is None or type(value) is str


def _is_optional_int(value: object) -> bool:
    return value is None or type(value) is int


def _has_ready_market_authority(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
    return (
        snapshot.contract_version == _CONTRACT_VERSION
        and snapshot.passed is True
        and snapshot.status_code == _MARKET_READY_STATUS
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
    )


def _has_valid_market_identity(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
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


def _has_valid_market_values(snapshot: CanonicalGoldMarketFactsSnapshotV1) -> bool:
    quote = snapshot.quote
    symbol = snapshot.symbol_spec
    freshness = snapshot.freshness
    if quote is None or symbol is None or freshness is None:
        return False
    reference = _parse_utc_z(snapshot.reference_time_utc)
    if reference is None or not 0 <= quote.digits <= 8 or symbol.digits != quote.digits:
        return False
    pattern = _source_price_pattern(quote.digits)
    quote_values = tuple(
        _parse_fixed_price(value, pattern)
        for value in (
            quote.bid_decimal,
            quote.ask_decimal,
            quote.spread_decimal,
            quote.point_decimal,
            symbol.point_decimal,
            symbol.tick_size_decimal,
        )
    )
    if any(value is None for value in quote_values):
        return False
    bid, ask, spread, point, symbol_point, tick_size = (
        value for value in quote_values if value is not None
    )
    if not (
        bid > 0
        and ask > 0
        and ask >= bid
        and spread >= 0
        and point == symbol_point == 1
        and tick_size > 0
        and quote.spread_points >= 0
        and ask - bid == spread
        and quote.spread_points * point == spread
    ):
        return False
    non_price = tuple(
        _parse_positive_decimal(value)
        for value in (
            symbol.tick_value_decimal,
            symbol.contract_size_decimal,
            symbol.min_lot_decimal,
            symbol.lot_step_decimal,
            symbol.max_lot_decimal,
        )
    )
    if any(value is None for value in non_price):
        return False
    tick_value, contract_size, min_lot, lot_step, max_lot = non_price
    if not (
        tick_value is not None
        and contract_size is not None
        and min_lot is not None
        and lot_step is not None
        and max_lot is not None
        and _compare_scaled(min_lot, max_lot) <= 0
        and _compare_scaled(lot_step, max_lot) <= 0
    ):
        return False
    if not (
        symbol.base_currency == "XAU"
        and symbol.profit_currency == "USD"
        and _is_safe_label(symbol.margin_currency)
        and _is_safe_label(symbol.trade_mode_readonly_label)
        and _is_safe_label(symbol.session_status_readonly_label)
    ):
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
    if (
        tick_time is None
        or spec_time is None
        or _microseconds_between(reference, tick_time) != ages[0]
        or _microseconds_between(reference, spec_time) != ages[2]
    ):
        return False
    try:
        bars_payload_time = reference - timedelta(microseconds=ages[1])
    except OverflowError:
        return False
    if len(snapshot.timeframes) != 4:
        return False
    for timeframe, authority in zip(snapshot.timeframes, _TIMEFRAME_PERIODS, strict=True):
        if (
            (timeframe.timeframe, timeframe.period_seconds) != authority
            or not 1 <= len(timeframe.bars) <= 500
        ):
            return False
        previous_time: datetime | None = None
        for bar in timeframe.bars:
            bar_time = _parse_utc_z(bar.open_time_utc)
            if (
                bar_time is None
                or (previous_time is not None and bar_time <= previous_time)
                or bar.tick_volume < 0
                or bar.spread_points < 0
            ):
                return False
            previous_time = bar_time
            try:
                if bar_time + timedelta(seconds=timeframe.period_seconds) > bars_payload_time:
                    return False
            except OverflowError:
                return False
            prices = tuple(
                _parse_fixed_price(value, pattern)
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
            if (
                high_value < max(open_value, low_value, close_value)
                or low_value > min(open_value, high_value, close_value)
            ):
                return False
    return True


def _has_valid_calendar_authority(snapshot: CanonicalGoldEconomicCalendarSnapshotV1) -> bool:
    upstream = snapshot.upstream_evidence
    return (
        snapshot.read_only is True
        and snapshot.demo_only is True
        and snapshot.contains_raw_provider_payload is False
        and upstream.adapter_passed is True
        and upstream.adapter_status_code == _CALENDAR_READY_STATUS
        and upstream.schema_validated is True
        and upstream.identity_validated is True
        and upstream.timestamps_normalized is True
        and upstream.same_snapshot_bound is True
        and upstream.warning_codes == ()
        and upstream.raw_payload_discarded is True
    )


def _has_valid_calendar_identity(snapshot: CanonicalGoldEconomicCalendarSnapshotV1) -> bool:
    return (
        snapshot.contract_version == _CONTRACT_VERSION
        and snapshot.calendar_schema_version == _CONTRACT_VERSION
        and snapshot.source_profile_version == _CALENDAR_SOURCE_PROFILE_VERSION
        and _is_identifier(snapshot.calendar_snapshot_id, 16, 64)
    )


def _has_valid_calendar_freshness(reference: datetime, generated: datetime) -> bool:
    age = _microseconds_between(reference, generated)
    return 0 <= age <= _CALENDAR_MAXIMUM_AGE_MICROSECONDS


def _has_valid_calendar_coverage(
    reference: datetime,
    start: datetime | None,
    end: datetime | None,
) -> bool:
    if start is None or end is None or start >= end:
        return False
    try:
        required_start = reference - timedelta(seconds=_SEARCH_HORIZON_SECONDS)
        required_end = reference + timedelta(seconds=_SEARCH_HORIZON_SECONDS)
    except OverflowError:
        return False
    return (
        start <= required_start
        and end > required_end
        and _microseconds_between(end, start) <= _MAXIMUM_COVERAGE_SPAN_MICROSECONDS
    )


def _has_valid_events(
    snapshot: CanonicalGoldEconomicCalendarSnapshotV1,
    coverage_start: datetime | None,
    coverage_end: datetime | None,
) -> bool:
    if (
        coverage_start is None
        or coverage_end is None
        or len(snapshot.events) > _MAXIMUM_CALENDAR_EVENTS
    ):
        return False
    previous_key: tuple[datetime, str] | None = None
    event_ids: set[str] = set()
    for event in snapshot.events:
        scheduled = _parse_utc_z(event.scheduled_at_utc)
        if not (
            _is_identifier(event.event_id, 8, 64)
            and scheduled is not None
            and coverage_start <= scheduled < coverage_end
            and event.country_code == "US"
            and event.currency_code == "USD"
            and event.event_category_code in _EVENT_CATEGORIES
            and event.impact_code in _IMPACT_CODES
            and event.source_revision > 0
            and event.event_status_code in _EVENT_STATUS_CODES
            and event.event_id not in event_ids
        ):
            return False
        key = (scheduled, event.event_id)
        if previous_key is not None and key <= previous_key:
            return False
        previous_key = key
        event_ids.add(event.event_id)
    return True


def _build_event_windows(
    events: tuple[CanonicalGoldEconomicEventSourceV1, ...],
    reference: datetime,
) -> tuple[CanonicalGoldEconomicEventWindowFactsV1, ...]:
    search_start = reference - timedelta(seconds=_SEARCH_HORIZON_SECONDS)
    search_end = reference + timedelta(seconds=_SEARCH_HORIZON_SECONDS)
    output: list[CanonicalGoldEconomicEventWindowFactsV1] = []
    for event in events:
        scheduled = _parse_utc_z(event.scheduled_at_utc)
        if scheduled is None:
            raise RuntimeError("validated event lost timestamp")
        if not (
            event.event_status_code == "SCHEDULED"
            and event.impact_code in ("MEDIUM", "HIGH")
            and search_start <= scheduled < search_end
        ):
            continue
        window_seconds = 1_800 if event.impact_code == "HIGH" else 900
        window_start = scheduled - timedelta(seconds=window_seconds)
        window_end = scheduled + timedelta(seconds=window_seconds)
        start_offset = _microseconds_between(window_start, reference)
        end_offset = _microseconds_between(window_end, reference)
        if start_offset > 0:
            relation = "UPCOMING"
        elif end_offset > 0:
            relation = "ACTIVE"
        else:
            relation = "ELAPSED"
        output.append(
            CanonicalGoldEconomicEventWindowFactsV1(
                event_id=event.event_id,
                scheduled_at_utc=event.scheduled_at_utc,
                country_code=event.country_code,
                currency_code=event.currency_code,
                event_category_code=event.event_category_code,
                impact_code=event.impact_code,
                source_revision=event.source_revision,
                window_start_utc=_format_utc_z(window_start),
                window_end_utc=_format_utc_z(window_end),
                event_offset_microseconds=_microseconds_between(scheduled, reference),
                window_start_offset_microseconds=start_offset,
                window_end_offset_microseconds=end_offset,
                window_relation_code=relation,
                is_active_observation_window=relation == "ACTIVE",
            )
        )
    return tuple(output)


def _build_summary(
    event_windows: tuple[CanonicalGoldEconomicEventWindowFactsV1, ...],
    reference: datetime,
    generated: datetime,
) -> CanonicalGoldEconomicWindowSummaryV1:
    active = tuple(
        event for event in event_windows if event.is_active_observation_window
    )
    previous = _select_nearest(event_windows, previous=True)
    following = _select_nearest(event_windows, previous=False)
    return CanonicalGoldEconomicWindowSummaryV1(
        calendar_age_microseconds=_microseconds_between(reference, generated),
        relevant_event_count=len(event_windows),
        active_window_count=len(active),
        inside_any_observation_window=bool(active),
        active_event_ids=tuple(event.event_id for event in active),
        nearest_previous_event_id=None if previous is None else previous.event_id,
        nearest_previous_event_offset_microseconds=(
            None if previous is None else previous.event_offset_microseconds
        ),
        nearest_next_event_id=None if following is None else following.event_id,
        nearest_next_event_offset_microseconds=(
            None if following is None else following.event_offset_microseconds
        ),
        highest_active_impact_code=(
            "HIGH"
            if any(event.impact_code == "HIGH" for event in active)
            else "MEDIUM" if active else "NONE"
        ),
    )


def _select_nearest(
    events: tuple[CanonicalGoldEconomicEventWindowFactsV1, ...],
    *,
    previous: bool,
) -> CanonicalGoldEconomicEventWindowFactsV1 | None:
    candidates = tuple(
        event
        for event in events
        if (
            event.event_offset_microseconds <= 0
            if previous
            else event.event_offset_microseconds > 0
        )
    )
    if not candidates:
        return None
    selected_offset = (
        max(event.event_offset_microseconds for event in candidates)
        if previous
        else min(event.event_offset_microseconds for event in candidates)
    )
    tied = tuple(
        event for event in candidates if event.event_offset_microseconds == selected_offset
    )
    return min(
        tied,
        key=lambda event: (
            0 if event.impact_code == "HIGH" else 1,
            event.event_id,
        ),
    )


def _ready_result(
    market: CanonicalGoldMarketFactsSnapshotV1,
    calendar: CanonicalGoldEconomicCalendarSnapshotV1,
    event_windows: tuple[CanonicalGoldEconomicEventWindowFactsV1, ...],
    summary: CanonicalGoldEconomicWindowSummaryV1,
) -> CanonicalGoldEconomicWindowFactsV1:
    return CanonicalGoldEconomicWindowFactsV1(
        contract_version=_CONTRACT_VERSION,
        facts_profile_version=_FACTS_PROFILE_VERSION,
        passed=True,
        status_code=_READY_STATUS,
        reason_codes=(),
        warning_codes=(),
        identity_available=True,
        source_contract_version=market.contract_version,
        bundle_schema_version=market.bundle_schema_version,
        bundle_id=market.bundle_id,
        sequence=market.sequence,
        canonical_symbol=market.canonical_symbol,
        broker_symbol=market.broker_symbol,
        reference_time_utc=market.reference_time_utc,
        calendar_contract_version=calendar.contract_version,
        calendar_schema_version=calendar.calendar_schema_version,
        calendar_snapshot_id=calendar.calendar_snapshot_id,
        calendar_source_profile_version=calendar.source_profile_version,
        calendar_generated_at_utc=calendar.generated_at_utc,
        calendar_coverage_start_utc=calendar.coverage_start_utc,
        calendar_coverage_end_utc=calendar.coverage_end_utc,
        event_windows=event_windows,
        summary=summary,
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
    market: CanonicalGoldMarketFactsSnapshotV1,
    calendar: CanonicalGoldEconomicCalendarSnapshotV1,
    event_windows: tuple[CanonicalGoldEconomicEventWindowFactsV1, ...],
    summary: CanonicalGoldEconomicWindowSummaryV1,
) -> bool:
    try:
        if not _is_exact_record(result, CanonicalGoldEconomicWindowFactsV1, _RESULT_FIELDS):
            return False
        scalar_types = (
            type(result.contract_version) is str
            and type(result.facts_profile_version) is str
            and type(result.passed) is bool
            and type(result.status_code) is str
            and _is_string_tuple(result.reason_codes)
            and _is_string_tuple(result.warning_codes)
            and type(result.identity_available) is bool
            and all(
                _is_optional_str(getattr(result, field))
                for field in _RESULT_FIELDS[7:10] + _RESULT_FIELDS[11:21]
            )
            and _is_optional_int(result.sequence)
            and type(result.event_windows) is tuple
            and type(result.summary) is CanonicalGoldEconomicWindowSummaryV1
            and all(
                type(getattr(result, field)) is bool for field in _RESULT_FIELDS[23:]
            )
        )
        if not scalar_types or not all(_has_exact_window_shape(item) for item in result.event_windows):
            return False
        if not _has_exact_summary_shape(result.summary):
            return False
        expected_identity = (
            market.contract_version,
            market.bundle_schema_version,
            market.bundle_id,
            market.sequence,
            market.canonical_symbol,
            market.broker_symbol,
            market.reference_time_utc,
            calendar.contract_version,
            calendar.calendar_schema_version,
            calendar.calendar_snapshot_id,
            calendar.source_profile_version,
            calendar.generated_at_utc,
            calendar.coverage_start_utc,
            calendar.coverage_end_utc,
        )
        actual_identity = tuple(getattr(result, field) for field in _RESULT_FIELDS[7:21])
        if not (
            result.contract_version == _CONTRACT_VERSION
            and result.facts_profile_version == _FACTS_PROFILE_VERSION
            and result.passed is True
            and result.status_code == _READY_STATUS
            and result.reason_codes == ()
            and result.warning_codes == ()
            and result.identity_available is True
            and actual_identity == expected_identity
            and result.event_windows == event_windows
            and result.summary == summary
            and _has_safety_flags(result)
        ):
            return False
        reference = _parse_utc_z(market.reference_time_utc)
        generated = _parse_utc_z(calendar.generated_at_utc)
        return (
            reference is not None
            and generated is not None
            and _windows_match_sources(calendar.events, result.event_windows, reference)
            and _has_closed_result_facts(
                result.event_windows,
                result.summary,
                _microseconds_between(reference, generated),
            )
        )
    except (AttributeError, TypeError):
        return False


def _has_exact_window_shape(value: object) -> bool:
    return _is_exact_record(value, CanonicalGoldEconomicEventWindowFactsV1, _WINDOW_FIELDS) and (
        all(type(getattr(value, field)) is str for field in _WINDOW_FIELDS[:6])
        and type(value.source_revision) is int
        and all(type(getattr(value, field)) is str for field in _WINDOW_FIELDS[7:9])
        and all(type(getattr(value, field)) is int for field in _WINDOW_FIELDS[9:12])
        and type(value.window_relation_code) is str
        and type(value.is_active_observation_window) is bool
    )


def _has_exact_summary_shape(value: object) -> bool:
    return _is_exact_record(value, CanonicalGoldEconomicWindowSummaryV1, _SUMMARY_FIELDS) and (
        type(value.calendar_age_microseconds) is int
        and type(value.relevant_event_count) is int
        and type(value.active_window_count) is int
        and type(value.inside_any_observation_window) is bool
        and _is_string_tuple(value.active_event_ids)
        and _is_optional_str(value.nearest_previous_event_id)
        and _is_optional_int(value.nearest_previous_event_offset_microseconds)
        and _is_optional_str(value.nearest_next_event_id)
        and _is_optional_int(value.nearest_next_event_offset_microseconds)
        and type(value.highest_active_impact_code) is str
    )


def _windows_match_sources(
    sources: tuple[CanonicalGoldEconomicEventSourceV1, ...],
    windows: tuple[CanonicalGoldEconomicEventWindowFactsV1, ...],
    reference: datetime,
) -> bool:
    search_start = reference - timedelta(seconds=_SEARCH_HORIZON_SECONDS)
    search_end = reference + timedelta(seconds=_SEARCH_HORIZON_SECONDS)
    relevant: list[tuple[CanonicalGoldEconomicEventSourceV1, datetime]] = []
    for source in sources:
        scheduled = _parse_utc_z(source.scheduled_at_utc)
        if scheduled is None:
            return False
        if (
            source.event_status_code == "SCHEDULED"
            and source.impact_code in ("MEDIUM", "HIGH")
            and search_start <= scheduled < search_end
        ):
            relevant.append((source, scheduled))
    if len(relevant) != len(windows):
        return False
    for window, (source, scheduled) in zip(windows, relevant, strict=True):
        window_seconds = 1_800 if source.impact_code == "HIGH" else 900
        window_start = scheduled - timedelta(seconds=window_seconds)
        window_end = scheduled + timedelta(seconds=window_seconds)
        start_offset = _microseconds_between(window_start, reference)
        end_offset = _microseconds_between(window_end, reference)
        relation = (
            "UPCOMING"
            if start_offset > 0
            else "ACTIVE" if end_offset > 0 else "ELAPSED"
        )
        if tuple(getattr(window, field) for field in _WINDOW_FIELDS) != (
            source.event_id,
            source.scheduled_at_utc,
            source.country_code,
            source.currency_code,
            source.event_category_code,
            source.impact_code,
            source.source_revision,
            _format_utc_z(window_start),
            _format_utc_z(window_end),
            _microseconds_between(scheduled, reference),
            start_offset,
            end_offset,
            relation,
            relation == "ACTIVE",
        ):
            return False
    return True


def _has_closed_result_facts(
    events: tuple[CanonicalGoldEconomicEventWindowFactsV1, ...],
    summary: CanonicalGoldEconomicWindowSummaryV1,
    expected_calendar_age: int,
) -> bool:
    for event in events:
        relation = (
            "UPCOMING"
            if event.window_start_offset_microseconds > 0
            else "ACTIVE" if event.window_end_offset_microseconds > 0 else "ELAPSED"
        )
        if (
            event.window_relation_code != relation
            or event.is_active_observation_window is not (relation == "ACTIVE")
        ):
            return False
    active = tuple(event for event in events if event.is_active_observation_window)
    previous = _select_nearest(events, previous=True)
    following = _select_nearest(events, previous=False)
    return (
        summary.calendar_age_microseconds == expected_calendar_age
        and summary.relevant_event_count == len(events)
        and summary.active_window_count == len(active)
        and summary.inside_any_observation_window is bool(active)
        and summary.active_event_ids == tuple(event.event_id for event in active)
        and summary.nearest_previous_event_id == (None if previous is None else previous.event_id)
        and summary.nearest_previous_event_offset_microseconds
        == (None if previous is None else previous.event_offset_microseconds)
        and summary.nearest_next_event_id == (None if following is None else following.event_id)
        and summary.nearest_next_event_offset_microseconds
        == (None if following is None else following.event_offset_microseconds)
        and summary.highest_active_impact_code
        == (
            "HIGH"
            if any(event.impact_code == "HIGH" for event in active)
            else "MEDIUM" if active else "NONE"
        )
    )


def _failure(status: str, reason: str) -> CanonicalGoldEconomicWindowFactsV1:
    return CanonicalGoldEconomicWindowFactsV1(
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
        calendar_contract_version=None,
        calendar_schema_version=None,
        calendar_snapshot_id=None,
        calendar_source_profile_version=None,
        calendar_generated_at_utc=None,
        calendar_coverage_start_utc=None,
        calendar_coverage_end_utc=None,
        event_windows=(),
        summary=None,
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


def _parse_fixed_price(value: str, pattern: re.Pattern[str]) -> int | None:
    if not value.isascii() or pattern.fullmatch(value) is None:
        return None
    try:
        return int(value.replace(".", ""))
    except (ValueError, OverflowError):
        return None


def _parse_positive_decimal(value: str) -> tuple[int, int] | None:
    if not value.isascii() or _POSITIVE_DECIMAL_PATTERN.fullmatch(value) is None:
        return None
    whole, separator, fraction = value.partition(".")
    try:
        coefficient = int(whole + fraction)
    except (ValueError, OverflowError):
        return None
    return (coefficient, len(fraction)) if coefficient > 0 else None


def _compare_scaled(left: tuple[int, int], right: tuple[int, int]) -> int:
    scale = max(left[1], right[1])
    left_value = left[0] * (10 ** (scale - left[1]))
    right_value = right[0] * (10 ** (scale - right[1]))
    return (left_value > right_value) - (left_value < right_value)


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


def _format_utc_z(value: datetime) -> str:
    value = value.astimezone(UTC)
    if value.microsecond == 0:
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _microseconds_between(later: datetime, earlier: datetime) -> int:
    delta = later - earlier
    return delta.days * 86_400 * 1_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def _is_identifier(value: str, minimum: int, maximum: int) -> bool:
    return (
        type(value) is str
        and value.isascii()
        and minimum <= len(value) <= maximum
        and _IDENTIFIER_PATTERN.fullmatch(value) is not None
    )


def _is_safe_label(value: str) -> bool:
    return value.isascii() and _SAFE_LABEL_PATTERN.fullmatch(value) is not None


def _has_safety_flags(result: CanonicalGoldEconomicWindowFactsV1) -> bool:
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
