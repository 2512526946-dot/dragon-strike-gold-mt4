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
- a command-line adapter, API, CI job, daemon, or autonomous state service;
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
- for a new development candidate, the current branch is exactly `main`;
- local `main` and `origin/main` are readable, synchronized, and identify the
  same immutable commit;
- the worktree status is readable;
- visible work branches can be classified by ancestry;
- the applicable WBS evidence and capability state are readable;
- the proposed objective, exact files, checks, branch, commit message, push
  destination, boundaries, dependencies, and stop conditions are frozen.

For new work, a dirty worktree, unsynchronized main, active unmerged work,
unresolved
ancestry, occupied target branch, missing dependency, unknown scope, or
unreadable evidence prevents an allowed planning result. The integration must
stop before branch creation or file writes.

When the current branch contains active unmerged work, `jlgo` may recommend
only the applicable review, revision, or merge path. It must not construct a
new development candidate. When the current branch is neither `main` nor the
one active work branch being routed, `jlgo` must stop without proposing a new
development order. A clean retained historical branch is not a substitute for
being on synchronized `main` when planning new work.

Retained historical branches whose tips are already ancestors of `main` are
not active work and must not create a false stop.

Planning an explicitly requested revision or preservation recovery on that
same active branch is not a new development candidate. Read-only JLGO may
freeze a fresh revision packet after proving the shared pre-write contract
section 6 recovery conditions and the user's exact adopted history, state,
scope and authority. These modes do not override AGENTS: a task starting with
preserved dirty work must include explicit one-time authority addressing that
stop rule; absent that exception only read-only diagnosis is permitted.
Expected edits within an already accepted development phase are not a new
checkpoint. It must not call an evaluator when the user requested
diagnosis only. An ordinary dirty worktree does not grant recovery authority.
Parallel work still requires a separate explicit user exception; it is never
inferred from the availability of worktrees.

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
| `work_branch` | One canonical `work/...` branch with the approved new, revision or recovery existence rule. |
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

### 5.1 Shared audit packet and invocation ledger

This section is the single caller-owned record protocol for JLGO, pre-write,
review, and Supervisor. It does not add an evaluator field, a persistence
service, or an autonomous workflow engine. Earlier capability tables describe
their original deliveries, not a new WBS maturity claim.

Strict read-only planning and review use existing local refs and, when needed,
`git ls-remote`; never fetch, prune, refresh tags, update the index, or write
audit records. Use `git --no-optional-locks` for inspection. Tests must disable
repository caches and write temporary output only outside the worktree.
Unavailable remote evidence is unknown, not assumed synchronization.

Only a write-authorized owner with explicit user approval for the exact
external record directory may append audit records. Keep that directory outside
all repository worktrees and tracked scope. Read-only callers emit the packet
in their response and may read previously authorized records; they do not save
it. Audit storage permission is separate from project-file permission.
AGENTS output-safety rules still govern stored and displayed content. Permission
to write a directory is not permission to disclose raw output or sensitive
paths, market payload/checksums, credentials or exception text. Keep private
proof references separate from the safe user-facing packet summary. Storing
workflow-integrity digests requires explicit private integrity-metadata
authority consistent with AGENTS, or a user-approved narrow exception; without
it, emit only safe evidence and request that authority, never weaken the rule.
Do not claim a redacted summary is a complete restorable packet.

Required packet sections are ordered below. These are caller metadata, not
new `TaskSizeGateEvidence` fields or production types:

<!-- WORKFLOW_PACKET_BEGIN -->
| Section | Required proof |
| --- | --- |
| record_identity | Unique packet and attempt IDs, stage, format version, predecessor digest. |
| approval | Exact user-approved action, scope, stop conditions, model and record-write authority sources. |
| git_state | Repository/worktree identity, base, pre-Head, local/remote heads, branch mode, index and worktree state. |
| scope_manifest | Approved cumulative scope and current revision scope, with immutable base/head, approved preserved-content snapshot when applicable, and authority. |
| frozen_evidence | All 29 ordered fields with exact built-in types, original values and provenance. |
| frozen_results | Complete planning and latest accepted pre-write results, ordered reasons and their attempt IDs. |
| commit_authority | Ordered commit hashes, subjects, roles, packet ownership and explicit authority sources. |
| call_ledger | Per-stage attempt ID, evidence digest, invocation state, consumed calls and raw result reference. |
| check_evidence | Commands, exit status, counts, warnings/skips, source-tree, dependencies/config and check-set digests. |
| completion | Actual commit/push outcome and checked Head, or explicit pending state. |
<!-- WORKFLOW_PACKET_END -->

At planning time, pre-write/checks/completion are explicitly pending, never
invented. Before review, all required earlier results and checks must exist;
review completion itself remains pending. An accepted result must have one
unambiguous reference, not a filename guessed to mean "latest".

Preserve original bytes and digests. Append new records; never overwrite,
backdate, reconstruct missing history, or reinterpret a failed attempt as
accepted. A metadata correction references the original and proves unchanged
evidence/result bytes and values; it cannot change authority or call count.
A metadata-only correction may change a human-readable label/explanation,
not machine stage identity, source/dependency/check digests, raw check results,
commit/push outcomes, completion facts or accepted-result references. A failed
or stale check cannot be relabelled as accepted. Correcting those substantive
facts requires new independently proven evidence and explicit approval, with
the old failure preserved; rerun checks when their source binding is invalid.
Records are evidence copies, not approval, Git truth, or review PASS. Missing
history requires a new explicitly approved packet identifying the gap and
adopted history, never a fabricated old planning or pre-write result.

