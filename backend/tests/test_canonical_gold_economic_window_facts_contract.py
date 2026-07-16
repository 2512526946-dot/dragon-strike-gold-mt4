from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
import re
from types import MappingProxyType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_gold_economic_window_facts_v1_contract.md"
)

PUBLIC_SIGNATURE = """def build_canonical_gold_economic_window_facts_v1(
    *,
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,
    economic_calendar_snapshot: CanonicalGoldEconomicCalendarSnapshotV1,
) -> CanonicalGoldEconomicWindowFactsV1"""

PUBLIC_EXPORTS = (
    "CanonicalGoldEconomicCalendarSnapshotV1",
    "CanonicalGoldEconomicCalendarUpstreamEvidenceV1",
    "CanonicalGoldEconomicEventSourceV1",
    "CanonicalGoldEconomicWindowFactsV1",
    "CanonicalGoldEconomicEventWindowFactsV1",
    "CanonicalGoldEconomicWindowSummaryV1",
    "build_canonical_gold_economic_window_facts_v1",
)


@dataclass(frozen=True, slots=True)
class StatusReasonVector:
    priority: int
    status: str
    reason: str
    meaning: str


@dataclass(frozen=True, slots=True)
class TimestampVector:
    value: str
    accepted: bool


@dataclass(frozen=True, slots=True)
class BoundVector:
    name: str
    value: int
    accepted: bool
    expected_priority: int | None


@dataclass(frozen=True, slots=True)
class WindowVector:
    name: str
    impact: str
    event_offset_microseconds: int
    window_start_offset_microseconds: int
    window_end_offset_microseconds: int
    relation: str
    active: bool


@dataclass(frozen=True, slots=True)
class SummaryVector:
    name: str
    reference_time_utc: str
    calendar_generated_at_utc: str
    calendar_age_microseconds: int
    event_ids: tuple[str, ...]
    event_impacts: tuple[str, ...]
    event_offsets: tuple[int, ...]
    active_event_ids: tuple[str, ...]
    relevant_event_count: int
    active_window_count: int
    inside_any_observation_window: bool
    nearest_previous_event_id: str | None
    nearest_previous_event_offset_microseconds: int | None
    nearest_next_event_id: str | None
    nearest_next_event_offset_microseconds: int | None
    highest_active_impact_code: str


@dataclass(frozen=True, slots=True)
class ShapeMutationVector:
    schema: str
    mutation: str
    original: tuple[str, ...]
    mutated: object
    expected_priority: int


@dataclass(frozen=True, slots=True)
class ValueMutationVector:
    mutation: str
    field_path: tuple[str, ...]
    invalid_value: object
    expected_priority: int
    expected_status: str
    expected_reason: str


@dataclass(frozen=True, slots=True)
class ObjectGraphExpectationVector:
    market_input_unchanged: bool
    calendar_input_unchanged: bool
    nested_inputs_unchanged: bool
    repeated_values_equal: bool
    result_identity_distinct: bool
    event_tuple_identity_distinct: bool
    event_record_identity_distinct: bool
    summary_identity_distinct: bool
    caller_reference_isolated: bool
    exception_text_absent: bool


@dataclass(frozen=True, slots=True)
class EventSourceFixtureVector:
    event_id: str
    scheduled_at_utc: str
    country_code: str
    currency_code: str
    event_category_code: str
    impact_code: str
    source_revision: int
    event_status_code: str


@dataclass(frozen=True, slots=True)
class UpstreamEvidenceFixtureVector:
    adapter_passed: bool
    adapter_status_code: str
    schema_validated: bool
    identity_validated: bool
    timestamps_normalized: bool
    same_snapshot_bound: bool
    warning_codes: tuple[str, ...]
    raw_payload_discarded: bool


@dataclass(frozen=True, slots=True)
class CalendarSnapshotFixtureVector:
    contract_version: str
    calendar_schema_version: str
    calendar_snapshot_id: str
    source_profile_version: str
    generated_at_utc: str
    coverage_start_utc: str
    coverage_end_utc: str
    events: tuple[EventSourceFixtureVector, ...]
    upstream_evidence: UpstreamEvidenceFixtureVector
    read_only: bool
    demo_only: bool
    contains_raw_provider_payload: bool


class StrictStringSubclass(str):
    pass


CALENDAR_FIELDS = (
    ("contract_version", "str"),
    ("calendar_schema_version", "str"),
    ("calendar_snapshot_id", "str"),
    ("source_profile_version", "str"),
    ("generated_at_utc", "str"),
    ("coverage_start_utc", "str"),
    ("coverage_end_utc", "str"),
    ("events", "tuple[CanonicalGoldEconomicEventSourceV1, ...]"),
    (
        "upstream_evidence",
        "CanonicalGoldEconomicCalendarUpstreamEvidenceV1",
    ),
    ("read_only", "bool"),
    ("demo_only", "bool"),
    ("contains_raw_provider_payload", "bool"),
)

UPSTREAM_FIELDS = (
    ("adapter_passed", "bool"),
    ("adapter_status_code", "str"),
    ("schema_validated", "bool"),
    ("identity_validated", "bool"),
    ("timestamps_normalized", "bool"),
    ("same_snapshot_bound", "bool"),
    ("warning_codes", "tuple[str, ...]"),
    ("raw_payload_discarded", "bool"),
)

EVENT_SOURCE_FIELDS = (
    ("event_id", "str"),
    ("scheduled_at_utc", "str"),
    ("country_code", "str"),
    ("currency_code", "str"),
    ("event_category_code", "str"),
    ("impact_code", "str"),
    ("source_revision", "int"),
    ("event_status_code", "str"),
)

RESULT_FIELDS = (
    ("contract_version", "str"),
    ("facts_profile_version", "str"),
    ("passed", "bool"),
    ("status_code", "str"),
    ("reason_codes", "tuple[str, ...]"),
    ("warning_codes", "tuple[str, ...]"),
    ("identity_available", "bool"),
    ("source_contract_version", "str | None"),
    ("bundle_schema_version", "str | None"),
    ("bundle_id", "str | None"),
    ("sequence", "int | None"),
    ("canonical_symbol", "str | None"),
    ("broker_symbol", "str | None"),
    ("reference_time_utc", "str | None"),
    ("calendar_contract_version", "str | None"),
    ("calendar_schema_version", "str | None"),
    ("calendar_snapshot_id", "str | None"),
    ("calendar_source_profile_version", "str | None"),
    ("calendar_generated_at_utc", "str | None"),
    ("calendar_coverage_start_utc", "str | None"),
    ("calendar_coverage_end_utc", "str | None"),
    (
        "event_windows",
        "tuple[CanonicalGoldEconomicEventWindowFactsV1, ...]",
    ),
    ("summary", "CanonicalGoldEconomicWindowSummaryV1 | None"),
    ("read_only", "bool"),
    ("demo_only", "bool"),
    ("is_tradable", "bool"),
    ("can_execute", "bool"),
    ("is_trading_permission", "bool"),
    ("is_execution_instruction", "bool"),
    ("allowed_to_call_ea", "bool"),
    ("allowed_to_modify_risk", "bool"),
)

