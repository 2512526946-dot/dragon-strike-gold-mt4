# DemoReadOnlyDiagnosticsApiContract

本文定义未来 demo-only 只读诊断 API 的契约规划。当前工单只写文档，不实现 API、route、router、前端页面、前端 API client、reader、parser、MT4 bridge、EA、MQL4、风控、仓位计算、执行链路或自动交易。

## 文件用途

本文用于约束未来 demo-only 只读诊断 API 的 endpoint、响应字段、安全字段、禁止字段、错误处理和前端展示边界。

本文必须被理解为 API 契约规划：

- 本文档只是 API 契约规划。
- 本轮不实现 API。
- API 未来只用于展示 docs fixture validation summary。
- API 不是交易接口。
- API 不是执行接口。
- API 不是 MT4 连接接口。
- API 不能返回交易建议。
- API 不能返回执行许可。
- API 不能暴露完整 raw payload。

未来如果实现该 API，也只能把现有 docs fixture 只读校验摘要整理为安全展示信息。任何通过状态、READY 状态或 HTTP 200 都不得被解释为交易许可。

## API 定位

未来 API 的定位必须保持：

- demo-only。
- read-only。
- diagnostics only。
- `source_scope=docs_fixture_only`。
- 只展示校验摘要。
- 不展示完整账户快照。
- 不展示完整持仓。
- 不展示完整订单历史。
- 不展示完整行情 payload。
- 不接 MT4。
- 不接真实 `data/` 运行文件。
- 不生成 `TradePlan`。
- 不进入 `RiskGate`。
- 不进入 `PositionSizing`。
- 不进入 `ExecutionGate`。
- 不进入执行链路。

该 API 只能说明 docs 示例 fixture 的只读校验状态，不能说明任何真实账号、真实行情、真实持仓、真实订单或真实执行状态。

## 候选 Endpoint 规划

未来候选 endpoint：

```text
GET /api/demo-readonly/diagnostics
```

该 endpoint 只是未来规划：

- 当前工单不创建 route。
- 当前工单不修改 FastAPI。
- 当前工单不新增 router。
- 当前工单不新增前端调用。
- 当前工单不新增 API 测试。
- 当前工单不新增任何运行时读取逻辑。

任何实现该 endpoint 的后续工单，都必须重新审查本文档的安全字段、禁止字段和错误处理规则。

## 未来数据来源

未来 API 第一版只能调用：

```text
summarize_demo_readonly_docs_fixture_validation()
```

允许的数据来源链路必须是：

```text
DemoReadOnlyDocsFixtureValidationSummary
↓
DemoReadOnlyDocsFixtureBundleValidation
↓
DemoReadOnlyDocsFixtureReader
↓
DemoReadOnlyFixturePathGuard
↓
docs 示例 fixture
```

未来实现不得绕过安全链路：

- 不能绕过 `DemoReadOnlyFixturePathGuard`。
- 不能绕过 `DemoReadOnlyDocsFixtureBundleValidation`。
- 不能直接读取 `data/`。
- 不能自动发现 fixture。
- 不能搜索文件系统。
- 不能 fallback 到运行目录。
- 不能读取真实 MT4 数据。
- 不能读取真实账号数据。
- 不能读取日志、数据库、缓存或模型文件。

## API Response 推荐字段

未来 response 至少应包含以下字段：

```json
{
  "api_version": "1.0",
  "endpoint": "/api/demo-readonly/diagnostics",
  "generated_at": "ISO-8601 timestamp",
  "passed": false,
  "status_code": "DEMO_READONLY_DIAGNOSTICS_BLOCKED",
  "source_scope": "docs_fixture_only",
  "validation_stage": "demo_readonly_docs_fixture_validation_summary",
  "fixture_source": "docs_implementation_plans",
  "bundle_validation_status": "blocked",
  "component_statuses": [],
  "block_reasons": [],
  "warning_reasons": [],
  "readiness_notes": [],
  "next_allowed_stage": "1P-2 backend read-only diagnostics API",
  "next_blocked_stage": "execution_chain",
  "read_only": true,
  "demo_only": true,
  "is_tradable": false,
  "can_execute": false,
  "is_trading_permission": false,
  "is_execution_instruction": false,
  "allowed_to_call_ea": false,
  "allowed_to_modify_risk": false
}
```

