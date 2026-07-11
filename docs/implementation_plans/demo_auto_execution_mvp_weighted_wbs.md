# Demo Auto-Execution MVP Weighted WBS

Status: WF-4A planning baseline. This document establishes an engineering-hour
weighted work breakdown structure for the Dragon Strike Demo auto-execution
MVP and the separately frozen Live auto-execution goal. It does not implement,
integrate, activate, or authorize any capability.

Baseline commit at estimation time:

```text
0cc09964c62a0e1eb445b57a1f282530970d582e
```

The commit is evidence for this estimate, not a permanent runtime checkpoint.
Future WBS updates must inspect the then-current repository state and must not
assume that this commit is still current.

## 1. Authority and safety boundary

This WBS preserves the repository policy:

- the current system is Demo-only and Read-only;
- the Agent or LLM has advice authority only;
- program Gates have veto authority;
- an EA may execute only a separately authorized Demo order in a future phase;
- automatic Demo training and execution remain disabled by default;
- no current capability grants trading or execution permission;
- Live trading is outside the current development authorization;
- no-stop, martingale, grid, and overnight trading remain prohibited;
- any failed Gate stops the chain.

An implemented capability is not necessarily integrated. An integrated
capability is not necessarily activated. An activated capability is not
necessarily verified. Readiness for sanitized read-only analysis is never
trading permission.

## 2. Capability maturity vocabulary

Every work package uses exactly one maturity value:

| Maturity | Meaning |
| --- | --- |
| `NOT_STARTED` | No approved policy, contract, tests, or production implementation establishes the capability. |
| `POLICY_ONLY` | Intent or safety policy exists, but no complete executable contract exists. |
| `CONTRACT_ONLY` | An approved architecture or interface contract exists; production capability is not implemented. |
| `TESTS_ONLY` | Contract tests or vectors exist, but production capability is not implemented. |
| `IMPLEMENTED` | Production code exists in isolation but is not connected to its intended runtime boundary. |
| `INTEGRATED` | Production components are connected, but operational activation or evidence is incomplete. |
| `ACTIVATED` | The capability is enabled in its approved environment but lacks the required observation evidence. |
| `VERIFIED` | The capability has passed its required automated, integration, and where applicable calendar-based evidence. |

Maturity is evidence-based. A filename, document, test, commit message, tag, or
UI label alone cannot raise a package to `IMPLEMENTED`, `INTEGRATED`,
`ACTIVATED`, or `VERIFIED`.

## 3. Two separate project endpoints

### 3.1 Demo Auto-Execution MVP

The Demo MVP denominator covers W0 through W20. Its first version is limited
to:

- TradeMax Global MT4 Demo;
- canonical instrument XAUUSD and a separately confirmed broker-symbol mapping
  such as GOLD;
- one Canonical Bundle data chain;
- one deterministic, explainable analysis path;
- one RiskGate and one PositionSizing implementation;
- one immutable TradePlan representation;
- Shadow Mode before execution;
- one ExecutionGate;
- one EA Demo channel;
- idempotency, duplicate prevention, kill switch, and no-overnight enforcement;
- execution acknowledgements, rejection feedback, restart recovery, audit, and
  replay;
- a separately reviewed and approved Demo GoLiveGate.

The Demo MVP explicitly defers multiple instruments, brokers, accounts, and
strategy portfolios; machine-learning trading decisions; LLM-controlled final
lot sizing or order decisions; automatic parameter optimization; complex
portfolio management; real funds; nonessential advanced UI; mobile clients;
and distributed cloud execution.

### 3.2 Live Auto-Execution

The Live denominator covers W0 through W21 and is a planning estimate only.
W21 is frozen and has no current implementation or activation authorization.

The following implications are prohibited:

```text
execution code implemented != execution activated
Shadow Mode completed != Demo execution permitted
Demo execution completed != Live execution permitted
GoLiveGate designed != GoLiveGate passed
engineering progress != activation readiness
```

Live requires long-duration Demo evidence, an independent Live GoLiveGate,
operational and security review, and a new explicit user authorization. Current
automatic-order prohibitions in `AGENTS.md` remain unchanged.

## 4. Estimation method

### 4.1 Unit

