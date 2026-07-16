from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
import inspect
from pathlib import Path

import pytest

from app.services import canonical_gold_volatility_structure_facts as facts
from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldBarFactsV1,
    CanonicalGoldFreshnessFactsV1,
    CanonicalGoldMarketFactsSnapshotV1,
    CanonicalGoldQuoteFactsV1,
    CanonicalGoldSymbolFactsV1,
    CanonicalGoldTimeframeFactsV1,
)


RESULT_FIELDS = (
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
TIMEFRAME_FIELDS = (
    "timeframe",
    "period_seconds",
    "source_bar_count",
    "pair_count",
    "bar_pairs",
)
PAIR_FIELDS = (
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
SAFETY_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}


def test_public_types_exports_and_builder_signature_are_exact() -> None:
    assert facts.__all__ == (
        "CanonicalGoldVolatilityStructureFactsV1",
        "CanonicalGoldTimeframeVolatilityStructureFactsV1",
        "CanonicalGoldBarPairVolatilityStructureFactsV1",
        "build_canonical_gold_volatility_structure_facts_v1",
    )
    for record_type, expected_fields in (
        (facts.CanonicalGoldVolatilityStructureFactsV1, RESULT_FIELDS),
        (facts.CanonicalGoldTimeframeVolatilityStructureFactsV1, TIMEFRAME_FIELDS),
        (facts.CanonicalGoldBarPairVolatilityStructureFactsV1, PAIR_FIELDS),
    ):
        assert tuple(field.name for field in fields(record_type)) == expected_fields
        assert record_type.__slots__ == expected_fields
        assert "__dict__" not in record_type.__dict__

    assert facts.CanonicalGoldVolatilityStructureFactsV1.__annotations__ == {
        "contract_version": "str",
        "facts_profile_version": "str",
        "passed": "bool",
        "status_code": "str",
        "reason_codes": "tuple[str, ...]",
        "warning_codes": "tuple[str, ...]",
        "identity_available": "bool",
        "source_contract_version": "str | None",
        "bundle_schema_version": "str | None",
        "bundle_id": "str | None",
        "sequence": "int | None",
        "canonical_symbol": "str | None",
        "broker_symbol": "str | None",
        "reference_time_utc": "str | None",
        "timeframes": "tuple[CanonicalGoldTimeframeVolatilityStructureFactsV1, ...]",
        "total_pair_count": "int",
        "read_only": "bool",
        "demo_only": "bool",
        "is_tradable": "bool",
        "can_execute": "bool",
        "is_trading_permission": "bool",
        "is_execution_instruction": "bool",
        "allowed_to_call_ea": "bool",
        "allowed_to_modify_risk": "bool",
    }
    signature = inspect.signature(
        facts.build_canonical_gold_volatility_structure_facts_v1
    )
    assert tuple(signature.parameters) == ("market_facts_snapshot",)
    parameter = signature.parameters["market_facts_snapshot"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.annotation == "CanonicalGoldMarketFactsSnapshotV1"
    assert signature.return_annotation == "CanonicalGoldVolatilityStructureFactsV1"


def test_ready_result_is_exact_fresh_detached_and_deterministic() -> None:
    snapshot = _snapshot()
    frozen_input = repr(snapshot)

    first = facts.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=snapshot
    )
    second = facts.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=snapshot
    )

    assert first == second
    assert first is not second
    assert repr(snapshot) == frozen_input
    assert first.contract_version == "1.0"
    assert first.facts_profile_version == "canonical_gold_volatility_structure_profile_v1"
    assert first.passed is True
    assert first.status_code == "CANONICAL_GOLD_VOLATILITY_STRUCTURE_READY"
    assert first.reason_codes == ()
    assert first.warning_codes == ()
    assert first.identity_available is True
    assert (
        first.source_contract_version,
        first.bundle_schema_version,
        first.bundle_id,
        first.sequence,
        first.canonical_symbol,
        first.broker_symbol,
        first.reference_time_utc,
    ) == (
        "1.0",
        "1.0",
        "bundle_g196_ready",
        196,
        "XAUUSD",
        "GOLD",
        "2026-07-10T13:00:00Z",
    )
    assert tuple(item.timeframe for item in first.timeframes) == (
        "M15",
        "H1",
        "H4",
        "D1",
    )
    assert tuple(item.period_seconds for item in first.timeframes) == (
        900,
        3600,
        14400,
        86400,
    )
    assert tuple(item.source_bar_count for item in first.timeframes) == (3, 3, 3, 3)
    assert tuple(item.pair_count for item in first.timeframes) == (2, 2, 2, 2)
    assert first.total_pair_count == 8
    assert all(left is not right for left, right in zip(first.timeframes, second.timeframes))
    assert all(
        left.bar_pairs is not right.bar_pairs
        for left, right in zip(first.timeframes, second.timeframes)
    )
    assert all(
        left_pair is not right_pair
        for left, right in zip(first.timeframes, second.timeframes)
        for left_pair, right_pair in zip(left.bar_pairs, right.bar_pairs)
    )
    _assert_safety(first)
    with pytest.raises(FrozenInstanceError):
        first.passed = False  # type: ignore[misc]


