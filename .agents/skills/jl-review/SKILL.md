---
name: jl-review
description: Perform a strict read-only review of a 巨龙出击 branch or commit against main. Use after a development or revision branch is pushed. Inspect actual code, tests, Git scope, and safety boundaries. Never modify files, commit, merge, push, or tag.
---

# 巨龙验收

1. 先读取仓库根目录 `AGENTS.md`。
2. 在选择任何 review conclusion 前，执行下方 TaskSizeGate review checkpoint；没有完整冻结 review packet 时固定 `NO-GO`。
3. 只读审查当前 branch 或用户指定 commit 相对 `main` 的状态。
4. `/review` 可用时优先使用 Review against a base branch，并在当前任务运行，不使用 Detached review。
5. 检查实际 diff、生产代码、测试证明范围、修改范围、Git ancestry、安全语义、输出泄露、能力陈述和 ff-only 条件。
6. 必要时运行测试，但不得修改任何文件。
7. 只允许以下结论：`PASS`、`PASS WITH FOLLOW-UP`、`FIX BEFORE MERGE`、`NO-GO`。
8. 结论为 `FIX BEFORE MERGE` 时，列出精确 findings，生成最小修订工单，明确继续原分支，并将下一 Skill 指向 `$jl-develop`。
9. 结论为 `PASS` 或明确可合并的 `PASS WITH FOLLOW-UP` 时，给出 main、branch HEAD、修改范围和测试基线，生成 merge 工单，并将下一 Skill 指向 `$jl-merge`。
10. 不修改工作树，不 commit、push、merge 或 tag。输出结论后停止。

## TaskSizeGate review checkpoint

This is the runtime procedure for the read-only checkpoint specified by
`docs/implementation_plans/task_size_gate_jl_review_checkpoint_integration_contract.md`.
It reuses the production evaluator; it does not create a review-local classifier,
adapter, threshold, reason code, or evidence field.

The review caller must freeze a review packet before any evaluator call: exact
base `main` and base commit, exact work branch and head, local and remote branch
heads, ordered ordinary commit subjects with their authority sources, immutable
work order, frozen planning result, latest accepted pre-write result, exact
cumulative diff, required check evidence, and explicit review-only authority.
The original work-order `commit_message` remains the evidence value for the
whole review; ordered later commit subjects are separately proven against their
manual-revision or Supervisor automatic-revision authority. Missing, extra,
reordered, duplicated, or unprovable commit evidence is a pre-call failure.

Use the existing backend Python runtime interface only:

```python
from app.services.task_size_gate import (
    ALLOW_SINGLE_WORK_ORDER,
    CONDITIONAL_PRO_RESUME,
    ELIGIBLE,
    INPUT_INVALID,
    MODEL_STOP_UNCERTAIN,
    NORMAL_ALLOWED,
    NOT_ELIGIBLE,
    PRO_MODEL_REQUIRED,
    PRO_REQUIRED,
    SINGLE_WORK_ORDER_ALLOWED,
    SIZE_UNCLASSIFIABLE,
    STOP_UNCERTAIN,
    TaskSizeGateEvidence,
    TaskSizeGateResult,
    UNKNOWN_EVIDENCE,
    evaluate_task_size_gate,
)
```

Before constructing evidence, independently prove that the worktree and index
are clean and conflict-free; local `main` and `origin/main` equal the frozen
base; local and remote work heads equal the frozen head; base is an ancestor;
the commits are exactly the frozen linear ordinary list; the cumulative diff is
within exact canonical allowed scope; prohibited files and capabilities are
absent; dependencies, checks, ModelGate, risks, policies, and all Git facts are
still provable. The checkpoint never checks out, switches, creates, moves,
resets, cleans, stashes, rebases, commits, pushes, merges, tags, or deletes.

Construct the following fresh, frozen, exact `TaskSizeGateEvidence` fields in
this order from caller-owned frozen artifacts and the independently rechecked
repository facts. Do not infer, omit, add, narrow, repair, or rewrite evidence:

```text
TASK_SIZE_GATE_REVIEW_EVIDENCE_FIELDS_BEGIN
objective
objective_count
wbs_package_ids
current_maturity
target_maturity
maturity_reason
base_branch
base_main_commit
work_branch
commit_message
push_destination
stop_conditions
estimated_engineering_hours_lower
estimated_engineering_hours_upper
allowed_files
prohibited_files
prohibited_capabilities
capability_layers
subsystem_boundaries
affected_surfaces
required_checks
known_dependencies
dependency_evidence_known
risk_and_policy_impacts
high_risk_reasons
model_gate
model_gate_evidence
unknowns
cross_package_activation
TASK_SIZE_GATE_REVIEW_EVIDENCE_FIELDS_END
```

### Non-activating verification scope proof

For a frozen `INTEGRATED -> VERIFIED` non-activating verification order, before
constructing evidence prove from actual Git, frozen scope, dependencies, risk,
and policy facts that every allowed file is offline verification evidence only,
every affected subsystem has reviewed `INTEGRATED` evidence at frozen base
`main`, and no production code, runtime authority, deployment, activation,
MT4, EA, order, execution, or trading surface is present. A path name, desired
result, developer report, or absence of an activation file is not proof.

