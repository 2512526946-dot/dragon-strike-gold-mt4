from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass, replace
from decimal import Decimal
from pathlib import Path
import re
from types import MappingProxyType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_gold_volatility_structure_facts_v1_contract.md"
)
G175_CONTRACT_PATH = (
    REPO_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_gold_market_facts_snapshot_v1_contract.md"
)

PUBLIC_SIGNATURE = """build_canonical_gold_volatility_structure_facts_v1(
    *,
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,
) -> CanonicalGoldVolatilityStructureFactsV1"""

PUBLIC_EXPORTS = (
    "CanonicalGoldVolatilityStructureFactsV1",
    "CanonicalGoldTimeframeVolatilityStructureFactsV1",
    "CanonicalGoldBarPairVolatilityStructureFactsV1",
    "build_canonical_gold_volatility_structure_facts_v1",
)


@dataclass(frozen=True, slots=True)
class StatusReasonVector:
    priority: int
    status: str
    reason: str
    meaning: str


@dataclass(frozen=True, slots=True)
class PairVector:
    name: str
    digits: int
    previous: tuple[str, str, str, str]
    current: tuple[str, str, str, str]
    expected_decimals: tuple[str, ...]
    expected_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FormatVector:
    branch: str
    digits: int
    text: str
    accepted: bool


@dataclass(frozen=True, slots=True)
class ShapeMutationVector:
    mutation: str
    original_fields: tuple[str, ...]
    mutated_fields: tuple[str, ...]
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
class AdjacentPairIdentityVector:
    timeframe: str
    source_open_times: tuple[str, ...]
    expected_pair_times: tuple[tuple[str, str], ...]
    expected_source_bar_count: int
    expected_pair_count: int


@dataclass(frozen=True, slots=True)
class ObjectGraphExpectationVector:
    input_snapshot_unchanged: bool
    nested_input_records_unchanged: bool
    repeated_values_equal: bool
    result_identity_distinct: bool
    timeframe_identity_distinct: bool
    pair_tuple_identity_distinct: bool
    pair_record_identity_distinct: bool
    caller_reference_isolated: bool
    hidden_mutable_state_absent: bool


class StrictStringSubclass(str):
    pass


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
    (
        "timeframes",
        "tuple[CanonicalGoldTimeframeVolatilityStructureFactsV1, ...]",
    ),
    ("total_pair_count", "int"),
    ("read_only", "bool"),
    ("demo_only", "bool"),
    ("is_tradable", "bool"),
    ("can_execute", "bool"),
    ("is_trading_permission", "bool"),
    ("is_execution_instruction", "bool"),
    ("allowed_to_call_ea", "bool"),
    ("allowed_to_modify_risk", "bool"),
)

TIMEFRAME_FIELDS = (
    ("timeframe", "str"),
    ("period_seconds", "int"),
    ("source_bar_count", "int"),
    ("pair_count", "int"),
    (
        "bar_pairs",
        "tuple[CanonicalGoldBarPairVolatilityStructureFactsV1, ...]",
    ),
)

PAIR_FIELDS = (
    ("previous_open_time_utc", "str"),
    ("current_open_time_utc", "str"),
    ("previous_range_decimal", "str"),
    ("current_range_decimal", "str"),
    ("true_range_decimal", "str"),
    ("body_signed_decimal", "str"),
    ("body_absolute_decimal", "str"),
    ("upper_wick_decimal", "str"),
    ("lower_wick_decimal", "str"),
    ("close_change_decimal", "str"),
    ("high_change_decimal", "str"),
    ("low_change_decimal", "str"),
    ("direction_code", "str"),
    ("range_relation_code", "str"),
    ("range_containment_code", "str"),
    ("current_high_vs_previous_high_code", "str"),
    ("current_low_vs_previous_low_code", "str"),
    ("current_close_vs_previous_range_code", "str"),
)

