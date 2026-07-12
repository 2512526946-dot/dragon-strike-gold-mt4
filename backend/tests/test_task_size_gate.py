from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from app.services.task_size_gate import (
    ALLOW_SINGLE_WORK_ORDER,
    CONDITIONAL_PRO_RESUME,
    CROSS_PACKAGE_ACTIVATION,
    ELIGIBLE,
    INPUT_INVALID,
    MODEL_STOP_UNCERTAIN,
    MULTIPLE_OBJECTIVES,
    NON_ADJACENT_LAYERS,
    NORMAL_ALLOWED,
    NOT_ELIGIBLE,
    OVERSIZED,
    PRO_MODEL_REQUIRED,
    PRO_REQUIRED,
    REQUIRED_CHECK_CATEGORIES,
    SINGLE_WORK_ORDER_ALLOWED,
    SIZE_UNCLASSIFIABLE,
    SPLIT_REQUIRED,
    STOP_UNCERTAIN,
    UNKNOWN_EVIDENCE,
    TaskSizeGateEvidence,
    TaskSizeGateResult,
    evaluate_task_size_gate,
)


BASE_COMMIT = "1ba36a7a3e205e17f03effb9e6812edcd8c52a39"


def _evidence(**overrides: object) -> TaskSizeGateEvidence:
    values: dict[str, object] = {
        "objective": "Implement one pure TaskSizeGate evaluator",
        "objective_count": 1,
        "wbs_package_ids": ("W0",),
        "current_maturity": "CONTRACT_ONLY",
        "target_maturity": "TESTS_ONLY",
        "maturity_reason": "Add the approved contract tests",
        "base_branch": "main",
        "base_main_commit": BASE_COMMIT,
        "work_branch": "work/g166-task-size-gate-pure-evaluator",
        "commit_message": "feat: implement pure TaskSizeGate evaluator",
        "push_destination": "origin/work/g166-task-size-gate-pure-evaluator",
        "stop_conditions": ("scope_expansion", "test_failure"),
        "estimated_engineering_hours_lower": 4,
        "estimated_engineering_hours_upper": 8,
        "allowed_files": (
            "backend/app/services/task_size_gate.py",
            "backend/tests/test_task_size_gate.py",
        ),
        "prohibited_files": ("AGENTS.md",),
        "prohibited_capabilities": ("merge", "tag", "activation"),
        "capability_layers": ("TESTS",),
        "subsystem_boundaries": ("repository_workflow",),
        "affected_surfaces": ("pure_python_evaluator",),
        "required_checks": (
            "targeted",
            "regression",
            "full_suite",
            "build:not_applicable",
            "grep",
            "diff",
            "scope",
        ),
        "known_dependencies": ("WF-4B", "WF-4C"),
        "dependency_evidence_known": True,
        "risk_and_policy_impacts": ("no_policy_change",),
        "high_risk_reasons": (),
        "model_gate": NORMAL_ALLOWED,
        "model_gate_evidence": ("tests_only_normal_example",),
        "unknowns": (),
        "cross_package_activation": False,
    }
    values.update(overrides)
    return TaskSizeGateEvidence(**values)  # type: ignore[arg-type]


def _result(**overrides: object) -> TaskSizeGateResult:
    values: dict[str, object] = {
        "task_size": "S",
        "task_decision": ALLOW_SINGLE_WORK_ORDER,
        "model_gate": NORMAL_ALLOWED,
        "supervisor_eligibility": ELIGIBLE,
        "reason_codes": (SINGLE_WORK_ORDER_ALLOWED,),
    }
    values.update(overrides)
    return TaskSizeGateResult(**values)  # type: ignore[arg-type]


def _assert_known_size_input_invalid(
    result: TaskSizeGateResult, *, expected_task_size: str = "S"
) -> None:
    assert result.task_size == expected_task_size
    assert result.task_decision == STOP_UNCERTAIN
    assert result.model_gate == STOP_UNCERTAIN
    assert result.supervisor_eligibility == NOT_ELIGIBLE
    assert result.reason_codes == (INPUT_INVALID,)


