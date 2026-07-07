# MT4 Demo ReadOnly File Bridge Integration Contract

本文档定义未来 `mt4_demo_readonly_file_bridge` 的接入契约，用于规划系统如何从当前 `docs_fixture_only` 安全过渡到 MT4 demo-only / read-only 文件桥接。本文档只是契约文档；当前 1U-1 工单只写文档，不实现代码，不接 MT4，不读取真实 MT4 文件，不接模拟账号，不接真实账号，不写 EA，不写 MQL4，不新增 API，不修改 Dashboard，不新增交易能力，不新增执行能力，不生成交易建议。

## 1. 文件用途

本文档用于约束未来 MT4 demo-only read-only file bridge 的输入来源、路径边界、文件白名单、字段安全、diagnostics / explanation 链路关系、Dashboard 展示边界、MT4 EA / MQL4 边界、Agent / LLM 边界和后续实现顺序。

当前工单明确不做：

- 不实现任何后端代码。
- 不实现任何前端代码。
- 不接入 MT4。
- 不读取 MT4 真实文件。
- 不读取模拟账号真实数据。
- 不读取真实账号数据。
- 不读取 `data/` 运行目录。
- 不读取 `.env`。
- 不读取日志或数据库。
- 不写 EA。
- 不写 MQL4。
- 不新增后端 API。
- 不修改现有 API。
- 不修改 Dashboard。
- 不新增前端页面或路由。
- 不新增自动刷新、自动轮询、WebSocket 或 SSE。
- 不新增交易、执行、风控、仓位、LLM、prompt executor 或 Agent 能力。
- 不返回或展示任何真实交易建议。

本文档只定义未来接入规则。任何实现都必须在后续独立工单中完成，并重新运行后端测试、前端 build、前端测试、diagnostics safety 和 explanation safety。

## 2. Source Mode 规划

未来 source mode 必须显式区分当前已启用状态、计划状态、只读桥接状态和永久禁止状态。

建议 source mode：

| source mode | 状态 | 说明 |
| --- | --- | --- |
| `docs_fixture_only` | 当前唯一已启用 | 只读取 docs 中的固定示例 fixture，用于 demo-only / read-only 契约验证。 |
| `mt4_demo_readonly_file_bridge_planned` | 未来计划 | 表示计划接入 demo-only / read-only MT4 文件桥接，但尚未启用读取。 |
| `mt4_demo_readonly_file_bridge_enabled` | 未来只读桥接启用 | 仅允许读取经过 PathGuard、文件名白名单、schema validation、forbidden field checker 和 DataQualityGate 的 demo-only / read-only 文件。 |
| `mt4_live_readonly_forbidden` | 禁止 | 真实账户即使只读也禁止进入当前 demo-only 链路。 |
| `mt4_live_execution_forbidden` | 禁止 | 真实交易执行永久禁止进入当前链路。 |
| `mt4_demo_execution_forbidden` | 禁止 | 模拟账号执行也禁止进入当前只读链路。 |

当前阶段只允许 `docs_fixture_only`。进入 `mt4_demo_readonly_file_bridge_enabled` 前，必须另开阶段，先完成路径防护、文件名白名单、schema validator、forbidden field checker、DataQualityGate、source summary adapter、API source mode 接入和前端 source mode 展示。

`source_mode` 不能被解释为交易许可、执行许可、EA 调用许可、风控放行或仓位计算许可。

## 3. 允许数据来源规划

未来只允许读取以下 demo-only / read-only 文件类型：

- `account_snapshot`
- `positions_order_history`
- `market_symbol`

允许文件必须满足：

