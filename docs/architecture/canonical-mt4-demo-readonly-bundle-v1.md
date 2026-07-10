# Canonical MT4 Demo Readonly Snapshot Bundle v1

Status: Accepted for G144 contract design

Scope: field-level protocol contract only. This document defines the canonical
MT4 Demo readonly snapshot bundle that future readers and writers must use. It
does not implement a reader, writer, API, dashboard, EA, MQL4 code, strategy,
risk engine, position sizing, execution gate, or trading workflow.

Related decisions:

- `docs/architecture/adr-001-canonical-mt4-demo-readonly-architecture.md`
- `docs/mt4_demo_readonly_bridge_preflight_contract.md`
- `docs/implementation_plans/mt4_demo_readonly_file_schemas.md`

## Non-negotiable Safety Meaning

The canonical bundle is a Demo-only, readonly data input for diagnostics and
readonly analysis.

It is not:

- a trading signal;
- a trading permission;
- an execution permission;
- an EA command;
- a position sizing result;
- a risk override;
- an account login artifact;
- a real account snapshot.

Every v1 file must preserve these safety flags:

| Field | Required value |
| --- | --- |
| `account_mode` | `demo_only` |
| `is_demo_account` | `true` |
| `is_live_account` | `false` |
| `read_only` | `true` |
| `demo_only` | `true` |
| `is_tradable` | `false` |
| `can_execute` | `false` |
| `is_trading_permission` | `false` |
| `is_execution_instruction` | `false` |
| `allowed_to_call_ea` | `false` |
| `allowed_to_modify_risk` | `false` |
| `contains_credentials` | `false` |
| `contains_password` | `false` |
| `contains_live_account` | `false` |

If any file conflicts with these values, the whole bundle must fail closed.

## Canonical v1 Bundle Boundary

The canonical v1 bundle consists of exactly one manifest and four required
payload files:

| File | Role | Required in v1 |
| --- | --- | --- |
| `snapshot_manifest.json` | Bundle commit marker and payload index | Yes |
| `live_tick.json` | Latest readonly quote snapshot | Yes |
| `latest_bars.json` | Latest readonly M15, H1, H4, D1 bar snapshots | Yes |
| `symbol_spec.json` | Readonly symbol specification and contract metadata | Yes |
| `account_snapshot.json` | Readonly Demo account balance and margin snapshot | Yes |

`positions_order_history.json` is reserved for a future extension. In v1:

- it is not required;
- it is not part of the canonical required bundle;
- `optional_files` must be an empty array;
- its absence must not block a v1 bundle;
- a canonical v1 writer should not publish it as a formal bundle component;
- this document does not define its fields.

## Common Payload Envelope

Each payload file and the manifest must be a JSON object encoded as UTF-8
without a byte-order mark. The following common envelope fields are required in
every file.

| Field | Type | Required value or rule |
| --- | --- | --- |
| `schema_version` | string | `1.0` |
| `file_type` | string | One of the canonical file types for the current file |
| `bundle_id` | string | Same value across all files in one bundle |
| `sequence` | integer | Same monotonic positive integer across all files in one bundle |
| `generated_at_utc` | string | UTC timestamp in `YYYY-MM-DDTHH:MM:SSZ` format |
| `source_id` | string | Stable non-sensitive source label, not a local path |
| `source_mode` | string | `mt4_demo_readonly_file_bridge_enabled` |
| `writer_version` | string | Non-sensitive writer version label |
| `terminal_id_masked` | string | Masked or synthetic Demo terminal identifier |
| `account_mode` | string | `demo_only` |
| `is_demo_account` | boolean | `true` |
| `is_live_account` | boolean | `false` |
| `read_only` | boolean | `true` |
| `demo_only` | boolean | `true` |
| `is_tradable` | boolean | `false` |
| `can_execute` | boolean | `false` |
| `is_trading_permission` | boolean | `false` |
| `is_execution_instruction` | boolean | `false` |
| `allowed_to_call_ea` | boolean | `false` |
| `allowed_to_modify_risk` | boolean | `false` |
| `contains_credentials` | boolean | `false` |
| `contains_password` | boolean | `false` |
| `contains_live_account` | boolean | `false` |
| `note` | string | Must state readonly, Demo-only, not trading advice, not trading permission |

