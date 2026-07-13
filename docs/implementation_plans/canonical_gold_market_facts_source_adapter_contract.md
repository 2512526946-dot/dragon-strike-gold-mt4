# Canonical Gold Market Facts Source Adapter Contract

Status: CONTRACT_ONLY
Scope: W6 server-owned same-attempt source authority
Contract version: 1.0
Default posture: Demo-only, Read-only, fail-closed

## 1. Purpose

This contract defines the internal source adapter boundary required between the
verified Canonical MT4 Demo Readonly Bundle v1 chain and the G175/G178
Canonical Gold Market Facts Snapshot v1 projector.

The adapter has one responsibility: after one server-owned canonical read has
passed the existing filesystem reader, value validator, and DataQualityGate
without warnings, construct one authoritative
`CanonicalGoldMarketFactsSourceV1` from facts captured during that exact read
attempt.

This document defines a future boundary only. It does not implement the
adapter, modify the reader or Gate, connect a fixture, call the projector, add
a ReplayRunner W6 stage, activate a reader, access MT4, or grant execution or
trading authority.

## 2. Existing Boundaries and the Gap

The current W1 chain deliberately returns safe envelopes:

- G148 reads and validates one canonical bundle and returns a sanitized reader
  envelope, not manifest or payload objects;
- the existing value validator is called inside that reader after one stable
  accepted attempt;
- G149 evaluates the reader envelope and returns a sanitized DataQualityGate
  envelope, not market facts;
- G151 and G153 are diagnostics-only and strip quotes, bars, paths, payloads,
  and internal source state; and
- G178 accepts a typed `CanonicalGoldMarketFactsSourceV1`, but type
  construction alone is not source authority.

Consequently, a caller cannot safely construct G175 source authority from the
current public envelopes. It is forbidden to reread files, recover values from
diagnostics, combine an envelope with separately loaded data, or duplicate the
reader, value-validator, or Gate algorithms.

## 3. Scope and Maturity

This contract advances only the narrow source-adapter boundary from
`POLICY_ONLY` to `CONTRACT_ONLY`. W6 as a package remains `TESTS_ONLY`.

Included:

- one private reader-owned accepted-attempt capsule;
- one server-owned authority capsule;
- one internal adapter result type and function;
- exact call order and zero/one-call behavior;
- exact G175 source-field provenance;
- deterministic fail-closed status and reason mapping; and
- output, isolation, and staged-delivery rules.

Excluded:

- contract vectors or production implementation;
- canonical fixture integration or deterministic verification;
- projector invocation or ReplayRunner W6 integration;
- session, economic-window, volatility, or structure features;
- API, frontend, reader activation, real MT4, EA, order, execution, or trading
  capability; and
- any W7-W21 capability.

## 4. Ownership and Authority

### 4.1 Server-owned authority

Only an approved server integration may create the private authority capsule.
No request, query, header, body, cookie, frontend state, plugin, environment
variable, working directory, arbitrary service caller, writer field, manifest,
or payload may provide or override:

- allowed root or bundle directory;
- reference time or clock;
- previous bundle identity;
- filesystem, freshness, future-skew, or DataQualityGate policy;
- policy-profile version;
- canonical or broker symbol mapping;
- reader, validator, Gate, adapter, or fallback dependency; or
- expected result, status, reason, or oracle.

The adapter function is an internal service boundary. It must not be imported
by an API router, frontend layer, plugin, MT4 integration, EA, strategy,
execution component, or arbitrary dependency-injection caller.

### 4.2 Private accepted-attempt ownership

The canonical filesystem reader owns the accepted-attempt capsule. A future
private reader seam may return the existing sanitized reader envelope together
with one capsule only to this adapter. The existing public reader function and
its returned envelope remain unchanged.

The capsule is a W1-owned generic immutable JSON evidence type. W1 does not
import the W6 adapter, G175 records, projector types, or any other downstream
market-facts type. Only the W6 adapter performs the one-way projection from
that private evidence to G175 source records.

Manifest and payload values may exist only in this private in-memory evidence
seam. They must not enter a public envelope, API, diagnostic result, log,
metric, trace, cache, or persistent store.

