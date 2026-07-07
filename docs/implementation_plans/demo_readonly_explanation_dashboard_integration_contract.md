# DemoReadOnlyExplanation Dashboard Integration Contract

本文档定义未来如何把 `DemoReadOnlyExplanationPanel` 安全接入现有 `DemoReadOnlyDiagnosticsDashboard`。本文档只是 Dashboard 接入契约；当前 1T-1 工单只写文档，不实现代码，不接入 Dashboard，不修改 `App.tsx`，不新增页面，不新增路由，不新增 API 调用，不新增刷新按钮，不新增自动刷新，不新增自动轮询，不新增交易、执行、风控、仓位、MT4、LLM 或 Agent 能力。

## 1. 文件用途

本文档用于约束未来 Dashboard 集成阶段的只读接入方式，确保 explanation UI foundation 在进入 Dashboard 时仍保持 demo-only、read-only、non-trading、non-execution。

当前工单明确不做：

- 不实现 React 代码。
- 不修改 `DemoReadOnlyDiagnosticsDashboard`。
- 不修改 `App.tsx`。
- 不接入 `DemoReadOnlyExplanationPanel`。
- 不新增前端页面或路由。
- 不新增 API 调用。
- 不新增手动刷新按钮。
- 不新增自动刷新或自动轮询。
- 不新增 WebSocket 或 SSE。
- 不新增后端 API。
- 不修改现有后端 API。
- 不新增交易、执行、风控、仓位、MT4、LLM、prompt executor 或 Agent 能力。

本文档只定义未来接入规则。任何实现都必须在后续独立工单中完成，并重新运行后端测试、前端 build、前端测试和安全检查。

## 2. 接入定位

未来接入后，`DemoReadOnlyDiagnosticsDashboard` 仍然是只读诊断展示层。`DemoReadOnlyExplanationPanel` 只能作为 diagnostics 状态的只读解释区块。

必须保持以下定位：

- Diagnostics Dashboard 负责展示只读诊断状态。
- Explanation panel 负责解释只读诊断状态。
- Explanation panel 不改变 diagnostics 的安全字段。
- Explanation panel 不改变系统状态。
- Explanation panel 不触发任何交易。
- Explanation panel 不触发任何执行。
- Explanation panel 不触发任何风控修改。
- Explanation panel 不触发任何仓位计算。
- Explanation panel 不连接 MT4。
- Explanation panel 不连接模拟账号或真实账号。
- Explanation panel 不提供信号、建议、可执行计划或操作入口。

`passed=true`、`ready`、HTTP 200、`next_allowed_stage`、解释文本、Dashboard 展示顺序或用户手动刷新动作，都不得被解释为交易许可、执行许可、风控放行、仓位计算许可、EA 调用许可或自动交易能力。

## 3. 允许的数据流

未来 Dashboard 集成只允许以下数据流：

```text
GET /api/demo-readonly/explanation
↓
fetchDemoReadOnlyExplanation
↓
mapDemoReadOnlyExplanationApiToViewModel
↓
DemoReadOnlyExplanationViewModel
↓
DemoReadOnlyExplanationPanel
```

数据流规则：

- UI 只能接收 `DemoReadOnlyExplanationViewModel`。
- UI 不能接收 raw API response。
- UI 不能绕过 mapper。
- UI 不能展示 unknown fields。
- UI 不能展示 raw payload。
- UI 不能展示 forbidden fields。
- UI 不能展示账号、密码、凭证、token、secret、login。
- UI 不能展示交易字段。
- UI 不能展示执行字段。
- UI 不能把 `next_allowed_stage` 解释为交易许可。
- UI 不能把 `user_safe_next_steps` 渲染成交易、执行、MT4、风控或仓位操作。

后端 explanation API 是第一层只读安全边界；前端 mapper 是第二层只读安全边界；Dashboard 组件是第三层展示边界。任一层发现安全字段异常或 forbidden fields，都必须 fail closed。

