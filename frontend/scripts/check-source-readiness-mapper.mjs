import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import ts from "typescript";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, "..");
const mapperPath = path.join(
  frontendRoot,
  "src",
  "features",
  "demoDiagnostics",
  "sourceReadinessMapper.ts",
);

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

const mapperSource = readSource(mapperPath);

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
  "OrderSend",
  "OrderClose",
  "OrderModify",
  "OrderDelete",
].forEach((forbidden) => {
  assert(
    !mapperSource.includes(forbidden),
    `sourceReadinessMapper.ts must not include ${forbidden}.`,
  );
});

const transpiled = ts.transpileModule(mapperSource, {
  compilerOptions: {
    module: ts.ModuleKind.ES2022,
    target: ts.ScriptTarget.ES2020,
  },
  fileName: mapperPath,
}).outputText;

const tempModulePath = path.join(
  frontendRoot,
  ".source-readiness-mapper-test.mjs",
);
fs.writeFileSync(tempModulePath, transpiled, "utf8");

const {
  mapDemoDiagnosticsSourceReadinessToUiModel,
  unsafeSourceReadinessModel,
} = await import(pathToFileURL(tempModulePath).href);

fs.unlinkSync(tempModulePath);

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

const forbiddenValueMarkers = [
  "C:\\Users\\",
  "\\Users\\",
  "/home/",
  "Traceback",
  "stack trace",
  "password",
  "credential",
  "token",
  "secret",
  "api_key",
  "ACC-123456",
  "LOGIN-123456",
  "TICKET-123456",
  "ORDER-123456",
  "suggested_lot",
  "final_lot",
  "buy_now",
  "sell_now",
  "should_buy",
  "should_sell",
  "open_position",
  "close_position",
  "OrderSend",
  "OrderClose",
  "OrderModify",
  "OrderDelete",
  "EA command",
  "TradePlan",
  "ExecutionPlan",
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
    component_statuses: {
      bundle: {
        passed: true,
        status_code: "SAFE",
        block_reasons: [],
        warning_reasons: [],
      },
    },
    validation_statuses: {
      source_config: {
        passed: true,
      },
    },
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

function map(input) {
  return mapDemoDiagnosticsSourceReadinessToUiModel(input);
}

function walk(value, visitor) {
  if (Array.isArray(value)) {
    value.forEach((item) => walk(item, visitor));
    return;
  }
  if (typeof value !== "object" || value === null) {
    visitor(null, value);
    return;
  }
  Object.entries(value).forEach(([key, child]) => {
    visitor(key, child);
    walk(child, visitor);
  });
}

function assertNoForbiddenOutputSurface(model, label) {
  walk(model, (key, value) => {
    if (key !== null) {
      assert(
        !forbiddenKeys.includes(key.toLowerCase()),
        `${label} leaked forbidden output key ${key}.`,
      );
    }
    if (typeof value === "string") {
      forbiddenValueMarkers.forEach((marker) => {
        assert(
          !value.toLowerCase().includes(marker.toLowerCase()),
          `${label} leaked forbidden output value marker ${marker}.`,
        );
      });
    }
  });
}

function assertAlwaysNonTrading(model, label) {
  assert(model.showAsTradable === false, `${label} must never be tradable.`);
  assert(model.showAsExecutable === false, `${label} must never be executable.`);
  assert(
    !Object.keys(model).some((key) =>
      [
        "source_mode_control",
        "bridge_dir_input",
        "base_dir_input",
        "candidate_path_input",
        "trade_button",
        "execution_button",
        "suggested_lot",
        "final_lot",
        "ea_command",
      ].includes(key.toLowerCase()),
    ),
    `${label} must not expose source controls or trading state keys.`,
  );
}

function expectSafe(model, label) {
  assert(model.isUnsafeResponse === false, `${label} should be safe.`);
  assert(model.canShowSourceReadinessCard === true, `${label} should show card.`);
  assert(model.showAsReadOnly === true, `${label} must show read-only true.`);
  assert(model.showAsDemoOnly === true, `${label} must show demo-only true.`);
  assertAlwaysNonTrading(model, label);
  assertNoForbiddenOutputSurface(model, label);
}

function expectUnsafe(model, label) {
  assert(model.isUnsafeResponse === true, `${label} should be unsafe.`);
  assert(
    model.readinessLevel === "unsafe_response",
    `${label} should map to unsafe_response.`,
  );
  assert(
    model.canShowSourceReadinessCard === false,
    `${label} should not show normal card.`,
  );
  assertAlwaysNonTrading(model, label);
  assertNoForbiddenOutputSurface(model, label);
}

const docsFixtureModel = map(baseInput());
expectSafe(docsFixtureModel, "docs_fixture_only");
assert(
  docsFixtureModel.displaySourceModeLabel === "文档示例 / 安全 fixture",
  "docs_fixture_only should map to fixture label.",
);
assert(
  docsFixtureModel.displayReaderStatusLabel === "未调用 reader",
  "docs_fixture_only should show reader not_called.",
);
assert(
  docsFixtureModel.displayBridgeEnabledLabel === "MT4 Demo 文件桥未启用",
  "docs_fixture_only should show bridge disabled.",
);
assert(
  docsFixtureModel.readinessLevel !== "unsafe_response",
  "docs_fixture_only should not be unsafe.",
);

const mt4ReadyModel = map(
  baseInput({
    source_mode: "mt4_demo_readonly_file_bridge_enabled",
    reader_status: "ready",
    reader_passed: true,
    reader_status_code: "READER_READY",
    mt4_demo_readonly_file_bridge_enabled: true,
  }),
);
expectSafe(mt4ReadyModel, "mt4 reader ready");
assert(
  mt4ReadyModel.displaySourceModeLabel === "MT4 Demo 只读文件桥",
  "mt4 ready should map source label.",
);
assert(
  mt4ReadyModel.displayReaderStatusLabel === "reader 已返回安全摘要",
  "mt4 ready should map reader label.",
);
assert(
  mt4ReadyModel.displayReaderResultLabel.includes("不代表交易许可"),
  "reader_passed=true must not imply trading permission.",
);

const sourceConfigPassedModel = map(baseInput({ source_config_passed: true }));
expectSafe(sourceConfigPassedModel, "source config passed");
assert(
  sourceConfigPassedModel.displaySourceConfigLabel.includes("仅表示配置安全通过"),
  "source_config_passed=true should only mean source config passed.",
);

const blockedModel = map(
  baseInput({
    reader_status: "blocked",
    reader_passed: false,
    block_reasons: ["reader_blocked"],
  }),
);
expectSafe(blockedModel, "reader blocked");
assert(
  blockedModel.readinessLevel === "blocked",
  "reader_status=blocked should map to blocked.",
);
assert(
  blockedModel.safeBlockReasons.includes("reader_blocked"),
  "reader blocked should preserve safe block reason.",
);

const errorSafeModel = map(
  baseInput({
    reader_status: "error_safe",
    reader_passed: false,
  }),
);
expectSafe(errorSafeModel, "reader error_safe");
assert(
  errorSafeModel.readinessLevel === "blocked",
  "reader_status=error_safe should map to blocked safe downgrade.",
);
assert(
  errorSafeModel.displayReaderStatusLabel === "reader 异常，已安全降级",
  "reader_status=error_safe should map safe error label.",
);

[
  ["missing read_only", (() => {
    const input = baseInput();
    delete input.read_only;
    return input;
  })()],
  ["read_only=false", baseInput({ read_only: false })],
  ["demo_only=false", baseInput({ demo_only: false })],
  ["is_tradable=true", baseInput({ is_tradable: true })],
  ["can_execute=true", baseInput({ can_execute: true })],
  ["is_trading_permission=true", baseInput({ is_trading_permission: true })],
  [
    "is_execution_instruction=true",
    baseInput({ is_execution_instruction: true }),
  ],
  ["allowed_to_call_ea=true", baseInput({ allowed_to_call_ea: true })],
  [
    "allowed_to_modify_risk=true",
    baseInput({ allowed_to_modify_risk: true }),
  ],
].forEach(([label, input]) => expectUnsafe(map(input), label));

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
  trade_signal: "trade_signal",
  trading_action: "trading_action",
};

