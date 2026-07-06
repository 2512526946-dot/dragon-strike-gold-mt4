# DemoReadOnlyExplanation Frontend Contract

本文档定义未来 `DemoReadOnlyExplanation` 前端只读解释展示契约，用于约束前端如何安全展示 `GET /api/demo-readonly/explanation` 返回的 `ReadOnlyExplanationReport`。

当前工单只写前端契约文档，不实现前端 API client，不实现 `ExplanationPanel`，不修改现有 `DemoReadOnlyDiagnosticsDashboard`，不新增页面、路由、自动刷新、轮询、WebSocket、后端 API、LLM、Agent、RiskGate、PositionSizing、ExecutionGate、TradePlanSchema 或任何执行链路。

## 1. 文件用途

本文档用于定义未来只读解释展示层的边界、字段映射、ViewModel、组件规划、UI 状态、安全文案、允许展示内容、禁止展示内容、与现有 Dashboard 的关系、与后端 explanation API 的关系、与 LLM / Agent 的关系，以及后续 1S 前端阶段顺序。

必须明确：

- 本文档只是前端契约。
- 本轮不实现前端 API client。
- 本轮不实现 `ExplanationPanel`。
- 本轮不修改现有 Dashboard。
- 本轮不新增页面。
- 本轮不新增路由。
- 本轮不修改后端。
- 前端未来只能展示 explanation API 的安全 response。
- 前端不能展示 raw payload。
- 前端不能展示交易建议。
- 前端不能展示执行指令。
- 前端不能把 explanation API 的 `passed=true` 解释成交易许可。
- 前端不能把 `next_allowed_stage_explanation` 解释成交易许可。
- 前端不能新增任何交易按钮或执行入口。
- 前端不能新增风控修改、仓位计算、MT4 操作或 EA 调用入口。

任何 `passed=true`、`READY`、`next_allowed_stage_explanation`、`status_code`、`HTTP 200` 或解释文本，都只能表示只读解释状态，不代表交易许可、执行许可、风控放行、仓位计算许可、EA 调用许可或自动交易能力。

## 2. 前端展示定位

未来 `DemoReadOnlyExplanationPanel` 的定位必须保持：

- demo-only。
- read-only。
- explanation display only。
- human-readable explanation only。
- non-trading。
- non-execution。
- no advice。
- no order。
- no risk override。
- no position sizing。
- no MT4 interaction。

`ExplanationPanel` 只是解释区块，不是交易面板，不是执行面板，不是风控面板，不是信号面板，不是 MT4 控制面板，不是仓位计算面板。

该区块只回答一个问题：当前只读解释报告可以怎样被用户安全理解。它不回答是否可以交易、是否可以执行、是否可以下单、是否可以连接 MT4、是否可以覆盖风控、是否可以计算手数、是否可以生成 `TradePlan`。

## 3. API 来源

未来前端只允许从以下只读 API 获取解释报告：

```text
GET /api/demo-readonly/explanation
```

API 调用边界：

- 只允许 `GET`。
- 不允许 `POST` / `PUT` / `PATCH` / `DELETE`。
- 不允许 WebSocket。
- 不允许 SSE。
- 不允许自动轮询。
- 不允许后台自动刷新。
- 不允许 `localStorage` / `sessionStorage` 写入。
- 不允许读取文件。
- 不允许读取 `data/` 运行目录。
- 不允许读取 `.env`。
- 不允许读取日志。
- 不允许读取数据库。
- 不允许连接 MT4。
- 不允许连接模拟账号或真实账号。
- 不允许访问任何交易、执行、风控、仓位、EA 或 Agent 入口。

当前 1S-4 工单不实现该 API 调用，不访问网络，不新增 `fetch` / `axios` / client / hook / service。未来允许调用时，也只能通过白名单 mapper 把安全字段转换为只读 ViewModel。

## 4. 前端 ViewModel 规划

未来前端可以规划 `DemoReadOnlyExplanationViewModel`。本轮仅写文档，不创建 `types.ts`、`contracts.ts`、`mapper.ts`、`api.ts` 或任何 React 组件。

