# review_attribution_policy 复盘归因规则

本文定义观察信号复盘中的归因规则，用于避免把系统信号质量、用户执行纪律、数据质量、市场环境、纸面结果和真实盈亏混为一谈。当前阶段只定义文档，不实现计算、不实现写入逻辑、不新增 API、不修改前端页面、不生成真实数据集、不训练模型。

## 文件用途

`review_attribution_policy` 用于约束未来复盘分析时的归因口径。它说明哪些结果可以归因于系统观察信号质量，哪些结果属于用户执行纪律，哪些结果受数据质量或市场环境影响，哪些结果只属于纸面行情表现。

该文档不是交易策略，不生成买卖信号，不记录真实 PnL，不代表系统允许交易。

## 归因对象

未来复盘至少应区分以下归因对象：

- `system_signal_quality`：系统观察信号质量。
- `user_execution_discipline`：用户执行纪律。
- `data_quality_issue`：数据质量问题。
- `market_environment`：市场环境因素。
- `paper_outcome`：纸面行情结果。
- `real_trade_outcome_future_only`：未来真实交易结果，仅在未来真实成交读取阶段才存在。
- `mixed_or_unclear`：混合或无法明确归因。
- `not_applicable`：不适用。

这些归因对象只用于复盘分类，不是交易许可，不是自动交易指令。

## 核心原则

- `observation_signal` 记录系统当时提出的 observation_only 观察信号。
- `manual_execution_event` 记录用户是否执行以及如何执行。
- `paper_review_result` 记录观察信号后续纸面行情表现。
- `signal_review_dataset` 只用于未来信号质量学习。
- `paper_result` 不等于 `real_pnl`。
- 未执行信号不得计入真实 PnL。
- 用户没执行，不代表信号质量差。
- 用户晚进场亏损，不能直接归因于系统信号质量。
- 用户计划外操作，不能归入系统信号质量。
- 数据质量失败的记录不得进入高可信样本。
- 这些规则不代表真实交易许可。

## 建议归因字段

未来可以在复盘聚合或离线样本生成阶段使用以下字段，但当前阶段不实现代码：

- `attribution_primary`
- `attribution_secondary`
- `signal_quality_label`
- `execution_discipline_label`
- `data_quality_label`
- `paper_outcome_label`
- `ml_inclusion_status`
- `real_pnl_handling`
- `attribution_note`

这些字段只用于复盘归因和未来数据治理，不得直接驱动交易。

## signal_quality_label 枚举

建议枚举：

- `positive_paper_outcome`
- `negative_paper_outcome`
- `false_breakout`
- `expired_unresolved`
- `neutral_or_unclear`
- `manually_invalidated`
- `data_invalid`
- `not_enough_information`

这些标签只描述系统观察信号的纸面质量，不代表真实交易盈亏，不代表真实交易建议。

## execution_discipline_label 枚举

建议枚举：

- `not_executed`
- `paper_only`
- `followed_plan_future_only`
- `late_entry`
- `early_entry`
- `entered_without_confirmation`
- `skipped_valid_signal`
- `unplanned_trade`
- `executed_during_prohibited_state`
- `oversize_future_only`
- `no_stop_loss_future_only`
- `manually_invalidated`
- `not_applicable`

这些标签用于复盘用户行为和纪律，不用于判断系统信号质量。用户执行纪律和系统信号质量必须分开评估。

## ml_inclusion_status 枚举

建议枚举：

- `eligible_for_signal_quality_dataset`
- `excluded_no_paper_result`
- `excluded_data_quality_failed`
- `excluded_manual_invalidated`
- `excluded_unplanned_trade`
- `excluded_real_pnl_only`
- `excluded_unclear_lineage`

未来机器学习样本只能来自可追溯的 `observation_signal` + `paper_review_result`。不能直接用真实 PnL 替代纸面标签，不能用计划外人工交易反推系统信号质量。

数据质量失败、手动无效、计划外交易不得进入高可信训练集。

## real_pnl_handling 枚举

建议枚举：

- `not_applicable`
- `must_be_null`
- `future_real_trade_record_only`
- `do_not_mix_with_paper_result`
- `excluded_from_real_pnl`

