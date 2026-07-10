# Canonical MT4 Demo Readonly Snapshot Bundle v1

Status: Accepted for G144-R1 contract design

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
readonly analysis. It contains account and market facts supplied by the MT4
writer. It does not contain server policy.

It is not:

- a trading signal or trading plan;
- trading or execution permission;
- an EA command;
- a position sizing result;
- a risk policy or risk override;
- an account login artifact;
- a live account snapshot.

Every v1 file must preserve these safety values:

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

If any file conflicts with these values, the whole bundle must fail closed.
Readiness only means that the data may proceed to readonly analysis. It never
means that trading or execution is permitted.

## Writer Facts and Server Policy

The MT4 writer may publish only observed Demo account facts, observed market
facts, bundle identity, and the fixed safety envelope. It must not declare,
select, or override server policy.

The following are server-side policy and must not appear in the manifest or any
payload:

- per-trade loss limit, including the project baseline of 1 percent;
- daily loss limit, including the project baseline of 3 percent;
- no-overnight policy;
- primary session policy, including the Asia-session preference;
- permitted leverage cap, including the project ceiling of 10x;
- freshness and future-skew thresholds;
- file-size limits.

Future typed settings, Risk Policy, and program gates own those decisions. A
writer-reported `leverage` value is an observed MT4 account fact only. It is not
the leverage that the system permits.

## Canonical v1 Bundle Boundary

The canonical v1 bundle consists of exactly one manifest and four required
payload files:

| File | Role | Required in v1 |
| --- | --- | --- |
| `snapshot_manifest.json` | Bundle commit marker and payload index | Yes |
| `live_tick.json` | Latest readonly quote snapshot | Yes |
| `latest_bars.json` | Completed M15, H1, H4, and D1 bar snapshots | Yes |
| `symbol_spec.json` | Readonly symbol and contract facts | Yes |
| `account_snapshot.json` | Readonly Demo account and margin facts | Yes |

`positions_order_history.json` is reserved for a future extension. In v1:

- it is not required;
- it is not a canonical v1 bundle component;
- `optional_files` must be an empty array;
- its absence must not block a v1 bundle;
- a canonical v1 writer must not publish it as a formal bundle component until
  an independent extension contract is accepted;
- this document does not define its fields.

## Common Payload Envelope

Each of the four payload files must be a JSON object encoded as UTF-8 without a
byte-order mark. Each payload has exactly these common envelope fields before
its payload-specific fields:

| Field | Type | Required value or rule |
| --- | --- | --- |
| `schema_version` | string | `1.0` |
| `file_type` | string | Canonical file type for the current payload |
| `bundle_id` | string | Same value across every file in the bundle |
| `sequence` | integer | Same monotonic positive integer across every file |
| `generated_at_utc` | string | UTC timestamp ending in `Z` |
| `source_id` | string | `trademax_mt4_demo_readonly_bridge` |
| `writer_version` | string | Non-sensitive writer version label |
| `terminal_id_masked` | string | Masked or synthetic Demo terminal label |
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

The payload envelope does not carry source-selection state, credential
assertions, live-account assertions, free-form notes, freshness policy, size
policy, or risk policy. Source selection and policy remain server-side.

Forbidden fields at any depth include:

- credentials and account identifiers: `password`, `token`, `secret`,
  `api_key`, `login`, `account_number`;
- local paths and internals: `path`, `base_dir`, `candidate_path`, `bridge_dir`,
  `absolute_path`, `traceback`;
- execution fields: `ea_command`, `execute_trade`, `order_send`, `order_close`,
  `order_modify`, `order_delete`, `ticket`, `order_id`;
- trading-decision fields: `can_trade`, `allow_trade`, `should_buy`,
  `should_sell`, `buy_now`, `sell_now`, `suggested_lot`, `final_lot`,
  `open_position`, `close_position`, `trade_signal`, `trading_action`,
  `override_risk`, `bypass_gate`;
- writer-owned policy containers, percentage limits, session restrictions,
  overnight restrictions, leverage ceilings, or derived daily-loss ratios.

A future reader must fail closed on any forbidden field and must not reflect
the unsafe field or value in a public API response.

## `snapshot_manifest.json`

The manifest is a JSON object and the only canonical bundle commit marker. It
is not a payload and therefore does not use `file_type` or the common payload
envelope.

### Required Fields