All hours are equivalent experienced-engineer hours, including design, code,
tests, review fixes, integration, and required operational evidence work. They
are ranges, not time-sheet records and not elapsed calendar promises.

### 4.2 Progress formula

For a work package:

```text
package progress =
  (estimated total engineering hours - estimated remaining engineering hours)
  / estimated total engineering hours
```

For an endpoint:

```text
endpoint progress =
  sum(estimated invested engineering hours for included packages)
  / sum(estimated total engineering hours for included packages)
```

The central estimate uses the midpoint of each hour range. The lower and upper
bounds combine the conservative range endpoints. These bounds express
estimation uncertainty; they are not confidence intervals from measured time
series data.

Progress must never be calculated from:

- G or WF work-order numbers;
- commit counts;
- test counts;
- file counts or lines of code;
- tag or version numbers;
- document counts;
- branch counts.

Those quantities may be supporting evidence, but they are not measures of
remaining engineering work.

## 5. Weighted work breakdown structure

In the table, `Invested / Remaining` is an engineering-hour range. `Tasks`
means the estimated number of remaining minimal work orders, including separate
contract, tests, implementation, hardening, integration, activation, review,
and evidence stages where applicable.

Critical-path values are:

- `ENABLER`: required engineering governance;
- `BASELINE`: completed foundation that must remain stable;
- `CRITICAL`: currently expected to control the Demo MVP finish date;
- `PARALLEL_CRITICAL`: may proceed in parallel but must converge before Demo
  activation;
- `SUPPORTING`: required but not currently date-controlling;
- `EVIDENCE_GATE`: requires evidence in addition to code;
- `FROZEN`: outside current development authorization.

