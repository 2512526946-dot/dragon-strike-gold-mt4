# DemoOpenPositionsAndOrderHistory Schema Contract

本文定义未来 MT4 demo account 第一阶段只读连接时的当前持仓明细与订单历史摘要/明细数据契约和示例 JSON。当前阶段只定义格式，不实现读取逻辑，不接 MT4，不写 EA，不写 API。

## 定位

DemoOpenPositionsAndOrderHistory 是未来 MT4 demo-only 只读阶段的持仓与订单历史快照。它只用于读取模拟账号持仓和历史订单状态，并作为后续只读展示、风险状态判断、执行审计和复盘训练数据积累的输入之一。

DemoOpenPositionsAndOrderHistory 必须明确：

- DemoOpenPositionsAndOrderHistory 是未来 MT4 demo-only 只读阶段的持仓与订单历史快照。
- DemoOpenPositionsAndOrderHistory 只用于读取模拟账号持仓和历史订单状态。
- DemoOpenPositionsAndOrderHistory 不是交易信号。
- DemoOpenPositionsAndOrderHistory 不是交易计划。
- DemoOpenPositionsAndOrderHistory 不是交易许可。
- DemoOpenPositionsAndOrderHistory 不触发 EA 执行。
- DemoOpenPositionsAndOrderHistory 不保存账号密码。
- DemoOpenPositionsAndOrderHistory 不保存登录凭证。
- DemoOpenPositionsAndOrderHistory 不允许 live account。
- 当前阶段只定义格式，不实现读取逻辑，不接 MT4，不写 EA，不写 API。

## 数据用途

该快照未来用于：

- 只读展示当前持仓。
- 只读展示今日订单历史。
- 帮助 RiskGate 判断是否已有持仓冲突。
- 帮助 RiskGate 统计今日交易次数。
- 帮助 RiskGate 统计连续亏损次数。
- 帮助 RiskGate 判断今日已实现盈亏。
- 帮助 RiskGate 检查是否存在无止损持仓。
- 帮助 ExecutionAuditLog 记录执行前账号状态。
- 帮助复盘系统理解模拟账号行为。

同时必须明确：

- 当前不实现 RiskGate。
- 当前不实现 ExecutionGate。
- 当前不实现 reader。
- 当前不实现 API。
- 当前不执行任何交易。
- 当前不接账号。

## 最小结构

DemoOpenPositionsAndOrderHistory 示例结构见 `demo_positions_order_history.example.json`。示例只用于格式说明，不得被当作交易信号、交易计划、交易许可、订单指令、EA 命令或自动交易记录。

关键结构包括：

- 顶层元数据：`schema_version`、`record_type`、`generated_at`、`source`、`account_mode`。
- 只读模拟账号摘要：`demo_account`。
- 当前持仓摘要：`open_positions_summary`。
- 当前持仓明细：`open_positions`。
- 今日订单历史摘要：`order_history_summary`。
- 已关闭订单明细：`closed_orders`。
- 只读风控特征能力说明：`risk_readonly_features`。
- 桥接状态：`bridge_status`。
- 安全标记：`safety_flags`。
- 安全说明：`note`。

## 字段规则

DemoOpenPositionsAndOrderHistory 字段规则：

- `record_type` 必须为 `demo_positions_order_history`。
- `account_mode` 必须为 `demo_only`。
- `demo_account.is_demo_account` 必须为 `true`。
- `demo_account.is_live_account` 必须为 `false`。
- `demo_account.account_number` 当前示例必须为 `null`，避免提交真实账号。
- 不允许包含账号密码。
- 不允许包含登录凭证。
- `order_ref` / `position_ref` 只能是脱敏引用，不是真实敏感凭证。
- `safety_flags.demo_only` 必须为 `true`。
- `safety_flags.is_tradable` 必须为 `false`。
- `safety_flags.can_execute` 必须为 `false`。
- `safety_flags.contains_credentials` 必须为 `false`。
- `safety_flags.contains_password` 必须为 `false`。
- `safety_flags.contains_live_account` 必须为 `false`。
- `note` 必须明确只读模拟账号数据、不是交易建议、不是交易许可、不是订单指令、不是自动交易。

## Demo Account

`demo_account` 只记录模拟账号的只读身份摘要，不记录登录凭证，不记录账号密码，不记录可泄露账号安全的信息。

建议字段包括：

- `is_demo_account`
- `is_live_account`
- `account_alias`
- `account_number`
- `currency`

