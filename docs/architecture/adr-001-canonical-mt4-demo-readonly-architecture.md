# ADR-001: Canonical MT4 Demo Readonly Architecture

Status: Accepted for staged migration planning

Date: 2026-07-10

Checkpoint reviewed: 782049b3e3924917ceb635de853347484694c60b

Scope: Architecture decision only. This ADR does not implement a reader, writer,
API change, frontend change, MT4 bridge, EA, agent, risk engine, position sizing,
execution gate, or trading workflow.

## Context

The project now has two MT4 diagnostics paths and multiple readonly snapshot
protocols:

- The older MT4 diagnostics path is exposed at `/api/mt4/diagnostics`.
- The newer demo-readonly diagnostics path is exposed at
  `/api/demo-readonly/diagnostics`.
- The older four-file protocol is documented under `mt4/file_formats/`.
- The newer demo-readonly reader protocol is documented under
  `docs/implementation_plans/`.
- A separate `DemoAccountReadOnlySnapshot` example exists as an aggregate
  contract for demo-only account state.
- The frontend currently has both the older MT4 diagnostics card path and the
  newer Demo Readonly Diagnostics Dashboard path.

This overlap was useful while building the safety layers incrementally, but it
now creates architectural ambiguity. The project needs one canonical MT4 Demo
readonly architecture before any real MT4 file bridge activation work continues.

## Verified Current-State Inventory

This inventory is based on the repository state at checkpoint
`782049b3e3924917ceb635de853347484694c60b`.

### Backend route registration

- `backend/app/main.py` registers both `mt4_router` and `demo_readonly_router`.
- This means both `/api/mt4/*` and `/api/demo-readonly/*` surfaces are active in
  the application.

### Old diagnostics chain: `/api/mt4/diagnostics`

- Route: `backend/app/api/mt4.py`
- Public endpoint: `GET /api/mt4/diagnostics`
- Data directory source: `backend/app/config.py` via `Settings.mt4_data_path`
- Default relative data directory: `data/mt4`
- Main service: `backend/app/services/mt4_diagnostics.py`
- Reader: `backend/app/services/mt4_snapshot_reader.py`
- Reader file set:
  - `live_tick.json`
  - `latest_bars.json`
  - `symbol_spec.json`
  - `account_snapshot.json`
- Validation/status layers:
  - `mt4_snapshot_status.py`
  - `mt4_snapshot_metadata.py`
  - `mt4_snapshot_freshness.py`
  - `mt4_required_fields.py`
  - `mt4_field_types.py`
  - `mt4_numeric_ranges.py`
  - `mt4_cross_field_checks.py`
  - `data_quality_gate.py`
- Response schema: `backend/app/schemas/mt4_diagnostics.py`
- Safety posture:
  - Response includes `is_tradable = false`.
  - Response note says diagnostics are not trading permission or trading
    signals.
- Important current behavior:
  - This route reads from configured local files when called.
  - It is not protected by the newer demo-readonly source config guard.

### New diagnostics chain: `/api/demo-readonly/diagnostics`

- Route: `backend/app/api/demo_readonly.py`
- Public endpoint: `GET /api/demo-readonly/diagnostics`
- Default server-side source config: an internal empty config equivalent to `{}`
- Source config guard:
  - `backend/app/services/mt4_demo_readonly_source_config_guard.py`
- Default source mode:
  - `docs_fixture_only`
- Conditional reader:
  - `backend/app/services/mt4_demo_readonly_reader.py`
- Reader file set when explicitly enabled by server-side config only:
  - `account_snapshot.json`
  - `positions_order_history.json`
  - `market_symbol.json`
- Schema validator:
  - `backend/app/services/mt4_demo_readonly_schema_validator.py`
- Source summary adapter:
  - `backend/app/services/mt4_demo_readonly_source_summary_adapter.py`
- Response schema and sanitizer:
  - `backend/app/schemas/demo_readonly_diagnostics.py`
- Safety posture:
  - Default reader status is `not_called`.
  - Request query/header/body cannot select source mode.
  - Reader activation requires explicit server-side config.
  - Unsafe source config is blocked.
  - Reader exceptions are converted to safe diagnostics summaries.
  - Forbidden output fields are filtered from the response.
  - Safety flags remain demo-only, readonly, non-tradable, and non-executable.

### Explanation chain

- Route: `backend/app/api/demo_readonly.py`
- Public endpoint: `GET /api/demo-readonly/explanation`
- Current state:
  - It is related to demo-readonly explanation output.
  - It is not the canonical MT4 diagnostics reader activation path.
  - It is not the focus of this ADR.

### Frontend diagnostics surfaces

