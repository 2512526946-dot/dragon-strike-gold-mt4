"""Static contract vectors for the TaskSizeGate pre-write checkpoint.

These vectors lock the WF-4G boundary and its jl-develop and jl-supervisor
Skill integrations.
They deliberately do not import or call the TaskSizeGate evaluator, so they
do not claim review, CI, activation, or end-to-end verification.
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
JL_DEVELOP_SKILL_PATH = REPOSITORY_ROOT / ".agents" / "skills" / "jl-develop" / "SKILL.md"
JL_SUPERVISOR_SKILL_PATH = (
    REPOSITORY_ROOT / ".agents" / "skills" / "jl-supervisor" / "SKILL.md"
)


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

NON_ACTIVATING_VERIFICATION_PRE_WRITE_VALUES = (
    'current_maturity="INTEGRATED"',
    'target_maturity="VERIFIED"',
    'maturity_reason="non-activating verification"',
    "objective_count=1",
    'capability_layers=("VERIFICATION",)',
    "cross_package_activation=False",
    'affected_surfaces=("offline_verification_evidence",)',
    'risk_and_policy_impacts=("verification_does_not_grant_activation","no_runtime_authority_change","no_trading_or_execution_authority")',
    'prohibited_capabilities=("merge","push_main","tag","deployment","activation","runtime_source_change","mt4_access","ea_call","order_execution","trading","second_work_order")',
)

NON_ACTIVATING_VERIFICATION_SCOPE_FAILURE_VECTORS = MappingProxyType(
    {
        case_id: MappingProxyType(
            {
                "expected_evaluator_calls": 0,
                "expected_outcome": "STOP_UNCERTAIN",
                "next_skill": "none",
                "writes_allowed": False,
            }
        )
        for case_id in (
            "allowed_file_not_offline_verification_evidence",
            "affected_subsystem_not_integrated",
            "production_code_surface_present",
            "runtime_authority_surface_present",
            "activation_surface_present",
            "mt4_or_ea_surface_present",
            "order_execution_or_trading_surface_present",
            "dependency_evidence_missing",
            "scope_evidence_ambiguous",
            "risk_or_policy_evidence_stale",
            "frozen_scope_drifted",
        )
    }
)

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


def _marked_fields(text: str) -> tuple[str, ...]:
    start = "TASK_SIZE_GATE_PRE_WRITE_EVIDENCE_FIELDS_BEGIN"
    end = "TASK_SIZE_GATE_PRE_WRITE_EVIDENCE_FIELDS_END"
    before, marker, remainder = text.partition(start)
    assert marker and before
    body, marker, after = remainder.partition(end)
    assert marker and after
    return tuple(line.strip() for line in body.splitlines() if line.strip())


def _marked_non_activating_values(text: str) -> tuple[str, ...]:
    start = "TASK_SIZE_GATE_NON_ACTIVATING_VERIFICATION_PRE_WRITE_VALUES_BEGIN"
    end = "TASK_SIZE_GATE_NON_ACTIVATING_VERIFICATION_PRE_WRITE_VALUES_END"
    before, marker, remainder = text.partition(start)
    assert marker and before
    body, marker, after = remainder.partition(end)
    assert marker and after
    return tuple(line.strip() for line in body.splitlines() if line.strip())


def _parse_assignments(lines: tuple[str, ...]) -> dict[str, object]:
    values: dict[str, object] = {}
    for line in lines:
        name, separator, value = line.partition("=")
        assert separator and name and name not in values
        values[name] = ast.literal_eval(value)
    return values


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


def test_jl_develop_integrates_the_exact_production_interface_and_29_fields() -> None:
    skill = _read(JL_DEVELOP_SKILL_PATH)

    assert _marked_fields(skill) == EVIDENCE_FIELDS
    assert "在 `backend` Python runtime 中直接复用" in skill
    assert "TaskSizeGateEvidence" in skill
    assert "TaskSizeGateResult" in skill
    assert skill.count("result = evaluate_task_size_gate(evidence=evidence)") == 1
    assert all(name in skill for name in (
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
    ))


def test_jl_develop_checks_new_and_revision_git_state_before_writes() -> None:
    skill = _normalized(_read(JL_DEVELOP_SKILL_PATH))

    assert "new work 必须在当前分支仍为 `main` 时完成 checkpoint" in skill
    assert "没有 active unmerged branch" in skill
    assert "目标 work branch 本地和远端均不存在" in skill
    assert "checkpoint 通过前不得创建或切换目标分支" in skill
    assert "approved revision 必须在当前分支已经是冻结 revision branch 时完成 checkpoint" in skill
    assert "本地与远端 work-branch head 等于批准 revision head" in skill
    assert "累计 diff 均可证明且未越界" in skill
    assert "未合并实现不得提升 frozen base-main `current_maturity`" in skill


def test_jl_develop_prewrite_call_order_is_zero_or_exactly_one_without_retry() -> None:
    skill = _normalized(_read(JL_DEVELOP_SKILL_PATH))

    assert "调用 evaluator 零次" in skill
    assert "只有全部 pre-evaluator checks 和 drift checks 通过后，才允许恰好一次" in skill
    assert "不得 monkeypatch、retry、fallback、调用第二次" in skill
    assert "evaluator unavailable、exception、invalid result、planning/result drift" in skill
    assert "pre-write contract 第 10 节的一个固定、净化后 `PRE_WRITE_*` 阻断类别" in skill
    assert "这些 workflow 类别不得放入 `TaskSizeGateResult.reason_codes`" in skill


def test_jl_develop_requires_exact_planning_result_and_preserves_authority() -> None:
    skill = _normalized(_read(JL_DEVELOP_SKILL_PATH))

    assert "与冻结 planning result 完全相等" in skill
    assert "frozen order、evidence 和 Git checkpoint 在 evaluator 调用前后必须保持相同" in skill
    assert "未知、缺失、重复、乱序、额外" in skill
    assert "`STOP_UNCERTAIN` 或 `SPLIT_REQUIRED` 不得进入写操作" in skill
    assert "`NOT_ELIGIBLE` 只禁止 Supervisor 自动 闭环，不禁止用户已经显式批准的 `jl-develop` 工单" in skill
    assert "checkpoint 通过只表示" in skill
    assert "当前已批准工单可以继续，不是新用户批准" in skill
    assert "不自动执行 branch、write、Skill、commit、push、merge、tag、部署或 activation" in skill
    assert "本节不执行 `jl-supervisor` 或 `jl-review`，也不实现 test tooling、CI" in skill


def test_jl_develop_prewrite_stop_routing_is_always_none() -> None:
    skill = _normalized(_read(JL_DEVELOP_SKILL_PATH))

    assert "工单不完整时停止；在 TaskSizeGate pre-write 上下文中，下一 Skill 固定为 `无`" in skill
    assert "TaskSizeGate pre-write 的 `STOP_UNCERTAIN`、任一前置失败、post-call 失败或 checkpoint 异常时，`下一 Skill` 必须写 `无`" in skill
    assert "不得建议或自动路由到 `$jlgo`" in skill
    assert "或在需要重新规划时写 `$jlgo`" not in skill


def test_jl_supervisor_integrates_the_exact_production_interface_and_29_fields() -> None:
    skill = _read(JL_SUPERVISOR_SKILL_PATH)

    assert _marked_fields(skill) == EVIDENCE_FIELDS
    assert "In the `backend` Python runtime" in skill
    assert "TaskSizeGateEvidence" in skill
    assert "TaskSizeGateResult" in skill
    assert skill.count("result = evaluate_task_size_gate(evidence=evidence)") == 1
    assert all(name in skill for name in (
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
    ))


def test_jl_supervisor_checks_new_revision_and_recovery_before_writes() -> None:
    skill = _normalized(_read(JL_SUPERVISOR_SKILL_PATH))

    assert "For new work, run the checkpoint while still on clean synchronized `main`" in skill
    assert "target branch must exist neither locally nor remotely" in skill
    assert "For an approved revision, run the checkpoint on the frozen work branch before the first revision write" in skill
    assert "cumulative scope must be exact" in skill
    assert "must not advance the frozen base-main `current_maturity`" in skill
    assert "For Git recovery, use current Git evidence and authentic frozen audit records" in skill
    assert "existing user authority and remaining revision limit" in skill
    assert "Do not create an autonomous state service, progress JSON scheduler" in skill
    assert "approved preserved state must be provable" in skill


def test_jl_supervisor_prewrite_call_order_is_zero_or_exactly_one() -> None:
    skill = _normalized(_read(JL_SUPERVISOR_SKILL_PATH))

    assert "uses zero evaluator calls" in skill
    assert "Only after every Git, frozen-order, dependency, evidence, Pro-authority, and pre-evaluator drift check passes may Supervisor call exactly once" in skill
    assert "Do not monkeypatch, retry, fallback, call a second time" in skill
    assert "If the evaluator interface is unavailable before invocation" in skill
    assert "`PRE_WRITE_EVALUATOR_UNAVAILABLE` with zero evaluator calls" in skill
    assert "Once the single evaluator call begins" in skill
    assert "consumes the one permitted call" in skill
    assert "without retry, fallback, result repair, or a second call" in skill
    assert "stops after the one permitted call" not in skill
    assert "These workflow categories must never enter `TaskSizeGateResult.reason_codes`" in skill


def test_jl_supervisor_requires_exact_result_and_current_pro_authority() -> None:
    skill = _normalized(_read(JL_SUPERVISOR_SKILL_PATH))

    assert "complete equality with the frozen planning result" in skill
    assert "ordered, unique public `reason_codes`" in skill
    assert "`STOP_UNCERTAIN`, `SPLIT_REQUIRED`, or `NOT_ELIGIBLE` always stops" in skill
    assert "`CONDITIONAL_PRO_RESUME` plus explicit current Codex Pro authorization" in skill
    assert "`PRO_REQUIRED` must never be downgraded" in skill
    assert "The frozen order, evidence, planning result, and Git checkpoint must remain unchanged" in skill


def test_jl_supervisor_prewrite_stop_routing_is_always_none() -> None:
    skill = _normalized(_read(JL_SUPERVISOR_SKILL_PATH))

    assert "the next Skill must be `无`" in skill
    assert "do not recommend or automatically route to `$jlgo` or any other Skill" in skill
    assert "The checkpoint itself does not create or switch a branch, write a file, invoke another Skill" in skill
    assert "This section does not implement the `jl-review` checkpoint, test tooling, CI" in skill


def test_vectors_are_immutable_and_do_not_call_the_runtime_evaluator() -> None:
    with pytest.raises(TypeError):
        PRE_WRITE_MODE_VECTORS["new_work"]["base_branch"] = "work/not-main"
    with pytest.raises(TypeError):
        PRE_EVALUATOR_FAILURE_VECTORS["dirty_worktree"] = "PROCEED"
    with pytest.raises(TypeError):
        NON_ACTIVATING_VERIFICATION_SCOPE_FAILURE_VECTORS[
            "scope_evidence_ambiguous"
        ]["expected_evaluator_calls"] = 1

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


def test_non_activating_verification_values_are_exact_for_both_prewrite_owners() -> None:
    for skill_path in (JL_DEVELOP_SKILL_PATH, JL_SUPERVISOR_SKILL_PATH):
        marked_values = _marked_non_activating_values(_read(skill_path))
        assert marked_values == NON_ACTIVATING_VERIFICATION_PRE_WRITE_VALUES

        assignments = _parse_assignments(marked_values)
        assert type(assignments["current_maturity"]) is str
        assert type(assignments["target_maturity"]) is str
        assert type(assignments["maturity_reason"]) is str
        assert type(assignments["objective_count"]) is int
        assert type(assignments["cross_package_activation"]) is bool
        for name in (
            "capability_layers",
            "affected_surfaces",
            "risk_and_policy_impacts",
            "prohibited_capabilities",
        ):
            assert type(assignments[name]) is tuple
            assert all(type(value) is str for value in assignments[name])


def test_non_activating_scope_failures_stop_before_evaluator_and_writes() -> None:
    assert set(NON_ACTIVATING_VERIFICATION_SCOPE_FAILURE_VECTORS) == {
        "allowed_file_not_offline_verification_evidence",
        "affected_subsystem_not_integrated",
        "production_code_surface_present",
        "runtime_authority_surface_present",
        "activation_surface_present",
        "mt4_or_ea_surface_present",
        "order_execution_or_trading_surface_present",
        "dependency_evidence_missing",
        "scope_evidence_ambiguous",
        "risk_or_policy_evidence_stale",
        "frozen_scope_drifted",
    }
    for vector in NON_ACTIVATING_VERIFICATION_SCOPE_FAILURE_VECTORS.values():
        assert vector == {
            "expected_evaluator_calls": 0,
            "expected_outcome": "STOP_UNCERTAIN",
            "next_skill": "none",
            "writes_allowed": False,
        }

    for skill_path in (JL_DEVELOP_SKILL_PATH, JL_SUPERVISOR_SKILL_PATH):
        skill = _normalized(_read(skill_path))
        assert "every allowed file contains offline verification evidence only" in skill
        assert "every affected subsystem already has reviewed `INTEGRATED` evidence" in skill
        assert "no production code, runtime-authority code, deployment, activation, MT4, EA, order, execution, or trading surface" in skill
        assert "stops before evidence construction" in skill
        assert "uses zero evaluator calls" in skill
        assert "workflow-level `STOP_UNCERTAIN`" in skill
        assert "sets the next Skill to `无`" in skill


def test_non_activating_prewrite_uses_one_existing_call_without_new_authority() -> None:
    develop = _normalized(_read(JL_DEVELOP_SKILL_PATH))
    supervisor = _normalized(_read(JL_SUPERVISOR_SKILL_PATH))

    assert develop.count("result = evaluate_task_size_gate(evidence=evidence)") == 1
    assert supervisor.count("result = evaluate_task_size_gate(evidence=evidence)") == 1
    assert "this adds no thirtieth field" in develop
    assert "this adds no thirtieth field" in supervisor
    assert "does not complete verification, grant new authority, activate anything, or authorize G174" in develop
    assert "does not complete verification, grant new authority, activate anything, or authorize G174" in supervisor
    assert "Review propagation remains a separately approved stage" in develop
    assert "Review propagation remains a separately approved stage" in supervisor

RECOVERY_ORACLE = (
    ("clean_initial_or_revision", "one_fresh_attempt", "approved_first_write_after_acceptance"),
    ("approved_preserved_state_new_revision", "one_fresh_attempt", "approved_revision_after_acceptance"),
    ("accepted_prewrite_expected_dirty", "no_recall", "authorized_checks_or_commit"),
    ("accepted_checks_local_commit", "no_recall", "authorized_work_branch_push"),
    ("published_exact_head", "review_separate_attempt", "independent_read_only_review"),
    ("unknown_or_changed_state", "no_call", "stop_read_only_diagnosis"),
)


def _recovery_rows(contract: str) -> tuple[tuple[str, ...], ...]:
    start = "<!-- WORKFLOW_RECOVERY_BEGIN -->"
    end = "<!-- WORKFLOW_RECOVERY_END -->"
    assert contract.count(start) == contract.count(end) == 1
    lines = tuple(
        line.strip()
        for line in contract.split(start, 1)[1].split(end, 1)[0].splitlines()
        if line.strip()
    )
    assert all(line.startswith("|") and line.endswith("|") for line in lines)
    return tuple(tuple(cell.strip() for cell in line.split("|")[1:-1]) for line in lines[2:])


def test_phase_specific_recovery_does_not_recall_accepted_prewrite() -> None:
    assert _recovery_rows(_read(CONTRACT_PATH)) == RECOVERY_ORACLE
    assert RECOVERY_ORACLE[2][1] == RECOVERY_ORACLE[3][1] == "no_recall"
    assert RECOVERY_ORACLE[-1][1:] == ("no_call", "stop_read_only_diagnosis")


@pytest.mark.parametrize("row", RECOVERY_ORACLE)
def test_recovery_mutations_cannot_reauthorize_writes_or_reset_calls(row: tuple[str, ...]) -> None:
    contract = _read(CONTRACT_PATH)
    original = "| " + " | ".join(row) + " |"
    mutants = (
        contract.replace(original, "", 1),
        contract.replace(original, original + "\n" + original, 1),
        contract.replace(original, "| " + " | ".join((row[0], "one_fresh_attempt", "unconditional_write")) + " |", 1),
    )
    for mutant in mutants:
        with pytest.raises(AssertionError):
            assert _recovery_rows(mutant) == RECOVERY_ORACLE


def test_recovery_requires_content_and_phase_proof_not_just_file_names() -> None:
    contract = _normalized(_read(CONTRACT_PATH))
    for rule in (
        "exact local-only commits or dirty-file content and staged/unstaged state",
        "path-only approval is insufficient",
        "Remote-only or unexplained changes stop",
        "preservation-only commits which never prove acceptance",
        "recovery cannot renew the allowance",
        "source, dependency/config and check-set digests",
        "Never replay planning/pre-write solely because",
        "not a false completion or reused report for different content",
        "including staged, unstaged and untracked files",
        "adopted historical paths are not permission to edit them again",
        "do not union historical paths into its 29 fields",
        "A broader historical manifest cannot hide a current delta",
    ):
        assert rule in contract
    for skill_path in (JL_DEVELOP_SKILL_PATH, JL_SUPERVISOR_SKILL_PATH):
        skill = _read(skill_path)
        assert "task_size_gate_jlgo_planning_integration_contract.md" in skill
        assert "invocation ledger" in skill
        assert "6.3-6.4" in skill


# Exact synthetic worktree/index entries; no files, Git or checkpoint are used.
# Entry fields: worktree kind/content, index kind/content, tracked flag.
HEAD_ENTRIES = MappingProxyType({
    "A": ("file", b"a0", "file", b"a0", True),
    "B": ("file", b"b0", "file", b"b0", True),
})
PRESERVED_B_ENTRIES = (
    ("unstaged", ("file", b"b1", "file", b"b0", True)),
    ("staged", ("file", b"b1", "file", b"b1", True)),
    ("untracked", ("file", b"b1", None, None, False)),
    ("deleted", (None, None, "file", b"b0", True)),
    ("kind", ("symlink", b"literal-target", "file", b"b0", True)),
)
WRITE_SCOPE = frozenset({"A"})


def _snapshot_delta(before: MappingProxyType, after: MappingProxyType) -> frozenset[str]:
    return frozenset(
        path for path in before.keys() | after.keys()
        if before.get(path) != after.get(path)
    )


def _assert_preserved_scope(
    approved: MappingProxyType,
    baseline: MappingProxyType,
    current: MappingProxyType,
) -> None:
    assert type(approved) is type(baseline) is type(current) is MappingProxyType
    assert baseline == approved
    assert _snapshot_delta(baseline, current) <= WRITE_SCOPE


def test_scope_contract_keeps_git_inventory_and_content_baseline_separate() -> None:
    contract = _normalized(_read(CONTRACT_PATH))
    for rule in (
        "full pre-Head-to-current-state Git inventory",
        "never filter preserved paths out of the cumulative audit",
        "exact user-adopted content snapshot, NOT pre-Head alone",
        "existence, file kind, exact worktree content/digest, exact index entry/content and tracked/untracked state",
        "Missing, stale or substituted baseline proof stops",
        "untouched preserved file outside current write scope is not a new modification",
        "byte-for-byte and index-state identical",
        "Preservation approval is not permission to stage or commit preserved content",
        "Formal review still requires a clean, synchronized reviewed Head",
        "original in-scope revision authority covers its fresh pre-write attempt",
        "not a retry of a failed or uncertain checkpoint",
    ):
        assert rule in contract


@pytest.mark.parametrize("case,entry", PRESERVED_B_ENTRIES)
def test_untouched_preserved_content_is_not_a_new_write(case: str, entry: tuple) -> None:
    approved = MappingProxyType({
        "A": ("file", b"a1", "file", b"a0", True),
        "B": entry,
    })
    current = MappingProxyType({**approved, "A": ("file", b"a2", "file", b"a0", True)})
    _assert_preserved_scope(approved, approved, current)
    assert _snapshot_delta(approved, current) == frozenset({"A"})
    assert current["B"] == approved["B"] == entry
    assert _snapshot_delta(HEAD_ENTRIES, current) == frozenset({"A", "B"})
    # The old pre-Head baseline would reject untouched B in every saved state.
    with pytest.raises(AssertionError):
        assert _snapshot_delta(HEAD_ENTRIES, current) <= WRITE_SCOPE
    assert tuple(approved) == ("A", "B") and type(entry) is tuple
    with pytest.raises(TypeError):
        approved["B"] = HEAD_ENTRIES["B"]  # type: ignore[index]


@pytest.mark.parametrize("mutation", (
    "content", "restore_head_content", "index", "kind", "tracked",
    "delete", "rename", "new_untracked",
))
def test_changes_to_preserved_or_new_paths_fail_closed(mutation: str) -> None:
    approved = MappingProxyType({
        "A": ("file", b"a1", "file", b"a0", True),
        "B": ("file", b"b1", "file", b"b0", True),
    })
    entries = {**approved, "A": ("file", b"a2", "file", b"a0", True)}
    replacements = {
        "content": ("file", b"b2", "file", b"b0", True),
        "restore_head_content": HEAD_ENTRIES["B"],
        "index": ("file", b"b1", "file", b"b1", True),
        "kind": ("symlink", b"b1", "file", b"b0", True),
        "tracked": ("file", b"b1", "file", b"b0", False),
    }
    if mutation in replacements:
        entries["B"] = replacements[mutation]
    elif mutation == "delete":
        del entries["B"]
    elif mutation == "rename":
        entries["C"] = entries.pop("B")
    else:
        entries["C"] = ("file", b"generated", None, None, False)
    with pytest.raises(AssertionError):
        _assert_preserved_scope(approved, approved, MappingProxyType(entries))


def test_preserved_baseline_cannot_be_replaced_by_head_or_recaptured_content() -> None:
    approved = MappingProxyType({
        "A": ("file", b"a1", "file", b"a0", True),
        "B": ("file", b"b1", "file", b"b0", True),
    })
    polluted = MappingProxyType({**approved, "B": ("file", b"b2", "file", b"b0", True)})
    for substitute in (HEAD_ENTRIES, polluted, MappingProxyType({"A": approved["A"]})):
        with pytest.raises(AssertionError):
            _assert_preserved_scope(approved, substitute, polluted)


def test_preservation_does_not_authorize_commit_inclusion_or_hide_history() -> None:
    approved = MappingProxyType({
        "A": ("file", b"a1", "file", b"a0", True),
        "B": ("file", b"b1", "file", b"b1", True),
    })
    staged = MappingProxyType({**approved, "A": ("file", b"a2", "file", b"a2", True)})
    _assert_preserved_scope(approved, approved, staged)
    staged_paths = frozenset(
        path for path in staged
        if staged[path][2:4] != HEAD_ENTRIES[path][2:4]
    )
    assert staged_paths == frozenset({"A", "B"})
    with pytest.raises(AssertionError):
        assert staged_paths <= WRITE_SCOPE
    assert staged_paths <= frozenset({"A", "B"})  # Only a separate inclusion approval.

    base = MappingProxyType({**HEAD_ENTRIES, "C": ("file", b"c0", "file", b"c0", True)})
    pre_head = MappingProxyType({**base, "C": ("file", b"c1", "file", b"c1", True)})
    after = MappingProxyType({**pre_head, "A": ("file", b"a2", "file", b"a2", True)})
    assert _snapshot_delta(pre_head, after) == WRITE_SCOPE
    cumulative = _snapshot_delta(base, after)
    assert cumulative == frozenset({"A", "C"})
    with pytest.raises(AssertionError):
        assert cumulative <= WRITE_SCOPE
    assert cumulative <= frozenset({"A", "C"})
