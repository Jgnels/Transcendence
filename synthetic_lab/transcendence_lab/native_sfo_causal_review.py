from __future__ import annotations

from collections import Counter
from typing import Any

from .canonical import digest
from .native_diagnostic_study import (
    APPLICATION_AUTHORITY,
    APPLICATION_ELIGIBLE,
    AUTHORITY,
    RESEARCH_VISIBILITY,
)

CAUSAL_REVIEW_CONTRACT = "NATIVE_CAI_SFO_CAUSAL_COMPOSITION_REVIEW_V1"
REPLICATION_POLICY_CONTRACT = "NATIVE_CAI_SFO_REPLICATION_POLICY_V1"
VANILLA_ENVELOPE_MIN = 0.222222
VANILLA_ENVELOPE_MAX = 0.317073
TEMPORAL_MIN_ELIGIBLE_WINDOWS = 20


def _authority_fields() -> dict[str, Any]:
    return {
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": APPLICATION_ELIGIBLE,
    }


def _shape(window: dict[str, Any]) -> str:
    regions = list(window.get("regions", []))
    if len(regions) != 3:
        return "MALFORMED"
    a, b, c = regions
    if a == c and a != b:
        return "ABA_REGION"
    if a == b == c:
        return "SAME_REGION"
    if len({a, b, c}) == 3:
        return "THREE_REGIONS"
    return "OTHER"


def _faction_map(cluster: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["faction"]): row for row in cluster.get("faction_rows", [])}


def _aggregate_for_factions(cluster: dict[str, Any], factions: set[str]) -> dict[str, Any]:
    rows = _faction_map(cluster)
    eligible = sum(int(rows[f]["eligible_windows"]) for f in factions if f in rows)
    candidates = sum(int(rows[f]["reversal_candidates"]) for f in factions if f in rows)
    return {
        "eligible_windows": eligible,
        "reversal_candidates": candidates,
        "reversal_candidate_rate": None if eligible == 0 else round(candidates / eligible, 6),
    }


