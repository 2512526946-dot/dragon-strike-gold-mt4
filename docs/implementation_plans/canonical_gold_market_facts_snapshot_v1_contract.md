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

| Order | Field | Exact value or rule |
| ---: | --- | --- |
| 1 | `reader_passed` | built-in `bool`, exactly `true` |
| 2 | `reader_status_code` | `CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID` |
| 3 | `value_status_code` | `CANONICAL_MT4_BUNDLE_V1_VALUE_VALID` |
| 4 | `data_quality_passed` | built-in `bool`, exactly `true` |
| 5 | `data_quality_status_code` | `CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED` |
| 6 | `ready_for_readonly_analysis` | built-in `bool`, exactly `true` |
| 7 | `warning_codes` | exact empty built-in tuple |
| 8 | `same_attempt_identity_bound` | built-in `bool`, exactly `true` |

V1 deliberately rejects passed-with-warning upstream evidence. A later policy
may define specific warning handling through a separate contract. It must not
be inferred in the first implementation.

### 6.2 Tick source

`CanonicalGoldTickSourceV1` contains, in order:

```text
bid
ask
spread
spread_points
digits
point
tick_time_utc
```

The values retain the canonical JSON numeric and timestamp meaning. Numeric
values must be finite exact built-in `int` or `float` values, excluding
`bool`. Integer fields must be exact built-in `int`. Cross-field rules from the
canonical contract remain mandatory.

### 6.3 Timeframe and bar source

`timeframes` contains exactly `M15`, `H1`, `H4`, and `D1` in that order. Each
`CanonicalGoldTimeframeSourceV1` contains, in order:

```text
timeframe
period_seconds
bars
```

The fixed period mapping remains `900`, `3600`, `14400`, and `86400` seconds.
Each `bars` value is a non-empty built-in tuple of no more than 500
`CanonicalGoldBarSourceV1` records. Each bar contains, in order:

```text
open_time_utc
open
high
low
close
tick_volume
spread_points
```

Bars must be completed, strictly ascending, unique, finite, and internally
consistent under the canonical Bundle v1 rules. Lists, mappings, iterators, and
subclassed containers are invalid source records.

### 6.4 Symbol source

`CanonicalGoldSymbolSpecSourceV1` contains, in order:

```text
spec_time_utc
digits
point
tick_size
tick_value
contract_size
min_lot
lot_step
max_lot
base_currency
profit_currency
margin_currency
trade_mode_readonly_label
session_status_readonly_label
```

The values retain their canonical contract meaning. The two readonly labels
are observed writer metadata only. They are not market-session policy,
broker-trade permission, system permission, or ExecutionGate evidence.

## 7. Result Type

`CanonicalGoldMarketFactsSnapshotV1` has exactly these fields in this order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `contract_version` | built-in `str` |
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
| 14 | `timeframes` | built-in tuple of facts records |
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

`CanonicalGoldQuoteFactsV1` contains, in order:

```text
bid_decimal
ask_decimal
spread_decimal
spread_points
digits
point_decimal
tick_time_utc
```

Decimal fields are built-in ASCII strings in fixed-point notation. They are
not binary floating-point values in the result.

### 7.2 Bar facts

Result timeframes preserve the exact canonical timeframe order. Each result
bar contains, in order:

```text
open_time_utc
open_decimal
high_decimal
low_decimal
close_decimal
tick_volume
spread_points
```

The snapshot does not add indicators, labels, classifications, or inferred
bar completion fields.

### 7.3 Symbol facts

`CanonicalGoldSymbolFactsV1` contains, in order:

```text
spec_time_utc
digits
point_decimal
tick_size_decimal
tick_value_decimal
contract_size_decimal
min_lot_decimal
lot_step_decimal
max_lot_decimal
base_currency
profit_currency
margin_currency
trade_mode_readonly_label
session_status_readonly_label
```

These are facts only. Lot fields do not calculate or authorize a lot size.

### 7.4 Freshness facts

`CanonicalGoldFreshnessFactsV1` contains, in order:

```text
tick_age_microseconds
bars_payload_age_microseconds
symbol_spec_age_microseconds
```

Each value is a non-negative exact built-in `int` derived from the server-owned
reference time and accepted source timestamp. The bars age uses
`bars_generated_at_utc`, not a bar open time. These values describe age only.
They do not carry thresholds, pass/fail policy, source readiness, session
permission, or trading permission.

## 8. Deterministic Normalization

The future implementation must use one documented decimal normalization
algorithm:

1. reject `bool`, subclasses, non-finite numbers, strings, and unsupported
   numeric types;
2. convert each accepted built-in `int` or `float` through its canonical
   base-10 string representation into `Decimal`;
3. derive the fixed price quantum from the exact accepted `digits` and `point`;
4. require tick, bar, and symbol price values to be representable at the
   canonical precision without a value-changing round operation;
5. emit fixed-point ASCII text with exactly `digits` decimal places for price
   fields;
6. emit other decimal symbol values in normalized fixed-point ASCII form with
   no exponent, leading plus sign, `NaN`, or infinity; and
7. reject any normalization exception or ambiguous value rather than rounding,
   sorting, repairing, or substituting it.

The source `spread`, `spread_points`, and `point` relation must remain exact
under normalized decimal arithmetic. Tick and symbol `digits` and `point` must
match. No tolerance may silently convert an invalid source into a passed facts
snapshot.

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
