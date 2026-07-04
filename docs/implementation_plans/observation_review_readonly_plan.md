# observation_review_readonly_plan 观察复盘链路只读实现规划

本文规划未来观察复盘链路的只读实现路径，包括只读读取、格式校验、数据血缘检查、状态汇总、归因摘要和安全边界。当前阶段只写规划文档，不实现 reader、parser、validator、lineage checker、summary、API、frontend、写入逻辑、归因计算、纸面复盘计算、数据集生成、机器学习训练或自动交易。

## 文件用途

`observation_review_readonly_plan` 用于约束未来如何安全读取 1E / 1F 已定义的观察复盘文件，并把读取结果整理为诊断和摘要。

该规划只描述未来实现顺序和边界，不生成真实买卖信号，不返回真实交易建议，不计算真实 PnL，不代表系统允许交易。

## 未来只读对象

未来只读链路可能读取以下运行时文件：

- `data/signals/observation_signal.jsonl`
- `data/signals/manual_execution_event.jsonl`
- `data/signals/paper_review_result.jsonl`
- `data/ml/signal_review_dataset.csv`
- `data/ml/signal_review_dataset.parquet`

这些路径是未来运行时路径。本轮不得创建这些真实运行文件，不得提交任何真实信号日志、纸面复盘日志、人工执行日志、机器学习数据集或 MT4 数据。

## 只读原则

未来只读模块必须遵守：

- 只能读取文件。
- 不写入文件。
- 不修改文件。
- 不补全字段。
- 不修复数据。
- 不生成交易信号。
- 不生成真实交易建议。
- 不计算真实 PnL。
- 不触发任何交易动作。
- 不绕过 DataQualityGate。
- 不绕过 `review_attribution_policy`。

读取结果只能用于诊断、摘要和未来离线治理，不得直接驱动交易。

## 未来实现分层规划

### 阶段 A：Schema / DTO 定义

未来可以先定义只读类型：

- `observation_signal`
- `manual_execution_event`
- `paper_review_result`
- `signal_review_dataset`

该阶段只做结构校验，不写入真实日志，不生成真实数据集，不生成交易建议。

### 阶段 B：JSONL / CSV 只读 reader

未来 reader 可以负责：

- 逐行读取 JSONL。
- 读取 CSV 表头和行。
- 读取 Parquet 时只返回文件级诊断和行级摘要。
- 单行错误不应导致静默通过。
- 返回文件级和行级诊断。
- 不修改源文件。

该阶段不得修复 JSONL 行，不得补齐 CSV 列，不得生成新的运行时文件。

### 阶段 C：Lineage / data consistency 检查

未来 lineage 检查可以覆盖：

- `signal_id` 是否能关联。
- `review_id` 是否能关联。
- `event_id` 是否唯一。
- `sample_id` 是否唯一。
- `observation_signal` 与 `paper_review_result` 是否匹配。
- `manual_execution_event` 是否引用存在的 `signal_id`。
- `signal_review_dataset` 是否能追溯到对应 `signal_id` / `review_id`。

不一致时只返回诊断，不自动修复，不自动删除记录，不自动生成替代记录。

### 阶段 D：Review summary 聚合

未来 summary 可以统计：

- `observation_only` 信号数量。
- `paper_result` 分布。
- 用户执行标记分布。
- 可进入未来 ML 样本候选的数量。
- `excluded` 原因分布。
- 数据质量失败数量。
- 血缘断裂数量。

该阶段不计算真实 PnL，不生成交易建议，不生成可下单结论。

### 阶段 E：Read-only API 规划

未来可以规划只读 API，但当前阶段不实现 API。

未来 API 只能返回：

- 文件读取摘要。
- 行级错误摘要。
- 血缘诊断。
- 复盘状态摘要。
- 归因摘要。
- 安全边界说明。

未来 API 不得返回交易建议，不得返回可下单结论，不得返回建议手数，不得返回真实账户信息。

### 阶段 F：Frontend read-only display 规划

未来可以在前端展示复盘摘要，但当前阶段不实现前端页面。

前端只能展示只读复盘状态，不展示：

- 买入。
- 卖出。
- 开仓。
- 平仓。
- 建议手数。
- 可以交易。
- 允许交易。
- 自动下单。

前端展示必须明确这是只读复盘，不是交易许可，不生成交易信号。

