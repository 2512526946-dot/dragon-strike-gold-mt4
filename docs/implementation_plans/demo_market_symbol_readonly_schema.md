# DemoMarketAndSymbolReadOnly Schema Contract

本文定义未来 MT4 demo account 第一阶段只读连接时的行情、点差、交易品种规格、交易环境状态数据契约和示例 JSON。当前阶段只定义格式，不实现读取逻辑，不接 MT4，不写 EA，不写 API。

## 定位

DemoMarketAndSymbolReadOnly 是未来 MT4 demo-only 只读阶段的行情、点差与品种规格快照。它只用于读取模拟账号环境下的行情和 symbol spec，并作为后续只读展示、DataQualityGate、RiskGate、PositionSizing、ExecutionGate 和复盘系统的输入之一。

DemoMarketAndSymbolReadOnly 必须明确：

- DemoMarketAndSymbolReadOnly 是未来 MT4 demo-only 只读阶段的行情、点差与品种规格快照。
- DemoMarketAndSymbolReadOnly 只用于读取模拟账号环境下的行情和 symbol spec。
- DemoMarketAndSymbolReadOnly 不是交易信号。
- DemoMarketAndSymbolReadOnly 不是交易计划。
- DemoMarketAndSymbolReadOnly 不是交易许可。
- DemoMarketAndSymbolReadOnly 不触发 EA 执行。
- DemoMarketAndSymbolReadOnly 不保存账号密码。
- DemoMarketAndSymbolReadOnly 不保存登录凭证。
- DemoMarketAndSymbolReadOnly 不允许 live account。
- 当前阶段只定义格式，不实现读取逻辑，不接 MT4，不写 EA，不写 API。

## 数据用途

该快照未来用于：

- 只读展示当前 XAUUSD Bid / Ask。
- 只读展示点差。
- 帮助 DataQualityGate 判断 tick 是否新鲜。
- 帮助 DataQualityGate 判断 symbol spec 是否完整。
- 帮助 RiskGate 判断点差是否异常。
- 帮助 RiskGate 判断市场是否开盘。
- 帮助 RiskGate 判断是否处于重大数据窗口。
- 帮助 PositionSizing 获取 tick_size / tick_value / contract_size / min_lot / lot_step。
- 帮助 ExecutionGate 判断 EA 执行前行情环境是否仍有效。
- 帮助复盘系统理解模拟交易发生时的行情环境。

同时必须明确：

- 当前不实现 DataQualityGate 新逻辑。
- 当前不实现 RiskGate。
- 当前不实现 PositionSizing。
- 当前不实现 ExecutionGate。
- 当前不实现 reader。
- 当前不实现 API。
- 当前不执行任何交易。
- 当前不接账号。

## 最小结构

DemoMarketAndSymbolReadOnly 示例结构见 `demo_market_symbol_readonly.example.json`。示例只用于格式说明，不得被当作交易信号、交易计划、交易许可、订单指令、EA 命令或自动交易记录。

关键结构包括：

- 顶层元数据：`schema_version`、`record_type`、`generated_at`、`source`、`account_mode`。
- 只读模拟账号摘要：`demo_account`。
- 品种标识：`symbol`。
- 行情快照：`quote`。
- 品种规格：`symbol_spec`。
- 市场与交易环境状态：`market_session`。
- 只读风控特征能力说明：`risk_readonly_features`。
- 桥接状态：`bridge_status`。
- 安全标记：`safety_flags`。
- 安全说明：`note`。

## 字段规则

DemoMarketAndSymbolReadOnly 字段规则：

- `record_type` 必须为 `demo_market_symbol_readonly`。
- `account_mode` 必须为 `demo_only`。
- `demo_account.is_demo_account` 必须为 `true`。
- `demo_account.is_live_account` 必须为 `false`。
- `demo_account.account_number` 当前示例必须为 `null`，避免提交真实账号。
- `symbol` 当前优先为 `XAUUSD`。
- `quote.bid` / `quote.ask` 必须存在。
- `quote.ask` 必须大于或等于 `quote.bid`。
- `quote.spread` 必须大于或等于 `0`。
- `quote.last_tick_time` 必须存在。
- `symbol_spec.tick_size` / `symbol_spec.tick_value` / `symbol_spec.contract_size` / `symbol_spec.min_lot` / `symbol_spec.lot_step` 是未来 PositionSizing 的输入，但本轮不实现 PositionSizing。
- 不允许包含账号密码。
- 不允许包含登录凭证。
- `safety_flags.demo_only` 必须为 `true`。
- `safety_flags.is_tradable` 必须为 `false`。
- `safety_flags.can_execute` 必须为 `false`。
- `safety_flags.contains_credentials` 必须为 `false`。
- `safety_flags.contains_password` 必须为 `false`。
- `safety_flags.contains_live_account` 必须为 `false`。
- `note` 必须明确只读模拟行情数据、不是交易建议、不是交易许可、不是订单指令、不是自动交易。

