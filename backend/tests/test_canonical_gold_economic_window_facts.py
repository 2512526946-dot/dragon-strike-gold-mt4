from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
import inspect
from pathlib import Path

import pytest

from app.services import canonical_gold_economic_window_facts as facts
from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldBarFactsV1,
    CanonicalGoldFreshnessFactsV1,
    CanonicalGoldMarketFactsSnapshotV1,
    CanonicalGoldQuoteFactsV1,
    CanonicalGoldSymbolFactsV1,
    CanonicalGoldTimeframeFactsV1,
    build_canonical_gold_market_facts_snapshot_v1,
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


class StrictStringSubclass(str):
    pass


def test_public_types_exports_and_keyword_only_builder_are_exact() -> None:
    assert facts.__all__ == (
        "CanonicalGoldEconomicCalendarSnapshotV1",
        "CanonicalGoldEconomicCalendarUpstreamEvidenceV1",
        "CanonicalGoldEconomicEventSourceV1",
        "CanonicalGoldEconomicWindowFactsV1",
        "CanonicalGoldEconomicEventWindowFactsV1",
        "CanonicalGoldEconomicWindowSummaryV1",
        "build_canonical_gold_economic_window_facts_v1",
    )
    expected = {
        facts.CanonicalGoldEconomicCalendarSnapshotV1: (
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
        ),
        facts.CanonicalGoldEconomicCalendarUpstreamEvidenceV1: (
            "adapter_passed",
            "adapter_status_code",
            "schema_validated",
            "identity_validated",
            "timestamps_normalized",
            "same_snapshot_bound",
            "warning_codes",
            "raw_payload_discarded",
        ),
        facts.CanonicalGoldEconomicEventSourceV1: (
            "event_id",
            "scheduled_at_utc",
            "country_code",
            "currency_code",
            "event_category_code",
            "impact_code",
            "source_revision",
            "event_status_code",
        ),
        facts.CanonicalGoldEconomicWindowFactsV1: _RESULT_FIELDS,
        facts.CanonicalGoldEconomicEventWindowFactsV1: (
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
        ),
        facts.CanonicalGoldEconomicWindowSummaryV1: (
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
        ),
    }
    expected_annotations = {
        facts.CanonicalGoldEconomicCalendarSnapshotV1: (
            "str", "str", "str", "str", "str", "str", "str",
            "tuple[CanonicalGoldEconomicEventSourceV1, ...]",
            "CanonicalGoldEconomicCalendarUpstreamEvidenceV1",
            "bool", "bool", "bool",
        ),
        facts.CanonicalGoldEconomicCalendarUpstreamEvidenceV1: (
            "bool", "str", "bool", "bool", "bool", "bool", "tuple[str, ...]", "bool",
        ),
        facts.CanonicalGoldEconomicEventSourceV1: (
            "str", "str", "str", "str", "str", "str", "int", "str",
        ),
        facts.CanonicalGoldEconomicWindowFactsV1: (
            "str", "str", "bool", "str", "tuple[str, ...]", "tuple[str, ...]", "bool",
            "str | None", "str | None", "str | None", "int | None", "str | None",
            "str | None", "str | None", "str | None", "str | None", "str | None",
            "str | None", "str | None", "str | None", "str | None",
            "tuple[CanonicalGoldEconomicEventWindowFactsV1, ...]",
            "CanonicalGoldEconomicWindowSummaryV1 | None",
            "bool", "bool", "bool", "bool", "bool", "bool", "bool", "bool",
        ),
        facts.CanonicalGoldEconomicEventWindowFactsV1: (
            "str", "str", "str", "str", "str", "str", "int", "str", "str",
            "int", "int", "int", "str", "bool",
        ),
        facts.CanonicalGoldEconomicWindowSummaryV1: (
            "int", "int", "int", "bool", "tuple[str, ...]", "str | None", "int | None",
            "str | None", "int | None", "str",
        ),
    }
    for public_type, field_names in expected.items():
        assert tuple(field.name for field in fields(public_type)) == field_names
        assert public_type.__slots__ == field_names
        assert tuple(public_type.__annotations__.values()) == expected_annotations[public_type]
        with pytest.raises(FrozenInstanceError):
            setattr(_sample_for_type(public_type), field_names[0], "changed")

    signature = inspect.signature(facts.build_canonical_gold_economic_window_facts_v1)
    assert tuple(signature.parameters) == (
        "market_facts_snapshot",
        "economic_calendar_snapshot",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert str(signature.return_annotation) == "CanonicalGoldEconomicWindowFactsV1"


def test_ready_result_is_exact_detached_fresh_and_deterministic() -> None:
    market = _market_snapshot()
    calendar = _calendar_snapshot()
    market_before = _market_snapshot()
    calendar_before = _calendar_snapshot()

    first = facts.build_canonical_gold_economic_window_facts_v1(
        market_facts_snapshot=market,
        economic_calendar_snapshot=calendar,
    )
    second = facts.build_canonical_gold_economic_window_facts_v1(
        market_facts_snapshot=market,
        economic_calendar_snapshot=calendar,
    )

    assert first == second
    assert first is not second
    assert first.event_windows is not second.event_windows
    assert first.summary is not second.summary
    assert all(left is not right for left, right in zip(first.event_windows, second.event_windows))
    assert market == market_before
    assert calendar == calendar_before
    assert first.contract_version == "1.0"
    assert first.facts_profile_version == "canonical_gold_economic_window_profile_v1"
    assert first.passed is True
    assert first.status_code == "CANONICAL_GOLD_ECONOMIC_WINDOW_READY"
    assert first.reason_codes == ()
    assert first.warning_codes == ()
    assert first.identity_available is True
    assert tuple(getattr(first, field) for field in _RESULT_FIELDS[7:21]) == (
        "1.0",
        "1.0",
        "bundle_g201_ready",
        201,
        "XAUUSD",
        "GOLD",
        "2026-07-10T13:00:00Z",
        "1.0",
        "1.0",
        "calendar.g201.ready",
        "canonical_gold_economic_calendar_source_v1",
        "2026-07-10T12:59:59.900000Z",
        "2026-07-09T13:00:00Z",
        "2026-07-11T13:00:00.000001Z",
    )
    _assert_safety(first)


def test_windows_overlap_endpoints_nearest_ties_and_summary_are_exact() -> None:
    result = _build()
    assert tuple(event.event_id for event in result.event_windows) == (
        "event.elapsed.high",
        "event.active.medium",
        "event.high.a",
        "event.medium.a",
        "event.next.high.a",
        "event.next.medium.a",
    )
    assert tuple(event.window_relation_code for event in result.event_windows) == (
        "ELAPSED",
        "ACTIVE",
        "ACTIVE",
        "ACTIVE",
        "ACTIVE",
        "ACTIVE",
    )
    assert result.summary == facts.CanonicalGoldEconomicWindowSummaryV1(
        calendar_age_microseconds=100_000,
        relevant_event_count=6,
        active_window_count=5,
        inside_any_observation_window=True,
        active_event_ids=(
            "event.active.medium",
            "event.high.a",
            "event.medium.a",
            "event.next.high.a",
            "event.next.medium.a",
        ),
        nearest_previous_event_id="event.high.a",
        nearest_previous_event_offset_microseconds=0,
        nearest_next_event_id="event.next.high.a",
        nearest_next_event_offset_microseconds=600_000_000,
        highest_active_impact_code="HIGH",
    )
    high = result.event_windows[2]
    assert high.window_start_utc == "2026-07-10T12:30:00Z"
    assert high.window_end_utc == "2026-07-10T13:30:00Z"
    assert high.event_offset_microseconds == 0
    assert high.window_start_offset_microseconds == -1_800_000_000
    assert high.window_end_offset_microseconds == 1_800_000_000
    assert high.is_active_observation_window is True


@pytest.mark.parametrize(
    ("event_time", "expected_relation"),
    (
        ("2026-07-10T13:30:00Z", "ACTIVE"),
        ("2026-07-10T13:00:00Z", "ACTIVE"),
        ("2026-07-10T12:30:00Z", "ELAPSED"),
        ("2026-07-10T13:30:00.000001Z", "UPCOMING"),
    ),
)
def test_half_open_high_impact_window_endpoints(
    event_time: str,
    expected_relation: str,
) -> None:
    event = _event("event.endpoint", event_time, impact="HIGH")
    result = _build(calendar=_calendar_snapshot(events=(event,)))
    assert result.passed is True
    assert result.event_windows[0].window_relation_code == expected_relation
    assert result.event_windows[0].is_active_observation_window is (
        expected_relation == "ACTIVE"
    )


def test_empty_relevant_result_is_closed() -> None:
    events = (
        _event("event.cancelled", "2026-07-10T13:00:00Z", status="CANCELLED"),
        _event("event.low.only", "2026-07-10T14:00:00Z", impact="LOW"),
    )
    result = _build(calendar=_calendar_snapshot(events=events))
    assert result.passed is True
    assert result.event_windows == ()
    assert result.summary == facts.CanonicalGoldEconomicWindowSummaryV1(
        calendar_age_microseconds=100_000,
        relevant_event_count=0,
        active_window_count=0,
        inside_any_observation_window=False,
        active_event_ids=(),
        nearest_previous_event_id=None,
        nearest_previous_event_offset_microseconds=None,
        nearest_next_event_id=None,
        nearest_next_event_offset_microseconds=None,
        highest_active_impact_code="NONE",
    )


@pytest.mark.parametrize(
    ("index", "market_change", "calendar_change"),
    (
        (0, {"status_code": StrictStringSubclass("CANONICAL_GOLD_MARKET_FACTS_READY")}, {}),
        (1, {"passed": False}, {}),
        (2, {"bundle_id": "short"}, {}),
        (3, {"quote_ask_decimal": "100.21"}, {}),
        (4, {}, {"upstream_warning": "warning"}),
        (5, {}, {"calendar_snapshot_id": "short"}),
        (6, {}, {"generated_at_utc": "2026-07-10T13:00:00.000001Z"}),
        (7, {}, {"coverage_end_utc": "2026-07-11T13:00:00Z"}),
        (8, {}, {"invalid_event_category": "UNKNOWN"}),
    ),
)
def test_ordered_failure_categories_clear_identity_and_facts(
    index: int,
    market_change: dict[str, object],
    calendar_change: dict[str, object],
) -> None:
    market_changes = dict(market_change)
    quote_ask_decimal = market_changes.pop("quote_ask_decimal", None)
    market = _market_snapshot()
    if quote_ask_decimal is not None:
        market_changes["quote"] = replace(
            market.quote,
            ask_decimal=quote_ask_decimal,
        )
    market = replace(market, **market_changes)
    calendar_changes = dict(calendar_change)
    upstream_warning = calendar_changes.pop("upstream_warning", None)
    invalid_event_category = calendar_changes.pop("invalid_event_category", None)
    calendar = _calendar_snapshot()
    if upstream_warning is not None:
        calendar_changes["upstream_evidence"] = replace(
            calendar.upstream_evidence,
            warning_codes=(upstream_warning,),
        )
    if invalid_event_category is not None:
        calendar_changes["events"] = (
            _event(
                "event.invalid",
                "2026-07-10T13:00:00Z",
                category=invalid_event_category,
            ),
        )
    calendar = replace(calendar, **calendar_changes)
    _assert_failure(_build(market=market, calendar=calendar), *_FAILURES[index])


def test_first_failure_priority_is_not_swappable() -> None:
    market = replace(_market_snapshot(), passed=False, bundle_id="short")
    calendar = replace(
        _calendar_snapshot(),
        source_profile_version="bad",
        generated_at_utc="bad",
    )
    _assert_failure(_build(market=market, calendar=calendar), *_FAILURES[1])

    market = replace(_market_snapshot(), bundle_id="short", quote=object())  # type: ignore[arg-type]
    _assert_failure(_build(market=market, calendar=calendar), *_FAILURES[0])


def test_genuine_g178_failure_envelope_maps_to_upstream_blocked() -> None:
    failed_market = build_canonical_gold_market_facts_snapshot_v1(
        validated_source=object(),  # type: ignore[arg-type]
    )
    assert failed_market.status_code == "CANONICAL_GOLD_MARKET_FACTS_INPUT_INVALID"
    assert failed_market.quote is None
    assert failed_market.timeframes == ()
    assert failed_market.symbol_spec is None
    assert failed_market.freshness is None

    _assert_failure(_build(market=failed_market), *_FAILURES[1])

    later_calendar_failure = replace(
        _calendar_snapshot(),
        upstream_evidence=replace(_upstream(), warning_codes=("warning",)),
    )
    _assert_failure(
        _build(market=failed_market, calendar=later_calendar_failure),
        *_FAILURES[1],
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("quote", object()),
        ("timeframes", (object(),)),
        ("symbol_spec", object()),
        ("freshness", object()),
    ),
)
def test_g178_failure_envelope_with_malformed_present_nested_record_is_input_invalid(
    field: str,
    value: object,
) -> None:
    failed_market = build_canonical_gold_market_facts_snapshot_v1(
        validated_source=object(),  # type: ignore[arg-type]
    )
    polluted_market = replace(failed_market, **{field: value})
    _assert_failure(_build(market=polluted_market), *_FAILURES[0])


