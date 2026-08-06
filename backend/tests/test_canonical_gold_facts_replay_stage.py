from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
import inspect
from pathlib import Path

import pytest

from app.services import canonical_gold_facts_replay_stage as stage


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

    def diagnostics(*, replay_case: object) -> object:
        calls.append("diagnostics")
        return originals["diagnostics"](replay_case=replay_case)

    def source() -> object:
        calls.append("source")
        return originals["source"]()

    def snapshot(*, validated_source: object) -> object:
        calls.append("snapshot")
        if mutation_stage == "source":
            object.__setattr__(validated_source.live_tick, "bid", validated_source.live_tick.bid + 1.0)
        return originals["snapshot"](validated_source=validated_source)

    def session(*, market_facts_snapshot: object) -> object:
        calls.append("session")
        if mutation_stage == "snapshot":
            object.__setattr__(market_facts_snapshot.quote, "bid_decimal", "9999.99")
        return originals["session"](market_facts_snapshot=market_facts_snapshot)

    def volatility(*, market_facts_snapshot: object) -> object:
        calls.append("volatility")
        return originals["volatility"](market_facts_snapshot=market_facts_snapshot)

    def calendar(*, authority: object) -> object:
        calls.append("calendar")
        return originals["calendar"](authority=authority)

    def economic(*, market_facts_snapshot: object, economic_calendar_snapshot: object) -> object:
        calls.append("economic")
        return originals["economic"](
            market_facts_snapshot=market_facts_snapshot,
            economic_calendar_snapshot=economic_calendar_snapshot,
        )

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
