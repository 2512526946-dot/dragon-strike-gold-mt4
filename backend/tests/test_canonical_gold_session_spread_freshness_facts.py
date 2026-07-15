from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
import inspect
from pathlib import Path

import pytest

from app.services import canonical_gold_session_spread_freshness_facts as facts
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
    "bundle_schema_version",
    "bundle_id",
    "sequence",
    "canonical_symbol",
    "broker_symbol",
    "reference_time_utc",
    "session",
    "spread",
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
SESSION_FIELDS = (
    "utc_weekday_code",
    "utc_second_of_day",
    "session_bucket_code",
    "window_start_second_utc",
    "window_end_second_utc",
    "seconds_since_window_start",
    "seconds_until_window_end",
    "observed_writer_session_status_label",
)
SPREAD_FIELDS = (
    "bid_decimal",
    "ask_decimal",
    "mid_decimal",
    "spread_decimal",
    "spread_points",
    "digits",
    "point_decimal",
    "spread_to_mid_ppm_decimal",
)
FRESHNESS_FIELDS = (
    "tick_age_microseconds",
    "bars_payload_age_microseconds",
    "symbol_spec_age_microseconds",
    "maximum_source_age_microseconds",
    "oldest_source_component_code",
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


def test_public_types_and_builder_signature_are_exact() -> None:
    schemas = (
        (facts.CanonicalGoldSessionSpreadFreshnessFactsV1, RESULT_FIELDS),
        (facts.CanonicalGoldSessionFactsV1, SESSION_FIELDS),
        (facts.CanonicalGoldSpreadFactsV1, SPREAD_FIELDS),
        (facts.CanonicalGoldSourceFreshnessFactsV1, FRESHNESS_FIELDS),
    )
    for record_type, expected_fields in schemas:
        assert tuple(field.name for field in fields(record_type)) == expected_fields
        assert record_type.__slots__ == expected_fields
        assert "__dict__" not in record_type.__dict__

    assert facts.CanonicalGoldSessionSpreadFreshnessFactsV1.__annotations__ == {
        "contract_version": "str",
        "facts_profile_version": "str",
        "passed": "bool",
        "status_code": "str",
        "reason_codes": "tuple[str, ...]",
        "warning_codes": "tuple[str, ...]",
        "identity_available": "bool",
        "bundle_schema_version": "str | None",
        "bundle_id": "str | None",
        "sequence": "int | None",
        "canonical_symbol": "str | None",
        "broker_symbol": "str | None",
        "reference_time_utc": "str | None",
        "session": "CanonicalGoldSessionFactsV1 | None",
        "spread": "CanonicalGoldSpreadFactsV1 | None",
        "freshness": "CanonicalGoldSourceFreshnessFactsV1 | None",
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
        facts.build_canonical_gold_session_spread_freshness_facts_v1
    )
    assert tuple(signature.parameters) == ("market_facts_snapshot",)
    parameter = signature.parameters["market_facts_snapshot"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.annotation == "CanonicalGoldMarketFactsSnapshotV1"
    assert signature.return_annotation == "CanonicalGoldSessionSpreadFreshnessFactsV1"


def test_ready_result_is_exact_detached_fresh_and_deterministic() -> None:
    snapshot = _snapshot()
    frozen_input = repr(snapshot)

    first = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=snapshot
    )
    second = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=snapshot
    )

    assert first == second
    assert first is not second
    assert first.session is not second.session
    assert first.spread is not second.spread
    assert first.freshness is not second.freshness
    assert repr(snapshot) == frozen_input
    assert first.contract_version == "1.0"
    assert first.facts_profile_version == "canonical_gold_session_spread_freshness_profile_v1"
    assert first.passed is True
    assert first.status_code == "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_READY"
    assert first.reason_codes == ()
    assert first.warning_codes == ()
    assert first.identity_available is True
    assert (
        first.bundle_schema_version,
        first.bundle_id,
        first.sequence,
        first.canonical_symbol,
        first.broker_symbol,
        first.reference_time_utc,
    ) == (
        "1.0",
        "bundle_g191_ready",
        1,
        "XAUUSD",
        "GOLD",
        "2026-07-10T13:00:00Z",
    )
    assert first.session == facts.CanonicalGoldSessionFactsV1(
        utc_weekday_code="FRIDAY",
        utc_second_of_day=46800,
        session_bucket_code="LONDON_NEW_YORK_OVERLAP_UTC",
        window_start_second_utc=46800,
        window_end_second_utc=57600,
        seconds_since_window_start=0,
        seconds_until_window_end=10800,
        observed_writer_session_status_label="WRITER_OBSERVATION",
    )
    assert first.spread == facts.CanonicalGoldSpreadFactsV1(
        bid_decimal="3300.00",
        ask_decimal="3300.20",
        mid_decimal="3300.100",
        spread_decimal="0.20",
        spread_points=20,
        digits=2,
        point_decimal="0.01",
        spread_to_mid_ppm_decimal="60.604224",
    )
    assert first.freshness == facts.CanonicalGoldSourceFreshnessFactsV1(
        tick_age_microseconds=1_000_000,
        bars_payload_age_microseconds=1_000_000,
        symbol_spec_age_microseconds=2_000_000,
        maximum_source_age_microseconds=2_000_000,
        oldest_source_component_code="SYMBOL_SPEC",
    )
    _assert_safety_flags(first)
    with pytest.raises(FrozenInstanceError):
        first.passed = False  # type: ignore[misc]


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    (
        ("2026-07-06T00:00:00Z", ("MONDAY", "ASIA_UTC", 0, 28800, 0, 28800)),
        ("2026-07-06T07:59:59Z", ("MONDAY", "ASIA_UTC", 0, 28800, 28799, 1)),
        ("2026-07-06T08:00:00Z", ("MONDAY", "LONDON_UTC", 28800, 46800, 0, 18000)),
        ("2026-07-06T13:00:00Z", ("MONDAY", "LONDON_NEW_YORK_OVERLAP_UTC", 46800, 57600, 0, 10800)),
        ("2026-07-06T16:00:00Z", ("MONDAY", "NEW_YORK_UTC", 57600, 79200, 0, 21600)),
        ("2026-07-06T22:00:00Z", ("MONDAY", "OFF_HOURS_UTC", 79200, 86400, 0, 7200)),
        ("2026-07-12T23:59:59.999999Z", ("SUNDAY", "OFF_HOURS_UTC", 79200, 86400, 7199, 1)),
    ),
)
def test_session_windows_are_half_open_and_use_reference_time_only(
    timestamp: str,
    expected: tuple[str, str, int, int, int, int],
) -> None:
    result = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=_snapshot(reference_time_utc=timestamp)
    )
    assert result.passed is True
    assert result.session is not None
    weekday, bucket, start, end, since, until = expected
    assert (
        result.session.utc_weekday_code,
        result.session.session_bucket_code,
        result.session.window_start_second_utc,
        result.session.window_end_second_utc,
        result.session.seconds_since_window_start,
        result.session.seconds_until_window_end,
    ) == (weekday, bucket, start, end, since, until)
    assert result.session.observed_writer_session_status_label == "WRITER_OBSERVATION"


