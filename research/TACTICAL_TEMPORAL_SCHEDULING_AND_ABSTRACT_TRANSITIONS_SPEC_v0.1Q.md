# Tactical Temporal Scheduling and Abstract Transitions — v0.1Q

## Purpose

Convert independent v0.1P per-slice assignments into a deterministic advisory lifecycle that can retain, review, supersede, cancel, or retire abstract plans across observations without issuing commands or inventing execution outcomes.

## Authority and evidence

- Per-slice contract: `TACTICAL_TEMPORAL_SCHEDULE_V1`.
- Trajectory contract: `TACTICAL_TEMPORAL_SCHEDULE_TRAJECTORY_V1`.
- Authority: `NO_ORDERS`.
- Active-plan status: `ABSTRACT_SCHEDULED_NOT_ISSUED`.
- Counterfactual status: `UNVERIFIED`.
- Battle 4 evidence: `CONTROL_OFFLINE_DERIVED_FROM_OBSERVED_INPUT`.
- Temporal matrix evidence: `CONTROL_SYNTHETIC`.

No record establishes WH3 command legality, issue, acceptance, acknowledgement, execution, movement time, route feasibility, formation feasibility, or causal success.

## Trusted inputs

The scheduler accepts only digest-valid `TACTICAL_STATE_VISIBILITY_SAFE_V2` state and canonical `TACTICAL_OBJECTIVE_ASSIGNMENT_V1` output for the same slice and time. It rebuilds the assignment from state and requires semantic equality. Stale state digests, forged objectives, source substitution, altered authority, malformed proposed actions, non-increasing time, and noncanonical assignments fail closed.

Representation order may vary. Tactical meaning may not.

## Temporal state model

Each accepted assignment may create one abstract plan keyed by objective identity, actor identity, and objective type. A plan records:

- observed start and last-review times;
- minimum and maximum commitment boundaries;
- review interval and same-action cooldown;
- the bounded desired transition language inherited from the objective policy;
- observed preconditions and current lifecycle status;
- explicit interpretation limits.

One actor may have at most one active abstract plan per observation.

## Project-owned timing policy

The timing windows are bounded control contracts selected for deterministic anti-thrashing tests. They are **not measured WH3 travel or animation durations**.

| Objective class | Minimum commitment | Review interval | Maximum commitment | Cooldown |
|---|---:|---:|---:|---:|
| Commander extraction | 4 s | 8 s | 20 s | 6 s |
| Artillery evacuation | 5 s | 10 s | 25 s | 8 s |
| Cavalry disengagement | 3 s | 7 s | 18 s | 6 s |
| Ranged repositioning | 4 s | 9 s | 22 s | 7 s |
| Pursuit termination | 2 s | 5 s | 12 s | 4 s |
| Reform and preserve | 4 s | 8 s | 20 s | 6 s |
| Frontline relief | 5 s | 9 s | 20 s | 7 s |
| Local-rout containment | 4 s | 8 s | 18 s | 6 s |
| Reserve commitment | 4 s | 8 s | 18 s | 6 s |
| Selective pursuit | 3 s | 7 s | 16 s | 5 s |

The continuity horizon is 30 seconds. A larger observation gap erases lifecycle certainty and starts a fresh advisory epoch.

## Lifecycle events

The scheduler may emit:

- `PLAN_STARTED`;
- `PLAN_CONTINUED`;
- `PLAN_RETAINED_MINIMUM_COMMITMENT`;
- `PLAN_REASSIGNED_AFTER_REVIEW`;
- `PLAN_SUPERSEDED_SELF_PRESERVATION`;
- `PLAN_CANCELLED_PRECONDITION_FAILED`;
- `PLAN_CANCELLED_TERMINAL`;
- `PLAN_RESOLVED_BY_OBSERVATION_NOT_ATTRIBUTED`;
- `PLAN_REVIEW_REQUIRED_MAX_COMMITMENT`;
- `PLAN_BLOCKED_COOLDOWN`;
- `PLAN_STARTED_CRITICAL_COOLDOWN_OVERRIDE`;
- `CONTINUITY_RESET_OBSERVATION_GAP`.

Objective disappearance is observational retirement only. It does not credit the prior proposal with causing the change.

## Preconditions and arbitration

A prior plan can continue only when:

- the actor remains locally controlled and eligible;
- the objective or protected concern remains canonically present;
- the battle is nonterminal;
- the observation remains inside the continuity horizon.

During minimum commitment, a still-legal prior responder is retained over a minor assignment-score change. After review, the canonical current responder may replace it. A newly required self-preservation objective can supersede an actor's prior support or pursuit plan. Same actor/action churn is blocked by cooldown unless the returning objective is critical, in which case the override is explicit and auditable.

## Bounded abstract transition model

Desired transitions are qualitative safety envelopes such as “danger should not increase” or “support balance should not worsen.” They contain no predicted coordinate, path, duration, casualty count, command result, or success probability.

The scheduler observes later state; it does not simulate that a proposal caused later state.

## Determinism and invariants

The v0.1Q matrix requires:

- 12/12 lifecycle scenario contracts;
- no double-booked active actor;
- no active plan in terminal observations;
- order independence under reversed units and reversed assignment records;
- invariance under uniform coordinate translation;
- explicit cooldown, critical override, review, supersession, cancellation, observational retirement, and continuity-reset behavior;
- all outputs remain `NO_ORDERS`.

## Interpretation boundary

v0.1Q answers only: *How should canonical abstract assignments persist or change across a bounded sequence of trusted observations without thrashing or fabricating execution?*

It does not answer whether WH3 can receive the action, whether a route exists, whether a unit completed the proposal, or whether gameplay improved.
