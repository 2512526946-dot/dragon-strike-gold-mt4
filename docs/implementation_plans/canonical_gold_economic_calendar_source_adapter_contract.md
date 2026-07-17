# Canonical Gold Economic Calendar Source Adapter v1 Contract

Status: G202 contract only.

WBS package: W6.

Narrow capability transition: `POLICY_ONLY -> CONTRACT_ONLY`.

W6 package maturity remains `TESTS_ONLY`.

This document defines the future server-owned, internal-only source-adapter
boundary that may construct one exact
`CanonicalGoldEconomicCalendarSnapshotV1` for the G201 economic-window
builder. It does not implement contract vectors, a fixture asset, a fixture
reader, production adapter behavior, provider integration, composition,
verification, ReplayRunner staging, activation, execution, or trading
permission.

## 1. Purpose

G199 and G201 accept an exact canonical calendar snapshot, but they do not
own a source, path, reader, provider, clock, or source-selection policy. G202
freezes the missing boundary between a future fixed offline calendar fixture
and that accepted pure-memory input.

The adapter must:

- keep path, reference time, schema, profile, identity, policy, dependency,
  and oracle authority on the server;
- read at most one fixed offline fixture in one attempt;
- validate one exact fixture document without sorting, repairing, retrying,
  or switching source;
- construct fresh G201-owned calendar source records;
- return one strict, sanitized adapter result;
- discard parser-owned and raw fixture data before returning; and
- preserve Demo-only, Read-only, non-execution, and non-trading boundaries.

An adapter READY result is calendar input evidence only. It is not a
DataQualityGate PASS, market readiness, an approved analysis window,
activation, execution authority, or trading permission.

## 2. Explicit Non-Scope

G202 does not:

- create or modify a calendar fixture asset;
- create immutable contract vectors;
- implement the future adapter module or fixture reader;
- connect a network, provider SDK, API, database, cache, queue, browser,
  environment variable, settings object, or ambient clock;
- call the G201 economic-window builder;
- call G185, G178, ReplayRunner, an API route, reader activation, MT4, an EA,
  an order, execution code, or trading code;
- define provider credentials, refresh schedules, deployment configuration,
  or runtime source selection;
- implement genuine fixture composition or deterministic verification;
- implement later W6 facts or features; or
- change W1, W5, W6, W7-W21, the weighted WBS, or any policy authority.

No statement in this document authorizes a future provider or live calendar
source. A provider adapter requires a separate contract, tests,
implementation, integration, activation, and verification sequence.

## 3. Ownership and Authority

### 3.1 G201 ownership

G201 owns these public source records and their accepted value semantics:

- `CanonicalGoldEconomicCalendarSnapshotV1`;
- `CanonicalGoldEconomicCalendarUpstreamEvidenceV1`; and
- `CanonicalGoldEconomicEventSourceV1`.

The future adapter imports these exact types from
`canonical_gold_economic_window_facts`. It must not redefine, subclass,
re-export, or maintain parallel versions of them. It must not copy the G201
economic-window builder, result mapping, event-window calculations, nearest
event logic, or summary logic.

The adapter owns only fixture-bound authority, fixture validation, canonical
calendar source construction, and its own adapter result envelope.

### 3.2 Server-owned authority

Only an approved internal integration may construct the private authority
capsule. No request, query, header, body, cookie, frontend state, plugin,
environment variable, working directory, arbitrary dependency-injection
caller, fixture field, provider field, writer field, market snapshot, or
client may provide or override:

- the allowed root or fixture path;
- the reference time or clock;
- the expected calendar identity;
- schema or source-profile versions;
- file-size, age, coverage, event-count, or search-horizon policy;
- reader, parser, validator, adapter, provider, fallback, or oracle;
- expected status or reason; or
- safety flags.

Possessing a calendar snapshot, fixture-shaped object, parsed JSON object,
or look-alike authority independently proves nothing. Authority exists only
when the adapter receives the module-private token in an exact private
authority record and performs its complete bounded call in one stack.

### 3.3 Internal-only boundary

