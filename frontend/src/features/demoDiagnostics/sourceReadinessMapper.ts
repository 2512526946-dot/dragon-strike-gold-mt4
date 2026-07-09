export type SourceReadinessLevel =
  | "safe_ready"
  | "safe_warning"
  | "blocked"
  | "unsafe_response"
  | "unknown";

export type SourceReadinessUiModel = {
  displaySourceModeLabel: string;
  displaySourceStatusLabel: string;
  displaySourceConfigLabel: string;
  displayReaderStatusLabel: string;
  displayReaderResultLabel: string;
  displayBridgeEnabledLabel: string;
  readinessLevel: SourceReadinessLevel;
  readinessBadge: string;
  safeBlockReasons: string[];
  safeWarningReasons: string[];
  safeDataQualityNotes: string[];
  showAsReadOnly: boolean;
  showAsDemoOnly: boolean;
  showAsTradable: false;
  showAsExecutable: false;
  isUnsafeResponse: boolean;
  unsafeReasons: string[];
  canShowSourceReadinessCard: boolean;
};

type UnknownRecord = Record<string, unknown>;

const UNSAFE_REASON = "Unsafe source readiness response blocked.";

const FORBIDDEN_FIELD_NAMES = [
  "bridge_dir",
  "base_dir",
  "candidate_path",
  "raw_payload",
  "system_path",
  "traceback",
  "stack_trace",
  "password",
  "credential",
  "token",
  "secret",
  "api_key",
  "login",
  "account_number",
  "ticket",
  "order_id",
  "suggested_lot",
  "final_lot",
  "buy_now",
  "sell_now",
  "should_buy",
  "should_sell",
  "open_position",
  "close_position",
  "order_send",
  "order_close",
  "order_modify",
  "order_delete",
  "ea_command",
  "trade_signal",
  "trading_action",
  "override_risk",
  "bypass_gate",
  "execute_trade",
  "can_trade",
  "allow_trade",
] as const;

const FORBIDDEN_TEXT_MARKERS = [
  "c:\\users\\",
  "\\users\\",
  "/home/",
  ".py:",
  "traceback",
  "stack trace",
  "password",
  "credential",
  "token",
  "secret",
  "api_key",
  "account_number",
  "login",
  "ticket",
  "order_id",
  "suggested_lot",
  "final_lot",
  "buy_now",
  "sell_now",
  "should_buy",
  "should_sell",
  "open_position",
  "close_position",
  "order_send",
  "order_close",
  "order_modify",
  "order_delete",
  "ordersend",
  "orderclose",
  "ordermodify",
  "orderdelete",
  "ea command",
  "tradeplan",
  "executionplan",
  "trade_signal",
  "trading_action",
] as const;

export function mapDemoDiagnosticsSourceReadinessToUiModel(
  response: unknown,
): SourceReadinessUiModel {
  if (collectUnsafeContent(response).length > 0) {
    return unsafeSourceReadinessModel();
  }

  if (!isRecord(response)) {
    return unsafeSourceReadinessModel();
  }

  if (collectSafetyFlagIssues(response).length > 0) {
    return unsafeSourceReadinessModel();
  }

  const sourceMode = readString(response.source_mode, "unknown");
  const sourceStatus = readString(response.source_status, "unknown");
  const sourceConfigPassed = response.source_config_passed === true;
  const readerStatus = readString(response.reader_status, "unknown");
  const readerPassed = response.reader_passed === true;
  const bridgeEnabled =
    response.mt4_demo_readonly_file_bridge_enabled === true;
  const safeBlockReasons = readSafeStringArray(response.block_reasons);
  const safeWarningReasons = readSafeStringArray(response.warning_reasons);
  const safeDataQualityNotes = readSafeStringArray(response.data_quality_notes);
  const readinessLevel = resolveReadinessLevel({
    sourceStatus,
    sourceConfigPassed,
    readerStatus,
    safeBlockReasons,
    safeWarningReasons,
  });

  return {
    displaySourceModeLabel: sourceModeLabel(sourceMode),
    displaySourceStatusLabel: sourceStatusLabel(sourceStatus),
    displaySourceConfigLabel: sourceConfigPassed
      ? "source config 校验通过，仅表示配置安全通过"
      : "source config 未通过或不可用",
    displayReaderStatusLabel: readerStatusLabel(readerStatus),
    displayReaderResultLabel: readerPassed
      ? "reader 安全摘要通过，不代表交易许可"
      : "reader 未通过或未调用，不代表交易许可",
    displayBridgeEnabledLabel: bridgeEnabled
      ? "MT4 Demo 只读文件桥已启用"
      : "MT4 Demo 文件桥未启用",
    readinessLevel,
    readinessBadge: readinessBadge(readinessLevel),
    safeBlockReasons,
    safeWarningReasons,
    safeDataQualityNotes,
    showAsReadOnly: true,
    showAsDemoOnly: true,
    showAsTradable: false,
    showAsExecutable: false,
    isUnsafeResponse: false,
    unsafeReasons: [],
    canShowSourceReadinessCard: true,
  };
}

