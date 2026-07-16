"""Deterministic offline G185 -> G178 -> G196 composition verification only.

W6 remains TESTS_ONLY. This does not verify a ReplayRunner W6 stage, activate
a reader or MT4, or grant EA, order, execution, or trading permission.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import fields
from pathlib import Path

import pytest

from app.services import canonical_gold_market_facts_docs_fixture_integration as g185
from app.services import canonical_gold_market_facts_snapshot_projector as g178
from app.services import canonical_gold_volatility_structure_facts as g196
from tests import (
    test_canonical_gold_volatility_structure_facts_fixture_composition_integration
    as g197,
)


REAL_RUN_COUNT = 5
FAILURE_RUN_COUNT = 3


def test_real_composition_is_deterministic_detached_and_fresh_for_five_runs(
) -> None:
    fixture_before = g197._fixture_state()
    fixed_paths = g185._FIXED_PATHS
    fixed_identity = g185._FIXTURE_IDENTITY
    reference_time = g185._REFERENCE_TIME
    runs = []

    for _ in range(REAL_RUN_COUNT):
        source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
        assert source_result.source is not None
        frozen_source = deepcopy(source_result.source)
        snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
            validated_source=source_result.source
        )
        assert source_result.source == frozen_source
        frozen_snapshot = deepcopy(snapshot)
        result = g196.build_canonical_gold_volatility_structure_facts_v1(
            market_facts_snapshot=snapshot
        )
        assert snapshot == frozen_snapshot
        runs.append((source_result, snapshot, result))

    assert all(run == runs[0] for run in runs)
    graph_ids = tuple(g197._object_graph_ids(run) for run in runs)
    assert all(len(ids) == len(graph_ids[0]) for ids in graph_ids)
    for left_index, left in enumerate(graph_ids):
        for right in graph_ids[left_index + 1 :]:
            assert left.isdisjoint(right)

    for source_result, snapshot, result in runs:
        g197._assert_ready_source_result(source_result)
        g197._assert_ready_snapshot(snapshot)
        g197._assert_ready_result(result, snapshot)
        assert (
            g197._source_identity(source_result.source)
            == g197._snapshot_identity(snapshot)
            == g197._result_identity(result)
            == g197.IDENTITY
        )
        assert g197._object_graph_ids(snapshot).isdisjoint(
            g197._object_graph_ids(result)
        )
        g197._assert_no_sensitive_output(source_result, snapshot, result)

    assert fixture_before.matches(g197._fixture_state())
    assert g185._FIXED_PATHS is fixed_paths
    assert g185._FIXTURE_IDENTITY is fixed_identity
    assert g185._REFERENCE_TIME is reference_time


def test_tampering_with_detached_run_cannot_change_later_real_composition() -> None:
    fixture_before = g197._fixture_state()
    first = _run_real_composition()
    expected = deepcopy(first)
    source_result, snapshot, result = first
    assert source_result.source is not None
    assert result.timeframes
    assert result.timeframes[0].bar_pairs

    object.__setattr__(source_result.source, "bundle_id", "caller-local-source")
    object.__setattr__(snapshot, "bundle_id", "caller-local-snapshot")
    object.__setattr__(result, "status_code", "CALLER_LOCAL_RESULT")
    object.__setattr__(
        result.timeframes[0].bar_pairs[0],
        "true_range_decimal",
        "caller-local-pair",
    )

    subsequent = _run_real_composition()

    assert first != expected
    assert subsequent == expected
    assert g197._object_graph_ids(subsequent).isdisjoint(
        g197._object_graph_ids(first)
    )
    g197._assert_ready_result(subsequent[2], subsequent[1])
    g197._assert_no_sensitive_output(*subsequent)
    assert fixture_before.matches(g197._fixture_state())


def test_delegating_spies_confirm_one_ordered_call_after_genuine_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g197._fixture_state()
    genuine_anchor = _run_real_composition()
    original_source = g185.build_canonical_gold_market_facts_docs_fixture_source_v1
    original_projector = g178.build_canonical_gold_market_facts_snapshot_v1
    original_builder = g196.build_canonical_gold_volatility_structure_facts_v1
    calls: list[str] = []

    def source_spy() -> object:
        calls.append("G185")
        return original_source()

    def projector_spy(*, validated_source: object) -> object:
        calls.append("G178")
        assert g197._source_identity(validated_source) == g197.IDENTITY
        return original_projector(validated_source=validated_source)  # type: ignore[arg-type]

    def builder_spy(*, market_facts_snapshot: object) -> object:
        calls.append("G196")
        assert g197._snapshot_identity(market_facts_snapshot) == g197.IDENTITY
        return original_builder(  # type: ignore[arg-type]
            market_facts_snapshot=market_facts_snapshot
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
            g196,
            "build_canonical_gold_volatility_structure_facts_v1",
            builder_spy,
        )
        observed = _run_real_composition()

    assert calls == ["G185", "G178", "G196"]
    assert observed == genuine_anchor
    assert g197._object_graph_ids(observed).isdisjoint(
        g197._object_graph_ids(genuine_anchor)
    )
    assert fixture_before.matches(g197._fixture_state())


def test_projector_source_mutation_bypass_is_rejected_after_genuine_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g197._fixture_state()
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
    subsequent = _run_real_composition()
    assert subsequent == genuine_anchor
    assert fixture_before.matches(g197._fixture_state())


def test_builder_snapshot_mutation_bypass_is_rejected_after_genuine_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g197._fixture_state()
    genuine_anchor = _run_real_composition()
    original_builder = g196.build_canonical_gold_volatility_structure_facts_v1
    calls: list[str] = []

    def mutating_builder(*, market_facts_snapshot: object) -> object:
        result = original_builder(  # type: ignore[arg-type]
            market_facts_snapshot=market_facts_snapshot
        )
        calls.append("snapshot")
        object.__setattr__(
            market_facts_snapshot.timeframes[0].bars[0],
            "high_decimal",
            "caller-local-mutation",
        )
        return result

    with monkeypatch.context() as context:
        context.setattr(
            g196,
            "build_canonical_gold_volatility_structure_facts_v1",
            mutating_builder,
        )
        with pytest.raises(AssertionError):
            _run_real_composition()

    assert calls == ["snapshot"]
    subsequent = _run_real_composition()
    assert subsequent == genuine_anchor
    assert fixture_before.matches(g197._fixture_state())


def test_invalid_inputs_are_deterministic_sanitized_and_fresh() -> None:
    results = tuple(
        g196.build_canonical_gold_volatility_structure_facts_v1(
            market_facts_snapshot=object()  # type: ignore[arg-type]
        )
        for _ in range(FAILURE_RUN_COUNT)
    )

    assert all(result == results[0] for result in results)
    assert len({id(result) for result in results}) == FAILURE_RUN_COUNT
    for result in results:
        _assert_exact_failure(
            result,
            status="CANONICAL_GOLD_VOLATILITY_STRUCTURE_INPUT_INVALID",
            reason="GOLD_VOLATILITY_STRUCTURE_INPUT_TYPE_INVALID",
        )
        g197._assert_no_sensitive_output(result)


def test_post_anchor_exceptions_are_deterministic_sanitized_and_fresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = g197._fixture_state()
    source_result, snapshot, genuine_anchor = _run_real_composition()
    frozen_snapshot = deepcopy(snapshot)
    calls: list[tuple[object, ...]] = []

    def raising_ready_result(*args: object) -> object:
        calls.append(args)
        raise RuntimeError("sensitive composition failure detail")

    with monkeypatch.context() as context:
        context.setattr(g196, "_ready_result", raising_ready_result)
        failures = tuple(
            g196.build_canonical_gold_volatility_structure_facts_v1(
                market_facts_snapshot=snapshot
            )
            for _ in range(FAILURE_RUN_COUNT)
        )

    assert snapshot == frozen_snapshot
    assert len(calls) == FAILURE_RUN_COUNT
    assert all(call[0] is snapshot and len(call) == 2 for call in calls)
    assert all(result == failures[0] for result in failures)
    assert len({id(result) for result in failures}) == FAILURE_RUN_COUNT
    for result in failures:
        _assert_exact_failure(
            result,
            status="CANONICAL_GOLD_VOLATILITY_STRUCTURE_SAFE_FAILURE",
            reason="GOLD_VOLATILITY_STRUCTURE_EXCEPTION_SANITIZED",
        )
        g197._assert_no_sensitive_output(result)

    subsequent = _run_real_composition()
    assert subsequent == (source_result, snapshot, genuine_anchor)
    assert g197._object_graph_ids(subsequent).isdisjoint(
        g197._object_graph_ids((source_result, snapshot, genuine_anchor))
    )
    assert fixture_before.matches(g197._fixture_state())


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
            "build_canonical_gold_volatility_structure_facts_v1",
        }
    )
    names = {node.id for node in ast.walk(primary) if isinstance(node, ast.Name)}
    attributes = {
        node.attr for node in ast.walk(primary) if isinstance(node, ast.Attribute)
    }

    assert production_calls == (
        "build_canonical_gold_market_facts_docs_fixture_source_v1",
        "build_canonical_gold_market_facts_snapshot_v1",
        "build_canonical_gold_volatility_structure_facts_v1",
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

    assert "deterministic offline g185 -> g178 -> g196 composition verification only" in scope
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


def _run_real_composition() -> tuple[object, object, object]:
    source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
    assert source_result.source is not None
    frozen_source = deepcopy(source_result.source)
    snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
        validated_source=source_result.source
    )
    assert source_result.source == frozen_source
    frozen_snapshot = deepcopy(snapshot)
    result = g196.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=snapshot
    )
    assert snapshot == frozen_snapshot
    return source_result, snapshot, result


def _assert_exact_failure(result: object, *, status: str, reason: str) -> None:
    assert type(result) is g196.CanonicalGoldVolatilityStructureFactsV1
    assert tuple(field.name for field in fields(type(result))) == g197.RESULT_FIELDS
    assert result.contract_version == "1.0"
    assert result.facts_profile_version == (
        "canonical_gold_volatility_structure_profile_v1"
    )
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
    ) == (None, None, None, None, None, None, None)
    assert result.timeframes == ()
    assert result.total_pair_count == 0
    for name, expected in g197.SAFETY_FLAGS.items():
        assert getattr(result, name) is expected