The adapter function is an internal service boundary. It must not be called
by an API router, frontend layer, plugin, strategy, risk component, MT4
integration, EA, execution component, or arbitrary application caller.

No public result may contain the private authority, path, parser object, raw
fixture document, checksum, token, exception, traceback, policy object, or
internal source status.

## 4. Future Module and Interfaces

The future production module is:

```text
backend/app/services/canonical_gold_economic_calendar_source_adapter.py
```

Its exact public exports are:

```python
__all__ = (
    "CanonicalGoldEconomicCalendarSourceAdapterResultV1",
    "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
)
```

The only public function is:

```python
def build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
    *,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    ...
```

The function is keyword-only and has exactly one parameter. The authority
type is private, frozen, and slotted. It is not exported or re-exported. The
function rejects subclasses, look-alikes, additional parameters, positional
arguments, and any authority without the exact module-private token identity.

### 4.1 Approved private result seams

The adapter module alone owns these pure-memory private helpers:

```python
def _is_safe_canonical_gold_economic_calendar_source_adapter_result_v1(
    *,
    adapter_result: object,
) -> bool:
    ...

def _build_canonical_gold_economic_calendar_source_adapter_safe_failure_v1(
) -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    ...
```

The validator verifies the exact adapter result and, when present, the exact
G201 calendar snapshot. It performs no I/O and returns false on every invalid
input or internal validation exception. The sanitizer returns a fresh exact
SAFE_FAILURE result with no snapshot. A later approved integration boundary
must reuse these helpers and must not copy result validation, status mapping,
or failure construction.

These helpers are not public exports. No API, provider, ReplayRunner, or
arbitrary caller may import them.

The future implementation must move the existing G201 calendar source-shape
and accepted-value checks behind one explicitly approved G201-owned private
pure-memory seam and reuse that seam from the adapter result validator. It
must not copy those checks into a parallel adapter-side snapshot validator.
Raw fixture parsing and fixture-authority checks remain adapter-owned because
they occur before a G201 snapshot exists. This contract does not add that seam
or modify G201.

## 5. Private Authority and Policy Types

### 5.1 Expected identity

`_CanonicalGoldEconomicCalendarExpectedIdentityV1` is a frozen, slotted
dataclass with exactly these fields in order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `calendar_snapshot_id` | built-in `str` |
| 2 | `generated_at_utc` | built-in `str` |
| 3 | `coverage_start_utc` | built-in `str` |
| 4 | `coverage_end_utc` | built-in `str` |

Every string must satisfy the exact G199 ASCII identifier or UTC rule for its
field. The fixed docs-fixture authority uses exactly:

```text
calendar_snapshot_id = "canonical-gold-economic-calendar-docs-fixture-v1"
generated_at_utc = "2026-07-10T02:29:05.000000Z"
coverage_start_utc = "2026-07-09T02:30:05.000000Z"
coverage_end_utc = "2026-07-11T02:30:05.000001Z"
```

These values are server-owned and may not be supplied by the fixture document
as an oracle. The document values must equal this expected identity.

### 5.2 Read policy

`_CanonicalGoldEconomicCalendarReadPolicyV1` is a frozen, slotted dataclass
with exactly these fields and exact built-in integer values in order:

| Order | Field | Value |
| ---: | --- | ---: |
| 1 | `maximum_fixture_bytes` | `1048576` |
| 2 | `maximum_calendar_events` | `512` |
| 3 | `maximum_calendar_age_microseconds` | `300000000` |
| 4 | `maximum_coverage_span_microseconds` | `259200000000` |
| 5 | `search_horizon_microseconds` | `86400000000` |
| 6 | `maximum_read_attempts` | `1` |

Built-in `bool`, integer subclasses, floats, strings, `Decimal`, aliases, or
different values are invalid. The adapter does not derive or widen policy
from fixture contents.

### 5.3 Authority capsule

`_CanonicalGoldEconomicCalendarSourceAuthorityV1` is a frozen, slotted
dataclass with exactly these fields in order:

| Order | Field | Exact type or value |
| ---: | --- | --- |
| 1 | `authority_token` | exact built-in `object` identity held by the module |
| 2 | `allowed_root` | exact concrete platform `WindowsPath` or `PosixPath` |
| 3 | `fixture_path` | same exact concrete platform path type as `allowed_root` |
| 4 | `reference_time_utc` | exact aware UTC `datetime.datetime` |
| 5 | `expected_identity` | exact `_CanonicalGoldEconomicCalendarExpectedIdentityV1` |
| 6 | `read_policy` | exact `_CanonicalGoldEconomicCalendarReadPolicyV1` |
| 7 | `calendar_schema_version` | built-in `str`, exactly `"1.0"` |
| 8 | `source_profile_version` | built-in `str`, exactly `"canonical_gold_economic_calendar_source_v1"` |

The server factory constructs both path fields through `pathlib.Path`. Their
runtime types must be the platform's exact concrete `WindowsPath` or
`PosixPath` class and must match. Built-in strings, `PurePath`, the `Path`
factory class itself, concrete-path subclasses, wrong-platform paths, and
other path-like objects are invalid.

`fixture_path` must resolve to one fixed regular file beneath `allowed_root`.
Containment, symlink, reparse-point, parent, extension, and regular-file
checks occur before the read. The repository-relative built-in path-parts tuple
is exactly:

```python
(
    "docs",
    "architecture",
    "fixtures",
    "canonical-gold-economic-calendar-v1",
    "economic_calendar.json",
)
```

The server factory resolves those parts from the repository root. Neither the
relative parts nor the resolved path may be overridden, and neither enters a
public result.

`reference_time_utc` has exact runtime type `datetime.datetime`, non-null
`tzinfo`, and `utcoffset() == datetime.timedelta(0)`. The fixed docs-fixture
composition authority uses exactly
`datetime.datetime(2026, 7, 10, 2, 30, 5, tzinfo=datetime.UTC)`, the same
server-owned reference instant as the G185 market fixture. The adapter never
calls an ambient clock.

Invalid authority fails before any fixture read.

## 6. Private Fixture Schema

The future fixture reader uses a structured JSON parser that preserves object
pairs long enough to reject duplicate keys. It must not use string scanning
or parse into an object that silently discards duplicates before validation.

The top-level fixture document contains exactly these seven keys in order:

| Order | Key | Exact JSON value |
| ---: | --- | --- |
| 1 | `fixture_contract_version` | string, exactly `"1.0"` |
| 2 | `calendar_schema_version` | string, exactly `"1.0"` |
| 3 | `calendar_snapshot_id` | G199-valid ASCII identifier string |
| 4 | `generated_at_utc` | strict canonical UTC `Z` string |
| 5 | `coverage_start_utc` | strict canonical UTC `Z` string |
| 6 | `coverage_end_utc` | strict canonical UTC `Z` string |
| 7 | `events` | JSON array containing zero through 512 event objects |

Each event object contains exactly these eight keys in order:

| Order | Key | Exact JSON value |
| ---: | --- | --- |
| 1 | `event_id` | G199-valid ASCII identifier string |
| 2 | `scheduled_at_utc` | strict canonical UTC `Z` string |
| 3 | `country_code` | string from the closed G199 enum |
| 4 | `currency_code` | string from the closed G199 enum |
| 5 | `event_category_code` | string from the closed G199 enum |
| 6 | `impact_code` | string from the closed G199 enum |
| 7 | `source_revision` | built-in JSON integer, zero or greater |
| 8 | `event_status_code` | string from the closed G199 enum |

The parser freezes one private detached document record and one private
detached event record per event. Missing, extra, reordered, duplicated,
aliased, case-changed, subclassed, wrong-container, wrong-element, non-ASCII,
or out-of-domain values are invalid.

Events must already be in the exact G199 canonical order by
`(scheduled_at_utc, event_id)`. Event IDs are unique. Equal scheduled times
use ASCII event-ID order. The adapter validates this order and never sorts,
deduplicates, repairs, or rewrites the fixture.

The fixture document is private read evidence. It is never returned, logged,
cached, persisted elsewhere, exposed to diagnostics, or retained after
canonical source construction.

