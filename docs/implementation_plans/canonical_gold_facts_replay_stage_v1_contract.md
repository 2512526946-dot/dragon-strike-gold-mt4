# Canonical Gold Facts Replay Stage v1 Contract

Status: G208 contract-only design. This document advances the narrow W6
Canonical Gold facts replay-stage boundary from `POLICY_ONLY` to
`CONTRACT_ONLY`. W6 as a package remains `TESTS_ONLY`.

This document does not add contract vectors, production types, a runtime
runner, integration evidence, deterministic verification, reader activation,
MT4 access, analysis, W7 behavior, EA calls, orders, execution, trading, or
activation.

## 1. Purpose

Canonical Gold Facts Replay Stage v1 is a future deterministic,
non-activating, offline replay boundary for the reviewed Canonical Gold facts
chain:

```text
existing Canonical Bundle ReplayRunner v1
    -> G185 fixed docs-fixture market-source boundary
    -> G178 Canonical Gold market-facts projector
    -> G191 session and spread/freshness facts builder
    -> G196 volatility and structure facts builder
    -> G204 fixed economic-calendar source adapter
    -> G201 economic-window facts builder
```

The stage will compare each complete safe result with one server-owned,
versioned, immutable registry oracle. A replay match will mean only that the
fixed offline case reproduced its registered safe evidence. It will not mean
that market data is currently ready, an analysis or Gate passed, a trading
session is approved, or any execution is permitted.

The capability layers remain separate:

| Layer | State after G208 |
| --- | --- |
| Policy | A versioned, deterministic, offline W6 facts replay stage is allowed. |
| Contract | This document defines the future boundary. |
| Tests | Not implemented. Immutable contract vectors require a later work order. |
| Implementation | Not implemented. No replay-stage production type or runner exists. |
| Integration | Not implemented. The reviewed component integrations remain separate evidence. |
| Activation | Not implemented and not authorized. |
| Verification | Not implemented for this replay stage. Existing component verification is not replay-stage verification. |

## 2. Versioning and ReplayRunner v1 compatibility

The exact version and identifier constants are:

```text
REPLAY_CONTRACT_VERSION = canonical_bundle_replay_v2
STAGE_CONTRACT_VERSION = canonical_gold_facts_replay_stage_v1
REGISTRY_VERSION = canonical_gold_facts_replay_registry_v1
AUTHORITY_PROFILE_VERSION = canonical_gold_facts_replay_authority_v1
STAGE_ID = canonical_gold_facts
UPSTREAM_REPLAY_CONTRACT_VERSION = canonical_bundle_replay_v1
UPSTREAM_REPLAY_REGISTRY_VERSION = canonical_bundle_replay_registry_v1
IDENTIFIER_PATTERN = ^[a-z0-9](?:[a-z0-9_-]{0,62})$
PUBLIC_CODE_PATTERN = ^[A-Z][A-Z0-9_]{0,127}$
```

`canonical_bundle_replay_v2` is a new future wrapper contract. It does not
rename, edit, extend in place, or supersede the verified
`canonical_bundle_replay_v1` implementation. The following v1 artifacts remain
byte-for-byte and behaviorally unchanged:

- `CanonicalBundleReplayCaseV1`;
- `CanonicalBundleReplayResultV1`;
- `canonical_bundle_replay_registry_v1`;
- the one-stage v1 order containing only `canonical_diagnostics`;
- every v1 golden vector, integration test, and deterministic verification
  result.

The future v2 implementation must call the existing
`run_canonical_bundle_replay_case` entry point. It must not copy v1, call G153
directly, add a W6 stage to the v1 registry, reinterpret a v1 result, or change
a v1 oracle.

The stage contract version and outer replay contract version are independent.
A later change to the stage schema requires a new stage contract version. A
later change to the outer replay order requires a new replay contract version.
Neither version may be silently widened.

## 3. Future module and exact public exports

The future implementation belongs in one separately approved production
module:

```text
backend.app.services.canonical_gold_facts_replay_stage
```

Its exact ordered `__all__` must be:

```python
__all__ = (
    "CanonicalGoldFactsReplayCaseV1",
    "CanonicalGoldFactsReplayExpectedOracleV1",
    "CanonicalGoldFactsReplayRegistryRecordV1",
    "CanonicalGoldFactsReplayResultV1",
    "run_canonical_gold_facts_replay_case_v1",
)
```

The single public entry point must be keyword-only:

```python
def run_canonical_gold_facts_replay_case_v1(
    *,
    replay_case: CanonicalGoldFactsReplayCaseV1,
) -> CanonicalGoldFactsReplayResultV1:
    ...
```

It accepts exactly one argument. It must reject positional input and must not
accept a path, root, directory, clock, datetime, policy, dependency, callback,
registry, expected result, oracle, source object, fixture payload, settings
object, request, environment value, runtime mode, or authority object.

## 4. Exact public types

All four public records must be `@dataclass(frozen=True, slots=True)`. Exact
class identity, field names, field order, annotations, and strict built-in
values are part of the contract. Subclasses and merely similar objects are
invalid.

### 4.1 Five-field public case

```python
@dataclass(frozen=True, slots=True)
class CanonicalGoldFactsReplayCaseV1:
    replay_contract_version: str
    stage_contract_version: str
    stage_id: str
    case_id: str
    fixture_id: str
```

An accepted case must satisfy:

- `type(replay_case) is CanonicalGoldFactsReplayCaseV1`;
- the exact five fields occur in the declared order;
- each value has exact built-in type `str`;
- the first three fields equal the constants in section 2;
- `case_id` and `fixture_id` full-match `IDENTIFIER_PATTERN`;
- all strings are non-empty and contain ASCII only; and
- the exact `(case_id, fixture_id)` pair resolves one registry record.

The case carries no bundle identity, calendar identity, path, time, policy,
dependency, expected status, expected reason, expected value, or runtime
authority. Missing, extra, reordered, duplicated, aliased, case-changed,
subclassed, or wrong-container values fail before any dependency call.

### 4.2 Recursive immutable oracle value

The registry oracle uses one closed, tagged value grammar. Every encoded value
is an exact built-in tuple. A container tag is never omitted, so values from
different source types cannot collide merely because their children compare
equal.

```text
FrozenNoneV1 :=
    ("NONE_V1",)

FrozenBoolV1 :=
    ("BOOL_V1", exact built-in bool)

FrozenIntV1 :=
    ("INT_V1", exact built-in int)

FrozenStringV1 :=
    ("STRING_V1", exact built-in str)

FrozenFloatV1 :=
    ("FLOAT_HEX_V1", exact canonical built-in str)

FrozenTupleV1 :=
    ("TUPLE_V1", exact built-in tuple[FrozenValueV1, ...])

FrozenListV1 :=
    ("LIST_V1", exact built-in tuple[FrozenValueV1, ...])

FrozenDictV1 :=
    (
        "DICT_V1",
        exact built-in tuple[
            exact built-in tuple[FrozenValueV1, FrozenValueV1],
            ...,
        ],
    )

FrozenDataclassV1 :=
    (
        "DATACLASS_V1",
        exact contract-owned type code str,
        exact built-in tuple[
            exact built-in tuple[exact field-name str, FrozenValueV1],
            ...,
        ],
    )

FrozenValueV1 :=
    FrozenNoneV1
    | FrozenBoolV1
    | FrozenIntV1
    | FrozenStringV1
    | FrozenFloatV1
    | FrozenTupleV1
    | FrozenListV1
    | FrozenDictV1
    | FrozenDataclassV1

FrozenRecordV1 := FrozenDataclassV1
```

All tags above are exact ASCII built-in strings. The fixed tag and arity are
part of each alternative. A tag may not be aliased, case-changed, omitted, or
used with another alternative's payload shape.

An encoded oracle contains no raw `float`, `Decimal`, `bytes`, `bytearray`,
`Path`, `datetime`, `dict`, `list`, `set`, custom mapping, enum, subclass,
object identity, exception, or mutable container. The encoder accepts only the
strict source values described below and emits only values in the tagged tuple
grammar.

The exact finite-float encoding is:

1. accept a value only when `type(value) is float`;
2. require `math.isfinite(value) is True`;
3. set the payload to the exact built-in result of `value.hex()`;
4. require `type(payload) is str`;
5. require `float.fromhex(payload).hex() == payload`; and
6. emit `("FLOAT_HEX_V1", payload)`.

This is the sole permitted float-to-string transform. It preserves the exact
binary value and signed zero without Decimal arithmetic, ambient Decimal
context, locale, rounding, formatting policy, or platform-native byte order.
`NaN`, positive or negative infinity, float subclasses, malformed or
non-canonical hex strings, and values not already accepted by the G185 result
validator are invalid.

An exact built-in list node is accepted only within the genuine v1
`canonical_summary` subtree after the existing G151 validator has accepted the
complete exact 20-key summary. It is encoded as
`("LIST_V1", tuple(encoded_items_in_source_order))`. An exact built-in tuple is
encoded separately as
`("TUPLE_V1", tuple(encoded_items_in_source_order))`. This distinction is
mandatory even for empty or equal-valued containers.

Every exact built-in dict node within that validated `canonical_summary`
subtree is encoded as
`("DICT_V1", tuple((encoded_key, encoded_value) for each item in insertion
order))`. The implementation must not sort any key. No dict or list is
accepted from any other stage result.

Every exact allowlisted dataclass is encoded with
`("DATACLASS_V1", fixed_type_code, ordered_fields)`. The future module owns one
closed mapping from each exact production class object, including every
allowed nested dataclass class, to one unique fixed ASCII type code. Each
ordered field entry is `(exact_field_name, encoded_value)`. The encoder must
require exact class identity and the complete declared field order at every
dataclass node, not only at the root.

The future implementation may convert an allowlisted safe result to
`FrozenRecordV1` only by:

1. validating the complete stage result with the existing authoritative
   result boundary before encoding;
2. requiring exact allowlisted class identity at every dataclass node;
3. visiting dataclass fields, dict items, lists, and tuples in their existing
   contract order;
4. applying the exact tagged alternative for the source value's strict type;
5. accepting finite floats only in validator-approved G185 source fields;
6. accepting dicts and lists only in the validator-approved v1
   `canonical_summary`; and
7. rejecting every unsupported, missing, extra, reordered, aliased,
   case-changed, subclassed, mutable, non-finite, or wrong-context value.

The encoder must not sort, coerce, normalize, round, repair, hash, use `repr`,
use `str(value)`, use generic formatting, serialize JSON, pickle a value, or
drop a field. Apart from the exact `float.hex()` rule above, it must not
stringify a value.

### 4.3 Seven-field expected oracle

```python
@dataclass(frozen=True, slots=True)
class CanonicalGoldFactsReplayExpectedOracleV1:
    diagnostics_result: tuple[object, ...]
    market_source_result: tuple[object, ...]
    market_facts_snapshot: tuple[object, ...]
    session_spread_freshness_facts: tuple[object, ...]
    volatility_structure_facts: tuple[object, ...]
    economic_calendar_result: tuple[object, ...]
    economic_window_facts: tuple[object, ...]
```

Every field must be an exact built-in `FrozenRecordV1`, not an arbitrary
`tuple[object, ...]`. The annotation avoids a second runtime wrapper type; the
closed grammar above remains normative.

The seven fields are ordered exactly like the seven dependency calls in
section 7. Each field contains the complete recursively frozen safe result,
not a selected status summary. An oracle may not omit nested facts, identity,
warnings, reasons, safety flags, or a diagnostics-summary value.

### 4.4 Eighteen-field registry record

```python
@dataclass(frozen=True, slots=True)
class CanonicalGoldFactsReplayRegistryRecordV1:
    registry_version: str
    replay_contract_version: str
    stage_contract_version: str
    authority_profile_version: str
    stage_id: str
    case_id: str
    fixture_id: str
    diagnostics_case: CanonicalBundleReplayCaseV1
    market_source_profile_version: str
    market_facts_contract_version: str
    session_facts_profile_version: str
    volatility_facts_profile_version: str
    calendar_source_profile_version: str
    economic_window_facts_profile_version: str
    reference_time_utc: str
    expected_market_identity: tuple[object, ...]
    expected_calendar_identity: tuple[object, ...]
    expected_oracle: CanonicalGoldFactsReplayExpectedOracleV1
```

