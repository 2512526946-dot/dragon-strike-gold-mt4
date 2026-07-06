# DemoReadOnlyDiagnostics FrontendContract

本文定义未来 `DemoReadOnlyDiagnostics Dashboard` 的前端只读展示契约。当前工单只写文档，不实现 React 页面、前端组件、前端 API client、`types.ts`、`mapper.ts`、`api.ts`、后端 API、reader、parser、MT4 bridge、EA、MQL4、风控、仓位计算、执行链路或自动交易。

## 文件用途

本文档用于定义未来 `DemoReadOnlyDiagnostics Dashboard` 的前端数据契约、页面结构、字段映射规则、安全过滤规则、UI 状态规则和后续实现边界。

本文必须被理解为前端展示契约：

- 本文档只是前端展示契约。
- 本轮不实现 React 页面。
- 本轮不实现前端 API client。
- 本轮不调用后端 API。
- 本轮不修改后端。
- Dashboard 未来只用于展示 demo-only / read-only diagnostics。
- Dashboard 不是交易页面。
- Dashboard 不是执行页面。
- Dashboard 不是 MT4 控制台。
- Dashboard 不能展示交易建议。
- Dashboard 不能展示执行许可。
- Dashboard 不能展示完整 raw payload。

任何通过状态、READY 状态、HTTP 200 或下一阶段提示，都不得被解释为交易许可、执行许可、下单许可、EA 调用许可或风控覆盖许可。

## 当前后端接口背景

当前后端已有只读诊断接口：

```text
GET /api/demo-readonly/diagnostics
```

该 API 已具备：

- demo-only。
- read-only。
- diagnostics only。
- 不返回 raw payload。
- 不返回账号密码、凭证、登录字段。
- 不返回交易建议字段。
- 不返回执行指令字段。
- 递归阻断或清洗禁止字段。
- 不安全安全字段触发 safety violation。
- 异常时安全失败。
- 始终 `can_execute=false`。

前端 Dashboard 只能把该 API 的安全摘要映射为只读展示状态。前端不得把 API 响应扩展为交易入口、执行入口、MT4 控制入口、风控入口或仓位计算入口。

## 前端定位

未来 Dashboard 的定位必须保持：

- demo-only diagnostics dashboard。
- read-only observability panel。
- 只读安全控制台。
- 只展示诊断状态。
- 只展示安全摘要。
- 不提供任何交易动作。
- 不提供任何执行动作。
- 不提供任何自动交易开关。
- 不提供任何 MT4 操作入口。
- 不提供任何风控参数修改入口。
- 不提供任何仓位计算入口。

Dashboard 只回答一个问题：当前 demo-only / read-only diagnostics 摘要是否可以安全展示。Dashboard 不回答是否可以交易、是否可以执行、是否可以接入 MT4、是否可以计算仓位、是否可以覆盖风控。

## 前端数据契约规划

未来前端可以规划以下 TypeScript 类型，但当前工单不创建任何代码文件：

- `DemoDiagnosticsApiResponse`
- `DemoDiagnosticsViewModel`
- `ComponentStatusViewModel`
- `BundleStatusViewModel`
- `ReadinessViewModel`
- `SafetyFlagsViewModel`

这些类型只是未来代码规划，本轮不实现 `types.ts`、`contracts.ts`、`mapper.ts` 或 `api.ts`。

安全字段必须包含：

- `read_only`
- `demo_only`
- `is_tradable`
- `can_execute`
- `is_trading_permission`
- `is_execution_instruction`
- `allowed_to_call_ea`
- `allowed_to_modify_risk`

安全字段在 ViewModel 中必须满足：

- `read_only=true`
- `demo_only=true`
- `is_tradable=false`
- `can_execute=false`
- `is_trading_permission=false`
- `is_execution_instruction=false`
- `allowed_to_call_ea=false`
- `allowed_to_modify_risk=false`

未来类型草案可以采用以下只读展示方向：

