# Canonical Gold Market Facts Docs-Fixture Integration Contract

Status: contract only
Version: 1.0
Scope: W6 offline canonical-fixture integration boundary
Mode: Demo-only, Read-only, non-trading

## 1. Purpose

This contract defines the future server-owned integration boundary that may
construct one fixed authority for the existing G182 bounded source adapter and
run it against the checked-in canonical docs fixture.

G175 defines the market-facts source and snapshot records. G178 implements the
pure-memory projector. G179 defines the same-attempt source-adapter boundary.
G180 locks that boundary with static vectors. G181 implements its private
accepted-attempt reader seam and production types. G182 implements bounded
reader-to-Gate orchestration and detached source construction.

Those artifacts do not define or authorize a W6 fixture factory. In particular,
the existing diagnostics producer and the W5 ReplayRunner own different
purposes and authority. Their fixed fixture constants are evidence that the
checked-in fixture exists, not authority for W6 to import or reuse them.

This document defines a contract. It does not implement the integration entry
point, create an authority at runtime, call the reader, activate MT4, or prove
integration or verification.

## 2. Capability Boundary

This contract may define only:

- one W6-owned, server-owned, internal-only, zero-argument fixture entry point;
- one fixed factory for the existing private G179 authority capsule;
- the exact checked-in fixture, reference time, policies, and prior identity;
- the single call from that entry point to the existing G182 adapter;
- strict result acceptance, call accounting, fail-closed behavior, and
  isolation rules; and
- later contract-vector, implementation, integration-evidence, and
  deterministic-verification stages.

This contract does not authorize:

- a request-selectable path, clock, policy, dependency, source, or oracle;
- any change to G148, G149, G151, G153, G175, G178, G179, or G182 behavior;
- a second reader, validator, Gate, adapter, projector, or ReplayRunner path;
- diagnostics-summary or W5 ReplayRunner output as market facts;
- API, CLI, frontend, plugin, settings, environment, network, database, cache,
  runtime `data/`, or real MT4 integration;
- reader activation, ReplayRunner W6 stage, W7-W21 work, EA calls, orders,
  execution, trading, deployment, or activation; or
- a claim that W6 is integrated, activated, or verified.

## 3. Future Production Surface

The future integration implementation is owned by exactly this module:

```text
backend/app/services/canonical_gold_market_facts_docs_fixture_integration.py
```

It may expose exactly one production name:

```python
def build_canonical_gold_market_facts_docs_fixture_source_v1(
) -> CanonicalGoldMarketFactsSourceAdapterResultV1:
    ...
```

The function has no positional parameters, keyword parameters, variadic
parameters, dependency injection, context object, or ambient configuration.
Its `__all__`, if present, is exactly:

```python
("build_canonical_gold_market_facts_docs_fixture_source_v1",)
```

No API router, frontend, plugin, settings layer, strategy, risk component,
execution component, or arbitrary service caller may provide the authority.
The function is an internal offline Demo fixture boundary, not a source-mode
selector and not a reader-activation surface.

## 4. Private Authority Ownership

The future integration module is the only additional server integration
authorized to construct the existing exact private
`_CanonicalGoldMarketFactsSourceAuthorityV1` type. This narrow authorization
exists only for the fixed zero-argument function in section 3.

The integration module may privately import exactly these G182-owned symbols.
The authority token, authority type, result type, and adapter callable already
exist; the validator and sanitizer are the future private seams defined below:

```text
_AUTHORITY_TOKEN
_CanonicalGoldMarketFactsSourceAuthorityV1
_build_canonical_gold_market_facts_source_adapter_safe_failure_v1
_is_safe_canonical_gold_market_facts_source_adapter_result_v1
CanonicalGoldMarketFactsSourceAdapterResultV1
build_server_owned_canonical_gold_market_facts_source_v1
```

It must not re-export, alias publicly, persist, log, serialize, or return the
private token or authority object. It must not import or construct the private
accepted-attempt capsule; W1 remains its sole owner.

No other module receives authority from this contract. A test importing a
private symbol can inspect the future implementation but does not become a
production authority source.

### 4.1 G182-owned result authority

The two private helper names above are future G182-owned integration seams.
They are not implemented by this contract and must not be public or included
in `__all__`. Their exact future interfaces are:

```python
def _is_safe_canonical_gold_market_facts_source_adapter_result_v1(
    *,
    result: object,
) -> bool:
    ...

def _build_canonical_gold_market_facts_source_adapter_safe_failure_v1(
) -> CanonicalGoldMarketFactsSourceAdapterResultV1:
    ...
```

The validator is the sole authority for exact G182 result and nested source
type validation. It owns the 15-field order, strict built-in and dataclass
types, closed status/reason/warning combinations, source availability,
G175-source exact type through G182's existing private G178 alias, and all
eight safety flags. It is pure memory, does not mutate its input, performs no
I/O or dependency call, catches validation exceptions, and returns exact
built-in `False` for every invalid value.

