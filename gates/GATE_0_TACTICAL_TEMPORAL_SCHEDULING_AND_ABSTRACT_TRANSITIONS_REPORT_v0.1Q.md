# Gate 0 Segment — Tactical Temporal Scheduling and Abstract Transitions v0.1Q

## Result

**CLOSED OFFLINE.** v0.1Q converts independent v0.1P assignments into a deterministic, non-executable temporal lifecycle with explicit commitment, review, cancellation, supersession, cooldown, continuity-reset, and observational-retirement semantics.

The owner-machine canonical base is v0.1P: 46 SyntheticLab tests, 61 Runtime Probe tests, 107 total tests, 12 assignment scenarios, three metamorphic checks, and 200 canonical hashes. No WH3, save, Workshop, active-mod, runtime, or remote-GitHub state was changed by this gate.

## Implemented

- `TACTICAL_TEMPORAL_SCHEDULE_V1` and trajectory contract;
- canonical state-and-assignment authenticity checks;
- ten project-owned action policies with bounded commitment, review, maximum-duration, and cooldown windows;
- one active abstract plan per actor;
- continuation, minimum-commitment retention, reviewed reassignment, self-preservation supersession, precondition cancellation, terminal cancellation, maximum-commitment review, same-action cooldown, critical cooldown override, and observation-gap reset;
- observational resolution with no causal credit;
- qualitative desired-transition envelopes with no route, timing, numeric-outcome, or execution prediction;
- Battle 4 temporal schedule and a 12-scenario synthetic lifecycle matrix.

## Defects corrected

1. **Per-slice assignment had no memory.** Adjacent assignments could change actors without a commitment window, review event, cancellation reason, or lifecycle identity. v0.1Q makes every change explicit.
2. **Objective disappearance could be mistaken for completed action.** Retirement is now `PLAN_RESOLVED_BY_OBSERVATION_NOT_ATTRIBUTED`; no success is credited.
3. **Sparse observations could be treated as continuous execution.** Gaps over 30 seconds emit `CONTINUITY_RESET_OBSERVATION_GAP`, retire certainty, clear cooldown state, and begin a new advisory epoch.
4. **Reappearing objectives could thrash actor/action state.** Project-owned cooldowns block noncritical reactivation; critical preservation may override only through an explicit event.
5. **Assignment packets could be forged or stale.** The scheduler verifies contracts, authority, digests, time, proposed-action bounds, and semantic equality with the assignment canonically rebuilt from the state.

## Battle 4 measurements

The eight milestone slices are intentionally sparse. They produce:

- raw assignments: 34;
- plan starts: 34;
- plan continuations: 0;
- minimum-commitment retentions: 0;
- reviewed reassignments: 0;
- supersessions: 0;
- observational resolutions: 1;
- precondition cancellations: 1;
- terminal cancellations: 10;
- maximum-commitment reviews: 4;
- continuity-reset events across active plans: 18;
- maximum active plans in one slice: 10;
- double-booked active actors: 0.

The absence of Battle 4 continuations is a limiting result of the compact milestone cadence, not evidence that temporal persistence is unnecessary or defective.

## Synthetic temporal matrix

- scenarios: 12/12 passed;
- metamorphic checks: 3/3 passed;
- plan starts: 27;
- continuations: 2;
- minimum-commitment retentions: 1;
- cooldown blocks: 1;
- continuity resets: 2;
- double-booked active actors: 0;
- all outputs: `NO_ORDERS`.

The matrix covers balanced inactivity, stable continuation, observational retirement, actor control loss, minimum-commitment retention, reviewed reassignment, self-preservation supersession, cooldown blocking, critical cooldown override, maximum-commitment replan, continuity-gap reset, and terminal cancellation.

## Determinism and closure validation

The two generated v0.1Q evidence artifacts were rebuilt independently with byte-identical output. The complete repository suite passed twice before packaging:

- SyntheticLab: 51 passed;
- Runtime Probe: 61 passed;
- total: 112 passed;
- canonical repository hashes: 208 validated.

The owner-machine installation remains the only unexecuted release step. No gameplay run is required for this offline gate.

## Exact evidence identities

- temporal-matrix seed: `20260730`;
- temporal-suite digest: `d6c34221a1abe64e8bfc86ef2e7f01cc03c0b8a704422cae84ca9ce95f299270`;
- Battle 4 temporal result digest: `eeea9726dc33557110def72771dba8adc26b43934a46345edb7e631202f8af0e`;
- temporal-matrix result digest: `126d5665fa7554fca2578abfd65491e47de88278fcb933ac3701737cd5ee7ebe`;
- Battle 4 temporal file SHA-256: `f0924f7498f4faa7e943947707fabbd4aafb81be8f38980d4dd8c7d03cc0386e`;
- temporal-matrix file SHA-256: `995fc5c278d7bef0ee226f236ae7f9720fba3be39249fba9205eebf339a9a341`;
- scenario-suite file SHA-256: `457b2f8eb337cd244ce3d156b9d8f95b4d8ec87c329f30facc25ea7fecad2a4d`.

## Capability classification

Promoted:

- deterministic abstract plan lifecycle: `CONTROL_OFFLINE`;
- explicit anti-thrashing commitment and cooldown semantics: `CONTROL_OFFLINE`;
- precondition cancellation and continuity reset: `CONTROL_OFFLINE`;
- temporal matrix and representation invariants: `CONTROL_SYNTHETIC`.

Still unverified:

- WH3 action availability and controllability;
- legal command construction, issue, acceptance, acknowledgement, execution, interruption, and outcome;
- measured movement and animation timing;
- path, formation, collision, and reachability feasibility;
- causal casualty reduction, tactical superiority, and player enjoyment;
- SFO, siege, ambush, reinforcement, monster, flying-unit, and broad faction generalization.

## Next gate

The next gate should freeze a read-only live action-authority and feasibility evidence packet: observed controllability, candidate action, issue attempt, acknowledgement/execution distinction, ordered position or target state, interruption/cancellation timing, and reachability evidence. Only after that packet and its fail-closed parser are complete should the owner perform one batched gameplay capture. No live order authority is authorized.