- 文件由 MT4 端导出为只读数据。
- 文件只描述 demo-only 观察数据。
- 文件不包含密码。
- 文件不包含登录凭证。
- 文件不包含 API key、token 或 secret。
- 文件不包含可执行 EA 指令。
- 文件不包含 `OrderSend` / `OrderClose` / `OrderModify` / `OrderDelete`。
- 文件不包含自动下单、自动平仓、自动改止损、马丁格尔或网格加仓逻辑。
- 文件不包含真实账户数据。
- 文件不包含真实交易历史。
- 文件不包含完整 raw payload 直接展示给 UI。
- 文件必须经过 summary adapter 后才能进入 diagnostics / explanation。

允许数据来源只是只读输入，不等于系统允许交易，也不等于系统可以执行。

## 4. 禁止数据来源

未来必须禁止以下来源进入读取链路：

- 真实账号文件。
- 真实账户登录数据。
- 账号密码。
- investor password。
- master password。
- API key。
- token。
- secret。
- terminal config。
- `.env`。
- MT4 日志。
- 数据库。
- 交易执行日志。
- EA 指令文件。
- MQL4 执行脚本。
- 自动下单脚本。
- 未经过 PathGuard 的文件。
- 未经过 schema validation 的文件。
- 未经过 DataQualityGate 的文件。
- 未经过 forbidden field checker 的文件。

任何禁止来源一旦出现，未来实现必须 fail closed，并返回只读阻断摘要，不能把底层文件内容透传到 API、explanation 或 UI。

## 5. 文件路径安全

未来路径规则必须先于读取动作执行。路径防护失败时，系统不能尝试读取文件内容。

路径规则：

- 只能从明确配置的 demo readonly input directory 读取。
- 不允许自动搜索整个文件系统。
- 不允许递归扫描用户目录。
- 不允许读取 Desktop / Downloads / Documents 任意文件。
- 不允许读取 `.env`。
- 不允许读取 logs。
- 不允许读取 database。
- 不允许读取 MT4 terminal 敏感配置目录。
- 必须经过 PathGuard。
- 必须经过 allowed file name whitelist。
- 必须经过 extension whitelist。
- 必须拒绝 path traversal。
- 必须拒绝绝对路径绕过。
- 必须拒绝 symlink 绕过。

未来 PathGuard 建议检查：

- 解析后的路径必须位于配置目录内部。
- 原始路径不能包含 `..` 绕过。
- 原始路径不能是绝对路径。
- 扩展名必须为 `.json`。
- 文件名必须命中文件名白名单。
- symlink 或 junction 必须被拒绝。
- 读取失败不能泄漏系统路径、traceback 或 raw exception。

## 6. 文件名白名单规划

未来第一版只允许以下文件名：

- `account_snapshot.json`
- `positions_order_history.json`
- `market_symbol.json`

未来如需扩展，必须另开工单，先更新契约、测试、PathGuard、filename whitelist、schema validator、forbidden field checker 和 safety scripts。

禁止文件名：

- `orders_to_send.json`
- `trade_plan.json`
- `execution_command.json`
- `ea_command.json`
- `risk_override.json`
- `position_sizing.json`
- `credentials.json`
- `login.json`
- `password.json`
- `.env`

白名单命中只代表文件名允许进入下一层校验，不代表文件内容可信，不代表数据质量通过，不代表可以交易。

## 7. 数据字段安全要求

未来任何 MT4 demo readonly 文件进入 summary adapter 前，必须保持以下安全字段语义：

- `read_only=true`
- `demo_only=true`
- `is_tradable=false`
- `can_execute=false`
- `is_trading_permission=false`
- `is_execution_instruction=false`
- `allowed_to_call_ea=false`
- `allowed_to_modify_risk=false`

任何字段缺失、类型异常、值异常或语义冲突时，必须 safety blocked。

安全字段规则：

- `read_only=false` 必须阻断。
- `demo_only=false` 必须阻断。
- `is_tradable=true` 必须阻断。
- `can_execute=true` 必须阻断。
- `is_trading_permission=true` 必须阻断。
- `is_execution_instruction=true` 必须阻断。
- `allowed_to_call_ea=true` 必须阻断。
- `allowed_to_modify_risk=true` 必须阻断。
- 未知字段不能自动进入 API / UI。
- 任何字段名或字段值带有交易或执行语义，都必须进入 forbidden field checker。

