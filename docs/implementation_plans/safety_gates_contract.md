# Safety Gates Contract

本文用于定义未来 RiskGate、PositionSizing、ExecutionGate 在 MT4 demo-only 模拟账号训练链路中的职责边界、输入输出、否决权和禁止事项。

当前阶段只做文档约束，不实现任何代码，不接 demo account，不接 live account，不保存凭证，不自动交易。

## 文件用途

该文档是未来模拟账号训练链路的安全闸门契约，用于避免智能体越权、风控被绕过、仓位计算被混用，或 EA 被直接调用。

本契约覆盖：

- RiskGate：判断风险状态是否允许继续。
- PositionSizing：根据账户净值、止损距离、风险比例硬计算手数。
- ExecutionGate：作为最后执行闸门，决定是否允许进入 demo EA 命令发送阶段。
- ExecutionAuditLog：记录执行尝试全过程，保留审计链路。

这些模块未来只服务于 demo-only 模拟训练，不构成实盘许可，不生成真实交易建议。

## 总执行链路

未来任何模拟交易执行都必须按以下链路逐层通过：

```text
智能体生成 TradePlan
↓
DataQualityGate 检查数据质量
↓
RiskGate 检查是否允许进入风险评估
↓
PositionSizing 根据账户净值、止损距离、风险比例硬计算手数
↓
ExecutionGate 做最终执行许可检查
↓
ManualConfirmFlow 用户确认 / 或 AutoDemoTrainingMode 后期打开
↓
MT4 EA 只在 demo account 执行
↓
ExecutionAuditLog 记录全过程
```

任何一层失败，都必须阻断后续执行。四个闸门和确认流程都不等于实盘许可，也不允许绕过。

## 智能体权限边界

智能体只能生成 TradePlan。TradePlan 是待审查计划，不是订单，不是交易许可，也不是 EA 命令。

智能体必须遵守以下边界：

- 智能体只能生成 TradePlan。
- TradePlan 不是订单。
- TradePlan 不是交易许可。
- 智能体不能直接调用 EA。
- 智能体不能修改 RiskGate。
- 智能体不能修改 PositionSizing。
- 智能体不能修改 ExecutionGate。
- 智能体不能绕过 DataQualityGate。
- 智能体不能绕过用户确认。
- 智能体不能开启 AutoDemoTrainingMode。

智能体输出的任何方向、价格或理由都必须被后续闸门视为不可信输入，只有通过完整链路后，才可能进入 demo-only 执行准备阶段。

## RiskGate 职责

RiskGate 未来负责判断风险状态是否允许继续。RiskGate 有否决权，可以阻断任何 TradePlan 进入 PositionSizing 或 ExecutionGate。

RiskGate 至少检查：

- 是否 demo-only。
- 是否 DataQualityGate passed。
- 是否数据过期。
- 是否重大数据窗口。
- 是否今日亏损达到限制。
- 是否连续亏损达到限制。
- 是否已有持仓冲突。
- 是否隔夜风险。
- 是否超过每日交易次数。
- 是否违反禁止马丁 / 禁止网格。
- 是否缺少止损。
- 是否账户净值缺失。
- 是否系统处于暂停状态。

RiskGate 建议输出：

- `risk_gate_passed: true / false`
- `risk_status_code`
- `block_reasons`
- `warning_reasons`
- `max_risk_percent_allowed`
- `must_manual_confirm`

RiskGate 通过只表示可以继续进入风险和仓位计算链路，不代表允许执行，不代表可以发送 EA 命令，更不代表实盘许可。

## PositionSizing 职责

PositionSizing 未来只负责硬计算手数，不负责判断方向，不负责决定是否交易，不负责生成交易理由。

PositionSizing 至少输入：

- `account_equity`
- `risk_percent`
- `entry_price`
- `stop_loss_price`
- `symbol`
- `tick_size`
- `tick_value`
- `contract_size`
- `min_lot`
- `max_lot`
- `lot_step`
- `spread`
- `slippage_buffer`

PositionSizing 至少输出：

- `calculated_lot`
- `rounded_lot`
- `max_loss_amount`
- `risk_percent_used`
- `stop_distance`
- `lot_sizing_status`
- `block_reason`

PositionSizing 必须遵守：

- 没有止损价不得计算通过。
- 没有账户净值不得计算通过。
- 止损距离为 0 或异常不得通过。
- 计算结果低于最小手数且风险超限时不得执行。
- 初期自动 demo 最大手数为 0.01。
- 初期默认风险建议为 0.2% 到 0.3%。
- 单笔最大风险不得超过 1%。
- PositionSizing 不能放大风险。
- PositionSizing 不能被智能体覆盖。

PositionSizing 只能减少或阻断风险，不能提高 RiskGate 给出的风险上限。任何来自智能体的 lot、仓位、风险比例都只能作为候选输入，不能直接覆盖硬计算结果。

## ExecutionGate 职责

ExecutionGate 是最后执行闸门。它负责在任何 demo EA 命令发送前做最终许可检查。

ExecutionGate 至少检查：