def test_public_evidence_and_result_shapes_are_frozen_and_exact() -> None:
    assert tuple(field.name for field in fields(TaskSizeGateEvidence)) == (
        "objective",
        "objective_count",
        "wbs_package_ids",
        "current_maturity",
        "target_maturity",
        "maturity_reason",
        "base_branch",
        "base_main_commit",
        "work_branch",
        "commit_message",
        "push_destination",
        "stop_conditions",
        "estimated_engineering_hours_lower",
        "estimated_engineering_hours_upper",
        "allowed_files",
        "prohibited_files",
        "prohibited_capabilities",
        "capability_layers",
        "subsystem_boundaries",
        "affected_surfaces",
        "required_checks",
        "known_dependencies",
        "dependency_evidence_known",
        "risk_and_policy_impacts",
        "high_risk_reasons",
        "model_gate",
        "model_gate_evidence",
        "unknowns",
        "cross_package_activation",
    )
    assert tuple(field.name for field in fields(TaskSizeGateResult)) == (
        "task_size",
        "task_decision",
        "model_gate",
        "supervisor_eligibility",
        "reason_codes",
    )

    evidence = _evidence()
    result = evaluate_task_size_gate(evidence=evidence)
    with pytest.raises(FrozenInstanceError):
        evidence.objective = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.task_size = "XL"  # type: ignore[misc]


def test_normal_small_evidence_is_allowed_and_supervisor_eligible() -> None:
    evidence = _evidence()

    assert evaluate_task_size_gate(evidence=evidence) == _result()
    assert evidence == _evidence()


@pytest.mark.parametrize(
    ("upper", "expected"),
    (
        (1, "XS"),
        (2, "XS"),
        (3, "S"),
        (8, "S"),
        (9, "M"),
        (16, "M"),
        (17, "L"),
        (40, "L"),
        (41, "XL"),
    ),
)
def test_hour_boundaries_are_exact(upper: int, expected: str) -> None:
    evidence = _evidence(
        estimated_engineering_hours_lower=1,
        estimated_engineering_hours_upper=upper,
        allowed_files=("one.py",),
    )

    assert evaluate_task_size_gate(evidence=evidence).task_size == expected


@pytest.mark.parametrize(
    ("count", "expected"),
    (
        (1, "XS"),
        (2, "S"),
        (3, "S"),
        (4, "M"),
        (5, "M"),
        (6, "L"),
        (10, "L"),
        (11, "XL"),
    ),
)
def test_file_boundaries_are_exact(count: int, expected: str) -> None:
    evidence = _evidence(
        estimated_engineering_hours_lower=1,
        estimated_engineering_hours_upper=1,
        allowed_files=tuple(f"file_{index}.py" for index in range(count)),
    )

    assert evaluate_task_size_gate(evidence=evidence).task_size == expected


@pytest.mark.parametrize(
    ("layers", "expected"),
    (
        (("TESTS",), "XS"),
        (("TESTS", "IMPLEMENTATION"), "M"),
        (("CONTRACT", "IMPLEMENTATION"), "L"),
        (("TESTS", "IMPLEMENTATION", "INTEGRATION"), "L"),
        (("CONTRACT", "TESTS", "IMPLEMENTATION", "INTEGRATION"), "XL"),
    ),
)
def test_layer_boundaries_and_adjacency_are_exact(
    layers: tuple[str, ...], expected: str
) -> None:
    transition_by_target_layer = {
        "TESTS": ("CONTRACT_ONLY", "TESTS_ONLY"),
        "IMPLEMENTATION": ("TESTS_ONLY", "IMPLEMENTED"),
        "INTEGRATION": ("IMPLEMENTED", "INTEGRATED"),
    }
    current_maturity, target_maturity = transition_by_target_layer[layers[-1]]
    evidence = _evidence(
        estimated_engineering_hours_lower=1,
        estimated_engineering_hours_upper=1,
        allowed_files=("one.py",),
        capability_layers=layers,
        current_maturity=current_maturity,
        target_maturity=target_maturity,
        maturity_reason="one adjacent maturity transition",
    )

    assert evaluate_task_size_gate(evidence=evidence).task_size == expected


