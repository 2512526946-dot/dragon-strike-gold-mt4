from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
from types import MappingProxyType, UnionType
from typing import get_args, get_origin, get_type_hints

import pytest

from app.services import canonical_gold_market_facts_snapshot_projector as projector


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPOSITORY_ROOT
    / "backend"
    / "app"
    / "services"
    / "canonical_gold_market_facts_snapshot_projector.py"
)

TYPE_FIELDS = MappingProxyType(
    {
        "CanonicalGoldMarketFactsSourceV1": (
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
        ),
        "CanonicalGoldUpstreamEvidenceV1": (
            "reader_passed",
            "reader_status_code",
            "value_status_code",
            "data_quality_passed",
            "data_quality_status_code",
            "ready_for_readonly_analysis",
            "warning_codes",
            "same_attempt_identity_bound",
        ),
        "CanonicalGoldTickSourceV1": (
            "bid",
            "ask",
            "spread",
            "spread_points",
            "digits",
            "point",
            "tick_time_utc",
        ),
        "CanonicalGoldTimeframeSourceV1": (
            "timeframe",
            "period_seconds",
            "bars",
        ),
        "CanonicalGoldBarSourceV1": (
            "open_time_utc",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "spread_points",
        ),
        "CanonicalGoldSymbolSpecSourceV1": (
            "spec_time_utc",
            "digits",
            "point",
            "tick_size",
            "tick_value",
            "contract_size",
            "min_lot",
            "lot_step",
            "max_lot",
            "base_currency",
            "profit_currency",
            "margin_currency",
            "trade_mode_readonly_label",
            "session_status_readonly_label",
        ),
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

TYPE_ANNOTATIONS = MappingProxyType(
    {
        "CanonicalGoldMarketFactsSourceV1": (
            str,
            str,
            str,
            int,
            str,
            str,
            str,
            str,
            projector.CanonicalGoldUpstreamEvidenceV1,
            projector.CanonicalGoldTickSourceV1,
            str,
            tuple[projector.CanonicalGoldTimeframeSourceV1, ...],
            projector.CanonicalGoldSymbolSpecSourceV1,
        ),
        "CanonicalGoldUpstreamEvidenceV1": (
            bool,
            str,
            str,
            bool,
            str,
            bool,
            tuple[str, ...],
            bool,
        ),
        "CanonicalGoldTickSourceV1": (
            int | float,
            int | float,
            int | float,
            int,
            int,
            int | float,
            str,
        ),
        "CanonicalGoldTimeframeSourceV1": (
            str,
            int,
            tuple[projector.CanonicalGoldBarSourceV1, ...],
        ),
        "CanonicalGoldBarSourceV1": (
            str,
            int | float,
            int | float,
            int | float,
            int | float,
            int,
            int,
        ),
        "CanonicalGoldSymbolSpecSourceV1": (
            str,
            int,
            int | float,
            int | float,
            int | float,
            int | float,
            int | float,
            int | float,
            int | float,
            str,
            str,
            str,
            str,
            str,
        ),
        "CanonicalGoldMarketFactsSnapshotV1": (
            str,
            bool,
            str,
            tuple[str, ...],
            tuple[str, ...],
            bool,
            str | None,
            str | None,
            int | None,
            str | None,
            str | None,
            str | None,
            projector.CanonicalGoldQuoteFactsV1 | None,
            tuple[projector.CanonicalGoldTimeframeFactsV1, ...],
            projector.CanonicalGoldSymbolFactsV1 | None,
            projector.CanonicalGoldFreshnessFactsV1 | None,
            bool,
            bool,
            bool,
            bool,
            bool,
            bool,
            bool,
            bool,
        ),
        "CanonicalGoldQuoteFactsV1": (str, str, str, int, int, str, str),
        "CanonicalGoldTimeframeFactsV1": (
            str,
            int,
            tuple[projector.CanonicalGoldBarFactsV1, ...],
        ),
        "CanonicalGoldBarFactsV1": (str, str, str, str, str, int, int),
        "CanonicalGoldSymbolFactsV1": (
            str,
            int,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
        ),
        "CanonicalGoldFreshnessFactsV1": (int, int, int),
    }
)


def test_all_contract_types_are_exact_frozen_slotted_dataclasses() -> None:
    assert tuple(TYPE_FIELDS) == (
        "CanonicalGoldMarketFactsSourceV1",
        "CanonicalGoldUpstreamEvidenceV1",
        "CanonicalGoldTickSourceV1",
        "CanonicalGoldTimeframeSourceV1",
        "CanonicalGoldBarSourceV1",
        "CanonicalGoldSymbolSpecSourceV1",
        "CanonicalGoldMarketFactsSnapshotV1",
        "CanonicalGoldQuoteFactsV1",
        "CanonicalGoldTimeframeFactsV1",
        "CanonicalGoldBarFactsV1",
        "CanonicalGoldSymbolFactsV1",
        "CanonicalGoldFreshnessFactsV1",
    )

    for type_name, expected_fields in TYPE_FIELDS.items():
        record_type = getattr(projector, type_name)
        assert is_dataclass(record_type)
        assert record_type.__dataclass_params__.frozen is True
        assert record_type.__slots__ == expected_fields
        assert tuple(field.name for field in fields(record_type)) == expected_fields
        assert record_type.__dictoffset__ == 0


def test_all_annotations_match_the_contract_exactly() -> None:
    for type_name, expected_annotations in TYPE_ANNOTATIONS.items():
        record_type = getattr(projector, type_name)
        resolved = get_type_hints(record_type)
        assert tuple(resolved) == TYPE_FIELDS[type_name]
        assert tuple(resolved.values()) == expected_annotations

    numeric = get_type_hints(projector.CanonicalGoldTickSourceV1)["bid"]
    assert get_origin(numeric) is UnionType
    assert get_args(numeric) == (int, float)
    optional = get_type_hints(projector.CanonicalGoldMarketFactsSnapshotV1)["quote"]
    assert get_origin(optional) is UnionType
    assert get_args(optional) == (projector.CanonicalGoldQuoteFactsV1, type(None))
    bars = get_type_hints(projector.CanonicalGoldTimeframeFactsV1)["bars"]
    assert get_origin(bars) is tuple
    assert get_args(bars) == (projector.CanonicalGoldBarFactsV1, Ellipsis)


def test_source_instances_are_fresh_nested_and_immutable() -> None:
    first = _source()
    second = _source()

    assert first == second
    assert first is not second
    assert first.upstream_evidence is not second.upstream_evidence
    assert first.live_tick is not second.live_tick
    assert first.timeframes is not second.timeframes
    assert first.timeframes[0] is not second.timeframes[0]
    assert first.timeframes[0].bars is not second.timeframes[0].bars
    assert first.timeframes[0].bars[0] is not second.timeframes[0].bars[0]
    assert first.symbol_spec is not second.symbol_spec

    with pytest.raises(FrozenInstanceError):
        first.bundle_id = "replacement_bundle"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        first.live_tick.bid = 0  # type: ignore[misc]


def test_result_instances_are_fresh_nested_and_immutable() -> None:
    first = _result()
    second = _result()

    assert first == second
    assert first is not second
    assert first.quote is not second.quote
    assert first.timeframes is not second.timeframes
    assert first.timeframes[0] is not second.timeframes[0]
    assert first.timeframes[0].bars[0] is not second.timeframes[0].bars[0]
    assert first.symbol_spec is not second.symbol_spec
    assert first.freshness is not second.freshness

    with pytest.raises(FrozenInstanceError):
        first.passed = False  # type: ignore[misc]
    assert first.contract_version == "1.0"
    assert first.read_only is True
    assert first.demo_only is True
    assert first.is_tradable is False
    assert first.can_execute is False
    assert first.is_trading_permission is False
    assert first.is_execution_instruction is False
    assert first.allowed_to_call_ea is False
    assert first.allowed_to_modify_risk is False


def test_type_module_has_no_runtime_io_or_projector_behavior() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )

    assert imports == {"__future__", "dataclasses"}
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(tree)
    )
    assert not hasattr(projector, "build_canonical_gold_market_facts_snapshot_v1")
    assert not {
        "pathlib",
        "os",
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "datetime",
        "decimal",
    }.intersection(imports)


