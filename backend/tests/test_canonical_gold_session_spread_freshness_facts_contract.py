from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import re
from types import MappingProxyType

import pytest


CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "implementation_plans"
    / "canonical_gold_session_spread_freshness_facts_v1_contract.md"
)

PUBLIC_SIGNATURE = """build_canonical_gold_session_spread_freshness_facts_v1(
    *,
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,
) -> CanonicalGoldSessionSpreadFreshnessFactsV1"""


@dataclass(frozen=True, slots=True)
class RecordVector:
    record_type: str
    fields: tuple[tuple[str, object], ...]


@dataclass(frozen=True, slots=True)
class StatusReasonVector:
    passed: bool
    status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SessionBoundaryVector:
    utc_second_of_day: int
    bucket: str
    start: int
    end: int
    since_start: int
    until_end: int


@dataclass(frozen=True, slots=True)
class HalfEvenVector:
    numerator: int
    denominator: int
    quotient: int
    remainder: int
    rounded: int


@dataclass(frozen=True, slots=True)
class FreshnessVector:
    tick_age: int
    bars_payload_age: int
    symbol_spec_age: int
    maximum_age: int
    oldest_component: str


@dataclass(frozen=True, slots=True)
class ShapeMutationVector:
    mutation: str
    original_fields: tuple[str, ...]
    mutated_fields: tuple[str, ...]
    expected_status: str
    expected_reason: str


@dataclass(frozen=True, slots=True)
class StrictValueMutationVector:
    mutation: str
    field_path: tuple[str, ...]
    invalid_value: object
    invalid_type: type[object]
    expected_status: str
    expected_reason: str
    priority: int


RESULT_FIELDS = (
    ("contract_version", "str"),
    ("facts_profile_version", "str"),
    ("passed", "bool"),
    ("status_code", "str"),
    ("reason_codes", "tuple[str, ...]"),
    ("warning_codes", "tuple[str, ...]"),
    ("identity_available", "bool"),
    ("bundle_schema_version", "str | None"),
    ("bundle_id", "str | None"),
    ("sequence", "int | None"),
    ("canonical_symbol", "str | None"),
    ("broker_symbol", "str | None"),
    ("reference_time_utc", "str | None"),
    ("session", "CanonicalGoldSessionFactsV1 | None"),
    ("spread", "CanonicalGoldSpreadFactsV1 | None"),
    ("freshness", "CanonicalGoldSourceFreshnessFactsV1 | None"),
    ("read_only", "bool"),
    ("demo_only", "bool"),
    ("is_tradable", "bool"),
    ("can_execute", "bool"),
    ("is_trading_permission", "bool"),
    ("is_execution_instruction", "bool"),
    ("allowed_to_call_ea", "bool"),
    ("allowed_to_modify_risk", "bool"),
)

SESSION_FIELDS = (
    ("utc_weekday_code", "str"),
    ("utc_second_of_day", "int"),
    ("session_bucket_code", "str"),
    ("window_start_second_utc", "int"),
    ("window_end_second_utc", "int"),
    ("seconds_since_window_start", "int"),
    ("seconds_until_window_end", "int"),
    ("observed_writer_session_status_label", "str"),
)

SPREAD_FIELDS = (
    ("bid_decimal", "str"),
    ("ask_decimal", "str"),
    ("mid_decimal", "str"),
    ("spread_decimal", "str"),
    ("spread_points", "int"),
    ("digits", "int"),
    ("point_decimal", "str"),
    ("spread_to_mid_ppm_decimal", "str"),
)

FRESHNESS_FIELDS = (
    ("tick_age_microseconds", "int"),
    ("bars_payload_age_microseconds", "int"),
    ("symbol_spec_age_microseconds", "int"),
    ("maximum_source_age_microseconds", "int"),
    ("oldest_source_component_code", "str"),
)

