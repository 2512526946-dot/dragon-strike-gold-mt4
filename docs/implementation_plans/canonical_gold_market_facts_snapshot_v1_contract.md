# Canonical Gold Market Facts Snapshot v1 Contract

Status: Accepted design candidate for G175

Maturity effect: W6 contract maintenance only. W6 remains `CONTRACT_ONLY`.

This document defines the future internal, deterministic, read-only projection
boundary between one fully validated Canonical MT4 Demo Readonly Bundle v1 and
the later W6 facts and feature stages. It does not implement that boundary.

## 1. Purpose

W1 defines canonical writer facts and validation. W5 v1 replays the safe
diagnostics chain. Neither capability currently exposes a typed market-facts
snapshot for W6:

- the canonical filesystem reader returns a safe validation envelope, not raw
  payloads;
- the DataQualityGate returns a safe readiness envelope, not raw payloads;
- G153 returns the G151 diagnostics summary; and
- the G151 summary intentionally strips bars, quotes, paths, payloads, and
  internal source state.

The G151 diagnostics summary is therefore not a W6 calculation input. W6 must
not reconstruct market facts from diagnostics status fields.

The first W6 boundary is an internal snapshot containing only normalized
XAUUSD/GOLD market and symbol facts from the same accepted canonical bundle
attempt. It is intended to become the immutable input to later, separately
contracted session, volatility, structure, and deterministic analysis stages.

## 2. Scope

This v1 contract defines:

- the authority that may create a validated source record;
- exact future source and result type fields and their order;
- safe projection of tick, completed bars, symbol specification, identity, and
  factual freshness ages;
- deterministic decimal normalization;
- exact status and reason mappings;
- fail-closed, immutable, detached result behavior; and
- Demo-only, Read-only, non-trading safety semantics.

This v1 contract does not define:

- a filesystem reader or a change to the existing reader result;
- a new DataQualityGate, parallel validator, or diagnostics adapter;
- an API, CLI, settings entry, source selector, background job, or cache;
- reader activation, runtime `data/` access, environment-variable input, or
  real MT4 access;
- account, position, order, PnL, balance, equity, margin, or credential facts;
- session classification, rollover rules, market-open policy, or news windows;
- ATR, realized volatility, trend, support, resistance, structure, momentum,
  opportunity, signal, recommendation, or invalidation logic;
- RiskGate, PositionSizing, TradePlan, Shadow Mode, ExecutionGate, EA, order,
  execution, or trading capability; or
- activation or verification of any W6 runtime capability.

## 3. Safety Meaning

A passed facts snapshot means only that one deterministic market-facts input is
safe for a later read-only analysis stage. It is not:

- a trading signal;
- a trade plan;
- risk approval;
- position-sizing approval;
- execution permission;
- an EA command;
- Demo execution approval; or
- Live activation approval.

Every result, including a blocked result, has these fixed values:

| Field | Value |
| --- | --- |
| `read_only` | `true` |
| `demo_only` | `true` |
| `is_tradable` | `false` |
| `can_execute` | `false` |
| `is_trading_permission` | `false` |
| `is_execution_instruction` | `false` |
| `allowed_to_call_ea` | `false` |
| `allowed_to_modify_risk` | `false` |

No status, reason, warning, identity, fact, or future feature may override these
values.

## 4. Authority and Ownership

### 4.1 Server-owned authority

The future source adapter is internal and server-owned. It must create one
`CanonicalGoldMarketFactsSourceV1` atomically from the same successful
canonical read and validation attempt, before raw payload objects are
discarded. Its evidence must prove all of the following:

1. the manifest and all four required payloads were accepted as one coherent
   canonical bundle;
2. canonical structure, value, freshness, filesystem, and DataQualityGate
   checks passed;
3. the DataQualityGate produced no warning;
4. the projected manifest, tick, bars, and symbol facts share the same bundle
   identity and symbol mapping;
5. the reference time and policy profile are server-owned; and
6. all fixed Demo-only and Read-only flags passed.