def _source() -> projector.CanonicalGoldMarketFactsSourceV1:
    bar = projector.CanonicalGoldBarSourceV1(
        open_time_utc="2026-07-10T02:00:00Z",
        open=3300.0,
        high=3301.0,
        low=3299.0,
        close=3300.5,
        tick_volume=100,
        spread_points=20,
    )
    return projector.CanonicalGoldMarketFactsSourceV1(
        contract_version="1.0",
        bundle_schema_version="1.0",
        bundle_id="bundle_20260710_001",
        sequence=1,
        canonical_symbol="XAUUSD",
        broker_symbol="GOLD",
        reference_time_utc="2026-07-10T02:30:05Z",
        policy_profile_version="canonical_gold_market_facts_policy_v1",
        upstream_evidence=projector.CanonicalGoldUpstreamEvidenceV1(
            reader_passed=True,
            reader_status_code="CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID",
            value_status_code="CANONICAL_MT4_BUNDLE_V1_VALUE_VALID",
            data_quality_passed=True,
            data_quality_status_code="CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED",
            ready_for_readonly_analysis=True,
            warning_codes=(),
            same_attempt_identity_bound=True,
        ),
        live_tick=projector.CanonicalGoldTickSourceV1(
            bid=3300.0,
            ask=3300.2,
            spread=0.2,
            spread_points=20,
            digits=2,
            point=0.01,
            tick_time_utc="2026-07-10T02:30:00Z",
        ),
        bars_generated_at_utc="2026-07-10T02:30:00Z",
        timeframes=tuple(
            projector.CanonicalGoldTimeframeSourceV1(
                timeframe=timeframe,
                period_seconds=period_seconds,
                bars=(bar,),
            )
            for timeframe, period_seconds in (
                ("M15", 900),
                ("H1", 3600),
                ("H4", 14400),
                ("D1", 86400),
            )
        ),
        symbol_spec=projector.CanonicalGoldSymbolSpecSourceV1(
            spec_time_utc="2026-07-10T02:30:00Z",
            digits=2,
            point=0.01,
            tick_size=0.01,
            tick_value=1.0,
            contract_size=100.0,
            min_lot=0.01,
            lot_step=0.01,
            max_lot=100.0,
            base_currency="XAU",
            profit_currency="USD",
            margin_currency="USD",
            trade_mode_readonly_label="demo",
            session_status_readonly_label="observed",
        ),
    )


