from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
from types import MappingProxyType

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_gold_market_facts_snapshot_v1_contract.md"
)
TEST_PATH = Path(__file__).resolve()


@dataclass(frozen=True, slots=True)
class FieldVector:
    field: str
    exact_type: str
    authority: str | None = None


@dataclass(frozen=True, slots=True)
class TimeframeVector:
    timeframe: str
    period_seconds: int


@dataclass(frozen=True, slots=True)
class StatusReasonVector:
    status_code: str
    passed: bool
    reason_code: str | None
    identity_available: bool
    timeframe_count: int


@dataclass(frozen=True, slots=True)
class NormalizationRuleVector:
    name: str
    exact_step: str


@dataclass(frozen=True, slots=True)
class InvalidRecordShapeVector:
    name: str
    record_name: str
    expected_fields: tuple[str, ...]
    observed_fields: tuple[str, ...]
    accepted: bool


@dataclass(frozen=True, slots=True)
class InvalidTypeShapeVector:
    name: str
    value_path: str
    expected_type: type[object] | str
    observed_type: type[object] | str
    accepted: bool


@dataclass(frozen=True, slots=True)
class InvalidTimeframeShapeVector:
    name: str
    expected_timeframes: tuple[str, ...]
    observed_timeframes: tuple[str, ...]
    accepted: bool


class _StringSubclass(str):
    pass


SOURCE_FIELDS = (
    FieldVector("contract_version", "built-in `str`", "Fixed `1.0`"),
    FieldVector(
        "bundle_schema_version",
        "built-in `str`",
        "Accepted manifest; fixed `1.0`",
    ),
    FieldVector("bundle_id", "built-in `str`", "Accepted manifest identity"),
    FieldVector("sequence", "built-in `int`", "Accepted manifest identity"),
    FieldVector("canonical_symbol", "built-in `str`", "Fixed `XAUUSD`"),
    FieldVector("broker_symbol", "built-in `str`", "Fixed `GOLD` in v1"),
    FieldVector(
        "reference_time_utc",
        "built-in `str`",
        "Server-owned validation attempt",
    ),
    FieldVector(
        "policy_profile_version",
        "built-in `str`",
        "Server-owned fixed profile",
    ),
    FieldVector(
        "upstream_evidence",
        "`CanonicalGoldUpstreamEvidenceV1`",
        "Same accepted attempt",
    ),
    FieldVector(
        "live_tick",
        "`CanonicalGoldTickSourceV1`",
        "Accepted `live_tick.json`",
    ),
    FieldVector(
        "bars_generated_at_utc",
        "built-in `str`",
        "Accepted `latest_bars.json`",
    ),
    FieldVector(
        "timeframes",
        "exact tuple of four `CanonicalGoldTimeframeSourceV1`",
        "Accepted `latest_bars.json`",
    ),
    FieldVector(
        "symbol_spec",
        "`CanonicalGoldSymbolSpecSourceV1`",
        "Accepted `symbol_spec.json`",
    ),
)

RESULT_FIELDS = (
    FieldVector("contract_version", "built-in `str`, exactly `1.0`"),
    FieldVector("passed", "built-in `bool`"),
    FieldVector("status_code", "built-in `str`"),
    FieldVector("reason_codes", "built-in `tuple[str, ...]`"),
    FieldVector("warning_codes", "built-in `tuple[str, ...]`"),
    FieldVector("identity_available", "built-in `bool`"),
    FieldVector("bundle_schema_version", "built-in `str` or `None`"),
    FieldVector("bundle_id", "built-in `str` or `None`"),
    FieldVector("sequence", "built-in `int` or `None`"),
    FieldVector("canonical_symbol", "built-in `str` or `None`"),
    FieldVector("broker_symbol", "built-in `str` or `None`"),
    FieldVector("reference_time_utc", "built-in `str` or `None`"),
    FieldVector("quote", "`CanonicalGoldQuoteFactsV1` or `None`"),
    FieldVector(
        "timeframes",
        "exact built-in tuple: four `CanonicalGoldTimeframeFactsV1` records "
        "when passed; empty when non-passed",
    ),
    FieldVector("symbol_spec", "`CanonicalGoldSymbolFactsV1` or `None`"),
    FieldVector("freshness", "`CanonicalGoldFreshnessFactsV1` or `None`"),
    FieldVector("read_only", "built-in `bool`"),
    FieldVector("demo_only", "built-in `bool`"),
    FieldVector("is_tradable", "built-in `bool`"),
    FieldVector("can_execute", "built-in `bool`"),
    FieldVector("is_trading_permission", "built-in `bool`"),
    FieldVector("is_execution_instruction", "built-in `bool`"),
    FieldVector("allowed_to_call_ea", "built-in `bool`"),
    FieldVector("allowed_to_modify_risk", "built-in `bool`"),
)

