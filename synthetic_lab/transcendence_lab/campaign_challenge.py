from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from .canonical import digest
from .contracts import ContractError, validate_campaign_scenario, visible_scenario

CONTRACT = "CAMPAIGN_STRATEGIC_CHALLENGE_ENVELOPE_V1"
AUTHORITY = "NO_ORDERS"
APPLICATION_AUTHORITY = "PROHIBITED"
FRONT_HORIZON_TURNS = 2.0
RECOVERY_REPLENISHMENT_THRESHOLD = 0.65
COHERENT_ARMY_SHARE_THRESHOLD = 0.50
FRAGMENTED_DOMINANT_SHARE_CEILING = 0.65


class CampaignChallengeError(ValueError):
    pass


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def _at_war(wars: list[list[str]], a: str, b: str) -> bool:
    return [a, b] in wars or [b, a] in wars


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _shares(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(value)) for value in values.values())
    if total <= 0:
        return {key: 0.0 for key in sorted(values)}
    return {key: round(max(0.0, float(values[key])) / total, 6) for key in sorted(values)}


def _front_record(
    region: dict[str, Any],
    own_armies: list[dict[str, Any]],
    hostile_armies: list[dict[str, Any]],
) -> dict[str, Any]:
    nearby_hostiles: list[dict[str, Any]] = []
    for army in hostile_armies:
        eta = _distance(army, region) / max(float(army["movement"]), 1.0)
        if eta <= FRONT_HORIZON_TURNS:
            nearby_hostiles.append(
                {
                    "army_id": army["id"],
                    "faction": army["faction"],
                    "eta_turns_geometric": round(eta, 6),
                }
            )
    nearby_hostiles.sort(key=lambda item: (item["eta_turns_geometric"], item["faction"], item["army_id"]))

    nearby_own: list[dict[str, Any]] = []
    for army in own_armies:
        eta = _distance(army, region) / max(float(army["movement"]), 1.0)
        if eta <= FRONT_HORIZON_TURNS:
            nearby_own.append(
                {"army_id": army["id"], "eta_turns_geometric": round(eta, 6)}
            )
    nearby_own.sort(key=lambda item: (item["eta_turns_geometric"], item["army_id"]))

    same_faction_counts: dict[str, int] = {}
    for item in nearby_hostiles:
        same_faction_counts[item["faction"]] = same_faction_counts.get(item["faction"], 0) + 1
    colocated_same_faction_pressure = any(count >= 2 for count in same_faction_counts.values())

    threatened = bool(region["under_siege"] or nearby_hostiles)
    covered = bool(nearby_own)
    if region["under_siege"]:
        state = "SIEGED_COVERED" if covered else "SIEGED_EXPOSED"
    elif nearby_hostiles:
        state = "CONTESTED" if covered else "EXPOSED"
    else:
        state = "QUIET"

    return {
        "region_id": region["id"],
        "region_value": round(float(region["value"]), 6),
        "under_siege": bool(region["under_siege"]),
        "front_state": state,
        "threatened": threatened,
        "covered_by_visible_controlled_force": covered,
        "nearby_visible_hostiles": nearby_hostiles,
        "nearby_controlled_armies": nearby_own,
        "colocated_same_faction_pressure": colocated_same_faction_pressure,
        "coordination_claim": "NOT_INFERRED_FROM_COLOCATION",
    }


