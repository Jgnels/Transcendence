from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

from .canonical import digest

ROLE_TARGET_PRIORITY = {
    "artillery": ["artillery", "ranged", "frontline", "cavalry", "reserve"],
    "ranged": ["cavalry", "frontline", "ranged", "reserve", "artillery"],
    "cavalry": ["ranged", "artillery", "reserve", "frontline", "cavalry"],
    "frontline": ["frontline", "reserve", "cavalry", "ranged", "artillery"],
    "reserve": ["cavalry", "frontline", "reserve", "ranged", "artillery"],
}


def _validate(scenario: dict[str, Any]) -> None:
    required = {"schema_version", "scenario_id", "sides", "max_ticks"}
    missing = required - scenario.keys()
    if missing:
        raise ValueError(f"battle scenario missing: {sorted(missing)}")
    if len(scenario["sides"]) != 2:
        raise ValueError("battle surrogate currently requires exactly two sides")
    for side in scenario["sides"]:
        if not side.get("units"):
            raise ValueError("each side requires units")


def _choose_target(unit: dict[str, Any], enemies: list[dict[str, Any]]) -> dict[str, Any] | None:
    alive = [enemy for enemy in enemies if enemy["hp"] > 0]
    if not alive:
        return None
    priorities = ROLE_TARGET_PRIORITY.get(unit["role"], ROLE_TARGET_PRIORITY["frontline"])
    return min(
        alive,
        key=lambda enemy: (
            priorities.index(enemy["role"]) if enemy["role"] in priorities else len(priorities),
            enemy["hp"],
            enemy["id"],
        ),
    )


def run_battle(raw_scenario: dict[str, Any], seed: int) -> dict[str, Any]:
    _validate(raw_scenario)
    scenario = deepcopy(raw_scenario)
    rng = random.Random(seed)
    sides = scenario["sides"]
    idle_actions = 0
    reserve_commit_tick: dict[str, int] = {}
    actions: list[dict[str, Any]] = []
    for tick in range(1, scenario["max_ticks"] + 1):
        for side_index, side in enumerate(sides):
            enemy = sides[1 - side_index]
            for unit in sorted(side["units"], key=lambda item: item["id"]):
                if unit["hp"] <= 0 or unit["morale"] <= 0:
                    continue
                if unit["role"] == "reserve" and tick < unit.get("commit_tick", 6):
                    idle_actions += 1
                    continue
                if unit["role"] == "reserve" and unit["id"] not in reserve_commit_tick:
                    reserve_commit_tick[unit["id"]] = tick
                target = _choose_target(unit, enemy["units"])
                if target is None:
                    idle_actions += 1
                    continue
                ranged_multiplier = 1.0
                if unit["role"] in {"ranged", "artillery"}:
                    if unit.get("ammo", 0) <= 0:
                        ranged_multiplier = 0.35
                    else:
                        unit["ammo"] -= 1
                        ranged_multiplier = 1.2
                flank_multiplier = 1.22 if unit["role"] == "cavalry" and target["role"] in {"ranged", "artillery"} else 1.0
                variance = rng.uniform(0.85, 1.15)
                damage = max(0.2, (unit["attack"] * ranged_multiplier * flank_multiplier * variance) - target["defense"] * 0.35)
                target["hp"] = max(0.0, target["hp"] - damage)
                target["morale"] = max(0.0, target["morale"] - damage * 0.12)
                actions.append({"tick": tick, "unit": unit["id"], "target": target["id"], "damage": round(damage, 4)})
        alive_sides = [side for side in sides if any(unit["hp"] > 0 and unit["morale"] > 0 for unit in side["units"])]
        if len(alive_sides) <= 1:
            break
    remaining = {
        side["id"]: round(sum(max(0.0, unit["hp"]) for unit in side["units"]), 4)
        for side in sides
    }
    winner = max(remaining, key=lambda key: (remaining[key], key))
    result = {
        "schema_version": 1,
        "tier": 4,
        "fidelity_label": "UNCALIBRATED_TACTICAL_SURROGATE",
        "scenario_id": scenario["scenario_id"],
        "seed": seed,
        "winner": winner,
        "remaining_hp": remaining,
        "idle_actions": idle_actions,
        "reserve_commit_tick": reserve_commit_tick,
        "actions": actions,
        "warnings": ["Not calibrated against WH3 pathing, animation, collision, morale, spells, or battle AI."],
        "evidence_status": "HYPOTHESIS",
    }
    result["result_digest"] = digest(result)
    return result