NESTED_FIELDS = MappingProxyType(
    {
        "CanonicalGoldUpstreamEvidenceV1": (
            FieldVector("reader_passed", "built-in `bool`", "Exactly `true`"),
            FieldVector(
                "reader_status_code",
                "built-in `str`",
                "`CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID`",
            ),
            FieldVector(
                "value_status_code",
                "built-in `str`",
                "`CANONICAL_MT4_BUNDLE_V1_VALUE_VALID`",
            ),
            FieldVector(
                "data_quality_passed",
                "built-in `bool`",
                "Exactly `true`",
            ),
            FieldVector(
                "data_quality_status_code",
                "built-in `str`",
                "`CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED`",
            ),
            FieldVector(
                "ready_for_readonly_analysis",
                "built-in `bool`",
                "Exactly `true`",
            ),
            FieldVector(
                "warning_codes",
                "exact built-in `tuple[str, ...]`",
                "Exactly empty",
            ),
            FieldVector(
                "same_attempt_identity_bound",
                "built-in `bool`",
                "Exactly `true`",
            ),
        ),
        "CanonicalGoldTickSourceV1": (
            FieldVector("bid", "built-in `int` or built-in `float`"),
            FieldVector("ask", "built-in `int` or built-in `float`"),
            FieldVector("spread", "built-in `int` or built-in `float`"),
            FieldVector("spread_points", "built-in `int`"),
            FieldVector("digits", "built-in `int`"),
            FieldVector("point", "built-in `int` or built-in `float`"),
            FieldVector("tick_time_utc", "built-in `str`"),
        ),
        "CanonicalGoldTimeframeSourceV1": (
            FieldVector("timeframe", "built-in `str`"),
            FieldVector("period_seconds", "built-in `int`"),
            FieldVector(
                "bars",
                "exact built-in `tuple[CanonicalGoldBarSourceV1, ...]`",
            ),
        ),
        "CanonicalGoldBarSourceV1": (
            FieldVector("open_time_utc", "built-in `str`"),
            FieldVector("open", "built-in `int` or built-in `float`"),
            FieldVector("high", "built-in `int` or built-in `float`"),
            FieldVector("low", "built-in `int` or built-in `float`"),
            FieldVector("close", "built-in `int` or built-in `float`"),
            FieldVector("tick_volume", "built-in `int`"),
            FieldVector("spread_points", "built-in `int`"),
        ),
        "CanonicalGoldSymbolSpecSourceV1": (
            FieldVector("spec_time_utc", "built-in `str`"),
            FieldVector("digits", "built-in `int`"),
            FieldVector("point", "built-in `int` or built-in `float`"),
            FieldVector("tick_size", "built-in `int` or built-in `float`"),
            FieldVector("tick_value", "built-in `int` or built-in `float`"),
            FieldVector("contract_size", "built-in `int` or built-in `float`"),
            FieldVector("min_lot", "built-in `int` or built-in `float`"),
            FieldVector("lot_step", "built-in `int` or built-in `float`"),
            FieldVector("max_lot", "built-in `int` or built-in `float`"),
            FieldVector("base_currency", "built-in `str`"),
            FieldVector("profit_currency", "built-in `str`"),
            FieldVector("margin_currency", "built-in `str`"),
            FieldVector("trade_mode_readonly_label", "built-in `str`"),
            FieldVector("session_status_readonly_label", "built-in `str`"),
        ),
        "CanonicalGoldQuoteFactsV1": (
            FieldVector("bid_decimal", "built-in `str`"),
            FieldVector("ask_decimal", "built-in `str`"),
            FieldVector("spread_decimal", "built-in `str`"),
            FieldVector("spread_points", "built-in `int`"),
            FieldVector("digits", "built-in `int`"),
            FieldVector("point_decimal", "built-in `str`"),
            FieldVector("tick_time_utc", "built-in `str`"),
        ),
        "CanonicalGoldTimeframeFactsV1": (
            FieldVector("timeframe", "built-in `str`"),
            FieldVector("period_seconds", "built-in `int`"),
            FieldVector(
                "bars",
                "exact built-in `tuple[CanonicalGoldBarFactsV1, ...]`",
            ),
        ),
        "CanonicalGoldBarFactsV1": (
            FieldVector("open_time_utc", "built-in `str`"),
            FieldVector("open_decimal", "built-in `str`"),
            FieldVector("high_decimal", "built-in `str`"),
            FieldVector("low_decimal", "built-in `str`"),
            FieldVector("close_decimal", "built-in `str`"),
            FieldVector("tick_volume", "built-in `int`"),
            FieldVector("spread_points", "built-in `int`"),
        ),
        "CanonicalGoldSymbolFactsV1": (
            FieldVector("spec_time_utc", "built-in `str`"),
            FieldVector("digits", "built-in `int`"),
            FieldVector("point_decimal", "built-in `str`"),
            FieldVector("tick_size_decimal", "built-in `str`"),
            FieldVector("tick_value_decimal", "built-in `str`"),
            FieldVector("contract_size_decimal", "built-in `str`"),
            FieldVector("min_lot_decimal", "built-in `str`"),
            FieldVector("lot_step_decimal", "built-in `str`"),
            FieldVector("max_lot_decimal", "built-in `str`"),
            FieldVector("base_currency", "built-in `str`"),
            FieldVector("profit_currency", "built-in `str`"),
            FieldVector("margin_currency", "built-in `str`"),
            FieldVector("trade_mode_readonly_label", "built-in `str`"),
            FieldVector("session_status_readonly_label", "built-in `str`"),
        ),
        "CanonicalGoldFreshnessFactsV1": (
            FieldVector("tick_age_microseconds", "built-in `int`"),
            FieldVector("bars_payload_age_microseconds", "built-in `int`"),
            FieldVector("symbol_spec_age_microseconds", "built-in `int`"),
        ),
    }
)

