"""Static contract vectors for the TaskSizeGate pre-write checkpoint.

These vectors lock the WF-4G boundary.  They deliberately do not import or
call a future pre-write integration, the TaskSizeGate evaluator, or any
workflow Skill; therefore they do not claim runtime integration is complete.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "implementation_plans"
    / "task_size_gate_pre_write_integration_contract.md"
)
EVALUATOR_PATH = REPOSITORY_ROOT / "backend" / "app" / "services" / "task_size_gate.py"


EVIDENCE_FIELD_SOURCE_RULES = MappingProxyType(
    {
        "objective": "Exact single outcome from the approved frozen order; unchanged.",
        "objective_count": "Recount independently deliverable outcomes; any increase is drift.",
        "wbs_package_ids": "Current WBS evidence for the approved scope; no added package.",
        "current_maturity": "Narrow capability maturity proven at frozen base main; an unmerged work-branch implementation does not advance it.",
        "target_maturity": "Original approved adjacent target; only a separately planned order may use a maturity-preserving revision target.",
        "maturity_reason": "Exact original approved transition reason, or the reason from a separately planned hardening/maintenance order.",
        "base_branch": "Strict `main` in new, revision, and recovery modes; current branch state is not stored in this field.",
        "base_main_commit": "Fresh equality of local and remote main to the frozen commit.",
        "work_branch": "Exact approved branch and mode-specific existence rule.",
        "commit_message": "Exact approved ordinary commit message.",
        "push_destination": "Exact `origin/<work_branch>` destination; never `main`.",
        "stop_conditions": "Frozen stop conditions plus no silently weakened condition.",
        "estimated_engineering_hours_lower": "Approved defensible lower estimate; never reduced to obtain allow.",
        "estimated_engineering_hours_upper": "Re-estimated upper bound including newly discovered work; any increase is drift.",
        "allowed_files": "Exact canonical relative files; newly required files are drift.",
        "prohibited_files": "Exact canonical relative files that remain forbidden.",
        "prohibited_capabilities": "Frozen merge, tag, deployment, activation, policy, and capability limits.",
        "capability_layers": "Ordered distinct layers actually touched; newly discovered layer is drift.",
        "subsystem_boundaries": "Exact approved repository ownership boundaries.",
        "affected_surfaces": "Fresh impact review of all touched workflow surfaces.",
        "required_checks": "Complete seven-category verification set with explicit N/A where valid.",
        "known_dependencies": "Fresh repository proof for every approved dependency.",
        "dependency_evidence_known": "Strict true only when all dependency evidence remains known.",
        "risk_and_policy_impacts": "Fresh safety and policy review; any new impact is drift.",
        "high_risk_reasons": "Current ModelGate reasons without omission or downgrading.",
        "model_gate": "Approved ModelGate rechecked against current AGENTS and task evidence.",
        "model_gate_evidence": "Concrete current evidence supporting the ModelGate value.",
        "unknowns": "Every unresolved fact; never delete one to obtain allow.",
        "cross_package_activation": "Strict true when the current scope crosses packages for activation.",
    }
)
EVIDENCE_FIELDS = tuple(EVIDENCE_FIELD_SOURCE_RULES)

PRE_WRITE_MODE_VECTORS = MappingProxyType(
    {
        "new_work": MappingProxyType(
            {
                "mode": "new",
                "base_branch": "main",
                "current_maturity_source": "frozen base main",
                "expected_evaluator_calls": 1,
                "expected_outcome": "PROCEED_ONLY_WITH_EXISTING_APPROVAL",
            }
        ),
        "approved_revision": MappingProxyType(
            {
                "mode": "revision",
                "base_branch": "main",
                "current_maturity_source": "frozen base main",
                "target_transition_source": "original approved transition",
                "expected_evaluator_calls": 1,
                "expected_outcome": "PROCEED_ONLY_WITH_EXISTING_APPROVAL",
            }
        ),
        "supervisor_recovery": MappingProxyType(
            {
                "mode": "recovery",
                "base_branch": "main",
                "current_maturity_source": "frozen base main",
                "target_transition_source": "original approved transition",
                "expected_evaluator_calls": 1,
                "expected_outcome": "PROCEED_ONLY_WITH_EXISTING_APPROVAL",
            }
        ),
    }
)

PRE_EVALUATOR_FAILURE_VECTORS = MappingProxyType(
    {
        "dirty_worktree": "PRE_WRITE_GIT_INVALID",
        "main_or_origin_mismatch": "PRE_WRITE_GIT_INVALID",
        "occupied_or_unknown_branch": "PRE_WRITE_BRANCH_STATE_INVALID",
        "invalid_frozen_order": "PRE_WRITE_FROZEN_ORDER_INVALID",
        "missing_dependency": "PRE_WRITE_DEPENDENCY_INVALID",
        "scope_drift": "PRE_WRITE_SCOPE_DRIFT",
        "hours_or_layer_drift": "PRE_WRITE_SIZE_OR_LAYER_DRIFT",
        "risk_or_policy_drift": "PRE_WRITE_RISK_OR_POLICY_DRIFT",
        "model_or_authority_drift": "PRE_WRITE_MODEL_AUTHORITY_INVALID",
    }
)
POST_CALL_FAILURE_VECTORS = MappingProxyType(
    {
        "evaluator_unavailable": "PRE_WRITE_EVALUATOR_UNAVAILABLE",
        "invalid_or_drifted_result": "PRE_WRITE_EVALUATOR_RESULT_INVALID",
        "unexpected_exception": "PRE_WRITE_UNEXPECTED_FAILURE",
    }
)
NO_AUTOMATIC_WRITE_ACTIONS = (
    "create or switch a branch",
    "modify a file",
    "invoke another Skill",
    "commit or push",
    "merge, tag, deploy, or activate",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _contract_table_rules(text: str) -> dict[str, str]:
    rules: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2:
            continue
        field = cells[0].strip("`")
        rules[field] = cells[1]
    return rules


def _called_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            names.add(node.func.attr)
    return names


def test_all_29_caller_owned_fields_have_exact_nonempty_source_rules() -> None:
    table_rules = _contract_table_rules(_read(CONTRACT_PATH))

    assert len(EVIDENCE_FIELD_SOURCE_RULES) == 29
    assert tuple(table_rules) == EVIDENCE_FIELDS
    assert table_rules == dict(EVIDENCE_FIELD_SOURCE_RULES)
    assert all(field and rule for field, rule in EVIDENCE_FIELD_SOURCE_RULES.items())


def test_missing_empty_or_mismatched_field_source_rules_fail_the_contract() -> None:
    source_rules = _contract_table_rules(_read(CONTRACT_PATH))

    missing = dict(source_rules)
    missing.pop("base_branch")
    empty = dict(source_rules)
    empty["base_branch"] = ""
    mismatched = dict(source_rules)
    mismatched["base_branch"] = source_rules["work_branch"]

    assert missing != dict(EVIDENCE_FIELD_SOURCE_RULES)
    assert empty != dict(EVIDENCE_FIELD_SOURCE_RULES)
    assert mismatched != dict(EVIDENCE_FIELD_SOURCE_RULES)


def test_new_revision_and_recovery_vectors_keep_base_branch_at_main() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert set(PRE_WRITE_MODE_VECTORS) == {
        "new_work",
        "approved_revision",
        "supervisor_recovery",
    }
    assert all(vector["base_branch"] == "main" for vector in PRE_WRITE_MODE_VECTORS.values())
    assert all(
        vector["expected_evaluator_calls"] == 1
        for vector in PRE_WRITE_MODE_VECTORS.values()
    )
    assert "TaskSizeGateEvidence.base_branch` remains strict `main`" in contract
    assert "recovery branch is represented only by the Git precondition and `work_branch`" in contract


def test_revision_and_recovery_keep_frozen_base_main_maturity() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    for vector_name in ("approved_revision", "supervisor_recovery"):
        vector = PRE_WRITE_MODE_VECTORS[vector_name]
        assert vector["current_maturity_source"] == "frozen base main"
        assert vector["target_transition_source"] == "original approved transition"

    assert "initial work-branch implementation is not treated as proof" in contract
    assert "preserves the frozen base-main maturity and original approved target transition" in contract
    assert "hardening or maintenance order must receive its own planning result and explicit user approval" in contract


def test_pre_evaluator_failures_require_zero_calls_and_no_write() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert set(PRE_EVALUATOR_FAILURE_VECTORS.values()) == {
        "PRE_WRITE_GIT_INVALID",
        "PRE_WRITE_BRANCH_STATE_INVALID",
        "PRE_WRITE_FROZEN_ORDER_INVALID",
        "PRE_WRITE_DEPENDENCY_INVALID",
        "PRE_WRITE_SCOPE_DRIFT",
        "PRE_WRITE_SIZE_OR_LAYER_DRIFT",
        "PRE_WRITE_RISK_OR_POLICY_DRIFT",
        "PRE_WRITE_MODEL_AUTHORITY_INVALID",
    }
    assert "workflow-level `STOP_UNCERTAIN` with zero evaluator calls" in contract
    assert "stops before branch creation or file writes" in contract
    assert "Drift detected before a valid evidence object and evaluator invocation causes zero evaluator calls." in contract


def test_valid_attempt_makes_one_call_and_post_call_failure_never_retries() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert set(POST_CALL_FAILURE_VECTORS.values()) == {
        "PRE_WRITE_EVALUATOR_UNAVAILABLE",
        "PRE_WRITE_EVALUATOR_RESULT_INVALID",
        "PRE_WRITE_UNEXPECTED_FAILURE",
    }
    assert "evaluate_task_size_gate(evidence=evidence)` exactly once" in contract
    assert "must not trigger another call" in contract
    assert "no retry, alternate evaluator, or manual result repair" in contract
    assert "one permitted evaluator call" in contract


def test_result_must_equal_frozen_planning_result_and_passing_is_not_authority() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert "entire result exactly equals the frozen planning result" in contract
    assert "planning/pre-write result difference are `STOP_UNCERTAIN`" in contract
    assert "checkpoint is not user approval" in contract
    assert all(action in contract for action in NO_AUTOMATIC_WRITE_ACTIONS)


def test_contract_uses_the_single_existing_production_evaluator_interface() -> None:
    contract = _normalized(_read(CONTRACT_PATH))
    evaluator = _read(EVALUATOR_PATH)

    assert "TaskSizeGateEvidence" in contract
    assert "TaskSizeGateResult" in contract
    assert "evaluate_task_size_gate" in contract
    assert "class TaskSizeGateEvidence" in evaluator
    assert "class TaskSizeGateResult" in evaluator
    assert "def evaluate_task_size_gate(*, evidence: object)" in evaluator
    assert "base_branch != \"main\"" in evaluator


def test_vectors_are_immutable_and_do_not_claim_runtime_integration() -> None:
    with pytest.raises(TypeError):
        PRE_WRITE_MODE_VECTORS["new_work"]["base_branch"] = "work/not-main"
    with pytest.raises(TypeError):
        PRE_EVALUATOR_FAILURE_VECTORS["dirty_worktree"] = "PROCEED"

    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )

    assert imported_modules <= {"__future__", "ast", "pathlib", "types", "pytest"}
    assert "app" not in imported_modules
    assert "evaluate_task_size_gate" not in _called_names(tree)
