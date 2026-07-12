# TaskSizeGate jl-review Checkpoint Integration Contract

Status: WF-4K contract-only design. This document defines the future
TaskSizeGate checkpoint used by `jl-review` before it may issue a review
conclusion. It does not modify a Skill, add tests, implement the checkpoint,
configure CI, or activate any workflow or trading capability.

## 1. Purpose and capability boundary

The repository already has a TaskSizeGate contract, immutable contract
vectors, a pure production evaluator, a JLGO planning integration, and
pre-write integrations for `jl-develop` and `jl-supervisor`. The generic
TaskSizeGate policy also says that review must detect undeclared size or layer
expansion. There is not yet a dedicated `jl-review` checkpoint contract,
contract-vector suite, or runtime Skill integration.

This contract defines one read-only checkpoint that validates the frozen work
order against the actual branch before the independent reviewer chooses one of
the existing conclusions:

```text
PASS
PASS WITH FOLLOW-UP
FIX BEFORE MERGE
NO-GO
```

The checkpoint is workflow governance. It is not DataQualityGate, RiskGate,
PositionSizing, ExecutionGate, or GoLiveGate. It does not evaluate market data,
grant trading permission, or change Demo-only, Read-only, and user-approval
policy.

The narrow capability maturity before WF-4K is `POLICY_ONLY`; this document
advances only that narrow review-checkpoint capability to `CONTRACT_ONLY`.

## 2. Position in the review flow

The future `jl-review` flow must be ordered as follows:

1. receive an immutable base, head, work branch, frozen work order, frozen
   planning result, and latest accepted pre-write result;
2. prove Git, commit, ancestry, remote synchronization, cumulative diff, and
   exact scope without changing the repository;
3. inspect the actual interfaces, capability layers, tests, checks, risks, and
   policy effects represented by the cumulative diff;
4. construct all 29 caller-owned `TaskSizeGateEvidence` fields;
5. perform pre-evaluator drift checks;
6. call the production evaluator exactly once;
7. validate exact result type, values, ordered reason codes, and equality with
   the frozen planning and pre-write results;
8. recheck Git and evidence for post-call drift; and
9. only after the checkpoint passes, continue the independent correctness,
   security, regression, and test-quality review.

A passing checkpoint is only permission to continue the already requested
read-only review. It is not a `PASS`, `PASS WITH FOLLOW-UP`, user approval,
merge authorization, branch action, next-Skill invocation, deployment, or
activation.

## 3. Immutable review inputs and ownership

The review caller owns and freezes these artifacts before any evaluator call:

- immutable base branch `main` and base commit;
- exact work branch and reviewed head;
- local and remote work-branch heads;
- ordered ordinary commit list between base and head, including each commit
  hash and exact subject;
- an immutable ordered commit-authority list that pairs every commit with its
  role and authority source without adding a TaskSizeGate evidence field;
- frozen objective, WBS package, maturity transition, scope, checks, commit,
  push destination, ModelGate, risks, policy impacts, and stop conditions;
- exact frozen planning `TaskSizeGateResult`;
- exact latest accepted pre-write `TaskSizeGateResult` and its call evidence;
- actual cumulative diff and changed-file list;
- actual test, build, grep, diff, and scope evidence; and
- explicit review-only authority.

The reviewer must obtain Git and diff facts itself. A developer report,
Supervisor self-assessment, commit message, test count, file name, or claimed
capability state is not proof. Missing, mutable, inaccessible, or contradictory
artifacts fail closed before evaluation.

The commit-authority list exists only in the immutable review packet for the
current task. It is not a repository file, state file, progress record,
database, or thirtieth `TaskSizeGateEvidence` field. Its entries are ordered
exactly like the Git commit list and use only these authority sources:

- the initial commit subject is the original frozen work-order
  `commit_message`;
- a manually approved revision subject is the exact message in that approved
  revision order; and
- a bounded Supervisor automatic revision subject is frozen before the first
  write of that revision inside the same authorized task and remaining
  revision allowance. The original bounded Supervisor authorization covers
  that in-scope revision, so no additional per-round user approval is implied.

The reviewer must prove the source for every entry from the current task's
immutable work-order or revision evidence. It must not infer authority from a
commit subject, developer report, branch history, or desired conclusion.

## 4. Git and branch preconditions

Before constructing evidence, the reviewer must prove all of the following:

- the worktree and index are clean and conflict-free;
- local `main` and `origin/main` both equal the frozen base commit;
- the current review target is the exact frozen work branch and head;
- local and remote work-branch heads equal the frozen head;
- frozen base `main` is an ancestor of the reviewed head;
- `main..head` contains only the expected linear ordinary commits;
- no merge commit, rebase, rewritten commit, unpushed commit, or uncommitted
  change is present;
- cumulative changed files are canonical relative paths and remain within the
  frozen allowed scope;
- no prohibited file or capability is present; and
- the branch has not already been merged, moved, deleted, or replaced.

The checkpoint is read-only. It must not checkout, switch, create, move,
reset, clean, stash, rebase, commit, push, merge, tag, or delete anything.
Failure of any precondition uses zero evaluator calls.

## 5. Production interface reuse

The future integration must import the existing public interface and reason
constants from `app.services.task_size_gate` in the backend Python runtime:

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

It must not copy thresholds, create a local classifier, add an adapter, patch
the evaluator, repair a result, or add review-only values to production
`reason_codes`.

## 6. Exact 29 caller-owned evidence fields

The reviewer must construct every field below in this exact order. Each field
has one review-owned source and revalidation rule.

| Field | Review source and revalidation rule |
| --- | --- |
| `objective` | Exact single outcome from the frozen approved work order; unchanged by implementation or review. |
| `objective_count` | Recount independently deliverable outcomes in the actual cumulative diff; any value other than the frozen count is drift. |
| `wbs_package_ids` | Frozen package IDs checked against current WBS ownership; an added package is drift. |
| `current_maturity` | Narrow capability maturity proven at frozen base main; unmerged commits never advance it. |
| `target_maturity` | Exact frozen adjacent target, or exact separately approved maturity-preserving target. |
| `maturity_reason` | Exact frozen transition or separately approved hardening/maintenance reason. |
| `base_branch` | Strict `main`; the reviewed work branch is never substituted here. |
| `base_main_commit` | Fresh equality of local main, remote main, and the frozen base commit. |
| `work_branch` | Exact frozen branch whose local and remote tips equal the reviewed head. |
| `commit_message` | Exact original frozen work-order message used at planning; it remains unchanged for the entire review and is never replaced by a manual or Supervisor revision message. Actual commit subjects and their authority are validated separately through the ordered commit-authority list. |
| `push_destination` | Exact `origin/<work_branch>` destination and never `main`. |
| `stop_conditions` | Exact frozen stop conditions; no deletion, weakening, or post hoc rewrite. |
| `estimated_engineering_hours_lower` | Frozen approved lower estimate; review must not reduce it to obtain an allow result. |
| `estimated_engineering_hours_upper` | Frozen upper estimate compared with actual scope and effort evidence; any required increase is drift. |
| `allowed_files` | Exact frozen canonical relative-file scope, checked against every cumulative changed path. |
| `prohibited_files` | Exact frozen canonical prohibited paths, checked case-insensitively against the cumulative diff. |
| `prohibited_capabilities` | Frozen capability, policy, merge, release, deployment, and activation exclusions checked against actual behavior. |
| `capability_layers` | Ordered distinct frozen layers compared with actual interfaces and effects; any undeclared layer is drift. |
| `subsystem_boundaries` | Frozen ownership boundaries checked against all imports, files, contracts, and runtime effects. |
| `affected_surfaces` | Frozen impact surfaces revalidated against the actual diff and tests; any added surface is drift. |
| `required_checks` | Complete targeted, regression, full-suite, build or explicit N/A, grep, diff, and scope categories with actual evidence. |
| `known_dependencies` | Every frozen dependency re-proven from repository evidence; newly required dependency is drift. |
| `dependency_evidence_known` | Strict true only when every dependency remains present, compatible, and reviewable. |
| `risk_and_policy_impacts` | Frozen impacts rechecked against actual code, tests, outputs, permissions, and safety policy. |
| `high_risk_reasons` | Exact current ModelGate reasons with no omission, downgrade, or post hoc addition. |
| `model_gate` | Frozen ModelGate rechecked against AGENTS and actual capability effect; `PRO_REQUIRED` is never downgraded. |
| `model_gate_evidence` | Concrete frozen and current evidence supporting the same ModelGate result. |
| `unknowns` | Every unresolved Git, scope, interface, test, dependency, risk, or policy fact; never removed to obtain allow. |
| `cross_package_activation` | Strict true only when actual scope performs cross-package activation; any change from frozen false is drift and any true value is outside this reviewable single-order path. |

