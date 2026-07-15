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

#### 3.2.1 Closed G175 shape and value predicate

The accepted predicate is closed over the public G175 result. Exact slot order
is required for each record:

```text
CanonicalGoldMarketFactsSnapshotV1 =
  (contract_version, passed, status_code, reason_codes, warning_codes,
   identity_available, bundle_schema_version, bundle_id, sequence,
   canonical_symbol, broker_symbol, reference_time_utc, quote, timeframes,
   symbol_spec, freshness, read_only, demo_only, is_tradable, can_execute,
   is_trading_permission, is_execution_instruction, allowed_to_call_ea,
   allowed_to_modify_risk)
CanonicalGoldQuoteFactsV1 =
  (bid_decimal, ask_decimal, spread_decimal, spread_points, digits,
   point_decimal, tick_time_utc)
CanonicalGoldTimeframeFactsV1 = (timeframe, period_seconds, bars)
CanonicalGoldBarFactsV1 =
  (open_time_utc, open_decimal, high_decimal, low_decimal, close_decimal,
   tick_volume, spread_points)
CanonicalGoldSymbolFactsV1 =
  (spec_time_utc, digits, point_decimal, tick_size_decimal,
   tick_value_decimal, contract_size_decimal, min_lot_decimal,
   lot_step_decimal, max_lot_decimal, base_currency, profit_currency,
   margin_currency, trade_mode_readonly_label,
   session_status_readonly_label)
CanonicalGoldFreshnessFactsV1 =
  (tick_age_microseconds, bars_payload_age_microseconds,
   symbol_spec_age_microseconds)
```

Every record must have the exact named G175 type; subclasses are invalid.
Every scalar must have its annotated exact built-in type, `bool` is not an
`int`, and every tuple must be an exact built-in tuple with exact element
types. At the top level, textual fields are exact built-in strings, boolean
fields are exact built-in booleans, `sequence` is an exact built-in integer,
and reason/warning fields are exact built-in tuples of exact built-in strings.
Quote decimal and timestamp fields are strings while its count fields are
integers; timeframe and bar labels/timestamps/decimals are strings while their
period/count fields are integers; every symbol field except `digits` is a
string; and all freshness fields are integers. After this shape check, the
following value rules are mandatory:

- `bundle_schema_version` is exactly `"1.0"`; `bundle_id` is 16 through 64
  ASCII characters and matches `[A-Za-z0-9._-]+`; `sequence` is positive;
  `canonical_symbol` is `"XAUUSD"`; and `broker_symbol` is `"GOLD"`.
  `reference_time_utc` remains an exact built-in string and is validated by
  the session rule below.
- `quote.digits` is in the inclusive range 0 through 8. Its four decimal
  strings are finite, unsigned, non-exponent fixed-point strings that reproduce
  byte-for-byte under `format(value, f".{digits}f")`. When `digits == 0` the
  strings contain no decimal point. Bid and ask are positive, spread is
  nonnegative, point is positive and equals
  `Decimal(1).scaleb(-digits)`, `spread_points` is nonnegative, and the two
  exact identities `ask - bid == spread` and
  `Decimal(spread_points) * point == spread` hold. `tick_time_utc` is strict
  UTC Z.
- `timeframes` contains exactly `("M15", 900)`, `("H1", 3600)`,
  `("H4", 14400)`, and `("D1", 86400)` in that order. Each bars tuple has 1
  through 500 records. Bar times are strict UTC Z, unique, and strictly
  ascending. Each OHLC string obeys the quote fixed-point rule, parses to a
  positive value, and satisfies `high >= max(open, low, close)` and
  `low <= min(open, high, close)`. `tick_volume` and `spread_points` are
  nonnegative.
- `symbol_spec.spec_time_utc` is strict UTC Z; its `digits` equals
  `quote.digits`; its `point_decimal` equals `quote.point_decimal`; and point
  equals the price quantum. `tick_size_decimal` is positive and obeys the same
  fixed-point format. `tick_value_decimal`, `contract_size_decimal`,
  `min_lot_decimal`, `lot_step_decimal`, and `max_lot_decimal` are finite,
  positive canonical G175 non-price strings: no exponent, leading plus sign,
  signed zero, or unnecessary trailing fractional zero, and formatting by the
  G175 trim-only algorithm reproduces each string byte-for-byte. Min lot and
  lot step do not exceed max lot. Base currency is `"XAU"`, profit currency is
  `"USD"`, and margin currency plus both readonly labels are nonempty ASCII
  strings matching `[A-Za-z0-9._:-]+`.
- All three freshness ages are nonnegative exact built-in integers. The exact
  age from `reference_time_utc` to `quote.tick_time_utc` equals
  `tick_age_microseconds`; the exact age to `symbol_spec.spec_time_utc` equals
  `symbol_spec_age_microseconds`. Subtracting
  `bars_payload_age_microseconds` from the reference instant yields the G175
  bars-payload instant; every bar is completed only when
  `open_time + period_seconds <= bars_payload_instant`.

These checks validate a purported G175 result; they do not normalize prices,
project source values, sort bars, replace G178, or create source authority.

