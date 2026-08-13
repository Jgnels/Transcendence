from __future__ import annotations

from collections import defaultdict
from typing import Any

from .canonical import digest
from .observed_battle import validate_observed_battle_corpus
from .tactical_state import build_tactical_state_trajectory


SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
MAX_SELECTED_OPPORTUNITIES_PER_SLICE = 6


def _severity(score: float) -> str:
    if score >= 0.78:
        return "CRITICAL"
    if score >= 0.60:
        return "HIGH"
    if score >= 0.40:
        return "MEDIUM"
    return "LOW"


def _opportunity_score(unit: dict[str, Any], urgency_bonus: float = 0.0) -> float:
    derived = unit["derived"]
    score = (
        0.48 * derived["danger_score"]
        + 0.27 * derived["asset_value_score"]
        + 0.18 * derived["collapse_risk_score"]
        + 0.07 * (1.0 - derived["withdrawal_recoverability_proxy"])
        + urgency_bonus
    )
    return round(max(0.0, min(1.0, score)), 6)


def _confidence(
    state: dict[str, Any], *, path_sensitive: bool, direct_metrics: bool = True
) -> dict[str, Any]:
    hidden = state["observation_scope"]["hidden_enemy_unit_count"]
    if direct_metrics and hidden == 0 and not path_sensitive:
        level = "HIGH"
    elif direct_metrics and hidden <= 2:
        level = "MEDIUM"
    else:
        level = "LOW"
    limitations = [
        "No accepted or executed Transcendence command exists for comparison.",
        "The proposed alternatives are unobserved counterfactuals.",
    ]
    if hidden:
        limitations.append(
            f"{hidden} enemy units are intentionally hidden from detailed evaluation."
        )
    if path_sensitive:
        limitations.append(
            "Terrain-aware withdrawal paths and WH3 pathfinding feasibility are unavailable."
        )
    return {
        "level": level,
        "basis": "observed state plus deterministic disclosed derivation",
        "limitations": limitations,
    }


def _alternative(
    alternative_id: str, description: str, tradeoff: str
) -> dict[str, str]:
    return {
        "alternative_id": alternative_id,
        "description": description,
        "tradeoff": tradeoff,
        "status": "PROPOSED_NOT_EXECUTED",
    }


def _make_unit_opportunity(
    state: dict[str, Any],
    unit: dict[str, Any],
    opportunity_type: str,
    diagnosis: str,
    alternatives: list[dict[str, str]],
    *,
    urgency_bonus: float = 0.0,
    path_sensitive: bool = True,
) -> dict[str, Any]:
    observed = unit["observed"]
    derived = unit["derived"]
    utility = _opportunity_score(unit, urgency_bonus)
    opportunity_key = f"{opportunity_type}:UNIT:{observed['stable_unit_id']}"
    return {
        "opportunity_id": f"{state['slice_id']}:{opportunity_key}",
        "opportunity_key": opportunity_key,
        "opportunity_type": opportunity_type,
        "scope": "UNIT",
        "subject_unit_ids": [observed["stable_unit_id"]],
        "severity": _severity(utility),
        "utility_score": utility,
        "observed_state": {
            "role": observed["role"],
            "hitpoints_fraction": observed["hitpoints_fraction"],
            "model_fraction": observed["men_fraction"],
            "fatigue": observed["fatigue"],
            "routing": observed["routing"],
            "shattered": observed["shattered"],
            "wavering": observed["wavering"],
            "in_melee": observed["in_melee"],
            "under_missile_attack": observed["under_missile_attack"],
        },
        "derived_metrics": {
            "danger_score": derived["danger_score"],
            "asset_value_score": derived["asset_value_score"],
            "collapse_risk_score": derived["collapse_risk_score"],
            "withdrawal_recoverability_proxy": derived[
                "withdrawal_recoverability_proxy"
            ],
            "marginal_engagement_value_proxy": derived[
                "marginal_engagement_value_proxy"
            ],
            "support_balance": derived["support_balance"],
            "trend": derived["trend"],
        },
        "tactical_diagnosis": diagnosis,
        "proposed_alternatives": alternatives,
        "confidence": _confidence(state, path_sensitive=path_sensitive),
        "counterfactual_status": "UNVERIFIED",
        "expires_when": [
            "the observed danger condition clears",
            "the unit leaves the observed hierarchy",
            "a newer tactical-state sample supersedes this window",
        ],
        "authority": "ADVISORY_ONLY",
    }


