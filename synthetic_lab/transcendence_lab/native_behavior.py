from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from .campaign_challenge import (
    APPLICATION_AUTHORITY,
    AUTHORITY,
    FRONT_HORIZON_TURNS,
    RECOVERY_REPLENISHMENT_THRESHOLD,
    evaluate_campaign_snapshot,
)
from .canonical import digest
from .contracts import validate_campaign_scenario, visible_scenario

CONTRACT = "NATIVE_CAI_BEHAVIOR_TRACE_ANALYSIS_V1"
TRACE_CONTRACT = "NATIVE_CAI_BEHAVIOR_TRACE_V1"
POSITION_IDLE_EPSILON = 0.25
APPROACH_DELTA_EPSILON = 0.25


class NativeBehaviorError(ValueError):
    pass


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def _at_war(wars: list[list[str]], a: str, b: str) -> bool:
    return [a, b] in wars or [b, a] in wars


def _owned_armies(scenario: dict[str, Any]) -> dict[str, dict[str, Any]]:
    observer = scenario["controlled_faction"]
    visible = visible_scenario(scenario, observer)
    result: dict[str, dict[str, Any]] = {}
    for army in visible["armies"]:
        if army["faction"] != observer:
            continue
        observation = army.get("observation")
        if isinstance(observation, dict) and observation.get("planner_eligible") is False:
            continue
        result[army["id"]] = deepcopy(army)
    return result


def _anchors(scenario: dict[str, Any], challenge: dict[str, Any]) -> dict[str, dict[str, Any]]:
    observer = scenario["controlled_faction"]
    visible = visible_scenario(scenario, observer)
    result: dict[str, dict[str, Any]] = {}

    for front in challenge["fronts"]:
        if not front["threatened"]:
            continue
        region = next((r for r in visible["regions"] if r["id"] == front["region_id"]), None)
        if region is None:
            continue
        key = f"DEFEND_REGION:{region['id']}"
        result[key] = {
            "target_proxy": key,
            "target_class": "DEFEND_REGION",
            "target_id": region["id"],
            "x": float(region["x"]),
            "y": float(region["y"]),
            "critical_context": bool(front["under_siege"] or front["front_state"] == "EXPOSED"),
        }

    for region in visible["regions"]:
        if region["owner"] == observer or not _at_war(visible["wars"], observer, region["owner"]):
            continue
        key = f"ATTACK_REGION:{region['id']}"
        result[key] = {
            "target_proxy": key,
            "target_class": "ATTACK_REGION",
            "target_id": region["id"],
            "x": float(region["x"]),
            "y": float(region["y"]),
            "critical_context": False,
        }

    for army in visible["armies"]:
        if army["faction"] == observer or not _at_war(visible["wars"], observer, army["faction"]):
            continue
        key = f"ENGAGE_FORCE:{army['id']}"
        result[key] = {
            "target_proxy": key,
            "target_class": "ENGAGE_FORCE",
            "target_id": army["id"],
            "x": float(army["x"]),
            "y": float(army["y"]),
            "critical_context": False,
        }
    return result


