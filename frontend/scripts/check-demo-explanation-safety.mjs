import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, "..");
const srcRoot = path.join(frontendRoot, "src");
const featureRoot = path.join(srcRoot, "features", "demoExplanation");

const files = {
  packageJson: path.join(frontendRoot, "package.json"),
  types: path.join(featureRoot, "types.ts"),
  contracts: path.join(featureRoot, "contracts.ts"),
  mapper: path.join(featureRoot, "mapper.ts"),
  api: path.join(featureRoot, "api.ts"),
  index: path.join(featureRoot, "index.ts"),
  panel: path.join(
    featureRoot,
    "components",
    "DemoReadOnlyExplanationPanel.tsx",
  ),
  safetyBanner: path.join(
    featureRoot,
    "components",
    "ExplanationSafetyBanner.tsx",
  ),
  overallPanel: path.join(
    featureRoot,
    "components",
    "ExplanationOverallPanel.tsx",
  ),
  statusPanel: path.join(
    featureRoot,
    "components",
    "ExplanationStatusPanel.tsx",
  ),
  componentList: path.join(
    featureRoot,
    "components",
    "ExplanationComponentList.tsx",
  ),
  blockerList: path.join(
    featureRoot,
    "components",
    "ExplanationBlockerList.tsx",
  ),
  warningList: path.join(
    featureRoot,
    "components",
    "ExplanationWarningList.tsx",
  ),
  readinessPanel: path.join(
    featureRoot,
    "components",
    "ExplanationReadinessPanel.tsx",
  ),
  nextStagePanel: path.join(
    featureRoot,
    "components",
    "ExplanationNextStagePanel.tsx",
  ),
  safeNextStepsPanel: path.join(
    featureRoot,
    "components",
    "ExplanationSafeNextStepsPanel.tsx",
  ),
  forbiddenActionsPanel: path.join(
    featureRoot,
    "components",
    "ExplanationForbiddenActionsPanel.tsx",
  ),
  app: path.join(srcRoot, "App.tsx"),
  diagnosticsDashboard: path.join(
    srcRoot,
    "features",
    "demoDiagnostics",
    "components",
    "DemoReadOnlyDiagnosticsDashboard.tsx",
  ),
};

const failures = [];

function readSource(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function fail(message) {
  failures.push(message);
}

function assertFileExists(label, filePath) {
  if (!fs.existsSync(filePath)) {
    fail(`${label} file is missing: ${filePath}`);
  }
}

function listSourceFiles(rootDir) {
  return fs.readdirSync(rootDir, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      if (["dist", "node_modules"].includes(entry.name)) {
        return [];
      }
      return listSourceFiles(entryPath);
    }

    return /\.(ts|tsx|js|jsx|mjs)$/.test(entry.name) ? [entryPath] : [];
  });
}

function assertIncludes(label, source, expected) {
  if (!source.includes(expected)) {
    fail(`${label} must include ${JSON.stringify(expected)}.`);
  }
}

function assertNotIncludes(label, source, forbidden) {
  if (source.toLowerCase().includes(forbidden.toLowerCase())) {
    fail(`${label} must not include ${JSON.stringify(forbidden)}.`);
  }
}

function assertMatches(label, source, pattern, description) {
  if (!pattern.test(source)) {
    fail(`${label} must match ${description}.`);
  }
}

function assertNotMatches(label, source, pattern, description) {
  if (pattern.test(source)) {
    fail(`${label} must not match ${description}.`);
  }
}

Object.entries(files).forEach(([label, filePath]) =>
  assertFileExists(label, filePath),
);

