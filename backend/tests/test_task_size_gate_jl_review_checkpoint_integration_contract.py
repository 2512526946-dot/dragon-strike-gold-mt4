"""Static contract vectors for the future jl-review TaskSizeGate checkpoint.

These tests lock the WF-4K contract without importing or calling the production
evaluator, a workflow Skill, or a future runtime integration. They do not prove
that the jl-review checkpoint is implemented, activated, or verified end to end.
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
    / "task_size_gate_jl_review_checkpoint_integration_contract.md"
)
EVALUATOR_PATH = REPOSITORY_ROOT / "backend" / "app" / "services" / "task_size_gate.py"
JL_REVIEW_SKILL_PATH = REPOSITORY_ROOT / ".agents" / "skills" / "jl-review" / "SKILL.md"


EVIDENCE_FIELD_SOURCE_RULES = MappingProxyType(
    {
        "objective": "Exact single outcome from the frozen approved work order; unchanged by implementation or review.",
        "objective_count": "Recount independently deliverable outcomes in the actual cumulative diff; any value other than the frozen count is drift.",
        "wbs_package_ids": "Frozen package IDs checked against current WBS ownership; an added package is drift.",
        "current_maturity": "Narrow capability maturity proven at frozen base main; unmerged commits never advance it.",
        "target_maturity": "Exact frozen adjacent target, or exact separately approved maturity-preserving target.",
        "maturity_reason": "Exact frozen transition or separately approved hardening/maintenance reason.",
        "base_branch": "Strict `main`; the reviewed work branch is never substituted here.",
        "base_main_commit": "Fresh equality of local main, remote main, and the frozen base commit.",
        "work_branch": "Exact frozen branch whose local and remote tips equal the reviewed head.",
        "commit_message": "Exact original frozen work-order message used at planning; it remains unchanged for the entire review and is never replaced by a manual or Supervisor revision message. Actual commit subjects and their authority are validated separately through the ordered commit-authority list.",
        "push_destination": "Exact `origin/<work_branch>` destination and never `main`.",
        "stop_conditions": "Exact frozen stop conditions; no deletion, weakening, or post hoc rewrite.",
        "estimated_engineering_hours_lower": "Frozen approved lower estimate; review must not reduce it to obtain an allow result.",
        "estimated_engineering_hours_upper": "Frozen upper estimate compared with actual scope and effort evidence; any required increase is drift.",
        "allowed_files": "Exact frozen canonical relative-file scope, checked against every cumulative changed path.",
        "prohibited_files": "Exact frozen canonical prohibited paths, checked case-insensitively against the cumulative diff.",
        "prohibited_capabilities": "Frozen capability, policy, merge, release, deployment, and activation exclusions checked against actual behavior.",
        "capability_layers": "Ordered distinct frozen layers compared with actual interfaces and effects; any undeclared layer is drift.",
        "subsystem_boundaries": "Frozen ownership boundaries checked against all imports, files, contracts, and runtime effects.",
        "affected_surfaces": "Frozen impact surfaces revalidated against the actual diff and tests; any added surface is drift.",
        "required_checks": "Complete targeted, regression, full-suite, build or explicit N/A, grep, diff, and scope categories with actual evidence.",
        "known_dependencies": "Every frozen dependency re-proven from repository evidence; newly required dependency is drift.",
        "dependency_evidence_known": "Strict true only when every dependency remains present, compatible, and reviewable.",
        "risk_and_policy_impacts": "Frozen impacts rechecked against actual code, tests, outputs, permissions, and safety policy.",
        "high_risk_reasons": "Exact current ModelGate reasons with no omission, downgrade, or post hoc addition.",
        "model_gate": "Frozen ModelGate rechecked against AGENTS and actual capability effect; `PRO_REQUIRED` is never downgraded.",
        "model_gate_evidence": "Concrete frozen and current evidence supporting the same ModelGate result.",
        "unknowns": "Every unresolved Git, scope, interface, test, dependency, risk, or policy fact; never removed to obtain allow.",
        "cross_package_activation": "Strict true only when actual scope performs cross-package activation; any change from frozen false is drift and any true value is outside this reviewable single-order path.",
    }
)
EVIDENCE_FIELDS = tuple(EVIDENCE_FIELD_SOURCE_RULES)

IMMUTABLE_REVIEW_INPUTS = (
    "immutable base branch `main` and base commit",
    "exact work branch and reviewed head",
    "local and remote work-branch heads",
    "ordered ordinary commit list between base and head",
    "immutable ordered commit-authority list",
    "exact frozen planning `TaskSizeGateResult`",
    "exact latest accepted pre-write `TaskSizeGateResult`",
    "actual cumulative diff and changed-file list",
    "actual test, build, grep, diff, and scope evidence",
    "explicit review-only authority",
)

COMMIT_AUTHORITY_VECTORS = (
    MappingProxyType(
        {
            "role": "initial",
            "subject_source": "original frozen work-order commit_message",
            "per_round_user_approval": False,
        }
    ),
    MappingProxyType(
        {
            "role": "manual_revision",
            "subject_source": "exact message in the approved revision order",
            "per_round_user_approval": True,
        }
    ),
    MappingProxyType(
        {
            "role": "supervisor_automatic_revision",
            "subject_source": "message frozen before the first revision write",
            "per_round_user_approval": False,
        }
    ),
)

PRE_CALL_GIT_FAILURE_VECTORS = MappingProxyType(
    {
        "dirty_or_conflicted_worktree": "REVIEW_CHECKPOINT_GIT_INVALID",
        "main_or_origin_mismatch": "REVIEW_CHECKPOINT_GIT_INVALID",
        "local_or_remote_head_mismatch": "REVIEW_CHECKPOINT_GIT_INVALID",
        "base_not_ancestor": "REVIEW_CHECKPOINT_GIT_INVALID",
        "nonlinear_or_rewritten_commits": "REVIEW_CHECKPOINT_GIT_INVALID",
        "unpushed_or_uncommitted_change": "REVIEW_CHECKPOINT_GIT_INVALID",
        "scope_or_prohibited_file_drift": "REVIEW_CHECKPOINT_SCOPE_DRIFT",
        "merged_moved_deleted_or_replaced_branch": "REVIEW_CHECKPOINT_GIT_INVALID",
    }
)

INVALID_COMMIT_EVIDENCE_VECTORS = tuple(
    MappingProxyType(
        {
            "case_id": case_id,
            "failure_category": "REVIEW_CHECKPOINT_FROZEN_ORDER_INVALID",
            "evaluator_calls": 0,
            "conclusion": "NO-GO",
            "next_skill": "none",
        }
    )
    for case_id in (
        "missing_commit_or_authority_entry",
        "extra_commit_or_authority_entry",
        "reordered_commit_or_authority_entry",
        "duplicated_commit_subject_or_authority_entry",
        "unprovable_commit_role_or_authority_source",
    )
)

PRE_CALL_FAILURE_CATEGORIES = (
    "REVIEW_CHECKPOINT_GIT_INVALID",
    "REVIEW_CHECKPOINT_FROZEN_ORDER_INVALID",
    "REVIEW_CHECKPOINT_DEPENDENCY_INVALID",
    "REVIEW_CHECKPOINT_SCOPE_DRIFT",
    "REVIEW_CHECKPOINT_SIZE_OR_LAYER_DRIFT",
    "REVIEW_CHECKPOINT_RISK_OR_POLICY_DRIFT",
    "REVIEW_CHECKPOINT_EVALUATOR_UNAVAILABLE",
)
POST_CALL_FAILURE_CATEGORIES = (
    "REVIEW_CHECKPOINT_EVALUATOR_RESULT_INVALID",
    "REVIEW_CHECKPOINT_UNEXPECTED_FAILURE",
)

CALL_ACCOUNTING_VECTORS = MappingProxyType(
    {
        "pre_call_failure": MappingProxyType(
            {
                "evaluator_calls": 0,
                "retry": False,
                "conclusion": "NO-GO",
                "next_skill": "none",
            }
        ),
        "valid_attempt": MappingProxyType(
            {
                "evaluator_calls": 1,
                "retry": False,
                "conclusion": "CONTINUE_INDEPENDENT_REVIEW",
                "next_skill": "none",
            }
        ),
        "post_call_failure": MappingProxyType(
            {
                "evaluator_calls": 1,
                "retry": False,
                "conclusion": "NO-GO",
                "next_skill": "none",
            }
        ),
    }
)

ALLOWED_RESULT_VECTORS = (
    MappingProxyType(
        {
            "task_sizes": ("XS", "S"),
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "ELIGIBLE",
            "reason_codes": ("SINGLE_WORK_ORDER_ALLOWED",),
            "result_identity": "planning == pre_write == review",
        }
    ),
    MappingProxyType(
        {
            "task_sizes": ("M",),
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "NORMAL_ALLOWED",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes": ("SINGLE_WORK_ORDER_ALLOWED",),
            "result_identity": "planning == pre_write == review",
        }
    ),
    MappingProxyType(
        {
            "task_sizes": ("XS", "S"),
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "PRO_REQUIRED",
            "supervisor_eligibility": "CONDITIONAL_PRO_RESUME",
            "reason_codes": (
                "SINGLE_WORK_ORDER_ALLOWED",
                "PRO_MODEL_REQUIRED",
            ),
            "result_identity": "planning == pre_write == review",
        }
    ),
    MappingProxyType(
        {
            "task_sizes": ("M",),
            "task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "model_gate": "PRO_REQUIRED",
            "supervisor_eligibility": "NOT_ELIGIBLE",
            "reason_codes": (
                "SINGLE_WORK_ORDER_ALLOWED",
                "PRO_MODEL_REQUIRED",
            ),
            "result_identity": "planning == pre_write == review",
        }
    ),
)

INVALID_RESULT_VECTORS = tuple(
    MappingProxyType(
        {
            "case_id": case_id,
            "evaluator_calls": 1,
            "conclusion": "NO-GO",
            "next_skill": "none",
        }
    )
    for case_id in (
        "unknown_or_extra_reason",
        "missing_reason",
        "duplicate_reason",
        "out_of_order_reason",
        "model_gate_reason_mismatch",
        "task_size_decision_or_eligibility_mismatch",
        "planning_pre_write_or_review_result_mismatch",
        "stop_or_split_result_on_a_reviewable_branch",
    )
)

NO_AUTOMATIC_ACTIONS = (
    "approve the work on the user's behalf",
    "create, switch, move, or delete a branch",
    "modify files or tests",
    "invoke another Skill or agent",
    "commit, push, merge, rebase, tag, release, deploy, or activate",
    "enable a reader, access real MT4, call an EA, or create an order",
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
        rules[cells[0].strip("`")] = cells[1]
    return rules


def _dataclass_fields(source: str, class_name: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return tuple(
                statement.target.id
                for statement in node.body
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
            )
    raise AssertionError(f"missing dataclass {class_name}")


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


def test_contract_vectors_are_immutable() -> None:
    with pytest.raises(TypeError):
        EVIDENCE_FIELD_SOURCE_RULES["objective"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        PRE_CALL_GIT_FAILURE_VECTORS["new"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        CALL_ACCOUNTING_VECTORS["valid_attempt"]["retry"] = True  # type: ignore[index]


def test_all_29_evidence_fields_have_exact_nonempty_review_sources() -> None:
    contract_rules = _contract_table_rules(_read(CONTRACT_PATH))
    evaluator_fields = _dataclass_fields(
        _read(EVALUATOR_PATH), "TaskSizeGateEvidence"
    )

    assert len(EVIDENCE_FIELD_SOURCE_RULES) == 29
    assert len(set(EVIDENCE_FIELD_SOURCE_RULES)) == 29
    assert tuple(contract_rules) == EVIDENCE_FIELDS
    assert contract_rules == dict(EVIDENCE_FIELD_SOURCE_RULES)
    assert evaluator_fields == EVIDENCE_FIELDS
    assert all(field and source for field, source in EVIDENCE_FIELD_SOURCE_RULES.items())


def test_missing_empty_or_mismatched_review_source_rules_fail() -> None:
    rules = _contract_table_rules(_read(CONTRACT_PATH))
    missing = dict(rules)
    missing.pop("commit_message")
    empty = dict(rules)
    empty["commit_message"] = ""
    mismatched = dict(rules)
    mismatched["commit_message"] = rules["work_branch"]

    assert missing != dict(EVIDENCE_FIELD_SOURCE_RULES)
    assert empty != dict(EVIDENCE_FIELD_SOURCE_RULES)
    assert mismatched != dict(EVIDENCE_FIELD_SOURCE_RULES)


def test_immutable_review_inputs_are_complete_and_caller_owned() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert len(IMMUTABLE_REVIEW_INPUTS) == 10
    assert all(item in contract for item in IMMUTABLE_REVIEW_INPUTS)
    assert "The reviewer must obtain Git and diff facts itself" in contract
    assert "Missing, mutable, inaccessible, or contradictory artifacts fail closed" in contract


def test_commit_message_remains_original_and_authority_is_separate() -> None:
    contract = _normalized(_read(CONTRACT_PATH))
    roles = tuple(vector["role"] for vector in COMMIT_AUTHORITY_VECTORS)

    assert roles == (
        "initial",
        "manual_revision",
        "supervisor_automatic_revision",
    )
    assert COMMIT_AUTHORITY_VECTORS[0]["subject_source"] == (
        "original frozen work-order commit_message"
    )
    assert COMMIT_AUTHORITY_VECTORS[1]["per_round_user_approval"] is True
    assert COMMIT_AUTHORITY_VECTORS[2]["per_round_user_approval"] is False
    assert "it remains unchanged for the entire review" in contract
    assert "never replaced by a manual or Supervisor revision message" in contract
    assert "without adding a TaskSizeGate evidence field" in contract
    assert "not a repository file, state file, progress record, database, or thirtieth" in contract
    assert "no additional per-round user approval is implied" in contract


def test_invalid_commit_evidence_fails_before_the_evaluator() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert tuple(
        vector["case_id"] for vector in INVALID_COMMIT_EVIDENCE_VECTORS
    ) == (
        "missing_commit_or_authority_entry",
        "extra_commit_or_authority_entry",
        "reordered_commit_or_authority_entry",
        "duplicated_commit_subject_or_authority_entry",
        "unprovable_commit_role_or_authority_source",
    )
    assert all(
        vector["failure_category"]
        == "REVIEW_CHECKPOINT_FROZEN_ORDER_INVALID"
        and vector["evaluator_calls"] == 0
        and vector["conclusion"] == "NO-GO"
        and vector["next_skill"] == "none"
        for vector in INVALID_COMMIT_EVIDENCE_VECTORS
    )
    assert "Missing, extra, reordered, duplicated, or unprovable commits, subjects, roles, or authority entries" in contract
    assert "commit-subject authority" in contract
    assert "makes zero evaluator calls" in contract
    assert "frozen-order failure" in contract


def test_git_preconditions_are_complete_zero_call_vectors() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert len(PRE_CALL_GIT_FAILURE_VECTORS) == 8
    assert set(PRE_CALL_GIT_FAILURE_VECTORS.values()) == {
        "REVIEW_CHECKPOINT_GIT_INVALID",
        "REVIEW_CHECKPOINT_SCOPE_DRIFT",
    }
    for required in (
        "worktree and index are clean and conflict-free",
        "local `main` and `origin/main` both equal the frozen base commit",
        "local and remote work-branch heads equal the frozen head",
        "frozen base `main` is an ancestor of the reviewed head",
        "contains only the expected linear ordinary commits",
        "no merge commit, rebase, rewritten commit, unpushed commit, or uncommitted change",
        "remain within the frozen allowed scope",
        "branch has not already been merged, moved, deleted, or replaced",
    ):
        assert required in contract
    assert "Failure of any precondition uses zero evaluator calls" in contract


def test_call_accounting_is_zero_then_exactly_one_without_retry() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert CALL_ACCOUNTING_VECTORS["pre_call_failure"] == {
        "evaluator_calls": 0,
        "retry": False,
        "conclusion": "NO-GO",
        "next_skill": "none",
    }
    assert CALL_ACCOUNTING_VECTORS["valid_attempt"]["evaluator_calls"] == 1
    assert CALL_ACCOUNTING_VECTORS["post_call_failure"] == {
        "evaluator_calls": 1,
        "retry": False,
        "conclusion": "NO-GO",
        "next_skill": "none",
    }
    assert "reviewer call exactly once" in contract
    assert "consumes the one permitted call" in contract
    assert "no failure may retry, fallback" in contract
    assert "call a second time" in contract


def test_production_interface_is_reused_without_a_local_classifier() -> None:
    contract = _read(CONTRACT_PATH)
    evaluator = _read(EVALUATOR_PATH)

    for name in (
        "TaskSizeGateEvidence",
        "TaskSizeGateResult",
        "SINGLE_WORK_ORDER_ALLOWED",
        "PRO_MODEL_REQUIRED",
        "evaluate_task_size_gate",
    ):
        assert name in contract
        assert name in evaluator
    assert "result = evaluate_task_size_gate(evidence=evidence)" in contract
    assert contract.count("result = evaluate_task_size_gate(evidence=evidence)") == 1
    assert "must not copy thresholds, create a local classifier" in _normalized(contract)


def test_allowed_results_require_ordered_public_reasons_and_identity() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert len(ALLOWED_RESULT_VECTORS) == 4
    assert tuple(
        (
            vector["task_sizes"],
            vector["model_gate"],
            vector["supervisor_eligibility"],
        )
        for vector in ALLOWED_RESULT_VECTORS
    ) == (
        (("XS", "S"), "NORMAL_ALLOWED", "ELIGIBLE"),
        (("M",), "NORMAL_ALLOWED", "NOT_ELIGIBLE"),
        (("XS", "S"), "PRO_REQUIRED", "CONDITIONAL_PRO_RESUME"),
        (("M",), "PRO_REQUIRED", "NOT_ELIGIBLE"),
    )
    assert all(
        vector["task_decision"] == "ALLOW_SINGLE_WORK_ORDER"
        for vector in ALLOWED_RESULT_VECTORS
    )
    assert ALLOWED_RESULT_VECTORS[0]["reason_codes"] == (
        "SINGLE_WORK_ORDER_ALLOWED",
    )
    assert ALLOWED_RESULT_VECTORS[1]["reason_codes"] == (
        "SINGLE_WORK_ORDER_ALLOWED",
    )
    assert ALLOWED_RESULT_VECTORS[2]["reason_codes"] == (
        "SINGLE_WORK_ORDER_ALLOWED",
        "PRO_MODEL_REQUIRED",
    )
    assert ALLOWED_RESULT_VECTORS[3]["reason_codes"] == (
        "SINGLE_WORK_ORDER_ALLOWED",
        "PRO_MODEL_REQUIRED",
    )
    assert all(
        vector["result_identity"] == "planning == pre_write == review"
        for vector in ALLOWED_RESULT_VECTORS
    )
    assert "an allowed NORMAL result has exactly `(SINGLE_WORK_ORDER_ALLOWED,)`" in contract
    assert "an allowed PRO result has exactly `(SINGLE_WORK_ORDER_ALLOWED, PRO_MODEL_REQUIRED)`" in contract
    assert "entire result equals both the frozen planning result and the latest accepted pre-write result" in contract


def test_invalid_results_and_reasons_always_fail_closed() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert len(INVALID_RESULT_VECTORS) == 8
    assert all(
        vector["evaluator_calls"] == 1
        and vector["conclusion"] == "NO-GO"
        and vector["next_skill"] == "none"
        for vector in INVALID_RESULT_VECTORS
    )
    for phrase in (
        "unknown or extra reason",
        "missing reason",
        "duplicate reason",
        "out-of-order reason",
        "any result mismatch fails closed",
        "STOP_UNCERTAIN",
        "SPLIT_REQUIRED",
    ):
        assert phrase in contract
    assert "must not reinterpret a stopped or split result" in contract


def test_failure_categories_are_exact_and_never_production_reasons() -> None:
    contract = _normalized(_read(CONTRACT_PATH))
    expected = PRE_CALL_FAILURE_CATEGORIES + POST_CALL_FAILURE_CATEGORIES

    assert len(expected) == 9
    assert len(set(expected)) == 9
    assert all(category in contract for category in expected)
    assert "not production TaskSizeGate reason codes" in contract
    assert "must never enter `TaskSizeGateResult.reason_codes`" in contract


def test_checkpoint_failures_are_no_go_with_no_next_skill() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert "Any checkpoint failure prevents `PASS` and `PASS WITH FOLLOW-UP`" in contract
    assert "formal review conclusion is fixed to `NO-GO`" in contract
    assert "next Skill is `无`" in contract
    assert "no merge, release, replanning, revision, activation, or dangerous instruction" in contract


def test_passing_checkpoint_only_continues_independent_review() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert CALL_ACCOUNTING_VECTORS["valid_attempt"]["conclusion"] == (
        "CONTINUE_INDEPENDENT_REVIEW"
    )
    assert "passing checkpoint is only permission to continue the already requested read-only review" in contract
    assert "It is not a `PASS`, `PASS WITH FOLLOW-UP`, user approval" in contract
    assert "checkpoint itself must never manufacture either conclusion" in contract


def test_checkpoint_never_performs_automatic_actions_or_grants_authority() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert all(action in contract for action in NO_AUTOMATIC_ACTIONS)
    assert "Merge still requires a separate explicit user approval and `jl-merge`" in contract
    assert "grant Demo or Live trading permission" in contract


def test_governance_budget_returns_to_product_after_minimal_integration() -> None:
    contract = _normalized(_read(CONTRACT_PATH))

    assert "immutable review-checkpoint contract vectors" in contract
    assert "minimal `jl-review` Skill integration using the production evaluator" in contract
    assert "After that minimal checkpoint is accepted and merged, planning must return to the Demo MVP product critical path" in contract
    assert "must not expand into test tooling, one-click verification, CI, metrics, another workflow checkpoint" in contract


def test_vectors_do_not_import_or_call_runtime_integration() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert not any(module.startswith("app") for module in imported_modules)
    assert "evaluate_task_size_gate" not in _called_names(tree)
    assert "TaskSizeGateEvidence" not in _called_names(tree)
    assert "TaskSizeGateResult" not in _called_names(tree)


def test_jl_review_runtime_integration_is_still_absent() -> None:
    skill = _read(JL_REVIEW_SKILL_PATH)

    assert "evaluate_task_size_gate" not in skill
    assert "TaskSizeGateEvidence" not in skill
    assert "TaskSizeGateResult" not in skill
    assert "result = evaluate_task_size_gate(evidence=evidence)" not in skill


def test_contract_vectors_do_not_claim_implementation_or_activation() -> None:
    module_doc = ast.get_docstring(ast.parse(Path(__file__).read_text(encoding="utf-8")))
    contract = _normalized(_read(CONTRACT_PATH))

    assert module_doc is not None
    assert "do not prove" in module_doc
    assert "implemented, activated, or verified end to end" in module_doc
    assert "does not modify a Skill, add tests, implement the checkpoint" in contract
    assert "does not implement or claim runtime integration, activation, verification" in contract