Forbidden fields at any depth include:

- credential fields: `password`, `token`, `secret`, `api_key`, `login`,
  `account_number`;
- path fields: `path`, `base_dir`, `candidate_path`, `bridge_dir`,
  `absolute_path`, `traceback`;
- execution fields: `ea_command`, `execute_trade`, `order_send`,
  `order_close`, `order_modify`, `order_delete`, `ticket`, `order_id`;
- trading decision fields: `can_trade`, `allow_trade`, `should_buy`,
  `should_sell`, `buy_now`, `sell_now`, `suggested_lot`, `final_lot`,
  `open_position`, `close_position`, `trade_signal`, `trading_action`,
  `override_risk`, `bypass_gate`.

If a future reader encounters any forbidden field, it must fail closed and must
not reflect the unsafe field or value in a public API response.

## `snapshot_manifest.json`

The manifest is the only canonical bundle commit marker. It must be written
last.

### Required Fields

In addition to the common envelope, `snapshot_manifest.json` must contain:

| Field | Type | Rule |
| --- | --- | --- |
| `file_type` | string | `snapshot_manifest` |
| `bundle_version` | string | `1.0` |
| `writer_heartbeat_utc` | string | UTC timestamp for latest writer heartbeat |
| `publish_started_at_utc` | string | UTC timestamp before payload publish starts |
| `published_at_utc` | string | UTC timestamp after all payload files are replaced |
| `commit_state` | string | `complete` |
| `required_files` | array[string] | Exactly the four required payload filenames |
| `optional_files` | array | Must be empty in v1 |
| `payloads` | object | One entry per required payload file |
| `freshness_thresholds_seconds` | object | Per-file freshness thresholds |
| `file_size_limits_bytes` | object | Per-file byte limits |
| `max_total_bundle_bytes` | integer | Whole-bundle byte limit |
| `checksum_policy` | object | v1 checksum decision |

Each `payloads` entry must contain:

| Field | Type | Rule |
| --- | --- | --- |
| `file_type` | string | Expected payload file type |
| `schema_version` | string | `1.0` |
| `bundle_id` | string | Same as manifest `bundle_id` |
| `sequence` | integer | Same as manifest `sequence` |
| `generated_at_utc` | string | Expected payload generation timestamp |
| `max_age_seconds` | integer | Freshness threshold for that payload |
| `max_size_bytes` | integer | Maximum file size for that payload |

### Freshness Baseline

The canonical v1 baseline is:

| File | Maximum age |
| --- | --- |
| `live_tick.json` | 10 seconds |
| `latest_bars.json` | 60 seconds |
| `symbol_spec.json` | 86400 seconds |
| `account_snapshot.json` | 30 seconds |

The writer heartbeat is advisory for source liveness. A stale heartbeat must
make the source not ready for readonly analysis. It must not create trading
permission.

### File Size Limits

| File | Maximum bytes |
| --- | --- |
| `snapshot_manifest.json` | 32768 |
| `live_tick.json` | 16384 |
| `latest_bars.json` | 262144 |
| `symbol_spec.json` | 32768 |
| `account_snapshot.json` | 32768 |

`max_total_bundle_bytes` is `524288`.

### Checksum Decision

v1 does not require a cryptographic checksum to accept a bundle. The manifest
must state:

```json
{
  "algorithm": "none",
  "checksum_required": false,
  "if_present_reader_must_verify": true
}
```

If a future writer adds checksum fields before a new protocol version is
approved, a reader may ignore absent checksums, but any present checksum that is
malformed or mismatched must fail closed.

## `live_tick.json`

Purpose: latest readonly XAUUSD quote snapshot.

Required body fields:

| Field | Type | Rule |
| --- | --- | --- |
| `symbol` | string | `XAUUSD` |
| `server_time_utc` | string | UTC timestamp |
| `bid` | number | Finite positive number |
| `ask` | number | Finite positive number, `ask >= bid` |
| `spread` | number | Finite number, `spread >= 0` |
| `spread_points` | number | Finite number, `spread_points >= 0` |
| `digits` | integer | Positive integer |
| `point` | number | Finite positive number |
| `tick_time_msc` | integer | Positive Unix epoch milliseconds |