def build_causal_review(sfo_result: dict[str, Any], vanilla_cluster_reference: dict[str, Any]) -> dict[str, Any]:
    sfo_cluster = sfo_result["territorial_cluster_diagnostics"]
    vanilla_cluster = vanilla_cluster_reference["cluster_diagnostics"]
    sfo_rows = _faction_map(sfo_cluster)
    vanilla_rows = _faction_map(vanilla_cluster)
    sfo_factions = set(sfo_rows)
    vanilla_factions = set(vanilla_rows)
    shared = sfo_factions & vanilla_factions
    union = sfo_factions | vanilla_factions

    shared_sfo = _aggregate_for_factions(sfo_cluster, shared)
    shared_vanilla = _aggregate_for_factions(vanilla_cluster, shared)
    aggregate_sfo_rate = float(sfo_cluster["reversal_candidate_rate"])
    aggregate_vanilla_rate = float(vanilla_cluster["reversal_candidate_rate"])
    shared_sfo_rate = shared_sfo["reversal_candidate_rate"]
    shared_vanilla_rate = shared_vanilla["reversal_candidate_rate"]

    aggregate_direction = "SFO_HIGHER" if aggregate_sfo_rate > aggregate_vanilla_rate else "SFO_LOWER" if aggregate_sfo_rate < aggregate_vanilla_rate else "EQUAL"
    if shared_sfo_rate is None or shared_vanilla_rate is None:
        shared_direction = "UNAVAILABLE"
    else:
        shared_direction = "SFO_HIGHER" if shared_sfo_rate > shared_vanilla_rate else "SFO_LOWER" if shared_sfo_rate < shared_vanilla_rate else "EQUAL"

    sfo_shapes = Counter(_shape(row) for row in sfo_cluster.get("candidate_windows", []))
    vanilla_shapes = Counter(_shape(row) for row in vanilla_cluster.get("candidate_windows", []))

    loo = sfo_cluster.get("leave_one_faction_out", {})
    loo_min = loo.get("rate_min")
    loo_max = loo.get("rate_max")
    all_single_faction_deletions_above_vanilla_envelope = (
        loo_min is not None and float(loo_min) > VANILLA_ENVELOPE_MAX
    )

    max_share = sfo_cluster.get("candidate_concentration", {}).get("max_faction_candidate_share")
    candidate_faction = None
    candidate_faction_count = -1
    for row in sfo_cluster.get("faction_rows", []):
        count = int(row.get("reversal_candidates", 0))
        if count > candidate_faction_count:
            candidate_faction = row.get("faction")
            candidate_faction_count = count
    without_top = None
    if candidate_faction is not None:
        remaining_e = int(sfo_cluster["eligible_windows"]) - int(sfo_rows[candidate_faction]["eligible_windows"])
        remaining_c = int(sfo_cluster["reversal_candidates"]) - int(sfo_rows[candidate_faction]["reversal_candidates"])
        without_top = {
            "excluded_faction": candidate_faction,
            "remaining_eligible_windows": remaining_e,
            "remaining_reversal_candidates": remaining_c,
            "reversal_candidate_rate": None if remaining_e <= 0 else round(remaining_c / remaining_e, 6),
        }

    direction_reversal = (
        aggregate_direction == "SFO_HIGHER" and shared_direction == "SFO_LOWER"
    ) or (
        aggregate_direction == "SFO_LOWER" and shared_direction == "SFO_HIGHER"
    )

    review: dict[str, Any] = {
        "contract": CAUSAL_REVIEW_CONTRACT,
        "study_version": "v0.2Q",
        **_authority_fields(),
        "source": {
            "sfo_result_digest": sfo_result.get("result_digest"),
            "sfo_decision_table_digest": sfo_result.get("precommitted_post_sfo_decision", {}).get("decision_table_digest"),
            "vanilla_cluster_reference_digest": vanilla_cluster_reference.get("reference_digest"),
        },
        "frozen_v0_2p_decision_preserved": sfo_result.get("precommitted_post_sfo_decision"),
        "aggregate_robustness": {
            "sfo_territorial_rate": aggregate_sfo_rate,
            "vanilla_territorial_rate": aggregate_vanilla_rate,
            "sfo_leave_one_faction_out_min": loo_min,
            "sfo_leave_one_faction_out_max": loo_max,
            "all_single_faction_deletions_remain_above_vanilla_envelope": all_single_faction_deletions_above_vanilla_envelope,
            "max_faction_candidate_share": max_share,
            "top_candidate_faction": candidate_faction,
            "top_candidate_faction_count": candidate_faction_count,
            "sfo_without_top_candidate_faction": without_top,
        },
        "campaign_composition_review": {
            "sfo_eligible_faction_count": len(sfo_factions),
            "vanilla_eligible_faction_count": len(vanilla_factions),
            "shared_eligible_faction_count": len(shared),
            "union_eligible_faction_count": len(union),
            "faction_jaccard_overlap": None if not union else round(len(shared) / len(union), 6),
            "shared_factions": sorted(shared),
            "shared_faction_sfo": shared_sfo,
            "shared_faction_vanilla": shared_vanilla,
            "aggregate_direction": aggregate_direction,
            "shared_faction_direction": shared_direction,
            "direction_reversal_under_shared_faction_restriction": direction_reversal,
        },
        "candidate_geometry_review": {
            "sfo_candidate_shape_counts": dict(sorted(sfo_shapes.items())),
            "vanilla_candidate_shape_counts": dict(sorted(vanilla_shapes.items())),
            "note": "Geometry classes are descriptive only and do not identify native task identity or causation.",
        },
        "adjudication": {
            "formal_v0_2p_branch": sfo_result.get("precommitted_post_sfo_decision", {}).get("temporal", {}).get("branch"),
            "formal_v0_2p_action": sfo_result.get("precommitted_post_sfo_decision", {}).get("temporal", {}).get("action"),
            "causal_attribution_status": "BLOCKED_BY_CAMPAIGN_COMPOSITION_INSTABILITY",
            "native_row_ablation_earned": False,
            "copy_sfo_priority_increases": "PROHIBITED",
            "next_gate": "FRESH_SFO_REPLICATION_FIRST; FRESH_VANILLA_REPLICATION_ONLY_IF_ELEVATED_SFO_AGGREGATE_REPLICATES",
            "reason": (
                "The aggregate SFO rate is elevated and robust to deleting any single SFO faction, but only a small subset of eligible factions overlaps across campaigns and the shared-faction comparison reverses direction. "
                "The one-vs-one campaign comparison therefore cannot identify a profile-level causal effect or a row-level mechanism."
            ),
        },
        "interpretation_limits": [
            "The v0.2P descriptive worsening branch remains valid and is not rewritten by this causal review.",
            "Shared-faction restriction is post-result causal review, not a confirmatory endpoint.",
            "Different campaigns expose different faction/force compositions; one campaign per profile cannot separate profile effect from composition effect.",
            "No p-value over overlapping trajectory windows is authorized.",
            "No SFO row or project-owned controller is application-authorized by this review.",
        ],
    }
    review["review_digest"] = digest(review)
    return review


