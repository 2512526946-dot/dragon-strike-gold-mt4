import type { SafetyFlagsViewModel } from "./types";

export const DEMO_DIAGNOSTICS_ENDPOINT = "/api/demo-readonly/diagnostics";

export const SECURITY_BLOCKED_STATUS_CODE = "SECURITY_BLOCKED";

export const SECURITY_BLOCKED_MESSAGE =
  "SECURITY BLOCKED - INVALID DIAGNOSTICS STATE";

export const SAFE_FLAGS: SafetyFlagsViewModel = {
  read_only: true,
  demo_only: true,
  is_tradable: false,
  can_execute: false,
  is_trading_permission: false,
  is_execution_instruction: false,
  allowed_to_call_ea: false,
  allowed_to_modify_risk: false,
};

export const ALLOWED_RESPONSE_FIELDS = [
  "api_version",
  "endpoint",
  "generated_at",
  "passed",
  "status_code",
  "source_scope",
  "validation_stage",
  "fixture_source",
  "source_mode",
  "source_status",
  "source_config_status_code",
  "source_config_passed",
  "reader_status",
  "reader_passed",
  "reader_status_code",
  "mt4_demo_readonly_file_bridge_enabled",
  "data_quality_notes",
  "bundle_validation_status",
  "component_statuses",
  "block_reasons",
  "warning_reasons",
  "readiness_notes",
  "next_allowed_stage",
  "next_blocked_stage",
  "read_only",
  "demo_only",
  "is_tradable",
  "can_execute",
  "is_trading_permission",
  "is_execution_instruction",
  "allowed_to_call_ea",
  "allowed_to_modify_risk",
] as const;

export const FORBIDDEN_FIELDS = [
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

export const FORBIDDEN_TEXT_MARKERS = [
  ...FORBIDDEN_FIELDS,
  "stack trace",
  ".env",
  "c:\\",
  "\\users\\",
  "/users/",
] as const;
