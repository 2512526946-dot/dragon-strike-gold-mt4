# JL Supervisor Single Work Order Contract

Status: WF-3 workflow contract. This document defines one bounded automation
loop for repository work. It does not activate the supervisor, merge a branch,
deploy software, connect MT4, or grant trading authority.

## 1. Purpose

JL Supervisor coordinates one explicitly started work order from Git preflight
through development, verification, work-branch publication, independent
read-only review, and no more than two scoped revision rounds. A successful run
stops after review PASS and emits a merge authorization card for the user.

The supervisor is not a nested Skill caller. It reads AGENTS.md and the five
existing workflow Skills as repository specifications, then executes its own
bounded state machine. It must not claim that jlgo, jl-develop, jl-review,
jl-merge, or jl-release ran unless the Codex runtime actually activated that
Skill.

## 2. Architecture and trust boundary

The architecture has two roles:

1. The main supervisor thread performs preflight, freezes one work order,
   applies ModelGate, develops within the frozen scope, runs tests, commits, and
   pushes the work branch.
2. A newly started custom subagent named jl_supervisor_reviewer independently
   reviews the base, head, frozen work order, actual diff, and test evidence in
   a read-only sandbox.

The reviewer receives evidence, not the developer's private reasoning or
self-assessment. It inspects the actual Git diff and returns only PASS,
PASS WITH FOLLOW-UP, FIX BEFORE MERGE, or NO-GO. If the reviewer cannot be
started, cannot inspect the evidence, or cannot complete, the supervisor stops
without assigning itself PASS. Manual jl-review is then required.

## 3. Invocation modes

The supervisor supports exactly three modes.

### 3.1 Autonomous low-risk

The user explicitly invokes jl-supervisor without supplying an approved work
order. The supervisor may select exactly one smallest NORMAL_ALLOWED work order
only when clean synchronized main, branch ancestry, repository evidence, exact
file scope, tests, and commit requirements make the choice unique. It freezes
that order before creating a branch or editing files.

### 3.2 Approved work order

The user explicitly supplies or approves one complete work order. The
supervisor validates the order against Git and repository policy, applies
ModelGate, and may proceed only if the result is NORMAL_ALLOWED.

### 3.3 Pro resume

When ModelGate returns PRO_REQUIRED, the supervisor stops before creating or
switching a work branch and before writing any file. A later resume requires
the user to explicitly state that Codex Pro is active and authorize only the
frozen work order's development, tests, work-branch commits and push, and
independent review. That authorization never includes merge, push main, tag,
deployment, MT4 activation, automatic Demo execution, live trading, risk-policy
changes, or a second work order.

## 4. Preflight

Before selecting or resuming work, the supervisor must:

- read AGENTS.md and all five existing workflow Skill files;
- fetch origin with prune and tags when network access is available;
- verify the working tree state, current branch, main, origin/main, recent
  commits, tags, visible work branches, and branch ancestry;
- classify retained work branches using merge-base and main..<branch> evidence;
- ignore branch tips already contained by main;
- verify that main and origin/main are synchronized for new work;
- detect an existing target branch before trying to create it;
- inspect relevant contracts, production code, tests, and capability state;
- distinguish policy, contract, tests, production implementation, integration,
  and activation.

Dirty or ambiguous state is STOP_UNCERTAIN. The supervisor must not stash,
delete, overwrite, reset, rebase, force push, or guess ownership.

## 5. Git recovery without state files

The supervisor stores no progress JSON, database, or runtime log. Recovery is
derived only from Git, the frozen work order in the current task, and repository
evidence.

Safe recovery is allowed only when exactly one relevant active work branch is
identifiable, its base and head are provable, its diff remains inside the frozen
scope, its history is linear, and the working tree is clean. The supervisor may
resume from the earliest incomplete state: verification, commit, push, review,
or a previously authorized revision round.

If the working tree is dirty, more than one branch could match, scope has
expanded, the work order cannot be reconstructed exactly, ancestry is unclear,
or evidence conflicts, recovery is STOP_UNCERTAIN. No state file may be created
to bypass this rule.

## 6. Frozen work order

Before any branch creation or file write, the supervisor freezes:

- one task name and objective;
- the exact base main and expected branch name;
- every allowed file path;
- prohibited files and capabilities;
- targeted, regression, full-suite, build, grep, and diff checks as applicable;
- commit message and push destination;
- ModelGate result;
- completion and stop conditions.

One run owns one work order and one work branch. Scope expansion requires a new
user decision and ends the current run. Passing review does not authorize a
second work order.

## 7. ModelGate

ModelGate has three mutually exclusive outcomes with deterministic priority:

STOP_UNCERTAIN > PRO_REQUIRED > NORMAL_ALLOWED.

### 7.1 STOP_UNCERTAIN

Use STOP_UNCERTAIN when Git state, work ownership, branch ancestry, work-order
uniqueness, file scope, tests, capability impact, policy compatibility, or
required evidence cannot be determined safely. No automatic loop is allowed.

### 7.2 PRO_REQUIRED

