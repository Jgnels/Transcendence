# Gate 0 Segment — Campaign Theater Force Assignment and Commitment v0.2G

## Result

**CLOSED OFFLINE.** v0.2G converts exact v0.2F strategic/theater priorities into deterministic, exclusive shadow army allocations and a multi-turn anti-thrashing commitment lifecycle while retaining `NO_ORDERS` and application `PROHIBITED`.

## Implemented

- exact v0.2E/v0.2F source verification before assignment;
- critical-overflow expansion back to exact source obligations;
- one `ARMY_STRATEGIC_COMMITMENT_SLOT` per eligible controlled field army;
- recovery protection with explicit critical-only override;
- abstract healthy strategic-reserve preservation when possible;
- aggressive-commitment veto propagation from v0.2F;
- deterministic candidate ranking using observer-safe geometry, replenishment, normalized strength, and existing front coverage;
- explicit unfilled priorities and resource conflicts when force capacity is insufficient;
- temporal `START`, `CONTINUE`, `REASSIGN_AFTER_REVIEW`, `SUPERSEDE`, `CANCEL`, `RETIRE`, and `CONTINUITY_RESET` events;
- 2-turn minimum commitment, 4-turn review window, and 0.15 material-score margin as disclosed project-owned anti-thrashing parameters;
- CLI/smoke integration, frozen cross-evidence artifact, adversarial matrix, and runtime-surface safety tests.

## Adversarial matrix

8/8 assignment cases, 6/6 temporal cases, and 7/7 metamorphic checks pass.

Assignment coverage includes unique actors across two exposed fronts, recovery/reserve protection, explicit critical recovery override, posture-only low pressure, planner-ineligible actor exclusion, seven-critical-front overflow with three-army shortage disclosure, nonwar visible-asset exclusion, and deterministic equal-score tie resolution.

Temporal coverage includes small-geometry anti-thrash retention, review-window reassignment only after material improvement, recovery cancellation, noncausal retirement, turn-gap continuity reset, and higher-severity supersession.

Metamorphic checks preserve assignment/commitment semantics under hidden-enemy injection, player→NPC relabeling, input reordering, coordinate translation, uniform strength scaling, temporal input reordering, and temporal coordinate translation.

## Observed and synthetic result

Observed Reikland turns 4–6 assign no army because their v0.2F state is low-pressure consolidation. Turn 7 creates exactly one shadow assignment: `CONTAIN_COHERENT_VISIBLE_RIVAL` to `force:65`. The observed temporal schedule therefore contains a single `START` and is explicitly a limiting result, not calibration of multi-turn persistence.

The synthetic late-game case assigns siege-relief coverage and strategic reserve to distinct healthy actors, protects the recovering army, and leaves rival pressure unfilled under `AGGRESSIVE_COMMITMENT_VETO`. Critical force-assignment coverage is 1.0 in that case with zero actor double-booking.

## Performance and regression

- SyntheticLab: 138 tests passed twice.
- Runtime Probe: 143 tests passed twice.
- Total direct tests: 281.
- `compileall`: pass.
- Frozen allocation and matrix generation reproduced byte-for-byte twice.
- 500-asset assignment evaluation repeated 10 times with one result digest; mean 0.1212 s, min 0.1134 s, max 0.1610 s; six assignments, 1.0 critical coverage, zero double booking on every run.

## Frozen identities

- cross-evidence force-allocation result digest: `1ea40164577d918e349bd7f2873c0afb4a24ecf98f0e437c244f0ada12ea9f72`;
- adversarial matrix result digest: `61fa5cc91ba3c4a6f96c4e43f3613b01e6b484e606192c3039b33134f821e353`.

- force-allocation artifact SHA-256: `9f2f6380d1430bbb01603051a47850fe4c5a67ba2800aeeec54b113f93234c1e`;
- adversarial scenario SHA-256: `16b915e1c63f6c32d8346346c91fb09924e943087b0a98e982f77a5f8ff5ab15`;
- adversarial result artifact SHA-256: `e6a3749794053511f47f6a3a3d7c443a9a9f971c0dc0cc3aa045e5287cb0fde6`.

## Defects found and corrected during the gate

- Recovery protection initially pre-claimed recovering actors so completely that the documented critical-emergency override could never occur. Critical obligations now explicitly override the protection record only when necessary and mark the exception.
- A fresh higher-priority geometric proposal could initially steal an actor from a lower plan even when that incoming priority was already covered by another retained plan. Supersession now checks active coverage first, preventing geometry-driven reverse-use churn.
- Frozen matrix recomputation initially differed after JSON round-trip because runtime semantic metrics used tuples while JSON stores arrays. Semantic metrics now emit JSON-native arrays, preserving exact frozen-artifact equality.

## Still unverified

Campaign path feasibility, movement/action legality, stances, zone-of-control effects, interceptions, settlement access, campaign command issue/acceptance/acknowledgement/execution, causal strategic outcomes, economy/recruitment recovery, diplomacy/blocs, SFO longitudinal strategy, optimal allocation, timing calibration, and owner enjoyment.

## Next gate

Build a bounded campaign strategic feasibility/action-authority envelope over v0.2G assignments. Keep route and application claims fail-closed: first establish exactly which campaign movement/target/action questions can be represented and checked offline from known capability contracts, and freeze the smallest read-only owner observation packet only if WH3 runtime evidence is genuinely required. Do not issue campaign orders yet.
