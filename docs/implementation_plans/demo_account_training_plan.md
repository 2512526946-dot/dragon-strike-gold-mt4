# demo_account_training_plan MT4 模拟账号训练方向设计

本文规划未来接入 MT4 模拟账号进行训练的方向。当前阶段只做文档设计，不实现 MT4 连接、EA、MQL4、执行 API、前端确认按钮、风控计算、仓位计算、ExecutionGate、TradePlan、ExecutionAuditLog、AutoDemoTrainingMode、机器学习训练或自动交易。

## 核心目标

未来巨龙出击可以连接用户的 MT4 模拟账号，用于读取模拟盘数据并提升训练效率、复盘质量和数据积累效率。未来可读取的数据包括：

- 模拟盘真实行情。
- Bid / Ask。
- 点差。
- 账户余额。
- 账户净值。
- 今日盈亏。
- 当前持仓。
- 订单历史。
- 成交。
- 盈亏。

当前阶段不接模拟账号，不接真实 MT4，不接真实行情，不读取真实账户，不保存登录凭证。

## 总体安全原则

- 只允许 Demo Account / 模拟账号。
- 第一阶段不允许实盘，不允许真实资金交易。
- 智能体不能直接自由下单。
- 智能体只有建议权。
- 风控模块有否决权。
- EA 只有在 ExecutionGate 通过后才允许执行。
- 所有执行必须经过 DataQualityGate、RiskGate、PositionSizing、ExecutionGate。
- 第一版优先做只读和半自动确认。
- 自动模拟交易必须后置，并且默认关闭。
- 实盘交易不在当前阶段范围内。

## 未来目标架构

```text
智能体生成交易计划
↓
DataQualityGate 检查数据是否可靠
↓
RiskGate 检查是否允许交易
↓
PositionSizing 硬计算手数
↓
ExecutionGate 检查是否允许执行
↓
用户确认 / 或后期 AutoDemoTrainingMode 开启
↓
MT4 EA 在模拟账号执行
↓
ExecutionAuditLog 记录执行前检查、是否通过、是否执行、执行结果
↓
复盘数据进入 observation / paper review / manual execution / demo execution review 链路
```

智能体不是执行者，不能绕过风控。RiskGate 和 ExecutionGate 都可以否决。EA 只执行被批准的命令。DemoAccountMode 必须在 UI 和后端状态中明确显示当前只处于模拟账号模式。

## 阶段 1：只读模拟账号

第一阶段只读，不执行任何交易。

MT4 EA 未来只读取数据，不下单。读取内容包括：

- 黄金价格。
- Bid / Ask。
- 点差。
- 账户余额。
- 账户净值。
- 今日盈亏。
- 当前持仓。
- 订单历史。
- 最后更新时间。

该阶段用于验证：

- MT4Bridge。
- DataQualityGate。
- 前端实时状态展示。

该阶段不执行任何交易，不生成真实交易建议，不允许实盘。

## 阶段 2：半自动模拟交易

第二阶段仍然只允许模拟账号。

智能体只能生成交易计划。交易计划必须包含：

- `direction`
- `entry_price`
- `stop_loss_price`
- `suggested_risk_percent`
- `suggested_lot`
- `max_loss_amount`
- `reason`

前端必须显示用户确认按钮。只有用户手动确认后，EA 才允许在模拟账号执行。

禁止执行条件：

- 没有止损价。
- 没有账户净值。
- 数据过期。
- 风控不通过。
- 非 demo 账号。

该阶段不允许实盘，不允许智能体直接下单。

## 阶段 3：极小手数自动模拟训练

第三阶段必须后置，且 AutoDemoTrainingMode 默认关闭。

限制：

- 只允许模拟账号。
- 初期最大手数限制为 0.01 手。
- 每天最多交易 3 笔。
- 每单必须带止损。
- 单笔最大风险不超过账户净值 1%。
- 初期建议默认 0.2% 到 0.3%。
- 连续亏损 2 笔自动暂停。
- 日亏损达到限制自动暂停。
- 重大数据前后禁止开新仓。
- 不允许马丁加仓。
- 不允许网格加仓。
- 不允许智能体修改风控规则。
- 不允许隔夜持仓。
- 不允许实盘。

AutoDemoTrainingMode 不能由智能体自行开启。

## 阶段 4：长期模拟验证

长期模拟验证至少需要：

- 50 到 100 次智能体判断记录。
- 30 到 50 笔模拟交易记录。
- 自动生成复盘报告。

统计内容包括：

- 智能体建议胜率。
- 盈亏比。
- 最大回撤。
- 常见错误。
- 是否违反纪律。
- 是否违反风控。

在没有足够模拟盘验证前，不允许进入实盘讨论。实盘交易仍不属于当前阶段。

## 未来模块规划

以下模块只是未来规划，本轮不得创建代码文件。

### ExecutionGate

ExecutionGate 是执行闸门，用于判断是否允许 EA 执行订单。它检查 DataQualityGate、RiskGate、PositionSizing、DemoAccountMode、ManualConfirmFlow、AutoDemoTrainingMode 状态，并可以否决任何交易计划。

### DemoAccountMode

DemoAccountMode 明确系统当前只能连接模拟账号。UI 和后端状态都必须显示 demo-only。非 demo 账户必须阻断。

### TradePlanSchema

TradePlanSchema 定义智能体输出的交易计划结构。它必须包含方向、入场价、止损价、风险比例、建议手数、最大亏损金额、理由。

TradePlan 不是订单，不是交易许可，必须经过闸门。

### ExecutionAuditLog

ExecutionAuditLog 记录每次执行前检查，包括 DataQualityGate、RiskGate、PositionSizing、ExecutionGate 结果、是否用户确认、是否发送给 EA、EA 返回结果、是否失败、拒绝或暂停。

ExecutionAuditLog 不记录密码，不记录敏感登录凭证。

### ManualConfirmFlow

ManualConfirmFlow 是半自动确认流程。用户在前端确认后才允许发送执行请求。未确认不得执行。确认不是风控豁免，用户确认后仍需 ExecutionGate 最终通过。

### AutoDemoTrainingMode

AutoDemoTrainingMode 是后期极小手数自动模拟训练模式。它默认关闭，只允许 demo，受严格次数、亏损、手数、止损、重大数据、隔夜限制。它不能用于实盘，不能由智能体自行开启。

## 当前模块现状

- DataQualityGate：已有 `backend/app/services/data_quality_gate.py` 和相关测试。
- RiskGate：当前未实现代码，只存在未来规划和安全边界。
- PositionSizing：当前未实现代码，只存在未来规划和仓位设计原则。
- ExecutionGate：当前未实现代码，本轮只新增规划。

## 本轮明确不做

本轮不实现：

- 不接 MT4。
- 不接模拟账号。
- 不保存账号密码。
- 不保存登录凭证。
- 不写 EA。
- 不写 MQL4。
- 不写 OrderSend。
- 不写 OrderClose。
- 不写 OrderModify。
- 不写 OrderDelete。
- 不写执行 API。
- 不写前端确认按钮。
- 不写风控计算。
- 不写仓位计算。
- 不写 ExecutionGate 代码。
- 不写 TradePlan 代码。
- 不写 ExecutionAuditLog 代码。
- 不写 AutoDemoTrainingMode 代码。
- 不开放自动交易。
- 不开放实盘交易。

## 安全边界

OrderSend、OrderClose、OrderModify、OrderDelete 等词只允许出现在禁止事项、安全边界或未来规划中，不能作为当前功能或可执行逻辑出现。

当前系统不得保存账号密码、登录凭证、真实 MT4 数据、真实交易日志或模拟账号真实运行数据。