def test_ready_envelope_with_missing_nested_facts_is_market_value_invalid() -> None:
    market = replace(
        _market_snapshot(),
        quote=None,
        timeframes=(),
        symbol_spec=None,
        freshness=None,
    )
    _assert_failure(_build(market=market), *_FAILURES[3])


def test_result_contradiction_and_unexpected_exception_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = facts._ready_result

    def contradictory(*args: object, **kwargs: object) -> facts.CanonicalGoldEconomicWindowFactsV1:
        result = original(*args, **kwargs)  # type: ignore[arg-type]
        assert result.summary is not None
        return replace(result, summary=replace(result.summary, relevant_event_count=999))

    monkeypatch.setattr(facts, "_ready_result", contradictory)
    _assert_failure(_build(), *_FAILURES[9])

    def explode(*args: object, **kwargs: object) -> tuple[object, ...]:
        raise RuntimeError("secret path payload checksum")

    monkeypatch.setattr(facts, "_build_event_windows", explode)
    result = _build()
    _assert_failure(result, *_FAILURES[10])
    assert "secret" not in repr(result)
    assert "path" not in repr(result)
    assert "payload" not in repr(result)
    assert "checksum" not in repr(result)


def test_result_validator_independently_rejects_window_and_calendar_age_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_windows = facts._build_event_windows
    original_summary = facts._build_summary

    def drifted_windows(*args: object, **kwargs: object) -> tuple[facts.CanonicalGoldEconomicEventWindowFactsV1, ...]:
        windows = original_windows(*args, **kwargs)  # type: ignore[arg-type]
        return (
            replace(windows[0], window_start_utc="2026-07-10T11:29:59Z"),
            *windows[1:],
        )

    monkeypatch.setattr(facts, "_build_event_windows", drifted_windows)
    _assert_failure(_build(), *_FAILURES[9])

    monkeypatch.setattr(facts, "_build_event_windows", original_windows)

    def drifted_summary(*args: object, **kwargs: object) -> facts.CanonicalGoldEconomicWindowSummaryV1:
        summary = original_summary(*args, **kwargs)  # type: ignore[arg-type]
        return replace(summary, calendar_age_microseconds=200_000)

    monkeypatch.setattr(facts, "_build_summary", drifted_summary)
    _assert_failure(_build(), *_FAILURES[9])