def test_conservative_maximum_uses_largest_dimension() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            estimated_engineering_hours_lower=1,
            estimated_engineering_hours_upper=1,
            allowed_files=("a.py", "b.py", "c.py", "d.py"),
        )
    )

    assert result.task_size == "M"
    assert result.task_decision == ALLOW_SINGLE_WORK_ORDER
    assert result.supervisor_eligibility == NOT_ELIGIBLE


def test_two_non_adjacent_layers_force_l_and_split() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            capability_layers=("CONTRACT", "IMPLEMENTATION"),
            allowed_files=("one.py",),
            estimated_engineering_hours_lower=1,
            estimated_engineering_hours_upper=1,
            current_maturity="TESTS_ONLY",
            target_maturity="IMPLEMENTED",
            maturity_reason="one adjacent maturity transition",
        )
    )

    assert result.task_size == "L"
    assert result.task_decision == SPLIT_REQUIRED
    assert result.reason_codes == (NON_ADJACENT_LAYERS, OVERSIZED)


def test_multiple_objectives_force_l_and_split() -> None:
    result = evaluate_task_size_gate(evidence=_evidence(objective_count=2))

    assert result.task_size == "L"
    assert result.task_decision == SPLIT_REQUIRED
    assert result.reason_codes == (MULTIPLE_OBJECTIVES, OVERSIZED)


def test_cross_package_activation_forces_xl_split_and_pro() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(cross_package_activation=True)
    )

    assert result.task_size == "XL"
    assert result.task_decision == SPLIT_REQUIRED
    assert result.model_gate == PRO_REQUIRED
    assert result.supervisor_eligibility == NOT_ELIGIBLE
    assert result.reason_codes == (
        CROSS_PACKAGE_ACTIVATION,
        OVERSIZED,
        PRO_MODEL_REQUIRED,
    )


def test_unclassifiable_size_uses_null_and_stops() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            estimated_engineering_hours_lower=None,
            estimated_engineering_hours_upper=None,
            allowed_files=(),
            capability_layers=(),
        )
    )

    assert result == _result(
        task_size=None,
        task_decision=STOP_UNCERTAIN,
        model_gate=STOP_UNCERTAIN,
        supervisor_eligibility=NOT_ELIGIBLE,
        reason_codes=(SIZE_UNCLASSIFIABLE,),
    )


@pytest.mark.parametrize(
    "overrides",
    (
        {"dependency_evidence_known": False},
        {"unknowns": ("dependency_scope",)},
    ),
)
def test_known_size_is_preserved_when_other_evidence_is_unknown(
    overrides: dict[str, object],
) -> None:
    result = evaluate_task_size_gate(evidence=_evidence(**overrides))

    assert result == _result(
        task_decision=STOP_UNCERTAIN,
        model_gate=STOP_UNCERTAIN,
        supervisor_eligibility=NOT_ELIGIBLE,
        reason_codes=(UNKNOWN_EVIDENCE,),
    )


def test_explicit_model_stop_has_priority_and_preserves_size() -> None:
    result = evaluate_task_size_gate(evidence=_evidence(model_gate=STOP_UNCERTAIN))

    assert result == _result(
        task_decision=STOP_UNCERTAIN,
        model_gate=STOP_UNCERTAIN,
        supervisor_eligibility=NOT_ELIGIBLE,
        reason_codes=(MODEL_STOP_UNCERTAIN,),
    )


def test_pro_small_task_is_conditionally_supervisor_eligible() -> None:
    result = evaluate_task_size_gate(evidence=_evidence(model_gate=PRO_REQUIRED))

    assert result == _result(
        model_gate=PRO_REQUIRED,
        supervisor_eligibility=CONDITIONAL_PRO_RESUME,
        reason_codes=(SINGLE_WORK_ORDER_ALLOWED, PRO_MODEL_REQUIRED),
    )


def test_high_risk_reason_forces_pro_without_inflating_task_size() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(high_risk_reasons=("canonical_protocol",))
    )

    assert result == _result(
        model_gate=PRO_REQUIRED,
        supervisor_eligibility=CONDITIONAL_PRO_RESUME,
        reason_codes=(SINGLE_WORK_ORDER_ALLOWED, PRO_MODEL_REQUIRED),
    )


