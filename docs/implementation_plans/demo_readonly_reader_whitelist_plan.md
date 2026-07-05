# DemoReadOnlyReaderWhitelistPlan

本文定义未来 demo-only 只读 reader 的路径白名单、禁止路径、读取顺序、路径安全规则、错误处理规则和安全边界。

本文件只做规划，不实现 reader、parser、API、前端页面、MT4 bridge、EA、MQL4、风控、仓位计算或执行链路。

## 文件用途

本文用于明确未来 demo-only 只读 reader：

- 只能读取哪些固定文件。
- 不能读取哪些路径和文件类型。
- 如何防止路径越界和敏感文件误读。
- 如何处理读取、解析和校验失败。
- 如何把 fixture payload 交给现有 validator 和 validation bundle。
- 如何在进入真实 MT4 demo bridge 之前保持只读、安全、不可执行边界。

该文档不是 reader 实现说明，不授权读取 `data/` 运行文件，不授权连接 demo account，不授权连接真实 MT4，也不授权返回任何交易建议或执行许可。

## Reader 定位

未来 demo-only reader 的职责必须被限制为读取白名单内的 JSON fixture 文件。

Reader 必须满足：

- Reader 只负责读取文件。
- Reader 只读取固定白名单路径。
- Reader 不写入文件。
- Reader 不修改文件。
- Reader 不修复数据。
- Reader 不补全字段。
- Reader 不生成交易建议。
- Reader 不生成交易许可。
- Reader 不计算手数。
- Reader 不触发 EA。
- Reader 不连接 MT4。
- Reader 不连接模拟账号。
- Reader 不连接真实账号。
- Reader 不保存账号密码。
- Reader 不保存登录凭证。
- Reader 读取后必须交给 validator / validation bundle。
- Reader 不得绕过 validator。

Reader 不是 DataQualityGate、RiskGate、PositionSizing、ExecutionGate 或自动交易入口。Reader 的输出即使全部通过，也只能作为只读诊断输入。

## 第一阶段允许读取的文件

第一版 reader 只能读取 docs 示例 fixture，优先使用已有 docs 示例。

允许读取：

- `docs/implementation_plans/demo_account_readonly_snapshot.example.json`
- `docs/implementation_plans/demo_positions_order_history.example.json`
- `docs/implementation_plans/demo_market_symbol_readonly.example.json`

这些文件只是示例 fixture，不是真实 demo account 数据，不包含真实账号、真实行情、真实持仓或真实订单历史。

第一阶段不得读取 `data/` 运行目录，不得从 MT4 输出目录读取文件，不得扫描项目目录寻找替代输入。

## 后续可规划的 Fixture 路径

后续阶段可以单独规划本地 sandbox fixture 路径：

- `fixtures/demo_readonly/account_snapshot.example.json`
- `fixtures/demo_readonly/positions_order_history.example.json`
- `fixtures/demo_readonly/market_symbol.example.json`

这些路径只是未来规划。本轮不创建这些文件，不读取这些路径，不提交任何真实数据。

若未来要启用这些路径，必须单独工单、单独审查、单独测试，并继续保持 demo-only / read-only / no execution 边界。

## 禁止读取的路径

未来 reader 必须明确禁止读取：

- `.env`
- `.env.*`
- 任何包含 `password` / `credential` / `secret` / `token` / `key` / `login` 的文件。
- `data/signals/*`
- `data/ml/*`
- `data/mt4/*`
- `logs/*`
- `*.log`
- `*.db`
- `*.sqlite`
- `*.duckdb`
- `frontend/dist/*`
- `frontend/node_modules/*`
- `models/*`
- `__pycache__/*`
- `.pytest_cache/*`
- 任何真实 MT4 账号数据。
- 任何真实模拟账号数据。
- 任何真实行情数据。
- 任何真实持仓数据。
- 任何真实订单历史。
- 任何真实交易日志。
- 任何真实账户快照。
- 任何真实凭证或账号安全相关文件。

禁止路径命中时必须阻断。不得尝试 fallback 到其他路径，不得尝试猜测同名文件，不得自动创建默认文件。

## 路径安全规则

未来 reader 必须遵守以下路径安全规则：

- 使用固定白名单。
- 禁止用户任意传入路径。
- 禁止绝对路径。
- 禁止 `..` 路径穿越。
- 禁止符号链接跳出项目目录。
- 禁止读取项目目录外文件。
- 禁止读取隐藏文件。
- 禁止自动搜索文件系统。
- 禁止 fallback 到 `data/` 运行目录。
- 禁止读取扩展名不在白名单内的文件。
- 禁止读取超大文件。
- 禁止读取非 JSON fixture。
- 禁止读取任何运行时真实数据。
- 禁止在读取失败后尝试猜测路径。
- 禁止在读取失败后创建默认文件。
- 禁止在读取失败后修复源文件。

