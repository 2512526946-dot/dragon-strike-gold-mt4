# MT4 Demo ReadOnly File Schemas

本文档定义未来 MT4 demo-only / read-only 文件桥接允许读取的三类文件 schema：

1. `account_snapshot.json`
2. `positions_order_history.json`
3. `market_symbol.json`

本文档只是 schema 契约；当前 1U-2 工单只写文档，不实现 validator，不实现 reader，不接 MT4，不读取真实 MT4 文件，不接模拟账号，不接真实账号，不写 EA，不写 MQL4，不新增 API，不修改 Dashboard，不生成交易建议，不生成执行指令。

## 1. 文件用途

本文档用于约束未来 `mt4_demo_readonly_file_bridge_enabled` 模式下的 demo-only / read-only 文件格式。schema 的唯一用途是为未来只读诊断链路提供结构化输入边界。

当前工单明确不做：

- 不实现 validators。
- 不实现 reader。
- 不实现 PathGuard。
- 不实现 filename whitelist。
- 不实现 source summary adapter。
- 不接 MT4。
- 不读取 MT4 文件。
- 不读取真实 `data/`。
- 不读取 `data/` 运行目录。
- 不读取 `.env`。
- 不读取日志或数据库。
- 不写入运行文件。
- 不写 EA。
- 不写 MQL4。
- 不新增后端 API。
- 不修改现有 API。
- 不修改前端代码。
- 不修改 Dashboard。
- 不新增交易能力。
- 不新增执行能力。

即使未来 schema 校验通过，也只表示文件格式满足只读诊断输入要求，不表示交易许可、执行许可、EA 调用许可、风控放行或仓位计算许可。

## 2. 全局 Schema 安全字段

三个文件未来都必须包含或由上游包装提供以下安全字段：

| 字段 | 必须值 | 类型 | 说明 |
| --- | --- | --- | --- |
| `read_only` | `true` | boolean | 文件只能作为只读输入。 |
| `demo_only` | `true` | boolean | 文件只能来自 demo-only 范围。 |
| `source_mode` | `mt4_demo_readonly_file_bridge_enabled` | string | 未来启用后的唯一允许 file bridge source mode。 |
| `is_tradable` | `false` | boolean | 文件不能表示可交易。 |
| `can_execute` | `false` | boolean | 文件不能表示可执行。 |
| `is_trading_permission` | `false` | boolean | 文件不能表示交易许可。 |
| `is_execution_instruction` | `false` | boolean | 文件不能表示执行指令。 |
| `allowed_to_call_ea` | `false` | boolean | 文件不能允许调用 EA。 |
| `allowed_to_modify_risk` | `false` | boolean | 文件不能允许修改风控。 |

安全字段规则：

- 任何安全字段缺失、类型错误或值异常，都必须 safety blocked。
- 即使文件内容校验通过，也不代表交易许可。
- 即使 `market_symbol` 可读，也不代表可以买卖。
- 即使 `positions_order_history` 可读，也不代表可以平仓或开仓。
- schema 只服务于只读诊断，不服务于交易执行。
- safety flags 不能被前端 mapper、explanation、Dashboard 或任何未来 Agent / LLM 改写成交易含义。

## 3. `account_snapshot.json` Schema

`account_snapshot.json` 只能用于只读账户状态诊断。它不能包含完整账号、密码、登录凭证、真实账户标识、交易许可或执行能力。