def test_m_task_is_not_supervisor_eligible_even_when_allowed() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            estimated_engineering_hours_upper=9,
            capability_layers=("TESTS", "IMPLEMENTATION"),
            current_maturity="TESTS_ONLY",
            target_maturity="IMPLEMENTED",
            maturity_reason="one adjacent maturity transition",
        )
    )

    assert result.task_size == "M"
    assert result.task_decision == ALLOW_SINGLE_WORK_ORDER
    assert result.supervisor_eligibility == NOT_ELIGIBLE


def test_maturity_preserving_hardening_is_valid() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            current_maturity="TESTS_ONLY",
            target_maturity="TESTS_ONLY",
            maturity_reason="maturity-preserving test hardening",
        )
    )

    assert result.task_decision == ALLOW_SINGLE_WORK_ORDER


@pytest.mark.parametrize(
    "capability_layer",
    ("IMPLEMENTATION", "INTEGRATION", "ACTIVATION", "VERIFICATION"),
)
def test_maturity_preserving_revision_cannot_touch_a_higher_layer(
    capability_layer: str,
) -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            current_maturity="TESTS_ONLY",
            target_maturity="TESTS_ONLY",
            maturity_reason="maturity-preserving test hardening",
            capability_layers=(capability_layer,),
        )
    )

    _assert_known_size_input_invalid(result)


def test_maturity_preserving_change_without_reason_fails_closed() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            current_maturity="TESTS_ONLY",
            target_maturity="TESTS_ONLY",
            maturity_reason="same state",
        )
    )

    assert result == _result(
        task_decision=STOP_UNCERTAIN,
        model_gate=STOP_UNCERTAIN,
        supervisor_eligibility=NOT_ELIGIBLE,
        reason_codes=(INPUT_INVALID,),
    )


@pytest.mark.parametrize(
    ("current_maturity", "target_maturity", "capability_layers"),
    (
        ("VERIFIED", "TESTS_ONLY", ("TESTS",)),
        ("CONTRACT_ONLY", "VERIFIED", ("VERIFICATION",)),
        ("CONTRACT_ONLY", "TESTS_ONLY", ("IMPLEMENTATION",)),
        ("NOT_STARTED", "NOT_STARTED", ("POLICY",)),
    ),
)
def test_invalid_maturity_transitions_fail_closed(
    current_maturity: str,
    target_maturity: str,
    capability_layers: tuple[str, ...],
) -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            current_maturity=current_maturity,
            target_maturity=target_maturity,
            maturity_reason="maturity-preserving hardening",
            capability_layers=capability_layers,
        )
    )

    _assert_known_size_input_invalid(result)


def test_required_check_categories_are_exact_and_complete() -> None:
    assert REQUIRED_CHECK_CATEGORIES == (
        "targeted",
        "regression",
        "full_suite",
        "build",
        "grep",
        "diff",
        "scope",
    )
    assert evaluate_task_size_gate(evidence=_evidence()).task_decision == (
        ALLOW_SINGLE_WORK_ORDER
    )


@pytest.mark.parametrize("missing_category", REQUIRED_CHECK_CATEGORIES)
def test_missing_required_check_category_fails_closed(
    missing_category: str,
) -> None:
    checks = tuple(
        check
        for check in _evidence().required_checks
        if check.partition(":")[0] != missing_category
    )
    result = evaluate_task_size_gate(
        evidence=_evidence(required_checks=checks)
    )

    _assert_known_size_input_invalid(result)


def test_duplicate_or_unknown_check_categories_fail_closed() -> None:
    duplicate = _evidence().required_checks + ("targeted:second",)
    unknown = _evidence().required_checks + ("custom",)

    _assert_known_size_input_invalid(
        evaluate_task_size_gate(evidence=_evidence(required_checks=duplicate))
    )
    _assert_known_size_input_invalid(
        evaluate_task_size_gate(evidence=_evidence(required_checks=unknown))
    )


def test_allowed_and_prohibited_file_overlap_fails_closed() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            prohibited_files=("backend/app/services/task_size_gate.py",)
        )
    )

    _assert_known_size_input_invalid(result)


