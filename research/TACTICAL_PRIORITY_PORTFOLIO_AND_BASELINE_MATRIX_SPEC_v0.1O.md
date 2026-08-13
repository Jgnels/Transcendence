# Tactical Priority Portfolio and Baseline Matrix Specification — v0.1O

## Purpose

v0.1O tests whether the v0.1N role-aware tactical adviser remains coherent outside the eight original Battle 4 slices and whether a bounded advisory budget can preserve all critical concerns.

The gate is entirely offline. It does not issue WH3 orders, simulate pathfinding, establish command acceptance, or claim battle-outcome improvement.

## Inputs

- frozen `BATTLE_TRACE_TACTICAL_INPUT_V2` Battle 4 slices;
- project-owned `TACTICAL_BASELINE_MATRIX_V1` synthetic mutations;
- v0.1N tactical state and candidate-opportunity extraction;
- deterministic policy baselines.

Synthetic mutations inherit the exact strict unit and visibility validation boundary but are labeled `CONTROL_SYNTHETIC`, not `OBSERVED`.

## Priority portfolio

`TACTICAL_PRIORITY_PORTFOLIO_V1` groups equivalent unit-level opportunities by opportunity type before applying the six-priority workload bound.

A portfolio record preserves:

- all source opportunity IDs and stable keys;
- the union of subject unit identities;
- maximum severity and utility plus mean utility;
- the representative diagnosis and alternatives;
- the minimum confidence and union of limitations;
- `UNVERIFIED` counterfactual status;
- `ADVISORY_ONLY` authority.

Critical source opportunities may not disappear silently. If more than six distinct critical groups exist, five groups remain explicit and the remainder are represented by one `CRITICAL_PORTFOLIO_OVERFLOW` record. That record preserves source identities and subjects but does not establish an executable sequence.

## Heterogeneous fixture matrix

The matrix contains 16 project-owned scenarios covering:

- healthy first contact with no spurious action;
- commander extraction;
- role-threshold asymmetry;
- artillery breach;
- ranged rear-flank pressure at two unit scales;
- cavalry overextension;
- frontline crisis with and without a reserve;
- selective exploitation of a breaking enemy;
- rout-cascade preservation;
- hidden-enemy uncertainty;
- simultaneous local and enemy collapse;
- terminal no-action behavior;
- six-group critical saturation;
- seven-group critical overflow.

Each scenario defines required and forbidden intents, required subjects where applicable, state-machine expectations, and the maximum advisory count. These are project-owned contract invariants, not observed gold actions.

## Baselines

The matrix compares:

1. `ROLE_AWARE_PORTFOLIO_V1`;
2. frozen `LEGACY_ROLE_AWARE_V2` selection;
3. `UNIFORM_DANGER_045`;
4. `PRESERVATION_ONLY_035`;
5. `PRESSURE_ONLY`;
6. `PASSIVE_HOLD`.

Comparison reports required-intent recall, forbidden-intent safety, scenario-contract passes, advisory volume, distinct intents, pairwise disagreement, and equivalence checks. It is explicitly noncausal and is not a tactical-quality ranking.

## Gate conditions

The gate closes only when:

- all 16 synthetic state contracts pass;
- the role-aware portfolio passes all 16 intent contracts;
- required-intent recall and forbidden-intent safety are both 1.0;
- the half-scale ranged fixture is semantically equivalent to its full-scale pair;
- critical source coverage is 1.0 in ordinary saturation and overflow cases;
- selected priorities never exceed six;
- overflow is explicit rather than silent;
- Battle 4 portfolio generation is deterministic and digest-stable;
- the v0.1N artifacts remain frozen;
- all repository tests and hash validation pass;
- authority remains `NO_ORDERS`.

## Non-claims

Passing does not establish:

- tactical superiority;
- causal casualty reduction;
- terrain-aware movement or path feasibility;
- assignment or command sequencing;
- command issue, acceptance, acknowledgement, or success;
- ordinary-live, SFO, siege, ambush, reinforcement, monster/flying, or other-faction generalization.