| ID | Name | MVP target and repository evidence | Maturity | Completed evidence | Remaining gap | Dependencies: before -> after | Risk | ModelGate | Critical path | Tasks | Invested / Remaining hours | Uncertainty | Calendar observation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| W0 | Repository governance, Skills, Supervisor, and CI | Repeatable scoped delivery. Skills and bounded Supervisor exist. | `IMPLEMENTED` | Development, review, merge, release, and Supervisor rules are present. | Weighted WBS maintenance, TaskSizeGate, test layers, one-click verification, CI, and engineering metrics. | none -> all packages | Medium | `PRO_REQUIRED` for workflow architecture | ENABLER | 6-9 | 35-55 / 30-50 | Medium | No |
| W1 | Canonical Bundle protocol and validation | One authoritative Bundle v1 contract and validation chain. | `VERIFIED` | Manifest/payload contract, structure, identity, value, freshness, filesystem isolation, and DataQualityGate regressions exist. | Protocol maintenance and later real-writer compatibility evidence. | W0 -> W2, W4, W5 | Medium | `PRO_REQUIRED` | BASELINE | 2-4 | 110-160 / 10-20 | Low | No |
| W2 | Diagnostics and legacy migration | Both diagnostics surfaces consume the canonical safe chain without duplicate readers. | `INTEGRATED` | Canonical Demo diagnostics pipeline is guarded and integrated; legacy mapping adapter exists. | Complete legacy endpoint migration, hardening, and compatibility verification. | W1, W3 -> W19 | High | `PRO_REQUIRED` | CRITICAL | 3-5 | 100-150 / 20-35 | Medium | No |
| W3 | Canonical docs fixture producer | Deterministic checked-in default source for canonical diagnostics. | `VERIFIED` | Canonical assets, zero-argument producer, strict envelope validation, and fail-closed tests exist. | Connect the approved producer only through the separately reviewed diagnostics migration boundary. | W1 -> W2, W5 | Medium | `PRO_REQUIRED` | CRITICAL | 1-2 | 35-55 / 5-10 | Low | No |
| W4 | TradeMax MT4 Demo Writer and real Bundle bridge | MT4 Demo publishes atomic canonical bundles through one approved bridge. | `CONTRACT_ONLY` | Read-only bridge and Bundle writer requirements are documented. | MQL4 writer, manifest-last atomic publish, symbol mapping, sandbox integration, and real Demo evidence. | W1 -> W6, W14, W20 | High | `PRO_REQUIRED` | PARALLEL_CRITICAL | 8-12 | 15-25 / 80-140 | High | Yes, estimated 2-4 weeks of broker-terminal observation |
| W5 | ReplayRunner | Deterministic offline replay of the complete decision chain. | `POLICY_ONLY` | Read-only review/replay intent exists. | Typed inputs/results, fixed clock, golden vectors, failure injection, runner, and deterministic regression suite. | W1, W3 -> W6-W13, W18 | High | `PRO_REQUIRED` | CRITICAL | 6-10 | 5-10 / 50-90 | Medium | No |
| W6 | Gold market facts and feature calculation | Pure deterministic facts and features for XAUUSD/GOLD. | `CONTRACT_ONLY` | Market, bars, tick, symbol, and account facts exist in canonical schemas. | Session facts, spread/freshness facts, volatility and structure features, economic-window inputs, and fixtures. | W4 or W5 -> W7 | High | `PRO_REQUIRED` | CRITICAL | 5-8 | 15-25 / 45-80 | Medium | No |
| W7 | Deterministic analysis and opportunity assessment | One explainable, versioned, non-LLM decision path. | `POLICY_ONLY` | Advice authority and explanation boundaries are documented; placeholder observation logic exists. | Strategy contract, deterministic candidate logic, invalidation conditions, reason codes, and replay evidence. | W6 -> W10 | High | `PRO_REQUIRED` | CRITICAL | 6-10 | 10-20 / 50-90 | High | No |
| W8 | RiskGate | One server-owned fail-closed risk decision. | `CONTRACT_ONLY` | Safety-gate and execution-authority contracts define veto semantics and major prohibitions. | Typed policy, daily loss, consecutive loss, spread, freshness, event, stop-loss, leverage, and no-overnight enforcement. | W10 -> W9, W13 | High | `PRO_REQUIRED` | CRITICAL | 5-8 | 10-20 / 45-80 | Medium | No |
| W9 | PositionSizing | Hard-calculated GOLD lot size within approved loss limits. | `CONTRACT_ONLY` | Position sizing authority and required inputs are documented. | Contract math, broker precision, min/max/step handling, loss caps, invalid contract handling, and regression vectors. | W8, W10 -> W11, W13 | High | `PRO_REQUIRED` | CRITICAL | 5-8 | 8-15 / 40-70 | High | No |
| W10 | Unified TradePlan schema and pure builder | One immutable, versioned plan across analysis and Gates. | `CONTRACT_ONLY` | TradePlan schema and example exist. | Canonical typed schema, pure builder, ownership rules, versioning, immutable stage results, and exact contracts. | W7 -> W8, W9, W11 | High | `PRO_REQUIRED` | CRITICAL | 4-6 | 8-15 / 25-45 | Medium | No |
| W11 | Shadow Mode | Run the full decision chain with no execution side effects. | `POLICY_ONLY` | Demo training and authority documents require pre-execution observation. | Shadow runner, decision ledger, comparison outputs, controls, dashboard status, and observation evidence. | W8-W10 -> W12, W13, W20 | High | `PRO_REQUIRED` | CRITICAL | 5-8 | 5-10 / 45-75 | Medium | Yes, estimated 2-6 weeks before Demo execution consideration |
| W12 | FakeExecutionAdapter | Deterministic simulated acceptance, rejection, and fills behind the execution interface. | `NOT_STARTED` | No production adapter or contract evidence was found. | Adapter protocol, AuthorizedDemoOrder input, idempotency, fill/reject/failure policies, audit output, and replay tests. | W10, W13 -> W15, W17, W18 | High | `PRO_REQUIRED` | CRITICAL | 4-6 | 0-3 / 25-45 | Medium | No |
| W13 | ExecutionGate | Final server-owned authorization immediately before an adapter. | `CONTRACT_ONLY` | Authority contract assigns final veto responsibility. | Typed Gate, allowed stage/state checks, session/kill/recovery controls, AuthorizedDemoOrder output, and fail-closed tests. | W8-W11 -> W12, W14-W17 | High | `PRO_REQUIRED` | CRITICAL | 5-8 | 8-15 / 45-80 | Medium | No |
| W14 | MQL4 EA and Demo execution bridge | EA executes only an authorized, idempotent Demo order. | `POLICY_ONLY` | EA authority and Demo-only limits are documented; no MQL4 execution implementation exists. | Command/ack protocol, MQL4 EA, authentication boundary, stop protection, Demo lab, rejection handling, and restart tests. | W4, W13, W15-W17 -> W20 | Critical | `PRO_REQUIRED` | CRITICAL | 10-16 | 5-10 / 100-180 | High | Yes, estimated 4-8 weeks of staged Demo lab work |
| W15 | Idempotency, duplicate prevention, and order recovery | At-most-once intent with recoverable order state. | `POLICY_ONLY` | Bundle idempotency concepts exist, but order idempotency does not. | Client order IDs, dedupe store, state machine, uncertain acknowledgement handling, reconciliation, and restart recovery. | W12-W14 -> W20 | Critical | `PRO_REQUIRED` | CRITICAL | 7-11 | 3-8 / 60-100 | High | Yes, fault and restart campaigns required |
| W16 | Kill switch, circuit breakers, and no-overnight | Independently enforce stop conditions and forced session closure. | `POLICY_ONLY` | Risk policies prohibit overnight and define stop conditions. | Runtime controls, persistent state, daily and consecutive-loss breakers, stale-data breaker, shutdown behavior, and tests. | W13-W15 -> W20 | Critical | `PRO_REQUIRED` | CRITICAL | 6-10 | 5-10 / 50-90 | High | Yes, multi-session observation required |
| W17 | Execution feedback, audit, and end-to-end identity | Trace every fact, plan, Gate decision, order attempt, and fill. | `CONTRACT_ONLY` | Execution audit schema exists. | Trace/correlation/causation IDs, event model, masked broker tickets, rejection/fill ingestion, durable audit, and replay linkage. | W10, W12, W14 -> W18-W20 | High | `PRO_REQUIRED` | CRITICAL | 7-11 | 10-20 / 60-100 | Medium | No |
| W18 | Automated review, performance, and error attribution | Reconstruct outcomes and attribute data, analysis, risk, execution, and broker errors. | `CONTRACT_ONLY` | Observation review, report, and training plans exist. | Replay comparison, metrics, attribution taxonomy, daily reports, strategy/policy version comparison, and evidence retention. | W5, W12, W17 -> W20 | High | `PRO_REQUIRED` | EVIDENCE_GATE | 8-12 | 15-25 / 70-120 | High | Yes, estimated 4-12 weeks of representative sessions |
| W19 | Dashboard and user-visible state | Show source, readiness, Shadow, Gate, execution, kill, recovery, and audit state without granting permission. | `INTEGRATED` | Source/readiness and explanation views are integrated. | Shadow/execution/audit/recovery panels, controls with explicit authority, and end-to-end UI safety tests. | W2, W11, W17 -> W20 | Medium | `PRO_REQUIRED` for execution-state integration | SUPPORTING | 4-7 | 70-110 / 35-60 | Medium | No |
| W20 | Demo GoLiveGate | Separate evidence-based authorization for limited Demo execution. | `POLICY_ONLY` | Demo-only, manual confirmation, safety limits, and activation principles are documented. | Measurable criteria, evidence collector, review packet, user approval state, rollback drill, and controlled activation decision. | W4-W19 -> Demo activation | Critical | `PRO_REQUIRED` | EVIDENCE_GATE | 6-10 | 5-10 / 60-100 | High | Yes, at least 4-12 weeks after the chain is operational |
| W21 | Live GoLiveGate and real-account activation | Future independent Live safety and authorization program. | `POLICY_ONLY` | Live is explicitly excluded and frozen. | Regulatory, operational, credential, broker, security, capital, monitoring, incident, long-Demo-evidence, and independent authorization work. | W20 -> Live activation | Critical | `PRO_REQUIRED` | FROZEN | 12-20 | 5-10 / 140-250 | Very high | Yes, minimum planning assumption 12-24 weeks after verified Demo evidence; not authorized |