### 3.1 允许字段

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `schema_version` | string | 初始为 `"1.0"`。 |
| `generated_at` | ISO 8601 string | 文件生成时间。 |
| `source_mode` | string | 必须为 `mt4_demo_readonly_file_bridge_enabled`。 |
| `terminal_name` | string | 终端显示名，不得包含路径或凭证。 |
| `server_name_masked` | string | 只能是 masked server name，不能保存完整敏感标识。 |
| `account_type` | string enum | 例如 `demo`，不得为 live。 |
| `currency` | string | 账户币种。 |
| `balance` | number | 只读余额。 |
| `equity` | number | 只读权益。 |
| `margin` | number | 只读保证金占用。 |
| `free_margin` | number | 只读可用保证金。 |
| `margin_level` | number | 只读保证金比例。 |
| `leverage` | number | 只读杠杆信息。 |
| `positions_count` | number | 只读持仓数量摘要。 |
| `orders_count` | number | 只读订单数量摘要。 |
| `read_only` | boolean | 必须为 `true`。 |
| `demo_only` | boolean | 必须为 `true`。 |
| `is_tradable` | boolean | 必须为 `false`。 |
| `can_execute` | boolean | 必须为 `false`。 |
| `is_trading_permission` | boolean | 必须为 `false`。 |
| `is_execution_instruction` | boolean | 必须为 `false`。 |
| `allowed_to_call_ea` | boolean | 必须为 `false`。 |
| `allowed_to_modify_risk` | boolean | 必须为 `false`。 |
| `data_quality_notes` | string[] | 只读数据质量说明。 |

### 3.2 禁止字段

`account_snapshot.json` 必须禁止：

- `account_number`
- `login`
- `password`
- `investor_password`
- `master_password`
- `credential`
- `token`
- `secret`
- `api_key`
- `raw_payload`
- `order_send`
- `order_close`
- `order_modify`
- `order_delete`
- `ea_command`
- `trade_signal`
- `suggested_lot`
- `final_lot`

`server_name` 只能以 `server_name_masked` 形式出现。不得保存完整账号，不得保存密码，不得保存登录凭证，不得保存真实账户标识。`account_snapshot` 只能用于只读账户状态诊断，不能进入任何交易执行链路。

## 4. `positions_order_history.json` Schema

`positions_order_history.json` 只能用于只读持仓和历史摘要诊断。它不能包含可直接执行的订单标识，也不能把持仓状态解释为平仓、开仓或方向建议。

### 4.1 顶层允许字段

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `schema_version` | string | 初始为 `"1.0"`。 |
| `generated_at` | ISO 8601 string | 文件生成时间。 |
| `source_mode` | string | 必须为 `mt4_demo_readonly_file_bridge_enabled`。 |
| `read_only` | boolean | 必须为 `true`。 |
| `demo_only` | boolean | 必须为 `true`。 |
| `is_tradable` | boolean | 必须为 `false`。 |
| `can_execute` | boolean | 必须为 `false`。 |
| `is_trading_permission` | boolean | 必须为 `false`。 |
| `is_execution_instruction` | boolean | 必须为 `false`。 |
| `allowed_to_call_ea` | boolean | 必须为 `false`。 |
| `allowed_to_modify_risk` | boolean | 必须为 `false`。 |
| `open_positions` | array | 只读持仓摘要数组。 |
| `recent_closed_orders` | array | 只读近期历史摘要数组。 |
| `pending_orders_summary` | object | 只读挂单摘要，不包含可执行订单号。 |
| `data_quality_notes` | string[] | 只读数据质量说明。 |

### 4.2 `open_positions` 允许字段

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `position_ref` | string | 不可执行引用，不能是原始 ticket。 |
| `symbol` | string | 品种。 |
| `side_masked` | string | masked 或非行动建议的归一化方向标签。 |
| `volume` | number | 只读历史/当前持仓量。 |
| `open_time` | ISO 8601 string | 开仓时间摘要。 |
| `open_price` | number | 只读开仓价。 |
| `current_price` | number | 只读当前价。 |
| `floating_pnl` | number | 只读浮动盈亏。 |
| `swap` | number | 只读 swap。 |
| `commission` | number | 只读手续费。 |
| `age_minutes` | number | 持仓时间摘要。 |
| `read_only_note` | string | 只读说明。 |

### 4.3 `recent_closed_orders` 允许字段

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `order_ref` | string | 不可执行引用，不能是原始 order id。 |
| `symbol` | string | 品种。 |
| `side_masked` | string | masked 或非行动建议的归一化方向标签。 |
| `volume` | number | 只读历史成交量。 |
| `open_time` | ISO 8601 string | 开仓时间摘要。 |
| `close_time` | ISO 8601 string | 平仓时间摘要。 |
| `open_price` | number | 只读开仓价。 |
| `close_price` | number | 只读平仓价。 |
| `realized_pnl` | number | 只读已实现盈亏。 |
| `swap` | number | 只读 swap。 |
| `commission` | number | 只读手续费。 |
| `duration_minutes` | number | 持续时间摘要。 |
| `read_only_note` | string | 只读说明。 |