The registry is an exact built-in tuple of exact
`CanonicalGoldFactsReplayRegistryRecordV1` objects. The approved registry
object and every nested object are server-owned. The public runner never
accepts a registry argument and never returns a registry record or oracle.

The two identity tuples have exact shapes:

```text
expected_market_identity = (
    source_contract_version: exact str,
    bundle_schema_version: exact str,
    bundle_id: exact str,
    sequence: exact int,
    canonical_symbol: exact str,
    broker_symbol: exact str,
    reference_time_utc: exact str,
)

expected_calendar_identity = (
    calendar_contract_version: exact str,
    calendar_schema_version: exact str,
    calendar_snapshot_id: exact str,
    calendar_source_profile_version: exact str,
    calendar_generated_at_utc: exact str,
    calendar_coverage_start_utc: exact str,
    calendar_coverage_end_utc: exact str,
)
```

Both are exact built-in tuples of the declared length and order. Their string
values must satisfy the reviewed G175/G178 and G199/G201/G204 contracts. The
registry must bind the existing v1 diagnostics case
`canonical_docs_ready/canonical_docs_fixture_v1`, the fixed G185 market
fixture, and the fixed G204 calendar fixture as one case. It must not combine
identities from different cases, fixtures, attempts, reference times, policy
profiles, source profiles, or contract versions.

The exact initial profile values are:

```text
market_source_profile_version = canonical_gold_market_facts_policy_v1
market_facts_contract_version = 1.0
session_facts_profile_version = canonical_gold_session_spread_freshness_profile_v1
volatility_facts_profile_version = canonical_gold_volatility_structure_profile_v1
calendar_source_profile_version = canonical_gold_economic_calendar_source_v1
economic_window_facts_profile_version = canonical_gold_economic_window_profile_v1
reference_time_utc = 2026-07-10T02:30:05.000000Z
```

The future production registry must freeze exact expected values from reviewed
fixture evidence. This contract deliberately does not copy those large golden
values. A later tests-only work order must lock them before runtime
implementation.

### 4.5 Twenty-six-field public result

```python
@dataclass(frozen=True, slots=True)
class CanonicalGoldFactsReplayResultV1:
    replay_contract_version: str
    stage_contract_version: str
    registry_version: str
    stage_id: str
    passed: bool
    status_code: str
    reason_codes: tuple[str, ...]
    identity_available: bool
    case_id: str | None
    fixture_id: str | None
    completed_stage_ids: tuple[str, ...]
    diagnostics_result: CanonicalBundleReplayResultV1 | None
    market_source_result: CanonicalGoldMarketFactsSourceAdapterResultV1 | None
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1 | None
    session_spread_freshness_facts: CanonicalGoldSessionSpreadFreshnessFactsV1 | None
    volatility_structure_facts: CanonicalGoldVolatilityStructureFactsV1 | None
    economic_calendar_result: CanonicalGoldEconomicCalendarSourceAdapterResultV1 | None
    economic_window_facts: CanonicalGoldEconomicWindowFactsV1 | None
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool
```

Every result field must have the exact declared type. `reason_codes` and
`completed_stage_ids` must be exact built-in tuples containing exact built-in
strings, with no duplicates. Every nested successful result must have exact
production type and be a fresh detached object graph.

## 5. Server-owned authority

The future module owns one immutable registry and one private authority capsule
per registry record. The private capsule is not exported, accepted, logged, or
returned. It binds:

- the exact existing v1 replay function identity and v1 case;
- the exact G185 zero-argument fixed docs-fixture function identity;
- the exact G178, G191, G196, G204, and G201 function identities;
- the fixed G185 market fixture and authority profile;
- one freshly constructed exact G204 authority using G204-owned token, allowed
  root, fixture path, reference time, expected identity, read policy, schema
  version, and source profile;
- the exact reference time and market/calendar identity tuples;
- all stage and profile versions; and
- the complete seven-field expected oracle.

The registry stores only safe public identity and oracle values. Filesystem
paths, concrete path types, datetime objects, policy objects, function objects,
authority tokens, and dependency identities remain in the private capsule.
They must never enter the public case, result, error, log, or oracle.

