# observation_review_lifecycle 观察复盘生命周期与数据血缘

本文说明观察信号、人工执行标记、纸面复盘结果和未来机器学习样本之间的生命周期、数据血缘、关联键和安全边界。当前阶段只定义文档，不实现写入逻辑、不实现计算逻辑、不新增 API、不修改前端页面、不接入真实 MT4 或真实账户。

## 文件用途

`observation_review_lifecycle` 是 1E 观察复盘格式的总览文档。它用于说明一个 `observation_signal` 从创建到纸面复盘、人工执行标记、未来样本候选的完整链路。

该文档只描述数据关系和安全边界，不生成真实买卖信号，不计算真实 PnL，不代表用户已执行，也不代表系统允许交易。

## 四类文件关系

1E 阶段的四类格式文件分别承担不同职责：

| 文件 | 作用 | 当前阶段边界 |
| --- | --- | --- |
| `observation_signal.jsonl` | 记录系统观察信号 | 只记录 observation_only 观察候选，不是交易建议 |
| `manual_execution_event.jsonl` | 记录用户是否执行、跳过、纸面观察、晚进场、提前进场等人工标记 | 用于复盘用户执行行为和纪律问题，不是 MT4 成交记录 |
| `paper_review_result.jsonl` | 记录观察信号后续纸面行情表现 | 记录纸面结果，不是真实 PnL |
| `signal_review_dataset.csv` / `signal_review_dataset.parquet` | 未来由观察信号和纸面复盘结果派生出的信号质量学习样本 | 当前阶段不生成真实数据集，不训练模型 |

这四类文件共同形成观察复盘链路，但它们都不是交易执行链路。

## 关联键

核心关联键如下：

- `signal_id` 是 `observation_signal` 的核心关联键。
- `manual_execution_event` 必须通过 `signal_id` 关联 `observation_signal`。
- `paper_review_result` 必须通过 `signal_id` 关联 `observation_signal`。
- `signal_review_dataset` 必须通过 `signal_id` 关联 `observation_signal`。
- `signal_review_dataset` 可通过 `review_id` 关联 `paper_review_result`。
- `manual_execution_event` 使用 `event_id` 区分多次人工标记。
- `paper_review_result` 使用 `review_id` 区分纸面复盘结果。
- `signal_review_dataset` 使用 `sample_id` 区分未来样本。

这些关联键只用于观察、复盘、纪律分析和未来样本血缘，不是订单号，不是真实 ticket，不代表持仓。

## lifecycle_status 建议枚举

未来可以在复盘聚合层定义 `lifecycle_status`，但当前阶段不实现代码。

建议状态：

- `signal_recorded`：观察信号已记录。
- `user_action_pending`：等待用户是否执行、跳过或纸面观察的标记。
- `user_action_recorded`：用户人工标记已记录。
- `paper_review_pending`：等待纸面复盘。
- `paper_review_completed`：纸面复盘已完成。
- `dataset_candidate`：可作为未来样本候选。
- `dataset_ready`：未来数据集样本已准备。
- `excluded_from_dataset`：不适合作为样本。
- `manually_invalidated`：人工复盘标记无效。

这些状态不是交易状态，不代表可以交易，不代表真实订单状态，不代表系统允许交易。

## 数据血缘示例

一个 observation_only 场景的数据血缘可以表示为：

```text
observation_signal.signal_id
  -> manual_execution_event.signal_id
  -> paper_review_result.signal_id
  -> signal_review_dataset.signal_id / review_id
```

示例说明：

| 阶段 | 记录 | 关联方式 | 含义 |
| --- | --- | --- | --- |
| 1 | `observation_signal.signal_id = GOLD-H1-20260703-001` | 根记录 | 系统记录一个观察信号 |
| 2 | `manual_execution_event.signal_id = GOLD-H1-20260703-001` | 通过 `signal_id` 关联 | 用户标记未执行、纸面观察或晚进场等行为 |
| 3 | `paper_review_result.signal_id = GOLD-H1-20260703-001` | 通过 `signal_id` 关联 | 记录后续纸面行情表现 |
| 4 | `signal_review_dataset.signal_id = GOLD-H1-20260703-001` | 通过 `signal_id` 关联 | 未来形成信号质量学习样本 |
| 5 | `signal_review_dataset.review_id = REVIEW-GOLD-H1-20260703-001` | 通过 `review_id` 关联 | 追溯对应纸面复盘结果 |

该链路只描述 observation_only 观察和纸面复盘，不包含真实订单，不包含真实 ticket，不包含真实 PnL。

## 系统信号质量与用户执行纪律

必须区分以下概念：

- 系统信号质量：主要由 `observation_signal` 和 `paper_review_result` 判断。
- 用户执行纪律：主要由 `manual_execution_event` 判断。
- 未来机器学习样本：主要来自 `observation_signal` 和 `paper_review_result`。
- 用户真实盈亏：当前阶段不存在，不得从这些日志推导。

关键原则：

- 一个信号纸面结果好，不代表用户真实赚钱。
- 一个用户没有执行，不代表信号质量差。
- 一个用户晚进场亏损，不能直接归因于系统信号质量。
- 未执行信号不得计入真实 PnL。
- 纸面复盘结果不得等同于真实交易盈亏。
- 人工执行标记不得等同于 MT4 成交记录。

## 与真实交易记录的区别

这些文件不是 MT4 订单，不是持仓，不是真实 ticket，不是真实成交记录，不计入真实盈亏，不代表用户已经执行，不代表系统允许交易，也不触发自动交易。

当前阶段不读取真实 MT4 成交记录，不读取真实账户，不接真实行情，不连接真实交易账户。

## 与未来机器学习的关系

`signal_review_dataset` 未来只能用于信号质量学习。当前阶段不训练模型，不生成真实数据集，不自动优化策略，不生成模型文件。

未来模型输出不能绕过：

- DataQualityGate
- RiskGate
- PositionGate
- GoLiveGate
- AutoTradeGate
- 人工决策

未来模型只能作为 `signal quality filter` 的输入之一，不能直接生成真实交易建议，不能直接驱动交易。

## 安全边界

- 不自动下单。
- 不生成真实交易建议。
- 不记录真实交易盈亏。
- 不绕过 DataQualityGate。
- 不绕过人工决策。
- 不代表 GoLiveGate 通过。
- 不代表 AutoTradeGate 通过。
- 不允许这些日志直接驱动交易。
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

- 真实 observation_signal 写入。
- 真实 manual_execution_event 写入。
- 真实 paper_review_result 写入。
- 真实 signal_review_dataset 生成。
- 后端 API。
- 前端展示。
- 纸面复盘计算。
- 信号生成。
- 风控计算。
- 仓位计算。
- 机器学习训练。
- 自动交易。