## 6. Endpoint progress baseline

### 6.1 Demo Auto-Execution MVP

W0 through W20 sum to:

```text
estimated invested hours: 477-771
estimated remaining hours: 950-1660
central weighted progress: 32.3%
mathematical estimate bounds: 22.3%-44.8%
reporting range after judgment: approximately 25%-40%
```

The reporting range is deliberately wider than a point estimate. The largest
uncertainty lies in the real TradeMax bridge, EA integration, recovery,
circuit-breaker behavior, and calendar-based Demo evidence.

### 6.2 Live Auto-Execution

W0 through W21 sum to:

```text
estimated invested hours: 482-781
estimated remaining hours: 1090-1910
central engineering progress: 29.6%
mathematical estimate bounds: 20.2%-41.7%
reporting range after judgment: approximately 20%-40%
Live activation readiness: 0%
```

The Live engineering percentage primarily reflects reusable read-only and Demo
foundations. It must never be reported as readiness to trade real funds. W21 is
frozen, and its calendar evidence cannot be earned through coding effort.

## 7. Critical path

The current expected Demo MVP critical path is:

```text
W0 engineering governance
  -> W2/W3 canonical diagnostics closeout
  -> W5 ReplayRunner
  -> W6 facts and features
  -> W7 deterministic analysis
  -> W10 Unified TradePlan
  -> W8 RiskGate
  -> W9 PositionSizing
  -> W11 Shadow Mode
  -> W13 ExecutionGate
  -> W12 FakeExecutionAdapter
  -> W15 idempotency and recovery
  -> W14 EA Demo bridge
  -> W18 evidence and attribution
  -> W20 Demo GoLiveGate
```

