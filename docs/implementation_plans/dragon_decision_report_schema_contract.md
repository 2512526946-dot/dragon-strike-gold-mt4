# DragonDecisionReportSchema Contract

本文定义未来 `DragonDecisionAgent` 的统一输出契约 `DragonDecisionReportSchema`。

本轮只写文档，不实现 `DragonDecisionReportSchema` 代码、Pydantic model、`DragonDecisionAgent` 代码、Agent 代码、智能体类、LLM 调用、prompt 执行器、后端 API、前端页面、reader、parser、MT4 EA、MQL4、执行 API 或自动交易。

## 文件用途

`DragonDecisionReport` 是总决策表达报告，用于汇总硬闸门状态和多个专业智能体的 `AgentReport`，并输出最终安全表达。

`DragonDecisionReport` 必须始终满足：

- `DragonDecisionReport` 是总决策表达报告。
- `DragonDecisionReport` 不是交易许可。
- `DragonDecisionReport` 不是订单。
- `DragonDecisionReport` 不是 EA 指令。
- `DragonDecisionReport` 不能驱动自动交易。
- `DragonDecisionReport` 不能绕过任何硬闸门。
- `DragonDecisionAgent` 只能汇总硬闸门状态和 `AgentReport`，不能替代硬闸门。

`DragonDecisionAgent` 的职责是汇总、解释和安全表达，不是放行、执行、下单、修改风控或调用 EA。

简明结论：DragonDecisionReport 不是交易许可，DragonDecisionReport 不是执行指令，DragonDecisionReport 不是订单，DragonDecisionReport 不是 EA 指令。

## 适用范围

`DragonDecisionReportSchema` 只适用于：

- `DragonDecisionAgent`

`DragonDecisionReportSchema` 不适用于以下专业智能体：

- `DataQualityAgent`
- `MarketStructureAgent`
- `MacroEventAgent`
- `RiskAgent`
- `PositionSizingAgent`
- `ReviewAgent`

专业智能体继续使用 `AgentReportSchema`。专业智能体负责专项分析和解释，`DragonDecisionAgent` 负责汇总多个 `AgentReport` 与硬闸门状态。

## 推荐字段

未来 `DragonDecisionReportSchema` 可以包含以下字段。本轮只定义文档契约，不实现代码。

- `report_version`：报告契约版本，例如 `1.0`。
- `report_type`：报告类型，建议为 `dragon_decision_report`。
- `generated_at`：报告生成时间。
- `decision_agent_name`：总决策智能体名称，建议为 `DragonDecisionAgent`。
- `input_scope`：输入范围摘要，例如使用了哪些硬闸门结果和哪些 `AgentReport`。
- `data_scope`：数据范围枚举，说明输入来自 docs fixture、manual input、demo readonly fixture、demo readonly API 或 unknown。
- `gate_summary`：硬闸门状态摘要。
- `agent_reports_used`：本次汇总使用的 `AgentReport` 列表或引用。
- `agent_summary`：多个专业智能体报告的归纳摘要。
- `final_action`：最终安全动作枚举。
- `direction_bias`：方向候选或倾向表达枚举。
- `trade_plan_allowed`：是否允许形成观察性计划候选。
- `manual_confirm_required`：是否需要人工确认。
- `risk_review_required`：是否需要风险复核。
- `close_only`：是否只允许关闭风险或退出方向的安全状态表达。
- `main_reasons`：主要理由。
- `block_reasons`：阻断原因。
- `warning_reasons`：警告原因。
- `risk_points`：风险点。
- `wait_conditions`：等待条件。
- `invalidation_conditions`：失效条件。
- `review_reminders`：复盘提醒。
- `assumptions`：明确假设。
- `unknowns`：未知事项。
- `evidence_refs`：证据引用，必须引用安全、允许的输入。
- `cannot_override_gates`：是否不能覆盖硬闸门。
- `is_trading_permission`：是否为交易许可。
- `is_execution_instruction`：是否为执行指令。
- `can_execute`：是否可执行。
- `requires_execution_gate`：是否必须经过 `ExecutionGate`。
- `allowed_to_call_ea`：是否允许调用 EA。
- `allowed_to_modify_risk`：是否允许修改风控。
- `notes`：补充说明。

安全字段必须值：

- `is_trading_permission` 必须永远为 `false`。
- `is_execution_instruction` 必须永远为 `false`。
- `can_execute` 当前阶段必须永远为 `false`。
- `allowed_to_call_ea` 必须永远为 `false`。
- `allowed_to_modify_risk` 必须永远为 `false`。
- `cannot_override_gates` 必须永远为 `true`。
- `requires_execution_gate` 必须为 `true`。

## final_action 枚举

`final_action` 只能使用安全状态，不直接表达订单或执行命令。

可选值：

- `observe_only`
- `blocked`
- `plan_candidate`
- `manual_confirm_required`
- `close_only`
- `risk_review_required`
- `data_invalid`
- `wait_for_confirmation`
- `review_only`

这些动作不是订单，不是 EA 指令，不是实盘交易建议，也不是自动交易许可。它们不能直接转换为 `OrderSend`、`OrderClose`、`OrderModify` 或 `OrderDelete`。

`final_action` 只能描述当前安全表达状态。是否进入真实或模拟执行链路，未来必须由独立硬闸门、人工确认流程或 demo-only 训练模式决定。

## direction_bias 枚举

`direction_bias` 只能表达方向候选或倾向，不表达执行许可。

可选值：

- `long_candidate`
- `short_candidate`
- `neutral_candidate`
- `no_bias`
- `unknown`

边界：

- `direction_bias` 只是方向候选或倾向表达。
- `direction_bias` 不等于执行许可。
- `long_candidate` 不等于 `buy`。
- `short_candidate` 不等于 `sell`。
- `no_bias` / `unknown` 不代表系统故障。
- 任何 `direction_bias` 都不能绕过硬闸门。

## data_scope 枚举

`data_scope` 用于说明 `DragonDecisionReport` 使用的数据来源范围。

可选值：

- `docs_fixture_only`
- `demo_readonly_fixture`
- `demo_readonly_api`
- `manual_input`
- `unknown`

当前阶段只能使用：

- `docs_fixture_only`
- `manual_input`
- `unknown`

当前阶段不能使用真实 MT4 数据，不能使用真实 demo account 数据，不能接入真实宏观数据源。未来如果使用 `demo_readonly_api`，必须经过单独 API 阶段验收。

## gate_summary 结构规划

`gate_summary` 用于汇总硬闸门状态，至少覆盖：

- `DataQualityGate`
- `RiskGate`
- `PositionSizing`
- `ExecutionGate`

每个 gate 建议字段：

- `gate_name`：硬闸门名称。
- `status`：硬闸门状态。
- `passed`：是否通过。
- `block_reasons`：阻断原因。
- `warning_reasons`：警告原因。
- `evidence_refs`：证据引用。
- `can_be_overridden`：是否可以被覆盖。

`status` 可选值：

- `pass`
- `warning`
- `blocked`
- `unknown`
- `not_implemented`
- `not_applicable`

硬规则：

- `can_be_overridden` 必须为 `false`。
- 当前未实现的 gate 必须标记为 `not_implemented` 或 `unknown`。
- 不能把未实现 gate 当作 `pass`。
- 不能把 `unknown` gate 当作交易许可。
- `DragonDecisionAgent` 不能把任何硬闸门结果改写成更安全或更乐观的结果。

## agent_summary 结构规划

`agent_summary` 用于汇总多个专业智能体的 `AgentReport`。

每个 agent summary 建议字段：

- `agent_name`：专业智能体名称。
- `status`：专业报告状态。
- `confidence_level`：置信度。
- `key_findings`：关键发现。
- `block_reasons`：阻断原因。
- `warning_reasons`：警告原因。
- `unknowns`：未知事项。
- `used_in_decision`：是否被本次总决策表达引用。
- `is_trading_permission`：该报告是否为交易许可。
- `is_execution_instruction`：该报告是否为执行指令。

