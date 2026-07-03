# observation_signal.jsonl 观察信号日志格式

本文定义未来观察信号和纸面复盘信号的 JSONL 日志格式。当前阶段只定义格式，不实现信号生成、不实现写入逻辑、不接入真实行情或真实账户。

## 文件用途

`observation_signal.jsonl` 是未来观察信号日志。它用于记录系统观察到的黄金 XAUUSD 纸面复盘机会，服务于复盘、训练和未来机器学习样本积累。

该文件不是用户真实交易记录，不是订单，不是持仓，不代表用户已执行，也不代表系统允许交易。未执行信号不得计入真实 PnL。

## 路径约定

未来运行时路径建议为：

```text
data/signals/observation_signal.jsonl
```

该路径属于未来运行时日志目录。本轮不得创建或提交真实运行日志。

示例文件路径为：

```text
docs/signal_formats/observation_signal.example.jsonl
```

## JSONL 规则

- 一行一个 JSON object。
- 不允许多行 JSON object。
- 每行必须能独立解析。
- 文件适合追加写入。
- 文件适合后续复盘、样本标注和机器学习样本读取。

每一行都必须包含 `record_type="observation_signal"`，并明确标记为 `signal_mode="observation_only"`。

## 执行状态边界

短期阶段，用户不会真实下单。用户未执行时必须记录：

```text
execution_mode = observation_only
executed_by_user = false
real_pnl = null
```

观察信号只描述纸面复盘候选，不记录真实盈亏，不构成真实交易建议。

## 字段说明

核心字段：

- `schema_version`：格式版本。
- `record_type`：固定为 `observation_signal`。
- `signal_id`：观察信号唯一标识。
- `created_at`：观察信号创建时间。
- `symbol`：交易品种示例为 `XAUUSD`。
- `source`：信号来源，示例为 `dragon_strike`。
- `signal_mode`：固定为 `observation_only`。
- `direction`：允许值为 `long_watch`、`short_watch`、`neutral_watch`。
- `timeframe_basis`：主要分析周期。
- `confirmation_timeframe`：确认周期。
- `data_quality_status`：DataQualityGate 只读摘要。
- `market_context`：纸面观察上下文，不是交易指令。
- `reference_plan`：纸面参考区间，不是交易指令。
- `signal_reason`：观察原因列表。
- `execution`：用户是否执行和真实盈亏占位。
- `paper_review`：纸面复盘结果占位。
- `is_tradable`：必须为 `false`。
- `is_real_trade`：必须为 `false`。
- `is_auto_trade`：必须为 `false`。
- `note`：必须明确说明仅用于纸面复盘，不是交易建议，不是交易许可，不是已执行交易。

禁止作为业务字段使用：

- `should_buy`
- `should_sell`
- `can_trade`
- `allow_trade`
- `suggested_lot`
- 真实订单 ticket

## 与真实交易的区别

`observation_signal` 不是真实交易，不是订单，不是持仓，不计入真实盈亏，不代表用户已执行，不代表系统允许交易。

纸面参考计划中的入场区、止损参考和止盈参考只用于复盘样本，不是下单指令。

## 与纸面复盘的关系

未来可以后续补充纸面复盘字段：

- `paper_result`
- `paper_mfe`
- `paper_mae`
- `paper_time_to_result`
- `review_label`

`paper_result` 用于后续记录信号结果。`paper_mfe` / `paper_mae` 用于记录最大浮盈和最大反向波动。纸面复盘结果不等于真实盈亏，`paper_result` 不等于 `real_pnl`，未执行信号不得计入真实 PnL。

## 与未来机器学习的关系

该日志未来可用于信号质量学习和样本积累。可能的学习目标包括：

- TP 是否先于 SL。
- 是否假突破。
- 最大浮盈。
- 最大回撤。
- 信号有效时长。

当前阶段不实现机器学习，不训练模型，不生成可执行信号。

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

该格式只定义观察信号日志结构，不实现写入服务、不新增 API、不修改前端页面、不接真实 MT4、不接真实行情、不读取真实账户。