The exact built-in values and ordering are mandatory; this adds no thirtieth
evidence field:

```text
TASK_SIZE_GATE_NON_ACTIVATING_VERIFICATION_REVIEW_VALUES_BEGIN
current_maturity="INTEGRATED"
target_maturity="VERIFIED"
maturity_reason="non-activating verification"
objective_count=1
capability_layers=("VERIFICATION",)
cross_package_activation=False
affected_surfaces=("offline_verification_evidence",)
risk_and_policy_impacts=("verification_does_not_grant_activation","no_runtime_authority_change","no_trading_or_execution_authority")
prohibited_capabilities=("merge","push_main","tag","deployment","activation","runtime_source_change","mt4_access","ea_call","order_execution","trading","second_work_order")
TASK_SIZE_GATE_NON_ACTIVATING_VERIFICATION_REVIEW_VALUES_END
```

Missing, ambiguous, stale, contradictory, or drifted proof is a pre-call
failure. It makes zero evaluator calls, has no automatic action, fixes the
conclusion to `NO-GO`, and sets the next Skill to `无`. A passing classification
does not complete verification, grant activation, or authorize G174.

### Single call, exact result, and routing

Any Git, frozen-order, commit-authority, dependency, scope, size-or-layer,
risk-or-policy, evaluator-availability, or evidence-construction failure stops
before invocation. Report only the appropriate sanitized workflow category:

```text
REVIEW_CHECKPOINT_GIT_INVALID
REVIEW_CHECKPOINT_FROZEN_ORDER_INVALID
REVIEW_CHECKPOINT_DEPENDENCY_INVALID
REVIEW_CHECKPOINT_SCOPE_DRIFT
REVIEW_CHECKPOINT_SIZE_OR_LAYER_DRIFT
REVIEW_CHECKPOINT_RISK_OR_POLICY_DRIFT
REVIEW_CHECKPOINT_EVALUATOR_UNAVAILABLE
```

After all preconditions and pre-call drift checks pass, call exactly once:

```python
result = evaluate_task_size_gate(evidence=evidence)
```

Require `type(result) is TaskSizeGateResult`, exact built-in field types,
ordered unique public reason codes, and whole-result equality with both frozen
planning and latest accepted pre-write results. An allowed NORMAL result is
exactly `(SINGLE_WORK_ORDER_ALLOWED,)`; an allowed PRO result is exactly
`(SINGLE_WORK_ORDER_ALLOWED, PRO_MODEL_REQUIRED)`, with
`PRO_MODEL_REQUIRED` last. `M` with `NOT_ELIGIBLE` is valid for an explicitly
approved manual `jl-develop` work order but is not Supervisor-eligible.

After the call, recheck the frozen packet, Git state, commit list, diff, and
evidence. An exception, invalid or contradictory result, reason-code failure,
planning/pre-write/review mismatch, or post-call drift consumes the one call;
report only `REVIEW_CHECKPOINT_EVALUATOR_RESULT_INVALID` or
`REVIEW_CHECKPOINT_UNEXPECTED_FAILURE`. Do not retry, fallback, invoke a local
classifier, call a second time, mutate evidence, repair the result, or change
the frozen work order.

Every checkpoint failure prevents `PASS` and `PASS WITH FOLLOW-UP`, fixes the
formal conclusion to `NO-GO`, and fixes the next Skill to `无`. Workflow
categories never enter `TaskSizeGateResult.reason_codes`; do not disclose
exceptions, tracebacks, credentials, environment values, absolute paths, or
raw user content.

A passing checkpoint only permits continuation of the already requested
independent read-only review. It is not a `PASS`, `PASS WITH FOLLOW-UP`, user
approval, merge authority, next-Skill invocation, deployment, activation, or
G174 authorization. Only the subsequent independent correctness, security,
regression, and test-quality review may choose one of the existing conclusions.

## 下一步操作卡

验收结论之后必须追加 `【下一步操作卡】`：

```text
【下一步操作卡】
1. 当前状态：
2. 下一步要做什么：
3. 是否需要用户显式批准：
4. 模型要求：
5. 下一 Skill：
6. 可直接复制发送给 Codex 的完整指令：
```

状态映射：

- `PASS`：`下一 Skill` 写 `$jl-merge`，完整指令必须要求用户显式批准 fast-forward 合并。
- `PASS WITH FOLLOW-UP`：若结论明确可合并，`下一 Skill` 写 `$jl-merge`；若 follow-up 阻断合并，`下一 Skill` 写 `$jl-develop`。
- `FIX BEFORE MERGE`：`下一 Skill` 写 `$jl-develop`，完整指令必须要求继续原分支做最小修订，不得 merge。
- TaskSizeGate checkpoint failure 的 `NO-GO`：`下一 Skill` 必须写 `无`；不得建议或自动路由到 `$jlgo`。
- 其他 `NO-GO`：`下一 Skill` 写 `无`，或仅在需要重新规划时写 `$jlgo`；不得生成合并、发布或危险开发指令。
- 完整指令必须只调用一个 Skill，并要求下一轮结束时继续输出新的【下一步操作卡】。
- 不得通过操作卡自动 merge、tag、删除分支或进入下一工单。