硬规则：

- `AgentReport` 中的 `is_trading_permission` 必须为 `false`。
- `AgentReport` 中的 `is_execution_instruction` 必须为 `false`。
- `DragonDecisionAgent` 不能把某个 `AgentReport` 当作交易许可。
- `DragonDecisionAgent` 不能把某个 `AgentReport` 的 warning 当作交易许可。
- `DragonDecisionAgent` 不能把某个 `AgentReport` 的 unknown 当成可执行。
- 缺失关键 `AgentReport` 时，必须进入 `wait_for_confirmation`、`observe_only` 或 unknown 风险提示。

## 硬闸门 veto 规则

硬闸门 veto 优先级必须明确：

- `DataQualityGate BLOCK` > 所有 `AgentReport`。
- `RiskGate BLOCK` > 所有 `AgentReport`。
- `PositionSizing BLOCK` > 所有 `AgentReport`。
- `ExecutionGate BLOCK` > 所有 `AgentReport`。

任何硬闸门 `blocked` 时，`DragonDecisionReport` 只能输出以下安全 `final_action` 之一：

- `blocked`
- `observe_only`
- `close_only`
- `risk_review_required`
- `data_invalid`

不得输出：

- `plan_candidate`
- `manual_confirm_required`

例外只允许在文档明确该 block 不影响观察性计划时使用，并且仍然必须保持：

- `is_trading_permission=false`
- `is_execution_instruction=false`
- `can_execute=false`
- `allowed_to_call_ea=false`

硬闸门 `unknown` / `not_implemented` 时，不能视为 `pass`。当前阶段 `ExecutionGate` 未实现，因此 `can_execute` 必须为 `false`。

## 不同场景的输出规则

### A. DataQualityGate blocked

输出要求：

- `final_action` 应为 `data_invalid` 或 `blocked`。
- `direction_bias` 应为 `no_bias` 或 `unknown`。
- `trade_plan_allowed=false`。
- `can_execute=false`。
- 只允许解释数据问题。

### B. RiskGate blocked

输出要求：

- `final_action` 应为 `blocked`、`close_only` 或 `risk_review_required`。
- `trade_plan_allowed=false`。
- `can_execute=false`。
- 必须说明风险阻断原因。

### C. PositionSizing blocked

输出要求：

- `final_action` 应为 `risk_review_required` 或 `blocked`。
- 不允许输出 `suggested_lot` / `final_lot`。
- `can_execute=false`。

### D. ExecutionGate blocked / not_implemented

输出要求：

- `can_execute=false`。
- `requires_execution_gate=true`。
- 不允许输出任何 EA 指令。
- 当前阶段不能执行。

### E. MarketStructureAgent 看多但硬闸门未全部通过

输出要求：

- 可以 `direction_bias=long_candidate`。
- 但 `final_action` 只能是 `observe_only`、`wait_for_confirmation` 或 `plan_candidate`。
- `can_execute=false`。
- 必须说明方向候选不等于执行许可。

### F. MacroEventAgent unknown

输出要求：

- 不能编造宏观事件。
- 必须在 `unknowns` 中说明宏观数据源不可用。
- 不得把 `unknown` 当作 low risk。

## 禁止字段

`DragonDecisionReport` 禁止包含以下字段或同义含义：

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

`DragonDecisionReport` 可以表达 `direction_bias`，但不能表达执行命令。`DragonDecisionReport` 不能输出最终手数。最终手数未来必须由 `PositionSizing` 程序硬计算。

## 与 AgentReportSchema 的关系

多智能体汇总链路为：

```text
专业智能体
↓
AgentReport
↓
DragonDecisionAgent
↓
DragonDecisionReport
```

关系边界：

