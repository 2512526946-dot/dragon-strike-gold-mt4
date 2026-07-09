# Dashboard Source Readiness Status Display Contract

本文档定义未来 `DemoReadOnlyDiagnostics Dashboard` 如何安全展示 diagnostics API 返回的 source/readiness 状态。当前 1X-1 工单只写文档，不实现前端代码，不修改后端代码，不新增 API，不接 Dashboard，不读取 MT4 文件，不接 MT4，不生成交易建议，不生成执行指令。

## 1. 本轮边界

本轮只定义 Dashboard 展示契约。

本轮明确不做：

- 不修改 `frontend`。
- 不修改 `backend`。
- 不新增 API。
- 不修改现有 API。
- 不接 Dashboard。
- 不读取 MT4 文件。
- 不读取 `data/` 运行目录。
- 不读取 `.env`。
- 不接 MT4。
- 不接 EA / MQL4。
- 不接 explanation API reader。
- 不实现 Agent / LLM。
- 不实现 RiskGate / PositionSizing / ExecutionGate。
- 不实现 TradePlanSchema。
- 不生成交易建议。
- 不生成执行指令。
- 不下单。

本文档不能被解释为启用 reader、启用 MT4 文件桥、启用 Dashboard 展示、启用 Agent、启用风控、启用仓位计算、启用 EA 或启用自动交易。

## 2. Dashboard 未来只能消费 diagnostics API 的安全字段

未来 Dashboard 只能从以下只读接口的安全响应中读取展示字段：

```text
GET /api/demo-readonly/diagnostics
```

Dashboard 不得直接读取文件，不得直接调用 reader，不得直接调用 MT4，不得绕过 diagnostics API。

### 2.1 允许展示的字段方向

未来 Dashboard 只允许展示以下安全字段方向：

- `source_mode`
- `source_status`
- `source_config_status_code`
- `source_config_passed`
- `reader_status`
- `reader_passed`
- `reader_status_code`
- `mt4_demo_readonly_file_bridge_enabled`
- `source_scope`
- `component_statuses` 的安全摘要
- `validation_statuses` 的安全摘要
- `block_reasons` 的安全摘要
- `warning_reasons` 的安全摘要
- `data_quality_notes` 的安全摘要
- `read_only`
- `demo_only`
- `is_tradable`
- `can_execute`
- `is_trading_permission`
- `is_execution_instruction`
- `allowed_to_call_ea`
- `allowed_to_modify_risk`

允许字段也必须经过前端白名单 mapper。允许展示不等于允许展示原始响应、原始路径、原始 payload、异常原文、敏感值、交易字段或执行字段。

### 2.2 禁止展示的字段

Dashboard、ViewModel、mapper、组件 props、UI state 和用户可见文案不得展示或保留：

- `bridge_dir`
- `base_dir`
- `candidate_path`
- `raw_payload`
- `system_path`
- `traceback`
- `stack_trace`
- `password`
- `credential`
- `token`
- `secret`
- `api_key`
- `login`
- `account_number`
- `ticket`
- `order_id`
- `suggested_lot`
- `final_lot`
- `buy_now`
- `sell_now`
- `should_buy`
- `should_sell`
- `open_position`
- `close_position`
- `order_send`
- `order_close`
- `order_modify`
- `order_delete`
- `ea_command`
- `trade_signal`
- `trading_action`
- `override_risk`
- `bypass_gate`
- `execute_trade`
- `can_trade`
- `allow_trade`

禁止字段不得以重命名字段、嵌套字段、debug 字段、metadata、数组项、错误对象、raw response 或 UI state 的形式进入 Dashboard。未来 mapper 检测到这些字段时，必须丢弃该字段或进入 `security_blocked` / `unsafe response blocked`。

## 3. Dashboard 不得提供控制 source 的入口

Dashboard 只能展示后端安全摘要，不能成为 source 配置入口。

必须禁止：

- Dashboard 不能提供 `source_mode` 切换按钮。
- Dashboard 不能提供 `bridge_dir` 输入框。
- Dashboard 不能提供 `base_dir` 输入框。
- Dashboard 不能提供 `candidate_path` 输入框。
- Dashboard 不能提供“启用 MT4 文件桥”按钮。
- Dashboard 不能提供“连接真实账号”按钮。
- Dashboard 不能提供“连接 Demo 账号并下单”按钮。
- Dashboard 不能提供 buy / sell / open / close 按钮。
- Dashboard 不能触发 reader。
- Dashboard 不能直接调用 MT4。
- Dashboard 不能直接读取文件。
- Dashboard 不能绕过 diagnostics API。