```ts
interface SafetyFlagsViewModel {
  read_only: true;
  demo_only: true;
  is_tradable: false;
  can_execute: false;
  is_trading_permission: false;
  is_execution_instruction: false;
  allowed_to_call_ea: false;
  allowed_to_modify_risk: false;
}

interface ComponentStatusViewModel extends SafetyFlagsViewModel {
  component_name: string;
  status: "passed" | "blocked" | "warning" | "unknown";
  block_reasons: string[];
  warning_reasons: string[];
  safe_count?: number;
  safe_summary?: string;
}

interface BundleStatusViewModel extends SafetyFlagsViewModel {
  passed: boolean;
  status_code: string;
  block_summary: string;
  warning_summary: string;
}

interface ReadinessViewModel {
  readiness_notes: string[];
  next_allowed_stage: string | null;
  next_blocked_stage: string | null;
}

interface DemoDiagnosticsViewModel extends SafetyFlagsViewModel {
  api_version?: string;
  endpoint: "/api/demo-readonly/diagnostics";
  generated_at?: string;
  passed: boolean;
  status_code: string;
  source_scope: "docs_fixture_only";
  validation_stage: string;
  fixture_source?: string;
  bundle: BundleStatusViewModel;
  components: ComponentStatusViewModel[];
  block_reasons: string[];
  warning_reasons: string[];
  readiness: ReadinessViewModel;
  ui_state: "loading" | "success" | "blocked" | "security_blocked" | "error";
}
```

上述类型草案不得被理解为本轮代码实现。未来 1Q-2 才允许创建前端代码文件。

## 未来目录结构规划

未来前端目录结构建议如下：

```text
frontend/src/features/demoDiagnostics/
├─ types.ts
├─ contracts.ts
├─ mapper.ts
├─ api.ts
└─ components/
   ├─ DemoReadOnlyDiagnosticsDashboard.tsx
   ├─ OverallStatusPanel.tsx
   ├─ BundleStatusPanel.tsx
   ├─ ComponentStatusList.tsx
   └─ ReadinessPanel.tsx
```

目录规划说明：

- 当前工单不创建这些前端文件。
- 这些路径仅作为 1Q-2 实现参考。
- 1Q-2 才允许实现前端代码。
- `types.ts` 只定义白名单类型。
- `contracts.ts` 只定义允许字段、禁止字段和安全不变量。
- `mapper.ts` 只做 API response 到 ViewModel 的白名单转换。
- `api.ts` 未来只能调用 `GET /api/demo-readonly/diagnostics`。
- `components/` 未来只做只读展示，不做执行入口。

## Dashboard 页面结构规划

未来页面根组件：

```text
DemoReadOnlyDiagnosticsDashboard
```

未来页面必须包含四个区域。

### A. OverallStatusPanel

允许展示：

- `passed`
- `status_code`
- `validation_stage`
- `source_scope`
- `read_only` badge
- `demo_only` badge
- `is_tradable=false` badge
- `can_execute=false` badge
- `is_trading_permission=false` badge
- `is_execution_instruction=false` badge
- `allowed_to_call_ea=false` badge
- `allowed_to_modify_risk=false` badge

必须明确展示：

- 只读诊断。
- 非交易许可。
- 非执行指令。
- 交易能力禁用。
- 执行能力禁用。
- 不可自动下单。

### B. BundleStatusPanel

允许展示：

- `bundle_validation_status.passed`
- `bundle_validation_status.status_code`
- bundle block summary
- bundle warning summary

不得展示：

- raw payload。
- bundle 内部原始结构。
- 账号字段。
- 登录字段。
- 交易字段。
- 执行字段。

### C. ComponentStatusList

允许展示组件：

- `account_snapshot`
- `positions_order_history`
- `market_symbol`

每个 component 只能展示：

- component name。
- status。
- block_reasons。
- warning_reasons。
- safe count。
- safe summary。

不得展示完整 raw component payload。不得展示完整账号快照、完整持仓、完整订单历史、完整行情 payload 或任何账号标识。

### D. ReadinessPanel

允许展示：

- `readiness_notes`
- `next_allowed_stage`
- `next_blocked_stage`

必须明确：

- `next_allowed_stage` 是流程提示，不是交易许可。
- `next_blocked_stage` 是阶段限制，不是交易指令。
- `readiness_notes` 是只读开发阶段说明，不是交易建议。