## 7. Unique Bounded Algorithm

The future adapter has exactly this order:

1. Require the exact private authority, token identity, concrete path types,
   UTC reference time, expected identity, read policy, schema version, and
   source-profile version. Capture immutable authority values for drift
   checks. Failure returns AUTHORITY_INVALID with zero reads.
2. Validate fixed path containment and safety under `allowed_root`. Failure
   returns AUTHORITY_INVALID with zero file-content reads.
3. Perform exactly one bounded read of `fixture_path`. Reject missing,
   inaccessible, non-regular, empty, or oversized content. Never retry or
   read a second source.
4. Decode strict UTF-8 and parse one JSON document while preserving key pairs
   for duplicate detection. Reject a byte-order mark, trailing content,
   non-JSON values, duplicate keys, non-finite numeric tokens, or parser
   ambiguity.
5. Require the exact top-level and event shapes from section 6.
6. Require exact equality to the server-owned expected identity, schema, and
   source-profile authority. A fixture value cannot change authority.
7. Parse each timestamp once using the G199 strict UTC `Z` algorithm and
   integer microsecond conversion. Require real UTC calendar dates. The
   adapter validates canonical strings and copies them unchanged; it does not
   normalize malformed input.
8. Require generated time not later than reference time, calendar age not
   greater than 300000000 microseconds, coverage start not after reference,
   coverage end not before reference, full 86400000000-microsecond search
   horizon on both sides, and total coverage span not greater than
   259200000000 microseconds.
9. Require zero through 512 events, exact canonical event order, unique IDs,
   valid closed codes, non-negative exact revisions, and every G199 event
   invariant. Do not select, filter, rank, or derive event windows.
10. Recheck captured authority, path, expected identity, policy, frozen
    document, and frozen event values for substitution or mutation. Any drift
    is invalid.
11. Construct fresh exact G201 event records, one fresh exact G201 upstream
    evidence record, and one fresh exact G201 calendar snapshot. No
    parser-owned container or raw document may be reachable from the result.
12. Validate the complete adapter result exactly once through the
    adapter-owned pure-memory result validator. An exact `False` return maps
    only to RESULT_INVALID, without a snapshot and without a second validator
    call. Any unexpected exception outside the helper boundary maps only to
    the adapter-owned SAFE_FAILURE sanitizer.
13. Return one fresh result and release private fixture evidence when the
    stack unwinds.

No step may retry, fallback, reread, sort, repair, infer, round, switch source,
call a provider, change policy, call G201, or continue after failure.

### 7.1 Call accounting

| Outcome | Fixture reads | Parser calls | Result-validator calls |
| --- | ---: | ---: | ---: |
| Authority or path invalid | 0 | 0 | 0 |
| Fixture unavailable or bounded read fails | 1 | 0 | 0 |
| Decode or parse fails | 1 | 1 | 0 |
| Shape, identity, time, coverage, or event validation fails | 1 | 1 | 0 |
| Construction or post-read drift fails | 1 | 1 | 0 |
| Constructed result is invalid | 1 | 1 | 1 |
| READY | 1 | 1 | 1 |

An exception after a call begins consumes that call. No outcome permits a
second read, parser call, validator call, source, or attempt.

## 8. Exact G201 Source Construction

### 8.1 Calendar snapshot

The adapter constructs all 12
`CanonicalGoldEconomicCalendarSnapshotV1` fields in this exact order:

| Order | Field | Exact source or value |
| ---: | --- | --- |
| 1 | `contract_version` | adapter constant `"1.0"` |
| 2 | `calendar_schema_version` | exact validated authority and fixture value `"1.0"` |
| 3 | `calendar_snapshot_id` | exact validated expected-identity value |
| 4 | `source_profile_version` | authority constant `"canonical_gold_economic_calendar_source_v1"` |
| 5 | `generated_at_utc` | exact validated fixture string |
| 6 | `coverage_start_utc` | exact validated fixture string |
| 7 | `coverage_end_utc` | exact validated fixture string |
| 8 | `events` | fresh exact tuple of fresh G201 event records |
| 9 | `upstream_evidence` | fresh record from section 8.2 |
| 10 | `read_only` | exact built-in `True` |
| 11 | `demo_only` | exact built-in `True` |
| 12 | `contains_raw_provider_payload` | exact built-in `False` |