PUBLIC_SCHEMAS = MappingProxyType(
    {
        "CanonicalGoldVolatilityStructureFactsV1": RESULT_FIELDS,
        "CanonicalGoldTimeframeVolatilityStructureFactsV1": TIMEFRAME_FIELDS,
        "CanonicalGoldBarPairVolatilityStructureFactsV1": PAIR_FIELDS,
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
    '`contract_version == "1.0"`, `passed is True`, status is exact '
    "`CANONICAL_GOLD_MARKET_FACTS_READY`, and both code tuples are empty.",
    "`identity_available is True`; bundle schema version is exact `\"1.0\"`; "
    "bundle id matches `^[A-Za-z0-9._-]{16,64}$`; sequence is a positive strict "
    "`int`; symbols are exact `XAUUSD` and `GOLD`; reference time is a strict "
    "valid UTC `Z` timestamp.",
    "Quote, symbol, freshness, and all four timeframes are present with exact "
    "G175 types. The timeframe tuple is exactly M15/H1/H4/D1 with matching "
    "periods and 1 through 500 bars in each record. A one-bar timeframe is valid "
    "G175 input but is insufficient for this pair-based contract and maps to the "
    "dedicated history failure in Section 10.",
    "Bar open times are strict UTC `Z`, strictly increasing within each "
    "timeframe, and each bar is complete at the snapshot reference time.",
    "Every price string is finite, canonical fixed-point text in the exact G175 "
    "`digits` format. Every bar open, high, low, and close is strictly greater "
    "than zero. Bid and ask are positive, ask is not below bid, and `ask - bid "
    "== spread == spread_points * point`. Quote and symbol digits and point are "
    "identical; point is the exact price quantum. Tick size is positive; tick "
    "value, contract size, min lot, lot step, and max lot are canonical positive "
    "decimals; min lot and lot step do not exceed max lot; base/profit currencies "
    "are exact XAU/USD; each remaining label fully matches strict ASCII "
    "`^[A-Za-z0-9._:-]+$`.",
    "Each bar has nonnegative strict `int` tick volume and spread points; `high "
    ">= max(open, close)` and `low <= min(open, close)`.",
    "Tick, bars-payload, and symbol-spec ages are nonnegative strict `int` "
    "microseconds. Tick and symbol ages equal reference time minus their exact "
    "timestamps. Let `bars_payload_time` equal reference time minus the exact "
    "bars-payload age; every bar must satisfy `open_time + period_seconds <= "
    "bars_payload_time`. Overflow is invalid.",
    "All eight safety flags are exact: Read-only and Demo-only true; tradable, "
    "executable, permission, instruction, EA-call, and risk-modification false.",
)

TIMEFRAME_AUTHORITY = (
    ("M15", 900),
    ("H1", 3600),
    ("H4", 14400),
    ("D1", 86400),
)

CALCULATION_FORMULAS = (
    "previous_range = PH - PL",
    "current_range = H - L",
    "true_range = max(H - L, abs(H - PC), abs(L - PC))",
    "body_signed = C - O",
    "body_absolute = abs(C - O)",
    "upper_wick = H - max(O, C)",
    "lower_wick = min(O, C) - L",
    "close_change = C - PC",
    "high_change = H - PH",
    "low_change = L - PL",
)

STRUCTURE_RULES = MappingProxyType(
    {
        "direction": (
            "C > O  -> UP",
            "C < O  -> DOWN",
            "C == O -> FLAT",
        ),
        "range_relation": (
            "current_range > previous_range  -> EXPANDED",
            "current_range < previous_range  -> CONTRACTED",
            "current_range == previous_range -> EQUAL",
        ),
        "range_containment": (
            "H == PH and L == PL                 -> EXACT_MATCH",
            "H <= PH and L >= PL                 -> INSIDE",
            "H >= PH and L <= PL                 -> OUTSIDE",
            "H > PH and L > PL                   -> SHIFTED_UP",
            "H < PH and L < PL                   -> SHIFTED_DOWN",
        ),
        "high_relation": (
            "H > PH  -> ABOVE_PREVIOUS_HIGH",
            "H < PH  -> BELOW_PREVIOUS_HIGH",
            "H == PH -> AT_PREVIOUS_HIGH",
        ),
        "low_relation": (
            "L > PL  -> ABOVE_PREVIOUS_LOW",
            "L < PL  -> BELOW_PREVIOUS_LOW",
            "L == PL -> AT_PREVIOUS_LOW",
        ),
        "close_relation": (
            "C > PH  -> ABOVE_PREVIOUS_HIGH",
            "C == PH -> AT_PREVIOUS_HIGH",
            "C > PL  -> INSIDE_PREVIOUS_RANGE",
            "C == PL -> AT_PREVIOUS_LOW",
            "C < PL  -> BELOW_PREVIOUS_LOW",
        ),
    }
)

PAIR_VECTORS = (
    PairVector(
        "exact_match_flat",
        2,
        ("100.00", "110.00", "90.00", "100.00"),
        ("100.00", "110.00", "90.00", "100.00"),
        (
            "20.00",
            "20.00",
            "20.00",
            "0.00",
            "0.00",
            "10.00",
            "10.00",
            "0.00",
            "0.00",
            "0.00",
        ),
        (
            "FLAT",
            "EQUAL",
            "EXACT_MATCH",
            "AT_PREVIOUS_HIGH",
            "AT_PREVIOUS_LOW",
            "INSIDE_PREVIOUS_RANGE",
        ),
    ),
    PairVector(
        "inside_up",
        2,
        ("100.00", "110.00", "90.00", "100.00"),
        ("95.00", "108.00", "92.00", "105.00"),
        (
            "20.00",
            "16.00",
            "16.00",
            "10.00",
            "10.00",
            "3.00",
            "3.00",
            "5.00",
            "-2.00",
            "2.00",
        ),
        (
            "UP",
            "CONTRACTED",
            "INSIDE",
            "BELOW_PREVIOUS_HIGH",
            "ABOVE_PREVIOUS_LOW",
            "INSIDE_PREVIOUS_RANGE",
        ),
    ),
    PairVector(
        "outside_down",
        2,
        ("100.00", "110.00", "90.00", "100.00"),
        ("105.00", "112.00", "88.00", "95.00"),
        (
            "20.00",
            "24.00",
            "24.00",
            "-10.00",
            "10.00",
            "7.00",
            "7.00",
            "-5.00",
            "2.00",
            "-2.00",
        ),
        (
            "DOWN",
            "EXPANDED",
            "OUTSIDE",
            "ABOVE_PREVIOUS_HIGH",
            "BELOW_PREVIOUS_LOW",
            "INSIDE_PREVIOUS_RANGE",
        ),
    ),
    PairVector(
        "shifted_up_close_above",
        2,
        ("100.00", "110.00", "90.00", "100.00"),
        ("111.00", "120.00", "100.00", "115.00"),
        (
            "20.00",
            "20.00",
            "20.00",
            "4.00",
            "4.00",
            "5.00",
            "11.00",
            "15.00",
            "10.00",
            "10.00",
        ),
        (
            "UP",
            "EQUAL",
            "SHIFTED_UP",
            "ABOVE_PREVIOUS_HIGH",
            "ABOVE_PREVIOUS_LOW",
            "ABOVE_PREVIOUS_HIGH",
        ),
    ),
    PairVector(
        "shifted_down_close_below",
        2,
        ("100.00", "110.00", "90.00", "100.00"),
        ("89.00", "100.00", "80.00", "85.00"),
        (
            "20.00",
            "20.00",
            "20.00",
            "-4.00",
            "4.00",
            "11.00",
            "5.00",
            "-15.00",
            "-10.00",
            "-10.00",
        ),
        (
            "DOWN",
            "EQUAL",
            "SHIFTED_DOWN",
            "BELOW_PREVIOUS_HIGH",
            "BELOW_PREVIOUS_LOW",
            "BELOW_PREVIOUS_LOW",
        ),
    ),
    PairVector(
        "gap_up_true_range_uses_previous_close",
        2,
        ("100.00", "110.00", "90.00", "100.00"),
        ("120.00", "125.00", "118.00", "122.00"),
        (
            "20.00",
            "7.00",
            "25.00",
            "2.00",
            "2.00",
            "3.00",
            "2.00",
            "22.00",
            "15.00",
            "28.00",
        ),
        (
            "UP",
            "CONTRACTED",
            "SHIFTED_UP",
            "ABOVE_PREVIOUS_HIGH",
            "ABOVE_PREVIOUS_LOW",
            "ABOVE_PREVIOUS_HIGH",
        ),
    ),
    PairVector(
        "gap_down_true_range_uses_previous_close",
        2,
        ("100.00", "110.00", "90.00", "100.00"),
        ("80.00", "82.00", "75.00", "78.00"),
        (
            "20.00",
            "7.00",
            "25.00",
            "-2.00",
            "2.00",
            "2.00",
            "3.00",
            "-22.00",
            "-28.00",
            "-15.00",
        ),
        (
            "DOWN",
            "CONTRACTED",
            "SHIFTED_DOWN",
            "BELOW_PREVIOUS_HIGH",
            "BELOW_PREVIOUS_LOW",
            "BELOW_PREVIOUS_LOW",
        ),
    ),
)

ADJACENT_PAIR_IDENTITY_VECTORS = (
    AdjacentPairIdentityVector(
        "M15",
        (
            "2026-01-02T00:00:00Z",
            "2026-01-02T00:15:00Z",
            "2026-01-02T00:30:00Z",
            "2026-01-02T00:45:00Z",
        ),
        (
            ("2026-01-02T00:00:00Z", "2026-01-02T00:15:00Z"),
            ("2026-01-02T00:15:00Z", "2026-01-02T00:30:00Z"),
            ("2026-01-02T00:30:00Z", "2026-01-02T00:45:00Z"),
        ),
        4,
        3,
    ),
    AdjacentPairIdentityVector(
        "H1",
        (
            "2026-01-02T00:00:00Z",
            "2026-01-02T01:00:00Z",
            "2026-01-02T02:00:00Z",
        ),
        (
            ("2026-01-02T00:00:00Z", "2026-01-02T01:00:00Z"),
            ("2026-01-02T01:00:00Z", "2026-01-02T02:00:00Z"),
        ),
        3,
        2,
    ),
    AdjacentPairIdentityVector(
        "H4",
        ("2026-01-01T20:00:00Z", "2026-01-02T00:00:00Z"),
        (("2026-01-01T20:00:00Z", "2026-01-02T00:00:00Z"),),
        2,
        1,
    ),
    AdjacentPairIdentityVector(
        "D1",
        (
            "2025-12-30T00:00:00Z",
            "2025-12-31T00:00:00Z",
            "2026-01-01T00:00:00Z",
            "2026-01-02T00:00:00Z",
            "2026-01-03T00:00:00Z",
        ),
        (
            ("2025-12-30T00:00:00Z", "2025-12-31T00:00:00Z"),
            ("2025-12-31T00:00:00Z", "2026-01-01T00:00:00Z"),
            ("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"),
            ("2026-01-02T00:00:00Z", "2026-01-03T00:00:00Z"),
        ),
        5,
        4,
    ),
)

OBJECT_GRAPH_EXPECTATIONS = ObjectGraphExpectationVector(
    input_snapshot_unchanged=True,
    nested_input_records_unchanged=True,
    repeated_values_equal=True,
    result_identity_distinct=True,
    timeframe_identity_distinct=True,
    pair_tuple_identity_distinct=True,
    pair_record_identity_distinct=True,
    caller_reference_isolated=True,
    hidden_mutable_state_absent=True,
)

CLOSE_BOUNDARY_VECTORS = (
    ("111.00", "ABOVE_PREVIOUS_HIGH"),
    ("110.00", "AT_PREVIOUS_HIGH"),
    ("100.00", "INSIDE_PREVIOUS_RANGE"),
    ("90.00", "AT_PREVIOUS_LOW"),
    ("89.00", "BELOW_PREVIOUS_LOW"),
)

FORMAT_VECTORS = (
    FormatVector("source", 0, "1", True),
    FormatVector("source", 0, "1.", False),
    FormatVector("source", 0, "-1", False),
    FormatVector("source", 2, "1.00", True),
    FormatVector("source", 2, "1", False),
    FormatVector("source", 2, "01.00", False),
    FormatVector("unsigned", 0, "0", True),
    FormatVector("unsigned", 0, "0.", False),
    FormatVector("unsigned", 2, "0.00", True),
    FormatVector("unsigned", 2, "-0.00", False),
    FormatVector("signed", 0, "-1", True),
    FormatVector("signed", 0, "+1", False),
    FormatVector("signed", 2, "-1.00", True),
    FormatVector("signed", 2, "+1.00", False),
    FormatVector("signed", 2, "-0.00", False),
    FormatVector("source", 8, f"{'9' * 72}.00000000", True),
)

STATUS_REASON_VECTORS = (
    StatusReasonVector(
        1,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_INPUT_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_INPUT_TYPE_INVALID",
        "top-level or nested exact shape/type invalid",
    ),
    StatusReasonVector(
        2,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_UPSTREAM_BLOCKED",
        "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_NOT_READY",
        "top-level G175 passed/status/code or fixed safety semantics not satisfied",
    ),
    StatusReasonVector(
        3,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_IDENTITY_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_IDENTITY_INVALID",
        "bundle/symbol/reference identity invalid",
    ),
    StatusReasonVector(
        4,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID",
        "timeframe order, period, bar order, completion, or OHLC relation invalid",
    ),
    StatusReasonVector(
        5,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT",
        "GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT",
        "any timeframe has fewer than two completed bars",
    ),
    StatusReasonVector(
        6,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_DECIMAL_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_DECIMAL_INPUT_INVALID",
        "fixed-point parse, arithmetic, representability, or formatting invalid",
    ),
    StatusReasonVector(
        7,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID",
        "derived count, ordering, code, or invariant is contradictory",
    ),
    StatusReasonVector(
        8,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_SAFE_FAILURE",
        "GOLD_VOLATILITY_STRUCTURE_EXCEPTION_SANITIZED",
        "unexpected exception at the public boundary",
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
        "timeframes": (),
        "total_pair_count": 0,
        "warning_codes": (),
    }
)

RESULT_FIELD_NAMES = tuple(name for name, _ in RESULT_FIELDS)
SHAPE_MUTATION_VECTORS = (
    ShapeMutationVector("missing", RESULT_FIELD_NAMES, RESULT_FIELD_NAMES[:-1], 1),
    ShapeMutationVector(
        "extra",
        RESULT_FIELD_NAMES,
        RESULT_FIELD_NAMES + ("unexpected",),
        1,
    ),
    ShapeMutationVector(
        "reordered",
        RESULT_FIELD_NAMES,
        (RESULT_FIELD_NAMES[1], RESULT_FIELD_NAMES[0]) + RESULT_FIELD_NAMES[2:],
        1,
    ),
    ShapeMutationVector(
        "duplicate",
        RESULT_FIELD_NAMES,
        RESULT_FIELD_NAMES[:-1] + (RESULT_FIELD_NAMES[0],),
        1,
    ),
    ShapeMutationVector(
        "alias",
        RESULT_FIELD_NAMES,
        tuple("reasons" if item == "reason_codes" else item for item in RESULT_FIELD_NAMES),
        1,
    ),
    ShapeMutationVector(
        "case_change",
        RESULT_FIELD_NAMES,
        tuple("BundleId" if item == "bundle_id" else item for item in RESULT_FIELD_NAMES),
        1,
    ),
)

VALUE_MUTATION_VECTORS = (
    ValueMutationVector(
        "subclass",
        ("contract_version",),
        StrictStringSubclass("1.0"),
        1,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_INPUT_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_INPUT_TYPE_INVALID",
    ),
    ValueMutationVector(
        "wrong_container",
        ("timeframes",),
        [],
        1,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_INPUT_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_INPUT_TYPE_INVALID",
    ),
    ValueMutationVector(
        "wrong_element",
        ("timeframes", 0),
        object(),
        1,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_INPUT_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_INPUT_TYPE_INVALID",
    ),
    ValueMutationVector(
        "not_ready",
        ("passed",),
        False,
        2,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_UPSTREAM_BLOCKED",
        "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_NOT_READY",
    ),
    ValueMutationVector(
        "warning_present",
        ("warning_codes",),
        ("WARNING",),
        2,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_UPSTREAM_BLOCKED",
        "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_NOT_READY",
    ),
    ValueMutationVector(
        "bundle_regex",
        ("bundle_id",),
        "short",
        3,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_IDENTITY_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_IDENTITY_INVALID",
    ),
    ValueMutationVector(
        "reference_timestamp",
        ("reference_time_utc",),
        "2026-01-01",
        3,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_IDENTITY_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_IDENTITY_INVALID",
    ),
    ValueMutationVector(
        "timeframe_order",
        ("timeframes",),
        ("H1", "M15", "H4", "D1"),
        4,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID",
    ),
    ValueMutationVector(
        "bar_timestamp",
        ("timeframes", 0, "bars", 0, "open_time_utc"),
        "bad",
        4,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID",
    ),
    ValueMutationVector(
        "zero_ohlc",
        ("timeframes", 0, "bars", 0, "open_decimal"),
        "0.00",
        4,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID",
    ),
    ValueMutationVector(
        "ohlc_relation",
        ("timeframes", 0, "bars", 0, "high_decimal"),
        "1.00",
        4,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID",
    ),
    ValueMutationVector(
        "history",
        ("timeframes", 0, "bars"),
        ("one_bar",),
        5,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT",
        "GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT",
    ),
    ValueMutationVector(
        "digits_zero_trailing_point",
        ("quote", "bid_decimal"),
        "1.",
        6,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_DECIMAL_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_DECIMAL_INPUT_INVALID",
    ),
    ValueMutationVector(
        "digits_positive_missing_point",
        ("quote", "bid_decimal"),
        "100",
        6,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_DECIMAL_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_DECIMAL_INPUT_INVALID",
    ),
    ValueMutationVector(
        "nonfinite_decimal",
        ("quote", "bid_decimal"),
        "NaN",
        6,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_DECIMAL_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_DECIMAL_INPUT_INVALID",
    ),
    ValueMutationVector(
        "result_count",
        ("total_pair_count",),
        -1,
        7,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID",
    ),
    ValueMutationVector(
        "result_code",
        ("timeframes", 0, "bar_pairs", 0, "direction_code"),
        "BUY",
        7,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID",
    ),
    ValueMutationVector(
        "unexpected_exception",
        ("public_boundary",),
        RuntimeError,
        8,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_SAFE_FAILURE",
        "GOLD_VOLATILITY_STRUCTURE_EXCEPTION_SANITIZED",
    ),
)

EXPECTED_VALUE_MUTATION_PRIORITIES = MappingProxyType(
    {
        "subclass": 1,
        "wrong_container": 1,
        "wrong_element": 1,
        "not_ready": 2,
        "warning_present": 2,
        "bundle_regex": 3,
        "reference_timestamp": 3,
        "timeframe_order": 4,
        "bar_timestamp": 4,
        "zero_ohlc": 4,
        "ohlc_relation": 4,
        "history": 5,
        "digits_zero_trailing_point": 6,
        "digits_positive_missing_point": 6,
        "nonfinite_decimal": 6,
        "result_count": 7,
        "result_code": 7,
        "unexpected_exception": 8,
    }
)

STAGED_DELIVERY = (
    "immutable static contract vectors for this exact G194 contract;",
    "production types and the pure-memory builder;",
    "genuine offline composition evidence through G185, G178, and this builder;",
    "deterministic non-activating verification for this facts stage;",
    "a separate contract and delivery for economic-window inputs;",
    "a separately versioned ReplayRunner W6 stage covering reviewed W6 facts; and",
    "only then, separately contracted W7 deterministic analysis.",
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="ascii")


def _section(text: str, start: str, end: str | None = None) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index) if end is not None else len(text)
    return text[start_index:end_index]


