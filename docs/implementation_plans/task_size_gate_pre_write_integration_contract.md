# TaskSizeGate Pre-Write Checkpoint Integration Contract

## 1. Purpose

This document defines the shared pre-write checkpoint boundary for
`jl-develop` and `jl-supervisor`. The checkpoint revalidates one explicitly
approved, frozen work order immediately before branch creation or any file
write. It consumes current repository evidence and the existing production
TaskSizeGate without creating a second classifier.

This is a contract-only deliverable. It does not modify either Skill, invoke a
pre-write checkpoint at runtime, create a branch, write project files, or grant
authority to continue after a failed check.

## 2. Maturity and authority

| Layer | State after this contract |
| --- | --- |
| Policy | Pre-write revalidation is required by the repository workflow. |
| Contract | This document defines the shared boundary. |
| Tests | No dedicated pre-write integration contract vectors exist yet. |
| Implementation | The pure TaskSizeGate evaluator exists. No pre-write integration implementation exists. |
| Integration | Neither `jl-develop` nor `jl-supervisor` invokes TaskSizeGate at pre-write. |
| Activation | No pre-write workflow enforcement is active. |
| Verification | No end-to-end pre-write behavior has been verified. |

The narrow pre-write capability moves from `POLICY_ONLY` to `CONTRACT_ONLY`.
The broader W0 package remains governed by its existing weighted WBS state.
This document does not change WBS hours or progress.

The checkpoint is not user approval. A passing result does not authorize a
branch, file write, commit, push, merge, tag, deployment, activation, MT4
access, EA call, or trading action.

## 3. Ownership boundary

The caller is the currently and explicitly authorized owner of one frozen work
order:

- `jl-develop` for a user-approved development or revision order; or
- `jl-supervisor` for one bounded approved order, including an explicitly
  authorized Pro resume.

Both callers must implement the same evidence, evaluator, result-validation,
drift, and fail-closed rules. Neither caller may weaken the checkpoint or keep
a separate TaskSize, ModelGate, or Supervisor-eligibility classifier.

`jlgo` owns the planning checkpoint. `jl-review` owns the later review
checkpoint. This contract does not move either responsibility into pre-write.

## 4. Existing production interface is the only classifier

Future integration must import and use the existing public interface directly:

```python
from app.services.task_size_gate import (
    TaskSizeGateEvidence,
    TaskSizeGateResult,
    evaluate_task_size_gate,
)
```

The only permitted evaluation call is:

```python
result = evaluate_task_size_gate(evidence=evidence)
```

For one pre-write attempt, the caller must construct one fresh, frozen, exact
`TaskSizeGateEvidence` and call `evaluate_task_size_gate` exactly once. It must
not monkeypatch, retry, fall back to a local classifier, overwrite a result,
remove unknowns, reduce scope, or create an adapter around the evaluator.

The evaluator remains pure and must not read Git, files, environment variables,
network state, WBS documents, or persistent workflow state. Those facts remain
caller-owned.

## 5. Frozen planning input

Before pre-write begins, the caller must possess one complete work order that
the user explicitly approved. The following planning artifacts are immutable
inputs:

- one objective and one WBS scope;
- base branch and immutable base main commit;
- work branch and whether the order is new work or a revision/recovery;
- exact allowed and prohibited files and capabilities;
- maturity, engineering-hour, capability-layer, dependency, risk, and
  ModelGate evidence;
- required targeted, regression, full-suite, build-or-N/A, grep, diff, and
  scope checks;
- exact ordinary commit message and work-branch push destination;
- planning `TaskSizeGateResult` and sanitized reason codes;
- explicit user authority, including explicit Pro authority when required;
- stop conditions.

Missing, mutable, ambiguous, or reconstructed planning artifacts are
`STOP_UNCERTAIN`. The caller must not infer them from the desired result.

## 6. Git preconditions by mode

Git facts must be fetched and read again immediately before evaluation. A stale
planning snapshot is not pre-write evidence.

### 6.1 New work

All conditions are required:

- current branch is `main`;
- worktree and index are clean and conflict-free;
- local `main` and `origin/main` equal the frozen base commit;
- every visible work branch is classified by ancestry;
- no active unmerged work branch exists;
- the target work branch exists neither locally nor remotely;
- all frozen dependencies still exist at the required maturity;
- no tag, config, policy, contract, code, or test change invalidates the order.

The checkpoint itself must finish before branch creation.

### 6.2 Approved revision

All conditions are required:

- current branch is the one frozen revision branch;
- worktree and index are clean and conflict-free;
- local and remote work-branch heads equal the approved revision head;
- `main` and `origin/main` still equal the frozen base commit;
- base ancestry and the exact linear commit list are provable;
- cumulative diff remains inside the frozen allowed files;
- the reviewer-requested revision is one objective and does not add a new
  maturity transition, subsystem, capability layer, dependency, or policy
  effect.

An unapproved branch, local-only commit, remote-only commit, dirty revision, or
expanded review request is `STOP_UNCERTAIN`.

### 6.3 Supervisor recovery before another write

Recovery uses Git only; no progress JSON, state file, database, daemon, or
persistent runtime log may be introduced. Before any recovery write:

- exactly one relevant active branch is unambiguous;
- its base, head, remote head, ancestry, commits, and diff are provable;
- the worktree is clean;
- the branch remains inside the original frozen work order;
- the authorized revision-round limit has not been exhausted; and
- the next recovery action is already authorized by the bounded Supervisor
  state machine.

Failure to prove any item stops recovery without a fallback path.

## 7. Exact caller-owned evidence

The caller must populate all 29 fields below from the approved order and fresh
repository evidence. A field must never be copied blindly when its underlying
fact can change between planning and pre-write.

| Field | Pre-write source and revalidation rule |
| --- | --- |
| `objective` | Exact single outcome from the approved frozen order; unchanged. |
| `objective_count` | Recount independently deliverable outcomes; any increase is drift. |
| `wbs_package_ids` | Current WBS evidence for the approved scope; no added package. |
| `current_maturity` | Current narrow capability evidence from repository state. |
| `target_maturity` | Approved adjacent target, or approved maturity-preserving revision target. |
| `maturity_reason` | Exact transition or hardening/maintenance reason. |
| `base_branch` | Fresh Git evidence; new work requires `main`. |
| `base_main_commit` | Fresh equality of local and remote main to the frozen commit. |
| `work_branch` | Exact approved branch and mode-specific existence rule. |
| `commit_message` | Exact approved ordinary commit message. |
| `push_destination` | Exact `origin/<work_branch>` destination; never `main`. |
| `stop_conditions` | Frozen stop conditions plus no silently weakened condition. |
| `estimated_engineering_hours_lower` | Approved defensible lower estimate; never reduced to obtain allow. |
| `estimated_engineering_hours_upper` | Re-estimated upper bound including newly discovered work; any increase is drift. |
| `allowed_files` | Exact canonical relative files; newly required files are drift. |
| `prohibited_files` | Exact canonical relative files that remain forbidden. |
| `prohibited_capabilities` | Frozen merge, tag, deployment, activation, policy, and capability limits. |
| `capability_layers` | Ordered distinct layers actually touched; newly discovered layer is drift. |
| `subsystem_boundaries` | Exact approved repository ownership boundaries. |
| `affected_surfaces` | Fresh impact review of all touched workflow surfaces. |
| `required_checks` | Complete seven-category verification set with explicit N/A where valid. |
| `known_dependencies` | Fresh repository proof for every approved dependency. |
| `dependency_evidence_known` | Strict true only when all dependency evidence remains known. |
| `risk_and_policy_impacts` | Fresh safety and policy review; any new impact is drift. |
| `high_risk_reasons` | Current ModelGate reasons without omission or downgrading. |
| `model_gate` | Approved ModelGate rechecked against current AGENTS and task evidence. |
| `model_gate_evidence` | Concrete current evidence supporting the ModelGate value. |
| `unknowns` | Every unresolved fact; never delete one to obtain allow. |
| `cross_package_activation` | Strict true when the current scope crosses packages for activation. |

The fresh evidence object, the frozen planning artifacts, and the Git
checkpoint must remain unchanged before and after the single evaluator call.

## 8. Drift rules

Pre-write drift exists when current evidence differs materially from the
approved planning evidence, including:

- dirty state, main mismatch, unknown ancestry, changed or occupied branch;
- changed objective count or WBS packages;
- added, removed, aliased, wildcard, or noncanonical scope;
- higher engineering-hour upper bound;
- added capability layer, subsystem, affected surface, or dependency;
- missing check or newly required build/test work;
- changed maturity transition or revision reason;
- new risk, policy impact, ModelGate reason, unknown, or activation effect;
- changed commit message, push destination, or stop condition; or
- changed evaluator result, reason-code sequence, or caller eligibility.

The caller must not update the frozen order in place. Drift returns
workflow-level `STOP_UNCERTAIN`, names only a sanitized drift category, sets
the next Skill to `none`, and stops before branch creation or file writes. A new
planning decision and explicit user approval are required.

## 9. Result validation and planning equality