def _result() -> projector.CanonicalGoldMarketFactsSnapshotV1:
    bar = projector.CanonicalGoldBarFactsV1(
        open_time_utc="2026-07-10T02:00:00Z",
        open_decimal="3300.00",
        high_decimal="3301.00",
        low_decimal="3299.00",
        close_decimal="3300.50",
        tick_volume=100,
        spread_points=20,
    )
    return projector.CanonicalGoldMarketFactsSnapshotV1(
        contract_version="1.0",
        passed=True,
        status_code="CANONICAL_GOLD_MARKET_FACTS_READY",
        reason_codes=(),
        warning_codes=(),
        identity_available=True,
        bundle_schema_version="1.0",
        bundle_id="bundle_20260710_001",
        sequence=1,
        canonical_symbol="XAUUSD",
        broker_symbol="GOLD",
        reference_time_utc="2026-07-10T02:30:05Z",
        quote=projector.CanonicalGoldQuoteFactsV1(
            bid_decimal="3300.00",
            ask_decimal="3300.20",
            spread_decimal="0.20",
            spread_points=20,
            digits=2,
            point_decimal="0.01",
            tick_time_utc="2026-07-10T02:30:00Z",
        ),
        timeframes=tuple(
            projector.CanonicalGoldTimeframeFactsV1(
                timeframe=timeframe,
                period_seconds=period_seconds,
                bars=(bar,),
            )
            for timeframe, period_seconds in (
                ("M15", 900),
                ("H1", 3600),
                ("H4", 14400),
                ("D1", 86400),
            )
        ),
        symbol_spec=projector.CanonicalGoldSymbolFactsV1(
            spec_time_utc="2026-07-10T02:30:00Z",
            digits=2,
            point_decimal="0.01",
            tick_size_decimal="0.01",
            tick_value_decimal="1",
            contract_size_decimal="100",
            min_lot_decimal="0.01",
            lot_step_decimal="0.01",
            max_lot_decimal="100",
            base_currency="XAU",
            profit_currency="USD",
            margin_currency="USD",
            trade_mode_readonly_label="demo",
            session_status_readonly_label="observed",
        ),
        freshness=projector.CanonicalGoldFreshnessFactsV1(
            tick_age_microseconds=5_000_000,
            bars_payload_age_microseconds=5_000_000,
            symbol_spec_age_microseconds=5_000_000,
        ),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )
