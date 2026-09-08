from __future__ import annotations

import ast
from collections.abc import Callable
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import DecimalException
import inspect
from pathlib import Path

import pytest

from app.services import canonical_gold_facts_replay_stage as stage
from app.services.demo_readonly_canonical_diagnostics_summary_validator import (
    is_safe_demo_readonly_canonical_diagnostics_summary,
)


EXPECTED_EXPORTS = (
    "CanonicalGoldFactsReplayCaseV1",
    "CanonicalGoldFactsReplayExpectedOracleV1",
    "CanonicalGoldFactsReplayRegistryRecordV1",
    "CanonicalGoldFactsReplayResultV1",
    "run_canonical_gold_facts_replay_case_v1",
)
EXPECTED_PUBLIC_FIELDS = (
    (
        stage.CanonicalGoldFactsReplayCaseV1,
        (
            "replay_contract_version",
            "stage_contract_version",
            "stage_id",
            "case_id",
            "fixture_id",
        ),
    ),
    (
        stage.CanonicalGoldFactsReplayExpectedOracleV1,
        (
            "diagnostics_result",
            "market_source_result",
            "market_facts_snapshot",
            "session_spread_freshness_facts",
            "volatility_structure_facts",
            "economic_calendar_result",
            "economic_window_facts",
        ),
    ),
    (
        stage.CanonicalGoldFactsReplayRegistryRecordV1,
        (
            "registry_version",
            "replay_contract_version",
            "stage_contract_version",
            "authority_profile_version",
            "stage_id",
            "case_id",
            "fixture_id",
            "diagnostics_case",
            "market_source_profile_version",
            "market_facts_contract_version",
            "session_facts_profile_version",
            "volatility_facts_profile_version",
            "calendar_source_profile_version",
            "economic_window_facts_profile_version",
            "reference_time_utc",
            "expected_market_identity",
            "expected_calendar_identity",
            "expected_oracle",
        ),
    ),
    (
        stage.CanonicalGoldFactsReplayResultV1,
        (
            "replay_contract_version",
            "stage_contract_version",
            "registry_version",
            "stage_id",
            "passed",
            "status_code",
            "reason_codes",
            "identity_available",
            "case_id",
            "fixture_id",
            "completed_stage_ids",
            "diagnostics_result",
            "market_source_result",
            "market_facts_snapshot",
            "session_spread_freshness_facts",
            "volatility_structure_facts",
            "economic_calendar_result",
            "economic_window_facts",
            "read_only",
            "demo_only",
            "is_tradable",
            "can_execute",
            "is_trading_permission",
            "is_execution_instruction",
            "allowed_to_call_ea",
            "allowed_to_modify_risk",
        ),
    ),
)


def _case() -> stage.CanonicalGoldFactsReplayCaseV1:
    return stage.CanonicalGoldFactsReplayCaseV1(
        replay_contract_version=stage.REPLAY_CONTRACT_VERSION,
        stage_contract_version=stage.STAGE_CONTRACT_VERSION,
        stage_id=stage.STAGE_ID,
        case_id="canonical_docs_ready",
        fixture_id="canonical_docs_fixture_v1",
    )


def _run() -> stage.CanonicalGoldFactsReplayResultV1:
    return stage.run_canonical_gold_facts_replay_case_v1(replay_case=_case())


def _nested_results(result: stage.CanonicalGoldFactsReplayResultV1) -> tuple[object, ...]:
    return (
        result.diagnostics_result,
        result.market_source_result,
        result.market_facts_snapshot,
        result.session_spread_freshness_facts,
        result.volatility_structure_facts,
        result.economic_calendar_result,
        result.economic_window_facts,
    )


def _dataclass_ids(value: object) -> tuple[int, ...]:
    found: list[int] = []

    def visit(item: object) -> None:
        if is_dataclass(item) and not isinstance(item, type):
            found.append(id(item))
            for field in fields(item):
                visit(getattr(item, field.name))
        elif type(item) in {tuple, list}:
            for child in item:
                visit(child)
        elif type(item) is dict:
            for key, child in item.items():
                visit(key)
                visit(child)

    visit(value)
    return tuple(found)


def _install_delegating_capsule(
    monkeypatch: pytest.MonkeyPatch,
    *,
    mutation_stage: str | None = None,
    result_transform: tuple[str, Callable[[object], object]] | None = None,
) -> list[str]:
    calls: list[str] = []
    originals = {
        "diagnostics": stage.replay_v1.run_canonical_bundle_replay_case,
        "source": stage.market_fixture.build_canonical_gold_market_facts_docs_fixture_source_v1,
        "snapshot": stage.market_facts.build_canonical_gold_market_facts_snapshot_v1,
        "session": stage.session_facts.build_canonical_gold_session_spread_freshness_facts_v1,
        "volatility": stage.volatility.build_canonical_gold_volatility_structure_facts_v1,
        "calendar": stage.calendar.build_server_owned_canonical_gold_economic_calendar_snapshot_v1,
        "economic": stage.economic.build_canonical_gold_economic_window_facts_v1,
    }

    def finish(name: str, result: object) -> object:
        if result_transform is not None and result_transform[0] == name:
            return result_transform[1](result)
        return result

    def diagnostics(*, replay_case: object) -> object:
        calls.append("diagnostics")
        return finish("diagnostics", originals["diagnostics"](replay_case=replay_case))

    def source() -> object:
        calls.append("source")
        return finish("source", originals["source"]())

    def snapshot(*, validated_source: object) -> object:
        calls.append("snapshot")
        if mutation_stage == "source":
            object.__setattr__(validated_source.live_tick, "bid", validated_source.live_tick.bid + 1.0)
        return finish("snapshot", originals["snapshot"](validated_source=validated_source))

    def session(*, market_facts_snapshot: object) -> object:
        calls.append("session")
        if mutation_stage == "snapshot":
            object.__setattr__(market_facts_snapshot.quote, "bid_decimal", "9999.99")
        return finish("session", originals["session"](market_facts_snapshot=market_facts_snapshot))

    def volatility(*, market_facts_snapshot: object) -> object:
        calls.append("volatility")
        return finish("volatility", originals["volatility"](market_facts_snapshot=market_facts_snapshot))

    def calendar(*, authority: object) -> object:
        calls.append("calendar")
        return finish("calendar", originals["calendar"](authority=authority))

    def economic(*, market_facts_snapshot: object, economic_calendar_snapshot: object) -> object:
        calls.append("economic")
        return finish("economic", originals["economic"](
            market_facts_snapshot=market_facts_snapshot,
            economic_calendar_snapshot=economic_calendar_snapshot,
        ))

    bindings = (
        (stage.replay_v1, "run_canonical_bundle_replay_case", "_EXPECTED_RUN_DIAGNOSTICS", "diagnostics_runner", diagnostics),
        (stage.market_fixture, "build_canonical_gold_market_facts_docs_fixture_source_v1", "_EXPECTED_BUILD_MARKET_SOURCE", "market_source_builder", source),
        (stage.market_facts, "build_canonical_gold_market_facts_snapshot_v1", "_EXPECTED_BUILD_MARKET_FACTS", "market_projector", snapshot),
        (stage.session_facts, "build_canonical_gold_session_spread_freshness_facts_v1", "_EXPECTED_BUILD_SESSION_FACTS", "session_builder", session),
        (stage.volatility, "build_canonical_gold_volatility_structure_facts_v1", "_EXPECTED_BUILD_VOLATILITY_FACTS", "volatility_builder", volatility),
        (stage.calendar, "build_server_owned_canonical_gold_economic_calendar_snapshot_v1", "_EXPECTED_BUILD_CALENDAR", "calendar_builder", calendar),
        (stage.economic, "build_canonical_gold_economic_window_facts_v1", "_EXPECTED_BUILD_ECONOMIC_FACTS", "economic_builder", economic),
    )
    capsule_changes: dict[str, object] = {}
    for module, public_name, expected_name, capsule_name, wrapper in bindings:
        monkeypatch.setattr(module, public_name, wrapper)
        monkeypatch.setattr(stage, expected_name, wrapper)
        capsule_changes[capsule_name] = wrapper
    capsule = replace(stage._APPROVED_CAPSULE, **capsule_changes)
    monkeypatch.setattr(stage, "_APPROVED_CAPSULE", capsule)
    monkeypatch.setattr(stage, "_CAPSULE", capsule)
    return calls


def test_public_interface_and_exact_production_schemas_are_frozen() -> None:
    assert stage.__all__ == EXPECTED_EXPORTS
    assert tuple(inspect.signature(stage.run_canonical_gold_facts_replay_case_v1).parameters) == (
        "replay_case",
    )
    assert inspect.signature(stage.run_canonical_gold_facts_replay_case_v1).parameters[
        "replay_case"
    ].kind is inspect.Parameter.KEYWORD_ONLY
    for class_object, ordered_fields in EXPECTED_PUBLIC_FIELDS:
        assert tuple(field.name for field in fields(class_object)) == ordered_fields
        assert class_object.__dataclass_params__.frozen is True
        assert "__slots__" in class_object.__dict__
    assert len(stage._PRODUCTION_SCHEMAS) == 28
    assert len(stage._SCHEMA_BY_CLASS) == len(stage._SCHEMA_BY_TYPE_CODE) == 28
    assert all(
        tuple(field.name for field in fields(schema.class_object)) == schema.ordered_fields
        for schema in stage._PRODUCTION_SCHEMAS
    )
    with pytest.raises(FrozenInstanceError):
        _case().case_id = "changed"  # type: ignore[misc]


def test_fixed_case_runs_all_seven_stages_and_matches_static_oracle() -> None:
    before = stage._fixture_state(stage._CAPSULE)
    result = _run()
    assert result.passed is True
    assert result.status_code == stage.CANONICAL_GOLD_FACTS_REPLAY_MATCHED
    assert result.reason_codes == ()
    assert result.identity_available is True
    assert result.case_id == "canonical_docs_ready"
    assert result.fixture_id == "canonical_docs_fixture_v1"
    assert result.completed_stage_ids == stage.STAGE_ORDER
    assert stage._result_is_safe(result) is True
    assert stage._fixture_state(stage._CAPSULE) == before
    for index, nested in enumerate(_nested_results(result)):
        assert type(nested) is stage._RESULT_TYPES[index]
        assert stage._freeze_value(
            nested,
            allow_summary_containers=index == 0,
            allow_market_floats=index == 1,
        ) == stage._FROZEN_ORACLES[index]


def test_repeated_results_are_equal_fresh_and_fully_detached() -> None:
    first = _run()
    second = _run()
    assert first == second
    first_ids = set(_dataclass_ids(first))
    second_ids = set(_dataclass_ids(second))
    assert first_ids
    assert second_ids
    assert first_ids.isdisjoint(second_ids)
    assert first.completed_stage_ids is not stage.STAGE_ORDER
    assert first.completed_stage_ids == stage.STAGE_ORDER
    assert first.market_source_result.source is not first.market_facts_snapshot


def test_delegating_authority_proves_exact_single_call_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_delegating_capsule(monkeypatch)
    result = _run()
    assert result.passed is True
    assert calls == [
        "diagnostics",
        "source",
        "snapshot",
        "session",
        "volatility",
        "calendar",
        "economic",
    ]


@pytest.mark.parametrize("mutation_stage", ("source", "snapshot"))
def test_nested_input_mutation_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    mutation_stage: str,
) -> None:
    calls = _install_delegating_capsule(monkeypatch, mutation_stage=mutation_stage)
    result = _run()
    assert result.passed is False
    assert result.status_code == stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID
    assert result.reason_codes == (stage.GOLD_FACTS_REPLAY_RESULT_INVALID,)
    assert result.completed_stage_ids == ()
    assert result.identity_available is False
    expected_prefix = ["diagnostics", "source", "snapshot"]
    if mutation_stage == "snapshot":
        expected_prefix.append("session")
    assert calls == expected_prefix


def test_input_registry_and_authority_fail_closed_before_stage_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid = replace(_case(), stage_id="wrong")
    assert stage.run_canonical_gold_facts_replay_case_v1(replay_case=invalid).status_code == (
        stage.CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID
    )

    drifted_record = replace(stage._REGISTRY[0], fixture_id="drifted")
    monkeypatch.setattr(stage, "_REGISTRY", (drifted_record,))
    assert _run().status_code == stage.CANONICAL_GOLD_FACTS_REPLAY_REGISTRY_INVALID
    monkeypatch.setattr(stage, "_REGISTRY", stage._APPROVED_REGISTRY)

    drifted_capsule = replace(stage._CAPSULE, diagnostics_runner=object())
    monkeypatch.setattr(stage, "_CAPSULE", drifted_capsule)
    assert _run().status_code == stage.CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID


def test_oracle_grammar_is_lossless_and_type_disjoint() -> None:
    encoded = {
        stage._freeze_value(["x"], allow_summary_containers=True),
        stage._freeze_value(("x",), allow_summary_containers=True),
        stage._freeze_value({"x": 1}, allow_summary_containers=True),
        stage._freeze_value(1.5, allow_market_floats=True),
        stage._freeze_value((1.5).hex()),
    }
    assert len(encoded) == 5
    assert stage._freeze_value(0.0, allow_market_floats=True) != stage._freeze_value(
        -0.0,
        allow_market_floats=True,
    )
    for invalid in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(TypeError):
            stage._freeze_value(invalid, allow_market_floats=True)


def test_all_outer_failures_clear_evidence_and_keep_fixed_safety_flags() -> None:
    assert len(stage._STATUS_REASONS) == 14
    for status, reasons in stage._STATUS_REASONS:
        if status == stage.CANONICAL_GOLD_FACTS_REPLAY_MATCHED:
            continue
        result = stage._failure(status, reasons[0])
        assert stage._result_is_safe(result) is True
        assert result.passed is False
        assert result.identity_available is False
        assert result.case_id is None
        assert result.fixture_id is None
        assert result.completed_stage_ids == ()
        assert all(value is None for value in _nested_results(result))
        assert result.read_only is True
        assert result.demo_only is True
        assert result.is_tradable is False
        assert result.can_execute is False
        assert result.is_trading_permission is False
        assert result.is_execution_instruction is False
        assert result.allowed_to_call_ea is False
        assert result.allowed_to_modify_risk is False


def test_polluted_blocked_dependency_results_are_invalid() -> None:
    record = stage._REGISTRY[0]
    blocked_results = (
        (
            2,
            stage.market_facts._failure(
                stage.market_facts._INPUT_INVALID_STATUS,
                stage.market_facts._SOURCE_TYPE_INVALID,
            ),
            ("contract_version",),
        ),
        (
            3,
            stage.session_facts._failure(
                stage.session_facts._INPUT_INVALID_STATUS,
                stage.session_facts._INPUT_TYPE_INVALID,
            ),
            ("contract_version", "facts_profile_version"),
        ),
        (
            4,
            stage.volatility._failure(
                stage.volatility._INPUT_INVALID_STATUS,
                stage.volatility._INPUT_TYPE_INVALID,
            ),
            ("contract_version", "facts_profile_version"),
        ),
        (
            6,
            stage.economic._failure(*stage.economic._FAILURES[0]),
            ("contract_version", "facts_profile_version"),
        ),
    )
    for index, blocked, version_fields in blocked_results:
        assert stage._assess_stage(index, blocked, record) == "blocked"
        assert stage._assess_stage(
            index,
            replace(blocked, warning_codes=("POLLUTED_WARNING",)),
            record,
        ) == "invalid"
        for field_name in version_fields:
            assert stage._assess_stage(
                index,
                replace(blocked, **{field_name: "drifted"}),
                record,
            ) == "invalid"


CALL_ORDER = ("diagnostics", "source", "snapshot", "session", "volatility", "calendar", "economic")


class _StringSubclass(str):
    pass


class _TupleSubclass(tuple):
    pass


def _assert_terminal_failure(result: object, status: str, reason: str) -> None:
    assert type(result) is stage.CanonicalGoldFactsReplayResultV1
    assert result.status_code == status
    assert result.reason_codes == (reason,)
    assert result.passed is False
    assert result.identity_available is False
    assert result.case_id is result.fixture_id is None
    assert type(result.completed_stage_ids) is tuple and result.completed_stage_ids == ()
    assert all(value is None for value in _nested_results(result))
    assert result.read_only is result.demo_only is True
    for name in ("is_tradable", "can_execute", "is_trading_permission",
                 "is_execution_instruction", "allowed_to_call_ea", "allowed_to_modify_risk"):
        assert getattr(result, name) is False
    assert "CONTROLLED_SECRET" not in repr(result)


def _blocked_result(index: int) -> object:
    if index == 0:
        return stage.replay_v1._failure_result(
            status_code=stage.replay_v1.CANONICAL_BUNDLE_REPLAY_INPUT_INVALID,
            reason_code=stage.replay_v1.REPLAY_CASE_INPUT_INVALID,
        )
    if index == 1:
        return stage.market_fixture._EXPECTED_BUILD_SAFE_FAILURE()
    if index == 2:
        return stage.market_facts._failure(stage.market_facts._INPUT_INVALID_STATUS, stage.market_facts._SOURCE_TYPE_INVALID)
    if index == 3:
        return stage.session_facts._failure(stage.session_facts._INPUT_INVALID_STATUS, stage.session_facts._INPUT_TYPE_INVALID)
    if index == 4:
        return stage.volatility._failure(stage.volatility._INPUT_INVALID_STATUS, stage.volatility._INPUT_TYPE_INVALID)
    if index == 5:
        return stage.calendar._failure(*stage.calendar._FAILURES[0])
    return stage.economic._failure(*stage.economic._FAILURES[0])


@pytest.mark.parametrize("index", range(7), ids=CALL_ORDER)
@pytest.mark.parametrize("blocked", (False, True), ids=("ready", "blocked"))
@pytest.mark.parametrize("mutation", (
    "wrong_container", "subclass", "passed_int", "passed_none", "status_subclass",
    "reason_list", "reason_element", "warning_list", "warning_element", "missing_slot", "unsafe_flag",
))
def test_public_boundary_rejects_malformed_dependency_envelopes(
    monkeypatch: pytest.MonkeyPatch, index: int, blocked: bool, mutation: str,
) -> None:
    def corrupt(ready: object) -> object:
        result = _blocked_result(index) if blocked else ready
        reason_name = "replay_reason_codes" if index == 0 else "reason_codes"
        warning_name = "canonical_warning_codes" if index == 0 else "warning_codes"
        if mutation == "wrong_container":
            return {field.name: getattr(result, field.name) for field in fields(result)}
        if mutation == "subclass":
            child_type = type("ImpostorResult", (type(result),), {})
            return child_type(**{field.name: getattr(result, field.name) for field in fields(result)})
        if mutation == "missing_slot":
            object.__delattr__(result, warning_name)
            return result
        changes = {
            "passed_int": ("passed", int(result.passed)),
            "passed_none": ("passed", None),
            "status_subclass": ("status_code", _StringSubclass(result.status_code)),
            "reason_list": (reason_name, list(getattr(result, reason_name))),
            "reason_element": (reason_name, (123,)),
            "warning_list": (warning_name, []),
            "warning_element": (warning_name, (123,)),
            "unsafe_flag": ("can_execute", 0),
        }
        name, value = changes[mutation]
        return replace(result, **{name: value})

    calls = _install_delegating_capsule(monkeypatch, result_transform=(CALL_ORDER[index], corrupt))
    result = _run()
    _assert_terminal_failure(result, stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    assert calls == list(CALL_ORDER[:index + 1])


@pytest.mark.parametrize("index", range(7), ids=CALL_ORDER)
def test_public_boundary_preserves_safe_blocked_stage_mapping(monkeypatch: pytest.MonkeyPatch, index: int) -> None:
    calls = _install_delegating_capsule(
        monkeypatch, result_transform=(CALL_ORDER[index], lambda ready: _blocked_result(index)),
    )
    result = _run()
    _assert_terminal_failure(result, *stage._BLOCKED_BY_STAGE[index])
    assert calls == list(CALL_ORDER[:index + 1])


@pytest.mark.parametrize("index,transform", (
    (0, lambda value: replace(value, canonical_summary={1: "wrong key type"})),
    (1, lambda value: replace(value, source=replace(value.source, live_tick=replace(value.source.live_tick, bid=float("nan"))))),
    (1, lambda value: replace(value, source=replace(value.source, timeframes=_TupleSubclass(value.source.timeframes)))),
    (2, lambda value: replace(value, quote=replace(value.quote, bid_decimal=123))),
    (2, lambda value: replace(value, quote=replace(value.quote, bid_decimal=_StringSubclass(value.quote.bid_decimal)))),
    (2, lambda value: replace(value, quote=replace(value.quote, spread_points=True))),
    (2, lambda value: replace(value, timeframes=("M15",))),
    (2, lambda value: replace(value, timeframes=(replace(value.timeframes[0], bars=[value.timeframes[0].bars[0]]), *value.timeframes[1:]))),
    (3, lambda value: replace(value, spread=replace(value.spread, spread_points=False))),
    (4, lambda value: replace(value, timeframes=(replace(value.timeframes[0], bar_pairs=(123,)), *value.timeframes[1:]))),
    (5, lambda value: replace(value, snapshot=replace(value.snapshot, events=(replace(value.snapshot.events[0], source_revision=True), *value.snapshot.events[1:])))),
    (6, lambda value: replace(value, summary=replace(value.summary, relevant_event_count=False))),
    (6, lambda value: replace(value, event_windows=(replace(value.event_windows[0], is_active_observation_window=1), *value.event_windows[1:]))),
))
def test_public_boundary_rejects_nested_wrong_types(
    monkeypatch: pytest.MonkeyPatch, index: int, transform: Callable[[object], object],
) -> None:
    calls = _install_delegating_capsule(monkeypatch, result_transform=(CALL_ORDER[index], transform))
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    assert calls == list(CALL_ORDER[:index + 1])


@pytest.mark.parametrize("index,changes", (
    (0, {"passed": False}), (0, {"canonical_block_reasons": ("BLOCKED",)}),
    (1, {"source_available": False}), (1, {"source": None}),
    (2, {"identity_available": False}), (2, {"quote": None}), (2, {"timeframes": ()}),
    (2, {"contract_version": "drifted"}), (2, {"bundle_id": "different_identity"}),
    (3, {"session": None}), (3, {"facts_profile_version": "drifted"}),
    (4, {"timeframes": ()}), (4, {"total_pair_count": 0}),
    (5, {"snapshot_available": False}), (6, {"summary": None}),
))
def test_public_boundary_rejects_contradictory_ready_states(
    monkeypatch: pytest.MonkeyPatch, index: int, changes: dict[str, object],
) -> None:
    calls = _install_delegating_capsule(
        monkeypatch, result_transform=(CALL_ORDER[index], lambda value: replace(value, **changes)),
    )
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    assert calls == list(CALL_ORDER[:index + 1])


def test_public_boundary_preserves_legitimate_oracle_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    def change_observation(value: object) -> object:
        return replace(value, session=replace(value.session, observed_writer_session_status_label="CLOSED"))

    calls = _install_delegating_capsule(monkeypatch, result_transform=("session", change_observation))
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_MISMATCH, stage.GOLD_FACTS_REPLAY_EXPECTATION_MISMATCH)
    assert calls == list(CALL_ORDER[:4])


@pytest.mark.parametrize("name,value", (
    ("passed", 1), ("passed", False), ("can_execute", True),
    ("status_code", "POLLUTED"), ("readiness_notes", [123]),
    ("warning_reasons", ["CONTROLLED_SECRET"]), ("component_statuses", []),
))
def test_public_boundary_rejects_malformed_diagnostics_summary(
    monkeypatch: pytest.MonkeyPatch, name: str, value: object,
) -> None:
    def corrupt(result: object) -> object:
        return replace(result, canonical_summary={**result.canonical_summary, name: value})

    calls = _install_delegating_capsule(monkeypatch, result_transform=("diagnostics", corrupt))
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    assert calls == ["diagnostics"]


@pytest.mark.parametrize("path,transform", (
    (("readiness_notes",), lambda value: ["Changed observation"]),
    (("readiness_notes",), lambda value: []),
    (("readiness_notes",), lambda value: list(reversed(value))),
    (("readiness_notes",), lambda value: [*value, value[0]]),
    (("readiness_notes",), lambda value: tuple(value)),
    (("readiness_notes",), lambda value: [_StringSubclass(value[0]), *value[1:]]),
    (("next_allowed_stage",), lambda value: ["execution_chain"]),
    (("next_allowed_stage",), lambda value: []),
    (("next_allowed_stage",), lambda value: [*value, value[0]]),
    (("next_blocked_stage",), lambda value: []),
    (("next_blocked_stage",), lambda value: list(reversed(value))),
    (("next_blocked_stage",), lambda value: [*value, "unregistered_stage"]),
    (("bundle_validation_status", "status_code"), lambda value: "POLLUTED"),
    (("component_statuses", "canonical_data_quality_gate", "status_code"), lambda value: "POLLUTED"),
    (("bundle_validation_status",), lambda value: dict(reversed(tuple(value.items())))),
    (("component_statuses", "canonical_data_quality_gate"), lambda value: dict(reversed(tuple(value.items())))),
    ((), lambda value: dict(reversed(tuple(value.items())))),
))
def test_public_boundary_rejects_g151_invalid_diagnostics_content_and_order(
    monkeypatch: pytest.MonkeyPatch, path: tuple[str, ...], transform: Callable[[object], object],
) -> None:
    assert _run().passed is True

    def changed(result: object) -> object:
        summary = deepcopy(result.canonical_summary)
        assert is_safe_demo_readonly_canonical_diagnostics_summary(canonical_summary=summary) is True
        if path:
            container = summary
            for key in path[:-1]:
                container = container[key]
            container[path[-1]] = transform(container[path[-1]])
        else:
            summary = transform(summary)
        assert is_safe_demo_readonly_canonical_diagnostics_summary(canonical_summary=summary) is False
        return replace(result, canonical_summary=summary)

    calls = _install_delegating_capsule(monkeypatch, result_transform=("diagnostics", changed))
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    assert calls == ["diagnostics"]


@pytest.mark.parametrize("error", (ValueError, TypeError, OverflowError, AttributeError, RecursionError, DecimalException, RuntimeError))
@pytest.mark.parametrize("helper", (
    "_registry_is_safe", "_authority_is_safe", "_immutable_state",
    "_fixture_state", "_has_exact_registered_shape", "_freeze_value",
))
def test_post_stage_internal_exceptions_reach_public_sanitizer(
    monkeypatch: pytest.MonkeyPatch, error: type[Exception], helper: str,
) -> None:
    assert _run().passed is True
    calls = _install_delegating_capsule(monkeypatch)
    original_check = stage._evidence_is_unchanged
    original_helper = getattr(stage, helper)
    checking_earlier_results = False
    faults = 0

    def observe_check(*args: object, **kwargs: object) -> bool:
        nonlocal checking_earlier_results
        checking_earlier_results = bool(args[-1])
        try:
            return original_check(*args, **kwargs)
        finally:
            checking_earlier_results = False

    def internal_fault(*args: object, **kwargs: object) -> object:
        nonlocal faults
        if checking_earlier_results:
            faults += 1
            raise error("CONTROLLED_SECRET")
        return original_helper(*args, **kwargs)

    monkeypatch.setattr(stage, "_evidence_is_unchanged", observe_check)
    monkeypatch.setattr(stage, helper, internal_fault)
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE, stage.GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED)
    assert faults == 1
    assert calls == ["diagnostics", "source"]


@pytest.mark.parametrize("mutation", ("missing_slot", "unsupported_value", "changed_value"))
def test_post_stage_malformed_earlier_result_remains_result_invalid(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    assert _run().passed is True
    calls = _install_delegating_capsule(monkeypatch)
    original_check = stage._evidence_is_unchanged
    mutations = 0

    def corrupt_earlier_result(*args: object, **kwargs: object) -> bool:
        nonlocal mutations
        earlier_results = args[-1]
        if earlier_results:
            mutations += 1
            if mutation == "missing_slot":
                object.__delattr__(earlier_results[0], "status_code")
            else:
                value = object() if mutation == "unsupported_value" else "Changed observation"
                earlier_results[0].canonical_summary["readiness_notes"] = [value]
        return original_check(*args, **kwargs)

    monkeypatch.setattr(stage, "_evidence_is_unchanged", corrupt_earlier_result)
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    assert mutations == 1
    assert calls == ["diagnostics", "source"]


@pytest.mark.parametrize("error", (ValueError, TypeError, OverflowError, AttributeError, RecursionError, DecimalException, RuntimeError))
@pytest.mark.parametrize("location", ("dependency", "encoder", "shape", "final_validator"))
def test_unexpected_internal_exceptions_remain_sanitized(
    monkeypatch: pytest.MonkeyPatch, error: type[Exception], location: str,
) -> None:
    target: list[object] = []

    def observe(value: object) -> object:
        if location == "dependency":
            raise error("CONTROLLED_SECRET")
        target.append(value)
        return value

    calls = _install_delegating_capsule(monkeypatch, result_transform=("snapshot", observe))
    if location in {"encoder", "shape"}:
        name = "_freeze_value" if location == "encoder" else "_matches_declared_type"
        original = getattr(stage, name)

        def fail_on_target(value: object, *args: object, **kwargs: object) -> object:
            if target and value is target[0]:
                raise error("CONTROLLED_SECRET")
            return original(value, *args, **kwargs)

        monkeypatch.setattr(stage, name, fail_on_target)
    elif location == "final_validator":
        def broken_validator(value: object) -> bool:
            raise error("CONTROLLED_SECRET")

        monkeypatch.setattr(stage, "_result_is_safe", broken_validator)
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE, stage.GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED)
    assert calls == list(CALL_ORDER if location == "final_validator" else CALL_ORDER[:3])


@pytest.mark.parametrize("matched,changes", (
    (True, {"passed": 1}), (False, {"passed": None}), (False, {"identity_available": 0}),
    (True, {"passed": False}),
    (False, {"status_code": stage.CANONICAL_GOLD_FACTS_REPLAY_MATCHED, "reason_codes": ()}),
    (True, {"completed_stage_ids": list(stage.STAGE_ORDER)}),
    (True, {"case_id": _StringSubclass("canonical_docs_ready")}),
    (False, {"reason_codes": _TupleSubclass((stage.GOLD_FACTS_REPLAY_RESULT_INVALID,))}),
    (False, {"can_execute": 0}),
))
def test_independent_final_validator_rejects_illegal_types_and_states(matched: bool, changes: dict[str, object]) -> None:
    original = _run() if matched else stage._failure(stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    assert stage._result_is_safe(replace(original, **changes)) is False


@pytest.mark.parametrize("changes", (
    {"passed": 1}, {"passed": None}, {"passed": False}, {"identity_available": 1},
    {"status_code": stage.CANONICAL_GOLD_FACTS_REPLAY_MISMATCH, "reason_codes": (stage.GOLD_FACTS_REPLAY_EXPECTATION_MISMATCH,)},
))
def test_public_boundary_rejects_corrupted_matched_construction(monkeypatch: pytest.MonkeyPatch, changes: dict[str, object]) -> None:
    original = stage.CanonicalGoldFactsReplayResultV1.__init__

    def polluted_init(self: object, **kwargs: object) -> None:
        original(self, **kwargs)
        if kwargs["passed"] is True:
            for name, value in changes.items():
                object.__setattr__(self, name, value)

    monkeypatch.setattr(stage.CanonicalGoldFactsReplayResultV1, "__init__", polluted_init)
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)


def test_malformed_failure_construction_uses_terminal_safe_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    original = stage.CanonicalGoldFactsReplayResultV1.__init__

    def polluted_init(self: object, **kwargs: object) -> None:
        original(self, **kwargs)
        if kwargs["status_code"] == stage.CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID:
            object.__setattr__(self, "passed", None)

    monkeypatch.setattr(stage.CanonicalGoldFactsReplayResultV1, "__init__", polluted_init)
    result = stage.run_canonical_gold_facts_replay_case_v1(replay_case=replace(_case(), stage_id="wrong"))
    _assert_terminal_failure(result, stage.CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE, stage.GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED)


def test_public_boundary_rejects_cyclic_summary_without_leaking(monkeypatch: pytest.MonkeyPatch) -> None:
    def cyclic(value: object) -> object:
        summary: dict[str, object] = {}
        summary["cycle"] = summary
        return replace(value, canonical_summary=summary)

    calls = _install_delegating_capsule(monkeypatch, result_transform=("diagnostics", cyclic))
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    assert calls == ["diagnostics"]


def test_module_ast_has_no_direct_forbidden_runtime_surface() -> None:
    path = Path(stage.__file__)
    source = path.read_text(encoding="ascii")
    tree = ast.parse(source)
    imported_modules = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not any("g151" in name.lower() or "g153" in name.lower() for name in imported_modules)
    assert not ({"place_order", "send_order", "call_ea", "modify_risk"} & called_names)
    assert "requests" not in source
    assert "subprocess" not in source
    assert "socket" not in source


@pytest.mark.parametrize("field_name", EXPECTED_PUBLIC_FIELDS[0][1])
@pytest.mark.parametrize("after_stage", (False, True), ids=("entry", "post-stage"))
def test_recovery_missing_case_slot_has_structural_classification(
    monkeypatch: pytest.MonkeyPatch, field_name: str, after_stage: bool,
) -> None:
    assert _run().passed is True
    replay_case = _case()

    def remove_slot(result: object) -> object:
        object.__delattr__(replay_case, field_name)
        return result

    calls = _install_delegating_capsule(
        monkeypatch, result_transform=("diagnostics", remove_slot) if after_stage else None,
    )
    if not after_stage:
        remove_slot(None)
    result = stage.run_canonical_gold_facts_replay_case_v1(replay_case=replay_case)
    if after_stage:
        _assert_terminal_failure(result, stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    else:
        _assert_terminal_failure(result, stage.CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID, stage.GOLD_FACTS_REPLAY_CASE_INPUT_INVALID)
    assert calls == (["diagnostics"] if after_stage else [])


def _attempt_child(value: object, key: str | int) -> object:
    return value[key] if type(value) in {dict, tuple, list} else getattr(value, key)


def _attempt_node(value: object, path: tuple[str | int, ...]) -> object:
    for key in path:
        value = _attempt_child(value, key)
    return value


def _substitute_attempt_node(value: object, path: tuple[str | int, ...], replacement: object) -> object:
    if not path:
        return replacement
    key = path[0]
    changed = _substitute_attempt_node(_attempt_child(value, key), path[1:], replacement)
    if type(value) is tuple:
        items = list(value)
        items[key] = changed
        return tuple(items)
    if type(value) in {dict, list}:
        value[key] = changed
    else:
        object.__setattr__(value, key, changed)
    return value


@pytest.mark.parametrize("index,path", (
    (0, ("canonical_summary",)),
    (0, ("canonical_summary", "readiness_notes")),
    (0, ("canonical_summary", "component_statuses", "canonical_data_quality_gate")),
    (1, ("source",)),
    (1, ("source", "live_tick")),
    (1, ("source", "upstream_evidence")),
    (1, ("source", "timeframes")),
    (1, ("source", "timeframes", 0, "bars")),
    (1, ("source", "timeframes", 0, "bars", 0)),
    (1, ("source", "symbol_spec")),
    (2, ("quote",)),
    (2, ("timeframes",)),
    (2, ("timeframes", 0, "bars")),
    (2, ("timeframes", 0, "bars", 0)),
    (2, ("symbol_spec",)),
    (2, ("freshness",)),
    (3, ("session",)),
    (3, ("spread",)),
    (3, ("freshness",)),
    (4, ("timeframes",)),
    (4, ("timeframes", 0, "bar_pairs")),
    (4, ("timeframes", 0, "bar_pairs", 0)),
    (5, ("snapshot",)),
    (5, ("snapshot", "events")),
    (5, ("snapshot", "events", 0)),
    (5, ("snapshot", "upstream_evidence")),
))
def test_attempt_boundary_rejects_equal_foreign_nested_objects(
    monkeypatch: pytest.MonkeyPatch, index: int, path: tuple[str | int, ...],
) -> None:
    previous = _run()
    assert previous.passed is True
    foreign = _attempt_node(_nested_results(previous)[index], path)
    accepted: dict[int, object] = {}
    original_after = stage._after_stage
    substitutions = 0

    def remember(stage_index: int, result: object, *args: object, **kwargs: object) -> object:
        failure = original_after(stage_index, result, *args, **kwargs)
        if failure is None:
            accepted[stage_index] = result
        return failure

    def substitute(result: object) -> object:
        nonlocal substitutions
        earlier = accepted[index]
        current = _attempt_node(earlier, path)
        assert current == foreign and current is not foreign
        before = deepcopy(earlier)
        assert _substitute_attempt_node(earlier, path, foreign) is earlier
        assert earlier == before
        assert _attempt_node(earlier, path) is foreign
        substitutions += 1
        return result

    with monkeypatch.context() as controlled:
        controlled.setattr(stage, "_after_stage", remember)
        calls = _install_delegating_capsule(
            controlled, result_transform=(CALL_ORDER[index + 1], substitute),
        )
        _assert_terminal_failure(
            _run(), stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID,
            stage.GOLD_FACTS_REPLAY_RESULT_INVALID,
        )
        assert substitutions == 1
        assert calls == list(CALL_ORDER[:index + 2])
    assert _run() == previous


@pytest.mark.parametrize("error", (ValueError, TypeError, OverflowError, AttributeError, RecursionError, DecimalException, RuntimeError))
@pytest.mark.parametrize("location", ("final_identity", "final_safety", "post_stage_fixture", "post_stage_graph"))
def test_attempt_boundary_internal_faults_reach_terminal_sanitizer(
    monkeypatch: pytest.MonkeyPatch, error: type[Exception], location: str,
) -> None:
    assert _run().passed is True
    calls = _install_delegating_capsule(monkeypatch)
    observer_name = {
        "final_identity": "_identities_match",
        "final_safety": "_safety_flags_are_safe",
        "post_stage_fixture": "_evidence_is_unchanged",
        "post_stage_graph": "_after_stage",
    }[location]
    owner, fault_name = {
        "final_identity": (stage, "_market_identity_from_source"),
        "final_safety": (stage, "_safety_values"),
        "post_stage_fixture": (Path, "read_bytes"),
        "post_stage_graph": (stage, "_object_graph"),
    }[location]
    original_observer = getattr(stage, observer_name)
    original_leaf = getattr(owner, fault_name)
    in_scope = False
    faults = 0

    def observe(*args: object, **kwargs: object) -> object:
        nonlocal in_scope
        if location == "final_safety":
            in_scope = type(args[0]) is stage.CanonicalGoldFactsReplayResultV1 and args[0].passed is True
        elif location == "post_stage_fixture":
            in_scope = bool(args[-1])
        elif location == "post_stage_graph":
            in_scope = args[0] == 1
        else:
            in_scope = True
        try:
            return original_observer(*args, **kwargs)
        finally:
            in_scope = False

    def internal_fault(*args: object, **kwargs: object) -> object:
        nonlocal faults
        if in_scope:
            faults += 1
            raise error("CONTROLLED_SECRET")
        return original_leaf(*args, **kwargs)

    monkeypatch.setattr(stage, observer_name, observe)
    monkeypatch.setattr(owner, fault_name, internal_fault)
    _assert_terminal_failure(
        _run(), stage.CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE,
        stage.GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED,
    )
    assert faults == 1
    assert calls == list(CALL_ORDER if location.startswith("final") else CALL_ORDER[:2])


@pytest.mark.parametrize("after_stage", (False, True), ids=("entry", "post-stage"))
def test_attempt_boundary_expected_filesystem_failure_remains_structural(
    monkeypatch: pytest.MonkeyPatch, after_stage: bool,
) -> None:
    assert _run().passed is True
    calls = _install_delegating_capsule(monkeypatch)
    original_check = stage._evidence_is_unchanged
    original_read = Path.read_bytes
    checking_earlier = False
    faults = 0

    def observe(*args: object, **kwargs: object) -> bool:
        nonlocal checking_earlier
        checking_earlier = bool(args[-1])
        try:
            return original_check(*args, **kwargs)
        finally:
            checking_earlier = False

    def unavailable(path: Path) -> bytes:
        nonlocal faults
        if not after_stage or checking_earlier:
            faults += 1
            raise PermissionError("CONTROLLED_SECRET")
        return original_read(path)

    monkeypatch.setattr(stage, "_evidence_is_unchanged", observe)
    monkeypatch.setattr(Path, "read_bytes", unavailable)
    expected = (
        (stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
        if after_stage else
        (stage.CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID, stage.GOLD_FACTS_REPLAY_AUTHORITY_INVALID)
    )
    _assert_terminal_failure(_run(), *expected)
    assert faults == 1
    assert calls == (list(CALL_ORDER[:2]) if after_stage else [])


def test_attempt_boundary_persistent_safety_helper_fault_stays_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _run().passed is True
    calls = _install_delegating_capsule(monkeypatch)

    def broken_safety() -> dict[str, bool]:
        raise RuntimeError("CONTROLLED_SECRET")

    monkeypatch.setattr(stage, "_safety_values", broken_safety)
    _assert_terminal_failure(
        _run(), stage.CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE,
        stage.GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED,
    )
    assert calls == ["diagnostics"]



@pytest.mark.parametrize("error", (ValueError, TypeError, OverflowError, AttributeError, RecursionError, DecimalException, RuntimeError))
@pytest.mark.parametrize("helper", ("_schemas_are_safe", "_is_valid_frozen_value", "isfinite"))
@pytest.mark.parametrize("after_stage", (False, True), ids=("entry", "post-stage"))
def test_recovery_deep_internal_fault_is_not_structural_invalidity(
    monkeypatch: pytest.MonkeyPatch, error: type[Exception], helper: str, after_stage: bool,
) -> None:
    assert _run().passed is True
    calls = _install_delegating_capsule(monkeypatch)
    owner = stage.math if helper == "isfinite" else stage
    original = getattr(owner, helper)
    original_check = stage._evidence_is_unchanged
    checking_earlier_results = False
    faults = 0

    def observe_check(*args: object, **kwargs: object) -> bool:
        nonlocal checking_earlier_results
        checking_earlier_results = bool(args[-1])
        try:
            return original_check(*args, **kwargs)
        finally:
            checking_earlier_results = False

    def internal_fault(*args: object, **kwargs: object) -> object:
        nonlocal faults
        if not after_stage or checking_earlier_results:
            faults += 1
            raise error("CONTROLLED_SECRET")
        return original(*args, **kwargs)

    monkeypatch.setattr(stage, "_evidence_is_unchanged", observe_check)
    monkeypatch.setattr(owner, helper, internal_fault)
    _assert_terminal_failure(_run(), stage.CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE, stage.GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED)
    assert faults == 1
    assert calls == (["diagnostics", "source"] if after_stage else [])


@pytest.mark.parametrize("target_name,field_name", (
    ("record", "reference_time_utc"),
    ("record", "expected_oracle"),
    ("oracle", "diagnostics_result"),
    ("capsule", "market_projector"),
))
@pytest.mark.parametrize("after_stage", (False, True), ids=("entry", "post-stage"))
def test_recovery_missing_authority_slots_remain_structural_failures(
    monkeypatch: pytest.MonkeyPatch, target_name: str, field_name: str, after_stage: bool,
) -> None:
    assert _run().passed is True
    target = None

    def remove_slot(result: object) -> object:
        object.__delattr__(target, field_name)
        return result

    calls = _install_delegating_capsule(
        monkeypatch, result_transform=("diagnostics", remove_slot) if after_stage else None,
    )
    record = replace(stage._REGISTRY[0], expected_oracle=replace(stage._EXPECTED_ORACLE))
    monkeypatch.setattr(stage, "_EXPECTED_ORACLE", record.expected_oracle)
    monkeypatch.setattr(stage, "_APPROVED_REGISTRY", (record,))
    monkeypatch.setattr(stage, "_REGISTRY", stage._APPROVED_REGISTRY)
    target = {"record": record, "oracle": record.expected_oracle, "capsule": stage._CAPSULE}[target_name]
    if not after_stage:
        remove_slot(None)
    result = _run()
    if after_stage:
        expected = (stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    elif target_name == "capsule":
        expected = (stage.CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID, stage.GOLD_FACTS_REPLAY_AUTHORITY_INVALID)
    else:
        expected = (stage.CANONICAL_GOLD_FACTS_REPLAY_REGISTRY_INVALID, stage.GOLD_FACTS_REPLAY_REGISTRY_INVALID)
    _assert_terminal_failure(result, *expected)
    assert calls == (["diagnostics"] if after_stage else [])


@pytest.mark.parametrize("encoded", (
    ("FLOAT_HEX_V1", "not-hex"),
    ("FLOAT_HEX_V1", "0x1p+9999999999"),
    ("FLOAT_HEX_V1", "nan"),
    ("FLOAT_HEX_V1", "inf"),
    ("FLOAT_HEX_V1", "0x1p+0"),
    ("FLOAT_HEX_V1", 1),
    ("DICT_V1", ((("STRING_V1", "key"), ("NONE_V1",)), (("STRING_V1", "key"), ("NONE_V1",)))),
    ("DICT_V1", ((),)),
    ("DICT_V1", ((("STRING_V1", "key"), ["NONE_V1"]),)),
    ("TUPLE_V1", (("INT_V1", True),)),
    ("LIST_V1", [("NONE_V1",)]),
))
@pytest.mark.parametrize("after_stage", (False, True), ids=("entry", "post-stage"))
def test_recovery_invalid_frozen_oracle_is_not_an_internal_exception(
    monkeypatch: pytest.MonkeyPatch, encoded: object, after_stage: bool,
) -> None:
    assert _run().passed is True
    oracle = replace(stage._EXPECTED_ORACLE)

    def corrupt(result: object) -> object:
        object.__setattr__(oracle, "diagnostics_result", encoded)
        return result

    calls = _install_delegating_capsule(
        monkeypatch, result_transform=("diagnostics", corrupt) if after_stage else None,
    )
    record = replace(stage._REGISTRY[0], expected_oracle=oracle)
    monkeypatch.setattr(stage, "_EXPECTED_ORACLE", oracle)
    monkeypatch.setattr(stage, "_APPROVED_REGISTRY", (record,))
    monkeypatch.setattr(stage, "_REGISTRY", stage._APPROVED_REGISTRY)
    if not after_stage:
        corrupt(None)
    result = _run()
    if after_stage:
        _assert_terminal_failure(result, stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    else:
        _assert_terminal_failure(result, stage.CANONICAL_GOLD_FACTS_REPLAY_REGISTRY_INVALID, stage.GOLD_FACTS_REPLAY_REGISTRY_INVALID)
    assert calls == (["diagnostics"] if after_stage else [])


@pytest.mark.parametrize("pairs", (((),), (None,), (("field",),), (["field", ("NONE_V1",)],), ((123, ("NONE_V1",)),)))
def test_recovery_malformed_dataclass_oracle_pairs_are_rejected(pairs: object) -> None:
    type_code = stage._PRODUCTION_SCHEMAS[0].type_code
    assert stage._is_valid_frozen_value(("DATACLASS_V1", type_code, pairs)) is False


@pytest.mark.parametrize("mutation", ("missing_class", "missing_fields", "not_dataclass", "instance"))
@pytest.mark.parametrize("after_stage", (False, True), ids=("entry", "post-stage"))
def test_recovery_malformed_schema_authority_is_not_an_internal_exception(
    monkeypatch: pytest.MonkeyPatch, mutation: str, after_stage: bool,
) -> None:
    assert _run().passed is True
    schema = replace(stage._PRODUCTION_SCHEMAS[0])

    def corrupt(result: object) -> object:
        if mutation.startswith("missing"):
            object.__delattr__(schema, "class_object" if mutation == "missing_class" else "ordered_fields")
        else:
            object.__setattr__(schema, "class_object", str if mutation == "not_dataclass" else _case())
        monkeypatch.setattr(stage, "_PRODUCTION_SCHEMAS", (schema, *stage._PRODUCTION_SCHEMAS[1:]))
        return result

    calls = _install_delegating_capsule(
        monkeypatch, result_transform=("diagnostics", corrupt) if after_stage else None,
    )
    if not after_stage:
        corrupt(None)
    result = _run()
    if after_stage:
        _assert_terminal_failure(result, stage.CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, stage.GOLD_FACTS_REPLAY_RESULT_INVALID)
    else:
        _assert_terminal_failure(result, stage.CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID, stage.GOLD_FACTS_REPLAY_AUTHORITY_INVALID)
    assert calls == (["diagnostics"] if after_stage else [])