The implementation must validate exact module-level dependency identity and
private authority state before the first dependency call and after every call.
It must snapshot the public case, registry, oracle, dependency bindings,
authority, and both fixed fixture trees before execution. Any substitution,
mutation, missing slot, subclass, equal-but-distinct authority replacement,
fixture drift, or dependency drift fails closed.

The private capsule must not contain caller callbacks or configurable source
selection. It must not read environment variables, settings, the wall clock,
current working directory, request state, API input, or runtime MT4 state.

## 6. Exact stage order

The ordered stage identifiers are:

```text
STAGE_ORDER = (
    canonical_diagnostics_v1,
    canonical_gold_market_source_v1,
    canonical_gold_market_snapshot_v1,
    canonical_gold_session_spread_freshness_v1,
    canonical_gold_volatility_structure_v1,
    canonical_gold_economic_calendar_v1,
    canonical_gold_economic_window_v1,
)
```

No stage may be omitted, duplicated, reordered, run concurrently, or called
after an earlier failure. `completed_stage_ids` is either this exact tuple for
a matched result or the exact empty tuple for every failure result. Partial
stage lists are prohibited.

## 7. Exact calls and zero/one accounting

After case, registry, dependency, authority, fixture, and oracle validation,
the future runner must perform exactly these calls in order:

```python
diagnostics_result = run_canonical_bundle_replay_case(
    replay_case=registry_record.diagnostics_case,
)

market_source_result = (
    build_canonical_gold_market_facts_docs_fixture_source_v1()
)

market_facts_snapshot = build_canonical_gold_market_facts_snapshot_v1(
    validated_source=market_source_result.source,
)

session_spread_freshness_facts = (
    build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=market_facts_snapshot,
    )
)

volatility_structure_facts = (
    build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=market_facts_snapshot,
    )
)

economic_calendar_result = (
    build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=fresh_registry_owned_calendar_authority,
    )
)

economic_window_facts = build_canonical_gold_economic_window_facts_v1(
    market_facts_snapshot=market_facts_snapshot,
    economic_calendar_snapshot=economic_calendar_result.snapshot,
)
```

Each accepted dependency is called at most once. The first call invokes the
existing v1 runner, which continues to own its one G153 call. The W6 runner
must not call G153, G151, W1 reader/value/DataQualityGate, or any lower-level
reader directly.

Call accounting is fail-fast:

| Failure point | Earlier calls | Current and later calls |
| --- | --- | --- |
| Case, registry, oracle, dependency, authority, or fixture precheck | Zero | Zero |
| Existing v1 diagnostics result | Diagnostics once | G185 and later zero |
| G185 result | Earlier stages once | G178 and later zero |
| G178 result | Earlier stages once | G191 and later zero |
| G191 result | Earlier stages once | G196 and later zero |
| G196 result | Earlier stages once | G204 and G201 zero |
| G204 result | Earlier stages once | G201 zero |
| G201 result | Every stage once | No retry |

There is no retry, fallback, alternate registry, alternate fixture, source
switch, dependency replacement, result repair, sorting, reclassification, or
second call.

## 8. Per-stage acceptance

After each call and before the next call, the runner must:

1. confirm the exact production result class and declared field order;
2. confirm the result is the one safe READY or MATCHED state registered for
   the initial case;
3. confirm exact reason, warning, identity, profile, and safety-flag values;
4. convert the complete result to `FrozenRecordV1`;
5. compare it with the corresponding registry oracle field;
6. prove the public case, registry, private authority, fixtures, inputs, and
   all earlier results remain unchanged; and
7. stop immediately if any check fails.

The initial positive case requires:

- v1 diagnostics `passed=true`,
  `status_code=CANONICAL_BUNDLE_REPLAY_MATCHED`, empty replay reasons, and the
  exact registered safe G151 summary;
- G185 `passed=true`, source available, exact READY adapter result, and the
  exact 13-field source;
- G178 `passed=true`,
  `status_code=CANONICAL_GOLD_MARKET_FACTS_READY`;
