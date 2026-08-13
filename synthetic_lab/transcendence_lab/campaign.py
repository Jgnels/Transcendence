from __future__ import annotations

import math
import random
from copy import deepcopy
from typing import Any

from .canonical import digest
from .contracts import validate_campaign_scenario
from .decision import assign_objectives
from .profiles import normalized_profile


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def _move_toward(army: dict[str, Any], target: dict[str, Any]) -> None:
    dx = float(target["x"]) - float(army["x"])
    dy = float(target["y"]) - float(army["y"])
    distance = math.hypot(dx, dy)
    if distance <= 0:
        return
    step = min(float(army["movement"]), distance)
    army["x"] += dx / distance * step
    army["y"] += dy / distance * step


def run_campaign(
    raw_scenario: dict[str, Any],
    raw_profile: dict[str, Any],
    turns: int,
    seed: int,
) -> dict[str, Any]:
    if turns < 1:
        raise ValueError("turns must be positive")
    state = validate_campaign_scenario(raw_scenario)
    profile = normalized_profile(raw_profile)
    rng = random.Random(seed)
    history: list[dict[str, Any]] = []
    objective_changes = 0
    total_controlled_army_turns = 0
    hold_turns = 0
    captures = 0
    battles = 0
    previous: dict[str, tuple[str, str | None]] = {}

    for _ in range(turns):
        decision = assign_objectives(state, profile)
        targets = {region["id"]: region for region in state["regions"]}
        targets.update({army["id"]: army for army in state["armies"]})
        turn_events: list[dict[str, Any]] = []
        for assignment in decision["assignments"]:
            army = next(a for a in state["armies"] if a["id"] == assignment["army_id"])
            objective = assignment["objective"]
            signature = (objective["type"], objective["target_id"])
            if army["id"] in previous and previous[army["id"]] != signature:
                objective_changes += 1
            previous[army["id"]] = signature
            total_controlled_army_turns += 1
            if objective["type"] == "HOLD":
                hold_turns += 1
                army["replenishment"] = min(1.0, army["replenishment"] + 0.04)
                continue
            target = targets.get(objective["target_id"])
            if target is None:
                continue
            _move_toward(army, target)
            if objective["type"] == "REPLENISH" and _distance(army, target) <= 0.01:
                army["replenishment"] = min(1.0, army["replenishment"] + 0.22)
                army["strength"] *= 1.03
            elif objective["type"] in {"DEFEND_REGION", "RELIEVE_SIEGE"} and _distance(army, target) <= 0.01:
                target["threat"] = max(0.0, target["threat"] - army["strength"] / 250.0)
                if target["threat"] < 0.15:
                    target["under_siege"] = False
            elif objective["type"] == "CAPTURE_REGION" and _distance(army, target) <= 0.01:
                battles += 1
                uncertainty = rng.uniform(0.88, 1.12)
                if army["strength"] * uncertainty >= target["garrison_strength"]:
                    old_owner = target["owner"]
                    target["owner"] = army["faction"]
                    target["threat"] = 0.1
                    target["under_siege"] = False
                    army["strength"] *= rng.uniform(0.82, 0.94)
                    captures += 1
                    turn_events.append({"type": "REGION_CAPTURED", "region": target["id"], "from": old_owner})
                else:
                    army["strength"] *= rng.uniform(0.55, 0.78)
            elif objective["type"] == "ATTACK_ARMY" and _distance(army, target) <= 0.01:
                battles += 1
                uncertainty = rng.uniform(0.82, 1.18)
                if army["strength"] * uncertainty >= target["strength"]:
                    army["strength"] *= rng.uniform(0.78, 0.93)
                    target["strength"] = 0.0
                    turn_events.append({"type": "ARMY_DEFEATED", "army": target["id"]})
                else:
                    target["strength"] *= rng.uniform(0.78, 0.93)
                    army["strength"] *= rng.uniform(0.5, 0.76)
        state["armies"] = [army for army in state["armies"] if army["strength"] >= 8.0]
        for region in state["regions"]:
            if region["owner"] == state["controlled_faction"]:
                region["threat"] = min(1.5, max(0.0, region["threat"] + rng.uniform(-0.04, 0.08)))
        state["turn"] += 1
        history.append(
            {
                "turn": state["turn"],
                "decision_digest": decision["result_digest"],
                "events": turn_events,
                "state_digest": digest(state),
            }
        )

    controlled_regions = sum(1 for region in state["regions"] if region["owner"] == state["controlled_faction"])
    controlled_armies = sum(1 for army in state["armies"] if army["faction"] == state["controlled_faction"])
    metrics = {
        "objective_changes": objective_changes,
        "objective_churn_rate": round(objective_changes / max(total_controlled_army_turns, 1), 6),
        "hold_rate": round(hold_turns / max(total_controlled_army_turns, 1), 6),
        "captures": captures,
        "battles": battles,
        "controlled_regions_final": controlled_regions,
        "controlled_armies_final": controlled_armies,
    }
    result = {
        "schema_version": 1,
        "tier": 2,
        "fidelity_label": "UNCALIBRATED_OPERATIONAL_SURROGATE",
        "scenario_id": state["scenario_id"],
        "seed": seed,
        "turns": turns,
        "profile_id": profile.get("profile_id", "unnamed"),
        "metrics": metrics,
        "history": history,
        "final_state_digest": digest(state),
        "warnings": ["Comparative synthetic result only; not a WH3 outcome prediction."],
        "evidence_status": "HYPOTHESIS",
    }
    result["result_digest"] = digest(result)
    return result