### 8.2 Upstream evidence

The eight `CanonicalGoldEconomicCalendarUpstreamEvidenceV1` fields are:

| Order | Field | Exact READY value |
| ---: | --- | --- |
| 1 | `adapter_passed` | built-in `True` |
| 2 | `adapter_status_code` | `"CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY"` |
| 3 | `schema_validated` | built-in `True` |
| 4 | `identity_validated` | built-in `True` |
| 5 | `timestamps_normalized` | built-in `True` after exact canonical UTC validation, without rewriting |
| 6 | `same_snapshot_bound` | built-in `True` after the single-attempt and drift checks |
| 7 | `warning_codes` | exact empty built-in tuple |
| 8 | `raw_payload_discarded` | built-in `True` only when no raw object is reachable from output |

Warnings are not accepted in v1. No passed source contains warnings.

### 8.3 Event source

Each `CanonicalGoldEconomicEventSourceV1` copies the exact validated fixture
values in the same eight-field order. The adapter performs no category
translation, impact promotion, status inference, time shift, event filtering,
window derivation, nearest-event calculation, or provider-specific mapping.

The event tuple preserves the exact validated canonical source order. Every
record and the tuple itself are fresh and detached.

## 9. Adapter Result Contract

`CanonicalGoldEconomicCalendarSourceAdapterResultV1` is a frozen, slotted
dataclass with exactly these 15 fields in order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `contract_version` | built-in `str`, exactly `"1.0"` |
| 2 | `passed` | built-in `bool` |
| 3 | `status_code` | built-in `str` |
| 4 | `reason_codes` | exact built-in `tuple[str, ...]` |
| 5 | `warning_codes` | exact built-in `tuple[str, ...]` |
| 6 | `snapshot_available` | built-in `bool` |
| 7 | `snapshot` | exact G201 `CanonicalGoldEconomicCalendarSnapshotV1` or `None` |
| 8 | `read_only` | built-in `bool` |
| 9 | `demo_only` | built-in `bool` |
| 10 | `is_tradable` | built-in `bool` |
| 11 | `can_execute` | built-in `bool` |
| 12 | `is_trading_permission` | built-in `bool` |
| 13 | `is_execution_instruction` | built-in `bool` |
| 14 | `allowed_to_call_ea` | built-in `bool` |
| 15 | `allowed_to_modify_risk` | built-in `bool` |

READY has `snapshot_available is True` and one exact snapshot. Every failure
has `snapshot_available is False` and `snapshot is None`. Warning codes are
always the exact empty built-in tuple.

No result field may contain a path, filename, provider, raw payload, source
bytes, checksum, digest, exception, traceback, private token, policy object,
fixture status detail, credential, account, strategy, risk decision, order,
or execution instruction.

## 10. Status, Reason, and First-Failure Mapping

A READY result has no reason. Every failure has exactly one reason. The
closed first-failure order is:

| Priority | Status | Single reason | Meaning |
| ---: | --- | --- | --- |
| 1 | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_AUTHORITY_INVALID` | `GOLD_ECONOMIC_CALENDAR_AUTHORITY_INVALID` | Authority, path policy, token, time, expected identity, schema, or profile invalid before content read |
| 2 | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_FIXTURE_UNAVAILABLE` | `GOLD_ECONOMIC_CALENDAR_FIXTURE_UNAVAILABLE` | One bounded fixture read cannot return approved content |
| 3 | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_FIXTURE_INVALID` | `GOLD_ECONOMIC_CALENDAR_FIXTURE_INPUT_INVALID` | Decode, JSON, duplicate-key, top-level, or nested fixture shape invalid |
| 4 | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_IDENTITY_INVALID` | `GOLD_ECONOMIC_CALENDAR_IDENTITY_INVALID` | Schema, snapshot identity, expected metadata, or post-read identity drift invalid |
| 5 | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_FRESHNESS_INVALID` | `GOLD_ECONOMIC_CALENDAR_FRESHNESS_INVALID` | Generated timestamp or calendar age invalid |
| 6 | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_COVERAGE_INVALID` | `GOLD_ECONOMIC_CALENDAR_COVERAGE_INVALID` | Coverage order, horizon, or span invalid |
| 7 | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_EVENT_INVALID` | `GOLD_ECONOMIC_CALENDAR_EVENT_INPUT_INVALID` | Event count, shape, code, timestamp, revision, uniqueness, or canonical order invalid |
| 8 | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_RESULT_INVALID` | `GOLD_ECONOMIC_CALENDAR_RESULT_INVALID` | Constructed source or result fails exact independent validation |
| 9 | `CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_SAFE_FAILURE` | `GOLD_ECONOMIC_CALENDAR_EXCEPTION_SANITIZED` | Unexpected boundary, read, parser, conversion, construction, or validation exception |

The only success mapping is:

```text
passed = True
status_code = "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY"
reason_codes = ()
warning_codes = ()
snapshot_available = True
```

If multiple conditions are observable, the first reached category wins. The
adapter must not collect, reorder, combine, relabel, or expose internal
reasons. A malformed returned object is not a normal fixture rejection.

Unexpected exception type, message, traceback, path, fixture bytes, parsed
content, token, or source status must not enter the result or a log.

## 11. Fixed Safety Envelope

Every adapter result, including READY, has these exact built-in values:

| Field | Value |
| --- | --- |
| `read_only` | `True` |
| `demo_only` | `True` |
| `is_tradable` | `False` |
| `can_execute` | `False` |
| `is_trading_permission` | `False` |
| `is_execution_instruction` | `False` |
| `allowed_to_call_ea` | `False` |
| `allowed_to_modify_risk` | `False` |

The nested snapshot also has `read_only is True`, `demo_only is True`, and
`contains_raw_provider_payload is False`. No status, event, impact, source,
window, observation, or later fact may override these values.

## 12. Fail-Closed and Isolation Rules

The adapter fails closed for:

- missing, extra, reordered, duplicate, subclassed, aliased, case-changed,
  wrong-container, or wrong-element authority, policy, fixture, event,
  snapshot, evidence, or result values;
- path escape, symlink or reparse ambiguity, wrong concrete path type,
  non-regular file, size overflow, or path drift;
- caller-provided path, time, identity, profile, policy, parser, provider,
  dependency, status, reason, or oracle;
- empty, malformed, ambiguous, duplicate-key, non-UTF-8, or non-canonical JSON;
- identity, timestamp, age, coverage, event count, event code, revision,
  uniqueness, order, or same-snapshot drift;
- any warning, raw-provider marker, parser-owned alias, mutable nested object,
  or raw object reachable from output;
- partial snapshot construction or inconsistent result fields; and
- every unexpected exception.

The adapter must not:

- copy G201 builder, result mapping, window logic, summary logic, or maintain a
  parallel calendar snapshot contract;
- import or call G185, G178, ReplayRunner, an API, MT4, EA, order, execution,
  or trading component;
- read environment variables, settings, ambient time, network, database,
  cache, frontend state, provider SDK, or runtime data outside its one fixed
  offline fixture path;
- retry, fallback, reread, sort, repair, normalize malformed timestamps,
  infer, round, switch source, or call a second dependency;
- expose private fixture evidence or authority; or
- return a partial snapshot.

Inputs and private frozen evidence must remain unchanged. Every returned
result, snapshot, upstream record, event tuple, and event record is fresh and
detached. Repeated calls with unchanged fixed authority and fixture content
must be equal but must not share result or nested object identity.

## 13. Required Contract Vectors

A later tests-only work order must use immutable static vectors. It must not
import or call the future adapter. At minimum it must lock:

1. exact public exports, keyword-only signature, private authority, expected
   identity, read policy, fixture document, fixture event, result fields,
   order, annotations, frozen/slotted rules, and strict built-in types;
