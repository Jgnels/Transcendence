# Native CAI Reconciliation Workplan

**Date:** 2026-08-02  
**Current schema target:** RPFM schema commit `d12f59cb6de106d205f51b81739951adbc840c49` — `Updated wh3 schemas for patch 8.1` (2026-07-09).  
**Schema blob at current master:** `232216808ff5d38edd9e056c7828afdc1700d297` (Git blob SHA).  
**RPFM repository schema submodule observed before the update:** `229a393f8973b182458bedec8146cab4ef6d97fb`; 8.1 schema commit is one commit ahead and changes only `schema_wh3.ron` (+863/-2 lines).

## Priority table families

1. `cai_gds_task_generators_tables`
2. `cai_task_management_system_task_generator_groups_generators_junctions_tables`
3. `cai_task_management_system_task_generator_variable_group_junctions_tables`
4. `cai_task_management_system_task_generator_variables_tables`
5. `cai_task_management_system_variable_group_junctions_tables`
6. `cai_task_management_system_variables_tables`
7. `cai_variables_tables`
8. `cai_variables_overides_tables`
9. `cai_personalities_tables`
10. `cai_personality_strategic_components_tables`
11. `cai_personality_variables_tables`
12. `cai_personality_variable_set_junctions_tables`
13. `cai_personalities_budget_allocations_tables`
14. `cai_personalities_income_allocations_tables`
15. `cai_personality_faction_potential_modifiers_tables`
16. every present `cai_decision_*` family relevant to strategic policy
17. `cai_query_variable_set_junctions_tables`
18. `campaign_ai_manager_behaviour_junctions_tables`
19. `cdir_military_generator_template_ratios_tables`
20. `cdir_military_generator_unit_qualities_tables`

First decode target: `cai_task_management_system_task_generator_groups_generators_junctions_tables`, because it is the one family already observed across DeepWar, Hecleas and SFO. Shared presence alone does not prove row collision.

## Exact row-diff output

For each source and table preserve:
- schema/commit identity;
- RPFM-decoded definition version, field list/types/references, and effective primary-key fields;
- source pack/file identity and SHA-256;
- exported TSV/CSV SHA-256;
- field names/types and schema key information;
- row count;
- `ADDED_ROW`, `REMOVED_ROW`, `CHANGED_CELL`, `SAME_ROW`;
- cross-mod `ROW_KEY_OVERLAP` and `LOAD_ORDER_COLLISION_RISK` where proven;
- semantic category: `STRATEGIC_CAI`, `ECONOMY_BUDGET`, `FACTION_POTENTIAL_DIFFICULTY`, `RECRUITMENT_COMPOSITION`, `ENVIRONMENT_RULES`, `SCRIPTED_BYPASS`, `UNVERIFIED`.

## Official native facts already strong enough to guide the gate

Creative Assembly currently documents that:
- foreign-threat detection uses a query system plus an influence map;
- threat and force strength are different evaluations;
- task priority is distance-scaled in turns, with stance-aware movement and recruitment time considered;
- task generation can combine multiple generators;
- allocation pairs tasks and armies and performs another batching pass;
- sufficient force strength is a prerequisite for assignment to stronger enemies;
- Patch 8.1 added turn-since-campaign-start dependent priority control, de-prioritising late-game defensive tasks and slightly increasing tasks targeting enemy forces.

These facts establish substantial overlap with v0.2E-G at the responsibility level. They do **not** prove native reserves, recovery protection, assignment exclusivity, memory, hysteresis or multi-turn commitment.

## Patch 8.1 exposure question

Official existence: `PROVEN`.  
Exact public table/column/variable: `UNVERIFIED`.  
DB modder control: `UNVERIFIED`.  
Script control: `UNVERIFIED`.

Do not infer exposure simply because CA calls it a "mechanism".

## Current high-value mod acquisition targets

| Priority | Mod | Workshop ID | Current evidence status | Why |
|---:|---|---:|---|---|
| 1 | SFO: Grimhammer III | `2792731173` | existing extracted audit | target environment/profile |
| 2 | DeepWar AI | `2978779730` | existing PFH5 audit | narrow native CAI reference |
| 3 | Hecleas AI Overhaul | `2905096541` | existing PFH5 audit | broad CAI/diplomacy reference |
| 4 | AI Army Tasks and Strategy (Incata) | `2935815665` | pack not yet frozen | direct task/strategy prior art |
| 5 | AI Camping Settlements Fix 8.x | `3594429287` | current title/ID externally corroborated; pack not frozen | narrow idle/defense dwell fix |
| 6 | Campaign AI Tweaks (Sleepy) | `3485519396` | externally current through 2026-06; pack not frozen | potential/task behavior tuning |
| 7 | Better AI Army Builder | `3617312541` | externally current; pack not frozen | recruitment composition confounder/reference |

Workshop descriptions/community reports remain weaker than pack evidence.

## Owner work intentionally deferred

Do not launch WH3 for this gate yet. The next owner action is local artifact acquisition/export from RPFM and Workshop, not gameplay.

## Primary-key derivation

The owner exporter now asks RPFM to `DecodePackedFile` for each selected DB file and captures the serialized `TableInMemory.definition` plus `definition_patch`. RPFM's current schema implementation defines `Field.is_key` as primary-key membership and allows patches to override it. The exporter applies any `is_key` patch and emits `rpfm_table_key_spec.json` only when all decoded vanilla instances of a table agree. Conflicts or keyless observations remain unresolved; no key is guessed.

This reduces the local schema-byte requirement to provenance/semantic verification rather than forcing a separate hand-maintained key map.