def test_event_count_coverage_bounds_order_uniqueness_and_real_utc_are_strict() -> None:
    reference = _parse_time("2026-07-10T13:00:00Z")
    events_512 = tuple(
        _event(
            f"event.bound.{index:04d}",
            _utc(reference + timedelta(microseconds=index)),
            impact="LOW",
        )
        for index in range(512)
    )
    assert _build(calendar=_calendar_snapshot(events=events_512)).passed is True
    events_513 = events_512 + (
        _event("event.bound.0512", _utc(reference + timedelta(microseconds=512)), impact="LOW"),
    )
    _assert_failure(_build(calendar=_calendar_snapshot(events=events_513)), *_FAILURES[8])

    start = reference - timedelta(seconds=86_400)
    exact_end = start + timedelta(seconds=259_200)
    assert _build(
        calendar=_calendar_snapshot(
            events=(),
            coverage_start_utc=_utc(start),
            coverage_end_utc=_utc(exact_end),
        )
    ).passed is True
    _assert_failure(
        _build(
            calendar=_calendar_snapshot(
                events=(),
                coverage_start_utc=_utc(start),
                coverage_end_utc=_utc(exact_end + timedelta(microseconds=1)),
            )
        ),
        *_FAILURES[7],
    )
    reversed_events = tuple(reversed(_calendar_snapshot().events))
    _assert_failure(_build(calendar=_calendar_snapshot(events=reversed_events)), *_FAILURES[8])
    duplicate = (_event("event.duplicate", "2026-07-10T12:00:00Z"),) * 2
    _assert_failure(_build(calendar=_calendar_snapshot(events=duplicate)), *_FAILURES[8])
    _assert_failure(
        _build(calendar=replace(_calendar_snapshot(), generated_at_utc="2026-02-29T12:00:00Z")),
        *_FAILURES[6],
    )


