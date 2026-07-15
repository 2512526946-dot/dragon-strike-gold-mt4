# Canonical Gold Session and Spread/Freshness Facts v1 Contract

Status: G189 contract candidate

Scope: W6 deterministic, pure-memory facts only

Maturity effect: the narrow session and spread/freshness facts boundary moves
from `POLICY_ONLY` to `CONTRACT_ONLY`. W6 as a package remains `TESTS_ONLY`.

## 1. Purpose

G175-G188 establish one immutable Canonical Gold Market Facts Snapshot v1,
its server-owned docs-fixture source path, genuine offline integration, and
deterministic non-activating verification. That snapshot contains normalized
quote, completed-bar, symbol, and source-age facts. It does not classify a UTC
session bucket or expose a separately versioned spread/freshness facts result.

This contract defines the next W6 boundary. It consumes exactly one safe G175
snapshot in memory and produces deterministic session, spread, and freshness
facts. It does not read a source, decide whether trading is allowed, or create
analysis, risk, order, or execution authority.

## 2. Scope

This contract defines:

- one keyword-only pure-memory interface;
- exact frozen and slotted public result and nested fact types;
- the only accepted G175 READY input envelope;
- one server-owned session facts profile and exact UTC windows;
- deterministic Decimal spread calculations;
- deterministic source freshness aggregation;
- exact status, reason, identity, and failure-clearing behavior; and
- fixed Demo-only, Read-only, non-trading safety flags.

This contract does not define or authorize:

- contract vectors, production types, or a production builder;
- filesystem, environment, network, settings, API, database, cache, or clock
  access;
- a reader, source adapter, DataQualityGate, diagnostics path, or fixture
  integration;
- market-open, broker-availability, rollover, weekend, holiday, economic-event,
  or news-window policy;
- spread limits, freshness limits, warning thresholds, pass/fail thresholds,
  or any Gate result;
- ATR, realized volatility, trend, momentum, support, resistance, market
  structure, opportunity, recommendation, or invalidation logic;
- a ReplayRunner W6 stage, W7 analysis, RiskGate, PositionSizing, TradePlan,
  Shadow Mode, ExecutionGate, EA, order, execution, or trading capability; or
- reader activation, MT4 activation, Demo execution activation, Live
  activation, deployment, or verification of the complete W6 package.

## 3. Authority and Input Ownership

### 3.1 Sole input

The future builder accepts exactly one keyword-only input:

```python
build_canonical_gold_session_spread_freshness_facts_v1(
    *,
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,
) -> CanonicalGoldSessionSpreadFreshnessFactsV1
```

No positional argument or additional parameter is allowed. The caller cannot
provide or override a path, clock, reference time, session window, profile,
threshold, source, validator, dependency, expected result, or oracle.

The builder accepts only `type(market_facts_snapshot) is
CanonicalGoldMarketFactsSnapshotV1`. It must validate the exact G175 slot and
field order before reading a value. A dataclass constructor call is not source
authority.

### 3.2 Exact READY envelope

The input is usable only when all conditions below hold:

- `contract_version == "1.0"`;
- `passed is True`;
- `status_code == "CANONICAL_GOLD_MARKET_FACTS_READY"`;
- `reason_codes == ()` and `warning_codes == ()` as exact built-in tuples;
- `identity_available is True`;
- all six identity fields are present with exact built-in types;
- `canonical_symbol == "XAUUSD"` and `broker_symbol == "GOLD"`;
- `quote`, `symbol_spec`, and `freshness` are exact G175 nested types;
- `timeframes` is the exact ordered M15, H1, H4, D1 tuple and every bars tuple
  is non-empty;
- every nested object has the exact G175 slots, field order, and built-in
  types; and
- all eight G175 safety flags have their fixed safe values.

Missing, extra, reordered, subclassed, aliased, wrong-container, polluted, or
contradictory input fails closed. The builder must not call G178 to repair or
reproject a value and must not copy G178 projection algorithms.

### 3.3 Time and session authority

`market_facts_snapshot.reference_time_utc` is the sole clock input. It already
belongs to the server-owned G175 source attempt. The builder must not call an
ambient clock or accept a caller-provided time.

