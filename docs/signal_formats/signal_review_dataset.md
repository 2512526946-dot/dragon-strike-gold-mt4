# signal_review_dataset 机器学习样本字段规划

本文定义未来从 `observation_signal.jsonl` 和 `paper_review_result.jsonl` 派生出的信号复盘机器学习样本字段格式。当前阶段只定义字段规划，不生成真实数据集，不训练模型，不实现信号生成、纸面复盘计算或交易策略。

## 文件用途

`signal_review_dataset` 是未来用于信号质量学习的训练样本格式。它记录观察信号在纸面复盘中的后续表现，例如 TP 是否先于 SL、是否假突破、最大纸面浮盈、最大纸面反向波动、信号有效时长，以及不同市场环境下的信号质量差异。

该数据集不用于真实交易盈亏学习，不包含真实 PnL，不代表真实交易，不代表用户已执行，也不代表系统允许交易。

## 路径约定

未来运行时路径建议为：

```text
data/ml/signal_review_dataset.csv
data/ml/signal_review_dataset.parquet
```

这些路径属于未来运行时数据目录。本轮不得创建或提交真实机器学习数据集文件。

示例文件路径为：

```text
docs/signal_formats/signal_review_dataset.example.csv
```

当前建议先定义 CSV 字段格式。未来可以扩展为 Parquet，以支持更大的样本量、更稳定的类型信息和更高效的离线训练读取。

## CSV 规则

- 第一行必须是表头。
- 每一行表示一个由观察信号和纸面复盘结果派生出的样本。
- 每一行列数必须与表头一致。
- 示例 CSV 只用于格式说明，不是真实数据集。
- `dataset_type` 必须为 `signal_review_dataset`。
- `signal_mode` 必须为 `observation_only`。
- `execution_mode` 必须为 `observation_only`。
- `executed_by_user` 必须为 `false`。
- `real_pnl` 必须为空值或 `null` 字符串，并且不代表真实盈亏。
- `is_real_trade` 必须为 `false`。
- `is_auto_trade` 必须为 `false`。
- `not_real_pnl` 必须为 `true`。
- `is_tradable` 必须为 `false`。
- `note` 必须明确说明这是纸面复盘机器学习样本，不是真实 PnL，不是交易建议，不是交易许可，不是已执行交易。

## 与 observation_signal 的关系

`signal_review_dataset` 通过 `signal_id` 关联一条 `observation_signal`。观察信号提供信号创建时间、方向标签、周期基础、确认周期、市场上下文、参考计划和 DataQualityGate 摘要。

该关系只用于构建纸面复盘样本，不表示系统生成了真实买卖信号。

## 与 paper_review_result 的关系

`signal_review_dataset` 通过 `review_id` 和 `signal_id` 关联一条 `paper_review_result`。纸面复盘结果提供 `paper_result`、`paper_mfe`、`paper_mae`、`paper_time_to_result_minutes`、`first_touch` 和未来可用的信号质量标签。

该关系只描述观察信号后续纸面表现，不记录真实订单结果，也不计入真实盈亏。

## 字段说明

基础标识字段：

- `schema_version`：格式版本。
- `dataset_type`：固定为 `signal_review_dataset`。
- `sample_id`：样本唯一标识。
- `signal_id`：关联的观察信号标识。
- `review_id`：关联的纸面复盘标识。
- `symbol`：交易品种示例为 `XAUUSD`。
- `created_at`：观察信号创建时间。
- `reviewed_at`：纸面复盘时间。

信号字段：

- `signal_mode`：固定为 `observation_only`。
- `direction`：观察方向标签，例如 `long_watch`、`short_watch` 或 `neutral_watch`。
- `timeframe_basis`：主要观察周期。
- `confirmation_timeframe`：确认周期。

执行边界字段：

- `execution_mode`：固定为 `observation_only`。
- `executed_by_user`：必须为 `false`。
- `real_pnl`：必须为空值或 `null` 字符串，不代表真实盈亏。
- `is_real_trade`：必须为 `false`。
- `is_auto_trade`：必须为 `false`。
- `not_real_pnl`：必须为 `true`。

数据质量字段：

- `data_quality_passed`：DataQualityGate 摘要结果。
- `gate_status_code`：DataQualityGate 状态码。

市场环境字段：

- `d1_bias`：D1 方向背景。
- `h4_context`：H4 结构背景。
- `h1_setup`：H1 观察形态。
- `m15_confirmation`：M15 确认信息。
- `session`：观察发生的交易时段标签。

参考计划字段：

- `entry_zone_width`：纸面入场参考区间宽度。
- `stop_distance`：纸面止损参考距离。
- `take_profit_distance`：纸面止盈参考距离。
- `risk_reward_reference`：纸面风险收益参考值。

纸面结果字段：

- `paper_result`：纸面结果枚举，例如 `hit_tp_before_sl` 或 `false_breakout`。
- `paper_result_status`：复盘状态。
- `paper_mfe`：纸面最大浮盈。
- `paper_mae`：纸面最大反向波动。
- `paper_time_to_result_minutes`：纸面结果形成耗时。
- `first_touch`：先触达的纸面参考位置。

机器学习标签字段：

- `ml_label`：未来信号质量学习标签，不是交易建议。
- `label_group`：标签分组。
- `eligible_for_signal_quality_dataset`：是否可作为未来信号质量数据集样本。

安全字段：

- `is_tradable`：必须为 `false`。
- `note`：必须说明不是交易建议、不是交易许可、不是已执行交易、不是真实 PnL。

禁止作为业务字段使用：

- `can_trade`
- `allow_trade`
- `should_buy`
- `should_sell`
- `suggested_lot`
- 真实订单 `ticket`

## ml_label 枚举

`ml_label` 只是未来信号质量学习标签，不是交易建议，不代表真实交易盈亏。

建议枚举：

- `positive_paper_outcome`
- `negative_paper_outcome`
- `false_breakout`
- `expired_unresolved`
- `neutral_or_unclear`
- `manually_invalidated`

`label_group` 建议枚举：

- `positive`
- `negative`
- `neutral`
- `invalid`

这些标签只描述观察信号纸面表现，不代表真实交易盈亏，也不构成任何买卖建议。

## 与真实交易的区别

`signal_review_dataset` 不是真实交易，不是订单，不是持仓，不计入真实盈亏，不代表用户已执行，不代表系统允许交易。

该数据集只描述观察信号和纸面复盘结果之间的样本关系。即使某个样本被标记为 `positive_paper_outcome`，也只说明纸面表现较好，不表示应该交易。

## 与未来机器学习的关系

该格式未来可用于信号质量学习。当前阶段不训练模型，不生成模型文件，不用于自动交易，不用于直接生成交易建议。

未来它只能作为 `signal quality filter` 的输入之一，并且仍必须受 DataQualityGate、人工决策、GoLiveGate 和 AutoTradeGate 等安全边界约束。

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
- 不实现风控计算。
- 不实现仓位计算。
- 不训练机器学习模型。
- 不生成模型文件。

该格式只定义未来机器学习样本字段，不新增后端 API、不修改前端页面、不接真实 MT4、不接真实行情、不读取真实账户、不提交真实运行数据集。
