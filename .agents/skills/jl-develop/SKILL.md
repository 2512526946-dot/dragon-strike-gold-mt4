---
name: jl-develop
description: Execute exactly one explicitly approved 巨龙出击 development or revision work order. Use only when the user has supplied or approved a complete scoped work order. Never merge main, create a tag, or continue into another work order.
---

# 巨龙开发

1. 先读取仓库根目录 `AGENTS.md`。
2. 确认用户已明确批准唯一工单。
3. 确认工单至少包含任务名称、main checkpoint、目标分支、允许修改文件、禁止范围、验证命令和提交要求。
4. 工单不完整时停止并指向 `$jlgo`。
5. 判断工单要求从 `main` 新建分支，还是继续现有修订分支。
6. 修订工单明确继续原分支时，不得因为分支存在而停止。
7. 在创建新工作分支或首次文件写入前，严格执行下方 TaskSizeGate pre-write checkpoint。
8. 只有 checkpoint 通过后，才可在现有用户批准内创建新工作分支或开始修改文件。
9. 只修改工单允许的范围，并保留所有无关用户改动。
10. 依次运行 targeted tests、相关 regression、必要的 full tests 和 `git diff --check`。
11. 按工单要求 commit，并 push 工作分支。
12. 不 merge，不 tag，不自动 review，不进入下一工单。
13. 只汇报当前工单结果，并建议用户显式调用 `$jl-review`。
14. 最终汇报末尾必须追加 `【下一步操作卡】`。

## TaskSizeGate pre-write checkpoint

本节只处理用户已经明确批准的一个 new work 或 approved revision 工单。它复用
`docs/implementation_plans/task_size_gate_pre_write_integration_contract.md`
和现有 production evaluator，不建立第二套 TaskSize、ModelGate、reason-code
或 Supervisor eligibility 分类逻辑。

在 `backend` Python runtime 中直接复用以下公开接口和 reason 常量：

```python
from app.services.task_size_gate import (
    CROSS_PACKAGE_ACTIVATION,
    INPUT_INVALID,
    MODEL_STOP_UNCERTAIN,
    MULTIPLE_OBJECTIVES,
    NON_ADJACENT_LAYERS,
    OVERSIZED,
    PRO_MODEL_REQUIRED,
    SINGLE_WORK_ORDER_ALLOWED,
    SIZE_UNCLASSIFIABLE,
    TaskSizeGateEvidence,
    TaskSizeGateResult,
    UNKNOWN_EVIDENCE,
    evaluate_task_size_gate,
)
```

### 调用前顺序

先冻结用户批准的完整工单、planning `TaskSizeGateResult`、显式 ModelGate/Pro
授权和 stop conditions，再重新读取 Git 与仓库证据。以下任一前置失败时固定
workflow-level `STOP_UNCERTAIN`，下一 Skill 为 `无`，调用 evaluator 零次，且
不得创建、切换或移动分支，也不得写文件：

- 工单缺失、可变、歧义，或 planning result / reason codes 不完整；
- worktree/index dirty、冲突、main mismatch 或 ancestry 无法确认；
- 目标分支占用、依赖证据缺失，或 allowed/prohibited scope 不再精确；
- objective、WBS、maturity、工时、层、依赖、风险、ModelGate、验证或 stop
  conditions 相对冻结工单发生漂移；
- 无法构造 fresh、frozen、strict exact `TaskSizeGateEvidence`。

new work 必须在当前分支仍为 `main` 时完成 checkpoint：worktree/index 干净，
本地 `main`、`origin/main` 与冻结 base commit 相同，所有 work branch ancestry
可确认且没有 active unmerged branch，目标 work branch 本地和远端均不存在。
checkpoint 通过前不得创建或切换目标分支。

approved revision 必须在当前分支已经是冻结 revision branch 时完成 checkpoint：
worktree/index 干净，本地与远端 work-branch head 等于批准 revision head，
`main` 和 `origin/main` 仍等于冻结 base commit，base ancestry、线性 commit
列表和累计 diff 均可证明且未越界。`base_branch` 仍严格为 `main`；当前分支只由
Git 前置状态和 `work_branch` 表达。未合并实现不得提升 frozen base-main
`current_maturity`，原批准 `target_maturity` 和 `maturity_reason` 不得变化。

### 29 项 caller-owned evidence

字段必须按以下顺序全部构造，不得缺失、增加、猜测、从 result 反推，或为了
获得 allow 而删除 unknown、缩小工时、文件范围或风险：

```text
TASK_SIZE_GATE_PRE_WRITE_EVIDENCE_FIELDS_BEGIN
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
TASK_SIZE_GATE_PRE_WRITE_EVIDENCE_FIELDS_END
```

每个字段必须按 pre-write contract 第 7 节的 caller-owned source rule 从冻结工单
和当前仓库事实重新验证。frozen order、evidence 和 Git checkpoint 在 evaluator
调用前后必须保持相同。

### 唯一 evaluator 调用与结果验证

只有全部 pre-evaluator checks 和 drift checks 通过后，才允许恰好一次：

```python
result = evaluate_task_size_gate(evidence=evidence)
```

不得 monkeypatch、retry、fallback、调用第二次、使用本地 classifier、修补
result、忽略 reason code 或更新冻结工单。返回值必须是 exact
`TaskSizeGateResult`，并且全部字段、strict types、枚举、ordered unique
`reason_codes` 与冻结 planning result 完全相等。reason code 组合必须使用上述
production 常量并满足 JLGO planning contract；未知、缺失、重复、乱序、额外或
与 TaskSize、Task decision、ModelGate、Supervisor eligibility 矛盾的组合均阻断。

`STOP_UNCERTAIN` 或 `SPLIT_REQUIRED` 不得进入写操作。只有 exact
`ALLOW_SINGLE_WORK_ORDER` 且当前调用方、ModelGate 和显式 Pro 授权与冻结工单
一致时，才可在原用户批准范围内继续。`NOT_ELIGIBLE` 只禁止 Supervisor 自动
闭环，不禁止用户已经显式批准的 `jl-develop` 工单。

evaluator unavailable、exception、invalid result、planning/result drift 或调用后
Git/evidence 变化，统一返回 pre-write contract 第 10 节的一个固定、净化后
`PRE_WRITE_*` 阻断类别并停止；这些 workflow 类别不得放入
`TaskSizeGateResult.reason_codes`。不得输出异常文本、traceback、绝对路径、环境值
或 raw user content。

checkpoint 通过只表示当前已批准工单可以继续，不是新用户批准，也不自动执行
branch、write、Skill、commit、push、merge、tag、部署或 activation。

本节不实现 `jl-supervisor` recovery、`jl-review` checkpoint、test tooling、CI、
MT4、reader、EA、交易或执行能力。

## 下一步操作卡

开发或修订工单结束后必须输出：

```text
【下一步操作卡】
1. 当前状态：
2. 下一步要做什么：
3. 是否需要用户显式批准：
4. 模型要求：
5. 下一 Skill：
6. 可直接复制发送给 Codex 的完整指令：
```

映射规则：

- 开发成功、commit 并 push 工作分支后，`下一 Skill` 写 `$jl-review`。
- checkpoint 异常、工作区不干净、测试失败、commit 失败或 push 失败时，`下一 Skill` 写 `无`，或在需要重新规划时写 `$jlgo`。
- 完整指令必须要求只读验收，不得要求 merge、tag 或进入下一业务工单。
- 完整指令必须只调用一个 Skill，并要求下一轮结束时继续输出新的【下一步操作卡】。
- 不得通过操作卡自动调用 `$jl-review`；必须等待用户显式批准。