- 专业智能体输出 `AgentReport`。
- `DragonDecisionAgent` 汇总多个 `AgentReport`。
- `DragonDecisionAgent` 输出 `DragonDecisionReport`。
- `DragonDecisionReport` 不能覆盖 `AgentReport` 中的安全字段。
- `DragonDecisionReport` 不能把 `AgentReport` 的 warning 当成交易许可。
- `DragonDecisionReport` 不能把 `AgentReport` 的 unknown 当成可执行。
- `DragonDecisionReport` 不能把某个专业智能体观点提升为硬闸门结果。

## 与 TradePlan 的关系

`DragonDecisionReport` 不是 `TradePlan`。

DragonDecisionReport 不是 TradePlan。

未来如需形成 `TradePlan`，必须另走：

```text
DragonDecisionReport
↓
TradePlan 生成
↓
DataQualityGate
↓
RiskGate
↓
PositionSizing
↓
ExecutionGate
↓
ManualConfirmFlow / AutoDemoTrainingMode
↓
MT4 EA demo-only
```

当前阶段不生成 `TradePlan`，不实现 `TradePlanSchema` 代码，当前阶段不执行。未来 `TradePlan` 也不能绕过硬闸门。

## 与未来 demo-only 执行链路的关系

即使未来进入 demo-only 半自动阶段，也必须满足：

- 只能 demo-only。
- read-only 数据先通过 `DataQualityGate`。
- `RiskGate` 通过。
- `PositionSizing` 程序硬计算。
- `ExecutionGate` 通过。
- 用户人工确认或 `AutoDemoTrainingMode` 明确开启。
- MT4 EA 只能 demo-only。
- live account 必须阻断。
- 没有止损不得执行。
- 马丁格尔禁止。
- 网格加仓禁止。
- 隔夜执行禁止。

`DragonDecisionReport` 仍然只是一层表达，不是执行入口。

## DragonDecisionReport 示例

以下示例只用于文档说明，不是代码文件，不是运行数据，不得提交到 `data/`。

### 示例 1：DataQualityGate blocked

```json
{
  "report_version": "1.0",
  "report_type": "dragon_decision_report",
  "generated_at": "2026-07-05T10:00:00Z",
  "decision_agent_name": "DragonDecisionAgent",
  "input_scope": "DataQualityGate blocked with limited AgentReport context.",
  "data_scope": "docs_fixture_only",
  "gate_summary": [
    {
      "gate_name": "DataQualityGate",
      "status": "blocked",
      "passed": false,
      "block_reasons": ["MT4 snapshot is stale"],
      "warning_reasons": [],
      "evidence_refs": ["data_quality_gate.status_code"],
      "can_be_overridden": false
    },
    {
      "gate_name": "RiskGate",
      "status": "not_implemented",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["RiskGate is not implemented in the current stage"],
      "evidence_refs": [],
      "can_be_overridden": false
    },
    {
      "gate_name": "PositionSizing",
      "status": "not_implemented",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["PositionSizing is not implemented in the current stage"],
      "evidence_refs": [],
      "can_be_overridden": false
    },
    {
      "gate_name": "ExecutionGate",
      "status": "not_implemented",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["ExecutionGate is not implemented in the current stage"],
      "evidence_refs": [],
      "can_be_overridden": false
    }
  ],
  "agent_reports_used": ["DataQualityAgent"],
  "agent_summary": [
    {
      "agent_name": "DataQualityAgent",
      "status": "blocked",
      "confidence_level": "high",
      "key_findings": ["Input data is stale"],
      "block_reasons": ["DataQualityGate blocked"],
      "warning_reasons": [],
      "unknowns": [],
      "used_in_decision": true,
      "is_trading_permission": false,
      "is_execution_instruction": false
    }
  ],
  "final_action": "data_invalid",
  "direction_bias": "no_bias",
  "trade_plan_allowed": false,
  "manual_confirm_required": false,
  "risk_review_required": false,
  "close_only": false,
  "main_reasons": ["Data quality is blocked"],
  "block_reasons": ["DataQualityGate blocked"],
  "warning_reasons": ["Other gates are not implemented"],
  "risk_points": ["Using stale data would be unsafe"],
  "wait_conditions": ["Refresh read-only data and rerun DataQualityGate"],
  "invalidation_conditions": ["Any stale or malformed MT4 file remains invalid"],
  "review_reminders": ["Do not treat stale data as a signal"],
  "assumptions": [],
  "unknowns": ["RiskGate, PositionSizing, and ExecutionGate are not implemented"],
  "evidence_refs": ["DataQualityGate"],
  "cannot_override_gates": true,
  "is_trading_permission": false,
  "is_execution_instruction": false,
  "can_execute": false,
  "requires_execution_gate": true,
  "allowed_to_call_ea": false,
  "allowed_to_modify_risk": false,
  "notes": "Read-only safety expression only. Not trading advice, not trading permission, and not an EA command."
}
```