`account_number` 在示例和文档阶段必须为 `null`。未来如确需标识账号，也应使用不可逆别名或本地映射，不得提交真实账号。

## Open Positions

`open_positions_summary` 和 `open_positions` 用于只读展示当前模拟账号持仓状态。

建议摘要字段包括：

- `open_positions_count`
- `xauusd_positions_count`
- `long_positions_count`
- `short_positions_count`
- `total_lots`
- `floating_pnl`
- `has_position_conflict`

建议持仓明细字段包括：

- `position_ref`
- `symbol`
- `direction`
- `lot`
- `open_price`
- `current_bid`
- `current_ask`
- `stop_loss`
- `take_profit`
- `floating_pnl`
- `swap`
- `commission`
- `opened_at`
- `comment`

这些字段只用于只读展示和未来风险状态判断，不得被解释为自动平仓、自动加仓、自动修改止损或自动交易指令。

## Order History

`order_history_summary` 和 `closed_orders` 用于只读展示今日订单历史和复盘上下文。

建议摘要字段包括：

- `history_window`
- `orders_count`
- `closed_orders_count`
- `winning_orders_count`
- `losing_orders_count`
- `consecutive_losses`
- `today_closed_pnl`
- `today_commission`
- `today_swap`
- `last_closed_order_time`

建议已关闭订单明细字段包括：

- `order_ref`
- `symbol`
- `direction`
- `lot`
- `open_price`
- `close_price`
- `stop_loss`
- `take_profit`
- `opened_at`
- `closed_at`
- `closed_pnl`
- `swap`
- `commission`
- `close_reason`
- `comment`

`order_ref` 只能是脱敏引用。该字段不得保存真实订单票号、账号密码、登录凭证或任何可连接真实账户的敏感信息。

## Risk Readonly Features

`risk_readonly_features` 只描述该快照未来可支持哪些只读风险判断输入，不表示当前已实现 RiskGate，也不表示系统允许执行。

建议字段包括：

- `can_detect_open_position_conflict`
- `can_count_daily_trades`
- `can_count_consecutive_losses`
- `can_compute_today_closed_pnl`
- `can_detect_missing_stop_loss`

这些字段是能力声明，不是交易许可，不是执行许可，也不是策略结果。

## Bridge Status

`bridge_status` 用于记录未来只读桥接状态：

- `read_only`
- `last_update_age_seconds`
- `data_freshness_status`
- `bridge_status_code`

`bridge_status.read_only` 必须为 `true`。数据过期时未来必须阻断，不得继续执行任何计划。

## 安全边界

DemoOpenPositionsAndOrderHistory 必须遵守：

- 该快照不能直接驱动交易。
- 该快照不能作为执行许可。
- 该快照不能证明可以下单。
- 该快照不能用于 live account。
- live account 检测到时未来必须阻断。
- 数据过期时未来必须阻断。
- 持仓缺少 stop_loss 时未来必须阻断新执行。
- 今日交易次数达到限制时未来必须阻断。
- 连续亏损达到限制时未来必须阻断。
- 任何执行都必须经过 DataQualityGate / RiskGate / PositionSizing / ExecutionGate。
- 第一阶段只读，不执行。

## 与后续模块关系

该快照未来可作为以下模块的输入之一：

- RiskGate：识别持仓冲突、日内交易次数、连续亏损、已实现盈亏、缺少止损等风险状态。
- ExecutionAuditLog：记录执行前账号持仓与历史订单上下文。
- 复盘系统：理解模拟账号行为和训练样本来源。

该快照不负责：

- 不生成交易方向。
- 不生成交易理由。
- 不计算仓位。
- 不计算风险。
- 不决定是否执行。
- 不绕过 DataQualityGate / RiskGate / PositionSizing / ExecutionGate。

## 本轮不实现

本轮只新增文档和示例 JSON，不实现任何代码。

本轮不实现：

- 不实现 MT4 EA。
- 不实现 MQL4。
- 不接入 MT4 模拟账号。
- 不接入真实 MT4。
- 不保存账号密码。
- 不保存登录凭证。
- 不实现后端 reader。
- 不新增后端 API。
- 不修改前端页面。
- 不新增交易策略。
- 不新增 TradePlanSchema 代码。
- 不新增 ExecutionAuditLog 代码。
- 不新增 RiskGate 代码。
- 不新增 PositionSizing 代码。
- 不新增 ExecutionGate 代码。
- 不新增执行 API。
- 不新增自动交易。
- 不返回任何真实交易建议。
