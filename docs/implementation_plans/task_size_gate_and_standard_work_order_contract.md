# TaskSizeGate and Standard Work Order Contract

Status: WF-4B contract-only design. This document defines a future repository
planning boundary for sizing one proposed work order and expressing that work
order consistently. It does not implement TaskSizeGate, modify a workflow
Skill, change Supervisor behavior, add pytest markers, add a verification
script, or configure CI.

## 1. Purpose and current capability state

The repository already has:

- a weighted WBS for engineering-hour progress;
- a three-outcome ModelGate;
- a bounded single-work-order Supervisor;
- separate development, review, merge, and release Skills.

Those controls do not yet provide a deterministic task-size decision. In
particular, ModelGate answers whether the required model and evidence are safe;
it does not answer whether a proposed objective is small enough to remain one
work order.

The intended future planning flow is:

```text
repository evidence and WBS
    -> capability-layer classification
    -> TaskSizeGate
    -> ModelGate
    -> one frozen standard work order or a stop/split decision
    -> explicit user approval
```

The capability layers at the start of WF-4B remain separate:

| Layer | Current state |
| --- | --- |
| Policy | Git discipline, ModelGate, single-work-order ownership, and explicit approval are established. |
| Contract | This document will define TaskSizeGate and the standard work-order shape. |
| Tests | No TaskSizeGate contract tests exist. |
| Implementation | No TaskSizeGate parser, evaluator, or command exists. |
| Integration | No Skill invokes a TaskSizeGate implementation. |
| Activation | No automated size gate is active. |
| Verification | No runtime TaskSizeGate behavior has been verified. |

WF-4B changes only the contract layer. It must not be cited as evidence that a
TaskSizeGate implementation or enforcement integration exists.

## 2. Independent decision dimensions

Every future planning decision must keep these dimensions separate:

1. **Capability maturity** describes repository evidence using the WBS values
   `NOT_STARTED`, `POLICY_ONLY`, `CONTRACT_ONLY`, `TESTS_ONLY`, `IMPLEMENTED`,
   `INTEGRATED`, `ACTIVATED`, and `VERIFIED`.
2. **TaskSize** estimates the largest bounded engineering scope in the proposed
   work order using `XS`, `S`, `M`, `L`, or `XL`.
3. **Task decision** says whether the objective may remain one work order using
   `ALLOW_SINGLE_WORK_ORDER`, `SPLIT_REQUIRED`, or `STOP_UNCERTAIN`.
4. **ModelGate** preserves the existing model and uncertainty decision using
   `NORMAL_ALLOWED`, `PRO_REQUIRED`, or `STOP_UNCERTAIN`.
5. **Supervisor eligibility** says whether the already bounded Supervisor may
   execute the frozen work order. It does not grant merge, release, deployment,
   activation, MT4 access, or trading authority.

A small task can still be `PRO_REQUIRED`. A large task can be conceptually
simple and still require `SPLIT_REQUIRED`. A documented policy or contract does
not imply implementation or activation.

The five TaskSize values are the complete classification vocabulary. When the
size itself cannot be classified safely and Task decision is
`STOP_UNCERTAIN`, the output field is `task_size = null`. `null` is an absence
of classification, not a sixth TaskSize value.

## 3. TaskSizeGate inputs

TaskSizeGate must receive or derive all of the following from repository
evidence and the candidate work order before any branch creation or file write:

- one objective stated as a testable outcome;
- applicable WBS package IDs;
- current capability maturity;
- one intended maturity transition, or one explicitly maturity-preserving
  revision with the current and target maturity equal and a hardening or
  maintenance reason;
- exact base main and proposed branch;
- estimated invested and remaining engineering-hour range for this order;
- exact allowed file paths and their count;
- exact prohibited file paths and capabilities;
- capability layers touched by the work order;
- subsystem and work-package boundaries touched;
- public interfaces, schemas, protocols, settings, filesystems, external
  systems, and activation surfaces affected;
