# DemoAccountReadOnlySnapshot Schema Contract

本文定义未来 MT4 demo account 第一阶段只读连接时的账号快照数据契约和示例 JSON。当前阶段只定义格式，不实现读取逻辑，不接 MT4，不写 EA，不写 API。

## 定位

DemoAccountReadOnlySnapshot 是未来 MT4 demo-only 只读阶段的账号快照。它只用于读取模拟账号状态，并作为后续只读展示、数据质量检查和复盘上下文的输入之一。

DemoAccountReadOnlySnapshot 必须明确：

- DemoAccountReadOnlySnapshot 是未来 MT4 demo-only 只读阶段的账号快照。
- DemoAccountReadOnlySnapshot 只用于读取模拟账号状态。
- DemoAccountReadOnlySnapshot 不是交易信号。
- DemoAccountReadOnlySnapshot 不是交易计划。
- DemoAccountReadOnlySnapshot 不是交易许可。
- DemoAccountReadOnlySnapshot 不触发 EA 执行。
- DemoAccountReadOnlySnapshot 不保存账号密码。
- DemoAccountReadOnlySnapshot 不保存登录凭证。
- DemoAccountReadOnlySnapshot 不允许 live account。
- 当前阶段只定义格式，不实现读取逻辑，不接 MT4，不写 EA，不写 API。

## 数据用途

该快照未来用于：

- 验证 MT4Bridge 只读数据通道。
- 验证 demo-only 模式。
- 验证 DataQualityGate。
- 显示前端只读账号状态。
- 复盘时辅助理解模拟账号状态。
- 作为后续 RiskGate / PositionSizing 的输入来源之一。

同时必须明确：

- 当前不实现 RiskGate / PositionSizing。
- 当前不实现 ExecutionGate。
- 当前不执行任何交易。
- 当前不写入真实日志。
- 当前不接账号。

## 最小结构

DemoAccountReadOnlySnapshot 示例结构见 `demo_account_readonly_snapshot.example.json`。示例只用于格式说明，不得被当作交易信号、交易计划、交易许可、订单、EA 命令或自动交易记录。

关键结构包括：

- 顶层元数据：`schema_version`、`record_type`、`generated_at`、`source`、`account_mode`。
- 只读账号摘要：`demo_account`。
- 品种快照：`symbol_snapshot`。
- 当前持仓摘要：`positions_summary`。
- 当前持仓示例：`open_positions`。
- 订单历史摘要：`order_history_summary`。
- 桥接状态：`bridge_status`。
- 安全标记：`safety_flags`。
- 安全说明：`note`。

## 字段规则

DemoAccountReadOnlySnapshot 字段规则：

- `record_type` 必须为 `demo_account_readonly_snapshot`。
- `account_mode` 必须为 `demo_only`。
- `demo_account.is_demo_account` 必须为 `true`。
- `demo_account.is_live_account` 必须为 `false`。
- `demo_account.account_number` 当前示例必须为 `null`，避免提交真实账号。
- 不允许包含账号密码。
- 不允许包含登录凭证。
- `safety_flags.demo_only` 必须为 `true`。
- `safety_flags.is_tradable` 必须为 `false`。
- `safety_flags.can_execute` 必须为 `false`。
- `safety_flags.contains_credentials` 必须为 `false`。
- `safety_flags.contains_password` 必须为 `false`。
- `safety_flags.contains_live_account` 必须为 `false`。
- `note` 必须明确只读模拟账号数据、不是交易建议、不是交易许可、不是订单、不是自动交易。

## Demo Account

`demo_account` 只记录模拟账号状态摘要，不记录登录凭证，不记录账号密码，不记录可泄露账号安全的信息。

建议字段包括：

- `is_demo_account`
- `is_live_account`
- `account_alias`
- `account_number`
- `server_name`
- `currency`
- `balance`
- `equity`
- `margin`
- `free_margin`
- `margin_level`
- `today_realized_pnl`
- `today_floating_pnl`

`account_number` 在示例和文档阶段必须为 `null`。未来如确需标识账号，也应使用不可逆别名或本地映射，不得提交真实账号。

## Symbol Snapshot

`symbol_snapshot` 用于记录只读行情快照：

- `symbol`
- `bid`
- `ask`
- `spread`
- `spread_points`
- `digits`
- `last_tick_time`

这些字段只用于行情上下文和数据质量检查，不是交易信号，不是交易许可，不触发 EA。

## Positions Summary

`positions_summary` 和 `open_positions` 用于只读展示模拟账号状态。

它们不得被解释为自动平仓、自动加仓或自动交易指令。任何未来执行都必须重新经过 DataQualityGate / RiskGate / PositionSizing / ExecutionGate。

## Bridge Status

`bridge_status` 用于记录只读桥接状态：

- `read_only`
- `last_update_age_seconds`
- `data_freshness_status`
- `bridge_status_code`

`bridge_status.read_only` 必须为 `true`。数据过期时未来必须阻断，不得继续执行任何计划。

## 安全边界

DemoAccountReadOnlySnapshot 必须遵守：

- 该快照不能直接驱动交易。
- 该快照不能作为执行许可。
- 该快照不能证明可以下单。
- 该快照不能用于 live account。
- live account 检测到时未来必须阻断。
- 数据过期时未来必须阻断。
- 没有 equity 时未来必须阻断。
- 没有 stop_loss 时未来不得执行任何计划。
- 任何执行都必须经过 DataQualityGate / RiskGate / PositionSizing / ExecutionGate。
- 第一阶段只读，不执行。

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

