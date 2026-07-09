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
const mapperPath = path.join(featureRoot, "sourceReadinessMapper.ts");
const componentPath = path.join(featureRoot, "SourceReadinessCard.tsx");

const failures = [];

function fail(message) {
  failures.push(message);
}

function assert(condition, message) {
  if (!condition) {
    fail(message);
  }
}

function readSource(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function transpileToTempModule(sourcePath, tempName, jsx = false) {
  const source = readSource(sourcePath);
  const outputText = ts.transpileModule(source, {
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

const componentSource = readSource(componentPath);

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
].forEach((forbidden) => {
  assert(
    !componentSource.includes(forbidden),
    `SourceReadinessCard.tsx must not include ${forbidden}.`,
  );
});

const mapperModulePath = transpileToTempModule(
  mapperPath,
  ".source-readiness-mapper-card-test.mjs",
);
const componentModulePath = transpileToTempModule(
  componentPath,
  ".source-readiness-card-test.mjs",
  true,
);

const {
  mapDemoDiagnosticsSourceReadinessToUiModel,
  unsafeSourceReadinessModel,
} = await import(pathToFileURL(mapperModulePath).href);
const { SourceReadinessCard } = await import(
  pathToFileURL(componentModulePath).href
);

fs.unlinkSync(mapperModulePath);
fs.unlinkSync(componentModulePath);

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
  "可以交易",
  "允许交易",
  "可以下单",
  "可以执行",
  "可以开仓",
  "可以平仓",
  "推荐买卖",
  "推荐手数",
  "自动交易",
  "下单按钮",
];

function baseInput(overrides = {}) {
  return {
    source_mode: "docs_fixture_only",
    source_status: "ready",
    source_config_status_code: "SOURCE_CONFIG_VALID",
    source_config_passed: true,
    reader_status: "not_called",
    reader_passed: false,
    reader_status_code: "READER_NOT_CALLED",
    mt4_demo_readonly_file_bridge_enabled: false,
    source_scope: "docs_fixture_only",
    component_statuses: {},
    validation_statuses: {},
    block_reasons: [],
    warning_reasons: [],
    data_quality_notes: ["safe readonly summary"],
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

function render(model) {
  return renderToStaticMarkup(
    React.createElement(SourceReadinessCard, {
      sourceReadiness: model,
    }),
  );
}

function renderFromInput(input) {
  return render(mapDemoDiagnosticsSourceReadinessToUiModel(input));
}

function assertIncludes(label, html, expected) {
  assert(html.includes(expected), `${label} must include ${expected}.`);
}

function assertNotIncludes(label, html, forbidden) {
  assert(
    !html.toLowerCase().includes(forbidden.toLowerCase()),
    `${label} must not include ${forbidden}.`,
  );
}

function assertNoForbiddenSurface(label, html) {
  forbiddenRenderedText.forEach((forbidden) =>
    assertNotIncludes(label, html, forbidden),
  );
  [
    "<button",
    "<input",
    "<select",
    "<textarea",
    "<form",
    "onclick",
  ].forEach((forbidden) => assertNotIncludes(label, html, forbidden));
}

const docsFixtureHtml = renderFromInput(baseInput());
assertIncludes(
  "docs_fixture_only",
  docsFixtureHtml,
  "当前数据源",
);
assertIncludes(
  "docs_fixture_only",
  docsFixtureHtml,
  "文档示例 / 安全 fixture",
);
assertIncludes("docs_fixture_only", docsFixtureHtml, "未调用 reader");
assertIncludes("docs_fixture_only", docsFixtureHtml, "MT4 Demo 文件桥未启用");
assertIncludes("docs_fixture_only", docsFixtureHtml, "只读观察");
assertIncludes("docs_fixture_only", docsFixtureHtml, "交易许可");
assertIncludes("docs_fixture_only", docsFixtureHtml, "不可执行");
assertNoForbiddenSurface("docs_fixture_only", docsFixtureHtml);

const readyHtml = renderFromInput(
  baseInput({
    source_mode: "mt4_demo_readonly_file_bridge_enabled",
    reader_status: "ready",
    reader_passed: true,
    mt4_demo_readonly_file_bridge_enabled: true,
  }),
);
assertIncludes("reader ready", readyHtml, "MT4 Demo 只读文件桥");
assertIncludes("reader ready", readyHtml, "reader 已返回安全摘要");
assertIncludes("reader ready", readyHtml, "reader 安全摘要通过");
assertIncludes("reader ready", readyHtml, "不代表交易许可");
assertIncludes("reader ready", readyHtml, "不可执行");
assertNoForbiddenSurface("reader ready", readyHtml);

const blockedHtml = renderFromInput(
  baseInput({
    reader_status: "blocked",
    block_reasons: ["reader_blocked"],
  }),
);
assertIncludes("reader blocked", blockedHtml, "reader 安全阻断");
assertIncludes("reader blocked", blockedHtml, "reader_blocked");
assertNoForbiddenSurface("reader blocked", blockedHtml);

const errorSafeHtml = renderFromInput(
  baseInput({
    reader_status: "error_safe",
  }),
);
assertIncludes("reader error_safe", errorSafeHtml, "reader 异常，已安全降级");
assertNoForbiddenSurface("reader error_safe", errorSafeHtml);

const unsafeHtml = render(unsafeSourceReadinessModel());
assertIncludes("unsafe", unsafeHtml, "响应安全检查失败");
assertIncludes("unsafe", unsafeHtml, "已阻断展示危险字段");
assertNotIncludes("unsafe", unsafeHtml, "只读 ready");
assertNotIncludes("unsafe", unsafeHtml, "reader 已返回安全摘要");
assertNoForbiddenSurface("unsafe", unsafeHtml);

[
  ["unsafe read_only", baseInput({ read_only: false })],
  ["unsafe demo_only", baseInput({ demo_only: false })],
  ["unsafe tradable", baseInput({ is_tradable: true })],
  ["unsafe executable", baseInput({ can_execute: true })],
  [
    "unsafe execution instruction",
    baseInput({ is_execution_instruction: true }),
  ],
].forEach(([label, input]) => {
  const html = renderFromInput(input);
  assertIncludes(label, html, "响应安全检查失败");
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
  const html = renderFromInput(
    baseInput({
      component_statuses: {
        polluted_component: {
          [fieldName]: fieldValue,
        },
      },
    }),
  );
  assertIncludes(`forbidden field ${fieldName}`, html, "响应安全检查失败");
  assertNoForbiddenSurface(`forbidden field ${fieldName}`, html);
});

[
  "C:\\Users\\86135\\secret\\account.json",
  "/home/demo/secret/account.json",
  "Traceback (most recent call last): backend/app/file.py",
  "password token secret credential api_key",
  "LOGIN-123456 account_number",
  "ticket order_id",
  "OrderSend OrderClose OrderModify OrderDelete",
  "EA command",
  "TradePlan ExecutionPlan",
].forEach((unsafeText) => {
  const html = renderFromInput(
    baseInput({
      warning_reasons: [unsafeText],
    }),
  );
  assertIncludes(`forbidden value ${unsafeText}`, html, "响应安全检查失败");
  assertNoForbiddenSurface(`forbidden value ${unsafeText}`, html);
});

const optionalArraysHtml = render({
  ...mapDemoDiagnosticsSourceReadinessToUiModel(baseInput()),
  safeBlockReasons: undefined,
  safeWarningReasons: undefined,
  safeDataQualityNotes: undefined,
});
assertIncludes("optional arrays", optionalArraysHtml, "暂无安全阻断原因。");
assertIncludes("optional arrays", optionalArraysHtml, "暂无安全警告原因。");
assertIncludes("optional arrays", optionalArraysHtml, "暂无数据质量备注。");
assertNoForbiddenSurface("optional arrays", optionalArraysHtml);

if (failures.length > 0) {
  console.error("[source-readiness-card] failed");
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(
  "[source-readiness-card] passed: component renders source/readiness state as pure, read-only, demo-only, non-trading output.",
);