def _schema_rows(
    text: str,
    heading: str,
    next_heading: str,
) -> tuple[tuple[str, str], ...]:
    body = _section(text, heading, next_heading)
    return tuple(
        re.findall(
            r"(?m)^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|",
            body,
        )
    )


def _g175_schema_fields() -> dict[str, tuple[str, ...]]:
    text = G175_CONTRACT_PATH.read_text(encoding="ascii")
    timeframe_body = _section(text, "### 7.2 Timeframe", "### 7.3 Symbol facts")
    boundaries = (
        ("CanonicalGoldMarketFactsSnapshotV1", "## 7. Result Type", "### 7.1 Quote facts"),
        ("CanonicalGoldQuoteFactsV1", "### 7.1 Quote facts", "### 7.2 Timeframe"),
        ("CanonicalGoldTimeframeFactsV1", "### 7.2 Timeframe", "Each bar has"),
        ("CanonicalGoldSymbolFactsV1", "### 7.3 Symbol facts", "### 7.4 Freshness facts"),
        ("CanonicalGoldFreshnessFactsV1", "### 7.4 Freshness facts", "## 8. Deterministic"),
    )
    parsed: dict[str, tuple[str, ...]] = {}
    for record, start, end in boundaries:
        body = _section(text, start, end)
        parsed[record] = tuple(
            re.findall(r"(?m)^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|", body)
        )
    bar_body = timeframe_body[timeframe_body.index("Each bar has") :]
    parsed["CanonicalGoldBarFactsV1"] = tuple(
        re.findall(r"(?m)^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|", bar_body)
    )
    return parsed