建议类型草案：

```ts
type DemoReadOnlyExplanationUiSafetyStatus =
  | "ready"
  | "blocked"
  | "api_error"
  | "security_blocked"
  | "empty"
  | "stale_or_unknown";

interface DemoReadOnlyExplanationSafetyFlags {
  readOnly: true;
  demoOnly: true;
  isTradable: false;
  canExecute: false;
  isTradingPermission: false;
  isExecutionInstruction: false;
  allowedToCallEa: false;
  allowedToModifyRisk: false;
}

interface DemoReadOnlyExplanationComponentViewModel {
  componentName: string;
  statusCode: string;
  explanation: string;
  blockReasons: string[];
  warningReasons: string[];
}

interface DemoReadOnlyExplanationViewModel
  extends DemoReadOnlyExplanationSafetyFlags {
  passed: boolean;
  statusCode: string;
  reportVersion: string;
  reportType: "demo_readonly_explanation";
  generatedAt: string | null;
  sourceScope: string;
  explanationScope: string;
  overallExplanation: string;
  statusExplanation: string;
  componentExplanations: DemoReadOnlyExplanationComponentViewModel[];
  blockerExplanations: string[];
  warningExplanations: string[];
  readinessExplanation: string;
  nextAllowedStageExplanation: string | null;
  nextBlockedStageExplanation: string | null;
  userSafeNextSteps: string[];
  userForbiddenActions: string[];
  unknowns: string[];
  safetyFlags: DemoReadOnlyExplanationSafetyFlags;
  blockReasons: string[];
  warningReasons: string[];
  notes: string[];
  uiSafetyStatus: DemoReadOnlyExplanationUiSafetyStatus;
  uiSafetyMessage: string;
}
```

安全字段必须映射为：

```text
readOnly=true
demoOnly=true
isTradable=false
canExecute=false
isTradingPermission=false
isExecutionInstruction=false
allowedToCallEa=false
allowedToModifyRisk=false
```

如果后端响应缺失以上安全字段，或字段值与安全约束不一致，未来 mapper 必须把 `uiSafetyStatus` 设置为 `security_blocked` 或 `blocked`，并阻止解释内容进入正常展示状态。

## 5. Mapper 规划

未来 mapper 建议命名：

```text
mapDemoReadOnlyExplanationApiToViewModel(apiResponse)
```

mapper 必须执行：

- 白名单字段映射。
- unknown fields 默认丢弃。
- forbidden fields 默认丢弃或触发 `SECURITY BLOCKED`。
- raw payload 不进入 ViewModel。
- 敏感字段不进入 ViewModel。
- 交易字段不进入 ViewModel。
- 执行字段不进入 ViewModel。
- safety flags 异常时 `uiSafetyStatus=security_blocked` 或 `uiSafetyStatus=blocked`。
- API 错误时 `uiSafetyStatus=api_error` 或 `uiSafetyStatus=blocked`。
- `passed=true` 不能映射为可以交易。
- `next_allowed_stage_explanation` 不能映射为交易许可。
- `next_blocked_stage_explanation` 只能展示为流程阻断说明。
- `user_safe_next_steps` 只能保留非交易、非执行、非 MT4、非风控修改动作。
- `user_forbidden_actions` 只能作为禁止事项展示，不得变成按钮或快捷操作。

允许进入 ViewModel 的来源字段只能来自 explanation API 的安全摘要字段，例如：

- `passed`
- `status_code`
- `report_version`
- `report_type`
- `generated_at`
- `source_scope`
- `explanation_scope`
- `overall_explanation`
- `status_explanation`
- `component_explanations`
- `blocker_explanations`
- `warning_explanations`
- `readiness_explanation`
- `next_allowed_stage_explanation`
- `next_blocked_stage_explanation`
- `user_safe_next_steps`
- `user_forbidden_actions`
- `unknowns`
- `safety_flags`
- `block_reasons`
- `warning_reasons`
- `notes`
- `read_only`
- `demo_only`
- `is_tradable`
- `can_execute`
- `is_trading_permission`
- `is_execution_instruction`
- `allowed_to_call_ea`
- `allowed_to_modify_risk`

mapper 不得把 API response 原样 dump 到页面，不得把未知字段透传为 props，不得把安全字段异常的 response 当作正常解释内容展示。

## 6. 未来组件规划

以下组件只是未来规划，本轮不实现任何代码。

### 6.1 DemoReadOnlyExplanationPanel

用途：只读解释主容器。

限制：

- 只读展示。
- 不包含按钮型交易动作。
- 不包含执行入口。
- 不包含风控修改入口。
- 不包含仓位计算入口。
- 不包含 MT4 操作入口。
- 不显示 raw payload。
- 不显示账号密码、凭证、token、secret、login。
- 不显示交易建议字段。
- 不显示执行指令字段。

### 6.2 ExplanationOverallPanel

用途：展示 `overallExplanation`、`passed` 和 `uiSafetyMessage`。

限制：

- `passed=true` 只能显示为解释报告通过安全展示检查。
- 不得显示为交易许可。
- 不得显示为执行许可。
- 不得显示为风控放行。

### 6.3 ExplanationStatusPanel

用途：展示 `statusCode`、`reportVersion`、`reportType`、`generatedAt`、`sourceScope`、`explanationScope`。

限制：

- 不展示系统路径。
- 不展示 traceback。
- 不展示 raw response。
- 不展示 data 文件来源明细。

### 6.4 ExplanationComponentList

用途：展示 `componentExplanations` 的只读摘要。

限制：

- 每个 component 只能展示名称、状态码、解释、阻断原因、警告原因。
- 不展示 raw component payload。
- 不展示账号、订单、持仓、行情原文。
- 不展示交易动作字段。

### 6.5 ExplanationBlockerList

用途：展示 `blockerExplanations` 和 `blockReasons`。

限制：

- 阻断原因只能解释为什么不能进入下一只读阶段。
- 阻断原因不能变成操作按钮。
- 阻断原因不能变成交易建议。

### 6.6 ExplanationWarningList

用途：展示 `warningExplanations` 和 `warningReasons`。

限制：

- 警告只能作为只读提醒。
- 警告不能暗示可以绕过安全边界。
- 警告不能触发任何自动流程。

### 6.7 ExplanationReadinessPanel

用途：展示 `readinessExplanation`。

限制：

- readiness 只能说明只读解释准备度。
- readiness 不代表交易准备度。
- readiness 不代表执行准备度。

### 6.8 ExplanationNextStagePanel

用途：展示 `nextAllowedStageExplanation` 和 `nextBlockedStageExplanation`。

限制：

- `nextAllowedStageExplanation` 只是流程提示。
- `nextBlockedStageExplanation` 只是流程阻断说明。
- 二者都不能作为交易许可、执行指令、Agent 指令或 EA 指令。

### 6.9 ExplanationSafeNextStepsPanel

用途：展示 `userSafeNextSteps`。

限制：

- 只允许非交易、非执行、非 MT4、非风控修改、非仓位计算的用户下一步。
- 不得把 safe next step 渲染成会触发后端写入或执行的按钮。

### 6.10 ExplanationForbiddenActionsPanel

用途：展示 `userForbiddenActions`。

限制：

- 只能用于提醒禁止事项。
- 不得把禁止事项渲染成可点击动作。
- 不得提供快捷执行入口。

### 6.11 ExplanationSafetyBanner

用途：始终展示只读安全提示。

必须表达：

- 只读解释。
- 非交易许可。
- 非执行指令。
- 交易能力禁用。
- 执行能力禁用。
- demo-only。
- read-only。

## 7. UI 状态规划

### 7.1 loading

用户看到：

- 正在读取只读解释。
- 只读、安全、非交易提示。

不显示：

- raw payload。
- 交易字段。
- 执行字段。
- 敏感字段。

是否允许手动刷新：不建议重复点击，可显示禁用状态。

