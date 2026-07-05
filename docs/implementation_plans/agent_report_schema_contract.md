# AgentReportSchema Contract

本文定义未来专业智能体统一输出的 `AgentReportSchema` 契约。

本轮只写文档，不实现 schema 代码、Pydantic model、Agent 代码、智能体类、LLM 调用、prompt 执行器、后端 API、前端页面、reader、parser、MT4 EA、MQL4 或自动交易。

## 文件用途

`AgentReport` 是专业智能体输出的分析报告，用于让 `DragonDecisionAgent` 汇总不同专业视角。

`AgentReport` 必须始终满足：

- `AgentReport` 是分析报告。
- `AgentReport` 不是交易许可。
- `AgentReport` 不是订单。
- `AgentReport` 不是 EA 指令。
- `AgentReport` 不能驱动自动交易。
- `AgentReport` 不能绕过任何硬闸门。

专业智能体可以解释、观察、归因和提醒，但不能放行、执行、下单或修改风控规则。

## 适用智能体范围

`AgentReportSchema` 适用于以下专业智能体：

- `DataQualityAgent`
- `MarketStructureAgent`
- `MacroEventAgent`
- `RiskAgent`
- `PositionSizingAgent`
- `ReviewAgent`

`DragonDecisionAgent` 不使用 `AgentReportSchema`。`DragonDecisionAgent` 未来使用单独的 `DragonDecisionReportSchema`，用于汇总多个 `AgentReport` 和硬闸门状态。

## 推荐字段

未来 `AgentReportSchema` 可以包含以下字段。本轮只定义文档契约，不实现代码。

- `report_version`：报告契约版本，例如 `1.0`。
- `report_type`：报告类型，建议为 `agent_report`。
- `agent_name`：输出报告的智能体名称。
- `agent_role`：智能体职责说明。
- `generated_at`：报告生成时间。
- `input_summary`：输入摘要，只能描述已允许的数据来源。
- `data_scope`：数据范围，说明输入来自 docs fixture、demo readonly fixture、manual input 或 unknown。
- `gate_context`：硬闸门上下文摘要，只能引用闸门状态，不能覆盖闸门。
- `findings`：分析发现。
- `confidence_level`：置信度枚举。
- `status`：报告状态枚举。
- `block_reasons`：阻断原因列表。
- `warning_reasons`：警告原因列表。
- `evidence_refs`：证据引用，必须引用安全、允许的输入。
- `assumptions`：明确假设。
- `unknowns`：未知事项。
- `recommended_follow_up`：建议的后续检查或等待条件。
- `cannot_override_gates`：是否不能覆盖硬闸门。
- `is_trading_permission`：是否为交易许可。
- `is_execution_instruction`：是否为执行指令。
- `can_execute`：是否可执行。
- `allowed_to_call_ea`：是否允许调用 EA。
- `allowed_to_modify_risk`：是否允许修改风控。
- `notes`：补充说明。

安全字段必须值：

- `is_trading_permission` 必须永远为 `false`。
- `is_execution_instruction` 必须永远为 `false`。
- `can_execute` 必须永远为 `false`。
- `allowed_to_call_ea` 必须永远为 `false`。
- `allowed_to_modify_risk` 必须永远为 `false`。
- `cannot_override_gates` 必须永远为 `true`。

## 枚举值规划

### agent_name

`agent_name` 可选值：

- `DataQualityAgent`
- `MarketStructureAgent`
- `MacroEventAgent`
- `RiskAgent`
- `PositionSizingAgent`
- `ReviewAgent`

### confidence_level

`confidence_level` 可选值：

- `unknown`
- `low`
- `medium`
- `high`

### status

`status` 可选值：

- `info_only`
- `ok`
- `warning`
- `blocked`
- `unknown`
- `insufficient_data`

### data_scope

`data_scope` 可选值：

- `docs_fixture_only`
- `demo_readonly_fixture`
- `demo_readonly_api`
- `manual_input`
- `unknown`

当前阶段只能使用：

- `docs_fixture_only`
- `manual_input`
- `unknown`

当前不能使用真实 MT4 数据，不能使用真实 demo account 数据。

## 禁止字段

`AgentReport` 禁止包含以下字段或同义含义：

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

方向候选可以表达为：

- `long_candidate`
- `short_candidate`
- `neutral_candidate`

方向候选不能表达为执行命令，不能作为交易许可，不能驱动 EA。

## 各专业智能体报告边界

### DataQualityAgent

`DataQualityAgent` 的 `AgentReport` 只能解释 `DataQualityGate` 结果。

边界：

- 不能自行判定数据通过。
- 不能把数据质量 warning 当作交易许可。
- `DataQualityGate BLOCK` 时，`DataQualityAgent` 只能报告 `blocked` 或 `insufficient_data`。
- 不能覆盖 `DataQualityGate`。

### MarketStructureAgent

`MarketStructureAgent` 的 `AgentReport` 只能描述市场结构。

可以报告：

- `trend_up`
- `trend_down`
- `range`
- `breakout`
- `false_breakout`
- `high_volatility`
- `unclear`

边界：

- 不能输出 `should_buy`。
- 不能输出 `should_sell`。
- 不能输出 `can_trade`。
- 不能绕过 `DataQualityGate` 或 `RiskGate`。
- 市场结构观点只能是 observation-only。

### MacroEventAgent

`MacroEventAgent` 的 `AgentReport` 只能描述宏观事件风险。

可以报告：

- `event_risk_high`
- `event_risk_medium`
- `event_risk_low`
- `unknown`

边界：

- 没有可靠宏观数据源时必须输出 `unknown`。
- 不能编造 CPI、非农、FOMC、鲍威尔讲话、美元指数、美债收益率或新闻事件。
- 当前阶段不接入真实宏观数据源。

### RiskAgent

`RiskAgent` 的 `AgentReport` 只能解释 `RiskGate` 风险状态。

边界：

- `RiskAgent` 不能替代 `RiskGate`。
- `RiskAgent` 不能自行放行交易。
- `RiskGate BLOCK` 时，`RiskAgent` 必须报告 `blocked`。
- `RiskAgent` 只能解释风险，不得修改风险规则。

### PositionSizingAgent

`PositionSizingAgent` 的 `AgentReport` 只能解释 `PositionSizing` 程序结果或仓位逻辑。

边界：

- 不能直接决定最终手数。
- 不能输出 `suggested_lot`。
- 不能输出 `final_lot`。
- 不能放大风险。
- 不能覆盖 `PositionSizing` 程序结果。

### ReviewAgent

`ReviewAgent` 的 `AgentReport` 只能做行为复盘和提醒。

可以报告：

- `chasing_risk`
- `revenge_trade_risk`
- `overtrading_risk`
- `similar_to_past_loss`
- `discipline_warning`

边界：

- 不能把纸面复盘结果当真实 PnL。
- 不能触发交易。
- 不能修改交易结果。

## 与硬闸门关系

`AgentReport` 必须服从硬闸门：

- `AgentReport` 不能覆盖 `DataQualityGate`。
- `AgentReport` 不能覆盖 `RiskGate`。
- `AgentReport` 不能覆盖 `PositionSizing`。
- `AgentReport` 不能覆盖 `ExecutionGate`。
- `AgentReport` 不能把 `BLOCK` 改成 `PASS`。
- `AgentReport` 不能把 warning 改成交易许可。
- `AgentReport` 不能把 `unknown` 改成可执行。

任何硬闸门 `BLOCK` 时，`AgentReport` 只能解释原因，不能建议执行。

## 与 DragonDecisionAgent 的关系

专业智能体输出 `AgentReport`。

`DragonDecisionAgent` 汇总多个 `AgentReport`。

`DragonDecisionAgent` 未来输出 `DragonDecisionReport`。

`DragonDecisionAgent` 不能把 `AgentReport` 当作交易许可。

`DragonDecisionAgent` 不能因为某个 `AgentReport` 看多或看空就绕过硬闸门。

`DragonDecisionAgent` 的职责是汇总和表达，不是执行、下单或替代硬闸门。

## AgentReport 示例

以下示例只是文档示例，不是代码文件，不是运行数据。

### 示例 1：DataQualityAgent data_invalid / blocked

```json
{
  "report_version": "1.0",
  "report_type": "agent_report",
  "agent_name": "DataQualityAgent",
  "agent_role": "Explain DataQualityGate status",
  "generated_at": "2026-07-05T10:00:00Z",
  "input_summary": "Docs fixture shows stale or missing market fields.",
  "data_scope": "docs_fixture_only",
  "gate_context": {
    "gate_name": "DataQualityGate",
    "gate_status": "BLOCK"
  },
  "findings": ["data_invalid", "missing_price"],
  "confidence_level": "high",
  "status": "blocked",
  "block_reasons": ["DataQualityGate blocked because required price fields are missing."],
  "warning_reasons": [],
  "evidence_refs": ["docs fixture only"],
  "assumptions": [],
  "unknowns": [],
  "recommended_follow_up": ["Provide valid demo-only read-only fixture data."],
  "cannot_override_gates": true,
  "is_trading_permission": false,
  "is_execution_instruction": false,
  "can_execute": false,
  "allowed_to_call_ea": false,
  "allowed_to_modify_risk": false,
  "notes": "This report explains data quality only and is not trading permission."
}
```

### 示例 2：MarketStructureAgent trend_up

```json
{
  "report_version": "1.0",
  "report_type": "agent_report",
  "agent_name": "MarketStructureAgent",
  "agent_role": "Explain market structure observation",
  "generated_at": "2026-07-05T10:05:00Z",
  "input_summary": "Docs fixture suggests higher highs and higher lows.",
  "data_scope": "docs_fixture_only",
  "gate_context": {
    "gate_name": "DataQualityGate",
    "gate_status": "UNKNOWN"
  },
  "findings": ["trend_up", "long_candidate"],
  "confidence_level": "medium",
  "status": "info_only",
  "block_reasons": [],
  "warning_reasons": ["Direction candidate is observation-only and cannot execute."],
  "evidence_refs": ["docs fixture only"],
  "assumptions": ["No live market feed is connected."],
  "unknowns": ["Real-time spread", "Current macro event risk"],
  "recommended_follow_up": ["Wait for DataQualityGate and RiskGate status."],
  "cannot_override_gates": true,
  "is_trading_permission": false,
  "is_execution_instruction": false,
  "can_execute": false,
  "allowed_to_call_ea": false,
  "allowed_to_modify_risk": false,
  "notes": "trend_up is not should_buy and is not an order instruction."
}
```

### 示例 3：MacroEventAgent unknown

```json
{
  "report_version": "1.0",
  "report_type": "agent_report",
  "agent_name": "MacroEventAgent",
  "agent_role": "Explain macro event risk",
  "generated_at": "2026-07-05T10:10:00Z",
  "input_summary": "No reliable macro calendar or news source is connected.",
  "data_scope": "unknown",
  "gate_context": {
    "gate_name": "MacroDataAvailability",
    "gate_status": "UNKNOWN"
  },
  "findings": ["unknown"],
  "confidence_level": "unknown",
  "status": "unknown",
  "block_reasons": [],
  "warning_reasons": ["No reliable macro data source is available."],
  "evidence_refs": [],
  "assumptions": [],
  "unknowns": ["CPI schedule", "FOMC schedule", "USD index context", "US yield context"],
  "recommended_follow_up": ["Connect a reliable macro calendar in a future approved phase."],
  "cannot_override_gates": true,
  "is_trading_permission": false,
  "is_execution_instruction": false,
  "can_execute": false,
  "allowed_to_call_ea": false,
  "allowed_to_modify_risk": false,
  "notes": "unknown macro context must not be converted into trading permission."
}
```

## 当前仍不实现

本轮不实现：

- 不实现 `AgentReportSchema` 代码。
- 不实现 Pydantic model。
- 不实现 Agent 代码。
- 不实现智能体类。
- 不实现 LLM 调用。
- 不实现 prompt 执行器。
- 不实现后端 API。
- 不实现前端页面。
- 不实现 reader。
- 不实现 parser。
- 不实现 MT4 EA。
- 不实现 MQL4。
- 不接 MT4。
- 不接模拟账号。
- 不保存凭证。
- 不实现自动交易。