## 8. Forbidden Fields

未来以下字段禁止进入 summary / API / UI：

- `password`
- `credential`
- `token`
- `secret`
- `api_key`
- `login`
- `account_number`
- `raw_payload`
- `order_id`
- `ticket`
- `order_send`
- `order_close`
- `order_modify`
- `order_delete`
- `ea_command`
- `execute_trade`
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
- `trade_signal`
- `trading_action`
- `override_risk`
- `bypass_gate`

forbidden field checker 必须同时检查字段名、嵌套字段名和可疑字符串值。检查结果只能进入安全摘要，不能把命中的 raw payload 原文透传给用户。

## 9. 与 Diagnostics / Explanation 链路关系

未来数据流只能是：

```text
MT4 demo readonly files
-> PathGuard
-> FileNameWhitelist
-> SchemaValidator
-> ForbiddenFieldChecker
-> DataQualityGate
-> DemoReadOnlyDiagnosticsSummary
-> GET /api/demo-readonly/diagnostics
-> GET /api/demo-readonly/explanation
-> Mapper
-> Dashboard
```

链路规则：

- MT4 文件不能直接进入 UI。
- MT4 文件不能直接进入 explanation。
- MT4 文件不能绕过 diagnostics summary。
- MT4 文件不能绕过 mapper。
- MT4 文件不能绕过 safety flags。
- MT4 文件不能直接生成交易建议。
- MT4 文件不能直接生成执行指令。
- MT4 文件不能直接生成 `TradePlan`。
- MT4 文件不能触发 RiskGate、PositionSizing 或 ExecutionGate。
- MT4 文件不能触发 EA。

`GET /api/demo-readonly/diagnostics` 只能返回安全摘要。`GET /api/demo-readonly/explanation` 只能解释安全摘要。两者都不能返回 raw MT4 file、账号密码、真实账号数据、交易指令或执行能力。

## 10. 与 Dashboard 的关系

Dashboard 未来仍然只展示只读诊断和只读解释。

Dashboard 必须保持：

- 不展示 raw MT4 文件。
- 不展示账号密码。
- 不展示登录凭证。
- 不展示可执行订单。
- 不展示交易建议。
- 不展示 `suggested_lot` / `final_lot`。
- 不展示 buy / sell / open / close 指令。
- 不展示 EA 指令。
- 不新增交易按钮。
- 不新增执行按钮。
- 不新增 MT4 操作入口。
- 不新增风控修改入口。
- 不新增仓位计算入口。
- 不新增自动刷新。
- 不新增自动轮询。
- 不新增 WebSocket / SSE。

Dashboard 允许展示：

- source mode 安全状态。
- demo-only / read-only badge。
- diagnostics passed / blocked 摘要。
- explanation 只读解释。
- DataQualityGate 摘要。
- forbidden field checker 摘要。
- PathGuard 摘要。
- 文件名白名单摘要。
- 用户可执行的非交易性下一步，例如继续完善契约、运行测试、查看只读诊断。

Dashboard 的任何绿色、通过、ready、passed 或 next allowed 文案都不能表示交易许可或执行许可。

## 11. 与 MT4 EA / MQL4 的关系

当前不写 EA，当前不写 MQL4。未来如写 MT4 端导出脚本，也必须只导出只读文件。

MT4 端脚本不得包含：

- `OrderSend`
- `OrderClose`
- `OrderModify`
- `OrderDelete`
- 自动下单逻辑
- 自动平仓逻辑
- 自动改止损逻辑
- 马丁格尔
- 网格加仓
- 密码保存逻辑
- 登录凭证保存逻辑
- 发送命令回 MT4 的逻辑
- 读取服务端执行命令的逻辑