def test_case_variant_file_scope_overlap_fails_closed() -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            prohibited_files=("BACKEND/APP/SERVICES/TASK_SIZE_GATE.PY",)
        )
    )

    _assert_known_size_input_invalid(result)


@pytest.mark.parametrize(
    "work_branch",
    (
        "work/../main",
        "work//branch",
        "work/*",
        "work/.hidden",
        "work/name.lock",
        "work/trailing/",
        "work/space name",
    ),
)
def test_invalid_work_branch_fails_closed_without_leaking_input(
    work_branch: str,
) -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            work_branch=work_branch,
            push_destination=f"origin/{work_branch}",
        )
    )

    _assert_known_size_input_invalid(result)
    assert work_branch not in repr(result)


@pytest.mark.parametrize(
    "evidence",
    (
        object(),
        {"objective": "not typed evidence"},
        None,
    ),
)
def test_non_evidence_inputs_fail_closed(evidence: object) -> None:
    assert evaluate_task_size_gate(evidence=evidence) == _result(
        task_size=None,
        task_decision=STOP_UNCERTAIN,
        model_gate=STOP_UNCERTAIN,
        supervisor_eligibility=NOT_ELIGIBLE,
        reason_codes=(INPUT_INVALID,),
    )


@pytest.mark.parametrize(
    ("field_name", "bad_value", "expected_task_size"),
    (
        ("estimated_engineering_hours_upper", True, None),
        ("allowed_files", ["one.py"], None),
        ("capability_layers", ["TESTS"], None),
        ("model_gate", "UNKNOWN", "S"),
        ("dependency_evidence_known", 1, "S"),
        ("base_main_commit", "not-a-commit", "S"),
        ("push_destination", "origin/main", "S"),
    ),
)
def test_wrong_field_types_or_values_fail_closed(
    field_name: str, bad_value: object, expected_task_size: str | None
) -> None:
    evidence = _evidence()
    object.__setattr__(evidence, field_name, bad_value)

    result = evaluate_task_size_gate(evidence=evidence)

    assert result.task_size == expected_task_size
    assert result.task_decision == STOP_UNCERTAIN
    assert result.model_gate == STOP_UNCERTAIN
    assert result.supervisor_eligibility == NOT_ELIGIBLE
    assert result.reason_codes == (INPUT_INVALID,)


@pytest.mark.parametrize(
    "bad_path",
    (
        "../outside.py",
        "/absolute.py",
        "C:/absolute.py",
        "backend/**/*.py",
        "backend\\app\\service.py",
        ".",
        "backend/./file.py",
        "backend//file.py",
        "backend/",
    ),
)
def test_non_exact_file_scope_fails_closed(bad_path: str) -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(allowed_files=(bad_path,))
    )

    assert result.task_size is None
    assert result.task_decision == STOP_UNCERTAIN
    assert result.reason_codes == (INPUT_INVALID,)
    assert bad_path not in repr(result)


@pytest.mark.parametrize(
    "allowed_alias",
    ("backend/./file.py", "backend//file.py"),
)
def test_noncanonical_scope_alias_cannot_bypass_overlap_check(
    allowed_alias: str,
) -> None:
    result = evaluate_task_size_gate(
        evidence=_evidence(
            allowed_files=(allowed_alias,),
            prohibited_files=("backend/file.py",),
        )
    )

    assert result.task_size is None
    assert result.task_decision == STOP_UNCERTAIN
    assert result.model_gate == STOP_UNCERTAIN
    assert result.supervisor_eligibility == NOT_ELIGIBLE
    assert result.reason_codes == (INPUT_INVALID,)
    assert allowed_alias not in repr(result)


def test_runtime_module_has_no_io_or_integration_dependencies() -> None:
    module_path = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "task_size_gate.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert imported_roots <= {"__future__", "dataclasses", "re", "typing"}
    assert called_names.isdisjoint({"open", "exec", "eval", "compile"})
    assert called_attributes.isdisjoint(
        {
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "getenv",
            "run",
            "Popen",
        }
    )
