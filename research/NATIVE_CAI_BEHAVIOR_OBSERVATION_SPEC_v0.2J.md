# v0.2J Native CAI Behavior Observation Spec

**Date:** 2026-08-02  
**Status:** `OFFLINE_DETECTOR_READY`  
**Authority:** `NO_ORDERS`  
**Application:** `PROHIBITED`

## Purpose

The post-review architecture makes current WH3 native CAI the default strategic planner/executor. v0.2J therefore does **not** ask whether Transcendence's v0.2G allocator would choose a different army. It defines a fail-closed observational detector for the remaining behavior gaps that row/schema evidence did not resolve:

1. recovering-army offensive re-entry;
2. threatened-front coverage and response latency;
3. a bounded home-zone reserve-capacity proxy;
4. directional intent-churn proxies;
5. explicit non-observability of native assignment exclusivity, task memory, and hysteresis from trajectories alone.

The detector is designed to falsify native adequacy when a reproducible material failure is observed. Absence of a detector flag is not proof that an undocumented native mechanism exists.

## Why trajectory evidence is the correct next layer

Creative Assembly documents that Campaign AI generates tasks, combines compatible tasks, evaluates target/force strength, modifies task priority by distance measured in turns, allocates tasks to armies, and now changes priorities according to campaign progression. Those facts make project-owned task/army assignment an inappropriate default comparison target.

Primary official sources:

- Creative Assembly, **Improving AI in Campaign - Part 2**, 2025-04-09: threat/strength assessment, distance-in-turns scaling, recruitment-aware distance, aggression calibration.  
  https://community.creative-assembly.com/total-war/total-war-warhammer/blogs/69%20style%3Dbutton
- Creative Assembly, **Hotfix 6.3.4**, 2025-11-05: multiple task generators, generation/allocation split, task batching, force-strength prerequisites.  
  https://community.creative-assembly.com/total-war/total-war-warhammer/forums/7-patch-notes-amp-announcements/threads/11820-total-war-warhammer-iii-hotfix-6-3-4
- Creative Assembly, **Patch 8.1 Release Notes**, 2026-07-09: turn-dependent Campaign AI prioritisation and late-game defensive/task-target changes.  
  https://community.creative-assembly.com/total-war/total-war-warhammer/blogs/101-total-war-warhammer-iii-patch-8-1-release-notes

These sources do **not** establish native persistent assignment memory, deliberate land-army reserves, recovery gating, assignment exclusivity, or reassignment hysteresis. v0.2J keeps those engine-internal dimensions unavailable unless direct evidence appears.

## Input contract

`NATIVE_CAI_BEHAVIOR_TRACE_V1`

A trace contains:

- one controlled faction identity;
- unique increasing campaign turns;
- canonical observer-safe campaign snapshots;
- optional **observed** `ARMY_ENGAGEMENT` events for controlled field armies;
- `NO_ORDERS` and application `PROHIBITED` authority markers.

An engagement event must carry the actor's replenishment measurement **at engagement time**. Current/post-battle snapshot replenishment is insufficient for recovery-misuse classification because battle damage could otherwise create a false positive.

The v1 event contract intentionally does not accept a synthetic `NATIVE_TASK_ASSIGNMENT` event. Native task identity is not available merely because the project would find it useful.

## Metrics

### Threatened-front coverage

For every observer-safe threatened owned region, reuse the v0.2E geometric front envelope and count whether a controlled field army is within the project's two-turn geometric horizon.

Outputs:

- critical/threatened-front opportunity count;
- covered opportunity count;
- coverage rate;
- observed response latency;
- right-censored threats still uncovered at trace end;
- threats ending before observed coverage.

The two-turn horizon remains a project engineering hypothesis, not a discovered WH3 constant.

### Recovering-army offensive use

An offensive engagement enters the numerator only when:

1. the engagement is actually observed;
2. the actor is a controlled field army;
3. the engagement is labeled `OFFENSIVE` by the observation contract;
4. actor replenishment **measured at engagement** is below the existing project recovery threshold `0.65`.

Defensive engagements are not counted as offensive misuse. Missing engagement evidence cannot be converted into a safe/unsafe conclusion.

### Home-zone buffer proxy

A controlled army contributes to the reserve-capacity proxy only when it is:

- at or above the project recovery threshold;
- not observed in an engagement that turn;
- outside every currently threatened-front coverage set;
- within the project's two-turn geometric horizon of at least one owned region.

This is deliberately named a **home-zone buffer proxy**. It is not proof that native CAI deliberately maintains a strategic reserve.

### Directional target proxy and churn

For a controlled army visible in consecutive observations, v0.2J compares its geometric movement against currently observable strategic anchors:

- threatened owned regions (`DEFEND_REGION`);
- hostile regions (`ATTACK_REGION`);
- visible hostile forces (`ENGAGE_FORCE`).

If movement clearly closes distance to one anchor, the result receives a `DIRECTIONAL_TARGET_PROXY`. Equal/ambiguous approaches remain unresolved.

A target-proxy change is separated into:

- `UNEXPLAINED_DIRECTIONAL_REVERSAL_PROXY`; or
- `CONTEXT_EXPLAINED_RETARGET_PROXY` when, for example, a new local crisis appears or the old target is no longer observable.

This is movement interpretation, not native task telemetry.

## Explicit unavailable dimensions

The v0.2J output fixes the following fields:

- `internal_task_visibility = UNAVAILABLE`
- `assignment_exclusivity_visibility = UNAVAILABLE_FROM_TRAJECTORY_ONLY`
- `native_assignment_memory_visibility = UNAVAILABLE`
- `native_hysteresis_visibility = UNAVAILABLE`

No absence-of-failure argument may promote those labels.

## Adversarial matrix

`synthetic_lab/scenarios/native_cai_behavior_adversarial_matrix_v0.2J.json`

Nine deterministic cases cover:

1. covered front plus healthy rear-area buffer proxy;
2. recovering offensive engagement;
3. recovering defensive engagement excluded from misuse numerator;
4. persistent-target directional reversal;
5. crisis-driven retarget without false thrashing label;
6. stationary-position idle proxy without task-idle claim;
7. persistently uncovered right-censored front;
8. one-turn observed front response;
9. threat ending before coverage without false right-censoring.

Frozen result:

`synthetic_lab/results/native_cai_behavior_adversarial_matrix_v0.2J.json`

## Application boundary

v0.2J contains no runtime adapter and no order API. It is an evaluator contract only. It may later consume a separately verified read-only observation export, but it cannot itself collect privileged hidden state, mutate campaign state, or issue an order.

A future native correction proposal still requires the post-review falsification sequence:

`reproducible material failure -> narrow native DB intervention -> remeasurement -> narrower bounded correction -> only then consider project-owned planning`.
