from __future__ import annotations

from copy import deepcopy
from typing import Any

PROHIBITED_KEY_FRAGMENTS = {
    "api_key",
    "secret",
    "password",
    "token",
    "absolute_path",
    "local_path",
    "save_path",
    "user_profile",
}

ALLOWED_OBJECTIVES = {
    "DEFEND_REGION",
    "RELIEVE_SIEGE",
    "ATTACK_ARMY",
    "CAPTURE_REGION",
    "REPLENISH",
    "HOLD",
}


class ContractError(ValueError):
    pass


def _walk_for_prohibited(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in PROHIBITED_KEY_FRAGMENTS):
                raise ContractError(f"prohibited private field at {path}.{key}")
            _walk_for_prohibited(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_for_prohibited(child, f"{path}[{index}]")


def _require(mapping: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys - mapping.keys())
    if missing:
        raise ContractError(f"{label} missing required fields: {', '.join(missing)}")


def validate_campaign_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    _walk_for_prohibited(scenario)
    _require(
        scenario,
        {"schema_version", "scenario_id", "turn", "controlled_faction", "armies", "regions", "wars"},
        "scenario",
    )
    if scenario["schema_version"] != 1:
        raise ContractError("unsupported campaign scenario schema_version")
    if not isinstance(scenario["turn"], int) or scenario["turn"] < 1:
        raise ContractError("turn must be a positive integer")
    army_ids: set[str] = set()
    for army in scenario["armies"]:
        _require(
            army,
            {"id", "faction", "strength", "x", "y", "movement", "replenishment", "visible_to"},
            "army",
        )
        if army["id"] in army_ids:
            raise ContractError(f"duplicate army id: {army['id']}")
        army_ids.add(army["id"])
        if army["strength"] < 0 or army["movement"] < 0:
            raise ContractError("army strength and movement must be non-negative")
        if not 0 <= army["replenishment"] <= 1:
            raise ContractError("army replenishment must be within [0, 1]")
        current = army.get("current_objective")
        if current is not None and current.get("type") not in ALLOWED_OBJECTIVES:
            raise ContractError(f"unsupported current objective: {current.get('type')}")
    region_ids: set[str] = set()
    for region in scenario["regions"]:
        _require(
            region,
            {"id", "owner", "x", "y", "value", "threat", "under_siege", "garrison_strength"},
            "region",
        )
        if region["id"] in region_ids:
            raise ContractError(f"duplicate region id: {region['id']}")
        region_ids.add(region["id"])
        if region["value"] < 0 or region["threat"] < 0 or region["garrison_strength"] < 0:
            raise ContractError("region numeric values must be non-negative")
    for war in scenario["wars"]:
        if not isinstance(war, list) or len(war) != 2 or war[0] == war[1]:
            raise ContractError("wars must contain two distinct faction ids")
    return deepcopy(scenario)


def visible_scenario(scenario: dict[str, Any], observer: str) -> dict[str, Any]:
    """Return an observer-safe snapshot; hidden enemy armies never reach planners."""
    clean = deepcopy(scenario)
    clean["armies"] = [
        army
        for army in clean["armies"]
        if army["faction"] == observer or observer in army.get("visible_to", [])
    ]
    return clean