Older surface:

- API client: `frontend/src/api/mt4Diagnostics.ts`
- Endpoint called: `/api/mt4/diagnostics`
- Component: `frontend/src/components/Mt4DiagnosticsStatusCard.tsx`
- App integration: `frontend/src/App.tsx`

Newer surface:

- Endpoint contract: `frontend/src/features/demoDiagnostics/contracts.ts`
- API client: `frontend/src/features/demoDiagnostics/api.ts`
- Endpoint called: `/api/demo-readonly/diagnostics`
- Dashboard:
  - `frontend/src/features/demoDiagnostics/components/DemoReadOnlyDiagnosticsDashboard.tsx`
- Source readiness mapper:
  - `frontend/src/features/demoDiagnostics/sourceReadinessMapper.ts`
- Source readiness component:
  - `frontend/src/features/demoDiagnostics/SourceReadinessCard.tsx`

Current frontend conclusion:

- The app has two diagnostics UI paths.
- The newer Demo Readonly Diagnostics Dashboard is the better canonical
  destination.
- Useful status hierarchy from the older `Mt4DiagnosticsStatusCard` should be
  migrated or adapted into the canonical dashboard instead of keeping two
  long-term refresh paths.

### Documented snapshot protocols

Older four-file MT4 file bridge protocol:

- Directory: `mt4/file_formats/`
- Files:
  - `live_tick.json`
  - `latest_bars.json`
  - `symbol_spec.json`
  - `account_snapshot.json`
- Intended path: `data/mt4/`
- Strengths:
  - Good market/account separation.
  - Metadata, freshness, required fields, type checks, range checks, cross-field
    checks, and DataQualityGate work already exist around this structure.
- Gap:
  - It does not include a canonical bundle manifest.
  - It is not guarded by the newer source config guard at the old endpoint.

Newer three-file demo-readonly protocol:

- Directory: `docs/implementation_plans/`
- Files:
  - `account_snapshot.json`
  - `positions_order_history.json`
  - `market_symbol.json`
- Strengths:
  - Strong demo-only and readonly safety language.
  - Source config guard integration.
  - Reader default closed.
  - Response sanitization and forbidden-field filtering.
- Gap:
  - It does not reuse the old four-file market/freshness/DataQualityGate stack
    as the canonical bundle validation chain.

Aggregate DemoAccountReadOnlySnapshot protocol:

- Example:
  - `docs/implementation_plans/demo_account_readonly_snapshot.example.json`
- Schema documentation:
  - `docs/implementation_plans/demo_account_readonly_snapshot_schema.md`
- Strengths:
  - Good demo account contract for readonly account and symbol state.
  - Useful validation precedent for demo-only safety flags.
- Gap:
  - It is an aggregate example and should not become the sole canonical live
    MT4 bridge bundle without a manifest and multi-file consistency design.

## Problem Statement

The current architecture has drift across five dimensions:

1. Two public diagnostics endpoints have overlapping purposes.
2. Two reader families use different file sets.
3. Multiple snapshot protocols define overlapping account, market, and safety
   concepts.
4. Frontend diagnostics has two display paths and two refresh sources.
5. The strongest safety features are split across old and new chains.

If this is not resolved before real MT4 bridge activation, the project risks:

- validating one snapshot protocol while reading another;
- showing one frontend status while backend readiness means another;
- allowing tests to prove only a subset of the intended safety boundary;
- duplicating reader logic;
- making future writer or EA contracts unclear;
- expanding a compatibility path into the accidental production architecture.

## Decision

The canonical public diagnostics endpoint will be:

```text
GET /api/demo-readonly/diagnostics
```

The old endpoint:

```text
GET /api/mt4/diagnostics
```

is deprecated for new development. It may remain temporarily as a compatibility
surface, but it must not receive new product features. During the compatibility
migration phase, it must become a thin compatibility adapter that calls the same
canonical internal diagnostics service as `/api/demo-readonly/diagnostics`. It
must not continue to maintain an independent reader, freshness chain,
DataQualityGate chain, or product capability. It must not be removed immediately;
frontend users and other callers should migrate first, and compatibility tests
must pass. Whether the old endpoint is ultimately removed should be decided by a
separate ADR after compatibility migration is complete.

The canonical internal MT4 Demo readonly diagnostics architecture will converge
on one service chain:

```text
Server-side Config
-> SourceConfigGuard
-> Canonical Bundle Reader
-> Bundle Consistency Validation
-> Metadata Validation
-> Freshness Check
-> Required Fields Check
-> Field Types Check
-> Numeric Ranges Check
-> Cross-field Checks
-> DataQualityGate
-> Safe Diagnostics Response
-> Demo Readonly Diagnostics Dashboard
```

