import {
  DEMO_READONLY_EXPLANATION_ALLOWED_STATUS_CODES,
  DEMO_READONLY_EXPLANATION_API_ERROR_STATUS_CODE,
  DEMO_READONLY_EXPLANATION_BLOCKED_STATUS_CODE,
  DEMO_READONLY_EXPLANATION_FORBIDDEN_FIELD_NAMES,
  DEMO_READONLY_EXPLANATION_FORBIDDEN_TEXT_MARKERS,
  DEMO_READONLY_EXPLANATION_REQUIRED_SAFETY_FIELDS,
  DEMO_READONLY_EXPLANATION_SAFE_FLAGS,
  DEMO_READONLY_EXPLANATION_SAFE_NEXT_STEP_KEYWORDS,
  DEMO_READONLY_EXPLANATION_SECURITY_BLOCKED_STATUS_CODE,
} from "./contracts";
import type {
  DemoReadOnlyExplanationComponentStatus,
  DemoReadOnlyExplanationComponentViewModel,
  DemoReadOnlyExplanationUiSafetyStatus,
  DemoReadOnlyExplanationViewModel,
} from "./types";

type UnknownRecord = Record<string, unknown>;

const DEFAULT_REPORT_VERSION = "unknown";
const DEFAULT_REPORT_TYPE = "read_only_explanation_report";
const DEFAULT_SOURCE_SCOPE = "demo_readonly_explanation_api";
const DEFAULT_EXPLANATION_SCOPE = "demo_readonly_diagnostics_summary_only";
const DEFAULT_UI_SAFETY_MESSAGE =
  "Read-only demo explanation only. This is not trading permission and not an execution instruction.";

export function mapDemoReadOnlyExplanationApiToViewModel(
  apiResponse: unknown,
): DemoReadOnlyExplanationViewModel {
  const forbiddenReasons = collectForbiddenContentReasons(apiResponse);
  if (forbiddenReasons.length > 0) {
    return securityBlockedViewModel(forbiddenReasons);
  }

  if (!isRecord(apiResponse)) {
    return blockedViewModel(["Explanation response must be an object."]);
  }

  const missingReasons = requiredFieldReasons(apiResponse);
  if (missingReasons.length > 0) {
    return blockedViewModel(missingReasons);
  }

  const safetyReasons = validateSafetyFlags(apiResponse);
  if (safetyReasons.length > 0) {
    return securityBlockedViewModel(safetyReasons);
  }

  const statusCode = readString(apiResponse.status_code, "");
  if (!isAllowedStatusCode(statusCode)) {
    return blockedViewModel(["Explanation status_code is not allowed."]);
  }

  const passed = apiResponse.passed === true;
  const blockReasons = readStringArray(apiResponse.block_reasons);
  const warningReasons = readStringArray(apiResponse.warning_reasons);

  return {
    ...DEMO_READONLY_EXPLANATION_SAFE_FLAGS,
    passed,
    statusCode,
    reportVersion: readString(
      apiResponse.report_version,
      DEFAULT_REPORT_VERSION,
    ),
    reportType: readString(apiResponse.report_type, DEFAULT_REPORT_TYPE),
    generatedAt: readNullableString(apiResponse.generated_at),
    sourceScope: readString(apiResponse.source_scope, DEFAULT_SOURCE_SCOPE),
    inputStatusCode: readString(apiResponse.input_status_code, "unknown"),
    inputPassed: apiResponse.input_passed === true,
    explanationScope: readString(
      apiResponse.explanation_scope,
      DEFAULT_EXPLANATION_SCOPE,
    ),
    overallExplanation: readString(apiResponse.overall_explanation, ""),
    statusExplanation: readString(apiResponse.status_explanation, ""),
    componentExplanations: mapComponentExplanations(
      apiResponse.component_explanations,
    ),
    blockerExplanations: readStringArray(apiResponse.blocker_explanations),
    warningExplanations: readStringArray(apiResponse.warning_explanations),
    readinessExplanation: readStringArray(apiResponse.readiness_explanation),
    nextAllowedStageExplanation: readStringArray(
      apiResponse.next_allowed_stage_explanation,
    ),
    nextBlockedStageExplanation: readStringArray(
      apiResponse.next_blocked_stage_explanation,
    ),
    userSafeNextSteps: readSafeNextSteps(apiResponse.user_safe_next_steps),
    userForbiddenActions: readStringArray(apiResponse.user_forbidden_actions),
    unknowns: readStringArray(apiResponse.unknowns),
    safetyFlags: DEMO_READONLY_EXPLANATION_SAFE_FLAGS,
    blockReasons,
    warningReasons,
    notes: readStringArray(apiResponse.notes),
    uiSafetyStatus: passed ? "ready" : "blocked",
    uiSafetyMessage: DEFAULT_UI_SAFETY_MESSAGE,
  };
}

