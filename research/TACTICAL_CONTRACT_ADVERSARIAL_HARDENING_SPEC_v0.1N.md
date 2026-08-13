# Tactical Contract Adversarial Hardening Specification — v0.1N

## Purpose

Harden the v0.1M tactical-state and decision-opportunity interfaces before any planner expansion or live order-authority work. The milestone tests whether malformed, ambiguous, or adversarial observations can cross the visibility-safe boundary and whether state/priority lifecycle semantics remain coherent under deterministic perturbations.

## Authority and evidence

- Runtime authority: `NO_ORDERS`.
- Adversarial-suite classification: `CONTROL_OFFLINE`.
- Tactical recommendations: `HYPOTHESIS`.
- Proposed alternatives: `PROPOSED_NOT_EXECUTED`.
- Counterfactual outcomes: `UNVERIFIED`.
- No WH3, save, Workshop, active-mod, or remote-GitHub state is modified.

## Frozen inputs

| Input | File SHA-256 | Embedded result digest |
|---|---|---|
| Battle 4 visibility-safe slices | `2a961d55f26bf272eed3c28603ee054793993e2b32c5f644001fcd2c296820c9` | `ccb23dc2e24102b53c5833ecae9047ebfd449476cd0508aacd4ec0fd6dc56360` |
| Battle 4 dense observed corpus | `bc89d3cd1adea0540199989b095278d15c5e354343802742970820fefe22be97` | frozen v0.1L dense corpus |
| v0.1N adversarial suite | `39b17cb7e00927e3d4c4ba04a4e6fc9cc96f2718a4a291a9418b59e37bdf2e62` | seed `20260730` |

## Input contract

`BATTLE_TRACE_TACTICAL_INPUT_V2` rejects rather than repairs:

- non-boolean truth values for alliance, movement, engagement, routing, visibility, and threat flags;
- non-finite, non-numeric, or out-of-range health, model, ammunition, geometry, and time values;
- inconsistent model counts/fractions;
- unknown roles or fatigue states;
- missing positions and invalid target sentinels;
- duplicate stable identities;
- local units labeled as foreign-visible or foreign units labeled as local;
- slice times outside the battle duration;
- foreign identity/detail that violates the local-alliance visibility scope.

Downstream scoring may clamp its own derived metrics, but validation may not silently convert malformed observations into plausible tactical facts.

## State contracts

- Unit/battle state: `TACTICAL_STATE_VISIBILITY_SAFE_V2`.
- Trajectory: `TACTICAL_STATE_TRAJECTORY_V2`.
- Local condition and global tactical phase are separate:
  - local condition describes the local force only;
  - enemy rout/collapse can change the tactical phase without erasing local crisis;
  - simultaneous local and enemy collapse must preserve the local-collapse response.
- Battle 4 majority-rout state is therefore `LOCAL_CRISIS` plus `RECOVERY_REQUIRED`, not a falsely recovered local force.

## Stable opportunity lifecycle

A per-slice `opportunity_id` identifies one evaluated instance. A separate stable `opportunity_key` identifies the continuing tactical concern across slices. Command-budget lifecycle metrics compare stable keys, not slice-specific instance IDs.

The corrected Battle 4 reference metrics are:

- 44 candidate opportunities;
- 25 selected opportunities;
- 28 advisory priority transitions;
- 11 continued advisory priorities;
- maximum six selected in one slice;
- 100% minimum critical-opportunity coverage;
- 397 observed owner command events as a noncausal reference;
- transition/command ratio `0.070529`, labeled `REFERENCE_ONLY_NOT_CAUSAL`.

## Adversarial suite

The suite contains 24 deterministic cases:

- 18 invalid-input mutations that must fail closed;
- 6 metamorphic cases covering unit-order independence, global x/z translation, monotonic commander deterioration, simultaneous local/enemy collapse, hidden-enemy terminal guarding, and stable opportunity lifecycle.

All failing inputs, mutations, paths, expected classifications, input hashes, and the seed are preserved in `synthetic_lab/scenarios/tactical_contract_adversarial_suite_v0.1N.json`.

## Acceptance

The gate passes only when:

1. all 18 malformed-input cases are rejected;
2. all 6 metamorphic invariants pass;
3. the three v0.1N artifacts rebuild byte-identically twice;
4. the frozen v0.1M artifacts remain unchanged as historical evidence;
5. the full SyntheticLab and Runtime Probe suites pass;
6. repository hash validation remains complete beneath ignored-name checkout ancestors;
7. no output gains order, acknowledgement, success, pathfinding, causal-improvement, or generalization authority.

## Remaining uncertainty

This milestone proves contract integrity against one frozen vanilla land-battle trace and synthetic perturbations. It does not prove tactical quality, live command feasibility, terrain-aware withdrawal, SFO compatibility, siege/ambush/reinforcement behavior, other-faction generalization, or causal casualty reduction.