Source mode authority is server-side only. Query parameters, headers, request
bodies, cookies, and browser state must not select source mode, bridge directory,
base directory, or candidate file paths.

### Canonical Configuration Authority

Canonical source configuration authority is server-side only.

Long-term implementation should use typed server-side settings or an explicit
dependency/config object. That configuration should be loaded at application
startup or through a deliberate internal dependency boundary.

The following inputs must not enter the canonical source configuration object:

- request query parameters;
- request headers;
- request body;
- request cookies;
- request form fields;
- request path parameters;
- frontend state.

The current module-level mutable dictionary used by the demo-readonly route is
only a transitional implementation detail. It is not the canonical long-term
configuration authority. This ADR decides the direction; it does not modify
configuration code and does not claim typed settings have already been
implemented for this path.

The canonical first bundle will use a manifest plus the established four core
files:

```text
snapshot_manifest.json
live_tick.json
latest_bars.json
symbol_spec.json
account_snapshot.json
```

`positions_order_history.json` is an optional later extension for review and
training analysis, not a required first activation file.

The canonical frontend will be the Demo Readonly Diagnostics Dashboard. The
`SourceReadinessCard` remains the source/readiness summary. Useful layer status
presentation from `Mt4DiagnosticsStatusCard` should be migrated into the
dashboard rather than preserving two independent diagnostics panels forever.

## Canonical Target Data Flow

```text
MT4 Demo readonly writer
-> writes temporary files
-> atomically publishes canonical bundle files
-> snapshot_manifest.json declares bundle identity and commit state
-> backend receives GET /api/demo-readonly/diagnostics
-> backend loads server-side source config
-> SourceConfigGuard rejects unsafe or non-server-selected reader activation
-> Canonical Bundle Reader reads only the configured bundle directory
-> Bundle Consistency Validation checks manifest/file cohesion
-> Metadata Validation checks source, file type, and schema version
-> Freshness Check blocks stale data from readonly analysis
-> Required Fields Check verifies required keys
-> Field Types Check verifies expected primitive/container types
-> Numeric Ranges Check blocks impossible or unsafe values
-> Cross-field Checks verify bid/ask/spread/account relations
-> DataQualityGate decides whether readonly analysis may proceed
-> Safe Diagnostics Response strips raw payload and sensitive details
-> Dashboard displays readonly status only
```

No step in this chain grants trading permission. Passing diagnostics may only
mean the data is acceptable for readonly analysis. It does not authorize orders,
position sizing, execution, EA calls, or trading advice.

## Canonical Bundle Boundary

The canonical bundle boundary is the smallest set of files required to evaluate
data readiness for MT4 Demo readonly analysis.

Required first-version files:

- `snapshot_manifest.json`
- `live_tick.json`
- `latest_bars.json`
- `symbol_spec.json`
- `account_snapshot.json`

Optional later extension:

- `positions_order_history.json`

The manifest is the bundle coordinator. It should eventually define:

- `schema_version`
- `bundle_id`
- `sequence`
- `generated_at_utc`
- `source_id`
- `writer_version`
- `terminal_id_masked`
- `account_mode`
- demo/live marker
- writer heartbeat
- commit state
- required files
- optional files
- payload compatibility range
- file identity or checksum fields

This ADR intentionally does not define the final field-level manifest schema.
That belongs in a later work order.

## Compatibility and Migration Matrix