def evaluate_campaign_snapshot(raw_scenario: dict[str, Any]) -> dict[str, Any]:
    scenario = validate_campaign_scenario(raw_scenario)
    observer = str(scenario["controlled_faction"])
    visible = visible_scenario(scenario, observer)
    own_armies = [army for army in visible["armies"] if army["faction"] == observer]
    hostile_armies = [
        army
        for army in visible["armies"]
        if army["faction"] != observer and _at_war(visible["wars"], observer, army["faction"])
    ]
    own_regions = [region for region in visible["regions"] if region["owner"] == observer]
    hostile_regions = [
        region
        for region in visible["regions"]
        if region["owner"] != observer and _at_war(visible["wars"], observer, region["owner"])
    ]

    at_war_factions = sorted(
        {
            b if a == observer else a
            for a, b in visible["wars"]
            if a == observer or b == observer
        }
    )
    hostile_strength_by_faction = {faction: 0.0 for faction in at_war_factions}
    hostile_army_count_by_faction = {faction: 0 for faction in at_war_factions}
    hostile_region_value_by_faction = {faction: 0.0 for faction in at_war_factions}
    hostile_region_count_by_faction = {faction: 0 for faction in at_war_factions}
    for army in hostile_armies:
        hostile_strength_by_faction[army["faction"]] = hostile_strength_by_faction.get(army["faction"], 0.0) + float(army["strength"])
        hostile_army_count_by_faction[army["faction"]] = hostile_army_count_by_faction.get(army["faction"], 0) + 1
    for region in hostile_regions:
        hostile_region_value_by_faction[region["owner"]] = hostile_region_value_by_faction.get(region["owner"], 0.0) + float(region["value"])
        hostile_region_count_by_faction[region["owner"]] = hostile_region_count_by_faction.get(region["owner"], 0) + 1

    strength_shares = _shares(hostile_strength_by_faction)
    nonzero_strength_shares = [share for share in strength_shares.values() if share > 0]
    hhi = round(sum(share * share for share in nonzero_strength_shares), 6)
    dominant_faction = None
    dominant_share = 0.0
    if strength_shares:
        dominant_faction, dominant_share = min(
            strength_shares.items(), key=lambda item: (-item[1], item[0])
        )
        if dominant_share <= 0:
            dominant_faction = None

    rivals: list[dict[str, Any]] = []
    coherent_candidates: list[str] = []
    for faction in at_war_factions:
        share = strength_shares.get(faction, 0.0)
        armies = hostile_army_count_by_faction.get(faction, 0)
        regions = hostile_region_count_by_faction.get(faction, 0)
        coherent = armies >= 2 and regions >= 1 and share >= COHERENT_ARMY_SHARE_THRESHOLD
        if coherent:
            coherent_candidates.append(faction)
        rivals.append(
            {
                "faction": faction,
                "visible_army_count": armies,
                "visible_army_strength": round(hostile_strength_by_faction.get(faction, 0.0), 6),
                "visible_army_strength_share": share,
                "observed_region_count": regions,
                "observed_region_value": round(hostile_region_value_by_faction.get(faction, 0.0), 6),
                "coherent_visible_rival_candidate": coherent,
            }
        )

    hostile_asset_factions = [
        faction
        for faction in at_war_factions
        if hostile_army_count_by_faction.get(faction, 0) > 0 or hostile_region_count_by_faction.get(faction, 0) > 0
    ]
    if coherent_candidates:
        rival_structure = "COHERENT_VISIBLE_RIVAL_CANDIDATE"
    elif len(hostile_asset_factions) >= 2 and dominant_share < FRAGMENTED_DOMINANT_SHARE_CEILING:
        rival_structure = "FRAGMENTED_VISIBLE_PRESSURE"
    elif hostile_asset_factions:
        rival_structure = "SINGLE_OR_PARTIAL_VISIBLE_RIVAL"
    else:
        rival_structure = "NO_VISIBLE_HOSTILE_ASSETS"

    fronts = [_front_record(region, own_armies, hostile_armies) for region in own_regions]
    fronts.sort(key=lambda item: item["region_id"])
    threatened_fronts = [item for item in fronts if item["threatened"]]
    covered_fronts = [item for item in threatened_fronts if item["covered_by_visible_controlled_force"]]
    exposed_fronts = [item for item in threatened_fronts if not item["covered_by_visible_controlled_force"]]
    colocated_pressure_fronts = [item for item in fronts if item["colocated_same_faction_pressure"]]

    own_strength = sum(float(army["strength"]) for army in own_armies)
    hostile_strength = sum(float(army["strength"]) for army in hostile_armies)
    own_region_value = sum(float(region["value"]) for region in own_regions)
    hostile_region_value = sum(float(region["value"]) for region in hostile_regions)
    recovery_armies = [army for army in own_armies if float(army["replenishment"]) < RECOVERY_REPLENISHMENT_THRESHOLD]
    recovery_strength = sum(float(army["strength"]) for army in recovery_armies)

    if any(item["under_siege"] for item in fronts) or exposed_fronts:
        pressure_class = "LOCAL_CRISIS_OR_EXPOSED_FRONT"
    elif threatened_fronts:
        pressure_class = "COVERED_VISIBLE_FRONT_PRESSURE"
    elif hostile_asset_factions:
        pressure_class = "VISIBLE_RIVAL_WITHOUT_NEAR_FRONT_PRESSURE"
    else:
        pressure_class = "LOW_VISIBLE_PRESSURE"

    metrics = {
        "controlled_army_count": len(own_armies),
        "controlled_army_strength": round(own_strength, 6),
        "controlled_region_count": len(own_regions),
        "controlled_region_value": round(own_region_value, 6),
        "at_war_faction_count": len(at_war_factions),
        "visible_hostile_army_count": len(hostile_armies),
        "visible_hostile_army_strength": round(hostile_strength, 6),
        "observed_hostile_region_count": len(hostile_regions),
        "observed_hostile_region_value": round(hostile_region_value, 6),
        "visible_hostile_to_controlled_army_ratio": _safe_ratio(hostile_strength, own_strength),
        "observed_hostile_to_controlled_region_value_ratio": _safe_ratio(hostile_region_value, own_region_value),
        "visible_hostile_army_concentration_hhi": hhi,
        "dominant_visible_hostile_faction": dominant_faction,
        "dominant_visible_hostile_army_share": dominant_share,
        "threatened_front_count": len(threatened_fronts),
        "covered_threatened_front_count": len(covered_fronts),
        "exposed_front_count": len(exposed_fronts),
        "front_coverage_ratio": _safe_ratio(float(len(covered_fronts)), float(len(threatened_fronts))),
        "colocated_same_faction_pressure_front_count": len(colocated_pressure_fronts),
        "controlled_recovery_army_count": len(recovery_armies),
        "controlled_recovery_strength_fraction": _safe_ratio(recovery_strength, own_strength),
    }

    result = {
        "schema_version": 1,
        "contract": CONTRACT,
        "scenario_id": visible["scenario_id"],
        "turn": visible["turn"],
        "controlled_faction": observer,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "evidence_status": "CONTROL_OFFLINE_OVER_OBSERVER_SAFE_SNAPSHOT",
        "visibility_policy": {
            "hidden_enemy_armies_consumed": False,
            "human_or_player_identity_consumed": False,
            "region_scope": "SCENARIO_SUPPLIED_OBSERVED_REGIONS_ONLY",
        },
        "engineering_thresholds": {
            "front_horizon_turns_geometric": FRONT_HORIZON_TURNS,
            "recovery_replenishment_threshold": RECOVERY_REPLENISHMENT_THRESHOLD,
            "coherent_visible_rival_army_share_threshold": COHERENT_ARMY_SHARE_THRESHOLD,
            "fragmented_visible_pressure_dominant_share_ceiling": FRAGMENTED_DOMINANT_SHARE_CEILING,
            "status": "PROJECT_OWNED_BENCHMARK_THRESHOLDS_NOT_EMPIRICAL_TRUTH",
        },
        "rival_structure": rival_structure,
        "pressure_class": pressure_class,
        "rivals": rivals,
        "fronts": fronts,
        "metrics": metrics,
        "unavailable_dimensions": {
            "anti_player_bias": "REQUIRES_TARGETING_HISTORY_AND_NONPLAYER_COUNTERFACTUALS",
            "diplomatic_bloc_intent": "REQUIRES_DIPLOMACY_STATE_BEYOND_WAR_EDGES",
            "recovery_capacity": "REQUIRES_ECONOMY_RECRUITMENT_AND_REPLENISHMENT_HISTORY",
            "native_ai_intent": "NOT_OBSERVABLE_FROM_POSITION_SNAPSHOT",
            "campaign_quality": "REQUIRES_LONGITUDINAL_OUTCOMES_AND_OWNER_RATINGS",
        },
        "guardrails": [
            "Do not reward the number of factions at war as a challenge metric.",
            "Do not consume hidden hostile army identity or state.",
            "Do not infer coordination from colocated same-faction pressure.",
            "Do not infer anti-player bias from a single snapshot.",
            "Keep decision quality separate from stat, resource, or difficulty bonuses.",
            "Treat late-game rival coherence and front pressure as separate benchmark dimensions.",
        ],
    }
    result["result_digest"] = digest(result)
    return result