def replication_policy() -> dict[str, Any]:
    policy: dict[str, Any] = {
        "contract": REPLICATION_POLICY_CONTRACT,
        "study_version": "v0.2Q",
        **_authority_fields(),
        "purpose": "STAGED_PROFILE_REPLICATION_AFTER_COMPOSITION_UNSTABLE_ONE_VANILLA_VS_ONE_SFO_COMPARISON",
        "fixed_inputs": {
            "original_vanilla_rate": 0.270833,
            "original_sfo_rate": 0.461538,
            "vanilla_cluster_envelope_min": VANILLA_ENVELOPE_MIN,
            "vanilla_cluster_envelope_max": VANILLA_ENVELOPE_MAX,
            "minimum_territorial_eligible_windows_per_campaign": TEMPORAL_MIN_ELIGIBLE_WINDOWS,
        },
        "stage_a_fresh_sfo_replication": {
            "run_first": True,
            "same_profile_requirement": "Exact SFO hash + exact diagnostic probe hash + no extra mods + same campaign/difficulty protocol.",
            "branches": [
                {
                    "branch": "SFO_REPLICATION_INSUFFICIENT_EXPOSURE",
                    "condition": "territorial_eligible_windows < 20",
                    "action": "EXTEND_OR_REPEAT_SFO_ONLY; NO_ABLATION",
                },
                {
                    "branch": "SFO_REPLICATION_REPEATED_TERRITORIAL_SIGNAL",
                    "condition": "territorial_eligible_windows >= 20 AND repeated_reversal_force_count > 0",
                    "action": "CAUSAL_REVIEW_SPECIAL_POLICY_FIRST; DO_NOT_COPY_SFO_PRIORITY_INCREASES",
                },
                {
                    "branch": "SFO_ELEVATION_REPLICATED",
                    "condition": "territorial_eligible_windows >= 20 AND repeated_reversal_force_count == 0 AND reversal_candidate_rate > 0.317073",
                    "action": "PROCEED_TO_FRESH_VANILLA_REPLICATION; NO_ROW_ABLATION_YET",
                },
                {
                    "branch": "SFO_ELEVATION_NOT_REPLICATED",
                    "condition": "territorial_eligible_windows >= 20 AND repeated_reversal_force_count == 0 AND reversal_candidate_rate <= 0.317073",
                    "action": "STOP_PROFILE_WORSENING_NOMINATION; NO_ROW_ABLATION",
                },
            ],
        },
        "stage_b_fresh_vanilla_replication": {
            "run_only_if": "Stage A branch SFO_ELEVATION_REPLICATED",
            "same_profile_requirement": "Exact vanilla diagnostic profile, no gameplay mods, same campaign/difficulty protocol.",
            "profile_separation_rule": "min(SFO_run1_rate, SFO_run2_rate) > max(VANILLA_run1_rate, VANILLA_run2_rate)",
            "composition_guard": {
                "shared_faction_definition": "Faction contributes at least one eligible territorial window in at least one campaign of each profile.",
                "minimum_pooled_shared_eligible_windows_each_profile": 20,
                "required_direction": "pooled_shared_faction_SFO_rate > pooled_shared_faction_VANILLA_rate",
                "if_insufficient_or_direction_conflicts": "BLOCK_MECHANISTIC_NOMINATION_AS_COMPOSITION_UNRESOLVED",
            },
            "if_profile_separation_and_composition_guard_pass": "PROFILE_LEVEL_WORSENING_REPLICATED; EARN_MECHANISM_SELECTION_REVIEW_ONLY, NOT APPLICATION OR SFO-ROW COPYING",
            "otherwise": "NO_NATIVE_ROW_ABLATION_EARNED",
        },
        "recovery": {
            "status": "DEPRIORITIZED_NO_SIGNAL_IN_BOTH_EXISTING_CAMPAIGNS",
            "original_vanilla_rate": 0.157895,
            "original_sfo_rate": 0.142857,
            "rule": "Continue recording recovery telemetry opportunistically, but do not request extra owner runs solely for recovery unless a future cohort crosses the existing preregistered positive threshold.",
        },
        "global_rules": [
            "Fresh SFO replication is staged before another vanilla run to minimize owner burden.",
            "No result from Stage A alone earns a native-row ablation.",
            "No wholesale SFO row copying is permitted.",
            "No privileged diagnostic telemetry may become an application-time input.",
            "No branch revives v0.2G/v0.2I or project-owned campaign orders.",
        ],
    }
    policy["policy_digest"] = digest(policy)
    return policy