export function blockedViewModel(
  reasons: string[],
  uiSafetyStatus: DemoReadOnlyExplanationUiSafetyStatus = "blocked",
): DemoReadOnlyExplanationViewModel {
  return {
    ...DEMO_READONLY_EXPLANATION_SAFE_FLAGS,
    passed: false,
    statusCode:
      uiSafetyStatus === "api_error"
        ? DEMO_READONLY_EXPLANATION_API_ERROR_STATUS_CODE
        : DEMO_READONLY_EXPLANATION_BLOCKED_STATUS_CODE,
    reportVersion: DEFAULT_REPORT_VERSION,
    reportType: DEFAULT_REPORT_TYPE,
    generatedAt: null,
    sourceScope: DEFAULT_SOURCE_SCOPE,
    inputStatusCode: "unknown",
    inputPassed: false,
    explanationScope: DEFAULT_EXPLANATION_SCOPE,
    overallExplanation:
      "Read-only explanation is unavailable. No trading permission or execution instruction is provided.",
    statusExplanation:
      "The explanation response was blocked before display mapping.",
    componentExplanations: [],
    blockerExplanations: reasons.length > 0 ? reasons : ["Blocked."],
    warningExplanations: [],
    readinessExplanation: [],
    nextAllowedStageExplanation: [],
    nextBlockedStageExplanation: ["Read-only explanation display is blocked."],
    userSafeNextSteps: ["Review the read-only explanation safety status."],
    userForbiddenActions: [
      "Do not treat this blocked explanation as permission or instruction.",
    ],
    unknowns: [],
    safetyFlags: DEMO_READONLY_EXPLANATION_SAFE_FLAGS,
    blockReasons: reasons.length > 0 ? reasons : ["Blocked."],
    warningReasons: [],
    notes: [DEFAULT_UI_SAFETY_MESSAGE],
    uiSafetyStatus,
    uiSafetyMessage: DEFAULT_UI_SAFETY_MESSAGE,
  };
}

export function securityBlockedViewModel(
  reasons: string[],
): DemoReadOnlyExplanationViewModel {
  return {
    ...blockedViewModel(
      reasons.length > 0 ? reasons : ["Unsafe explanation content blocked."],
      "security_blocked",
    ),
    statusCode: DEMO_READONLY_EXPLANATION_SECURITY_BLOCKED_STATUS_CODE,
    uiSafetyStatus: "security_blocked",
  };
}

export function apiErrorViewModel(): DemoReadOnlyExplanationViewModel {
  return blockedViewModel(
    ["Read-only explanation API request failed safely."],
    "api_error",
  );
}

function mapComponentExplanations(
  value: unknown,
): DemoReadOnlyExplanationComponentViewModel[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    if (!isRecord(item)) {
      return [];
    }

    return [
      {
        componentName: readString(item.component_name, "unknown"),
        status: readComponentStatus(item.status),
        plainLanguageSummary: readString(item.plain_language_summary, ""),
        blockReasonsExplained: readStringArray(item.block_reasons_explained),
        warningReasonsExplained: readStringArray(
          item.warning_reasons_explained,
        ),
        userImpact: readString(item.user_impact, ""),
        safeNextStep: readSafeNextStep(item.safe_next_step),
        forbiddenInterpretation: readString(item.forbidden_interpretation, ""),
      },
    ];
  });
}

