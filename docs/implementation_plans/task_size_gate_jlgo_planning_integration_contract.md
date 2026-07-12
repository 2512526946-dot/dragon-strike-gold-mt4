# TaskSizeGate JLGO Planning-Checkpoint Integration Contract

## 1. Purpose and capability state

This contract defines the future integration boundary between the repository
`jlgo` planning Skill and the production TaskSizeGate evaluator. It narrows the
planning checkpoint described by the existing TaskSizeGate contract. It does
not integrate or activate the evaluator in this work order.

The capability states remain separate:

| Layer | State after this contract |
| --- | --- |
| Policy | The planning checkpoint is required by the repository workflow. |
| Contract | This document defines the exact JLGO boundary. |
| Tests | No JLGO integration contract vectors exist yet. |
| Implementation | The pure in-memory evaluator already exists. |
| Integration | No Skill invokes the production evaluator. |
| Activation | No TaskSizeGate workflow enforcement is active. |
| Verification | No end-to-end Skill invocation has been verified. |

The broad W0 work package may remain `IMPLEMENTED` while this narrower
planning-integration capability moves from `POLICY_ONLY` to `CONTRACT_ONLY`.
Neither statement means TaskSizeGate is integrated or activated.

## 2. Scope

The future integration covered here has one responsibility:

1. `jlgo` gathers repository evidence without changing repository state.
2. `jlgo` constructs one strict `TaskSizeGateEvidence` value.
3. `jlgo` calls the production evaluator exactly once.
4. `jlgo` validates and maps the returned `TaskSizeGateResult`.
5. `jlgo` emits one planning recommendation and waits for explicit user
   approval.

This boundary applies only to the planning checkpoint. It does not cover:

- the pre-write checkpoint owned by `jl-develop` or `jl-supervisor`;
- the review checkpoint owned by `jl-review`;
- merge or release checks;
- a command-line adapter, API, CI job, daemon, or persistent state file;
- reader, MT4, EA, Demo execution, Live execution, or trading activation.

## 3. Single production owner

Future JLGO integration must reuse these public objects from
`backend/app/services/task_size_gate.py`:

```python
TaskSizeGateEvidence
TaskSizeGateResult
evaluate_task_size_gate(*, evidence: object) -> TaskSizeGateResult
```

The integration must not copy TaskSize thresholds, maturity rules, ModelGate
precedence, reason-code logic, Supervisor eligibility, or fail-closed behavior
into `jlgo`. The production evaluator remains the single classification owner.

`jlgo` owns evidence collection. The evaluator does not read Git, the WBS,
files, environment variables, network state, user-interface state, or prior
conversation summaries.

## 4. Planning preconditions

Before constructing evidence, future `jlgo` integration must prove:

- the repository root is known;
- the current branch, `main`, and `origin/main` are readable;
- the worktree status is readable;
- visible work branches can be classified by ancestry;
- the applicable WBS evidence and capability state are readable;
- the proposed objective, exact files, checks, branch, commit message, push
  destination, boundaries, dependencies, and stop conditions are frozen.

A dirty worktree, unsynchronized main, active unmerged work, unresolved
ancestry, occupied target branch, missing dependency, unknown scope, or
unreadable evidence prevents an allowed planning result. The integration must
stop before branch creation or file writes.

Retained historical branches whose tips are already ancestors of `main` are
not active work and must not create a false stop.

## 5. Evidence ownership and field mapping

All fields are caller-owned. `jlgo` must build a fresh frozen
`TaskSizeGateEvidence`; it must not mutate caller input or infer missing values
from an evaluator result.