### 4.4 `pending_orders_summary` 允许字段

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `count` | number | 只读挂单数量摘要。 |
| `symbols` | string[] | 品种列表，不包含订单号。 |
| `read_only_note` | string | 只读说明。 |

### 4.5 禁止字段

`positions_order_history.json` 必须禁止：

- `ticket`
- `order_id`
- `account_number`
- `login`
- `password`
- `credential`
- `token`
- `secret`
- `raw_payload`
- `order_send`
- `order_close`
- `order_modify`
- `order_delete`
- `close_position`
- `open_position`
- `buy_now`
- `sell_now`
- `should_buy`
- `should_sell`
- `ea_command`
- `trade_signal`
- `trading_action`
- `suggested_lot`
- `final_lot`

`ticket` / `order_id` 必须被替换为不可执行引用 `position_ref` / `order_ref`。`side` 只能 masked 或归一化为非行动建议。不得把持仓状态解释成平仓或开仓建议。不得输出可直接执行的订单标识。该文件只能用于只读持仓 / 历史诊断。

## 5. `market_symbol.json` Schema

`market_symbol.json` 只能用于只读行情和品种状态诊断。它不能生成方向判断、买卖建议、入场建议或出场建议。

### 5.1 允许字段

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `schema_version` | string | 初始为 `"1.0"`。 |
| `generated_at` | ISO 8601 string | 文件生成时间。 |
| `source_mode` | string | 必须为 `mt4_demo_readonly_file_bridge_enabled`。 |
| `symbol` | string | 品种，例如 `XAUUSD`。 |
| `bid` | number | 只读 bid。 |
| `ask` | number | 只读 ask，必须大于或等于 bid。 |
| `spread_points` | number | 只读点差诊断字段。 |
| `digits` | number | 小数位。 |
| `point` | number | 点值单位。 |
| `tick_size` | number | tick size。 |
| `tick_value` | number | tick value。 |
| `contract_size` | number | 合约规模。 |
| `trade_mode_readonly_label` | string | 只读交易模式标签，不代表交易许可。 |
| `session_status_readonly_label` | string | 只读时段状态标签，不代表执行许可。 |
| `last_tick_time` | ISO 8601 string | 最近 tick 时间。 |
| `data_age_seconds` | number | 数据年龄。 |
| `read_only` | boolean | 必须为 `true`。 |
| `demo_only` | boolean | 必须为 `true`。 |
| `is_tradable` | boolean | 必须为 `false`。 |
| `can_execute` | boolean | 必须为 `false`。 |
| `is_trading_permission` | boolean | 必须为 `false`。 |
| `is_execution_instruction` | boolean | 必须为 `false`。 |
| `allowed_to_call_ea` | boolean | 必须为 `false`。 |
| `allowed_to_modify_risk` | boolean | 必须为 `false`。 |
| `data_quality_notes` | string[] | 只读数据质量说明。 |

### 5.2 禁止字段

`market_symbol.json` 必须禁止：

- `buy`
- `sell`
- `buy_now`
- `sell_now`
- `should_buy`
- `should_sell`
- `open_position`
- `close_position`
- `execute_trade`
- `can_trade`
- `allow_trade`
- `suggested_lot`
- `final_lot`
- `order_send`
- `order_close`
- `order_modify`
- `order_delete`
- `ea_command`
- `trade_signal`
- `trading_action`
- `override_risk`
- `bypass_gate`
- `raw_payload`

`bid` / `ask` 是只读行情。`spread_points` 只是诊断字段。`trade_mode_readonly_label` 不能代表交易许可。`session_status_readonly_label` 不能代表执行许可。`market_symbol` 不能生成方向判断，不能生成买卖建议，不能生成入场或出场建议。

## 6. 字段类型规划

未来 validators 必须采用严格字段类型规则：

