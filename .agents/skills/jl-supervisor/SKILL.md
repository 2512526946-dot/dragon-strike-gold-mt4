---
name: jl-supervisor
description: Run one bounded 巨龙出击 work-order loop from Git preflight through development, tests, independent read-only review, and at most two scoped revisions. Use only through explicit user invocation. Never merge main, push main, tag, deploy, activate MT4, enable automatic trading, or continue into a second work order.
---

# 巨龙监督

## 1. Role and authority

JL Supervisor runs one bounded work-order loop after explicit user invocation.
It is not a nested Skill caller. Read AGENTS.md and these repository Skills as
specifications before acting:

- .agents/skills/jlgo/SKILL.md
- .agents/skills/jl-develop/SKILL.md
- .agents/skills/jl-review/SKILL.md
- .agents/skills/jl-merge/SKILL.md
- .agents/skills/jl-release/SKILL.md

Execute planning, development, tests, revisions, and evidence collection inside
this Skill's own state machine. Do not claim that another Skill ran unless the
Codex runtime actually activated it.

The explicit start authorizes only one NORMAL_ALLOWED work order, one work
branch, its tests, ordinary commits, work-branch push, independent read-only
review, and at most two minimal revision rounds. It does not authorize merge,
push main, tag, deploy, activation, risk-policy changes, or a second work order.

## 2. Invocation modes

Support exactly three modes:

1. Autonomous low-risk: select the unique smallest NORMAL_ALLOWED order from a
   clean synchronized main only when repository evidence makes scope, tests,
   commit, and completion requirements exact.
2. Approved work order: validate and freeze the one complete order supplied or
   approved by the user, then apply ModelGate.
3. Pro resume: continue only the previously frozen PRO_REQUIRED work order
   after the user explicitly states that Codex Pro is active and authorizes
   development, tests, work-branch commit/push, and independent review only.

Normal shortest invocation:

~~~text
请使用仓库级 Skill jl-supervisor。
继续完成一个巨龙工单闭环。
~~~

Required Pro resume wording must carry the same meaning as:

~~~text
我已切换 Codex Pro，并授权 jl-supervisor 仅继续已冻结工单的开发、测试、
工作分支 commit/push 和独立 review。该授权不包含 merge、push main、tag、
部署、MT4 激活、自动交易激活、实盘或第二工单。
~~~

## 3. PREFLIGHT

Before selecting, creating, switching, or editing:

1. Read AGENTS.md, all five existing Skill files, and relevant metadata.
2. Fetch origin with prune and tags when network access is available.
3. Inspect status, current branch, main, origin/main, recent commits, tags,
   visible work branches, and ancestry.
4. Ignore retained branch tips already contained by main. Treat only branches
   with commits absent from main as active unmerged work.
5. For new work require a clean synchronized main, no active unmerged branch,
   and a target branch that does not already exist locally or remotely.
6. Inspect relevant policy, contract, tests, production implementation,
   integration, and activation evidence.

Dirty, conflicting, or unprovable state is STOP_UNCERTAIN. Do not stash, reset,
delete, overwrite, rebase, force push, or guess.

## 4. Git recovery

Do not create a supervisor state file, progress JSON, database, or persistent
runtime log. Recover only from Git evidence and the frozen work order in the
current task.

Recovery is allowed only when one relevant active branch is unambiguous, the
working tree is clean, base/head and linear ancestry are proven, and the actual
diff remains inside frozen scope. Resume at the earliest incomplete state:
verification, ordinary commit, work-branch push, review, or an authorized
revision round. Otherwise return STOP_UNCERTAIN and stop.

## 5. Freeze exactly one work order

Before branch creation or file writes, freeze:

- one objective and one work branch;
- exact base main and allowed files;
- forbidden files, capabilities, and policy changes;
- targeted, regression, full, build, grep, diff, and scope checks;
- commit message and work-branch push destination;
- ModelGate classification;
- completion and stop criteria.

Scope expansion or a second work order ends the run and requires a new user
decision.

## 6. ModelGate

Use exactly three classifications. Their priority is:

STOP_UNCERTAIN > PRO_REQUIRED > NORMAL_ALLOWED

### STOP_UNCERTAIN

Stop when Git ownership, ancestry, unique task choice, exact file scope, tests,
capability impact, policy compatibility, or required evidence is ambiguous.
Do not suggest or run an automatic closed loop.

### PRO_REQUIRED