The returned value must be exact type `TaskSizeGateResult`. Its `task_size`,
`task_decision`, `model_gate`, `supervisor_eligibility`, and ordered
`reason_codes` must satisfy the production constants and the JLGO planning
integration contract.

Pre-write succeeds only when the entire result exactly equals the frozen
planning result and remains compatible with the explicitly approved caller:

- `STOP_UNCERTAIN` always stops with no next Skill;
- `SPLIT_REQUIRED` always stops and returns only a read-only decomposition
  requirement;
- `ALLOW_SINGLE_WORK_ORDER` may proceed only after all Git and drift checks;
- a Supervisor caller requires `ELIGIBLE`, or `CONDITIONAL_PRO_RESUME` plus
  explicit current Pro authorization for the same frozen order;
- `NOT_ELIGIBLE` must never enter the bounded Supervisor path; and
- `PRO_REQUIRED` must never be downgraded to `NORMAL_ALLOWED`.

Unknown enums, non-exact types, missing, extra, duplicated, or out-of-order
reason codes, impossible combinations, or any planning/pre-write result
difference are `STOP_UNCERTAIN`. There is no retry, alternate evaluator, or
manual result repair.

## 10. Fixed fail-closed behavior

The following categories stop before branch creation or any write:

```text
PRE_WRITE_GIT_INVALID
PRE_WRITE_BRANCH_STATE_INVALID
PRE_WRITE_FROZEN_ORDER_INVALID
PRE_WRITE_DEPENDENCY_INVALID
PRE_WRITE_SCOPE_DRIFT
PRE_WRITE_SIZE_OR_LAYER_DRIFT
PRE_WRITE_RISK_OR_POLICY_DRIFT
PRE_WRITE_MODEL_AUTHORITY_INVALID
PRE_WRITE_EVALUATOR_UNAVAILABLE
PRE_WRITE_EVALUATOR_RESULT_INVALID
PRE_WRITE_UNEXPECTED_FAILURE
```

These are workflow-level sanitized categories, not new TaskSizeGate production
reason constants. They must not be passed into or returned from
`TaskSizeGateResult`.

Failure output must not contain exception text, traceback, absolute paths,
environment values, credentials, raw user content, or other sensitive data.
Failure must not create, switch, reset, delete, or move a branch; write a file;
invoke another Skill; commit; push; merge; tag; deploy; or activate anything.

## 11. Passing checkpoint does not perform the write

The pre-write checkpoint returns only an internal proceed-or-stop decision for
the already approved work order. Even a valid allow result does not itself:

- supply new user approval;
- choose a different caller or work order;
- create or switch a branch;
- modify a file;
- invoke another Skill;
- commit or push;
- merge, tag, deploy, or activate; or
- access MT4, call an EA, create an order, or grant trading permission.

After a passing checkpoint, the already authorized caller may perform only the
next action inside the same frozen work order and its existing authority.

## 12. Safety and policy invariants

This workflow Gate is not DataQualityGate, RiskGate, PositionSizing,
ExecutionGate, or GoLiveGate. It does not evaluate market data, readiness,
orders, leverage, position size, or trading permission.

Demo-only, Read-only, user authority, no automatic ordering, and all approved
trading and risk policies remain unchanged. No writer, manifest, payload,
client, work order, Skill, or Gate result may override them.

## 13. Required staged delivery

This contract does not authorize later stages. They remain separate:

1. independent review and explicit fast-forward merge of this contract;
2. tests-only immutable pre-write contract vectors;
3. `jl-develop` pre-write integration and hardening;
4. `jl-supervisor` pre-write integration and hardening;
5. review-checkpoint contract, tests, and integration;
6. test-layer and one-click verification contract and tooling;
7. CI contract and implementation;
8. W0 evidence review and WBS re-estimation when supported by engineering-hour
   evidence.

No stage may combine, invoke, merge, release, deploy, or activate the next
stage automatically.

## 14. Acceptance checklist

Review must confirm:

- one shared contract governs both pre-write owners;
- new work, approved revision, and Supervisor recovery are deterministic;
- all 29 evidence fields have exact caller-owned revalidation rules;
- the production evaluator is the only classifier and is called once;
- frozen inputs and Git remain unchanged across evaluation;
- planning/pre-write drift always fails closed without updating the order;
- result equality, caller eligibility, and Pro authority are strict;
- sanitized failures do not leak sensitive data or perform writes;
- passing does not grant approval or perform a branch or file operation;
- later tests, Skill integration, review integration, tooling, and CI remain
  separate; and
- no MT4, EA, execution, deployment, activation, or trading capability is
  implemented or authorized.
