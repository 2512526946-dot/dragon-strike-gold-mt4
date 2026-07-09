# MT4 Demo Readonly Bridge Preflight Contract

This document defines the preflight contract for any future MT4 Demo readonly
file bridge activation work. It is a planning and acceptance document only. It
does not enable the reader by default, does not read real MT4 files, does not
connect to an EA, does not generate trade advice, and does not permit live or
automated trading.

## 1. Purpose

The purpose of this document is to set the minimum safety and acceptance
contract that must be satisfied before future work may implement MT4 Demo
readonly file bridge behavior.

This document establishes:

- Preconditions for future MT4 Demo readonly file bridge implementation.
- Safety boundaries that must not be weakened.
- The relationship between source config, reader behavior, diagnostics,
  Dashboard display, and future data-quality gates.
- Required tests and review gates before any reader default can change.
- Capabilities that remain explicitly out of scope.

Current scope remains limited:

- The reader is not enabled by default.
- No real MT4 file is read.
- No EA is connected.
- No execution path is created.
- No trade advice is generated.
- Live trading and automated trading remain prohibited.

## 2. Current Stable Baseline

Current stable baseline:

- Main commit: `d6c627d9dfe50aa34e1f54f9e55cf43689563884`.
- Tag: `v0.30.0-dashboard-source-readiness-core`.
- System mode: Demo-only / Read-only.
- Reader: conditionally available in the diagnostics layer, but disabled by
  default.
- Dashboard source/readiness: display chain is implemented and stable.
- Diagnostics API: has guarded reader-conditional wiring capability, but does
  not enable the reader by default.
- Query, header, and body inputs must not enable the reader.
- Any bridge directory must come only from server-side internal configuration.

The stable baseline is a readonly diagnostic and display foundation. It is not
a trading system and not an execution system.

## 3. Non-Goals

This stage does not do any of the following:

- Connect to real MT4.
- Read real MT4 files.
- Enable reader default mode.
- Write EA or MQL4 code.
- Connect automated order placement.
- Connect live trading.
- Add Agent or LLM trading decisions.
- Add RiskGate, PositionSizing, or ExecutionGate behavior.
- Add TradePlanSchema behavior.
- Generate real trade advice.
- Expose bridge paths in the frontend.
- Add source-mode controls or bridge-directory inputs.
- Add trade buttons, execution buttons, or automated trading switches.

## 4. Safety Principles

The future bridge activation path must preserve these safety principles:

1. The Agent has advisory authority only.
2. Program gates have veto authority.
3. The EA is the only future execution authority, and only for authorized Demo
   orders.
4. Semi-automatic phases require explicit user confirmation.
5. Automatic Demo training is disabled by default.
6. Live trading is not allowed in the current stage.
7. Default behavior is Demo-only / Read-only.
8. Martingale behavior is prohibited.
9. Grid averaging behavior is prohibited.
10. Trading without a stop loss is prohibited.
11. Overnight holding is prohibited.
12. Stale data must prevent trade-advice generation.
13. Any Gate rejection must stop the chain.
14. The reader must not be enabled by query, header, or body input.
15. Any bridge directory must come only from server-side internal config.
16. The frontend must not expose `bridge_dir`, `base_dir`, or
    `candidate_path`.

These principles apply even if a source config check passes, a reader summary
passes, diagnostics are healthy, or the Dashboard renders a ready state.

## 5. Future Bridge Activation Preconditions

Future MT4 Demo readonly file bridge implementation must not begin until these
preconditions are satisfied and reviewed:

- Readonly fixture-file tests exist.
- Stale data tests exist.
- Malformed file tests exist.
- Missing file tests exist.
- Path injection tests exist.
- Forbidden field tests exist.
- Unsafe response tests exist.
- Tests prove query, header, and body inputs cannot enable the reader.
- Tests prove the bridge directory can only come from server-side internal
  configuration.
- Tests prove reader failure makes diagnostics fail closed.
- Tests prove the Dashboard displays readiness only and does not display
  sensitive local paths.
- Tests prove `source_config_passed` and `reader_passed` do not represent
  trading permission.
- Tests prove all execution-related capabilities remain unavailable.
- Review confirms that no real account data, real positions, real order
  history, credentials, secrets, or sensitive paths can be emitted.

## 6. Expected Future Gate Chain

The recommended future gate chain is:

```text
SourceConfigGuard
  -> DemoReadonlyReaderValidation
  -> DataFreshnessCheck
  -> DataQualityGate
  -> Diagnostics Readiness Output
  -> Dashboard Display Only
```

This chain is descriptive only. This document does not implement any gate and
does not rename or replace existing code.

Expected meaning of each step:

- `SourceConfigGuard`: confirms the source mode is safe and server-controlled.
- `DemoReadonlyReaderValidation`: validates readonly reader output without
  exposing raw payloads or paths.