The capsule is:

- created only after the existing structure, filesystem, checksum, manifest
  consistency, and value checks pass for one attempt;
- populated from that accepted in-memory manifest and its four required
  payloads before those objects are discarded;
- frozen, slotted, detached from parser-owned containers, and unavailable to
  public callers;
- single-use within the adapter call stack;
- never logged, serialized, cached, persisted, returned by an API, or stored in
  diagnostics; and
- destroyed by ordinary scope release after the adapter returns.

An account snapshot remains a required member of the accepted W1 bundle and
must pass existing validation, but none of its account fields may enter a gold
market-facts source or adapter result.

### 4.3 No authority by construction

Possessing a `CanonicalGoldMarketFactsSourceV1`, a private capsule-like object,
a passed reader envelope, or a passed Gate envelope independently proves
nothing. Authority exists only when the adapter itself obtains the reader
envelope and accepted-attempt capsule as one private return, calls the Gate on
that exact envelope in the same stack frame, verifies all results, and then
constructs the source.

## 5. Future Module and Interfaces

The future production module is:

```text
backend/app/services/canonical_gold_market_facts_source_adapter.py
```

It may expose exactly these production names:

```python
@dataclass(frozen=True, slots=True)
class CanonicalGoldMarketFactsSourceAdapterResultV1:
    ...

def build_server_owned_canonical_gold_market_facts_source_v1(
    *,
    authority: _CanonicalGoldMarketFactsSourceAuthorityV1,
) -> CanonicalGoldMarketFactsSourceAdapterResultV1:
    ...
```

`_CanonicalGoldMarketFactsSourceAuthorityV1` and every accepted-attempt type
are private. They must not be exported through `__all__` or re-exported from a
package. The function must reject a subclassed or look-alike authority object.

### 5.1 Authority capsule

`_CanonicalGoldMarketFactsSourceAuthorityV1` is a frozen, slotted dataclass
with exactly these fields in order:

| Order | Field | Exact type | Authority |
| ---: | --- | --- | --- |
| 1 | `authority_token` | exact built-in `object` identity | Module-private singleton |
| 2 | `allowed_root` | exact concrete platform path: `pathlib.WindowsPath` on Windows or `pathlib.PosixPath` on POSIX | Server configuration |
| 3 | `bundle_dir` | same exact concrete platform path type as `allowed_root` | Server configuration inside allowed root |
| 4 | `reference_time_utc` | exact `datetime.datetime` | Server-owned aware UTC time |
| 5 | `previous_identity` | `_CanonicalBundlePreviousIdentityV1` or `None` | Server-owned prior accepted identity |
| 6 | `read_policy` | exact existing `CanonicalMt4DemoReadonlyBundleV1ReadPolicy` | Server policy |
| 7 | `filesystem_policy` | exact existing `CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy` | Server policy |
| 8 | `data_quality_policy` | exact existing `CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy` | Server policy |
| 9 | `policy_profile_version` | exact built-in `str` | Fixed `canonical_gold_market_facts_policy_v1` |

`_CanonicalBundlePreviousIdentityV1` is frozen and slotted with exact built-in
`str bundle_id` followed by exact built-in `int sequence`. The filesystem
policy must set `max_manifest_consistency_retries` to exact built-in integer
zero for this adapter. Invalid authority fails before any reader or Gate call.

The server factory constructs both path fields with `pathlib.Path`. Their
runtime types must be the platform's exact concrete `WindowsPath` or
`PosixPath` class and must match each other. Built-in strings, `PurePath`, the
factory `Path` class itself, a concrete-path subclass, a wrong-platform path,
or any other path-like object is invalid. The existing reader remains solely
responsible for resolution, containment, symlink, and filesystem safety.

`reference_time_utc` must have exact runtime type `datetime.datetime`, non-null
`tzinfo`, and `utcoffset() == datetime.timedelta(0)`. The adapter creates the
G175 source string by exactly:

```python
reference_time_utc.astimezone(datetime.UTC).isoformat(
    timespec="microseconds"
).replace("+00:00", "Z")
```