TABLE_FRAGMENTS = MappingProxyType(
    {
        "CanonicalGoldUpstreamEvidenceV1": (
            "`CanonicalGoldUpstreamEvidenceV1` has exactly these fields"
        ),
        "CanonicalGoldTickSourceV1": (
            "`CanonicalGoldTickSourceV1` has exactly these fields"
        ),
        "CanonicalGoldTimeframeSourceV1": (
            "`CanonicalGoldTimeframeSourceV1` records. Their `timeframe` values"
        ),
        "CanonicalGoldBarSourceV1": (
            "`CanonicalGoldBarSourceV1` records. Each bar has exactly these fields"
        ),
        "CanonicalGoldSymbolSpecSourceV1": (
            "`CanonicalGoldSymbolSpecSourceV1` has exactly these fields"
        ),
        "CanonicalGoldQuoteFactsV1": (
            "`CanonicalGoldQuoteFactsV1` has exactly these fields"
        ),
        "CanonicalGoldTimeframeFactsV1": (
            "`CanonicalGoldTimeframeFactsV1` records. Their"
        ),
        "CanonicalGoldBarFactsV1": (
            "`CanonicalGoldBarFactsV1` records. Each bar has"
        ),
        "CanonicalGoldSymbolFactsV1": (
            "`CanonicalGoldSymbolFactsV1` has exactly these fields"
        ),
        "CanonicalGoldFreshnessFactsV1": (
            "`CanonicalGoldFreshnessFactsV1` has exactly these fields"
        ),
    }
)

TIMEFRAMES = (
    TimeframeVector("M15", 900),
    TimeframeVector("H1", 3600),
    TimeframeVector("H4", 14400),
    TimeframeVector("D1", 86400),
)

STATUS_REASON_VECTORS = (
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_READY",
        True,
        None,
        True,
        4,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_INPUT_INVALID",
        False,
        "GOLD_MARKET_FACTS_SOURCE_TYPE_INVALID",
        False,
        0,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_AUTHORITY_INVALID",
        False,
        "GOLD_MARKET_FACTS_SOURCE_AUTHORITY_INVALID",
        False,
        0,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_UPSTREAM_BLOCKED",
        False,
        "GOLD_MARKET_FACTS_UPSTREAM_NOT_READY",
        False,
        0,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_UPSTREAM_BLOCKED",
        False,
        "GOLD_MARKET_FACTS_UPSTREAM_WARNINGS_REJECTED",
        False,
        0,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_IDENTITY_INVALID",
        False,
        "GOLD_MARKET_FACTS_IDENTITY_INVALID",
        False,
        0,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_VALUE_INVALID",
        False,
        "GOLD_MARKET_FACTS_TICK_INVALID",
        False,
        0,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_VALUE_INVALID",
        False,
        "GOLD_MARKET_FACTS_BARS_INVALID",
        False,
        0,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_VALUE_INVALID",
        False,
        "GOLD_MARKET_FACTS_SYMBOL_SPEC_INVALID",
        False,
        0,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_VALUE_INVALID",
        False,
        "GOLD_MARKET_FACTS_FRESHNESS_INVALID",
        False,
        0,
    ),
    StatusReasonVector(
        "CANONICAL_GOLD_MARKET_FACTS_SAFE_FAILURE",
        False,
        "GOLD_MARKET_FACTS_EXCEPTION_SANITIZED",
        False,
        0,
    ),
)

