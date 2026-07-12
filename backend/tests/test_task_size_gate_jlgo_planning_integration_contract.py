"""Contract vectors and static requirements for the JLGO TaskSizeGate checkpoint.

These tests lock the approved planning boundary and Skill integration text.
They deliberately do not call the evaluator or claim end-to-end verification.
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
    / "task_size_gate_jlgo_planning_integration_contract.md"
)
EVALUATOR_PATH = REPOSITORY_ROOT / "backend" / "app" / "services" / "task_size_gate.py"
JLGO_SKILL_PATH = REPOSITORY_ROOT / ".agents" / "skills" / "jlgo" / "SKILL.md"


EVIDENCE_FIELDS = (
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
REASON_CODE_CONSTANT_NAMES = (
    "INPUT_INVALID",
    "SIZE_UNCLASSIFIABLE",
    "UNKNOWN_EVIDENCE",
    "MODEL_STOP_UNCERTAIN",
    "CROSS_PACKAGE_ACTIVATION",
    "MULTIPLE_OBJECTIVES",
    "NON_ADJACENT_LAYERS",
    "OVERSIZED",
    "SINGLE_WORK_ORDER_ALLOWED",
    "PRO_MODEL_REQUIRED",
)
CALLER_OWNED_SOURCE_RULES = MappingProxyType(
    {
        "objective": "One testable outcome from the frozen candidate order.",
        "objective_count": (
            "Count independently deliverable objectives; never force it to one to "
            "obtain an allow result."
        ),
        "wbs_package_ids": (
            "Exact current WBS package identifiers supported by repository evidence."
        ),
        "current_maturity": (
            "Current narrow capability maturity proven from policy, contract, tests, "
            "implementation, integration, activation, and verification evidence."
        ),
        "target_maturity": (
            "One adjacent forward maturity, or the same maturity for an explicit "
            "hardening/maintenance revision."
        ),
        "maturity_reason": (
            "Concrete transition or maturity-preserving reason; not a generic label."
        ),
        "base_branch": "The verified base branch; normal new work uses `main`.",
        "base_main_commit": "Full immutable commit from verified local and remote main.",
        "work_branch": "One unoccupied canonical `work/...` branch.",
        "commit_message": "Exact ordinary commit message for this work order.",
        "push_destination": (
            "Exact `origin/<work_branch>` destination; never `main`."
        ),
        "stop_conditions": (
            "Frozen conditions that end the order without scope expansion."
        ),
        "estimated_engineering_hours_lower": (
            "Defensible lower equivalent-engineer-hour estimate."
        ),
        "estimated_engineering_hours_upper": (
            "Defensible upper estimate including development, tests, review-fix "
            "allowance, and required documentation."
        ),
        "allowed_files": (
            "Exact canonical relative file paths; no wildcard or directory placeholder."
        ),
        "prohibited_files": (
            "Exact canonical relative file paths that must not change."
        ),
        "prohibited_capabilities": (
            "Explicit forbidden behavior, including merge, tag, deployment, and "
            "activation when applicable."
        ),
        "capability_layers": "Ordered distinct layers actually touched by this order.",
        "subsystem_boundaries": (
            "Exact repository subsystems whose ownership boundary is affected."
        ),
        "affected_surfaces": (
            "Public interfaces, schemas, protocols, settings, filesystem, external "
            "systems, or workflow surfaces affected."
        ),
        "required_checks": (
            "Exact targeted, regression, full-suite, build or explicit N/A, grep, "
            "diff, and scope checks."
        ),
        "known_dependencies": "Dependencies whose repository evidence was inspected.",
        "dependency_evidence_known": (
            "Strict boolean; false when any dependency evidence is unavailable."
        ),
        "risk_and_policy_impacts": (
            "Explicit safety, authority, data, workflow, and trading-policy impacts."
        ),
        "high_risk_reasons": (
            "Exact reasons that require Pro; empty only when evidence proves no "
            "high-risk category applies."
        ),
        "model_gate": (
            "Caller classification using only `NORMAL_ALLOWED`, `PRO_REQUIRED`, or "
            "`STOP_UNCERTAIN`."
        ),
        "model_gate_evidence": (
            "Repository and policy evidence supporting the caller classification."
        ),
        "unknowns": (
            "Every unresolved fact that could change size, scope, checks, "
            "dependencies, risk, or authority."
        ),
        "cross_package_activation": (
            "Strict boolean; true only for an order that crosses packages while "
            "activating a capability."
        ),
    }
)

PREFLIGHT_VECTOR_KEYS = frozenset(
    {
        "case_id",
        "current_branch",
        "main_and_origin_synchronized",
        "worktree_clean",
        "active_unmerged_work_branch",
        "ancestry_known",
        "target_branch_available",
        "expected_disposition",
        "expected_next_skill",
    }
)
PREFLIGHT_VECTORS = (
    MappingProxyType(
        {
            "case_id": "clean_synchronized_main",
            "current_branch": "main",
            "main_and_origin_synchronized": True,
            "worktree_clean": True,
            "active_unmerged_work_branch": False,
            "ancestry_known": True,
            "target_branch_available": True,
            "expected_disposition": "CONSTRUCT_EVIDENCE",
            "expected_next_skill": "none_until_evaluator_mapping",
        }
    ),
    MappingProxyType(
        {
            "case_id": "active_work_branch_routes_existing_work_only",
            "current_branch": "work/example",
            "main_and_origin_synchronized": True,
            "worktree_clean": True,
            "active_unmerged_work_branch": True,
            "ancestry_known": True,
            "target_branch_available": True,
            "expected_disposition": "ROUTE_REVIEW_REVISION_OR_MERGE",
            "expected_next_skill": "existing_work_path_only",
        }
    ),
    MappingProxyType(
        {
            "case_id": "dirty_worktree_stops",
            "current_branch": "main",
            "main_and_origin_synchronized": True,
            "worktree_clean": False,
            "active_unmerged_work_branch": False,
            "ancestry_known": True,
            "target_branch_available": True,
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "main_mismatch_stops",
            "current_branch": "main",
            "main_and_origin_synchronized": False,
            "worktree_clean": True,
            "active_unmerged_work_branch": False,
            "ancestry_known": True,
            "target_branch_available": True,
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "non_main_without_active_work_stops",
            "current_branch": "archive/old-work",
            "main_and_origin_synchronized": True,
            "worktree_clean": True,
            "active_unmerged_work_branch": False,
            "ancestry_known": True,
            "target_branch_available": True,
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "unknown_ancestry_stops",
            "current_branch": "main",
            "main_and_origin_synchronized": True,
            "worktree_clean": True,
            "active_unmerged_work_branch": False,
            "ancestry_known": False,
            "target_branch_available": True,
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "occupied_target_branch_stops",
            "current_branch": "main",
            "main_and_origin_synchronized": True,
            "worktree_clean": True,
            "active_unmerged_work_branch": False,
            "ancestry_known": True,
            "target_branch_available": False,
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
)

RESULT_VECTOR_KEYS = frozenset(
    {
        "case_id",
        "task_size",
        "task_decision",
        "model_gate",
        "supervisor_eligibility",
        "reason_codes_state",
        "expected_disposition",
        "expected_next_skill",
    }
)
RESULT_VECTORS = (
    MappingProxyType(
        {
            "case_id": "unclassifiable_size_stops",
            "task_size": None,
            "task_decision": "STOP_UNCERTAIN",
            "model_gate": "STOP_UNCERTAIN",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_blocking",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "known_size_blocked_stops",
            "task_size": "S",
            "task_decision": "STOP_UNCERTAIN",
            "model_gate": "STOP_UNCERTAIN",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_blocking",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "large_normal_work_splits",
            "task_size": "L",
            "task_decision": "SPLIT_REQUIRED",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_split",
            "expected_disposition": "READ_ONLY_DECOMPOSITION",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "extra_large_pro_work_splits",
            "task_size": "XL",
            "task_decision": "SPLIT_REQUIRED",
            "model_gate": "PRO_REQUIRED",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_split",
            "expected_disposition": "READ_ONLY_DECOMPOSITION",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "extra_small_normal_work_is_supervisor_candidate",
            "task_size": "XS",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "RECOMMEND_WITH_APPROVAL",
            "expected_next_skill": "jl-supervisor",
        }
    ),
    MappingProxyType(
        {
            "case_id": "small_normal_work_is_supervisor_candidate",
            "task_size": "S",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "RECOMMEND_WITH_APPROVAL",
            "expected_next_skill": "jl-supervisor",
        }
    ),
    MappingProxyType(
        {
            "case_id": "medium_normal_work_uses_develop",
            "task_size": "M",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "RECOMMEND_WITH_APPROVAL",
            "expected_next_skill": "jl-develop",
        }
    ),
    MappingProxyType(
        {
            "case_id": "extra_small_pro_work_is_conditional_supervisor_candidate",
            "task_size": "XS",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "PRO_REQUIRED",
            "supervisor_eligibility": "CONDITIONAL_PRO_RESUME",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "RECOMMEND_WITH_EXPLICIT_PRO_APPROVAL",
            "expected_next_skill": "jl-supervisor",
        }
    ),
    MappingProxyType(
        {
            "case_id": "small_pro_work_is_conditional_supervisor_candidate",
            "task_size": "S",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "PRO_REQUIRED",
            "supervisor_eligibility": "CONDITIONAL_PRO_RESUME",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "RECOMMEND_WITH_EXPLICIT_PRO_APPROVAL",
            "expected_next_skill": "jl-supervisor",
        }
    ),
    MappingProxyType(
        {
            "case_id": "medium_pro_work_uses_develop",
            "task_size": "M",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "PRO_REQUIRED",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "RECOMMEND_WITH_EXPLICIT_PRO_APPROVAL",
            "expected_next_skill": "jl-develop",
        }
    ),
)

INVALID_RESULT_VECTORS = (
    MappingProxyType(
        {
            "case_id": "unknown_task_size",
            "task_size": "UNKNOWN",
            "task_decision": "STOP_UNCERTAIN",
            "model_gate": "STOP_UNCERTAIN",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_blocking",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "small_normal_not_eligible_conflict",
            "task_size": "S",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "medium_normal_eligible_conflict",
            "task_size": "M",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "small_pro_not_eligible_conflict",
            "task_size": "S",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "PRO_REQUIRED",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "medium_pro_conditional_conflict",
            "task_size": "M",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "PRO_REQUIRED",
            "supervisor_eligibility": "CONDITIONAL_PRO_RESUME",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "large_allow_conflict",
            "task_size": "L",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "unknown_task_decision",
            "task_size": "S",
            "task_decision": "UNKNOWN",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "unknown_model_gate",
            "task_size": "S",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "UNKNOWN",
            "supervisor_eligibility": "ELIGIBLE",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "unknown_supervisor_eligibility",
            "task_size": "S",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "UNKNOWN",
            "reason_codes_state": "valid_allow",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "inconsistent_reason_code",
            "task_size": "S",
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "ELIGIBLE",
            "reason_codes_state": "inconsistent",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "unknown_reason_code",
            "task_size": "S",
            "task_decision": "STOP_UNCERTAIN",
            "model_gate": "STOP_UNCERTAIN",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "unknown",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
    MappingProxyType(
        {
            "case_id": "duplicate_reason_code",
            "task_size": "S",
            "task_decision": "STOP_UNCERTAIN",
            "model_gate": "STOP_UNCERTAIN",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes_state": "duplicated",
            "expected_disposition": "STOP_UNCERTAIN",
            "expected_next_skill": "none",
        }
    ),
)


def _dataclass_fields(source: str, class_name: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return tuple(
                child.target.id
                for child in node.body
                if isinstance(child, ast.AnnAssign)
                and isinstance(child.target, ast.Name)
            )
    raise AssertionError(f"missing dataclass {class_name}")


def _import_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _marked_lines(text: str, *, start: str, end: str) -> tuple[str, ...]:
    assert text.count(start) == 1
    assert text.count(end) == 1
    body = text.split(start, 1)[1].split(end, 1)[0]
    return tuple(line.strip() for line in body.splitlines() if line.strip())


def _python_code_blocks(text: str) -> tuple[str, ...]:
    return tuple(
        segment.split("```", 1)[0].strip()
        for segment in text.split("```python")[1:]
    )


def _caller_owned_source_rules(contract: str) -> dict[str, str]:
    rules: dict[str, str] = {}
    for line in contract.splitlines():
        cells = line.split("|")
        if len(cells) != 4:
            continue
        field = cells[1].strip()
        if not (field.startswith("`") and field.endswith("`")):
            continue
        field = field.removeprefix("`").removesuffix("`")
        if field in EVIDENCE_FIELDS:
            rules[field] = cells[2].strip()
    return rules


def _assert_exact_caller_owned_source_rules(contract: str) -> None:
    for field in EVIDENCE_FIELDS:
        assert contract.count(f"| `{field}` |") == 1
    assert _caller_owned_source_rules(contract) == dict(CALLER_OWNED_SOURCE_RULES)


def test_contract_has_exactly_twenty_nine_caller_owned_evidence_fields() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    evaluator = EVALUATOR_PATH.read_text(encoding="utf-8")

    assert len(EVIDENCE_FIELDS) == 29
    assert len(set(EVIDENCE_FIELDS)) == 29
    assert _dataclass_fields(evaluator, "TaskSizeGateEvidence") == EVIDENCE_FIELDS
    assert type(CALLER_OWNED_SOURCE_RULES) is MappingProxyType
    assert tuple(CALLER_OWNED_SOURCE_RULES) == EVIDENCE_FIELDS
    assert len(CALLER_OWNED_SOURCE_RULES) == 29
    with pytest.raises(TypeError):
        CALLER_OWNED_SOURCE_RULES["objective"] = "rewritten"  # type: ignore[index]
    _assert_exact_caller_owned_source_rules(contract)
    assert "All fields are caller-owned." in contract
    assert "must build a fresh frozen\n`TaskSizeGateEvidence`" in contract


def test_caller_owned_source_rules_reject_missing_empty_and_mismatched_rows() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    objective_row = (
        "| `objective` | "
        f"{CALLER_OWNED_SOURCE_RULES['objective']} |"
    )

    assert objective_row in contract
    invalid_contracts = (
        contract.replace(objective_row, "", 1),
        contract.replace(objective_row, "| `objective` |  |", 1),
        contract.replace(
            objective_row,
            "| `objective` | Exact ordinary commit message for this work order. |",
            1,
        ),
    )
    for invalid_contract in invalid_contracts:
        with pytest.raises(AssertionError):
            _assert_exact_caller_owned_source_rules(invalid_contract)


def test_preflight_vectors_are_immutable_and_lock_main_only_planning() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert {vector["case_id"] for vector in PREFLIGHT_VECTORS} == {
        "clean_synchronized_main",
        "active_work_branch_routes_existing_work_only",
        "dirty_worktree_stops",
        "main_mismatch_stops",
        "non_main_without_active_work_stops",
        "unknown_ancestry_stops",
        "occupied_target_branch_stops",
    }
    for vector in PREFLIGHT_VECTORS:
        assert type(vector) is MappingProxyType
        assert frozenset(vector) == PREFLIGHT_VECTOR_KEYS
    with pytest.raises(TypeError):
        PREFLIGHT_VECTORS[0]["current_branch"] = "work/not-allowed"  # type: ignore[index]

    assert "current branch is exactly `main`" in contract
    assert "same immutable commit" in contract
    assert "active unmerged work" in contract
    assert "unresolved\nancestry" in contract
    assert "occupied target branch" in contract
    assert "only the applicable review, revision, or merge path" in contract
    assert "must stop without proposing a new\ndevelopment order" in contract


def test_result_vectors_lock_legal_mapping_and_explicit_approval_boundary() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert len(RESULT_VECTORS) == 10
    for vector in RESULT_VECTORS:
        assert type(vector) is MappingProxyType
        assert frozenset(vector) == RESULT_VECTOR_KEYS

    allowed_vectors = [
        vector
        for vector in RESULT_VECTORS
        if vector["task_decision"] == "ALLOW_SINGLE_WORK_ORDER"
    ]
    assert {
        (
            vector["task_size"],
            vector["model_gate"],
            vector["supervisor_eligibility"],
            vector["expected_next_skill"],
        )
        for vector in allowed_vectors
    } == {
        ("XS", "NORMAL_ALLOWED", "ELIGIBLE", "jl-supervisor"),
        ("S", "NORMAL_ALLOWED", "ELIGIBLE", "jl-supervisor"),
        ("M", "NORMAL_ALLOWED", "NOT_ELIGIBLE", "jl-develop"),
        ("XS", "PRO_REQUIRED", "CONDITIONAL_PRO_RESUME", "jl-supervisor"),
        ("S", "PRO_REQUIRED", "CONDITIONAL_PRO_RESUME", "jl-supervisor"),
        ("M", "PRO_REQUIRED", "NOT_ELIGIBLE", "jl-develop"),
    }
    split_vectors = [
        vector
        for vector in RESULT_VECTORS
        if vector["task_decision"] == "SPLIT_REQUIRED"
    ]
    assert {vector["task_size"] for vector in split_vectors} == {"L", "XL"}
    assert all(vector["expected_next_skill"] == "none" for vector in split_vectors)
    assert "planning disposition but never user authority" in contract
    assert "Every write\noperation still requires explicit user approval" in contract


def test_unknown_or_contradictory_result_vectors_always_fail_closed() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert len(INVALID_RESULT_VECTORS) == 12
    assert len({vector["case_id"] for vector in INVALID_RESULT_VECTORS}) == 12
    for vector in INVALID_RESULT_VECTORS:
        assert type(vector) is MappingProxyType
        assert frozenset(vector) == RESULT_VECTOR_KEYS
        assert vector["expected_disposition"] == "STOP_UNCERTAIN"
        assert vector["expected_next_skill"] == "none"
    with pytest.raises(TypeError):
        INVALID_RESULT_VECTORS[0]["task_size"] = "S"  # type: ignore[index]

    assert "Any unknown or contradictory TaskSize" in contract
    assert "reason-code combination" in contract
    assert "emit `STOP_UNCERTAIN`" in contract
    assert "no next\nSkill" in contract
    assert "reason codes are unknown, inconsistent, duplicated, or malformed" in contract


def test_historical_contract_keeps_staging_and_authority_boundaries() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    required_boundaries = (
        "not integrate or activate the evaluator in this work order.",
        "must not construct a\nnew development candidate.",
        "without separate approval.",
        "No stage may silently combine the next stage",
    )
    for boundary in required_boundaries:
        assert boundary in contract
    assert "tests-only JLGO planning-integration contract vectors" in contract
    assert "JLGO planning-checkpoint Skill integration and hardening" in contract


def test_jlgo_constructs_all_fields_and_calls_the_production_evaluator_once() -> None:
    skill = JLGO_SKILL_PATH.read_text(encoding="utf-8")
    python_blocks = _python_code_blocks(skill)

    assert _marked_lines(
        skill,
        start="TASK_SIZE_GATE_EVIDENCE_FIELDS_BEGIN",
        end="TASK_SIZE_GATE_EVIDENCE_FIELDS_END",
    ) == EVIDENCE_FIELDS
    assert len(python_blocks) == 2
    import_tree = ast.parse(python_blocks[0])
    import_node = import_tree.body[0]
    assert isinstance(import_node, ast.ImportFrom)
    assert import_node.module == "app.services.task_size_gate"
    assert tuple(alias.name for alias in import_node.names) == (
        "CROSS_PACKAGE_ACTIVATION",
        "INPUT_INVALID",
        "MODEL_STOP_UNCERTAIN",
        "MULTIPLE_OBJECTIVES",
        "NON_ADJACENT_LAYERS",
        "OVERSIZED",
        "PRO_MODEL_REQUIRED",
        "SINGLE_WORK_ORDER_ALLOWED",
        "SIZE_UNCLASSIFIABLE",
        "TaskSizeGateEvidence",
        "TaskSizeGateResult",
        "UNKNOWN_EVIDENCE",
        "evaluate_task_size_gate",
    )
    assert ast.unparse(ast.parse(python_blocks[1])) == (
        "result = evaluate_task_size_gate(evidence=evidence)"
    )
    assert skill.count("result = evaluate_task_size_gate(evidence=evidence)") == 1
    assert "fresh、frozen、strict `TaskSizeGateEvidence`" in skill
    assert "不得 monkeypatch、retry、创建 fallback classifier" in skill


def test_jlgo_requires_exact_result_reason_codes_and_fail_closed_mapping() -> None:
    skill = JLGO_SKILL_PATH.read_text(encoding="utf-8")
    normalized = " ".join(skill.split())

    assert "type(result) is TaskSizeGateResult" in skill
    assert all(name in skill for name in REASON_CODE_CONSTANT_NAMES)
    for requirement in (
        "strict `tuple[str, ...]`",
        "非空、无重复、确定顺序",
        "blocked result 必须恰好一个 reason",
        "且只能来自 `INPUT_INVALID`、`SIZE_UNCLASSIFIABLE`、`UNKNOWN_EVIDENCE` 或 `MODEL_STOP_UNCERTAIN`",
        "allow result 必须是 `SINGLE_WORK_ORDER_ALLOWED`",
        "split result 必须至少包含一个 `CROSS_PACKAGE_ACTIVATION`",
        "workflow-level `STOP_UNCERTAIN`",
        "下一 Skill 为 `无`",
        "失败调用不得 fallback、retry 或推荐另一个 Skill",
    ):
        assert requirement in normalized


def test_jlgo_locks_result_dispositions_and_explicit_user_authority() -> None:
    skill = JLGO_SKILL_PATH.read_text(encoding="utf-8")
    normalized = " ".join(skill.split())

    for combination in (
        "`L/XL` + `SPLIT_REQUIRED` + `NORMAL_ALLOWED/PRO_REQUIRED`",
        "`XS/S` + `ALLOW_SINGLE_WORK_ORDER` + `NORMAL_ALLOWED` + `ELIGIBLE`",
        "`M` + `ALLOW_SINGLE_WORK_ORDER` + `NORMAL_ALLOWED` + `NOT_ELIGIBLE`",
        "`XS/S` + `ALLOW_SINGLE_WORK_ORDER` + `PRO_REQUIRED`",
        "`M` + `ALLOW_SINGLE_WORK_ORDER` + `PRO_REQUIRED` + `NOT_ELIGIBLE`",
    ):
        assert combination in normalized
    assert "TaskSizeGate result 只是规划分类，不是用户批准" in normalized
    assert "创建或切换分支、修改文件、调用 Skill、merge、tag、部署、activation" in normalized
    assert "显式批准" in normalized


def test_static_tests_do_not_call_evaluator_or_claim_end_to_end_verification() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    skill = JLGO_SKILL_PATH.read_text(encoding="utf-8")

    assert _import_roots(tree) <= {"__future__", "ast", "pathlib", "types", "pytest"}
    call_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert {
        "evaluate_task_size_gate",
        "TaskSizeGateEvidence",
        "TaskSizeGateResult",
    }.isdisjoint(call_names)
    assert "must not claim that TaskSizeGate is integrated" in CONTRACT_PATH.read_text(
        encoding="utf-8"
    )
    assert "不代表\npre-write/review/CI integration、workflow activation 或 end-to-end verification" in skill