The replacement must occur exactly once at the terminal suffix. The result is
an exact built-in ASCII `str` with six fractional digits and terminal `Z`.
Naive, non-zero-offset, subclassed, unformattable, or otherwise ambiguous time
input fails authority validation before the reader call. The adapter must not
read an ambient clock, round, truncate, choose another timespec, or accept an
alternate UTC spelling.

The future fixture integration may own a factory for this capsule, but that
factory, fixture path, and fixture reference time are not defined or authorized
by G179.

### 5.2 Accepted-attempt capsule

The W1 reader owns these private recursive immutable JSON aliases:

```text
_CanonicalJsonScalarV1 = exact built-in str | int | float | bool | None
_CanonicalJsonObjectV1 = exact built-in tuple[tuple[str, _CanonicalJsonValueV1], ...]
_CanonicalJsonArrayV1 = exact built-in tuple[_CanonicalJsonValueV1, ...]
_CanonicalJsonValueV1 = _CanonicalJsonScalarV1 | _CanonicalJsonObjectV1 | _CanonicalJsonArrayV1
```

Every object member is an exact built-in two-item tuple whose key is an exact
built-in `str`. Object-member and array-element order must remain exactly as
accepted by W1. The reader must not sort, normalize, round, repair, infer, or
add values when it creates this representation. Duplicate names and all other
invalid JSON shapes have already been rejected by the existing W1 validation
path and cannot enter the capsule.

The private reader-owned `_CanonicalMt4DemoReadonlyAcceptedAttemptV1` is frozen
and slotted with exactly these fields in order:

| Order | Field | Exact type | Source |
| ---: | --- | --- | --- |
| 1 | `attempt_token` | exact built-in `object` identity | Fresh reader-owned singleton for one call |
| 2 | `manifest` | exact `_CanonicalJsonObjectV1` | Accepted manifest from this attempt |
| 3 | `payloads_by_filename` | exact built-in `tuple[tuple[str, _CanonicalJsonObjectV1], ...]` | Four accepted payloads from this attempt |

`payloads_by_filename` has exactly four exact built-in two-item tuples in this
order: `live_tick.json`, `latest_bars.json`, `symbol_spec.json`, then
`account_snapshot.json`. Each filename is an exact built-in `str`; each value
is the immutable object representation of the payload accepted under that
filename. The account payload remains private W1 validation evidence and is
never mapped into a G175 source field.

The capsule is evidence from already accepted values, not a second validator
and not a W6 projection. W1 must not import the W6 adapter or any G175 source or
result type. The W6 adapter alone projects selected frozen manifest and payload
members into fresh G175 records after the reader and Gate pass. The capsule
contains no filesystem path, digest, checksum, policy object, exception,
traceback, log field, API state, execution field, or free text beyond the exact
accepted JSON values. It is never returned, logged, cached, persisted, or
exposed outside the private in-memory stack.

The future private reader seam returns one exact built-in tuple in this order:

```text
(reader_envelope, accepted_attempt_or_none)
```

The first item is the existing reader result object produced by that call. The
second item is the exact private capsule only when that same call accepted one
attempt; otherwise it is `None`. No public reader result gains a capsule,
payload, token, or new key.

### 5.3 Adapter result

`CanonicalGoldMarketFactsSourceAdapterResultV1` is a frozen, slotted dataclass
with exactly these fields in order:

| Order | Field | Exact type |
| ---: | --- | --- |
| 1 | `contract_version` | built-in `str`, exactly `1.0` |
| 2 | `passed` | built-in `bool` |
| 3 | `status_code` | built-in `str` |
| 4 | `reason_codes` | exact built-in `tuple[str, ...]` |
| 5 | `warning_codes` | exact built-in `tuple[str, ...]` |
| 6 | `source_available` | built-in `bool` |
| 7 | `source` | exact `CanonicalGoldMarketFactsSourceV1` or `None` |
| 8 | `read_only` | built-in `bool` |
| 9 | `demo_only` | built-in `bool` |
| 10 | `is_tradable` | built-in `bool` |
| 11 | `can_execute` | built-in `bool` |
| 12 | `is_trading_permission` | built-in `bool` |
| 13 | `is_execution_instruction` | built-in `bool` |
| 14 | `allowed_to_call_ea` | built-in `bool` |
| 15 | `allowed_to_modify_risk` | built-in `bool` |