推荐字段含义：

- `api_version`：诊断 API 契约版本。
- `endpoint`：当前响应对应的规划 endpoint。
- `generated_at`：响应生成时间。
- `passed`：只读诊断摘要是否通过。
- `status_code`：只读诊断状态码，不是交易状态。
- `source_scope`：数据来源范围，当前只能是 `docs_fixture_only`。
- `validation_stage`：摘要来自哪个只读校验阶段。
- `fixture_source`：fixture 来源描述，只能指向 docs 示例 fixture。
- `bundle_validation_status`：bundle 校验摘要状态。
- `component_statuses`：组件级安全状态摘要，不包含完整 raw payload。
- `block_reasons`：阻断原因。
- `warning_reasons`：警告原因。
- `readiness_notes`：后续规划说明。
- `next_allowed_stage`：下一步允许规划的阶段。
- `next_blocked_stage`：当前仍阻断的阶段。

安全字段必须始终满足：

- `read_only` 必须为 `true`。
- `demo_only` 必须为 `true`。
- `is_tradable` 必须为 `false`。
- `can_execute` 必须为 `false`。
- `is_trading_permission` 必须为 `false`。
- `is_execution_instruction` 必须为 `false`。
- `allowed_to_call_ea` 必须为 `false`。
- `allowed_to_modify_risk` 必须为 `false`。

这些安全字段不能由前端、HTTP 状态、请求参数或任何 fixture 内容覆盖。

## Status Code 规划

未来 API 可以使用以下安全 status_code：

- `DEMO_READONLY_DIAGNOSTICS_READY`
- `DEMO_READONLY_DIAGNOSTICS_BLOCKED`
- `DEMO_READONLY_SOURCE_ERROR`
- `DEMO_READONLY_SUMMARY_UNAVAILABLE`
- `DEMO_READONLY_INTERNAL_ERROR`

status_code 解释规则：

- `status_code` 不是交易状态。
- `status_code` 不是交易许可。
- `DEMO_READONLY_DIAGNOSTICS_READY` 只表示只读诊断摘要可展示。
- `DEMO_READONLY_DIAGNOSTICS_READY` 不表示可以交易。
- `DEMO_READONLY_DIAGNOSTICS_BLOCKED` 不表示需要开仓或平仓，只表示诊断阻断。
- 任何 status_code 都不得触发 EA、执行 API、风控覆盖或仓位计算。

## HTTP 状态规划

未来 HTTP 行为建议：

- summary service 正常返回但 validation failed 时，HTTP 可以仍为 `200`，body 中 `passed=false`。
- server 内部异常时才使用 `5xx`。
- source fixture 缺失、PathGuard 阻断或 bundle validation failed 时，应通过 body 中的 `passed=false` 和 `block_reasons` 表达。
- 用户不应从 HTTP `200` 推断可以交易。
- 前端不应从 HTTP `200` 推断执行链路可用。
- API body 中 `can_execute` 必须始终为 `false`。

HTTP 只代表诊断 API 请求是否被服务端处理，不代表交易状态、交易许可或执行许可。

## 不得返回 Raw Payload

未来 API 不得返回完整 raw payload：

- 不得返回完整 `account_snapshot`。
- 不得返回完整 `positions_order_history`。
- 不得返回完整 `market_symbol`。
- 不得返回完整 order history。
- 不得返回完整 price feed。
- 不得返回 `account_number`。
- 不得返回 `login`。
- 不得返回 `password`。
- 不得返回 `credential`。
- 不得返回 `token`。
- 不得返回 `key`。
- 不得返回 `secret`。

