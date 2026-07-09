import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, "..");
const featureRoot = path.join(
  frontendRoot,
  "src",
  "features",
  "demoDiagnostics",
);
const componentRoot = path.join(featureRoot, "components");

const files = {
  packageJson: path.join(frontendRoot, "package.json"),
  api: path.join(featureRoot, "api.ts"),
  types: path.join(featureRoot, "types.ts"),
  contracts: path.join(featureRoot, "contracts.ts"),
  mapper: path.join(featureRoot, "sourceReadinessMapper.ts"),
  card: path.join(featureRoot, "SourceReadinessCard.tsx"),
  dashboard: path.join(componentRoot, "DemoReadOnlyDiagnosticsDashboard.tsx"),
};

const failures = [];

function fail(message) {
  failures.push(message);
}

function assert(condition, message) {
  if (!condition) {
    fail(message);
  }
}

function assertIncludes(label, source, expected) {
  assert(
    source.includes(expected),
    `${label} must include ${JSON.stringify(expected)}.`,
  );
}

function assertNotIncludes(label, source, forbidden) {
  assert(
    !source.toLowerCase().includes(forbidden.toLowerCase()),
    `${label} must not include ${JSON.stringify(forbidden)}.`,
  );
}

function readSource(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function assertFileExists(label, filePath) {
  assert(fs.existsSync(filePath), `${label} is missing: ${filePath}`);
}

function transpileToTempModule(sourcePath, tempName, jsx = false) {
  const outputText = ts.transpileModule(readSource(sourcePath), {
    compilerOptions: {
      jsx: jsx ? ts.JsxEmit.ReactJSX : undefined,
      module: ts.ModuleKind.ES2022,
      target: ts.ScriptTarget.ES2020,
    },
    fileName: sourcePath,
  }).outputText;
  const tempPath = path.join(frontendRoot, tempName);
  fs.writeFileSync(tempPath, outputText, "utf8");
  return tempPath;
}

Object.entries(files).forEach(([label, filePath]) =>
  assertFileExists(label, filePath),
);

const packageSource = readSource(files.packageJson);
const apiSource = readSource(files.api);
const typesSource = readSource(files.types);
const contractsSource = readSource(files.contracts);
const mapperSource = readSource(files.mapper);
const cardSource = readSource(files.card);
const dashboardSource = readSource(files.dashboard);

assertIncludes(
  "package.json",
  packageSource,
  "test:source-readiness-dashboard-integration",
);
assertIncludes(
  "package.json",
  packageSource,
  "check-source-readiness-dashboard-integration.mjs",
);

assertIncludes(
  "api.ts",
  apiSource,
  "mapDemoDiagnosticsSourceReadinessToUiModel",
);
assertIncludes("api.ts", apiSource, "source_readiness:");
assertIncludes("api.ts", apiSource, "mapDemoDiagnosticsApiToViewModel(response)");
assertIncludes(
  "api.ts",
  apiSource,
  "mapDemoDiagnosticsSourceReadinessToUiModel(response)",
);
[
  "apiPost",
  "apiPut",
  "apiPatch",
  "apiDelete",
  "reader(",
  "readMt4",
  "bridge_dir",
  "base_dir",
  "candidate_path",
  "localStorage",
  "sessionStorage",
  "WebSocket",
  "EventSource",
  "setInterval",
].forEach((forbidden) => assertNotIncludes("api.ts", apiSource, forbidden));

assertIncludes("types.ts", typesSource, "source_readiness");
[
  "source_mode?: unknown",
  "source_status?: unknown",
  "source_config_status_code?: unknown",
  "source_config_passed?: unknown",
  "reader_status?: unknown",
  "reader_passed?: unknown",
  "reader_status_code?: unknown",
  "mt4_demo_readonly_file_bridge_enabled?: unknown",
  "data_quality_notes?: unknown",
].forEach((expected) => assertIncludes("types.ts", typesSource, expected));

[
  "source_mode",
  "source_status",
  "source_config_status_code",
  "source_config_passed",
  "reader_status",
  "reader_passed",
  "reader_status_code",
  "mt4_demo_readonly_file_bridge_enabled",
  "data_quality_notes",
].forEach((expected) =>
  assertIncludes("contracts.ts allowed fields", contractsSource, expected),
);

assertIncludes("Dashboard", dashboardSource, "SourceReadinessCard");
assertIncludes("Dashboard", dashboardSource, "diagnostics.source_readiness");
assertIncludes("Dashboard", dashboardSource, "getDemoReadOnlyDiagnostics");
assertIncludes("Dashboard", dashboardSource, "handleRefreshDiagnostics");
assertIncludes("Dashboard", dashboardSource, "Demo 数据源只读状态");
[
  "useEffect",
  "setInterval",
  "setTimeout",
  "WebSocket",
  "EventSource",
  "localStorage",
  "sessionStorage",
  "<form",
  "<input",
  "<select",
  "<textarea",
  "source_mode",
  "bridge_dir",
  "base_dir",
  "candidate_path",
  "启用 MT4 文件桥",
  "连接 MT4",
  "连接 Demo 账号",
  "连接真实账号",
  "自动交易开关",
  "RiskGate override",
  "bypass gate",
].forEach((forbidden) =>
  assertNotIncludes("Dashboard", dashboardSource, forbidden),
);

const dashboardButtonCount = dashboardSource.match(/<button\b/g)?.length ?? 0;
assert(
  dashboardButtonCount === 1,
  `Dashboard must keep exactly one manual refresh button, found ${dashboardButtonCount}.`,
);

[
  "fetch(",
  "XMLHttpRequest",
  "WebSocket",
  "EventSource",
  "localStorage",
  "sessionStorage",
  "window.",
  "document.",
  "process.env",
  "os.environ",
  "readFile",
  "writeFile",
  "node:fs",
  "useEffect",
  "onClick",
  "<button",
  "<input",
  "<form",
  "<select",
  "<textarea",
].forEach((forbidden) =>
  assertNotIncludes("SourceReadinessCard.tsx", cardSource, forbidden),
);

[
  "fetch(",
  "XMLHttpRequest",
  "WebSocket",
  "EventSource",
  "localStorage",
  "sessionStorage",
  "window.",
  "document.",
  "process.env",
  "os.environ",
  "readFile",
  "writeFile",
  "node:fs",
].forEach((forbidden) =>
  assertNotIncludes("sourceReadinessMapper.ts", mapperSource, forbidden),
);

const mapperModulePath = transpileToTempModule(
  files.mapper,
  ".source-readiness-dashboard-mapper-test.mjs",
);
const cardModulePath = transpileToTempModule(
  files.card,
  ".source-readiness-dashboard-card-test.mjs",
  true,
);

const { mapDemoDiagnosticsSourceReadinessToUiModel } = await import(
  pathToFileURL(mapperModulePath).href
);
const { SourceReadinessCard } = await import(pathToFileURL(cardModulePath).href);

fs.unlinkSync(mapperModulePath);
fs.unlinkSync(cardModulePath);

const forbiddenKeys = [
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
];

const forbiddenRenderedText = [
  ...forbiddenKeys,
  "C:\\Users\\",
  "\\Users\\",
  "/home/",
  "Traceback",
  "stack trace",
  "OrderSend",
  "OrderClose",
  "OrderModify",
  "OrderDelete",
  "EA command",
  "TradePlan",
  "ExecutionPlan",
  "可以买",
  "可以卖",
  "可以买入",
  "可以卖出",
  "可以下单",
  "可以执行",
  "可以开仓",
  "可以平仓",
  "允许交易",
  "推荐买入",
  "推荐卖出",
  "推荐手数",
  "自动交易",
  "下单按钮",
];

function baseResponse(overrides = {}) {
  return {
    source_mode: "docs_fixture_only",
    source_status: "ready",
    source_config_status_code: "SOURCE_CONFIG_VALID",
    source_config_passed: true,
    reader_status: "not_called",
    reader_passed: false,
    reader_status_code: "READER_NOT_CALLED",
    mt4_demo_readonly_file_bridge_enabled: false,
    data_quality_notes: ["safe readonly summary"],
    block_reasons: [],
    warning_reasons: [],
    read_only: true,
    demo_only: true,
    is_tradable: false,
    can_execute: false,
    is_trading_permission: false,
    is_execution_instruction: false,
    allowed_to_call_ea: false,
    allowed_to_modify_risk: false,
    ...overrides,
  };
}

function renderFromResponse(response) {
  const sourceReadiness =
    mapDemoDiagnosticsSourceReadinessToUiModel(response);
  return renderToStaticMarkup(
    React.createElement(SourceReadinessCard, { sourceReadiness }),
  );
}

function assertHtmlIncludes(label, html, expected) {
  assert(html.includes(expected), `${label} must include ${expected}.`);
}

function assertHtmlNotIncludes(label, html, forbidden) {
  assert(
    !html.toLowerCase().includes(forbidden.toLowerCase()),
    `${label} must not include ${forbidden}.`,
  );
}

function assertNoForbiddenSurface(label, html) {
  forbiddenRenderedText.forEach((forbidden) =>
    assertHtmlNotIncludes(label, html, forbidden),
  );
  ["<button", "<input", "<select", "<textarea", "<form", "onclick"].forEach(
    (forbidden) => assertHtmlNotIncludes(label, html, forbidden),
  );
}

const docsFixtureHtml = renderFromResponse(baseResponse());
assertHtmlIncludes(
  "docs_fixture_only dashboard card",
  docsFixtureHtml,
  "文档示例 / 安全 fixture",
);
assertHtmlIncludes(
  "docs_fixture_only dashboard card",
  docsFixtureHtml,
  "未调用 reader",
);
assertHtmlIncludes(
  "docs_fixture_only dashboard card",
  docsFixtureHtml,
  "MT4 Demo 文件桥未启用",
);
assertHtmlIncludes("docs_fixture_only dashboard card", docsFixtureHtml, "只读观察");
assertHtmlIncludes("docs_fixture_only dashboard card", docsFixtureHtml, "交易许可");
assertHtmlIncludes("docs_fixture_only dashboard card", docsFixtureHtml, "否");
assertHtmlIncludes("docs_fixture_only dashboard card", docsFixtureHtml, "不可执行");
assertNoForbiddenSurface("docs_fixture_only dashboard card", docsFixtureHtml);

const readerReadyHtml = renderFromResponse(
  baseResponse({
    source_mode: "mt4_demo_readonly_file_bridge_enabled",
    reader_status: "ready",
    reader_passed: true,
    reader_status_code: "READER_READY",
    mt4_demo_readonly_file_bridge_enabled: true,
  }),
);
assertHtmlIncludes("reader ready dashboard card", readerReadyHtml, "MT4 Demo 只读文件桥");
assertHtmlIncludes("reader ready dashboard card", readerReadyHtml, "reader 已返回安全摘要");
assertHtmlIncludes("reader ready dashboard card", readerReadyHtml, "reader 安全摘要通过");
assertHtmlIncludes("reader ready dashboard card", readerReadyHtml, "只读 / Demo-only");
assertHtmlIncludes("reader ready dashboard card", readerReadyHtml, "不可执行");
assertNoForbiddenSurface("reader ready dashboard card", readerReadyHtml);

const readerBlockedHtml = renderFromResponse(
  baseResponse({
    reader_status: "blocked",
    block_reasons: ["reader_blocked"],
  }),
);
assertHtmlIncludes("reader blocked dashboard card", readerBlockedHtml, "reader 安全阻断");
assertHtmlIncludes("reader blocked dashboard card", readerBlockedHtml, "reader_blocked");
assertNoForbiddenSurface("reader blocked dashboard card", readerBlockedHtml);

const readerErrorSafeHtml = renderFromResponse(
  baseResponse({
    reader_status: "error_safe",
  }),
);
assertHtmlIncludes(
  "reader error_safe dashboard card",
  readerErrorSafeHtml,
  "reader 异常，已安全降级",
);
assertNoForbiddenSurface("reader error_safe dashboard card", readerErrorSafeHtml);

[
  ["unsafe read_only", baseResponse({ read_only: false })],
  ["unsafe demo_only", baseResponse({ demo_only: false })],
  ["unsafe tradable", baseResponse({ is_tradable: true })],
  ["unsafe executable", baseResponse({ can_execute: true })],
  [
    "unsafe execution instruction",
    baseResponse({ is_execution_instruction: true }),
  ],
].forEach(([label, response]) => {
  const html = renderFromResponse(response);
  assertHtmlIncludes(label, html, "响应安全检查失败");
  assertHtmlIncludes(label, html, "已阻断展示危险字段");
  assertHtmlNotIncludes(label, html, "只读 ready");
  assertHtmlNotIncludes(label, html, "reader 已返回安全摘要");
  assertNoForbiddenSurface(label, html);
});

const forbiddenFieldPayloads = {
  bridge_dir: "C:\\Users\\86135\\mt4",
  base_dir: "C:\\Users\\86135\\mt4",
  candidate_path: "C:\\Users\\86135\\mt4\\account_snapshot.json",
  raw_payload: { secret: "token-value" },
  traceback: "Traceback file.py:1",
  system_path: "C:\\Users\\86135\\AppData\\file.py",
  password: "password-value",
  token: "token-value",
  secret: "secret-value",
  login: "LOGIN-123456",
  account_number: "ACC-123456",
  ticket: "TICKET-123456",
  order_id: "ORDER-123456",
  suggested_lot: 0.01,
  final_lot: 0.01,
  buy_now: true,
  sell_now: true,
  should_buy: true,
  should_sell: true,
  open_position: true,
  close_position: true,
  order_send: true,
  order_close: true,
  order_modify: true,
  order_delete: true,
  ea_command: "EA command",
};

Object.entries(forbiddenFieldPayloads).forEach(([fieldName, fieldValue]) => {
  const html = renderFromResponse(
    baseResponse({
      component_statuses: {
        polluted_component: {
          [fieldName]: fieldValue,
        },
      },
    }),
  );
  assertHtmlIncludes(`forbidden field ${fieldName}`, html, "响应安全检查失败");
  assertNoForbiddenSurface(`forbidden field ${fieldName}`, html);
});

[
  "C:\\Users\\86135\\secret\\account.json",
  "/home/demo/secret/account.json",
  "Traceback (most recent call last): backend/app/file.py",
  "password token secret credential api_key",
  "LOGIN-123456 account_number",
  "ticket order_id",
  "suggested_lot final_lot",
  "buy_now sell_now should_buy should_sell",
  "open_position close_position",
  "OrderSend OrderClose OrderModify OrderDelete",
  "EA command",
  "TradePlan ExecutionPlan",
].forEach((unsafeText) => {
  const html = renderFromResponse(
    baseResponse({
      warning_reasons: [unsafeText],
    }),
  );
  assertHtmlIncludes(`forbidden value ${unsafeText}`, html, "响应安全检查失败");
  assertNoForbiddenSurface(`forbidden value ${unsafeText}`, html);
});

if (failures.length > 0) {
  console.error("[source-readiness-dashboard-integration] failed");
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(
  "[source-readiness-dashboard-integration] passed: dashboard uses existing diagnostics response to render source readiness safely without new API, reader, MT4, or controls.",
);
