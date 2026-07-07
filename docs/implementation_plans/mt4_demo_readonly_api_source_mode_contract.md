# MT4 Demo Readonly API Source Mode Integration Contract

本文档定义未来 diagnostics / explanation API 如何在默认 `docs_fixture_only`
不变的前提下，安全接入 `mt4_demo_readonly_file_bridge_enabled`。本文档只是
API source_mode integration contract；当前 1W-1 工单只写文档，不实现 API，
不修改现有 API，不接 Dashboard，不接 MT4，不读取文件，不读取 `.env`，
不新增配置读取代码，不生成交易建议，不生成执行指令。

## 1. 本轮边界

本轮只做契约规划，明确禁止：

- 不实现 API。
- 不修改现有 API。
- 不接 diagnostics API。
- 不接 explanation API。
- 不接 Dashboard。
- 不读取 MT4 文件。
- 不读取 `data/` 运行目录。
- 不读取 `.env`。
- 不读取日志或数据库。
- 不接 MT4。
- 不连接模拟账号。
- 不连接真实账号。
- 不生成交易建议。
- 不生成执行指令。
- 不生成 EA 指令。
- 不生成 `TradePlan`。

本文档不能被解释为启用 API source mode、启用 MT4 bridge、启用 Dashboard
展示、启用模拟账号连接、启用真实账号连接、启用交易或启用执行能力。

## 2. Source Mode 规划

当前默认 source mode 必须保持：

```text
docs_fixture_only
```

未来唯一允许规划的 MT4 demo readonly source mode：

```text
mt4_demo_readonly_file_bridge_enabled
```

明确禁止的 source mode：

- `mt4_live_readonly`
- `mt4_live_execution`
- `mt4_demo_execution`
- `raw_terminal_export`
- `unknown_live_source`
- `any_execution_source`

约束：

- 默认 source_mode 必须仍然是 `docs_fixture_only`，直到另一个实现工单显式接入。
- 未来即使启用 `mt4_demo_readonly_file_bridge_enabled`，也仍然是 demo-only / read-only。
- `source_mode` 不是交易许可。
- `source_mode` 不是执行权限。
- `source_mode` 不能改变 safety flags。
- `source_mode` 不能允许 API 或 Dashboard 绕过 reader。
- 未知 source_mode 必须 blocked，不能 fallback 到 live source。

## 3. 未来 API 数据流

当前默认数据流必须保持：

```text
docs_fixture_only
↓
现有 DemoReadOnlyDiagnosticsSummary
↓
Explanation
↓
Frontend Mapper
↓
Dashboard
```

未来允许规划的数据流只能是：

```text
server-side configured MT4_DEMO_READONLY_BRIDGE_DIR
↓
MT4 demo readonly reader
↓
PathGuard
↓
FilenameWhitelist
↓
只读三个白名单 JSON
↓
SchemaValidator
↓
SourceSummaryAdapter
↓
DemoReadOnlySourceSummary
↓
Diagnostics Summary Adapter
↓
Explanation
↓
Frontend Mapper
↓
Dashboard
```

API 集成必须遵守：

- API 不能绕过 reader。
- API 不能绕过 PathGuard。
- API 不能绕过 FilenameWhitelist。
- API 不能绕过 SchemaValidator。
- API 不能绕过 SourceSummaryAdapter。
- API 不能把 raw payload 直接返回给前端。
- API 不能返回 `candidate_path`。
- API 不能返回 `base_dir`。
- API 不能返回 system path。
- API 不能返回 traceback 或 stack trace。
- API 不能返回异常原文。
- API 不能返回敏感值、交易字段或执行字段。

## 4. Base Dir 与配置安全

未来 `base_dir` 只能来自后端服务端显式配置，例如：

```text
MT4_DEMO_READONLY_BRIDGE_DIR
```

当前 1W-1 不实现配置读取，不读取 `.env`，不读取任何运行文件。未来如果需要
配置读取，必须另开工单。

未来配置规则：