- targeted, regression, full-suite, build, grep, diff, and scope checks;
- known dependencies and whether their evidence is already present;
- risk and policy impact;
- ModelGate evidence;
- unknowns that could expand scope or weaken verification.

Caller estimates, commit counts, test counts, file counts alone, and a desired
deadline are not sufficient evidence of engineering effort. File and layer
counts constrain scope but do not replace engineering-hour estimates.

## 4. Counting rules

### 4.1 Engineering hours

Use the upper bound of the proposed equivalent-engineer-hour range when
classifying TaskSize. The range must include design, implementation, tests,
review-fix allowance, integration checks, and required documentation for this
work order. It must not count merge, release, or calendar observation as if
they were implementation in the same order.

If no defensible upper bound can be produced, the result is `STOP_UNCERTAIN`.
Because the size itself is then unclassifiable, `task_size` must be `null`.

### 4.2 Files

Count every file that may be added, modified, renamed, generated, or deleted by
the work order. A directory wildcard is not an exact file scope. Generated
files and snapshots cannot be omitted to make the task appear smaller.

If the exact file set cannot be frozen, the result is `STOP_UNCERTAIN`.

### 4.3 Capability layers

Count each distinct layer touched from this ordered vocabulary:

```text
POLICY
CONTRACT
TESTS
IMPLEMENTATION
INTEGRATION
ACTIVATION
VERIFICATION
```

Adjacent layers are consecutive values in that order. Review, merge, and
release are separate work orders and are not capability layers added to a
development order.

### 4.4 Conservative maximum

Calculate the size implied by hours, files, and layers independently. The final
TaskSize is the largest result. Scope cannot be downgraded because one metric is
small.

## 5. TaskSize classifications

| TaskSize | Maximum engineering-hour upper bound | Maximum files | Maximum capability layers | Single-order interpretation |
| --- | ---: | ---: | ---: | --- |
| `XS` | 2 hours | 1 | 1 | Trivial, exact, isolated change. |
| `S` | 8 hours | 3 | 1 | Small change in one capability layer. |
| `M` | 16 hours | 5 | 2 adjacent layers | Reviewable bounded work, normally handled manually. |
| `L` | 40 hours | 10 | 3 layers | Too large for one standard work order and must be decomposed. |
| `XL` | More than 40 hours | More than 10 | More than 3 layers | Program-sized work or multi-package activation; must be decomposed before development. |

Boundary rules:

- an upper bound equal to a threshold remains in that threshold's class;
- an upper bound above 2 hours starts at `S`;
- an upper bound above 8 hours starts at `M`;
- an upper bound above 16 hours starts at `L`;
- an upper bound above 40 hours is `XL`;
- 2 non-adjacent layers require at least `L` even when hours and files are
  smaller;
- cross-package activation, deployment, or Live enablement is always `XL` and
  is not currently authorized;
- a work order with multiple independent objectives is at least `L` and must be
  split, regardless of its claimed hour estimate.

## 6. Task decision

Task decision uses exactly these values:

```text
ALLOW_SINGLE_WORK_ORDER
SPLIT_REQUIRED
STOP_UNCERTAIN
```

### 6.1 ALLOW_SINGLE_WORK_ORDER

Allowed only when:

- the objective, base, branch, files, capability impact, dependencies, tests,
  commit, push destination, and stop conditions are exact;
- there is one objective and either one intended maturity transition or one
  explicitly maturity-preserving revision;
- TaskSize is `XS`, `S`, or `M`;
- no prohibited combination below applies;
- ModelGate is independently resolvable;
- a failed check can stop without editing unrelated files.

`ALLOW_SINGLE_WORK_ORDER` is a planning result, not user approval and not
permission to merge, release, deploy, activate, or trade.

### 6.2 SPLIT_REQUIRED

Required when:

- TaskSize is `L` or `XL`;
- the order contains multiple independent objectives;
- it combines non-adjacent capability layers;
- it combines contract, implementation, integration, and activation without
  independently reviewable boundaries;