The safe-failure constructor is the sole authority for the fixed sanitized
adapter failure. It reuses G182's existing private blocked-result construction
and returns a fresh exact result with
`CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE` and
`GOLD_SOURCE_EXCEPTION_SANITIZED`. It performs no I/O or dependency call.

Only G182 may import its private G178 source alias or interpret adapter status
and reason mappings. The integration module must call these helpers; it must
not import G178, reconstruct nested source type rules, copy the validator,
construct an adapter result directly, or reproduce the status mapping. Adding
these private pure helpers in a later implementation stage does not change the
existing public G182 interface or its bounded adapter behavior.

## 5. Exact Fixed Fixture Authority

### 5.1 Paths and fixture identity

The future module derives its repository root only by:

```python
Path(__file__).resolve().parents[3]
```

It constructs these server-owned concrete paths with `pathlib.Path`:

```text
allowed_root = <repository root>/docs/architecture/fixtures
bundle_dir = <allowed_root>/canonical-mt4-demo-readonly-bundle-v1
```

Runtime path types must be the platform's exact concrete `WindowsPath` or
`PosixPath` type and must match. A caller string, `PurePath`, subclass,
wrong-platform path, alternate root, symlink-derived replacement, working
directory, environment value, or runtime `data/` path is invalid.

The accepted fixture identity is fixed to:

```text
schema_version = "1.0"
bundle_id = "demo-bundle-000000000001"
sequence = 1
canonical_symbol = "XAUUSD"
broker_symbol = "GOLD"
```

These values are an integration oracle checked after W1 accepts the bundle.
They do not replace or duplicate W1 manifest/payload identity validation.

### 5.2 Reference time

The sole reference time is an exact built-in `datetime.datetime`:

```python
datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
```

No ambient clock, request time, filesystem time, alternate UTC spelling,
rounding, truncation, or caller override is allowed.

### 5.3 Previous identity and policies

The authority values are fixed exactly as follows:

| Authority field | Exact value |
| --- | --- |
| `authority_token` | Existing G182 module-private singleton identity |
| `allowed_root` | Fixed path from section 5.1 |
| `bundle_dir` | Fixed path from section 5.1 |
| `reference_time_utc` | Fixed exact UTC datetime from section 5.2 |
| `previous_identity` | `None` |
| `read_policy` | Exact policy values below |
| `filesystem_policy` | Exact policy values below |
| `data_quality_policy` | Exact policy values below |
| `policy_profile_version` | `canonical_gold_market_facts_policy_v1` |

The exact `CanonicalMt4DemoReadonlyBundleV1ReadPolicy` values are:

```text
writer_heartbeat_max_age_seconds = 15
live_tick_max_age_seconds = 10
latest_bars_max_age_seconds = 60
symbol_spec_max_age_seconds = 86400
account_snapshot_max_age_seconds = 30
max_future_skew_seconds = 5
```

The exact `CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy` values are:

```text
manifest_max_bytes = 65536
live_tick_max_bytes = 32768
latest_bars_max_bytes = 2097152
symbol_spec_max_bytes = 65536
account_snapshot_max_bytes = 131072
max_manifest_consistency_retries = 0
```

The exact `CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy` value is:

```text
allow_upstream_warnings = false
```

Every scalar must have its exact built-in type. A missing, extra, reordered,
subclassed, aliased, mutable, or different value is authority invalid. The
factory must create fresh policy and authority objects for every invocation.

## 6. Sole Call Chain

The future zero-argument function performs these steps in order:

1. Confirm that its fixed constants, exact private imports, direct G182
   callable, G182 validator, and G182 safe-failure constructor are available
   and unchanged.
2. Construct fresh exact policy objects from section 5.3.
3. Construct one fresh private G182 authority object from section 5.
4. Freeze a scalar snapshot of the authority values for post-call comparison.
5. Call `build_server_owned_canonical_gold_market_facts_source_v1` exactly once
   with only `authority=<fresh authority>`.
6. Confirm the authority snapshot is unchanged. On drift, return one result
   from the G182 safe-failure constructor without validating or repairing the
   adapter result.
7. Call the G182-owned result validator exactly once with only
   `result=<adapter result>`. If it returns exact `False` or raises, return one
   result from the G182 safe-failure constructor.
8. Return a validated blocked result unchanged without inspecting or
   reclassifying its status or source internals.
9. On validated READY, compare only the five fixed scalar fixture identity
   fields in section 5.1. On mismatch, return one result from the G182
   safe-failure constructor; do not construct or repair a result locally.
10. Return the validated exact adapter result only after all applicable checks
    pass.
11. Release the private authority and any result-local references when the
    call stack unwinds.