为什么不是交易许可：loading 只代表正在读取解释报告，尚无可展示结论，也不包含任何执行能力。

为什么不是执行指令：loading 不携带任何指令字段，不触发任何后端写入或 MT4 操作。

### 7.2 ready

用户看到：

- 安全映射后的解释报告。
- `readOnly=true`、`demoOnly=true`。
- `isTradable=false`、`canExecute=false`。
- 只读解释、安全文案、阻断和警告摘要。

不显示：

- raw payload。
- 账号、凭证、路径、traceback。
- 交易建议。
- 执行指令。

是否允许手动刷新：允许未来通过显式按钮手动刷新，但不允许自动刷新。

为什么不是交易许可：ready 只代表解释报告可以安全展示，不代表任何交易、风控或执行许可。

为什么不是执行指令：ready 没有执行入口，且 `canExecute=false`。

### 7.3 blocked

用户看到：

- 只读解释被阻断。
- 阻断原因。
- 安全字段摘要。

不显示：

- raw payload。
- 未清洗字段。
- 交易字段。
- 执行字段。

是否允许手动刷新：允许未来手动刷新。

为什么不是交易许可：blocked 明确表示只读解释不能正常展示或不能进入下一只读阶段。

为什么不是执行指令：blocked 不包含执行能力，且必须展示执行能力禁用。

### 7.4 api_error

用户看到：

- 无法读取只读解释。
- 请确认后端只读解释 API 可用。
- 这不是交易许可，也不是执行指令。

不显示：

- stack trace。
- system path。
- raw error object。
- token、secret、credential。

是否允许手动刷新：允许未来手动刷新。

为什么不是交易许可：API 错误没有产生安全解释报告。

为什么不是执行指令：API 错误不触发任何执行流程。

### 7.5 security_blocked

用户看到：

- 安全检查阻断。
- 响应包含不允许字段或安全字段异常。
- 页面不会展示该响应内容。

不显示：

- 触发阻断的敏感原文。
- forbidden field 的值。
- raw response。
- raw payload。

是否允许手动刷新：允许未来手动刷新。

为什么不是交易许可：security blocked 表示安全异常，必须 fail closed。

为什么不是执行指令：security blocked 会阻断展示和执行语义。

### 7.6 empty

用户看到：

- 暂无只读解释。
- 可以手动刷新只读解释。
- 当前页面不提供交易、下单、风控修改或仓位计算能力。

不显示：

- 默认成功状态。
- 默认交易状态。
- 默认下一步交易提示。

是否允许手动刷新：允许未来手动刷新。

为什么不是交易许可：empty 没有解释报告。

为什么不是执行指令：empty 没有指令内容。

### 7.7 stale_or_unknown

用户看到：

- 只读解释状态未知或可能过旧。
- 需要重新读取只读解释。
- 仍然保持非交易、非执行、安全阻断语义。

不显示：

- 过旧 raw payload。
- 过旧交易语义。
- 过旧执行语义。

是否允许手动刷新：允许未来手动刷新。

为什么不是交易许可：状态未知或过旧时必须 fail closed。

为什么不是执行指令：状态未知或过旧不能生成任何执行动作。

## 8. 用户可见安全文案

未来 UI 必须显示或等价显示：

- 只读解释。
- 非交易许可。
- 非执行指令。
- 交易能力禁用。
- 执行能力禁用。
- demo-only。
- read-only。
- `next_allowed_stage` 只是流程提示。
- 当前页面不提供交易、下单、风控修改或仓位计算能力。

建议文案：

```text
这是只读解释区块，仅用于理解 demo-only / read-only 诊断状态。
它不是交易许可，不是执行指令，不生成交易信号。
交易能力禁用，执行能力禁用。
next_allowed_stage 只是流程提示，不代表可以交易或可以执行。
```

未来 UI 应避免使用“可以交易”“允许交易”等容易误导的文案。若必须在安全说明中提及这些词，只能用于否定语义或 forbidden list。

## 9. 允许展示内容