- it combines production implementation with API, reader, MT4, EA, Demo
  execution, or Live activation;
- its tests cannot attribute failure to one bounded change;
- one review could not safely accept or reject the whole diff.

A split decision must return to read-only planning. It must not create several
parallel work branches automatically.

### 6.3 STOP_UNCERTAIN

Required when Git state, work ownership, ancestry, objective uniqueness, hour
range, file scope, capability layers, dependency evidence, tests, policy
compatibility, ModelGate, or expected outputs cannot be determined safely.

`STOP_UNCERTAIN` must not be converted to `SPLIT_REQUIRED` merely to keep work
moving. Missing evidence must be resolved first.

TaskSize handling for a stopped decision is fixed:

- `task_size = null` is permitted only when Task decision is
  `STOP_UNCERTAIN` and the size classification itself is unsafe;
- if TaskSize is known but another required dimension is uncertain, preserve
  the known `XS`, `S`, `M`, `L`, or `XL` value and return `STOP_UNCERTAIN`;
- `ALLOW_SINGLE_WORK_ORDER` and `SPLIT_REQUIRED` must always carry exactly one
  of the five TaskSize values and must never carry `null`.

## 7. ModelGate compatibility

TaskSizeGate does not add or rename ModelGate values. ModelGate continues to
use exactly:

```text
NORMAL_ALLOWED
PRO_REQUIRED
STOP_UNCERTAIN
```

Existing priority remains:

```text
STOP_UNCERTAIN > PRO_REQUIRED > NORMAL_ALLOWED
```

`PRO_REQUIRED` applies, regardless of TaskSize, to repository architecture,
canonical protocol changes, first production validators/readers/writers, API
reader activation, Settings or source-mode integration, Windows filesystem
security, real MT4 access, RiskGate, PositionSizing, TradePlanSchema,
ExecutionGate, MQL4, EA, GoLiveGate, automatic Demo execution activation, Live
trading, deployment, or any execution chain.

Overall planning disposition is evaluated conservatively:

```text
STOP_UNCERTAIN
    > SPLIT_REQUIRED
    > PRO_REQUIRED
    > NORMAL_ALLOWED
```

This ordering does not merge Task decision and ModelGate into one enum. It only
defines which blocking condition is reported first.

## 8. Supervisor eligibility

Supervisor eligibility uses:

```text
ELIGIBLE
CONDITIONAL_PRO_RESUME
NOT_ELIGIBLE
```

### 8.1 ELIGIBLE

All of these are required:

- Task decision is `ALLOW_SINGLE_WORK_ORDER`;
- TaskSize is `XS` or `S`;
- ModelGate is `NORMAL_ALLOWED`;
- main is clean and synchronized;
- no active unmerged work branch exists;
- exact files and all required checks are frozen;
- no policy relaxation, merge, release, deployment, activation, MT4 access, or
  second work order is included.

### 8.2 CONDITIONAL_PRO_RESUME

This state may be reported only when:

- Task decision is `ALLOW_SINGLE_WORK_ORDER`;
- TaskSize is `XS` or `S`;
- ModelGate is `PRO_REQUIRED`;
- the exact work order has already been frozen;
- the Supervisor stops before branch creation or writes;
- the user later explicitly confirms Codex Pro and authorizes only that frozen
  order's development, tests, work-branch commit/push, and independent review.

It never authorizes merge, main push, tag, deployment, activation, MT4 or EA
execution, policy relaxation, or a second work order.

### 8.3 NOT_ELIGIBLE

Required for:

- TaskSize `M`, `L`, or `XL`;
- `SPLIT_REQUIRED` or `STOP_UNCERTAIN`;
- unresolved ModelGate;
- any scope that exceeds the Supervisor's existing resource and authority
  limits.

`NOT_ELIGIBLE` does not mean the work is forbidden. It means the work requires
manual planning and the normal separated Skills after any required split.

## 9. Evaluation checkpoints

The future Gate must be evaluated independently at three checkpoints.

### 9.1 Planning checkpoint