def _validate_observed_report(report: dict[str, Any]) -> None:
    if report.get("mode") != "SHADOW_NO_ORDERS":
        raise CampaignChallengeError("observed report must be SHADOW_NO_ORDERS")
    authority = report.get("authority")
    if not isinstance(authority, dict):
        raise CampaignChallengeError("observed report authority missing")
    if authority.get("game_orders_emitted") is not False or authority.get("save_values_written") is not False:
        raise CampaignChallengeError("observed report crosses no-order authority boundary")
    turns = report.get("turn_results")
    if not isinstance(turns, list) or not turns:
        raise CampaignChallengeError("observed report turn_results missing")
    parsed_turns: list[int] = []
    for item in turns:
        if not isinstance(item, dict) or not isinstance(item.get("scenario"), dict):
            raise CampaignChallengeError("observed report contains malformed turn result")
        scenario = validate_campaign_scenario(item["scenario"])
        if int(item.get("turn", scenario["turn"])) != scenario["turn"]:
            raise CampaignChallengeError("observed report turn/scenario mismatch")
        parsed_turns.append(scenario["turn"])
    if parsed_turns != sorted(parsed_turns) or len(set(parsed_turns)) != len(parsed_turns):
        raise CampaignChallengeError("observed report turns must be unique and ordered")