未来 MT4 端脚本只能做：

- 从 demo-only 环境导出只读观察数据。
- 输出受限 JSON 文件。
- 不接收系统命令。
- 不执行任何交易。
- 不修改任何订单。
- 不保存账号密码。
- 不把系统输出转成 EA 指令。

## 12. 与 Agent / LLM 的关系

当前不接 Agent，当前不接 LLM。

必须明确：

- MT4 demo readonly file bridge 不等于 Agent。
- MT4 demo readonly file bridge 不等于交易系统。
- Agent 不能把只读 MT4 数据当作交易许可。
- LLM 不能把只读 MT4 数据转换成交易建议。
- LLM 不能把只读 MT4 数据转换成执行指令。
- LLM 不能生成 `TradePlan`。
- LLM 不能生成仓位、手数或风控修改建议。
- LLM 不能绕过 forbidden field checker。
- LLM 不能看到 raw MT4 payload。

未来如接 Agent / LLM，必须另开阶段，并经过 source mode 契约、forbidden field checker、DataQualityGate、read-only explanation contract、Dashboard safety scripts 和人工验收。

## 13. 未来实现阶段顺序

建议后续阶段顺序：

1. 1U-1：定义 MT4 Demo ReadOnly File Bridge Integration Contract 文档。
2. 1U-2：定义 MT4 demo readonly file schemas。
3. 1U-3：实现 MT4 demo readonly path guard / filename whitelist。
4. 1U-4：实现 demo readonly file schema validators。
5. 1U-5：实现 demo readonly source summary adapter。
6. 1U-6：API 接入 source_mode，但默认仍为 `docs_fixture_only`。
7. 1U-7：前端显示 source_mode 与数据来源安全状态。
8. 之后再考虑是否进入 MT4 端只读导出脚本阶段。

当前工单只做 1U-1。当前工单不实现 1U-2 到 1U-7，不读取 MT4 文件，不新增 API，不修改前端，不修改 Dashboard，不连接任何账号，不新增交易或执行能力。

## 14. 验收边界

1U-1 完成时，唯一预期变更是新增本文档。

验收必须确认：

- 本文档存在。
- 本文档说明本轮只写契约文档。
- 本文档说明本轮不接 MT4。
- 本文档定义 source mode。
- 本文档定义允许数据来源。
- 本文档定义禁止数据来源。
- 本文档定义文件路径安全。
- 本文档定义文件名白名单。
- 本文档定义数据字段安全要求。
- 本文档定义 forbidden fields。
- 本文档说明与 diagnostics / explanation 链路关系。
- 本文档说明与 Dashboard 的关系。
- 本文档说明与 MT4 EA / MQL4 的关系。
- 本文档说明与 Agent / LLM 的关系。
- 本文档说明未来 1U 阶段顺序。
- 本文档说明当前工单只做 1U-1。

验收还必须确认：

- 不修改后端代码。
- 不修改前端代码。
- 不新增后端 API。
- 不修改现有 API。
- 不接入 MT4。
- 不读取 MT4 文件。
- 不读取真实 data。
- 不读取 `data/` 运行目录。
- 不读取 `.env`。
- 不读取日志或数据库。
- 不写入运行文件。
- 不写 EA。
- 不写 MQL4。
- 不新增 `OrderSend` / `OrderClose` / `OrderModify` / `OrderDelete` 可执行逻辑。
- 不新增 Agent。
- 不新增 LLM。
- 不新增 RiskGate。
- 不新增 PositionSizing。
- 不新增 ExecutionGate。
- 不新增 TradePlanSchema。
- 不新增执行 API。
- 不新增自动交易。
- 不连接模拟账号。
- 不连接真实账号。
- 不返回或展示真实交易建议。
- 不返回 `suggested_lot` / `final_lot`。
- 不返回 buy / sell / open / close 指令。
- 不返回 EA 指令。
- 不返回完整 raw payload。
