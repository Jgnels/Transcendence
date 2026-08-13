# Native CAI Reconciliation Gate — Execution Plan

## Phase 0 — Preserve and pin
DONE in this bundle:
- freeze all external reports verbatim;
- bind them to exact SHA-256 hashes;
- bind the review to owner-validated v0.2I-r3 baseline;
- record durable corrections/retractions;
- pin current observed schema blob identity.

## Phase 1 — Schema and vanilla row acquisition
Highest-value next evidence.

Acquire the exact pinned `schema_wh3.ron` bytes and current vanilla WH3 DB rows for these families first:
1. cai_gds_task_generators_tables
2. cai_task_management_system_task_generator_groups_generators_junctions_tables
3. cai_task_management_system_task_generator_variable_group_junctions_tables
4. cai_task_management_system_task_generator_variables_tables
5. cai_task_management_system_variable_group_junctions_tables
6. cai_task_management_system_variables_tables
7. cai_variables_tables
8. cai_variables_overides_tables
9. cai_personalities_tables
10. cai_personality_strategic_components_tables
11. cai_personality_variables_tables
12. cai_personality_variable_set_junctions_tables
13. cai_personalities_budget_allocations_tables
14. cai_personalities_income_allocations_tables
15. cai_personality_faction_potential_modifiers_tables
16. cai_decision_* families
17. cai_query_variable_set_junctions_tables
18. campaign_ai_manager_behaviour_junctions_tables
19. cdir_military_generator_template_ratios_tables
20. cdir_military_generator_unit_qualities_tables

Output needed per table:
- schema version;
- primary key(s);
- foreign-key relationships;
- field names/types/descriptions;
- vanilla row count;
- canonical TSV/CSV export + SHA-256.

## Phase 2 — Exact mod row diffs
Use same schema and normalization for each pack.
Priority order:
1. SFO (highest-priority project profile)
2. DeepWar
3. Hecleas
4. Incata AI Army Tasks and Strategy, if obtainable
5. AI Camping Settlements Fix
6. Campaign AI Tweaks
7. high-value recruitment/construction/diplomacy mods

For each table/key:
- ADDED_ROW
- REMOVED_ROW
- CHANGED_CELL
- SAME_ROW
- TABLE_FAMILY_OVERLAP_ONLY
- ROW_KEY_OVERLAP
- LOAD_ORDER_COLLISION_RISK
- SEMANTIC_INTERACTION_POSSIBLE

Separate strategic reasoning from confounders:
- STRATEGIC_CAI
- ECONOMY_BUDGET
- FACTION_POTENTIAL_DIFFICULTY
- RECRUITMENT_COMPOSITION
- ENVIRONMENT_RULES
- SCRIPTED_BYPASS

## Phase 3 — Patch 8.1 priority mechanism
Preserve official existence as fact, then determine exposure:
- DB_EXPOSED
- SCRIPT_EXPOSED
- ENGINE_INTERNAL
- UNVERIFIED

Do not infer table exposure from the official phrase "new mechanism".

## Phase 4 — Responsibility reconciliation
Map each Transcendence responsibility to:
- ALREADY_NATIVE
- TUNABLE_NATIVE
- SCRIPT_CORRECTABLE
- PROJECT_SHOULD_MEASURE
- PROJECT_MUST_OWN
- UNAVAILABLE_OR_UNVERIFIED

No application-control path is restored merely because a project implementation is cleaner or more explainable.

## Phase 5 — Only then owner live ablation
Owner work should be minimized and batched.
Design observable tests from army positions, stances, replenishment, battles/sieges, region changes, diplomacy and visible threat state. Do not require hidden native task IDs/priorities unless an API has first been proven to expose them.
