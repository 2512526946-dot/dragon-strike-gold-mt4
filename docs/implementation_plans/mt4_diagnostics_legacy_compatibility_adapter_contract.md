# Legacy MT4 Diagnostics Compatibility Adapter Contract

Status: G156 contract-only design. This document defines a future compatibility
adapter; it does not implement or activate the adapter.

## 1. Scope

The deprecated `GET /api/mt4/diagnostics` endpoint has an existing response
contract and existing callers. The future adapter will translate the safe
canonical Demo Readonly diagnostics summary into that legacy response shape
without creating a second diagnostics pipeline.

The canonical source is the already-defined in-memory chain:

```text
G148 isolated filesystem reader
    -> G149 canonical DataQualityGate
    -> G151 canonical diagnostics summary adapter
```

The adapter may consume only the sanitized G151 summary. It must not consume
raw payloads, reader internals, filesystem paths, checksum details, exception
text, request values, or an alternate copy of any Gate.

This is a compatibility surface, not a new readiness or execution authority.
The legacy endpoint remains read-only and must not become a source selector or
an execution interface.

## 2. Legacy response contract

The adapter must emit exactly these top-level keys, matching the current
`Mt4DiagnosticsResponse` contract. No additional keys are permitted:

```text
stage
status_code
data_quality_passed
can_proceed_to_read_only_analysis
is_tradable
note
read_summary
metadata_status
freshness_status
gate_v0_result
required_fields_status
field_types_status
numeric_ranges_status
cross_field_status
gate_v1_result
```

The adapter must preserve the legacy field types and nested shapes required by
the existing response schema. Where canonical Bundle v1 intentionally does not
publish a legacy detail, the adapter must use the existing safe unavailable or
summary-only representation. It must never invent a successful legacy detail
from missing information.

## 3. Canonical status mapping

The mapping is deterministic and accepts only the canonical status vocabulary
and internally consistent combinations defined by G149 and G151.

| Canonical summary status | Legacy data quality | Legacy readonly-analysis readiness | Mapping rule |
| --- | --- | --- | --- |
| `READY` | `true` | `true` | Preserve the successful, sanitized summary and map only to the existing legacy status vocabulary. |
| `READY_WITH_WARNINGS` | `true` | `true` | Preserve only the allowlisted safe warning meaning; do not turn warnings into permission or execution state. |
| `BLOCKED` | `false` | `false` | Return a deterministic legacy blocked result and safe unavailable detail structures. |
| `INPUT_INVALID` | `false` | `false` | Return a deterministic invalid-input result without exposing validation internals. |
| `SAFE_FAILURE` | `false` | `false` | Return a deterministic safe-failure result with sanitized, non-diagnostic detail. |

The adapter must verify the canonical `passed`, status, warning, block-reason,
readiness, and next-stage fields before mapping them. Unknown statuses,
missing fields, extra fields, or contradictory combinations must fail closed as
a legacy blocked or invalid result using the existing public legacy status
vocabulary. They must never be treated as successful or warning-successful
results.

The adapter must not introduce a new execution status code merely to represent
the canonical status. Reuse the existing public legacy constants and semantics
when the production adapter is implemented and tested.

## 4. Field-level mapping

The following rules define the future mapping from the sanitized canonical
summary to the exact legacy response:

| Legacy field | Canonical source or fixed value | Required behavior |
| --- | --- | --- |
| `stage` | Existing legacy stage identifier | Preserve compatibility wording; do not claim a new execution or trading stage. |
| `status_code` | Deterministic mapping from the five accepted canonical statuses | Use only existing legacy status vocabulary; unknown or inconsistent input fails closed. |
| `data_quality_passed` | Canonical `passed`, after status consistency validation | `true` only for consistent `READY` or `READY_WITH_WARNINGS`; otherwise `false`. |
| `can_proceed_to_read_only_analysis` | Canonical readonly readiness, after status consistency validation | `true` only for consistent `READY` or `READY_WITH_WARNINGS`; this is not trading permission. |
| `is_tradable` | Fixed constant | Always `false`. The adapter cannot derive or propagate a tradable value. |
| `note` | Fixed safe note | State that this is read-only diagnostics, not trading permission, and does not generate trading signals. |
| `read_summary` | Safe canonical summary projection or existing unavailable shape | Do not expose raw bundle content or filesystem details. |
| `metadata_status` | Safe summary-only projection or unavailable shape | Do not expose source paths, timestamps, or internal metadata evidence. |
| `freshness_status` | Safe summary-only projection or unavailable shape | Do not expose raw timestamps, age calculations, or exception text. |
| `gate_v0_result` | Existing compatibility-safe projection | Do not duplicate or re-run a Gate; do not claim legacy Gate evidence not present in the canonical summary. |
| `required_fields_status` | Existing compatibility-safe projection or unavailable shape | Never fabricate a successful required-field result. |
| `field_types_status` | Existing compatibility-safe projection or unavailable shape | Never expose raw payload or validation internals. |
| `numeric_ranges_status` | Existing compatibility-safe projection or unavailable shape | Never expose prices, balances, checksums, or raw numeric evidence. |
| `cross_field_status` | Existing compatibility-safe projection or unavailable shape | Never fabricate a successful cross-field result. |
| `gate_v1_result` | Existing compatibility-safe projection | Do not copy internal canonical source status or present readiness as permission. |