前端允许展示以下经过 mapper 白名单进入 ViewModel 的内容：

- `overallExplanation`
- `statusExplanation`
- `componentExplanations`
- `blockerExplanations`
- `warningExplanations`
- `readinessExplanation`
- `nextAllowedStageExplanation`
- `nextBlockedStageExplanation`
- `userSafeNextSteps`
- `userForbiddenActions`
- `unknowns`
- `safetyFlags`
- `notes`
- `readOnly`
- `demoOnly`
- `isTradable`
- `canExecute`
- `isTradingPermission`
- `isExecutionInstruction`
- `allowedToCallEa`
- `allowedToModifyRisk`
- `passed`
- `statusCode`
- `reportVersion`
- `reportType`
- `generatedAt`
- `sourceScope`
- `explanationScope`
- `blockReasons`
- `warningReasons`
- `uiSafetyStatus`
- `uiSafetyMessage`

允许展示不等于允许执行。所有展示都必须是只读、非交易、非执行语义。

## 10. 禁止展示字段

前端 UI、ViewModel、组件 props 不得展示或保留：

- `raw_payload`
- `raw_account_snapshot`
- `raw_positions_order_history`
- `raw_market_symbol`
- `account_number`
- `login`
- `password`
- `credential`
- `token`
- `secret`
- `api_key`
- `key`
- `traceback`
- `stack_trace`
- `system_path`
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
- `trade_signal`
- `trading_action`

如果未来 API response 出现上述字段，mapper 必须丢弃，并可触发 `security_blocked`。这些字段不得进入用户可见 UI，不得进入 ViewModel，不得进入组件 props，不得进入可复制的展示内容。

## 11. 禁止 UI 文案

前端用户可见文案不得将以下语义作为行动建议、按钮、状态、推荐或解释结果：

- 买入
- 卖出
- 开仓
- 平仓
- 建议手数
- 可以交易
- 允许交易
- 自动下单
- 自动交易
- 执行交易
- 下单指令
- 风控放行
- 绕过风控
- buy
- sell
- should buy
- should sell
- open position
- close position
- execute trade
- allow trade
- can trade
- suggested lot

这些词可以出现在文档、测试、安全常量、forbidden field list 中，用于安全检查。但不得作为用户可见行动建议、按钮、状态、推荐或解释结果出现。

## 12. 用户安全下一步

前端可以展示的 safe next steps 只能是非交易动作，例如：

- 查看只读解释。
- 查看只读诊断。
- 手动刷新只读解释。
- 手动刷新只读诊断。
- 查看阻断原因。
- 查看警告原因。
- 检查数据校验状态。
- 等待下一阶段开发。
- 进行文档审查。
- 进行安全回归检查。
- 进行 Dashboard 展示检查。

不得展示：

- 下单。
- 开仓。
- 平仓。
- 加仓。
- 减仓。
- 自动交易。
- 自动训练。
- 调用 EA。
- 修改风控。
- 计算手数。
- 生成 `TradePlan`。
- 连接真实账户。
- 连接模拟账号。
- 读取真实 MT4 数据。

safe next step 不能变成会写入后端、执行交易、连接账号、读取运行目录、修改风控或触发 Agent 的按钮。

## 13. 与现有 Dashboard 的关系

现有 `DemoReadOnlyDiagnosticsDashboard` 展示诊断状态。未来 `ExplanationPanel` 只解释诊断状态。

必须保持：

- Diagnostics Dashboard 展示诊断状态。
- ExplanationPanel 解释诊断状态。
- ExplanationPanel 不能改变 Diagnostics Dashboard 的安全字段。
- ExplanationPanel 不能让 `can_execute` 变成 `true`。
- ExplanationPanel 不能让 `is_tradable` 变成 `true`。
- ExplanationPanel 不能新增交易按钮。
- ExplanationPanel 不能新增执行按钮。
- ExplanationPanel 不能新增自动刷新。
- ExplanationPanel 未来只能作为 Dashboard 内的只读区块或旁侧只读区块。
- ExplanationPanel 不能向 Dashboard 注入交易、执行、风控、仓位、MT4、EA 或 Agent 操作。