## API 到 UI 字段映射规则

未来映射分为两层：

```text
API response -> DemoDiagnosticsViewModel -> UI panels
```

映射规则：

- 使用白名单字段映射。
- 未知字段默认丢弃。
- 禁止字段必须丢弃或触发 `security_blocked`。
- HTTP 200 不等于可以交易。
- `passed=true` 不等于可以交易。
- `status_code=READY` 不等于可以交易。
- `next_allowed_stage` 不等于交易许可。
- `readiness_notes` 不等于交易建议。
- ViewModel 中所有安全字段必须保持固定安全值。

字段映射表：

| API 字段 | ViewModel 字段 | UI 区域 | 规则 |
| --- | --- | --- | --- |
| `api_version` | `api_version` | OverallStatusPanel | 可选展示为诊断版本 |
| `endpoint` | `endpoint` | OverallStatusPanel | 只能是 `/api/demo-readonly/diagnostics` |
| `generated_at` | `generated_at` | OverallStatusPanel | 可选展示为生成时间 |
| `passed` | `passed` | OverallStatusPanel | 只表示诊断摘要是否通过 |
| `status_code` | `status_code` | OverallStatusPanel | 只表示诊断状态，不是交易状态 |
| `source_scope` | `source_scope` | OverallStatusPanel | 必须保持 docs fixture 范围 |
| `validation_stage` | `validation_stage` | OverallStatusPanel | 展示当前只读校验阶段 |
| `fixture_source` | `fixture_source` | OverallStatusPanel | 只展示 fixture 来源摘要 |
| `bundle_validation_status` | `bundle` | BundleStatusPanel | 只抽取安全状态摘要 |
| `component_statuses` | `components` | ComponentStatusList | 只抽取安全组件摘要 |
| `block_reasons` | `block_reasons` | BundleStatusPanel / ComponentStatusList | 只展示安全阻断原因 |
| `warning_reasons` | `warning_reasons` | BundleStatusPanel / ComponentStatusList | 只展示安全警告原因 |
| `readiness_notes` | `readiness.readiness_notes` | ReadinessPanel | 只展示流程说明 |
| `next_allowed_stage` | `readiness.next_allowed_stage` | ReadinessPanel | 只展示下一规划阶段 |
| `next_blocked_stage` | `readiness.next_blocked_stage` | ReadinessPanel | 只展示仍阻断阶段 |
| `read_only` | `read_only` | OverallStatusPanel | 必须为 `true` |
| `demo_only` | `demo_only` | OverallStatusPanel | 必须为 `true` |
| `is_tradable` | `is_tradable` | OverallStatusPanel | 必须为 `false` |
| `can_execute` | `can_execute` | OverallStatusPanel | 必须为 `false` |
| `is_trading_permission` | `is_trading_permission` | OverallStatusPanel | 必须为 `false` |
| `is_execution_instruction` | `is_execution_instruction` | OverallStatusPanel | 必须为 `false` |
| `allowed_to_call_ea` | `allowed_to_call_ea` | OverallStatusPanel | 必须为 `false` |
| `allowed_to_modify_risk` | `allowed_to_modify_risk` | OverallStatusPanel | 必须为 `false` |

## 显式允许展示字段

前端 mapper、ViewModel、UI state 和页面可以展示以下字段：

- `api_version`
- `endpoint`
- `generated_at`
- `passed`
- `status_code`
- `source_scope`
- `validation_stage`
- `fixture_source`
- `bundle_validation_status`
- `component_statuses`
- `block_reasons`
- `warning_reasons`
- `readiness_notes`
- `next_allowed_stage`
- `next_blocked_stage`
- `read_only`
- `demo_only`
- `is_tradable`
- `can_execute`
- `is_trading_permission`
- `is_execution_instruction`
- `allowed_to_call_ea`
- `allowed_to_modify_risk`

允许字段也必须经过白名单转换。允许展示不代表可以展示其内部 raw payload。

## 显式禁止字段

前端 mapper、ViewModel、UI state 和页面文案不得包含以下字段或同义字段：

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

