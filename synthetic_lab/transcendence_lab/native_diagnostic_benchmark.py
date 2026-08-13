from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .canonical import digest
from .native_sfo_mechanistic import (
    VANILLA_TERRITORIAL_LOO_MAX,
    VANILLA_TERRITORIAL_LOO_MIN,
    choose_recovery_branch,
    choose_temporal_branch,
    post_sfo_decision_table,
)
from .native_diagnostic_study import (
    APPLICATION_AUTHORITY,
    APPLICATION_ELIGIBLE,
    AUTHORITY,
    HEADING_REVERSAL_COSINE_MAX,
    MAX_HEALTH_RANGE_PCT,
    MAX_STRENGTH_RATIO,
    MAX_UNIT_COUNT_RANGE,
    MIN_DIRECTIONAL_DISTANCE,
    RESEARCH_VISIBILITY,
    TEMPORAL_MIN_ELIGIBLE_WINDOWS,
    _battle_participation_between,
    _cosine,
    _force_map,
    _health,
    _region_set,
    _strength,
    _unit_count,
    _vector,
    _war_set,
    analyze_native_diagnostic_behavior_study,
    frozen_thresholds_digest,
)

RESULT_CONTRACT = "NATIVE_CAI_SFO_MATCHED_BEHAVIOR_BENCHMARK_RESULT_V2"
VANILLA_REFERENCE_CONTRACT = "NATIVE_CAI_VANILLA_BEHAVIOR_REFERENCE_V1"
SFO_WORKSHOP_ID = "2792731173"
SFO_PACK_NAME = "sfo_grimhammer_3_main.pack"
SFO_REFERENCE_SHA256 = "ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603"
VANILLA_SOURCE_BUNDLE_SHA256 = "9416e0b73765570e6ffda1c1855a0430133b447e14cd63d307c966312987429d"
VANILLA_V02N_RESULT_DIGEST = "ebe747ca69a8b7da86586a7ea6759d65e2f81f5128cf45917fd9c41c495a8542"


class NativeDiagnosticBenchmarkError(ValueError):
    pass


def benchmark_spec() -> dict[str, Any]:
    return {
        "study_version": "v0.2P",
        "base_behavior_threshold_digest": frozen_thresholds_digest(),
        "sfo_workshop_id": SFO_WORKSHOP_ID,
        "sfo_pack_name": SFO_PACK_NAME,
        "sfo_reference_sha256": SFO_REFERENCE_SHA256,
        "vanilla_source_bundle_sha256": VANILLA_SOURCE_BUNDLE_SHA256,
        "vanilla_v0_2n_result_digest": VANILLA_V02N_RESULT_DIGEST,
        "primary_temporal_population": "TERRITORIAL_FACTION_WINDOWS",
        "territorial_population_rule": "stable owned-region set is non-empty throughout the eligible window",
        "nonterritorial_population_rule": "stable owned-region set is empty throughout the eligible window",
        "temporal_min_eligible_windows_per_primary_population": TEMPORAL_MIN_ELIGIBLE_WINDOWS,
        "comparison_interpretation": "prospective SFO benchmark against hash-frozen vanilla reference; vanilla stratification is retrospective and comparison is not randomized causal attribution",
        "territorial_cluster_sensitivity_envelope": {
            "kind": "VANILLA_LEAVE_ONE_FACTION_OUT_DESCRIPTIVE_RANGE",
            "min": VANILLA_TERRITORIAL_LOO_MIN,
            "max": VANILLA_TERRITORIAL_LOO_MAX,
            "not_a_confidence_interval": True,
        },
        "post_sfo_decision_table_digest": post_sfo_decision_table()["decision_table_digest"],
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": APPLICATION_ELIGIBLE,
    }


def benchmark_spec_digest() -> str:
    return digest(benchmark_spec())