def _ordered_items(body: str) -> tuple[str, ...]:
    items: list[str] = []
    current: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if match is not None:
            if current:
                items.append(" ".join(current))
            current = [match.group(1)]
        elif current and stripped:
            current.append(stripped)
    if current:
        items.append(" ".join(current))
    return tuple(items)


def _g175_ready_predicates(text: str) -> tuple[str, ...]:
    body = _section(
        text,
        "An accepted input must satisfy all of the following:",
        "Missing, extra, reordered, duplicate, aliased",
    )
    return _ordered_items(body)


def _status_rows(text: str) -> tuple[StatusReasonVector, ...]:
    body = _section(text, "## 10. Status", "READY is exactly:")
    return tuple(
        StatusReasonVector(int(priority), status, reason, meaning.strip())
        for priority, status, reason, meaning in re.findall(
            r"(?m)^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|$",
            body,
        )
    )


def _code_block_lines(text: str, start: str, end: str) -> tuple[str, ...]:
    body = _section(text, start, end)
    match = re.search(r"```text\n(.*?)\n```", body, re.DOTALL)
    assert match is not None
    return tuple(line.strip() for line in match.group(1).splitlines())


def _structure_rules(text: str) -> dict[str, tuple[str, ...]]:
    return {
        "direction": _code_block_lines(text, "### 9.1 Direction", "### 9.2"),
        "range_relation": _code_block_lines(text, "### 9.2 Range relation", "### 9.3"),
        "range_containment": _code_block_lines(text, "### 9.3 Range containment", "### 9.4"),
        "high_relation": _code_block_lines(text, "### 9.4 Current high", "### 9.5"),
        "low_relation": _code_block_lines(text, "### 9.5 Current low", "### 9.6"),
        "close_relation": _code_block_lines(text, "### 9.6 Current close", "## 10."),
    }