def _battle_opportunity(
    state: dict[str, Any],
    opportunity_type: str,
    diagnosis: str,
    alternatives: list[dict[str, str]],
    subject_unit_ids: list[str],
    utility_score: float,
    *,
    path_sensitive: bool,
) -> dict[str, Any]:
    utility_score = round(max(0.0, min(1.0, utility_score)), 6)
    opportunity_key = f"{opportunity_type}:BATTLE"
    return {
        "opportunity_id": f"{state['slice_id']}:{opportunity_key}",
        "opportunity_key": opportunity_key,
        "opportunity_type": opportunity_type,
        "scope": "BATTLE",
        "subject_unit_ids": sorted(subject_unit_ids),
        "severity": _severity(utility_score),
        "utility_score": utility_score,
        "observed_state": {
            "local_stability_state": state["battle_state"][
                "local_stability_state"
            ],
            "tactical_phase_state": state["battle_state"]["tactical_phase_state"],
            "visible_enemy_collapse_state": state["battle_state"][
                "visible_enemy_collapse_state"
            ],
            "outcome_state": state["battle_state"]["outcome_state"],
            "hidden_enemy_unit_count": state["observation_scope"][
                "hidden_enemy_unit_count"
            ],
        },
        "derived_metrics": {
            "local_pressure_score": state["battle_state"][
                "local_pressure_score"
            ],
            "local_integrity_score": state["battle_state"]["local"][
                "integrity_score"
            ],
            "visible_enemy_integrity_score": state["battle_state"][
                "visible_enemy"
            ]["integrity_score"],
            "local_routing_fraction": state["battle_state"]["local"][
                "routing_fraction"
            ],
            "visible_enemy_routing_fraction": state["battle_state"][
                "visible_enemy"
            ]["routing_fraction"],
        },
        "tactical_diagnosis": diagnosis,
        "proposed_alternatives": alternatives,
        "confidence": _confidence(state, path_sensitive=path_sensitive),
        "counterfactual_status": "UNVERIFIED",
        "expires_when": [
            "battle posture changes",
            "a newer tactical-state sample supersedes this window",
        ],
        "authority": "ADVISORY_ONLY",
    }


def _visible_enemy_target_score(unit: dict[str, Any], cleanup_mode: bool) -> float:
    observed = unit["observed"]
    derived = unit["derived"]
    role_weight = {
        "commander": 2.0,
        "artillery": 1.8,
        "ranged": 1.5,
        "cavalry": 1.4,
        "frontline": 1.0,
        "unknown": 1.0,
    }.get(observed["role"], 1.0)
    combat_threat = role_weight * (
        0.45 + observed["hitpoints_fraction"]
    ) * (0.45 + observed["men_fraction"])
    if observed["in_melee"]:
        combat_threat += 0.5
    if observed["ammo"] > 0:
        combat_threat += 0.3
    routed = observed["routing"] or observed["shattered"]
    if routed:
        combat_threat *= 0.28 if not cleanup_mode else 0.60
    # Prefer coherent threats over easy but strategically irrelevant cleanup.
    combat_threat *= 0.75 + 0.25 * derived["marginal_engagement_value_proxy"]
    return round(combat_threat, 6)


def _posture(state: dict[str, Any]) -> str:
    battle = state["battle_state"]
    if battle["visible_enemy_collapse_state"] in {
        "ROUT_CASCADE",
        "TERMINAL_COUNTDOWN",
        "TERMINAL",
    }:
        return "TERMINATE_WITH_PRESERVATION"
    if battle["local_stability_state"] in {
        "LOCAL_CRISIS",
        "RECOVERABLE_COLLAPSE",
        "IRREVERSIBLE_COLLAPSE",
    }:
        return "CRISIS_STABILIZATION"
    if battle["local"]["melee_fraction"] > 0.0:
        return "COMBINED_ENGAGEMENT"
    if battle["visible_enemy"]["missile_pressure_fraction"] > 0.0:
        return "RANGED_CONTACT"
    return "DEPLOYMENT_AND_INFORMATION"


def _priority_for_local_unit(unit: dict[str, Any]) -> dict[str, Any] | None:
    observed = unit["observed"]
    derived = unit["derived"]
    role = observed["role"]
    policy = derived["policy"]
    reasons: list[str] = []
    priority_type: str | None = None

    if role == "commander" and (
        observed["hitpoints_fraction"] < policy["preserve_hp"]
        or observed["routing"]
        or observed["wavering"]
        or observed["shattered"]
    ):
        priority_type = "PRESERVE_CHARACTER"
        reasons.append("role-specific character preservation threshold")
    elif role == "artillery" and (
        observed["men_fraction"] < policy["preserve_models"]
        or derived["danger_score"] >= 0.42
        or observed["routing"]
        or observed["shattered"]
        or observed["in_melee"]
    ):
        priority_type = "EXTRACT_OR_SCREEN_ARTILLERY"
        reasons.append("artillery combat power at risk")
    elif role == "cavalry" and (
        observed["men_fraction"] < policy["preserve_models"]
        or derived["fatigue_severity"] >= 0.55
        or derived["danger_score"] >= 0.45
        or observed["routing"]
        or observed["shattered"]
    ):
        priority_type = "DISENGAGE_OR_PRESERVE_CAVALRY"
        reasons.append("cavalry attrition, fatigue, or isolation threshold")
    elif role == "frontline" and (
        observed["men_fraction"] < policy["preserve_models"]
        or observed["routing"]
        or observed["wavering"]
        or derived["collapse_risk_score"] >= 0.48
    ):
        priority_type = "STABILIZE_OR_RELIEVE_FRONTLINE"
        reasons.append("frontline collapse risk")
    elif role == "ranged" and (
        observed["men_fraction"] < policy["preserve_models"]
        or derived["danger_score"] >= 0.43
        or observed["routing"]
        or observed["wavering"]
        or observed["in_melee"]
        or observed["under_missile_attack"]
        or observed["left_flank_threatened"]
        or observed["right_flank_threatened"]
        or observed["rear_flank_threatened"]
    ):
        priority_type = "PROTECT_OR_REPOSITION_RANGED"
        reasons.append("ranged asset exposed")

    if priority_type is None:
        return None
    if observed["routing"]:
        reasons.append("routing")
    if observed["shattered"]:
        reasons.append("shattered")
    if observed["wavering"]:
        reasons.append("wavering")
    if observed["under_missile_attack"]:
        reasons.append("missile pressure")
    if observed["in_melee"]:
        reasons.append("melee contact")
    if derived["trend"]["status"] == "DETERIORATING":
        reasons.append("deteriorating since previous milestone")
    return {
        "priority_type": priority_type,
        "stable_unit_id": observed["stable_unit_id"],
        "unit_type": observed["unit_type"],
        "role": role,
        "preservation_score": round(
            derived["danger_score"]
            * (1.0 + derived["asset_value_score"])
            * (1.15 - 0.35 * derived["withdrawal_recoverability_proxy"]),
            6,
        ),
        "model_fraction": observed["men_fraction"],
        "hitpoints_fraction": observed["hitpoints_fraction"],
        "danger_score": derived["danger_score"],
        "withdrawal_recoverability_proxy": derived[
            "withdrawal_recoverability_proxy"
        ],
        "reasons": sorted(set(reasons)),
        "authority": "ADVISORY_ONLY",
    }


