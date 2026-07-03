# paper_review_result.jsonl 纸面复盘结果日志格式

本文定义未来观察信号纸面复盘结果的 JSONL 日志格式。当前阶段只定义格式，不实现纸面复盘计算、不实现写入逻辑、不实现机器学习训练。

## 文件用途

`paper_review_result.jsonl` 是未来观察信号的纸面复盘结果日志。它用于记录 `observation_signal.jsonl` 中观察信号后续的纸面表现，服务于复盘、训练和未来机器学习样本积累。

该文件记录的是纸面结果，不是用户真实交易结果，不是真实订单，不是持仓，不计入真实盈亏，不代表用户已执行，也不代表系统允许交易。

## 路径约定

未来运行时路径建议为：

```text
data/signals/paper_review_result.jsonl
```

该路径属于未来运行时日志目录。本轮不得创建或提交真实运行日志。

示例文件路径为：

```text
docs/signal_formats/paper_review_result.example.jsonl
```

## JSONL 规则

- 一行一个 JSON object。
- 不允许多行 JSON object。
- 每行必须能独立解析。
- 文件适合追加写入。
- 文件适合后续复盘、样本标注和机器学习样本读取。

每一行都必须包含 `record_type="paper_review_result"`，并通过 `signal_id` 关联一条 `observation_signal`。

## 与 observation_signal 的关系

- `paper_review_result` 必须通过 `signal_id` 关联 `observation_signal`。
- 一个 `observation_signal` 可以对应 0 个或 1 个最终 `paper_review_result`。
- 后续如果支持多次复盘修订，需要用 `review_id` 区分。

`paper_review_result` 是观察信号的后续纸面结果，不是新的信号生成结果。

## 执行状态边界

短期阶段，用户不会真实下单。用户未执行时必须记录：

```text
execution_mode = observation_only
executed_by_user = false
real_trade_id = null
real_pnl = null
```

纸面结果只描述观察信号后续行情表现，不记录真实盈亏，不构成真实交易建议。

## paper_result 枚举

建议枚举：

- `hit_tp_before_sl`：纸面止盈参考先于止损参考触达。
- `hit_sl_before_tp`：纸面止损参考先于止盈参考触达。
- `expired`：观察信号超时，未形成明确结果。
- `false_breakout`：纸面表现符合假突破特征。
- `unresolved`：尚未完成纸面复盘。
- `manually_invalidated`：人工复盘标记为无效。

这些结果只描述信号后续行情表现，不代表真实交易盈亏。

## 字段说明

核心字段：

- `schema_version`：格式版本。
- `record_type`：固定为 `paper_review_result`。
- `review_id`：纸面复盘记录唯一标识。
- `signal_id`：关联的观察信号标识。
- `created_at`：记录创建时间。
- `reviewed_at`：复盘时间。
- `symbol`：交易品种示例为 `XAUUSD`。
- `source`：来源，示例为 `dragon_strike`。
- `signal_mode`：固定为 `observation_only`。
- `direction`：来自观察信号的方向标签，例如 `long_watch` 或 `short_watch`。
- `execution`：用户是否执行和真实盈亏占位。
- `paper_outcome`：纸面复盘结果。
- `review_labels`：人工或系统复盘标签。
- `quality_tags`：信号质量标签。
- `machine_learning_usage`：未来机器学习样本使用信息。
- `is_tradable`：必须为 `false`。
- `is_real_trade`：必须为 `false`。
- `is_auto_trade`：必须为 `false`。
- `note`：必须明确说明这是纸面复盘结果，不是真实 PnL，不是交易建议，不是交易许可，不是已执行交易。

禁止作为业务字段使用：

- `can_trade`
- `allow_trade`
- `should_buy`
- `should_sell`
- `suggested_lot`
- 真实订单 ticket

## 与真实交易的区别

`paper_review_result` 不是真实交易，不是订单，不是持仓，不计入真实盈亏，不代表用户已执行，不代表系统允许交易。

`paper_result` 不等于真实 PnL。`paper_mfe` / `paper_mae` 只记录纸面最大浮盈和最大反向波动。未执行信号不得计入真实 PnL。

## 与机器学习的关系

该日志未来可用于信号质量学习和样本积累。`machine_learning_usage.label` 可用于未来监督学习。

可能的学习目标包括：

- TP 是否先于 SL。
- 是否假突破。
- 最大浮盈。
- 最大反向波动。
- 信号有效时长。

当前阶段不实现机器学习训练，不训练模型，不生成可执行信号。

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

该格式只定义纸面复盘结果日志结构，不实现复盘计算服务、不实现写入服务、不新增 API、不修改前端页面、不接真实 MT4、不接真实行情、不读取真实账户。
