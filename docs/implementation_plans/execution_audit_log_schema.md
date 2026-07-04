# ExecutionAuditLog Schema Contract

本文定义未来 ExecutionAuditLog 的文档结构和示例字段。当前阶段只定义格式，不实现写入逻辑，不实现 API，不接 MT4，不执行交易。

## 定位

ExecutionAuditLog 是未来 demo-only 执行尝试的审计记录。它用于记录执行前检查、执行许可、用户确认、EA 返回结果和拒绝原因。

ExecutionAuditLog 必须明确：

- ExecutionAuditLog 是未来 demo-only 执行尝试的审计记录。
- ExecutionAuditLog 用于记录执行前检查、执行许可、用户确认、EA 返回结果和拒绝原因。
- ExecutionAuditLog 不是订单。
- ExecutionAuditLog 不是 MT4 ticket。
- ExecutionAuditLog 不是真实成交记录。
- ExecutionAuditLog 不是真实 PnL 记录。
- ExecutionAuditLog 不保存账号密码。
- ExecutionAuditLog 不保存登录凭证。
- ExecutionAuditLog 不代表系统允许实盘交易。
- 当前阶段只定义格式，不实现写入逻辑，不实现 API，不接 MT4，不执行交易。

## 最小结构

ExecutionAuditLog 示例结构见 `execution_audit_log.example.json`。示例只用于格式说明，不得被当作订单、MT4 ticket、真实成交记录、真实 PnL、交易建议、交易许可或自动交易记录。

关键结构包括：

- 顶层元数据：`schema_version`、`record_type`、`audit_id`、`trade_plan_id`、`created_at`。
- 执行范围：`symbol`、`account_mode`、`execution_mode`、`source`。
- TradePlan 摘要：`trade_plan_snapshot`。
- 闸门结果：`gate_results`。
- 用户确认：`manual_confirm`。
- 自动模拟训练状态：`auto_demo_training`。
- EA 命令状态：`ea_command`。
- EA 返回结果：`ea_result`。
- 最终决策：`final_decision`。
- 安全标记：`safety_flags`。
- 安全说明：`note`。

## 字段规则

ExecutionAuditLog 字段规则：

- `record_type` 必须为 `execution_audit_log`。
- `account_mode` 必须为 `demo_only`。
- `trade_plan_id` 必须存在，用于关联 TradePlan。
- `audit_id` 必须唯一。
- ExecutionAuditLog 可以记录被阻断的执行尝试。
- 被阻断时 `ea_command.command_sent` 必须为 `false`。
- 被阻断时 `ea_result.executed` 必须为 `false`。
- `ea_command_allowed=false` 时不得发送 EA 命令。
- `manual_confirm.user_confirmed=false` 时不得执行 `manual_confirm_demo`。
- `auto_demo_training.enabled` 默认必须为 `false`。
- `safety_flags.contains_credentials` 必须为 `false`。
- `safety_flags.contains_password` 必须为 `false`。
- `safety_flags.contains_real_pnl` 必须为 `false`。
- `note` 必须明确不是订单、不是真实 PnL、不是交易建议、不是交易许可、不是自动交易。

## Gate Results

`gate_results` 用于记录各安全闸门的检查状态，而不是重新计算或修改结果。

`gate_results` 至少包含：

- `data_quality_gate`
- `risk_gate`
- `position_sizing`
- `execution_gate`

每个 gate 结果应该说明：

- 是否执行检查。
- 是否通过。
- 状态码。
- 阻断原因。
- 警告原因。
- 与本 gate 相关的只读摘要。

ExecutionAuditLog 不能修改 DataQualityGate、RiskGate、PositionSizing 或 ExecutionGate 的结果，只能记录它们的输出。

## Manual Confirm

`manual_confirm` 用于记录用户确认状态。

字段建议：

- `required`
- `user_confirmed`
- `confirmed_at`
- `confirmation_source`

