# ReadOnlyExplainerLayerContract

本文档定义未来 `ReadOnlyExplainerLayer` 的只读解释层契约。当前工单只新增契约文档，不实现解释器代码、不实现 `Explainer` class、不实现 Agent、不接入 LLM、不编写 prompt 或 prompt executor、不修改 API、不修改前端 Dashboard、不新增前端页面、不接 MT4、不读取真实 `data/` 运行文件、不进入任何执行链路。

解释层的唯一用途，是把当前已经安全清洗过的 diagnostics summary / Dashboard 状态解释成人能读懂的话。解释层不是交易系统，不是决策系统，不是执行系统，不能输出交易建议，不能输出执行指令，不能生成 `TradePlan`，不能绕过任何安全字段。

## 1. 文件用途

本文档用于约束未来 `ReadOnlyExplainerLayer` 的定位、输入、输出、字段、禁止事项、前端关系、Agent 关系、LLM 关系和后续实现顺序。

必须明确：

- 本文档只是解释层契约。
- 本轮不实现解释器代码。
- 本轮不实现 `Explainer` class。
- 本轮不实现 Agent。
- 本轮不接 LLM。
- 本轮不写 prompt。
- 本轮不写 prompt executor。
- 本轮不修改 API。
- 本轮不修改前端。
- 本轮不修改 Dashboard。
- 解释层只解释 diagnostics summary / dashboard 状态。
- 解释层不是交易系统。
- 解释层不是决策系统。
- 解释层不是执行系统。
- 解释层不能输出交易建议。
- 解释层不能输出执行指令。
- 解释层不能生成 `TradePlan`。
- 解释层不能绕过 `read_only`、`demo_only`、`is_tradable=false`、`can_execute=false` 等安全字段。

任何 `passed=true`、`status=passed`、`HTTP 200`、`next_allowed_stage`、`readiness_notes` 或解释文本，都不能被解释为交易许可、执行许可、EA 调用许可、风控放行或仓位计算许可。

## 2. 解释层定位

`ReadOnlyExplainerLayer` 的定位必须保持：

- demo-only。
- read-only。
- diagnostics explanation only。
- human-readable explanation only。
- `source_scope` 当前只能来自 `docs_fixture_only` / `demo_readonly_diagnostics_api`。
- 只解释状态，不改变状态。
- 只解释 `block_reasons` / `warning_reasons`，不放行 block。
- 只解释 `next_allowed_stage`，不能把它变成交易许可。
- 只解释 `next_blocked_stage`，不能把它变成交易指令。
- 不接 MT4。
- 不读真实 `data/`。
- 不读取日志。
- 不读取数据库。
- 不调用 `RiskGate`。
- 不调用 `PositionSizing`。
- 不调用 `ExecutionGate`。
- 不调用 `TradePlanSchema`。
- 不调用 EA。

解释层只能回答：

```text
当前 demo-only / read-only diagnostics 状态是什么意思？
当前哪些组件阻断了只读展示或下一阶段流程？
当前 warning 是否需要用户注意？
当前用户只能做哪些非交易性动作？
当前哪些动作仍然被禁止？
```

解释层不能回答：

```text
是否应该交易？
是否可以执行？
是否可以连接 MT4？
是否可以绕过风控？
是否可以生成 TradePlan？
是否可以计算手数？
是否可以调用 EA？
```

## 3. 输入来源契约

未来解释层只允许接收已经安全摘要化、白名单化或 ViewModel 化的数据。

### 3.1 允许输入

允许输入：

- `DemoReadOnlyDocsFixtureValidationSummary`。
- `GET /api/demo-readonly/diagnostics` 的安全 response。
- `DemoReadOnlyDiagnostics Dashboard` 的 ViewModel。
- 已经过白名单 mapper 清洗后的安全字段。
- `component_statuses` 中的安全摘要字段。
- `bundle_result` / `bundle_validation_status` 的安全摘要字段。
- `readiness_notes`、`next_allowed_stage`、`next_blocked_stage` 的安全摘要字段。
- 顶层安全字段：`read_only=true`、`demo_only=true`、`is_tradable=false`、`can_execute=false`、`is_execution_instruction=false`。