## 未来建议模块名

未来可以规划以下模块，但本轮不得创建这些 backend 文件：

- `backend/app/services/observation_review_readers.py`
- `backend/app/services/observation_review_lineage.py`
- `backend/app/services/observation_review_summary.py`
- `backend/app/schemas/observation_review.py`
- `backend/tests/test_observation_review_readers.py`
- `backend/tests/test_observation_review_lineage.py`
- `backend/tests/test_observation_review_summary.py`

这些名称只是未来规划，不代表当前已经实现 reader、parser、validator、API 或 summary。

## 未来诊断状态建议

未来可以定义以下诊断状态，但当前阶段不实现代码：

- `REVIEW_DATA_NOT_FOUND`
- `REVIEW_DATA_EMPTY`
- `REVIEW_DATA_READABLE`
- `REVIEW_DATA_PARTIAL`
- `REVIEW_DATA_INVALID_JSONL`
- `REVIEW_DATA_INVALID_CSV`
- `REVIEW_LINEAGE_OK`
- `REVIEW_LINEAGE_BROKEN`
- `REVIEW_SUMMARY_READY`
- `REVIEW_SUMMARY_BLOCKED`

这些状态不是交易状态，不代表允许交易，不代表真实订单状态，不代表系统可下单。

## 错误与风险场景

未来只读实现至少需要处理：

- 文件不存在。
- 文件为空。
- JSONL 某一行解析失败。
- CSV 表头缺失。
- CSV 行列数不一致。
- `signal_id` 缺失。
- `signal_id` 重复。
- `review_id` 重复。
- `manual_execution_event` 引用不存在的 `signal_id`。
- `paper_review_result` 引用不存在的 `signal_id`。
- `signal_review_dataset` 引用不存在的 `review_id`。
- `real_pnl` 非 null。
- `is_tradable` 不为 false。
- `is_auto_trade` 不为 false。
- 数据质量失败但样本被标记为 eligible。
- 文件过大。
- 路径越界。
- 真实运行数据被误提交到 Git。

这些风险只能生成诊断结果，不得触发自动修复、自动交易或真实交易建议。

## 安全校验规则

未来只读实现至少应检查：

- `signal_mode` 是否为 `observation_only`。
- `execution_mode` 是否为 `observation_only`。
- `real_pnl` 是否为 null 或空。
- `is_tradable` 是否为 false。
- `is_auto_trade` 是否为 false。
- `not_real_pnl` 是否为 true。
- `note` 是否明确不是交易建议、不是交易许可、不是真实 PnL。
- 数据质量失败样本不得进入高可信样本。
- `paper_result` 不得当作 `real_pnl`。
- `real_pnl` 不得当作 ML 标签。

安全校验失败时，未来系统只能返回只读诊断和阻断原因，不得补齐数据，不得放行交易。

## 与真实交易的边界

当前阶段没有真实交易记录。观察复盘文件不是 MT4 订单，不是持仓，不是真实 ticket，不是真实成交流水，不计入真实盈亏，不代表用户已经执行，不代表系统允许交易，也不触发自动交易。

未来即使增加真实成交读取，也必须把真实成交链路与观察复盘链路分开，不能把纸面复盘结果、人工执行标记或未来样本标签当作真实交易事实。

## 与机器学习的边界

当前阶段不训练模型，不生成真实数据集，不生成模型文件。

未来 `signal_review_dataset` 只能用于信号质量学习，不能用真实 PnL 直接替代纸面标签，不能用计划外人工交易反推系统信号质量。

未来模型不能绕过：

- DataQualityGate
- RiskGate
- PositionGate
- GoLiveGate
- AutoTradeGate
- 人工决策

模型不能直接生成真实交易建议，不能直接驱动交易。

## 本轮不实现

本轮明确不实现：

- 不实现 reader。
- 不实现 parser。
- 不实现 validator。
- 不实现 lineage checker。
- 不实现 summary。
- 不实现 API。
- 不实现 frontend。
- 不实现写入。
- 不实现归因计算。
- 不实现纸面复盘计算。
- 不实现数据集生成。
- 不实现机器学习训练。
- 不实现自动交易。
- 不接真实 MT4。
- 不接真实行情。
- 不读取真实账户。
- 不生成模型文件。