def test_large_fixed_point_and_exact_half_even_spread_vectors() -> None:
    coefficient = "9" * 64
    large = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=_snapshot(
            digits=8,
            bid=f"{coefficient}.00000000",
            ask=f"{coefficient}.00000000",
            spread="0.00000000",
            spread_points=0,
        )
    )
    assert large.passed is True
    assert large.spread is not None
    assert large.spread.mid_decimal == f"{coefficient}.000000000"
    assert large.spread.spread_to_mid_ppm_decimal == "0.000000"

    even_tie = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=_snapshot(
            digits=0, bid="16383", ask="16385", spread="2", spread_points=2
        )
    )
    odd_tie = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=_snapshot(
            digits=0, bid="16381", ask="16387", spread="6", spread_points=6
        )
    )
    assert even_tie.spread is not None
    assert odd_tie.spread is not None
    assert even_tie.spread.spread_to_mid_ppm_decimal == "122.070312"
    assert odd_tie.spread.spread_to_mid_ppm_decimal == "366.210938"


@pytest.mark.parametrize(
    ("ages", "expected"),
    (
        ((10, 2, 3), (10, "TICK")),
        ((10, 10, 2), (10, "TICK")),
        ((2, 10, 10), (10, "BARS_PAYLOAD")),
        ((2, 3, 10), (10, "SYMBOL_SPEC")),
    ),
)
def test_freshness_uses_exact_maximum_and_tie_priority(
    ages: tuple[int, int, int], expected: tuple[int, str]
) -> None:
    snapshot = _snapshot(ages=ages)
    result = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=snapshot
    )
    assert result.passed is True
    assert result.freshness is not None
    assert (
        result.freshness.maximum_source_age_microseconds,
        result.freshness.oldest_source_component_code,
    ) == expected


