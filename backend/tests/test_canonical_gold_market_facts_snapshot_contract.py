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
    required_text: tuple[str, ...]
    forbidden_text: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InvalidShapeVector:
    name: str
    mutation: str
    accepted: bool


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
        ("type(value) is int", "type(value) is float"),
        ("bool", "subclasses", "strings"),
    ),
    NormalizationRuleVector(
        "single_decimal_conversion",
        ("Decimal(str(value))",),
        ("Decimal(value)", "repr(value)", "binary float arithmetic"),
    ),
    NormalizationRuleVector(
        "local_decimal_context",
        (
            "prec=64",
            "rounding=ROUND_HALF_EVEN",
            "Emin=-999999",
            "Emax=999999",
            "capitals=1",
            "clamp=0",
        ),
        ("permission to round",),
    ),
    NormalizationRuleVector(
        "price_quantum",
        ("Decimal(1).scaleb(-digits)",),
        ("being quantized",),
    ),
    NormalizationRuleVector(
        "fixed_point_price_output",
        ('format(decimal_value, f".{digits}f")', "trailing zeroes"),
        ("exponent", "leading plus sign"),
    ),
    NormalizationRuleVector(
        "exact_spread_identity",
        (
            "spread == ask - bid",
            "spread == spread_points_decimal * point",
        ),
        ("epsilon", "tolerance"),
    ),
    NormalizationRuleVector(
        "signed_zero_rejected",
        ("reject signed zero",),
        (),
    ),
    NormalizationRuleVector(
        "ambiguity_fails_closed",
        ("ambiguity fails closed",),
        ("round, sort, repair", "retry", "fallback algorithm"),
    ),
)

INVALID_SHAPE_VECTORS = (
    InvalidShapeVector("missing_field", "missing", False),
    InvalidShapeVector("extra_field", "extra", False),
    InvalidShapeVector("reordered_field", "reordered", False),
    InvalidShapeVector("duplicate_field", "duplicate", False),
    InvalidShapeVector("aliased_field", "aliased", False),
    InvalidShapeVector("case_changed_field", "case-changed", False),
    InvalidShapeVector("subclassed_value", "subclasses", False),
    InvalidShapeVector("wrong_container", "wrong tuple", False),
    InvalidShapeVector("wrong_element_type", "wrong tuple element types", False),
    InvalidShapeVector("wrong_timeframe_length", "tuple length", False),
    InvalidShapeVector("wrong_timeframe_order", "timeframe order", False),
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
        "exact_spread_identity",
        "signed_zero_rejected",
        "ambiguity_fails_closed",
    )
    for rule in NORMALIZATION_RULES:
        for required_text in rule.required_text:
            assert required_text in text
        for forbidden_text in rule.forbidden_text:
            assert forbidden_text in text
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
    for vector in INVALID_SHAPE_VECTORS:
        assert vector.mutation in text
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
