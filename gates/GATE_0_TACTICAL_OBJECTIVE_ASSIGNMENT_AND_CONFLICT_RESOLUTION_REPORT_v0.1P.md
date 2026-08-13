# Gate 0 Segment — Tactical Objective Assignment and Conflict Resolution v0.1P

## Result

**CLOSED OFFLINE.** v0.1P converts the v0.1O advisory portfolio into deterministic, non-executable unit-to-objective proposals while preserving infeasibility, conflict, visibility, and authority boundaries.

The owner-machine canonical base is v0.1O: 41 SyntheticLab tests, 61 Runtime Probe tests, 102 total tests, 16 heterogeneous scenarios, and 192 canonical hashes. No WH3, save, Workshop, active-mod, runtime, or remote-GitHub state was changed by this gate.

## Implemented

- `TACTICAL_OBJECTIVE_ASSIGNMENT_V1` and trajectory contract;
- deterministic objective construction from canonical v0.1O source opportunities;
- self-directed and support objective classes;
- responder eligibility by role, control state, danger, recoverability, fatigue, protected-subject status, and source pool;
- one abstract `UNIT_ACTION_SLOT` per local unit per slice;
- deterministic maximum-weight conflict resolution with stable tie-breaks;
- explicit `SUBJECT_NOT_CONTROLLABLE`, `NO_LEGAL_CANDIDATE`, and `RESOURCE_CONFLICT_WITH_HIGHER_VALUE_OBJECTIVE` results;
- canonical source-set validation that rejects stale or forged portfolios;
- unit-order, portfolio-order, and coordinate-translation invariance checks;
- Battle 4 assignment trajectory and a 12-scenario assignment matrix.

## Battle 4 measurements

- objectives: 50;
- assignments: 34;
- unfilled objectives: 16;
- unassignable objectives: 12;
- uncontrollable-subject objectives: 9;
- resource-conflict omissions: 4;
- minimum assignable-objective coverage: 0.75;
- minimum critical-assignable coverage: 1.0;
- maximum assignments in one slice: 10;
- double-booked actors: 0.

The zero value for minimum all-critical assignment coverage occurs because observed routing/shattered subjects remain critical but unassignable. The separate critical-*assignable* coverage is the relevant optimizer measurement. Neither measurement is a live command-success claim.

## Synthetic matrix

- scenarios: 12/12 passed;
- metamorphic checks: 3/3 passed;
- objectives examined: 26;
- assignments selected: 12;
- unassignable objectives retained: 12;
- resource conflicts retained: 2;
- double-booked actors: 0;
- all outputs: `NO_ORDERS`.

Covered conditions include balanced contact, commander extraction, artillery evacuation, ranged repositioning, cavalry disengagement, reserve relief, selective pursuit, uncontrollable routing subjects, simultaneous local/enemy collapse, critical overflow with one legal responder, hidden-enemy uncertainty, and terminal no-action behavior.

## Defects corrected

1. **Portfolio inputs were trusted too broadly.** A caller could supply a digest-stale, authority-altered, or source-substituted portfolio to the assignment layer. v0.1P verifies state/portfolio digests, contracts, authority, counts, per-priority digests, and exact canonical source-opportunity membership.
2. **All no-candidate cases had one generic label.** Self-directed subjects that could not receive orders were indistinguishable from support objectives with no legal responder. v0.1P preserves `SUBJECT_NOT_CONTROLLABLE` separately.
3. **Unit input order was not explicitly canonicalized.** Tactical-state unit derivation now sorts stable identities before geometry and state construction; frozen prior artifacts remain unchanged.

## Determinism and closure validation

The two generated v0.1P artifacts were rebuilt twice with byte-identical output. The complete repository suite passed twice before packaging:

- SyntheticLab: 46 passed;
- Runtime Probe: 61 passed;
- total: 107 passed;
- canonical repository hashes: 200 validated.

The owner-machine installation remains the only unexecuted release step; no WH3 gameplay or runtime capture is required for this gate.

## Exact evidence identities

- assignment-suite seed: `20260730`;
- assignment-suite result digest: `8a29d77eefdc9c56c64ddf38627e4821e82d268e1f3e5abf5b6207af0d8dd024`;
- Battle 4 assignment result digest: `b3103d2e03acbb948e7ae3064d3d40aeff1843bc8164e3c999e14865f1c46b3d`;
- assignment-matrix result digest: `ed6433f24d10fe0bf9ee51c4715bb64a9b8f734ee1deb7d118e9fe27ffbc0ac5`;
- Battle 4 assignment file SHA-256: `246831feb0c7c88dcf54b8ccea6ec8a7fbde91c05a0eccde4c40396aa0fa01e2`;
- assignment-matrix file SHA-256: `350140ab1b06d9c6347875589f23c2cb8d104aa46533f289bbdef7a3da47aaf6`.

## Capability classification

Promoted:

- deterministic unit-to-objective arbitration: `CONTROL_OFFLINE`;
- explicit single-slot conflict resolution: `CONTROL_OFFLINE`;
- assignment matrix and metamorphic invariants: `CONTROL_SYNTHETIC`;
- forged/stale portfolio rejection: `CONTROL_OFFLINE`.

Still unverified:

- terrain-aware paths and formation feasibility;
- WH3 command legality and controllability at runtime;
- command issue, acceptance, acknowledgement, execution, or outcome;
- temporal sequencing across multiple commands;
- causal casualty reduction or tactical superiority;
- SFO, siege, ambush, reinforcement, monster, flying-unit, and broad faction generalization.

## Next gate

The next offline layer should add multi-step temporal scheduling, action preconditions, cancellation/replan rules, and a bounded abstract transition model. A live gameplay run is premature until that packet defines exactly which reachability, controllability, acknowledgement, and timing fields must be collected.
