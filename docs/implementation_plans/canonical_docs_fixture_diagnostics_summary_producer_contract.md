# Canonical Docs Fixture Diagnostics Summary Producer Contract

Status: G161 contract-only design. This document defines the missing
server-owned source seam required by the legacy diagnostics activation plan. It
does not add fixture assets, implement a producer, call a reader, change an API,
or activate any runtime capability.

## 1. Purpose and capability state

The legacy diagnostics activation contract requires the default
`docs_fixture_only` source to produce a genuine G151 canonical diagnostics
summary before that source may enter the G158 compatibility adapter.

The intended future flow is:

```text
fixed server-owned canonical docs fixture bundle
    -> G153 canonical diagnostics pipeline
    -> genuine G151 exact 20-key summary
    -> later G158 compatibility adapter integration
```

The capability layers at the start of G161 remain separate:

| Layer | Current state |
| --- | --- |
| Policy | Demo-only, read-only, server-owned source authority is approved. |
| Contract | G159 requires a genuine canonical docs-fixture summary producer. |
| Tests | G160 locks the future legacy API activation boundary. |
| Production implementation | G153 and G158 exist, but this producer does not. |
| Integration | G158 is not connected to the legacy API. |
| Activation | The legacy API still uses its independent old diagnostics chain. |

G161 changes only the contract layer. It does not claim that fixture assets,
the producer, integration, or activation have been implemented.

## 2. Future public boundary

The future producer public function is fixed as:

```python
def build_demo_readonly_canonical_docs_fixture_diagnostics_summary() -> dict[str, Any]:
    ...
```

The function intentionally accepts no caller-controlled values. In
particular, it must not accept:

- `allowed_root`;
- `bundle_dir`;
- `now_utc`;
- source mode;
- request data;
- reader, filesystem, freshness, or DataQualityGate policy;
- previous bundle identity;
- a manifest or payload object.

The no-argument boundary prevents a request, client, writer, manifest, payload,
environment variable, or configuration file from selecting the fixture source
or validation policy.

## 3. Canonical fixture source layout

### 3.1 Existing examples are authoring examples only

The existing directory:

```text
docs/architecture/examples/canonical-mt4-demo-readonly-bundle-v1/
```

contains authoring examples named with the `*.example.json` suffix. Those files
document the protocol, but they are not a filesystem bundle accepted by G148.
They must not be renamed in memory, relabeled, padded, or passed to G153 as if
they already had canonical filenames.

### 3.2 Future runtime fixture bundle

A later, separately reviewed asset task must add an immutable checked-in bundle
at the fixed repository-relative location:

```text
docs/architecture/fixtures/canonical-mt4-demo-readonly-bundle-v1/
```

That bundle must contain exactly the G148 canonical filenames:

```text
snapshot_manifest.json
live_tick.json
latest_bars.json
symbol_spec.json
account_snapshot.json
```

The asset task must prove that the bundle is a valid, internally consistent
Canonical MT4 Demo Readonly Bundle v1 and that its facts remain aligned with the
approved authoring examples. The producer must fail closed if the directory or
any required file is absent.

The fixture bundle must be:

- committed to the repository;
- immutable at runtime;
- a normal directory containing regular files;
- free of symlinks, hard-link assumptions, generated aliases, or optional
  filename mappings;
- clearly marked as synthetic Demo-only documentation data.

## 4. No runtime materialization

The producer must never create a bundle dynamically. It must not:

- copy or rename `*.example.json` files;
- create a temporary directory;
- write, rewrite, delete, move, or replace any file;
- create symlinks or hard links;
- extract an archive;
- download fixture content;
- use `data/`, an MT4 terminal directory, or a broker directory as fallback;
- modify the repository checkout.

This rule keeps the default docs source deterministic and preserves G148 as the
only filesystem reader in the canonical chain.

## 5. Server-owned path authority

The future producer owns fixed internal constants equivalent to:

```text
fixture_root = docs/architecture/fixtures
fixture_bundle_dir =
  docs/architecture/fixtures/canonical-mt4-demo-readonly-bundle-v1
```

The paths must be resolved from a fixed repository anchor in server code. They
must not come from:

- query parameters, headers, body, cookies, or frontend state;
- URL fragments or request extensions;
- environment variables;
- application settings or configuration files;
- current working directory assumptions;
- manifest or payload fields;
- writer output;
- the legacy `mt4_data_path` setting.

Resolved paths and filenames are internal validation details. They must never
appear in a G151 summary, G158 output, API response, log, or exception message
returned to a caller.

## 6. Deterministic fixture reference time

Static documentation data must not use the wall clock for freshness. Otherwise
an unchanged approved fixture would become stale as time passes and tests would
depend on the date they are executed.

The producer must own one fixed UTC reference time:

```text
2026-07-10T02:30:05Z
```

This value is server-owned test-fixture policy. It is deliberately close to the
approved example bundle generation time and must be reviewed together with any
future fixture asset update.

The reference time must not be:

- accepted as a function argument;
- derived from the current wall clock;
- read from the manifest, payloads, writer, request, environment, or settings;
- returned in public output;
- reused for a real reader source.

The fixed reference time is valid only for `docs_fixture_only`. The real
server-side canonical reader path must continue using an actual server-owned
UTC clock and normal freshness policy.

## 7. G153 is the single orchestration owner

The future producer may call only:

```python
build_demo_readonly_canonical_diagnostics_summary(
    allowed_root=<fixed fixture root>,
    bundle_dir=<fixed fixture bundle directory>,
    now_utc=<fixed fixture reference time>,
)
```

It must call G153 exactly once and return the resulting summary without
relabeling, padding, rewriting, weakening, or constructing a parallel envelope.

The producer must not directly import or call:

- G148 filesystem reader;
- G149 canonical DataQualityGate integration;
- G151 canonical summary adapter;
- G158 legacy compatibility adapter;
- the old four-file reader or old diagnostics service.

It must not provide custom read, filesystem, or DataQualityGate policies. G153
and its typed defaults remain the owners of those policies for this fixture
boundary.

## 8. Required G151 output

The only successful producer result is the genuine G151 exact 20-key summary:

```text
passed
status_code
source_scope
validation_stage
fixture_source
bundle_validation_status
component_statuses
block_reasons
warning_reasons
readiness_notes
next_allowed_stage
next_blocked_stage
read_only
demo_only
is_tradable
can_execute
is_trading_permission
is_execution_instruction
allowed_to_call_ea
allowed_to_modify_risk
```

The producer must not add a path, filename, timestamp, checksum, source-reader
status, upstream status, payload, exception, account secret, price, balance,
order, signal, action, lot, ticket, or EA field.

Every output state must keep:

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

`ready_for_readonly_analysis` semantics inside the canonical chain remain only
readiness for sanitized read-only analysis. They are not trading permission or
execution authorization.

## 9. Fail-closed behavior

G153 owns reader, value, DataQualityGate, and summary adaptation failures. The
producer must preserve G153's safe result and must not convert a blocked result
into READY or READY_WITH_WARNINGS.

The following conditions must remain blocked:

- fixture root or bundle directory missing;
- unexpected, missing, renamed, or extra required bundle files;
- symlink, path escape, unreadable file, invalid UTF-8, invalid JSON, or
  duplicate JSON object key;
- manifest instability or mixed generation;
- integrity failure;
- structure, identity, value, or freshness failure;
- unknown or disallowed warning;
- DataQualityGate rejection;
- any unexpected dependency exception.

There is no fallback to:

- `DemoReadOnlyDocsFixtureValidationSummary`;
- ad hoc G151 construction;
- the old diagnostics reader or service;
- the three-file demo reader;
- a live or Demo MT4 directory;
- a second validation or DataQualityGate chain.

If the future producer itself cannot invoke G153, the caller must treat that as
invalid input to the next boundary. It must not manufacture a successful G151
summary.

## 10. Integration boundary

This producer is a source seam only. It must not:

- call G158;
- construct `Mt4DiagnosticsResponse`;
- modify either diagnostics route;
- inspect request values;
- select between docs and reader modes;
- activate a canonical reader source;
- modify frontend behavior;
- connect to MT4 or an account;
- grant analysis, trading, risk, EA, or execution authority.

A later legacy API activation task may call this producer only after
SourceConfigGuard has selected `docs_fixture_only`. That route then passes the
genuine G151 result to G158 exactly once.

## 11. Required staged delivery after G161

No stage is automatically authorized. Future work remains separated:

1. **Tests-only producer contract.** Lock the no-argument interface, fixed
   source authority, fixed reference time, G153 delegation, exact G151 output,
   no runtime writes, and fail-closed behavior.
2. **Canonical fixture asset task.** Add and review the canonical-named bundle
   under the fixed fixture directory. Do not implement the producer in the same
   task.
3. **Pure producer implementation.** Add the no-argument server-owned seam and
   direct tests. Do not modify an API in that task.
4. **Producer safety hardening.** Verify missing assets, contaminated outputs,
   exception handling, input isolation, and no path or timestamp leakage.
5. **Legacy API activation.** Connect SourceConfigGuard, the approved docs
   producer or server reader pipeline, and G158 only after all prerequisites
   pass review and merge.
6. **Review and fast-forward merge.** Each stage requires independent review,
   explicit user approval, and `--ff-only` merge.
7. **Release decision.** Tagging remains a separate user-approved task.

## 12. Explicit non-goals for G161

G161 does not:

- add or modify fixture files;
- implement the producer;
- add tests;
- modify G148, G149, G151, G153, or G158;
- modify or activate either diagnostics API;
- call or enable a reader;
- read real MT4 files or `data/`;
- read environment variables or settings;
- modify frontend, MT4, MQL4, models, or dependencies;
- implement Agent, LLM, RiskGate, PositionSizing, ExecutionGate, or EA logic;
- add automatic Demo trading or live trading;
- create trading permission or execution authority.

## 13. Acceptance checklist

G161 is complete only when review confirms that this document alone defines:

- the no-argument future producer interface;
- the distinction between authoring examples and a canonical runtime fixture;
- the fixed future canonical fixture directory and exact filenames;
- the prohibition on runtime copy, rename, temp directories, links, or writes;
- fixed server-side path authority;
- the deterministic server-owned fixture reference time;
- G153 as the only orchestration dependency;
- the genuine G151 exact 20-key output boundary;
- fixed read-only, Demo-only, non-tradable, and non-executable flags;
- fail-closed behavior with no fallback to old summaries or readers;
- separation from G158, API integration, reader activation, MT4, and trading;
- the tests, assets, implementation, hardening, activation, review, merge, and
  release sequence.

This document is an architecture and safety contract only. It is not evidence
that canonical fixture assets, a producer, API migration, MT4 integration, or
any trading capability exists.