The existing reader and DataQualityGate envelopes do not bind a public payload
copy to their safe status. A future adapter must preserve same-attempt identity
internally. It must not combine a passed envelope from one attempt with payload
objects from another attempt.

The adapter, its tests, and its integration are separate future work. G175 does
not authorize their implementation.

### 4.2 Caller boundary

No API request, query, header, body, cookie, frontend state, plugin, environment
variable, working directory, or arbitrary service caller may provide or
override:

- a path or filename;
- a source mode;
- a reference time or clock;
- freshness or future-skew policy;
- canonical or broker symbol mapping;
- expected bundle identity;
- a validator, reader, Gate, dependency, or fallback;
- an expected outcome or oracle; or
- account, strategy, risk, execution, or trading state.

The future projector is an internal pure-memory service. Its typed source value
is caller-supplied only in the narrow Python dependency-injection sense; the
caller must be the separately approved server-owned adapter. The projector
must still validate the exact source type and every field. Type construction
alone is not authority.

### 4.3 Diagnostics boundary

The following are explicitly forbidden:

- treating a G151 summary as a market-facts source;
- adding raw payloads or bars to G151, G153, or either diagnostics API;
- calling the docs-fixture diagnostics producer to obtain market facts;
- recovering payloads from paths, reason codes, component statuses, or logs;
- silently appending W6 stages to ReplayRunner v1; and
- copying G148, G149, G151, G153, or shared-validator logic.

## 5. Future Pure Interface

The future production module may expose exactly one keyword-only projection
function:

```python
build_canonical_gold_market_facts_snapshot_v1(
    *,
    validated_source: CanonicalGoldMarketFactsSourceV1,
) -> CanonicalGoldMarketFactsSnapshotV1
```

Both types must be frozen and slotted dataclasses. Nested records must also be
frozen and slotted. The function must perform no filesystem, environment,
network, clock, settings, API, MT4, database, cache, logging, or process I/O.
It must not mutate its input and must return a fresh detached result on every
call.

The names above are contract names for future tests and implementation. They
do not claim that a module or import currently exists.

## 6. Source Type

`CanonicalGoldMarketFactsSourceV1` has exactly these fields in this order:

| Order | Field | Exact type | Authority |
| ---: | --- | --- | --- |
| 1 | `contract_version` | built-in `str` | Fixed `1.0` |
| 2 | `bundle_schema_version` | built-in `str` | Accepted manifest; fixed `1.0` |
| 3 | `bundle_id` | built-in `str` | Accepted manifest identity |
| 4 | `sequence` | built-in `int` | Accepted manifest identity |
| 5 | `canonical_symbol` | built-in `str` | Fixed `XAUUSD` |
| 6 | `broker_symbol` | built-in `str` | Fixed `GOLD` in v1 |
| 7 | `reference_time_utc` | built-in `str` | Server-owned validation attempt |
| 8 | `policy_profile_version` | built-in `str` | Server-owned fixed profile |
| 9 | `upstream_evidence` | `CanonicalGoldUpstreamEvidenceV1` | Same accepted attempt |
| 10 | `live_tick` | `CanonicalGoldTickSourceV1` | Accepted `live_tick.json` |
| 11 | `bars_generated_at_utc` | built-in `str` | Accepted `latest_bars.json` |
| 12 | `timeframes` | exact tuple of four `CanonicalGoldTimeframeSourceV1` | Accepted `latest_bars.json` |
| 13 | `symbol_spec` | `CanonicalGoldSymbolSpecSourceV1` | Accepted `symbol_spec.json` |

Subclasses are invalid. `bool` is not an `int`. Lists are not tuples. Missing,
extra, reordered, duplicate, aliased, case-changed, or unknown fields fail
closed.

`bundle_id` must be 16 through 64 ASCII characters and satisfy
`[A-Za-z0-9._-]+`, exactly preserving the W1 canonical rule. `sequence` must be
positive. `reference_time_utc` and `bars_generated_at_utc` must be strict UTC
`Z` timestamps. `policy_profile_version` is fixed to
`canonical_gold_market_facts_policy_v1`.

