from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_WEIGHTS = {
    "urgency": 2.0,
    "strategic_value": 1.25,
    "feasibility": 2.25,
    "continuity": 0.8,
    "recovery_need": 1.5,
    "travel_cost": -0.9,
    "overconcentration": -1.4,
}


def normalized_profile(profile: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(profile)
    result.setdefault("schema_version", 1)
    result.setdefault("compatibility_status", "UNVERIFIED")
    result.setdefault("weights", {})
    result["weights"] = {**DEFAULT_WEIGHTS, **result["weights"]}
    result.setdefault("target_capacity", 2)
    result.setdefault("minimum_attack_ratio", 0.82)
    result.setdefault("minimum_capture_ratio", 0.90)
    result.setdefault("replenish_threshold", 0.64)
    result.setdefault("continuity_turns", 3)
    return result