The quote is a data snapshot only. It is not a market order, signal, or
permission to trade.

## `latest_bars.json`

Purpose: latest readonly bar snapshots for multiple timeframes.

Required body fields:

| Field | Type | Rule |
| --- | --- | --- |
| `symbol` | string | `XAUUSD` |
| `required_timeframes` | array[string] | Exactly `M15`, `H1`, `H4`, `D1` |
| `timeframes` | object | Must contain `M15`, `H1`, `H4`, `D1` |

Each timeframe object must contain:

| Field | Type | Rule |
| --- | --- | --- |
| `timeframe` | string | Same as the object key |
| `bar_count` | integer | Positive integer |
| `bars` | array[object] | Non-empty array |

Each bar object must contain:

| Field | Type | Rule |
| --- | --- | --- |
| `bar_open_time_utc` | string | UTC timestamp |
| `open_price` | number | Finite positive number |
| `high_price` | number | Finite positive number |
| `low_price` | number | Finite positive number |
| `close_price` | number | Finite positive number |
| `tick_volume` | number | Finite number, `>= 0` |
| `spread_points` | number | Finite number, `>= 0` |
| `is_closed` | boolean | Whether the bar is closed |

For each bar, `high_price >= max(open_price, close_price, low_price)` and
`low_price <= min(open_price, close_price, high_price)`.

## `symbol_spec.json`

Purpose: readonly XAUUSD symbol specification and contract metadata.

Required body fields:

| Field | Type | Rule |
| --- | --- | --- |
| `symbol` | string | `XAUUSD` |
| `digits` | integer | Positive integer |
| `point` | number | Finite positive number |
| `tick_size` | number | Finite positive number |
| `tick_value` | number | Finite positive number |
| `lot_size` | number | Finite positive number |
| `min_lot` | number | Finite positive number |
| `lot_step` | number | Finite positive number |
| `max_lot` | number | Finite number, `max_lot >= min_lot` |
| `margin_required_per_lot` | number | Finite non-negative number |
| `stop_level_points` | number | Finite non-negative number |
| `freeze_level_points` | number | Finite non-negative number |
| `profit_currency` | string | Non-empty string |
| `margin_currency` | string | Non-empty string |
| `trade_allowed_by_broker` | boolean | Broker metadata only, not system permission |

`trade_allowed_by_broker` must never be interpreted as system trading
permission.

## `account_snapshot.json`

Purpose: readonly Demo account balance, equity, and margin snapshot.

Required body fields:

| Field | Type | Rule |
| --- | --- | --- |
| `account_currency` | string | Non-empty string, example `USD` |
| `account_identifier_masked` | string | Masked or synthetic label only |
| `balance` | number | Finite non-negative number |
| `equity` | number | Finite non-negative number |
| `margin` | number | Finite non-negative number |
| `free_margin` | number | Finite non-negative number |
| `margin_level_pct` | number or null | Finite non-negative number when present |
| `daily_realized_pnl` | number | Finite number |
| `daily_unrealized_pnl` | number | Finite number |
| `daily_loss_pct` | number | Finite non-negative number |
| `open_positions_count` | integer | Non-negative integer |
| `pending_orders_count` | integer | Non-negative integer |
| `risk_limits` | object | Readonly limits for future gates |

`risk_limits` must contain:

| Field | Type | Rule |
| --- | --- | --- |
| `max_single_trade_loss_pct` | number | Finite positive number, baseline `1.0` |
| `max_daily_loss_pct` | number | Finite positive number, baseline `3.0` |
| `no_overnight` | boolean | `true` |
| `primary_session` | string | Baseline `Asia` |
| `leverage_cap` | number | Baseline `10` |

The account snapshot must not contain account login, password, real account
number, order ticket, order history, or position details.

## Bundle Identity and Sequence Rules

`bundle_id` is the unique identity of one coherent snapshot generation. It must
be a non-sensitive string, for example:

`mt4-demo-readonly-20260710T023000Z-000001`

Rules:

- every file in one bundle must have the same `bundle_id`;
- every file in one bundle must have the same `sequence`;
- `sequence` must be a positive integer;
- a later successful bundle must have a higher `sequence`;
- sequence rollback must fail closed;
- duplicate sequence with a different `bundle_id` must fail closed;
- a sequence gap may produce a warning, but must not block by itself when the
  current bundle is coherent, fresh, and otherwise valid.

## UTC Time Rules

All protocol timestamps must be UTC strings ending in `Z`. Local time fields are
not part of canonical v1. A future reader may reject:

- missing timestamps;
- timestamps without `Z`;
- future skew beyond the reader tolerance;
- stale timestamps beyond the per-file freshness threshold;
- mixed `generated_at_utc` values that do not match the manifest payload index.

## Demo-only and Live Conflict Rules

Any one of the following conflicts must block the whole bundle:

- `account_mode` is not `demo_only`;
- `is_demo_account` is not `true`;
- `is_live_account` is not `false`;
- `demo_only` is not `true`;
- `read_only` is not `true`;
- `contains_live_account` is not `false`;
- any account number, login, password, credential, token, or API key appears;
- any field claims trading or execution permission.

## Writer Publish Protocol

The canonical writer protocol is manifest-last atomic publish:

1. Build all payload JSON objects for one `bundle_id` and `sequence`.
2. Write each payload to a temporary file such as `live_tick.tmp`.
3. Atomically replace each payload `.json` file.
4. Build `snapshot_manifest.json` after payload replacement.
5. Write `snapshot_manifest.tmp`.
6. Atomically replace `snapshot_manifest.json` last.

The manifest is the commit marker. A reader must not treat payload files as a
complete bundle without a valid manifest.

## Reader Consistency Protocol

A future reader must use a double-manifest-read strategy:

1. Read `snapshot_manifest.json` as M1.
2. Validate M1 envelope, safety flags, required files, file sizes, and commit
   state.
3. Read all required payload files.
4. Validate each payload envelope and field rules.
5. Read `snapshot_manifest.json` again as M2.
6. Confirm M1 and M2 have the same `bundle_id`, `sequence`,
   `published_at_utc`, `required_files`, and payload index.
7. Accept only if the manifest is stable and every required payload belongs to
   the same bundle.

If the manifest changes during the read, the reader must retry a bounded number
of times or fail closed. It must not publish partial diagnostics as ready.

## Fail-closed Conditions

The bundle must be considered not ready for readonly analysis if any of these
conditions occurs:

- missing manifest;
- invalid JSON;
- non-object JSON;
- missing required file;
- missing required field;
- unsafe safety flag;
- forbidden field;
- mismatched `bundle_id`;
- mismatched `sequence`;
- mismatched `schema_version`;
- mismatched `file_type`;
- stale file;
- writer heartbeat stale;
- sequence rollback;
- duplicate sequence with different `bundle_id`;
- payload file exceeds size limit;
- whole bundle exceeds size limit;
- manifest changes during double read;
- payload field quality check fails.

Failing closed means:

- no reader readiness;
- no readonly analysis readiness;
- no trading permission;
- no execution permission;
- no EA command;
- no trading advice.

## Schema Version Compatibility

Canonical v1 accepts only `schema_version = "1.0"` and `bundle_version = "1.0"`.
Unknown versions, missing versions, or incompatible major/minor versions must
fail closed until a new ADR explicitly defines compatibility.

## JSON and Numeric Rules

- JSON encoding must be UTF-8 without BOM.
- Top-level value must be an object.
- Numbers must be finite JSON numbers.
- `NaN`, `Infinity`, and stringified numbers are invalid.
- Boolean safety flags must be JSON booleans, not strings.
- Timestamps must be UTC strings with `Z`.
- Public API responses derived from this bundle must not include raw payloads,
  local file paths, tracebacks, credentials, or execution fields.

## Future Implementation Notes

Future work may implement a reader, contract tests, dashboard mapping, or
source-mode activation. Those future changes must preserve this contract.

This G144 contract still does not implement:

- MT4 reader activation;
- writer or EA code;
- MQL4;
- backend API changes;
- frontend dashboard changes;
- explanation API integration;
- source-mode controls;
- `RiskGate`, `PositionSizing`, `ExecutionGate`, or `TradePlanSchema`;
- Agent or LLM execution;
- automatic trading;
- Demo order execution;
- live trading.