The exact nested representations for unavailable legacy details must be fixed
by the later tests-only contract and pure adapter stages. In all cases, the
output must remain schema-valid, deterministic, and fail closed.

## 5. Safety and information filtering

The legacy response must contain no raw or sensitive material. The adapter
must reject or remove, rather than pass through, all of the following:

- raw payloads and arbitrary unknown keys;
- `bridge_dir`, `base_dir`, `candidate_path`, system paths, or filenames;
- traceback, exception messages, stack details, or validation internals;
- checksum values, checksum internals, manifest internals, or file-generation details;
- credentials, tokens, passwords, account secrets, or login material;
- order, lot, signal, action, ticket, EA, or execution fields;
- `can_trade`, `allow_trade`, `should_buy`, `should_sell`, `suggested_lot`,
  `OrderSend`, `OrderClose`, `OrderModify`, and `OrderDelete` values or text.

The output key set must remain exactly the legacy key set in section 2. A
value that is safe in the canonical internal summary is not automatically safe
for the legacy response; every field must pass the legacy schema and this
allowlist.

The following safety values are fixed and non-overridable:

```text
is_tradable = false
```

The legacy response does not gain `can_execute`, an EA authorization flag, a
trade permission flag, or any other execution capability. Readiness only means
that the sanitized diagnostics summary permits read-only analysis. It never
means trading permission, order authorization, or Gate approval for execution.

## 6. Source and request boundary

The old endpoint must not allow a client to select or alter the diagnostics
source. Query parameters, headers, body fields, cookies, and frontend state
must not control `source_mode`, `bridge_dir`, `base_dir`, `candidate_path`, or
any equivalent source setting.

Any future source selection must come only from the server-side source
configuration guard. The compatibility adapter itself is pure in-memory
mapping and must not read environment variables, configuration files, the
`data/` runtime directory, or MT4 files.

The legacy route must not call the old reader, a second reader, or the
canonical reader directly once migration begins. The route-level integration
will provide a sanitized canonical summary to the adapter. The adapter must
not call the API router, a reader, the canonical pipeline, a Gate, or any
filesystem operation.

## 7. Fail-closed behavior

The future implementation must fail closed for all of these cases:

1. canonical status is unknown;
2. required canonical keys are missing or extra keys are present;
3. canonical status does not agree with `passed`, warnings, block reasons,
   readiness, or next stages;
4. a source scope or validation stage is not the expected canonical scope;
5. an internal source status, raw path, checksum, exception, or payload is
   present in the proposed legacy projection;
6. the adapter receives an unexpected exception or invalid object.

Fail closed means the exact legacy response shape is returned with
`data_quality_passed=false`,
`can_proceed_to_read_only_analysis=false`, `is_tradable=false`, a
deterministic safe status, and sanitized unavailable details. Exception text,
paths, raw values, and internal statuses must not appear in the response.

## 8. Staged delivery order

This contract intentionally separates policy, contract, tests, production
implementation, integration, and activation:

1. **G156, this document: contract.** Define the exact legacy mapping and
   safety boundary only.
2. **Next: tests-only contract.** Add behavior tests for every accepted status,
   contradictory status, unknown status, exact keys, fixed safety flags,
   filtering, and client-source injection resistance. Tests must use controlled
   in-memory inputs and must not read real MT4 or runtime data.
3. **After tests pass: pure adapter production boundary.** Implement one
   in-memory adapter that consumes the sanitized G151 summary, reuses existing
   public constants, preserves the legacy schema, and has no reader/API/
   filesystem/environment dependency.
4. **After adapter review: API activation.** Separately migrate the old route to
   the canonical source behind the server-side source guard. This stage must
   preserve default and legacy compatibility behavior and requires its own
   tests and review.
5. **After activation evidence: separate review, merge, and release work.**

No stage may be skipped, combined, or auto-advanced. User approval is required
before development, merge, or release actions.

## 9. Explicit non-goals for G156

This contract does not implement or activate any of the following:

- the compatibility adapter;
- tests, production code, route changes, or schema changes;
- the canonical diagnostics pipeline or any Gate;
- the G148 reader or filesystem access;
- MT4, Demo accounts, real accounts, or real market data;
- query/header/body/cookie source controls;
- agents, LLMs, trade plans, risk or position sizing;
- order execution, EA commands, automatic trading, or trading permission.

## 10. Acceptance checklist

G156 is complete only when this document is the sole changed file and a later
review confirms that it defines:

- the exact legacy top-level keys and field-level mapping;
- deterministic READY, READY_WITH_WARNINGS, BLOCKED, INPUT_INVALID, and
  SAFE_FAILURE behavior;
- fail-closed handling for unknown or contradictory canonical states;
- fixed `is_tradable=false` and the distinction between readiness and trading
  permission;
- filtering for raw payload, path, checksum, exception, source status, and
  execution-related content;
- server-side-only source configuration and client-parameter rejection;
- the tests-only, pure-adapter, and API-activation sequence;
- explicit boundaries excluding reader access, real MT4, and trading.
