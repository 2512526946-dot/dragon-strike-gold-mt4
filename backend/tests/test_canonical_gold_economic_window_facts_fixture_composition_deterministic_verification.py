"""Deterministic offline G185 -> G178 -> G204 -> G201 verification only.

W6 remains TESTS_ONLY. This does not verify a ReplayRunner W6 stage, activate
a reader or MT4, or grant EA, order, execution, or trading permission.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import fields
from pathlib import Path

import pytest

from app.services import canonical_gold_economic_calendar_source_adapter as g204
from app.services import canonical_gold_economic_window_facts as g201
from app.services import canonical_gold_market_facts_docs_fixture_integration as g185
from app.services import canonical_gold_market_facts_snapshot_projector as g178
from tests import (
    test_canonical_gold_economic_window_facts_fixture_composition_integration
    as g206,
)


REAL_RUN_COUNT = 5
FAILURE_RUN_COUNT = 3


def test_real_composition_is_deterministic_detached_and_fresh_for_five_runs(
) -> None:
    fixture_before = g206._fixture_state()
    fixed_market_paths = g185._FIXED_PATHS
    fixed_market_identity = g185._FIXTURE_IDENTITY
    fixed_market_reference_time = g185._REFERENCE_TIME
    fixed_calendar_path = g204._EXPECTED_FIXTURE_PATH
    fixed_calendar_reference_time = g204._FIXED_REFERENCE_TIME
    fixed_calendar_identity = g204._EXPECTED_IDENTITY
    fixed_calendar_policy = g204._READ_POLICY
    runs = []

    for _ in range(REAL_RUN_COUNT):
        source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
        assert source_result.source is not None
        frozen_source = deepcopy(source_result.source)
        market_snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
            validated_source=source_result.source
        )
        assert source_result.source == frozen_source

        authority = g206._calendar_authority()
        frozen_authority = g204._authority_snapshot(authority)
        calendar_result = (
            g204.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
                authority=authority
            )
        )
        assert g204._authority_snapshot(authority) == frozen_authority
        assert calendar_result.snapshot is not None

        frozen_market_snapshot = deepcopy(market_snapshot)
        frozen_calendar_snapshot = deepcopy(calendar_result.snapshot)
        result = g201.build_canonical_gold_economic_window_facts_v1(
            market_facts_snapshot=market_snapshot,
            economic_calendar_snapshot=calendar_result.snapshot,
        )
        assert market_snapshot == frozen_market_snapshot
        assert calendar_result.snapshot == frozen_calendar_snapshot
        runs.append((source_result, market_snapshot, calendar_result, result))

    assert all(run == runs[0] for run in runs)
    graph_ids = tuple(g206._object_graph_ids(run) for run in runs)
    assert all(len(ids) == len(graph_ids[0]) for ids in graph_ids)
    for left_index, left in enumerate(graph_ids):
        for right in graph_ids[left_index + 1 :]:
            assert left.isdisjoint(right)

    for source_result, market_snapshot, calendar_result, result in runs:
        g206._assert_ready_source_result(source_result)
        g206._assert_ready_market_snapshot(market_snapshot)
        g206._assert_ready_calendar_result(calendar_result)
        g206._assert_ready_result(result)
        assert calendar_result.snapshot is not None
        assert (
            g206._market_identity(source_result.source)
            == g206._market_identity(market_snapshot)
            == g206._result_market_identity(result)
            == g206.MARKET_IDENTITY
        )
        assert (
            g206._calendar_identity(calendar_result.snapshot)
            == g206._result_calendar_identity(result)
            == g206.CALENDAR_IDENTITY
        )
        element_graphs = tuple(
            g206._object_graph_ids(value)
            for value in (
                source_result,
                market_snapshot,
                calendar_result,
                result,
            )
        )
        assert all(
            left.isdisjoint(right)
            for left_index, left in enumerate(element_graphs)
            for right in element_graphs[left_index + 1 :]
        )
        g206._assert_no_sensitive_output(
            source_result,
            market_snapshot,
            calendar_result,
            result,
        )

    assert fixture_before.matches(g206._fixture_state())
    assert g185._FIXED_PATHS is fixed_market_paths
    assert g185._FIXTURE_IDENTITY is fixed_market_identity
    assert g185._REFERENCE_TIME is fixed_market_reference_time
    assert g204._EXPECTED_FIXTURE_PATH is fixed_calendar_path
    assert g204._FIXED_REFERENCE_TIME is fixed_calendar_reference_time
    assert g204._EXPECTED_IDENTITY is fixed_calendar_identity
    assert g204._READ_POLICY is fixed_calendar_policy


def test_tampering_with_detached_run_cannot_change_later_real_composition() -> None:
    fixture_before = g206._fixture_state()
    first = _run_real_composition()
    expected = deepcopy(first)
    source_result, market_snapshot, calendar_result, result = first
    assert source_result.source is not None
    assert market_snapshot.quote is not None
    assert calendar_result.snapshot is not None
    assert calendar_result.snapshot.events
    assert result.event_windows
    assert result.summary is not None

    object.__setattr__(source_result.source.live_tick, "bid", -1.0)
    object.__setattr__(
        market_snapshot.quote,
        "bid_decimal",
        "caller-local-market",
    )
    object.__setattr__(
        calendar_result.snapshot.events[0],
        "impact_code",
        "LOW",
    )
    object.__setattr__(
        result.event_windows[0],
        "impact_code",
        "LOW",
    )
    object.__setattr__(
        result.summary,
        "highest_active_impact_code",
        "NONE",
    )

    subsequent = _run_real_composition()

    assert first != expected
    assert subsequent == expected
    assert g206._object_graph_ids(subsequent).isdisjoint(
        g206._object_graph_ids(first)
    )
    g206._assert_ready_result(subsequent[3])
    g206._assert_no_sensitive_output(*subsequent)
    assert fixture_before.matches(g206._fixture_state())


def test_delegating_spies_confirm_one_ordered_call_after_genuine_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g206._fixture_state()
    genuine_anchor = _run_real_composition()
    original_source = g185.build_canonical_gold_market_facts_docs_fixture_source_v1
    original_projector = g178.build_canonical_gold_market_facts_snapshot_v1
    original_calendar = (
        g204.build_server_owned_canonical_gold_economic_calendar_snapshot_v1
    )
    original_builder = g201.build_canonical_gold_economic_window_facts_v1
    calls: list[str] = []

    def source_spy() -> object:
        calls.append("G185")
        return original_source()

    def projector_spy(*, validated_source: object) -> object:
        calls.append("G178")
        assert g206._market_identity(validated_source) == g206.MARKET_IDENTITY
        return original_projector(validated_source=validated_source)  # type: ignore[arg-type]

    def calendar_spy(*, authority: object) -> object:
        calls.append("G204")
        assert g204._authority_snapshot(authority) == g204._authority_snapshot(
            g206._calendar_authority()
        )
        return original_calendar(authority=authority)  # type: ignore[arg-type]

    def builder_spy(
        *,
        market_facts_snapshot: object,
        economic_calendar_snapshot: object,
    ) -> object:
        calls.append("G201")
        assert (
            g206._market_identity(market_facts_snapshot)
            == g206.MARKET_IDENTITY
        )
        assert (
            g206._calendar_identity(economic_calendar_snapshot)
            == g206.CALENDAR_IDENTITY
        )
        return original_builder(  # type: ignore[arg-type]
            market_facts_snapshot=market_facts_snapshot,
            economic_calendar_snapshot=economic_calendar_snapshot,
        )

    with monkeypatch.context() as context:
        context.setattr(
            g185,
            "build_canonical_gold_market_facts_docs_fixture_source_v1",
            source_spy,
        )
        context.setattr(
            g178,
            "build_canonical_gold_market_facts_snapshot_v1",
            projector_spy,
        )
        context.setattr(
            g204,
            "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
            calendar_spy,
        )
        context.setattr(
            g201,
            "build_canonical_gold_economic_window_facts_v1",
            builder_spy,
        )
        observed = _run_real_composition()

    assert calls == ["G185", "G178", "G204", "G201"]
    assert observed == genuine_anchor
    assert g206._object_graph_ids(observed).isdisjoint(
        g206._object_graph_ids(genuine_anchor)
    )
    assert fixture_before.matches(g206._fixture_state())


def test_projector_source_mutation_bypass_is_rejected_after_genuine_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g206._fixture_state()
    genuine_anchor = _run_real_composition()
    original_projector = g178.build_canonical_gold_market_facts_snapshot_v1
    calls: list[str] = []

    def mutating_projector(*, validated_source: object) -> object:
        snapshot = original_projector(  # type: ignore[arg-type]
            validated_source=validated_source
        )
        calls.append("source")
        object.__setattr__(validated_source.live_tick, "bid", -1.0)
        return snapshot

    with monkeypatch.context() as context:
        context.setattr(
            g178,
            "build_canonical_gold_market_facts_snapshot_v1",
            mutating_projector,
        )
        with pytest.raises(AssertionError):
            _run_real_composition()

    assert calls == ["source"]
    assert _run_real_composition() == genuine_anchor
    assert fixture_before.matches(g206._fixture_state())


def test_builder_market_snapshot_mutation_bypass_is_rejected_after_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g206._fixture_state()
    genuine_anchor = _run_real_composition()
    original_builder = g201.build_canonical_gold_economic_window_facts_v1
    calls: list[str] = []

    def mutating_builder(
        *,
        market_facts_snapshot: object,
        economic_calendar_snapshot: object,
    ) -> object:
        result = original_builder(  # type: ignore[arg-type]
            market_facts_snapshot=market_facts_snapshot,
            economic_calendar_snapshot=economic_calendar_snapshot,
        )
        calls.append("market")
        object.__setattr__(
            market_facts_snapshot.timeframes[0].bars[0],
            "high_decimal",
            "caller-local-mutation",
        )
        return result

    with monkeypatch.context() as context:
        context.setattr(
            g201,
            "build_canonical_gold_economic_window_facts_v1",
            mutating_builder,
        )
        with pytest.raises(AssertionError):
            _run_real_composition()

    assert calls == ["market"]
    assert _run_real_composition() == genuine_anchor
    assert fixture_before.matches(g206._fixture_state())


def test_builder_calendar_snapshot_mutation_bypass_is_rejected_after_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g206._fixture_state()
    genuine_anchor = _run_real_composition()
    original_builder = g201.build_canonical_gold_economic_window_facts_v1
    calls: list[str] = []

    def mutating_builder(
        *,
        market_facts_snapshot: object,
        economic_calendar_snapshot: object,
    ) -> object:
        result = original_builder(  # type: ignore[arg-type]
            market_facts_snapshot=market_facts_snapshot,
            economic_calendar_snapshot=economic_calendar_snapshot,
        )
        calls.append("calendar")
        object.__setattr__(
            economic_calendar_snapshot.events[0],
            "event_category_code",
            "US_GDP",
        )
        return result

    with monkeypatch.context() as context:
        context.setattr(
            g201,
            "build_canonical_gold_economic_window_facts_v1",
            mutating_builder,
        )
        with pytest.raises(AssertionError):
            _run_real_composition()

    assert calls == ["calendar"]
    assert _run_real_composition() == genuine_anchor
    assert fixture_before.matches(g206._fixture_state())


def test_calendar_authority_mutation_bypass_is_rejected_after_genuine_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g206._fixture_state()
    genuine_anchor = _run_real_composition()
    original_calendar = (
        g204.build_server_owned_canonical_gold_economic_calendar_snapshot_v1
    )
    calls: list[str] = []

    def mutating_calendar(*, authority: object) -> object:
        result = original_calendar(authority=authority)  # type: ignore[arg-type]
        calls.append("authority")
        replacement = deepcopy(authority.expected_identity)
        object.__setattr__(replacement, "calendar_snapshot_id", "drift")
        object.__setattr__(authority, "expected_identity", replacement)
        return result

    with monkeypatch.context() as context:
        context.setattr(
            g204,
            "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
            mutating_calendar,
        )
        with pytest.raises(AssertionError):
            _run_real_composition()

    assert calls == ["authority"]
    assert _run_real_composition() == genuine_anchor
    assert fixture_before.matches(g206._fixture_state())


def test_invalid_inputs_are_deterministic_sanitized_and_fresh() -> None:
    results = tuple(
        g201.build_canonical_gold_economic_window_facts_v1(
            market_facts_snapshot=object(),  # type: ignore[arg-type]
            economic_calendar_snapshot=object(),  # type: ignore[arg-type]
        )
        for _ in range(FAILURE_RUN_COUNT)
    )

    assert all(result == results[0] for result in results)
    assert len({id(result) for result in results}) == FAILURE_RUN_COUNT
    for result in results:
        _assert_exact_failure(
            result,
            status="CANONICAL_GOLD_ECONOMIC_WINDOW_INPUT_INVALID",
            reason="GOLD_ECONOMIC_WINDOW_INPUT_TYPE_INVALID",
        )
        g206._assert_no_sensitive_output(result)


def test_post_anchor_exceptions_are_deterministic_sanitized_and_fresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g206._fixture_state()
    source_result, market_snapshot, calendar_result, genuine_anchor = (
        _run_real_composition()
    )
    assert calendar_result.snapshot is not None
    frozen_market_snapshot = deepcopy(market_snapshot)
    frozen_calendar_snapshot = deepcopy(calendar_result.snapshot)
    calls: list[tuple[object, ...]] = []

    def raising_ready_result(*args: object) -> object:
        calls.append(args)
        raise RuntimeError("sensitive composition failure detail")

    with monkeypatch.context() as context:
        context.setattr(g201, "_ready_result", raising_ready_result)
        failures = tuple(
            g201.build_canonical_gold_economic_window_facts_v1(
                market_facts_snapshot=market_snapshot,
                economic_calendar_snapshot=calendar_result.snapshot,
            )
            for _ in range(FAILURE_RUN_COUNT)
        )

    assert market_snapshot == frozen_market_snapshot
    assert calendar_result.snapshot == frozen_calendar_snapshot
    assert len(calls) == FAILURE_RUN_COUNT
    assert all(
        call[0] is market_snapshot
        and call[1] is calendar_result.snapshot
        and len(call) == 4
        for call in calls
    )
    assert all(result == failures[0] for result in failures)
    assert len({id(result) for result in failures}) == FAILURE_RUN_COUNT
    for result in failures:
        _assert_exact_failure(
            result,
            status="CANONICAL_GOLD_ECONOMIC_WINDOW_SAFE_FAILURE",
            reason="GOLD_ECONOMIC_WINDOW_EXCEPTION_SANITIZED",
        )
        g206._assert_no_sensitive_output(result)

    subsequent = _run_real_composition()
    assert subsequent == (
        source_result,
        market_snapshot,
        calendar_result,
        genuine_anchor,
    )
    assert g206._object_graph_ids(subsequent).isdisjoint(
        g206._object_graph_ids(
            (source_result, market_snapshot, calendar_result, genuine_anchor)
        )
    )
    assert fixture_before.matches(g206._fixture_state())


def test_primary_verification_anchor_has_exact_unpatched_call_order() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    primary = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "test_real_composition_is_deterministic_detached_and_fresh_for_five_runs"
    )
    production_calls = tuple(
        node.func.attr
        for node in ast.walk(primary)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr
        in {
            "build_canonical_gold_market_facts_docs_fixture_source_v1",
            "build_canonical_gold_market_facts_snapshot_v1",
            "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
            "build_canonical_gold_economic_window_facts_v1",
        }
    )
    names = {node.id for node in ast.walk(primary) if isinstance(node, ast.Name)}
    attributes = {
        node.attr for node in ast.walk(primary) if isinstance(node, ast.Attribute)
    }

    assert production_calls == (
        "build_canonical_gold_market_facts_docs_fixture_source_v1",
        "build_canonical_gold_market_facts_snapshot_v1",
        "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
        "build_canonical_gold_economic_window_facts_v1",
    )
    assert names.isdisjoint({"monkeypatch", "patch", "Mock", "MagicMock", "spy"})
    assert attributes.isdisjoint({"setattr", "setitem"})


def test_verification_scope_is_offline_non_activating_and_bounded() -> None:
    scope = " ".join((__doc__ or "").casefold().split())
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert (
        "deterministic offline g185 -> g178 -> g204 -> g201 verification only"
        in scope
    )
    assert "w6 remains tests_only" in scope
    assert "does not verify a replayrunner w6 stage" in scope
    assert "activate a reader or mt4" in scope
    assert "ea, order, execution, or trading permission" in scope
    assert not any(
        forbidden in imported
        for forbidden in (
            "canonical_bundle_replay_runner",
            "fastapi",
            "requests",
            "httpx",
            "socket",
            "subprocess",
        )
        for imported in imports
    )


def _run_real_composition() -> tuple[object, object, object, object]:
    source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
    assert source_result.source is not None
    frozen_source = deepcopy(source_result.source)
    market_snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
        validated_source=source_result.source
    )
    assert source_result.source == frozen_source

    authority = g206._calendar_authority()
    frozen_authority = g204._authority_snapshot(authority)
    calendar_result = (
        g204.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
            authority=authority
        )
    )
    assert g204._authority_snapshot(authority) == frozen_authority
    assert calendar_result.snapshot is not None

    frozen_market_snapshot = deepcopy(market_snapshot)
    frozen_calendar_snapshot = deepcopy(calendar_result.snapshot)
    result = g201.build_canonical_gold_economic_window_facts_v1(
        market_facts_snapshot=market_snapshot,
        economic_calendar_snapshot=calendar_result.snapshot,
    )
    assert market_snapshot == frozen_market_snapshot
    assert calendar_result.snapshot == frozen_calendar_snapshot
    return source_result, market_snapshot, calendar_result, result


def _assert_exact_failure(result: object, *, status: str, reason: str) -> None:
    assert type(result) is g201.CanonicalGoldEconomicWindowFactsV1
    assert tuple(field.name for field in fields(type(result))) == g206.RESULT_FIELDS
    assert result.contract_version == "1.0"
    assert result.facts_profile_version == "canonical_gold_economic_window_profile_v1"
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
        result.calendar_contract_version,
        result.calendar_schema_version,
        result.calendar_snapshot_id,
        result.calendar_source_profile_version,
        result.calendar_generated_at_utc,
        result.calendar_coverage_start_utc,
        result.calendar_coverage_end_utc,
    ) == (None,) * 14
    assert result.event_windows == ()
    assert result.summary is None
    for name, expected in g206.SAFETY_FLAGS.items():
        assert getattr(result, name) is expected