The integration boundary must not call the reader, value validator, or Gate
directly. G182 owns their sole order and call accounting. It must not call the
G178 projector, diagnostics producer, G151/G153 pipeline, W5 ReplayRunner, or a
second adapter.

## 7. Call Accounting

| Outcome | G182 adapter | G182 validator | G182 sanitizer |
| --- | ---: | ---: | ---: |
| Fixed constant or authority construction invalid while sanitizer is available | 0 | 0 | 1 |
| G182 callable unavailable or changed before invocation | 0 | 0 | 1 |
| G182 validator unavailable or changed before invocation | 0 | 0 | 1 |
| G182 sanitizer unavailable or changed before invocation | 0 | 0 | 0 |
| G182 invocation begins and raises | 1 | 0 | 1 |
| Post-call authority drift | 1 | 0 | 1 |
| G182 returns an invalid or polluted result | 1 | 1 | 1 |
| G182 returns a validated blocked result | 1 | 1 | 0 |
| G182 returns validated READY with fixed identity mismatch | 1 | 1 | 1 |
| G182 returns validated READY for the fixed fixture | 1 | 1 | 0 |

An invocation consumes its one permitted adapter call when control enters
G182. The validator is called at most once and only after post-call authority
stability passes. The sanitizer is called exactly once only on a failure path.
No failure permits retry, fallback, another call of the same dependency, a
reread, source switching, local result construction, or result repair.

The G182 sanitizer is the terminal failure constructor. If it is unavailable,
changed, raises, or returns an invalid value, the fixture integration is
unavailable and returns no source. The integration module must not handcraft a
fallback envelope, expose a partial result, call another dependency, or log
exception details.

## 8. Adapter Result Acceptance

The integration module must submit the opaque adapter return to the exact
G182-owned validator from section 4.1. It may treat the return as a G182 result
only after that validator returns exact built-in `True`. The result's exact
runtime type, 15 fields, order, strict types, status/reason/warning mapping,
nested G175 source type, source availability, and eight safety flags remain
exclusively governed by G179/G182.

Every accepted result has exactly:

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

A validator-approved G182 blocked result is returned unchanged. The
integration boundary must not inspect or relabel a reader block, warning
rejection, Gate block, identity block, source-construction block, or G182 safe
failure.

An invalid type, contradictory field combination, mutable or subclassed tuple,
non-empty warning tuple, unsafe flag, partial source, or nested source type
error is rejected only by the G182-owned validator. A validated READY source
whose five scalar fixture identity fields differ from section 5.1 is rejected
by the integration identity comparison. An unexpected integration exception
is also a boundary failure. Every such path must call the G182-owned
safe-failure constructor exactly once and return its fresh result:

```text
status_code = CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE
reason_codes = (GOLD_SOURCE_EXCEPTION_SANITIZED,)
warning_codes = ()
source_available = false
source = None
```

The fixed safety flags remain unchanged. The integration module does not
construct this envelope and does not import its private status constants. It
must not inspect or classify reader, value, Gate, capsule, manifest, payload,
result, or nested source details and must not become a parallel G182 adapter,
validator, status mapper, or result-repair algorithm.

## 9. Same-Attempt and W1 Authority

The approved fixture run is one G182 invocation and therefore one W1 accepted
attempt. The reader envelope, manifest, four required payloads, value-validator
result, Gate result, and G175 source must originate from that same invocation.

W1 exclusively owns:

- filesystem containment and symlink protection;
- file-size, JSON, manifest-consistency, and checksum checks;
- manifest and payload schema/value validation;
- manifest/payload identity equality;
- accepted-attempt token and capsule creation; and
- the reader/value/Gate status details consumed by G182.

The integration module checks only fixed factory authority, direct callable
identity, exact G182 result shape, fixed fixture identity, and post-call
authority drift. It must not parse fixture files, duplicate W1 checks, inspect
raw payloads, or combine evidence from different attempts.

## 10. Immutability and Determinism

Later integration evidence must prove all of the following:

- the checked-in fixture tree is byte-for-byte unchanged before and after the
  call without exposing digests in a public result;
- the fixed authority values and direct dependency identities are unchanged;
- repeated genuine executions return equal adapter results;
- every execution returns a fresh result object and a fresh detached source;
- nested source records and tuples are fresh, frozen, and detached;
- mutating or replacing any returned local reference cannot alter fixture
  assets, another result, or a later result; and
- no path, raw payload, checksum, exception text, traceback, internal source
  status, or private token appears in the public result or test diagnostics.

Determinism here is an offline fixture property. It is not reader activation,
real MT4 integration, market-data freshness evidence, or trading permission.

## 11. Fail-Closed Rules

The future boundary fails closed for:

- missing, extra, reordered, subclassed, aliased, mutable, or wrong-container
  fixed constants, policies, authority fields, result fields, source fields, or
  identity values;