### 6.1 Upstream evidence

`CanonicalGoldUpstreamEvidenceV1` has exactly these fields in this order:

| Order | Field | Exact type | Exact value or rule |
| ---: | --- | --- | --- |
| 1 | `reader_passed` | built-in `bool` | Exactly `true` |
| 2 | `reader_status_code` | built-in `str` | `CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID` |
| 3 | `value_status_code` | built-in `str` | `CANONICAL_MT4_BUNDLE_V1_VALUE_VALID` |
| 4 | `data_quality_passed` | built-in `bool` | Exactly `true` |
| 5 | `data_quality_status_code` | built-in `str` | `CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED` |
| 6 | `ready_for_readonly_analysis` | built-in `bool` | Exactly `true` |
| 7 | `warning_codes` | exact built-in `tuple[str, ...]` | Exactly empty |
| 8 | `same_attempt_identity_bound` | built-in `bool` | Exactly `true` |

V1 deliberately rejects passed-with-warning upstream evidence. A later policy
may define specific warning handling through a separate contract. It must not
be inferred in the first implementation.

### 6.2 Tick source

`CanonicalGoldTickSourceV1` has exactly these fields in this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `bid` | built-in `int` or built-in `float` |
| 2 | `ask` | built-in `int` or built-in `float` |
| 3 | `spread` | built-in `int` or built-in `float` |
| 4 | `spread_points` | built-in `int` |
| 5 | `digits` | built-in `int` |
| 6 | `point` | built-in `int` or built-in `float` |
| 7 | `tick_time_utc` | built-in `str` |

The numeric values retain the canonical JSON meaning and must be finite.
`bool` and every numeric subclass are invalid. `tick_time_utc` is a strict UTC
`Z` timestamp. Cross-field rules from the canonical contract remain
mandatory.

### 6.3 Timeframe and bar source

`timeframes` is an exact built-in tuple containing exactly four
`CanonicalGoldTimeframeSourceV1` records. Their `timeframe` values are `M15`,
`H1`, `H4`, and `D1` in that order. Each record has exactly these fields in
this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `timeframe` | built-in `str` |
| 2 | `period_seconds` | built-in `int` |
| 3 | `bars` | exact built-in `tuple[CanonicalGoldBarSourceV1, ...]` |

The fixed period mapping remains `900`, `3600`, `14400`, and `86400` seconds.
Each `bars` value is non-empty and contains no more than 500 exact
`CanonicalGoldBarSourceV1` records. Each bar has exactly these fields in this
order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `open_time_utc` | built-in `str` |
| 2 | `open` | built-in `int` or built-in `float` |
| 3 | `high` | built-in `int` or built-in `float` |
| 4 | `low` | built-in `int` or built-in `float` |
| 5 | `close` | built-in `int` or built-in `float` |
| 6 | `tick_volume` | built-in `int` |
| 7 | `spread_points` | built-in `int` |

Bars must be completed, strictly ascending, unique, finite, and internally
consistent under the canonical Bundle v1 rules. Lists, mappings, iterators, and
subclassed containers are invalid source records.

### 6.4 Symbol source

`CanonicalGoldSymbolSpecSourceV1` has exactly these fields in this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `spec_time_utc` | built-in `str` |
| 2 | `digits` | built-in `int` |
| 3 | `point` | built-in `int` or built-in `float` |
| 4 | `tick_size` | built-in `int` or built-in `float` |
| 5 | `tick_value` | built-in `int` or built-in `float` |
| 6 | `contract_size` | built-in `int` or built-in `float` |
| 7 | `min_lot` | built-in `int` or built-in `float` |
| 8 | `lot_step` | built-in `int` or built-in `float` |
| 9 | `max_lot` | built-in `int` or built-in `float` |
| 10 | `base_currency` | built-in `str` |
| 11 | `profit_currency` | built-in `str` |
| 12 | `margin_currency` | built-in `str` |
| 13 | `trade_mode_readonly_label` | built-in `str` |
| 14 | `session_status_readonly_label` | built-in `str` |