Stop before creating a branch or writing a file for repository architecture,
canonical protocol changes, first production validator/reader/writer, API
reader activation, Settings or source mode integration, Windows filesystem
security, real MT4, RiskGate, PositionSizing, ExecutionGate, TradePlanSchema,
MQL4, EA, GoLiveGate, automatic Demo execution activation, live trading,
deployment, or any execution chain.

The root thread cannot switch its own model. PRO_REQUIRED is not high-risk
development authorization. A Pro resume authorizes only the frozen development,
tests, work-branch push, and review; high-risk development authorization does
not equal deployment or activation authorization.

### NORMAL_ALLOWED

Proceed only for a precise low-risk order with clean synchronized main, no
active unmerged work, exact file scope, known tests and commit requirements,
and no high-risk capability or policy change.

## 7. Development and verification

For an allowed frozen order:

1. Create or safely recover one work branch.
2. Edit only exact allowed files.
3. Run targeted tests first.
4. Run related regressions.
5. Run full backend tests and frontend tests/build when required by scope.
6. Run isolation grep, git diff --check, and exact file-scope checks.
7. Confirm no forbidden capability, policy, state file, or secret was added.
8. Create an ordinary new commit and push only the work branch.

Do not amend. Do not force push. Do not weaken safety tests or expand scope to
obtain a pass.

## 8. Independent reviewer subagent

After every initial push or revision push, start a new custom subagent named
jl_supervisor_reviewer. Its sandbox must be read-only.

Pass only:

- immutable base and head;
- work branch and commit list;
- frozen work order and allowed files;
- actual Git diff;
- executed test commands, results, warnings, and skips;
- relevant repository contracts and safety rules.

Do not pass developer private reasoning, chain-of-thought, or self-assessment.
The reviewer must inspect evidence independently and output only PASS,
PASS WITH FOLLOW-UP, FIX BEFORE MERGE, or NO-GO.

If the reviewer is unavailable or evidence cannot be inspected, stop. The
supervisor must not self-assign PASS. Require manual jl-review instead.

## 9. Revision state machine

- PASS: stop and emit the final merge authorization card.
- PASS WITH FOLLOW-UP: emit the card only if follow-up is explicitly
  non-blocking; otherwise treat it as FIX BEFORE MERGE.
- FIX BEFORE MERGE: make one minimal frozen-scope revision, rerun all required
  validation, create an ordinary new commit, push the same branch, and start a
  new independent reviewer.
- NO-GO: stop without a merge, release, or dangerous development instruction.

Allow at most two automatic revision rounds. Never amend, never force push,
never expand scope, never weaken safety tests, and never change approved trading
or risk policy. If the branch is not mergeable after two rounds, stop for user
direction.

## 10. Hard boundaries and resource cap

One run is limited to one work order, one work branch, one initial development
commit, at most two revision commits, one initial reviewer, and at most two new
reviewer rounds. Use only the frozen test/build/check set. Do not start a daemon,
polling loop, progress JSON, database, or persistent runtime log.

Hard stops: no merge; no push main; no tag; no deploy; no activation. Never
activate MT4, automatic Demo execution, live trading, an EA, or any execution
chain. Never change or loosen approved trading/risk policy. Never enter a second
work order.

## 11. Required output

During execution report PREFLIGHT, frozen order, ModelGate, branch/commit,
validation, review outcome, revisions used, safety boundaries, and current stop
state using this complete run card:

~~~text
【Supervisor 执行卡】
- Invocation mode:
- PREFLIGHT result:
- Frozen work order:
- ModelGate classification:
- Base main:
- Work branch:
- Current head:
- Exact modified files:
- Targeted / regression / full / build evidence:
- Diff / grep / scope evidence:
- Commit and work-branch push:
- Independent reviewer status:
- Review conclusion:
- Revision rounds used:
- Stop reason:
- Merge performed: no
- Tag created: no
- Deployment or activation: no
~~~

After mergeable PASS also output:

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

This card is not authorization and must not invoke jl-merge automatically.

Every terminal outcome must also end with:

~~~text
【下一步操作卡】
1. 当前状态：
2. 下一步要做什么：
3. 是否需要用户显式批准：
4. 模型要求：
5. 下一 Skill：
6. 可直接复制发送给 Codex 的完整指令：
~~~

On PASS the next Skill may be $jl-merge, but only after explicit user approval.
On reviewer failure, exhausted revisions, NO-GO, or STOP_UNCERTAIN, use no
dangerous merge, release, activation, or second-work-order instruction.
