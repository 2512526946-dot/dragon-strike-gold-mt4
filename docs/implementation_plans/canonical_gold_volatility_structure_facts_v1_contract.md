# Canonical Gold Volatility and Structure Facts v1 Contract

Status: G194 contract candidate

Scope: W6 deterministic, pure-memory completed-bar facts only

Maturity effect: the narrow volatility and structure facts boundary moves from
`POLICY_ONLY` to `CONTRACT_ONLY`. W6 as a package remains `TESTS_ONLY`.

## 1. Purpose

G175-G193 establish one immutable Canonical Gold Market Facts Snapshot v1,
fixed offline source authority, session and spread/freshness facts, genuine
offline composition, and deterministic non-activating verification. The G175
snapshot contains exact ordered completed bars for M15, H1, H4, and D1. It does
not expose a separately versioned volatility and structure result.

This contract defines the next W6 boundary. It consumes exactly one safe G175
snapshot in memory and derives deterministic facts from every adjacent pair of
completed bars in each existing timeframe tuple. It does not select a trading
strategy, infer an opportunity, approve risk, or authorize execution.

## 2. Scope and non-goals

This contract defines:

- one keyword-only pure-memory interface;
- exact frozen and slotted public result and nested fact types;
- the complete accepted G175 READY input predicate;
- one server-owned facts profile and fixed M15/H1/H4/D1 authority;
- exact fixed-point Decimal calculations for completed-bar range, true range,
  body, wick, and adjacent changes;
- deterministic direction, range-relation, containment, high/low relation,
  and close-location fact codes;
- exact status, reason, identity, failure-clearing, and first-failure rules;
  and
- fixed Demo-only, Read-only, non-trading safety flags.

This contract does not define or authorize:

- ATR, moving averages, standard deviation, variance, annualization, z-score,
  percentile, ranking, threshold, regime, trend, momentum, or signal logic;
- swing selection, pivot selection, support, resistance, breakout approval,
  invalidation, opportunity, recommendation, confidence, or score;
- economic calendar, holiday, news, event-impact, blackout-window, or
  economic-window facts or policy;
- a Gate result, market-open decision, trade-session approval, risk decision,
  TradePlan, PositionSizing, Shadow Mode, or execution decision;
- a file reader, source adapter, DataQualityGate, fixture boundary, API, CLI,
  frontend, environment, network, database, cache, log, or ambient clock;
- ReplayRunner W6 staging or any W7-W21 capability; or
- reader activation, real MT4, EA calls, orders, execution, deployment,
  activation, or trading permission.

## 3. Public interface and exports

A later implementation must expose exactly:

```python
def build_canonical_gold_volatility_structure_facts_v1(
    *,
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,
) -> CanonicalGoldVolatilityStructureFactsV1:
    ...
```

The function is keyword-only and has exactly one argument. The caller cannot
supply a path, source, timeframe selection, bar window, clock, profile,
threshold, Decimal context, dependency, policy, or output oracle.

The future module is:

```text
backend.app.services.canonical_gold_volatility_structure_facts
```

Its ordered `__all__` must be exactly:

```python
(
    "CanonicalGoldVolatilityStructureFactsV1",
    "CanonicalGoldTimeframeVolatilityStructureFactsV1",
    "CanonicalGoldBarPairVolatilityStructureFactsV1",
    "build_canonical_gold_volatility_structure_facts_v1",
)
```

The module may import the published G175/G178 snapshot result types. It must
not call G178, G185, G191, a reader, a Gate, diagnostics, or ReplayRunner. It
must not copy source construction, projection, or session/spread logic.

## 4. Server-owned authority

The following values are immutable module authority:

```text
contract_version = "1.0"
facts_profile_version = "canonical_gold_volatility_structure_profile_v1"
timeframe_order = ("M15", "H1", "H4", "D1")
timeframe_periods = (("M15",900),("H1",3600),("H4",14400),("D1",86400))
minimum_bars_per_timeframe = 2
maximum_bars_per_timeframe = 500
```

The builder must process every accepted bar in the existing G175 order. It
must not select a shorter window, drop an endpoint, sort, deduplicate, resample,
interpolate, repair, synthesize, merge timeframes, or switch sources.