PUBLIC_SCHEMAS = MappingProxyType(
    {
        "CanonicalGoldSessionSpreadFreshnessFactsV1": RESULT_FIELDS,
        "CanonicalGoldSessionFactsV1": SESSION_FIELDS,
        "CanonicalGoldSpreadFactsV1": SPREAD_FIELDS,
        "CanonicalGoldSourceFreshnessFactsV1": FRESHNESS_FIELDS,
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
        "CanonicalGoldTimeframeFactsV1": ("timeframe", "period_seconds", "bars"),
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

WEEKDAY_CODES = (
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
)

SESSION_WINDOWS = (
    ("ASIA_UTC", 0, 28800),
    ("LONDON_UTC", 28800, 46800),
    ("LONDON_NEW_YORK_OVERLAP_UTC", 46800, 57600),
    ("NEW_YORK_UTC", 57600, 79200),
    ("OFF_HOURS_UTC", 79200, 86400),
)

SESSION_BOUNDARY_VECTORS = (
    SessionBoundaryVector(0, "ASIA_UTC", 0, 28800, 0, 28800),
    SessionBoundaryVector(28799, "ASIA_UTC", 0, 28800, 28799, 1),
    SessionBoundaryVector(28800, "LONDON_UTC", 28800, 46800, 0, 18000),
    SessionBoundaryVector(46799, "LONDON_UTC", 28800, 46800, 17999, 1),
    SessionBoundaryVector(
        46800,
        "LONDON_NEW_YORK_OVERLAP_UTC",
        46800,
        57600,
        0,
        10800,
    ),
    SessionBoundaryVector(
        57599,
        "LONDON_NEW_YORK_OVERLAP_UTC",
        46800,
        57600,
        10799,
        1,
    ),
    SessionBoundaryVector(57600, "NEW_YORK_UTC", 57600, 79200, 0, 21600),
    SessionBoundaryVector(79199, "NEW_YORK_UTC", 57600, 79200, 21599, 1),
    SessionBoundaryVector(79200, "OFF_HOURS_UTC", 79200, 86400, 0, 7200),
    SessionBoundaryVector(86399, "OFF_HOURS_UTC", 79200, 86400, 7199, 1),
)

HALF_EVEN_VECTORS = (
    HalfEvenVector(5, 2, 2, 1, 2),
    HalfEvenVector(7, 2, 3, 1, 4),
    HalfEvenVector(4, 3, 1, 1, 1),
    HalfEvenVector(5, 3, 1, 2, 2),
)

FRESHNESS_VECTORS = (
    FreshnessVector(10, 2, 3, 10, "TICK"),
    FreshnessVector(10, 10, 2, 10, "TICK"),
    FreshnessVector(2, 10, 10, 10, "BARS_PAYLOAD"),
    FreshnessVector(2, 3, 10, 10, "SYMBOL_SPEC"),
)

STATUS_REASON_VECTORS = (
    StatusReasonVector(True, "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_READY", ()),
    StatusReasonVector(
        False,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        ("GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",),
    ),
    StatusReasonVector(
        False,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_UPSTREAM_BLOCKED",
        ("GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_NOT_READY",),
    ),
    StatusReasonVector(
        False,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_IDENTITY_INVALID",
        ("GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_IDENTITY_INVALID",),
    ),
    StatusReasonVector(
        False,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID",
        ("GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID",),
    ),
    StatusReasonVector(
        False,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID",
        ("GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID",),
    ),
    StatusReasonVector(
        False,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",
        ("GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",),
    ),
    StatusReasonVector(
        False,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SAFE_FAILURE",
        ("GOLD_SESSION_SPREAD_FRESHNESS_EXCEPTION_SANITIZED",),
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
        "bundle_schema_version": None,
        "bundle_id": None,
        "sequence": None,
        "canonical_symbol": None,
        "broker_symbol": None,
        "reference_time_utc": None,
        "session": None,
        "spread": None,
        "freshness": None,
    }
)


def _bar(timeframe: str) -> RecordVector:
    return RecordVector(
        "CanonicalGoldBarFactsV1",
        (
            ("open_time_utc", {
                "M15": "2026-01-02T11:30:00Z",
                "H1": "2026-01-02T10:00:00Z",
                "H4": "2026-01-02T04:00:00Z",
                "D1": "2026-01-01T00:00:00Z",
            }[timeframe]),
            ("open_decimal", "2500.00000000"),
            ("high_decimal", "2501.00000000"),
            ("low_decimal", "2499.00000000"),
            ("close_decimal", "2500.50000000"),
            ("tick_volume", 1),
            ("spread_points", 0),
        ),
    )


TIMEFRAME_VECTORS = tuple(
    RecordVector(
        "CanonicalGoldTimeframeFactsV1",
        (("timeframe", timeframe), ("period_seconds", period), ("bars", (_bar(timeframe),))),
    )
    for timeframe, period in (("M15", 900), ("H1", 3600), ("H4", 14400), ("D1", 86400))
)

LARGE_64_COEFFICIENT = "9" * 64
READY_72_DIGIT_FIXED_POINT = f"{LARGE_64_COEFFICIENT}.00000000"

READY_INPUT_VECTOR = RecordVector(
    "CanonicalGoldMarketFactsSnapshotV1",
    (
        ("contract_version", "1.0"),
        ("passed", True),
        ("status_code", "CANONICAL_GOLD_MARKET_FACTS_READY"),
        ("reason_codes", ()),
        ("warning_codes", ()),
        ("identity_available", True),
        ("bundle_schema_version", "1.0"),
        ("bundle_id", "g189-static-ready"),
        ("sequence", 1),
        ("canonical_symbol", "XAUUSD"),
        ("broker_symbol", "GOLD"),
        ("reference_time_utc", "2026-01-02T12:00:00Z"),
        (
            "quote",
            RecordVector(
                "CanonicalGoldQuoteFactsV1",
                (
                    ("bid_decimal", READY_72_DIGIT_FIXED_POINT),
                    ("ask_decimal", READY_72_DIGIT_FIXED_POINT),
                    ("spread_decimal", "0.00000000"),
                    ("spread_points", 0),
                    ("digits", 8),
                    ("point_decimal", "0.00000001"),
                    ("tick_time_utc", "2026-01-02T11:59:59Z"),
                ),
            ),
        ),
        ("timeframes", TIMEFRAME_VECTORS),
        (
            "symbol_spec",
            RecordVector(
                "CanonicalGoldSymbolFactsV1",
                (
                    ("spec_time_utc", "2026-01-02T11:59:58Z"),
                    ("digits", 8),
                    ("point_decimal", "0.00000001"),
                    ("tick_size_decimal", "0.00000001"),
                    ("tick_value_decimal", "1"),
                    ("contract_size_decimal", "100"),
                    ("min_lot_decimal", "0.01"),
                    ("lot_step_decimal", "0.01"),
                    ("max_lot_decimal", "100"),
                    ("base_currency", "XAU"),
                    ("profit_currency", "USD"),
                    ("margin_currency", "USD"),
                    ("trade_mode_readonly_label", "ENABLED"),
                    ("session_status_readonly_label", "WRITER_OBSERVATION"),
                ),
            ),
        ),
        (
            "freshness",
            RecordVector(
                "CanonicalGoldFreshnessFactsV1",
                (
                    ("tick_age_microseconds", 1_000_000),
                    ("bars_payload_age_microseconds", 1_000_000),
                    ("symbol_spec_age_microseconds", 2_000_000),
                ),
            ),
        ),
        ("read_only", True),
        ("demo_only", True),
        ("is_tradable", False),
        ("can_execute", False),
        ("is_trading_permission", False),
        ("is_execution_instruction", False),
        ("allowed_to_call_ea", False),
        ("allowed_to_modify_risk", False),
    ),
)

_RESULT_NAMES = tuple(name for name, _ in RESULT_FIELDS)

SHAPE_MUTATION_VECTORS = (
    ShapeMutationVector(
        "missing",
        _RESULT_NAMES,
        _RESULT_NAMES[:-1],
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
    ),
    ShapeMutationVector(
        "extra",
        _RESULT_NAMES,
        _RESULT_NAMES + ("caller_oracle",),
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
    ),
    ShapeMutationVector(
        "reordered",
        _RESULT_NAMES,
        (_RESULT_NAMES[1], _RESULT_NAMES[0], *_RESULT_NAMES[2:]),
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
    ),
    ShapeMutationVector(
        "duplicate",
        _RESULT_NAMES,
        (*_RESULT_NAMES[:-1], _RESULT_NAMES[-2]),
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
    ),
    ShapeMutationVector(
        "alias",
        _RESULT_NAMES,
        (*_RESULT_NAMES[:8], "bundle_identity", *_RESULT_NAMES[9:]),
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
    ),
    ShapeMutationVector(
        "case_change",
        _RESULT_NAMES,
        ("Contract_version", *_RESULT_NAMES[1:]),
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
    ),
)


class StrictStringSubclass(str):
    pass


STRICT_VALUE_MUTATION_VECTORS = (
    StrictValueMutationVector(
        "subclass",
        ("status_code",),
        StrictStringSubclass("CANONICAL_GOLD_MARKET_FACTS_READY"),
        StrictStringSubclass,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
        1,
    ),
    StrictValueMutationVector(
        "wrong_container",
        ("reason_codes",),
        frozenset(),
        frozenset,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
        1,
    ),
    StrictValueMutationVector(
        "wrong_element",
        ("reason_codes", "0"),
        1,
        int,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
        1,
    ),
    StrictValueMutationVector(
        "wrong_ready_status",
        ("status_code",),
        "CANONICAL_GOLD_MARKET_FACTS_BLOCKED",
        str,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_UPSTREAM_BLOCKED",
        "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_NOT_READY",
        2,
    ),
    StrictValueMutationVector(
        "bar_order",
        ("timeframes", "M15", "bars", "open_time_utc"),
        ("2026-01-02T11:30:00Z", "2026-01-02T11:15:00Z"),
        tuple,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_UPSTREAM_BLOCKED",
        "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_NOT_READY",
        2,
    ),
    StrictValueMutationVector(
        "identity",
        ("bundle_id",),
        "bad bundle id",
        str,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_IDENTITY_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_IDENTITY_INVALID",
        3,
    ),
    StrictValueMutationVector(
        "timestamp",
        ("reference_time_utc",),
        "2026-01-02T12:00:00+00:00",
        str,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID",
        4,
    ),
    StrictValueMutationVector(
        "writer_label",
        ("symbol_spec", "session_status_readonly_label"),
        "",
        str,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID",
        4,
    ),
    StrictValueMutationVector(
        "decimal_exponent",
        ("quote", "bid_decimal"),
        "2.5E+3",
        str,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID",
        5,
    ),
    StrictValueMutationVector(
        "spread_identity",
        ("quote", "spread_decimal"),
        "1.00000000",
        str,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID",
        5,
    ),
    StrictValueMutationVector(
        "negative_freshness",
        ("freshness", "tick_age_microseconds"),
        -1,
        int,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",
        6,
    ),
    StrictValueMutationVector(
        "incomplete_bar",
        ("timeframes", "D1", "bars", "open_time_utc"),
        "2026-01-02T00:00:00Z",
        str,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",
        6,
    ),
    StrictValueMutationVector(
        "unexpected_exception",
        ("public_boundary",),
        "sanitized",
        str,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SAFE_FAILURE",
        "GOLD_SESSION_SPREAD_FRESHNESS_EXCEPTION_SANITIZED",
        7,
    ),
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="ascii")


def _section(text: str, start: str, end: str | None = None) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index) if end is not None else len(text)
    return text[start_index:end_index]


def _schema_rows(text: str, heading: str, next_heading: str) -> tuple[tuple[str, str], ...]:
    body = _section(text, heading, next_heading)
    matches = re.findall(
        r"(?m)^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|$",
        body,
    )
    return tuple(matches)


def _status_rows(text: str) -> tuple[StatusReasonVector, ...]:
    body = _section(text, "## 8. Result and Failure Mapping", "## 9. Identity")
    rows: list[StatusReasonVector] = []
    for passed, status, reasons in re.findall(
        r"(?m)^\| `(true|false)` \| `([^`]+)` \| `([^`]*)` \|$",
        body,
    ):
        parsed_reasons = () if reasons == "()" else (reasons.split('"')[1],)
        rows.append(StatusReasonVector(passed == "true", status, parsed_reasons))
    return tuple(rows)


def _g175_schema_fields(text: str) -> dict[str, tuple[str, ...]]:
    body = _section(
        text,
        "CanonicalGoldMarketFactsSnapshotV1 =",
        "```\n\nEvery record must have the exact named G175 type",
    )
    parsed: dict[str, tuple[str, ...]] = {}
    for record_name in G175_INPUT_FIELDS:
        match = re.search(
            rf"{record_name}\s*=\s*\((.*?)\)\s*(?=\nCanonicalGold|\Z)",
            body,
            re.DOTALL,
        )
        assert match is not None
        parsed[record_name] = tuple(
            field.strip() for field in match.group(1).replace("\n", " ").split(",") if field.strip()
        )
    return parsed


def _session_rows(text: str) -> tuple[tuple[str, int, int], ...]:
    body = _section(text, "### 5.2 Exact half-open windows", "## 6. Decimal")
    return tuple(
        (name, int(start), int(end))
        for name, start, end in re.findall(
            r"(?m)^\| `([^`]+)` \| (\d+) \| (\d+) \|$",
            body,
        )
    )


def _assert_closed_contract(text: str) -> None:
    assert PUBLIC_SIGNATURE in text
    assert _schema_rows(text, "### 4.1 ", "### 4.2 ") == RESULT_FIELDS
    assert _schema_rows(text, "### 4.2 ", "### 4.3 ") == SESSION_FIELDS
    assert _schema_rows(text, "### 4.3 ", "### 4.4 ") == SPREAD_FIELDS
    assert _schema_rows(text, "### 4.4 ", "## 5. ") == FRESHNESS_FIELDS
    assert _g175_schema_fields(text) == dict(G175_INPUT_FIELDS)
    assert _status_rows(text) == STATUS_REASON_VECTORS
    assert _session_rows(text) == SESSION_WINDOWS
    assert "M = 5 * (B + A)" in text
    assert "N = 2 * S * (10 ** 12)" in text
    assert "q, r = divmod(N, D)" in text
    assert "if 2 * r == D: rounded = q when q is even, otherwise q + 1" in text
    assert "must not impose an independent digit-count limit on a formatted\nG175 Decimal coefficient" in text
    assert "This remains exact when `B + A` has 65 digits and never rounds." in text
    assert "Ties use the fixed priority `TICK`, `BARS_PAYLOAD`, then\n`SYMBOL_SPEC`" in text
    staged = _section(
        text,
        "Later work must remain separately planned and approved:",
        "No stage silently includes the next.",
    )
    assert re.findall(r"(?m)^(\d+)\.", staged) == [str(index) for index in range(1, 8)]


def test_contract_vectors_are_frozen_and_use_exact_public_schemas() -> None:
    with pytest.raises(FrozenInstanceError):
        STATUS_REASON_VECTORS[0].passed = False  # type: ignore[misc]
    with pytest.raises(TypeError):
        PUBLIC_SCHEMAS["unexpected"] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        SAFETY_FLAGS["is_tradable"] = True  # type: ignore[index]

    assert type(RESULT_FIELDS) is tuple and len(RESULT_FIELDS) == 24
    assert type(SESSION_FIELDS) is tuple and len(SESSION_FIELDS) == 8
    assert type(SPREAD_FIELDS) is tuple and len(SPREAD_FIELDS) == 8
    assert type(FRESHNESS_FIELDS) is tuple and len(FRESHNESS_FIELDS) == 5
    assert tuple(PUBLIC_SCHEMAS) == (
        "CanonicalGoldSessionSpreadFreshnessFactsV1",
        "CanonicalGoldSessionFactsV1",
        "CanonicalGoldSpreadFactsV1",
        "CanonicalGoldSourceFreshnessFactsV1",
    )


def test_contract_document_locks_signature_fields_and_strict_types() -> None:
    text = _contract_text()
    _assert_closed_contract(text)
    assert "No positional argument or additional parameter is allowed." in text
    assert "type(market_facts_snapshot) is" in text
    assert "Every type in this section must be a `@dataclass(frozen=True, slots=True)`." in text
    assert "Every scalar must have its annotated exact built-in type" in text
    assert "`bool` is not an\n`int`" in text


def test_g175_ready_input_vector_is_complete_strict_and_immutable() -> None:
    assert READY_INPUT_VECTOR.record_type == "CanonicalGoldMarketFactsSnapshotV1"
    assert tuple(name for name, _ in READY_INPUT_VECTOR.fields) == G175_INPUT_FIELDS[
        "CanonicalGoldMarketFactsSnapshotV1"
    ]
    values = dict(READY_INPUT_VECTOR.fields)
    assert type(values["passed"]) is bool and values["passed"] is True
    assert type(values["reason_codes"]) is tuple and values["reason_codes"] == ()
    assert type(values["warning_codes"]) is tuple and values["warning_codes"] == ()
    assert type(values["sequence"]) is int and values["sequence"] > 0
    assert values["canonical_symbol"] == "XAUUSD"
    assert values["broker_symbol"] == "GOLD"
    assert type(values["timeframes"]) is tuple
    assert tuple(dict(item.fields)["timeframe"] for item in values["timeframes"]) == (
        "M15",
        "H1",
        "H4",
        "D1",
    )
    assert READY_72_DIGIT_FIXED_POINT.endswith(".00000000")
    assert len(Decimal(READY_72_DIGIT_FIXED_POINT).as_tuple().digits) == 72

    text = _contract_text()
    assert _g175_schema_fields(text) == dict(G175_INPUT_FIELDS)
    assert "The accepted predicate is closed over the public G175 result." in text
    assert "every bars tuple\n  is non-empty" in text
    assert "1\n  through 500 records" in text
    assert "open_time + period_seconds <= bars_payload_instant" in text


def test_session_profile_windows_endpoints_and_writer_label_are_exact() -> None:
    assert WEEKDAY_CODES == (
        "MONDAY",
        "TUESDAY",
        "WEDNESDAY",
        "THURSDAY",
        "FRIDAY",
        "SATURDAY",
        "SUNDAY",
    )
    assert _session_rows(_contract_text()) == SESSION_WINDOWS
    assert tuple(vector.utc_second_of_day for vector in SESSION_BOUNDARY_VECTORS) == (
        0,
        28799,
        28800,
        46799,
        46800,
        57599,
        57600,
        79199,
        79200,
        86399,
    )
    for vector in SESSION_BOUNDARY_VECTORS:
        assert vector.start <= vector.utc_second_of_day < vector.end
        assert vector.since_start == vector.utc_second_of_day - vector.start
        assert vector.until_end == vector.end - vector.utc_second_of_day

    text = _contract_text()
    assert "MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY" in text
    assert "canonical_gold_session_spread_freshness_profile_v1" in text
    assert "start <= value < end" in text
    assert "equal to an end belongs to the next bucket" in text
    assert "copied only into the explicit\nobserved-label field" in text
    assert "never selects a session bucket" in text


def test_exact_midpoint_and_half_even_vectors_cover_large_coefficients() -> None:
    bid = int("9" * 63 + "8")
    ask = bid + 1
    assert len(str(bid)) == 64
    assert len(str(ask)) == 64
    assert len(str(bid + ask)) == 65
    midpoint_coefficient = 5 * (bid + ask)
    assert Fraction(midpoint_coefficient, 10) == Fraction(bid + ask, 2)
    assert str(midpoint_coefficient) == "9" * 63 + "85"

    for vector in HALF_EVEN_VECTORS:
        quotient, remainder = divmod(vector.numerator, vector.denominator)
        assert (quotient, remainder) == (vector.quotient, vector.remainder)
        if 2 * remainder < vector.denominator:
            rounded = quotient
        elif 2 * remainder > vector.denominator:
            rounded = quotient + 1
        else:
            rounded = quotient if quotient % 2 == 0 else quotient + 1
        assert rounded == vector.rounded

    text = _contract_text()
    assert "must not impose an independent digit-count limit on a formatted\nG175 Decimal coefficient" in text
    assert "This remains exact when `B + A` has 65 digits and never rounds." in text
    assert "binary float arithmetic" in text
    assert "unique exact `ROUND_HALF_EVEN` result" in text
    assert "0.000000" in text


def test_source_freshness_vectors_lock_maximum_and_tie_priority() -> None:
    assert FRESHNESS_VECTORS == (
        FreshnessVector(10, 2, 3, 10, "TICK"),
        FreshnessVector(10, 10, 2, 10, "TICK"),
        FreshnessVector(2, 10, 10, 10, "BARS_PAYLOAD"),
        FreshnessVector(2, 3, 10, 10, "SYMBOL_SPEC"),
    )
    for vector in FRESHNESS_VECTORS:
        assert vector.maximum_age == max(
            vector.tick_age,
            vector.bars_payload_age,
            vector.symbol_spec_age,
        )

    text = _contract_text()
    assert "No threshold or warning classification is applied." in text
    assert "No per-timeframe\nage" in text
    assert "No timestamp is reparsed to derive a second freshness value." in text


def test_status_reason_identity_and_safety_vectors_are_exact() -> None:
    assert len(STATUS_REASON_VECTORS) == 8
    assert _status_rows(_contract_text()) == STATUS_REASON_VECTORS
    assert STATUS_REASON_VECTORS[0].reasons == ()
    assert all(len(vector.reasons) == 1 for vector in STATUS_REASON_VECTORS[1:])
    assert len({vector.status for vector in STATUS_REASON_VECTORS}) == 8
    assert len({vector.reasons for vector in STATUS_REASON_VECTORS}) == 8
    assert tuple(FAILURE_CLEARED_FIELDS) == (
        "identity_available",
        "bundle_schema_version",
        "bundle_id",
        "sequence",
        "canonical_symbol",
        "broker_symbol",
        "reference_time_utc",
        "session",
        "spread",
        "freshness",
    )
    assert tuple(SAFETY_FLAGS.items()) == (
        ("read_only", True),
        ("demo_only", True),
        ("is_tradable", False),
        ("can_execute", False),
        ("is_trading_permission", False),
        ("is_execution_instruction", False),
        ("allowed_to_call_ea", False),
        ("allowed_to_modify_risk", False),
    )
    text = _contract_text()
    for name, value in SAFETY_FLAGS.items():
        assert f"| `{name}` | `{'true' if value else 'false'}` |" in text
    assert "identity fields 8 through 13 are `None`" in text
    assert "`session`, `spread`, and `freshness` are `None`" in text


def test_negative_shape_and_value_vectors_lock_first_failure_priority() -> None:
    assert tuple(vector.mutation for vector in SHAPE_MUTATION_VECTORS) == (
        "missing",
        "extra",
        "reordered",
        "duplicate",
        "alias",
        "case_change",
    )
    for vector in SHAPE_MUTATION_VECTORS:
        assert type(vector.original_fields) is tuple
        assert type(vector.mutated_fields) is tuple
        assert vector.mutated_fields != vector.original_fields
        assert vector.expected_status.endswith("_INPUT_INVALID")
        assert vector.expected_reason.endswith("_INPUT_TYPE_INVALID")

    assert tuple(vector.priority for vector in STRICT_VALUE_MUTATION_VECTORS) == (
        1,
        1,
        1,
        2,
        2,
        3,
        4,
        4,
        5,
        5,
        6,
        6,
        7,
    )
    assert tuple(vector.mutation for vector in STRICT_VALUE_MUTATION_VECTORS) == (
        "subclass",
        "wrong_container",
        "wrong_element",
        "wrong_ready_status",
        "bar_order",
        "identity",
        "timestamp",
        "writer_label",
        "decimal_exponent",
        "spread_identity",
        "negative_freshness",
        "incomplete_bar",
        "unexpected_exception",
    )
    assert type(STRICT_VALUE_MUTATION_VECTORS[0].invalid_value) is StrictStringSubclass
    assert type(STRICT_VALUE_MUTATION_VECTORS[1].invalid_value) is frozenset
    assert STRICT_VALUE_MUTATION_VECTORS[1].invalid_type is frozenset
    assert STRICT_VALUE_MUTATION_VECTORS[2].invalid_type is int

    text = _contract_text()
    priority = _section(
        text,
        "#### 3.2.2 Deterministic invalid-input classification",
        "### 3.3 Time and session authority",
    )
    assert re.findall(r"(?m)^(\d+)\.", priority) == [str(index) for index in range(1, 8)]
    for vector in STRICT_VALUE_MUTATION_VECTORS:
        assert vector.expected_status in text
        assert vector.expected_reason in text


def test_contract_mutation_probes_reject_boundary_formula_and_mapping_drift() -> None:
    text = _contract_text()
    mutations = (
        text.replace("market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,", "clock: object,"),
        text.replace("| 1 | `contract_version` | `str` |", "| 1 | `passed` | `bool` |"),
        text.replace("| `ASIA_UTC` | 0 | 28800 |", "| `ASIA_UTC` | 0 | 28801 |"),
        text.replace("M = 5 * (B + A)", "M = (B + A) // 2"),
        text.replace(
            "must not impose an independent digit-count limit on a formatted\nG175 Decimal coefficient",
            "must impose a 64 digit limit on every formatted G175 Decimal coefficient",
        ),
        text.replace(
            "Ties use the fixed priority `TICK`, `BARS_PAYLOAD`, then\n`SYMBOL_SPEC`",
            "Ties use the priority `SYMBOL_SPEC`, `BARS_PAYLOAD`, then `TICK`",
        ),
        text.replace(
            "7. a separately versioned ReplayRunner W6 stage before W7.",
            "7. a separately versioned ReplayRunner W6 stage before W7.\n8. runtime activation.",
        ),
        text.replace(
            "| `false` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID` | "
            "`(\"GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID\",)` |",
            "| `false` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID` | "
            "`(\"GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID\",)` |",
        ),
    )
    for mutated in mutations:
        with pytest.raises(AssertionError):
            _assert_closed_contract(mutated)


def test_staged_delivery_and_isolation_remain_closed() -> None:
    text = _contract_text()
    staged = _section(
        text,
        "Later work must remain separately planned and approved:",
        "No stage silently includes the next.",
    )
    assert re.findall(r"(?m)^(\d+)\.", staged) == [str(index) for index in range(1, 8)]
    assert "immutable static contract vectors for this exact contract" in staged
    assert "production types and the pure-memory builder" in staged
    assert "G185 READY source, then the\n   G178 projector, then the G189 builder" in staged
    assert "deterministic non-activating verification" in staged
    assert "volatility and structure features" in staged
    assert "economic-window inputs" in staged
    assert "ReplayRunner W6 stage before W7" in staged

    for prohibited in (
        "filesystem",
        "environment",
        "network",
        "settings",
        "logging",
        "clock",
        "database",
        "cache",
        "frontend I/O",
    ):
        assert prohibited in text
    assert "W6 remains `TESTS_ONLY`" in text
    assert "Reader activation, real MT4, EA, order, execution" in text
    assert "trading remain prohibited" in text


def test_contract_vector_module_has_no_runtime_import_or_builder() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
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
    assert not any(module == "app" or module.startswith("app.") for module in imported_modules)
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "build_canonical_gold_session_spread_freshness_facts_v1" not in function_names
    assert "canonical_gold_session_spread_freshness_facts" not in imported_modules
    assert all(ord(character) < 128 for character in Path(__file__).read_text(encoding="ascii"))