## 4. 触发方式规划

未来第一版 Dashboard 接入建议只允许手动触发，不允许后台自动触发。

允许的触发方式：

- 页面加载后不自动持续请求 explanation。
- 用户点击现有 diagnostics 手动刷新时，可以由父组件同步刷新 explanation。
- 或者由父组件控制独立的只读解释加载状态，但不得新增交易按钮、执行按钮、MT4 操作入口、风控修改入口或仓位计算入口。

未来如确需单独按钮，按钮文案必须保持只读语义。

允许文案：

- 刷新只读解释
- 更新只读解释
- 重新加载只读解释

禁止文案：

- 执行
- 运行交易
- 生成交易
- 获取买卖建议
- 自动下单
- 风控放行
- 计算仓位

禁止触发方式：

- 不允许自动轮询。
- 不允许后台自动刷新。
- 不允许 WebSocket。
- 不允许 SSE。
- 不允许定时刷新。
- 不允许隐藏请求。
- 不允许交易触发。
- 不允许执行触发。
- 不允许通过 localStorage 或 sessionStorage 保存状态后自动恢复执行。

## 5. UI 布局规划

未来 Dashboard 内部结构建议：

```text
DemoReadOnlyDiagnosticsDashboard
├─ Diagnostics 主区块
│  ├─ OverallStatusPanel
│  ├─ BundleStatusPanel
│  ├─ ComponentStatusList
│  └─ ReadinessPanel
└─ Explanation 只读解释区块
   ├─ ExplanationSafetyBanner
   ├─ ExplanationOverallPanel
   ├─ ExplanationStatusPanel
   ├─ ExplanationComponentList
   ├─ ExplanationNextStagePanel
   ├─ ExplanationSafeNextStepsPanel
   └─ ExplanationForbiddenActionsPanel
```

布局规则：

- Explanation 区块不能放在交易操作区域。
- Explanation 区块不能带有交易操作按钮。
- Explanation 区块不能带有执行操作按钮。
- Explanation 区块不能显示为“信号”。
- Explanation 区块不能显示为“建议”。
- Explanation 区块不能显示为“可执行计划”。
- Explanation 区块必须明确是只读解释。
- Explanation 区块只能显示 mapper 清洗后的 ViewModel。
- Explanation 区块不能展示 raw payload、敏感字段、交易字段或执行字段。

## 6. 状态规划

未来 Dashboard 集成必须定义并安全展示以下状态。

### 6.1 not_loaded

用户看到：

- 尚未加载只读解释。
- 当前区块保持只读。
- 非交易许可、非执行指令、安全边界文案。

不显示：

- 默认成功状态。
- 默认交易状态。
- 默认下一步交易提示。
- raw payload。

是否允许再次加载：允许未来通过明确的只读加载动作触发。

为什么不代表交易许可：没有解释 ViewModel，也没有任何交易字段。

为什么不代表执行指令：没有执行内容，没有执行入口，`canExecute` 必须保持 false。

### 6.2 loading

用户看到：

- 正在读取只读解释。
- 只读、安全、非交易提示。

不显示：

- raw payload。
- 交易字段。
- 执行字段。
- 敏感字段。

是否允许再次加载：不建议重复点击；可由父组件禁用重复加载。

为什么不代表交易许可：loading 只代表读取解释报告，不包含交易许可。

为什么不代表执行指令：loading 不携带执行字段，不触发后端写入或 MT4 操作。

### 6.3 ready

用户看到：

- 安全映射后的只读解释。
- `readOnly=true`、`demoOnly=true`。
- `isTradable=false`、`canExecute=false`。
- 只读解释、安全文案、阻断和警告摘要。

不显示：

- raw payload。
- 账号、凭证、路径、traceback。
- 交易建议。
- 执行指令。

是否允许再次加载：允许未来手动刷新只读解释，但不允许自动刷新。