`jlgo` classifies the proposed order from current Git, WBS, policy, contracts,
tests, production code, integration, activation, and verification evidence. It
returns one TaskSize, one Task decision, one ModelGate, and one Supervisor
eligibility value. It does not write files or create a branch.

### 9.2 Pre-write checkpoint

`jl-develop` or `jl-supervisor` rechecks the frozen values immediately before
branch creation or file writes. Changed Git state, a newly occupied branch,
dirty worktree, missing dependency, or uncertain scope stops the task.

If implementation reveals a larger file set, extra objective, higher layer,
larger hour upper bound, or new safety impact, the current work order stops. It
must not silently expand scope.

### 9.3 Review checkpoint

`jl-review` recalculates TaskSize against the actual commit list, diff, files,
interfaces, tests, and capability effect. Review must reject an undeclared size
or layer expansion even when tests pass.

`jl-merge` verifies the already approved scope and ancestry. It does not repair
or reclassify an oversized work order during merge.

## 10. Standard work-order template

Every future development or revision order must be expressible with the
following fields before approval:

```text
【Work order identity】
- Work order name:
- One objective:
- WBS package IDs:
- Current maturity:
- Target maturity:
- Intended maturity transition, or current == target with a specific
  maturity-preserving hardening/maintenance reason:

【Git checkpoint】
- Base branch and immutable base commit:
- Required origin/main commit:
- Work branch:
- New branch or revision branch:
- Required clean-state and ancestry evidence:

【Gate decisions】
- Estimated engineering-hour range:
- TaskSize:
- TaskSize evidence by hours, files, and layers:
- Task decision:
- ModelGate:
- ModelGate reasons:
- Supervisor eligibility:

【Exact scope】
- Files allowed to add:
- Files allowed to modify:
- Files allowed to delete or rename:
- Forbidden files:
- Forbidden capabilities and policy changes:

【Technical contract】
- Existing interfaces and owners to reuse:
- Public interfaces to add or change:
- Inputs and strict types:
- Outputs and exact keys/types:
- Deterministic precedence and reason codes:
- Fail-closed semantics:
- Input immutability and output-safety requirements:
- Explicit non-goals:

【Verification】
- Targeted tests:
- Related regressions:
- Full backend tests:
- Frontend tests/typecheck/build:
- Isolation grep:
- git diff --check:
- Exact file-scope check:
- Warning and skipped policy:
- Stop conditions:

【Delivery】
- Ordinary commit message:
- Work-branch push destination:
- Amend and force-push policy:
- Merge, tag, deployment, and activation boundaries:
- Required next review Skill:

【WBS accounting】
- Expected invested-hour movement:
- Expected remaining-hour movement:
- Uncertainty or calendar evidence changed:
- Re-estimation required after merge:

【Final report】
- Actual branch and commit:
- Actual files and tests:
- Warning/skipped:
- Push/merge/tag/activation status:
- Capability still not implemented or enabled:
- User explicit approval required before the next write stage: yes
- Required `【下一步操作卡】` with current state, one next action, model,
  next Skill, and one copyable instruction:
```

Omitted fields must be written explicitly as `not applicable` with a reason.
They must not be silently deleted from the template.

## 11. Decision examples