任何 source mode、bridge dir、reader 开关或 MT4 文件桥启用状态，只能来自服务端内部固定配置和后端安全摘要，不能来自前端控件、query、header、body、localStorage、sessionStorage、Agent 或 LLM。

## 4. 状态展示规则

未来 Dashboard 文案必须只表达只读诊断状态，不能表达交易许可、执行许可、风控放行、仓位计算许可或 EA 调用许可。

### 4.1 `source_mode=docs_fixture_only`

建议展示：

- 当前数据源：文档示例 / 安全 fixture。
- Reader 状态：`not_called`。
- 说明：MT4 Demo 文件桥未启用。
- 交易状态：不可交易 / 只读观察。

不得展示：

- reader 已读取。
- MT4 文件已读取。
- 可以交易。
- 可以执行。
- EA 可以调用。

### 4.2 `source_mode=mt4_demo_readonly_file_bridge_enabled` 且 `reader_status=ready`

建议展示：

- 当前数据源：MT4 Demo 只读文件桥。
- Reader 已读取安全 summary。
- 只读。
- Demo-only。
- 不可执行。
- 非交易许可。

不得展示：

- 可以交易。
- 允许交易。
- 可以执行。
- EA 可以执行。
- 任何交易建议或执行指令。

`reader_status=ready` 只表示 reader 形成了可展示的安全摘要，不代表交易许可、执行许可、风控放行、仓位计算放行或 EA 调用许可。

### 4.3 `reader_status=blocked`

建议展示：

- MT4 Demo 只读数据不可用。
- 安全 block reason。
- 当前只读诊断被阻断。

不得展示：

- 原始路径。
- raw payload。
- 异常文本。
- traceback。
- system path。
- 账号、订单、ticket、手数或交易动作。

### 4.4 `reader_status=error_safe`

建议展示：

- Reader 异常，已安全降级。
- 只读诊断暂不可用。
- 安全错误摘要。

不得展示：

- traceback。
- system path。
- exception text。
- raw error object。
- reader 内部路径。
- reader 原始输出。

### 4.5 `source_config_passed=true`

`source_config_passed=true` 只能表示 source config 校验通过。

它不代表：

- 交易许可。
- reader 已读取。
- MT4 文件可用。
- 风控放行。
- 可以下单。
- EA 可以执行。

### 4.6 `reader_passed=true`

`reader_passed=true` 只能表示 reader 安全 summary 通过。

它不代表：

- 交易许可。
- 可以下单。
- EA 可以执行。
- 风控放行。
- 仓位计算放行。
- 自动交易可用。

## 5. Safety Flags 展示规则

Dashboard 必须始终展示或内部检查以下安全 flags：

- `read_only=true`
- `demo_only=true`
- `is_tradable=false`
- `can_execute=false`
- `is_trading_permission=false`
- `is_execution_instruction=false`
- `allowed_to_call_ea=false`
- `allowed_to_modify_risk=false`

这些 flags 是硬边界。它们不能被 `source_mode`、`source_status`、`source_config_passed`、`reader_status`、`reader_passed`、HTTP 200、`passed=true`、`ready`、Dashboard 状态、Agent、LLM 或用户操作改写成交易许可、执行许可、EA 调用许可或风控覆盖许可。

如果任何 safety flag 缺失、异常或不安全：

- Dashboard 必须显示 `blocked` / `unsafe response blocked`。
- Dashboard 不得展示交易建议。
- Dashboard 不得展示仓位建议。
- Dashboard 不得展示执行按钮。
- Dashboard 不得继续渲染危险字段。
- Dashboard 不得 fallback 到正常展示。

## 6. Source Readiness Card 建议

未来 Dashboard 可以增加一个 `SourceReadinessCard`。该卡片只能展示安全摘要，不展示配置路径、原始 payload、账号、订单、ticket、手数、交易动作或 EA command。

建议展示字段：

| 展示项 | 数据来源 | 展示规则 |
| --- | --- | --- |
| 数据源模式 | `source_mode` | 只显示安全枚举或安全文案 |
| 数据源状态 | `source_status` | 只显示 ready / blocked / safe warning 等安全状态 |
| 配置检查 | `source_config_passed` | true 只表示配置校验通过 |
| Reader 状态 | `reader_status` | 显示 `not_called` / `ready` / `blocked` / `error_safe` |
| Reader 结果 | `reader_passed` | true 只表示 reader 安全摘要通过 |
| 文件桥是否启用 | `mt4_demo_readonly_file_bridge_enabled` | true 仍不代表交易许可 |
| 只读状态 | `read_only` | 必须为 true |
| Demo-only 状态 | `demo_only` | 必须为 true |
| 可交易状态 | `is_tradable` | 必须显示 false 或不可交易 |
| 可执行状态 | `can_execute` | 必须显示 false 或不可执行 |
| 阻断原因 | safe `block_reasons` | 只展示安全 reason code 或清洗后的短文案 |
| 警告原因 | safe `warning_reasons` | 只展示安全 warning code 或清洗后的短文案 |