if (failures.length === 0) {
  const packageSource = readSource(files.packageJson);
  const typesSource = readSource(files.types);
  const contractsSource = readSource(files.contracts);
  const mapperSource = readSource(files.mapper);
  const apiSource = readSource(files.api);
  const indexSource = readSource(files.index);
  const appSource = readSource(files.app);
  const diagnosticsDashboardSource = readSource(files.diagnosticsDashboard);
  const srcFiles = listSourceFiles(srcRoot);
  const componentFiles = [
    files.panel,
    files.safetyBanner,
    files.overallPanel,
    files.statusPanel,
    files.componentList,
    files.blockerList,
    files.warningList,
    files.readinessPanel,
    files.nextStagePanel,
    files.safeNextStepsPanel,
    files.forbiddenActionsPanel,
  ];
  const componentSource = componentFiles.map(readSource).join("\n");

  [
    '"test:demo-explanation-safety"',
    "check-demo-explanation-safety.mjs",
    '"test:demo-diagnostics-safety"',
    "check-demo-diagnostics-safety.mjs",
    '"test"',
    "test:demo-diagnostics-safety",
  ].forEach((expected) =>
    assertIncludes("package.json", packageSource, expected),
  );
  [
    '"vitest"',
    '"jest"',
    '"@testing-library/react"',
    '"@testing-library/jest-dom"',
    '"playwright"',
    '"cypress"',
  ].forEach((forbidden) =>
    assertNotIncludes("package.json", packageSource, forbidden),
  );

  [
    "DemoReadOnlyExplanationApiResponse",
    "DemoReadOnlyExplanationViewModel",
    "DemoReadOnlyExplanationComponentViewModel",
    "DemoReadOnlyExplanationUiSafetyStatus",
    "DemoReadOnlyExplanationSafetyFlags",
    "readOnly: true",
    "demoOnly: true",
    "isTradable: false",
    "canExecute: false",
    "isTradingPermission: false",
    "isExecutionInstruction: false",
    "allowedToCallEa: false",
    "allowedToModifyRisk: false",
  ].forEach((expected) => assertIncludes("types.ts", typesSource, expected));

  [
    "DEMO_READONLY_EXPLANATION_ENDPOINT",
    "/api/demo-readonly/explanation",
    "DEMO_READONLY_EXPLANATION_ALLOWED_METHODS",
    "GET",
    "READONLY_EXPLANATION_READY",
    "READONLY_EXPLANATION_BLOCKED",
    "READONLY_EXPLANATION_INPUT_INVALID",
    "READONLY_EXPLANATION_SAFETY_FIELD_VIOLATION",
    "READONLY_EXPLANATION_SOURCE_ERROR",
    "READONLY_EXPLANATION_API_ERROR",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
    "DEMO_READONLY_EXPLANATION_FORBIDDEN_FIELD_NAMES",
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
    "traceback",
    "stack_trace",
    "system_path",
    "suggested_lot",
    "final_lot",
    "ea_command",
    "trade_signal",
    "trading_action",
    "DEMO_READONLY_EXPLANATION_FORBIDDEN_UI_ADVICE_PHRASES",
    "买入",
    "卖出",
    "开仓",
    "平仓",
    "建议手数",
    "可以交易",
    "允许交易",
    "自动下单",
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
  ].forEach((expected) =>
    assertIncludes("contracts.ts", contractsSource, expected),
  );

  [
    "mapDemoReadOnlyExplanationApiToViewModel",
    "collectForbiddenContentReasons",
    "collectForbiddenContent",
    "validateSafetyFlags",
    "requiredFieldReasons",
    "securityBlockedViewModel",
    "blockedViewModel",
    "apiErrorViewModel",
    "DEMO_READONLY_EXPLANATION_SAFE_FLAGS",
    "DEMO_READONLY_EXPLANATION_ALLOWED_STATUS_CODES",
    "DEMO_READONLY_EXPLANATION_REQUIRED_SAFETY_FIELDS",
    "DEMO_READONLY_EXPLANATION_FORBIDDEN_FIELD_NAMES",
    "DEMO_READONLY_EXPLANATION_FORBIDDEN_TEXT_MARKERS",
    "uiSafetyStatus: passed ? \"ready\" : \"blocked\"",
    "uiSafetyStatus: \"security_blocked\"",
    "uiSafetyStatus === \"api_error\"",
    "apiResponse.passed === true",
    "next_allowed_stage_explanation",
    "user_safe_next_steps",
    "readSafeNextSteps",
    "isSafeNextStepText",
  ].forEach((expected) => assertIncludes("mapper.ts", mapperSource, expected));

  [
    "...apiResponse",
    "Object.assign",
    "localStorage",
    "sessionStorage",
    "setInterval",
    "setTimeout",
    "WebSocket",
    "EventSource",
  ].forEach((forbidden) => assertNotIncludes("mapper.ts", mapperSource, forbidden));

  [
    "fetchDemoReadOnlyExplanation",
    "apiGet",
    "DEMO_READONLY_EXPLANATION_ENDPOINT",
    "mapDemoReadOnlyExplanationApiToViewModel",
    "apiErrorViewModel",
  ].forEach((expected) => assertIncludes("api.ts", apiSource, expected));
  [
    "fetch(",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "WebSocket",
    "EventSource",
    "setInterval",
    "setTimeout",
    "localStorage",
    "sessionStorage",
  ].forEach((forbidden) => assertNotIncludes("api.ts", apiSource, forbidden));

  [
    "fetchDemoReadOnlyExplanation",
    "mapDemoReadOnlyExplanationApiToViewModel",
    "DemoReadOnlyExplanationViewModel",
    "DemoReadOnlyExplanationPanel",
    "ExplanationSafetyBanner",
    "ExplanationOverallPanel",
    "ExplanationStatusPanel",
    "ExplanationComponentList",
    "ExplanationBlockerList",
    "ExplanationWarningList",
    "ExplanationReadinessPanel",
    "ExplanationNextStagePanel",
    "ExplanationSafeNextStepsPanel",
    "ExplanationForbiddenActionsPanel",
  ].forEach((expected) => assertIncludes("index.ts", indexSource, expected));
  [
    "fetch(",
    "apiGet(",
    "axios",
    "XMLHttpRequest",
    "useEffect",
    "setInterval",
    "setTimeout",
    "WebSocket",
    "EventSource",
    "localStorage",
    "sessionStorage",
    "window.location",
    "<button",
    "<form",
    "onSubmit",
    "submit",
    "raw_payload",
    "suggested_lot",
    "final_lot",
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
    "ea_command",
    "trade_signal",
    "trading_action",
  ].forEach((forbidden) => assertNotIncludes("index.ts", indexSource, forbidden));

  [
    "DemoReadOnlyExplanationPanel",
    "DemoReadOnlyExplanationPanelProps",
    "viewModel: DemoReadOnlyExplanationViewModel",
    "ExplanationSafetyBanner",
    "ExplanationOverallPanel",
    "ExplanationStatusPanel",
    "ExplanationComponentList",
    "ExplanationBlockerList",
    "ExplanationWarningList",
    "ExplanationReadinessPanel",
    "ExplanationNextStagePanel",
    "ExplanationSafeNextStepsPanel",
    "ExplanationForbiddenActionsPanel",
    "ready",
    "blocked",
    "api_error",
    "security_blocked",
    "empty",
    "stale_or_unknown",
  ].forEach((expected) =>
    assertIncludes("component files", componentSource, expected),
  );
  [
    /type\s+DemoReadOnlyExplanationPanelProps\s*=\s*{\s*viewModel:\s*DemoReadOnlyExplanationViewModel;\s*}/s,
    /function\s+DemoReadOnlyExplanationPanel\s*\(\s*{\s*viewModel\s*,?\s*}\s*:\s*DemoReadOnlyExplanationPanelProps\s*\)/s,
  ].forEach((pattern) =>
    assertMatches(
      "component files",
      componentSource,
      pattern,
      `safe ViewModel-only props pattern ${pattern}`,
    ),
  );

  [
    "只读解释",
    "非交易许可",
    "非执行指令",
    "交易能力禁用",
    "执行能力禁用",
    "demo-only",
    "read-only",
    "next_allowed_stage 只是流程提示",
    "当前区块不提供交易、执行、风控修改或仓位计算能力",
    "SECURITY BLOCKED",
  ].forEach((expected) =>
    assertIncludes("component files", componentSource, expected),
  );

  [
    "fetchDemoReadOnlyExplanation(",
    "mapDemoReadOnlyExplanationApiToViewModel(",
    "apiGet(",
    "fetch(",
    "axios",
    "XMLHttpRequest",
    "useEffect",
    "setInterval",
    "setTimeout",
    "WebSocket",
    "EventSource",
    "localStorage",
    "sessionStorage",
    "window.location",
    "<button",
    "<form",
    "onSubmit",
    "submit",
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
    "label: \"key\"",
    "label: 'key'",
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
    "should buy",
    "should sell",
    "open position",
    "close position",
    "execute trade",
    "allow trade",
    "can trade",
    "suggested lot",
  ].forEach((forbidden) =>
    assertNotIncludes("component files", componentSource, forbidden),
  );

  [
    /:\s*any\b/,
    /:\s*unknown\b/,
    /Record\s*</,
    /DemoReadOnlyExplanationApiResponse/,
    /raw\s*api/i,
    /raw\s*object/i,
    /credentials/i,
    /account\s+data/i,
    /order\s+data/i,
    /trade\s+action\s+data/i,
    /交易按钮/,
    /执行按钮/,
    /刷新按钮/,
    /API\s*请求按钮/i,
    /MT4\s*操作入口/i,
    /风控修改入口/,
    /仓位计算入口/,
    /账号连接入口/,
    /文件读取入口/,
    /读取文件入口/,
    /手动刷新按钮/,
    /交易\s*\/\s*执行按钮/,
  ].forEach((pattern) =>
    assertNotMatches(
      "component files",
      componentSource,
      pattern,
      `forbidden component safety pattern ${pattern}`,
    ),
  );

  [
    "demoExplanation",
    "fetchDemoReadOnlyExplanation",
    "DemoReadOnlyExplanationPanel",
    "ExplanationPanel",
  ].forEach((forbidden) => assertNotIncludes("App.tsx", appSource, forbidden));
  [
    "fetchDemoReadOnlyExplanation",
    "DemoReadOnlyExplanationPanel",
    "apiErrorViewModel",
    "explanationState",
    "setExplanationState",
    "fetchDemoReadOnlyExplanation().catch(() => apiErrorViewModel())",
    "setExplanationState({ state: \"ready\", viewModel: apiErrorViewModel() })",
  ].forEach((expected) =>
    assertIncludes(
      "DemoReadOnlyDiagnosticsDashboard.tsx",
      diagnosticsDashboardSource,
      expected,
    ),
  );
  [
    "useEffect",
    "setInterval",
    "setTimeout",
    "WebSocket",
    "EventSource",
    "localStorage",
    "sessionStorage",
    "window.location",
    "<form",
    "onSubmit",
    "submit",
    "刷新只读解释",
    "加载解释</button",
    "加载解释",
    "API 请求按钮",
    "交易按钮",
    "执行按钮",
    "自动交易开关",
    "自动训练开关",
    "MT4 操作入口",
    "MT4 操作按钮",
    "风控修改入口",
    "风控按钮",
    "仓位计算入口",
    "仓位按钮",
    "账号连接入口",
    "账号连接按钮",
    "文件读取入口",
    "文件读取按钮",
    "raw API response",
    "raw payload",
  ].forEach((forbidden) =>
    assertNotIncludes(
      "DemoReadOnlyDiagnosticsDashboard.tsx",
      diagnosticsDashboardSource,
      forbidden,
    ),
  );
  [
    /useEffect\s*\([^)]*fetchDemoReadOnlyExplanation/s,
    /fetchDemoReadOnlyExplanation\s*\(\s*\)(?!\.catch)/,
    /onClick=\{(?!handleRefreshDiagnostics)[^}]*\}/,
    /<a\s+/i,
  ].forEach((pattern) =>
    assertNotMatches(
      "DemoReadOnlyDiagnosticsDashboard.tsx",
      diagnosticsDashboardSource,
      pattern,
      `forbidden dashboard integration pattern ${pattern}`,
    ),
  );

  const directExplanationPanelReferences = srcFiles.filter((filePath) => {
    const source = readSource(filePath);
    return (
      source.includes("DemoReadOnlyExplanationPanel") &&
      !filePath.endsWith(path.join("components", "DemoReadOnlyExplanationPanel.tsx")) &&
      filePath !== files.diagnosticsDashboard &&
      !filePath.endsWith(path.join("features", "demoExplanation", "index.ts"))
    );
  });
  if (directExplanationPanelReferences.length > 0) {
    fail(
      `DemoReadOnlyExplanationPanel must only be directly used by the diagnostics dashboard: ${directExplanationPanelReferences.join(", ")}`,
    );
  }

  const dashboardButtonCount =
    diagnosticsDashboardSource.match(/<button\b/g)?.length ?? 0;
  if (dashboardButtonCount !== 1) {
    fail(
      `DemoReadOnlyDiagnosticsDashboard.tsx must keep exactly one existing diagnostics refresh button, found ${dashboardButtonCount}.`,
    );
  }
  [
    "handleRefreshDiagnostics",
    "刷新 Demo 只读诊断",
    "只读解释",
    "非交易许可",
    "非执行指令",
    "交易能力禁用",
    "执行能力禁用",
    "demo-only",
    "read-only",
    "next_allowed_stage 只是流程提示",
    "当前区块不提供交易、执行、风控修改或仓位计算能力",
  ].forEach((expected) =>
    assertIncludes(
      "DemoReadOnlyDiagnosticsDashboard.tsx",
      diagnosticsDashboardSource,
      expected,
    ),
  );
}

if (failures.length > 0) {
  console.error("[demo-explanation-safety] failed");
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(
  "[demo-explanation-safety] passed: explanation client, mapper, panel, and dashboard integration stay manual, read-only, and demo-only.",
);