| Example | Evidence | TaskSize | Task decision | ModelGate | Supervisor eligibility |
| --- | --- | --- | --- | --- | --- |
| One-file wording correction, 1 hour, docs-only | Exact file and content check | `XS` | `ALLOW_SINGLE_WORK_ORDER` | `NORMAL_ALLOWED` | `ELIGIBLE` |
| Three-file tests-only safety contract, 6 hours | One TESTS layer and known regressions | `S` | `ALLOW_SINGLE_WORK_ORDER` | `NORMAL_ALLOWED` | `ELIGIBLE` |
| Five-file adjacent tests plus implementation, 14 hours | One objective, two adjacent layers | `M` | `ALLOW_SINGLE_WORK_ORDER` | `NORMAL_ALLOWED` | `NOT_ELIGIBLE` |
| One-file canonical protocol contract, 6 hours | Small scope but critical architecture | `S` | `ALLOW_SINGLE_WORK_ORDER` | `PRO_REQUIRED` | `CONDITIONAL_PRO_RESUME` |
| RiskGate test hardening, 3 files, 8 hours | One TESTS layer but high-risk boundary | `S` | `ALLOW_SINGLE_WORK_ORDER` | `PRO_REQUIRED` | `CONDITIONAL_PRO_RESUME` |
| Eight-file CI and Skill implementation, 28 hours | Multiple governance surfaces | `L` | `SPLIT_REQUIRED` | `PRO_REQUIRED` | `NOT_ELIGIBLE` |
| End-to-end EA plus API activation, 60 hours | Multiple packages and activation | `XL` | `SPLIT_REQUIRED` | `PRO_REQUIRED` | `NOT_ELIGIBLE` |
| Candidate with wildcard files, unknown regressions, and no defensible size upper bound | Scope, size, and verification cannot be frozen | `null` | `STOP_UNCERTAIN` | `STOP_UNCERTAIN` | `NOT_ELIGIBLE` |

These examples describe classification only. They do not authorize those work
orders or their capabilities.

## 12. WBS accounting boundary

TaskSizeGate consumes WBS estimates but does not rewrite them automatically.
After an accepted merge, `jlgo` reviews whether actual evidence materially
changes invested or remaining engineering-hour ranges. Any change follows the
WBS update protocol and preserves Demo and Live as separate denominators.

WF-4B does not change the existing WBS hours or progress percentages. A new
document is not, by itself, sufficient reason to increase business-capability
progress.

## 13. Required staged delivery after WF-4B

No later stage is automatically authorized. Expected future stages remain
separate:

1. independent review and explicit fast-forward merge of this contract;
2. tests-only TaskSizeGate contract vectors;
3. TaskSizeGate implementation in a separately approved exact scope;
4. Skill integration and hardening;
5. test-layer and one-click verification contract;
6. verification tooling implementation;
7. CI contract and implementation;
8. W0 evidence review and WBS re-estimation if justified.

Each stage requires its own TaskSizeGate and ModelGate decision, work order,
review, user merge approval, and next-action card.

## 14. Explicit non-goals

WF-4B does not:

- modify `AGENTS.md`;
- modify any Skill or `openai.yaml`;
- implement or activate TaskSizeGate;
- add a parser, command, script, pytest marker, GitHub Action, or CI workflow;
- modify the weighted WBS or its current hour ranges;
- modify backend, frontend, MT4, data, models, dependencies, or runtime config;
- implement ReplayRunner, TradePlan, RiskGate, PositionSizing, ExecutionGate,
  EA, or an execution chain;
- connect to MT4, enable a reader, place an order, or authorize Demo or Live
  trading;
- authorize WF-4C or any business work order.

This document is a repository workflow contract only. It is not an enforcement
implementation and is not evidence that TaskSizeGate has been integrated or
activated.

## 15. Acceptance checklist

WF-4B is complete only when review confirms that this document alone defines:

- the independence of capability maturity, TaskSize, Task decision, ModelGate,
  and Supervisor eligibility;
- exact `XS`, `S`, `M`, `L`, and `XL` thresholds;
- `task_size = null` only for an unclassifiable `STOP_UNCERTAIN`, without a
  sixth TaskSize value;
- conservative hour, file, and capability-layer counting;
- exact Task decision and ModelGate vocabularies;
- deterministic stop, split, Pro, and normal priority;
- high-risk ModelGate overrides without inflating TaskSize artificially;
- Supervisor normal and explicit-Pro-resume boundaries;
- planning, pre-write, and review checkpoints;
- a complete standard work-order template;
- explicit maturity-changing and maturity-preserving revision forms;
- examples for every TaskSize and blocking outcome;
- WBS accounting without automatic progress inflation;
- separation from tests, implementation, Skill integration, validation tooling,
  CI, activation, execution, and the next work order.