如果未来 Dashboard 读取 diagnostics 和 explanation 两个 API，二者都必须保持手动触发、只读展示、白名单映射和安全字段 fail closed。

## 14. 与后端 explanation API 的关系

后端 `GET /api/demo-readonly/explanation` 已有安全守卫，但前端仍必须做白名单 mapper。

前端规则：

- 不能直接信任所有字段。
- 不能展示 API raw response。
- 不能把 API response 原样 dump 到页面。
- 必须丢弃未知字段。
- 必须阻断 forbidden fields。
- 必须在安全字段异常时显示 `SECURITY BLOCKED`。
- 必须把 `read_only=true`、`demo_only=true`、`is_tradable=false`、`can_execute=false` 作为硬性展示前置条件。
- 必须把 `is_trading_permission=false`、`is_execution_instruction=false`、`allowed_to_call_ea=false`、`allowed_to_modify_risk=false` 作为硬性安全约束。

后端安全守卫是第一层，前端 mapper 是第二层。任何一层发现异常，都必须 fail closed。

## 15. 与 LLM / Agent 的关系

当前前端不接 LLM，不接 Agent，不写 prompt，不调用 prompt executor。

未来如果接 LLM，必须另开阶段，并满足：

- LLM 输出必须经过后端 forbidden field checker。
- LLM 输出必须经过前端 forbidden field checker。
- LLM 不能生成交易建议。
- LLM 不能生成执行指令。
- LLM 不能生成 `TradePlan`。
- LLM 不能修改风险参数。
- LLM 不能调用 EA。
- LLM 不能连接 MT4。
- Agent 不能把 `ExplanationPanel` 展示结果当作交易许可。
- Agent 不能把 `ExplanationPanel` 展示结果当作执行指令。
- Agent 不能把 `nextAllowedStageExplanation` 当作执行下一步交易任务。

Explanation 前端层只是展示层，不是 prompt executor，不是 Agent controller，不是交易策略入口。

## 16. 未来实现阶段顺序

建议后续顺序：

```text
1S-4：定义 DemoReadOnlyExplanation Frontend Contract 文档
1S-5：实现前端 explanation API client 与 mapper
1S-6：实现 DemoReadOnlyExplanationPanel 只读展示
1S-7：前端 ExplanationPanel 安全回归检查
然后再考虑是否创建 v0.23.0-readonly-explanation-ui
```

当前工单只做 1S-4，不实现任何代码，不修改任何运行逻辑，不进入 1S-5。

## 17. 当前仍不实现

当前仍不实现：

- 前端 API client。
- `ExplanationPanel`。
- React 页面。
- 前端路由。
- Dashboard 修改。
- 自动刷新。
- 自动轮询。
- WebSocket。
- SSE。
- 后端 API。
- 后端业务逻辑。
- LLM。
- prompt executor。
- Agent 代码。
- RiskGate。
- PositionSizing。
- ExecutionGate。
- TradePlanSchema。
- 执行 API。
- 自动交易。
- MT4 连接。
- 模拟账号连接。
- 真实账号连接。
- 真实 data 读取。
- `data/` 运行目录读取。
- `.env` 读取。
- 日志读取。
- 数据库读取。
- 运行文件写入。
- 网络访问。
- 真实交易建议。
- suggested lot 或 final lot。
- buy / sell / open / close 指令。
- EA 指令。
- 完整 raw payload 展示。

## 18. 安全结论

`DemoReadOnlyExplanation` 前端展示层必须始终保持 demo-only、read-only、non-trading、non-execution。它只能把后端只读解释报告转换为安全的人类可读说明。

该层不能提供交易许可，不能提供执行指令，不能提供风险覆盖，不能提供仓位计算，不能调用 MT4，不能调用 EA，不能连接账号，不能读取运行数据，不能展示 raw payload，不能展示敏感字段，不能生成或展示任何真实交易建议。