### 3.2 禁止输入

禁止输入：

- raw payload。
- `account_snapshot` 完整 JSON。
- `positions_order_history` 完整 JSON。
- `market_symbol` 完整 JSON。
- 真实 MT4 数据。
- 真实账号数据。
- 模拟账号真实数据。
- `data/` 运行文件。
- 日志。
- 数据库。
- `.env`。
- 凭证。
- token。
- password。
- API key。
- 交易记录真实文件。
- 未经过安全清洗的 API response。

解释层不能绕过 API / mapper / summary 的安全边界直接读取底层数据。解释层不能主动搜索文件系统，不能自动发现 fixture，不能读取运行目录，不能读取本地环境变量，不能把底层 JSON 原文转述给用户。

## 4. 输出定位契约

解释层未来只能输出只读解释文本和安全摘要字段。

### 4.1 允许输出

允许输出：

- 当前状态解释。
- blocked 原因解释。
- warning 原因解释。
- component 状态解释。
- readiness notes 解释。
- `next_allowed_stage` 的流程解释。
- `next_blocked_stage` 的限制解释。
- 用户当前只能继续做哪些非交易性动作。
- 用户当前不能做哪些交易性动作。
- 不确定项 `unknowns`。
- 安全字段摘要。
- 数据校验、展示校验、流程限制相关说明。

### 4.2 禁止输出

解释层不能输出：

- 交易方向。
- 买入 / 卖出。
- 开仓 / 平仓。
- 建议手数。
- 止盈止损。
- 仓位比例。
- 风控放行。
- 执行许可。
- EA 指令。
- `TradePlan`。
- 自动交易建议。
- 任何真实交易建议。
- 任何可执行动作。
- 任何账号密码、凭证、token、系统路径、stack trace 或 raw payload。

解释层输出必须始终保留：

- `is_trading_permission=false`。
- `is_execution_instruction=false`。
- `can_execute=false`。
- `allowed_to_call_ea=false`。
- `allowed_to_modify_risk=false`。

## 5. ReadOnlyExplanationReport 契约规划

未来可以规划 `ReadOnlyExplanationReport`，但本轮不实现任何代码。

建议字段：

```text
report_version
report_type
generated_at
source_scope
input_status_code
input_passed
explanation_scope
overall_explanation
status_explanation
component_explanations
blocker_explanations
warning_explanations
readiness_explanation
next_allowed_stage_explanation
next_blocked_stage_explanation
user_safe_next_steps
user_forbidden_actions
unknowns
safety_flags
is_trading_permission
is_execution_instruction
can_execute
allowed_to_call_ea
allowed_to_modify_risk
notes
```

字段约束：

- `report_type` 只能表示只读解释报告，例如 `read_only_explanation_report`。
- `source_scope` 只能表示 demo-only / read-only 来源。
- `input_passed=true` 只能说明输入摘要通过校验，不能说明可以交易。
- `overall_explanation` 只能解释诊断状态。
- `user_safe_next_steps` 只能列出非交易动作。
- `user_forbidden_actions` 必须列出仍被禁止的交易和执行动作。
- `safety_flags.is_trading_permission` 必须为 `false`。
- `safety_flags.is_execution_instruction` 必须为 `false`。
- `safety_flags.can_execute` 必须为 `false`。
- `safety_flags.allowed_to_call_ea` 必须为 `false`。
- `safety_flags.allowed_to_modify_risk` 必须为 `false`。

## 6. component_explanations 契约规划

未来解释层可以解释以下组件：

- `account_snapshot`。
- `positions_order_history`。
- `market_symbol`。
- `bundle_validation`。
- `diagnostics_api`。
- `frontend_dashboard_safety`。

每个 component explanation 可以包含：

```text
component_name
status
plain_language_summary
block_reasons_explained
warning_reasons_explained
user_impact
safe_next_step
forbidden_interpretation
```

