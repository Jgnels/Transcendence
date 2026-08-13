# Patch 8.1 Campaign-AI Priority Mechanism — Evidence Reconciliation

**Date:** 2026-08-02  
**Authority:** `READ_ONLY_RESEARCH`

## Official fact

Creative Assembly Patch 8.1 states that a new mechanism controls Campaign-AI priorities as turns pass, with late-game defensive tasks reduced and enemy-force-targeting tasks increased. This is `OFFICIAL_GAME_FACT`.

Primary source: https://community.creative-assembly.com/total-war/total-war-warhammer/blogs/101-total-war-warhammer-iii-patch-8-1-release-notes

## Current local pack evidence

The owner’s current vanilla DB export contains:

- `wh3_combi_tms_generator_group_endgame_overrides`;
- a timed `DEFEND_OWN_REGIONS` row bound to `elapsed_rounds_bounded_lerp_to_0_at_30`;
- endgame enemy-force task priorities of 9–10;
- variable groups named `elapsed_rounds_bounded_lerp`, `elapsed_rounds_bounded_lerp_to_0_at_30`, `elapsed_rounds_bounded_lerp_to_0_5_at_30`, `timed_priority_boost_quick`, and `timed_priority_boost_instant`;
- task-generator variables controlling elapsed-round lerp and timed-priority activation.

Classification: `VERIFIED_MOD_SOURCE_OR_PACK_FACT` for the rows and names.

## Causal interpretation

`STRONG_INFERENCE`: these current DB rows are part of, or data configuration used by, the public turn-dependent-priority behavior described by CA.

What is **not** proven yet:

- that every listed row/group was newly introduced in 8.1;
- that the entire mechanism is DB-exposed rather than partly engine logic;
- the exact current schema primary keys/foreign keys for every row;
- whether other, unexported table families participate.

Those points remain `UNVERIFIED` pending a pre-8.1 row comparison and exact schema pin.

## Mod interaction from exact acquired rows

- DeepWar does not directly supply `wh3_combi_tms_generator_group_endgame_overrides` rows in the acquired table. It therefore inherits vanilla’s rows in this family unless another loaded pack supersedes them.
- SFO likewise has no row from that group in its 93-row selective override file.
- Hecleas carries the group and drastically changes its priorities.

## Impact on Transcendence

v0.2F’s phase-/pressure-dependent application priorities are **partially redundant at the responsibility level** with a current native system that already changes task priorities over time and exposes task-generator/variable-group surfaces to data.

Recommended disposition remains:

- v0.2F application controller: `REMOVE_AS_DEFAULT_CONTROLLER`;
- v0.2F metrics: `PROJECT_SHOULD_MEASURE`;
- native timed task-priority rows: `TUNABLE_NATIVE`;
- bounded correction: only after a controlled native-row ablation fails preregistered behavior metrics.
