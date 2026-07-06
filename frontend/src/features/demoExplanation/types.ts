export type DemoReadOnlyExplanationUiSafetyStatus =
  | "ready"
  | "blocked"
  | "api_error"
  | "security_blocked"
  | "empty"
  | "stale_or_unknown";

export type DemoReadOnlyExplanationComponentStatus =
  | "passed"
  | "blocked"
  | "warning"
  | "unknown";

export type DemoReadOnlyExplanationSafetyFlags = {
  readOnly: true;
  demoOnly: true;
  isTradable: false;
  canExecute: false;
  isTradingPermission: false;
  isExecutionInstruction: false;
  allowedToCallEa: false;
  allowedToModifyRisk: false;
};

export type DemoReadOnlyExplanationApiSafetyFlags = {
  read_only?: unknown;
  demo_only?: unknown;
  is_tradable?: unknown;
  can_execute?: unknown;
  is_trading_permission?: unknown;
  is_execution_instruction?: unknown;
  allowed_to_call_ea?: unknown;
  allowed_to_modify_risk?: unknown;
};

export type DemoReadOnlyExplanationApiComponent = {
  component_name?: unknown;
  status?: unknown;
  status_code?: unknown;
  plain_language_summary?: unknown;
  block_reasons_explained?: unknown;
  warning_reasons_explained?: unknown;
  user_impact?: unknown;
  safe_next_step?: unknown;
  forbidden_interpretation?: unknown;
};

export type DemoReadOnlyExplanationApiResponse =
  DemoReadOnlyExplanationApiSafetyFlags & {
    passed?: unknown;
    status_code?: unknown;
    report_version?: unknown;
    report_type?: unknown;
    generated_at?: unknown;
    source_scope?: unknown;
    input_status_code?: unknown;
    input_passed?: unknown;
    explanation_scope?: unknown;
    overall_explanation?: unknown;
    status_explanation?: unknown;
    component_explanations?: unknown;
    blocker_explanations?: unknown;
    warning_explanations?: unknown;
    readiness_explanation?: unknown;
    next_allowed_stage_explanation?: unknown;
    next_blocked_stage_explanation?: unknown;
    user_safe_next_steps?: unknown;
    user_forbidden_actions?: unknown;
    unknowns?: unknown;
    safety_flags?: unknown;
    block_reasons?: unknown;
    warning_reasons?: unknown;
    notes?: unknown;
  };

export type DemoReadOnlyExplanationComponentViewModel = {
  componentName: string;
  status: DemoReadOnlyExplanationComponentStatus;
  plainLanguageSummary: string;
  blockReasonsExplained: string[];
  warningReasonsExplained: string[];
  userImpact: string;
  safeNextStep: string;
  forbiddenInterpretation: string;
};

export type DemoReadOnlyExplanationViewModel =
  DemoReadOnlyExplanationSafetyFlags & {
    passed: boolean;
    statusCode: string;
    reportVersion: string;
    reportType: string;
    generatedAt: string | null;
    sourceScope: string;
    inputStatusCode: string;
    inputPassed: boolean;
    explanationScope: string;
    overallExplanation: string;
    statusExplanation: string;
    componentExplanations: DemoReadOnlyExplanationComponentViewModel[];
    blockerExplanations: string[];
    warningExplanations: string[];
    readinessExplanation: string[];
    nextAllowedStageExplanation: string[];
    nextBlockedStageExplanation: string[];
    userSafeNextSteps: string[];
    userForbiddenActions: string[];
    unknowns: string[];
    safetyFlags: DemoReadOnlyExplanationSafetyFlags;
    blockReasons: string[];
    warningReasons: string[];
    notes: string[];
    uiSafetyStatus: DemoReadOnlyExplanationUiSafetyStatus;
    uiSafetyMessage: string;
  };
