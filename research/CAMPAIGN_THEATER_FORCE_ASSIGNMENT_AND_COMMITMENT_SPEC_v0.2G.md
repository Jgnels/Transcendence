# Campaign Theater Force Assignment and Commitment Specification v0.2G

## Purpose

Convert the bounded v0.2F strategic/theater portfolio into deterministic shadow force allocations, then preserve those allocations across consecutive campaign observations without strategic thrashing. This layer remains entirely project-owned and offline: it does not prove campaign routes, issue commands, acknowledge execution, or assign causal credit.

## Contracts

- `CAMPAIGN_THEATER_TO_ARMY_ASSIGNMENT_V1`
- `CAMPAIGN_THEATER_TO_ARMY_CROSS_EVIDENCE_ASSIGNMENT_V1`
- `CAMPAIGN_STRATEGIC_TEMPORAL_COMMITMENT_V1`
- `CAMPAIGN_STRATEGIC_FORCE_ALLOCATION_CROSS_EVIDENCE_V1`
- `CAMPAIGN_THEATER_ASSIGNMENT_AND_COMMITMENT_ADVERSARIAL_MATRIX_V1`

An assignment must be recomputable from the exact canonical campaign scenario, v0.2E challenge envelope, and v0.2F strategic portfolio. Supplied challenge/portfolio inputs that are stale, forged, foreign, or semantically different from fresh recomputation fail closed.

## Force-allocation boundary

Each planner-eligible controlled field army owns one abstract `ARMY_STRATEGIC_COMMITMENT_SLOT`. An actor may occupy at most one assignment/protection slot per snapshot.

The allocator:

- expands `CRITICAL_STRATEGIC_OVERFLOW` back into its exact critical source priorities before resource allocation;
- protects armies below the frozen `0.65` recovery threshold from noncritical work;
- permits a critical obligation to use a recovering actor only through explicit `RECOVERY_PROTECTION_OVERRIDDEN_BY_CRITICAL` evidence;
- preserves one healthy unclaimed army as an abstract strategic reserve when possible for noncritical work;
- leaves shortages and conflicts explicit rather than fabricating capacity;
- respects the v0.2F aggressive-commitment veto;
- excludes planner-ineligible controlled forces;
- uses deterministic severity-first greedy arbitration and makes no optimality claim.

## Geometric reference, not path proof

For a region obligation, the observed region point is the reference anchor. For a visible hostile faction or rival set, the anchor is an observer-safe centroid of visible at-war assets. Candidate scores combine straight-line geometric reference, replenishment, normalized strength, and existing front coverage.

`geometric_eta_turns_reference` is a ranking feature only. The route state is always `NOT_EVALUATED_GEOMETRIC_REFERENCE_ONLY`. It does not establish WH3 campaign pathfinding, movement reachability, stance legality, zone-of-control legality, interception risk, settlement access, or action availability.

## Temporal commitment lifecycle

Across strictly increasing consecutive turns, shadow commitments may:

- `START`;
- `CONTINUE`;
- `REASSIGN_AFTER_REVIEW`;
- `SUPERSEDE`;
- `CANCEL`;
- `RETIRE`;
- `CONTINUITY_RESET`.

Project-owned anti-thrashing parameters are:

- minimum commitment window: 2 turns;
- reassignment review window: 4 turns;
- material assignment-score improvement required at review: 0.15.

A fresh geometric preference does not steal an actor from a valid retained plan merely because geometry changed. Reassignment after the review window also requires a materially better unclaimed actor. A higher-severity obligation may supersede a lower-severity claim, but not if the incoming priority is already covered by another retained plan. Turn gaps reset continuity rather than silently completing plans.

A disappearing priority is observational retirement with `NO_CAUSAL_CREDIT`; it is not evidence that the plan succeeded. Actor loss, recovery entry for noncritical work, or a new aggressive veto cancels the affected shadow commitment.

## Authority

- policy authority: `NO_ORDERS`;
- application authority: `PROHIBITED`;
- assignment status: `SHADOW_PROPOSED_NOT_EXECUTED`;
- route status: `NOT_EVALUATED_GEOMETRIC_REFERENCE_ONLY`.

No campaign controller, mutation adapter, movement call, target application, acknowledgement detector, execution detector, or outcome-credit mechanism is introduced.

## Evidence limits

Observed Reikland turns 4–7 contain only one planner-eligible controlled field army and end at the first coherent-rival assignment. They therefore constrain only the low-pressure-to-rival-awareness transition, not multi-army exclusivity, reserve behavior, overflow resolution, or the 2/4-turn temporal windows. Those mechanisms are controlled synthetic/adversarial evidence until a later campaign cohort provides longitudinal calibration.

The greedy solver, recovery threshold, reserve floor, timing windows, and 0.15 reassignment margin are engineering policies, not empirically optimal WH3 parameters. Economy, recruitment, diplomacy, native CAI intent, campaign path feasibility, order authority, acknowledgement, execution, causal outcome, SFO longitudinal strategy, and owner enjoyment remain outside this gate.
