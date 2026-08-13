from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from .canonical import digest
from .contracts import validate_campaign_scenario, visible_scenario
from .profiles import normalized_profile


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def _at_war(wars: list[list[str]], a: str, b: str) -> bool:
    return [a, b] in wars or [b, a] in wars


def _candidate(
    army: dict[str, Any],
    objective_type: str,
    target_id: str | None,
    components: dict[str, float],
    rationale: list[str],
) -> dict[str, Any]:
    return {
        "army_id": army["id"],
        "type": objective_type,
        "target_id": target_id,
        "components": components,
        "rationale": rationale,
    }


def generate_candidates(
    scenario: dict[str, Any],
    army: dict[str, Any],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    faction = army["faction"]
    candidates: list[dict[str, Any]] = []
    current = army.get("current_objective") or {}

    candidates.append(
        _candidate(
            army,
            "HOLD",
            None,
            {
                "urgency": 0.05,
                "strategic_value": 0.1,
                "feasibility": 1.0,
                "continuity": 0.2 if current.get("type") == "HOLD" else 0.0,
                "recovery_need": max(0.0, 1.0 - army["replenishment"]) * 0.2,
                "travel_cost": 0.0,
            },
            ["safe deterministic fallback"],
        )
    )

    if army["replenishment"] < profile["replenish_threshold"]:
        owned = [region for region in scenario["regions"] if region["owner"] == faction]
        nearest = min(owned, key=lambda region: (_distance(army, region), region["id"]), default=None)
        if nearest:
            distance = _distance(army, nearest)
            candidates.append(
                _candidate(
                    army,
                    "REPLENISH",
                    nearest["id"],
                    {
                        "urgency": 1.0 - army["replenishment"],
                        "strategic_value": nearest["value"] * 0.15,
                        "feasibility": 1.0,
                        "continuity": 0.7 if current.get("type") == "REPLENISH" else 0.0,
                        "recovery_need": 1.0 - army["replenishment"],
                        "travel_cost": distance / max(army["movement"], 1.0),
                    },
                    ["army is below replenishment threshold", f"nearest friendly region is {nearest['id']}"],
                )
            )

    for region in scenario["regions"]:
        distance = _distance(army, region)
        travel = distance / max(army["movement"], 1.0)
        if region["owner"] == faction and (region["under_siege"] or region["threat"] > 0.25):
            objective_type = "RELIEVE_SIEGE" if region["under_siege"] else "DEFEND_REGION"
            ratio = army["strength"] / max(region["garrison_strength"] + region["threat"] * 100.0, 1.0)
            candidates.append(
                _candidate(
                    army,
                    objective_type,
                    region["id"],
                    {
                        "urgency": min(1.5, region["threat"] + (0.8 if region["under_siege"] else 0.0)),
                        "strategic_value": region["value"],
                        "feasibility": min(1.5, ratio),
                        "continuity": 0.8 if current.get("target_id") == region["id"] else 0.0,
                        "recovery_need": 0.0,
                        "travel_cost": travel,
                    },
                    ["friendly region is threatened", "siege relief prioritized" if region["under_siege"] else "defensive pressure detected"],
                )
            )
        elif region["owner"] != faction and _at_war(scenario["wars"], faction, region["owner"]):
            ratio = army["strength"] / max(region["garrison_strength"], 1.0)
            if ratio >= profile["minimum_capture_ratio"]:
                candidates.append(
                    _candidate(
                        army,
                        "CAPTURE_REGION",
                        region["id"],
                        {
                            "urgency": min(1.0, region["threat"] * 0.5 + 0.15),
                            "strategic_value": region["value"],
                            "feasibility": min(1.5, ratio),
                            "continuity": 0.8 if current.get("target_id") == region["id"] else 0.0,
                            "recovery_need": 0.0,
                            "travel_cost": travel,
                        },
                        ["enemy region is a legal war target", f"estimated force ratio {ratio:.2f}"],
                    )
                )

    for target in scenario["armies"]:
        if target["faction"] == faction or not _at_war(scenario["wars"], faction, target["faction"]):
            continue
        distance = _distance(army, target)
        ratio = army["strength"] / max(target["strength"], 1.0)
        if ratio >= profile["minimum_attack_ratio"]:
            candidates.append(
                _candidate(
                    army,
                    "ATTACK_ARMY",
                    target["id"],
                    {
                        "urgency": 0.35 + min(0.8, target["strength"] / 150.0),
                        "strategic_value": min(1.5, target["strength"] / 100.0),
                        "feasibility": min(1.5, ratio),
                        "continuity": 0.8 if current.get("target_id") == target["id"] else 0.0,
                        "recovery_need": 0.0,
                        "travel_cost": distance / max(army["movement"], 1.0),
                    },
                    ["visible enemy army is a legal war target", f"estimated force ratio {ratio:.2f}"],
                )
            )
    return candidates


def _score(candidate: dict[str, Any], weights: dict[str, float], existing_assignments: int) -> float:
    components = candidate["components"]
    score = 0.0
    for key, weight in weights.items():
        if key == "overconcentration":
            score += weight * max(0, existing_assignments - 1)
        else:
            score += weight * float(components.get(key, 0.0))
    return round(score, 6)


def assign_objectives(
    raw_scenario: dict[str, Any],
    raw_profile: dict[str, Any],
) -> dict[str, Any]:
    scenario = validate_campaign_scenario(raw_scenario)
    profile = normalized_profile(raw_profile)
    observer = scenario["controlled_faction"]
    scenario = visible_scenario(scenario, observer)
    controlled = sorted(
        [army for army in scenario["armies"] if army["faction"] == observer],
        key=lambda army: (-army["strength"], army["id"]),
    )
    assignments: list[dict[str, Any]] = []
    target_counts: dict[str, int] = {}
    for army in controlled:
        scored: list[dict[str, Any]] = []
        for candidate in generate_candidates(scenario, army, profile):
            target_key = candidate["target_id"] or "__hold__"
            count = target_counts.get(target_key, 0)
            scored_candidate = deepcopy(candidate)
            scored_candidate["score"] = _score(candidate, profile["weights"], count)
            scored.append(scored_candidate)
        scored.sort(key=lambda item: (-item["score"], item["type"], item["target_id"] or ""))
        chosen = next(
            (
                item
                for item in scored
                if item["target_id"] is None
                or target_counts.get(item["target_id"], 0) < profile["target_capacity"]
            ),
            scored[0],
        )
        if chosen["target_id"] is not None:
            target_counts[chosen["target_id"]] = target_counts.get(chosen["target_id"], 0) + 1
        assignments.append(
            {
                "army_id": army["id"],
                "objective": {"type": chosen["type"], "target_id": chosen["target_id"]},
                "score": chosen["score"],
                "components": chosen["components"],
                "rationale": chosen["rationale"],
                "alternatives": [
                    {"type": item["type"], "target_id": item["target_id"], "score": item["score"]}
                    for item in scored[1:4]
                ],
            }
        )
    result = {
        "schema_version": 1,
        "tier": 1,
        "fidelity_label": "DECISION_QUALITY_HYPOTHESIS",
        "scenario_id": scenario["scenario_id"],
        "scenario_digest": digest(scenario),
        "profile_id": profile.get("profile_id", "unnamed"),
        "profile_digest": digest(profile),
        "assignments": assignments,
        "warnings": ["No campaign-outcome claim; Tier 1 evaluates one decision frame only."],
        "evidence_status": "HYPOTHESIS",
    }
    result["result_digest"] = digest(result)
    return result
