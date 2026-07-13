# TaskSizeGate Non-Activating Verification Transition Contract

Status: WF-4M contract-only maintenance. This document defines a future
TaskSizeGate maturity rule. It does not change the production evaluator,
contract vectors, Skills, CI, WBS values, activation state, or any business
capability.

## 1. Conflict and purpose

The current TaskSizeGate implementation treats the eight maturity values as one
strictly adjacent sequence. It therefore accepts:

```text
INTEGRATED -> ACTIVATED -> VERIFIED
```

and rejects `INTEGRATED -> VERIFIED` as a multi-stage jump.

That rule conflicts with the approved Canonical Bundle ReplayRunner v1 delivery
sequence. G168 requires real G153 integration evidence followed by a separate
deterministic regression verification task, while also stating that integration
into the test harness does not activate analysis or execution. G173 supplied the
integration evidence without activation. Requiring an `ACTIVATED` claim before
the verification task would therefore fabricate authority that does not exist.

This contract defines the smallest safe exception: an already integrated
capability may collect verification evidence without first being activated.

## 2. Fixed vocabulary and independent meanings

The maturity vocabulary remains exactly these eight values, in this spelling:

```text
NOT_STARTED
POLICY_ONLY
CONTRACT_ONLY
TESTS_ONLY
IMPLEMENTED
INTEGRATED
ACTIVATED
VERIFIED
```

No ninth maturity value, alias, nullable state, or combined
`ACTIVATED_AND_VERIFIED` state is introduced.

The meanings are evidence-based and independent:

- `INTEGRATED` means the implementation has proven integration evidence.
- `ACTIVATED` means a separately governed capability has been enabled in its
  approved operating boundary.
- `VERIFIED` means reviewed verification evidence exists for the stated
  capability and boundary.

`VERIFIED` does not mean `ACTIVATED`. Verification evidence does not grant
activation, deployment, MT4 access, EA authority, execution authority, or
trading permission. Activation readiness must remain separately proven and
must never be inferred from the maturity value alone.

## 3. Standard transitions remain unchanged

The future rule preserves the existing normal forward transitions:

```text
NOT_STARTED -> POLICY_ONLY
POLICY_ONLY -> CONTRACT_ONLY
CONTRACT_ONLY -> TESTS_ONLY
TESTS_ONLY -> IMPLEMENTED
IMPLEMENTED -> INTEGRATED
INTEGRATED -> ACTIVATED
ACTIVATED -> VERIFIED
```

Existing separately approved maturity-preserving hardening and maintenance
rules also remain unchanged.

Backward transitions remain invalid. Arbitrary multi-stage jumps remain
invalid. In particular, no state below `INTEGRATED` may transition directly to
`VERIFIED`.

## 4. Exact non-activating verification transition

The only new maturity-changing form is:

```text
INTEGRATED -> VERIFIED
```

It is valid only when every condition below is satisfied:

1. `current_maturity` is the exact built-in string `INTEGRATED`.
2. `target_maturity` is the exact built-in string `VERIFIED`.
3. `maturity_reason` is the exact built-in string
   `non-activating verification`.
4. `objective_count` is the exact built-in integer `1`.
5. `capability_layers` is the exact built-in tuple `("VERIFICATION",)`.
6. `cross_package_activation` is the exact built-in boolean `false`.
7. Git, scope, dependency, risk, ModelGate, required-check, and unknown
   evidence passes all existing TaskSizeGate validation.
8. The frozen work order contains no activation, deployment, runtime source,
   MT4, EA, order, execution, or trading surface.
9. Activation, deployment, merge, tag, and any second work order remain
   explicitly prohibited capabilities for the verification order.

The exact `maturity_reason` is the deterministic discriminator. The future
evaluator must not infer this transition from free text, task names, desired
results, file names, or the absence of an activation file. The existing 29
`TaskSizeGateEvidence` fields remain exact; this contract adds no thirtieth
field.

If any condition is missing, subclassed, contradictory, unknown, or drifted,
the transition is invalid and must fail closed under the existing
`STOP_UNCERTAIN` behavior. The evaluator must not rewrite the evidence to an
activation transition or a maturity-preserving maintenance task.

## 5. Task sizing and authority

TaskSize continues to use the actual work-order hours, exact file count, and
actual capability layers. The exception does not reduce size and does not
change ModelGate or Supervisor eligibility rules.

A passing TaskSizeGate result only classifies the frozen work order. It is not
user approval and does not create a branch, write files, invoke a Skill, merge,
tag, deploy, activate a capability, call MT4 or an EA, or permit trading.

For ReplayRunner v1, completing deterministic regression verification may
support the narrow maturity evidence `VERIFIED`, but it does not activate the
runner, the canonical reader, analysis, execution, Demo auto-execution, or Live
trading.

## 6. Required fail-closed vectors

Later contract vectors must cover at least:

- valid exact `INTEGRATED -> VERIFIED` non-activating verification;
- the same transition with normal and Pro ModelGate outcomes;
- `INTEGRATED -> ACTIVATED` and `ACTIVATED -> VERIFIED` remaining valid;
- every normal adjacent transition remaining valid;
- missing, altered, subclassed, or non-string maturity reason;
- extra capability layers or any layer other than exact `VERIFICATION`;
- zero or multiple objectives;
- `cross_package_activation=true`;
- every lower maturity attempting to jump directly to `VERIFIED`;
- backward transitions and unrelated multi-stage jumps;
- activation, deployment, MT4, EA, order, execution, or trading scope drift;
- proof that `VERIFIED` never changes activation readiness or authority.

Static vectors alone must not be described as production evaluator support,
Skill integration, activation, or end-to-end verification.

## 7. Mandatory staged delivery

The change must remain split into separately reviewed and explicitly approved
work orders:

```text
WF-4M contract
    -> immutable contract vectors
    -> production TaskSizeGate evaluator support
    -> JLGO planning propagation
    -> jl-develop and jl-supervisor pre-write propagation
    -> jl-review checkpoint propagation
    -> re-plan the blocked G174 verification order
```

Each stage must preserve the existing 29-field evidence boundary unless a new
contract explicitly replaces it. No stage may silently edit planning results,
retry a failed evaluator call, use a fallback classifier, or treat
verification as activation.

## 8. WF-4M acceptance boundary

WF-4M is complete only when this document:

- records the G168/current-TaskSizeGate conflict;
- preserves exactly eight maturity values;
- defines the strict non-activating `INTEGRATED -> VERIFIED` form;
- preserves normal adjacent and maturity-preserving transitions;
- rejects backward, lower-to-verified, and unrelated multi-stage transitions;
- keeps verification and activation authority separate;
- fixes fail-closed vectors and phased follow-up boundaries;
- does not modify or claim implementation of the evaluator, tests, Skills, CI,
  WBS, ReplayRunner verification, activation, MT4, EA, orders, or trading.

WF-4M does not authorize G174. G174 must be planned again only after the
contract, vectors, evaluator, and required workflow integrations have been
separately implemented, reviewed, approved, and merged.
