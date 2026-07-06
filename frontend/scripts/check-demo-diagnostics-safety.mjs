import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, "..");
const featureRoot = path.join(frontendRoot, "src", "features", "demoDiagnostics");
const componentRoot = path.join(featureRoot, "components");

const files = {
  contracts: path.join(featureRoot, "contracts.ts"),
  mapper: path.join(featureRoot, "mapper.ts"),
  api: path.join(featureRoot, "api.ts"),
  types: path.join(featureRoot, "types.ts"),
  dashboard: path.join(componentRoot, "DemoReadOnlyDiagnosticsDashboard.tsx"),
  overall: path.join(componentRoot, "OverallStatusPanel.tsx"),
  bundle: path.join(componentRoot, "BundleStatusPanel.tsx"),
  components: path.join(componentRoot, "ComponentStatusList.tsx"),
  readiness: path.join(componentRoot, "ReadinessPanel.tsx"),
};

const failures = [];

function readSource(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function fail(message) {
  failures.push(message);
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

function assertMatches(label, source, pattern, message) {
  if (!pattern.test(source)) {
    fail(`${label} ${message}`);
  }
}

function assertFileExists(label, filePath) {
  if (!fs.existsSync(filePath)) {
    fail(`${label} file is missing: ${filePath}`);
  }
}

Object.entries(files).forEach(([label, filePath]) => {
  assertFileExists(label, filePath);
});

if (failures.length === 0) {
  const contractsSource = readSource(files.contracts);
  const mapperSource = readSource(files.mapper);
  const apiSource = readSource(files.api);
  const typesSource = readSource(files.types);
  const dashboardSource = readSource(files.dashboard);
  const visibleComponentSource = [
    files.dashboard,
    files.overall,
    files.bundle,
    files.components,
    files.readiness,
  ]
    .map(readSource)
    .join("\n");

  [
    "DemoDiagnosticsApiResponse",
    "DemoDiagnosticsViewModel",
    "ComponentStatusViewModel",
    "BundleStatusViewModel",
    "ReadinessViewModel",
    "SafetyFlagsViewModel",
  ].forEach((typeName) => assertIncludes("types.ts", typesSource, typeName));

  [
    "ALLOWED_RESPONSE_FIELDS",
    "FORBIDDEN_FIELDS",
    "FORBIDDEN_TEXT_MARKERS",
    "SAFE_FLAGS",
    "SECURITY_BLOCKED_STATUS_CODE",
    "SECURITY_BLOCKED_MESSAGE",
    "raw_payload",
    "account_number",
    "password",
    "credential",
    "token",
    "secret",
    "login",
    "suggested_lot",
    "final_lot",
    "buy_now",
    "sell_now",
    "should_buy",
    "should_sell",
    "order_id",
    "ticket",
    "ea_command",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
  ].forEach((expected) =>
    assertIncludes("contracts.ts", contractsSource, expected),
  );

  [
    "mapDemoDiagnosticsApiToViewModel",
    "collectForbiddenContentReasons",
    "collectForbiddenContent",
    "validateTopLevelSafetyFlags",
    "validateNestedSafetyFlags",
    "securityBlockedViewModel",
    "readStringArray",
    "readString",
    "SAFE_FLAGS",
    "ui_state: \"security_blocked\"",
    "response.passed === true",
    "next_allowed_stage: readStringArray(response.next_allowed_stage)",
  ].forEach((expected) => assertIncludes("mapper.ts", mapperSource, expected));

  [
    "...response",
    "Object.assign",
    "localStorage",
    "sessionStorage",
    "setInterval",
    "WebSocket",
  ].forEach((forbidden) => assertNotIncludes("mapper.ts", mapperSource, forbidden));

  assertIncludes("api.ts", apiSource, "DEMO_DIAGNOSTICS_ENDPOINT");
  assertIncludes("api.ts", apiSource, "apiGet");
  ["apiPost", "fetch(", "method: \"POST\"", "method: 'POST'", "WebSocket"].forEach(
    (forbidden) => assertNotIncludes("api.ts", apiSource, forbidden),
  );

  assertIncludes("Dashboard component", dashboardSource, "handleRefreshDiagnostics");
  assertIncludes("Dashboard component", dashboardSource, "SECURITY_BLOCKED_MESSAGE");
  [
    "useEffect",
    "setInterval",
    "setTimeout",
    "WebSocket",
    "localStorage",
    "sessionStorage",
  ].forEach((forbidden) =>
    assertNotIncludes("Dashboard component", dashboardSource, forbidden),
  );

  [
    "只读诊断",
    "非交易许可",
    "非执行指令",
    "交易能力禁用",
    "执行能力禁用",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "next_allowed_stage 是流程提示，不是交易许可",
  ].forEach((expected) =>
    assertIncludes("visible dashboard components", visibleComponentSource, expected),
  );
  assertIncludes("contracts.ts", contractsSource, "SECURITY BLOCKED");
  assertIncludes(
    "Dashboard component",
    dashboardSource,
    "SECURITY_BLOCKED_MESSAGE",
  );

  [
    "raw payload",
    "raw_payload",
    "account_number",
    "login",
    "password",
    "credential",
    "token",
    "secret",
    "suggested_lot",
    "final_lot",
    "buy_now",
    "sell_now",
    "should_buy",
    "should_sell",
    "order_id",
    "ticket",
    "ea_command",
    "traceback",
    "stack_trace",
    "system_path",
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
    "open position",
    "close position",
    "suggested lot",
    "execute trade",
    "allow trade",
    "can trade",
  ].forEach((forbidden) =>
    assertNotIncludes("visible dashboard components", visibleComponentSource, forbidden),
  );

  assertMatches(
    "mapper.ts",
    mapperSource,
    /return\s*\{\s*\.\.\.SAFE_FLAGS,/,
    "must build view models from safe flags rather than forwarding API payloads.",
  );
  assertMatches(
    "mapper.ts",
    mapperSource,
    /if\s*\(!isRecord\(response\)\)/,
    "must guard missing or wrong response types.",
  );
}

if (failures.length > 0) {
  console.error("[demo-diagnostics-safety] failed");
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(
  "[demo-diagnostics-safety] passed: mapper, API client, and visible UI keep demo-only read-only safety boundaries.",
);
