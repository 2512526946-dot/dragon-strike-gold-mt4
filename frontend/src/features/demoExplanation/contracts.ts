import type { DemoReadOnlyExplanationSafetyFlags } from "./types";

export const DEMO_READONLY_EXPLANATION_ENDPOINT =
  "/api/demo-readonly/explanation";

export const DEMO_READONLY_EXPLANATION_ALLOWED_METHODS = ["GET"] as const;

export const DEMO_READONLY_EXPLANATION_ALLOWED_STATUS_CODES = [
  "READONLY_EXPLANATION_READY",
  "READONLY_EXPLANATION_BLOCKED",
  "READONLY_EXPLANATION_INPUT_INVALID",
  "READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION",
  "READONLY_EXPLANATION_SOURCE_ERROR",
  "READONLY_EXPLANATION_API_ERROR",
] as const;

export const DEMO_READONLY_EXPLANATION_BLOCKED_STATUS_CODE =
  "READONLY_EXPLANATION_BLOCKED";

export const DEMO_READONLY_EXPLANATION_SECURITY_BLOCKED_STATUS_CODE =
  "READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION";

export const DEMO_READONLY_EXPLANATION_API_ERROR_STATUS_CODE =
  "READONLY_EXPLANATION_API_ERROR";

export const DEMO_READONLY_EXPLANATION_SAFE_FLAGS: DemoReadOnlyExplanationSafetyFlags =
  {
    readOnly: true,
    demoOnly: true,
    isTradable: false,
    canExecute: false,
    isTradingPermission: false,
    isExecutionInstruction: false,
    allowedToCallEa: false,
    allowedToModifyRisk: false,
  };

export const DEMO_READONLY_EXPLANATION_REQUIRED_SAFETY_FIELDS = {
  read_only: true,
  demo_only: true,
  is_tradable: false,
  can_execute: false,
  is_trading_permission: false,
  is_execution_instruction: false,
  allowed_to_call_ea: false,
  allowed_to_modify_risk: false,
} as const;

export const DEMO_READONLY_EXPLANATION_ALLOWED_RESPONSE_FIELDS = [
  "passed",
  "status_code",
  "report_version",
  "report_type",
  "generated_at",
  "source_scope",
  "input_status_code",
  "input_passed",
  "explanation_scope",
  "overall_explanation",
  "status_explanation",
  "component_explanations",
  "blocker_explanations",
  "warning_explanations",
  "readiness_explanation",
  "next_allowed_stage_explanation",
  "next_blocked_stage_explanation",
  "user_safe_next_steps",
  "user_forbidden_actions",
  "unknowns",
  "safety_flags",
  "block_reasons",
  "warning_reasons",
  "read_only",
  "demo_only",
  "is_tradable",
  "can_execute",
  "is_trading_permission",
  "is_execution_instruction",
  "allowed_to_call_ea",
  "allowed_to_modify_risk",
  "notes",
] as const;

export const DEMO_READONLY_EXPLANATION_FORBIDDEN_FIELD_NAMES = [
  "raw_payload",
  "raw_account_snapshot",
  "raw_positions_order_history",
  "raw_market_symbol",
  "account_number",
  "login",
  "password",
  "credential",
  "token",
  "secret",
  "api_key",
  "key",
  "traceback",
  "stack_trace",
  "system_path",
  "order_id",
  "ticket",
  "execute_trade",
  "order_send",
  "order_close",
  "order_modify",
  "order_delete",
  "auto_trade",
  "can_trade",
  "allow_trade",
  "should_buy",
  "should_sell",
  "buy_now",
  "sell_now",
  "open_position",
  "close_position",
  "suggested_lot",
  "final_lot",
  "override_risk",
  "bypass_gate",
  "ea_command",
  "trade_signal",
  "trading_action",
] as const;

export const DEMO_READONLY_EXPLANATION_FORBIDDEN_UI_ADVICE_PHRASES = [
  "买入",
  "卖出",
  "开仓",
  "平仓",
  "建议手数",
  "可以交易",
  "允许交易",
  "自动下单",
  "自动交易",
  "执行交易",
  "下单指令",
  "风控放行",
  "绕过风控",
  "buy",
  "sell",
  "should buy",
  "should sell",
  "open position",
  "close position",
  "execute trade",
  "allow trade",
  "can trade",
  "suggested lot",
] as const;

export const DEMO_READONLY_EXPLANATION_FORBIDDEN_TEXT_MARKERS = [
  ...DEMO_READONLY_EXPLANATION_FORBIDDEN_FIELD_NAMES,
  ...DEMO_READONLY_EXPLANATION_FORBIDDEN_UI_ADVICE_PHRASES,
  "raw payload",
  "stack trace",
  ".env",
  "c:\\",
  "\\users\\",
  "/users/",
  "/home/",
] as const;

export const DEMO_READONLY_EXPLANATION_SAFE_NEXT_STEP_KEYWORDS = [
  "readonly",
  "read-only",
  "demo",
  "diagnostic",
  "diagnostics",
  "explanation",
  "review",
  "safety",
  "refresh",
  "blocked",
  "warning",
  "check",
  "display",
  "只读",
  "解释",
  "诊断",
  "刷新",
  "查看",
  "阻断",
  "警告",
  "安全",
  "检查",
  "展示",
] as const;