All numeric fields must be finite, exact built-in `int` or `float` values;
`bool` and subclasses are invalid. `spec_time_utc` is a strict UTC `Z`
timestamp. The values retain their canonical contract meaning. The two
readonly labels are observed writer metadata only. They are not market-session
policy, broker-trade permission, system permission, or ExecutionGate evidence.

## 7. Result Type

`CanonicalGoldMarketFactsSnapshotV1` has exactly these fields in this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `contract_version` | built-in `str`, exactly `1.0` |
| 2 | `passed` | built-in `bool` |
| 3 | `status_code` | built-in `str` |
| 4 | `reason_codes` | built-in `tuple[str, ...]` |
| 5 | `warning_codes` | built-in `tuple[str, ...]` |
| 6 | `identity_available` | built-in `bool` |
| 7 | `bundle_schema_version` | built-in `str` or `None` |
| 8 | `bundle_id` | built-in `str` or `None` |
| 9 | `sequence` | built-in `int` or `None` |
| 10 | `canonical_symbol` | built-in `str` or `None` |
| 11 | `broker_symbol` | built-in `str` or `None` |
| 12 | `reference_time_utc` | built-in `str` or `None` |
| 13 | `quote` | `CanonicalGoldQuoteFactsV1` or `None` |
| 14 | `timeframes` | exact built-in tuple: four `CanonicalGoldTimeframeFactsV1` records when passed; empty when non-passed |
| 15 | `symbol_spec` | `CanonicalGoldSymbolFactsV1` or `None` |
| 16 | `freshness` | `CanonicalGoldFreshnessFactsV1` or `None` |
| 17 | `read_only` | built-in `bool` |
| 18 | `demo_only` | built-in `bool` |
| 19 | `is_tradable` | built-in `bool` |
| 20 | `can_execute` | built-in `bool` |
| 21 | `is_trading_permission` | built-in `bool` |
| 22 | `is_execution_instruction` | built-in `bool` |
| 23 | `allowed_to_call_ea` | built-in `bool` |
| 24 | `allowed_to_modify_risk` | built-in `bool` |

The output has no free-text field, notes field, path, filename, digest,
checksum, raw payload container, account field, exception field, traceback,
source status, validator detail, policy object, strategy field, risk field, or
execution field.

### 7.1 Quote facts

`CanonicalGoldQuoteFactsV1` has exactly these fields in this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `bid_decimal` | built-in `str` |
| 2 | `ask_decimal` | built-in `str` |
| 3 | `spread_decimal` | built-in `str` |
| 4 | `spread_points` | built-in `int` |
| 5 | `digits` | built-in `int` |
| 6 | `point_decimal` | built-in `str` |
| 7 | `tick_time_utc` | built-in `str` |

Decimal fields are built-in ASCII strings in fixed-point notation. They are
not binary floating-point values in the result.

### 7.2 Timeframe and bar facts

For `CANONICAL_GOLD_MARKET_FACTS_READY`, `timeframes` is an exact built-in tuple
containing exactly four `CanonicalGoldTimeframeFactsV1` records. Their
`timeframe` values are `M15`, `H1`, `H4`, and `D1` in that order. Each record
has exactly these fields in this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `timeframe` | built-in `str` |
| 2 | `period_seconds` | built-in `int` |
| 3 | `bars` | exact built-in `tuple[CanonicalGoldBarFactsV1, ...]` |

The exact `period_seconds` values are `900`, `3600`, `14400`, and `86400` in
the same order. Every `bars` tuple is non-empty, preserves the accepted source
order, and contains exact `CanonicalGoldBarFactsV1` records. Each bar has
exactly these fields in this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `open_time_utc` | built-in `str` |
| 2 | `open_decimal` | built-in `str` |
| 3 | `high_decimal` | built-in `str` |
| 4 | `low_decimal` | built-in `str` |
| 5 | `close_decimal` | built-in `str` |
| 6 | `tick_volume` | built-in `int` |
| 7 | `spread_points` | built-in `int` |