- 时间字段使用 ISO 8601 string。
- 金额、价格、盈亏、点差、数量、年龄等数值字段使用 number。
- 状态字段使用 string enum。
- safety flags 使用 boolean。
- notes 使用 string[]。
- positions / orders 使用 array。
- unknown fields 默认拒绝或丢弃，具体策略必须在 validator 工单中显式声明。
- forbidden fields 出现时必须 safety blocked。
- `null` 值必须有明确允许规则，否则视为 invalid。
- number 字段不能接受字符串形式数字。
- boolean 字段不能接受 `"true"` / `"false"` 字符串。
- array 字段不能接受单对象替代。
- object 字段不能接受 array 替代。

类型规则服务于只读诊断，不服务于交易、执行、风控放行或仓位计算。

## 7. `schema_version` 规划

schema version 规则：

- `schema_version` 初始为 `"1.0"`。
- 不同文件可以独立版本。
- 版本不匹配时 validators 必须 blocked。
- 未来升级 schema 必须另开工单。
- 不能 silently accept unknown `schema_version`。
- 不能因为未知版本包含熟悉字段就继续处理。
- blocked 结果只能返回安全摘要，不能泄漏 raw payload。

## 8. `source_mode` 规划

未来 schema 允许：

- `mt4_demo_readonly_file_bridge_enabled`

当前系统默认仍为 `docs_fixture_only`，不能因为本文档存在而启用 MT4 file bridge。

未来 schema 禁止：

- `mt4_live_readonly`
- `mt4_live_execution`
- `mt4_demo_execution`
- `unknown_live_source`
- `raw_terminal_export`

禁止 source mode 出现时必须 safety blocked。`source_mode` 不能被解释为交易许可、执行许可、EA 调用许可、风控放行或仓位计算许可。

## 9. 数据质量字段

每个文件未来可以包含以下数据质量字段：

- `data_quality_notes`
- `missing_fields`
- `stale_data_flags`
- `validation_warnings`
- `validation_blockers`

数据质量字段规则：

- `data_quality_notes` 使用 string[]。
- `missing_fields` 使用 string[]，只列安全字段名或安全摘要名。
- `stale_data_flags` 使用 string[]，只表示数据新旧状态。
- `validation_warnings` 使用 string[]，不等于交易建议。
- `validation_blockers` 使用 string[]，不等于交易指令。
- stale data 不等于买卖时机。
- validation 只服务于只读诊断。
- 数据质量字段不能包含账号密码、路径、traceback、raw payload、订单号或交易动作。

## 10. Forbidden Field Handling

未来 validators 必须按 fail-closed 处理 forbidden fields：

- 出现 forbidden field 时 blocked。
- 出现 `password` / `token` / `secret` 时 blocked。
- 出现 `order_send` / `order_close` / `order_modify` / `order_delete` 等执行字段时 blocked。
- 出现 `suggested_lot` / `final_lot` 时 blocked。
- 出现 `buy_now` / `sell_now` 时 blocked。
- 出现 `raw_payload` 时 blocked。
- blocked 结果不能把 forbidden field 原文暴露给 UI。
- blocked 结果不能把可疑字段值透传到 API。
- blocked 结果只能返回安全摘要。
- forbidden field checker 必须覆盖顶层字段、嵌套字段和数组元素中的对象字段。

safe summary 示例语义：

```text
blocked=true
status_code=FORBIDDEN_FIELD_DETECTED
summary=Demo readonly file contains forbidden execution or sensitive fields.
is_tradable=false
can_execute=false
```

该摘要不能包含真实密码、真实 token、真实账号、真实路径、真实订单号或 raw payload。

## 11. 与 PathGuard / Filename Whitelist 的关系

schema validation 必须发生在 PathGuard 和 filename whitelist 之后。

未来读取顺序必须是：

```text
Configured demo readonly input directory
-> PathGuard
-> FilenameWhitelist
-> ExtensionWhitelist
-> JSON object reader
-> SchemaValidator
```

路径和文件名规则：

- 未来只能验证白名单文件。
- 不能验证任意用户文件。
- 不能自动搜索文件系统。
- 不能递归扫描用户目录。
- 不能读取 Desktop / Downloads / Documents 任意文件。
- 不能读取 `.env`。
- 不能读取 logs。
- 不能读取 database。
- 不能读取 MT4 terminal 敏感配置目录。
- 不能跟随 symlink 绕过允许目录。
- 不能接受 path traversal。