- `DemoAccountMode` 是否为 `true`。
- 账户是否确认是 demo。
- DataQualityGate 是否通过。
- RiskGate 是否通过。
- PositionSizing 是否通过。
- TradePlan 是否完整。
- 是否有 `stop_loss_price`。
- 是否有 `calculated_lot`。
- 是否超时。
- 是否用户已手动确认。
- AutoDemoTrainingMode 是否开启。
- 是否达到日交易次数限制。
- 是否连续亏损暂停。
- 是否日亏损暂停。
- 是否隔夜限制。
- 是否重大数据限制。
- 是否 EA 状态正常。

ExecutionGate 建议输出：

- `execution_allowed: true / false`
- `execution_mode: read_only / manual_confirm_demo / auto_demo_training`
- `execution_status_code`
- `block_reasons`
- `audit_required`
- `ea_command_allowed`

ExecutionGate 必须遵守：

- ExecutionGate 可以否决任何交易计划。
- ExecutionGate 通过也只表示可以发送 demo EA 命令。
- ExecutionGate 通过不代表实盘许可。
- ExecutionGate 不得允许真实账户执行。

ExecutionGate 是链路中离执行最近的一层，因此默认应保守。如果有任何字段缺失、状态过期、账户模式不明、用户确认缺失或 EA 状态异常，都必须拒绝执行。

## ExecutionAuditLog 职责

未来每次执行尝试都必须记录 ExecutionAuditLog。记录对象包括被拒绝的尝试、用户未确认的尝试、EA 未发送的尝试，以及最终发送到 demo EA 的尝试。

ExecutionAuditLog 至少记录：

- `trade_plan_id`
- `data_quality_result`
- `risk_gate_result`
- `position_sizing_result`
- `execution_gate_result`
- `user_confirmed`
- `auto_demo_training_enabled`
- `ea_command_sent`
- `ea_result`
- `rejected_reason`
- `created_at`

ExecutionAuditLog 必须遵守：

- 不记录密码。
- 不记录登录凭证。
- 不记录可泄露账号安全的信息。
- 不用于真实 PnL 统计。

ExecutionAuditLog 的目标是审计安全链路和训练流程，不是实盘绩效记录，也不是给出交易建议。

## 状态码建议

以下状态码只是未来接口设计建议，不是代码实现，不是交易建议。

RiskGate 示例：

- `RISK_OK`
- `RISK_BLOCKED_DATA_STALE`
- `RISK_BLOCKED_NO_STOP_LOSS`
- `RISK_BLOCKED_DAILY_LOSS_LIMIT`
- `RISK_BLOCKED_CONSECUTIVE_LOSSES`
- `RISK_BLOCKED_MAJOR_NEWS`
- `RISK_BLOCKED_OVERNIGHT`
- `RISK_BLOCKED_NOT_DEMO_MODE`

PositionSizing 示例：

- `POSITION_SIZE_OK`
- `POSITION_BLOCKED_NO_EQUITY`
- `POSITION_BLOCKED_NO_STOP_LOSS`
- `POSITION_BLOCKED_INVALID_STOP_DISTANCE`
- `POSITION_BLOCKED_MIN_LOT_RISK_TOO_HIGH`
- `POSITION_BLOCKED_LOT_EXCEEDS_LIMIT`

ExecutionGate 示例：

- `EXECUTION_ALLOWED_MANUAL_CONFIRM_DEMO`
- `EXECUTION_ALLOWED_AUTO_DEMO`
- `EXECUTION_BLOCKED_READ_ONLY_MODE`
- `EXECUTION_BLOCKED_NOT_DEMO_ACCOUNT`
- `EXECUTION_BLOCKED_NO_USER_CONFIRM`
- `EXECUTION_BLOCKED_RISK_GATE`
- `EXECUTION_BLOCKED_POSITION_SIZING`
- `EXECUTION_BLOCKED_EA_UNAVAILABLE`
- `EXECUTION_BLOCKED_LIVE_ACCOUNT`

这些状态码只用于描述安全链路状态，不得被解释为买卖建议、交易方向、实盘许可或自动执行承诺。

## 禁止事项

未来实现时仍必须保持以下禁止事项：

- 不允许实盘执行。
- 不允许真实账户执行。
- 不允许保存账号密码。
- 不允许保存登录凭证。
- 不允许智能体直接调用 EA。
- 不允许智能体覆盖 RiskGate。
- 不允许智能体覆盖 PositionSizing。
- 不允许智能体覆盖 ExecutionGate。
- 不允许绕过 DataQualityGate。
- 不允许绕过用户确认。
- 不允许没有止损的计划进入执行。
- 不允许数据过期的计划进入执行。
- 不允许马丁格尔执行逻辑。
- 不允许网格加仓执行逻辑。
- 不允许把状态码解释为交易建议。

## 本轮不实现

本轮只新增文档，不实现任何代码。

本轮不实现：

- 不实现 RiskGate 代码。
- 不实现 PositionSizing 代码。
- 不实现 ExecutionGate 代码。
- 不实现 ExecutionAuditLog。
- 不实现 TradePlanSchema。
- 不实现后端 API。
- 不实现前端确认。
- 不实现 MT4 EA。
- 不实现 MQL4。
- 不接 demo account。
- 不接 live account。
- 不保存凭证。
- 不自动交易。