function requiredFieldReasons(record: UnknownRecord): string[] {
  const requiredFields = [
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
  ];

  return requiredFields.flatMap((fieldName) =>
    fieldName in record ? [] : [`Missing explanation field: ${fieldName}.`],
  );
}

function validateSafetyFlags(record: UnknownRecord): string[] {
  const topLevelReasons = Object.entries(
    DEMO_READONLY_EXPLANATION_REQUIRED_SAFETY_FIELDS,
  ).flatMap(([fieldName, expectedValue]) =>
    record[fieldName] === expectedValue
      ? []
      : [`Unsafe safety field value: ${fieldName}.`],
  );

  const safetyFlags = record.safety_flags;
  if (!isRecord(safetyFlags)) {
    return [...topLevelReasons, "Missing safety_flags object."];
  }

  const nestedReasons = Object.entries(
    DEMO_READONLY_EXPLANATION_REQUIRED_SAFETY_FIELDS,
  ).flatMap(([fieldName, expectedValue]) =>
    safetyFlags[fieldName] === expectedValue
      ? []
      : [`Unsafe safety_flags value: ${fieldName}.`],
  );

  return [...topLevelReasons, ...nestedReasons];
}

function collectForbiddenContentReasons(value: unknown): string[] {
  const reasons: string[] = [];
  collectForbiddenContent(value, "$", reasons);
  return reasons;
}

function collectForbiddenContent(
  value: unknown,
  path: string,
  reasons: string[],
): void {
  if (typeof value === "string") {
    if (containsForbiddenText(value)) {
      reasons.push(`Unsafe explanation text blocked at ${path}.`);
    }
    return;
  }

  if (Array.isArray(value)) {
    value.forEach((item, index) =>
      collectForbiddenContent(item, `${path}[${index}]`, reasons),
    );
    return;
  }

  if (!isRecord(value)) {
    return;
  }

  Object.entries(value).forEach(([keyName, childValue]) => {
    if (isForbiddenFieldName(keyName)) {
      reasons.push(`Forbidden explanation field blocked: ${keyName}.`);
      return;
    }
    collectForbiddenContent(childValue, `${path}.${keyName}`, reasons);
  });
}

function isForbiddenFieldName(value: string): boolean {
  const normalized = value.toLowerCase();
  return DEMO_READONLY_EXPLANATION_FORBIDDEN_FIELD_NAMES.some(
    (fieldName) => normalized === fieldName,
  );
}

function containsForbiddenText(value: string): boolean {
  const normalized = value.toLowerCase();
  return DEMO_READONLY_EXPLANATION_FORBIDDEN_TEXT_MARKERS.some((marker) =>
    normalized.includes(marker.toLowerCase()),
  );
}

function isAllowedStatusCode(value: string): boolean {
  return DEMO_READONLY_EXPLANATION_ALLOWED_STATUS_CODES.some(
    (statusCode) => statusCode === value,
  );
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readString(value: unknown, fallback: string): string {
  if (typeof value !== "string") {
    return fallback;
  }
  return containsForbiddenText(value) ? fallback : value;
}

function readNullableString(value: unknown): string | null {
  return typeof value === "string" && !containsForbiddenText(value)
    ? value
    : null;
}

function readStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) =>
    typeof item === "string" && !containsForbiddenText(item) ? [item] : [],
  );
}

function readSafeNextSteps(value: unknown): string[] {
  return readStringArray(value).filter(isSafeNextStepText);
}

function readSafeNextStep(value: unknown): string {
  const text = readString(value, "");
  return isSafeNextStepText(text) ? text : "";
}

function isSafeNextStepText(value: string): boolean {
  const normalized = value.toLowerCase();
  return DEMO_READONLY_EXPLANATION_SAFE_NEXT_STEP_KEYWORDS.some((keyword) =>
    normalized.includes(keyword.toLowerCase()),
  );
}

function readComponentStatus(
  value: unknown,
): DemoReadOnlyExplanationComponentStatus {
  return value === "passed" ||
    value === "blocked" ||
    value === "warning" ||
    value === "unknown"
    ? value
    : "unknown";
}