def test_all_adjacent_pairs_and_exact_arithmetic_are_emitted_in_source_order() -> None:
    snapshot = _snapshot()
    result = facts.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=snapshot
    )
    assert result.passed is True
    first_timeframe = result.timeframes[0]
    assert tuple(
        (pair.previous_open_time_utc, pair.current_open_time_utc)
        for pair in first_timeframe.bar_pairs
    ) == tuple(
        (snapshot.timeframes[0].bars[index].open_time_utc,
         snapshot.timeframes[0].bars[index + 1].open_time_utc)
        for index in range(2)
    )
    first_pair, second_pair = first_timeframe.bar_pairs
    assert tuple(getattr(first_pair, name) for name in PAIR_FIELDS[2:12]) == (
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
    )
    assert tuple(getattr(first_pair, name) for name in PAIR_FIELDS[12:]) == (
        "UP",
        "CONTRACTED",
        "INSIDE",
        "BELOW_PREVIOUS_HIGH",
        "ABOVE_PREVIOUS_LOW",
        "INSIDE_PREVIOUS_RANGE",
    )
    assert tuple(getattr(second_pair, name) for name in PAIR_FIELDS[2:12]) == (
        "16.00",
        "24.00",
        "24.00",
        "-10.00",
        "10.00",
        "7.00",
        "7.00",
        "-10.00",
        "4.00",
        "-4.00",
    )


@pytest.mark.parametrize(
    ("current", "expected"),
    (
        (("100.00", "110.00", "90.00", "100.00"), ("FLAT", "EQUAL", "EXACT_MATCH")),
        (("95.00", "108.00", "92.00", "105.00"), ("UP", "CONTRACTED", "INSIDE")),
        (("105.00", "112.00", "88.00", "95.00"), ("DOWN", "EXPANDED", "OUTSIDE")),
        (("115.00", "120.00", "100.00", "115.00"), ("FLAT", "EQUAL", "SHIFTED_UP")),
        (("85.00", "100.00", "80.00", "85.00"), ("FLAT", "EQUAL", "SHIFTED_DOWN")),
    ),
)
def test_structure_code_mapping_is_exhaustive_and_ordered(
    current: tuple[str, str, str, str], expected: tuple[str, str, str]
) -> None:
    result = facts.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=_snapshot(
            bars=(
                ("100.00", "110.00", "90.00", "100.00"),
                current,
            )
        )
    )
    assert result.passed is True
    pair = result.timeframes[0].bar_pairs[0]
    assert (
        pair.direction_code,
        pair.range_relation_code,
        pair.range_containment_code,
    ) == expected


