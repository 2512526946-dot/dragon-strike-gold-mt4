# Canonical Bundle ReplayRunner v1 Contract

Status: G168 contract-only design. This document advances the narrow W5
ReplayRunner boundary from `POLICY_ONLY` to `CONTRACT_ONLY`. It does not add
fixtures, tests, production code, API integration, reader activation, MT4
access, analysis, risk logic, execution, or trading permission.

## 1. Purpose and capability state

ReplayRunner v1 is a deterministic, offline harness for replaying one
server-owned Canonical MT4 Demo Readonly Bundle v1 fixture through the existing
canonical diagnostics chain. Its first stage is deliberately limited to:

```text
registered offline replay case
    -> fixed server-owned fixture root, bundle directory, and UTC time
    -> G153 canonical diagnostics pipeline exactly once
    -> genuine G151 safe diagnostics summary
    -> typed replay result
```

This boundary supplies deterministic evidence for later W5 work. It is not the
complete Demo decision chain described by the WBS. Facts and features, analysis,
TradePlan, RiskGate, PositionSizing, Shadow Mode, ExecutionGate, adapters, EA,
orders, and execution feedback require separately approved contracts and
implementations.

The capability layers remain distinct:

| Layer | State after G168 |
| --- | --- |
| Policy | Offline, deterministic, Demo-only, read-only replay is approved. |
| Contract | This document defines ReplayRunner v1 inputs, results, orchestration, and failure semantics. |
| Tests | Not implemented. A later tests-only task must lock contract vectors. |
| Production implementation | Not implemented. |
| Integration | Not implemented. |
| Activation | Not implemented. |
| Verification | Not implemented. |

## 2. Authority and non-goals

ReplayRunner is an internal offline evidence tool. It has no request-facing or
trading authority. A replay result must never be interpreted as:

- permission to read a real MT4 terminal directory;
- live source readiness;
- permission to perform market analysis;
- a trading signal, order instruction, or position recommendation;
- execution authorization;
- Shadow Mode, Demo execution, or Live activation;
- proof that any later W5-W20 capability is implemented or verified.

The runner must not expose an API route, CLI that accepts arbitrary paths, UI
source selector, daemon, scheduler, background worker, or automatic workflow.

## 3. Future public boundary

The future implementation must expose one pure orchestration entry point with
no ambient source selection:

```python
def run_canonical_bundle_replay_case(
    *,
    replay_case: CanonicalBundleReplayCaseV1,
) -> CanonicalBundleReplayResultV1:
    ...
```

Both types must be frozen, slotted dataclasses. Exact field order is part of the
contract.

```python
@dataclass(frozen=True, slots=True)
class CanonicalBundleReplayCaseV1:
    replay_contract_version: str
    case_id: str
    fixture_id: str
    expected_outcome: str
    expected_status_code: str
    expected_block_reasons: tuple[str, ...]
    expected_warning_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CanonicalBundleReplayResultV1:
    replay_contract_version: str
    case_id: str
    passed: bool
    status_code: str
    canonical_summary: dict[str, Any]
    replay_reason_codes: tuple[str, ...]
    canonical_block_reasons: tuple[str, ...]
    canonical_warning_codes: tuple[str, ...]
    deterministic_observations: tuple[str, ...]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
```

The public function accepts exactly one keyword-only `replay_case`. It must not
accept paths, clocks, source modes, policy objects, dependencies, callbacks,
requests, settings, environment values, payloads, or writer output.

### 3.1 Strict input types

An accepted case must satisfy all of the following:

- `type(replay_case) is CanonicalBundleReplayCaseV1`;
- `replay_contract_version == "canonical_bundle_replay_v1"`;
- every string is an exact built-in, non-empty `str`;
- every code collection is an exact built-in `tuple[str, ...]` with no empty,
  duplicate, subclass, or unknown values;
- `case_id` and `fixture_id` match a conservative lowercase identifier grammar;
- `fixture_id` exists in the server-owned registry;
- expected outcome, status, reasons, and warnings form one allowed vector.

Invalid input must not be coerced, normalized, padded, or repaired.

## 4. Server-owned case registry

Replay source authority belongs to a fixed registry in future production code.
Each registry entry owns, as one immutable record:

```text
fixture_id
allowed_root
bundle_dir
reference_time_utc
previous_identity
expected_outcome
expected_status_code
expected_block_reasons
expected_warning_codes
```

The registry is code-owned and versioned. A public replay case carries only a
`fixture_id`; it cannot provide or override the paths, reference time, previous
identity, policies, or expected oracle.

The initial positive case may reference the existing checked-in bundle:

```text
docs/architecture/fixtures/canonical-mt4-demo-readonly-bundle-v1/
```

using the existing docs-fixture reference time:

```text
2026-07-10T02:30:05Z
```

This document does not approve additional fixture assets. Warning, stale,
malformed, mixed-generation, and failure vectors require later, separately
scoped asset or tests-only tasks. A case must never materialize, copy, rename,
rewrite, delete, or download a bundle at runtime.