- `base_dir` 只能由服务端显式配置提供。
- `base_dir` 不能来自 request body。
- `base_dir` 不能来自 query 参数。
- `base_dir` 不能来自 header。
- `base_dir` 不能来自 Dashboard。
- `base_dir` 不能来自 Agent / LLM。
- `base_dir` 不能被用户在前端输入。
- `base_dir` 不能由 API client 覆盖。
- `base_dir` 不能返回给 API response 或 UI。
- `base_dir` invalid 时必须 blocked。
- `base_dir` missing 时必须 fallback 到 `docs_fixture_only` 或 blocked，不能 silent live source。
- `base_dir` 不能指向 `.env`、日志、数据库、cache、项目 `data/` 运行目录或用户任意目录。
- `base_dir` 不能成为目录搜索起点。

## 5. 未来 Diagnostics API 行为要求

未来 diagnostics API 若支持 source_mode，必须满足：

- 默认仍走 `docs_fixture_only`。
- 只有服务端配置明确开启时，才可走 `mt4_demo_readonly_file_bridge_enabled`。
- 读取结果只能进入安全 summary。
- API response 必须保留 safety flags。
- API response 必须明确 `source_mode`。
- API response 必须明确 `source_status`。
- API response 必须明确 `reader_status`。
- API response 不能返回 raw payload。
- API response 不能返回路径。
- API response 不能返回 `candidate_path`。
- API response 不能返回 `base_dir`。
- API response 不能返回 system path。
- API response 不能返回 traceback。
- API response 不能返回敏感值。
- API response 不能返回交易建议。
- API response 不能返回执行指令。

允许的安全响应语义：

- source summary 可用于只读诊断。
- reader ready 只表示只读 reader 成功形成安全摘要。
- source blocked 只表示只读数据源不可用于展示。
- API success 只表示请求处理成功。

禁止的响应语义：

- 可以交易。
- 允许执行。
- 风控放行。
- 仓位计算放行。
- EA 调用许可。
- 自动交易可用。

## 6. 未来 Explanation API 行为要求

未来 explanation API 只能消费 diagnostics safe summary：

- 不能重新读取文件。
- 不能直接调用 reader。
- 不能接收 raw payload。
- 不能接收 `base_dir`。
- 不能接收 `candidate_path`。
- 不能读取 `.env`。
- 不能读取 `data/` 运行目录。
- 不能读取日志或数据库。
- 不能生成交易建议。
- 不能生成执行指令。
- 不能生成 EA 指令。
- 不能生成 `TradePlan`。

explanation API 只能解释已经安全清洗过的 diagnostics summary，不能成为新的
数据入口、文件读取入口、MT4 入口、Agent 入口、LLM 绕行入口或执行入口。

## 7. 失败策略

未来 API 必须覆盖以下失败场景：

- `source_mode` unknown。
- `source_mode` disabled。
- `base_dir` missing。
- `base_dir` invalid。
- reader blocked。
- file missing。
- invalid JSON。
- schema validation failed。
- source summary blocked。
- stale data。
- partial data。
- unsafe output sanitized。
- internal exception。

失败时必须：

- `passed=false` 或 `source_status=blocked`。
- safety flags 保持安全值。
- 不泄漏 raw payload。
- 不泄漏 `candidate_path`。
- 不泄漏 `base_dir`。
- 不泄漏 system path。
- 不泄漏 traceback。
- 不泄漏异常原文。
- 不泄漏 `password` / `token` / `secret` / `login` / `account_number`。
- 不泄漏 `ticket` / `order_id`。
- 不返回 `suggested_lot` / `final_lot`。
- 不返回 `buy` / `sell` / `open` / `close`。
- 不返回 EA 指令。
- 不返回交易建议。

允许使用安全 reason code，例如：

- `source_mode_unknown`
- `source_mode_disabled`
- `base_dir_missing`
- `base_dir_invalid`
- `reader_blocked`
- `file_missing`
- `invalid_json`
- `schema_validation_failed`
- `source_summary_blocked`
- `stale_data`
- `partial_data`
- `unsafe_output_sanitized`
- `internal_exception_sanitized`

禁止把底层异常消息、路径、payload 值或敏感值放入 `block_reasons`、
`warning_reasons`、`readiness_notes`、component summary、explanation 文案或 UI。

## 8. Safety Flags

未来 diagnostics API、explanation API、Frontend Mapper 和 Dashboard 输出必须始终保持：

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

解释规则：

- API success 不等于交易许可。
- reader ready 不等于交易许可。
- source summary ready 不等于交易许可。
- diagnostics summary ready 不等于交易许可。
- explanation ready 不等于交易许可。
- HTTP 200 不等于交易许可。
- `next_allowed_stage` 不等于交易许可。

