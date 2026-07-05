# MultiAgentTradingDepartmentArchitecture

本文定义“巨龙出击”的多智能体交易部门式架构。

本轮只做架构文档，不实现 Agent 代码、LLM 调用、prompt 执行器、后端 API、前端页面、MT4 EA、MQL4、执行 API 或自动交易。

## 文件用途

该文档用于描述未来“多专业智能体 + 一个总决策智能体”的协作方式。

核心原则：

- 专业智能体像员工，负责专项分析。
- `DragonDecisionAgent` 像部门经理，负责综合汇总。
- 硬闸门负责最终安全否决。
- 智能体负责解释、建议、复盘，不负责自由执行。

智能体不能自由下单，不能修改风控规则，不能绕过硬闸门，不能直接调用 EA。总决策智能体也不能绕过 `DataQualityGate`、`RiskGate`、`PositionSizing`、`ExecutionGate`。

任何硬闸门 `BLOCK` 时，最终只能输出禁止交易、只允许观察、只允许平仓或需要风险复核等安全状态，不得输出交易许可。

## 总体架构

未来系统可以拆成四层。

### 硬闸门层

硬闸门层负责“能不能”。

- `DataQualityGate`
- `RiskGate`
- `PositionSizing`
- `ExecutionGate`

硬闸门是系统安全边界。它们的结果优先于所有智能体观点。

### 专业智能体层

专业智能体层负责“为什么”。

- `DataQualityAgent`
- `MarketStructureAgent`
- `MacroEventAgent`
- `RiskAgent`
- `PositionSizingAgent`
- `ReviewAgent`

专业智能体只能解释状态、归纳原因、形成观察报告、提示风险。它们不能绕过硬闸门，不能生成执行许可，不能直接触发交易。

### 总决策层

总决策层负责“如何表达最终结论”。

- `DragonDecisionAgent`

`DragonDecisionAgent` 汇总硬闸门状态和各专业智能体报告，输出最终安全表达。它不是执行器，也不是硬闸门替代品。

### 审计复盘层

审计复盘层负责“事后追责和训练数据积累”。

- `ExecutionAuditLog`
- `ReviewAttributionPolicy`
- `PaperReviewResult`
- `ManualExecutionEvent`

审计复盘层只能记录、归因、复盘和积累训练数据，不得反向修改硬闸门结果，不得把纸面复盘结果当成真实 PnL。

## 专业智能体职责

### DataQualityAgent

职责：

- 解释 `DataQualityGate` 的结果。
- 说明数据是否过期。
- 说明价格是否缺失。
- 说明点差是否异常。
- 说明账户净值是否可用。
- 说明哪些字段缺失或异常。

边界：

- `DataQualityAgent` 不能替代 `DataQualityGate`。
- `DataQualityAgent` 不能自行判定数据通过。
- `DataQualityAgent` 只能解释硬闸门结果。
- `DataQualityGate BLOCK` 时，`DataQualityAgent` 只能说明阻断原因。

### MarketStructureAgent

职责：

- 分析黄金行情结构。
- 判断趋势上涨、趋势下跌、震荡、突破、假突破、高波动混乱等结构状态。
- 输出 observation-only 的市场结构解释。

边界：

- `MarketStructureAgent` 不能直接输出买入或卖出指令。
- `MarketStructureAgent` 不能绕过硬闸门。
- 市场结构观点只能作为观察输入，不等于执行许可。

### MacroEventAgent

职责：

- 分析宏观事件风险。
- 关注 CPI、非农、FOMC、鲍威尔讲话、美元指数、美债收益率、重大新闻风险。

边界：

- 没有可靠宏观日历或新闻源时，`MacroEventAgent` 只能输出 `unknown`。
- `MacroEventAgent` 不能编造宏观事件。
- `MacroEventAgent` 不能凭空声称存在重大数据。
- 当前阶段不接入真实宏观数据源。

### RiskAgent

职责：