## 5. Deterministic clock and identity

Every registry entry owns one timezone-aware UTC `reference_time_utc`. The
runner must not call the wall clock or derive time from the environment,
filesystem metadata, current working directory, request, manifest, or payload.

`case_id`, `fixture_id`, replay contract version, registry version, bundle
identity, and policy versions form the replay evidence identity. Internal file
digests may be used by existing canonical validation, but digest values and
filesystem paths must not appear in the public replay result.

Running an unchanged registered case against unchanged code and policy versions
must produce an equal result. Ordering of stages, reasons, warnings, and
observations is deterministic and contract-owned.

## 6. G153 is the only v1 orchestration dependency

After strict case and registry validation, ReplayRunner v1 must call exactly:

```python
build_demo_readonly_canonical_diagnostics_summary(
    allowed_root=<registry-owned allowed_root>,
    bundle_dir=<registry-owned bundle_dir>,
    now_utc=<registry-owned reference_time_utc>,
    previous_identity=<registry-owned previous_identity>,
)
```

It must call G153 exactly once for each accepted case. It must omit
`previous_identity` when the registry value is `None`, and it must not pass
custom read, filesystem, or DataQualityGate policies in v1.

The runner must not directly call or copy:

- G148 filesystem reader;
- G149 DataQualityGate;
- G151 summary adapter;
- G158 legacy compatibility adapter;
- either diagnostics API route;
- the old MT4 diagnostics reader or service.

The runner must not create a parallel reader, Gate, summary envelope, freshness
policy, source selector, or fallback chain.

## 7. Genuine G151 summary boundary

The only stage result accepted from G153 is a genuine G151 exact 20-key safe
summary. ReplayRunner must validate it by reusing the existing public G151
contract or one later approved shared validator. It must not copy the G151
validation algorithm into a parallel replay implementation.

The accepted summary states are:

```text
CANONICAL_DIAGNOSTICS_SUMMARY_READY
CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS
CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID
CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE
```

The summary's `passed`, nested source status, block reason, warning list,
readiness notes, next stages, and fixed safety flags must remain mutually
consistent. Missing, extra, reordered, subclassed, polluted, contradictory, or
unknown envelope content is replay input failure, not a successful replay.

The runner must not mutate, relabel, pad, filter, or repair a valid G153 result.
The result's `canonical_summary` is a detached safe snapshot whose content is
equal to the validated G151 result. Neither object may be mutated during replay.

## 8. Replay outcome mapping

Allowed `expected_outcome` values are:

```text
READY
READY_WITH_WARNINGS
BLOCKED
INPUT_INVALID
SAFE_FAILURE
```

Replay success means only that the actual deterministic stage result exactly
matches the registered oracle. It does not mean that the canonical data passed
or that analysis may proceed.

The replay result uses these status codes:

| Replay status | Meaning |
| --- | --- |
| `CANONICAL_BUNDLE_REPLAY_MATCHED` | Actual safe G151 status, reasons, and warnings exactly match the registry oracle. |
| `CANONICAL_BUNDLE_REPLAY_INPUT_INVALID` | Case or registry evidence is invalid before G153. |
| `CANONICAL_BUNDLE_REPLAY_RESULT_INVALID` | G153 returned an unsafe or contradictory envelope. |
| `CANONICAL_BUNDLE_REPLAY_MISMATCH` | Safe actual output does not equal the expected status/reason/warning oracle. |
| `CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE` | An exception was sanitized at the replay boundary. |

`passed` is true only for `CANONICAL_BUNDLE_REPLAY_MATCHED`. A matched BLOCKED,
INPUT_INVALID, or SAFE_FAILURE scenario may therefore have replay `passed=true`
while its nested G151 `passed=false`. The two fields answer different questions
and must never be conflated.

Replay-level reason codes are fixed to:

```text
REPLAY_CASE_INPUT_INVALID
REPLAY_CASE_REGISTRY_INVALID
REPLAY_CASE_RESULT_INVALID
REPLAY_CASE_EXPECTATION_MISMATCH
REPLAY_CASE_EXCEPTION_SANITIZED
```

A matched replay has `replay_reason_codes == ()`. Its ordered
`canonical_block_reasons` and `canonical_warning_codes` must exactly equal the
validated G151 summary and the registered oracle.

A replay-boundary failure has an empty `canonical_summary`, empty
`canonical_block_reasons`, empty `canonical_warning_codes`, and exactly one
fixed `replay_reason_codes` item matching its replay status. The two reason
namespaces must never be combined. Unknown or sensitive text must produce
`CANONICAL_BUNDLE_REPLAY_RESULT_INVALID` with the fixed replay reason
`REPLAY_CASE_RESULT_INVALID` and must not be copied into any result field.

## 9. Golden contract vectors

A later tests-only task must define immutable vectors for at least:

1. READY with no warning;
2. READY_WITH_WARNINGS for each approved warning and approved ordering;
3. stale BLOCKED;
4. malformed structure BLOCKED;
5. mixed-generation BLOCKED;
6. INPUT_INVALID;
7. SAFE_FAILURE;
8. unknown fixture id;
9. missing, extra, duplicate, reordered, or subclassed case evidence;
10. missing, extra, polluted, contradictory, or subclassed G151 output;
11. expected/actual status, reason, or warning mismatch;
12. exception sanitization;
13. repeated execution equality;
14. input, registry, fixture, and G153 output immutability.

Contract vectors must distinguish a replay match from canonical data readiness.
They must not use a mock main chain as proof that G153 integration works. At
least one successful vector must use the existing checked-in canonical fixture
and real G153. Spies may verify exact call shape and count only after that real
path is independently proven.

## 10. Controlled failure injection

Failure injection is offline and registry-owned. V1 uses immutable malformed or
boundary-specific fixture cases rather than arbitrary callbacks, monkeypatches,
client payloads, environment variables, or runtime file mutation.

An accepted failure case still calls G153 once and observes its normal
fail-closed behavior. Failures before case acceptance call G153 zero times.
Failures after the single G153 call never retry, fallback, switch source, repair
the summary, or call G153 again.

Infrastructure exception probes may use controlled test spies in the later
tests-only task, but those probes do not prove the real replay main chain.

## 11. Exact safety flags and output filtering

Every replay result fixes:

```text
read_only = true
demo_only = true
is_tradable = false
can_execute = false
is_execution_instruction = false
allowed_to_call_ea = false
```

No input, result, log, exception, observation, or artifact may expose:

- absolute or relative filesystem paths;
- bridge or candidate directories;
- raw manifest or payload content;
- file digests or digest internals;
- exception text or tracebacks;
- environment or settings values;
- credentials, account identifiers, or broker tickets;
- source-reader internal status fields not already present in the approved G151
  summary contract;
- signals, actions, lot sizes, orders, EA commands, or execution instructions.

Unknown values and unsafe text are never echoed. They map to one fixed replay
status and one fixed public reason code.

## 12. No ambient I/O or side effects

ReplayRunner v1 may perform only the checked-in fixture reads already owned by
G153/G148. It must not:

- access a real terminal, broker directory, or runtime `data/` directory;
- read environment variables, settings, credentials, network services, or the
  wall clock;
- accept request, query, header, body, cookie, frontend, or CLI source values;
- write files, create temporary bundles, mutate fixtures, persist state, or
  start a background process;
- call an API, legacy reader, EA, order adapter, or trading service.

The runner must behave independently of the process current working directory.

## 13. Versioning and future stages

`canonical_bundle_replay_v1` contains one stage only:

```text
canonical_diagnostics
```

Later W6-W13 stages must not be appended silently. Adding facts, features,
analysis, TradePlan, RiskGate, PositionSizing, Shadow Mode, ExecutionGate, or a
fake adapter requires a new approved contract version and separate maturity
transitions. Existing v1 golden vectors must remain reproducible.

ReplayRunner implementation does not activate any stage. Integration into a
test harness does not activate analysis or execution. Verification requires a
separate reviewed evidence task after implementation and integration.

## 14. Fail-closed algorithm

The future runner must use this order:

1. validate the exact replay case type and fields;
2. resolve one immutable registry entry by `fixture_id`;
3. validate registry consistency and expected oracle;
4. snapshot immutable input and fixture evidence;
5. call G153 exactly once with registry-owned values;
6. validate the genuine G151 envelope without rewriting it;
7. compare actual status, reasons, and warnings with the oracle;
8. construct one fresh exact replay result;
9. verify input and fixture evidence did not change;
10. return the result.

Any failure returns a fresh safe result. No failure may retry, choose another
fixture, use the docs producer as fallback, call a legacy chain, or continue to
another stage.

## 15. Delivery sequence

The remaining W5 delivery order is mandatory:

```text
G168 contract
    -> tests-only contract vectors
    -> production types and pure runner
    -> real G153 integration evidence
    -> deterministic regression verification
```

Each arrow requires a separate reviewed work order and explicit user approval.
No stage may combine tests, implementation, integration, activation, or
verification merely because this contract describes their future boundaries.

## 16. G168 acceptance checklist

G168 is complete only when this document:

- defines one deterministic offline v1 objective;
- fixes typed case and result fields;
- assigns all source, fixture, clock, identity, and oracle authority to the
  server-owned registry;
- makes G153 the only orchestration dependency and fixes zero/one call rules;
- defines strict G151 validation without a parallel reader, Gate, or envelope;
- defines replay outcome mapping and safe public reasons;
- defines golden vectors, controlled failure injection, immutability, and
  repeated-run equality;
- fixes Demo-only, Read-only, non-trading, non-execution semantics;
- prohibits ambient I/O, runtime writes, real MT4, APIs, EA, and trading;
- keeps tests, implementation, integration, activation, and verification
  explicitly unimplemented;
- preserves W6-W21 as separately authorized future work.

This document is a contract, not runtime evidence. Its presence does not prove
that ReplayRunner exists or that any replay, analysis, execution, or trading
capability is active.