如果 `manual_confirm.required=true` 且 `manual_confirm.user_confirmed=false`，则不得发送 EA 命令，不得执行 `manual_confirm_demo`。

## Auto Demo Training

`auto_demo_training` 用于记录 AutoDemoTrainingMode 状态。

字段建议：

- `enabled`
- `allowed`
- `reason`

AutoDemoTrainingMode 默认必须关闭。关闭时不得自动执行，不得发送 EA 命令。

## EA Command 与 EA Result

`ea_command` 只记录命令是否创建、是否发送，以及相关时间和 ID。它不是 EA 命令本身，也不得包含账号密码、登录凭证或可泄露账号安全的信息。

`ea_result` 只记录 EA 是否返回、是否在 demo account 中执行、demo 订单标识和错误信息。

如果执行在任何 gate 被阻断：

- `ea_command.command_created` 必须为 `false`。
- `ea_command.command_sent` 必须为 `false`。
- `ea_result.received` 必须为 `false`。
- `ea_result.executed` 必须为 `false`。

## 与其他对象的关系

ExecutionAuditLog 通过 `trade_plan_id` 关联 TradePlan。ExecutionAuditLog 可以关联 `observation_signal_id`，但不是必须。

ExecutionAuditLog 与其他对象的关系：

- ExecutionAuditLog 不等于 TradePlan。
- ExecutionAuditLog 不等于 MT4 order。
- ExecutionAuditLog 不等于真实成交记录。
- ExecutionAuditLog 不等于 paper_review_result。
- ExecutionAuditLog 可以为后续复盘提供执行过程证据。
- ExecutionAuditLog 不得直接作为真实 PnL 统计依据。

## 必须审计的场景

未来至少需要记录以下审计场景：

1. DataQualityGate 阻断：不进入 RiskGate / PositionSizing / EA。
2. RiskGate 阻断：不进入 EA。
3. PositionSizing 阻断：不进入 EA。
4. ExecutionGate 阻断：不进入 EA。
5. 用户未确认：不进入 EA。
6. AutoDemoTrainingMode 关闭：不得自动执行。
7. EA 不可用：不得执行。
8. EA 返回失败：记录失败，但不得重试马丁或网格。
9. demo account 不确认：必须阻断。
10. live account 检测到：必须阻断。

这些场景的记录目标是审计安全链路，不是生成交易建议，不是执行重试机制。

## 安全边界

ExecutionAuditLog 必须遵守：

- ExecutionAuditLog 不保存账号密码。
- ExecutionAuditLog 不保存登录凭证。
- ExecutionAuditLog 不保存真实账户敏感信息。
- ExecutionAuditLog 不允许记录可泄露账号安全的信息。
- ExecutionAuditLog 不能驱动交易。
- ExecutionAuditLog 只能记录结果。
- ExecutionAuditLog 不能修改风控结果。
- ExecutionAuditLog 不能修改手数。
- ExecutionAuditLog 不能重试下单。
- ExecutionAuditLog 不能绕过 ExecutionGate。
- ExecutionAuditLog 不适用于 live account。

ExecutionAuditLog 不能被任何智能体或 UI 当成执行许可。它只是一条审计记录。

## 本轮不实现

本轮只新增文档和示例 JSON，不实现任何代码。

本轮不实现：

- 不实现 ExecutionAuditLog 代码。
- 不实现 TradePlanSchema 代码。
- 不实现 RiskGate 代码。
- 不实现 PositionSizing 代码。
- 不实现 ExecutionGate 代码。
- 不实现后端 API。
- 不实现前端确认按钮。
- 不实现 MT4 EA。
- 不实现 MQL4。
- 不接入 MT4 模拟账号。
- 不接入真实 MT4。
- 不保存账号密码。
- 不保存登录凭证。
- 不新增交易策略。
- 不新增自动交易。
- 不返回任何真实交易建议。