- 解释 `RiskGate` 的风险状态。
- 说明今日亏损是否接近上限。
- 说明是否连续亏损。
- 说明是否只能观察、只允许平仓或禁止开仓。
- 提醒用户风险。

边界：

- `RiskAgent` 不能替代 `RiskGate`。
- `RiskAgent` 不能自行放行交易。
- `RiskAgent` 只能解释风险状态。
- `RiskGate BLOCK` 时，`RiskAgent` 只能解释 `BLOCK` 原因。

### PositionSizingAgent

职责：

- 解释仓位设计逻辑。
- 说明账户净值、止损距离、风险比例、`tick_value`、`lot_step` 等如何影响手数。
- 解释 `PositionSizing` 程序计算结果。

边界：

- `PositionSizingAgent` 不能直接决定最终手数。
- 最终手数必须由 `PositionSizing` 程序硬计算。
- `PositionSizingAgent` 不能覆盖 `PositionSizing` 结果。
- 智能体不能放大风险。

### ReviewAgent

职责：

- 复盘用户行为。
- 判断是否追单。
- 判断是否连续亏损后想扳回。
- 判断当前场景是否类似历史亏损场景。
- 输出行为提醒。

边界：

- `ReviewAgent` 不能修改交易结果。
- `ReviewAgent` 不能把纸面结果当真实 PnL。
- `ReviewAgent` 不能直接触发交易。

### DragonDecisionAgent

职责：

- 汇总所有专业智能体报告。
- 汇总硬闸门状态。
- 输出最终安全表达。
- 给出当前动作、方向偏好、是否允许计划、主要理由、风险点、等待条件、失效条件和复盘提醒。

边界：

- `DragonDecisionAgent` 不能绕过 `DataQualityGate`。
- `DragonDecisionAgent` 不能绕过 `RiskGate`。
- `DragonDecisionAgent` 不能绕过 `PositionSizing`。
- `DragonDecisionAgent` 不能绕过 `ExecutionGate`。
- `DragonDecisionAgent` 不能直接调用 EA。
- `DragonDecisionAgent` 不能自由下单。

`DragonDecisionAgent` 的价值是汇总和表达，而不是放行、执行或覆盖硬规则。

## 硬闸门优先级

硬闸门 veto 规则必须明确：

- `DataQualityGate BLOCK` > 所有智能体观点。
- `RiskGate BLOCK` > 所有智能体观点。
- `PositionSizing BLOCK` > 所有智能体观点。
- `ExecutionGate BLOCK` > 所有智能体观点。

即使 `MarketStructureAgent` 看多，即使 `MacroEventAgent` 认为无重大事件，即使 `DragonDecisionAgent` 想形成计划，只要任何硬闸门 `BLOCK`，最终只能输出：

- `blocked`
- `observe_only`
- `close_only`
- `risk_review_required`

不得输出交易许可。

## 推荐最终动作枚举

最终动作枚举应使用安全状态，不直接使用买或卖作为最终动作。

建议枚举：

- `observe_only`
- `blocked`
- `plan_candidate`
- `manual_confirm_required`
- `close_only`
- `risk_review_required`
- `data_invalid`
- `wait_for_confirmation`
- `review_only`

这些动作不是订单，不是 EA 指令，不是实盘交易建议，也不是自动交易许可。

## 方向表达规则

可以在 `TradePlan` 或观察计划中使用候选方向：

- `long_candidate`
- `short_candidate`
- `neutral_candidate`

不得直接使用以下字段表达业务结论：

- `should_buy`
- `should_sell`
- `can_trade`
- `allow_trade`
- `auto_buy`
- `auto_sell`

方向候选不等于执行许可。方向候选只能表示观察偏好或计划草案中的候选状态。

## AgentReportSchema 规划

未来可以规划 `AgentReportSchema`，但本轮不实现代码。

建议字段：