### 示例 2：MarketStructureAgent trend_up，但 ExecutionGate not_implemented

```json
{
  "report_version": "1.0",
  "report_type": "dragon_decision_report",
  "generated_at": "2026-07-05T10:05:00Z",
  "decision_agent_name": "DragonDecisionAgent",
  "input_scope": "MarketStructureAgent reports trend_up, but execution layer is unavailable.",
  "data_scope": "manual_input",
  "gate_summary": [
    {
      "gate_name": "DataQualityGate",
      "status": "warning",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["Manual input only"],
      "evidence_refs": ["manual_input"],
      "can_be_overridden": false
    },
    {
      "gate_name": "RiskGate",
      "status": "not_implemented",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["RiskGate is not implemented in the current stage"],
      "evidence_refs": [],
      "can_be_overridden": false
    },
    {
      "gate_name": "PositionSizing",
      "status": "not_implemented",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["PositionSizing is not implemented in the current stage"],
      "evidence_refs": [],
      "can_be_overridden": false
    },
    {
      "gate_name": "ExecutionGate",
      "status": "not_implemented",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["ExecutionGate is not implemented in the current stage"],
      "evidence_refs": [],
      "can_be_overridden": false
    }
  ],
  "agent_reports_used": ["MarketStructureAgent"],
  "agent_summary": [
    {
      "agent_name": "MarketStructureAgent",
      "status": "ok",
      "confidence_level": "medium",
      "key_findings": ["Market structure appears trend_up in the provided fixture"],
      "block_reasons": [],
      "warning_reasons": ["Hard gates are not all implemented"],
      "unknowns": ["Macro event context is unavailable"],
      "used_in_decision": true,
      "is_trading_permission": false,
      "is_execution_instruction": false
    }
  ],
  "final_action": "observe_only",
  "direction_bias": "long_candidate",
  "trade_plan_allowed": false,
  "manual_confirm_required": false,
  "risk_review_required": true,
  "close_only": false,
  "main_reasons": ["Market structure is only a direction candidate"],
  "block_reasons": ["ExecutionGate is not implemented"],
  "warning_reasons": ["Direction candidate is not execution permission"],
  "risk_points": ["Hard gates are incomplete"],
  "wait_conditions": ["Implement and pass RiskGate, PositionSizing, and ExecutionGate before any execution path"],
  "invalidation_conditions": ["Any gate blocked or unknown keeps execution disabled"],
  "review_reminders": ["Do not convert long_candidate into an order"],
  "assumptions": ["The trend_up finding came from allowed manual or fixture input"],
  "unknowns": ["Macro events and execution readiness are unknown"],
  "evidence_refs": ["MarketStructureAgent.AgentReport"],
  "cannot_override_gates": true,
  "is_trading_permission": false,
  "is_execution_instruction": false,
  "can_execute": false,
  "requires_execution_gate": true,
  "allowed_to_call_ea": false,
  "allowed_to_modify_risk": false,
  "notes": "Read-only direction candidate. Not trading advice, not trading permission, and not an EA command."
}
```

### 示例 3：RiskGate blocked