| Current asset | Current role | Decision | Migration target |
| --- | --- | --- | --- |
| `/api/demo-readonly/diagnostics` | New guarded diagnostics endpoint | Canonical | Keep and extend carefully |
| `/api/mt4/diagnostics` | Older four-file diagnostics endpoint | Deprecated compatibility | Later adapter or removal decision |
| `mt4_snapshot_reader.py` | Four-file reader | Reuse concepts | Adapt into canonical bundle reader |
| `mt4_snapshot_metadata.py` | Metadata validation | Reuse | Canonical metadata validation |
| `mt4_snapshot_freshness.py` | Freshness validation | Reuse | Canonical freshness validation |
| `mt4_required_fields.py` | Required field checks | Reuse | Canonical bundle validation |
| `mt4_field_types.py` | Type checks | Reuse | Canonical bundle validation |
| `mt4_numeric_ranges.py` | Range checks | Reuse | Canonical bundle validation |
| `mt4_cross_field_checks.py` | Cross-field checks | Reuse | Canonical bundle validation |
| `data_quality_gate.py` | Readonly analysis gate | Reuse | Final readonly analysis gate |
| `mt4_demo_readonly_source_config_guard.py` | Server-side source guard | Reuse | Canonical source mode authority |
| `mt4_demo_readonly_reader.py` | Guarded demo reader | Reuse safety patterns | Refactor toward canonical bundle reader |
| `mt4_demo_readonly_schema_validator.py` | Demo-only schema safety | Reuse safety patterns | Fold into canonical bundle validation |
| `demo_readonly_diagnostics.py` | Safe response schema/sanitizer | Reuse | Canonical response boundary |
| `DemoReadOnlyDiagnosticsDashboard` | New dashboard | Canonical | Main diagnostics UI |
| `SourceReadinessCard` | Source/readiness summary | Canonical | Keep |
| `Mt4DiagnosticsStatusCard` | Older diagnostics UI | Migrate useful parts | Do not keep as separate long-term path |
| Four-file MT4 protocol | Market/account file split | Reuse as core payload | Add manifest and consistency checks |
| Three-file demo protocol | Demo reader safety contract | Reuse guard ideas | Not the final canonical bundle alone |
| DemoAccountReadOnlySnapshot | Aggregate demo account example | Reuse safety constraints | Not the sole canonical live bundle |

## Endpoint Migration Plan

Phase 1: Freeze old endpoint scope

- No new product features should be added to `/api/mt4/diagnostics`.
- The old endpoint may remain available to avoid abrupt breakage.
- Tests should document that the old endpoint is compatibility-only.

Phase 2: Build canonical service behind demo-readonly endpoint

- Add canonical bundle reader behind server-side source config guard.
- Preserve default `docs_fixture_only` behavior until explicit server config
  enables the reader.
- Reuse old validation layers and new guard/sanitizer layers.

Phase 3: Adapt old endpoint

- `/api/mt4/diagnostics` must become a thin compatibility adapter to the
  canonical internal diagnostics service.
- It must not keep an independent reader.
- It must not keep an independent freshness or DataQualityGate business chain.
- It must not receive new product capabilities.
- It must remain available until frontend and caller migration is complete and
  compatibility tests pass.
- Final removal, if any, is a separate post-migration ADR. That later ADR decides
  endpoint removal only; this ADR already decides the migration mechanism.

Phase 4: Remove duplicated frontend dependency

- Frontend should rely on `/api/demo-readonly/diagnostics` as the source of
  truth.
- Any old status hierarchy still needed should appear inside the canonical
  dashboard.

## Frontend Migration Plan

The canonical frontend destination is:

```text
DemoReadOnlyDiagnosticsDashboard
```

The dashboard should own:

- source readiness;
- bundle status;
- component status;
- readonly readiness notes;
- safe explanation display when available;
- all diagnostics refresh behavior.

The older `Mt4DiagnosticsStatusCard` should not remain a separate long-term
diagnostics surface. Its useful display ideas can be adapted into the dashboard:

- read summary;
- metadata status;
- freshness status;
- required fields;
- field types;
- numeric ranges;
- cross-field checks;
- DataQualityGate status.

Long-term frontend constraints:

- one diagnostics refresh path;
- no `source_mode` selector;
- no bridge directory input;
- no base directory input;
- no candidate path input;
- no raw payload display;
- no trading buttons;
- no execution controls;
- no trading permission language.

## Safety Invariants

These invariants are mandatory for the canonical architecture:

1. Default mode is docs fixture only.
2. Reader activation is server-side only.
3. Request query, headers, body, cookies, form fields, path parameters, and
   frontend state cannot enable the reader.
4. The reader is never enabled by default.
5. Bridge directory is never client supplied.
6. Raw MT4 payload is never returned to the frontend.
7. System paths, candidate paths, tracebacks, passwords, tokens, and credentials
   are never returned to the frontend.
8. `read_only` remains true.
9. `demo_only` remains true for this stage.
10. `is_tradable` remains false.
11. `can_execute` remains false.
12. Diagnostics readiness is not trading permission.
13. DataQualityGate approval is not trading permission.
14. Stale data blocks readonly analysis readiness.
15. Any unsafe source config blocks reader activation.
16. Any gate rejection must stop the current chain from proceeding to a stronger
    claim.
17. No diagnostics endpoint may generate buy, sell, lot, order, execution, or
    position instructions.
18. No frontend diagnostics surface may present trading advice.
19. No EA call is allowed in the readonly diagnostics chain.
20. No live account connection belongs in the current stage.

## Consequences

Positive consequences:

- There is one canonical public diagnostics endpoint for future work.
- The stronger server-side source guard becomes the entry point for reader
  activation.