- `DataFreshnessCheck`: rejects stale snapshots before any downstream analysis.
- `DataQualityGate`: future gate for broader quality and consistency checks.
- `Diagnostics Readiness Output`: safe status summary, not trading permission.
- `Dashboard Display Only`: readonly UI status display, not execution control.

If an existing code name differs from a proposed name, future implementation
should prefer the existing code name and update this document in a docs-only
change first.

## 7. Diagnostics Contract Expectations

Diagnostics must express data-source state and readability state only. It must
not express trading permission.

Required expectations:

- `source_config_passed` only means the source config guard passed.
- `reader_passed` only means readonly reader validation passed.
- Readiness does not mean the system can buy or sell.
- Diagnostics must not return real trade advice.
- Diagnostics must not return order permission.
- Diagnostics must not expose sensitive local paths.
- Diagnostics must not expose account numbers, passwords, server credentials,
  real positions, or real order history.
- Diagnostics must fail closed when reader output is missing, stale, malformed,
  unsafe, or internally inconsistent.
- Diagnostics must keep `is_tradable=false` and `can_execute=false` while the
  system remains in Demo-only / Read-only mode.

Passing diagnostics are allowed to say that a readonly source appears
readable. They are not allowed to say that a trade may be placed.

## 8. Dashboard Contract Expectations

The Dashboard may display only safe source/readiness summaries:

- Current source-mode safety summary.
- Source readiness state.
- Reader status such as `ready`, `blocked`, or `error_safe`.
- Stale, malformed, missing, or unsafe file status.
- Safety explanation copy.
- Demo-only / Read-only indicators.
- Non-execution indicators such as `is_tradable=false` and
  `can_execute=false`.

The Dashboard must not display:

- `bridge_dir`.
- `base_dir`.
- `candidate_path`.
- Real account identifiers.
- Real positions.
- Real orders.
- Real trade logs.
- Trade buttons.
- Execution buttons.
- Automated trading switches.
- Trade advice.
- Position-size advice.
- Raw payloads.
- Stack traces.
- System paths.

The Dashboard is a display-only surface. It must not provide controls that
change source mode, configure paths, enable readers, connect accounts, connect
MT4, call an EA, or place orders.

## 9. Future Test Plan

Future bridge activation work should add or strengthen these test categories:

- Backend contract tests.
- Backend safety tests.
- Reader validation tests.
- Path injection tests.
- Stale snapshot tests.
- Malformed snapshot tests.
- Missing snapshot tests.
- Unsafe response tests.
- Forbidden field tests.
- Server-side config-only activation tests.
- Query/header/body non-activation tests.
- Frontend mapper tests.
- `SourceReadinessCard` display tests.
- Dashboard integration tests.
- No trading UI tests.
- No sensitive path rendering tests.
- No raw payload rendering tests.
- Fail-closed diagnostics tests.

These tests should be introduced before any change that reads MT4 Demo files
from a configured bridge directory.

## 10. Go / No-Go Checklist

Go conditions:

- All safety tests pass.
- The reader can still only be controlled by server-side config.
- Query, header, and body inputs cannot enable the reader.
- The Dashboard does not expose sensitive paths.
- Diagnostics do not generate trade advice.
- Stale data is rejected.
- Malformed data is rejected.
- Missing data enters a safe blocked or `error_safe` path.
- Reader failure causes diagnostics to fail closed.
- The system remains Demo-only / Read-only.
- `source_config_passed` and `reader_passed` are displayed only as source and
  reader status, not as trade permission.
- No execution-related UI or API path is introduced.

No-Go conditions:

- Query, header, or body input can affect reader activation.
- The frontend can input or display a bridge directory.
- Diagnostics return trade advice.
- The Dashboard shows a trade or execution button.
- Reader failure is still treated as ready.
- Stale data is shown as usable.
- Malformed data is shown as usable.
- Any live trading, EA execution, automated trading, or order-placement ability
  appears.
- Account identifiers, credentials, real positions, real order history, raw
  payloads, stack traces, or system paths are exposed.

If any No-Go condition appears, bridge activation must stop and the issue must
be handled as a separate safety-hardening work order.

## 11. Suggested Next Work Orders

Suggested future micro work orders, not to be executed by this document:

- G140: Add backend contract tests for MT4 Demo readonly bridge activation.
- G141: Add stale, malformed, and missing file fixture tests.
- G142: Add path injection and forbidden source activation safety tests.
- G143: Add internal config-only bridge directory fixture wiring while keeping
  the reader disabled by default.
- G144: Add finer-grained file bridge `error_safe` display states to the
  Dashboard.
- G145: Review the minimum MT4 Demo readonly file bridge implementation plan.

These work orders are proposals only. They do not grant permission to enable
the reader, read real MT4 files, connect MT4, connect an EA, or add trading
execution behavior.