For a timeframe containing `n` bars, the ordered output contains exactly
`n - 1` bar-pair records. Output pair `i` is derived only from input bars
`i` and `i + 1`, for `0 <= i < n - 1`.

## 5. Exact public types

Every public type must use `@dataclass(frozen=True, slots=True)`. Field names,
field order, and annotations are contract data. No subclass, alias field,
default value, optional extra field, dynamic attribute, or alternate container
is accepted.

### 5.1 CanonicalGoldVolatilityStructureFactsV1

The result has exactly 24 fields in this order:

| # | Field | Exact annotation | READY value |
| --- | --- | --- | --- |
| 1 | `contract_version` | `str` | `"1.0"` |
| 2 | `facts_profile_version` | `str` | `"canonical_gold_volatility_structure_profile_v1"` |
| 3 | `passed` | `bool` | `True` |
| 4 | `status_code` | `str` | `CANONICAL_GOLD_VOLATILITY_STRUCTURE_READY` |
| 5 | `reason_codes` | `tuple[str, ...]` | exact empty built-in tuple |
| 6 | `warning_codes` | `tuple[str, ...]` | exact empty built-in tuple |
| 7 | `identity_available` | `bool` | `True` |
| 8 | `source_contract_version` | `str | None` | copied exact G175 `contract_version` |
| 9 | `bundle_schema_version` | `str | None` | copied from input |
| 10 | `bundle_id` | `str | None` | copied from input |
| 11 | `sequence` | `int | None` | copied from input |
| 12 | `canonical_symbol` | `str | None` | `XAUUSD` |
| 13 | `broker_symbol` | `str | None` | `GOLD` |
| 14 | `reference_time_utc` | `str | None` | copied from input |
| 15 | `timeframes` | `tuple[CanonicalGoldTimeframeVolatilityStructureFactsV1, ...]` | exact four-item tuple |
| 16 | `total_pair_count` | `int` | sum of four exact `pair_count` values |
| 17 | `read_only` | `bool` | `True` |
| 18 | `demo_only` | `bool` | `True` |
| 19 | `is_tradable` | `bool` | `False` |
| 20 | `can_execute` | `bool` | `False` |
| 21 | `is_trading_permission` | `bool` | `False` |
| 22 | `is_execution_instruction` | `bool` | `False` |
| 23 | `allowed_to_call_ea` | `bool` | `False` |
| 24 | `allowed_to_modify_risk` | `bool` | `False` |

### 5.2 CanonicalGoldTimeframeVolatilityStructureFactsV1

Each timeframe record has exactly five fields:

| # | Field | Exact annotation | Rule |
| --- | --- | --- | --- |
| 1 | `timeframe` | `str` | exact item from M15/H1/H4/D1 order |
| 2 | `period_seconds` | `int` | exact matching 900/3600/14400/86400 |
| 3 | `source_bar_count` | `int` | exact accepted input bar count, 2 through 500 |
| 4 | `pair_count` | `int` | exactly `source_bar_count - 1` |
| 5 | `bar_pairs` | `tuple[CanonicalGoldBarPairVolatilityStructureFactsV1, ...]` | exact ordered adjacent-pair tuple |

The result contains exactly four records in M15, H1, H4, D1 order. It rejects
another length, order, period, container, or element type.

### 5.3 CanonicalGoldBarPairVolatilityStructureFactsV1

Each pair record has exactly 18 fields:

| # | Field | Exact annotation |
| --- | --- | --- |
| 1 | `previous_open_time_utc` | `str` |
| 2 | `current_open_time_utc` | `str` |
| 3 | `previous_range_decimal` | `str` |
| 4 | `current_range_decimal` | `str` |
| 5 | `true_range_decimal` | `str` |
| 6 | `body_signed_decimal` | `str` |
| 7 | `body_absolute_decimal` | `str` |
| 8 | `upper_wick_decimal` | `str` |
| 9 | `lower_wick_decimal` | `str` |
| 10 | `close_change_decimal` | `str` |
| 11 | `high_change_decimal` | `str` |
| 12 | `low_change_decimal` | `str` |
| 13 | `direction_code` | `str` |
| 14 | `range_relation_code` | `str` |
| 15 | `range_containment_code` | `str` |
| 16 | `current_high_vs_previous_high_code` | `str` |
| 17 | `current_low_vs_previous_low_code` | `str` |
| 18 | `current_close_vs_previous_range_code` | `str` |