schema validator 不能自己发起文件发现，也不能接收任意路径字符串后直接读取。

## 12. 与 Diagnostics / Explanation 的关系

未来数据流必须是：

```text
MT4 demo readonly file
-> PathGuard
-> FilenameWhitelist
-> SchemaValidator
-> ForbiddenFieldChecker
-> DataQualityGate
-> DemoReadOnlyDiagnosticsSummary
-> Explanation
-> Frontend Mapper
-> Dashboard
```

链路规则：

- schema 不能直接进入 Dashboard。
- schema 不能直接进入 ExplanationPanel。
- schema 不能绕过 summary。
- schema 不能绕过 safety flags。
- schema 不能生成交易建议。
- schema 不能生成执行指令。
- schema 不能触发 RiskGate、PositionSizing 或 ExecutionGate。
- schema 不能生成 `TradePlan`。
- schema 不能调用 EA。
- schema 不能返回或展示完整 raw payload。

Diagnostics 只接收安全摘要。Explanation 只解释安全摘要。Frontend Mapper 只接收白名单字段。Dashboard 只展示只读诊断和只读解释。

## 13. 未来测试规划

未来 validators 至少需要覆盖：

- valid `account_snapshot` passes schema。
- valid `positions_order_history` passes schema。
- valid `market_symbol` passes schema。
- missing safety flags blocked。
- `read_only=false` blocked。
- `demo_only=false` blocked。
- `can_execute=true` blocked。
- `is_tradable=true` blocked。
- password field blocked。
- account_number field blocked。
- ticket / order_id field blocked。
- `order_send` / `order_close` blocked。
- `suggested_lot` / `final_lot` blocked。
- `buy_now` / `sell_now` blocked。
- `raw_payload` blocked。
- unknown `schema_version` blocked。
- forbidden source mode blocked。
- unknown fields rejected or dropped according to explicit policy。
- no raw forbidden values leak to summary / API / UI。
- validators do not read real `data/` files。
- validators use temporary test fixtures only。

测试必须继续确认 `is_tradable=false`、`can_execute=false`、`is_trading_permission=false`、`is_execution_instruction=false`。

## 14. 当前仍不实现

当前 1U-2 工单仍不实现：

- 不实现 validators。
- 不实现 reader。
- 不实现 PathGuard。
- 不实现 filename whitelist。
- 不实现 source summary adapter。
- 不接 MT4。
- 不读 MT4 文件。
- 不读模拟账号真实数据。
- 不读真实账号数据。
- 不读 `data/` 运行目录。
- 不写 EA。
- 不写 MQL4。
- 不新增 API。
- 不修改 Dashboard。
- 不新增交易能力。
- 不新增执行能力。
- 不新增 RiskGate。
- 不新增 PositionSizing。
- 不新增 ExecutionGate。
- 不新增 TradePlanSchema。
- 不新增 Agent。
- 不新增 LLM。

当前唯一预期产物是本文档。本文档存在不代表 MT4 file bridge 已启用，不代表 schema validator 已实现，不代表系统可以读取 MT4 文件。

## 15. 验收边界

1U-2 完成时，必须确认：

- 本文档存在。
- 本文档说明本轮只写 schema 契约。
- 本文档说明本轮不实现 validator。
- 本文档说明本轮不读取 MT4 文件。
- 本文档定义全局 safety flags。
- 本文档定义 `account_snapshot.json` schema。
- 本文档定义 `positions_order_history.json` schema。
- 本文档定义 `market_symbol.json` schema。
- 本文档定义字段类型规则。
- 本文档定义 `schema_version`。
- 本文档定义 `source_mode`。
- 本文档定义数据质量字段。
- 本文档定义 forbidden field handling。
- 本文档说明与 PathGuard / filename whitelist 的关系。
- 本文档说明与 diagnostics / explanation 的关系。
- 本文档规划未来测试。
- 本文档说明当前仍不实现代码。

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
