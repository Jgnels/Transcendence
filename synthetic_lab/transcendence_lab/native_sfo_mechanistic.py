from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import json

from .canonical import digest
from .native_diagnostic_study import (
    APPLICATION_AUTHORITY,
    APPLICATION_ELIGIBLE,
    AUTHORITY,
    RESEARCH_VISIBILITY,
)

REGISTRY_CONTRACT = "NATIVE_CAI_SFO_MECHANISTIC_REGISTRY_V1"
ABLATION_REGISTRY_CONTRACT = "NATIVE_CAI_SFO_ABLATION_CANDIDATE_REGISTRY_V1"
DECISION_TABLE_CONTRACT = "NATIVE_CAI_SFO_POST_BENCHMARK_DECISION_TABLE_V1"

TASK_TABLE = "cai_task_management_system_task_generator_groups_generators_junctions_tables"
ALLOCATOR_TABLE = "cai_task_management_system_variables_tables"

VANILLA_TERRITORIAL_RATE = 0.270833
VANILLA_TERRITORIAL_LOO_MIN = 0.222222
VANILLA_TERRITORIAL_LOO_MAX = 0.317073
VANILLA_TERRITORIAL_REPEATED_FORCE_COUNT = 0
RECOVERY_POSITIVE_RATE_THRESHOLD = 0.20
RECOVERY_MIN_EXPOSURES = 10
TEMPORAL_MIN_ELIGIBLE_WINDOWS = 20

GENERIC_PRIMARY_GROUP = "wh3_combi_tms_generator_group_default"
GENERIC_PRIORITY_CANDIDATES = (
    "CAI_TMS_TASK_GENERATOR_ATTACK_ALL_ENEMY_FORCES",
    "CAI_TMS_TASK_GENERATOR_ATTACK_ALL_LOCAL_FORCES_SIZE_SCALED",
    "CAI_TMS_TASK_GENERATOR_ATTACK_ALL_ENEMY_SETTLEMENTS",
    "CAI_TMS_TASK_GENERATOR_ATTACK_NEIGHBOURING_WAR_REGIONS",
    "CAI_TMS_TASK_GENERATOR_WAR_COORDINATION_ATTACK_FORCES",
    "CAI_TMS_TASK_GENERATOR_WAR_COORDINATION_ATTACK_REGIONS",
)


def _authority_fields() -> dict[str, Any]:
    return {
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": APPLICATION_ELIGIBLE,
    }


def _sfo_mod(table: dict[str, Any]) -> dict[str, Any] | None:
    mods = table.get("mods", {})
    value = mods.get("sfo")
    return value if isinstance(value, dict) else None