- a caller-supplied path, clock, previous identity, policy, dependency, source,
  expected status, reason, warning, or oracle;
- private token, authority type, adapter callable, G182 validator, G182
  sanitizer, fixture path, reference time, policy, or expected identity drift;
- dependency unavailability, authority-construction failure, G182 exception,
  invalid G182 result, READY identity mismatch, or post-call authority drift;
- warning-bearing, partial, unsafe, contradictory, or polluted output; or
- any attempt to use diagnostics, W5 ReplayRunner, runtime `data/`, environment,
  settings, network, database, cache, API, frontend, MT4, or EA state.

The boundary must not sort, normalize, repair, narrow, retry, fallback, infer,
substitute a fixture, switch source, alter policy, or continue after failure.

## 12. Isolation

The integration implementation must not import or call:

- `demo_readonly_canonical_docs_fixture_diagnostics_summary_producer`;
- `canonical_bundle_replay_runner`;
- G151 diagnostics adapter or G153 diagnostics pipeline;
- G178 projector;
- API routers, settings, frontend, plugin, MT4, EA, strategy, risk, order,
  execution, or trading modules.

The G178 prohibition applies to the integration module. The G182-owned
validator may continue using G182's existing private G178 source-type alias so
that exact nested source validation remains inside G182. The integration
module may not import that alias or any G178 symbol directly.

It may read only the approved checked-in fixture through the existing W1
reader reached inside the single G182 call. It must not read environment
variables, an ambient clock, the working directory, runtime `data/`, network,
database, cache, or arbitrary files.

The fixed fixture is Demo-only and Read-only. READY means only that the
detached G175 source is safe for later offline W6 processing. READY is not
activation, execution authority, or permission to trade.

## 13. Required Contract Vectors

A later tests-only work order must use immutable static vectors and must not
import or implement the future integration module. It must lock:

- the exact future module, single public function, zero-argument signature,
  return annotation, and `__all__` rule;
- exact private-import authority, G182 validator/sanitizer interfaces, and
  non-re-export rules;
- exact path derivation, fixture directory, reference time, previous identity,
  policy profile, read policy, filesystem policy, and Gate policy;
- exact fixture identity and W1 ownership boundary;
- zero/one G182 call accounting and no direct reader/Gate call;
- exact G182-owned adapter-result validation and sanitized failure envelope;
- genuine READY, valid G182 blocked, invalid result, exception, identity drift,
  policy drift, dependency drift, and post-call drift vectors;
- fixture, authority, result, and nested-source immutability requirements;
- repeated execution determinism and fresh-object requirements; and
- no diagnostics producer, W5 ReplayRunner, projector, ambient I/O, API, MT4,
  EA, order, execution, trading, activation, or verification claim.

Static vectors are tests-only evidence. They do not prove implementation,
fixture integration, activation, or verification.

## 14. Required Staged Delivery

Later work remains separately planned and approved:

1. immutable tests-only vectors for this contract;
2. the zero-argument production fixture integration boundary;
3. genuine offline fixture integration evidence through W1 and G182;
4. deterministic non-activating verification;
5. separate contracts and delivery for later W6 facts and features; and
6. a separately versioned ReplayRunner W6 stage before W7.

No stage silently includes the next. Contract is not tests, tests are not
implementation, implementation is not integration, integration is not
activation, and activation is not verification.

## 15. Acceptance Checklist

This contract is acceptable only if all statements below remain true:

- one exact W6-owned zero-argument fixture function is defined;
- no caller can provide or override path, time, policy, dependency, or oracle;
- fixture path, reference time, previous identity, policies, and profile are
  exact server-owned constants;
- the private G182 authority remains private and is never returned or logged;
- the integration function calls G182 zero or one time and never calls W1
  dependencies directly;
- exact result/source validation and sanitized result construction remain
  G182-owned private pure helpers and are never copied into integration;
- same-attempt and manifest/payload validation remain exclusively W1/G182
  responsibilities;
- valid blocked G182 results retain their exact classifications;
- invalid or exceptional outer results are sanitized without retry or repair;
- READY additionally proves the exact fixed fixture identity;
- all results preserve Demo-only, Read-only, non-trading safety flags;
- diagnostics producer and W5 ReplayRunner authority remain isolated;
- no projector, API, reader activation, real MT4, EA, order, execution,
  trading, deployment, or activation capability is added; and
- tests, implementation, integration evidence, deterministic verification,
  later features, and ReplayRunner W6 stage remain future work.

## 16. WBS Statement

This docs-only contract advances only the narrow fixture-integration boundary
from policy-only to contract-only. W6 as a package remains `TESTS_ONLY`.

The contract does not change weighted WBS hours, Demo or Live progress, or
Live activation readiness. It does not authorize a source adapter runtime,
reader/MT4 integration, activation, verification, execution, or trading.
