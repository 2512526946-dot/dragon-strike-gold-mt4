import {
  DEMO_DIAGNOSTICS_ENDPOINT,
  FORBIDDEN_FIELDS,
  FORBIDDEN_TEXT_MARKERS,
  SAFE_FLAGS,
  SECURITY_BLOCKED_STATUS_CODE,
} from "./contracts";
import { unsafeSourceReadinessModel } from "./sourceReadinessMapper";
import type {
  BundleStatusViewModel,
  ComponentStatusViewModel,
  DemoDiagnosticsStatus,
  DemoDiagnosticsViewModel,
  ReadinessViewModel,
} from "./types";

type UnknownRecord = Record<string, unknown>;

const DEFAULT_GENERATED_AT = "unavailable";
const DEFAULT_SOURCE_SCOPE = "docs_fixture_only";
const DEFAULT_VALIDATION_STAGE = "unknown";
const DEFAULT_FIXTURE_SOURCE = "unknown";

export function mapDemoDiagnosticsApiToViewModel(
  response: unknown,
): DemoDiagnosticsViewModel {
  const forbiddenReasons = collectForbiddenContentReasons(response);
  if (forbiddenReasons.length > 0) {
    return securityBlockedViewModel(forbiddenReasons);
  }

  if (!isRecord(response)) {
    return securityBlockedViewModel(["Diagnostics response must be an object."]);
  }

  const safetyReasons = validateTopLevelSafetyFlags(response);
  if (safetyReasons.length > 0) {
    return securityBlockedViewModel(safetyReasons);
  }

  const passed = response.passed === true;
  const blockReasons = readStringArray(response.block_reasons);
  const warningReasons = readStringArray(response.warning_reasons);

  return {
    ...SAFE_FLAGS,
    api_version: readString(response.api_version, "unknown"),
    endpoint: DEMO_DIAGNOSTICS_ENDPOINT,
    generated_at: readString(response.generated_at, DEFAULT_GENERATED_AT),
    passed,
    status_code: readString(response.status_code, "STATUS_UNAVAILABLE"),
    source_scope: readString(response.source_scope, DEFAULT_SOURCE_SCOPE),
    validation_stage: readString(
      response.validation_stage,
      DEFAULT_VALIDATION_STAGE,
    ),
    fixture_source: readString(response.fixture_source, DEFAULT_FIXTURE_SOURCE),
    bundle: mapBundleStatus(response.bundle_validation_status),
    components: mapComponentStatuses(response.component_statuses),
    block_reasons: blockReasons,
    warning_reasons: warningReasons,
    readiness: mapReadiness(response),
    source_readiness: unsafeSourceReadinessModel(),
    ui_state: passed ? "success" : "blocked",
  };
}

export function securityBlockedViewModel(
  reasons: string[],
): DemoDiagnosticsViewModel {
  return {
    ...SAFE_FLAGS,
    api_version: "unknown",
    endpoint: DEMO_DIAGNOSTICS_ENDPOINT,
    generated_at: DEFAULT_GENERATED_AT,
    passed: false,
    status_code: SECURITY_BLOCKED_STATUS_CODE,
    source_scope: DEFAULT_SOURCE_SCOPE,
    validation_stage: DEFAULT_VALIDATION_STAGE,
    fixture_source: DEFAULT_FIXTURE_SOURCE,
    bundle: emptyBundleStatus(),
    components: [],
    block_reasons: reasons.length > 0 ? reasons : ["Unsafe diagnostics state."],
    warning_reasons: [],
    readiness: {
      readiness_notes: [],
      next_allowed_stage: [],
      next_blocked_stage: ["security_blocked"],
    },
    source_readiness: unsafeSourceReadinessModel(),
    ui_state: "security_blocked",
  };
}

function mapBundleStatus(value: unknown): BundleStatusViewModel {
  const base = mapStatusObject(value, "bundle_validation_status");
  return {
    ...SAFE_FLAGS,
    passed: base.passed,
    status: base.status,
    status_code: base.status_code,
    block_reasons: base.block_reasons,
    warning_reasons: base.warning_reasons,
    block_summary: summarizeList(base.block_reasons, "无阻断原因"),
    warning_summary: summarizeList(base.warning_reasons, "无警告原因"),
  };
}

function mapComponentStatuses(value: unknown): ComponentStatusViewModel[] {
  if (!isRecord(value)) {
    return [];
  }

  return Object.entries(value).map(([componentName, componentValue]) => {
    const base = mapStatusObject(componentValue, componentName);
    const safeCount =
      base.block_reasons.length + base.warning_reasons.length === 0 ? 1 : 0;

    return {
      ...SAFE_FLAGS,
      component_name: componentName,
      status: base.status,
      status_code: base.status_code,
      block_reasons: base.block_reasons,
      warning_reasons: base.warning_reasons,
      safe_count: safeCount,
      safe_summary: base.passed
        ? "安全摘要可展示"
        : summarizeList(base.block_reasons, "组件摘要被阻断"),
    };
  });
}