当前阶段 `real_pnl` 必须为空或 `null`。未来即使接入真实成交，也必须把真实 PnL 与纸面复盘结果分开。纸面复盘结果不得计入真实盈亏。

## 场景归因表

| 场景 | 输入条件 | 归因规则 | 不允许的归因 |
| --- | --- | --- | --- |
| A | `observation_signal` 存在，用户未执行，`paper_result=hit_tp_before_sl` | `system_signal_quality=positive_paper_outcome`；`user_execution_discipline=not_executed`；`real_pnl_handling=excluded_from_real_pnl` | 不得把纸面 TP 结果记为真实赚钱 |
| B | `observation_signal` 存在，用户 `paper_only`，`paper_result=hit_sl_before_tp` | `system_signal_quality=negative_paper_outcome`；`user_execution_discipline=paper_only`；`real_pnl_handling=excluded_from_real_pnl` | 不得把纸面 SL 结果记为真实亏损 |
| C | `observation_signal` 纸面表现好，但用户 `late_entry` 导致未来真实结果不好 | 系统纸面信号质量和用户执行纪律必须分开；晚进场归入 `user_execution_discipline=late_entry` | 不得直接把用户晚进场结果归因于系统信号质量 |
| D | 用户没有 `observation_signal` 却自行操作 | `user_execution_discipline=unplanned_trade`；`ml_inclusion_status=excluded_unplanned_trade` | 不得进入 signal quality dataset；不得反推系统信号质量 |
| E | 数据质量未通过但存在观察记录 | `attribution_primary=data_quality_issue`；`ml_inclusion_status=excluded_data_quality_failed` | 不得作为高可信机器学习样本 |
| F | 用户在系统禁止状态下自行操作 | `execution_discipline_label=executed_during_prohibited_state`；属于纪律或风控违规 | 不得归因于系统信号质量 |

这些场景只用于归因说明，不代表真实交易记录，不触发任何自动交易。

## 与真实交易记录的区别

当前阶段没有真实成交读取。这些日志不是 MT4 订单，不是持仓，不是真实 ticket，不是真实成交流水，不计入真实盈亏，不代表用户已经执行，不代表系统允许交易，也不触发自动交易。

未来如引入真实成交读取，真实交易结果也必须独立于纸面复盘结果保存和解释，不能混用。

## 与未来机器学习的关系

机器学习只学习信号质量，不学习用户冲动操作。机器学习样本必须有清晰的 `signal_id` / `review_id` 血缘。

以下记录不得进入高可信训练集：

- 数据质量失败记录。
- 手动无效记录。
- 计划外交易记录。
- 只有真实 PnL、没有纸面复盘血缘的记录。
- `signal_id` 或 `review_id` 血缘不清楚的记录。

当前阶段不训练模型，不生成真实数据集，不自动优化策略，不生成模型文件。

未来模型不能绕过：

- DataQualityGate
- RiskGate
- PositionGate
- GoLiveGate
- AutoTradeGate
- 人工决策

模型不能直接生成真实交易建议，也不能直接驱动交易。

## 安全边界

- 不自动下单。
- 不生成真实交易建议。
- 不记录真实交易盈亏。
- 不绕过 DataQualityGate。
- 不绕过人工决策。
- 不代表 GoLiveGate 通过。
- 不代表 AutoTradeGate 通过。
- 不允许这些日志或归因规则直接驱动交易。
- 不开发 MT4 EA。
- 不开发 MQL4 交易代码。
- 不包含 OrderSend、OrderClose、OrderModify、OrderDelete 执行逻辑。
- 不实现信号生成引擎。
- 不实现纸面复盘计算引擎。
- 不实现执行记录写入逻辑。
- 不实现数据集生成代码。
- 不实现风控计算。
- 不实现仓位计算。
- 不训练机器学习模型。
- 不生成模型文件。

## 当前阶段未实现

当前阶段未实现：

- 真实信号日志写入。
- 真实纸面复盘日志写入。
- 真实人工执行日志写入。
- 真实机器学习数据集生成。
- 归因计算代码。
- 后端 API。
- 前端展示。
- 信号生成。
- 纸面复盘计算。
- 风控计算。
- 仓位计算。
- 机器学习训练。
- 自动交易。