def _stable_window(window: list[tuple[int, dict[str, Any], dict[str, Any]]]) -> bool:
    turns = [item[0] for item in window]
    if any(b - a != 1 for a, b in zip(turns, turns[1:])):
        return False
    forces = [item[1] for item in window]
    if any(_health(force) is None or _strength(force) is None or _unit_count(force) is None for force in forces):
        return False
    if len({_war_set(item[2]["end"]) for item in window}) != 1:
        return False
    if len({_region_set(item[2]["end"]) for item in window}) != 1:
        return False
    if len({str(force.get("stance")) for force in forces}) != 1:
        return False
    healths = [_health(force) for force in forces]
    strengths = [_strength(force) for force in forces]
    units = [_unit_count(force) for force in forces]
    if max(healths) - min(healths) > MAX_HEALTH_RANGE_PCT:  # type: ignore[arg-type]
        return False
    if max(strengths) / min(strengths) > MAX_STRENGTH_RATIO:  # type: ignore[arg-type]
        return False
    if max(units) - min(units) > MAX_UNIT_COUNT_RANGE:  # type: ignore[arg-type]
        return False
    return True


def _population(window: list[tuple[int, dict[str, Any], dict[str, Any]]]) -> str:
    return "territorial" if len(_region_set(window[1][2]["end"])) > 0 else "nonterritorial"