Use a versioned structured representation with explicit type tags for tuples
and ordered records. Decode only the declared tags; reject duplicate keys,
unknown tags, missing/extra/reordered fields, subclasses and scalar coercion.
Compare exact built-in strings and exact tuples, including commit records.
Never use eval/exec on record text or normalize an invalid evaluator result.
Preserve raw tool output alongside any explicitly defined decoding.

One stage attempt has the following closed invocation states. Counts refer to
actual production evaluator entry, not shell launches or ordinary test calls:

<!-- WORKFLOW_CALL_LEDGER_BEGIN -->
| Invocation evidence | Consumed calls | Permitted next action |
| --- | --- | --- |
| precondition_failed | 0 | diagnose_read_only |
| proven_not_started | 0 | authorized_transport_retry_same_packet |
| invocation_unknown | unknown | stop_and_reconcile_read_only |
| invoked_failed | 1 | stop_no_retry |
| invoked_accepted | 1 | resume_authorized_phase_without_recall |
<!-- WORKFLOW_CALL_LEDGER_END -->

A proven transport failure before process/evaluator start may retry only the
same frozen packet with explicit retry authority and fresh precondition checks.
Failure before invocation for another reason is not transport retry authority.
Unknown invocation state forbids blind retry. An exception or validation
failure after evaluator entry consumes the call. Re-running tests is not a
checkpoint call and cannot replace checkpoint evidence. Re-entering the same
logical checkpoint after a failed/uncertain attempt requires separate explicit
user approval, a new attempt ID and preserved history; no automatic loop or
reset of call count. Accepted checkpoints resume without another call.

Logical checkpoint identity is (approved order, phase, revision round), separate
from the invocation attempt ID. An authorized next phase or next bounded
Supervisor revision is a different checkpoint, not a retry. Existing approval
may cover it; no new per-round user approval is required inside the original
Supervisor allowance. Prove accepted predecessor checkpoints, any required
completed checks/commit/push, and an independent FIX BEFORE MERGE review before
a revision. Revalidate scope, ModelGate, frozen evidence and remaining budget;
freeze its commit subject before writing. Each new checkpoint gets one fresh
attempt and its own ledger entry, never another call on the predecessor.

Changing packet/attempt labels, phase or round cannot turn a failed/unknown
checkpoint into an authorized successor. Transition provenance must prove the
actual predecessor and original order; neither new records nor recovery reset
the at-most-two automatic revision budget. Missing authority, a skipped round,
exhausted budget or changed scope stops. Manual revisions still need explicit
approval. This distinction supplies no merge, tag, second-order or activation
authority.

The following scenarios count permitted NEW calls without a new retry/scope
approval; all other Git, evidence and phase prerequisites must already hold.
An independent code finding is not a failed TaskSizeGate checkpoint.

<!-- WORKFLOW_SUCCESSOR_BEGIN -->
| Scenario | Authority source | New calls | Continuation |
| --- | --- | --- | --- |
| accepted_same_checkpoint | existing_action_authority | 0 | resume_without_recall |
| failed_same_checkpoint | new_explicit_attempt_approval | 0 | stop |
| uncertain_same_checkpoint | new_explicit_attempt_approval | 0 | stop |
| accepted_next_phase | existing_phase_authority | 1 | fresh_attempt |
| supervisor_revision_one | existing_bounded_authority | 1 | fresh_attempt |
| supervisor_revision_two | existing_bounded_authority | 1 | fresh_attempt |
| supervisor_revision_three | user_direction_required | 0 | stop |
| missing_revision_review | not_authorized | 0 | stop |
| changed_revision_scope | new_planning_and_approval | 0 | stop |
| relabelled_failed_checkpoint | new_explicit_attempt_approval | 0 | stop |
<!-- WORKFLOW_SUCCESSOR_END -->

Checkpoint failure blocks writes and formal PASS, not useful read-only
diagnosis. Report verified facts, missing evidence and the precise approval
needed without another evaluator call or automatic Skill invocation.

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

| TaskSize and evaluator result | JLGO planning behavior |
| --- | --- |
| Valid TaskSize or `null` + `STOP_UNCERTAIN` Task decision + `STOP_UNCERTAIN` ModelGate + `NOT_ELIGIBLE` | Report the sanitized blocking category, set the next Skill to `none`, and stop. `null` is accepted only when the production evaluator could not classify size. |
| `L` or `XL` + `SPLIT_REQUIRED` + `NORMAL_ALLOWED` or `PRO_REQUIRED` + `NOT_ELIGIBLE` | Return to read-only decomposition, set the next Skill to `none`, and do not create parallel branches. |
| `XS` or `S` + `ALLOW_SINGLE_WORK_ORDER` + `NORMAL_ALLOWED` + `ELIGIBLE` | JLGO may recommend explicit `jl-supervisor` invocation when all Supervisor preconditions remain true. |
| `M` + `ALLOW_SINGLE_WORK_ORDER` + `NORMAL_ALLOWED` + `NOT_ELIGIBLE` | Recommend explicit `jl-develop`; do not use Supervisor. |
| `XS` or `S` + `ALLOW_SINGLE_WORK_ORDER` + `PRO_REQUIRED` + `CONDITIONAL_PRO_RESUME` | Freeze the order, require the user to state that Codex Pro is active and explicitly authorize the bounded Supervisor resume. |
| `M` + `ALLOW_SINGLE_WORK_ORDER` + `PRO_REQUIRED` + `NOT_ELIGIBLE` | Require Codex Pro and explicit `jl-develop` authorization. |
| Any unknown or contradictory TaskSize, Task decision, ModelGate, Supervisor eligibility, or reason-code combination | Treat as integration failure, emit `STOP_UNCERTAIN`, set the next Skill to `none`, and stop without recommending another Skill. |

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