def test_true_range_uses_previous_close_for_gap_up_and_gap_down() -> None:
    for current in (
        ("120.00", "125.00", "118.00", "122.00"),
        ("80.00", "82.00", "75.00", "78.00"),
    ):
        result = facts.build_canonical_gold_volatility_structure_facts_v1(
            market_facts_snapshot=_snapshot(
                bars=(
                    ("100.00", "110.00", "90.00", "100.00"),
                    current,
                )
            )
        )
        pair = result.timeframes[0].bar_pairs[0]
        assert pair.current_range_decimal == "7.00"
        assert pair.true_range_decimal == "25.00"


def test_digits_zero_and_long_coefficients_are_exact_without_float_arithmetic() -> None:
    zero_digits = facts.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=_snapshot(
            digits=0,
            bid="100",
            ask="102",
            spread="2",
            spread_points=2,
            bars=(("100", "110", "90", "100"), ("95", "108", "92", "105")),
        )
    )
    assert zero_digits.passed is True
    pair = zero_digits.timeframes[0].bar_pairs[0]
    assert pair.previous_range_decimal == "20"
    assert pair.body_signed_decimal == "10"
    assert "." not in pair.true_range_decimal

    base = int("8" * 72)
    values = tuple(
        str(value) + ".00"
        for value in (base, base + 10, base - 10, base)
    )
    current = tuple(
        str(value) + ".00"
        for value in (base - 5, base + 8, base - 8, base + 5)
    )
    long_result = facts.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=_snapshot(
            bid=f"{base}.00",
            ask=f"{base}.20",
            spread="0.20",
            bars=(values, current),
        )
    )
    assert long_result.passed is True
    assert long_result.timeframes[0].bar_pairs[0].current_range_decimal == "16.00"


def test_ordered_failure_mappings_clear_identity_facts_and_sensitive_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _snapshot()

    class StrictStringSubclass(str):
        pass

    original_ready_result = facts._ready_result

    def invalid_ready_result(*args: object, **kwargs: object) -> object:
        return replace(original_ready_result(*args, **kwargs), total_pair_count=-1)

    cases = (
        (
            replace(snapshot, contract_version=StrictStringSubclass("1.0")),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_INPUT_INVALID",
            "GOLD_VOLATILITY_STRUCTURE_INPUT_TYPE_INVALID",
        ),
        (
            replace(snapshot, warning_codes=("POLLUTED",)),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_UPSTREAM_BLOCKED",
            "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_NOT_READY",
        ),
        (
            replace(snapshot, bundle_id="sensitive bad bundle"),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_IDENTITY_INVALID",
            "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_IDENTITY_INVALID",
        ),
        (
            _replace_bar(snapshot, 0, 0, open_decimal="0.00"),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID",
            "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID",
        ),
        (
            _replace_timeframe(snapshot, 0, bars=(snapshot.timeframes[0].bars[0],)),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT",
            "GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT",
        ),
        (
            replace(snapshot, quote=replace(snapshot.quote, bid_decimal="100")),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_DECIMAL_INVALID",
            "GOLD_VOLATILITY_STRUCTURE_DECIMAL_INPUT_INVALID",
        ),
    )
    for invalid_snapshot, status, reason in cases:
        _assert_failure(
            facts.build_canonical_gold_volatility_structure_facts_v1(
                market_facts_snapshot=invalid_snapshot
            ),
            status,
            reason,
        )

    monkeypatch.setattr(facts, "_ready_result", invalid_ready_result)
    _assert_failure(
        facts.build_canonical_gold_volatility_structure_facts_v1(
            market_facts_snapshot=snapshot
        ),
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID",
    )
    monkeypatch.undo()

    def unexpected(*args: object, **kwargs: object) -> object:
        raise RuntimeError("secret path payload checksum")

    monkeypatch.setattr(facts, "_build_timeframes", unexpected)
    failure = facts.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=snapshot
    )
    _assert_failure(
        failure,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_SAFE_FAILURE",
        "GOLD_VOLATILITY_STRUCTURE_EXCEPTION_SANITIZED",
    )
    assert "secret" not in repr(failure)
    assert snapshot.bundle_id not in repr(failure)