The evidence object must be a fresh, frozen, exact `TaskSizeGateEvidence`.
Actual branch evidence is used to verify that the frozen evidence remains true;
it must not silently rewrite the approved order. A smaller or larger actual
classification, changed reason sequence, or changed eligibility is result
drift rather than permission to replace the frozen planning result.

The initial Git commit subject must equal the evidence `commit_message`.
Every later subject must equal its corresponding immutable manual-revision or
Supervisor-revision message. Missing, extra, reordered, duplicated, or
unprovable commits, subjects, roles, or authority entries are frozen-order
failure. They must not change `commit_message`, add an evidence field, or be
converted into evaluator input.

## 7. Zero-call and one-call ordering

The call accounting is deterministic:

- Git, frozen-order, commit-subject authority, dependency, scope,
  test-evidence, interface, or evidence-construction failure before invocation
  makes zero evaluator calls;
- an unavailable evaluator or public interface detected before invocation
  makes zero evaluator calls;
- only after every precondition and pre-evaluator drift check passes may the
  reviewer call exactly once:

```python
result = evaluate_task_size_gate(evidence=evidence)
```

- once invocation begins, an exception, invalid result, contradictory result,
  reason-code failure, planning/pre-write/review result mismatch, or post-call
  Git/evidence drift consumes the one permitted call; and
- no failure may retry, fallback, invoke a local classifier, call a second
  time, patch evidence, repair the result, or change the frozen work order.

The frozen work order, evidence, planning result, pre-write result, base, head,
commit list, diff, and Git checkpoint must remain unchanged across evaluation.

## 8. Exact result and reason-code validation

The result must satisfy all of these conditions:

- `type(result) is TaskSizeGateResult`;
- every field has its exact built-in type and a public production enum value;
- `reason_codes` is a non-empty exact `tuple` of unique built-in strings;
- an allowed NORMAL result has exactly
  `(SINGLE_WORK_ORDER_ALLOWED,)`;
- an allowed PRO result has exactly
  `(SINGLE_WORK_ORDER_ALLOWED, PRO_MODEL_REQUIRED)`;
- `PRO_MODEL_REQUIRED` is present only for `PRO_REQUIRED` and is always last;
- the TaskSize, task decision, ModelGate, eligibility, and reason sequence form
  one combination accepted by the production evaluator and JLGO contract; and
- the entire result equals both the frozen planning result and the latest
  accepted pre-write result.

Only an exact `ALLOW_SINGLE_WORK_ORDER` result may pass this checkpoint. For a
manually developed work order, `M` with `NOT_ELIGIBLE` remains a valid frozen
planning combination but does not become Supervisor-eligible. For a bounded
Supervisor work order, only `XS` or `S` with `ELIGIBLE`, or with
`CONDITIONAL_PRO_RESUME` and the same explicit Pro authority, is valid.

`STOP_UNCERTAIN`, `SPLIT_REQUIRED`, an impossible eligibility, unknown enum,
unknown or extra reason, missing reason, duplicate reason, out-of-order reason,
or any result mismatch fails closed. Review must not reinterpret a stopped or
split result as a code-review finding that can be fixed inside the current
authorization.

## 9. Drift categories

Review drift includes, without limitation:

- changed base, head, remote state, ancestry, commit graph, or worktree;
- missing, extra, reordered, duplicated, or unprovable commit subjects or
  commit-authority entries;
- extra, aliased, noncanonical, renamed, generated, or prohibited files;
- changed objective count, WBS ownership, maturity, hours, layer, subsystem,
  interface, dependency, affected surface, check, risk, policy, ModelGate,
  authority, commit, push destination, or stop condition;
- missing targeted, regression, full-suite, build/N/A, grep, diff, or scope
  evidence;
- capability behavior not declared by the frozen order;
- changed planning, pre-write, or review result or reason sequence; or
- any fact that cannot be independently proved from current repository
  evidence.

Drift never updates the frozen work order in place. It must not be converted to
`FIX BEFORE MERGE` merely to keep the branch moving.

## 10. Fixed fail-closed routing

The future checkpoint may report only one sanitized workflow category:

```text
REVIEW_CHECKPOINT_GIT_INVALID
REVIEW_CHECKPOINT_FROZEN_ORDER_INVALID
REVIEW_CHECKPOINT_DEPENDENCY_INVALID
REVIEW_CHECKPOINT_SCOPE_DRIFT
REVIEW_CHECKPOINT_SIZE_OR_LAYER_DRIFT
REVIEW_CHECKPOINT_RISK_OR_POLICY_DRIFT
REVIEW_CHECKPOINT_EVALUATOR_UNAVAILABLE
REVIEW_CHECKPOINT_EVALUATOR_RESULT_INVALID
REVIEW_CHECKPOINT_UNEXPECTED_FAILURE
```

These categories are not production TaskSizeGate reason codes. They must never
enter `TaskSizeGateResult.reason_codes`.

Any checkpoint failure prevents `PASS` and `PASS WITH FOLLOW-UP`. The formal
review conclusion is fixed to `NO-GO`, the next Skill is `无`, and no merge,
release, replanning, revision, activation, or dangerous instruction is
generated. The output must not contain exception text, traceback, credentials,
environment values, absolute local paths, raw user content, or other sensitive
material.

After a passing checkpoint, independent review findings continue to use the
existing `jl-review` mappings. A correctness or test finding may still produce
`FIX BEFORE MERGE`; a clean review may produce `PASS`. The checkpoint itself
must never manufacture either conclusion.

## 11. Authority and safety invariants

Neither a passing checkpoint nor a later review conclusion may automatically:

- approve the work on the user's behalf;
- create, switch, move, or delete a branch;
- modify files or tests;
- invoke another Skill or agent;
- commit, push, merge, rebase, tag, release, deploy, or activate;
- enable a reader, access real MT4, call an EA, or create an order; or
- grant Demo or Live trading permission.

Review remains strictly read-only. Merge still requires a separate explicit
user approval and `jl-merge`. Demo-only, Read-only, fixed safety flags, no
automatic ordering, and all approved trading and risk policies remain intact.

## 12. Staged delivery and governance budget

WF-4K delivers only this contract. Later stages are separately approved and
remain limited to the smallest review checkpoint:

1. immutable review-checkpoint contract vectors;
2. minimal `jl-review` Skill integration using the production evaluator; and
3. focused hardening only when independent review identifies a blocking gap.

After that minimal checkpoint is accepted and merged, planning must return to
the Demo MVP product critical path. This sequence must not expand into test
tooling, one-click verification, CI, metrics, another workflow checkpoint, or
a second governance objective.

## 13. Verification for WF-4K

WF-4K is docs-only. Its required checks are:

- targeted: inspect all required sections and the exact 29-field table;
- regression: confirm consistency with the TaskSizeGate, JLGO planning, and
  shared pre-write contracts;
- full suite: not applicable because no code, tests, or runtime configuration
  changes;
- build: not applicable because no frontend or generated artifact changes;
- grep: verify field names, call accounting, result identity, fail-closed
  routing, authority boundaries, and isolation terms;
- diff: run `git diff --check`; and
- scope: prove the cumulative diff contains only this document.

## 14. Acceptance checklist

Independent review must confirm that this document alone:

- defines a read-only checkpoint before any `jl-review` conclusion;
- preserves the independent correctness and test-quality review;
- freezes base, head, commits, work order, planning result, and pre-write
  result;
- keeps evidence `commit_message` equal to the original frozen work-order
  value while validating every actual commit subject and authority separately;
- distinguishes initial, manually approved revision, and bounded Supervisor
  automatic-revision authority without a thirtieth field or persistent state;
- defines all 29 evidence fields and their review-owned sources;
- uniquely reuses `TaskSizeGateEvidence`, `TaskSizeGateResult`, public reason
  constants, and `evaluate_task_size_gate`;
- makes pre-call failure zero calls and a valid attempt exactly one call;
- forbids retry, fallback, local classification, evidence mutation, and result
  repair;
- requires exact planning/pre-write/review result and reason-code identity;
- detects Git, scope, size, layer, dependency, test, risk, policy, authority,
  and post-call drift;
- maps every checkpoint failure to sanitized `NO-GO` with next Skill `无`;
- states that passing the checkpoint is not `PASS` or merge authority;
- leaves AGENTS, Skills, evaluator, WBS, tests, CI, and business code unchanged;
- does not implement or claim runtime integration, activation, verification,
  MT4, reader, EA, execution, or trading capability; and
- caps further governance work at the minimal review checkpoint before return
  to the Demo MVP product critical path.