| Field | Type | Required value or rule |
| --- | --- | --- |
| `schema_version` | string | `1.0` |
| `manifest_type` | string | `mt4_demo_readonly_snapshot_manifest` |
| `bundle_id` | string | Same value as all required payloads |
| `sequence` | integer | Same value as all required payloads |
| `generated_at_utc` | string | UTC time the manifest data was assembled |
| `committed_at_utc` | string | UTC time the manifest was committed last |
| `writer_heartbeat_at_utc` | string | Latest writer heartbeat in UTC |
| `source_id` | string | `trademax_mt4_demo_readonly_bridge` |
| `writer_version` | string | Same value as all required payloads |
| `terminal_id_masked` | string | Same masked label as all payloads |
| `account_mode` | string | `demo_only` |
| `is_demo_account` | boolean | `true` |
| `is_live_account` | boolean | `false` |
| `canonical_symbol` | string | `XAUUSD` |
| `broker_symbol` | string | `GOLD` for this contract example |
| `commit_state` | string | `complete` |
| `required_files` | array[object] | Exactly four descriptors defined below |
| `optional_files` | array | Empty array in v1 |
| `compatible_reader_schema_versions` | array[string] | Exactly `["1.0"]` |
| `read_only` | boolean | `true` |
| `demo_only` | boolean | `true` |
| `is_tradable` | boolean | `false` |
| `can_execute` | boolean | `false` |
| `is_trading_permission` | boolean | `false` |
| `is_execution_instruction` | boolean | `false` |
| `allowed_to_call_ea` | boolean | `false` |
| `allowed_to_modify_risk` | boolean | `false` |

`required_files` must contain exactly one descriptor for each payload, in this
canonical order:

1. `live_tick.json`
2. `latest_bars.json`
3. `symbol_spec.json`
4. `account_snapshot.json`

Each descriptor contains only:

| Field | Type | Rule |
| --- | --- | --- |
| `filename` | string | Exact canonical filename |
| `file_type` | string | Matching canonical payload type |
| `schema_version` | string | `1.0` |
| `content_sha256` | string or null | `null` in the v1 example |

Canonical v1 does not require a checksum. A null `content_sha256` is valid. If
a future compatible writer supplies a non-null checksum, it must be a
lowercase 64-character hexadecimal SHA-256 digest and the reader must verify
it before accepting the payload.

The manifest must not carry payload copies, payload metadata maps, freshness
thresholds, file-size limits, total-bundle limits, source selection, checksum
policy objects, free-form notes, or risk policy.

## Server-side Read Policy Defaults

Freshness, future-skew tolerance, and file-size limits are server-side typed
configuration. They are not writer input and are not client input. Neither a
writer nor an API query, header, or body may modify or override them.

### Freshness Defaults

| Check | Server default | Canonical timestamp |
| --- | --- | --- |
| Writer heartbeat | 15 seconds | `writer_heartbeat_at_utc` |
| `live_tick.json` | 10 seconds | `tick_time_utc` |
| `latest_bars.json` | 60 seconds | payload `generated_at_utc` |
| `symbol_spec.json` | 86400 seconds | `spec_time_utc` |
| `account_snapshot.json` | 30 seconds | `snapshot_time_utc` |
| Future skew | 5 seconds | Every canonical UTC timestamp |

An exceeded threshold makes the source not ready for readonly analysis. It
does not create any trading or execution meaning.

### File-size Defaults

| File | Maximum bytes |
| --- | --- |
| `snapshot_manifest.json` | 65536 |
| `live_tick.json` | 32768 |
| `latest_bars.json` | 2097152 |
| `symbol_spec.json` | 65536 |
| `account_snapshot.json` | 131072 |

A file over its server-side limit must fail closed. The manifest and payloads
must not carry values that claim to raise or lower these limits.

## `live_tick.json`

Purpose: latest readonly XAUUSD/GOLD quote facts.

In addition to the common payload envelope, it contains only:

| Field | Type | Rule |
| --- | --- | --- |
| `canonical_symbol` | string | `XAUUSD` |
| `broker_symbol` | string | `GOLD` |
| `bid` | number | Finite positive number |
| `ask` | number | Finite positive number and `ask >= bid` |
| `spread` | number | Finite number and `spread >= 0` |
| `spread_points` | integer | Non-negative integer |
| `digits` | integer | Non-negative integer |
| `point` | number | Finite positive number |
| `tick_time_utc` | string | UTC timestamp ending in `Z` |

The quote is a data snapshot only. It is not a market order, signal, or
permission to trade.

## `latest_bars.json`

Purpose: completed readonly bars for M15, H1, H4, and D1.

In addition to the common payload envelope, it contains only:

| Field | Type | Rule |
| --- | --- | --- |
| `canonical_symbol` | string | `XAUUSD` |
| `broker_symbol` | string | `GOLD` |
| `timeframes` | array[object] | Exactly one object for each required timeframe |

Each timeframe object contains only:

| Field | Type | Rule |
| --- | --- | --- |
| `timeframe` | string | One of `M15`, `H1`, `H4`, `D1` |
| `period_seconds` | integer | Fixed mapping below |
| `bar_count` | integer | Number of entries in `bars`, from 1 through 500 |
| `bars` | array[object] | Completed bars in strict ascending time order |

The fixed timeframe mapping is:

| Timeframe | `period_seconds` |
| --- | ---: |
| `M15` | 900 |
| `H1` | 3600 |
| `H4` | 14400 |
| `D1` | 86400 |

Each bar contains only:

| Field | Type | Rule |
| --- | --- | --- |
| `open_time_utc` | string | UTC timestamp ending in `Z` |
| `open` | number | Finite positive number |
| `high` | number | Finite positive number |
| `low` | number | Finite positive number |
| `close` | number | Finite positive number |
| `tick_volume` | integer | Non-negative integer |
| `spread_points` | integer | Non-negative integer |

Only completed bars are allowed. There is no completion-state field in v1; a
writer must omit an in-progress bar. For every bar,
`high >= max(open, close, low)` and `low <= min(open, close, high)`. Bar times
must be strictly increasing within each timeframe, and `bar_count` must equal
the array length.

## `symbol_spec.json`

Purpose: readonly XAUUSD/GOLD symbol and contract facts.

In addition to the common payload envelope, it contains only:

| Field | Type | Rule |
| --- | --- | --- |
| `canonical_symbol` | string | `XAUUSD` |
| `broker_symbol` | string | `GOLD` |
| `spec_time_utc` | string | UTC timestamp ending in `Z` |
| `digits` | integer | Non-negative integer |
| `point` | number | Finite positive number |
| `tick_size` | number | Finite positive number |
| `tick_value` | number | Finite positive number |
| `contract_size` | number | Finite positive number |
| `min_lot` | number | Finite positive number |
| `lot_step` | number | Finite positive number |
| `max_lot` | number | Finite number and `max_lot >= min_lot` |
| `base_currency` | string | `XAU` |
| `profit_currency` | string | `USD` |
| `margin_currency` | string | Non-empty currency code |
| `trade_mode_readonly_label` | string | Observed metadata label only |
| `session_status_readonly_label` | string | Observed metadata label only |

The two readonly labels must not be interpreted as system trading permission.
They cannot override a gate, risk policy, or execution policy.

## `account_snapshot.json`

Purpose: readonly Demo account and margin facts.

In addition to the common payload envelope, it contains only:

| Field | Type | Rule |
| --- | --- | --- |
| `snapshot_time_utc` | string | UTC timestamp ending in `Z` |
| `account_alias_masked` | string | Masked or synthetic label only |
| `server_name_masked` | string | Masked or synthetic label only |
| `account_currency` | string | Non-empty currency code |
| `balance` | number | Finite non-negative number |
| `equity` | number | Finite non-negative number |
| `margin` | number | Finite non-negative number |
| `free_margin` | number | Finite number |
| `margin_level` | number or null | Finite non-negative number when present |
| `leverage` | number | Finite positive observed MT4 account fact |
| `positions_count` | integer | Non-negative integer |
| `pending_orders_count` | integer | Non-negative integer |
| `daily_realized_pnl` | number | Finite number |
| `daily_floating_pnl` | number | Finite number |

`leverage` is descriptive account data. It is not the system leverage cap and
cannot authorize exposure. The account snapshot must not contain account
login, password, real account number, order tickets, order history, position
details, or server-side risk policy.

## Bundle Identity and Sequence Rules

`bundle_id` is a non-sensitive identity for one coherent publication. Every
manifest and payload in that publication must share it. The example uses
`demo-bundle-000000000001`.

Rules:

- every file in one bundle must have the same `bundle_id` and `sequence`;
- `sequence` must be a positive integer;
- a later successful publication must use a higher sequence;
- sequence rollback must fail closed;
- the same sequence with a different bundle ID must fail closed;
- a sequence gap may warn but does not fail by itself when the current bundle
  is coherent, fresh, and otherwise valid.

## UTC Time Rules

All canonical timestamps must be UTC strings ending in `Z`. Local-time fields
are not part of canonical v1. Missing, malformed, stale, or excessive
future-skew timestamps must fail closed according to server-side policy.