def build_sfo_mechanistic_registry(row_diff: dict[str, Any]) -> dict[str, Any]:
    tables = row_diff.get("tables", {})
    sfo_tables: dict[str, dict[str, Any]] = {}
    for table_name, table in sorted(tables.items()):
        mod = _sfo_mod(table)
        if mod is None:
            continue
        changed = [row for row in mod.get("deltas", []) if row.get("status") == "OVERRIDE_CHANGED"]
        same = [row for row in mod.get("deltas", []) if row.get("status") == "OVERRIDE_SAME_AS_VANILLA"]
        sfo_tables[table_name] = {
            "rows_carried": int(mod.get("rows", len(changed) + len(same))),
            "changed_rows": len(changed),
            "same_as_vanilla_rows": len(same),
        }

    task_mod = _sfo_mod(tables.get(TASK_TABLE, {})) or {}
    changed_task = [row for row in task_mod.get("deltas", []) if row.get("status") == "OVERRIDE_CHANGED"]
    priority_rows: list[dict[str, Any]] = []
    group_counts: Counter[str] = Counter()
    generator_counts: Counter[str] = Counter()
    increases = 0
    decreases = 0
    for row in changed_task:
        change = row.get("changes", {}).get("priority")
        if not isinstance(change, dict):
            continue
        vanilla = float(change["vanilla"])
        mod = float(change["mod"])
        delta = mod - vanilla
        if delta > 0:
            increases += 1
        elif delta < 0:
            decreases += 1
        source = row.get("vanilla", row.get("mod", {}))
        group = str(source.get("group"))
        generator = str(source.get("generator"))
        group_counts[group] += 1
        generator_counts[generator] += 1
        priority_rows.append({
            "group": group,
            "generator": generator,
            "variable_group": source.get("variable_group"),
            "vanilla_priority": vanilla,
            "sfo_priority": mod,
            "delta": delta,
            "direction": "INCREASE" if delta > 0 else "DECREASE" if delta < 0 else "UNCHANGED",
        })

    allocator_mod = _sfo_mod(tables.get(ALLOCATOR_TABLE, {}))
    allocator_rows_carried = 0 if allocator_mod is None else int(allocator_mod.get("rows", 0))
    allocator_changed = 0 if allocator_mod is None else int(allocator_mod.get("counts", {}).get("OVERRIDE_CHANGED", 0))

    registry: dict[str, Any] = {
        "contract": REGISTRY_CONTRACT,
        "study_version": "v0.2P",
        **_authority_fields(),
        "source": {
            "row_diff_contract": row_diff.get("schema_version"),
            "row_diff_authority": row_diff.get("authority"),
            "key_status": row_diff.get("key_status"),
        },
        "captured_sfo_cai_footprint": {
            "tables_with_decoded_sfo_rows": sfo_tables,
            "decoded_table_family_count": len(sfo_tables),
            "allocator_table": {
                "table": ALLOCATOR_TABLE,
                "rows_carried": allocator_rows_carried,
                "changed_rows": allocator_changed,
                "direct_sfo_allocator_override_observed": allocator_changed > 0,
            },
            "task_priority_table": {
                "table": TASK_TABLE,
                "rows_carried": int(task_mod.get("rows", 0)),
                "changed_priority_rows": len(priority_rows),
                "same_as_vanilla_rows": int(task_mod.get("counts", {}).get("OVERRIDE_SAME_AS_VANILLA", 0)),
                "priority_increases": increases,
                "priority_decreases": decreases,
                "distinct_generator_groups_changed": len(group_counts),
                "distinct_generators_changed": len(generator_counts),
                "changed_rows": sorted(priority_rows, key=lambda r: (r["group"], r["generator"], str(r["variable_group"]))),
                "generator_change_counts": dict(sorted(generator_counts.items())),
                "group_change_counts": dict(sorted(group_counts.items())),
            },
        },
        "endpoint_mechanism_eligibility": {
            "recovery": {
                "sfo_task_priority_rows": "ELIGIBLE_FOR_REPLICATION_ONLY_IF_SFO_RECOVERY_DIFFERS; INDIRECT_AND_NONCAUSAL",
                "allocator_release_return_rows": "NOT_ELIGIBLE_TO_EXPLAIN_AN_SFO_DIFFERENCE_FROM_CAPTURED_SFO_CAI_DB_FOOTPRINT; NO_SFO_ALLOCATOR_OVERRIDE_OBSERVED",
                "other_sfo_systems": "UNRESOLVED_CONFOUNDERS; SFO_MODIFIES_MANY_CAMPAIGN_SYSTEMS",
            },
            "territorial_temporal_reversal": {
                "sfo_task_priority_rows": "ELIGIBLE_FOR_REPLICATION_NOMINATION_IF_DIRECTIONALLY_CONSISTENT_BENCHMARK_DIFFERENCE_IS_OBSERVED",
                "allocator_release_return_rows": "NOT_ELIGIBLE_TO_EXPLAIN_AN_SFO_DIFFERENCE_FROM_CAPTURED_SFO_CAI_DB_FOOTPRINT",
                "project_owned_assignment_hysteresis": "NOT_AUTHORIZED; NATIVE_FIRST RULE REMAINS",
            },
        },
        "interpretation_limits": [
            "Decoded SFO row presence is not causal proof of behavior.",
            "The captured SFO CAI footprint may be incomplete outside the decoded targeted table set.",
            "No SFO row is application-authorized by this registry.",
            "Absence of a decoded SFO allocator override rules out only that direct captured-DB attribution path; it does not rule out indirect SFO systems or native engine interactions.",
        ],
    }
    registry["registry_digest"] = digest(registry)
    return registry