def stratify_temporal_trace(raw_trace: dict[str, Any]) -> dict[str, Any]:
    # Reuse the sealed v0.2N evaluator as the structural/authority validator.
    analyze_native_diagnostic_behavior_study(raw_trace)
    observations = sorted(raw_trace["observations"], key=lambda row: (int(row["turn"]), str(row["faction"])))
    battles = sorted(raw_trace["battle_sequences"], key=lambda row: int(row["begin_event_index"]))
    tracks: dict[tuple[str, str], list[tuple[int, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for row in observations:
        faction = str(row["faction"])
        for force_id, force in _force_map(row["end"]).items():
            tracks[(faction, force_id)].append((int(row["turn"]), force, row))

    populations: dict[str, dict[str, Any]] = {
        "territorial": {"eligible_windows": 0, "reversal_candidates": 0, "intervals": defaultdict(list)},
        "nonterritorial": {"eligible_windows": 0, "reversal_candidates": 0, "intervals": defaultdict(list)},
    }
    for (faction, force_id), rows in tracks.items():
        rows.sort(key=lambda item: item[0])
        for i in range(len(rows) - 2):
            window = rows[i:i + 3]
            if not _stable_window(window):
                continue
            v1 = _vector(window[0][1], window[1][1])
            v2 = _vector(window[1][1], window[2][1])
            if math.hypot(*v1) < MIN_DIRECTIONAL_DISTANCE or math.hypot(*v2) < MIN_DIRECTIONAL_DISTANCE:
                continue
            if _battle_participation_between(
                battles,
                faction,
                force_id,
                int(window[0][2]["end"]["end_event_index"]),
                int(window[-1][2]["end"]["end_event_index"]),
            ):
                continue
            population = _population(window)
            populations[population]["eligible_windows"] += 1
            cosine = _cosine(v1, v2)
            if cosine is None or cosine > HEADING_REVERSAL_COSINE_MAX:
                continue
            populations[population]["reversal_candidates"] += 1
            populations[population]["intervals"][(faction, force_id)].append((window[0][0], window[-1][0]))

    result: dict[str, Any] = {}
    for population, row in populations.items():
        repeated: list[dict[str, Any]] = []
        for (faction, force_id), intervals in sorted(row["intervals"].items()):
            selected: list[tuple[int, int]] = []
            for interval in sorted(intervals, key=lambda item: (item[1], item[0])):
                if not selected or interval[0] > selected[-1][1]:
                    selected.append(interval)
            if len(selected) >= 2:
                repeated.append({
                    "faction": faction,
                    "force_cqi": force_id,
                    "candidate_count": len(intervals),
                    "non_overlapping_candidate_count": len(selected),
                    "selected_non_overlapping_turn_intervals": [list(x) for x in selected],
                })
        eligible = int(row["eligible_windows"])
        candidates = int(row["reversal_candidates"])
        result[population] = {
            "eligible_windows": eligible,
            "reversal_candidates": candidates,
            "reversal_candidate_rate": None if eligible == 0 else round(candidates / eligible, 6),
            "repeated_reversal_force_count": len(repeated),
            "repeated_reversal_forces": repeated,
            "exposure_sufficient_for_primary_interpretation": eligible >= TEMPORAL_MIN_ELIGIBLE_WINDOWS,
        }
    result["contract"] = "NATIVE_CAI_TEMPORAL_POPULATION_STRATIFICATION_V1"
    result["authority"] = AUTHORITY
    result["application_authority"] = APPLICATION_AUTHORITY
    result["research_visibility"] = RESEARCH_VISIBILITY
    result["application_eligible"] = APPLICATION_ELIGIBLE
    result["population_rule_digest"] = digest({
        "territorial": benchmark_spec()["territorial_population_rule"],
        "nonterritorial": benchmark_spec()["nonterritorial_population_rule"],
        "base_behavior_threshold_digest": frozen_thresholds_digest(),
    })
    return result



def temporal_cluster_diagnostics(raw_trace: dict[str, Any], population: str = "territorial") -> dict[str, Any]:
    if population not in {"territorial", "nonterritorial"}:
        raise NativeDiagnosticBenchmarkError(f"unknown temporal population: {population}")
    analyze_native_diagnostic_behavior_study(raw_trace)
    observations = sorted(raw_trace["observations"], key=lambda row: (int(row["turn"]), str(row["faction"])))
    battles = sorted(raw_trace["battle_sequences"], key=lambda row: int(row["begin_event_index"]))
    tracks: dict[tuple[str, str], list[tuple[int, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for row in observations:
        faction = str(row["faction"])
        for force_id, force in _force_map(row["end"]).items():
            tracks[(faction, force_id)].append((int(row["turn"]), force, row))

    by_faction: dict[str, dict[str, int]] = defaultdict(lambda: {"eligible_windows": 0, "reversal_candidates": 0})
    candidate_windows: list[dict[str, Any]] = []
    for (faction, force_id), rows in tracks.items():
        rows.sort(key=lambda item: item[0])
        for i in range(len(rows) - 2):
            window = rows[i:i + 3]
            if not _stable_window(window):
                continue
            v1 = _vector(window[0][1], window[1][1])
            v2 = _vector(window[1][1], window[2][1])
            d1 = math.hypot(*v1)
            d2 = math.hypot(*v2)
            if d1 < MIN_DIRECTIONAL_DISTANCE or d2 < MIN_DIRECTIONAL_DISTANCE:
                continue
            if _battle_participation_between(
                battles,
                faction,
                force_id,
                int(window[0][2]["end"]["end_event_index"]),
                int(window[-1][2]["end"]["end_event_index"]),
            ):
                continue
            if _population(window) != population:
                continue
            by_faction[faction]["eligible_windows"] += 1
            cosine = _cosine(v1, v2)
            if cosine is None or cosine > HEADING_REVERSAL_COSINE_MAX:
                continue
            by_faction[faction]["reversal_candidates"] += 1
            candidate_windows.append({
                "faction": faction,
                "force_cqi": force_id,
                "turns": [window[0][0], window[1][0], window[2][0]],
                "regions": [window[0][1].get("region"), window[1][1].get("region"), window[2][1].get("region")],
                "heading_cosine": round(float(cosine), 6),
                "movement_distances": [round(d1, 6), round(d2, 6)],
            })

    eligible = sum(row["eligible_windows"] for row in by_faction.values())
    candidates = sum(row["reversal_candidates"] for row in by_faction.values())
    rows_out: list[dict[str, Any]] = []
    for faction, counts in sorted(by_faction.items()):
        e = counts["eligible_windows"]
        c = counts["reversal_candidates"]
        rows_out.append({
            "faction": faction,
            "eligible_windows": e,
            "reversal_candidates": c,
            "reversal_candidate_rate": None if e == 0 else round(c / e, 6),
        })
    loo: list[dict[str, Any]] = []
    for row in rows_out:
        remaining_e = eligible - row["eligible_windows"]
        remaining_c = candidates - row["reversal_candidates"]
        if remaining_e <= 0:
            continue
        loo.append({
            "excluded_faction": row["faction"],
            "remaining_eligible_windows": remaining_e,
            "remaining_reversal_candidates": remaining_c,
            "reversal_candidate_rate": round(remaining_c / remaining_e, 6),
        })
    loo_rates = [row["reversal_candidate_rate"] for row in loo]
    candidate_shares = [row["reversal_candidates"] / candidates for row in rows_out if candidates > 0 and row["reversal_candidates"] > 0]
    return {
        "contract": "NATIVE_CAI_TEMPORAL_CLUSTER_DIAGNOSTICS_V1",
        "population": population,
        "eligible_windows": eligible,
        "reversal_candidates": candidates,
        "reversal_candidate_rate": None if eligible == 0 else round(candidates / eligible, 6),
        "faction_cluster_count": len(rows_out),
        "faction_rows": rows_out,
        "candidate_windows": sorted(candidate_windows, key=lambda row: (row["faction"], row["force_cqi"], row["turns"])),
        "candidate_concentration": {
            "candidate_bearing_faction_count": sum(row["reversal_candidates"] > 0 for row in rows_out),
            "max_faction_candidate_share": None if not candidate_shares else round(max(candidate_shares), 6),
            "candidate_hhi_by_faction": None if not candidate_shares else round(sum(share * share for share in candidate_shares), 6),
        },
        "leave_one_faction_out": {
            "rows": loo,
            "rate_min": None if not loo_rates else min(loo_rates),
            "rate_max": None if not loo_rates else max(loo_rates),
            "rate_span": None if not loo_rates else round(max(loo_rates) - min(loo_rates), 6),
        },
        "interpretation": "DESCRIPTIVE_CLUSTER_SENSITIVITY_ONLY; OVERLAPPING_FORCE_WINDOWS_ARE_NOT_INDEPENDENT; NO_P_VALUE_AUTHORIZED",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": APPLICATION_ELIGIBLE,
    }

def analyze_sfo_benchmark(raw_trace: dict[str, Any], vanilla_reference: dict[str, Any]) -> dict[str, Any]:
    if vanilla_reference.get("contract") != VANILLA_REFERENCE_CONTRACT:
        raise NativeDiagnosticBenchmarkError("unexpected vanilla benchmark reference contract")
    if vanilla_reference.get("source_bundle", {}).get("sha256") != VANILLA_SOURCE_BUNDLE_SHA256:
        raise NativeDiagnosticBenchmarkError("vanilla benchmark source identity drifted")
    if vanilla_reference.get("base_result_digest") != VANILLA_V02N_RESULT_DIGEST:
        raise NativeDiagnosticBenchmarkError("vanilla v0.2N result digest drifted")

    base = analyze_native_diagnostic_behavior_study(raw_trace)
    stratified = stratify_temporal_trace(raw_trace)
    cluster_diagnostics = temporal_cluster_diagnostics(raw_trace, "territorial")
    territorial = stratified["territorial"]
    ref_territorial = vanilla_reference["temporal_stratification"]["territorial"]
    if territorial["eligible_windows"] < TEMPORAL_MIN_ELIGIBLE_WINDOWS:
        territorial_status = "INSUFFICIENT_TERRITORIAL_TEMPORAL_EXPOSURE"
    elif territorial["repeated_reversal_force_count"] > 0:
        territorial_status = "REPEATED_TERRITORIAL_REVERSAL_SIGNAL_OBSERVED"
    else:
        territorial_status = "NO_REPEATED_TERRITORIAL_REVERSAL_SIGNAL_IN_COHORT"

    candidate_rate_delta = None
    if territorial["reversal_candidate_rate"] is not None and ref_territorial["reversal_candidate_rate"] is not None:
        candidate_rate_delta = round(
            float(territorial["reversal_candidate_rate"]) - float(ref_territorial["reversal_candidate_rate"]), 6
        )

    result: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "study_version": "v0.2P",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": APPLICATION_ELIGIBLE,
        "benchmark_spec": benchmark_spec(),
        "benchmark_spec_digest": benchmark_spec_digest(),
        "base_v0_2n_result": base,
        "temporal_stratification": stratified,
        "primary_territorial_temporal_status": territorial_status,
        "recovery_status": base["recovery_status"],
        "comparison_to_hash_frozen_vanilla_reference": {
            "vanilla_reference_kind": "RETROSPECTIVELY_STRATIFIED_REFERENCE_NOT_RANDOMIZED_CAUSAL_BASELINE",
            "territorial_eligible_windows_vanilla": ref_territorial["eligible_windows"],
            "territorial_reversal_candidate_rate_vanilla": ref_territorial["reversal_candidate_rate"],
            "territorial_repeated_reversal_force_count_vanilla": ref_territorial["repeated_reversal_force_count"],
            "territorial_eligible_windows_sfo": territorial["eligible_windows"],
            "territorial_reversal_candidate_rate_sfo": territorial["reversal_candidate_rate"],
            "territorial_repeated_reversal_force_count_sfo": territorial["repeated_reversal_force_count"],
            "territorial_reversal_candidate_rate_delta_sfo_minus_vanilla": candidate_rate_delta,
            "recovery_attacker_side_rate_vanilla": vanilla_reference["recovery"]["recovering_attacker_side_rate"],
            "recovery_attacker_side_rate_sfo": base["metrics"]["recovering_attacker_side_rate"],
            "warning": "Differences are benchmark signals only. SFO changes many systems; this design does not identify which row/mechanism caused a difference.",
        },
        "territorial_cluster_diagnostics": cluster_diagnostics,
        "precommitted_post_sfo_decision": {
            "temporal": choose_temporal_branch(
                int(territorial["eligible_windows"]),
                int(territorial["reversal_candidates"]),
                int(territorial["repeated_reversal_force_count"]),
            ),
            "recovery": choose_recovery_branch(
                int(base["metrics"]["recovering_army_turn_count"]),
                int(base["metrics"]["recovering_attacker_side_army_turn_count"]),
            ),
            "decision_table_digest": post_sfo_decision_table()["decision_table_digest"],
        },
        "architecture_action": "NO_APPLICATION_AUTHORITY_CHANGE; REVIEW_DIFFERENCES_FOR_FUTURE_NARROW_NATIVE_OR_PROFILE_ABLATION_ONLY",
        "interpretation_limits": [
            "The primary strategic temporal cohort is territorial because the sole repeated v0.2N trigger was a non-territorial fixed-route Rogue Pirate patrol.",
            "The territorial/non-territorial split was chosen after the vanilla cohort and is therefore prospective only for SFO; the vanilla subgroup is a frozen reference, not a fresh confirmatory baseline.",
            "A lower or higher SFO rate does not establish causal effect of a specific SFO CAI row because SFO changes many campaign systems.",
            "Overlapping army windows are clustered within forces/factions; leave-one-faction-out diagnostics are descriptive sensitivity only and no p-value treating windows as independent is authorized.",
            "Privileged diagnostic data remains permanently application-ineligible.",
            "No benchmark result authorizes v0.2G/v0.2I or project-owned campaign orders.",
        ],
    }
    result["result_digest"] = digest(result)
    return result