EVENT_FACT_FIELDS = (
    ("event_id", "str"),
    ("scheduled_at_utc", "str"),
    ("country_code", "str"),
    ("currency_code", "str"),
    ("event_category_code", "str"),
    ("impact_code", "str"),
    ("source_revision", "int"),
    ("window_start_utc", "str"),
    ("window_end_utc", "str"),
    ("event_offset_microseconds", "int"),
    ("window_start_offset_microseconds", "int"),
    ("window_end_offset_microseconds", "int"),
    ("window_relation_code", "str"),
    ("is_active_observation_window", "bool"),
)

SUMMARY_FIELDS = (
    ("calendar_age_microseconds", "int"),
    ("relevant_event_count", "int"),
    ("active_window_count", "int"),
    ("inside_any_observation_window", "bool"),
    ("active_event_ids", "tuple[str, ...]"),
    ("nearest_previous_event_id", "str | None"),
    ("nearest_previous_event_offset_microseconds", "int | None"),
    ("nearest_next_event_id", "str | None"),
    ("nearest_next_event_offset_microseconds", "int | None"),
    ("highest_active_impact_code", "str"),
)

PUBLIC_SCHEMAS = MappingProxyType(
    {
        "CanonicalGoldEconomicCalendarSnapshotV1": CALENDAR_FIELDS,
        "CanonicalGoldEconomicCalendarUpstreamEvidenceV1": UPSTREAM_FIELDS,
        "CanonicalGoldEconomicEventSourceV1": EVENT_SOURCE_FIELDS,
        "CanonicalGoldEconomicWindowFactsV1": RESULT_FIELDS,
        "CanonicalGoldEconomicEventWindowFactsV1": EVENT_FACT_FIELDS,
        "CanonicalGoldEconomicWindowSummaryV1": SUMMARY_FIELDS,
    }
)

G175_INPUT_FIELDS = MappingProxyType(
    {
        "CanonicalGoldMarketFactsSnapshotV1": (
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
        ),
        "CanonicalGoldQuoteFactsV1": (
            "bid_decimal",
            "ask_decimal",
            "spread_decimal",
            "spread_points",
            "digits",
            "point_decimal",
            "tick_time_utc",
        ),
        "CanonicalGoldTimeframeFactsV1": (
            "timeframe",
            "period_seconds",
            "bars",
        ),
        "CanonicalGoldBarFactsV1": (
            "open_time_utc",
            "open_decimal",
            "high_decimal",
            "low_decimal",
            "close_decimal",
            "tick_volume",
            "spread_points",
        ),
        "CanonicalGoldSymbolFactsV1": (
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
        ),
        "CanonicalGoldFreshnessFactsV1": (
            "tick_age_microseconds",
            "bars_payload_age_microseconds",
            "symbol_spec_age_microseconds",
        ),
    }
)

G175_READY_PREDICATES = (
    "contract/version/status/reason/warning exact READY envelope",
    "bundle identity regex, positive sequence, XAUUSD/GOLD, strict UTC Z",
    "quote cross-field bid/ask/spread/point/digits identities",
    "M15/H1/H4/D1 exact ordered timeframes with matching periods",
    "one through 500 strictly ordered completed bars per timeframe",
    "finite canonical fixed-point prices and strictly positive OHLC",
    "nonnegative strict tick volume and spread points with OHLC relations",
    "symbol facts positive decimals, XAU/USD currencies, strict labels",
    "freshness ages equal source timestamps and completion authority",
    "eight exact Demo-only Read-only non-execution safety flags",
)

TIMEFRAME_AUTHORITY = (
    ("M15", 900),
    ("H1", 3600),
    ("H4", 14400),
    ("D1", 86400),
)

CALENDAR_AUTHORITY = MappingProxyType(
    {
        "contract_version": "1.0",
        "facts_profile_version": "canonical_gold_economic_window_profile_v1",
        "calendar_source_profile_version": (
            "canonical_gold_economic_calendar_source_v1"
        ),
        "calendar_maximum_age_microseconds": 300000000,
        "search_horizon_seconds": 86400,
        "maximum_calendar_events": 512,
        "maximum_coverage_span_seconds": 259200,
    }
)