def _public_exports(text: str) -> tuple[str, ...]:
    body = _section(text, "Its ordered `__all__` must be exactly:", "The module may import")
    return tuple(re.findall(r'\s+"([A-Za-z0-9_]+)",', body))


def _staged_delivery(text: str) -> tuple[str, ...]:
    body = _section(
        text,
        "Later work must remain separately planned and approved in this order:",
        "No stage silently includes the next.",
    )
    return _ordered_items(body)


def _format_pattern(branch: str, digits: int) -> re.Pattern[str]:
    sign = "-?" if branch == "signed" else ""
    if digits == 0:
        return re.compile(rf"^{sign}(?:0|[1-9][0-9]*)$", re.ASCII)
    return re.compile(
        rf"^{sign}(?:0|[1-9][0-9]*)\.[0-9]{{{digits}}}$",
        re.ASCII,
    )


def _format_is_accepted(vector: FormatVector) -> bool:
    if _format_pattern(vector.branch, vector.digits).fullmatch(vector.text) is None:
        return False
    return not (
        vector.branch == "signed"
        and vector.text.startswith("-")
        and Decimal(vector.text) == 0
    )


def _render(value: Decimal, digits: int) -> str:
    rendered = format(value, f".{digits}f")
    if value == 0:
        return "0" if digits == 0 else "0." + ("0" * digits)
    return rendered


def _calculated_decimals(vector: PairVector) -> tuple[str, ...]:
    _, previous_high, previous_low, previous_close = map(Decimal, vector.previous)
    current_open, current_high, current_low, current_close = map(Decimal, vector.current)
    values = (
        previous_high - previous_low,
        current_high - current_low,
        max(
            current_high - current_low,
            abs(current_high - previous_close),
            abs(current_low - previous_close),
        ),
        current_close - current_open,
        abs(current_close - current_open),
        current_high - max(current_open, current_close),
        min(current_open, current_close) - current_low,
        current_close - previous_close,
        current_high - previous_high,
        current_low - previous_low,
    )
    return tuple(_render(value, vector.digits) for value in values)


def _calculated_codes(vector: PairVector) -> tuple[str, ...]:
    _, previous_high, previous_low, _ = map(Decimal, vector.previous)
    current_open, current_high, current_low, current_close = map(Decimal, vector.current)
    previous_range = previous_high - previous_low
    current_range = current_high - current_low

    direction = "UP" if current_close > current_open else "DOWN" if current_close < current_open else "FLAT"
    range_relation = (
        "EXPANDED"
        if current_range > previous_range
        else "CONTRACTED"
        if current_range < previous_range
        else "EQUAL"
    )
    if current_high == previous_high and current_low == previous_low:
        containment = "EXACT_MATCH"
    elif current_high <= previous_high and current_low >= previous_low:
        containment = "INSIDE"
    elif current_high >= previous_high and current_low <= previous_low:
        containment = "OUTSIDE"
    elif current_high > previous_high and current_low > previous_low:
        containment = "SHIFTED_UP"
    else:
        containment = "SHIFTED_DOWN"
    high_relation = (
        "ABOVE_PREVIOUS_HIGH"
        if current_high > previous_high
        else "BELOW_PREVIOUS_HIGH"
        if current_high < previous_high
        else "AT_PREVIOUS_HIGH"
    )
    low_relation = (
        "ABOVE_PREVIOUS_LOW"
        if current_low > previous_low
        else "BELOW_PREVIOUS_LOW"
        if current_low < previous_low
        else "AT_PREVIOUS_LOW"
    )
    if current_close > previous_high:
        close_relation = "ABOVE_PREVIOUS_HIGH"
    elif current_close == previous_high:
        close_relation = "AT_PREVIOUS_HIGH"
    elif current_close > previous_low:
        close_relation = "INSIDE_PREVIOUS_RANGE"
    elif current_close == previous_low:
        close_relation = "AT_PREVIOUS_LOW"
    else:
        close_relation = "BELOW_PREVIOUS_LOW"
    return (
        direction,
        range_relation,
        containment,
        high_relation,
        low_relation,
        close_relation,
    )