On success, `source_available` is true and `source` is exact type
`CanonicalGoldMarketFactsSourceV1`. On every non-passed result,
`source_available` is false and `source` is `None`.

No result may contain a path, filename, raw payload, digest, checksum, account
fact, exception text, traceback, internal attempt token, source status detail,
policy object, dependency, strategy, risk decision, order, or execution field.

## 6. Unique Call Order

The adapter algorithm has one allowed order:

1. Require exact `_CanonicalGoldMarketFactsSourceAuthorityV1`, the private
   singleton token, strict UTC time, fixed policy-profile version, exact policy
   objects, and a filesystem policy with zero manifest retries.
2. Snapshot the frozen authority and Git-independent in-memory inputs for
   drift checks. Failure returns authority-invalid with zero reader and zero
   Gate calls.
3. Call the future private accepted-attempt seam of the existing canonical
   filesystem reader exactly once. Do not call the public reader in addition.
4. The reader performs its existing checks. It invokes the existing value
   validator only in its existing position and at most once because this
   adapter permits one read attempt and zero manifest retries. The adapter
   never calls the value validator directly.
5. Require an exact passed reader envelope, exact filesystem-valid and
   upstream-value-valid statuses, all existing consistency/check flags true,
   all fixed Demo-only/Read-only safety flags, no reasons, no warnings, and one
   exact accepted-attempt capsule returned by the same private call.
6. Call the existing production DataQualityGate exactly once with that exact
   reader envelope and the authority capsule's exact server-owned policy.
7. Require the exact passed Gate envelope, exact passed status, exact ready
   state, empty reasons and warnings, exact source reader/value statuses, and
   all fixed safety flags.
8. Recheck the authority, exact reader-envelope object, exact capsule object,
   and captured `attempt_token` object identity for substitution or mutation.
   Require the same capsule returned atomically with the reader envelope and
   the same reader-envelope object supplied to the Gate. Missing or replaced
   objects, token drift, mutation, or post-call drift is same-attempt-invalid.
   The adapter does not compare manifest and payload identity fields; those
   checks remain exclusively inside W1 before any capsule can be created.
9. Construct one fresh `CanonicalGoldUpstreamEvidenceV1` and one fresh
   `CanonicalGoldMarketFactsSourceV1` using only the mappings in section 7.
10. Require exact production types, exact field order, fixed constants, and
    equality to the captured accepted values. This is a construction check,
    not a copied projector validator.
11. Return one fresh success result. Release all private attempt evidence when
    the stack unwinds.

The adapter must not retry, fallback, call a second reader or Gate, reread a
file, sort or repair data, switch source, change policy, call G151 or G153, call
the diagnostics producer, invoke the projector, or continue after any failed
step.

### 6.1 Call accounting

| Outcome | Reader calls | Gate calls | Value-validator calls |
| --- | ---: | ---: | ---: |
| Authority invalid or dependency unavailable before reader call | 0 | 0 | 0 |
| Reader blocks before value validation | 1 | 0 | 0 |
| Reader blocks at value validation | 1 | 0 | 1 |
| Reader exception | 1 | 0 | 0 or 1, as reached internally |
| Invalid reader envelope or capsule return | 1 | 0 | 0 or 1, as reached internally |
| Reader warning rejected | 1 | 0 | 1 |
| Gate blocked | 1 | 1 | 1 |
| Invalid Gate envelope | 1 | 1 | 1 |
| Gate exception | 1 | 1 | 1 |
| Same-attempt identity or source construction invalid | 1 | 1 | 1 |
| Ready | 1 | 1 | 1 |

An exception after a call begins consumes that call. No outcome permits a
retry or second invocation.

## 7. Exact Source Provenance

### 7.1 Top-level 13 fields

| Order | G175 source field | Exact source |
| ---: | --- | --- |
| 1 | `contract_version` | Adapter constant `1.0` |
| 2 | `bundle_schema_version` | Adapter projection of accepted capsule `manifest.schema_version` |
| 3 | `bundle_id` | Adapter projection of accepted capsule `manifest.bundle_id` |
| 4 | `sequence` | Adapter projection of accepted capsule `manifest.sequence` |
| 5 | `canonical_symbol` | Adapter projection of accepted capsule `manifest.canonical_symbol`, required to equal `XAUUSD` |
| 6 | `broker_symbol` | Adapter projection of accepted capsule `manifest.broker_symbol`, required to equal `GOLD` in v1 |
| 7 | `reference_time_utc` | Authority `reference_time_utc`, converted only by the exact six-fractional-digit UTC `Z` algorithm in section 5.1 |
| 8 | `policy_profile_version` | Authority constant `canonical_gold_market_facts_policy_v1` |
| 9 | `upstream_evidence` | Fresh record from the exact reader and Gate envelopes in this call |
| 10 | `live_tick` | Fresh G175 record projected by the adapter from frozen accepted `live_tick.json` evidence |
| 11 | `bars_generated_at_utc` | Adapter projection of frozen accepted `latest_bars.json.generated_at_utc` evidence |
| 12 | `timeframes` | Fresh G175 records projected by the adapter from frozen accepted `latest_bars.json.timeframes` evidence |
| 13 | `symbol_spec` | Fresh G175 record projected by the adapter from frozen accepted `symbol_spec.json` evidence |

The existing W1 checks exclusively prove that manifest `schema_version`,
`bundle_id`, `sequence`, `canonical_symbol`, `broker_symbol`, and eight fixed
safety flags agree with every required payload. W1 creates the capsule only
after that proof passes. The adapter must not parse, repeat, weaken, or replace
that identity algorithm; it checks only atomic envelope/capsule return,
captured object identity, immutability, and post-call drift as specified in
section 6.

### 7.2 Upstream evidence

The eight `CanonicalGoldUpstreamEvidenceV1` fields are constructed exactly as
follows:

| Order | Field | Exact source or value |
| ---: | --- | --- |
| 1 | `reader_passed` | Exact reader envelope `passed`, required true |
| 2 | `reader_status_code` | Exact reader envelope status, required `CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID` |
| 3 | `value_status_code` | Exact reader upstream value status, required `CANONICAL_MT4_BUNDLE_V1_VALUE_VALID` |
| 4 | `data_quality_passed` | Exact Gate envelope `passed`, required true |
| 5 | `data_quality_status_code` | Exact Gate status, required `CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED` |
| 6 | `ready_for_readonly_analysis` | Exact Gate readiness, required true |
| 7 | `warning_codes` | Exact empty built-in tuple after both envelopes prove empty warnings |
| 8 | `same_attempt_identity_bound` | True only after all same-stack identity checks pass |

Passed-with-warning reader or Gate results are rejected. Warning codes are not
copied into a passed source.

### 7.3 Tick, timeframe, bar, and symbol records

The W6 adapter maps selected fields from the generic accepted-attempt capsule
without renaming values or repeating W1 validation:

- `CanonicalGoldTickSourceV1`: `bid`, `ask`, `spread`, `spread_points`,
  `digits`, `point`, and `tick_time_utc` come from the exact accepted
  `live_tick.json` fields in that order.
- `bars_generated_at_utc` comes from exact accepted
  `latest_bars.json.generated_at_utc`.
- The four timeframe records come from exact accepted
  `latest_bars.json.timeframes` in `M15`, `H1`, `H4`, `D1` order. Each carries
  `timeframe`, `period_seconds`, and an exact tuple of bars. `bar_count` is
  validation evidence only and is not copied into G175.
- Each `CanonicalGoldBarSourceV1` carries `open_time_utc`, `open`, `high`,
  `low`, `close`, `tick_volume`, and `spread_points` from the accepted bar in
  that order.
- `CanonicalGoldSymbolSpecSourceV1` carries `spec_time_utc`, `digits`,
  `point`, `tick_size`, `tick_value`, `contract_size`, `min_lot`, `lot_step`,
  `max_lot`, `base_currency`, `profit_currency`, `margin_currency`,
  `trade_mode_readonly_label`, and `session_status_readonly_label` from exact
  accepted `symbol_spec.json` fields in that order.

No adapter stage converts values to Decimal, computes freshness, interprets
labels as permission, or adds session, volatility, structure, economic, risk,
strategy, or execution meaning. Those responsibilities remain with G178 or
future separately contracted stages.

## 8. Result Status and Reason Mapping

Status and reason codes are closed ASCII enums. A blocked result has exactly
one reason. A ready result has no reason. Warning codes are always empty in v1.

| Condition | `passed` | Status | Exact reason |
| --- | --- | --- | --- |
| Exact successful source construction | true | `CANONICAL_GOLD_SOURCE_ADAPTER_READY` | none |
| Authority capsule, token, policy, time, or dependency invalid before reader call | false | `CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID` | `GOLD_SOURCE_AUTHORITY_INVALID` |
| Reader returned an exact internally consistent blocked envelope and no capsule | false | `CANONICAL_GOLD_SOURCE_ADAPTER_READER_BLOCKED` | `GOLD_SOURCE_READER_NOT_READY` |
| Reader return fails exact envelope/capsule pairing, type, field, or consistency checks, including a passed envelope without one capsule or a blocked envelope with a capsule | false | `CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE` | `GOLD_SOURCE_READER_RESULT_INVALID` |
| Reader returned any warning | false | `CANONICAL_GOLD_SOURCE_ADAPTER_WARNING_BLOCKED` | `GOLD_SOURCE_UPSTREAM_WARNING_REJECTED` |
| Gate blocked or was not exactly ready | false | `CANONICAL_GOLD_SOURCE_ADAPTER_DATA_QUALITY_BLOCKED` | `GOLD_SOURCE_DATA_QUALITY_NOT_READY` |
| Gate return fails exact envelope, type, field, or consistency checks | false | `CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE` | `GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID` |
| Attempt capsule, identity binding, or post-call drift invalid | false | `CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID` | `GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID` |
| Exact source type or construction consistency invalid | false | `CANONICAL_GOLD_SOURCE_ADAPTER_SOURCE_INVALID` | `GOLD_SOURCE_CONSTRUCTION_INVALID` |
| Unexpected reader, Gate, mapping, or boundary exception | false | `CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE` | `GOLD_SOURCE_EXCEPTION_SANITIZED` |

An exact, internally consistent reader or Gate blocked envelope retains its
blocked classification. A returned object with a wrong exact type, missing,
extra, reordered, subclassed, or wrong-container field, or a contradictory
status/reason/warning/readiness/safety combination uses its dedicated invalid
result reason above; it must not be relabeled as a normal blocked result.
Unexpected exceptions use `GOLD_SOURCE_EXCEPTION_SANITIZED`. Exception type,
message, traceback, input, path, payload content, internal status, or dependency
detail must not be returned or logged by this boundary.

If more than one invalid condition is observable, the first reached step in
section 6 wins. The adapter must not continue to collect, reorder, or combine
reasons.

## 9. Fixed Safety Envelope

Every adapter result, including ready, has these exact built-in values:

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

No source fact, status, identity, label, warning, readiness result, or later
feature may override this envelope. Readiness is not trading permission.

## 10. Fail-Closed and Isolation Rules

The adapter must fail closed when any of the following occurs:

- missing, extra, reordered, subclassed, aliased, or wrong-container authority,
  reader, Gate, capsule, source, or result fields;
- authority token mismatch or non-server-owned configuration;
- path, time, policy, dependency, symbol mapping, or oracle override;
- reader or Gate dependency unavailable before its permitted call;
- reader/Gate status, reason, warning, readiness, component, or safety-envelope
  inconsistency;
- no accepted-attempt capsule, an extra capsule, or a capsule from another
  call;
- a manifest/payload identity mismatch reported by W1, warning, mixed attempt,
  polluted evidence, post-call mutation, or ambiguous provenance;
- account, path, payload, checksum, exception, or internal state entering a
  source or result;
- source construction mismatch or any unexpected exception.