为什么不代表交易许可：ready 只代表解释报告可安全展示，不代表交易、风控或执行许可。

为什么不代表执行指令：ready 没有执行入口，且 `canExecute=false`。

### 6.4 blocked

用户看到：

- 只读解释被阻断。
- 阻断原因。
- 安全字段摘要。

不显示：

- raw payload。
- 未清洗字段。
- 交易字段。
- 执行字段。

是否允许再次加载：允许未来手动刷新。

为什么不代表交易许可：blocked 明确表示只读解释不能正常展示或不能进入下一只读阶段。

为什么不代表执行指令：blocked 不包含执行能力，且必须展示执行能力禁用。

### 6.5 api_error

用户看到：

- 无法读取只读解释。
- 请确认只读 explanation API 可用。
- 这不是交易许可，也不是执行指令。

不显示：

- stack trace。
- system path。
- raw error object。
- token、secret、credential。

是否允许再次加载：允许未来手动刷新。

为什么不代表交易许可：API 错误没有产生安全解释报告。

为什么不代表执行指令：API 错误不触发任何执行流程。

### 6.6 security_blocked

用户看到：

- `SECURITY BLOCKED`。
- 响应包含不允许字段或安全字段异常。
- 页面不会展示该响应内容。

不显示：

- 触发阻断的敏感原文。
- forbidden field 的值。
- raw response。
- raw payload。
- 异常原文。
- 交易或执行建议。

是否允许再次加载：允许未来手动刷新。

为什么不代表交易许可：security blocked 表示安全异常，必须 fail closed。

为什么不代表执行指令：security blocked 会阻断展示和执行语义。

### 6.7 stale_or_unknown

用户看到：

- 只读解释状态未知或可能过旧。
- 需要重新读取只读解释。
- 仍然保持非交易、非执行、安全阻断语义。

不显示：

- 过旧 raw payload。
- 过旧交易语义。
- 过旧执行语义。

是否允许再次加载：允许未来手动刷新。

为什么不代表交易许可：状态未知或过旧时必须 fail closed。

为什么不代表执行指令：状态未知或过旧不能生成任何执行动作。

## 7. 安全字段要求

未来接入后，页面必须继续展示或保持以下安全字段：

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

规则：

- 任一 safety flag 缺失或异常时，页面必须显示 `SECURITY BLOCKED`。
- `SECURITY BLOCKED` 不得暴露 raw payload。
- `SECURITY BLOCKED` 不得暴露异常原文。
- `SECURITY BLOCKED` 不得显示交易或执行建议。
- `SECURITY BLOCKED` 不得 fallback 到正常展示。
- `readOnly=true` 不代表可以交易。
- `demoOnly=true` 不代表可以执行。
- `isTradable=false` 和 `canExecute=false` 必须被视为硬边界。

## 8. 禁止展示字段

Dashboard 接入后，Explanation 区块、ViewModel、props、UI 不得展示或保留：

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

## 9. 禁止 UI 文案

Dashboard 接入后的用户可见文案不得将以下语义作为行动建议、按钮、状态、推荐或解释结果：

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

允许使用：

- 只读解释
- 只读诊断
- 非交易许可
- 非执行指令
- 交易能力禁用
- 执行能力禁用
- 流程提示
- 阶段限制
- 安全状态
- 解释层

禁止词可以出现在文档、测试、安全常量或 forbidden list 中，用于安全检查；不得作为用户可见行动建议、按钮、状态、推荐或解释结果出现。

## 10. 与现有 diagnostics Dashboard 的关系

未来接入必须保持：

