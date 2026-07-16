# Canonical Gold Economic Window Facts v1 Contract

Status: G199 contract only.

WBS package: W6.

Narrow capability transition: `POLICY_ONLY -> CONTRACT_ONLY`.

W6 package maturity remains `TESTS_ONLY`.

This document defines a deterministic, pure-memory, Demo-only and Read-only
contract for canonical XAUUSD/GOLD economic-event observation windows. It does
not implement contract vectors, production types, a builder, a calendar source
adapter, provider integration, fixture composition, verification, ReplayRunner
staging, activation, execution, or trading permission.

## 1. Purpose

G175-G198 provide reviewed market-facts, session/spread/freshness, and
volatility/structure boundaries. They deliberately do not define a canonical
economic-calendar authority or economic-window result.

G199 closes only the contract gap. It defines:

- one exact keyword-only pure-memory interface;
- one exact canonical calendar snapshot input owned by a future server-side
  adapter;
- exact frozen and slotted source, event, result, and nested facts types;
- the complete accepted G175 READY market snapshot predicate;
- one versioned server-owned relevance and observation-window profile;
- strict UTC, coverage, freshness, ordering, uniqueness, overlap, endpoint,
  nearest-event, and tie rules;
- deterministic status, reason, identity, clearing, and safety semantics; and
- staged delivery boundaries for all later work.

Economic-window facts are observations only. They do not say that the market
is open, that a broker permits trading, that risk is acceptable, that a trade
must be blocked, or that any order may be created or executed.

## 2. Explicit Non-Scope

This contract does not define or authorize:

- a calendar provider, provider account, provider identifier, credential,
  endpoint, request, response, raw payload, cache, database, or network call;
- filesystem, environment, settings, API, frontend, process, logging, or
  ambient-clock access;
- a production calendar adapter, validator, source registry, builder, fixture,
  or integration path;
- fallback to writer `market_session.is_major_news_window`, writer labels,
  diagnostics, paths, logs, or any legacy schema;
- market-open, broker-availability, holiday, weekend, rollover, spread,
  freshness, blackout, risk, order, or execution policy;
- event surprise, forecast, previous, actual, score, sentiment, direction,
  recommendation, confidence, opportunity, or invalidation logic;
- W7 analysis, RiskGate, PositionSizing, TradePlan, Shadow Mode, ExecutionGate,
  EA, order, execution, deployment, activation, or trading permission;
- a ReplayRunner W6 stage or any W7-W21 runtime capability; or
- verification of W6 as a package.

The old writer `is_major_news_window` boolean remains a non-authoritative
observation. It must not be copied into this contract, used as a fallback,
treated as a calendar snapshot, or interpreted as a result oracle.

## 3. Public Module and Interface

The future pure-memory module is:

```text
backend.app.services.canonical_gold_economic_window_facts
```

Its ordered `__all__` must be exactly:

```python
(
    "CanonicalGoldEconomicCalendarSnapshotV1",
    "CanonicalGoldEconomicCalendarUpstreamEvidenceV1",
    "CanonicalGoldEconomicEventSourceV1",
    "CanonicalGoldEconomicWindowFactsV1",
    "CanonicalGoldEconomicEventWindowFactsV1",
    "CanonicalGoldEconomicWindowSummaryV1",
    "build_canonical_gold_economic_window_facts_v1",
)
```

The only public function is:

```python
def build_canonical_gold_economic_window_facts_v1(
    *,
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1,
    economic_calendar_snapshot: CanonicalGoldEconomicCalendarSnapshotV1,
) -> CanonicalGoldEconomicWindowFactsV1:
    ...
```

Both arguments are keyword-only. Positional arguments, omitted arguments, and
additional parameters are invalid.

The caller cannot provide or override:

- a path, provider, endpoint, source mode, raw event, or raw payload;
- a clock or reference time;
- a calendar profile, relevance rule, impact rule, category list, search
  horizon, freshness limit, pre-window duration, or post-window duration;