Parallel convergence requirements:

- W4 may proceed in parallel with W5-W13, but must converge before W14 and W20.
- W16 and W17 may begin after their typed upstream boundaries exist, but must
  converge before W14 activation and W20.
- W19 may proceed incrementally, but the required kill, recovery, and audit
  state must be visible before W20.
- W21 must not begin merely because W20 is designed or implemented.

## 8. Remaining-work sequencing rules

Future planning should preserve these separate stages whenever they are
material:

```text
POLICY -> CONTRACT -> TESTS -> IMPLEMENTATION
       -> INTEGRATION -> ACTIVATION -> VERIFICATION
```

One work order must not silently combine contract, implementation, integration,
and activation. Every write task requires an approved file scope, test scope,
ModelGate decision, independent review, and separate merge approval.

The next planning sequence after this WBS is expected to be:

1. TaskSizeGate and standard work-order contract;
2. test layering, one-click verification, and CI contract;
3. one-click verification implementation;
4. CI implementation;
5. W2/W3 diagnostics closeout;
6. ReplayRunner contract, tests, implementation, and verification;
7. deterministic facts, analysis, TradePlan, RiskGate, and PositionSizing;
8. Shadow Mode, FakeExecutionAdapter, and ExecutionGate;
9. TradeMax writer, EA, idempotency, recovery, circuit breakers, and audit;
10. review evidence, Dashboard state, and Demo GoLiveGate;
11. keep Live frozen until a new planning and authorization decision.

This sequence is a dependency baseline, not authorization to enter any of
those tasks.

## 9. WBS update protocol

The WBS must be reviewed after each accepted merge that materially changes a
work package, and formally re-estimated at least at each stage release or when
actual effort invalidates a range.

An update must:

1. inspect the current `main`, `origin/main`, worktree, active branches, code,
   tests, architecture, and operational evidence;
2. record which capability layer changed;
3. update invested and remaining ranges independently;
4. explain any range movement greater than 10 percent for a package;
5. preserve uncertainty instead of forcing a false point estimate;
6. keep coding hours and required calendar observation separate;
7. recompute both Demo and Live denominators;
8. keep Live activation readiness at zero unless a separately authorized Live
   GoLiveGate has actually passed.

Historical estimates must not be rewritten merely to make progress appear
smoother. A newly discovered safety requirement may legitimately increase the
remaining denominator and reduce the reported percentage.

## 10. Explicit non-goals

WF-4A does not:

- implement TaskSizeGate, pytest markers, one-click validation, or CI;
- implement ReplayRunner, facts, features, analysis, or an Agent;
- implement RiskGate, PositionSizing, TradePlan, Shadow Mode,
  FakeExecutionAdapter, or ExecutionGate;
- implement an MT4 writer, MQL4 EA, bridge, order, fill, or recovery path;
- modify either diagnostics API;
- activate a reader, Demo execution, automatic training, or Live trading;
- create execution permission or trading advice;
- authorize the next work order.

This document is a planning denominator and dependency contract. It is not
evidence that the remaining capabilities exist or that any execution stage is
permitted.