路径安全检查应发生在文件读取之前。任何路径安全检查失败，都必须返回阻断状态，而不是继续读取。

## 文件类型规则

当前 demo readonly reader 输入只允许 `.json` fixture。

当前不允许：

- `.jsonl`
- `.csv`
- `.parquet`
- `.db`
- `.sqlite`
- `.duckdb`
- `.log`
- `.env`

如果后续允许更多格式，必须单独工单、单独审查、单独测试。不得在 reader 中偷偷扩展格式支持。

## 读取后的处理流程

未来 reader 读取后必须走以下流程：

1. 读取 fixture。
2. 解析 JSON。
3. 根据 `record_type` 分发到对应 validator。
4. `DemoAccountReadOnlySnapshot` payload 调用 `DemoAccountReadOnlySnapshot` validator。
5. `DemoPositionsOrderHistory` payload 调用 `DemoPositionsOrderHistory` validator。
6. `DemoMarketSymbolReadOnly` payload 调用 `DemoMarketSymbolReadOnly` validator。
7. 三类 payload 进入 `DemoReadOnlyValidationBundle`。
8. 返回只读诊断 summary。

Reader 本身不能绕过 validator，不能忽略 validator 失败结果，不能把未通过校验的数据标记为可用。

## Reader 输出边界

未来 reader 输出必须保持：

- `read_only=true`
- `demo_only=true`
- `is_tradable=false`
- `can_execute=false`

Reader 输出不得返回：

- 交易建议。
- 执行许可。
- 建议手数。
- 买入。
- 卖出。
- 开仓。
- 平仓。
- 允许交易。
- 可以交易。
- 任何可下单指令。
- 任何自动执行指令。

Reader 输出只能表示读取状态、解析状态、校验状态、阻断原因、警告原因和只读诊断摘要。

## 错误处理规则

未来 reader 遇到以下情况必须失败或阻断：

- 文件不存在。
- 文件不在白名单。
- 路径越界。
- 文件过大。
- 文件扩展名不允许。
- JSON 解析失败。
- `record_type` 不匹配。
- `account_mode` 不是 `demo_only`。
- live account。
- `account_number` 非 null。
- `contains_password=true`。
- `contains_credentials=true`。
- `can_execute=true`。
- `is_tradable=true`。
- validator 不通过。
- validation bundle 不通过。
- symbol 不一致。
- account_alias 不一致。
- 任何组件缺失。
- 任何组件试图表达执行许可。

错误处理必须保守：默认阻断，默认不修复，默认不创建文件，默认不继续推进到 API 或前端展示。

## 与当前 Validator 的关系

未来 reader 必须复用当前 validator 和 validation bundle：

- `DemoAccountReadOnlySnapshot` reader 必须调用 `DemoAccountReadOnlySnapshot` validator。
- `DemoPositionsOrderHistory` reader 必须调用 `DemoPositionsOrderHistory` validator。
- `DemoMarketSymbolReadOnly` reader 必须调用 `DemoMarketSymbolReadOnly` validator。
- 聚合 reader 必须调用 `DemoReadOnlyValidationBundle`。
- Reader 不得复制校验逻辑绕过 validator。
- Reader 不得忽略 validator 失败结果。
- Reader 不得在 validator 失败时返回通过。
- Reader 不得把 validator warning 当成交易许可。
- Reader 输出仍然必须 `is_tradable=false`、`can_execute=false`。

Validator 和 bundle 是 reader 之后的安全闸门。Reader 只负责读取与分发，不负责判断可交易，不负责生成执行动作。

## 与未来 MT4 Demo Bridge 的关系

当前不接 MT4，当前不写 EA，当前不读真实 demo account。

当前 reader 白名单规划只是进入未来 bridge 前的保护层。未来 MT4 demo bridge 必须另开阶段。

Bridge 之前必须完成：

- Fixture reader。
- 路径白名单。
- 路径安全测试。
- 只读 API 审查。
- 前端只读展示审查。

未来 bridge 只能 demo-only。Live account 必须阻断。Bridge 不得保存账号密码，不得保存登录凭证，不得开放执行能力。

即使未来进入 MT4 demo bridge，reader 仍然不得返回交易建议、执行许可、建议手数或自动执行指令。

## 当前仍不实现

本轮只新增规划文档，不实现任何代码。

本轮不实现：

- 不实现 reader。
- 不实现 parser。
- 不实现 validator 新逻辑。
- 不实现 API。
- 不实现 frontend。
- 不接 MT4。
- 不接模拟账号。
- 不接真实账号。
- 不写 EA。
- 不写 MQL4。
- 不保存凭证。
- 不实现 RiskGate。
- 不实现 PositionSizing。
- 不实现 ExecutionGate。
- 不实现执行 API。
- 不实现自动交易。