- G191 `passed=true`,
  `status_code=CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_READY`;
- G196 `passed=true`,
  `status_code=CANONICAL_GOLD_VOLATILITY_STRUCTURE_READY`;
- G204 `passed=true`, snapshot available, and
  `status_code=CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY`; and
- G201 `passed=true`,
  `status_code=CANONICAL_GOLD_ECONOMIC_WINDOW_READY`.

A safe non-READY result maps to that stage's blocked replay status. An unsafe,
malformed, contradictory, polluted, subclassed, or unsupported result maps to
the common result-invalid status. A complete safe READY result that differs
from its exact registered oracle maps to expectation mismatch. None of these
conditions may be repaired.

The runner must not copy G178, G191, G196, G204, or G201 algorithms. Full
oracle comparison is the replay boundary. Existing G185 and G204 validators
remain authoritative where their contracts provide them.

## 9. Cross-stage identity and attempt binding

Before a later stage may run, all available identity fields must equal the
registry exactly.

The market identity must be equal across:

- the G185 source;
- the G178 snapshot;
- the G191 result;
- the G196 result; and
- the market identity carried by the G201 result.

The calendar identity must be equal across:

- the G204 snapshot; and
- the calendar identity carried by the G201 result.

The reference time must be equal across the registry, G185 source, G178
snapshot, G191 result, G196 result, G204 authority, and G201 result. Contract
and profile versions must equal the corresponding registry fields. Symbols
must remain `XAUUSD` and `GOLD`.

G191 and G196 must receive the same exact G178 snapshot object from this
attempt. G201 must receive that same G178 snapshot object and the exact G204
snapshot object from this attempt. No result or nested record from another
case, fixture, attempt, stage, version, or registry may be substituted even if
its values compare equal.

The runner must snapshot the complete G185 source before G178, the complete
G178 snapshot before each G191/G196/G201 call, and the complete G204 snapshot
before G201. Each object and all nested records must remain equal and
structurally unchanged after the call.

## 10. Replay status and reason mapping

Public statuses and their only allowed reason tuples are:

| Status | Exact `reason_codes` |
| --- | --- |
| `CANONICAL_GOLD_FACTS_REPLAY_MATCHED` | `()` |
| `CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID` | `("GOLD_FACTS_REPLAY_CASE_INPUT_INVALID",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_REGISTRY_INVALID` | `("GOLD_FACTS_REPLAY_REGISTRY_INVALID",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID` | `("GOLD_FACTS_REPLAY_AUTHORITY_INVALID",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_DIAGNOSTICS_BLOCKED` | `("GOLD_FACTS_REPLAY_DIAGNOSTICS_NOT_READY",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_MARKET_SOURCE_BLOCKED` | `("GOLD_FACTS_REPLAY_MARKET_SOURCE_NOT_READY",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_BLOCKED` | `("GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_NOT_READY",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_SESSION_FACTS_BLOCKED` | `("GOLD_FACTS_REPLAY_SESSION_FACTS_NOT_READY",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_VOLATILITY_FACTS_BLOCKED` | `("GOLD_FACTS_REPLAY_VOLATILITY_FACTS_NOT_READY",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_CALENDAR_BLOCKED` | `("GOLD_FACTS_REPLAY_CALENDAR_NOT_READY",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_BLOCKED` | `("GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_NOT_READY",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID` | `("GOLD_FACTS_REPLAY_RESULT_INVALID",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_MISMATCH` | `("GOLD_FACTS_REPLAY_EXPECTATION_MISMATCH",)` |
| `CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE` | `("GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED",)` |

Every status and reason is an exact built-in `str` matching
`PUBLIC_CODE_PATTERN`. Unknown, duplicated, reordered, additional, aliased,
case-changed, subclassed, or wrong-container codes are invalid.

The deterministic first-error priority is:

1. public case shape and values;
2. registry shape, version, case resolution, identity, profiles, and oracle;
3. dependency bindings, private authority, and fixed fixture snapshots;
4. existing v1 diagnostics exact type, safe state, oracle, and drift;
5. G185 exact type, safe state, oracle, and drift;
6. G178 exact type, safe state, oracle, identity, and drift;
7. G191 exact type, safe state, oracle, identity, and drift;
8. G196 exact type, safe state, oracle, identity, and drift;
9. G204 exact type, safe state, oracle, identity, and drift;
10. G201 exact type, safe state, oracle, identity, and drift;
11. detached result construction and independent result validation; and
12. exception sanitization at the public boundary.

