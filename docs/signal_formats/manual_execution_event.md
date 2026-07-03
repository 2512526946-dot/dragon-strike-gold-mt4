# manual_execution_event.jsonl 人工执行标记日志格式

本文定义未来用户对 `observation_signal` 的人工执行标记日志格式。当前阶段只定义格式，不实现执行记录写入逻辑、不新增后端 API、不修改前端页面、不接入真实 MT4 或真实账户。

## 文件用途

`manual_execution_event.jsonl` 用于记录用户对观察信号的人工执行标记，例如未执行、跳过、仅纸面观察、晚进场、提前进场、没有等待确认或人工标记无效。

该日志用于复盘用户执行行为、纪律问题和信号执行差异。它不是 MT4 真实成交记录，不是订单记录，不是真实 ticket，不记录真实 PnL，不代表系统允许交易，也不会触发任何自动交易。

## 路径约定

未来运行时路径建议为：

```text
data/signals/manual_execution_event.jsonl
```

该路径属于未来运行时日志目录。本轮不得创建或提交真实运行日志。

示例文件路径为：

```text
docs/signal_formats/manual_execution_event.example.jsonl
```

## JSONL 规则

- 一行一个 JSON object。
- 不允许多行 JSON object。
- 每行必须能独立解析。
- 文件适合追加写入。
- 文件适合后续复盘、纪律分析和执行差异分析。

每一行都必须包含 `record_type="manual_execution_event"`，并通过 `signal_id` 关联一条 `observation_signal`。

## 与 observation_signal 的关系

- `manual_execution_event` 必须通过 `signal_id` 关联 `observation_signal`。
- 一个 `observation_signal` 可以有 0 个或多个 `manual_execution_event`。
- 多个事件可记录用户后续修正、补充标记或执行纪律复盘。

该日志只记录用户对观察信号的人工标记，不表示系统生成了新的交易信号。

## 与 paper_review_result 的区别

`paper_review_result` 记录观察信号后续行情表现，例如纸面 TP 是否先于 SL、是否假突破、最大纸面浮盈和最大纸面反向波动。

`manual_execution_event` 记录用户是否执行、如何执行、是否跳过、是否晚进场、是否提前进场，以及是否遵守系统状态或确认条件。

两者都不等于真实交易 PnL，也都不代表系统允许交易。

## 与真实 MT4 成交记录的区别

`manual_execution_event` 不是 MT4 订单，不是真实 ticket，不是真实成交流水，不是真实账户记录。当前阶段不读取真实成交记录，不读取真实账户，也不连接真实 MT4。

如果未来扩展 `manually_executed_real_future_only`，它只能作为未来人工标记枚举，不代表当前阶段支持实盘交易，也不代表系统具备自动交易能力。

## user_action 枚举

建议枚举：

- `not_executed`：用户未执行观察信号。
- `skipped`：用户主动跳过观察信号。
- `paper_only`：用户只进行纸面观察。
- `manually_executed_demo`：未来可用于标记用户在模拟账户中人工执行。
- `manually_executed_real_future_only`：仅作为未来扩展标记，当前阶段不支持实盘交易。
- `late_entry`：用户晚于参考条件人工进入观察。
- `early_entry`：用户早于确认条件人工进入观察。
- `entered_without_confirmation`：用户未等待确认即人工进入观察。
- `manually_invalidated`：用户人工标记观察信号无效。

这些枚举只用于复盘用户行为和纪律差异，不是交易建议，不是交易许可，不是自动交易指令。

## 字段说明

核心字段：

- `schema_version`：格式版本。
- `record_type`：固定为 `manual_execution_event`。
- `event_id`：人工执行标记事件唯一标识。
- `signal_id`：关联的观察信号标识。
- `created_at`：事件记录时间。
- `symbol`：交易品种示例为 `XAUUSD`。
- `source`：来源，示例为 `user_manual_mark`。
- `signal_mode`：固定为 `observation_only`。
- `user_action`：用户人工标记枚举。
- `execution`：人工执行标记详情。
- `discipline_review`：执行纪律和偏差复盘字段。
- `is_tradable`：必须为 `false`。
- `is_real_trade`：必须为 `false`。
- `is_auto_trade`：必须为 `false`。
- `note`：必须明确说明不是订单、不是真实 PnL、不是交易建议、不是交易许可、不是自动交易。

`execution` 字段：

- `execution_mode`：当前阶段固定为 `observation_only`，未来扩展必须单独评审。
- `executed_by_user`：用户是否人工执行或标记为已执行。
- `execution_channel`：执行或标记渠道，例如 `none`、`paper_review`、`manual_demo_mark`。
- `manual_entry_time`：人工进场标记时间；未执行时为 `null`。
- `manual_entry_price`：人工进场标记价格；未执行时为 `null`。
- `manual_lot`：人工标记手数；未执行或仅纸面时为 `null`。
- `real_trade_id`：必须为 `null`。
- `real_pnl`：必须为 `null`。

`discipline_review` 字段：

- `followed_system_state`：是否遵守系统状态或观察条件。
- `violated_system_state`：是否违反系统状态或观察条件。
- `entry_timing_label`：进场时机标签，例如 `not_applicable`、`paper_only`、`late_entry`。
- `position_size_label`：仓位纪律标签；当前阶段不计算仓位。
- `discipline_note`：人工执行行为复盘说明。

禁止作为业务字段使用：

- `can_trade`
- `allow_trade`
- `should_buy`
- `should_sell`
- `suggested_lot`
- 真实订单 `ticket`

## 安全边界

- 不自动下单。
- 不生成真实交易建议。
- 不记录真实交易盈亏。
- 不绕过 DataQualityGate。
- 不绕过人工决策。
- 不代表 GoLiveGate 或 AutoTradeGate 通过。
- 不开发 MT4 EA。
- 不开发 MQL4 交易代码。
- 不包含 OrderSend、OrderClose、OrderModify、OrderDelete 执行逻辑。
- 不实现信号生成引擎。
- 不实现纸面复盘计算引擎。
- 不实现执行记录写入逻辑。
- 不实现风控计算。
- 不实现仓位计算。
- 不训练机器学习模型。
- 不生成模型文件。

该格式只定义未来人工执行标记日志结构，不新增后端 API、不修改前端页面、不接真实 MT4、不接真实行情、不读取真实账户、不提交真实人工执行日志。
