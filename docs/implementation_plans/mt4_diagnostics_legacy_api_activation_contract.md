# Legacy MT4 Diagnostics API Activation Boundary Contract

Status: G159 contract-only design. This document defines the boundary for a
future migration of `GET /api/mt4/diagnostics`. It does not activate the route,
change source configuration, call a reader, or implement runtime integration.

## 1. Purpose and current capability state

The old MT4 diagnostics endpoint is a deprecated compatibility surface. The
canonical public diagnostics endpoint remains:

```text
GET /api/demo-readonly/diagnostics
```

The future activation goal for the old endpoint is a thin, read-only
compatibility flow:

```text
server-owned source config
    -> SourceConfigGuard
    -> approved canonical summary source
    -> G151 canonical 20-key diagnostics summary
    -> G158 legacy compatibility adapter
    -> exact Mt4DiagnosticsResponse
```

The capability layers at the start of G159 are intentionally distinct:

| Layer | Current state |
| --- | --- |
| Policy | Demo-only, read-only, and no execution authority are approved. |
| Contract | G156 defines the canonical-summary-to-legacy mapping. |
| Tests | G157 fixes contract vectors; G155 fixes the old endpoint safety surface. |
| Production implementation | G158 implements the pure in-memory compatibility adapter. |
| Integration | The G158 adapter is not connected to an API route. |
| Activation | The old endpoint still uses its old diagnostics chain and is not migrated. |

G159 changes only the contract layer. Policy text, existing tests, production
code, integration state, and activation state remain unchanged.

## 2. Source authority

Source selection is owned only by trusted server-side configuration. The
activation route must obtain a fresh internal copy of that configuration and
pass it to `validate_demo_readonly_source_config` before selecting any source.

The default internal configuration is equivalent to:

```text
{}
```

The guard must interpret that default as:

```text
selected_source_mode = docs_fixture_only
request_override_allowed = false
read_only = true
demo_only = true
is_tradable = false
can_execute = false
is_trading_permission = false
is_execution_instruction = false
allowed_to_call_ea = false
allowed_to_modify_risk = false
```

No request-derived value may be merged into, overlaid onto, or used as a
fallback for the server-owned configuration.

## 3. Default `docs_fixture_only` boundary

### 3.1 Source

`docs_fixture_only` means that the source is an approved repository docs
fixture selected by fixed server code. It does not mean the current MT4 runtime
directory, a broker terminal directory, an environment-selected directory, or
any client-supplied location.

The existing `DemoReadOnlyDocsFixtureValidationSummary` is not a G151 canonical
summary. Its source scope, validation stage, component set, status vocabulary,
and safety envelope are different from the G151 20-key contract.

Therefore the existing docs summary must not be:

- relabeled as a G151 summary;
- padded with missing G151 keys;
- translated by ad hoc route code;
- passed directly to the G158 adapter;
- treated as evidence that the canonical reader or DataQualityGate passed.

### 3.2 Activation prerequisite

Before the old endpoint can be activated on the default source, a separately
tested server-owned seam must produce a genuine G151 20-key summary from an
approved canonical docs-fixture source. That seam must use the canonical
validation and DataQualityGate semantics; it must not copy or simulate their
conclusions.

Until that prerequisite exists and passes review, the old endpoint activation
is not approved. G159 does not authorize a partial migration that preserves the
old MT4 reader behind the default branch.

### 3.3 Output and compatibility semantics

After the prerequisite is implemented, a valid default-source result may enter
G158 only as a genuine, internally consistent G151 summary. G158 then emits the
exact 15-key `Mt4DiagnosticsResponse` defined by G156 and the existing schema.

Compatibility means:

- the endpoint path and HTTP method remain unchanged;
- the response top-level key set and field types remain unchanged;
- READY and READY_WITH_WARNINGS may permit read-only analysis only;
- BLOCKED, INPUT_INVALID, SAFE_FAILURE, unknown, or inconsistent input fails
  closed;
- unavailable legacy details remain explicitly unavailable and never claim
  successful legacy evidence;
- no new source, reader, canonical, trading, or execution fields are added.