- `agent_name`
- `agent_role`
- `input_summary`
- `findings`
- `confidence_level`
- `status`
- `block_reasons`
- `warning_reasons`
- `cannot_override_gates`
- `is_trading_permission`
- `is_execution_instruction`

约束：

- `is_trading_permission` 必须为 `false`。
- `is_execution_instruction` 必须为 `false`。
- `AgentReport` 不能驱动交易。
- `AgentReport` 不能覆盖硬闸门。
- `AgentReport` 不能修改风控规则。

## DragonDecisionReportSchema 规划

未来可以规划 `DragonDecisionReportSchema`，但本轮不实现代码。

建议字段：

- `final_action`
- `direction_bias`
- `trade_plan_allowed`
- `manual_confirm_required`
- `gate_summary`
- `agent_summary`
- `main_reasons`
- `risk_points`
- `wait_conditions`
- `invalidation_conditions`
- `review_reminders`
- `is_trading_permission`
- `can_execute`
- `requires_execution_gate`

约束：

- `is_trading_permission` 必须为 `false`。
- `can_execute` 必须为 `false`，除非未来 `ExecutionGate` 单独通过。
- `requires_execution_gate` 必须为 `true`。
- 当前阶段始终不能执行。

`DragonDecisionReport` 可以表达“为什么等待”“为什么阻断”“为什么只观察”，但不能直接表达自动执行。

## 开发顺序

建议未来开发顺序：

1. 阶段 1：只写多智能体架构文档。
2. 阶段 2：定义 `AgentReportSchema`。
3. 阶段 3：定义 `DragonDecisionReportSchema`。
4. 阶段 4：实现 `DataQualityAgent` 只读解释版。
5. 阶段 5：实现 `RiskAgent` 只读解释版。
6. 阶段 6：实现 `PositionSizingAgent` 解释版。
7. 阶段 7：实现 `MarketStructureAgent` observation-only 版本。
8. 阶段 8：实现 `ReviewAgent`。
9. 阶段 9：最后再考虑 `MacroEventAgent`，且必须有可靠数据源。
10. 阶段 10：仍然不允许自由下单。

当前工单只做阶段 1。

## 与 Demo-Only 执行链路的关系

多智能体输出即使未来进入 demo-only 半自动阶段，也必须经过：

1. `TradePlan`
2. `DataQualityGate`
3. `RiskGate`
4. `PositionSizing`
5. `ExecutionGate`
6. `ManualConfirmFlow` / `AutoDemoTrainingMode`
7. `MT4 EA demo-only`

智能体不能跳过以上任何步骤。

智能体不能把观察、候选方向或复盘提醒转换成执行动作。`ExecutionGate` 之前没有执行许可；`ExecutionGate` 未通过时必须保持阻断。

## 安全边界

多智能体架构必须遵守：

- 不自动下单。
- 不生成真实交易建议。
- 不修改风控规则。
- 不保存凭证。
- 不接 live account。
- 不允许智能体直接调用 EA。
- 不允许智能体开启 `AutoDemoTrainingMode`。
- 不允许智能体修改 `PositionSizing`。
- 不允许智能体覆盖 `RiskGate`。
- 不允许智能体绕过 `ExecutionGate`。
- 不允许马丁。
- 不允许网格。
- 不允许无止损执行。
- 不允许隔夜执行。

任何智能体输出都必须低于硬闸门优先级。任何安全边界冲突，都必须默认阻断。

## 当前仍不实现

本轮不实现：

- 不实现 Agent 代码。
- 不实现 `AgentReportSchema` 代码。
- 不实现 `DragonDecisionAgent` 代码。
- 不实现 `DragonDecisionReportSchema` 代码。
- 不实现 LLM 调用。
- 不实现 prompt 执行器。
- 不实现后端 API。
- 不实现前端页面。
- 不实现 MT4 EA。
- 不实现 MQL4。
- 不接 MT4。
- 不接模拟账号。
- 不保存凭证。
- 不实现自动交易。