#### 3.2.2 Deterministic invalid-input classification

The closed predicate uses this exact ordered classification:

1. wrong top-level or nested type, slots, field order, scalar type, tuple
   container, or tuple element type maps to `INPUT_INVALID` /
   `GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID`;
2. wrong top-level READY status, reason/warning tuple, identity-availability
   flag, contract version, fixed safety flag, timeframe name/period, bar
   ordering/OHLC/volume/spread invariant, or non-spread and non-session symbol
   invariant maps to `UPSTREAM_BLOCKED` /
   `GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_NOT_READY`;
3. an invalid bundle-schema, bundle-id, sequence, symbol, or broker-symbol
   identity value maps to `IDENTITY_INVALID` /
   `GOLD_SESSION_SPREAD_FRESHNESS_SNAPSHOT_IDENTITY_INVALID`;
4. an invalid reference-time parse or observed writer session label maps to
   `SESSION_INVALID` / `GOLD_SESSION_SPREAD_FRESHNESS_SESSION_INVALID`;
5. an invalid quote value, quote timestamp, fixed-point representation,
   spread identity, or quote/symbol digits-and-point consistency maps to
   `SPREAD_INVALID` / `GOLD_SESSION_SPREAD_FRESHNESS_SPREAD_INVALID`;
6. an invalid age, age/timestamp identity, reconstructed bars-payload instant,
   or completed-bar check maps to `FRESHNESS_INVALID` /
   `GOLD_SESSION_SPREAD_FRESHNESS_FRESHNESS_INVALID`; and
7. only an unexpected exception reaching the public boundary maps to
   `SAFE_FAILURE` / `GOLD_SESSION_SPREAD_FRESHNESS_EXCEPTION_SANITIZED`.

Within one category, fields are checked in the public field order shown above;
timeframes and bars are checked in tuple order. No invalid value can be moved
to another category by retry, fallback, repair, or alternate validation.

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

The builder may parse only the normalized G175 quote strings. It constructs
`Decimal(value)` directly from each exact built-in string, never from `float`,
and checks the finite, unsigned, fixed-point representation required by Section
3.2. Decimal construction is exact and context-free. No price arithmetic may
run under a finite-precision Decimal context.

The builder must not impose an independent digit-count limit on a formatted
G175 Decimal coefficient. G178 applies its precision check before fixed-point
formatting; that formatting may append fractional zeroes or expand an accepted
positive exponent. Those output digits do not prove that the pre-format source
coefficient exceeded G175 authority. G189 validates the canonical public
fixed-point representation and must not attempt to reconstruct or reclassify
the private pre-format coefficient.

After validation, convert each fixed-point string to its exact nonnegative
base-10 integer coefficient by removing its one decimal point, if present. Let
`B`, `A`, `S`, and `P` be the bid, ask, spread, and point coefficients at the
common scale `10 ** -digits`. The conversion must reproduce the original
string under the fixed-point formatter; it is not normalization. Require:

```text
B > 0
A > 0
A >= B
S >= 0
P == 1
spread_points >= 0
A - B == S
spread_points * P == S
```

All coefficient and intermediate arithmetic uses exact built-in integers.
Python integer division is used only through the explicit `divmod` rule below;
binary float arithmetic and Decimal operations subject to a precision context
are forbidden.

Compute the midpoint coefficient exactly:

```text
M = 5 * (B + A)
```

`M` is at scale `10 ** -(digits + 1)`. Emit it as `mid_decimal` with exactly
`digits + 1` fractional digits, inserting leading fractional zeroes when
needed. This remains exact when `B + A` has 65 digits and never rounds.

For `spread_to_mid_ppm_decimal`, compute the correctly rounded integer number
of millionths of one ppm without first forming a non-terminating quotient:

```text
N = 2 * S * (10 ** 12)
D = B + A
q, r = divmod(N, D)
if 2 * r < D: rounded = q
if 2 * r > D: rounded = q + 1
if 2 * r == D: rounded = q when q is even, otherwise q + 1
```

The factor `10 ** 12` combines ppm's `10 ** 6` scale with the six output
fractional digits. Format `rounded` at scale `10 ** -6` with exactly six
fractional digits. This is the unique exact `ROUND_HALF_EVEN` result equivalent
to quantizing the mathematical ratio to `0.000001`; it does not perform an
earlier rounded division or a second quantization. Zero emits exactly
`0.000000`. Exponent notation, signed zero, approximation, overflow fallback,
and silent repair are forbidden.

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
3. genuine offline composition evidence through a G185 READY source, then the
   G178 projector, then the G189 builder, orchestrated outside the G189 module;
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
- source freshness aggregation is complete, uses no threshold or ambient
  clock, and defines no completed-bar or per-timeframe freshness fact;
- every status/reason pair and first-failure priority is unambiguous;
- failures clear identity and facts without leakage;
- no implementation, test vector, runtime integration, ReplayRunner stage,
  activation, execution, or trading capability is claimed;
- W6 remains `TESTS_ONLY`; and
- exact scope, ASCII, isolation, and `git diff --check` checks pass.