EVENT_CATEGORY_CODES = (
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

IMPACT_CODES = ("LOW", "MEDIUM", "HIGH")
EVENT_STATUS_CODES = ("SCHEDULED", "CANCELLED")
RELATION_CODES = ("UPCOMING", "ACTIVE", "ELAPSED")
HIGHEST_IMPACT_CODES = ("NONE", "MEDIUM", "HIGH")

TIMESTAMP_VECTORS = (
    TimestampVector("2026-07-17T12:00:00Z", True),
    TimestampVector("2026-07-17T12:00:00.1Z", True),
    TimestampVector("2026-07-17T12:00:00.123456Z", True),
    TimestampVector("2024-02-29T12:00:00Z", True),
    TimestampVector("2025-02-29T12:00:00Z", False),
    TimestampVector("2026-02-31T12:00:00Z", False),
    TimestampVector("2026-04-31T12:00:00Z", False),
    TimestampVector("0000-01-01T00:00:00Z", False),
    TimestampVector("2026-07-17T12:00:00.1234567Z", False),
    TimestampVector("2026-07-17T12:00:00+00:00", False),
    TimestampVector("2026-07-17T12:00:00z", False),
    TimestampVector(" 2026-07-17T12:00:00Z", False),
    TimestampVector("2026-07-17 12:00:00Z", False),
    TimestampVector("2026-07-17T12:00:60Z", False),
)

REFERENCE_TIME_UTC = "2026-07-17T12:00:00Z"
VALID_UPSTREAM_FIXTURE = UpstreamEvidenceFixtureVector(
    adapter_passed=True,
    adapter_status_code="CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY",
    schema_validated=True,
    identity_validated=True,
    timestamps_normalized=True,
    same_snapshot_bound=True,
    warning_codes=(),
    raw_payload_discarded=True,
)
VALID_EVENT_FIXTURE = EventSourceFixtureVector(
    event_id="event.0000",
    scheduled_at_utc=REFERENCE_TIME_UTC,
    country_code="US",
    currency_code="USD",
    event_category_code="US_CPI",
    impact_code="HIGH",
    source_revision=1,
    event_status_code="SCHEDULED",
)
VALID_CALENDAR_FIXTURE = CalendarSnapshotFixtureVector(
    contract_version="1.0",
    calendar_schema_version="1.0",
    calendar_snapshot_id="calendar.snap.0001",
    source_profile_version="canonical_gold_economic_calendar_source_v1",
    generated_at_utc="2026-07-17T11:59:59Z",
    coverage_start_utc="2026-07-16T12:00:00Z",
    coverage_end_utc="2026-07-19T12:00:00Z",
    events=(VALID_EVENT_FIXTURE,),
    upstream_evidence=VALID_UPSTREAM_FIXTURE,
    read_only=True,
    demo_only=True,
    contains_raw_provider_payload=False,
)
COVERAGE_OVERFLOW_CALENDAR_FIXTURE = replace(
    VALID_CALENDAR_FIXTURE,
    coverage_end_utc="2026-07-19T12:00:00.000001Z",
)
EVENT_COUNT_OVERFLOW_CALENDAR_FIXTURE = replace(
    VALID_CALENDAR_FIXTURE,
    events=tuple(
        replace(VALID_EVENT_FIXTURE, event_id=f"event.{index:04d}")
        for index in range(513)
    ),
)

BOUND_VECTORS = (
    BoundVector("event_count_zero", 0, True, None),
    BoundVector("event_count_maximum", 512, True, None),
    BoundVector("event_count_overflow", 513, False, 9),
    BoundVector("calendar_age_zero", 0, True, None),
    BoundVector("calendar_age_maximum", 300000000, True, None),
    BoundVector("calendar_age_stale", 300000001, False, 7),
    BoundVector("calendar_age_future", -1, False, 7),
    BoundVector("coverage_span_maximum", 259200000000, True, None),
    BoundVector("coverage_span_overflow", 259200000001, False, 8),
    BoundVector("coverage_start_exact_horizon", -86400000000, True, None),
    BoundVector("coverage_end_exact_horizon", 86400000000, False, 8),
    BoundVector("coverage_end_over_horizon", 86400000001, True, None),
)

WINDOW_VECTORS = (
    WindowVector(
        "high_before_start",
        "HIGH",
        1800000001,
        1,
        3600000001,
        "UPCOMING",
        False,
    ),
    WindowVector(
        "high_exact_start",
        "HIGH",
        1800000000,
        0,
        3600000000,
        "ACTIVE",
        True,
    ),
    WindowVector(
        "high_exact_event",
        "HIGH",
        0,
        -1800000000,
        1800000000,
        "ACTIVE",
        True,
    ),
    WindowVector(
        "high_exact_end",
        "HIGH",
        -1800000000,
        -3600000000,
        0,
        "ELAPSED",
        False,
    ),
    WindowVector(
        "medium_exact_start",
        "MEDIUM",
        900000000,
        0,
        1800000000,
        "ACTIVE",
        True,
    ),
    WindowVector(
        "medium_exact_end",
        "MEDIUM",
        -900000000,
        -1800000000,
        0,
        "ELAPSED",
        False,
    ),
)

SUMMARY_VECTORS = (
    SummaryVector(
        "empty",
        REFERENCE_TIME_UTC,
        "2026-07-17T11:55:00Z",
        300000000,
        (),
        (),
        (),
        (),
        0,
        0,
        False,
        None,
        None,
        None,
        None,
        "NONE",
    ),
    SummaryVector(
        "high_medium_and_ascii_ties",
        REFERENCE_TIME_UTC,
        "2026-07-17T11:59:59Z",
        1000000,
        (
            "event.high.a",
            "event.high.b",
            "event.med.a",
            "event.next.high.a",
            "event.next.high.b",
            "event.next.med.a",
        ),
        ("HIGH", "HIGH", "MEDIUM", "HIGH", "HIGH", "MEDIUM"),
        (0, 0, 0, 600000000, 600000000, 600000000),
        (
            "event.high.a",
            "event.high.b",
            "event.med.a",
            "event.next.high.a",
            "event.next.high.b",
            "event.next.med.a",
        ),
        6,
        6,
        True,
        "event.high.a",
        0,
        "event.next.high.a",
        600000000,
        "HIGH",
    ),
    SummaryVector(
        "elapsed_and_upcoming",
        REFERENCE_TIME_UTC,
        REFERENCE_TIME_UTC,
        0,
        ("event.prev.0001", "event.next.0001"),
        ("MEDIUM", "HIGH"),
        (-3600000000, 3600000000),
        (),
        2,
        0,
        False,
        "event.prev.0001",
        -3600000000,
        "event.next.0001",
        3600000000,
        "NONE",
    ),
)

STATUS_REASON_VECTORS = (
    StatusReasonVector(
        1,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_INPUT_INVALID",
        "GOLD_ECONOMIC_WINDOW_INPUT_TYPE_INVALID",
        "top-level or nested exact type, shape, field, or container invalid",
    ),
    StatusReasonVector(
        2,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_UPSTREAM_BLOCKED",
        "GOLD_ECONOMIC_WINDOW_MARKET_SNAPSHOT_NOT_READY",
        "G175 passed/status/code or fixed safety semantics not satisfied",
    ),
    StatusReasonVector(
        3,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_MARKET_IDENTITY_INVALID",
        "GOLD_ECONOMIC_WINDOW_MARKET_IDENTITY_INVALID",
        "bundle, symbol, or reference identity invalid",
    ),
    StatusReasonVector(
        4,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_MARKET_VALUE_INVALID",
        "GOLD_ECONOMIC_WINDOW_MARKET_FACTS_INVALID",
        "quote, timeframe, bar, symbol, freshness, or nested G175 value invariant invalid",
    ),
    StatusReasonVector(
        5,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_AUTHORITY_INVALID",
        "GOLD_ECONOMIC_WINDOW_CALENDAR_AUTHORITY_INVALID",
        "upstream evidence, Read-only/Demo-only flags, or raw-payload isolation invalid",
    ),
    StatusReasonVector(
        6,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_IDENTITY_INVALID",
        "GOLD_ECONOMIC_WINDOW_CALENDAR_IDENTITY_INVALID",
        "calendar contract/schema/source-profile version or snapshot id invalid",
    ),
    StatusReasonVector(
        7,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_FRESHNESS_INVALID",
        "GOLD_ECONOMIC_WINDOW_CALENDAR_FRESHNESS_INVALID",
        "generated time is future, stale, or malformed",
    ),
    StatusReasonVector(
        8,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_COVERAGE_INVALID",
        "GOLD_ECONOMIC_WINDOW_CALENDAR_COVERAGE_INVALID",
        "coverage interval, required horizon, or maximum coverage span invalid",
    ),
    StatusReasonVector(
        9,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_EVENT_INVALID",
        "GOLD_ECONOMIC_WINDOW_EVENT_INPUT_INVALID",
        "event count, identity, code, revision, timestamp, uniqueness, order, or coverage invalid",
    ),
    StatusReasonVector(
        10,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_RESULT_INVALID",
        "GOLD_ECONOMIC_WINDOW_RESULT_INVALID",
        "derived order, count, offset, relation, nearest selection, tie, or summary contradictory",
    ),
    StatusReasonVector(
        11,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_SAFE_FAILURE",
        "GOLD_ECONOMIC_WINDOW_EXCEPTION_SANITIZED",
        "unexpected public-boundary exception",
    ),
)

SAFETY_FLAGS = MappingProxyType(
    {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }
)

FAILURE_CLEARED_FIELDS = MappingProxyType(
    {
        "identity_available": False,
        "source_contract_version": None,
        "bundle_schema_version": None,
        "bundle_id": None,
        "sequence": None,
        "canonical_symbol": None,
        "broker_symbol": None,
        "reference_time_utc": None,
        "calendar_contract_version": None,
        "calendar_schema_version": None,
        "calendar_snapshot_id": None,
        "calendar_source_profile_version": None,
        "calendar_generated_at_utc": None,
        "calendar_coverage_start_utc": None,
        "calendar_coverage_end_utc": None,
        "event_windows": (),
        "summary": None,
        "warning_codes": (),
    }
)

SCHEMA_FIELD_NAMES = MappingProxyType(
    {
        schema: tuple(name for name, _ in fields)
        for schema, fields in PUBLIC_SCHEMAS.items()
    }
)


def _shape_vectors_for(
    schema: str,
    original: tuple[str, ...],
) -> tuple[ShapeMutationVector, ...]:
    return (
        ShapeMutationVector(schema, "missing", original, original[:-1], 1),
        ShapeMutationVector(
            schema,
            "extra",
            original,
            original + ("unexpected",),
            1,
        ),
        ShapeMutationVector(
            schema,
            "reordered",
            original,
            (original[1], original[0]) + original[2:],
            1,
        ),
        ShapeMutationVector(
            schema,
            "duplicate",
            original,
            original[:-1] + (original[-2],),
            1,
        ),
        ShapeMutationVector(
            schema,
            "alias",
            original,
            original[:1] + (f"{original[1]}_alias",) + original[2:],
            1,
        ),
        ShapeMutationVector(
            schema,
            "case_change",
            original,
            (original[0].swapcase(),) + original[1:],
            1,
        ),
        ShapeMutationVector(
            schema,
            "subclassed_key",
            original,
            (StrictStringSubclass(original[0]),) + original[1:],
            1,
        ),
        ShapeMutationVector(
            schema,
            "wrong_container",
            original,
            list(original),
            1,
        ),
        ShapeMutationVector(
            schema,
            "wrong_element",
            original,
            (object(),) + original[1:],
            1,
        ),
    )


SHAPE_MUTATION_VECTORS = tuple(
    vector
    for schema, original in SCHEMA_FIELD_NAMES.items()
    for vector in _shape_vectors_for(schema, original)
)


def _failure(priority: int) -> tuple[str, str]:
    vector = STATUS_REASON_VECTORS[priority - 1]
    return vector.status, vector.reason


VALUE_MUTATION_VECTORS = (
    ValueMutationVector(
        "top_level_subclass",
        ("market_facts_snapshot",),
        StrictStringSubclass("look-alike"),
        1,
        *_failure(1),
    ),
    ValueMutationVector(
        "market_not_ready",
        ("market_facts_snapshot", "passed"),
        False,
        2,
        *_failure(2),
    ),
    ValueMutationVector(
        "bundle_regex",
        ("market_facts_snapshot", "bundle_id"),
        "bad bundle id",
        3,
        *_failure(3),
    ),
    ValueMutationVector(
        "quote_cross_field_identity",
        ("market_facts_snapshot", "quote", "spread_points"),
        -1,
        4,
        *_failure(4),
    ),
    ValueMutationVector(
        "raw_payload_retained",
        ("economic_calendar_snapshot", "contains_raw_provider_payload"),
        True,
        5,
        *_failure(5),
    ),
    ValueMutationVector(
        "calendar_snapshot_alias",
        ("economic_calendar_snapshot", "calendar_snapshot_id"),
        "bad calendar id",
        6,
        *_failure(6),
    ),
    ValueMutationVector(
        "calendar_future",
        ("economic_calendar_snapshot", "generated_at_utc"),
        "2026-07-17T12:00:00.000001Z",
        7,
        *_failure(7),
    ),
    ValueMutationVector(
        "coverage_over_maximum",
        ("economic_calendar_snapshot",),
        COVERAGE_OVERFLOW_CALENDAR_FIXTURE,
        8,
        *_failure(8),
    ),
    ValueMutationVector(
        "event_count_513",
        ("economic_calendar_snapshot",),
        EVENT_COUNT_OVERFLOW_CALENDAR_FIXTURE,
        9,
        *_failure(9),
    ),
    ValueMutationVector(
        "relation_offset_swap",
        ("result", "event_windows", "window_relation_code"),
        "ACTIVE_WITH_POSITIVE_START",
        10,
        *_failure(10),
    ),
    ValueMutationVector(
        "unexpected_boundary_exception",
        ("public_boundary",),
        "sanitized",
        11,
        *_failure(11),
    ),
)

OBJECT_GRAPH_EXPECTATIONS = ObjectGraphExpectationVector(
    market_input_unchanged=True,
    calendar_input_unchanged=True,
    nested_inputs_unchanged=True,
    repeated_values_equal=True,
    result_identity_distinct=True,
    event_tuple_identity_distinct=True,
    event_record_identity_distinct=True,
    summary_identity_distinct=True,
    caller_reference_isolated=True,
    exception_text_absent=True,
)

STAGED_DELIVERY = (
    "immutable static contract vectors for this exact G199 contract;",
    "production source/result types and the pure-memory builder using controlled canonical calendar snapshots only;",
    "a separate server-owned calendar source-adapter contract and immutable adapter vectors;",
    "bounded adapter implementation and fixed offline calendar fixture evidence, with no provider activation;",
    "genuine offline composition through G185, G178, the approved calendar adapter/fixture, and the G199 builder;",
    "deterministic non-activating verification for that composition;",
    "any additional later W6 facts/features under separate contracts; and",
    "a separately versioned ReplayRunner W6 stage covering reviewed W6 facts before W7.",
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="ascii")


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _section(text: str, heading: str) -> str:
    start = text.index(heading) + len(heading)
    match = re.search(r"(?m)^#{2,3} ", text[start:])
    end = len(text) if match is None else start + match.start()
    return text[start:end]


def _code_block_after(text: str, marker: str, language: str) -> str:
    section = text[text.index(marker) + len(marker) :]
    match = re.search(rf"```{language}\n(.*?)\n```", section, re.DOTALL)
    assert match is not None
    return match.group(1)


def _public_exports(text: str) -> tuple[str, ...]:
    block = _code_block_after(text, "Its ordered `__all__` must be exactly:", "python")
    return tuple(re.findall(r'"([A-Za-z0-9_]+)"', block))


def _public_signature(text: str) -> str:
    block = _code_block_after(text, "The only public function is:", "python")
    return block.removesuffix(":\n    ...")


def _schema_fields(text: str, heading: str) -> tuple[tuple[str, str], ...]:
    name = heading.removeprefix("### ")
    heading_match = re.search(
        rf"(?m)^### (?:\d+\.\d+ )?{re.escape(name)}$",
        text,
    )
    assert heading_match is not None
    section = _section(text, heading_match.group(0))
    return tuple(
        (name, annotation)
        for name, annotation in re.findall(
            r"(?m)^\| \d+ \| `([^`]+)` \| `([^`]+)` \|",
            section,
        )
    )


def _status_rows(text: str) -> tuple[StatusReasonVector, ...]:
    section = _section(text, "## 14. Status, Reason, and First-Failure Mapping")
    return tuple(
        StatusReasonVector(int(priority), status, reason, meaning)
        for priority, status, reason, meaning in re.findall(
            r"(?m)^\| (\d+) \| `([^`]+)` \| `([^`]+)` \| (.+) \|$",
            section,
        )
    )


def _staged_delivery(text: str) -> tuple[str, ...]:
    section = _section(text, "## 18. Staged Delivery")
    stages: list[str] = []
    current: list[str] = []
    for line in section.splitlines():
        numbered = re.match(r"^\d+\. (.+)$", line)
        if numbered is not None:
            if current:
                stages.append(" ".join(current))
            current = [numbered.group(1)]
        elif current and line.startswith("   "):
            current.append(line.strip())
        elif current and not line.strip():
            stages.append(" ".join(current))
            current = []
    if current:
        stages.append(" ".join(current))
    return tuple(stages)


def _parse_strict_utc_z(value: str) -> datetime:
    pattern = re.compile(
        r"\d{4}-\d{2}-\d{2}T"
        r"(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d"
        r"(?:\.\d{1,6})?Z"
    )
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise ValueError
    parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    if parsed.tzinfo is not timezone.utc:
        raise ValueError
    return parsed


def _assert_strict_timestamp(vector: TimestampVector) -> None:
    try:
        _parse_strict_utc_z(vector.value)
    except ValueError:
        matched = False
    else:
        matched = True
    assert matched is vector.accepted


def _delta_microseconds(later: str, earlier: str) -> int:
    delta = _parse_strict_utc_z(later) - _parse_strict_utc_z(earlier)
    return (
        delta.days * 86400 * 1000000
        + delta.seconds * 1000000
        + delta.microseconds
    )


def _assert_event_fixture_types(event: EventSourceFixtureVector) -> None:
    assert type(event) is EventSourceFixtureVector
    assert type(event.event_id) is str
    assert type(event.scheduled_at_utc) is str
    assert type(event.country_code) is str
    assert type(event.currency_code) is str
    assert type(event.event_category_code) is str
    assert type(event.impact_code) is str
    assert type(event.source_revision) is int
    assert type(event.event_status_code) is str


def _assert_upstream_fixture_types(
    upstream: UpstreamEvidenceFixtureVector,
) -> None:
    assert type(upstream) is UpstreamEvidenceFixtureVector
    assert type(upstream.adapter_passed) is bool
    assert type(upstream.adapter_status_code) is str
    assert type(upstream.schema_validated) is bool
    assert type(upstream.identity_validated) is bool
    assert type(upstream.timestamps_normalized) is bool
    assert type(upstream.same_snapshot_bound) is bool
    assert type(upstream.warning_codes) is tuple
    assert all(type(code) is str for code in upstream.warning_codes)
    assert type(upstream.raw_payload_discarded) is bool


def _assert_calendar_fixture_types(calendar: CalendarSnapshotFixtureVector) -> None:
    assert type(calendar) is CalendarSnapshotFixtureVector
    for value in (
        calendar.contract_version,
        calendar.calendar_schema_version,
        calendar.calendar_snapshot_id,
        calendar.source_profile_version,
        calendar.generated_at_utc,
        calendar.coverage_start_utc,
        calendar.coverage_end_utc,
    ):
        assert type(value) is str
    assert type(calendar.events) is tuple
    assert type(calendar.upstream_evidence) is UpstreamEvidenceFixtureVector
    _assert_upstream_fixture_types(calendar.upstream_evidence)
    assert type(calendar.read_only) is bool
    assert type(calendar.demo_only) is bool
    assert type(calendar.contains_raw_provider_payload) is bool
    for event in calendar.events:
        _assert_event_fixture_types(event)


def _assert_window_vector(vector: WindowVector) -> None:
    duration = 1800000000 if vector.impact == "HIGH" else 900000000
    assert vector.window_start_offset_microseconds == (
        vector.event_offset_microseconds - duration
    )
    assert vector.window_end_offset_microseconds == (
        vector.event_offset_microseconds + duration
    )
    if vector.window_start_offset_microseconds > 0:
        expected_relation = "UPCOMING"
    elif vector.window_end_offset_microseconds > 0:
        expected_relation = "ACTIVE"
    else:
        expected_relation = "ELAPSED"
    assert vector.relation == expected_relation
    assert vector.active is (expected_relation == "ACTIVE")


def _assert_summary_vector(vector: SummaryVector) -> None:
    assert vector.calendar_age_microseconds == _delta_microseconds(
        vector.reference_time_utc,
        vector.calendar_generated_at_utc,
    )
    assert 0 <= vector.calendar_age_microseconds <= 300000000
    assert vector.relevant_event_count == len(vector.event_ids)
    assert len(vector.event_ids) == len(vector.event_offsets)
    assert len(vector.event_ids) == len(vector.event_impacts)
    assert all(impact in {"MEDIUM", "HIGH"} for impact in vector.event_impacts)
    assert len(vector.event_ids) == len(set(vector.event_ids))
    assert vector.active_window_count == len(vector.active_event_ids)
    assert vector.inside_any_observation_window is (
        vector.active_window_count > 0
    )
    expected_active_ids = tuple(
        event_id
        for event_id, impact, offset in zip(
            vector.event_ids,
            vector.event_impacts,
            vector.event_offsets,
            strict=True,
        )
        if offset - (1800000000 if impact == "HIGH" else 900000000) <= 0
        < offset + (1800000000 if impact == "HIGH" else 900000000)
    )
    assert vector.active_event_ids == expected_active_ids

    records = tuple(
        zip(
            vector.event_ids,
            vector.event_impacts,
            vector.event_offsets,
            strict=True,
        )
    )
    impact_priority = {"HIGH": 0, "MEDIUM": 1}

    previous = tuple(record for record in records if record[2] <= 0)
    if previous:
        selected_offset = max(record[2] for record in previous)
        candidates = tuple(
            record for record in previous if record[2] == selected_offset
        )
        selected = min(
            candidates,
            key=lambda record: (impact_priority[record[1]], record[0]),
        )
        assert vector.nearest_previous_event_id == selected[0]
        assert vector.nearest_previous_event_offset_microseconds == selected[2]
    else:
        assert vector.nearest_previous_event_id is None
        assert vector.nearest_previous_event_offset_microseconds is None

    next_events = tuple(record for record in records if record[2] > 0)
    if next_events:
        selected_offset = min(record[2] for record in next_events)
        candidates = tuple(
            record for record in next_events if record[2] == selected_offset
        )
        selected = min(
            candidates,
            key=lambda record: (impact_priority[record[1]], record[0]),
        )
        assert vector.nearest_next_event_id == selected[0]
        assert vector.nearest_next_event_offset_microseconds == selected[2]
    else:
        assert vector.nearest_next_event_id is None
        assert vector.nearest_next_event_offset_microseconds is None

    active_impacts = tuple(
        vector.event_impacts[vector.event_ids.index(event_id)]
        for event_id in vector.active_event_ids
    )
    expected_highest = (
        "HIGH"
        if "HIGH" in active_impacts
        else "MEDIUM"
        if "MEDIUM" in active_impacts
        else "NONE"
    )
    assert vector.highest_active_impact_code == expected_highest


def _assert_contract_oracle(text: str) -> None:
    assert _public_exports(text) == PUBLIC_EXPORTS
    assert _public_signature(text) == PUBLIC_SIGNATURE
    for name, fields in PUBLIC_SCHEMAS.items():
        assert _schema_fields(text, f"### {name}") == fields
    assert _status_rows(text) == STATUS_REASON_VECTORS
    assert _staged_delivery(text) == STAGED_DELIVERY

    normalized = _normalized(text)
    required_fragments = (
        "Both arguments are keyword-only.",
        "additional parameters are invalid.",
        "Only a later separately approved server-owned adapter may construct",
        "maximum_calendar_events = 512",
        "maximum_coverage_span_seconds = 259200",
        "`259200000000` microseconds is accepted",
        "A span one microsecond greater is",
        "An exact 512-item tuple is accepted; a 513-item",
        "UPCOMING iff window_start_offset_microseconds > 0",
        "is_active_observation_window iff window_relation_code == \"ACTIVE\"",
        "relevant_event_count = len(event_windows)",
        "active_window_count = len(active_event_ids)",
        "inside_any_observation_window = active_window_count > 0",
        "Each nearest offset is exactly the `event_offset_microseconds`",
        "When `event_windows == ()`, the exact summary is:",
        "Only READY may set `identity_available=True`.",
        "Static vectors are tests-only evidence.",
        "W6 remains `TESTS_ONLY`.",
    )
    for fragment in required_fragments:
        assert _normalized(fragment) in normalized


def test_vectors_are_frozen_and_public_schemas_are_exact() -> None:
    with pytest.raises(FrozenInstanceError):
        STATUS_REASON_VECTORS[0].priority = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        WINDOW_VECTORS[0].active = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        OBJECT_GRAPH_EXPECTATIONS.result_identity_distinct = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        VALID_EVENT_FIXTURE.event_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        VALID_UPSTREAM_FIXTURE.adapter_passed = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        VALID_CALENDAR_FIXTURE.events = ()  # type: ignore[misc]
    with pytest.raises(TypeError):
        PUBLIC_SCHEMAS["unexpected"] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        CALENDAR_AUTHORITY["maximum_calendar_events"] = 513  # type: ignore[index]

    assert tuple(PUBLIC_SCHEMAS) == PUBLIC_EXPORTS[:-1]
    assert tuple(len(fields) for fields in PUBLIC_SCHEMAS.values()) == (
        12,
        8,
        8,
        31,
        14,
        10,
    )
    assert all(type(fields) is tuple for fields in PUBLIC_SCHEMAS.values())
    assert all(
        type(name) is str and type(annotation) is str
        for fields in PUBLIC_SCHEMAS.values()
        for name, annotation in fields
    )


def test_contract_locks_exports_signature_and_all_public_schemas() -> None:
    text = _contract_text()

    assert _public_exports(text) == PUBLIC_EXPORTS
    assert _public_signature(text) == PUBLIC_SIGNATURE
    assert "Both arguments are keyword-only" in text
    assert "Positional arguments, omitted arguments" in text
    assert "additional parameters are invalid" in text
    for name, fields in PUBLIC_SCHEMAS.items():
        assert _schema_fields(text, f"### {name}") == fields


def test_complete_g175_ready_predicate_is_closed_without_runtime_import() -> None:
    text = _contract_text()
    section = _normalized(_section(text, "## 8. Complete Accepted G175 Predicate"))

    assert tuple(len(fields) for fields in G175_INPUT_FIELDS.values()) == (
        24,
        7,
        3,
        7,
        14,
        3,
    )
    assert len(G175_READY_PREDICATES) == 10
    assert TIMEFRAME_AUTHORITY == (
        ("M15", 900),
        ("H1", 3600),
        ("H4", 14400),
        ("D1", 86400),
    )
    for phrase in (
        "exact built-in",
        "Its 24 fields",
        "CANONICAL_GOLD_MARKET_FACTS_READY",
        "16 through 64 ASCII identifier rule",
        "positive exact built-in `int`",
        "XAUUSD",
        "GOLD",
        "M15/H1/H4/D1 order",
        "strictly increasing completed bars",
        "positive OHLC",
        "valid OHLC relations",
        "nonnegative freshness ages",
        "eight fixed safety flags",
    ):
        assert _normalized(phrase) in section

    assert any("quote cross-field" in item for item in G175_READY_PREDICATES)
    assert any("freshness ages" in item for item in G175_READY_PREDICATES)
    assert any("strictly positive OHLC" in item for item in G175_READY_PREDICATES)


def test_calendar_authority_identifiers_codes_and_source_order_are_exact() -> None:
    text = _contract_text()
    normalized = _normalized(text)

    assert CALENDAR_AUTHORITY == {
        "contract_version": "1.0",
        "facts_profile_version": "canonical_gold_economic_window_profile_v1",
        "calendar_source_profile_version": (
            "canonical_gold_economic_calendar_source_v1"
        ),
        "calendar_maximum_age_microseconds": 300000000,
        "search_horizon_seconds": 86400,
        "maximum_calendar_events": 512,
        "maximum_coverage_span_seconds": 259200,
    }
    assert re.fullmatch(r"[A-Za-z0-9._-]+", "calendar.snap_0001")
    assert 16 <= len("calendar.snap_0001") <= 64
    assert re.fullmatch(r"[A-Za-z0-9._-]+", "event.0001")
    assert 8 <= len("event.0001") <= 64
    assert len(EVENT_CATEGORY_CODES) == 13
    assert len(set(EVENT_CATEGORY_CODES)) == len(EVENT_CATEGORY_CODES)
    assert IMPACT_CODES == ("LOW", "MEDIUM", "HIGH")
    assert EVENT_STATUS_CODES == ("SCHEDULED", "CANCELLED")
    assert RELATION_CODES == ("UPCOMING", "ACTIVE", "ELAPSED")

    for code in EVENT_CATEGORY_CODES + IMPACT_CODES + EVENT_STATUS_CODES:
        assert type(code) is str
        assert code == code.upper()
    assert "(scheduled_at_utc, event_id)" in text
    assert "strict ascending" in text
    assert "must not sort" in text
    assert "country_code == \"US\"" in text
    assert "currency_code == \"USD\"" in text
    assert "source_revision` is an exact positive built-in `int`" in text


def test_utc_integer_microseconds_and_bounded_calendar_vectors_are_exact() -> None:
    for vector in TIMESTAMP_VECTORS:
        _assert_strict_timestamp(vector)
    assert next(
        vector
        for vector in TIMESTAMP_VECTORS
        if vector.value == "2024-02-29T12:00:00Z"
    ).accepted is True
    for impossible in (
        "2025-02-29T12:00:00Z",
        "2026-02-31T12:00:00Z",
        "2026-04-31T12:00:00Z",
        "0000-01-01T00:00:00Z",
    ):
        assert next(
            vector for vector in TIMESTAMP_VECTORS if vector.value == impossible
        ).accepted is False

    assert tuple(vector.name for vector in BOUND_VECTORS) == (
        "event_count_zero",
        "event_count_maximum",
        "event_count_overflow",
        "calendar_age_zero",
        "calendar_age_maximum",
        "calendar_age_stale",
        "calendar_age_future",
        "coverage_span_maximum",
        "coverage_span_overflow",
        "coverage_start_exact_horizon",
        "coverage_end_exact_horizon",
        "coverage_end_over_horizon",
    )
    assert next(v for v in BOUND_VECTORS if v.name == "event_count_overflow") == (
        BoundVector("event_count_overflow", 513, False, 9)
    )
    assert next(
        v for v in BOUND_VECTORS if v.name == "coverage_span_overflow"
    ) == BoundVector("coverage_span_overflow", 259200000001, False, 8)
    assert 259200 * 1000000 == 259200000000
    assert 259200000000 + 1 == 259200000001

    for calendar in (
        VALID_CALENDAR_FIXTURE,
        COVERAGE_OVERFLOW_CALENDAR_FIXTURE,
        EVENT_COUNT_OVERFLOW_CALENDAR_FIXTURE,
    ):
        _assert_calendar_fixture_types(calendar)
        assert calendar.contract_version == "1.0"
        assert calendar.calendar_schema_version == "1.0"
        assert calendar.source_profile_version == (
            "canonical_gold_economic_calendar_source_v1"
        )
        assert calendar.upstream_evidence == VALID_UPSTREAM_FIXTURE
        assert calendar.read_only is True
        assert calendar.demo_only is True
        assert calendar.contains_raw_provider_payload is False
        assert _delta_microseconds(
            REFERENCE_TIME_UTC,
            calendar.generated_at_utc,
        ) == 1000000

    assert _delta_microseconds(
        VALID_CALENDAR_FIXTURE.coverage_end_utc,
        VALID_CALENDAR_FIXTURE.coverage_start_utc,
    ) == 259200000000
    assert _delta_microseconds(
        COVERAGE_OVERFLOW_CALENDAR_FIXTURE.coverage_end_utc,
        COVERAGE_OVERFLOW_CALENDAR_FIXTURE.coverage_start_utc,
    ) == 259200000001
    assert COVERAGE_OVERFLOW_CALENDAR_FIXTURE.events == (
        VALID_EVENT_FIXTURE,
    )

    overflow_events = EVENT_COUNT_OVERFLOW_CALENDAR_FIXTURE.events
    assert len(overflow_events) == 513
    assert len({event.event_id for event in overflow_events}) == 513
    assert tuple(event.event_id for event in overflow_events) == tuple(
        sorted(event.event_id for event in overflow_events)
    )
    for event in overflow_events:
        assert re.fullmatch(r"[A-Za-z0-9._-]{8,64}", event.event_id)
        assert event.scheduled_at_utc == REFERENCE_TIME_UTC
        assert event.country_code == "US"
        assert event.currency_code == "USD"
        assert event.event_category_code in EVENT_CATEGORY_CODES
        assert event.impact_code in IMPACT_CODES
        assert event.source_revision > 0
        assert event.event_status_code in EVENT_STATUS_CODES

    text = _contract_text()
    normalized = _normalized(text)
    for phrase in (
        "delta.days * 86400 * 1000000",
        "delta.seconds * 1000000",
        "Do not use `total_seconds()`",
        "reference_time_utc` from the G175 snapshot is the only clock",
        "coverage_start_utc <= reference_time_utc - 86400 seconds",
        "coverage_end_utc > reference_time_utc + 86400 seconds",
        "exact 512-item tuple is accepted; a 513-item",
        "No duration is rounded",
    ):
        assert _normalized(phrase) in normalized


def test_relevance_half_open_windows_and_endpoint_vectors_are_closed() -> None:
    for vector in WINDOW_VECTORS:
        _assert_window_vector(vector)

    assert len({vector.name for vector in WINDOW_VECTORS}) == len(WINDOW_VECTORS)
    assert {vector.relation for vector in WINDOW_VECTORS} == set(RELATION_CODES)
    assert {vector.impact for vector in WINDOW_VECTORS} == {"MEDIUM", "HIGH"}

    text = _contract_text()
    normalized = _normalized(text)
    for phrase in (
        "HIGH` events use `pre_window_seconds=1800`",
        "MEDIUM` events use `pre_window_seconds=900`",
        "LOW` and `CANCELLED` events remain valid calendar source facts but are not",
        "[reference_time_utc - 86400 seconds,",
        "window_start <= reference_time_utc < window_end",
        "exact window start is `ACTIVE`",
        "exact scheduled time is `ACTIVE`",
        "exact window end is `ELAPSED`",
        "Filtering preserves the canonical source order",
    ):
        assert _normalized(phrase) in normalized


def test_summary_nearest_tie_and_empty_result_vectors_are_closed() -> None:
    for vector in SUMMARY_VECTORS:
        _assert_summary_vector(vector)

    empty = SUMMARY_VECTORS[0]
    assert empty == SummaryVector(
        "empty",
        REFERENCE_TIME_UTC,
        "2026-07-17T11:55:00Z",
        300000000,
        (),
        (),
        (),
        (),
        0,
        0,
        False,
        None,
        None,
        None,
        None,
        "NONE",
    )
    ties = SUMMARY_VECTORS[1]
    assert ties.event_offsets.count(0) == 3
    assert ties.event_offsets.count(600000000) == 3
    assert ties.nearest_previous_event_id == "event.high.a"
    assert ties.nearest_next_event_id == "event.next.high.a"
    assert ties.active_event_ids == (
        "event.high.a",
        "event.high.b",
        "event.med.a",
        "event.next.high.a",
        "event.next.high.b",
        "event.next.med.a",
    )
    assert ties.highest_active_impact_code == "HIGH"

    text = _contract_text()
    normalized = _normalized(text)
    for phrase in (
        "HIGH before MEDIUM, then event_id in ascending ASCII order",
        "An event exactly at reference time is previous, not next.",
        "Each nearest offset is exactly the `event_offset_microseconds`",
        "relevant_event_count = len(event_windows)",
        "active_event_ids = tuple(",
        "active_window_count = len(active_event_ids)",
        "inside_any_observation_window = active_window_count > 0",
        "highest_active_impact_code = \"NONE\"",
    ):
        assert _normalized(phrase) in normalized


def test_status_reason_priority_failure_clearing_and_safety_are_exact() -> None:
    assert _status_rows(_contract_text()) == STATUS_REASON_VECTORS
    assert tuple(vector.priority for vector in STATUS_REASON_VECTORS) == tuple(
        range(1, 12)
    )
    assert len({vector.status for vector in STATUS_REASON_VECTORS}) == 11
    assert len({vector.reason for vector in STATUS_REASON_VECTORS}) == 11
    assert STATUS_REASON_VECTORS[-1] == StatusReasonVector(
        11,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_SAFE_FAILURE",
        "GOLD_ECONOMIC_WINDOW_EXCEPTION_SANITIZED",
        "unexpected public-boundary exception",
    )
    assert SAFETY_FLAGS == {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }
    assert tuple(FAILURE_CLEARED_FIELDS) == (
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
        "warning_codes",
    )
    assert FAILURE_CLEARED_FIELDS["event_windows"] == ()
    assert FAILURE_CLEARED_FIELDS["summary"] is None
    assert FAILURE_CLEARED_FIELDS["warning_codes"] == ()


def test_negative_shape_and_value_vectors_cover_all_failure_categories() -> None:
    expected_mutations = (
        "missing",
        "extra",
        "reordered",
        "duplicate",
        "alias",
        "case_change",
        "subclassed_key",
        "wrong_container",
        "wrong_element",
    )
    assert len(SHAPE_MUTATION_VECTORS) == len(PUBLIC_SCHEMAS) * len(
        expected_mutations
    )
    assert {vector.schema for vector in SHAPE_MUTATION_VECTORS} == set(
        PUBLIC_SCHEMAS
    )
    for schema, original in SCHEMA_FIELD_NAMES.items():
        schema_vectors = tuple(
            vector for vector in SHAPE_MUTATION_VECTORS if vector.schema == schema
        )
        assert tuple(vector.mutation for vector in schema_vectors) == (
            expected_mutations
        )
        assert all(vector.original == original for vector in schema_vectors)
        assert all(vector.expected_priority == 1 for vector in schema_vectors)
        for vector in schema_vectors:
            if vector.mutation == "subclassed_key":
                assert vector.mutated == vector.original
                assert type(vector.mutated[0]) is StrictStringSubclass
            else:
                assert vector.mutated != vector.original
        assert type(schema_vectors[6].mutated[0]) is StrictStringSubclass
        assert type(schema_vectors[7].mutated) is list
        assert type(schema_vectors[8].mutated[0]) is object

    assert tuple(vector.expected_priority for vector in VALUE_MUTATION_VECTORS) == (
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
    )
    for vector in VALUE_MUTATION_VECTORS:
        expected = STATUS_REASON_VECTORS[vector.expected_priority - 1]
        assert vector.expected_status == expected.status
        assert vector.expected_reason == expected.reason
        assert type(vector.field_path) is tuple
        assert all(type(part) is str for part in vector.field_path)

    coverage_vector = next(
        vector
        for vector in VALUE_MUTATION_VECTORS
        if vector.mutation == "coverage_over_maximum"
    )
    event_count_vector = next(
        vector
        for vector in VALUE_MUTATION_VECTORS
        if vector.mutation == "event_count_513"
    )
    assert type(coverage_vector.invalid_value) is CalendarSnapshotFixtureVector
    assert type(event_count_vector.invalid_value) is CalendarSnapshotFixtureVector
    assert all(
        type(event) is EventSourceFixtureVector
        for event in event_count_vector.invalid_value.events
    )

    swapped = tuple(
        replace(
            vector,
            expected_reason=STATUS_REASON_VECTORS[
                vector.expected_priority % len(STATUS_REASON_VECTORS)
            ].reason,
        )
        for vector in VALUE_MUTATION_VECTORS
    )
    assert all(
        vector.expected_reason
        != STATUS_REASON_VECTORS[vector.expected_priority - 1].reason
        for vector in swapped
    )


def test_object_graph_determinism_and_sanitization_expectations_are_closed() -> None:
    for field_name in OBJECT_GRAPH_EXPECTATIONS.__slots__:
        assert getattr(OBJECT_GRAPH_EXPECTATIONS, field_name) is True
        mutated = replace(OBJECT_GRAPH_EXPECTATIONS, **{field_name: False})
        assert mutated != OBJECT_GRAPH_EXPECTATIONS

    first = replace(OBJECT_GRAPH_EXPECTATIONS)
    second = replace(OBJECT_GRAPH_EXPECTATIONS)
    assert first == second == OBJECT_GRAPH_EXPECTATIONS
    assert first is not second

    text = _contract_text()
    normalized = _normalized(text)
    for phrase in (
        "must not modify either input or any nested record",
        "Every call returns a fresh result and fresh nested facts.",
        "Equal exact inputs return value-equal results",
        "distinct result and nested object identities",
        "result must be detached from both inputs",
        "Exception text and traceback data must not be returned or logged",
    ):
        assert _normalized(phrase) in normalized


def test_contract_mutation_probes_reject_authority_mapping_and_stage_drift() -> None:
    text = _contract_text()
    _assert_contract_oracle(text)

    mutations = (
        text.replace(
            '    "build_canonical_gold_economic_window_facts_v1",\n)',
            '    "unexpected_export",\n'
            '    "build_canonical_gold_economic_window_facts_v1",\n)',
            1,
        ),
        text.replace(
            "    economic_calendar_snapshot: CanonicalGoldEconomicCalendarSnapshotV1,\n",
            "    economic_calendar_snapshot: CanonicalGoldEconomicCalendarSnapshotV1,\n"
            "    policy_override: object,\n",
            1,
        ),
        text.replace(
            "| 1 | `contract_version` | `str` | exactly `\"1.0\"` |\n"
            "| 2 | `calendar_schema_version` | `str` | exactly `\"1.0\"` |",
            "| 1 | `calendar_schema_version` | `str` | exactly `\"1.0\"` |\n"
            "| 2 | `contract_version` | `str` | exactly `\"1.0\"` |",
            1,
        ),
        text.replace("maximum_calendar_events = 512", "maximum_calendar_events = 513", 1),
        text.replace(
            "maximum_coverage_span_seconds = 259200",
            "maximum_coverage_span_seconds = 259201",
            1,
        ),
        text.replace(
            "is_active_observation_window iff window_relation_code == \"ACTIVE\"",
            "is_active_observation_window may differ from window_relation_code",
            1,
        ),
        text.replace(
            "`GOLD_ECONOMIC_WINDOW_EVENT_INPUT_INVALID`",
            "`GOLD_ECONOMIC_WINDOW_RESULT_INVALID`",
            1,
        ),
        text.replace(
            "1. immutable static contract vectors for this exact G199 contract;",
            "1. runtime implementation before contract vectors;",
            1,
        ),
    )
    assert len(set(mutations)) == len(mutations)
    for mutated in mutations:
        with pytest.raises(AssertionError):
            _assert_contract_oracle(mutated)


def test_staged_delivery_and_isolation_remain_closed() -> None:
    text = _contract_text()

    assert _staged_delivery(text) == STAGED_DELIVERY
    assert len(STAGED_DELIVERY) == 8
    assert STAGED_DELIVERY[0].startswith("immutable static contract vectors")
    assert "production source/result types" in STAGED_DELIVERY[1]
    assert "server-owned calendar source-adapter contract" in STAGED_DELIVERY[2]
    assert "no provider activation" in STAGED_DELIVERY[3]
    assert "genuine offline composition" in STAGED_DELIVERY[4]
    assert "deterministic non-activating verification" in STAGED_DELIVERY[5]
    assert "later W6 facts/features" in STAGED_DELIVERY[6]
    assert "ReplayRunner W6 stage" in STAGED_DELIVERY[7]

    for forbidden in (
        "provider SDK",
        "HTTP client",
        "socket",
        "filesystem reader",
        "environment",
        "ambient clock",
        "MT4",
        "EA",
    ):
        assert forbidden in text
    assert "W6 remains `TESTS_ONLY`" in text
    assert "W7-W21 remain unchanged and unauthorized" in text
    assert "not a Gate result or trading permission" in text
    assert "Reader activation, real MT4, calendar-provider activation" in text


def test_contract_vector_module_has_no_runtime_import_or_builder() -> None:
    source = Path(__file__).read_text(encoding="ascii")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert not any(module.startswith("app") for module in imported_modules)
    assert "canonical_gold_economic_window_facts" not in imported_modules
    assert "build_canonical_gold_economic_window_facts_v1" not in function_names
    assert "CanonicalGoldEconomicWindowFactsV1" not in {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    assert source.isascii()
