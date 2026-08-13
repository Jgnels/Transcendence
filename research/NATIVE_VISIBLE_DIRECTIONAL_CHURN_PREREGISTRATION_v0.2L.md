# Native Visible Directional Churn Preregistration — v0.2L

**Date:** 2026-08-02  
**Status:** `OFFLINE_PREREGISTERED / OWNER_RUN_NOT_YET_EXECUTED`  
**Policy authority:** `NO_ORDERS`  
**Application authority:** `PROHIBITED`

## Research question

Can a foreign AI field force that remains continuously visible to the human player exhibit **repeated strategic-direction oscillation under an unchanged player-visible context**, at a rate/pattern strong enough to justify a later bounded native-CAI tuning ablation?

This gate does **not** ask whether the engine has an internal task object, assignment memory, or hysteresis mechanism. Those remain unavailable. It asks only whether a conservative player-visible trajectory pathology can be observed reproducibly.

## Why this is the next falsification target

Official Campaign-AI material establishes that WH3 generates and evaluates tasks, modifies priorities by distance measured in turns, allocates tasks to assets, and performs batching. Patch 8.1 additionally introduced turn-dependent Campaign-AI priority control intended to reduce late-game defensive clustering/idling. These facts make a generic replacement allocator unjustified by default.

Sources:

- CA Patch 8.1 Release Notes: https://community.creative-assembly.com/total-war/total-war-warhammer/blogs/101
- CA Improving AI in Campaign — Part 2: https://community.creative-assembly.com/total-war/total-war-warhammer/blogs/69%20style%3Dbutton
- CA Hotfix 6.3.4 Campaign AI technical notes: https://community.creative-assembly.com/total-war/total-war-warhammer/forums/7-patch-notes-amp-announcements/threads/11820-total-war-warhammer-iii-hotfix-6-3-4
- WH3 scripting documentation for player-filtered foreign visibility: https://chadvandy.github.io/tw_modding_resources/WH3/scripting_doc.html

None of those sources documents project-equivalent multi-turn assignment commitment or reassignment hysteresis. That absence is an evidence gap, not proof of absence.

## Frozen primary endpoint

`REPEATED_STABLE_CONTEXT_REGION_OSCILLATION_CLUSTER`

The primary endpoint is intentionally much stricter than “direction changed.” A four-frame candidate requires all of the following:

1. the same foreign AI force remains player-visible for four consecutive local-player turns;
2. all three movement intervals produce a **unique visible-region directional proxy**;
3. the proxy pattern is `A -> B -> A`, where A and B are different visible regions;
4. both consecutive movement-heading changes are at least 120 degrees (`cosine <= -0.5`);
5. the exact set, ownership/faction, and coordinates of every **non-target player-visible anchor** remain unchanged across the four frames;
6. no privileged foreign-force enumeration is used.

One qualifying A→B→A episode is only:

`STABLE_OBSERVED_CONTEXT_REGION_ABA_OSCILLATION_CANDIDATE`

The preregistered primary signal requires **at least two non-overlapping qualifying episodes for the same actor and same two-region anchor pair**.

Example qualifying proxy sequence across seven turns:

`A -> B -> A | B -> A -> B`

The windows may share the boundary frame but may not share movement intervals.

## Why region anchors only

Moving armies are useful exploratory anchors but are excluded from the confirmatory endpoint. A target army can legitimately retarget because another army moves. Static region anchors reduce that ambiguity and make the primary detector harder, not easier, to trigger.

## Why exact observed-context stability is strict

Any movement of a non-target visible army, ownership change, visible-anchor appearance/disappearance, or coordinate change excludes the window from the primary denominator. This sacrifices sample size to reduce false-positive interpretation.

Even this strict rule does **not** establish true context stability. Hidden armies, hidden wars, native tasks, recruitment state, diplomatic state, and other engine internals can change outside player visibility.

Therefore a detected cluster remains:

`PLAYER_VISIBLE_REPEATED_DIRECTIONAL_OSCILLATION_REQUIRES_CAUSAL_REVIEW`

not:

`NATIVE_HYSTERESIS_FAILURE_PROVEN`.

## Primary interpretation rules

| Result | Allowed interpretation |
|---|---|
| >=1 repeated cluster | Repeated player-visible region-direction oscillation occurred under stable observed context; native tuning candidate may be elevated for a mechanistically related ablation |
| one A→B→A episode only | review candidate; not primary signal |
| no repeated cluster with eligible windows | no repeated signal observed in that exposure; not proof of good native hysteresis |
| zero eligible windows | insufficient exposure; no native-quality inference |
| actor leaves visibility | right-censored |
| ambiguous or unanchored movement | excluded from primary endpoint |
| nonconsecutive turns | excluded |
| observed context changes | excluded |

## Vanilla/SFO comparison contract

The eventual initial comparison is descriptive, not a significance test:

- exact-current vanilla + read-only Transcendence shadow probe;
- exact-current SFO + the same read-only shadow probe;
- same player faction and campaign setup;
- same observation protocol;
- exact executable/probe/SFO hashes bound in the owner manifest;
- raw eligible-window exposure reported for each profile;
- candidate and repeated-cluster counts reported separately.

No causal statement such as “SFO fixes churn” is allowed from one unmatched campaign pair. A profile difference may only nominate a **bounded native-row treatment** for a subsequent controlled ablation.

## Project-planner decision rule

Even a positive v0.2L result does **not** earn v0.2G application ownership.

The escalation ladder remains:

`observe repeated pathology -> identify plausible native row/mechanism -> preregister bounded native tuning -> compare -> bounded correction if needed -> project-owned planner only after repeated native+tuning falsification`

## Historical evidence result

The preserved owner-safe turns 4–7 were reprocessed under this frozen endpoint:

`research/runtime_evidence/PLAYER_VISIBLE_NATIVE_DIRECTIONAL_CHURN_REPROCESS_v0.2L.json`

Result:

- 0 eligible stable-context region windows;
- 0 A→B→A candidates;
- 0 repeated clusters.

This is a **limiting result only**. It contains insufficient primary-endpoint exposure and does not support a claim that native CAI has adequate hysteresis.

## Implemented evaluator

Pure SyntheticLab evaluator:

`synthetic_lab/transcendence_lab/native_churn.py`

Adversarial matrix:

- `synthetic_lab/scenarios/native_cai_visible_churn_adversarial_matrix_v0.2L.json`
- `synthetic_lab/results/native_cai_visible_churn_adversarial_matrix_v0.2L.json`

Runtime batch adapter:

`runtime_probe/tools/run_native_visible_churn.py`

Historical reprocessor:

`runtime_probe/tools/reprocess_native_visible_churn_evidence.py`

The new path does not import the v0.2F/v0.2G strategic assignment/commitment modules and contains no order adapter.
