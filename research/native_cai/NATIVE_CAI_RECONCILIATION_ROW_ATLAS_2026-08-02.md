# WH3 8.1 Native CAI Row Atlas — Owner-Pack Reconciliation

**Date:** 2026-08-02  
**Authority:** `READ_ONLY_RESEARCH`  
**Application:** `PROHIBITED`  
**Status:** partial row-level gate result from owner-installed vanilla + SFO + DeepWar + Hecleas evidence.

## Executive finding

The actual installed rows materially strengthen the native-first architecture. Current vanilla WH3 exposes task-priority, allocator distance/recruitment/release-return, timed variable-group, threat/strength-player-multiplier, campaign override and manager-behaviour data that overlaps responsibilities previously modeled in v0.2F/v0.2G. The evidence does **not** prove native reserves, recovery protection, exclusivity, assignment memory or hysteresis. Those remain evaluator questions / engine-internal unknowns.

## Exact decoded table coverage

| Table | Vanilla rows | Mod reconciliation |
|---|---:|---|
| `cai_variables_tables` | 266 | deepwar: 36 changed / 16 same / 0 mod-only; hecleas: 77 changed / 189 same / 0 mod-only |
| `cai_task_management_system_variables_tables` | 11 | deepwar: 6 changed / 5 same / 0 mod-only; hecleas: 10 changed / 1 same / 0 mod-only |
| `cai_task_management_system_variable_group_junctions_tables` | 14 | deepwar: 2 changed / 0 same / 2 mod-only; hecleas: 3 changed / 1 same / 0 mod-only |
| `cai_task_management_system_task_generator_variables_tables` | 14 | deepwar: 4 changed / 0 same / 0 mod-only; hecleas: 6 changed / 4 same / 0 mod-only |
| `cai_task_management_system_task_generator_variable_group_junctions_tables` | 22 | deepwar: 3 changed / 4 same / 0 mod-only; hecleas: 3 changed / 7 same / 0 mod-only |
| `cai_task_management_system_task_generator_groups_generators_junctions_tables` | 475 | deepwar: 28 changed / 438 same / 2 mod-only; hecleas: 439 changed / 36 same / 0 mod-only; sfo: 88 changed / 5 same / 0 mod-only |
| `cai_variables_overides_tables` | 30 | hecleas: 30 changed / 0 same / 0 mod-only |
| `cai_personality_variable_set_junctions_tables` | 74 | hecleas: 40 changed / 34 same / 0 mod-only |
| `campaign_ai_manager_behaviour_junctions_tables` | 17 | hecleas: 7 changed / 10 same / 0 mod-only |

`OVERRIDE_CHANGED` means a mod supplies the same decoded key with changed values. `OVERRIDE_SAME_AS_VANILLA` means the mod redundantly carries a row. `MOD_ONLY_ROW` means the mod adds a key not present in the exported vanilla table. A vanilla row absent from a mod is **inherited**, not deleted.

## Native allocator variables: exact current local rows

Current vanilla `cai_task_management_system_variables_tables` contains 11 allocator variables. The names themselves establish that native CAI has explicit allocator configuration for task-priority distance scaling, fresh-army recruitment thresholds, release/return thresholds, and recruiting/non-recruiting distance horizons.

| Variable | Vanilla | DeepWar | Hecleas |
|---|---:|---:|---:|
| `ALLOCATOR_PRE_SCORING_TASK_PRIORITY_DISTANCE_SCALING_NO_SCALING_WITHIN_TURNS_DISTANCE` | 2 | 3 | 1 |
| `ALLOCATOR_PRE_SCORING_TASK_PRIORITY_DISTANCE_SCALING_SCALE_MULTIPLES_OF_NO_SCALING_DISTANCE_BY_POWER` | 1 | 1 | 1 |
| `ALLOCATOR_RECRUIT_NEW_ARMY_UNIT_THRESHOLD` | 16 | 12 | 14 |
| `ALLOCATOR_RELEASE_FORCES_TO_AGGRESSIVE_ACTION_MORALE_THRESHOLD` | 0 | 0 | 0.5 |
| `ALLOCATOR_RELEASE_FORCES_TO_AGGRESSIVE_ACTION_UNITS_THRESHOLD` | 9 | 12 | 12 |
| `ALLOCATOR_REQUIRE_FORCES_TO_RETURN_ON_POST_RELEASE_MORAL_THRESHOLD` | 0 | 0 | 0.5 |
| `ALLOCATOR_REQUIRE_FORCES_TO_RETURN_ON_POST_RELEASE_UNITS_THRESHOLD` | 8 | 8 | 7 |
| `ALLOCATOR_SCORING_DISTANCE_SCALING_RETAINED_MINIMUM_SCORE_PROPORTION_NONRECRUITING` | 0.2 | 0.1 | 0.15 |
| `ALLOCATOR_SCORING_DISTANCE_SCALING_RETAINED_MINIMUM_SCORE_PROPORTION_RECRUITING` | 0.1 | 0.05 | 0.05 |
| `ALLOCATOR_SCORING_DISTANCE_SCALING_TIME_TO_TARGET_IN_ROUNDS_UPPER_BOUND_NONRECRUITING` | 5 | 6 | 6 |
| `ALLOCATOR_SCORING_DISTANCE_SCALING_TIME_TO_TARGET_IN_ROUNDS_UPPER_BOUND_RECRUITING` | 4 | 4 | 3 |