约束：

- `component_name` 只能使用白名单组件名。
- `status` 只能表示诊断状态，例如 passed / blocked / warning / unknown。
- `plain_language_summary` 只能解释展示或校验状态。
- `block_reasons_explained` 只能解释阻断原因，不能放行阻断。
- `warning_reasons_explained` 只能解释提醒原因，不能生成操作建议。
- `user_impact` 只能说明展示影响、诊断影响或流程影响。
- `user_impact` 不能说明交易影响。
- `safe_next_step` 只能是非交易动作。
- `forbidden_interpretation` 必须说明不能把该组件状态解释成交易许可、执行许可或风控许可。

示例解释边界：

```text
account_snapshot blocked
允许解释：账户示例快照未通过只读校验，因此只读诊断仍处于阻断状态。
禁止解释：账户状态不适合/适合交易。
```

## 7. allowed safe next steps

解释层允许表达的非交易性下一步：

- 查看只读诊断。
- 刷新只读诊断。
- 检查数据校验状态。
- 查看 block reasons。
- 查看 warning reasons。
- 等待下一阶段开发。
- 进行文档审查。
- 进行安全回归检查。
- 进行 dashboard 展示检查。
- 对契约文档进行人工复核。
- 对只读摘要字段进行人工核对。

这些表达只能作为流程或审查建议，不能成为任何交易、执行、连接 MT4、读取真实数据、修改风控或生成计划的入口。

## 8. forbidden actions

解释层必须禁止将以下行为作为用户下一步：

- 下单。
- 开仓。
- 平仓。
- 加仓。
- 减仓。
- 自动交易。
- 自动训练。
- 调用 EA。
- 修改风控。
- 计算手数。
- 生成 `TradePlan`。
- 连接真实账户。
- 连接模拟账号。
- 读取真实 MT4 数据。
- 读取真实账号数据。
- 读取日志或数据库。
- 绕过任何安全字段。

如果解释层需要说明这些动作，必须以“仍然禁止”“当前不允许”“非本阶段能力”这样的安全语义表达。

## 9. 禁止字段和禁止文案

解释层输出、未来 UI 文案、未来 summary 文案不得包含以下字段或同义字段作为用户行动建议。

### 9.1 禁止字段

```text
buy
sell
buy_now
sell_now
should_buy
should_sell
open_position
close_position
execute_trade
can_trade
allow_trade
suggested_lot
final_lot
order_send
order_close
order_modify
order_delete
ea_command
auto_trade
trade_signal
trading_action
override_risk
bypass_gate
```

这些字段可以出现在 forbidden field checker、契约文档或测试断言里，用于阻断和审计；不能作为用户行动建议、按钮文案、解释结论或状态许可出现。

### 9.2 中文禁止表达

以下中文表达不得作为行动建议或状态许可出现：

- 买入。
- 卖出。
- 开仓。
- 平仓。
- 建议手数。
- 可以交易。
- 允许交易。
- 自动下单。
- 自动交易。
- 执行交易。
- 下单指令。
- 风控放行。
- 绕过风控。

### 9.3 允许表达

允许表达：

- 只读诊断。
- 数据校验。
- 安全状态。
- 非交易许可。
- 非执行指令。
- 交易能力禁用。
- 执行能力禁用。
- 流程提示。
- 阶段限制。
- 观察层。
- 解释层。
- demo-only。
- read-only。

## 10. 与 Dashboard 的关系

Dashboard 和 ExplainerLayer 的关系：

- Dashboard 展示状态。
- ExplainerLayer 解释状态。
- ExplainerLayer 不能改变 Dashboard 的安全字段。
- ExplainerLayer 不能让 `can_execute` 变成 `true`。
- ExplainerLayer 不能让 `is_tradable` 变成 `true`。
- ExplainerLayer 不能新增交易按钮。
- ExplainerLayer 不能新增执行按钮。
- ExplainerLayer 不能新增自动刷新。
- ExplainerLayer 不能新增 WebSocket。
- ExplainerLayer 不能新增 localStorage / sessionStorage 写入。
- ExplainerLayer 未来如果接入前端，只能作为只读解释区块。