这些 safety flags 不能被 source_mode、配置、API 请求、Dashboard、Agent、LLM、
fixtures、reader 输出或异常状态改写成交易许可、执行许可、风控许可或 EA 调用许可。

## 9. 与 Dashboard 的关系

本轮不修改 Dashboard。

未来 Dashboard 只能展示 mapper 后的安全字段：

- status。
- summary。
- readiness notes。
- boolean safety flags。
- safe source status。
- safe reader status。
- safe block reasons。
- safe warning reasons。

Dashboard 明确禁止：

- 不展示 raw payload。
- 不展示 `base_dir`。
- 不展示 `candidate_path`。
- 不展示 system path。
- 不展示 traceback。
- 不展示 `ticket` / `order_id`。
- 不展示 `suggested_lot` / `final_lot`。
- 不展示 `buy` / `sell` / `open` / `close`。
- 不展示 EA 指令。
- 不提供切换到 live source 的按钮。
- 不提供切换到 execution source 的按钮。
- 不提供路径输入框。
- 不触发读取任意目录。
- 不新增自动轮询。
- 不新增 WebSocket。
- 不新增自动交易开关。

Dashboard 只能作为只读诊断和只读解释展示层，不能成为数据源配置入口、MT4
控制入口、交易入口或执行入口。

## 10. 与 MT4 / EA / MQL4 的关系

未来 API 与 MT4 / EA / MQL4 的关系必须保持：

- API 不连接 MT4。
- API 不调用 EA。
- API 不写 MQL4。
- API 不发送 MT4 命令。
- API 不调用 `OrderSend`。
- API 不调用 `OrderClose`。
- API 不调用 `OrderModify`。
- API 不调用 `OrderDelete`。
- API 只消费 reader 的安全 summary。
- 即使 API source_mode 是 `mt4_demo_readonly_file_bridge_enabled`，也仍然不可交易。
- 即使 reader ready，也仍然不可交易。
- 即使 diagnostics ready，也仍然不可交易。
- 即使 explanation ready，也仍然不可交易。

任何 MT4、EA、MQL4、账号连接、执行链路、风险闸门或仓位计算能力，都必须另开
阶段，并通过新的契约、测试和人工验收。

## 11. 未来测试规划

后续实现 API source_mode 时，必须至少覆盖：

- default source_mode remains `docs_fixture_only`。
- unknown source_mode blocked。
- `mt4_demo_readonly_file_bridge_enabled` disabled by default。
- base_dir not from request body。
- base_dir not from query。
- base_dir not from header。
- base_dir not from Dashboard。
- base_dir not exposed in response。
- reader blocked leads API blocked。
- reader success produces safe diagnostics summary。
- API response does not contain raw payload。
- API response does not contain `candidate_path` / `base_dir` / system path。
- API response does not contain traceback / exception text。
- API response does not contain `password` / `token` / `secret` / `login` / `account_number`。
- API response does not contain `ticket` / `order_id`。
- API response does not contain `suggested_lot` / `final_lot`。
- API response does not contain `buy` / `sell` / `open` / `close`。
- API response does not contain EA command。
- API response safety flags always safe。
- explanation API cannot directly read files。
- explanation API cannot directly call reader。
- Dashboard cannot input path。
- Dashboard cannot switch to live source。
- Dashboard cannot switch to execution source。
- API does not glob。
- API does not `os.walk`。
- API does not `Path.iterdir`。
- API does not access network。
- API does not write files。

测试必须使用 pytest temporary directory 或安全 fixture。测试不得读取真实 MT4
目录，不得读取项目 `data/` 运行目录，不得读取 `.env`，不得读取日志、数据库、
缓存或用户文件系统。

## 12. 当前仍不实现

当前 1W-1 仍不实现：

- API source_mode。
- diagnostics API 接入。
- explanation API 接入。
- Dashboard 接入。
- config/env loader。
- MT4 接入。
- EA / MQL4。
- 账号连接。
- 执行链路。
- RiskGate。
- PositionSizing。
- ExecutionGate。
- TradePlanSchema。
- Agent。
- LLM。
- 自动交易。
- 真实交易建议。

本文档只是未来 API source_mode 集成契约。下一步若进入实现阶段，必须另开工单，
并继续保持 demo-only、read-only、non-trading、non-execution 的安全边界。