The session facts profile is a module-owned constant:

```text
canonical_gold_session_spread_freshness_profile_v1
```

The profile is versioned calculation authority only. It is not trading policy,
market-open authority, broker permission, or an economic calendar.

`symbol_spec.session_status_readonly_label` is copied only into the explicit
observed-label field. It never selects a session bucket, changes a boundary,
or grants permission.

## 4. Public Types

Every type in this section must be a `@dataclass(frozen=True, slots=True)`.
Field names, order, annotations, and exact built-in container types are part of
the public contract.

### 4.1 CanonicalGoldSessionSpreadFreshnessFactsV1

The result has exactly 24 fields in this order:

| # | Field | Annotation |
| ---: | --- | --- |
| 1 | `contract_version` | `str` |
| 2 | `facts_profile_version` | `str` |
| 3 | `passed` | `bool` |
| 4 | `status_code` | `str` |
| 5 | `reason_codes` | `tuple[str, ...]` |
| 6 | `warning_codes` | `tuple[str, ...]` |
| 7 | `identity_available` | `bool` |
| 8 | `bundle_schema_version` | `str | None` |
| 9 | `bundle_id` | `str | None` |
| 10 | `sequence` | `int | None` |
| 11 | `canonical_symbol` | `str | None` |
| 12 | `broker_symbol` | `str | None` |
| 13 | `reference_time_utc` | `str | None` |
| 14 | `session` | `CanonicalGoldSessionFactsV1 | None` |
| 15 | `spread` | `CanonicalGoldSpreadFactsV1 | None` |
| 16 | `freshness` | `CanonicalGoldSourceFreshnessFactsV1 | None` |
| 17 | `read_only` | `bool` |
| 18 | `demo_only` | `bool` |
| 19 | `is_tradable` | `bool` |
| 20 | `can_execute` | `bool` |
| 21 | `is_trading_permission` | `bool` |
| 22 | `is_execution_instruction` | `bool` |
| 23 | `allowed_to_call_ea` | `bool` |
| 24 | `allowed_to_modify_risk` | `bool` |

`contract_version` is exactly `"1.0"`. `facts_profile_version` is exactly
`"canonical_gold_session_spread_freshness_profile_v1"` on every result.

### 4.2 CanonicalGoldSessionFactsV1

The session record has exactly eight fields in this order:

| # | Field | Annotation |
| ---: | --- | --- |
| 1 | `utc_weekday_code` | `str` |
| 2 | `utc_second_of_day` | `int` |
| 3 | `session_bucket_code` | `str` |
| 4 | `window_start_second_utc` | `int` |
| 5 | `window_end_second_utc` | `int` |
| 6 | `seconds_since_window_start` | `int` |
| 7 | `seconds_until_window_end` | `int` |
| 8 | `observed_writer_session_status_label` | `str` |

`utc_weekday_code` is exactly one of the ordered public codes:

```text
MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
```

### 4.3 CanonicalGoldSpreadFactsV1

The spread record has exactly eight fields in this order:

| # | Field | Annotation |
| ---: | --- | --- |
| 1 | `bid_decimal` | `str` |
| 2 | `ask_decimal` | `str` |
| 3 | `mid_decimal` | `str` |
| 4 | `spread_decimal` | `str` |
| 5 | `spread_points` | `int` |
| 6 | `digits` | `int` |
| 7 | `point_decimal` | `str` |
| 8 | `spread_to_mid_ppm_decimal` | `str` |

These are measurements only. No field says that spread is acceptable, safe,
normal, wide, narrow, or eligible for trading.

### 4.4 CanonicalGoldSourceFreshnessFactsV1

The freshness record has exactly five fields in this order:

| # | Field | Annotation |
| ---: | --- | --- |
| 1 | `tick_age_microseconds` | `int` |
| 2 | `bars_payload_age_microseconds` | `int` |
| 3 | `symbol_spec_age_microseconds` | `int` |
| 4 | `maximum_source_age_microseconds` | `int` |
| 5 | `oldest_source_component_code` | `str` |