- The stronger old validation layers are preserved instead of discarded.
- The frontend gets one clear diagnostics dashboard direction.
- Future MT4 writer work can target one bundle boundary.
- Test scope can become easier to explain and audit.

Costs and tradeoffs:

- Some existing code will become compatibility code.
- The old four-file reader and new demo reader will need refactoring before real
  bridge activation.
- Additional contract tests are needed to prevent endpoint drift.
- The canonical manifest schema must be designed before writer implementation.
- Frontend cleanup will need staged work to avoid breaking current display.

## Alternatives Considered

### Alternative A: Keep `/api/mt4/diagnostics` as canonical

Rejected. It already reads configured local files by default and lacks the newer
server-side source config guard, default-closed reader model, and response
sanitization boundary.

### Alternative B: Keep `/api/demo-readonly/diagnostics` but use the current
three-file demo reader protocol as-is

Rejected. It keeps the newer safety guard but does not fully reuse the mature
four-file market/account validation, freshness, and DataQualityGate chain.

### Alternative C: Collapse everything into one aggregate
`DemoAccountReadOnlySnapshot`

Rejected. The aggregate example is useful for demo account validation, but it is
not enough for a canonical MT4 writer-to-reader bundle with explicit multi-file
commit, freshness, and consistency semantics.

### Alternative D: Maintain both endpoints and both frontends indefinitely

Rejected. This preserves ambiguity and makes test evidence harder to interpret.

### Alternative E: Canonical guarded endpoint plus manifest-based four-core-file
bundle

Accepted. This keeps the safer public endpoint and source guard while reusing
the strongest validation layers from the older chain.

## Phased Migration Plan

| Phase | Goal | Output | Go/no-go condition |
| --- | --- | --- | --- |
| G143 | Record canonical architecture | This ADR | Docs-only decision merged |
| G144 | Define canonical manifest and bundle contract | Field-level protocol docs and tests | No writer implementation |
| G145 | Add backend contract tests for canonical bundle boundary | Tests only or docs plus tests | No reader activation by default |
| G146 | Refactor service seams for canonical bundle reader | Internal service structure | Existing endpoints unchanged |
| G147 | Adapt source config guard to canonical bundle reader | Guarded server-only reader selection | Query/header/body still blocked |
| G148 | Integrate validation layers into canonical chain | Metadata, freshness, required, type, range, cross-field, DataQualityGate | No trading permission semantics |
| G149 | Add compatibility adapter plan for old endpoint | Thin adapter or deprecation tests | No feature expansion on old endpoint |
| G150 | Migrate frontend status hierarchy | Dashboard becomes single diagnostics surface | No trading UI controls |
| Later | MT4 Demo writer planning | Writer contract only | No EA execution until explicit stage |

Phase numbers are planning labels, not commitments to exact work-order IDs.

Migration questions outside G144 are assigned as follows:

- Validation module wiring belongs to the canonical service/reader implementation
  phase, especially the service seam and validation integration work.
- Golden canonical fixtures belong to the canonical fixtures and contract tests
  phase.
- Old endpoint compatibility tests belong to the endpoint migration phase.

## Open Questions for G144

1. What exact manifest field names and types are required in
   `snapshot_manifest.json`?
2. Should the manifest include checksums for every payload file in the first
   version?
3. What is the canonical `commit_state` vocabulary?
4. How should bundle sequence gaps be handled?
5. What is the maximum acceptable writer heartbeat age?
6. Should `latest_bars.json` include all timeframes in one file or one file per
   timeframe?
7. Should `positions_order_history.json` be optional in the first bridge
   activation or deferred entirely?
8. What file size limits should apply to each payload?
9. What schema version compatibility range should the backend accept?
10. How should Windows atomic replace behavior be documented for MT4 writers?
11. Should `terminal_id_masked` be required or optional?
12. What exact fields from `account_snapshot.json` are required for readonly
    diagnostics before any future risk engine exists?

## Explicit Non-Goals

This ADR does not implement:

- MT4 reader activation;
- MT4 writer;
- MQL4 code;
- EA code;
- API route changes;
- frontend UI changes;
- frontend API changes;
- Dashboard integration changes;
- source mode controls;
- bridge directory controls;
- DataQualityGate migration code;
- RiskGate;
- PositionSizing;
- ExecutionGate;
- TradePlanSchema;
- Agent or LLM execution;
- prompt executor;
- user confirmation API;
- EA command bridge;
- demo order execution;
- live order execution;
- audit log writer;
- replay/training system;
- automatic trading;
- live trading.

This ADR also does not grant permission to read real MT4 files, connect to MT4,
connect to a demo account, connect to a live account, or produce trading advice.