The snapshot does not add indicators, labels, classifications, or inferred
bar completion fields.

Every non-passed result uses the exact empty built-in tuple required by
Section 10. Any other tuple length, timeframe order, container type, or element
type fails closed.

### 7.3 Symbol facts

`CanonicalGoldSymbolFactsV1` has exactly these fields in this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `spec_time_utc` | built-in `str` |
| 2 | `digits` | built-in `int` |
| 3 | `point_decimal` | built-in `str` |
| 4 | `tick_size_decimal` | built-in `str` |
| 5 | `tick_value_decimal` | built-in `str` |
| 6 | `contract_size_decimal` | built-in `str` |
| 7 | `min_lot_decimal` | built-in `str` |
| 8 | `lot_step_decimal` | built-in `str` |
| 9 | `max_lot_decimal` | built-in `str` |
| 10 | `base_currency` | built-in `str` |
| 11 | `profit_currency` | built-in `str` |
| 12 | `margin_currency` | built-in `str` |
| 13 | `trade_mode_readonly_label` | built-in `str` |
| 14 | `session_status_readonly_label` | built-in `str` |

These are facts only. Lot fields do not calculate or authorize a lot size.

### 7.4 Freshness facts

`CanonicalGoldFreshnessFactsV1` has exactly these fields in this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `tick_age_microseconds` | built-in `int` |
| 2 | `bars_payload_age_microseconds` | built-in `int` |
| 3 | `symbol_spec_age_microseconds` | built-in `int` |

Each value is non-negative and derived from the server-owned reference time
and accepted source timestamp. The bars age uses
`bars_generated_at_utc`, not a bar open time. These values describe age only.
They do not carry thresholds, pass/fail policy, source readiness, session
permission, or trading permission.

Every nested source and result record named in Sections 6 and 7 must be the
exact frozen, slotted dataclass type specified by this contract. Subclasses,
mappings, lists, iterators, wrong tuple element types, and records with
missing, extra, duplicated, aliased, case-changed, or reordered fields fail
closed.

## 8. Deterministic Normalization

The future implementation must use exactly this decimal normalization
algorithm:

1. Accept a numeric source value only when `type(value) is int` or
   `type(value) is float`. Reject `bool`, subclasses, strings, all other
   numeric types, and a float for which `math.isfinite(value)` is false.
2. Convert the value exactly once with `Decimal(str(value))`. Do not use
   `Decimal(value)`, `repr(value)`, prior formatting, binary float arithmetic,
   a locale, or any alternate conversion path. Reject a non-finite Decimal and
   reject signed zero (`decimal_value.is_zero()` and
   `decimal_value.is_signed()`).
3. Perform Decimal arithmetic in a fresh local context with `prec=64`,
   `rounding=ROUND_HALF_EVEN`, `Emin=-999999`, `Emax=999999`, `capitals=1`,
   and `clamp=0`. Trap `InvalidOperation`, `DivisionByZero`, and `Overflow`.
   Disable every other trap. Clear all flags before every arithmetic operation
   and reject the source if any context flag is set afterward. The configured
   rounding mode never grants permission to round: `Inexact` or `Rounded` is
   always a failure.
4. Compute `price_quantum` exactly as `Decimal(1).scaleb(-digits)`. The exact
   converted tick `point` and symbol `point` must both equal this quantum, and
   tick and symbol `digits` must be equal. A price Decimal is representable
   only when its tuple exponent is greater than or equal to `-digits`; a value
   with more fractional places fails rather than being quantized.
5. The price fields are tick `bid`, `ask`, `spread`, and `point`; bar `open`,
   `high`, `low`, and `close`; and symbol `point` and `tick_size`. Emit each
   with `format(decimal_value, f".{digits}f")`. The output must contain exactly
   `digits` digits after the decimal point, including trailing zeroes, and no
   exponent or leading plus sign. When `digits` is zero, the output contains
   no decimal point.