2. exact server-owned path, time, profile, identity, policy, and no-caller-
   override ownership;
3. exact top-level seven-key and nested eight-key fixture schemas, duplicate
   rejection, 1048576-byte boundary, and structured parser requirement;
4. zero/one read, parser, and result-validator accounting with no retry;
5. all 12 G201 snapshot fields, eight upstream fields, eight event fields,
   provenance, freshness, detachment, and raw-payload discard semantics;
6. zero, 512, and 513 event boundaries and 259200-second exact coverage span
   versus one-microsecond overflow;
7. strict real UTC dates, generated-time age, two-sided 86400-second coverage
   horizon, exact canonical event order, tie order, unique IDs, closed codes,
   and non-negative revisions;
8. the READY mapping, all nine ordered failure mappings, first-failure
   priority, failure snapshot clearing, and fixed safety flags;
9. missing, extra, reordered, duplicate, alias, case-change, subclass,
   wrong-container, wrong-element, path, identity, timestamp, coverage,
   event, warning, mutation, and result-consistency probes;
10. sanitizer and validator exceptions returning exact safe failures without
    exception or internal-state leakage;
11. no environment, ambient clock, network, provider, API, G185, G178, G201
    builder, ReplayRunner, MT4, EA, order, execution, or trading call; and
12. explicit evidence that vectors do not prove implementation, integration,
    activation, or verification.

## 14. Required Staged Delivery

Later work remains separately planned, approved, reviewed, and merged:

1. immutable tests-only contract vectors for G202;
2. production result and private authority types plus the bounded adapter and
   its approved pure-memory validation seams;
3. a fixed checked-in offline calendar fixture and controlled adapter tests;
4. genuine offline composition through G185 -> G178 -> approved calendar
   adapter/fixture -> G201;
5. deterministic non-activating verification of that exact composition;
6. separately contracted later W6 facts and features; and
7. a separately versioned ReplayRunner W6 stage before W7.

No stage silently includes the next. Contract is not tests, tests are not
implementation, implementation is not integration, integration is not
activation, and activation is not verification.

## 15. WBS and Capability Boundaries

- W1 remains `VERIFIED` for its existing canonical Bundle v1 authority. G202
  neither imports nor extends W1.
- W5 remains `VERIFIED` only for ReplayRunner v1 canonical diagnostics. G202
  adds no W6 ReplayRunner stage.
- W6 remains `TESTS_ONLY`. G202 closes only the dedicated calendar
  source-adapter contract gap.
- G199 remains the economic-window facts contract, G200 remains immutable
  tests-only vectors, and G201 remains an isolated pure-memory builder.
- W7-W21 remain unchanged and unauthorized.
- Reader activation, provider activation, real MT4, EA, order, execution,
  Demo auto-execution, Live, deployment, and trading remain prohibited.

## 16. G202 Acceptance Checklist

G202 is acceptable only when:

- this document is the only added file;
- ownership between G201 source types and the adapter boundary is explicit;
- the internal module, exact exports, keyword-only function, authority,
  policy, expected identity, fixture schema, result, and private helpers are
  deterministic;
- path, clock, schema, profile, identity, policy, dependency, and oracle
  authority are entirely server-owned;
- one bounded offline fixture read is the only source attempt;
- the seven-key document, eight-key events, strict parser, event ordering,
  UTC, age, coverage, count, and identity rules are closed;
- all G201 source fields have exact provenance and fresh detached ownership;
- READY and every ordered failure have exact status/reason semantics;
- failures contain no snapshot, warnings are rejected, and exceptions are
  sanitized;
- no path, raw payload, checksum, token, exception, provider, API, MT4,
  execution, or trading state can leak;
- Demo-only, Read-only, no-EA, no-execution, and no-trading flags remain fixed;
- vectors, implementation, fixture evidence, composition, verification,
  ReplayRunner W6, activation, and later features remain unimplemented;
- W6 package maturity remains `TESTS_ONLY`;
- `git diff --check` passes; and
- exact scope, ASCII, and isolation checks pass.
