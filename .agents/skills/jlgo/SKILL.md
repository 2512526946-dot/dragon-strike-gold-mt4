---
name: jlgo
description: Read-only project router and planner for the 巨龙出击 repository. Use when the user says continue, next step, status, plan, or asks what to do. Inspect Git and repository evidence, choose exactly one next action, and produce the next command or work order. Never modify files, branches, commits, tags, or the working tree.
---

# 巨龙推进

1. 先读取仓库根目录 `AGENTS.md`。
2. 只读检查工作区、当前分支、`main`、`origin/main`、最近 commits、tags、当前分支相对 `main`、可见 work branches，以及相关 ADR、协议、生产代码和测试基线。
3. 网络可用时可以运行 `git fetch origin --prune --tags`，但不得 checkout、创建或移动分支。
4. 对每个候选工作分支使用 Git ancestry 证据分类，推荐运行：

   ```bash
   git merge-base --is-ancestor <branch-tip> main
   git rev-list --count main..<branch>
   ```

   - 分支 tip 已是 `main` 的 ancestor：视为已合并历史分支并忽略。
   - `main..<branch>` commit 数为 0：视为已合并或没有独立工作并忽略。
   - 只有分支仍包含 `main` 中不存在的 commit，才视为 active unmerged work branch。
   - 已保留但已经合并的 G143、G148、WF-1 等历史工作分支，不得阻止新工单规划。
   - 无法确认 ancestry 时，将状态判定为 checkpoint 异常并停止，不得猜测。
5. 明确区分 policy 已写入 `AGENTS.md`、contract 已定义、tests 已存在、production code 已实现、capability 已接入和 capability 已启用。
6. 不得因为政策已经声明，就声称对应 Gate 或执行能力已经实现。
7. 继续区分 production implementation、tests only、docs only 和 not implemented。
8. 按以下优先级决定唯一下一步：
   - 工作区不干净或 checkpoint 异常：停止。
   - 存在 active unmerged work branch：只建议 review、修订或 merge，不生成新开发工单。
   - 位于干净 `main` 且无待处理分支：规划唯一下一开发工单。
   - 只有用户明确批准 tag 时才建议 release。
9. 下一开发任务需要 Pro 时，输出模型要求后停止，不在低强度下设计关键架构。
10. 每次只输出一个下一动作，不修改文件，不创建分支，不 commit、push、merge 或 tag。

## TaskSizeGate planning checkpoint

只有在第 8 步已经证明当前位于 clean synchronized `main`、没有 active
unmerged work branch，并且一个新开发候选工单已经冻结后，才执行本节。
active work branch 仍只进入 review、revision 或 merge 路径；其他分支、dirty
worktree、main mismatch、ancestry unknown 或目标分支被占用时，不得构造
TaskSizeGate evidence，也不得调用 evaluator。

以
`docs/implementation_plans/task_size_gate_jlgo_planning_integration_contract.md`
为 caller-owned evidence 来源契约。在 `backend` Python runtime 中直接复用：

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

必须创建一个 fresh、frozen、strict `TaskSizeGateEvidence`。字段顺序固定如下，
不得缺失、增加、猜测、从 evaluator result 反推或为了获得 allow 而弱化：

```text
TASK_SIZE_GATE_EVIDENCE_FIELDS_BEGIN
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
TASK_SIZE_GATE_EVIDENCE_FIELDS_END
```

证据必须来自本轮重新读取的 Git、WBS、成熟度、精确文件范围、验证、依赖、
风险和政策事实。用户提供的值只能作为候选，不能替代仓库证据。冻结输入后，
只允许调用一次：

```python
result = evaluate_task_size_gate(evidence=evidence)
```

不得 monkeypatch、retry、创建 fallback classifier、手工覆盖 TaskSize、删除
unknowns、缩小工时或文件范围，也不得使用临时文件、持久状态、环境变量、网络
或新的 adapter 传递 evidence。

返回值必须满足全部安全信封要求：

- `type(result) is TaskSizeGateResult`；
- `task_size` 只能是 strict `str` 的 `XS/S/M/L/XL`，或仅在无法分类时为
  `None`；
- `task_decision`、`model_gate`、`supervisor_eligibility` 必须是生产模块的
  公开枚举值；
- `reason_codes` 必须是非空、无重复、确定顺序的 strict `tuple[str, ...]`，
  且每项和组合都必须匹配生产模块公开常量及 WF-4D 第 8 节；
- evaluator 前后 frozen candidate、evidence 和 Git checkpoint 必须不变。

reason code 只能通过同一生产模块的公开常量验证，不得在 Skill 中另造字符串：
`INPUT_INVALID`、`SIZE_UNCLASSIFIABLE`、`UNKNOWN_EVIDENCE`、
`MODEL_STOP_UNCERTAIN`、`CROSS_PACKAGE_ACTIVATION`、`MULTIPLE_OBJECTIVES`、
`NON_ADJACENT_LAYERS`、`OVERSIZED`、`SINGLE_WORK_ORDER_ALLOWED` 和
`PRO_MODEL_REQUIRED`。blocked result 必须恰好一个 reason，且只能来自
`INPUT_INVALID`、`SIZE_UNCLASSIFIABLE`、`UNKNOWN_EVIDENCE` 或
`MODEL_STOP_UNCERTAIN`；allow result 必须是 `SINGLE_WORK_ORDER_ALLOWED`，并仅
在 Pro 时按顺序追加 `PRO_MODEL_REQUIRED`。split result 的 `reason_codes`
必须精确等于以下生产顺序形成的 tuple：仅在对应 evidence 条件成立时，依次最多一次
包含 `CROSS_PACKAGE_ACTIVATION`、`MULTIPLE_OBJECTIVES`、
`NON_ADJACENT_LAYERS`；随后必须恰好包含一个 `OVERSIZED`，即使前面已经存在
其他 split reason 也不得省略；仅当 ModelGate 为 `PRO_REQUIRED` 时，最后恰好
追加一个 `PRO_MODEL_REQUIRED`，`NORMAL_ALLOWED` 时不得包含它。缺失、重复或
顺序错误的 `OVERSIZED`、未知或额外 reason、以及 `PRO_MODEL_REQUIRED` 与
ModelGate 矛盾，全部视为矛盾结果并固定进入 workflow-level `STOP_UNCERTAIN`，
下一 Skill 为 `无`。