The adapter must not:

- copy or reimplement G148 reader, W1 validators, G149 Gate, G151 adapter,
  G153 pipeline, G170/G171 summary validator, or G178 projector logic;
- expose or persist the private capsule or authority object;
- call a public diagnostics endpoint or use a diagnostics result as facts;
- read environment variables, ambient clock, settings, network, database,
  cache, frontend state, or runtime data outside the approved reader call;
- retry, fallback, reread, sort, round, repair, infer, switch source, or call a
  second dependency;
- return a partial source; or
- call the projector, ReplayRunner, API, MT4, EA, order, execution, or trading
  component.

## 11. Required Contract Vectors

A later tests-only work order must use immutable static vectors. It must not
import or call the future adapter. At minimum it must lock:

- exact authority, previous-identity, immutable JSON aliases,
  accepted-attempt, result, source, and nested field names, order, types,
  constants, and ownership;
- exact function signature and internal-only import boundary;
- zero/one reader, value-validator, and Gate call accounting;
- the exact source-provenance tables in section 7;
- all status/reason pairs and first-failure order;
- exact separation of valid blocked envelopes, invalid reader/Gate returns,
  and sanitized exceptions;
- passed-with-warning rejection and empty-warning success;
- missing, extra, reordered, duplicate, subclassed, alias, wrong-container,
  mixed-attempt, mutation, and caller-override vectors;
- source unavailable on every failure and fixed safety flags on every result;
- no raw payload, account, path, checksum, exception, diagnostics, API, MT4,
  execution, or trading leakage; and
- explicit statements that static vectors do not prove implementation,
  integration, activation, or verification.

## 12. Required Staged Delivery

Later work must remain separately planned and approved:

1. immutable tests-only contract vectors for this adapter boundary;
2. private accepted-attempt reader seam and source-adapter production types;
3. bounded adapter behavior using the existing reader, value validator, and
   DataQualityGate;
4. offline canonical-fixture integration evidence;
5. deterministic non-activating verification;
6. separate contracts and vectors for remaining W6 facts and features; and
7. a separately versioned ReplayRunner W6 stage before W7.

No stage silently includes the next. Contract is not tests, tests are not
implementation, implementation is not integration, integration is not
activation, and activation is not verification.

## 13. WBS and Safety Boundaries

- W1 remains `VERIFIED` authority for Bundle v1 structure, value, filesystem,
  and DataQualityGate behavior. G179 does not alter W1.
- W5 remains `VERIFIED` only for ReplayRunner v1 canonical diagnostics. No W6
  stage is added by G179.
- W6 remains `TESTS_ONLY`. G179 closes only the source-adapter contract gap.
- W7-W21 remain unchanged and unauthorized.
- Reader activation, real MT4, EA, order, execution, Demo auto-execution, Live,
  deployment, and trading remain prohibited.

## 14. G179 Acceptance Checklist

G179 is acceptable only when:

- this document is the only added file;
- the adapter responsibility, future module, exact function, private authority,
  private accepted-attempt capsule, and safe result type are deterministic;
- W1 owns only the generic immutable accepted-attempt capsule and never imports
  W6, G175, or downstream market-facts types;
- the existing public reader and Gate envelopes remain unchanged;
- the reader, existing value validator, Gate, and construction call order is
  unique, with exact zero/one-call behavior and no retries;
- manifest, all four required payloads, reader envelope, Gate result, and
  source identity remain bound to one attempt;
- all 13 G175 source fields and every nested record have exact provenance;
- no raw payload, account, path, checksum, exception, internal token, API,
  diagnostics, MT4, or execution state can leak;
- blocked, invalid-envelope, warning, identity, construction, and exceptional
  outcomes fail closed with exact status/reason pairs;
- Demo-only, Read-only, no-EA, no-execution, and no-trading flags remain fixed;
- tests, implementation, fixture integration, verification, ReplayRunner W6,
  activation, and W7-W21 remain explicitly unimplemented;
- W6 package maturity remains `TESTS_ONLY`;
- `git diff --check` passes; and
- exact scope, ASCII, and isolation checks pass.