def build_ablation_candidate_registry(mechanistic_registry: dict[str, Any]) -> dict[str, Any]:
    task = mechanistic_registry["captured_sfo_cai_footprint"]["task_priority_table"]
    by_key = {(row["group"], row["generator"]): row for row in task["changed_rows"]}
    candidates: list[dict[str, Any]] = []
    for rank, generator in enumerate(GENERIC_PRIORITY_CANDIDATES, start=1):
        row = by_key.get((GENERIC_PRIMARY_GROUP, generator))
        if row is None:
            continue
        candidates.append({
            "rank": rank,
            "candidate_id": f"SFO_DEFAULT_{generator}",
            "table": TASK_TABLE,
            "group": row["group"],
            "generator": row["generator"],
            "variable_group": row["variable_group"],
            "vanilla_priority": row["vanilla_priority"],
            "sfo_priority": row["sfo_priority"],
            "delta": row["delta"],
            "evidence_class": "VERIFIED_MOD_SOURCE_OR_PACK_FACT_FOR_ROW_DELTA; HYPOTHESIS_FOR_BEHAVIORAL_RELEVANCE",
            "status": "DORMANT_REPLICATION_ONLY_NOT_EARNED",
            "eligible_endpoint": "TERRITORIAL_TEMPORAL_REVERSAL",
            "why_ranked": "Generic/default strategic attack-task priority; broad applicability is more plausible than faction-special rows, but actual generator activation for the observed cohort is not proven.",
            "application_eligible": False,
        })
    registry: dict[str, Any] = {
        "contract": ABLATION_REGISTRY_CONTRACT,
        "study_version": "v0.2P",
        **_authority_fields(),
        "mechanistic_registry_digest": mechanistic_registry["registry_digest"],
        "candidate_policy": {
            "status_before_sfo_data": "DORMANT_REPLICATION_ONLY_NOT_EARNED",
            "activation_rule": "A fresh matched SFO cohort must first produce a directionally compatible, exposure-sufficient benchmark nomination and then be replicated before any single-row ablation is authorized.",
            "copying_sfo_rows_wholesale": "PROHIBITED",
            "multirow_application": "PROHIBITED_BEFORE_SINGLE_ROW_OR_MINIMAL_MECHANISM_ABLATION",
        },
        "temporal_candidates": candidates,
        "recovery_candidates": [],
        "recovery_note": "No recovery row candidate is earned. SFO has no decoded direct allocator-variable override, and vanilla recovery did not meet the preregistered positive signal threshold.",
        "dormant_alternative_prior_art": {
            "deepwar_and_hecleas_allocator_rows": "RETAIN_FOR_FUTURE_TRIANGULATION_ONLY; NOT_ELIGIBLE_TO_EXPLAIN AN SFO DIFFERENCE AND NOT EARNED BY CURRENT VANILLA RECOVERY RESULT"
        },
    }
    registry["registry_digest"] = digest(registry)
    return registry