禁止字段不得以重命名、嵌套字段、metadata、debug 字段、列表项、错误对象、raw response 或 UI state 形式进入前端展示契约。未来如果 mapper 检测到禁止字段，应丢弃该字段或进入 `security_blocked`。

## UI 状态规则

未来 UI 状态必须只表达只读诊断状态。

### A. loading

loading 状态规则：

- 显示正在加载只读诊断。
- 不显示任何交易词。
- 不显示任何执行词。
- 不展示旧的 raw response。
- 不写 localStorage。
- 不写 sessionStorage。

### B. success / passed=true

success 状态规则：

- 可以显示通过状态。
- 仍必须显示 `can_execute=false`。
- 仍必须显示非交易许可。
- 仍必须显示非执行指令。
- 不得出现“可以交易”或“允许交易”。
- 不得出现交易建议、执行建议、EA 指令或建议手数。

### C. blocked / passed=false

blocked 状态规则：

- 显示阻断状态。
- 展示 `block_reasons`。
- 展示安全警告摘要。
- 不得出现“建议开仓/平仓”。
- 不得给出任何处理交易的行动建议。

### D. security_blocked

当 API 返回不安全字段或安全字段不满足时显示：

```text
SECURITY BLOCKED - INVALID DIAGNOSTICS STATE
```

security_blocked 状态规则：

- 不展示原始响应。
- 不展示敏感字段。
- 不展示 raw payload。
- 不展示 traceback。
- 不展示系统路径。
- 不展示 raw error object。
- 不 fallback 到正常展示。

### E. error

API 请求失败时：

- 显示安全错误。
- 不展示 stack trace。
- 不展示系统路径。
- 不展示 raw error object。
- 不推断后端状态。
- 不推断交易状态。
- 不推断执行状态。

## UI 文案规则

页面中必须避免以下中文或英文交易许可文案：

- 买入
- 卖出
- 开仓
- 平仓
- 建议手数
- 可以交易
- 允许交易
- 自动下单
- buy
- sell
- open position
- close position
- suggested lot
- execute trade
- allow trade
- can trade

允许使用以下只读诊断文案：

- 只读诊断
- 数据校验
- 安全状态
- 观察层
- 非交易许可
- 非执行指令
- 执行能力禁用
- 交易能力禁用
- demo-only
- read-only

所有 UI 文案必须避免把 `passed=true`、HTTP 200、READY、`next_allowed_stage` 或 `readiness_notes` 描述为交易许可、交易建议或执行许可。

## 未来 1Q-2 实现要求摘要

未来 1Q-2 实现时必须：

- 只调用 `GET /api/demo-readonly/diagnostics`。
- 不使用 `POST` / `PUT` / `PATCH` / `DELETE`。
- 不使用 WebSocket。
- 不自动轮询。
- 不写 localStorage。
- 不写 sessionStorage。
- 允许手动刷新。
- 使用 mapper 白名单转换。
- 实现 `security_blocked`。
- 不展示 raw payload。
- 不展示交易建议。
- 不展示执行指令。
- 不展示 EA 指令。
- 不展示建议手数。
- 不创建任何交易入口。
- 不创建任何执行入口。

未来 1Q-2 实现仍必须重新运行后端测试、前端 build、字段边界检查和安全检查。

## 当前仍不实现

本轮不实现：

- 不实现 React 页面。
- 不实现组件。
- 不实现 `types.ts`。
- 不实现 `mapper.ts`。
- 不实现 `api.ts`。
- 不调用 API。
- 不修改后端。
- 不新增后端 API。
- 不新增前端 API client。
- 不新增前端路由。
- 不新增 MT4 EA。
- 不新增 MQL4。
- 不接 MT4。
- 不接模拟账号。
- 不读取真实 `data/`。
- 不读取 `.env`。
- 不读取日志。
- 不读取数据库。
- 不保存凭证。
- 不实现 RiskGate。
- 不实现 PositionSizing。
- 不实现 ExecutionGate。
- 不实现 TradePlanSchema。
- 不实现执行 API。
- 不实现自动交易。

本文档只定义未来前端只读展示契约。任何代码实现都必须在后续独立工单中完成，并继续保持 demo-only、read-only、diagnostics only、安全失败和不进入执行链路的边界。