| Evidence field | Required JLGO source and rule |
| --- | --- |
| `objective` | One testable outcome from the frozen candidate order. |
| `objective_count` | Count independently deliverable objectives; never force it to one to obtain an allow result. |
| `wbs_package_ids` | Exact current WBS package identifiers supported by repository evidence. |
| `current_maturity` | Current narrow capability maturity proven from policy, contract, tests, implementation, integration, activation, and verification evidence. |
| `target_maturity` | One adjacent forward maturity, or the same maturity for an explicit hardening/maintenance revision. |
| `maturity_reason` | Concrete transition or maturity-preserving reason; not a generic label. |
| `base_branch` | The verified base branch; normal new work uses `main`. |
| `base_main_commit` | Full immutable commit from verified local and remote main. |
| `work_branch` | One unoccupied canonical `work/...` branch. |
| `commit_message` | Exact ordinary commit message for this work order. |
| `push_destination` | Exact `origin/<work_branch>` destination; never `main`. |
| `stop_conditions` | Frozen conditions that end the order without scope expansion. |
| `estimated_engineering_hours_lower` | Defensible lower equivalent-engineer-hour estimate. |
| `estimated_engineering_hours_upper` | Defensible upper estimate including development, tests, review-fix allowance, and required documentation. |
| `allowed_files` | Exact canonical relative file paths; no wildcard or directory placeholder. |
| `prohibited_files` | Exact canonical relative file paths that must not change. |
| `prohibited_capabilities` | Explicit forbidden behavior, including merge, tag, deployment, and activation when applicable. |
| `capability_layers` | Ordered distinct layers actually touched by this order. |
| `subsystem_boundaries` | Exact repository subsystems whose ownership boundary is affected. |
| `affected_surfaces` | Public interfaces, schemas, protocols, settings, filesystem, external systems, or workflow surfaces affected. |
| `required_checks` | Exact targeted, regression, full-suite, build or explicit N/A, grep, diff, and scope checks. |
| `known_dependencies` | Dependencies whose repository evidence was inspected. |
| `dependency_evidence_known` | Strict boolean; false when any dependency evidence is unavailable. |
| `risk_and_policy_impacts` | Explicit safety, authority, data, workflow, and trading-policy impacts. |
| `high_risk_reasons` | Exact reasons that require Pro; empty only when evidence proves no high-risk category applies. |
| `model_gate` | Caller classification using only `NORMAL_ALLOWED`, `PRO_REQUIRED`, or `STOP_UNCERTAIN`. |
| `model_gate_evidence` | Repository and policy evidence supporting the caller classification. |
| `unknowns` | Every unresolved fact that could change size, scope, checks, dependencies, risk, or authority. |
| `cross_package_activation` | Strict boolean; true only for an order that crosses packages while activating a capability. |

User wording may propose values, but it is not sufficient Git, WBS, maturity,
dependency, or safety evidence. `jlgo` must verify those values independently.

## 6. WBS and maturity rules

The WBS supplies planning evidence; TaskSizeGate does not rewrite it.

- `jlgo` must distinguish package maturity from the narrower sub-capability
  maturity used by the proposed order.
- A contract, test, implementation, integration, activation, and verification
  claim requires evidence at that exact layer.
- Static tests do not prove production implementation.
- A production evaluator does not prove Skill integration.
- Skill integration does not prove activation or end-to-end verification.
- A completed engineering capability never grants trading authority.

After an accepted merge, WBS hours may be reconsidered only through the WBS
update protocol. TaskSizeGate output alone must not change invested hours,
remaining hours, Demo progress, Live progress, or Live activation readiness.

## 7. Invocation boundary

Future integration must follow this deterministic sequence:

1. Complete read-only Git and repository preflight.
2. Freeze one candidate work order.
3. Construct one fresh strict `TaskSizeGateEvidence` object.
4. Call `evaluate_task_size_gate(evidence=evidence)` exactly once.
5. Require the returned value to be an exact `TaskSizeGateResult` with only
   valid TaskSize, Task decision, ModelGate, Supervisor eligibility, and
   reason-code combinations.
6. Map the result using Section 8.
7. Emit the planning output and stop for explicit user approval.

The future integration must not monkeypatch the evaluator, retry with weakened
evidence, remove unknowns, lower estimates, omit files, downgrade layers, or
rewrite a blocked result.

## 8. Deterministic result mapping

The evaluator result controls planning disposition but never user authority.

| Evaluator result | JLGO planning behavior |
| --- | --- |
| `STOP_UNCERTAIN` in Task decision or ModelGate | Report the sanitized blocking category, set the next Skill to `none`, and stop. |
| `SPLIT_REQUIRED` | Return to read-only decomposition, set the next Skill to `none`, and do not create parallel branches. |
| `ALLOW_SINGLE_WORK_ORDER` + `NORMAL_ALLOWED` + `ELIGIBLE` | JLGO may recommend explicit `jl-supervisor` invocation when all Supervisor preconditions remain true. |
| `ALLOW_SINGLE_WORK_ORDER` + `NORMAL_ALLOWED` + `NOT_ELIGIBLE` | Recommend explicit `jl-develop`; do not use Supervisor. |
| `ALLOW_SINGLE_WORK_ORDER` + `PRO_REQUIRED` + `CONDITIONAL_PRO_RESUME` | Freeze the order, require the user to state that Codex Pro is active and explicitly authorize the bounded Supervisor resume. |
| `ALLOW_SINGLE_WORK_ORDER` + `PRO_REQUIRED` + `NOT_ELIGIBLE` | Require Codex Pro and explicit `jl-develop` authorization. |
| Any unknown or contradictory combination | Treat as integration failure, emit `STOP_UNCERTAIN`, set the next Skill to `none`, and stop. |