`oldest_source_component_code` is exactly one of `TICK`, `BARS_PAYLOAD`, or
`SYMBOL_SPEC`.

## 5. UTC Session Algorithm

### 5.1 Timestamp parsing

The builder parses only the strict G175 UTC Z format:

```text
YYYY-MM-DDTHH:MM:SSZ
YYYY-MM-DDTHH:MM:SS.ffffffZ
```

Fractional precision is one through six digits. Leap seconds, offsets, naive
times, lowercase `z`, whitespace, and alternate forms are invalid. The parsed
datetime must be timezone-aware UTC.

`utc_second_of_day` is `hour * 3600 + minute * 60 + second`. Fractional
microseconds do not change the integer session bucket.

### 5.2 Exact half-open windows

The profile uses these exact ordered half-open UTC windows:

| Bucket | Start second | End second |
| --- | ---: | ---: |
| `ASIA_UTC` | 0 | 28800 |
| `LONDON_UTC` | 28800 | 46800 |
| `LONDON_NEW_YORK_OVERLAP_UTC` | 46800 | 57600 |
| `NEW_YORK_UTC` | 57600 | 79200 |
| `OFF_HOURS_UTC` | 79200 | 86400 |

Each second belongs to exactly one bucket by `start <= value < end`. A value
equal to an end belongs to the next bucket. No sorting, daylight-saving-time
lookup, locale, holiday calendar, fallback, or caller override is allowed.

For the selected window:

```text
seconds_since_window_start = utc_second_of_day - window_start_second_utc
seconds_until_window_end = window_end_second_utc - utc_second_of_day
```

The overlap bucket is an explicit profile bucket; it is not inferred by
returning multiple session codes. `OFF_HOURS_UTC` is a time bucket only. It
does not mean a market is closed or that trading is blocked.

## 6. Decimal Spread Algorithm

The builder may parse only the normalized G175 quote strings. It must use
`Decimal(value)` on the exact built-in strings and must never convert through
`float`.

Use one local Decimal context with:

```text
precision = 64
rounding = ROUND_HALF_EVEN
Emin = -999999
Emax = 999999
capitals = 1
clamp = 0
```

All parsed values must be finite. Require:

- `bid > 0`, `ask > 0`, `ask >= bid`, `spread >= 0`, and `point > 0`;
- `ask - bid == spread`;
- `Decimal(spread_points) * point == spread`; and
- `digits` is an exact built-in `int` in the G175 range.

Compute:

```text
mid = (bid + ask) / Decimal("2")
spread_to_mid_ppm = (spread / mid) * Decimal("1000000")
```

`mid_decimal` is fixed-point with exactly `digits + 1` fractional digits. This
operation is exact for two G175 fixed-point prices and must not round away a
nonzero remainder. `spread_to_mid_ppm_decimal` is quantized exactly once to
`Decimal("0.000001")` with `ROUND_HALF_EVEN` and emitted with exactly six
fractional digits. Positive and negative zero emit as unsigned zero. Exponent
notation, NaN, Infinity, context flags from an invalid operation, a second
quantization, and silent repair are forbidden.

The copied `bid_decimal`, `ask_decimal`, `spread_decimal`, and `point_decimal`
must remain byte-for-byte equal to the accepted G175 strings.

## 7. Freshness Algorithm

The three source ages are copied as exact nonnegative built-in integers from
the G175 freshness record. No threshold or warning classification is applied.

`maximum_source_age_microseconds` is the maximum of tick, bars-payload, and
symbol-spec age. Ties use the fixed priority `TICK`, `BARS_PAYLOAD`, then
`SYMBOL_SPEC` to choose `oldest_source_component_code`.

No timestamp is reparsed to derive a second freshness value. No per-timeframe
age, policy threshold, clamp, sort, or ambient-clock comparison is allowed.

## 8. Result and Failure Mapping

The ordered first-failure priority is input type and shape, READY authority,
identity, session, spread, freshness, then unexpected exception.