6. For `tick_value`, `contract_size`, `min_lot`, `lot_step`, and `max_lot`,
   first use `format(decimal_value, "f")`, remove trailing zeroes only from the
   fractional part, and then remove a trailing decimal point. An exact zero is
   emitted as `0`; every other integral value has no decimal point. The output
   has no exponent, leading plus sign, or unnecessary trailing fractional
   zero. Field positivity and ordering rules remain those of Bundle v1.
7. Convert `spread_points` exactly once with `Decimal(str(spread_points))`.
   In the same exact Decimal context, require `spread == ask - bid` and
   `spread == spread_points_decimal * point`. Both comparisons are exact. No
   epsilon, tolerance, binary float operation, or value-changing conversion is
   permitted.
8. Any conversion, context, precision, scale, comparison, or formatting
   ambiguity fails closed. The projector must not round, sort, repair,
   substitute, retry, or use a fallback algorithm.

This is the only permitted normalization algorithm. Tick and symbol `digits`
and `point` must match, and no tolerance may convert an invalid source into a
passed facts snapshot.

Age values use parsed UTC instants and exact integer microseconds. A future
timestamp, sub-microsecond timestamp, malformed timestamp, negative age, or
overflow fails closed. The projector does not read the clock.

## 9. Status and Reason Mapping

Status and reason codes are finite uppercase ASCII identifiers no longer than
96 characters. Reason tuples are ordered, unique, and contain exactly one code
for every non-passed result.

| Status | `passed` | Exact reason |
| --- | --- | --- |
| `CANONICAL_GOLD_MARKET_FACTS_READY` | `true` | none |
| `CANONICAL_GOLD_MARKET_FACTS_INPUT_INVALID` | `false` | `GOLD_MARKET_FACTS_SOURCE_TYPE_INVALID` |
| `CANONICAL_GOLD_MARKET_FACTS_AUTHORITY_INVALID` | `false` | `GOLD_MARKET_FACTS_SOURCE_AUTHORITY_INVALID` |
| `CANONICAL_GOLD_MARKET_FACTS_UPSTREAM_BLOCKED` | `false` | `GOLD_MARKET_FACTS_UPSTREAM_NOT_READY` |
| `CANONICAL_GOLD_MARKET_FACTS_UPSTREAM_BLOCKED` | `false` | `GOLD_MARKET_FACTS_UPSTREAM_WARNINGS_REJECTED` |
| `CANONICAL_GOLD_MARKET_FACTS_IDENTITY_INVALID` | `false` | `GOLD_MARKET_FACTS_IDENTITY_INVALID` |
| `CANONICAL_GOLD_MARKET_FACTS_VALUE_INVALID` | `false` | `GOLD_MARKET_FACTS_TICK_INVALID` |
| `CANONICAL_GOLD_MARKET_FACTS_VALUE_INVALID` | `false` | `GOLD_MARKET_FACTS_BARS_INVALID` |
| `CANONICAL_GOLD_MARKET_FACTS_VALUE_INVALID` | `false` | `GOLD_MARKET_FACTS_SYMBOL_SPEC_INVALID` |
| `CANONICAL_GOLD_MARKET_FACTS_VALUE_INVALID` | `false` | `GOLD_MARKET_FACTS_FRESHNESS_INVALID` |
| `CANONICAL_GOLD_MARKET_FACTS_SAFE_FAILURE` | `false` | `GOLD_MARKET_FACTS_EXCEPTION_SANITIZED` |

`warning_codes` is always the exact empty tuple in v1. Unknown, additional,
duplicate, reordered, subclassed, or contradictory status/reason/warning
values are invalid.

Validation uses this deterministic first-failure priority:

1. source exact type and field shape;
2. source authority constants and server ownership;
3. upstream readiness and warnings;
4. bundle and symbol identity;
5. tick facts;
6. timeframe and bar facts;
7. symbol facts;
8. freshness facts; and
9. detached result construction.

