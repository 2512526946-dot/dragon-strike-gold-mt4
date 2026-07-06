import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, "..");
const srcRoot = path.join(frontendRoot, "src");
const featureRoot = path.join(srcRoot, "features", "demoExplanation");

const files = {
  types: path.join(featureRoot, "types.ts"),
  contracts: path.join(featureRoot, "contracts.ts"),
  mapper: path.join(featureRoot, "mapper.ts"),
  api: path.join(featureRoot, "api.ts"),
  index: path.join(featureRoot, "index.ts"),
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

function assertFileMissing(label, filePath) {
  if (fs.existsSync(filePath)) {
    fail(`${label} must not exist: ${filePath}`);
  }
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

Object.entries(files).forEach(([label, filePath]) =>
  assertFileExists(label, filePath),
);
assertFileMissing(
  "ExplanationPanel",
  path.join(featureRoot, "components", "DemoReadOnlyExplanationPanel.tsx"),
);
assertFileMissing("demoExplanation components directory", path.join(featureRoot, "components"));

if (failures.length === 0) {
  const typesSource = readSource(files.types);
  const contractsSource = readSource(files.contracts);
  const mapperSource = readSource(files.mapper);
  const apiSource = readSource(files.api);
  const indexSource = readSource(files.index);
  const appSource = readSource(files.app);
  const diagnosticsDashboardSource = readSource(files.diagnosticsDashboard);

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
  ].forEach((expected) => assertIncludes("index.ts", indexSource, expected));

  [
    "demoExplanation",
    "fetchDemoReadOnlyExplanation",
    "DemoReadOnlyExplanationPanel",
    "ExplanationPanel",
  ].forEach((forbidden) => assertNotIncludes("App.tsx", appSource, forbidden));
  [
    "demoExplanation",
    "fetchDemoReadOnlyExplanation",
    "DemoReadOnlyExplanationPanel",
    "ExplanationPanel",
  ].forEach((forbidden) =>
    assertNotIncludes(
      "DemoReadOnlyDiagnosticsDashboard.tsx",
      diagnosticsDashboardSource,
      forbidden,
    ),
  );
}

if (failures.length > 0) {
  console.error("[demo-explanation-safety] failed");
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(
  "[demo-explanation-safety] passed: explanation client and mapper stay read-only, demo-only, and UI-free.",
);