### Architectural meaning

- `VERIFIED_MOD_SOURCE_OR_PACK_FACT`: Native allocation is not merely an opaque task-to-army black box; current DB data exposes concrete allocator policy knobs that experienced mods tune instead of replacing the allocator.
- `INFERENCE`: This makes v0.2G’s independent Euclidean allocator even harder to justify as the default application allocator because it would bypass native configuration that already incorporates turn-distance/recruitment policy.
- `UNVERIFIED`: These rows do not establish native exclusivity, reserve policy, recovery protection, multi-turn commitment or hysteresis.

## Patch-8.1-relevant task-priority rows

Current vanilla contains generator group `wh3_combi_tms_generator_group_endgame_overrides` with the following decoded rows:

| Generator | Variable group | Priority |
|---|---|---:|
| `CAI_TMS_GDS_TASK_GENERATOR_DEFEND_OWN_REGIONS` | `NULL` | 0 |
| `CAI_TMS_GDS_TASK_GENERATOR_DEFEND_OWN_REGIONS` | `elapsed_rounds_bounded_lerp_to_0_at_30` | 1 |
| `CAI_TMS_TASK_GENERATOR_ACTIVELY_DEFEND_CAPITAL` | `NULL` | 0.1 |
| `CAI_TMS_TASK_GENERATOR_ATTACK_ALL_ENEMY_FORCES` | `NULL` | 9 |
| `CAI_TMS_TASK_GENERATOR_ATTACK_ALL_ENEMY_FORCES_NEAR_RECENTLY_LOST_REGIONS` | `NULL` | 10 |
| `CAI_TMS_TASK_GENERATOR_ATTACK_ALL_ENEMY_MAIN_THREAT_FORCES` | `NULL` | 10 |
| `CAI_TMS_TASK_GENERATOR_ATTACK_ALL_ENEMY_SETTLEMENTS_IF_HAVENT_EXPANDED_RECENTLY` | `timed_priority_boost_quick` | 9 |
| `CAI_TMS_TASK_GENERATOR_ATTACK_ALL_LOCAL_FORCES_SIZE_SCALED` | `NULL` | 9 |

The same current vanilla table also binds task generators to time-dependent variable groups including `elapsed_rounds_bounded_lerp`, `elapsed_rounds_bounded_lerp_to_0_at_30`, `timed_priority_boost_quick`, and `timed_priority_boost_instant`.

### Prior-art behavior in this exact family

- DeepWar: 468 rows carried; 28 exact-key value changes, 438 rows identical to vanilla, 2 mod-only rows under the provisional composite key.
- Hecleas: 475 rows carried; 439 exact-key changes and only 36 identical under the provisional key. This is an extremely broad retune of the same native task-generator junction surface.
- SFO: 93 selective rows; 88 change current vanilla priorities and 5 are identical.
- Neither the acquired DeepWar nor SFO payload directly supplies rows in `wh3_combi_tms_generator_group_endgame_overrides`; therefore those current vanilla rows remain inherited when those mods are loaded unless another source overrides them.
- Hecleas does directly override that group and raises its values very substantially (for example enemy-force priorities into roughly the 90s and defensive rows into the 25–30 range).

## Current anti-player/fairness surface

Current vanilla `cai_personality_variable_set_junctions_tables` contains explicit player-specific variables:

- `ai_threat_score_personality_multiplier_player`
- `coordinator_player_strength_multiplier`

Observed current vanilla values include 0.9 on easy, 1.1 on hard, 1.15 on very hard and 1.2 on legendary for multiple default/chaos/elite variable sets. This is stronger evidence than relying on historical beta-blog numbers because it comes from the owner’s current installed vanilla DB payload.

Hecleas carries all 74 rows in this table and changes 40; many player threat/strength multipliers are flattened upward to `1.2`. This demonstrates how apparent “AI intelligence” can change through player-specific assessment parameters rather than new planning logic.

## Global CAI variable prior art

`cai_variables_tables` has 266 vanilla rows. DeepWar carries 52 rows and changes 36 of those; Hecleas carries all 266 and changes 77. Examples of directly exposed strategic controls include:

- attack-all-enemy-settlements after N rounds without expansion;
- max-priority ramp time for the above behavior;
- human-horde targeting by round and distance;
- global enemy threat modifiers;
- strategic-stance human weighting;
- safe-path strength modifiers.

## Corrected DeepWar finding

`cai_personalities_tables`: DeepWar carries a 227-row / ~175 KB table file, but after removing the DB header its payload is **byte-identical** to vanilla. The earlier inference “large file means broad personality rework” is therefore superseded. Table/file presence is not evidence of behavioral change.

## Current limitations

- The exact pinned `schema_wh3.ron` bytes were not captured by the owner acquisition (`selected_schema_exact=false`).
- The task-generator junction composite key `(group, generator, variable_group)` is strongly supported by zero duplicate keys across all 475 vanilla rows and the observed duplicate-generator/alternate-variable-group pattern, but remains `INFERENCE` until exact current schema `is_key` metadata is pinned.
- Several other acquired table families remain binary inventory-only because their exact current field definitions were not pinned in this pass. Their existence/row counts are evidence of surface area, but their row semantics are not guessed.
- Incata and narrow AI packs were not installed locally, so they are not included in exact pack-row diffs yet.