def test_complete_market_value_predicate_rejects_quote_bar_symbol_and_freshness_drift() -> None:
    base = _market_snapshot()
    invalid = (
        replace(base, quote=replace(base.quote, spread_points=-1)),
        _replace_bar(base, 0, 0, high_decimal="99.00"),
        _replace_bar(base, 0, 1, open_time_utc=base.timeframes[0].bars[0].open_time_utc),
        replace(base, symbol_spec=replace(base.symbol_spec, max_lot_decimal="0.001")),
        replace(base, freshness=replace(base.freshness, tick_age_microseconds=2_000_000)),
    )
    for snapshot in invalid:
        _assert_failure(_build(market=snapshot), *_FAILURES[3])


def test_module_is_ascii_pure_memory_and_isolated() -> None:
    path = Path(facts.__file__)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    assert imports == {
        "__future__",
        "dataclasses",
        "datetime",
        "re",
        "app.services.canonical_gold_market_facts_snapshot_projector",
    }
    assert calls.isdisjoint(
        {
            "open",
            "read_text",
            "read_bytes",
            "getenv",
            "environ",
            "now",
            "utcnow",
            "time",
            "sleep",
            "sort",
            "sorted",
            "total_seconds",
            "build_canonical_gold_market_facts_snapshot_v1",
        }
    )
    assert all(ord(character) < 128 for character in source)