Compatibility does not require preserving the independent old reader,
freshness chain, or DataQualityGate chain. Those duplicate chains must be
removed from the route when activation is eventually approved.

## 4. G151-to-G158 input boundary

The only successful input accepted by G158 is the exact G151 canonical summary
envelope. It contains exactly these 20 top-level keys:

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

G158 must continue to validate exact keys, strict types, fixed identity fields,
nested status consistency, warning allowlists, block-reason mapping, next-stage
semantics, and all safety flags. The route must not weaken or pre-sanitize an
invalid summary into an apparently valid one.

The route must not call G148, G149, or G151 individually. It may call only an
approved canonical orchestration boundary that owns that chain and returns the
sanitized G151 summary. The route then calls G158 exactly once.

## 5. SourceConfigGuard blocked behavior

If the source config result is missing, malformed, inconsistent, unsafe, or
blocked, the route must:

1. not call the canonical reader or canonical pipeline;
2. not call the old reader;
3. not construct a fake G151 summary;
4. enter G158 through its documented fail-closed invalid-input behavior;
5. return the fixed safe legacy blocked envelope.

The blocked envelope has exactly the legacy 15 top-level keys and these fixed
public semantics:

```text
stage = mt4_diagnostics_v1
status_code = BLOCKED_BY_GATE_V0
data_quality_passed = false
can_proceed_to_read_only_analysis = false
is_tradable = false
```

The fixed note must state that diagnostics are read-only, are not trading
permission, and do not generate trading signals.

Each unavailable legacy detail must use the fixed safe structure:

```text
available = false
status = unavailable
passed = false
```

`gate_v1_result` may additionally contain only the safe allowlisted
`warning_reasons` field. A guard-blocked or invalid-input result must use an
empty warning list. No guard status, path, exception text, internal source
status, or request value may appear in the response.

## 6. Server-side canonical reader activation

The canonical reader path is eligible only when the server-owned source config
explicitly contains an approved combination equivalent to:

```text
source_mode = mt4_demo_readonly_file_bridge_enabled
mt4_demo_readonly_file_bridge_enabled = true
allow_request_override = false
mt4_demo_readonly_bridge_dir = a server-owned approved directory
```

The SourceConfigGuard result must also be internally consistent and contain all
fixed safe values. A passed boolean alone is insufficient.

Only after those checks may an approved orchestration boundary call the G153
canonical pipeline. The pipeline owns G148 reader, G149 DataQualityGate, and
G151 summary adaptation. The old route must not import or call those lower
layers independently.

The resulting G151 summary is passed to G158. G158 determines whether the
legacy response is ready, warning-ready, or blocked. The route must not override
that result.

## 7. Request isolation

The following request surfaces must never select or alter the source:

- query parameters;
- headers;
- request body;
- cookies;
- frontend state;
- URL fragments or client-side storage;
- arbitrary request extensions.

Client values named `source_mode`, `bridge_dir`, `base_dir`, `candidate_path`,
`allowed_root`, freshness policy, filesystem policy, DataQualityGate policy, or
equivalent aliases must be ignored as source authority. They must not be copied
into server config or passed to the canonical pipeline.

The old endpoint remains a parameterless GET compatibility surface. It does not
gain source controls, upload controls, diagnostic policy controls, or any other
product capability.

## 8. Prohibited dependencies and data access

After activation, the old route must not call or retain:

- `build_mt4_diagnostics`;
- the old four-file MT4 snapshot reader;
- an independent freshness chain;
- an independent DataQualityGate chain;
- environment-variable source selection;
- configuration-file source selection;
- direct access to `data/` or another runtime directory;
- direct access to real MT4 or broker terminal files;
- a second canonical reader or parallel adapter.

G159 itself does not read any runtime file, connect to MT4, activate a reader,
or modify those dependencies.

## 9. Output safety and execution boundary

Every response state must preserve:

```text
is_tradable = false
```

The legacy response schema does not expose `can_execute`, trading permission,
execution instruction, EA authorization, or risk-override fields. Their absence
must not be interpreted as unknown or implicitly allowed; the server policy is
that all such capabilities remain false and unavailable.