Dashboard 当前负责把安全 ViewModel 展示给用户。未来解释层若加入 Dashboard，必须只消耗 Dashboard 已经允许展示的安全字段，不能读取 raw API response，不能扩展为新的数据入口，不能引入交易、执行、风控或 MT4 操作入口。

## 11. 与 Agent 的关系

`ReadOnlyExplainerLayer` 不是 Agent。

本轮不实现：

- `DataQualityAgent`。
- `RiskAgent`。
- `PositionSizingAgent`。
- `DragonDecisionAgent`。
- 任何 Agent orchestration。
- 任何 Agent memory。
- 任何 Agent action。

未来 Agent 也不能把解释层输出当作交易许可。未来 Agent 也不能把解释层输出当作执行指令。未来 Agent 必须遵守 `AgentReportSchema` / `DragonDecisionReportSchema` 的安全字段。

解释层可以作为未来 Agent 输入的一部分，但必须保留：

- read-only 边界。
- demo-only 边界。
- non-execution 边界。
- non-trading-permission 边界。
- forbidden field checker 边界。

## 12. 与 LLM 的关系

当前不接 LLM。

当前不做：

- 不写 prompt。
- 不写 prompt executor。
- 不调用模型。
- 不做模型路由。
- 不做智能体生成解释。
- 不把 diagnostics summary 发送给任何模型。

未来如果使用 LLM 生成解释，必须单独开阶段。LLM 只能解释安全字段，不得生成交易建议，不得生成方向判断，不得生成 `TradePlan`，不得绕过安全字段。

未来 LLM 输出必须再经过：

- forbidden field checker。
- forbidden text checker。
- safety flags checker。
- no raw payload checker。
- non-execution checker。
- non-trading-permission checker。

LLM 输出如果包含交易建议、执行指令、EA 指令、真实账号信息、凭证、系统路径、stack trace 或 raw payload，必须被阻断，不得进入 UI。

## 13. 与未来实现阶段关系

建议后续阶段顺序：

```text
1R-1：只写 ReadOnlyExplainerLayerContract 文档
1R-2：实现 deterministic ReadOnlyDiagnosticsExplainer 后端服务
1R-3：为解释器增加安全字段和 forbidden field 测试
1R-4：前端 Dashboard 增加只读解释区块
1R-5：前端解释区块安全回归检查
```

完成以上步骤后，再考虑是否进入更靠后的 Agent / Risk / TradePlan 设计。任何后续阶段都必须重新验证本文档的 demo-only、read-only、non-execution 和 non-trading-permission 边界。

当前工单只做 `1R-1`。

## 14. 当前仍不实现

本轮不实现：

- 不实现解释器代码。
- 不实现 `Explainer` class。
- 不实现 Agent。
- 不实现 LLM。
- 不实现 prompt。
- 不实现 prompt executor。
- 不修改 API。
- 不修改 Dashboard。
- 不新增前端页面。
- 不新增后端 API。
- 不接 MT4。
- 不接模拟账号。
- 不接真实账号。
- 不读取真实 `data/`。
- 不实现 `RiskGate`。
- 不实现 `PositionSizing`。
- 不实现 `ExecutionGate`。
- 不实现 `TradePlanSchema`。
- 不实现执行 API。
- 不实现自动交易。

## 15. 安全结论

`ReadOnlyExplainerLayer` 只能是解释层，不能成为新的数据入口、交易入口、执行入口、风控入口、MT4 控制入口或 Agent 决策入口。它只能解释已经安全清洗过的 demo-only / read-only diagnostics 状态，并且必须持续向用户说明：

- 当前是只读诊断。
- 当前不是交易许可。
- 当前不是执行指令。
- 当前交易能力禁用。
- 当前执行能力禁用。
- 当前流程提示不等于交易放行。
- 当前仍不能连接真实账户或模拟账号。
- 当前仍不能读取真实 MT4 数据。