def _assert_value_mutation_vector(vector: ValueMutationVector) -> None:
    expected_priority = EXPECTED_VALUE_MUTATION_PRIORITIES[vector.mutation]
    expected_failure = STATUS_REASON_VECTORS[expected_priority - 1]
    assert (
        vector.expected_priority,
        vector.expected_status,
        vector.expected_reason,
    ) == (
        expected_priority,
        expected_failure.status,
        expected_failure.reason,
    )


def _assert_adjacent_pair_identity_vector(vector: AdjacentPairIdentityVector) -> None:
    assert type(vector.timeframe) is str
    assert vector.timeframe in dict(TIMEFRAME_AUTHORITY)
    assert type(vector.source_open_times) is tuple
    assert all(type(value) is str for value in vector.source_open_times)
    assert type(vector.expected_pair_times) is tuple
    assert vector.expected_source_bar_count == len(vector.source_open_times)
    assert vector.expected_pair_count == vector.expected_source_bar_count - 1
    assert vector.expected_pair_times == tuple(
        zip(vector.source_open_times, vector.source_open_times[1:])
    )


def _assert_object_graph_expectations(
    vector: ObjectGraphExpectationVector,
) -> None:
    assert all(
        type(getattr(vector, field_name)) is bool
        and getattr(vector, field_name) is True
        for field_name in vector.__slots__
    )


def _assert_closed_contract(text: str) -> None:
    assert PUBLIC_SIGNATURE in text
    assert _public_exports(text) == PUBLIC_EXPORTS
    assert _schema_rows(text, "### 5.1 ", "### 5.2 ") == RESULT_FIELDS
    assert _schema_rows(text, "### 5.2 ", "### 5.3 ") == TIMEFRAME_FIELDS
    assert _schema_rows(text, "### 5.3 ", "## 6. ") == PAIR_FIELDS
    assert _g175_ready_predicates(text) == G175_READY_PREDICATES
    assert _status_rows(text) == STATUS_REASON_VECTORS
    assert _structure_rules(text) == dict(STRUCTURE_RULES)
    assert _staged_delivery(text) == STAGED_DELIVERY
    assert "minimum_bars_per_timeframe = 2" in text
    assert "maximum_bars_per_timeframe = 500" in text
    assert "For a timeframe containing `n` bars" in text
    assert "exactly\n`n - 1` bar-pair records" in text
    for formula in CALCULATION_FORMULAS:
        assert formula in text
    assert text.count('re.compile(r"^(?:0|[1-9][0-9]*)$", re.ASCII)') == 2
    assert text.count('rf"^(?:0|[1-9][0-9]*)\\.[0-9]{{{digits}}}$"') == 2
    assert text.count('re.compile(r"^-?(?:0|[1-9][0-9]*)$", re.ASCII)') == 1
    assert text.count('rf"^-?(?:0|[1-9][0-9]*)\\.[0-9]{{{digits}}}$"') == 1
    assert "Every bar open, high, low, and close is strictly greater\n   than zero." in text
    assert "Context(prec=coefficient_digits + 2, rounding=ROUND_HALF_EVEN)" in text
    assert "traps enabled for `InvalidOperation`, `DivisionByZero`, `Overflow`," in text
    assert "`Underflow`, `Inexact`, and `Rounded`" in text
    assert "No division or\n   quantization is needed or allowed." in text
    assert "Normalize any mathematical zero" in text
    assert "passed = False" in text
    assert "timeframes = ()" in text
    assert "total_pair_count = 0" in text
    assert "must not modify the input snapshot, any nested record, tuple, or\nstring" in text
    assert "A READY result is a fresh detached frozen object graph." in text
    assert "Every\ntimeframe, pair tuple, and pair record is newly constructed for that call." in text
    assert "Repeated calls with equal exact inputs return equal values but distinct result\nand nested object identities." in text
    assert "no\nambient I/O and has no hidden mutable registry or cache." in text


def test_vectors_are_frozen_and_public_schemas_are_exact() -> None:
    with pytest.raises(FrozenInstanceError):
        STATUS_REASON_VECTORS[0].reason = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        PAIR_VECTORS[0].digits = 4  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ADJACENT_PAIR_IDENTITY_VECTORS[0].timeframe = "H1"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        OBJECT_GRAPH_EXPECTATIONS.result_identity_distinct = False  # type: ignore[misc]
    with pytest.raises(TypeError):
        PUBLIC_SCHEMAS["unexpected"] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        SAFETY_FLAGS["is_tradable"] = True  # type: ignore[index]

    assert tuple(PUBLIC_SCHEMAS) == (
        "CanonicalGoldVolatilityStructureFactsV1",
        "CanonicalGoldTimeframeVolatilityStructureFactsV1",
        "CanonicalGoldBarPairVolatilityStructureFactsV1",
    )
    assert len(RESULT_FIELDS) == 24
    assert len(TIMEFRAME_FIELDS) == 5
    assert len(PAIR_FIELDS) == 18
    assert all(type(item) is tuple for item in PUBLIC_SCHEMAS.values())


def test_contract_locks_interface_authority_and_complete_g175_predicate() -> None:
    text = _contract_text()
    _assert_closed_contract(text)
    assert _g175_schema_fields() == dict(G175_INPUT_FIELDS)
    assert len(G175_READY_PREDICATES) == 8
    assert TIMEFRAME_AUTHORITY == (
        ("M15", 900),
        ("H1", 3600),
        ("H4", 14400),
        ("D1", 86400),
    )
    assert "The function is keyword-only and has exactly one argument." in text
    assert "The caller cannot\nsupply a path, source, timeframe selection" in text
    assert "not a subclass or look-alike" in text
    assert "field\nnames and slot order must equal the published G175 24-field result exactly" in text
    assert "All nested records and tuples must have their exact G175 production types" in text


