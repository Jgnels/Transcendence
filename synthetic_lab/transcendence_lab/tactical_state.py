from __future__ import annotations

import math
from typing import Any

from .battle_trace import TACTICAL_TRACE_INPUT_CONTRACT, validate_battle_trace_slices
from .canonical import digest


FATIGUE_SEVERITY = {
    "threshold_fresh": 0.0,
    "threshold_active": 0.1,
    "threshold_winded": 0.35,
    "threshold_tired": 0.55,
    "threshold_very_tired": 0.75,
    "threshold_exhausted": 1.0,
}

ROLE_POLICIES: dict[str, dict[str, float]] = {
    "commander": {
        "asset_base": 0.90,
        "preserve_hp": 0.45,
        "emergency_hp": 0.25,
        "preserve_models": 1.00,
        "engagement_weight": 0.75,
    },
    "artillery": {
        "asset_base": 0.84,
        "preserve_hp": 0.45,
        "emergency_hp": 0.25,
        "preserve_models": 0.75,
        "engagement_weight": 0.65,
    },
    "ranged": {
        "asset_base": 0.72,
        "preserve_hp": 0.40,
        "emergency_hp": 0.22,
        "preserve_models": 0.60,
        "engagement_weight": 0.85,
    },
    "cavalry": {
        "asset_base": 0.70,
        "preserve_hp": 0.40,
        "emergency_hp": 0.22,
        "preserve_models": 0.62,
        "engagement_weight": 0.90,
    },
    "frontline": {
        "asset_base": 0.50,
        "preserve_hp": 0.28,
        "emergency_hp": 0.15,
        "preserve_models": 0.38,
        "engagement_weight": 1.00,
    },
    "unknown": {
        "asset_base": 0.50,
        "preserve_hp": 0.35,
        "emergency_hp": 0.20,
        "preserve_models": 0.50,
        "engagement_weight": 0.90,
    },
}