def post_sfo_decision_table() -> dict[str, Any]:
    table: dict[str, Any] = {
        "contract": DECISION_TABLE_CONTRACT,
        "study_version": "v0.2P",
        **_authority_fields(),
        "frozen_before_fresh_sfo_owner_data": True,
        "vanilla_reference": {
            "territorial_candidate_rate": VANILLA_TERRITORIAL_RATE,
            "territorial_leave_one_faction_out_min": VANILLA_TERRITORIAL_LOO_MIN,
            "territorial_leave_one_faction_out_max": VANILLA_TERRITORIAL_LOO_MAX,
            "territorial_repeated_force_count": VANILLA_TERRITORIAL_REPEATED_FORCE_COUNT,
            "note": "Leave-one-faction-out range is a descriptive cluster-sensitivity envelope, not a confidence interval or p-value.",
        },
        "temporal_branches": [
            {
                "branch": "INSUFFICIENT_EXPOSURE",
                "condition": "territorial_eligible_windows < 20",
                "action": "EXTEND_OR_REDESIGN_ACQUISITION_ONLY",
                "mechanistic_nomination": "NONE",
            },
            {
                "branch": "REPEATED_TERRITORIAL_SIGNAL",
                "condition": "territorial_eligible_windows >= 20 AND repeated_reversal_force_count > 0",
                "action": "POSSIBLE_SFO_WORSENING_OR_SPECIAL_POLICY; CAUSAL_REVIEW_AND_REPLICATION",
                "mechanistic_nomination": "DO_NOT_COPY_SFO_PRIORITY_INCREASES; THEY ARE DIRECTIONALLY_SUSPECT_UNTIL_CAUSAL_REVIEW",
            },
            {
                "branch": "LOWER_THAN_VANILLA_CLUSTER_ENVELOPE",
                "condition": "territorial_eligible_windows >= 20 AND repeated_reversal_force_count == 0 AND reversal_candidate_rate < 0.222222",
                "action": "DESCRIPTIVE_IMPROVEMENT_NOMINATION; REPLICATE_MATCHED_PROFILE_BEFORE_ROW_ABLATION",
                "mechanistic_nomination": "SFO_TASK_PRIORITY_INCREASES_REPLICATION_ELIGIBLE; NO_CAUSAL_ROW_CLAIM",
            },
            {
                "branch": "WITHIN_VANILLA_CLUSTER_ENVELOPE",
                "condition": "territorial_eligible_windows >= 20 AND repeated_reversal_force_count == 0 AND 0.222222 <= reversal_candidate_rate <= 0.317073",
                "action": "NO_TEMPORAL_MECHANISTIC_NOMINATION",
                "mechanistic_nomination": "NONE",
            },
            {
                "branch": "HIGHER_THAN_VANILLA_CLUSTER_ENVELOPE",
                "condition": "territorial_eligible_windows >= 20 AND repeated_reversal_force_count == 0 AND reversal_candidate_rate > 0.317073",
                "action": "DESCRIPTIVE_WORSENING_NOMINATION; REPLICATE_AND_CAUSAL_REVIEW",
                "mechanistic_nomination": "DO_NOT_COPY_SFO_PRIORITY_INCREASES",
            },
        ],
        "recovery_branches": [
            {
                "branch": "INSUFFICIENT_RECOVERY_EXPOSURE",
                "condition": "recovering_army_turn_count < 10",
                "action": "EXTEND_ONLY",
                "mechanistic_nomination": "NONE",
            },
            {
                "branch": "SFO_RECOVERY_POSITIVE_SIGNAL",
                "condition": "recovering_army_turn_count >= 10 AND recovering_attacker_side_army_turn_count >= 2 AND recovering_attacker_side_rate >= 0.20",
                "action": "POSSIBLE_WORSENING_RELATIVE_TO_VANILLA_NEGATIVE_COHORT; REPLICATE_AND_CAUSAL_REVIEW",
                "mechanistic_nomination": "SFO_TASK_PRIORITIES_MAY_BE_RELEVANT_INDIRECTLY; SFO_ALLOCATOR_RELEASE_RETURN_ROWS_ARE_NOT_A_DIRECT_EXPLANATION_BECAUSE_NONE_WERE_OVERRIDDEN",
            },
            {
                "branch": "SFO_RECOVERY_NO_PREREGISTERED_SIGNAL",
                "condition": "recovering_army_turn_count >= 10 AND preregistered positive recovery condition is false",
                "action": "NO_RECOVERY_INTERVENTION_EARNED",
                "mechanistic_nomination": "NONE",
            },
        ],
        "global_rules": [
            "No single SFO-vs-vanilla cohort comparison is a randomized causal estimate.",
            "No p-value is authorized from overlapping army windows treated as independent samples.",
            "Any mechanistic nomination requires replication before a row ablation.",
            "Any row ablation must be minimal, native-first, separately preregistered, and application-ineligible until its own gate passes.",
            "No branch revives v0.2G/v0.2I or authorizes project-owned orders.",
        ],
    }
    table["decision_table_digest"] = digest(table)
    return table