`none` above is rendered as `无` in the repository next-action card.

An allowed result is not permission to create a branch, edit a file, invoke a
Skill, merge, tag, deploy, activate MT4, place an order, or trade. Every write
operation still requires explicit user approval under the repository workflow.

## 9. Fail-closed semantics

The planning integration must emit workflow-level `STOP_UNCERTAIN` and no next
Skill when any of the following occurs:

- the production module or public interface is unavailable;
- strict evidence construction fails;
- any required evidence is missing, unreadable, stale, or contradictory;
- the evaluator raises an unexpected exception;
- the result is not an exact `TaskSizeGateResult`;
- a result field has an unknown value or invalid type;
- result fields form a combination not allowed by Section 8;
- reason codes are unknown, inconsistent, duplicated, or malformed;
- repository state changes between evidence collection and planning output;
- exact scope, checks, dependencies, risk, or ModelGate cannot be frozen.

Failure output must be deterministic and sanitized. It must not include an
exception message, traceback, local absolute path, token, environment value,
raw user payload, or other sensitive repository content. It must not fabricate
a TaskSize, evaluator reason code, or successful Supervisor eligibility.

There is no fallback to manual TaskSize classification inside `jlgo`. A user
may later request new read-only planning after the failure is understood, but
the failed invocation itself remains blocked.

## 10. Input immutability and evidence freshness

- The frozen candidate order and collected source evidence must remain
  unchanged by evaluation.
- The integration constructs a fresh evidence object rather than mutating a
  prompt object, fixture, WBS record, or Git result.
- The evaluator result must not be modified to make a task eligible.
- Before any later write-capable Skill acts, its own checkpoint must recheck
  Git state and frozen scope. A prior JLGO result is not permanently fresh.

## 11. Output requirements

Future JLGO planning output must continue to distinguish:

- policy;
- contract;
- tests;
- production implementation;
- integration;
- activation;
- verification.

It must state the evaluator's TaskSize, Task decision, ModelGate, Supervisor
eligibility, and sanitized reason codes. It must also state that explicit user
approval is still required and provide exactly one next action.

It must not claim that TaskSizeGate is integrated merely because this contract
or future contract tests exist.

## 12. Security and authority boundaries

This contract does not change approved trading or risk policy. Future planning
integration must preserve:

- Demo-only and Read-only defaults;
- no automatic order placement;
- no EA or MQL4 execution;
- no reader or real MT4 activation;
- no Demo or Live execution activation;
- no interpretation of readiness or a Gate result as trading permission;
- no merge, tag, deployment, or second work order without separate approval.

TaskSizeGate is a repository workflow classifier. It is not DataQualityGate,
RiskGate, PositionSizing, ExecutionGate, GoLiveGate, or trading authorization.

## 13. Required staged delivery

This contract does not authorize later stages. They remain independently
reviewed and explicitly approved:

1. review and fast-forward merge of this contract;
2. tests-only JLGO planning-integration contract vectors;
3. JLGO planning-checkpoint Skill integration and hardening;
4. pre-write integration contracts, tests, and implementation;
5. review-checkpoint integration contracts, tests, and implementation;
6. test-layer and one-click verification contract and tooling;
7. CI contract and implementation;
8. W0 evidence review and WBS re-estimation when supported by engineering-hour
   evidence.

No stage may silently combine the next stage, and no stage may automatically
invoke, merge, release, deploy, or activate the following stage.

## 14. Acceptance checklist

This contract is acceptable only if review confirms:

- the boundary is limited to the future JLGO planning checkpoint;
- every `TaskSizeGateEvidence` field has one caller-owned source rule;
- the production evaluator is the only classification owner;
- Git, WBS, maturity, scope, checks, dependencies, risks, and ModelGate are
  verified before evaluation;
- unavailable, invalid, exceptional, unknown, contradictory, or stale evidence
  always stops without a next Skill;
- result mapping is deterministic and does not confer user authority;
- WBS mutation, pre-write integration, review integration, CI, activation,
  MT4, EA, and trading are outside this work order;
- the document does not claim that integration or activation exists;
- no current commit hash is embedded as a long-term workflow rule.