LOCAL_SUPPORT_RADIUS_M = 90.0
VISIBLE_PRESSURE_RADIUS_M = 90.0


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _rounded(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def _number(value: object, default: float = 0.0) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return default


def _model_fraction(unit: dict[str, Any]) -> float:
    initial = _number(unit.get("initial_men"), 0.0)
    alive = _number(unit.get("men_alive"), initial)
    if initial > 1.0:
        return _clamp(alive / initial)
    explicit = unit.get("men_fraction")
    if isinstance(explicit, (int, float)):
        return _clamp(float(explicit))
    return 1.0


def _hitpoints_fraction(unit: dict[str, Any]) -> float:
    return _clamp(_number(unit.get("hitpoints_fraction"), 1.0))


def _ammo_fraction(unit: dict[str, Any]) -> float | None:
    start = _number(unit.get("starting_ammo"), 0.0)
    if start <= 0.0:
        return None
    return _clamp(_number(unit.get("ammo"), 0.0) / start)


def _fatigue_severity(unit: dict[str, Any]) -> float:
    return FATIGUE_SEVERITY.get(str(unit.get("fatigue", "")), 0.5)


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    # WH3 horizontal tactical distance is represented by x/z. Elevation is retained
    # in the canonical state but is not treated as path length.
    dx = _number(a.get("position_x")) - _number(b.get("position_x"))
    dz = _number(a.get("position_z")) - _number(b.get("position_z"))
    return math.hypot(dx, dz)


def _nearest_distance(unit: dict[str, Any], candidates: list[dict[str, Any]]) -> float | None:
    distances = [_distance(unit, other) for other in candidates if other is not unit]
    return min(distances) if distances else None


def _count_within(
    unit: dict[str, Any], candidates: list[dict[str, Any]], radius: float
) -> int:
    return sum(
        1
        for other in candidates
        if other is not unit and _distance(unit, other) <= radius
    )


def _asset_value_score(unit: dict[str, Any]) -> float:
    role = str(unit.get("role", "unknown"))
    policy = ROLE_POLICIES.get(role, ROLE_POLICIES["unknown"])
    proxy = _number(unit.get("initial_strategic_value_proxy"), 400.0)
    proxy_component = 0.18 * _clamp(proxy / 1800.0)
    special_component = 0.04 * _clamp(
        _number(unit.get("num_special_abilities"), 0.0) / 4.0
    )
    ammo = _ammo_fraction(unit)
    output_component = 0.0
    if role in {"ranged", "artillery"} and ammo is not None:
        output_component = 0.08 * ammo
    return _clamp(policy["asset_base"] + proxy_component + special_component + output_component)


def _danger_score(
    unit: dict[str, Any],
    friendly_support_count: int,
    visible_enemy_pressure_count: int,
) -> float:
    hp_loss = 1.0 - _hitpoints_fraction(unit)
    model_loss = 1.0 - _model_fraction(unit)
    fatigue = _fatigue_severity(unit)
    flank_count = sum(
        bool(unit.get(key))
        for key in (
            "left_flank_threatened",
            "right_flank_threatened",
            "rear_flank_threatened",
        )
    )
    score = 0.27 * hp_loss + 0.22 * model_loss + 0.10 * fatigue
    score += 0.32 if unit.get("shattered") else 0.0
    score += 0.22 if unit.get("routing") else 0.0
    score += 0.12 if unit.get("wavering") else 0.0
    score += 0.07 if unit.get("under_missile_attack") else 0.0
    score += 0.05 if unit.get("in_melee") else 0.0
    score += 0.05 * flank_count
    score += min(0.14, 0.035 * visible_enemy_pressure_count)
    score -= min(0.10, 0.025 * friendly_support_count)
    if unit.get("leaving"):
        score += 0.08
    if unit.get("rampaging"):
        score += 0.08
    return _clamp(score)


def _withdrawal_recoverability(
    unit: dict[str, Any],
    friendly_support_count: int,
    visible_enemy_pressure_count: int,
) -> float:
    score = 0.78
    score += min(0.18, 0.045 * friendly_support_count)
    score -= min(0.28, 0.07 * visible_enemy_pressure_count)
    score -= 0.18 * _fatigue_severity(unit)
    score -= 0.18 * (1.0 - _hitpoints_fraction(unit))
    score -= 0.16 * (1.0 - _model_fraction(unit))
    score -= 0.35 if unit.get("routing") else 0.0
    score -= 0.55 if unit.get("shattered") else 0.0
    score -= 0.20 if unit.get("leaving") else 0.0
    score += 0.04 if unit.get("moving") else 0.0
    return _clamp(score)


def _engagement_value(
    unit: dict[str, Any], danger_score: float, asset_value_score: float
) -> float:
    role = str(unit.get("role", "unknown"))
    policy = ROLE_POLICIES.get(role, ROLE_POLICIES["unknown"])
    ammo = _ammo_fraction(unit)
    ammo_factor = 1.0 if ammo is None else 0.55 + 0.45 * ammo
    combat_power = (
        0.43 * _hitpoints_fraction(unit)
        + 0.37 * _model_fraction(unit)
        + 0.10 * (1.0 - _fatigue_severity(unit))
        + 0.10 * ammo_factor
    )
    preservation_penalty = danger_score * (0.35 + 0.45 * asset_value_score)
    return _clamp(
        combat_power * policy["engagement_weight"] - preservation_penalty
    )


def _canonical_observed_unit(unit: dict[str, Any]) -> dict[str, Any]:
    return {
        "stable_unit_id": unit["stable_unit_id"],
        "unit_type": unit["unit_type"],
        "unit_class": unit.get("unit_class"),
        "role": unit.get("role", "unknown"),
        "local_alliance": bool(unit.get("local_alliance")),
        "visibility_source": unit.get("visibility_source"),
        "position": {
            "x": _rounded(_number(unit.get("position_x"))),
            "y": _rounded(_number(unit.get("position_y"))),
            "z": _rounded(_number(unit.get("position_z"))),
        },
        "ordered_position": {
            "x": _rounded(_number(unit.get("ordered_position_x"))),
            "y": _rounded(_number(unit.get("ordered_position_y"))),
            "z": _rounded(_number(unit.get("ordered_position_z"))),
        },
        "bearing": _rounded(_number(unit.get("bearing"))),
        "ordered_bearing": _rounded(_number(unit.get("ordered_bearing"))),
        "ordered_width": _rounded(_number(unit.get("ordered_width"))),
        "hitpoints_fraction": _rounded(_hitpoints_fraction(unit)),
        "initial_men": int(_number(unit.get("initial_men"), 0.0)),
        "men_alive": int(_number(unit.get("men_alive"), 0.0)),
        "men_fraction": _rounded(_model_fraction(unit)),
        "ammo": int(_number(unit.get("ammo"), 0.0)),
        "starting_ammo": int(_number(unit.get("starting_ammo"), 0.0)),
        "fatigue": unit.get("fatigue"),
        "idle": bool(unit.get("idle")),
        "moving": bool(unit.get("moving")),
        "moving_fast": bool(unit.get("moving_fast")),
        "in_melee": bool(unit.get("in_melee")),
        "routing": bool(unit.get("routing")),
        "shattered": bool(unit.get("shattered")),
        "wavering": bool(unit.get("wavering")),
        "leaving": bool(unit.get("leaving")),
        "rampaging": bool(unit.get("rampaging")),
        "under_missile_attack": bool(unit.get("under_missile_attack")),
        "left_flank_threatened": bool(unit.get("left_flank_threatened")),
        "right_flank_threatened": bool(unit.get("right_flank_threatened")),
        "rear_flank_threatened": bool(unit.get("rear_flank_threatened")),
        "current_target_id": unit.get("current_target_id"),
        "current_target_distance": _rounded(
            _number(unit.get("current_target_distance"), -1.0)
        ),
        "current_target_in_range": bool(unit.get("current_target_in_range")),
        "missile_range": _rounded(_number(unit.get("missile_range"))),
        "is_commander": bool(unit.get("is_commander")),
        "num_special_abilities": int(
            _number(unit.get("num_special_abilities"), 0.0)
        ),
        "strategic_value_proxy": _rounded(
            _number(unit.get("strategic_value_proxy"), 0.0)
        ),
        "initial_strategic_value_proxy": _rounded(
            _number(unit.get("initial_strategic_value_proxy"), 0.0)
        ),
    }


def _unit_trend(
    observed: dict[str, Any],
    derived: dict[str, Any],
    previous_unit: dict[str, Any] | None,
) -> dict[str, Any]:
    if previous_unit is None:
        return {
            "status": "NEWLY_OBSERVED",
            "hitpoints_delta": None,
            "model_fraction_delta": None,
            "danger_delta": None,
            "new_routing": False,
            "new_shattered": False,
            "danger_persistent": False,
        }
    previous_observed = previous_unit["observed"]
    previous_derived = previous_unit["derived"]
    hp_delta = observed["hitpoints_fraction"] - previous_observed["hitpoints_fraction"]
    model_delta = observed["men_fraction"] - previous_observed["men_fraction"]
    danger_delta = derived["danger_score"] - previous_derived["danger_score"]
    new_routing = observed["routing"] and not previous_observed["routing"]
    new_shattered = observed["shattered"] and not previous_observed["shattered"]
    if new_shattered or new_routing or hp_delta <= -0.08 or model_delta <= -0.08 or danger_delta >= 0.12:
        status = "DETERIORATING"
    elif (
        (previous_observed["routing"] and not observed["routing"])
        or hp_delta >= 0.05
        or model_delta >= 0.05
        or danger_delta <= -0.12
    ):
        status = "IMPROVING"
    else:
        status = "STABLE"
    return {
        "status": status,
        "hitpoints_delta": _rounded(hp_delta),
        "model_fraction_delta": _rounded(model_delta),
        "danger_delta": _rounded(danger_delta),
        "new_routing": new_routing,
        "new_shattered": new_shattered,
        "danger_persistent": (
            previous_derived["danger_score"] >= 0.45
            and derived["danger_score"] >= 0.45
        ),
    }


def _force_summary(units: list[dict[str, Any]]) -> dict[str, Any]:
    if not units:
        return {
            "observed_units": 0,
            "integrity_score": 0.0,
            "routing_fraction": 0.0,
            "shattered_fraction": 0.0,
            "wavering_fraction": 0.0,
            "melee_fraction": 0.0,
            "flank_pressure_fraction": 0.0,
            "missile_pressure_fraction": 0.0,
            "high_value_at_risk": 0,
        }
    total_weight = 0.0
    weighted_integrity = 0.0
    for unit in units:
        observed = unit["observed"]
        derived = unit["derived"]
        weight = 0.55 + 0.45 * derived["asset_value_score"]
        integrity = 0.55 * observed["hitpoints_fraction"] + 0.45 * observed["men_fraction"]
        total_weight += weight
        weighted_integrity += weight * integrity
    count = len(units)
    return {
        "observed_units": count,
        "integrity_score": _rounded(weighted_integrity / total_weight if total_weight else 0.0),
        "routing_fraction": _rounded(
            sum(unit["observed"]["routing"] for unit in units) / count
        ),
        "shattered_fraction": _rounded(
            sum(unit["observed"]["shattered"] for unit in units) / count
        ),
        "wavering_fraction": _rounded(
            sum(unit["observed"]["wavering"] for unit in units) / count
        ),
        "melee_fraction": _rounded(
            sum(unit["observed"]["in_melee"] for unit in units) / count
        ),
        "flank_pressure_fraction": _rounded(
            sum(
                any(
                    unit["observed"][key]
                    for key in (
                        "left_flank_threatened",
                        "right_flank_threatened",
                        "rear_flank_threatened",
                    )
                )
                for unit in units
            )
            / count
        ),
        "missile_pressure_fraction": _rounded(
            sum(unit["observed"]["under_missile_attack"] for unit in units)
            / count
        ),
        "high_value_at_risk": sum(
            unit["observed"]["role"] in {"commander", "artillery", "ranged", "cavalry"}
            and unit["derived"]["danger_score"] >= 0.45
            for unit in units
        ),
    }


def _enemy_collapse_state(
    enemy: dict[str, Any], hidden_enemy_units: int, slice_id: str
) -> str:
    if slice_id == "battle_complete":
        return "TERMINAL"
    routing = enemy["routing_fraction"]
    shattered = enemy["shattered_fraction"]
    if hidden_enemy_units == 0 and routing >= 0.75 and shattered >= 0.50:
        return "TERMINAL_COUNTDOWN"
    if routing >= 0.50:
        return "ROUT_CASCADE"
    if routing >= 0.25 or enemy["integrity_score"] <= 0.55:
        return "BREAKING"
    if enemy["missile_pressure_fraction"] >= 0.20 or enemy["melee_fraction"] >= 0.20:
        return "PRESSURED"
    return "CONTESTED"


def _local_stability_state(
    local: dict[str, Any], slice_id: str
) -> tuple[str, float]:
    """Classify local force condition independently of enemy collapse state."""
    if slice_id == "battle_complete":
        return "TERMINAL", 0.0
    high_value_fraction = local["high_value_at_risk"] / max(1, local["observed_units"])
    pressure_score = _clamp(
        0.32 * (1.0 - local["integrity_score"])
        + 0.22 * local["routing_fraction"]
        + 0.12 * local["wavering_fraction"]
        + 0.12 * local["melee_fraction"]
        + 0.08 * local["flank_pressure_fraction"]
        + 0.06 * local["missile_pressure_fraction"]
        + 0.08 * high_value_fraction
    )
    if (
        pressure_score >= 0.55
        and local["routing_fraction"] + local["shattered_fraction"] >= 0.55
        and local["integrity_score"] <= 0.25
    ):
        return "IRREVERSIBLE_COLLAPSE", pressure_score
    if pressure_score >= 0.36 and local["routing_fraction"] >= 0.25:
        return "RECOVERABLE_COLLAPSE", pressure_score
    if pressure_score >= 0.17:
        return "LOCAL_CRISIS", pressure_score
    if pressure_score >= 0.05:
        return "PRESSURED", pressure_score
    return "STABLE", pressure_score


def _tactical_phase_state(
    local_stability_state: str, enemy_collapse_state: str, slice_id: str
) -> str:
    if slice_id == "battle_complete":
        return "TERMINAL"
    if enemy_collapse_state in {"ROUT_CASCADE", "TERMINAL_COUNTDOWN", "TERMINAL"}:
        return "RECOVERY_REQUIRED"
    if local_stability_state in {"RECOVERABLE_COLLAPSE", "IRREVERSIBLE_COLLAPSE"}:
        return "LOCAL_COLLAPSE_RESPONSE"
    return "ACTIVE_CONTEST"


def _outcome_state(
    enemy: dict[str, Any], hidden_enemy_units: int, enemy_collapse_state: str
) -> str:
    if enemy_collapse_state == "TERMINAL":
        return "OBSERVED_TERMINAL_RESULT"
    if enemy_collapse_state == "TERMINAL_COUNTDOWN" and hidden_enemy_units == 0:
        return "VISIBLE_ENEMY_DEFEAT_EFFECTIVELY_IRREVERSIBLE"
    if enemy_collapse_state == "ROUT_CASCADE":
        return "VISIBLE_ENEMY_ROUT_CASCADE"
    if enemy_collapse_state == "BREAKING":
        return "VISIBLE_ENEMY_BREAKING"
    return "CONTESTED"


def build_tactical_state(
    slice_record: dict[str, Any], previous_state: dict[str, Any] | None = None
) -> dict[str, Any]:
    ordered_units = sorted(
        slice_record["units"], key=lambda unit: unit["stable_unit_id"]
    )
    raw_local = [unit for unit in ordered_units if unit["local_alliance"]]
    raw_enemy = [unit for unit in ordered_units if not unit["local_alliance"]]
    previous_by_id = {
        unit["observed"]["stable_unit_id"]: unit
        for unit in (previous_state or {}).get("units", [])
    }

    units: list[dict[str, Any]] = []
    for raw in ordered_units:
        allies = raw_local if raw["local_alliance"] else raw_enemy
        opponents = raw_enemy if raw["local_alliance"] else raw_local
        friendly_support_count = _count_within(raw, allies, LOCAL_SUPPORT_RADIUS_M)
        visible_enemy_pressure_count = _count_within(
            raw, opponents, VISIBLE_PRESSURE_RADIUS_M
        )
        observed = _canonical_observed_unit(raw)
        asset = _asset_value_score(raw)
        danger = _danger_score(
            raw, friendly_support_count, visible_enemy_pressure_count
        )
        recoverability = _withdrawal_recoverability(
            raw, friendly_support_count, visible_enemy_pressure_count
        )
        derived = {
            "model_fraction": _rounded(_model_fraction(raw)),
            "ammo_fraction": _rounded(_ammo_fraction(raw)),
            "fatigue_severity": _rounded(_fatigue_severity(raw)),
            "nearest_friendly_distance_m": _rounded(
                _nearest_distance(raw, allies), 3
            ),
            "nearest_visible_enemy_distance_m": _rounded(
                _nearest_distance(raw, opponents), 3
            ),
            "friendly_support_count_90m": friendly_support_count,
            "visible_enemy_pressure_count_90m": visible_enemy_pressure_count,
            "support_balance": friendly_support_count - visible_enemy_pressure_count,
            "asset_value_score": _rounded(asset),
            "danger_score": _rounded(danger),
            "withdrawal_recoverability_proxy": _rounded(recoverability),
            "collapse_risk_score": _rounded(
                _clamp(danger * (1.15 - 0.45 * recoverability))
            ),
            "marginal_engagement_value_proxy": _rounded(
                _engagement_value(raw, danger, asset)
            ),
            "policy": dict(
                ROLE_POLICIES.get(
                    str(raw.get("role", "unknown")), ROLE_POLICIES["unknown"]
                )
            ),
        }
        derived["trend"] = _unit_trend(
            observed,
            derived,
            previous_by_id.get(raw["stable_unit_id"]),
        )
        units.append({"observed": observed, "derived": derived})

    local_units = [unit for unit in units if unit["observed"]["local_alliance"]]
    enemy_units = [unit for unit in units if not unit["observed"]["local_alliance"]]
    local_summary = _force_summary(local_units)
    enemy_summary = _force_summary(enemy_units)
    hidden_enemy_units = int(slice_record["hidden_enemy_units"])
    enemy_collapse = _enemy_collapse_state(
        enemy_summary, hidden_enemy_units, slice_record["slice_id"]
    )
    local_stability, local_pressure = _local_stability_state(
        local_summary, slice_record["slice_id"]
    )
    tactical_phase = _tactical_phase_state(
        local_stability, enemy_collapse, slice_record["slice_id"]
    )

    state: dict[str, Any] = {
        "schema_version": 1,
        "state_contract": "TACTICAL_STATE_VISIBILITY_SAFE_V2",
        "input_validation_contract": TACTICAL_TRACE_INPUT_CONTRACT,
        "slice_id": slice_record["slice_id"],
        "time_ms": slice_record["time_ms"],
        "observation_scope": {
            "local_unit_count": len(local_units),
            "visible_enemy_unit_count": len(enemy_units),
            "hidden_enemy_unit_count": hidden_enemy_units,
            "foreign_detail_policy": "VISIBLE_TO_LOCAL_ALLIANCE_ONLY",
            "terrain_pathfinding_available": False,
            "line_of_sight_geometry_available": False,
            "enemy_reserve_completeness": hidden_enemy_units == 0,
        },
        "battle_state": {
            "local": local_summary,
            "visible_enemy": enemy_summary,
            "local_pressure_score": _rounded(local_pressure),
            "local_stability_state": local_stability,
            "tactical_phase_state": tactical_phase,
            "visible_enemy_collapse_state": enemy_collapse,
            "outcome_state": _outcome_state(
                enemy_summary, hidden_enemy_units, enemy_collapse
            ),
        },
        "units": sorted(
            units, key=lambda item: item["observed"]["stable_unit_id"]
        ),
        "derivation_limits": [
            "Distances are straight-line x/z observations, not terrain-aware paths.",
            "Visible-enemy pressure omits hidden enemy identity and state.",
            "Withdrawal recoverability is a deterministic proxy, not proof that WH3 pathfinding can execute a retreat.",
            "Outcome state describes the observed visible scope and does not prove a counterfactual action would improve the result.",
        ],
        "evidence_status": "DERIVED_FROM_OBSERVED_INPUT",
        "authority": "NO_ORDERS",
    }
    state["result_digest"] = digest(state)
    return state


def build_tactical_state_trajectory(trace_corpus: dict[str, Any]) -> dict[str, Any]:
    trace_corpus = validate_battle_trace_slices(trace_corpus)
    states: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for slice_record in trace_corpus["slices"]:
        state = build_tactical_state(slice_record, previous)
        states.append(state)
        previous = state
    result: dict[str, Any] = {
        "schema_version": 1,
        "trajectory_contract": "TACTICAL_STATE_TRAJECTORY_V2",
        "input_validation_contract": TACTICAL_TRACE_INPUT_CONTRACT,
        "trace_corpus_id": trace_corpus["corpus_id"],
        "source_trace_digest": trace_corpus["result_digest"],
        "states": states,
        "role_policies": ROLE_POLICIES,
        "evidence_status": "DERIVED_FROM_OBSERVED_INPUT",
        "authority": "NO_ORDERS",
    }
    result["result_digest"] = digest(result)
    return result