def adjudicate_sfo_replication_stage_a(fresh_sfo_result: dict[str, Any]) -> dict[str, Any]:
    territorial = fresh_sfo_result["temporal_stratification"]["territorial"]
    eligible = int(territorial["eligible_windows"])
    repeated = int(territorial["repeated_reversal_force_count"])
    rate = territorial["reversal_candidate_rate"]
    if eligible < TEMPORAL_MIN_ELIGIBLE_WINDOWS:
        branch = "SFO_REPLICATION_INSUFFICIENT_EXPOSURE"
        action = "EXTEND_OR_REPEAT_SFO_ONLY; NO_ABLATION"
    elif repeated > 0:
        branch = "SFO_REPLICATION_REPEATED_TERRITORIAL_SIGNAL"
        action = "CAUSAL_REVIEW_SPECIAL_POLICY_FIRST; DO_NOT_COPY_SFO_PRIORITY_INCREASES"
    elif rate is not None and float(rate) > VANILLA_ENVELOPE_MAX:
        branch = "SFO_ELEVATION_REPLICATED"
        action = "PROCEED_TO_FRESH_VANILLA_REPLICATION; NO_ROW_ABLATION_YET"
    else:
        branch = "SFO_ELEVATION_NOT_REPLICATED"
        action = "STOP_PROFILE_WORSENING_NOMINATION; NO_ROW_ABLATION"
    out: dict[str, Any] = {
        "contract": "NATIVE_CAI_SFO_REPLICATION_STAGE_A_ADJUDICATION_V1",
        "study_version": "v0.2Q",
        **_authority_fields(),
        "replication_policy_digest": replication_policy()["policy_digest"],
        "fresh_sfo_result_digest": fresh_sfo_result.get("result_digest"),
        "territorial_eligible_windows": eligible,
        "territorial_repeated_reversal_force_count": repeated,
        "territorial_reversal_candidate_rate": rate,
        "branch": branch,
        "action": action,
        "native_row_ablation_earned": False,
        "fresh_vanilla_replication_required": branch == "SFO_ELEVATION_REPLICATED",
    }
    out["adjudication_digest"] = digest(out)
    return out