只接受以下确定性结果映射：

- valid TaskSize 或 `None` + `STOP_UNCERTAIN` + `STOP_UNCERTAIN` +
  `NOT_ELIGIBLE`：下一 Skill 为 `无` 并停止；`None` 只允许 size 无法分类；
- `L/XL` + `SPLIT_REQUIRED` + `NORMAL_ALLOWED/PRO_REQUIRED` +
  `NOT_ELIGIBLE`：只返回只读拆分建议，下一 Skill 为 `无`；
- `XS/S` + `ALLOW_SINGLE_WORK_ORDER` + `NORMAL_ALLOWED` + `ELIGIBLE`：
  可以建议用户显式批准 `jl-supervisor`；
- `M` + `ALLOW_SINGLE_WORK_ORDER` + `NORMAL_ALLOWED` + `NOT_ELIGIBLE`：
  可以建议用户显式批准 `jl-develop`；
- `XS/S` + `ALLOW_SINGLE_WORK_ORDER` + `PRO_REQUIRED` +
  `CONDITIONAL_PRO_RESUME`：要求用户确认 Codex Pro 并显式批准有界 Supervisor；
- `M` + `ALLOW_SINGLE_WORK_ORDER` + `PRO_REQUIRED` + `NOT_ELIGIBLE`：
  要求 Codex Pro 并显式批准 `jl-develop`。

module/public interface 不可用、evidence 构造失败、evaluator exception、返回值
不是 exact type、字段类型错误、未知枚举、reason code 未知/重复/乱序/矛盾、
结果组合不在白名单或 Git checkpoint 变化时，统一输出 workflow-level
`STOP_UNCERTAIN`，下一 Skill 为 `无`。错误输出只报告净化后的阻断类别，不得
包含 exception message、traceback、绝对路径、raw user payload、环境值或其他
敏感内容。失败调用不得 fallback、retry 或推荐另一个 Skill。

TaskSizeGate result 只是规划分类，不是用户批准。即使结果为 allow，也不得自动
创建或切换分支、修改文件、调用 Skill、merge、tag、部署、activation、调用 MT4
或产生交易动作。本节只完成 JLGO planning-checkpoint integration；不代表
pre-write/review/CI integration、workflow activation 或 end-to-end verification。

使用固定输出：

```text
【当前 checkpoint】
【已验证能力】
【尚未实现】
【状态判定】
【唯一下一步】
【模型要求】
【下一 Skill】
【一句执行指令】
```

下一步是开发时，额外输出 `【完整候选工单】`。

执行 TaskSizeGate planning checkpoint 时，`【状态判定】` 必须明确报告
TaskSize、Task decision、ModelGate、Supervisor eligibility 和净化后的 reason
codes；任何 blocked 或 invalid result 都不得生成写操作工单。

下一 Skill 只能是 `$jl-develop`、`$jl-review`、`$jl-merge`、`$jl-release` 或 `$jl-supervisor`。输出后停止，不自动调用它。

只有以下条件全部满足时，才可以建议用户显式调用 `$jl-supervisor`：

- 当前是 clean synchronized main；
- 没有 active unmerged work branch；
- 唯一工单精确且能够冻结；
- exact file scope 逐文件明确；
- targeted、regression、full/build、grep、diff 和 commit/push 要求明确；
- ModelGate 可以确定分类；
- 建议不会自动越过 explicit user approval。

`NORMAL_ALLOWED` 可以建议显式启动 Supervisor 的单工单自动闭环。`PRO_REQUIRED` 只能建议用户先切换 Pro，再显式调用 Supervisor 恢复已冻结工单；不得声称已经获得高风险开发、部署或激活授权。`STOP_UNCERTAIN` 不得建议自动闭环，下一 Skill 必须为 `无` 或回到安全的人工澄清。

## 下一步操作卡

固定输出之后必须追加 `【下一步操作卡】`：

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

- 规划开发工单时，`下一 Skill` 写 `$jl-develop`。
- 规划验收工单时，`下一 Skill` 写 `$jl-review`。
- 规划 fast-forward 合并工单时，`下一 Skill` 写 `$jl-merge`。
- 规划已明确批准的 tag-only release 时，`下一 Skill` 写 `$jl-release`。
- 规划满足全部安全条件的单工单自动闭环时，`下一 Skill` 可以写 `$jl-supervisor`。
- checkpoint 异常、工作区不干净、无安全下一步或应停止时，`下一 Skill` 写 `无`。
- 完整指令必须只调用一个 Skill，并要求下一轮结束时继续输出新的【下一步操作卡】。
- 不得通过完整指令自动越过用户批准，不得自动 merge、tag 或进入下一工单。