def test_all_failure_mappings_clear_identity_and_facts() -> None:
    base = _snapshot()

    class StrictStringSubclass(str):
        pass

    cases = (
        (
            replace(base, status_code=StrictStringSubclass(base.status_code)),
            "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
            "GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
        ),
        (
            replace(base, passed=False),
            "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_UPSTREAM_BLOCKED",
            "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_NOT_READY",
        ),
        (
            replace(base, bundle_id="bad bundle id"),
            "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_IDENTITY_INVALID",
            "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_IDENTITY_INVALID",
        ),
        (
            replace(base, reference_time_utc="2026-07-10T13:00:00+00:00"),
            "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID",
            "GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID",
        ),
        (
            replace(base, quote=replace(base.quote, spread_decimal="0.21")),
            "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID",
            "GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID",
        ),
        (
            replace(
                base,
                freshness=replace(base.freshness, tick_age_microseconds=-1),
            ),
            "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",
            "GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",
        ),
    )
    for snapshot, expected_status, expected_reason in cases:
        result = facts.build_canonical_gold_session_spread_freshness_facts_v1(
            market_facts_snapshot=snapshot
        )
        _assert_failure(result, expected_status, expected_reason)


def test_ordered_first_failure_priority_is_not_swappable() -> None:
    base = _snapshot()
    invalid_identity = replace(base, bundle_id="bad bundle id")
    invalid_session = replace(invalid_identity, reference_time_utc="bad-time")
    invalid_spread = replace(
        invalid_session,
        quote=replace(invalid_session.quote, spread_decimal="0.21"),
    )
    invalid_freshness = replace(
        invalid_spread,
        freshness=replace(invalid_spread.freshness, tick_age_microseconds=-1),
    )
    result = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=invalid_freshness
    )
    _assert_failure(
        result,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_IDENTITY_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_IDENTITY_INVALID",
    )

    upstream = replace(invalid_freshness, passed=False)
    result = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=upstream
    )
    _assert_failure(
        result,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_UPSTREAM_BLOCKED",
        "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_NOT_READY",
    )


def test_unexpected_exception_is_sanitized_without_input_leakage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sensitive = "C:/private/runtime/payload.json"

    def fail_identity(snapshot: object) -> bool:
        raise RuntimeError(sensitive)

    monkeypatch.setattr(facts, "_has_valid_identity", fail_identity)
    result = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=_snapshot()
    )
    _assert_failure(
        result,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SAFE_FAILURE",
        "GOLD_SESSION_SPREAD_FRESHNESS_EXCEPTION_SANITIZED",
    )
    assert sensitive not in repr(result)


def test_strict_upstream_invariants_fail_in_their_frozen_categories() -> None:
    base = _snapshot()
    reversed_bars = replace(
        base.timeframes[0],
        bars=(
            base.timeframes[0].bars[0],
            replace(base.timeframes[0].bars[0], open_time_utc="2026-07-10T11:00:00Z"),
        ),
    )
    upstream_result = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=replace(
            base, timeframes=(reversed_bars, *base.timeframes[1:])
        )
    )
    _assert_failure(
        upstream_result,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_UPSTREAM_BLOCKED",
        "GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_NOT_READY",
    )

    incomplete = replace(
        base.timeframes[-1],
        bars=(replace(base.timeframes[-1].bars[0], open_time_utc="2026-07-10T00:00:00Z"),),
    )
    freshness_result = facts.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=replace(
            base, timeframes=(*base.timeframes[:-1], incomplete)
        )
    )
    _assert_failure(
        freshness_result,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",
        "GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",
    )