function mapReadiness(response: UnknownRecord): ReadinessViewModel {
  return {
    readiness_notes: readStringArray(response.readiness_notes),
    next_allowed_stage: readStringArray(response.next_allowed_stage),
    next_blocked_stage: readStringArray(response.next_blocked_stage),
  };
}

function emptyBundleStatus(): BundleStatusViewModel {
  return {
    ...SAFE_FLAGS,
    passed: false,
    status: "blocked",
    status_code: SECURITY_BLOCKED_STATUS_CODE,
    block_reasons: ["Unsafe diagnostics state."],
    warning_reasons: [],
    block_summary: "Unsafe diagnostics state.",
    warning_summary: "无警告原因",
  };
}

function mapStatusObject(value: unknown, label: string) {
  if (!isRecord(value)) {
    return {
      passed: false,
      status: "unknown" as DemoDiagnosticsStatus,
      status_code: "STATUS_UNAVAILABLE",
      block_reasons: [`${label} summary unavailable.`],
      warning_reasons: [] as string[],
    };
  }

  const safetyReasons = validateNestedSafetyFlags(value, label);
  const passed = safetyReasons.length === 0 && value.passed === true;
  const blockReasons = [
    ...readStringArray(value.block_reasons),
    ...safetyReasons,
  ];
  const warningReasons = readStringArray(value.warning_reasons);

  return {
    passed,
    status: statusFrom(passed, blockReasons, warningReasons),
    status_code: readString(value.status_code, "STATUS_UNAVAILABLE"),
    block_reasons: blockReasons,
    warning_reasons: warningReasons,
  };
}

function statusFrom(
  passed: boolean,
  blockReasons: string[],
  warningReasons: string[],
): DemoDiagnosticsStatus {
  if (passed && warningReasons.length > 0) {
    return "warning";
  }
  if (passed) {
    return "passed";
  }
  if (blockReasons.length > 0) {
    return "blocked";
  }
  return "unknown";
}

function validateTopLevelSafetyFlags(record: UnknownRecord): string[] {
  const expectedSafetyValues = {
    read_only: true,
    demo_only: true,
    is_tradable: false,
    can_execute: false,
    is_trading_permission: false,
    is_execution_instruction: false,
    allowed_to_call_ea: false,
    allowed_to_modify_risk: false,
  };

  return Object.entries(expectedSafetyValues).flatMap(
    ([fieldName, expectedValue]) => {
      if (!(fieldName in record)) {
        return [`Missing safety field: ${fieldName}.`];
      }
      return record[fieldName] === expectedValue
        ? []
        : [`Unsafe safety field value: ${fieldName}.`];
    },
  );
}

function validateNestedSafetyFlags(
  record: UnknownRecord,
  label: string,
): string[] {
  const expectedSafetyValues = {
    read_only: true,
    demo_only: true,
    is_tradable: false,
    can_execute: false,
  };

  return Object.entries(expectedSafetyValues).flatMap(
    ([fieldName, expectedValue]) => {
      if (!(fieldName in record)) {
        return [];
      }
      return record[fieldName] === expectedValue
        ? []
        : [`Unsafe ${label} safety field value: ${fieldName}.`];
    },
  );
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
      reasons.push(`Unsafe text removed at ${path}.`);
    }
    return;
  }

  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      collectForbiddenContent(item, `${path}[${index}]`, reasons);
    });
    return;
  }

  if (!isRecord(value)) {
    return;
  }

  Object.entries(value).forEach(([keyName, childValue]) => {
    if (isForbiddenFieldName(keyName)) {
      reasons.push(`Forbidden field removed: ${keyName}.`);
      return;
    }
    collectForbiddenContent(childValue, `${path}.${keyName}`, reasons);
  });
}

function isForbiddenFieldName(value: string): boolean {
  const normalized = value.toLowerCase();
  return FORBIDDEN_FIELDS.some((fieldName) => normalized === fieldName);
}

function containsForbiddenText(value: string): boolean {
  const normalized = value.toLowerCase();
  return FORBIDDEN_TEXT_MARKERS.some((marker) =>
    normalized.includes(marker.toLowerCase()),
  );
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readString(value: unknown, fallback: string): string {
  return typeof value === "string" && !containsForbiddenText(value)
    ? value
    : fallback;
}

function readStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) =>
    typeof item === "string" && !containsForbiddenText(item) ? [item] : [],
  );
}

function summarizeList(values: string[], emptyText: string): string {
  return values.length > 0 ? values.join("；") : emptyText;
}