def test_all_adjacent_pair_arithmetic_and_counts_are_closed() -> None:
    assert tuple(vector.name for vector in PAIR_VECTORS) == (
        "exact_match_flat",
        "inside_up",
        "outside_down",
        "shifted_up_close_above",
        "shifted_down_close_below",
        "gap_up_true_range_uses_previous_close",
        "gap_down_true_range_uses_previous_close",
    )
    for vector in PAIR_VECTORS:
        assert type(vector.previous) is tuple and len(vector.previous) == 4
        assert type(vector.current) is tuple and len(vector.current) == 4
        assert _calculated_decimals(vector) == vector.expected_decimals
        assert _calculated_codes(vector) == vector.expected_codes

    gap_vectors = PAIR_VECTORS[-2:]
    assert tuple(vector.expected_decimals[1] for vector in gap_vectors) == (
        "7.00",
        "7.00",
    )
    assert tuple(vector.expected_decimals[2] for vector in gap_vectors) == (
        "25.00",
        "25.00",
    )
    assert all(
        vector.expected_decimals[2] != vector.expected_decimals[1]
        for vector in gap_vectors
    )

    for bar_count in (2, 3, 25, 500):
        assert bar_count - 1 == len(tuple(zip(range(bar_count), range(1, bar_count))))
    assert sum((2 - 1, 3 - 1, 4 - 1, 5 - 1)) == 10

    text = _contract_text()
    assert "must process every accepted bar in the existing G175 order" in text
    assert "must not select a shorter window, drop an endpoint, sort, deduplicate" in text
    assert "Output pair `i` is derived only from input bars\n`i` and `i + 1`" in text


def test_adjacent_pair_identity_and_object_graph_expectations_are_closed() -> None:
    assert tuple(vector.timeframe for vector in ADJACENT_PAIR_IDENTITY_VECTORS) == (
        "M15",
        "H1",
        "H4",
        "D1",
    )
    for vector in ADJACENT_PAIR_IDENTITY_VECTORS:
        _assert_adjacent_pair_identity_vector(vector)

    m15 = ADJACENT_PAIR_IDENTITY_VECTORS[0]
    with pytest.raises(AssertionError):
        _assert_adjacent_pair_identity_vector(
            replace(m15, expected_pair_times=m15.expected_pair_times[:-1])
        )
    with pytest.raises(AssertionError):
        _assert_adjacent_pair_identity_vector(
            replace(
                m15,
                expected_pair_times=(
                    m15.expected_pair_times[1],
                    m15.expected_pair_times[0],
                    m15.expected_pair_times[2],
                ),
            )
        )

    _assert_object_graph_expectations(OBJECT_GRAPH_EXPECTATIONS)
    first = replace(OBJECT_GRAPH_EXPECTATIONS)
    second = replace(OBJECT_GRAPH_EXPECTATIONS)
    assert first == second == OBJECT_GRAPH_EXPECTATIONS
    assert first is not second
    for field_name in OBJECT_GRAPH_EXPECTATIONS.__slots__:
        with pytest.raises(AssertionError):
            _assert_object_graph_expectations(
                replace(OBJECT_GRAPH_EXPECTATIONS, **{field_name: False})
            )

    text = _contract_text()
    assert "The two timestamps are copied from the exact adjacent input bars." in text
    assert "must not modify the input snapshot, any nested record, tuple, or\nstring" in text
    assert "A READY result is a fresh detached frozen object graph." in text
    assert "Every\ntimeframe, pair tuple, and pair record is newly constructed for that call." in text
    assert "Repeated calls with equal exact inputs return equal values but distinct result\nand nested object identities." in text
    assert "Mutating or replacing a caller-owned reference\ncannot alter another result or a later execution." in text
    assert "no\nambient I/O and has no hidden mutable registry or cache." in text


def test_decimal_vectors_lock_both_digit_branches_and_long_coefficients() -> None:
    for vector in FORMAT_VECTORS:
        assert _format_is_accepted(vector) is vector.accepted

    long_value = FORMAT_VECTORS[-1].text
    assert len(Decimal(long_value).as_tuple().digits) == 80
    assert long_value.endswith(".00000000")
    assert _render(Decimal("-0.00"), 2) == "0.00"
    assert _render(Decimal("-0"), 0) == "0"

    text = _contract_text()
    assert "Do not use float" in text
    assert "Do not use float,\n   `Decimal(float_value)`, or an ambient Decimal context." in text
    assert "A result whose exponent or value would require rounding is\n   invalid" in text
    assert "Parse the rendered text again with `Decimal(rendered)`" in text
    assert "For `digits == 0`, both derived\npatterns reject a trailing decimal point" in text
    assert "for `digits > 0`, both require the\npoint and exact fractional width." in text


def test_structure_codes_are_finite_ordered_and_cover_equality_boundaries() -> None:
    assert _structure_rules(_contract_text()) == dict(STRUCTURE_RULES)
    assert tuple(STRUCTURE_RULES) == (
        "direction",
        "range_relation",
        "range_containment",
        "high_relation",
        "low_relation",
        "close_relation",
    )
    assert tuple(rule.rsplit("->", 1)[1].strip() for rule in STRUCTURE_RULES["range_containment"]) == (
        "EXACT_MATCH",
        "INSIDE",
        "OUTSIDE",
        "SHIFTED_UP",
        "SHIFTED_DOWN",
    )
    previous_high = Decimal("110.00")
    previous_low = Decimal("90.00")
    observed = []
    for close_text, expected in CLOSE_BOUNDARY_VECTORS:
        close = Decimal(close_text)
        if close > previous_high:
            code = "ABOVE_PREVIOUS_HIGH"
        elif close == previous_high:
            code = "AT_PREVIOUS_HIGH"
        elif close > previous_low:
            code = "INSIDE_PREVIOUS_RANGE"
        elif close == previous_low:
            code = "AT_PREVIOUS_LOW"
        else:
            code = "BELOW_PREVIOUS_LOW"
        observed.append(code)
        assert code == expected
    assert tuple(observed) == tuple(value for _, value in CLOSE_BOUNDARY_VECTORS)