- Diagnostics Dashboard 的手动刷新仍然只代表只读诊断刷新。
- ExplanationPanel 的接入不能改变 diagnostics Dashboard 的原有安全检查。
- ExplanationPanel 的接入不能降低 diagnostics safety check。
- ExplanationPanel 的接入不能使 `can_execute` 变成 `true`。
- ExplanationPanel 的接入不能使 `is_tradable` 变成 `true`。
- ExplanationPanel 的接入不能新增交易按钮。
- ExplanationPanel 的接入不能新增执行按钮。
- ExplanationPanel 的接入不能新增风控入口。
- ExplanationPanel 的接入不能新增仓位入口。
- ExplanationPanel 的接入不能新增 MT4 操作入口。
- ExplanationPanel 的接入不能新增账号连接入口。

如果未来 Dashboard 同时读取 diagnostics 和 explanation 两个 API，二者都必须保持手动触发、只读展示、白名单映射和安全字段 fail closed。

## 11. 与前端安全检查的关系

未来接入时必须同步更新：

- `test:demo-diagnostics-safety`
- `test:demo-explanation-safety`

至少检查：

- App / Dashboard 接入是否只读。
- 是否只调用 `GET /api/demo-readonly/explanation`。
- 是否无自动轮询。
- 是否无自动刷新。
- 是否无 WebSocket / SSE。
- 是否无 localStorage / sessionStorage。
- 是否无交易按钮。
- 是否无执行按钮。
- 是否无刷新按钮的交易或执行语义。
- 是否无 MT4 / 风控 / 仓位入口。
- 是否不展示 raw payload / sensitive / trading / execution fields。
- 是否安全文案存在。
- 是否 `SECURITY BLOCKED` 状态存在。
- 是否 `DemoReadOnlyDiagnosticsDashboard` 的既有安全检查仍通过。

任何未来接入代码必须先让两个安全脚本通过，再进入验收。

## 12. 与 LLM / Agent 的关系

Dashboard 接入不等于 Agent 接入：

- Dashboard 接入不调用 LLM。
- Dashboard 接入不写 prompt。
- Dashboard 接入不调用 prompt executor。
- Dashboard 接入不让 Agent 使用 explanation 作为交易许可。
- Dashboard 接入不让 Agent 使用 explanation 作为执行指令。
- Dashboard 接入不让 Agent 使用 `next_allowed_stage` 作为交易任务。
- Dashboard 接入不生成 `TradePlan`。
- Dashboard 接入不新增 Agent controller。

未来如接 LLM / Agent，必须另开阶段，且必须重新定义 prompt、Agent、forbidden field、输出安全和执行隔离边界。

## 13. 未来实现阶段顺序

建议后续阶段顺序：

```text
1T-1：定义 Dashboard Integration Contract 文档
1T-2：实现 Dashboard 只读接入，但只允许手动加载/刷新 explanation
1T-3：强化 Dashboard + Explanation 集成安全回归检查
1T-4：创建 v0.24.0-readonly-explanation-dashboard-integration 阶段性 tag
```

当前工单只做 1T-1，不实现任何代码，不修改任何运行逻辑，不进入 1T-2。

## 14. 当前仍不实现

当前仍不实现：

- React 页面。
- Dashboard 接入。
- `App.tsx` 修改。
- 新前端页面。
- 新前端路由。
- 新 API 调用。
- 新手动刷新按钮。
- 自动刷新。
- 自动轮询。
- WebSocket。
- SSE。
- localStorage / sessionStorage 写入。
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
- 真实交易建议。
- suggested lot 或 final lot。
- buy / sell / open / close 指令。
- EA 指令。
- 完整 raw payload 展示。

## 15. 安全结论

`DemoReadOnlyExplanationPanel` 未来可以接入 `DemoReadOnlyDiagnosticsDashboard`，但只能作为只读解释区块。它不能改变 diagnostics 的安全字段，不能改变系统状态，不能触发交易、执行、风控修改、仓位计算、MT4、LLM 或 Agent 能力。

未来 Dashboard 集成必须始终保持 demo-only、read-only、non-trading、non-execution。任何异常 safety flag、forbidden field、raw payload、敏感字段、交易字段或执行字段，都必须触发 fail closed，并显示安全阻断状态。