An unexpected exception maps only to the sanitized safe-failure result. The
exception text must not be returned, logged by this boundary, or included in a
reason code.

## 10. Identity Availability and Empty Failures

Only `CANONICAL_GOLD_MARKET_FACTS_READY` may set
`identity_available=true`. A passed result contains all six identity fields and
all four fact sections.

Every non-passed result must set:

- `identity_available=false`;
- `bundle_schema_version=None`;
- `bundle_id=None`;
- `sequence=None`;
- `canonical_symbol=None`;
- `broker_symbol=None`;
- `reference_time_utc=None`;
- `quote=None`;
- `timeframes=()`;
- `symbol_spec=None`; and
- `freshness=None`.

Partial identity or partially projected facts must never escape. The projector
must construct a new ordinary failure object for each call.

## 11. Immutability and Isolation

The future implementation and tests must prove:

- the source record and every nested source record are unchanged after a call;
- the canonical fixture assets are unchanged before and after any separately
  approved integration test;
- the result, quote, each timeframe, each bar, symbol facts, freshness facts,
  and reason/warning tuples are detached immutable values;
- repeated calls with equal source values return equal results but fresh object
  identities;
- mutating a copied authoring payload cannot alter a completed result;
- no result contains a source mapping, raw list, path, checksum, or digest; and
- no ambient state can change the projection result.

The function must not retry, fallback, sort bars, repair key order, fill missing
facts, switch sources, call G153, call the docs producer, or invoke any API,
reader, Gate, adapter, strategy, Agent, or execution component.

## 12. WBS Boundaries

### W1

W1 remains the authority for the canonical Bundle v1 protocol and validation.
This contract does not replace or loosen W1.

### W5

W5 remains verified only for ReplayRunner v1 canonical diagnostics. A future
W6 replay stage requires a separate versioned contract, registry update,
vectors, implementation, integration evidence, and non-activating
verification. G175 does not change W5.

### W6

G175 closes only the facts-snapshot contract gap. It does not complete W6.
After this contract, W6 still lacks contract vectors, production projection,
integration evidence, feature fixtures, session facts, spread/freshness
features, volatility, structure, and economic-window inputs.

### W7 and later

No W7 opportunity assessment may be added to this snapshot. W8-W21 policy,
risk, sizing, plan, execution, audit, GoLiveGate, and activation work remain
separate and unimplemented unless independently evidenced.

## 13. Required Staged Delivery

Any later delivery must remain separately planned and approved:

1. immutable tests-only contract vectors for this snapshot;
2. a pure-memory projector implementation;
3. a separately reviewed server-owned same-attempt source adapter;
4. offline canonical-fixture integration evidence;
5. deterministic non-activating verification;
6. separate contracts and vectors for session and spread/freshness facts;
7. separate contracts and vectors for volatility and structure features; and
8. a separately versioned ReplayRunner stage before W7 integration.

No stage may silently include the next one. Tests do not equal implementation,
implementation does not equal integration, integration does not equal
activation, and activation does not equal verification.

## 14. G175 Acceptance Checklist

G175 is acceptable only when all of the following are true:

- this is the only added or modified file;
- W6 remains `CONTRACT_ONLY`;
- G151 and G153 are explicitly diagnostics-only and are not facts inputs;
- the server-owned same-attempt authority is explicit;
- source and result fields, order, built-in types, and ownership are exact;
- identity, quote, bars, symbol, freshness, status, reason, warning, and safety
  behavior are deterministic;
- decimal normalization has no silent sorting, rounding, repair, or fallback;
- account, credentials, paths, payloads, checksums, exceptions, policy, and
  execution details cannot leak;
- W5, W6, W7, reader, API, MT4, EA, order, execution, and trading boundaries
  remain explicit;
- tests, production implementation, integration, activation, and verification
  are stated as not implemented by G175;
- `git diff --check` passes; and
- exact scope and isolation checks pass.