def test_status_reason_priority_failure_clearing_and_safety_are_exact() -> None:
    assert _status_rows(_contract_text()) == STATUS_REASON_VECTORS
    assert tuple(vector.priority for vector in STATUS_REASON_VECTORS) == tuple(range(1, 9))
    assert len({vector.status for vector in STATUS_REASON_VECTORS}) == 8
    assert len({vector.reason for vector in STATUS_REASON_VECTORS}) == 8
    assert tuple(FAILURE_CLEARED_FIELDS.items()) == (
        ("identity_available", False),
        ("source_contract_version", None),
        ("bundle_schema_version", None),
        ("bundle_id", None),
        ("sequence", None),
        ("canonical_symbol", None),
        ("broker_symbol", None),
        ("reference_time_utc", None),
        ("timeframes", ()),
        ("total_pair_count", 0),
        ("warning_codes", ()),
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
    assert "Each non-READY result contains exactly one reason." in text
    assert "evaluates categories in the table order and stops at the first\nfailure" in text
    assert "exception text and internal state are never exposed" in text


def test_negative_vectors_cover_shape_value_and_category_swap_failures() -> None:
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
        assert vector.original_fields != vector.mutated_fields
        assert vector.expected_priority == 1

    assert type(VALUE_MUTATION_VECTORS[0].invalid_value) is StrictStringSubclass
    assert type(VALUE_MUTATION_VECTORS[1].invalid_value) is list
    assert type(VALUE_MUTATION_VECTORS[2].invalid_value) is object
    assert {vector.expected_priority for vector in VALUE_MUTATION_VECTORS} == set(range(1, 9))
    assert tuple(EXPECTED_VALUE_MUTATION_PRIORITIES) == tuple(
        vector.mutation for vector in VALUE_MUTATION_VECTORS
    )
    assert {vector.mutation for vector in VALUE_MUTATION_VECTORS} >= {
        "subclass",
        "wrong_container",
        "wrong_element",
        "reference_timestamp",
        "bar_timestamp",
        "zero_ohlc",
        "ohlc_relation",
        "history",
        "digits_zero_trailing_point",
        "digits_positive_missing_point",
        "nonfinite_decimal",
        "result_count",
        "result_code",
        "unexpected_exception",
    }
    for vector in VALUE_MUTATION_VECTORS:
        _assert_value_mutation_vector(vector)

    identity_vector = next(
        vector for vector in VALUE_MUTATION_VECTORS if vector.mutation == "bundle_regex"
    )
    timeframe_vector = next(
        vector for vector in VALUE_MUTATION_VECTORS if vector.mutation == "timeframe_order"
    )
    with pytest.raises(AssertionError):
        _assert_value_mutation_vector(
            replace(
                identity_vector,
                expected_priority=timeframe_vector.expected_priority,
                expected_status=timeframe_vector.expected_status,
                expected_reason=timeframe_vector.expected_reason,
            )
        )
    with pytest.raises(AssertionError):
        _assert_value_mutation_vector(
            replace(
                timeframe_vector,
                expected_priority=identity_vector.expected_priority,
                expected_status=identity_vector.expected_status,
                expected_reason=identity_vector.expected_reason,
            )
        )


def test_contract_mutation_probes_reject_predicate_formula_mapping_and_stage_drift() -> None:
    text = _contract_text()
    replacements = (
        (
            "market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,",
            "clock: object,",
        ),
        (
            "| 1 | `contract_version` | `str` |",
            "| 1 | `passed` | `bool` |",
        ),
        ("minimum_bars_per_timeframe = 2", "minimum_bars_per_timeframe = 3"),
        (
            "true_range = max(H - L, abs(H - PC), abs(L - PC))",
            "true_range = H - L",
        ),
        (
            're.compile(r"^(?:0|[1-9][0-9]*)$", re.ASCII)',
            're.compile(r"^(?:0|[1-9][0-9]*)\\.?$", re.ASCII)',
        ),
        (
            'rf"^(?:0|[1-9][0-9]*)\\.[0-9]{{{digits}}}$"',
            'rf"^(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$"',
        ),
        (
            "Every bar open, high, low, and close is strictly greater\n   than zero.",
            "Every bar open, high, low, and close is nonnegative.",
        ),
        (
            "H == PH and L == PL                 -> EXACT_MATCH",
            "H <= PH and L >= PL                 -> EXACT_MATCH",
        ),
        (
            "`GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_IDENTITY_INVALID`",
            "`GOLD_VOLATILITY_STRUCTURE_DECIMAL_INPUT_INVALID`",
        ),
        (
            "7. only then, separately contracted W7 deterministic analysis.",
            "7. only then, separately contracted W7 deterministic analysis.\n8. runtime activation.",
        ),
    )
    for original, replacement in replacements:
        assert original in text
        mutated = text.replace(original, replacement, 1)
        with pytest.raises(AssertionError):
            _assert_closed_contract(mutated)


def test_staged_delivery_and_isolation_remain_closed() -> None:
    text = _contract_text()
    assert _staged_delivery(text) == STAGED_DELIVERY
    assert "Static vectors are tests-only evidence." in text
    assert "They do not prove production types,\nbuilder behavior, integration, activation, or verification." in text
    assert "Contract is not tests, tests are not\nimplementation" in text
    assert "W6 remains `TESTS_ONLY`." in text
    assert "W5 remains verified only for ReplayRunner v1 canonical diagnostics." in text
    assert "Economic-window facts, ReplayRunner W6 staging, and W7-W21 remain separate" in text
    assert "Reader activation, real MT4, EA calls, orders, execution, Demo activation,\n  Live activation, and trading remain prohibited." in text
    for prohibited in (
        "file reader",
        "source adapter",
        "DataQualityGate",
        "fixture boundary",
        "network",
        "ambient clock",
        "API",
        "CLI",
        "frontend",
        "environment",
        "database",
        "cache",
        "ReplayRunner",
    ):
        assert prohibited in text


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
    assert not any(module == "app" or module.startswith("app.") for module in imported_modules)
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "build_canonical_gold_volatility_structure_facts_v1" not in function_names
    assert "canonical_gold_volatility_structure_facts" not in imported_modules
    assert all(ord(character) < 128 for character in source)
