# DemoReadOnlyExplanation API Contract

本文档定义未来 `GET /api/demo-readonly/explanation` 的只读解释 API 契约。当前工单只写 API 契约文档，不实现 API，不修改后端路由，不修改现有 API，不修改前端 Dashboard，不新增前端页面，不新增前端 API client，不接 LLM，不实现 Agent，不进入任何交易、风控或执行链路。

未来 API 只能暴露 `ReadOnlyExplanationReport`，只能解释 demo-only / read-only diagnostics summary，不能输出交易建议，不能输出执行指令，不能生成 `TradePlan`，不能绕过 `ReadOnlyDiagnosticsExplainer` 的安全守卫。

## 1. 文件用途

本文档用于约束未来只读解释 API 的路径、输入来源、输出字段、状态码、错误处理、组件解释、禁止字段、前端关系、LLM / Agent 关系和后续实现顺序。

必须明确：

- 本文档只是 API 契约。
- 本轮不实现 API。
- 本轮不修改后端路由。
- 本轮不修改前端。
- 本轮不接 LLM。
- 本轮不实现 Agent。
- 未来 API 只能暴露 `ReadOnlyExplanationReport`。
- 未来 API 只能解释 diagnostics summary。
- 未来 API 不是交易 API。
- 未来 API 不是执行 API。
- 未来 API 不是风控放行 API。
- 未来 API 不能输出交易建议。
- 未来 API 不能输出执行指令。
- 未来 API 不能生成 `TradePlan`。
- 未来 API 不能绕过 `ReadOnlyDiagnosticsExplainer` 的安全守卫。

任何 `passed=true`、`READONLY_EXPLANATION_READY`、`next_allowed_stage` 或解释文本，都只能表示只读解释状态，不代表交易许可、执行许可、EA 调用许可、风控放行或仓位计算许可。

## 2. API 路径规划

未来 endpoint：

```text
GET /api/demo-readonly/explanation
```

路径约束：

- 只允许 `GET`。
- 不允许 `POST` / `PUT` / `PATCH` / `DELETE`。
- 不允许 WebSocket。
- 不允许自动轮询。
- 不允许后台自动刷新。
- 不允许写入文件。
- 不允许读取 `data/` 运行目录。
- 不允许读取 `.env`。
- 不允许读取日志。
- 不允许读取数据库。
- 不允许连接 MT4。
- 不允许连接模拟账号。
- 不允许连接真实账号。

该 API 是只读解释入口，不是新的数据入口，不是执行入口，不是 MT4 控制入口。

## 3. API 输入来源

未来 API 层只能调用：

```text
explain_demo_readonly_docs_fixture_diagnostics()
```

或在已有安全 summary 由调用方提供时调用：

```text
explain_readonly_diagnostics_summary(summary)
```

### 3.1 允许输入

允许输入：

- `DemoReadOnlyDocsFixtureValidationSummary`。
- 已安全清洗的 diagnostics summary。
- `ReadOnlyDiagnosticsExplainer` 允许的安全 summary。
- 白名单字段组成的 component status summary。
- 白名单字段组成的 bundle validation summary。
- `readiness_notes`、`next_allowed_stage`、`next_blocked_stage` 的安全摘要。
- 顶层安全字段：
  - `read_only=true`
  - `demo_only=true`
  - `is_tradable=false`
  - `can_execute=false`
  - `is_trading_permission=false`
  - `is_execution_instruction=false`
  - `allowed_to_call_ea=false`
  - `allowed_to_modify_risk=false`

### 3.2 禁止输入

禁止输入：

- raw payload。
- 完整 `account_snapshot`。
- 完整 `positions_order_history`。
- 完整 `market_symbol`。
- 真实 MT4 数据。
- 真实账号数据。
- 模拟账号真实数据。
- `data/` 运行文件。
- 日志。
- 数据库。
- `.env`。
- credentials。
- 未经过安全清洗的 API response。