def _extract_unit_opportunities(
    state: dict[str, Any], local_units: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    local_stability = state["battle_state"]["local_stability_state"]
    for unit in local_units:
        observed = unit["observed"]
        derived = unit["derived"]
        policy = derived["policy"]
        role = observed["role"]

        if role == "commander" and (
            observed["hitpoints_fraction"] < policy["preserve_hp"]
            or derived["danger_score"] >= 0.48
            or observed["routing"]
            or observed["wavering"]
        ):
            opportunities.append(
                _make_unit_opportunity(
                    state,
                    unit,
                    "COMMANDER_EXTRACTION_WINDOW",
                    "A high-value character is below its preservation threshold or exposed to escalating danger.",
                    [
                        _alternative(
                            "EXTRACT_TO_FRIENDLY_DEPTH",
                            "Move the character toward supported friendly depth and stop low-value pursuit.",
                            "May surrender immediate damage or leadership influence to preserve campaign and battle value.",
                        ),
                        _alternative(
                            "SCREEN_THEN_WITHDRAW",
                            "Use a coherent nearby unit as a temporary screen before withdrawing the character.",
                            "Consumes another unit's attention and depends on path availability.",
                        ),
                        _alternative(
                            "CONTINUE_ONLY_FOR_DECISIVE_VALUE",
                            "Continue engagement only when the visible target has decisive marginal value and escape remains recoverable.",
                            "Highest survival risk; no counterfactual benefit is established.",
                        ),
                    ],
                    urgency_bonus=0.12,
                )
            )
        elif role == "artillery" and (
            observed["men_fraction"] < policy["preserve_models"]
            or observed["in_melee"]
            or derived["danger_score"] >= 0.40
            or observed["routing"]
        ):
            opportunities.append(
                _make_unit_opportunity(
                    state,
                    unit,
                    "ARTILLERY_EVACUATION_WINDOW",
                    "Artillery preservation value is high and continued exposure risks losing a low-mobility productive asset.",
                    [
                        _alternative(
                            "EVACUATE_ARTILLERY",
                            "Withdraw along the safest observed support direction.",
                            "May reduce immediate fire support and is not pathfinding-certified.",
                        ),
                        _alternative(
                            "ASSIGN_TEMPORARY_SCREEN",
                            "Screen the artillery while it disengages or resumes fire.",
                            "Commits another unit and may transfer risk rather than remove it.",
                        ),
                        _alternative(
                            "HOLD_FIRE_POSITION",
                            "Remain only if visible pressure is low and marginal fire value exceeds preservation risk.",
                            "Risks irreversible model loss if pressure is underestimated.",
                        ),
                    ],
                    urgency_bonus=0.08,
                )
            )
        elif role == "ranged" and (
            observed["men_fraction"] < policy["preserve_models"]
            or observed["in_melee"]
            or observed["under_missile_attack"]
            or any(
                observed[key]
                for key in (
                    "left_flank_threatened",
                    "right_flank_threatened",
                    "rear_flank_threatened",
                )
            )
            or derived["danger_score"] >= 0.42
        ):
            opportunities.append(
                _make_unit_opportunity(
                    state,
                    unit,
                    "RANGED_REPOSITION_WINDOW",
                    "A productive ranged unit is exposed, degraded, or losing safe firing conditions.",
                    [
                        _alternative(
                            "REPOSITION_BEHIND_COHERENT_LINE",
                            "Move behind supported friendly units while preserving a visible firing lane.",
                            "May interrupt fire and assumes a usable line and path exist.",
                        ),
                        _alternative(
                            "FOCUS_VISIBLE_IMMEDIATE_THREAT",
                            "Concentrate fire on the highest coherent visible threat before displacement.",
                            "Spends ammunition and may delay disengagement.",
                        ),
                        _alternative(
                            "CEASE_FIRE_AND_PRESERVE",
                            "Cease low-value fire and preserve ammunition and formation integrity.",
                            "Foregoes damage when a safe target may still exist.",
                        ),
                    ],
                    urgency_bonus=0.05,
                )
            )
        elif role == "cavalry" and (
            observed["men_fraction"] < policy["preserve_models"]
            or derived["fatigue_severity"] >= 0.55
            or derived["danger_score"] >= 0.42
            or derived["support_balance"] < 0
            or observed["routing"]
        ):
            opportunities.append(
                _make_unit_opportunity(
                    state,
                    unit,
                    "CAVALRY_DISENGAGEMENT_WINDOW",
                    "Cavalry combat power is being consumed by fatigue, attrition, or unsupported exposure.",
                    [
                        _alternative(
                            "DISENGAGE_AND_REFORM",
                            "Break contact, reform near friendly support, and retain mobility for a later decisive task.",
                            "May allow the current target to escape or re-form.",
                        ),
                        _alternative(
                            "SHORT_PURSUIT_WITH_STOP_CONDITION",
                            "Pursue only a vulnerable visible target with a strict fatigue, distance, and danger stop condition.",
                            "Can still overextend if terrain or hidden threats invalidate the proxy.",
                        ),
                        _alternative(
                            "SCREEN_WITHOUT_DEEP_COMMITMENT",
                            "Use presence and positioning rather than prolonged melee.",
                            "May produce less immediate damage.",
                        ),
                    ],
                    urgency_bonus=0.07,
                )
            )
        elif role == "frontline" and local_stability in {
            "LOCAL_CRISIS",
            "RECOVERABLE_COLLAPSE",
            "IRREVERSIBLE_COLLAPSE",
        } and (
            observed["men_fraction"] < 0.70
            or observed["routing"]
            or observed["wavering"]
            or derived["collapse_risk_score"] >= 0.40
        ):
            opportunities.append(
                _make_unit_opportunity(
                    state,
                    unit,
                    "FRONTLINE_RELIEF_WINDOW",
                    "A frontline element is at risk of local morale or formation failure while active opposition remains.",
                    [
                        _alternative(
                            "RELIEVE_WITH_COHERENT_SUPPORT",
                            "Rotate or reinforce with the nearest coherent support element.",
                            "May expose the supporting unit and requires formation space.",
                        ),
                        _alternative(
                            "FALL_BACK_TO_SHORTER_LINE",
                            "Withdraw toward a shorter supported line rather than preserve every current contact.",
                            "Concedes ground and may disrupt adjacent units.",
                        ),
                        _alternative(
                            "HOLD_FOR_BOUNDED_DELAY",
                            "Continue holding only when the delay protects higher-value assets or enables decisive pressure elsewhere.",
                            "Accepts attrition and must not become an automatic sacrifice rule.",
                        ),
                    ],
                    urgency_bonus=0.06,
                )
            )
    return opportunities


def _extract_battle_opportunities(
    state: dict[str, Any], local_units: list[dict[str, Any]], enemy_units: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    battle = state["battle_state"]
    local_stability = battle["local_stability_state"]
    enemy_collapse = battle["visible_enemy_collapse_state"]

    morale_failures = [
        unit["observed"]["stable_unit_id"]
        for unit in local_units
        if unit["observed"]["routing"] or unit["observed"]["wavering"]
    ]
    if morale_failures and enemy_collapse not in {"TERMINAL", "TERMINAL_COUNTDOWN"}:
        opportunities.append(
            _battle_opportunity(
                state,
                "LOCAL_ROUT_CONTAINMENT_WINDOW",
                "Local morale failure is present; continued unsupported exposure may propagate a rout cascade.",
                [
                    _alternative(
                        "STABILIZE_ADJACENT_COHERENT_UNITS",
                        "Reduce pressure on adjacent coherent units and restore a supported line.",
                        "May slow offensive momentum.",
                    ),
                    _alternative(
                        "ALLOW_ROUTING_UNIT_TO_CLEAR",
                        "Avoid feeding fresh units into the same collapsing contact while the routing unit clears.",
                        "Concedes local space and may expose a gap temporarily.",
                    ),
                ],
                morale_failures,
                min(1.0, 0.52 + 0.35 * battle["local"]["routing_fraction"]),
                path_sensitive=True,
            )
        )

    reserve_candidates = [
        unit["observed"]["stable_unit_id"]
        for unit in local_units
        if unit["observed"]["role"] in {"frontline", "cavalry"}
        and unit["observed"]["idle"]
        and unit["derived"]["fatigue_severity"] <= 0.35
        and unit["derived"]["danger_score"] < 0.35
        and not unit["observed"]["routing"]
        and not unit["observed"]["shattered"]
    ]
    if local_stability in {"LOCAL_CRISIS", "RECOVERABLE_COLLAPSE"} and reserve_candidates:
        opportunities.append(
            _battle_opportunity(
                state,
                "RESERVE_COMMITMENT_WINDOW",
                "A recoverable local crisis exists while coherent fresh reserve candidates remain uncommitted.",
                [
                    _alternative(
                        "COMMIT_MINIMUM_SUFFICIENT_RESERVE",
                        "Commit the smallest suitable reserve element to the highest-severity local failure.",
                        "May consume flexibility needed for an unseen or later threat.",
                    ),
                    _alternative(
                        "RETAIN_RESERVE_AND_SHORTEN_LINE",
                        "Preserve the reserve while reducing the frontage that must be supported.",
                        "Concedes space and may not relieve immediate pressure.",
                    ),
                ],
                reserve_candidates,
                min(1.0, 0.48 + battle["local_pressure_score"]),
                path_sensitive=True,
            )
        )

    coherent_visible_enemies = [
        unit
        for unit in enemy_units
        if not unit["observed"]["routing"] and not unit["observed"]["shattered"]
    ]
    if enemy_collapse == "BREAKING" and coherent_visible_enemies:
        safe_exploiters = [
            unit["observed"]["stable_unit_id"]
            for unit in local_units
            if unit["observed"]["role"] in {"cavalry", "ranged"}
            and unit["derived"]["danger_score"] < 0.40
            and unit["derived"]["fatigue_severity"] < 0.75
            and not unit["observed"]["routing"]
        ]
        opportunities.append(
            _battle_opportunity(
                state,
                "SELECTIVE_PURSUIT_WINDOW",
                "The visible enemy is breaking but retains coherent combat power; exploitation should be selective rather than universal.",
                [
                    _alternative(
                        "PRESS_COHERENT_HIGH_VALUE_THREAT",
                        "Use only suitable low-risk units against the highest coherent visible threat.",
                        "Can prolong exposure and may be invalidated by hidden enemies.",
                    ),
                    _alternative(
                        "REFORM_AND_FIRE",
                        "Reform damaged units while safe ranged assets continue bounded pressure.",
                        "Allows some routed units to escape.",
                    ),
                    _alternative(
                        "STOP_EXHAUSTED_HIGH_VALUE_ASSETS",
                        "Remove exhausted commanders, cavalry, and artillery from cleanup activity.",
                        "Reduces immediate pursuit damage but protects future value.",
                    ),
                ],
                safe_exploiters,
                0.62,
                path_sensitive=True,
            )
        )

    if enemy_collapse in {"ROUT_CASCADE", "TERMINAL_COUNTDOWN", "TERMINAL"}:
        endangered = [
            unit["observed"]["stable_unit_id"]
            for unit in local_units
            if unit["derived"]["danger_score"] >= 0.40
            or unit["derived"]["fatigue_severity"] >= 0.75
            or unit["observed"]["routing"]
            or unit["observed"]["wavering"]
        ]
        opportunities.append(
            _battle_opportunity(
                state,
                "PURSUIT_TERMINATION_WINDOW",
                "Visible enemy resistance has entered a rout cascade; marginal cleanup value is lower than preservation and reformation value for endangered units.",
                [
                    _alternative(
                        "TERMINATE_GENERAL_PURSUIT",
                        "Stop endangered or exhausted units and reform the force.",
                        "Allows some routed models to escape; no campaign-capture effect is modeled.",
                    ),
                    _alternative(
                        "ALLOW_ONLY_SAFE_SPECIALIST_PURSUIT",
                        "Permit only healthy suitable units to pursue with strict distance and fatigue limits.",
                        "Still risks hidden threats or pathing failures.",
                    ),
                    _alternative(
                        "CEASE_LOW_VALUE_RANGED_FIRE",
                        "Preserve ammunition when remaining visible targets are shattered or strategically irrelevant.",
                        "May reduce final casualties inflicted.",
                    ),
                ],
                endangered,
                min(
                    1.0,
                    0.64
                    + 0.22 * battle["visible_enemy"]["routing_fraction"]
                    + 0.12 * battle["local_pressure_score"],
                ),
                path_sensitive=True,
            )
        )

        if endangered:
            opportunities.append(
                _battle_opportunity(
                    state,
                    "REFORM_AND_PRESERVE_WINDOW",
                    "The visible outcome is no longer improved primarily by broad engagement; formation recovery and survivor preservation now dominate.",
                    [
                        _alternative(
                            "REFORM_AROUND_COHERENT_CORE",
                            "Gather surviving coherent units around a defensible friendly core.",
                            "Reduces chase pressure and may leave distant units unsupported during reformation.",
                        ),
                        _alternative(
                            "EXTRACT_ENDANGERED_ASSETS",
                            "Prioritize characters and productive ranged or artillery assets for safe separation.",
                            "May sacrifice remaining pursuit opportunities.",
                        ),
                    ],
                    endangered,
                    0.68,
                    path_sensitive=True,
                )
            )
    return opportunities


def collect_tactical_opportunity_candidates(
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return all deterministic advisory candidates before legacy budget selection.

    This is an offline planner-development seam. It does not select or emit a game
    order and preserves the v0.1N evaluator's historical selection behavior.
    """
    if state["battle_state"]["local_stability_state"] == "TERMINAL":
        return []
    local = [unit for unit in state["units"] if unit["observed"]["local_alliance"]]
    enemy = [unit for unit in state["units"] if not unit["observed"]["local_alliance"]]
    candidates = _extract_unit_opportunities(state, local)
    candidates.extend(_extract_battle_opportunities(state, local, enemy))
    return sorted(
        candidates,
        key=lambda item: (
            -SEVERITY_RANK[item["severity"]],
            -item["utility_score"],
            item["opportunity_id"],
        ),
    )


def _select_opportunities(
    candidates: list[dict[str, Any]], previous_selected_keys: set[str]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = sorted(
        candidates,
        key=lambda item: (
            -SEVERITY_RANK[item["severity"]],
            -item["utility_score"],
            item["opportunity_id"],
        ),
    )
    selected = candidates[:MAX_SELECTED_OPPORTUNITIES_PER_SLICE]
    selected_keys = {item["opportunity_key"] for item in selected}
    candidate_critical = sum(item["severity"] == "CRITICAL" for item in candidates)
    selected_critical = sum(item["severity"] == "CRITICAL" for item in selected)
    return selected, {
        "maximum_advisory_changes_this_cycle": MAX_SELECTED_OPPORTUNITIES_PER_SLICE,
        "candidate_opportunity_count": len(candidates),
        "selected_opportunity_count": len(selected),
        "suppressed_opportunity_count": max(0, len(candidates) - len(selected)),
        "critical_opportunity_coverage": round(
            selected_critical / candidate_critical if candidate_critical else 1.0,
            6,
        ),
        "new_selected_opportunity_count": len(selected_keys - previous_selected_keys),
        "continued_selected_opportunity_count": len(selected_keys & previous_selected_keys),
        "retired_selected_opportunity_count": len(previous_selected_keys - selected_keys),
        "lifecycle_identity": "STABLE_OPPORTUNITY_KEY_NOT_SLICE_INSTANCE_ID",
        "reason": "bounded advisory workload; persistent priorities do not count as new commands at every sample",
    }


def evaluate_tactical_state(
    state: dict[str, Any], previous_evaluation: dict[str, Any] | None = None
) -> dict[str, Any]:
    local = [unit for unit in state["units"] if unit["observed"]["local_alliance"]]
    enemy = [unit for unit in state["units"] if not unit["observed"]["local_alliance"]]
    posture = _posture(state)

    local_priorities = [
        item for item in (_priority_for_local_unit(unit) for unit in local) if item
    ]
    local_priorities.sort(
        key=lambda item: (-item["preservation_score"], item["stable_unit_id"])
    )

    cleanup_mode = posture == "TERMINATE_WITH_PRESERVATION"
    visible_targets = [
        {
            "stable_unit_id": unit["observed"]["stable_unit_id"],
            "unit_type": unit["observed"]["unit_type"],
            "role": unit["observed"]["role"],
            "target_score": _visible_enemy_target_score(unit, cleanup_mode),
            "routing": unit["observed"]["routing"],
            "shattered": unit["observed"]["shattered"],
            "authority": "VISIBLE_TARGET_CANDIDATE_ONLY",
        }
        for unit in enemy
    ]
    visible_targets.sort(key=lambda item: (-item["target_score"], item["stable_unit_id"]))

    candidates = collect_tactical_opportunity_candidates(state)
    previous_selected_keys = {
        item["opportunity_key"]
        for item in (previous_evaluation or {}).get("selected_decision_opportunities", [])
    }
    selected, command_budget = _select_opportunities(candidates, previous_selected_keys)

    result: dict[str, Any] = {
        "schema_version": 3,
        "slice_id": state["slice_id"],
        "time_ms": state["time_ms"],
        "source_tactical_state_digest": state["result_digest"],
        "posture": posture,
        "local_stability_state": state["battle_state"]["local_stability_state"],
        "tactical_phase_state": state["battle_state"]["tactical_phase_state"],
        "visible_enemy_collapse_state": state["battle_state"][
            "visible_enemy_collapse_state"
        ],
        "outcome_state": state["battle_state"]["outcome_state"],
        "hidden_enemy_units": state["observation_scope"]["hidden_enemy_unit_count"],
        "local_preservation_priorities": local_priorities[:8],
        "visible_enemy_target_candidates": visible_targets[:8],
        "selected_decision_opportunities": selected,
        "command_budget": command_budget,
        "constraints": [
            "No game command is emitted.",
            "No hidden enemy identity or state is consumed.",
            "A target score is a comparative hypothesis, not a proven optimal target.",
            "Every proposed alternative is unexecuted and counterfactual-uncertain.",
            "Straight-line distance and withdrawal recoverability are not pathfinding proof.",
        ],
        "evidence_status": "HYPOTHESIS",
        "authority": "OFFLINE_SHADOW_EVALUATION_ONLY",
    }
    result["result_digest"] = digest(result)
    return result


def evaluate_trace_slice(slice_record: dict[str, Any]) -> dict[str, Any]:
    # Compatibility entrypoint for callers evaluating one isolated slice. Temporal
    # trend and priority-transition fields remain explicitly limited in this mode.
    trace = {
        "schema_version": 1,
        "corpus_id": "isolated-slice-compatibility",
        "tier": "4R",
        "fidelity_label": "OBSERVED_TRACE_SLICES_NOT_GOLD_POLICY",
        "evidence_status": "OBSERVED",
        "source": {
            "replay_sha256": "0" * 64,
            "raw_trans_battle_log_sha256": "0" * 64,
            "capture_verification_result_digest": "0" * 64,
            "dense_corpus_result_digest": "0" * 64,
            "raw_replay_committed": False,
            "raw_log_committed": False,
        },
        "battle_identity": {},
        "duration_ms": slice_record["time_ms"],
        "visibility_contract": "VISIBLE_TO_LOCAL_ALLIANCE_ONLY",
        "slices": [slice_record],
        "evaluation_questions": [],
        "forbidden_inferences": [],
    }
    trace["result_digest"] = digest(trace)
    # build_tactical_state_trajectory requires a valid multi-slice corpus, so this
    # compatibility path imports the single-state builder directly.
    from .tactical_state import build_tactical_state

    return evaluate_tactical_state(build_tactical_state(slice_record))


def _derive_loss_prevention_diagnoses(
    evaluations: list[dict[str, Any]], dense_corpus: dict[str, Any] | None
) -> list[dict[str, Any]]:
    if dense_corpus is None:
        return []
    dense_corpus = validate_observed_battle_corpus(dense_corpus)
    opportunities_by_unit: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for evaluation in evaluations:
        for opportunity in evaluation["selected_decision_opportunities"]:
            if opportunity["scope"] != "UNIT":
                continue
            for unit_id in opportunity["subject_unit_ids"]:
                opportunities_by_unit[unit_id].append(
                    (evaluation["time_ms"], opportunity)
                )

    diagnoses: list[dict[str, Any]] = []
    for unit in dense_corpus["battle"]["units"]:
        if not unit["local_alliance"]:
            continue
        initial = max(1, unit["initial_men"])
        casualty_ratio = unit["casualties_observed_lower_bound"] / initial
        final_hp = unit["last_observed_hitpoints_fraction"]
        severe = casualty_ratio >= 0.50 or final_hp < 0.25
        if not severe:
            continue
        windows = sorted(opportunities_by_unit.get(unit["stable_unit_id"], []))
        first_time = windows[0][0] if windows else None
        first_opportunity = windows[0][1] if windows else None
        final_time = unit.get("last_observed_time_ms")
        lead_time = (
            max(0, int(final_time) - first_time)
            if isinstance(final_time, int) and first_time is not None
            else None
        )
        recoverability = (
            first_opportunity["derived_metrics"]["withdrawal_recoverability_proxy"]
            if first_opportunity
            else None
        )
        plausible = (
            first_opportunity is not None
            and lead_time is not None
            and lead_time >= 15000
            and recoverability is not None
            and recoverability >= 0.35
        )
        diagnoses.append(
            {
                "stable_unit_id": unit["stable_unit_id"],
                "unit_type": unit["unit_type"],
                "role": unit["role"],
                "observed_severe_degradation": {
                    "casualty_lower_bound_ratio": round(casualty_ratio, 6),
                    "last_observed_hitpoints_fraction": final_hp,
                    "terminal_state_complete": bool(unit.get("terminal_state_observed")),
                },
                "first_selected_warning": (
                    {
                        "time_ms": first_time,
                        "opportunity_type": first_opportunity["opportunity_type"],
                        "warning_lead_time_ms": lead_time,
                        "withdrawal_recoverability_proxy": recoverability,
                    }
                    if first_opportunity
                    else None
                ),
                "preventability_assessment": (
                    "PLAUSIBLY_PREVENTABLE_SEVERITY"
                    if plausible
                    else "INSUFFICIENT_EVIDENCE_OF_PREVENTABLE_SEVERITY"
                ),
                "confidence": "MEDIUM" if plausible else "LOW",
                "counterfactual_status": "UNVERIFIED",
                "required_future_evidence": [
                    "accepted and executed intervention telemetry",
                    "terrain/pathfinding feasibility",
                    "matched battle cohorts or a calibrated tactical surrogate",
                ],
            }
        )
    diagnoses.sort(
        key=lambda item: (
            item["preventability_assessment"]
            != "PLAUSIBLY_PREVENTABLE_SEVERITY",
            item["role"],
            item["stable_unit_id"],
        )
    )
    return diagnoses


def _command_budget_analysis(
    evaluations: list[dict[str, Any]], dense_corpus: dict[str, Any] | None
) -> dict[str, Any]:
    total_candidates = sum(
        item["command_budget"]["candidate_opportunity_count"]
        for item in evaluations
    )
    total_selected = sum(
        item["command_budget"]["selected_opportunity_count"]
        for item in evaluations
    )
    advisory_transitions = sum(
        item["command_budget"]["new_selected_opportunity_count"]
        + item["command_budget"]["retired_selected_opportunity_count"]
        for item in evaluations
    )
    continued_priorities = sum(
        item["command_budget"]["continued_selected_opportunity_count"]
        for item in evaluations
    )
    critical_coverage = min(
        (
            item["command_budget"]["critical_opportunity_coverage"]
            for item in evaluations
        ),
        default=1.0,
    )
    result: dict[str, Any] = {
        "candidate_opportunity_count": total_candidates,
        "selected_opportunity_count": total_selected,
        "advisory_priority_transition_count": advisory_transitions,
        "continued_advisory_priority_count": continued_priorities,
        "lifecycle_identity": "STABLE_OPPORTUNITY_KEY_NOT_SLICE_INSTANCE_ID",
        "maximum_selected_in_one_slice": max(
            (
                item["command_budget"]["selected_opportunity_count"]
                for item in evaluations
            ),
            default=0,
        ),
        "minimum_critical_opportunity_coverage": round(critical_coverage, 6),
        "efficiency_interpretation": (
            "Measures selectivity and high-severity coverage only; it does not prove fewer commands would win or reduce casualties."
        ),
    }
    if dense_corpus is not None:
        dense_corpus = validate_observed_battle_corpus(dense_corpus)
        raw_count = dense_corpus["battle"]["command_analysis"]["command_event_count"]
        result.update(
            {
                "observed_owner_command_event_reference": raw_count,
                "advisory_transition_to_owner_command_ratio": round(
                    advisory_transitions / raw_count if raw_count else 0.0, 6
                ),
                "comparison_status": "REFERENCE_ONLY_NOT_CAUSAL",
            }
        )
    return result


def run_trace_shadow_evaluator(
    trace_corpus: dict[str, Any], dense_corpus: dict[str, Any] | None = None
) -> dict[str, Any]:
    trajectory = build_tactical_state_trajectory(trace_corpus)
    if dense_corpus is not None:
        dense_corpus = validate_observed_battle_corpus(dense_corpus)
        if dense_corpus["result_digest"] != trace_corpus["source"][
            "dense_corpus_result_digest"
        ]:
            raise ValueError("dense corpus does not match trace-slice source digest")

    evaluations: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for state in trajectory["states"]:
        evaluation = evaluate_tactical_state(state, previous)
        evaluations.append(evaluation)
        previous = evaluation

    result: dict[str, Any] = {
        "schema_version": 3,
        "tier": "4R-SHADOW",
        "fidelity_label": "DETERMINISTIC_OFFLINE_ADVISER_OVER_OBSERVED_TRACE",
        "trace_corpus_id": trajectory["trace_corpus_id"],
        "source_trace_digest": trajectory["source_trace_digest"],
        "tactical_state_trajectory_digest": trajectory["result_digest"],
        "tactical_state_contract": trajectory["trajectory_contract"],
        "input_validation_contract": trajectory["input_validation_contract"],
        "evaluations": evaluations,
        "command_budget_analysis": _command_budget_analysis(
            evaluations, dense_corpus
        ),
        "loss_prevention_diagnoses": _derive_loss_prevention_diagnoses(
            evaluations, dense_corpus
        ),
        "quality_measurement_contract": {
            "independent_of_victory": [
                "high-value asset preservation",
                "time spent in avoidable high danger",
                "frontline and morale stability",
                "reserve commitment timing",
                "ammunition and ranged-output preservation",
                "pursuit termination discipline",
                "high-severity opportunity coverage",
                "advisory priority churn",
            ],
            "not_yet_measurable": [
                "causal casualty reduction from a proposed alternative",
                "accepted-command latency",
                "pathfinding success",
                "ordinary live battle generalization",
                "SFO generalization",
            ],
        },
        "architecture_allocation": {
            "constraints": [
                "visibility",
                "authority",
                "privacy",
                "legality",
                "counterfactual uncertainty",
            ],
            "utility": [
                "asset value",
                "danger",
                "recoverability",
                "marginal engagement value",
                "visible target threat",
            ],
            "state_machines": [
                "local stability",
                "visible enemy collapse",
                "pursuit termination",
            ],
            "assignment": [
                "reserve suitability",
                "screening candidates",
                "safe pursuit candidates",
            ],
            "deferred": {
                "behavior_trees": "defer until battle execution primitives and acknowledgement exist",
                "htn_or_search": "defer until a calibrated transition model can compare multi-step alternatives",
                "learning": "defer until heterogeneous battle cohorts and deterministic baselines exist",
            },
        },
        "evidence_status": "HYPOTHESIS",
        "authority": "NO_ORDERS",
        "warnings": [
            "This evaluator has not controlled or influenced WH3.",
            "The owner trace is not a gold policy label.",
            "Scores are designed for falsification and regression, not tactical-quality claims.",
            "Plausibly preventable severity is not proof that an alternative would improve the battle.",
        ],
    }
    result["result_digest"] = digest(result)
    return result