def _build(
    *,
    market: CanonicalGoldMarketFactsSnapshotV1 | None = None,
    calendar: facts.CanonicalGoldEconomicCalendarSnapshotV1 | None = None,
) -> facts.CanonicalGoldEconomicWindowFactsV1:
    return facts.build_canonical_gold_economic_window_facts_v1(
        market_facts_snapshot=_market_snapshot() if market is None else market,
        economic_calendar_snapshot=_calendar_snapshot() if calendar is None else calendar,
    )


def _market_snapshot() -> CanonicalGoldMarketFactsSnapshotV1:
    reference = _parse_time("2026-07-10T13:00:00Z")
    ages = (1_000_000, 1_000_000, 2_000_000)
    bars_payload_time = reference - timedelta(microseconds=ages[1])
    timeframes = tuple(
        CanonicalGoldTimeframeFactsV1(
            timeframe=timeframe,
            period_seconds=period,
            bars=tuple(
                CanonicalGoldBarFactsV1(
                    open_time_utc=_utc(bars_payload_time - timedelta(seconds=period * offset)),
                    open_decimal="100.00",
                    high_decimal="101.00",
                    low_decimal="99.00",
                    close_decimal="100.50",
                    tick_volume=offset,
                    spread_points=20,
                )
                for offset in (3, 2, 1)
            ),
        )
        for timeframe, period in (
            ("M15", 900),
            ("H1", 3600),
            ("H4", 14_400),
            ("D1", 86_400),
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
        bundle_id="bundle_g201_ready",
        sequence=201,
        canonical_symbol="XAUUSD",
        broker_symbol="GOLD",
        reference_time_utc="2026-07-10T13:00:00Z",
        quote=CanonicalGoldQuoteFactsV1(
            bid_decimal="100.00",
            ask_decimal="100.20",
            spread_decimal="0.20",
            spread_points=20,
            digits=2,
            point_decimal="0.01",
            tick_time_utc=_utc(reference - timedelta(microseconds=ages[0])),
        ),
        timeframes=timeframes,
        symbol_spec=CanonicalGoldSymbolFactsV1(
            spec_time_utc=_utc(reference - timedelta(microseconds=ages[2])),
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


def _calendar_snapshot(
    *,
    events: tuple[facts.CanonicalGoldEconomicEventSourceV1, ...] | None = None,
    coverage_start_utc: str = "2026-07-09T13:00:00Z",
    coverage_end_utc: str = "2026-07-11T13:00:00.000001Z",
) -> facts.CanonicalGoldEconomicCalendarSnapshotV1:
    if events is None:
        events = (
            _event("event.elapsed.high", "2026-07-10T12:00:00Z", impact="HIGH"),
            _event("event.active.medium", "2026-07-10T12:50:00Z", impact="MEDIUM"),
            _event("event.high.a", "2026-07-10T13:00:00Z", impact="HIGH"),
            _event("event.medium.a", "2026-07-10T13:00:00Z", impact="MEDIUM"),
            _event("event.next.high.a", "2026-07-10T13:10:00Z", impact="HIGH"),
            _event("event.next.medium.a", "2026-07-10T13:10:00Z", impact="MEDIUM"),
            _event("event.low.only", "2026-07-10T14:00:00Z", impact="LOW"),
            _event("event.cancelled", "2026-07-10T15:00:00Z", status="CANCELLED"),
        )
    return facts.CanonicalGoldEconomicCalendarSnapshotV1(
        contract_version="1.0",
        calendar_schema_version="1.0",
        calendar_snapshot_id="calendar.g201.ready",
        source_profile_version="canonical_gold_economic_calendar_source_v1",
        generated_at_utc="2026-07-10T12:59:59.900000Z",
        coverage_start_utc=coverage_start_utc,
        coverage_end_utc=coverage_end_utc,
        events=events,
        upstream_evidence=_upstream(),
        read_only=True,
        demo_only=True,
        contains_raw_provider_payload=False,
    )


def _upstream() -> facts.CanonicalGoldEconomicCalendarUpstreamEvidenceV1:
    return facts.CanonicalGoldEconomicCalendarUpstreamEvidenceV1(
        adapter_passed=True,
        adapter_status_code="CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY",
        schema_validated=True,
        identity_validated=True,
        timestamps_normalized=True,
        same_snapshot_bound=True,
        warning_codes=(),
        raw_payload_discarded=True,
    )


def _event(
    event_id: str,
    scheduled_at_utc: str,
    *,
    category: str = "US_CPI",
    impact: str = "HIGH",
    status: str = "SCHEDULED",
) -> facts.CanonicalGoldEconomicEventSourceV1:
    return facts.CanonicalGoldEconomicEventSourceV1(
        event_id=event_id,
        scheduled_at_utc=scheduled_at_utc,
        country_code="US",
        currency_code="USD",
        event_category_code=category,
        impact_code=impact,
        source_revision=1,
        event_status_code=status,
    )


def _replace_bar(
    snapshot: CanonicalGoldMarketFactsSnapshotV1,
    timeframe_index: int,
    bar_index: int,
    **changes: object,
) -> CanonicalGoldMarketFactsSnapshotV1:
    timeframes = list(snapshot.timeframes)
    bars = list(timeframes[timeframe_index].bars)
    bars[bar_index] = replace(bars[bar_index], **changes)
    timeframes[timeframe_index] = replace(timeframes[timeframe_index], bars=tuple(bars))
    return replace(snapshot, timeframes=tuple(timeframes))


def _sample_for_type(public_type: type[object]) -> object:
    if public_type is facts.CanonicalGoldEconomicCalendarSnapshotV1:
        return _calendar_snapshot()
    if public_type is facts.CanonicalGoldEconomicCalendarUpstreamEvidenceV1:
        return _upstream()
    if public_type is facts.CanonicalGoldEconomicEventSourceV1:
        return _event("event.sample", "2026-07-10T13:00:00Z")
    result = _build()
    if public_type is facts.CanonicalGoldEconomicWindowFactsV1:
        return result
    if public_type is facts.CanonicalGoldEconomicEventWindowFactsV1:
        return result.event_windows[0]
    assert result.summary is not None
    return result.summary


def _assert_failure(
    result: facts.CanonicalGoldEconomicWindowFactsV1,
    status: str,
    reason: str,
) -> None:
    assert tuple(field.name for field in fields(result)) == _RESULT_FIELDS
    assert result.passed is False
    assert result.status_code == status
    assert result.reason_codes == (reason,)
    assert result.warning_codes == ()
    assert result.identity_available is False
    assert tuple(getattr(result, field) for field in _RESULT_FIELDS[7:21]) == (None,) * 14
    assert result.event_windows == ()
    assert result.summary is None
    _assert_safety(result)


def _assert_safety(result: facts.CanonicalGoldEconomicWindowFactsV1) -> None:
    assert (
        result.read_only,
        result.demo_only,
        result.is_tradable,
        result.can_execute,
        result.is_trading_permission,
        result.is_execution_instruction,
        result.allowed_to_call_ea,
        result.allowed_to_modify_risk,
    ) == (True, True, False, False, False, False, False, False)


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(f"{value[:-1]}+00:00")


def _utc(value: datetime) -> str:
    value = value.astimezone(UTC)
    if value.microsecond:
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")