def build_campaign_challenge_envelope(
    observed_report: dict[str, Any], late_game_scenario: dict[str, Any]
) -> dict[str, Any]:
    _validate_observed_report(observed_report)
    observed_turns = [
        evaluate_campaign_snapshot(item["scenario"]) for item in observed_report["turn_results"]
    ]
    late_game = evaluate_campaign_snapshot(late_game_scenario)

    result = {
        "schema_version": 1,
        "contract": "CAMPAIGN_STRATEGIC_CHALLENGE_CROSS_EVIDENCE_ENVELOPE_V1",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "evidence_status": "CONTROL_OFFLINE_OVER_OBSERVED_AND_SYNTHETIC_INPUTS",
        "observed_source": {
            "report_result_digest": observed_report.get("result_digest"),
            "mode": observed_report.get("mode"),
            "profile_id": observed_report.get("profile_id"),
            "turns": [item["turn"] for item in observed_turns],
            "evidence_limit": "EARLY_REIKLAND_VISIBLE_SNAPSHOT_CALIBRATION_ONLY",
        },
        "observed_turns": observed_turns,
        "synthetic_late_game_reference": late_game,
        "benchmark_dimensions": [
            "visible_rival_structure",
            "visible_hostile_army_concentration",
            "front_pressure",
            "front_coverage",
            "same_faction_colocation_without_coordination_claim",
            "controlled_recovery_load",
            "visible_local_force_balance",
        ],
        "design_requirements": [
            "Late-game challenge should prefer coherent rival powers and meaningful fronts over many unrelated anti-player wars.",
            "Human/player identity must not enter strategic quality scoring or target utility.",
            "A strong rival still needs recovery capacity, diplomacy, economy, and longitudinal behavior evidence before being called durable.",
            "Visible local force balance is not world power rank and must not be used as omniscient campaign truth.",
            "Any later strategic director remains advisory until a separate campaign order-authority sandbox proves application semantics.",
        ],
        "generalization_limits": [
            "Observed calibration covers only four early vanilla Reikland turn-start snapshots from turns 4 through 7.",
            "The late-game reference is synthetic and cannot establish WH3 campaign quality.",
            "War edges do not establish coalitions, diplomacy intent, or anti-player bias.",
            "No economy, recruitment, treasury, income, autoresolve, or native CAI intent is consumed.",
            "SFO campaign observation is proven separately, but detailed SFO strategic-state calibration is not supplied to this envelope.",
        ],
    }
    result["result_digest"] = digest(result)
    return result


def semantic_snapshot_metrics(result: dict[str, Any]) -> dict[str, Any]:
    """Return ID- and absolute-scale-insensitive metrics for metamorphic comparisons."""
    metrics = result["metrics"]
    invariant_keys = [
        "controlled_army_count",
        "controlled_region_count",
        "at_war_faction_count",
        "visible_hostile_army_count",
        "observed_hostile_region_count",
        "visible_hostile_to_controlled_army_ratio",
        "observed_hostile_to_controlled_region_value_ratio",
        "visible_hostile_army_concentration_hhi",
        "dominant_visible_hostile_army_share",
        "threatened_front_count",
        "covered_threatened_front_count",
        "exposed_front_count",
        "front_coverage_ratio",
        "colocated_same_faction_pressure_front_count",
        "controlled_recovery_army_count",
        "controlled_recovery_strength_fraction",
    ]
    return {
        "rival_structure": result["rival_structure"],
        "pressure_class": result["pressure_class"],
        "metrics": {key: metrics.get(key) for key in invariant_keys},
        "front_states": sorted(front["front_state"] for front in result["fronts"]),
        "coherent_rival_count": sum(1 for rival in result["rivals"] if rival["coherent_visible_rival_candidate"]),
    }