Within a stage, unsafe shape or contradiction precedes blocked-state mapping,
blocked-state mapping precedes oracle mismatch, and post-call drift precedes
continuation. An exception never bypasses a more specific result that was
already deterministically established.

## 11. Success and failure construction

`passed` is true only for `CANONICAL_GOLD_FACTS_REPLAY_MATCHED`. A matched
result must have:

- every version and stage identifier equal to section 2;
- `identity_available=true`;
- registry-owned `case_id` and `fixture_id`;
- `reason_codes=()`;
- `completed_stage_ids` equal to the full `STAGE_ORDER`;
- all seven nested results present, exact, safe, and equal to the oracle;
- a fresh detached result object and fresh detached nested object graph; and
- the fixed safety flags in section 13.

Every non-matched result must clear all partial evidence:

```text
passed = false
identity_available = false
case_id = None
fixture_id = None
completed_stage_ids = ()
diagnostics_result = None
market_source_result = None
market_facts_snapshot = None
session_spread_freshness_facts = None
volatility_structure_facts = None
economic_calendar_result = None
economic_window_facts = None
```

It retains only the fixed replay/stage/registry version constants, fixed stage
identifier, one mapped status, one mapped reason, and fixed safety flags. It
must not expose which path, value, identity, event, price, payload, checksum,
token, internal dependency, or exception caused the failure.

The future implementation must independently validate the fully constructed
result before returning it. An invalid matched result becomes the fixed
result-invalid failure. If even sanitized failure construction cannot be
validated, the boundary still returns a fresh fixed safe-failure result; it
must not raise or leak an exception.

## 12. Determinism, detachment, and immutability

For unchanged case, registry, dependencies, fixtures, profiles, and reference
time, repeated runs must be equal.

Every run must return a fresh result. For matched runs:

- each of the seven nested results must be a fresh detached copy;
- every nested dataclass, tuple, and diagnostics-summary container must be
  detached from local dependency outputs, the registry oracle, prior runs,
  and sibling results;
- no mutable object may be shared between runs;
- the public case, registry, oracle, dependency bindings, private authority,
  G185 source, G178 snapshot, G204 snapshot, and both fixed fixture trees must
  remain unchanged; and
- result mutation attempts must not alter any later run or registry value.

The runner must not use object address, hash randomization, unordered
iteration, locale, timezone defaults, process state, filesystem enumeration
order, or ambient Decimal context to construct or compare evidence.

## 13. Fixed safety flags and sensitive-data isolation

Every matched or failed result fixes:

```text
read_only = true
demo_only = true
is_tradable = false
can_execute = false
is_trading_permission = false
is_execution_instruction = false
allowed_to_call_ea = false
allowed_to_modify_risk = false
```

No case, result, registry oracle, failure, log, test report, or diagnostic may
expose:

- absolute or relative filesystem paths;
- raw market or calendar fixture payloads;
- manifest content, checksum values, or digest internals;
- authority tokens, policy objects, dependency objects, or internal state;
- exception text, exception class names, tracebacks, or stack frames;
- environment, settings, request, credential, account, or ticket values;
- runtime MT4 state;
- signals, recommendations, lot sizes, orders, EA commands, or execution
  instructions.

The seven nested matched results are the only facts evidence allowed in the
public result. They are already bounded by their reviewed safe contracts.

## 14. Prohibited behavior

The future stage must not:

- mutate `canonical_bundle_replay_v1`, its registry, or its golden vectors;
- call G153 or G151 directly;
- duplicate G185, G178, G191, G196, G204, G201, W1 reader, value validator, or
  DataQualityGate logic;
- retry, fallback, repair, sort, normalize, round, coerce, or switch source;
- accept caller-controlled expected values, paths, time, policy, dependency,
  registry, fixture, or authority;