API 层不能绕过 explainer service 去直接读取底层数据。API 层不能主动搜索文件系统，不能读取运行目录，不能读取环境变量，不能把底层 JSON 原文转述给用户。

## 4. API 输出契约

未来 response 必须是 `ReadOnlyExplanationReport` 的安全白名单字段。至少包含：

```text
passed
status_code
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
block_reasons
warning_reasons
read_only
demo_only
is_tradable
can_execute
is_trading_permission
is_execution_instruction
allowed_to_call_ea
allowed_to_modify_risk
notes
```

安全字段必须始终为：

```text
read_only=true
demo_only=true
is_tradable=false
can_execute=false
is_trading_permission=false
is_execution_instruction=false
allowed_to_call_ea=false
allowed_to_modify_risk=false
```

输出约束：

- `report_type` 只能表示只读解释报告，例如 `read_only_explanation_report`。
- `source_scope` 只能表示 demo-only / read-only 来源。
- `input_passed=true` 只能说明输入摘要通过只读校验，不能说明可以交易。
- `overall_explanation` 只能解释只读诊断状态。
- `status_explanation` 只能解释只读解释状态。
- `user_safe_next_steps` 只能列出非交易动作。
- `user_forbidden_actions` 必须列出仍被禁止的交易和执行动作。
- `notes` 必须继续说明非交易许可、非执行指令、交易能力禁用、执行能力禁用。

## 5. status_code 规划

未来 API 至少支持以下状态：

| status_code | 含义 |
| --- | --- |
| `READONLY_EXPLANATION_READY` | 只读解释报告可用于展示；不代表交易许可或执行许可。 |
| `READONLY_EXPLANATION_BLOCKED` | 上游 diagnostics summary 存在阻断；解释层只说明阻断原因，不生成行动建议。 |
| `READONLY_EXPLANATION_INPUT_INVALID` | 输入 summary 缺失必要字段或结构不适合解释；API 必须安全失败。 |
| `READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION` | 输入 summary 出现不安全 safety fields 或 forbidden content；API 必须强制安全失败。 |
| `READONLY_EXPLANATION_SOURCE_ERROR` | explainer 调用 summary service 失败；API 必须隐藏异常细节并返回安全失败。 |
| `READONLY_EXPLANATION_API_ERROR` | API 层自身异常；必须返回安全失败响应，不能暴露内部细节。 |

任何状态码都不能表示：

- 交易许可。
- 执行许可。
- 风控放行。
- EA 调用许可。
- 仓位计算许可。
- `TradePlan` 生成许可。

## 6. API 错误处理

未来 API 发生异常时必须返回安全失败响应。错误响应也必须保留：

```text
passed=false
status_code=READONLY_EXPLANATION_API_ERROR
read_only=true
demo_only=true
is_tradable=false
can_execute=false
is_trading_permission=false
is_execution_instruction=false
allowed_to_call_ea=false
allowed_to_modify_risk=false
```

错误处理禁止暴露：

- traceback。
- stack trace。
- 系统路径。
- Windows 用户路径。
- Python 文件路径。
- `.env`。
- password。
- credential。
- token。
- secret。
- login。
- raw payload。

错误信息应使用安全概括，例如：

```text
只读解释 API 发生安全失败，未暴露内部细节。
当前仍是 demo-only / read-only 状态，非交易许可，非执行指令。
```

## 7. component_explanations 规划

未来 API 可以输出以下组件解释：

- `account_snapshot`
- `positions_order_history`
- `market_symbol`
- `bundle_validation`
- `diagnostics_api`
- `frontend_dashboard_safety`
- `readonly_explainer`
- `explanation_api`

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

组件解释要求：

