export type DemoDiagnosticsUiState =
  | "loading"
  | "success"
  | "blocked"
  | "security_blocked"
  | "error";

export type DemoDiagnosticsStatus =
  | "passed"
  | "blocked"
  | "warning"
  | "unknown";

export type SafetyFlagsViewModel = {
  read_only: true;
  demo_only: true;
  is_tradable: false;
  can_execute: false;
  is_trading_permission: false;
  is_execution_instruction: false;
  allowed_to_call_ea: false;
  allowed_to_modify_risk: false;
};

export type DemoDiagnosticsApiResponse = {
  api_version?: unknown;
  endpoint?: unknown;
  generated_at?: unknown;
  passed?: unknown;
  status_code?: unknown;
  source_scope?: unknown;
  validation_stage?: unknown;
  fixture_source?: unknown;
  bundle_validation_status?: unknown;
  component_statuses?: unknown;
  block_reasons?: unknown;
  warning_reasons?: unknown;
  readiness_notes?: unknown;
  next_allowed_stage?: unknown;
  next_blocked_stage?: unknown;
  read_only?: unknown;
  demo_only?: unknown;
  is_tradable?: unknown;
  can_execute?: unknown;
  is_trading_permission?: unknown;
  is_execution_instruction?: unknown;
  allowed_to_call_ea?: unknown;
  allowed_to_modify_risk?: unknown;
};

export type ComponentStatusViewModel = SafetyFlagsViewModel & {
  component_name: string;
  status: DemoDiagnosticsStatus;
  status_code: string;
  block_reasons: string[];
  warning_reasons: string[];
  safe_count: number;
  safe_summary: string;
};

export type BundleStatusViewModel = SafetyFlagsViewModel & {
  passed: boolean;
  status: DemoDiagnosticsStatus;
  status_code: string;
  block_reasons: string[];
  warning_reasons: string[];
  block_summary: string;
  warning_summary: string;
};

export type ReadinessViewModel = {
  readiness_notes: string[];
  next_allowed_stage: string[];
  next_blocked_stage: string[];
};

export type DemoDiagnosticsViewModel = SafetyFlagsViewModel & {
  api_version: string;
  endpoint: "/api/demo-readonly/diagnostics";
  generated_at: string;
  passed: boolean;
  status_code: string;
  source_scope: string;
  validation_stage: string;
  fixture_source: string;
  bundle: BundleStatusViewModel;
  components: ComponentStatusViewModel[];
  block_reasons: string[];
  warning_reasons: string[];
  readiness: ReadinessViewModel;
  ui_state: DemoDiagnosticsUiState;
};