def _validate_event(event: dict[str, Any], armies: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise NativeBehaviorError("trace event must be an object")
    if event.get("event_type") != "ARMY_ENGAGEMENT":
        raise NativeBehaviorError("only ARMY_ENGAGEMENT events are supported in v1")
    actor_id = event.get("actor_id")
    if actor_id not in armies:
        raise NativeBehaviorError("engagement actor must be an observed controlled field army")
    role = event.get("engagement_role")
    if role not in {"OFFENSIVE", "DEFENSIVE", "UNKNOWN"}:
        raise NativeBehaviorError("engagement_role must be OFFENSIVE, DEFENSIVE, or UNKNOWN")
    replenishment = event.get("actor_replenishment_at_engagement")
    if not isinstance(replenishment, (int, float)) or not 0 <= float(replenishment) <= 1:
        raise NativeBehaviorError("engagement must carry actor_replenishment_at_engagement within [0, 1]")
    cleaned = {
        "event_type": "ARMY_ENGAGEMENT",
        "actor_id": actor_id,
        "engagement_role": role,
        "actor_replenishment_at_engagement": round(float(replenishment), 6),
        "target_faction": event.get("target_faction"),
        "target_id": event.get("target_id"),
    }
    return cleaned


def _movement_proxy(
    previous_army: dict[str, Any],
    current_army: dict[str, Any],
    previous_anchors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    moved = _distance(previous_army, current_army)
    if moved <= POSITION_IDLE_EPSILON:
        return {
            "distance_moved": round(moved, 6),
            "position_idle_proxy": True,
            "target_proxy": None,
            "target_class": None,
            "approach_delta": 0.0,
            "proxy_status": "POSITION_STABLE_NO_TARGET_INFERRED",
        }

    candidates: list[tuple[float, str, dict[str, Any]]] = []
    for key, anchor in previous_anchors.items():
        before = _distance(previous_army, anchor)
        after = _distance(current_army, anchor)
        delta = before - after
        if delta > APPROACH_DELTA_EPSILON:
            candidates.append((delta, key, anchor))
    if not candidates:
        return {
            "distance_moved": round(moved, 6),
            "position_idle_proxy": False,
            "target_proxy": None,
            "target_class": None,
            "approach_delta": 0.0,
            "proxy_status": "MOVED_WITHOUT_UNAMBIGUOUS_STRATEGIC_APPROACH",
        }

    candidates.sort(key=lambda item: (-int(round(item[0] * 1_000_000)), item[1]))
    best_delta, best_key, best_anchor = candidates[0]
    ambiguous = len(candidates) > 1 and abs(best_delta - candidates[1][0]) <= APPROACH_DELTA_EPSILON
    return {
        "distance_moved": round(moved, 6),
        "position_idle_proxy": False,
        "target_proxy": None if ambiguous else best_key,
        "target_class": None if ambiguous else best_anchor["target_class"],
        "approach_delta": round(best_delta, 6),
        "proxy_status": "AMBIGUOUS_APPROACH_NO_TARGET_INFERRED" if ambiguous else "DIRECTIONAL_TARGET_PROXY",
    }


def _front_coverage_records(challenge: dict[str, Any], turn: int) -> list[dict[str, Any]]:
    records = []
    for front in challenge["fronts"]:
        if not front["threatened"]:
            continue
        records.append(
            {
                "turn": turn,
                "region_id": front["region_id"],
                "front_state": front["front_state"],
                "under_siege": front["under_siege"],
                "covered": front["covered_by_visible_controlled_force"],
                "nearby_controlled_army_ids": [item["army_id"] for item in front["nearby_controlled_armies"]],
            }
        )
    return records


def _response_latency(front_records_by_turn: list[tuple[int, list[dict[str, Any]]]]) -> list[dict[str, Any]]:
    active: dict[str, int] = {}
    results: list[dict[str, Any]] = []
    for turn, records in front_records_by_turn:
        present = {item["region_id"]: item for item in records}
        for region_id, first_turn in list(active.items()):
            if region_id not in present:
                results.append(
                    {
                        "region_id": region_id,
                        "first_threat_turn": first_turn,
                        "covered_turn": None,
                        "latency_turns": None,
                        "status": "THREAT_ENDED_BEFORE_OBSERVED_COVERAGE",
                    }
                )
                del active[region_id]
        for region_id, item in present.items():
            if region_id not in active:
                active[region_id] = turn
            if item["covered"]:
                first_turn = active.pop(region_id)
                results.append(
                    {
                        "region_id": region_id,
                        "first_threat_turn": first_turn,
                        "covered_turn": turn,
                        "latency_turns": turn - first_turn,
                        "status": "OBSERVED_COVERAGE",
                    }
                )
    for region_id, first_turn in sorted(active.items()):
        results.append(
            {
                "region_id": region_id,
                "first_threat_turn": first_turn,
                "covered_turn": None,
                "latency_turns": None,
                "status": "RIGHT_CENSORED_UNCOVERED_AT_TRACE_END",
            }
        )
    results.sort(key=lambda item: (item["first_threat_turn"], item["region_id"], item["status"]))
    return results


def analyze_native_behavior_trace(raw_trace: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_trace, dict):
        raise NativeBehaviorError("trace must be an object")
    if raw_trace.get("contract") != TRACE_CONTRACT:
        raise NativeBehaviorError("trace contract mismatch")
    if raw_trace.get("authority") != AUTHORITY or raw_trace.get("application_authority") != APPLICATION_AUTHORITY:
        raise NativeBehaviorError("native behavior trace must preserve NO_ORDERS / PROHIBITED authority")
    observations = raw_trace.get("observations")
    if not isinstance(observations, list) or not observations:
        raise NativeBehaviorError("trace observations must be a nonempty list")

    controlled_faction = raw_trace.get("controlled_faction")
    turns: list[int] = []
    validated: list[dict[str, Any]] = []
    for observation in observations:
        if not isinstance(observation, dict):
            raise NativeBehaviorError("observation must be an object")
        scenario = validate_campaign_scenario(observation.get("scenario"))
        if scenario["controlled_faction"] != controlled_faction:
            raise NativeBehaviorError("trace controlled faction mismatch")
        turn = scenario["turn"]
        if observation.get("turn") != turn:
            raise NativeBehaviorError("observation turn must match scenario turn")
        turns.append(turn)
        validated.append({"turn": turn, "scenario": scenario, "events": deepcopy(observation.get("events", []))})
    if turns != sorted(turns) or len(turns) != len(set(turns)):
        raise NativeBehaviorError("trace turns must be unique and increasing")

    slices: list[dict[str, Any]] = []
    front_records_by_turn: list[tuple[int, list[dict[str, Any]]]] = []
    movements: list[dict[str, Any]] = []
    offensive_engagement_count = 0
    recovering_offensive_engagement_count = 0
    total_engagement_count = 0
    previous: dict[str, Any] | None = None

    prior_target_by_actor: dict[str, dict[str, Any]] = {}
    unexplained_reversals: list[dict[str, Any]] = []
    context_explained_retargets: list[dict[str, Any]] = []

    for item in validated:
        scenario = item["scenario"]
        turn = item["turn"]
        challenge = evaluate_campaign_snapshot(scenario)
        armies = _owned_armies(scenario)
        anchors = _anchors(scenario, challenge)
        events = [_validate_event(event, armies) for event in item["events"]]
        front_records = _front_coverage_records(challenge, turn)
        front_records_by_turn.append((turn, front_records))

        for event in events:
            total_engagement_count += 1
            if event["engagement_role"] == "OFFENSIVE":
                offensive_engagement_count += 1
                if float(event["actor_replenishment_at_engagement"]) < RECOVERY_REPLENISHMENT_THRESHOLD:
                    recovering_offensive_engagement_count += 1

        movement_records: list[dict[str, Any]] = []
        if previous is not None:
            previous_scenario = previous["scenario"]
            previous_challenge = previous["challenge"]
            previous_armies = _owned_armies(previous_scenario)
            previous_anchors = _anchors(previous_scenario, previous_challenge)
            current_pressure = challenge["pressure_class"]
            previous_pressure = previous_challenge["pressure_class"]
            for actor_id in sorted(set(previous_armies) & set(armies)):
                proxy = _movement_proxy(previous_armies[actor_id], armies[actor_id], anchors)
                record = {
                    "from_turn": previous["turn"],
                    "to_turn": turn,
                    "actor_id": actor_id,
                    **proxy,
                }
                movement_records.append(record)
                movements.append(record)

                target_proxy = proxy.get("target_proxy")
                if target_proxy is None:
                    continue
                prior = prior_target_by_actor.get(actor_id)
                current_target = {
                    "target_proxy": target_proxy,
                    "target_class": proxy.get("target_class"),
                    "turn": turn,
                }
                if prior is not None and prior["target_proxy"] != target_proxy:
                    prior_still_present = prior["target_proxy"] in anchors
                    crisis_retarget = (
                        current_target["target_class"] == "DEFEND_REGION"
                        and current_pressure == "LOCAL_CRISIS_OR_EXPOSED_FRONT"
                        and previous_pressure != "LOCAL_CRISIS_OR_EXPOSED_FRONT"
                    )
                    event = {
                        "actor_id": actor_id,
                        "from_target_proxy": prior["target_proxy"],
                        "to_target_proxy": target_proxy,
                        "from_turn": prior["turn"],
                        "to_turn": turn,
                        "prior_target_still_observable": prior_still_present,
                        "pressure_change": f"{previous_pressure}->{current_pressure}",
                    }
                    if crisis_retarget or not prior_still_present:
                        event["classification"] = "CONTEXT_EXPLAINED_RETARGET_PROXY"
                        context_explained_retargets.append(event)
                    else:
                        event["classification"] = "UNEXPLAINED_DIRECTIONAL_REVERSAL_PROXY"
                        unexplained_reversals.append(event)
                prior_target_by_actor[actor_id] = current_target

        healthy_armies = [army for army in armies.values() if float(army["replenishment"]) >= RECOVERY_REPLENISHMENT_THRESHOLD]
        engaged_ids = {event["actor_id"] for event in events}
        healthy_not_engaged = [army for army in healthy_armies if army["id"] not in engaged_ids]
        threatened_front_ids = {record["region_id"] for record in front_records}
        front_army_ids = {actor_id for record in front_records for actor_id in record["nearby_controlled_army_ids"]}
        observer_visible = visible_scenario(scenario, scenario["controlled_faction"])
        own_regions = [region for region in observer_visible["regions"] if region["owner"] == scenario["controlled_faction"]]
        healthy_home_zone_buffer = []
        for army in healthy_not_engaged:
            if army["id"] in front_army_ids:
                continue
            if any(_distance(army, region) / max(float(army["movement"]), 1.0) <= FRONT_HORIZON_TURNS for region in own_regions):
                healthy_home_zone_buffer.append(army)

        slices.append(
            {
                "turn": turn,
                "pressure_class": challenge["pressure_class"],
                "critical_front_records": front_records,
                "controlled_army_count": len(armies),
                "healthy_controlled_army_count": len(healthy_armies),
                "recovering_controlled_army_count": len(armies) - len(healthy_armies),
                "observed_engagements": events,
                "healthy_unengaged_home_zone_buffer_count_proxy": len(healthy_home_zone_buffer),
                "threatened_front_count": len(threatened_front_ids),
                "movement_records": movement_records,
            }
        )
        previous = {"turn": turn, "scenario": scenario, "challenge": challenge}

    front_records_flat = [item for _, records in front_records_by_turn for item in records]
    threatened_front_opportunities = len(front_records_flat)
    covered_front_opportunities = sum(1 for item in front_records_flat if item["covered"])
    idle_movement_records = sum(1 for item in movements if item["position_idle_proxy"])
    interpretable_movement_records = sum(1 for item in movements if item["target_proxy"] is not None)
    response = _response_latency(front_records_by_turn)
    observed_latencies = [item["latency_turns"] for item in response if item["latency_turns"] is not None]

    metrics = {
        "turn_count": len(validated),
        "first_turn": turns[0],
        "last_turn": turns[-1],
        "critical_front_opportunity_count": threatened_front_opportunities,
        "covered_critical_front_opportunity_count": covered_front_opportunities,
        "critical_front_coverage_rate": None if threatened_front_opportunities == 0 else round(covered_front_opportunities / threatened_front_opportunities, 6),
        "observed_front_response_count": len(observed_latencies),
        "mean_observed_front_response_latency_turns": None if not observed_latencies else round(sum(observed_latencies) / len(observed_latencies), 6),
        "right_censored_front_count": sum(1 for item in response if item["status"].startswith("RIGHT_CENSORED")),
        "engagement_count": total_engagement_count,
        "offensive_engagement_count": offensive_engagement_count,
        "recovering_army_offensive_engagement_count": recovering_offensive_engagement_count,
        "recovering_army_offensive_engagement_rate": None if offensive_engagement_count == 0 else round(recovering_offensive_engagement_count / offensive_engagement_count, 6),
        "movement_transition_count": len(movements),
        "position_idle_transition_count_proxy": idle_movement_records,
        "position_idle_transition_rate_proxy": None if not movements else round(idle_movement_records / len(movements), 6),
        "directional_target_proxy_transition_count": interpretable_movement_records,
        "unexplained_directional_reversal_proxy_count": len(unexplained_reversals),
        "context_explained_retarget_proxy_count": len(context_explained_retargets),
        "turns_with_healthy_unengaged_home_zone_buffer_proxy": sum(
            1 for item in slices if item["healthy_unengaged_home_zone_buffer_count_proxy"] > 0
        ),
    }

    result = {
        "contract": CONTRACT,
        "trace_contract": TRACE_CONTRACT,
        "trace_id": raw_trace.get("trace_id"),
        "profile_id": raw_trace.get("profile_id"),
        "controlled_faction": controlled_faction,
        "evidence_status": "OBSERVATIONAL_PROXY_ONLY",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "internal_task_visibility": "UNAVAILABLE",
        "assignment_exclusivity_visibility": "UNAVAILABLE_FROM_TRAJECTORY_ONLY",
        "native_assignment_memory_visibility": "UNAVAILABLE",
        "native_hysteresis_visibility": "UNAVAILABLE",
        "thresholds": {
            "recovery_replenishment_threshold_project_hypothesis": RECOVERY_REPLENISHMENT_THRESHOLD,
            "front_horizon_turns_geometric_project_hypothesis": FRONT_HORIZON_TURNS,
            "position_idle_epsilon_geometric": POSITION_IDLE_EPSILON,
            "approach_delta_epsilon_geometric": APPROACH_DELTA_EPSILON,
        },
        "metrics": metrics,
        "front_response_records": response,
        "unexplained_directional_reversal_proxies": unexplained_reversals,
        "context_explained_retarget_proxies": context_explained_retargets,
        "turn_slices": slices,
        "interpretation_limits": [
            "Movement direction is a target proxy, not native task telemetry.",
            "A healthy unengaged force in the owned home-zone but outside threatened fronts is a reserve-capacity proxy, not proof of deliberate native reserve policy.",
            "Recovering-army offensive engagement uses a project hypothesis threshold and requires an observed engagement event with actor replenishment measured at engagement; absence of an event is not proof of safety.",
            "Assignment exclusivity, native assignment memory, and engine-internal hysteresis are not inferred from trajectory data alone.",
            "No result authorizes Transcendence to issue campaign orders.",
        ],
    }
    result["result_digest"] = digest(result)
    return result