未来 API 可以返回安全摘要：

- component name。
- component status。
- block_reasons。
- warning_reasons。
- readiness notes。
- source_scope。
- fixture_source。
- safe counts。
- safe status summary。

组件摘要必须只表达校验状态，不暴露完整业务 payload，不暴露账号标识，不暴露持仓明细，不暴露订单明细，不暴露行情明细。

## 禁止字段

未来 API response 禁止包含以下字段或同义含义：

- `order_id`
- `ticket`
- `execute_trade`
- `order_send`
- `order_close`
- `order_modify`
- `order_delete`
- `auto_trade`
- `can_trade`
- `allow_trade`
- `should_buy`
- `should_sell`
- `buy_now`
- `sell_now`
- `open_position`
- `close_position`
- `suggested_lot`
- `final_lot`
- `override_risk`
- `bypass_gate`
- `ea_command`
- `account_number`
- `password`
- `credential`
- `token`
- `secret`
- `login`

禁止字段不得以重命名、嵌套字段、列表项、metadata、debug 字段或 raw payload 形式返回。

## 前端展示边界

未来前端如果使用该 API，只能展示：

- demo-only。
- read-only。
- diagnostics only。
- validation status。
- block reasons。
- warning reasons。
- readiness notes。
- next allowed planning stage。
- blocked stages。

未来前端不得展示：

- 下单按钮。
- 自动交易开关。
- 自动训练开关。
- 立即买入。
- 立即卖出。
- 建议手数。
- 可以交易。
- 允许交易。
- 交易许可。
- EA 执行指令。

前端必须明确：该 API 是只读诊断，不是交易许可，不生成交易信号，不连接 MT4，不连接账号，不进入执行链路。

## 错误处理规则

未来 API 遇到以下情况必须安全失败：

- summary service failed。
- bundle validation failed。
- source fixture missing。
- source fixture invalid。
- PathGuard blocked。
- unexpected exception。
- unknown source_scope。
- missing safety fields。

失败时必须返回安全默认值：

- `passed=false`。
- `can_execute=false`。
- `is_tradable=false`。
- `is_trading_permission=false`。
- `is_execution_instruction=false`。
- `allowed_to_call_ea=false`。
- `allowed_to_modify_risk=false`。
- `block_reasons` 说明原因。
- 不 fallback 到 `data/`。
- 不搜索文件系统。
- 不创建默认文件。
- 不修复 fixture。
- 不读取真实 MT4 数据。
- 不读取真实账号数据。

错误处理必须默认阻断。不得为了让页面显示成功而补全字段、修复 fixture、降级读取真实数据或绕过任一校验层。

## 与后续阶段关系

阶段关系必须保持：

- 1P-1：只写 API 契约文档。
- 1P-2：未来才实现后端只读 diagnostics API。
- 1P-3：未来才实现 API 测试和安全检查加强。
- 1Q：未来才考虑前端只读展示。
- MT4 demo bridge 仍然更靠后。
- 执行链路仍然不进入。

未来任何阶段都必须继续保持 demo-only、read-only、diagnostics only 边界。通过 docs fixture validation summary 不等于允许接入 MT4，不等于允许读取真实 data，不等于允许计算仓位，不等于允许执行。

## 当前仍不实现

本轮仍不实现：

- 不实现后端 API。
- 不实现 FastAPI route。
- 不实现 router。
- 不实现前端页面。
- 不实现前端 API client。
- 不实现 MT4 EA。
- 不实现 MQL4。
- 不接 MT4。
- 不接模拟账号。
- 不读取真实 `data/`。
- 不保存凭证。
- 不实现 RiskGate。
- 不实现 PositionSizing。
- 不实现 ExecutionGate。
- 不实现 TradePlanSchema。
- 不实现执行 API。
- 不实现自动交易。

本文档只定义未来只读诊断 API 的安全契约。任何代码实现都必须在后续独立工单中完成，并重新运行后端测试、前端 build、字段边界检查和安全检查。