RESULT_SAFETY_FLAGS = MappingProxyType(
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

FAILURE_IDENTITY = MappingProxyType(
    {
        "identity_available": False,
        "bundle_schema_version": None,
        "bundle_id": None,
        "sequence": None,
        "canonical_symbol": None,
        "broker_symbol": None,
        "reference_time_utc": None,
        "quote": None,
        "timeframes": (),
        "symbol_spec": None,
        "freshness": None,
    }
)

NORMALIZATION_RULES = (
    NormalizationRuleVector(
        "strict_source_type",
        "Accept a numeric source value only when `type(value) is int` or "
        "`type(value) is float`. Reject `bool`, subclasses, strings, all other "
        "numeric types, and a float for which `math.isfinite(value)` is false.",
    ),
    NormalizationRuleVector(
        "single_decimal_conversion",
        "Convert the value exactly once with `Decimal(str(value))`. Do not use "
        "`Decimal(value)`, `repr(value)`, prior formatting, binary float "
        "arithmetic, a locale, or any alternate conversion path. Reject a "
        "non-finite Decimal and reject signed zero (`decimal_value.is_zero()` "
        "and `decimal_value.is_signed()`).",
    ),
    NormalizationRuleVector(
        "local_decimal_context",
        "Perform Decimal arithmetic in a fresh local context with `prec=64`, "
        "`rounding=ROUND_HALF_EVEN`, `Emin=-999999`, `Emax=999999`, "
        "`capitals=1`, and `clamp=0`. Trap `InvalidOperation`, "
        "`DivisionByZero`, and `Overflow`. Disable every other trap. Clear all "
        "flags before every arithmetic operation and reject the source if any "
        "context flag is set afterward. The configured rounding mode never "
        "grants permission to round: `Inexact` or `Rounded` is always a failure.",
    ),
    NormalizationRuleVector(
        "price_quantum",
        "Compute `price_quantum` exactly as `Decimal(1).scaleb(-digits)`. The "
        "exact converted tick `point` and symbol `point` must both equal this "
        "quantum, and tick and symbol `digits` must be equal. A price Decimal "
        "is representable only when its tuple exponent is greater than or equal "
        "to `-digits`; a value with more fractional places fails rather than "
        "being quantized.",
    ),
    NormalizationRuleVector(
        "fixed_point_price_output",
        "The price fields are tick `bid`, `ask`, `spread`, and `point`; bar "
        "`open`, `high`, `low`, and `close`; and symbol `point` and `tick_size`. "
        "Emit each with `format(decimal_value, f\".{digits}f\")`. The output must "
        "contain exactly `digits` digits after the decimal point, including "
        "trailing zeroes, and no exponent or leading plus sign. When `digits` "
        "is zero, the output contains no decimal point.",
    ),
    NormalizationRuleVector(
        "fixed_point_non_price_output",
        "For `tick_value`, `contract_size`, `min_lot`, `lot_step`, and "
        "`max_lot`, first use `format(decimal_value, \"f\")`, remove trailing "
        "zeroes only from the fractional part, and then remove a trailing "
        "decimal point. An exact zero is emitted as `0`; every other integral "
        "value has no decimal point. The output has no exponent, leading plus "
        "sign, or unnecessary trailing fractional zero. Field positivity and "
        "ordering rules remain those of Bundle v1.",
    ),
    NormalizationRuleVector(
        "exact_spread_identity",
        "Convert `spread_points` exactly once with "
        "`Decimal(str(spread_points))`. In the same exact Decimal context, "
        "require `spread == ask - bid` and "
        "`spread == spread_points_decimal * point`. Both comparisons are exact. "
        "No epsilon, tolerance, binary float operation, or value-changing "
        "conversion is permitted.",
    ),
    NormalizationRuleVector(
        "ambiguity_fails_closed",
        "Any conversion, context, precision, scale, comparison, or formatting "
        "ambiguity fails closed. The projector must not round, sort, repair, "
        "substitute, retry, or use a fallback algorithm.",
    ),
)

_SOURCE_FIELD_NAMES = tuple(vector.field for vector in SOURCE_FIELDS)
_RESULT_FIELD_NAMES = tuple(vector.field for vector in RESULT_FIELDS)
_QUOTE_FIELD_NAMES = tuple(
    vector.field for vector in NESTED_FIELDS["CanonicalGoldQuoteFactsV1"]
)
_BAR_FIELD_NAMES = tuple(
    vector.field for vector in NESTED_FIELDS["CanonicalGoldBarFactsV1"]
)
_TIMEFRAME_NAMES = tuple(vector.timeframe for vector in TIMEFRAMES)

INVALID_RECORD_SHAPE_VECTORS = (
    InvalidRecordShapeVector(
        "missing_field",
        "CanonicalGoldMarketFactsSourceV1",
        _SOURCE_FIELD_NAMES,
        _SOURCE_FIELD_NAMES[:-1],
        False,
    ),
    InvalidRecordShapeVector(
        "extra_field",
        "CanonicalGoldMarketFactsSnapshotV1",
        _RESULT_FIELD_NAMES,
        (*_RESULT_FIELD_NAMES, "unexpected_field"),
        False,
    ),
    InvalidRecordShapeVector(
        "reordered_field",
        "CanonicalGoldQuoteFactsV1",
        _QUOTE_FIELD_NAMES,
        (_QUOTE_FIELD_NAMES[1], _QUOTE_FIELD_NAMES[0], *_QUOTE_FIELD_NAMES[2:]),
        False,
    ),
    InvalidRecordShapeVector(
        "duplicate_field",
        "CanonicalGoldBarFactsV1",
        _BAR_FIELD_NAMES,
        (*_BAR_FIELD_NAMES, "spread_points"),
        False,
    ),
    InvalidRecordShapeVector(
        "aliased_field",
        "CanonicalGoldMarketFactsSnapshotV1",
        _RESULT_FIELD_NAMES,
        tuple(
            "reference_time" if field == "reference_time_utc" else field
            for field in _RESULT_FIELD_NAMES
        ),
        False,
    ),
    InvalidRecordShapeVector(
        "case_changed_field",
        "CanonicalGoldMarketFactsSourceV1",
        _SOURCE_FIELD_NAMES,
        tuple(
            "BUNDLE_ID" if field == "bundle_id" else field
            for field in _SOURCE_FIELD_NAMES
        ),
        False,
    ),
)

INVALID_TYPE_SHAPE_VECTORS = (
    InvalidTypeShapeVector(
        "subclassed_value",
        "CanonicalGoldTickSourceV1.tick_time_utc",
        str,
        _StringSubclass,
        False,
    ),
    InvalidTypeShapeVector(
        "wrong_container",
        "CanonicalGoldMarketFactsSnapshotV1.timeframes",
        tuple,
        list,
        False,
    ),
    InvalidTypeShapeVector(
        "wrong_element_type",
        "CanonicalGoldMarketFactsSnapshotV1.timeframes[*]",
        "CanonicalGoldTimeframeFactsV1",
        "CanonicalGoldBarFactsV1",
        False,
    ),
)

INVALID_TIMEFRAME_SHAPE_VECTORS = (
    InvalidTimeframeShapeVector(
        "wrong_timeframe_length",
        _TIMEFRAME_NAMES,
        _TIMEFRAME_NAMES[:-1],
        False,
    ),
    InvalidTimeframeShapeVector(
        "wrong_timeframe_order",
        _TIMEFRAME_NAMES,
        ("M15", "H4", "H1", "D1"),
        False,
    ),
)

INVALID_SHAPE_VECTORS = (
    *INVALID_RECORD_SHAPE_VECTORS,
    *INVALID_TYPE_SHAPE_VECTORS,
    *INVALID_TIMEFRAME_SHAPE_VECTORS,
)

CALLER_FORBIDDEN_OVERRIDES = (
    "a path or filename",
    "a source mode",
    "a reference time or clock",
    "freshness or future-skew policy",
    "canonical or broker symbol mapping",
    "expected bundle identity",
    "a validator, reader, Gate, dependency, or fallback",
    "an expected outcome or oracle",
    "account, strategy, risk, execution, or trading state",
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _strip_code(value: str) -> str:
    if value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def _table_after_fragment(
    text: str,
    fragment: str,
) -> tuple[FieldVector, ...]:
    lines = text.splitlines()
    fragment_index = next(
        index for index, line in enumerate(lines) if fragment in line
    )
    header_index = next(
        index
        for index in range(fragment_index + 1, len(lines))
        if lines[index].startswith("| Order | Field | Exact type")
    )
    rows: list[FieldVector] = []
    for line in lines[header_index + 2 :]:
        cells = tuple(cell.strip() for cell in line.split("|")[1:-1])
        if not cells or not cells[0].isdigit():
            break
        expected_order = len(rows) + 1
        assert int(cells[0]) == expected_order
        rows.append(
            FieldVector(
                field=_strip_code(cells[1]),
                exact_type=cells[2],
                authority=cells[3] if len(cells) == 4 else None,
            )
        )
    return tuple(rows)


def _status_rows(text: str) -> tuple[tuple[str, bool, str | None], ...]:
    lines = text.splitlines()
    header_index = lines.index("| Status | `passed` | Exact reason |")
    rows: list[tuple[str, bool, str | None]] = []
    for line in lines[header_index + 2 :]:
        cells = tuple(cell.strip() for cell in line.split("|")[1:-1])
        if len(cells) != 3 or not cells[0].startswith("`"):
            break
        reason = None if cells[2] == "none" else _strip_code(cells[2])
        rows.append(
            (
                _strip_code(cells[0]),
                _strip_code(cells[1]) == "true",
                reason,
            )
        )
    return tuple(rows)


def _numbered_steps_after_heading(
    text: str,
    heading: str,
) -> tuple[str, ...]:
    lines = text.splitlines()
    heading_index = lines.index(heading)
    steps: list[str] = []
    current: list[str] = []
    for line in lines[heading_index + 1 :]:
        if line.startswith("## "):
            break
        marker, separator, first_text = line.partition(". ")
        if separator and marker.isdigit():
            if current:
                steps.append(" ".join(current))
            current = [first_text.strip()]
        elif current and (line.startswith("   ") or not line):
            if line.strip():
                current.append(line.strip())
        elif current:
            break
    if current:
        steps.append(" ".join(current))
    return tuple(steps)


def test_contract_vectors_are_immutable_and_have_exact_top_level_fields() -> None:
    assert len(SOURCE_FIELDS) == 13
    assert len(RESULT_FIELDS) == 24
    assert tuple(vector.field for vector in SOURCE_FIELDS) == (
        "contract_version",
        "bundle_schema_version",
        "bundle_id",
        "sequence",
        "canonical_symbol",
        "broker_symbol",
        "reference_time_utc",
        "policy_profile_version",
        "upstream_evidence",
        "live_tick",
        "bars_generated_at_utc",
        "timeframes",
        "symbol_spec",
    )
    assert tuple(vector.field for vector in RESULT_FIELDS) == (
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
    with pytest.raises(FrozenInstanceError):
        setattr(SOURCE_FIELDS[0], "field", "changed")
    with pytest.raises(FrozenInstanceError):
        setattr(NORMALIZATION_RULES[0], "exact_step", "changed")
    with pytest.raises(FrozenInstanceError):
        setattr(INVALID_SHAPE_VECTORS[0], "accepted", True)
    with pytest.raises(TypeError):
        RESULT_SAFETY_FLAGS["read_only"] = False  # type: ignore[index]


def test_contract_document_matches_exact_source_and_result_vectors() -> None:
    text = _contract_text()
    assert _table_after_fragment(
        text,
        "`CanonicalGoldMarketFactsSourceV1` has exactly these fields",
    ) == SOURCE_FIELDS
    assert _table_after_fragment(
        text,
        "`CanonicalGoldMarketFactsSnapshotV1` has exactly these fields",
    ) == RESULT_FIELDS


def test_all_nested_source_and_result_schemas_are_exact() -> None:
    text = _contract_text()
    assert tuple(NESTED_FIELDS) == (
        "CanonicalGoldUpstreamEvidenceV1",
        "CanonicalGoldTickSourceV1",
        "CanonicalGoldTimeframeSourceV1",
        "CanonicalGoldBarSourceV1",
        "CanonicalGoldSymbolSpecSourceV1",
        "CanonicalGoldQuoteFactsV1",
        "CanonicalGoldTimeframeFactsV1",
        "CanonicalGoldBarFactsV1",
        "CanonicalGoldSymbolFactsV1",
        "CanonicalGoldFreshnessFactsV1",
    )
    for record_name, expected_fields in NESTED_FIELDS.items():
        assert _table_after_fragment(
            text,
            TABLE_FRAGMENTS[record_name],
        ) == expected_fields
    assert tuple(len(fields) for fields in NESTED_FIELDS.values()) == (
        8,
        7,
        3,
        7,
        14,
        7,
        3,
        7,
        14,
        3,
    )


def test_server_owned_authority_and_caller_boundary_are_frozen() -> None:
    text = _contract_text()
    assert SOURCE_FIELDS[0].authority == "Fixed `1.0`"
    assert SOURCE_FIELDS[4].authority == "Fixed `XAUUSD`"
    assert SOURCE_FIELDS[5].authority == "Fixed `GOLD` in v1"
    assert SOURCE_FIELDS[8].authority == "Same accepted attempt"
    assert "`canonical_gold_market_facts_policy_v1`" in text
    assert "atomically from the same successful" in text
    assert "server-owned" in text
    assert "Type construction\nalone is not authority." in text
    for forbidden_override in CALLER_FORBIDDEN_OVERRIDES:
        assert forbidden_override in text
    assert "G151 diagnostics summary is therefore not a W6 calculation input" in text
    assert "G153 returns the G151 diagnostics summary" in text


def test_timeframe_vectors_lock_ready_and_non_passed_shapes() -> None:
    text = _contract_text()
    assert tuple((item.timeframe, item.period_seconds) for item in TIMEFRAMES) == (
        ("M15", 900),
        ("H1", 3600),
        ("H4", 14400),
        ("D1", 86400),
    )
    assert "containing exactly four `CanonicalGoldTimeframeFactsV1` records" in text
    assert "`M15`, `H1`, `H4`, and `D1` in that order" in text
    assert "`900`, `3600`, `14400`, and `86400` in" in text
    assert "Every non-passed result uses the exact empty built-in tuple" in text
    assert "Any other tuple length, timeframe order, container type, or element" in text
    ready = STATUS_REASON_VECTORS[0]
    assert (ready.passed, ready.identity_available, ready.timeframe_count) == (
        True,
        True,
        4,
    )
    assert all(
        (not vector.passed)
        and (not vector.identity_available)
        and vector.timeframe_count == 0
        for vector in STATUS_REASON_VECTORS[1:]
    )


def test_decimal_normalization_rules_are_exact_and_have_no_fallback() -> None:
    text = _contract_text()
    assert tuple(rule.name for rule in NORMALIZATION_RULES) == (
        "strict_source_type",
        "single_decimal_conversion",
        "local_decimal_context",
        "price_quantum",
        "fixed_point_price_output",
        "fixed_point_non_price_output",
        "exact_spread_identity",
        "ambiguity_fails_closed",
    )
    expected_steps = tuple(rule.exact_step for rule in NORMALIZATION_RULES)
    assert _numbered_steps_after_heading(
        text,
        "## 8. Deterministic Normalization",
    ) == expected_steps

    semantically_inverted = text.replace(
        "Do not use\n   `Decimal(value)`",
        "Use\n   `Decimal(value)`",
        1,
    )
    assert semantically_inverted != text
    assert _numbered_steps_after_heading(
        semantically_inverted,
        "## 8. Deterministic Normalization",
    ) != expected_steps
    assert "This is the only permitted normalization algorithm." in text
    assert "The projector does not read the clock." in text


def test_status_reason_warning_identity_and_safety_vectors_are_exact() -> None:
    text = _contract_text()
    expected_status_rows = tuple(
        (vector.status_code, vector.passed, vector.reason_code)
        for vector in STATUS_REASON_VECTORS
    )
    assert len(expected_status_rows) == 11
    assert len(set(expected_status_rows)) == 11
    assert _status_rows(text) == expected_status_rows
    assert "`warning_codes` is always the exact empty tuple in v1" in text
    assert tuple(FAILURE_IDENTITY.items()) == (
        ("identity_available", False),
        ("bundle_schema_version", None),
        ("bundle_id", None),
        ("sequence", None),
        ("canonical_symbol", None),
        ("broker_symbol", None),
        ("reference_time_utc", None),
        ("quote", None),
        ("timeframes", ()),
        ("symbol_spec", None),
        ("freshness", None),
    )
    for field, value in FAILURE_IDENTITY.items():
        rendered = "None" if value is None else "false" if value is False else "()"
        assert f"`{field}={rendered}`" in text
    expected_safety = (
        ("read_only", True),
        ("demo_only", True),
        ("is_tradable", False),
        ("can_execute", False),
        ("is_trading_permission", False),
        ("is_execution_instruction", False),
        ("allowed_to_call_ea", False),
        ("allowed_to_modify_risk", False),
    )
    assert tuple(RESULT_SAFETY_FLAGS.items()) == expected_safety
    for field, value in expected_safety:
        assert f"| `{field}` | `{'true' if value else 'false'}` |" in text


def test_invalid_shape_vectors_are_complete_and_fail_closed() -> None:
    text = _contract_text()
    assert len(INVALID_SHAPE_VECTORS) == 11
    assert len({vector.name for vector in INVALID_SHAPE_VECTORS}) == 11
    assert all(vector.accepted is False for vector in INVALID_SHAPE_VECTORS)

    assert tuple(
        (
            vector.name,
            vector.record_name,
            vector.expected_fields,
            vector.observed_fields,
        )
        for vector in INVALID_RECORD_SHAPE_VECTORS
    ) == (
        (
            "missing_field",
            "CanonicalGoldMarketFactsSourceV1",
            _SOURCE_FIELD_NAMES,
            _SOURCE_FIELD_NAMES[:-1],
        ),
        (
            "extra_field",
            "CanonicalGoldMarketFactsSnapshotV1",
            _RESULT_FIELD_NAMES,
            (*_RESULT_FIELD_NAMES, "unexpected_field"),
        ),
        (
            "reordered_field",
            "CanonicalGoldQuoteFactsV1",
            _QUOTE_FIELD_NAMES,
            (_QUOTE_FIELD_NAMES[1], _QUOTE_FIELD_NAMES[0], *_QUOTE_FIELD_NAMES[2:]),
        ),
        (
            "duplicate_field",
            "CanonicalGoldBarFactsV1",
            _BAR_FIELD_NAMES,
            (*_BAR_FIELD_NAMES, "spread_points"),
        ),
        (
            "aliased_field",
            "CanonicalGoldMarketFactsSnapshotV1",
            _RESULT_FIELD_NAMES,
            tuple(
                "reference_time" if field == "reference_time_utc" else field
                for field in _RESULT_FIELD_NAMES
            ),
        ),
        (
            "case_changed_field",
            "CanonicalGoldMarketFactsSourceV1",
            _SOURCE_FIELD_NAMES,
            tuple(
                "BUNDLE_ID" if field == "bundle_id" else field
                for field in _SOURCE_FIELD_NAMES
            ),
        ),
    )
    assert all(
        type(vector.expected_fields) is tuple
        and type(vector.observed_fields) is tuple
        and vector.expected_fields != vector.observed_fields
        for vector in INVALID_RECORD_SHAPE_VECTORS
    )

    assert tuple(
        (
            vector.name,
            vector.value_path,
            vector.expected_type,
            vector.observed_type,
        )
        for vector in INVALID_TYPE_SHAPE_VECTORS
    ) == (
        (
            "subclassed_value",
            "CanonicalGoldTickSourceV1.tick_time_utc",
            str,
            _StringSubclass,
        ),
        (
            "wrong_container",
            "CanonicalGoldMarketFactsSnapshotV1.timeframes",
            tuple,
            list,
        ),
        (
            "wrong_element_type",
            "CanonicalGoldMarketFactsSnapshotV1.timeframes[*]",
            "CanonicalGoldTimeframeFactsV1",
            "CanonicalGoldBarFactsV1",
        ),
    )
    assert issubclass(_StringSubclass, str) and _StringSubclass is not str
    assert all(
        vector.expected_type != vector.observed_type
        for vector in INVALID_TYPE_SHAPE_VECTORS
    )

    assert tuple(
        (
            vector.name,
            vector.expected_timeframes,
            vector.observed_timeframes,
        )
        for vector in INVALID_TIMEFRAME_SHAPE_VECTORS
    ) == (
        ("wrong_timeframe_length", _TIMEFRAME_NAMES, _TIMEFRAME_NAMES[:-1]),
        ("wrong_timeframe_order", _TIMEFRAME_NAMES, ("M15", "H4", "H1", "D1")),
    )
    assert all(
        type(vector.expected_timeframes) is tuple
        and type(vector.observed_timeframes) is tuple
        and vector.expected_timeframes != vector.observed_timeframes
        for vector in INVALID_TIMEFRAME_SHAPE_VECTORS
    )

    normalized_text = " ".join(text.split())
    assert (
        "Every nested source and result record named in Sections 6 and 7 must "
        "be the exact frozen, slotted dataclass type specified by this contract. "
        "Subclasses, mappings, lists, iterators, wrong tuple element types, and "
        "records with missing, extra, duplicated, aliased, case-changed, or "
        "reordered fields fail closed."
    ) in normalized_text
    assert "Subclasses are invalid. `bool` is not an `int`. Lists are not tuples." in text
    assert "Unknown, additional,\nduplicate, reordered, subclassed, or contradictory" in text


def test_vectors_do_not_claim_projector_adapter_or_runtime_delivery() -> None:
    text = _contract_text()
    assert "W6 remains `CONTRACT_ONLY`" in text
    assert "It does not implement that boundary." in text
    assert "immutable tests-only contract vectors for this snapshot" in text
    assert "a pure-memory projector implementation" in text
    assert "a separately reviewed server-owned same-attempt source adapter" in text
    assert "offline canonical-fixture integration evidence" in text
    assert "deterministic non-activating verification" in text
    assert "No stage may silently include the next one." in text
    assert "No W7 opportunity assessment may be added to this snapshot." in text


def test_contract_vector_module_has_no_runtime_import_or_implementation() -> None:
    source = TEST_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: list[str] = []
    defined_names: list[str] = []
    argument_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.append(node.name)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                argument_names.extend(argument.arg for argument in node.args.args)
                argument_names.extend(
                    argument.arg for argument in node.args.kwonlyargs
                )
    assert not any(module == "app" or module.startswith("app.") for module in imported_modules)
    assert "canonical_gold_market_facts_snapshot" not in imported_modules
    assert "unittest.mock" not in imported_modules
    assert "build_canonical_gold_market_facts_snapshot_v1" not in defined_names
    assert not any(name.startswith("run_") for name in defined_names)
    assert "monkeypatch" not in argument_names