Within one coherent publication:

- `generated_at_utc` identifies when each object was generated;
- `committed_at_utc` identifies the manifest commit event and must not precede
  the manifest `generated_at_utc`;
- `writer_heartbeat_at_utc` is a writer-liveness fact, not a permission;
- payload-specific timestamps identify the observed fact represented by that
  payload.

## Demo-only and Live Conflict Rules

Any one of the following conflicts blocks the whole bundle:

- `account_mode` is not `demo_only`;
- `is_demo_account` is not `true`;
- `is_live_account` is not `false`;
- `demo_only` is not `true`;
- `read_only` is not `true`;
- any account number, login, password, credential, token, or API key appears;
- any field claims trading, execution, EA-call, or risk-modification permission.

## Manifest-last Atomic Publish

The canonical writer protocol is:

1. Build all four payload objects for one `bundle_id` and `sequence`.
2. Place every temporary file in the same directory and on the same filesystem
   volume as its final file.
3. Write each payload completely to its `.tmp` file, flush as required, and
   close the file handle.
4. Atomically replace each final payload `.json` file.
5. Build the complete manifest only after all payload replacements succeed.
6. Write `snapshot_manifest.tmp` completely, flush as required, and close its
   handle.
7. Atomically replace `snapshot_manifest.json` last.

Readers must ignore `.tmp` files. `snapshot_manifest.json` is the unique commit
marker. Payload files without a valid, complete manifest never form an
acceptable bundle.

## Double-manifest-read Consistency

A future reader must:

1. Read and validate `snapshot_manifest.json` as Manifest A.
2. Read and validate all four descriptors and payloads.
3. Read and validate `snapshot_manifest.json` again as Manifest B.
4. Compare A and B for exact equality of `bundle_id`, `sequence`,
   `committed_at_utc`, `required_files`, and `commit_state`.
5. Accept the bundle only when both manifests are stable and all payloads match
   the manifest identity, schema, type, and safety contract.

On an A/B mismatch, the reader may perform at most one bounded retry of the
whole read. A second mismatch, any retry failure, or any incomplete read must
fail closed. The reader must not publish partial diagnostics as ready.

## Fail-closed Conditions

The bundle is not ready for readonly analysis when any of these occurs:

- missing manifest or required payload;
- invalid or non-object JSON;
- missing, extra, duplicated, or malformed descriptor;
- `commit_state` is not `complete`;
- missing required field, forbidden field, or unsafe safety value;
- mismatched `bundle_id`, `sequence`, `schema_version`, or `file_type`;
- canonical/broker symbol mismatch;
- stale data, stale heartbeat, or excessive future skew;
- sequence rollback or same sequence with a different bundle ID;
- a file exceeds the server-side size limit;
- an invalid or mismatched non-null checksum;
- manifest A/B instability after one bounded retry;
- payload field, numeric, bar-order, or cross-field validation failure;
- any partial write or mixed-generation evidence.

Failing closed means no source readiness, no readonly-analysis readiness, no
trading permission, no execution permission, no EA call, and no trading advice.

## Schema Version Compatibility

Canonical v1 accepts only `schema_version = "1.0"`. The manifest must declare
`compatible_reader_schema_versions = ["1.0"]`. Unknown or missing versions
must fail closed until a new accepted contract explicitly defines
compatibility. `schema_version` is the sole v1 protocol-version discriminator.

## JSON and Numeric Rules

- JSON encoding must be UTF-8 without BOM.
- Every top-level value must be an object.
- Numbers must be finite JSON numbers; `NaN`, `Infinity`, and stringified
  numbers are invalid.
- Integer fields must be JSON integers, not fractional values or strings.
- Boolean safety values must be JSON booleans, not strings.
- Canonical timestamps must be strings ending in `Z` and parse as UTC.
- Object keys required by this contract must be unique.
- Public API responses derived from this bundle must not include raw payloads,
  local paths, tracebacks, credentials, execution fields, or writer policy.

## Future Implementation Notes

Future work may implement a reader, writer contract tests, dashboard mapping,
or source-mode activation. Those changes must preserve this contract.

G144-R1 still does not implement:

- reader activation or MT4 file access;
- writer, EA, or MQL4 code;
- backend API or frontend changes;
- endpoint migration or Dashboard integration;
- SourceConfigGuard or DataQualityGate changes;
- `RiskGate`, `PositionSizing`, `ExecutionGate`, or `TradePlanSchema`;
- Agent or LLM execution;
- automatic, Demo, or live trading.