def choose_temporal_branch(eligible: int, candidates: int, repeated: int) -> dict[str, Any]:
    rate = None if eligible <= 0 else round(candidates / eligible, 6)
    if eligible < TEMPORAL_MIN_ELIGIBLE_WINDOWS:
        branch = "INSUFFICIENT_EXPOSURE"
        action = "EXTEND_OR_REDESIGN_ACQUISITION_ONLY"
        nomination = "NONE"
    elif repeated > 0:
        branch = "REPEATED_TERRITORIAL_SIGNAL"
        action = "POSSIBLE_SFO_WORSENING_OR_SPECIAL_POLICY; CAUSAL_REVIEW_AND_REPLICATION"
        nomination = "DO_NOT_COPY_SFO_PRIORITY_INCREASES"
    elif rate is not None and rate < VANILLA_TERRITORIAL_LOO_MIN:
        branch = "LOWER_THAN_VANILLA_CLUSTER_ENVELOPE"
        action = "DESCRIPTIVE_IMPROVEMENT_NOMINATION; REPLICATION_REQUIRED"
        nomination = "SFO_TASK_PRIORITY_INCREASES_REPLICATION_ELIGIBLE"
    elif rate is not None and rate > VANILLA_TERRITORIAL_LOO_MAX:
        branch = "HIGHER_THAN_VANILLA_CLUSTER_ENVELOPE"
        action = "DESCRIPTIVE_WORSENING_NOMINATION; REPLICATION_AND_CAUSAL_REVIEW_REQUIRED"
        nomination = "DO_NOT_COPY_SFO_PRIORITY_INCREASES"
    else:
        branch = "WITHIN_VANILLA_CLUSTER_ENVELOPE"
        action = "NO_TEMPORAL_MECHANISTIC_NOMINATION"
        nomination = "NONE"
    return {"branch": branch, "rate": rate, "action": action, "mechanistic_nomination": nomination}


def choose_recovery_branch(exposures: int, attacker_reentries: int) -> dict[str, Any]:
    rate = None if exposures <= 0 else round(attacker_reentries / exposures, 6)
    if exposures < RECOVERY_MIN_EXPOSURES:
        branch = "INSUFFICIENT_RECOVERY_EXPOSURE"
        action = "EXTEND_ONLY"
        nomination = "NONE"
    elif attacker_reentries >= 2 and rate is not None and rate >= RECOVERY_POSITIVE_RATE_THRESHOLD:
        branch = "SFO_RECOVERY_POSITIVE_SIGNAL"
        action = "POSSIBLE_WORSENING_RELATIVE_TO_VANILLA_NEGATIVE_COHORT; REPLICATION_AND_CAUSAL_REVIEW_REQUIRED"
        nomination = "TASK_PRIORITIES_INDIRECTLY_ELIGIBLE; DIRECT_SFO_ALLOCATOR_ATTRIBUTION_NOT_ELIGIBLE"
    else:
        branch = "SFO_RECOVERY_NO_PREREGISTERED_SIGNAL"
        action = "NO_RECOVERY_INTERVENTION_EARNED"
        nomination = "NONE"
    return {"branch": branch, "rate": rate, "action": action, "mechanistic_nomination": nomination}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