Readiness means only that a sanitized diagnostics result may proceed to
read-only analysis. It is not:

- trading permission;
- order authorization;
- an execution instruction;
- DataQualityGate approval for execution;
- EA authorization;
- permission to change risk policy.

The response must not expose raw payloads, paths, filenames, checksum details,
timestamps used as validation evidence, exception text, internal source status,
credentials, account secrets, prices, balances, order data, signals, actions,
lot sizes, tickets, or EA commands.

## 10. Fail-closed activation matrix

| Condition | Canonical pipeline | G158 adapter | Legacy result |
| --- | --- | --- | --- |
| Default docs source lacks a genuine G151 producer | Not called | Not called for success | Activation blocked; existing route remains unchanged until prerequisites pass. |
| Guard missing, malformed, inconsistent, or blocked | Not called | Fail-closed path only | Fixed legacy blocked envelope. |
| Server reader config is not explicit and safe | Not called | Fail-closed path only | Fixed legacy blocked envelope. |
| Canonical orchestration raises unexpectedly | Safe failure only | Safe failure or invalid-input path | Fixed legacy blocked envelope with no exception text. |
| G151 summary is unknown, missing, extra, or contradictory | Already returned safely | Rejects input | Fixed legacy blocked envelope. |
| G151 summary is BLOCKED, INPUT_INVALID, or SAFE_FAILURE | Completed safely | Maps blocked state | Fixed legacy blocked envelope. |
| G151 summary is consistent READY | Completed safely | Maps success | Read-only legacy ready response. |
| G151 summary is consistent READY_WITH_WARNINGS | Completed safely | Maps allowlisted warnings | Read-only legacy warning-ready response. |

No blocked row may continue to another reader, Gate, adapter, analysis stage, or
execution stage.

## 11. Required staged delivery after G159

This contract does not authorize automatic progression. Future work must remain
separate:

1. **Tests-only activation contract.** Lock default-source behavior, guard
   blocking, request isolation, canonical delegation, exact legacy keys, and
   removal of old-reader calls.
2. **Missing source seam, if required.** Implement and review the genuine
   canonical docs-fixture summary producer. It must not relabel the existing
   docs summary.
3. **API activation implementation.** Modify the old route only after all
   prerequisites and tests are present.
4. **Safety hardening and review.** Recheck contaminated outputs, exceptions,
   source mismatches, exact keys, request injection, and fixed safety semantics.
5. **Fast-forward merge.** Requires a PASS review and explicit user approval.
6. **Release decision.** Tagging is a separate user-approved release task.

Every development, revision, review, merge, and release step requires its own
work order. No step may amend, force-push, auto-merge, or auto-tag.

## 12. Explicit non-goals for G159

G159 does not:

- modify either diagnostics endpoint;
- implement a canonical docs-fixture producer;
- implement API activation;
- change G151, G153, or G158;
- call or enable a reader;
- read MT4 files or the `data/` runtime directory;
- read environment variables or configuration files;
- add query, header, body, cookie, or frontend controls;
- add response fields or change schemas;
- implement Agent, LLM, RiskGate, PositionSizing, ExecutionGate, or EA logic;
- add automatic trading, Demo order execution, or live trading;
- grant trading permission or execution authority.

## 13. Acceptance checklist

G159 is complete only when review confirms that this document alone defines:

- the server-owned default `docs_fixture_only` source and compatibility intent;
- the prohibition on relabeling the existing docs summary as G151;
- the genuine G151 20-key input boundary for G158;
- the fixed legacy blocked result for unsafe source config;
- the only eligible server-side canonical reader activation path;
- rejection of request-controlled source selection;
- removal of old-reader and independent-Gate dependencies after activation;
- fixed read-only and non-tradable output semantics;
- fail-closed behavior for every unsafe or inconsistent state;
- the tests, implementation, review, explicit approval, fast-forward merge, and
  separate release sequence.

This document is architecture and safety policy only. It is not evidence that
the route migration, reader activation, MT4 integration, or any trading
capability exists.