- `component_name` 必须来自白名单。
- `status` 只能表示诊断或展示状态，例如 `passed` / `blocked` / `warning` / `unknown`。
- `plain_language_summary` 只能解释诊断、展示或流程状态。
- `block_reasons_explained` 只能解释阻断原因，不能放行阻断。
- `warning_reasons_explained` 只能解释提醒原因，不能生成操作建议。
- `user_impact` 只能说明诊断影响、展示影响或流程影响。
- `user_impact` 不能说明交易影响。
- `safe_next_step` 只能是非交易动作。
- `forbidden_interpretation` 必须说明不能把组件状态解释成交易许可或执行指令。

示例安全解释：

```text
account_snapshot blocked
允许解释：账户示例快照未通过只读校验，因此只读解释仍处于阻断状态。
禁止解释：账户状态适合交易或可以进入执行。
```

## 8. allowed safe next steps

允许输出的安全下一步只能是非交易动作，例如：

- 查看只读解释。
- 查看只读诊断。
- 刷新只读诊断。
- 查看阻断原因。
- 查看警告原因。
- 检查数据校验状态。
- 等待下一阶段开发。
- 进行文档审查。
- 进行安全回归检查。
- 进行 Dashboard 展示检查。

这些下一步只能作为只读查看、人工复核、文档审查、安全回归或展示检查，不能成为任何交易、执行、连接 MT4、读取真实数据、修改风控、计算仓位或生成计划的入口。

## 9. forbidden actions

禁止输出以下行为作为用户下一步：

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

如果 API 必须说明这些行为，只能以“仍然禁止”“当前不允许”“非本阶段能力”的安全语义表达。

## 10. 禁止字段与禁止文案

API response 任意层级不得包含以下字段名：

```text
raw_payload
raw_account_snapshot
raw_positions_order_history
raw_market_symbol
account_number
login
password
credential
token
secret
api_key
key
traceback
stack_trace
system_path
order_id
ticket
execute_trade
order_send
order_close
order_modify
order_delete
auto_trade
can_trade
allow_trade
should_buy
should_sell
buy_now
sell_now
open_position
close_position
suggested_lot
final_lot
override_risk
bypass_gate
ea_command
trade_signal
trading_action
```

API 面向用户的解释文案不得将以下语义作为行动建议：

```text
买入
卖出
开仓
平仓
建议手数
可以交易
允许交易
自动下单
自动交易
执行交易
下单指令
风控放行
绕过风控
buy
sell
should buy
should sell
open position
close position
execute trade
allow trade
can trade
suggested lot
```

允许表达：

- 只读解释。
- 只读诊断。
- 数据校验。
- 安全状态。
- 非交易许可。
- 非执行指令。
- 交易能力禁用。
- 执行能力禁用。
- 流程提示。
- 阶段限制。
- 解释层。
- demo-only。
- read-only。

禁止字段和禁止文案可以出现在契约文档、测试断言、forbidden field checker 或安全检查常量里，用于阻断和审计；不能作为用户行动建议、按钮文案、解释结论或状态许可出现。

## 11. 与 diagnostics API 的关系

`GET /api/demo-readonly/diagnostics` 和未来 `GET /api/demo-readonly/explanation` 的关系：

- diagnostics API 提供状态。
- explanation API 提供解释。
- explanation API 不能替代 diagnostics API。
- explanation API 不能改变 diagnostics API 的安全字段。
- explanation API 不能把 diagnostics `passed=true` 解释成交易许可。
- explanation API 不能把 `next_allowed_stage` 解释成交易许可。
- explanation API 不能把 `block_reasons` 解释成交易动作。
- explanation API 不能绕过 diagnostics summary 直接读取底层数据。
- explanation API 不能将 summary 中的不安全内容复述给用户。

如果 diagnostics API 阻断，explanation API 只能解释阻断原因和只读流程影响，不能提出交易、执行、风控、EA 或仓位相关下一步。

## 12. 与前端 Dashboard 的关系

当前 Dashboard 已经展示 diagnostics。未来前端可以新增只读解释区块，但必须遵守：