Object.entries(forbiddenFieldPayloads).forEach(([fieldName, fieldValue]) => {
  const model = map(
    baseInput({
      component_statuses: {
        polluted_component: {
          [fieldName]: fieldValue,
        },
      },
    }),
  );
  expectUnsafe(model, `forbidden field ${fieldName}`);
});

[
  "C:\\Users\\86135\\secret\\account.json",
  "/home/demo/secret/account.json",
  "Traceback (most recent call last): backend/app/file.py",
  "password token secret credential api_key",
  "ACC-123456 LOGIN-123456",
  "TICKET-123456 ORDER-123456",
  "buy_now sell_now should_buy should_sell",
  "open_position close_position",
  "OrderSend OrderClose OrderModify OrderDelete",
  "EA command",
  "TradePlan ExecutionPlan",
].forEach((unsafeText) => {
  const model = map(
    baseInput({
      warning_reasons: [unsafeText],
    }),
  );
  expectUnsafe(model, `forbidden value ${unsafeText}`);
});

expectUnsafe(map(null), "null input");
expectUnsafe(map(undefined), "undefined input");
expectUnsafe(map([]), "array input");
expectUnsafe(unsafeSourceReadinessModel(), "explicit unsafe model");

if (failures.length > 0) {
  console.error("[source-readiness-mapper] failed");
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(
  "[source-readiness-mapper] passed: source/readiness mapper stays pure, read-only, demo-only, and non-trading.",
);