| Passed | Status | Exact reason codes |
| --- | --- | --- |
| `true` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_READY` | `()` |
| `false` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID` | `("GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",)` |
| `false` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_UPSTREAM_BLOCKED` | `("GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_NOT_READY",)` |
| `false` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_IDENTITY_INVALID` | `("GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_IDENTITY_INVALID",)` |
| `false` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID` | `("GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID",)` |
| `false` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID` | `("GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID",)` |
| `false` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID` | `("GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID",)` |
| `false` | `CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SAFE_FAILURE` | `("GOLD_SESSION_SPREAD_FRESHNESS_EXCEPTION_SANITIZED",)` |

`warning_codes` is the exact empty built-in tuple on every result. A warning
must not be invented from a spread value, source age, session bucket, weekend,
or observed writer label.

For every non-passed result:

- `identity_available` is `false`;
- identity fields 8 through 13 are `None`;
- `session`, `spread`, and `freshness` are `None`;
- no input value, path, payload, checksum, exception, or internal state is
  returned; and
- a fresh result object is returned without retry, fallback, or partial data.

The builder catches unexpected exceptions only at the public boundary and
returns the sanitized SAFE_FAILURE result. It must not expose exception text
or traceback data.

## 9. Identity and Immutability

A READY result copies the six G175 identity fields exactly. The builder must
not synthesize, normalize, hash, redact, or replace identity. It must not
mutate the input snapshot or any nested object.

Every invocation returns a new result and new nested records. No mutable
container, global cache, retained input, singleton result, or shared nested
record is allowed. Equal accepted input produces value-equal output.

## 10. Fixed Safety Flags

Every result has these exact values:

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

Session membership, a zero spread, zero source age, READY status, or any future
feature can never override these flags.

## 11. Isolation and Prohibited Behavior

The future module may import only standard-library pure calculation types and
the exact G175 public snapshot types. It must not import or call G178 builder,
G182 adapter, G185 fixture boundary, W1 reader or Gate, G151/G153 diagnostics,
W5 ReplayRunner, an API, MT4, EA, or any W7-W21 component.

The builder performs no filesystem, environment, network, settings, process,
logging, clock, database, cache, or frontend I/O. It does not retry, fallback,
sort, repair, mutate, switch sources, or accept dependency injection.

## 12. Staged Delivery

Later work must remain separately planned and approved:

1. immutable static contract vectors for this exact contract;
2. production types and the pure-memory builder;
3. genuine offline integration from the G185 READY snapshot boundary;
4. deterministic non-activating verification for this facts stage;
5. a separate contract and delivery for volatility and structure features;
6. a separate contract and delivery for economic-window inputs; and
7. a separately versioned ReplayRunner W6 stage before W7.

No stage silently includes the next. Contract is not tests, tests are not
implementation, implementation is not integration, integration is not
activation, and activation is not verification.

## 13. WBS and Capability Boundaries

- W1 remains the verified authority for Bundle v1 validation and
  DataQualityGate behavior.
- W5 remains verified only for ReplayRunner v1 canonical diagnostics.
- G175-G188 remain the authority for the snapshot and its fixed offline
  fixture verification boundary.
- G189 defines only a new narrow contract. W6 remains `TESTS_ONLY`.
- W7-W21 remain unchanged and unauthorized.
- Reader activation, real MT4, EA, order, execution, Demo activation, Live
  activation, and trading remain prohibited.

## 14. G189 Acceptance Checklist

G189 is acceptable only when:

- this document is the only added file;
- the public interface has one exact keyword-only G175 snapshot input;
- the result has exactly 24 ordered fields and every nested type is exact;
- READY authority, identity, input shapes, and safety flags are strict;
- the UTC profile, windows, overlap, endpoint, and writer-label rules are
  deterministic and server-owned;
- Decimal spread calculations, formatting, and failure rules are complete;
- source and completed-bar freshness calculations are complete and use no
  threshold or ambient clock;
- every status/reason pair and first-failure priority is unambiguous;
- failures clear identity and facts without leakage;
- no implementation, test vector, runtime integration, ReplayRunner stage,
  activation, execution, or trading capability is claimed;
- W6 remains `TESTS_ONLY`; and
- exact scope, ASCII, isolation, and `git diff --check` checks pass.
