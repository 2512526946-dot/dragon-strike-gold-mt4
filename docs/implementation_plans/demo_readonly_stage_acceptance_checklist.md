# DemoReadOnlyStageAcceptanceChecklist

本文定义进入 MT4 demo-only 只读 reader、只读 API、前端只读展示之前必须满足的验收条件。

该清单的目的不是推进接入，而是防止过早接账号、过早开放 API、过早进入执行链路。当前阶段仍然只允许基于 docs 示例 JSON 和只读契约做验证，不允许读取 `data/` 运行文件，不允许接入 MT4，不允许产生交易建议或执行许可。

## 文件用途

本文件用于定义未来进入 demo-only 只读 reader / API / 前端展示之前的验收条件。

在满足本文全部准入项之前，项目不得：

- 接入 MT4 模拟账号。
- 接入真实 MT4。
- 读取真实运行数据。
- 暴露 demo account 只读 API。
- 在前端展示 demo account 只读数据。
- 将只读数据接入任何执行链路。

## 当前已完成能力

当前项目已经完成以下 demo-only 只读契约与校验能力：

- DemoAccountReadOnlySnapshot schema。
- DemoPositionsOrderHistory schema。
- DemoMarketSymbolReadOnly schema。
- DemoAccountReadOnlySnapshot validator。
- DemoPositionsOrderHistory validator。
- DemoMarketSymbolReadOnly validator。
- DemoReadOnlyValidationBundle。
- 当前测试通过数量为 `207 passed, 1 warning`。
- 当前所有校验仍基于 docs 示例 JSON。
- 当前没有读取 `data/` 运行文件。
- 当前没有接 MT4。
- 当前没有 API。
- 当前没有前端展示。

当前能力只证明 demo-only 只读契约、单项 validator 和 bundle validator 可以在示例数据上通过测试。它不证明系统可以连接账号，不证明可以读取真实行情，不证明可以交易，也不证明可以执行任何计划。

## 进入 Demo-Only 只读 Reader 前必须满足

进入 demo-only 只读 reader 之前，必须满足：

- 三个 schema 已封版。
- 三个 validator 已封版。
- validation bundle 已封版。
- 所有 validator 输出 `is_tradable=false`。
- 所有 validator 输出 `can_execute=false`。
- bundle 输出 `is_tradable=false`。
- bundle 输出 `can_execute=false`。
- live account 必须阻断。
- `account_number` 非 null 必须阻断。
- `contains_password` / `contains_credentials` 必须阻断。
- 示例 JSON 必须全部通过。
- 危险字段测试必须全部覆盖。
- 不得读取 `data/` 运行文件。
- 不得保存账号密码。
- 不得保存登录凭证。

Reader 规划完成前，所有测试输入只能来自 docs 示例 JSON 或明确的 mock / fixture，不得来自真实 MT4 文件、真实账号快照、真实持仓、真实订单历史或真实行情。

## 进入 Demo-Only 只读 API 前必须满足

进入 demo-only 只读 API 之前，必须满足：

- reader 阶段先完成。
- reader 只能读取白名单路径。
- reader 不得自动修复数据。
- reader 不得写入文件。
- reader 不得返回交易建议。
- reader 不得返回执行许可。
- API 只能返回只读诊断。
- API 不能返回买入 / 卖出 / 开仓 / 平仓 / 建议手数 / 允许交易 / 可以交易。
- API 响应中必须明确 `demo-only`、`read-only`、`is_tradable=false`、`can_execute=false`。

API 只能把 reader 和 validator 的只读状态、阻断原因、警告原因、数据质量摘要暴露给前端或调试工具。API 不得包装成交易信号，不得把经纪商状态解释成系统许可，不得生成任何执行动作。

## 进入 Demo-Only 前端展示前必须满足

进入 demo-only 前端展示之前，必须满足：

- API 已只读封版。
- 前端只展示状态，不展示交易建议。
- 前端不得展示下单按钮。
- 前端不得展示确认交易按钮。
- 前端不得展示自动训练开关。
- 前端必须显示 `demo-only`。
- 前端必须显示 `read-only`。
- 前端必须显示不是交易许可。
- 前端必须显示不能自动执行。

前端展示只能帮助用户理解 demo-only 只读数据状态、诊断状态和阻断原因。它不得诱导下单，不得展示可执行操作，不得展示任何买卖方向、建议手数或交易许可。

## 禁止事项

本阶段及进入后续 demo-only 只读阶段前，明确禁止：

- 不允许实盘。
- 不允许保存账号密码。
- 不允许保存登录凭证。
- 不允许智能体直接下单。
- 不允许 EA 执行。
- 不允许自动交易。
- 不允许绕过 DataQualityGate。
- 不允许绕过 RiskGate。
- 不允许绕过 PositionSizing。
- 不允许绕过 ExecutionGate。
- 不允许马丁。
- 不允许网格。
- 不允许隔夜执行。
- 不允许无止损执行。
- 不允许把只读数据当作交易许可。

只读数据只能作为状态输入或诊断输入。即使所有只读数据通过校验，也仍然不是交易建议，不是交易计划，不是执行许可，也不是自动交易入口。

## 阶段推进建议

未来建议按以下顺序推进：

- 阶段 A：demo-only reader 白名单规划文档。
- 阶段 B：demo-only reader 读取 docs / mock fixture，不读真实 `data/`。
- 阶段 C：demo-only reader 读取本地 sandbox fixture。
- 阶段 D：只读 API。
- 阶段 E：前端只读展示。
- 阶段 F：再讨论 MT4 demo read-only bridge。
- 阶段 G：仍不进入执行。

在 MT4 demo read-only bridge 之前，还必须完成 reader 白名单、路径安全、fixture 测试、API 只读审查。

任何阶段推进都必须保持：

- 默认阻断。
- 默认只读。
- 默认不执行。
- 默认不暴露凭证。
- 默认不返回交易建议。

## 当前仍不实现

本轮只新增验收清单文档，不实现任何代码。

本轮不实现：

- 不实现 reader。
- 不实现 API。
- 不实现 frontend。
- 不接 MT4。
- 不写 EA。
- 不写 MQL4。
- 不保存凭证。
- 不实现 RiskGate。
- 不实现 PositionSizing。
- 不实现 ExecutionGate。
- 不实现执行 API。
- 不实现自动交易。