```json
{
  "report_version": "1.0",
  "report_type": "dragon_decision_report",
  "generated_at": "2026-07-05T10:10:00Z",
  "decision_agent_name": "DragonDecisionAgent",
  "input_scope": "RiskGate blocked after reviewing risk context.",
  "data_scope": "docs_fixture_only",
  "gate_summary": [
    {
      "gate_name": "DataQualityGate",
      "status": "warning",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["Fixture data only"],
      "evidence_refs": ["docs_fixture"],
      "can_be_overridden": false
    },
    {
      "gate_name": "RiskGate",
      "status": "blocked",
      "passed": false,
      "block_reasons": ["Daily loss limit reached"],
      "warning_reasons": [],
      "evidence_refs": ["RiskGate.status_code"],
      "can_be_overridden": false
    },
    {
      "gate_name": "PositionSizing",
      "status": "not_implemented",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["PositionSizing is not implemented in the current stage"],
      "evidence_refs": [],
      "can_be_overridden": false
    },
    {
      "gate_name": "ExecutionGate",
      "status": "not_implemented",
      "passed": false,
      "block_reasons": [],
      "warning_reasons": ["ExecutionGate is not implemented in the current stage"],
      "evidence_refs": [],
      "can_be_overridden": false
    }
  ],
  "agent_reports_used": ["RiskAgent", "ReviewAgent"],
  "agent_summary": [
    {
      "agent_name": "RiskAgent",
      "status": "blocked",
      "confidence_level": "high",
      "key_findings": ["RiskGate blocked"],
      "block_reasons": ["Daily loss limit reached"],
      "warning_reasons": [],
      "unknowns": [],
      "used_in_decision": true,
      "is_trading_permission": false,
      "is_execution_instruction": false
    },
    {
      "agent_name": "ReviewAgent",
      "status": "warning",
      "confidence_level": "medium",
      "key_findings": ["Behavior review is required before any future plan"],
      "block_reasons": [],
      "warning_reasons": ["Potential discipline risk after loss"],
      "unknowns": [],
      "used_in_decision": true,
      "is_trading_permission": false,
      "is_execution_instruction": false
    }
  ],
  "final_action": "risk_review_required",
  "direction_bias": "no_bias",
  "trade_plan_allowed": false,
  "manual_confirm_required": false,
  "risk_review_required": true,
  "close_only": false,
  "main_reasons": ["RiskGate blocked the session"],
  "block_reasons": ["Daily loss limit reached"],
  "warning_reasons": ["ReviewAgent flagged behavior review"],
  "risk_points": ["Continuing after a risk block is unsafe"],
  "wait_conditions": ["Wait for next allowed review window and rerun RiskGate"],
  "invalidation_conditions": ["RiskGate remains blocked"],
  "review_reminders": ["Do not attempt to recover losses through forced action"],
  "assumptions": [],
  "unknowns": ["ExecutionGate and PositionSizing are not implemented"],
  "evidence_refs": ["RiskGate", "RiskAgent.AgentReport", "ReviewAgent.AgentReport"],
  "cannot_override_gates": true,
  "is_trading_permission": false,
  "is_execution_instruction": false,
  "can_execute": false,
  "requires_execution_gate": true,
  "allowed_to_call_ea": false,
  "allowed_to_modify_risk": false,
  "notes": "Read-only risk review expression. Not trading advice, not trading permission, and not an EA command."
}
```

## 当前仍不实现

本轮明确不实现：

- 不实现 `DragonDecisionReportSchema` 代码。
- 不实现 Pydantic model。
- 不实现 `DragonDecisionAgent` 代码。
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
- 不实现 `TradePlanSchema` 代码。
- 不实现 `RiskGate`。
- 不实现 `PositionSizing`。
- 不实现 `ExecutionGate`。
- 不实现执行 API。
- 不实现自动交易。

## 安全边界总结

`DragonDecisionReport` 只能表达安全汇总结果。它不能成为交易许可，不能成为执行指令，不能绕过硬闸门，不能调用 EA，不能输出最终手数，不能连接真实账户，不能连接模拟账号，不能返回任何真实交易建议。