Use PRO_REQUIRED before branch creation or file writes for repository-level
architecture, canonical protocol changes, first production validators/readers/
writers, API reader activation, Settings or source-mode integration, Windows
filesystem security, real MT4 access, RiskGate, PositionSizing, ExecutionGate,
TradePlanSchema, MQL4, EA, GoLiveGate, automatic Demo execution activation,
live trading, deployment, or any execution chain.

PRO_REQUIRED is a model requirement and a stop state. It is not high-risk
development authorization. Even after an explicit Pro resume, development
authorization does not become deployment or activation authorization.

### 7.3 NORMAL_ALLOWED

Use NORMAL_ALLOWED only for a precise low-risk work order with clean synchronized
Git state, no active unmerged work, exact file scope, known tests, fixed commit
requirements, and no high-risk capability or policy change.

## 8. Authorization matrix

| Action | Explicit supervisor start | Explicit Pro resume | Separate approval required |
| --- | --- | --- | --- |
| Plan one NORMAL_ALLOWED order | Yes | Yes, frozen order only | No |
| Develop and test frozen scope | Yes | Yes | No |
| Commit and push work branch | Yes | Yes | No |
| Independent read-only review | Yes | Yes | No |
| Up to two scoped revisions | Yes | Yes | No |
| Merge or push main | No | No | Always |
| Create or push tag | No | No | Always |
| Deploy | No | No | Always |
| Activate MT4 or a reader | No | No | Always |
| Activate Demo automatic execution | No | No | Always |
| Activate live trading | No | No | Always |
| Change approved risk policy | No | No | Always |
| Start a second work order | No | No | Always |

Automatic trading stages require separate explicit authorization at every
contract, implementation, integration, activation, and release boundary.

## 9. Development and validation loop

For NORMAL_ALLOWED work, or an explicitly resumed frozen Pro work order, the
main thread:

1. creates or safely recovers one work branch;
2. edits only frozen files;
3. runs targeted tests first;
4. runs related regressions;
5. runs full backend tests and frontend tests/build when the scope requires;
6. runs isolation grep, git diff --check, and exact scope checks;
7. creates an ordinary commit and pushes only the work branch;
8. starts a new jl_supervisor_reviewer subagent with independent evidence;
9. handles the review result according to the bounded state machine.

The supervisor never weakens a safety test to obtain a pass and never expands
scope to fix an unrelated failure.

## 10. Review outcomes and revisions

- PASS: stop and produce the final merge authorization card.
- PASS WITH FOLLOW-UP: produce the card only when the reviewer explicitly says
  the follow-up does not block merge; otherwise treat it as a required revision.
- FIX BEFORE MERGE: apply one minimal revision only within frozen scope, rerun
  all required validation, create one ordinary new commit, push the same work
  branch, and start a new independent reviewer.
- NO-GO: stop. Do not generate a merge or release instruction.

There may be at most two automatic revision rounds. Each round uses a normal
new commit. Amend and force push are forbidden. Revisions may not expand file
scope, weaken safety tests, alter approved trading/risk policy, or activate a
capability. If review is still not mergeable after two rounds, stop for user
direction.

## 11. Reviewer evidence

The reviewer receives only:

- base branch and immutable base commit;
- work branch and head commit;
- frozen work-order text and allowed-file list;
- actual commit list and Git diff;
- executed test commands and their results;
- known warnings and skips;
- relevant repository contracts and safety rules.

It does not receive private chain-of-thought, hidden developer reasoning, or a
request to confirm the developer's conclusion. Missing evidence prevents PASS.

## 12. Resource limits

One supervisor run is bounded to:

- one work order;
- one work branch;
- one initial development commit plus at most two revision commits;
- one initial reviewer plus at most two new reviewer rounds;
- only the frozen test/build/check command set;
- no background daemon, polling loop, status database, progress JSON, or
  persistent runtime log;
- no merge, main push, tag, deployment, activation, or second work order.

Unexpected resource growth, repeated infrastructure failure, or reviewer
unavailability stops the run.

## 13. Final merge authorization card

After a mergeable PASS, the supervisor stops and emits:

~~~text
【最终合并授权卡】
- Frozen work order:
- Base main:
- Work branch:
- Head commit:
- Commit list:
- Exact modified files:
- Test evidence:
- Warning / skipped:
- Independent review conclusion:
- Revision rounds used:
- Merge performed: no
- Tag created: no
- Deployment performed: no
- MT4 or trading activation: no
- User approval required: yes
- Recommended next Skill: $jl-merge
~~~

The card is evidence for a later user decision. It is not merge authorization
by itself and must not run jl-merge automatically.

## 14. Invocation text

The shortest normal invocation is:

~~~text
请使用仓库级 Skill jl-supervisor。
继续完成一个巨龙工单闭环。
~~~

A Pro resume must explicitly state:

~~~text
我已切换 Codex Pro，并授权 jl-supervisor 仅继续已冻结工单的开发、测试、
工作分支 commit/push 和独立 review。该授权不包含 merge、push main、tag、
部署、MT4 激活、自动交易激活、实盘或第二工单。
~~~

## 15. Non-goals

WF-3 does not execute the supervisor loop, merge main, push main, create a tag,
deploy, activate MT4, enable Demo automatic trading, enable live trading, call
an EA, modify approved leverage or loss limits, implement a trading Gate, or
start another business work order.