export function unsafeSourceReadinessModel(): SourceReadinessUiModel {
  return {
    displaySourceModeLabel: "安全响应被阻断",
    displaySourceStatusLabel: "source/readiness 响应不安全",
    displaySourceConfigLabel: "source config 未展示",
    displayReaderStatusLabel: "reader 状态未展示",
    displayReaderResultLabel: "reader 结果未展示",
    displayBridgeEnabledLabel: "MT4 Demo 文件桥状态未展示",
    readinessLevel: "unsafe_response",
    readinessBadge: "unsafe response blocked",
    safeBlockReasons: [UNSAFE_REASON],
    safeWarningReasons: [],
    safeDataQualityNotes: [],
    showAsReadOnly: false,
    showAsDemoOnly: false,
    showAsTradable: false,
    showAsExecutable: false,
    isUnsafeResponse: true,
    unsafeReasons: [UNSAFE_REASON],
    canShowSourceReadinessCard: false,
  };
}

function resolveReadinessLevel(input: {
  sourceStatus: string;
  sourceConfigPassed: boolean;
  readerStatus: string;
  safeBlockReasons: string[];
  safeWarningReasons: string[];
}): SourceReadinessLevel {
  const sourceStatus = input.sourceStatus.toLowerCase();
  const readerStatus = input.readerStatus.toLowerCase();

  if (
    input.safeBlockReasons.length > 0 ||
    !input.sourceConfigPassed ||
    sourceStatus.includes("blocked") ||
    readerStatus === "blocked" ||
    readerStatus === "error_safe"
  ) {
    return "blocked";
  }

  if (
    input.safeWarningReasons.length > 0 ||
    sourceStatus.includes("warning")
  ) {
    return "safe_warning";
  }

  if (
    sourceStatus === "ready" ||
    readerStatus === "ready" ||
    readerStatus === "not_called"
  ) {
    return "safe_ready";
  }

  return "unknown";
}

function sourceModeLabel(value: string): string {
  if (value === "docs_fixture_only") {
    return "文档示例 / 安全 fixture";
  }

  if (value === "mt4_demo_readonly_file_bridge_enabled") {
    return "MT4 Demo 只读文件桥";
  }

  return "未知只读数据源";
}

function sourceStatusLabel(value: string): string {
  const normalized = value.toLowerCase();

  if (normalized === "ready") {
    return "数据源状态：只读 ready";
  }
  if (normalized.includes("blocked")) {
    return "数据源状态：安全阻断";
  }
  if (normalized.includes("warning")) {
    return "数据源状态：安全警告";
  }

  return "数据源状态：未知";
}

function readerStatusLabel(value: string): string {
  if (value === "not_called") {
    return "未调用 reader";
  }
  if (value === "ready") {
    return "reader 已返回安全摘要";
  }
  if (value === "blocked") {
    return "reader 安全阻断";
  }
  if (value === "error_safe") {
    return "reader 异常，已安全降级";
  }

  return "reader 状态未知";
}

function readinessBadge(value: SourceReadinessLevel): string {
  if (value === "safe_ready") {
    return "只读 ready";
  }
  if (value === "safe_warning") {
    return "只读 warning";
  }
  if (value === "blocked") {
    return "只读 blocked";
  }
  if (value === "unsafe_response") {
    return "unsafe response blocked";
  }

  return "只读 unknown";
}

function collectSafetyFlagIssues(record: UnknownRecord): string[] {
  const expectedValues = {
    read_only: true,
    demo_only: true,
    is_tradable: false,
    can_execute: false,
    is_trading_permission: false,
    is_execution_instruction: false,
    allowed_to_call_ea: false,
    allowed_to_modify_risk: false,
  };

  return Object.entries(expectedValues).flatMap(
    ([fieldName, expectedValue]) => {
      if (!(fieldName in record)) {
        return ["Unsafe safety flag state."];
      }
      return record[fieldName] === expectedValue
        ? []
        : ["Unsafe safety flag state."];
    },
  );
}

function collectUnsafeContent(value: unknown): string[] {
  const reasons: string[] = [];
  collectUnsafeContentRecursive(value, reasons);
  return reasons;
}

function collectUnsafeContentRecursive(
  value: unknown,
  reasons: string[],
): void {
  if (typeof value === "string") {
    if (containsUnsafeText(value)) {
      reasons.push(UNSAFE_REASON);
    }
    return;
  }

  if (Array.isArray(value)) {
    value.forEach((item) => collectUnsafeContentRecursive(item, reasons));
    return;
  }

  if (!isRecord(value)) {
    return;
  }

  Object.entries(value).forEach(([fieldName, childValue]) => {
    if (isForbiddenFieldName(fieldName)) {
      reasons.push(UNSAFE_REASON);
      return;
    }
    collectUnsafeContentRecursive(childValue, reasons);
  });
}

function isForbiddenFieldName(value: string): boolean {
  const normalized = value.toLowerCase();
  return FORBIDDEN_FIELD_NAMES.some((fieldName) => fieldName === normalized);
}

function containsUnsafeText(value: string): boolean {
  const normalized = value.toLowerCase();
  return FORBIDDEN_TEXT_MARKERS.some((marker) =>
    normalized.includes(marker.toLowerCase()),
  );
}

function readString(value: unknown, fallback: string): string {
  return typeof value === "string" && !containsUnsafeText(value)
    ? value
    : fallback;
}

function readSafeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) =>
    typeof item === "string" && !containsUnsafeText(item) ? [item] : [],
  );
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