- 解释区块只能展示 explanation API 的安全字段。
- 不新增交易按钮。
- 不新增执行按钮。
- 不新增自动交易开关。
- 不新增风控修改入口。
- 不新增仓位计算入口。
- 不新增 MT4 操作入口。
- 不新增自动轮询。
- 不新增 WebSocket。
- 不读取 raw API response。
- 不展示 raw payload。
- 不展示账号、凭证、系统路径或异常细节。

未来 ExplanationPanel 只能作为 Dashboard 的只读说明区，帮助用户理解 diagnostics 状态、阻断原因、警告原因、流程提示和阶段限制。

## 13. 与 LLM / Agent 的关系

当前 API 不接 LLM：

- 不调用模型。
- 不写 prompt。
- 不写 prompt executor。
- 不做模型路由。
- 不把 diagnostics summary 发送给任何模型。

当前 API 不实现 Agent：

- 不实现 Agent orchestration。
- 不实现 Agent memory。
- 不实现 Agent action。
- 不实现任何自动决策。

未来如果接 LLM，必须另开阶段。LLM 输出必须经过：

- forbidden field checker。
- forbidden text checker。
- safety flags checker。
- no raw payload checker。
- non-execution checker。
- non-trading-permission checker。

Agent 不能把 explanation API 输出当作交易许可。Agent 不能把 explanation API 输出当作执行指令。explanation API 只能服务于只读解释层。

## 14. 未来实现阶段顺序

建议 1S 阶段顺序：

```text
1S-1：定义 DemoReadOnlyExplanation API Contract。
1S-2：实现 GET /api/demo-readonly/explanation。
1S-3：强化 explanation API response safety。
1S-4：定义前端 ExplanationPanel Contract。
1S-5：前端 Dashboard 增加只读 ExplanationPanel。
1S-6：前端 ExplanationPanel 安全回归检查。
```

然后再考虑是否创建：

```text
v0.22.0-demo-readonly-explanation-ui
```

当前工单只做 `1S-1`。本轮不实现任何代码、不修改任何 API、不修改任何前端页面、不连接 MT4、不读取真实数据、不进入任何交易或执行链路。

## 15. 当前仍不实现

本轮不实现：

- 不实现 API。
- 不修改现有 API。
- 不新增后端路由。
- 不修改前端 Dashboard。
- 不新增前端页面。
- 不新增前端 API client。
- 不调用 LLM。
- 不新增 prompt executor。
- 不新增 Agent 代码。
- 不新增 RiskGate 代码。
- 不新增 PositionSizing 代码。
- 不新增 ExecutionGate 代码。
- 不新增 TradePlanSchema 代码。
- 不新增执行 API。
- 不新增自动交易。
- 不连接 MT4。
- 不接入模拟账号。
- 不接入真实账号。
- 不读取真实 `data/`。
- 不读取 `data/` 运行目录。
- 不读取 `.env`。
- 不读取日志。
- 不读取数据库。
- 不写入运行文件。
- 不访问网络。
- 不返回或展示真实交易建议。
- 不返回 `suggested_lot` / `final_lot`。
- 不返回买卖或开平仓指令。
- 不返回 EA 指令。
- 不返回完整 raw payload。

## 16. 安全结论

`GET /api/demo-readonly/explanation` 未来只能是 demo-only / read-only / non-trading / non-execution 的解释 API。它只能暴露 `ReadOnlyExplanationReport`，只能解释已经安全清洗过的 diagnostics summary，不能成为新的数据入口、交易入口、执行入口、风控入口、MT4 控制入口、Agent 决策入口或 LLM 绕行入口。

该 API 的最终用户含义必须始终是：

- 当前是只读解释。
- 当前是只读诊断。
- 当前不是交易许可。
- 当前不是执行指令。
- 当前交易能力禁用。
- 当前执行能力禁用。
- 当前流程提示不等于交易放行。
- 当前仍不能连接真实账户或模拟账号。
- 当前仍不能读取真实 MT4 数据。
