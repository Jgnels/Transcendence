# Tactical Objective Assignment and Conflict Resolution — v0.1P

## Purpose

Convert the bounded v0.1O tactical-priority portfolio into deterministic, visibility-safe, non-executable unit-to-objective proposals. The layer must disclose infeasibility and resource conflicts rather than manufacturing a responder, route, or successful command.

## Authority and evidence

- Assignment contract: `TACTICAL_OBJECTIVE_ASSIGNMENT_V1`.
- Trace contract: `TACTICAL_OBJECTIVE_ASSIGNMENT_TRAJECTORY_V1`.
- Authority: `NO_ORDERS`.
- Individual assignment status: `PROPOSED_NOT_EXECUTED`.
- Counterfactual status: `UNVERIFIED`.
- Battle 4 output: `CONTROL_OFFLINE_DERIVED_FROM_OBSERVED_INPUT`.
- Heterogeneous matrix: `CONTROL_SYNTHETIC`.

No record establishes pathfinding, formation feasibility, issue, acceptance, acknowledgement, execution, casualty reduction, or improved battle outcome.

## Inputs

The layer accepts only:

1. a digest-valid `TACTICAL_STATE_VISIBILITY_SAFE_V2` state retaining `NO_ORDERS` authority; and
2. a digest-valid `TACTICAL_PRIORITY_PORTFOLIO_V1` whose selected source-opportunity set exactly matches the canonical portfolio rebuilt from that state.

Reordered but semantically identical priority records are accepted after digest recomputation. Added, removed, stale, forged, malformed, or authority-changing portfolio inputs fail closed.

## Objective construction

Selected source opportunities become explicit objective records.

### Self-directed objectives

- `EXTRACT_COMMANDER`
- `EVACUATE_ARTILLERY`
- `DISENGAGE_CAVALRY`
- `REPOSITION_RANGED`
- `TERMINATE_PURSUIT`
- `REFORM_AND_PRESERVE`

The subject unit is the only possible actor. If it is routing, shattered, leaving, or rampaging, the objective remains visible but is marked `SUBJECT_NOT_CONTROLLABLE`.

### Support objectives

- `RELIEVE_FRONTLINE`
- `CONTAIN_LOCAL_ROUT`
- `COMMIT_RESERVE`
- `SELECTIVE_PURSUIT`

Responder eligibility is constrained by local-alliance identity, role, current control state, danger, recoverability, fatigue where relevant, protected-subject status, and source actor pools. A unit that is itself protected by another objective cannot simultaneously be reassigned as a support responder.

## Assignment model

Each local unit has one abstract `UNIT_ACTION_SLOT` per slice. The deterministic optimizer maximizes:

1. objective severity;
2. objective utility;
3. actor suitability;
4. assignment count; and
5. a stable lexical tie-break.

This is a bounded offline exclusivity model, not a command scheduler. Straight-line distance is a ranking proxy only.

## Unfilled semantics

An objective can remain unfilled for three materially different reasons:

- `SUBJECT_NOT_CONTROLLABLE`: a self-directed subject cannot currently receive the proposed action;
- `NO_LEGAL_CANDIDATE`: no responder survives all eligibility constraints;
- `RESOURCE_CONFLICT_WITH_HIGHER_VALUE_OBJECTIVE`: at least one legal responder exists, but its single action slot is consumed by a higher-valued objective.

Unfilled objectives are retained in evidence. They are not removed to improve apparent coverage.

## Determinism and invariants

The v0.1P matrix requires:

- no actor assigned to more than one objective per slice;
- identical assignment output when unit input order is reversed;
- identical semantic assignment when selected portfolio records are reversed;
- identical semantic assignment after uniform coordinate translation;
- terminal states produce no objectives or assignments;
- hidden-enemy uncertainty does not create pursuit assignments;
- critical-overflow source opportunities expand into explicit objectives rather than disappearing;
- stale or forged portfolios fail closed.

## Interpretation boundary

The assignment layer answers only: *Given the current validated state and selected advisory concerns, which currently eligible local unit is the deterministic best abstract responder under these project-owned constraints?*

It does not answer:

- whether a route exists;
- whether formations can pass or disengage;
- whether the action is legal in WH3 at that moment;
- whether the command can be issued through a supported interface;
- whether WH3 accepts or executes it;
- whether the result improves casualties, victory probability, or player enjoyment.