- read the wall clock, environment variables, settings, API input, network,
  broker terminal, or runtime `data/`;
- write, copy, download, rename, delete, or materialize a fixture;
- persist replay state, start a worker, schedule a job, or expose a route,
  command, UI source selector, or background service;
- call MT4, MQL4, an EA, an order adapter, or an execution service; or
- convert a replay match into analysis, W7 input, activation, or trading
  permission.

## 15. Required future contract vectors

A separate tests-only work order must use immutable static vectors to lock at
least:

1. exact exports, keyword-only signature, 5/7/18/26 field schemas, field order,
   annotations, frozen/slotted records, and strict built-in types;
2. all constants, identifier grammars, public-code grammar, and v1
   compatibility;
3. exact `STAGE_ORDER`, zero/one accounting, and every fail-fast stop point;
4. complete recursive tagged oracle freezing, including exact G151 20-key
   dict/list conversion, exact finite G185 float-hex conversion, complete
   nested dataclass type codes, and rejection of unsupported values;
5. case, registry, authority, dependency, fixture, version, profile, identity,
   and oracle drift;
6. all fourteen status/reason mappings and deterministic first-error priority;
7. missing, extra, reordered, duplicate, alias, case-change, subclass,
   wrong-container, wrong-element, meaningless-nonempty, and type-tag
   collision values;
8. all market and calendar cross-stage identity equalities and mixed-attempt
   rejection;
9. input, registry, oracle, authority, fixture, source, snapshot, and
   dependency immutability;
10. repeated equality, fresh detached object graphs, and mutation isolation;
11. exception sanitization, failure clearing, safety flags, and sensitive-data
    isolation;
12. no import or runtime implementation of the future runner; and
13. real v1 diagnostics and real G185 READY oracle representability, including
    list-versus-tuple, finite-float, signed-zero, non-finite-float,
    float-subclass, malformed-float-hex, and dataclass/container type-tag
    bypass probes; and
14. explicit evidence that existing v1 source, registry, vectors, integration,
    and verification remain unchanged.

Static vectors must not claim production implementation, genuine integration,
deterministic verification, activation, W7 readiness, or trading authority.

## 16. Required staged delivery

Delivery remains strictly separated:

```text
1. G208 contract
2. immutable tests-only contract vectors
3. production types and bounded replay-stage runner
4. genuine offline integration evidence using the unmodified production chain
5. deterministic non-activating replay-stage verification
```

Every stage requires its own reviewed work order and explicit user approval.
No stage may automatically start, merge, tag, deploy, activate, or authorize
the next stage.

Later facts/features require their own contracts before they can enter a new
replay version. W7 analysis is outside this stage. Reader/MT4 activation, EA
calls, orders, execution, and trading are not stages in this delivery sequence.

## 17. Acceptance checklist

G208 is complete only when this document:

- defines a new version without changing ReplayRunner v1;
- fixes the exact public exports, keyword-only interface, and 5/7/18/26
  schemas;
- assigns all path, clock, policy, dependency, fixture, oracle, and runtime
  authority to the immutable server-owned registry and private capsule;
- defines the closed recursive oracle grammar and full-result equality;
- makes genuine v1 diagnostic lists and genuine finite G185 floats
  representable without type collisions, rounding, or ambient context;
- fixes the exact seven-stage order and zero/one call accounting;
- requires the existing v1 runner rather than direct G153/G151 calls;
- defines strict per-stage safe-result, identity, profile, oracle, and drift
  checks;
- prevents mixed case, fixture, attempt, source, reference time, identity,
  profile, or version evidence;
- defines all status/reason pairs, first-error priority, and failure clearing;
- requires deterministic equality, fresh detached graphs, and complete
  immutability;
- fixes Demo-only, Read-only, non-trading, and non-execution flags;
- prohibits retries, fallbacks, ambient authority, sensitive-data leakage,
  MT4, EA, order, execution, trading, and activation;
- keeps vectors, implementation, integration, and verification separately
  authorized; and
- leaves later facts/features and W7 outside this contract.

This contract is not runtime evidence. Its presence does not prove that the
new replay version, W6 replay stage, reader, MT4 integration, analysis,
activation, execution, or trading capability exists.