def test_first_failure_priority_is_not_swappable() -> None:
    snapshot = _snapshot()
    invalid = replace(
        _replace_bar(snapshot, 0, 0, open_decimal="0.00"),
        bundle_id="bad",
        warning_codes=("WARNING",),
    )
    result = facts.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=invalid
    )
    _assert_failure(
        result,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_UPSTREAM_BLOCKED",
        "GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_NOT_READY",
    )


def test_strict_shape_timestamp_ohlc_decimal_and_history_boundaries() -> None:
    snapshot = _snapshot()

    class SnapshotSubclass(CanonicalGoldMarketFactsSnapshotV1):
        pass

    subclassed = SnapshotSubclass(
        *(getattr(snapshot, name) for name in snapshot.__slots__)
    )
    _assert_failure(
        facts.build_canonical_gold_volatility_structure_facts_v1(
            market_facts_snapshot=subclassed
        ),
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_INPUT_INVALID",
        "GOLD_VOLATILITY_STRUCTURE_INPUT_TYPE_INVALID",
    )
    for invalid, status, reason in (
        (
            _replace_bar(snapshot, 0, 0, open_time_utc="bad"),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID",
            "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID",
        ),
        (
            _replace_bar(snapshot, 0, 0, high_decimal="99.00"),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID",
            "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID",
        ),
        (
            replace(snapshot, quote=replace(snapshot.quote, bid_decimal="NaN")),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_DECIMAL_INVALID",
            "GOLD_VOLATILITY_STRUCTURE_DECIMAL_INPUT_INVALID",
        ),
        (
            replace(snapshot, timeframes=tuple(reversed(snapshot.timeframes))),
            "CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID",
            "GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID",
        ),
    ):
        _assert_failure(
            facts.build_canonical_gold_volatility_structure_facts_v1(
                market_facts_snapshot=invalid
            ),
            status,
            reason,
        )


def test_production_module_is_ascii_pure_memory_and_isolated() -> None:
    module_path = Path(facts.__file__)
    source = module_path.read_text(encoding="ascii")
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
    assert imported_modules & {
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "time",
        "app.services.canonical_gold_market_facts_docs_fixture_integration",
        "app.services.canonical_gold_market_facts_source_adapter",
        "app.services.canonical_gold_session_spread_freshness_facts",
        "app.services.canonical_bundle_replay_runner",
        "app.api.mt4",
    } == set()
    forbidden_calls = {
        "open",
        "getenv",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "datetime.now",
        "datetime.utcnow",
    }
    call_names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            call_names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                call_names.add(f"{node.func.value.id}.{node.func.attr}")
            call_names.add(node.func.attr)
    assert call_names.isdisjoint(forbidden_calls)
    assert all(ord(character) < 128 for character in source)