The two timestamps are copied from the exact adjacent input bars. All Decimal
strings use the input quote `digits` and the output rules in Section 8.

## 6. Complete accepted G175 predicate

The only accepted input is exact built-in
`CanonicalGoldMarketFactsSnapshotV1`, not a subclass or look-alike. Its field
names and slot order must equal the published G175 24-field result exactly.
All nested records and tuples must have their exact G175 production types,
field names, slot order, built-in scalar types, and containers.

An accepted input must satisfy all of the following:

1. `contract_version == "1.0"`, `passed is True`, status is exact
   `CANONICAL_GOLD_MARKET_FACTS_READY`, and both code tuples are empty.
2. `identity_available is True`; bundle schema version is exact `"1.0"`;
   bundle id matches `^[A-Za-z0-9._-]{16,64}$`; sequence is a positive strict
   `int`; symbols are exact `XAUUSD` and `GOLD`; reference time is a strict
   valid UTC `Z` timestamp.
3. Quote, symbol, freshness, and all four timeframes are present with exact
   G175 types. The timeframe tuple is exactly M15/H1/H4/D1 with matching
   periods and 1 through 500 bars in each record. A one-bar timeframe is valid
   G175 input but is insufficient for this pair-based contract and maps to the
   dedicated history failure in Section 10.
4. Bar open times are strict UTC `Z`, strictly increasing within each
   timeframe, and each bar is complete at the snapshot reference time.
5. Every price string is finite, canonical fixed-point text with exactly the
   quote `digits`. Bid and ask are positive, ask is not below bid, and
   `ask - bid == spread == spread_points * point`. Quote and symbol digits and
   point are identical; point is the exact price quantum. Tick size is
   positive; tick value, contract size, min lot, lot step, and max lot are
   canonical positive decimals; min lot and lot step do not exceed max lot;
   base/profit currencies are exact XAU/USD; each remaining label fully
   matches strict ASCII `^[A-Za-z0-9._:-]+$`.
6. Each bar has nonnegative strict `int` tick volume and spread points;
   `high >= max(open, close)` and `low <= min(open, close)`.
7. Tick, bars-payload, and symbol-spec ages are nonnegative strict `int`
   microseconds. Tick and symbol ages equal reference time minus their exact
   timestamps. Let `bars_payload_time` equal reference time minus the exact
   bars-payload age; every bar must satisfy
   `open_time + period_seconds <= bars_payload_time`. Overflow is invalid.
8. All eight safety flags are exact: Read-only and Demo-only true; tradable,
   executable, permission, instruction, EA-call, and risk-modification false.

Missing, extra, reordered, duplicate, aliased, case-changed, subclassed,
wrong-container, wrong-element, malformed, contradictory, warning-bearing, or
polluted input fails closed. The builder must not call G178 to repair or
re-project an input and must not infer missing facts from another source.

## 7. Ordered bar-pair calculations

For one adjacent pair, let previous values be `PO`, `PH`, `PL`, `PC`, and
current values be `O`, `H`, `L`, `C`. The builder computes exactly:

```text
previous_range = PH - PL
current_range = H - L
true_range = max(H - L, abs(H - PC), abs(L - PC))
body_signed = C - O
body_absolute = abs(C - O)
upper_wick = H - max(O, C)
lower_wick = min(O, C) - L
close_change = C - PC
high_change = H - PH
low_change = L - PL
```

No average, rolling window, threshold, weighting, annualization, or cross-
timeframe calculation is permitted. A negative range, true range, absolute
body, or wick is invalid and cannot be clamped to zero.

## 8. Unique fixed-point Decimal algorithm

The implementation must use this exact algorithm for every price and derived
Decimal value:

1. Read `digits` only from the accepted G175 quote and require strict built-in
   `int` in the G175 range. Construct `quantum` exactly as
   `Decimal((0, (1,), -digits))`; this tuple constructor does not consult an
   ambient Decimal context.
2. Construct the strict ASCII pattern exactly as
   `re.compile(rf"^(?:0|[1-9][0-9]*)\.[0-9]{{{digits}}}$", re.ASCII)` and accept
   a source price only when it matches fully. Scientific notation, whitespace,
   signs, commas, `NaN`, and infinities are invalid.
3. Convert source text with exact `Decimal(source_text)`. Do not use float,
   `Decimal(float_value)`, or an ambient Decimal context.
4. Let `coefficient_digits` be the maximum number of coefficient digits among
   the quote and completed-bar fixed-point price strings used by this stage.
   Create a fresh local
   `decimal.Context(prec=coefficient_digits + 2, rounding=ROUND_HALF_EVEN)`
   with traps enabled for `InvalidOperation`, `DivisionByZero`, `Overflow`,
   `Underflow`, `Inexact`, and `Rounded`.
5. Perform only the subtraction, absolute-value, minimum, and maximum
   operations in Section 7 inside that local context. No division or
   quantization is needed or allowed.
6. Require every derived value to be finite and exactly representable at
   `quantum`. A result whose exponent or value would require rounding is
   invalid; it must not be quantized into acceptance.
7. Render with fixed-point notation and exactly `digits` fractional digits.
   Preserve trailing zeros. Normalize any mathematical zero, including a
   negative zero produced by subtraction, to the unsigned canonical zero.
8. Parse the rendered text again with `Decimal(rendered)` and require exact
   equality with the unrendered result. Any conversion, arithmetic, exponent,
   formatting, or round-trip ambiguity fails closed.

Unsigned derived fields (`previous_range_decimal`, `current_range_decimal`,
`true_range_decimal`, `body_absolute_decimal`, and both wick fields) use the
same unsigned fixed-point pattern as source prices and may be canonical zero.
Signed change/body fields use exact pattern
`^-?(?:0|[1-9][0-9]*)\.[0-9]{digits}$`; a leading plus is forbidden and a
negative mathematical zero must be rendered without the minus sign.

The `ROUND_HALF_EVEN` setting is frozen defensive context authority. V1 has no
operation that is allowed to round, so either `Rounded` or `Inexact` is a
failure.

## 9. Exact structure code mapping

Every code is a strict built-in `str` selected from the finite lists below.
The listed comparison order resolves equality deterministically.

### 9.1 Direction

```text
C > O  -> UP
C < O  -> DOWN
C == O -> FLAT
```

### 9.2 Range relation

```text
current_range > previous_range  -> EXPANDED
current_range < previous_range  -> CONTRACTED
current_range == previous_range -> EQUAL
```

### 9.3 Range containment

Apply the first matching rule only:

```text
H == PH and L == PL                 -> EXACT_MATCH
H <= PH and L >= PL                 -> INSIDE
H >= PH and L <= PL                 -> OUTSIDE
H > PH and L > PL                   -> SHIFTED_UP
H < PH and L < PL                   -> SHIFTED_DOWN
```

`INSIDE` and `OUTSIDE` therefore require at least one strict boundary because
the exact equality case is consumed first. The five codes are exhaustive for
two valid one-dimensional high/low intervals; no fallback code is permitted.
These are geometric facts, not a breakout signal or support/resistance
decision.

### 9.4 Current high versus previous high

```text
H > PH  -> ABOVE_PREVIOUS_HIGH
H < PH  -> BELOW_PREVIOUS_HIGH
H == PH -> AT_PREVIOUS_HIGH
```

### 9.5 Current low versus previous low

```text
L > PL  -> ABOVE_PREVIOUS_LOW
L < PL  -> BELOW_PREVIOUS_LOW
L == PL -> AT_PREVIOUS_LOW
```

### 9.6 Current close versus previous range

Apply in this exact order:

```text
C > PH  -> ABOVE_PREVIOUS_HIGH
C == PH -> AT_PREVIOUS_HIGH
C > PL  -> INSIDE_PREVIOUS_RANGE
C == PL -> AT_PREVIOUS_LOW
C < PL  -> BELOW_PREVIOUS_LOW
```

No code means favorable, unfavorable, actionable, confirmed, or tradable.

## 10. Status, reason, and first-failure mapping

Each non-READY result contains exactly one reason. The ordered mapping is:

| Priority | Status | Single reason | Meaning |
| --- | --- | --- | --- |
| 1 | `CANONICAL_GOLD_VOLATILITY_STRUCTURE_INPUT_INVALID` | `GOLD_VOLATILITY_STRUCTURE_INPUT_TYPE_INVALID` | top-level or nested exact shape/type invalid |
| 2 | `CANONICAL_GOLD_VOLATILITY_STRUCTURE_UPSTREAM_BLOCKED` | `GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_NOT_READY` | top-level G175 passed/status/code or fixed safety semantics not satisfied |
| 3 | `CANONICAL_GOLD_VOLATILITY_STRUCTURE_IDENTITY_INVALID` | `GOLD_VOLATILITY_STRUCTURE_SNAPSHOT_IDENTITY_INVALID` | bundle/symbol/reference identity invalid |
| 4 | `CANONICAL_GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INVALID` | `GOLD_VOLATILITY_STRUCTURE_TIMEFRAME_INPUT_INVALID` | timeframe order, period, bar order, completion, or OHLC relation invalid |
| 5 | `CANONICAL_GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT` | `GOLD_VOLATILITY_STRUCTURE_HISTORY_INSUFFICIENT` | any timeframe has fewer than two completed bars |
| 6 | `CANONICAL_GOLD_VOLATILITY_STRUCTURE_DECIMAL_INVALID` | `GOLD_VOLATILITY_STRUCTURE_DECIMAL_INPUT_INVALID` | fixed-point parse, arithmetic, representability, or formatting invalid |
| 7 | `CANONICAL_GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID` | `GOLD_VOLATILITY_STRUCTURE_RESULT_INVALID` | derived count, ordering, code, or invariant is contradictory |
| 8 | `CANONICAL_GOLD_VOLATILITY_STRUCTURE_SAFE_FAILURE` | `GOLD_VOLATILITY_STRUCTURE_EXCEPTION_SANITIZED` | unexpected exception at the public boundary |

READY is exactly:

```text
status_code = "CANONICAL_GOLD_VOLATILITY_STRUCTURE_READY"
reason_codes = ()
warning_codes = ()
```

The builder evaluates categories in the table order and stops at the first
failure. It does not retry, fallback, repair, sort, truncate, switch source,
change profile, catch an error and continue, or return partial timeframe facts.
An unexpected internal exception maps only to the terminal safe-failure pair;
exception text and internal state are never exposed.

## 11. Identity and failure clearing

A READY result copies the exact G175 source contract version, bundle schema
version, bundle id, sequence, symbols, and reference time. It contains exactly
four timeframe facts and the exact total pair count.

Every non-READY result must have:

```text
passed = False
identity_available = False
source_contract_version = None
bundle_schema_version = None
bundle_id = None
sequence = None
canonical_symbol = None
broker_symbol = None
reference_time_utc = None
timeframes = ()
total_pair_count = 0
warning_codes = ()
```

The fixed eight safety flags have the same values on every status. A failure
must not echo a malformed identifier, timestamp, price, bar, caller value,
exception, path, payload, checksum, token, or internal status.

## 12. Immutability and determinism

The builder must not modify the input snapshot, any nested record, tuple, or
string. A READY result is a fresh detached frozen object graph. Every
timeframe, pair tuple, and pair record is newly constructed for that call.

Repeated calls with equal exact inputs return equal values but distinct result
and nested object identities. Mutating or replacing a caller-owned reference
cannot alter another result or a later execution. The builder performs no
ambient I/O and has no hidden mutable registry or cache.

## 13. Safety meaning

Volatility and structure facts are observations only. In particular:

- `EXPANDED`, `OUTSIDE`, `ABOVE_PREVIOUS_HIGH`, or `UP` is not a buy signal;
- `CONTRACTED`, `INSIDE`, `BELOW_PREVIOUS_LOW`, or `DOWN` is not a sell signal;
- true range is not ATR, a spread limit, a risk amount, or position size;
- an adjacent high or low is not support, resistance, stop loss, take profit,
  invalidation, or breakout approval;
- READY means only that deterministic offline facts were constructed; and
- no result is Gate PASS, market-session approval, execution instruction, or
  trading permission.

## 14. Required contract vectors

A later tests-only work order must use immutable static vectors and must not
import or implement the future production module. It must lock at least:

1. exact public module, exports, interface, dataclass fields, annotations, and
   order;
2. complete G175 READY shape and value predicate plus strict built-in types;
3. exact M15/H1/H4/D1 order, periods, bar limits, and all-adjacent-pairs rule;
4. range, true range, signed/absolute body, wick, and adjacent-change values;
5. all finite direction, range, containment, high, low, and close codes;
6. equality boundaries, signed-zero normalization, very long fixed-point
   coefficients, and exact trailing zeros;
7. missing, extra, reordered, duplicate, alias, case-change, subclass,
   wrong-container, wrong-element, timestamp, OHLC, history, and Decimal
   failures;
8. all eight ordered status/reason mappings and category-swap probes;
9. failure identity/facts clearing and all fixed safety flags;
10. input and result immutability, fresh-object requirements, and repeated
    deterministic equality; and
11. no free text, path, payload, checksum, exception, policy, execution field,
    W7 analysis, economic window, or ReplayRunner authority.

Static vectors are tests-only evidence. They do not prove production types,
builder behavior, integration, activation, or verification.

## 15. Staged delivery

Later work must remain separately planned and approved in this order:

1. immutable static contract vectors for this exact G194 contract;
2. production types and the pure-memory builder;
3. genuine offline composition evidence through G185, G178, and this builder;
4. deterministic non-activating verification for this facts stage;
5. a separate contract and delivery for economic-window inputs;
6. a separately versioned ReplayRunner W6 stage covering reviewed W6 facts;
   and
7. only then, separately contracted W7 deterministic analysis.

No stage silently includes the next. Contract is not tests, tests are not
implementation, implementation is not integration, integration is not
activation, and activation is not verification.

## 16. WBS and architecture boundaries

- W1 remains the verified authority for Bundle v1 validation and
  DataQualityGate behavior.
- W5 remains verified only for ReplayRunner v1 canonical diagnostics.
- G175/G178 remain the authority for the snapshot contract and projector.
- G189/G191 remain the separate session and spread/freshness facts boundary.
- G192/G193 prove only their reviewed offline composition and deterministic
  non-activating verification boundary.
- G194 defines only this narrow contract. W6 remains `TESTS_ONLY`.
- Economic-window facts, ReplayRunner W6 staging, and W7-W21 remain separate
  and unauthorized.
- Reader activation, real MT4, EA calls, orders, execution, Demo activation,
  Live activation, and trading remain prohibited.

## 17. G194 acceptance checklist

G194 is acceptable only if:

- exactly one new contract document is added;
- the public function is keyword-only with exactly one G175 snapshot input;
- all three future public types have exact fields, order, annotations, and
  frozen/slotted requirements;
- the complete G175 READY predicate and exact four-timeframe authority are
  preserved without calling or copying the G178 projector;
- every accepted adjacent pair is processed exactly once in source order;
- Decimal calculations are unique, local, exact, fixed-point, and non-float;
- all structure-code equalities and first-match rules are unambiguous;
- all status/reason pairs, first-failure rules, failure clearing, and safety
  flags are exact;
- facts remain observations and cannot be interpreted as W7 analysis, a Gate,
  activation, execution, or trading permission;
- tests, production implementation, integration, activation, and verification
  remain unimplemented by G194; and
- ASCII, exact scope, isolation, and `git diff --check` checks pass.

This document is a contract, not runtime evidence. Its presence does not prove
that a volatility/structure builder exists or that any analysis, ReplayRunner
stage, reader, MT4, execution, activation, or trading capability is available.