- a validator, adapter, dependency, fallback, retry policy, or expected result;
- a Gate, blackout policy, risk policy, order policy, or output oracle; or
- MT4, account, strategy, execution, or trading state.

The typed calendar value is caller-supplied only in the narrow Python
composition sense. Construction of the dataclass is not calendar authority.
Only a later separately approved server-owned adapter may construct an accepted
calendar snapshot, and the builder must validate every field again.

## 4. Public Dataclass Rules

Every public type must use `@dataclass(frozen=True, slots=True)`. Field names,
field order, annotations, exact built-in scalar types, and exact built-in
container types are contract data.

No public type may have:

- a subclass, alias field, default field, optional extension, dynamic
  attribute, mapping view, iterator, mutable collection, or free-text field;
- a path, provider name, URL, credential, raw payload, checksum, digest,
  exception, traceback, internal token, or source status detail; or
- a Gate, permission, recommendation, order, or execution field other than the
  fixed negative safety flags in Section 13.

`bool` is not an `int`. A subclass of a built-in scalar or public dataclass is
invalid. A list is not a tuple. Missing, extra, reordered, duplicated, aliased,
case-changed, or unknown fields fail closed.

## 5. Canonical Calendar Source Types

### 5.1 CanonicalGoldEconomicCalendarSnapshotV1

The canonical calendar snapshot has exactly 12 fields in this order:

| # | Field | Exact annotation | Exact rule |
| ---: | --- | --- | --- |
| 1 | `contract_version` | `str` | exactly `"1.0"` |
| 2 | `calendar_schema_version` | `str` | exactly `"1.0"` |
| 3 | `calendar_snapshot_id` | `str` | Section 7 identity rule |
| 4 | `source_profile_version` | `str` | exactly `"canonical_gold_economic_calendar_source_v1"` |
| 5 | `generated_at_utc` | `str` | strict UTC Z timestamp |
| 6 | `coverage_start_utc` | `str` | strict UTC Z timestamp |
| 7 | `coverage_end_utc` | `str` | strict UTC Z timestamp |
| 8 | `events` | `tuple[CanonicalGoldEconomicEventSourceV1, ...]` | exact canonical ordered tuple |
| 9 | `upstream_evidence` | `CanonicalGoldEconomicCalendarUpstreamEvidenceV1` | exact accepted adapter evidence |
| 10 | `read_only` | `bool` | exactly `True` |
| 11 | `demo_only` | `bool` | exactly `True` |
| 12 | `contains_raw_provider_payload` | `bool` | exactly `False` |

The snapshot contains normalized canonical facts only. It must not retain a
provider response, provider event object, raw title, description, forecast,
actual value, previous value, URL, path, credential, locale, or timezone name.

### 5.2 CanonicalGoldEconomicCalendarUpstreamEvidenceV1

The safe upstream evidence record has exactly eight fields:

| # | Field | Exact annotation | Exact accepted value |
| ---: | --- | --- | --- |
| 1 | `adapter_passed` | `bool` | `True` |
| 2 | `adapter_status_code` | `str` | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY` |
| 3 | `schema_validated` | `bool` | `True` |
| 4 | `identity_validated` | `bool` | `True` |
| 5 | `timestamps_normalized` | `bool` | `True` |
| 6 | `same_snapshot_bound` | `bool` | `True` |
| 7 | `warning_codes` | `tuple[str, ...]` | exact empty built-in tuple |
| 8 | `raw_payload_discarded` | `bool` | `True` |

This record proves only that a future adapter accepted one canonical calendar
snapshot atomically. It does not expose provider identity or establish a Gate.

### 5.3 CanonicalGoldEconomicEventSourceV1

Each source event has exactly eight fields:

| # | Field | Exact annotation |
| ---: | --- | --- |
| 1 | `event_id` | `str` |
| 2 | `scheduled_at_utc` | `str` |
| 3 | `country_code` | `str` |
| 4 | `currency_code` | `str` |
| 5 | `event_category_code` | `str` |
| 6 | `impact_code` | `str` |
| 7 | `source_revision` | `int` |
| 8 | `event_status_code` | `str` |

The source event deliberately contains no human-authored title, description,
forecast, actual, previous, unit, free text, or provider field.

## 6. Result Types

### 6.1 CanonicalGoldEconomicWindowFactsV1

The result has exactly 31 fields in this order:

| # | Field | Exact annotation | READY value |
| ---: | --- | --- | --- |
| 1 | `contract_version` | `str` | `"1.0"` |
| 2 | `facts_profile_version` | `str` | `"canonical_gold_economic_window_profile_v1"` |
| 3 | `passed` | `bool` | `True` |
| 4 | `status_code` | `str` | `CANONICAL_GOLD_ECONOMIC_WINDOW_READY` |
| 5 | `reason_codes` | `tuple[str, ...]` | exact empty built-in tuple |
| 6 | `warning_codes` | `tuple[str, ...]` | exact empty built-in tuple |
| 7 | `identity_available` | `bool` | `True` |
| 8 | `source_contract_version` | `str | None` | copied exact G175 `contract_version` |
| 9 | `bundle_schema_version` | `str | None` | copied exact G175 value |
| 10 | `bundle_id` | `str | None` | copied exact G175 value |
| 11 | `sequence` | `int | None` | copied exact G175 value |
| 12 | `canonical_symbol` | `str | None` | `XAUUSD` |
| 13 | `broker_symbol` | `str | None` | `GOLD` |
| 14 | `reference_time_utc` | `str | None` | copied byte-for-byte from G175 |
| 15 | `calendar_contract_version` | `str | None` | copied exact calendar value |
| 16 | `calendar_schema_version` | `str | None` | copied exact calendar value |
| 17 | `calendar_snapshot_id` | `str | None` | copied exact calendar value |
| 18 | `calendar_source_profile_version` | `str | None` | copied exact calendar value |
| 19 | `calendar_generated_at_utc` | `str | None` | copied byte-for-byte |
| 20 | `calendar_coverage_start_utc` | `str | None` | copied byte-for-byte |
| 21 | `calendar_coverage_end_utc` | `str | None` | copied byte-for-byte |
| 22 | `event_windows` | `tuple[CanonicalGoldEconomicEventWindowFactsV1, ...]` | exact derived ordered tuple |
| 23 | `summary` | `CanonicalGoldEconomicWindowSummaryV1 | None` | exact derived summary |
| 24 | `read_only` | `bool` | `True` |
| 25 | `demo_only` | `bool` | `True` |
| 26 | `is_tradable` | `bool` | `False` |
| 27 | `can_execute` | `bool` | `False` |
| 28 | `is_trading_permission` | `bool` | `False` |
| 29 | `is_execution_instruction` | `bool` | `False` |
| 30 | `allowed_to_call_ea` | `bool` | `False` |
| 31 | `allowed_to_modify_risk` | `bool` | `False` |

### 6.2 CanonicalGoldEconomicEventWindowFactsV1

Each derived relevant event has exactly 14 fields:

| # | Field | Exact annotation |
| ---: | --- | --- |
| 1 | `event_id` | `str` |
| 2 | `scheduled_at_utc` | `str` |
| 3 | `country_code` | `str` |
| 4 | `currency_code` | `str` |
| 5 | `event_category_code` | `str` |
| 6 | `impact_code` | `str` |
| 7 | `source_revision` | `int` |
| 8 | `window_start_utc` | `str` |
| 9 | `window_end_utc` | `str` |
| 10 | `event_offset_microseconds` | `int` |
| 11 | `window_start_offset_microseconds` | `int` |
| 12 | `window_end_offset_microseconds` | `int` |
| 13 | `window_relation_code` | `str` |
| 14 | `is_active_observation_window` | `bool` |

`window_relation_code` is exactly one of `UPCOMING`, `ACTIVE`, or `ELAPSED`.
It describes reference-time membership only. It is not a blackout decision.

### 6.3 CanonicalGoldEconomicWindowSummaryV1

The summary has exactly ten fields:

| # | Field | Exact annotation |
| ---: | --- | --- |
| 1 | `calendar_age_microseconds` | `int` |
| 2 | `relevant_event_count` | `int` |
| 3 | `active_window_count` | `int` |
| 4 | `inside_any_observation_window` | `bool` |
| 5 | `active_event_ids` | `tuple[str, ...]` |
| 6 | `nearest_previous_event_id` | `str | None` |
| 7 | `nearest_previous_event_offset_microseconds` | `int | None` |
| 8 | `nearest_next_event_id` | `str | None` |
| 9 | `nearest_next_event_offset_microseconds` | `int | None` |
| 10 | `highest_active_impact_code` | `str` |

`highest_active_impact_code` is exactly `NONE`, `MEDIUM`, or `HIGH`. No
summary field says safe, unsafe, allowed, blocked, favorable, or tradable.

## 7. Strict Identity and Code Rules

### 7.1 Calendar identity

`calendar_snapshot_id` must be a built-in `str`, 16 through 64 ASCII
characters, and match exactly:

```text
[A-Za-z0-9._-]+
```

It is unique only for one canonical adapter snapshot. It is not a provider
request id, credential, checksum, path, or bundle id.

### 7.2 Event identity

Every `event_id` must be a built-in `str`, 8 through 64 ASCII characters, and
match exactly:

```text
[A-Za-z0-9._-]+
```

Event ids must be unique in the calendar snapshot. The result preserves each
accepted id byte-for-byte. The builder must not synthesize, hash, normalize,
redact, or replace it.

### 7.3 Exact source codes

Every accepted v1 source event has `country_code == "US"` and
`currency_code == "USD"`. A future adapter must exclude other countries and
currencies before constructing the canonical snapshot; the builder must not
filter or reinterpret an unknown source code. Source values must be uppercase
built-in strings.

`impact_code` is exactly one of the ordered source codes:

```text
LOW, MEDIUM, HIGH
```

`event_status_code` is exactly one of:

```text
SCHEDULED, CANCELLED
```

`source_revision` is an exact positive built-in `int`. Revision is a fact used
for identity validation only. It does not choose a more favorable event.

The exact ordered event-category vocabulary is:

```text
FOMC_RATE_DECISION
FOMC_STATEMENT
FOMC_PRESS_CONFERENCE
US_CPI
US_CORE_CPI
US_PCE
US_CORE_PCE
US_NONFARM_PAYROLLS
US_UNEMPLOYMENT_RATE
US_GDP
US_RETAIL_SALES
US_ISM_MANUFACTURING
US_ISM_SERVICES
```

Missing, unknown, aliased, lowercase, mixed-case, whitespace-padded, or
subclassed codes are invalid. A future vocabulary change requires a new
contract/profile version.

## 8. Complete Accepted G175 Predicate

The market input must be exact built-in
`CanonicalGoldMarketFactsSnapshotV1`, not a subclass or look-alike. Its 24
fields, slots, annotations, nested types, tuple containers, and order must
match the published G175/G178 production type exactly.

An accepted market snapshot satisfies all of the following:

1. `contract_version == "1.0"`, `passed is True`, status is exactly
   `CANONICAL_GOLD_MARKET_FACTS_READY`, and both code tuples are empty.
2. `identity_available is True`; bundle schema version is `"1.0"`;
   `bundle_id` satisfies the W1 16 through 64 ASCII identifier rule;
   `sequence` is a positive exact built-in `int`; symbols are exactly
   `XAUUSD` and `GOLD`; and `reference_time_utc` is strict UTC Z.
3. Quote, four timeframes in M15/H1/H4/D1 order, all exact bar records, symbol
   facts, and freshness facts satisfy the complete frozen G175 value
   predicate, including strict built-in types, fixed-point strings, quote
   identities, strictly increasing completed bars, positive OHLC, valid OHLC
   relations, and nonnegative freshness ages.
4. The eight fixed safety flags are exactly Read-only, Demo-only, non-tradable,
   non-executing, non-permission, non-instruction, no EA, and no risk change.

The builder must not call G178 or repair the market snapshot. A failed,
warning-bearing, partial, malformed, polluted, or contradictory snapshot is
rejected before calendar-derived facts are returned.

## 9. UTC Parsing and Integer Time Arithmetic

### 9.1 Accepted timestamp syntax

Every market and calendar timestamp uses exactly one of:

```text
YYYY-MM-DDTHH:MM:SSZ
YYYY-MM-DDTHH:MM:SS.ffffffZ
```

Fractional precision is one through six digits. Offsets, naive values,
lowercase `z`, whitespace, leap seconds, more than six fractional digits, and
alternate renderings are invalid. Parsing must produce an aware UTC datetime.

The result copies input identity timestamps byte-for-byte. Derived
`window_start_utc` and `window_end_utc` use the same syntax. They omit the
fraction only when microseconds are zero; otherwise they contain exactly six
fractional digits. No locale or timezone database is used.

### 9.2 Integer microseconds

All comparisons and offsets use exact integer microseconds. Compute a delta as:

```text
delta_microseconds = (
    delta.days * 86400 * 1000000
    + delta.seconds * 1000000
    + delta.microseconds
)
```

Do not use `total_seconds()`, float arithmetic, Decimal arithmetic, rounding,
clamping, tolerance, or ambient time.

`reference_time_utc` from the G175 snapshot is the only clock. The calendar
snapshot cannot override it.

## 10. Calendar Freshness, Coverage, and Ordering

The server-owned v1 constants are:

```text
contract_version = "1.0"
facts_profile_version = "canonical_gold_economic_window_profile_v1"
calendar_source_profile_version = "canonical_gold_economic_calendar_source_v1"
calendar_maximum_age_microseconds = 300000000
search_horizon_seconds = 86400
```

Calendar validity requires:

1. `generated_at_utc <= reference_time_utc`;
2. calendar age is at most `300000000` microseconds;
3. `coverage_start_utc < coverage_end_utc`;
4. `coverage_start_utc <= reference_time_utc - 86400 seconds`;
5. `coverage_end_utc > reference_time_utc + 86400 seconds`; and
6. every event timestamp is inside the half-open calendar coverage interval
   `[coverage_start_utc, coverage_end_utc)`.

The source `events` tuple may be empty. When nonempty, it must already be in
strict ascending `(scheduled_at_utc, event_id)` order. Timestamp comparison is
chronological; equal timestamps use ASCII event-id order. Event ids are unique
across the whole tuple.

The builder must validate this order and reject duplicates. It must not sort,
deduplicate, merge, truncate, reorder, or repair events.

## 11. Server-Owned Relevance and Window Profile

The caller and calendar source cannot select relevance or window durations.
The v1 facts profile uses these exact rules:

1. the event status must be `SCHEDULED`;
2. country and currency must be exactly `US` and `USD`;
3. category must be one of the exact Section 7.3 category codes;
4. `HIGH` events use `pre_window_seconds=1800` and
   `post_window_seconds=1800`;
5. `MEDIUM` events use `pre_window_seconds=900` and
   `post_window_seconds=900`; and
6. `LOW` and `CANCELLED` events remain valid calendar source facts but are not
   included in the derived relevant-event tuple.

No impact or category is inferred from a title, provider rank, writer boolean,
forecast, actual value, market move, spread, volatility, or strategy state.

Only relevant events whose scheduled time is inside the half-open search
interval

```text
[reference_time_utc - 86400 seconds,
 reference_time_utc + 86400 seconds)