## Quote

`quote` 用于记录只读行情快照。

建议字段包括：

- `bid`
- `ask`
- `mid`
- `spread`
- `spread_points`
- `last_tick_time`
- `last_update_age_seconds`
- `data_freshness_status`

`quote` 只用于行情上下文、数据质量检查和复盘，不是交易信号，不是交易许可，不触发 EA。

## Symbol Spec

`symbol_spec` 用于记录未来仓位计算和风控需要的品种规格。

建议字段包括：

- `digits`
- `point`
- `tick_size`
- `tick_value`
- `contract_size`
- `min_lot`
- `max_lot`
- `lot_step`
- `stop_level_points`
- `freeze_level_points`
- `margin_currency`
- `profit_currency`

这些字段是未来 PositionSizing 的候选输入，但当前不实现 PositionSizing，不计算手数，不生成任何交易建议，不证明可以执行。

## Market Session

`market_session` 用于描述只读市场环境状态。

建议字段包括：

- `market_open`
- `trade_allowed_by_broker`
- `session_label`
- `is_major_news_window`
- `is_rollover_window`
- `is_weekend`

`trade_allowed_by_broker` 只表示经纪商层面的环境状态，不等于系统允许交易，不等于 ExecutionGate 通过，也不等于实盘许可。

## Risk Readonly Features

`risk_readonly_features` 只描述该快照未来可支持哪些只读风险判断输入，不表示当前已实现 DataQualityGate 新逻辑、RiskGate、PositionSizing 或 ExecutionGate。

建议字段包括：

- `can_check_spread`
- `can_check_tick_freshness`
- `can_check_market_open`
- `can_check_symbol_spec`
- `can_support_position_sizing_inputs`

这些字段是能力声明，不是交易许可，不是执行许可，也不是策略结果。

## Bridge Status

`bridge_status` 用于记录未来只读桥接状态：

- `read_only`
- `bridge_status_code`
- `data_quality_hint`

`bridge_status.read_only` 必须为 `true`。数据过期、点差异常、市场未开盘或 symbol spec 缺失时，未来必须阻断或警告，不得继续执行任何计划。

## 与既有 MT4 文件格式文档的关系

项目已有 `mt4/file_formats/live_tick.md`、`mt4/file_formats/latest_bars.md`、`mt4/file_formats/symbol_spec.md` 等 MT4 文件格式规划。

DemoMarketAndSymbolReadOnly 与这些文件的关系：

- 本文档面向 demo account read-only training 场景。
- 本文档不替代既有 MT4 文件格式。
- 本文档是 demo-only 只读聚合快照契约。
- 后续实现时可以复用或映射既有 MT4 文件格式字段。
- 当前不实现映射代码。

## 安全边界

DemoMarketAndSymbolReadOnly 必须遵守：

- 该快照不能直接驱动交易。
- 该快照不能作为执行许可。
- 该快照不能证明可以下单。
- 该快照不能用于 live account。
- live account 检测到时未来必须阻断。
- 数据过期时未来必须阻断。
- 点差异常时未来必须阻断或警告。
- 市场未开盘时未来必须阻断。
- symbol spec 缺失时未来必须阻断。
- 任何执行都必须经过 DataQualityGate / RiskGate / PositionSizing / ExecutionGate。
- 第一阶段只读，不执行。

## 与后续模块关系

该快照未来可作为以下模块的输入之一：

- DataQualityGate：检查 tick 新鲜度、symbol spec 完整性、行情字段基本质量。
- RiskGate：识别点差异常、市场未开盘、重大数据窗口、周末或 rollover 风险。
- PositionSizing：读取 tick_size、tick_value、contract_size、min_lot、max_lot、lot_step。
- ExecutionGate：在执行前复核行情环境是否仍有效。
- 复盘系统：理解模拟交易发生时的行情环境。

该快照不负责：

- 不生成交易方向。
- 不生成交易理由。
- 不计算仓位。
- 不计算风险。
- 不决定是否执行。
- 不绕过 DataQualityGate / RiskGate / PositionSizing / ExecutionGate。

## 本轮不实现

本轮只新增文档和示例 JSON，不实现任何代码。

本轮不实现：

- 不实现 MT4 EA。
- 不实现 MQL4。
- 不接入 MT4 模拟账号。
- 不接入真实 MT4。
- 不保存账号密码。
- 不保存登录凭证。
- 不实现后端 reader。
- 不新增后端 API。
- 不修改前端页面。
- 不新增交易策略。
- 不新增 DataQualityGate 新逻辑。
- 不新增 TradePlanSchema 代码。
- 不新增 ExecutionAuditLog 代码。
- 不新增 RiskGate 代码。
- 不新增 PositionSizing 代码。
- 不新增 ExecutionGate 代码。
- 不新增执行 API。
- 不新增自动交易。
- 不返回任何真实交易建议。