def test_production_module_is_pure_memory_and_does_not_import_runtime_boundaries() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "canonical_gold_session_spread_freshness_facts.py"
    )
    source = module_path.read_text(encoding="ascii")
    tree = ast.parse(source)
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert imports == {
        "__future__",
        "dataclasses",
        "datetime",
        "app.services.canonical_gold_market_facts_snapshot_projector",
    }
    projector_import = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "app.services.canonical_gold_market_facts_snapshot_projector"
    )
    assert tuple(alias.name for alias in projector_import.names) == (
        "CanonicalGoldBarFactsV1",
        "CanonicalGoldFreshnessFactsV1",
        "CanonicalGoldMarketFactsSnapshotV1",
        "CanonicalGoldQuoteFactsV1",
        "CanonicalGoldSymbolFactsV1",
        "CanonicalGoldTimeframeFactsV1",
    )
    forbidden_calls = {
        "open",
        "getenv",
        "get_settings",
        "datetime.now",
        "datetime.utcnow",
        "time",
        "sleep",
        "sorted",
    }
    calls = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            calls.add(f"{node.func.value.id}.{node.func.attr}")
    assert calls.isdisjoint(forbidden_calls)
    forbidden_text = (
        "build_canonical_gold_market_facts_snapshot_v1",
        "canonical_gold_market_facts_source_adapter",
        "canonical_gold_market_facts_docs_fixture_integration",
        "canonical_bundle_replay_runner",
        "mt4",
    )
    assert all(value not in source for value in forbidden_text)


def _snapshot(
    *,
    reference_time_utc: str = "2026-07-10T13:00:00Z",
    digits: int = 2,
    bid: str = "3300.00",
    ask: str = "3300.20",
    spread: str = "0.20",
    spread_points: int = 20,
    ages: tuple[int, int, int] = (1_000_000, 1_000_000, 2_000_000),
) -> CanonicalGoldMarketFactsSnapshotV1:
    reference = _parse_test_time(reference_time_utc)
    tick_time = reference - timedelta(microseconds=ages[0])
    bars_payload_time = reference - timedelta(microseconds=ages[1])
    spec_time = reference - timedelta(microseconds=ages[2])
    point = "1" if digits == 0 else f"0.{('0' * (digits - 1))}1"
    timeframes = tuple(
        CanonicalGoldTimeframeFactsV1(
            timeframe=timeframe,
            period_seconds=period,
            bars=(
                CanonicalGoldBarFactsV1(
                    open_time_utc=_utc(bars_payload_time - timedelta(seconds=period * 2)),
                    open_decimal=bid,
                    high_decimal=ask,
                    low_decimal=bid,
                    close_decimal=bid,
                    tick_volume=1,
                    spread_points=spread_points,
                ),
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
        bundle_id="bundle_g191_ready",
        sequence=1,
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


def _parse_test_time(value: str) -> datetime:
    return datetime.fromisoformat(f"{value[:-1]}+00:00")


def _utc(value: datetime) -> str:
    value = value.astimezone(UTC)
    if value.microsecond:
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ").rstrip("0Z") + "Z"
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _assert_failure(
    result: facts.CanonicalGoldSessionSpreadFreshnessFactsV1,
    status: str,
    reason: str,
) -> None:
    assert result.passed is False
    assert result.status_code == status
    assert result.reason_codes == (reason,)
    assert result.warning_codes == ()
    assert result.identity_available is False
    assert (
        result.bundle_schema_version,
        result.bundle_id,
        result.sequence,
        result.canonical_symbol,
        result.broker_symbol,
        result.reference_time_utc,
        result.session,
        result.spread,
        result.freshness,
    ) == (None,) * 9
    _assert_safety_flags(result)


def _assert_safety_flags(
    result: facts.CanonicalGoldSessionSpreadFreshnessFactsV1,
) -> None:
    assert {name: getattr(result, name) for name in SAFETY_FLAGS} == SAFETY_FLAGS
