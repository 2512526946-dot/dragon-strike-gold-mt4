# TradePlan Schema Contract

本文定义未来智能体输出 TradePlan 的文档结构和示例字段。当前阶段只定义格式，不生成 TradePlan，不写策略，不执行交易，不实现任何代码。

## 定位

TradePlan 是智能体未来输出的交易计划候选对象。它只能作为 demo-only 路线中后续安全闸门的输入。

TradePlan 必须明确：

- TradePlan 是智能体未来输出的交易计划。
- TradePlan 不是订单。
- TradePlan 不是交易许可。
- TradePlan 不是真实交易建议。
- TradePlan 不能直接发送给 EA。
- TradePlan 不能绕过 DataQualityGate / RiskGate / PositionSizing / ExecutionGate。
- TradePlan 只能在 demo-only 路线中作为后续闸门检查输入。
- 当前阶段只定义格式，不生成 TradePlan，不写策略，不执行交易。

## 检查链路

未来 TradePlan 必须按以下链路检查：

```text
TradePlan created
↓
DataQualityGate checks market/account data
↓
RiskGate checks risk state
↓
PositionSizing calculates lot and max loss
↓
ExecutionGate decides whether EA command may be sent
↓
ManualConfirmFlow confirms user intent / or AutoDemoTrainingMode later
↓
Demo EA execution only if all gates pass
```

任何一层失败，TradePlan 都不得进入执行阶段。即使所有闸门通过，也只代表可以进入 demo account 的受控执行准备，不代表实盘许可。

## 字段规则

TradePlan 字段规则：

- `schema_version` 表示格式版本。
- `record_type` 必须为 `trade_plan`。
- `trade_plan_id` 必须能唯一标识本计划。
- `created_at` 必须使用 ISO 8601 时间。
- `symbol` 示例为 `XAUUSD`。
- `account_mode` 必须为 `demo_only`。
- `source` 示例为 `dragon_strike_agent`。
- `plan_mode` 示例为 `demo_training_candidate`。
- `direction` 只能使用候选表达，例如 `long_candidate`、`short_candidate`、`neutral_candidate`。
- 不允许使用 `should_buy` / `should_sell` / `can_trade` / `allow_trade` 字段。
- TradePlan 中的 `suggested_lot` 必须允许为 `null`。
- 最终手数必须由 PositionSizing 计算，不得由智能体直接决定。
- `max_loss_amount` 可以先为 `null`，最终必须由 PositionSizing 计算。
- `stop_loss_price` 必须存在，否则未来 RiskGate / ExecutionGate 必须阻断。
- `required_gates` 必须全部为 `true`。
- `safety_flags.is_order` 必须为 `false`。
- `safety_flags.is_tradable` 必须为 `false`。
- `safety_flags.is_real_trade` 必须为 `false`。
- `safety_flags.is_auto_trade` 必须为 `false`。
- `safety_flags.demo_only` 必须为 `true`。
- `note` 必须明确不是订单、不是交易建议、不是交易许可、不是实盘交易、不是自动交易。

## 最小结构

TradePlan 示例结构见 `trade_plan.example.json`。示例只用于格式说明，不得被当作真实交易建议、交易信号、交易许可或自动执行命令。

关键结构包括：

- 顶层元数据：`schema_version`、`record_type`、`trade_plan_id`、`created_at`。
- 计划范围：`symbol`、`account_mode`、`source`、`plan_mode`、`direction`。
- 周期依据：`timeframe_basis`、`confirmation_timeframe`。
- 市场上下文：`market_context`。
- 入场计划候选：`entry_plan`。
- 风险请求：`risk_request`。
- 必需闸门：`required_gates`。
- 智能体摘要：`agent_reasoning_summary`。
- 安全标记：`safety_flags`。
- 安全说明：`note`。

## Entry Plan 边界

`entry_plan` 只能描述候选计划，不是下单命令。

`entry_plan` 可以包含：

- `entry_type`
- `entry_price`
- `entry_zone_low`
- `entry_zone_high`
- `stop_loss_price`
- `take_profit_price`
- `invalidation_condition`

`entry_plan` 必须遵守：

- `entry_price` 不是执行价格承诺。
- `take_profit_price` 不是收益承诺。
- `stop_loss_price` 必须存在，否则后续 RiskGate / ExecutionGate 必须阻断。
- `invalidation_condition` 只能是说明文本，不得成为自动交易触发器。

## Risk Request 边界

`risk_request` 是给 PositionSizing 的输入候选，不是最终仓位。

`risk_request` 可以包含：

- `suggested_risk_percent`
- `max_risk_percent`
- `max_loss_amount`
- `suggested_lot`
- `requires_position_sizing`

`risk_request` 必须遵守：

- `suggested_risk_percent` 不得突破系统风险上限。
- `max_risk_percent` 只是候选上限，RiskGate 可以进一步降低或拒绝。
- `max_loss_amount` 可以为 `null`，最终必须由 PositionSizing 计算。
- `suggested_lot` 必须允许为 `null`。
- 最终手数必须由 PositionSizing 计算。
- 智能体不得直接决定最终手数。

## Required Gates

`required_gates` 必须全部为 `true`：

- `data_quality_gate_required`
- `risk_gate_required`
- `position_sizing_required`
- `execution_gate_required`
- `manual_confirm_required`

这些字段表达必须经过安全链路，不是交易许可，也不是执行许可。

## Safety Flags

`safety_flags` 必须明确安全状态：

- `is_order: false`
- `is_tradable: false`
- `is_real_trade: false`
- `is_auto_trade: false`
- `demo_only: true`
- `requires_user_confirmation: true`
- `requires_execution_gate: true`

这些字段不得被前端或后端解释为可以交易。它们用于阻止误读和越权执行。

## 与其他对象的关系

TradePlan 可以关联 `observation_signal_id`，也可以在未来产生 `execution_audit_id`。

TradePlan 与其他对象的关系：

- TradePlan 不等于 observation_signal。
- TradePlan 不等于 paper_review_result。
- TradePlan 不等于 manual_execution_event。
- TradePlan 不等于 MT4 order。
- TradePlan 不等于真实交易记录。
- TradePlan 可以作为 ExecutionAuditLog 的输入来源之一。
- TradePlan 可以被 RiskGate、PositionSizing、ExecutionGate 引用。

## 安全边界

TradePlan 必须遵守：

- 智能体不能直接执行 TradePlan。
- 智能体不能修改风险比例上限。
- 智能体不能修改 PositionSizing 结果。
- 智能体不能绕过用户确认。
- 智能体不能开启 AutoDemoTrainingMode。
- TradePlan 不能用于 live account。
- TradePlan 不能包含账号密码。
- TradePlan 不能包含登录凭证。
- TradePlan 不能直接驱动 EA。

TradePlan 只能在 demo-only 路线中作为后续闸门检查输入。任何 live account、真实资金、实盘执行、自动交易执行都不在当前阶段范围内。

## 本轮不实现

本轮只新增文档和示例 JSON，不实现任何代码。

本轮不实现：

- 不实现 TradePlanSchema 代码。
- 不实现 RiskGate 代码。
- 不实现 PositionSizing 代码。
- 不实现 ExecutionGate 代码。
- 不实现 ExecutionAuditLog 代码。
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