Source Readiness Card 不得展示：

- 路径。
- raw payload。
- 账号 ID。
- 订单 ID。
- ticket。
- 手数。
- buy / sell / open / close。
- EA command。
- source 控制按钮。
- MT4 连接按钮。
- reader 触发按钮。
- 交易或执行按钮。

## 7. Data Freshness 未来展示规则

当前 1X-1 不实现 DataQualityGate，不实现 freshness 计算，也不修改后端 API。本文档仅预留未来展示规则。

未来若后端安全摘要包含 data freshness，Dashboard 可以按后端 safe summary 展示：

- `data_age <= 5` 秒：`fresh`。
- `5 < data_age <= 10` 秒：`stale warning`，只允许解释，不允许交易计划。
- `data_age > 10` 秒：`stale blocked`，不允许智能体生成交易建议。

必须遵守：

- 没有 `data_age` 时不能显示“数据新鲜”。
- `data_age` 不能由前端自行计算来替代后端判断。
- 前端只能展示后端 safe summary。
- 数据过期时，Dashboard 不能展示可计划。
- 数据过期时，Dashboard 不能展示可交易。
- 数据过期时，Dashboard 不能展示可执行。

Freshness 只表示数据时效摘要，不代表交易许可或执行许可。

## 8. 与智能体和执行链路的关系

Dashboard source/readiness 只是展示数据源状态。

它不触发：

- Agent。
- LLM。
- RiskGate。
- PositionSizing。
- ExecutionGate。
- EA。
- MT4。
- 下单。
- TradePlan 生成。
- suggested_lot / final_lot 生成。
- buy / sell / open / close 展示。

未来若系统接入 Agent、LLM、RiskGate、PositionSizing、ExecutionGate、EA 或 TradePlanSchema，必须另开工单，不能通过 Dashboard source/readiness 展示契约隐式启用。

## 9. 未来测试规划

未来前端或契约测试至少应覆盖：

- diagnostics response 为 `docs_fixture_only` 时，Dashboard 显示 fixture 模式。
- `reader_status=not_called` 时，显示 MT4 bridge 未启用。
- `reader_status=ready` 时，显示只读 ready，但不显示可交易。
- `reader_status=blocked` 时，显示安全 blocked reason。
- `reader_status=error_safe` 时，不显示异常原文。
- response 包含 `bridge_dir` 时，Dashboard 不渲染该字段。
- response 包含 `raw_payload` 时，Dashboard 不渲染该字段。
- response 包含 `traceback` 时，Dashboard 不渲染该字段。
- response 包含 `account_number` / `login` / `token` / `password` 时，Dashboard 不渲染这些字段。
- response 包含 `ticket` / `order_id` 时，Dashboard 不渲染这些字段。
- response 包含 `suggested_lot` / `final_lot` 时，Dashboard 不渲染这些字段。
- response 包含 `buy` / `sell` / `open` / `close` 时，Dashboard 不渲染这些字段。
- unsafe safety flags 时，Dashboard 显示 `unsafe response blocked`。
- Dashboard 不提供 `source_mode` 控件。
- Dashboard 不提供 `bridge_dir` / `base_dir` 输入框。
- Dashboard 不提供交易按钮。
- Dashboard 不调用 reader。
- Dashboard 不读取文件。
- Dashboard 不连接 MT4。

未来测试也必须确认：

- `source_config_passed=true` 不会渲染为交易许可。
- `reader_passed=true` 不会渲染为交易许可。
- `mt4_demo_readonly_file_bridge_enabled=true` 不会渲染为可以执行。
- `read_only=true` 和 `demo_only=true` 不会被解释成交易许可。
- `is_tradable=false` 和 `can_execute=false` 始终保留。

## 10. 当前仍不实现

当前 1X-1 仍不实现：

- frontend 代码。
- Dashboard 组件。
- Dashboard mapper。
- Dashboard tests。
- backend API 修改。
- diagnostics API 修改。
- explanation API 修改。
- reader 默认开启。
- MT4 文件读取。
- MT4 接入。
- EA / MQL4。
- Agent / LLM。
- RiskGate。
- PositionSizing。
- ExecutionGate。
- TradePlanSchema。
- 自动交易。
- 实盘交易。

本文档只定义未来 Dashboard source/readiness 状态展示契约。任何代码实现必须在后续独立工单中完成，并继续保持 demo-only、read-only、non-trading、non-execution、安全失败和不进入执行链路的边界。