```

appear in `event_windows`. Filtering preserves the canonical source order.
The builder does not sort the filtered result.

## 12. Window, Overlap, Nearest, and Tie Algorithm

For each included event:

```text
window_start = scheduled_at_utc - pre_window_seconds
window_end = scheduled_at_utc + post_window_seconds
event_offset = scheduled_at_utc - reference_time_utc
window_start_offset = window_start - reference_time_utc
window_end_offset = window_end - reference_time_utc
```

The observation window is half-open:

```text
window_start <= reference_time_utc < window_end
```

Therefore:

- exact window start is `ACTIVE`;
- exact scheduled time is `ACTIVE`;
- exact window end is `ELAPSED`;
- before window start is `UPCOMING`; and
- no endpoint is widened by a tolerance.

Overlapping windows remain separate event facts. `active_event_ids` contains
all active event ids in the preserved `event_windows` order.
`active_window_count == len(active_event_ids)`, and
`inside_any_observation_window` is exactly `active_window_count > 0`.

The nearest previous event is selected from relevant included events with
`scheduled_at_utc <= reference_time_utc`. Choose the greatest scheduled time.
The nearest next event is selected from relevant included events with
`scheduled_at_utc > reference_time_utc`. Choose the least scheduled time. An
event exactly at reference time is previous, not next.

When multiple candidates share the selected scheduled time, use this exact
tie priority:

```text
HIGH before MEDIUM, then event_id in ascending ASCII order
```

The selected previous offset is nonpositive. The selected next offset is
strictly positive. When a side has no candidate, both its id and offset are
`None`.

`highest_active_impact_code` is `HIGH` if any active event is HIGH, otherwise
`MEDIUM` if any active event is MEDIUM, otherwise `NONE`.

## 13. Fixed Safety Flags and Meaning

Every result, including every failure, has these exact values:

| Field | Exact value |
| --- | --- |
| `read_only` | `True` |
| `demo_only` | `True` |
| `is_tradable` | `False` |
| `can_execute` | `False` |
| `is_trading_permission` | `False` |
| `is_execution_instruction` | `False` |
| `allowed_to_call_ea` | `False` |
| `allowed_to_modify_risk` | `False` |

In particular:

- `inside_any_observation_window=True` is not a RiskGate block;
- `inside_any_observation_window=False` is not permission to trade;
- `HIGH`, `MEDIUM`, `ACTIVE`, `UPCOMING`, or `ELAPSED` is not a signal;
- an empty calendar is not proof that no real-world event exists;
- READY means only that deterministic facts were constructed from accepted
  bounded inputs; and
- no field authorizes market access, an EA call, an order, or execution.

A future RiskGate may consume separately reviewed facts under its own
server-owned policy. It must not reinterpret this facts contract as a Gate.

## 14. Status, Reason, and First-Failure Mapping

READY is exactly:

```text
passed = True
status_code = "CANONICAL_GOLD_ECONOMIC_WINDOW_READY"
reason_codes = ()
warning_codes = ()
identity_available = True
```

Every non-READY result contains exactly one reason. The ordered first-failure
mapping is:

| Priority | Status | Single reason | Meaning |
| ---: | --- | --- | --- |
| 1 | `CANONICAL_GOLD_ECONOMIC_WINDOW_INPUT_INVALID` | `GOLD_ECONOMIC_WINDOW_INPUT_TYPE_INVALID` | top-level or nested exact type, shape, field, or container invalid |
| 2 | `CANONICAL_GOLD_ECONOMIC_WINDOW_UPSTREAM_BLOCKED` | `GOLD_ECONOMIC_WINDOW_MARKET_SNAPSHOT_NOT_READY` | G175 passed/status/code or fixed safety semantics not satisfied |
| 3 | `CANONICAL_GOLD_ECONOMIC_WINDOW_MARKET_IDENTITY_INVALID` | `GOLD_ECONOMIC_WINDOW_MARKET_IDENTITY_INVALID` | bundle, symbol, or reference identity invalid |
| 4 | `CANONICAL_GOLD_ECONOMIC_WINDOW_MARKET_VALUE_INVALID` | `GOLD_ECONOMIC_WINDOW_MARKET_FACTS_INVALID` | quote, timeframe, bar, symbol, freshness, or nested G175 value invariant invalid |
| 5 | `CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_AUTHORITY_INVALID` | `GOLD_ECONOMIC_WINDOW_CALENDAR_AUTHORITY_INVALID` | upstream evidence, Read-only/Demo-only flags, or raw-payload isolation invalid |
| 6 | `CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_IDENTITY_INVALID` | `GOLD_ECONOMIC_WINDOW_CALENDAR_IDENTITY_INVALID` | calendar contract/schema/source-profile version or snapshot id invalid |
| 7 | `CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_FRESHNESS_INVALID` | `GOLD_ECONOMIC_WINDOW_CALENDAR_FRESHNESS_INVALID` | generated time is future, stale, or malformed |
| 8 | `CANONICAL_GOLD_ECONOMIC_WINDOW_CALENDAR_COVERAGE_INVALID` | `GOLD_ECONOMIC_WINDOW_CALENDAR_COVERAGE_INVALID` | coverage interval or required horizon invalid |
| 9 | `CANONICAL_GOLD_ECONOMIC_WINDOW_EVENT_INVALID` | `GOLD_ECONOMIC_WINDOW_EVENT_INPUT_INVALID` | event identity, code, revision, timestamp, uniqueness, order, or coverage invalid |
| 10 | `CANONICAL_GOLD_ECONOMIC_WINDOW_RESULT_INVALID` | `GOLD_ECONOMIC_WINDOW_RESULT_INVALID` | derived order, count, offset, relation, nearest selection, tie, or summary contradictory |
| 11 | `CANONICAL_GOLD_ECONOMIC_WINDOW_SAFE_FAILURE` | `GOLD_ECONOMIC_WINDOW_EXCEPTION_SANITIZED` | unexpected public-boundary exception |

The builder evaluates categories in table order and stops at the first
failure. It does not retry, fallback, catch and continue, return partial facts,
change profile, or switch source.

`warning_codes` is the exact empty built-in tuple on every result. Unknown,
extra, duplicated, reordered, subclassed, or status/reason-swapped codes are
invalid.

## 15. Failure Identity and Facts Clearing

Only READY may set `identity_available=True`.

Every non-passed result has exactly:

```text
identity_available = False
source_contract_version = None
bundle_schema_version = None
bundle_id = None
sequence = None
canonical_symbol = None
broker_symbol = None
reference_time_utc = None
calendar_contract_version = None
calendar_schema_version = None
calendar_snapshot_id = None
calendar_source_profile_version = None
calendar_generated_at_utc = None
calendar_coverage_start_utc = None
calendar_coverage_end_utc = None
event_windows = ()
summary = None
warning_codes = ()
```

A failure does not echo malformed ids, timestamps, codes, caller values,
provider facts, paths, payloads, credentials, checksums, exceptions, internal
status, or partially derived events.

Unexpected exceptions are caught only at the public boundary and map only to
the terminal SAFE_FAILURE pair. Exception text and traceback data must not be
returned or logged by this boundary.

## 16. Immutability, Determinism, and Isolation

The future builder must not modify either input or any nested record, tuple, or
string. Every call returns a fresh result and fresh nested facts. Equal exact
inputs return value-equal results with distinct result and nested object
identities.

The result must be detached from both inputs. Mutating an authoring copy,
replacing a caller reference, or invoking another equal run cannot alter an
existing result or later execution.

The future module may import only standard-library pure calculation types, the
published G175/G178 snapshot result types, and its own public calendar source
types. It must not import or call:

- G178, G182, G185, G191, G196, W1 reader/Gate, G151/G153 diagnostics, or W5
  ReplayRunner;
- a provider SDK, HTTP client, socket, filesystem reader, environment,
  settings, API, database, cache, logger, process, or ambient clock; or
- W7 analysis, RiskGate, PositionSizing, TradePlan, ExecutionGate, MT4, or EA.

It must not sort, deduplicate, repair, synthesize, interpolate, enrich, fetch,
retry, fallback, change provider, use writer news flags, or accept dependency
injection.

## 17. Required Contract Vectors

A later tests-only work order must use immutable static vectors and must not
import or implement the future production module. It must lock at least:

1. exact module, ordered exports, keyword-only two-input interface, dataclass
   fields, annotations, slots, frozen semantics, and built-in containers;
2. the complete G175 READY predicate, identity, nested market facts, and fixed
   safety flags;
3. exact 12-field calendar snapshot, 8-field upstream evidence, 8-field source
   event, 31-field result, 14-field event facts, and 10-field summary;
4. calendar and event identifier regex, lengths, uniqueness, code vocabulary,
   source revision, status, and canonical source order;
5. strict UTC parsing, exact integer-microsecond algorithm, future/stale
   calendar cases, required coverage horizon, and event coverage;
6. HIGH/MEDIUM relevance, LOW/CANCELLED exclusion, fixed pre/post durations,
   search horizon, and no writer-boolean fallback;
7. half-open start/scheduled/end endpoints, overlapping windows, active-event
   order, previous/next selection, exact-at-reference behavior, and
   HIGH/MEDIUM/event-id tie priority;
8. all eleven ordered failure categories, exact status/reason pairing, category
   swaps, empty warning tuple, failure clearing, and fixed safety flags;
9. missing, extra, reordered, duplicate, alias, case-change, subclass,
   wrong-container, wrong-element, timestamp, identity, code, order, coverage,
   and contradiction mutations;
10. input immutability, fresh detached result graphs, repeated deterministic
    equality, pollution isolation, and sanitized exceptions; and
11. absence of free text, provider detail, path, payload, checksum, exception,
    Gate, permission, recommendation, execution, or trading authority.

Static vectors are tests-only evidence. They do not prove production types,
builder behavior, calendar authority, integration, activation, or
verification.

## 18. Staged Delivery

Later work must remain separately planned and approved in this order:

1. immutable static contract vectors for this exact G199 contract;
2. production source/result types and the pure-memory builder using controlled
   canonical calendar snapshots only;
3. a separate server-owned calendar source-adapter contract and immutable
   adapter vectors;
4. bounded adapter implementation and fixed offline calendar fixture evidence,
   with no provider activation;
5. genuine offline composition through G185, G178, the approved calendar
   adapter/fixture, and the G199 builder;
6. deterministic non-activating verification for that composition;
7. any additional later W6 facts/features under separate contracts; and
8. a separately versioned ReplayRunner W6 stage covering reviewed W6 facts
   before W7.

No stage silently includes the next. Contract is not tests, tests are not
implementation, implementation is not integration, integration is not
activation, and activation is not verification.

## 19. WBS and Capability Boundaries

- W1 remains the verified authority for Bundle v1 validation and
  DataQualityGate behavior.
- W5 remains verified only for ReplayRunner v1 canonical diagnostics.
- G175-G198 remain the reviewed authority for their existing market/session/
  volatility boundaries; G199 does not modify them.
- G199 defines only the economic-window contract. W6 remains `TESTS_ONLY`.
- W7-W21 remain unchanged and unauthorized.
- The old writer `is_major_news_window` remains non-authoritative.
- A READY economic-window result is not a Gate result or trading permission.
- Reader activation, real MT4, calendar-provider activation, EA, order,
  execution, Demo activation, Live activation, and trading remain prohibited.

## 20. G199 Acceptance Checklist

G199 is acceptable only when:

- this document is the only added file;
- the interface has exactly two keyword-only typed inputs and no dependency or
  policy override;
- every public type, field, order, annotation, code, and built-in container is
  exact;
- the complete G175 READY predicate and market identity remain authoritative;
- the future server-owned calendar adapter is the sole calendar source
  authority and raw provider data cannot cross the boundary;
- writer `is_major_news_window` is explicitly non-authoritative;
- UTC parsing, integer microseconds, freshness, coverage, canonical event order,
  relevance, windows, overlap, nearest-event, and tie rules are deterministic;
- all status/reason pairs, first-failure priority, clearing, immutability, and
  fixed safety flags are complete;
- economic-window facts are not represented as Gate, blackout, permission,
  recommendation, order, execution, or trading authority;
- vectors, production, adapter, composition, verification, ReplayRunner,
  activation, and W7-W21 remain separately staged;
- W6 remains `TESTS_ONLY`; and
- exact scope, ASCII, isolation, and `git diff --check` checks pass.