def _snapshot(
    *,
    reference_time_utc: str = "2026-07-10T13:00:00Z",
    digits: int = 2,
    bid: str = "100.00",
    ask: str = "100.20",
    spread: str = "0.20",
    spread_points: int = 20,
    bars: tuple[tuple[str, str, str, str], ...] = (
        ("100.00", "110.00", "90.00", "100.00"),
        ("95.00", "108.00", "92.00", "105.00"),
        ("105.00", "112.00", "88.00", "95.00"),
    ),
) -> CanonicalGoldMarketFactsSnapshotV1:
    reference = _parse_test_time(reference_time_utc)
    ages = (1_000_000, 1_000_000, 2_000_000)
    tick_time = reference - timedelta(microseconds=ages[0])
    bars_payload_time = reference - timedelta(microseconds=ages[1])
    spec_time = reference - timedelta(microseconds=ages[2])
    point = "1" if digits == 0 else f"0.{('0' * (digits - 1))}1"
    timeframes = tuple(
        CanonicalGoldTimeframeFactsV1(
            timeframe=timeframe,
            period_seconds=period,
            bars=tuple(
                CanonicalGoldBarFactsV1(
                    open_time_utc=_utc(
                        bars_payload_time
                        - timedelta(seconds=period * (len(bars) - index))
                    ),
                    open_decimal=values[0],
                    high_decimal=values[1],
                    low_decimal=values[2],
                    close_decimal=values[3],
                    tick_volume=index + 1,
                    spread_points=spread_points,
                )
                for index, values in enumerate(bars)
            ),
        )
        for timeframe, period in (
            ("M15", 900),
            ("H1", 3600),
            ("H4", 14400),
            ("D1", 86400),
        )
    )
    return CanonicalGoldMarketFactsSnapshotV1(
        contract_version="1.0",
        passed=True,
        status_code="CANONICAL_GOLD_MARKET_FACTS_READY",
        reason_codes=(),
        warning_codes=(),
        identity_available=True,
        bundle_schema_version="1.0",
        bundle_id="bundle_g196_ready",
        sequence=196,
        canonical_symbol="XAUUSD",
        broker_symbol="GOLD",
        reference_time_utc=reference_time_utc,
        quote=CanonicalGoldQuoteFactsV1(
            bid_decimal=bid,
            ask_decimal=ask,
            spread_decimal=spread,
            spread_points=spread_points,
            digits=digits,
            point_decimal=point,
            tick_time_utc=_utc(tick_time),
        ),
        timeframes=timeframes,
        symbol_spec=CanonicalGoldSymbolFactsV1(
            spec_time_utc=_utc(spec_time),
            digits=digits,
            point_decimal=point,
            tick_size_decimal=point,
            tick_value_decimal="1",
            contract_size_decimal="100",
            min_lot_decimal="0.01",
            lot_step_decimal="0.01",
            max_lot_decimal="100",
            base_currency="XAU",
            profit_currency="USD",
            margin_currency="USD",
            trade_mode_readonly_label="ENABLED",
            session_status_readonly_label="WRITER_OBSERVATION",
        ),
        freshness=CanonicalGoldFreshnessFactsV1(
            tick_age_microseconds=ages[0],
            bars_payload_age_microseconds=ages[1],
            symbol_spec_age_microseconds=ages[2],
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


def _replace_timeframe(
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
    index: int,
    **changes: object,
) -> CanonicalGoldMarketFactsSnapshotV1:
    timeframes = list(snapshot.timeframes)
    timeframes[index] = replace(timeframes[index], **changes)
    return replace(snapshot, timeframes=tuple(timeframes))


def _replace_bar(
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
    timeframe_index: int,
    bar_index: int,
    **changes: object,
) -> CanonicalGoldMarketFactsSnapshotV1:
    timeframe = snapshot.timeframes[timeframe_index]
    bars = list(timeframe.bars)
    bars[bar_index] = replace(bars[bar_index], **changes)
    return _replace_timeframe(snapshot, timeframe_index, bars=tuple(bars))


def _parse_test_time(value: str) -> datetime:
    return datetime.fromisoformat(f"{value[:-1]}+00:00")


def _utc(value: datetime) -> str:
    value = value.astimezone(UTC)
    if value.microsecond:
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ").rstrip("0Z") + "Z"
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _assert_failure(
    result: facts.CanonicalGoldVolatilityStructureFactsV1,
    status: str,
    reason: str,
) -> None:
    assert result.passed is False
    assert result.status_code == status
    assert result.reason_codes == (reason,)
    assert result.warning_codes == ()
    assert result.identity_available is False
    assert (
        result.source_contract_version,
        result.bundle_schema_version,
        result.bundle_id,
        result.sequence,
        result.canonical_symbol,
        result.broker_symbol,
        result.reference_time_utc,
    ) == (None,) * 7
    assert result.timeframes == ()
    assert result.total_pair_count == 0
    _assert_safety(result)


def _assert_safety(result: facts.CanonicalGoldVolatilityStructureFactsV1) -> None:
    assert {name: getattr(result, name) for name in SAFETY_FLAGS} == SAFETY_FLAGS
