from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from .canonical import digest

TRACE_CONTRACT = "NATIVE_CAI_PLAYER_VISIBLE_PARTIAL_TRACE_V1"
RESULT_CONTRACT = "NATIVE_CAI_PLAYER_VISIBLE_PARTIAL_ANALYSIS_V1"
AUTHORITY = "NO_ORDERS"
APPLICATION_AUTHORITY = "PROHIBITED"
VISIBILITY_SOURCE = "WH3_PLAYER_FILTERED_LISTS"
POSITION_IDLE_EPSILON = 0.05
APPROACH_DELTA_EPSILON = 0.05


class NativeVisibleBehaviorError(ValueError):
    pass


def _number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)):
        raise NativeVisibleBehaviorError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise NativeVisibleBehaviorError(f"{label} must be finite")
    return number


def _validate_entity(raw: Any, *, kind: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise NativeVisibleBehaviorError(f"{kind} must be an object")
    entity_id = raw.get("id")
    faction = raw.get("faction") if kind == "army" else raw.get("owner")
    if not isinstance(entity_id, str) or not entity_id:
        raise NativeVisibleBehaviorError(f"{kind} id must be a nonempty string")
    if not isinstance(faction, str) or not faction:
        raise NativeVisibleBehaviorError(f"{kind} faction/owner must be a nonempty string")
    return {
        "id": entity_id,
        "faction" if kind == "army" else "owner": faction,
        "x": _number(raw.get("x"), f"{kind}.x"),
        "y": _number(raw.get("y"), f"{kind}.y"),
    }


def _validate_trace(raw_trace: Any) -> dict[str, Any]:
    if not isinstance(raw_trace, dict):
        raise NativeVisibleBehaviorError("trace must be an object")
    if raw_trace.get("contract") != TRACE_CONTRACT:
        raise NativeVisibleBehaviorError("trace contract mismatch")
    if raw_trace.get("authority") != AUTHORITY or raw_trace.get("application_authority") != APPLICATION_AUTHORITY:
        raise NativeVisibleBehaviorError("trace must preserve NO_ORDERS / PROHIBITED authority")
    if raw_trace.get("foreign_visibility_source") != VISIBILITY_SOURCE:
        raise NativeVisibleBehaviorError("foreign visibility must come from WH3 player-filtered lists")
    observer = raw_trace.get("observer_faction")
    target = raw_trace.get("observed_ai_faction")
    if not isinstance(observer, str) or not observer or not isinstance(target, str) or not target:
        raise NativeVisibleBehaviorError("observer_faction and observed_ai_faction are required")
    if observer == target:
        raise NativeVisibleBehaviorError("partial visible-AI trace must observe a foreign faction")
    frames = raw_trace.get("frames")
    if not isinstance(frames, list) or len(frames) < 2:
        raise NativeVisibleBehaviorError("trace requires at least two frames")

    turns: list[int] = []
    cleaned_frames: list[dict[str, Any]] = []
    for raw_frame in frames:
        if not isinstance(raw_frame, dict):
            raise NativeVisibleBehaviorError("frame must be an object")
        turn = raw_frame.get("turn")
        if not isinstance(turn, int) or turn < 1:
            raise NativeVisibleBehaviorError("frame turn must be a positive integer")
        turns.append(turn)
        armies = [_validate_entity(item, kind="army") for item in raw_frame.get("visible_armies", [])]
        regions = [_validate_entity(item, kind="region") for item in raw_frame.get("visible_regions", [])]
        if len({item["id"] for item in armies}) != len(armies):
            raise NativeVisibleBehaviorError("duplicate visible army id within frame")
        if len({item["id"] for item in regions}) != len(regions):
            raise NativeVisibleBehaviorError("duplicate visible region id within frame")
        target_armies = [item for item in armies if item["faction"] == target]
        cleaned_frames.append(
            {
                "turn": turn,
                "visible_armies": sorted(armies, key=lambda item: item["id"]),
                "visible_regions": sorted(regions, key=lambda item: item["id"]),
                "observed_ai_army_ids": sorted(item["id"] for item in target_armies),
            }
        )
    if turns != sorted(turns) or len(turns) != len(set(turns)):
        raise NativeVisibleBehaviorError("frame turns must be unique and increasing")
    if not any(frame["observed_ai_army_ids"] for frame in cleaned_frames):
        raise NativeVisibleBehaviorError("observed_ai_faction is never present in the player-visible army set")

    return {
        "contract": TRACE_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "foreign_visibility_source": VISIBILITY_SOURCE,
        "observer_faction": observer,
        "observed_ai_faction": target,
        "frames": cleaned_frames,
    }


def _distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    return math.hypot(float(left["x"]) - float(right["x"]), float(left["y"]) - float(right["y"]))


def _anchors(frame: dict[str, Any], target_faction: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for army in frame["visible_armies"]:
        if army["faction"] == target_faction:
            continue
        key = f"VISIBLE_ARMY:{army['id']}"
        result[key] = {
            "anchor_id": key,
            "anchor_kind": "VISIBLE_ARMY",
            "entity_id": army["id"],
            "faction_or_owner": army["faction"],
            "x": army["x"],
            "y": army["y"],
        }
    for region in frame["visible_regions"]:
        key = f"VISIBLE_REGION:{region['id']}"
        result[key] = {
            "anchor_id": key,
            "anchor_kind": "VISIBLE_REGION",
            "entity_id": region["id"],
            "faction_or_owner": region["owner"],
            "x": region["x"],
            "y": region["y"],
        }
    return result


def _movement_proxy(previous: dict[str, Any], current: dict[str, Any], anchors: dict[str, dict[str, Any]]) -> dict[str, Any]:
    moved = _distance(previous, current)
    if moved <= POSITION_IDLE_EPSILON:
        return {
            "distance_moved": round(moved, 6),
            "position_idle_proxy": True,
            "anchor_proxy": None,
            "proxy_status": "POSITION_STABLE_NO_INTENT_INFERRED",
        }

    candidates: list[tuple[float, str]] = []
    for anchor_id, anchor in anchors.items():
        delta = _distance(previous, anchor) - _distance(current, anchor)
        if delta > APPROACH_DELTA_EPSILON:
            candidates.append((delta, anchor_id))
    if not candidates:
        return {
            "distance_moved": round(moved, 6),
            "position_idle_proxy": False,
            "anchor_proxy": None,
            "proxy_status": "MOVED_WITHOUT_VISIBLE_ANCHOR_APPROACH",
        }

    candidates.sort(key=lambda item: (-int(round(item[0] * 1_000_000)), item[1]))
    best_delta, best_anchor = candidates[0]
    ambiguous = len(candidates) > 1 and abs(best_delta - candidates[1][0]) <= APPROACH_DELTA_EPSILON
    return {
        "distance_moved": round(moved, 6),
        "position_idle_proxy": False,
        "anchor_proxy": None if ambiguous else best_anchor,
        "approach_delta": round(best_delta, 6),
        "proxy_status": "AMBIGUOUS_VISIBLE_ANCHOR_APPROACH" if ambiguous else "VISIBLE_ANCHOR_DIRECTION_PROXY",
    }


def analyze_player_visible_native_trace(raw_trace: dict[str, Any]) -> dict[str, Any]:
    trace = _validate_trace(raw_trace)
    target = trace["observed_ai_faction"]
    frames = trace["frames"]

    intervals: list[dict[str, Any]] = []
    visibility_gains: list[dict[str, Any]] = []
    visibility_losses: list[dict[str, Any]] = []
    anchor_change_candidates: list[dict[str, Any]] = []
    prior_anchor_by_actor: dict[str, dict[str, Any]] = {}

    comparable_actor_intervals = 0
    movement_intervals = 0
    position_idle_intervals = 0
    directional_proxy_intervals = 0
    ambiguous_intervals = 0
    unanchored_movement_intervals = 0

    for previous_frame, current_frame in zip(frames, frames[1:]):
        previous_armies = {
            item["id"]: item for item in previous_frame["visible_armies"] if item["faction"] == target
        }
        current_armies = {
            item["id"]: item for item in current_frame["visible_armies"] if item["faction"] == target
        }
        previous_ids = set(previous_armies)
        current_ids = set(current_armies)
        for actor_id in sorted(current_ids - previous_ids):
            visibility_gains.append(
                {
                    "actor_id": actor_id,
                    "turn": current_frame["turn"],
                    "classification": "ENTERED_PLAYER_VISIBLE_SET_OR_NEW_IDENTITY",
                }
            )
        for actor_id in sorted(previous_ids - current_ids):
            visibility_losses.append(
                {
                    "actor_id": actor_id,
                    "turn": current_frame["turn"],
                    "classification": "LEFT_PLAYER_VISIBLE_SET_RIGHT_CENSORED_NOT_DEATH",
                }
            )
            prior_anchor_by_actor.pop(actor_id, None)

        anchors = _anchors(previous_frame, target)
        current_anchor_ids = set(_anchors(current_frame, target))
        for actor_id in sorted(previous_ids & current_ids):
            comparable_actor_intervals += 1
            proxy = _movement_proxy(previous_armies[actor_id], current_armies[actor_id], anchors)
            if proxy["position_idle_proxy"]:
                position_idle_intervals += 1
            else:
                movement_intervals += 1
            status = proxy["proxy_status"]
            if status == "VISIBLE_ANCHOR_DIRECTION_PROXY":
                directional_proxy_intervals += 1
            elif status == "AMBIGUOUS_VISIBLE_ANCHOR_APPROACH":
                ambiguous_intervals += 1
            elif status == "MOVED_WITHOUT_VISIBLE_ANCHOR_APPROACH":
                unanchored_movement_intervals += 1

            interval = {
                "from_turn": previous_frame["turn"],
                "to_turn": current_frame["turn"],
                "actor_id": actor_id,
                **proxy,
            }
            intervals.append(interval)

            anchor_proxy = proxy.get("anchor_proxy")
            if anchor_proxy is None:
                continue
            prior = prior_anchor_by_actor.get(actor_id)
            if prior is not None and prior["anchor_proxy"] != anchor_proxy:
                anchor_change_candidates.append(
                    {
                        "actor_id": actor_id,
                        "from_anchor_proxy": prior["anchor_proxy"],
                        "to_anchor_proxy": anchor_proxy,
                        "from_turn": prior["turn"],
                        "to_turn": current_frame["turn"],
                        "prior_anchor_still_player_visible": prior["anchor_proxy"] in current_anchor_ids,
                        "classification": "VISIBLE_ANCHOR_DIRECTION_CHANGE_CANDIDATE_NOT_TASK_CHURN",
                    }
                )
            prior_anchor_by_actor[actor_id] = {
                "anchor_proxy": anchor_proxy,
                "turn": current_frame["turn"],
            }

    result: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "observation_scope": "PLAYER_VISIBLE_PARTIAL_FOREIGN_AI",
        "observer_faction": trace["observer_faction"],
        "observed_ai_faction": target,
        "foreign_visibility_source": VISIBILITY_SOURCE,
        "metrics": {
            "frame_count": len(frames),
            "first_turn": frames[0]["turn"],
            "last_turn": frames[-1]["turn"],
            "comparable_actor_intervals": comparable_actor_intervals,
            "movement_intervals": movement_intervals,
            "position_idle_intervals": position_idle_intervals,
            "position_idle_rate": round(position_idle_intervals / comparable_actor_intervals, 6) if comparable_actor_intervals else None,
            "directional_anchor_proxy_intervals": directional_proxy_intervals,
            "directional_anchor_proxy_rate": round(directional_proxy_intervals / movement_intervals, 6) if movement_intervals else None,
            "ambiguous_anchor_intervals": ambiguous_intervals,
            "unanchored_movement_intervals": unanchored_movement_intervals,
            "visible_anchor_direction_change_candidate_count": len(anchor_change_candidates),
            "visibility_gain_count": len(visibility_gains),
            "visibility_loss_count": len(visibility_losses),
        },
        "intervals": intervals,
        "visible_anchor_direction_change_candidates": anchor_change_candidates,
        "visibility_gains": visibility_gains,
        "visibility_losses": visibility_losses,
        "availability": {
            "target_intent": "UNAVAILABLE_DIRECTION_ONLY",
            "native_task_identity": "UNAVAILABLE",
            "front_coverage": "UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY",
            "response_latency": "UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY",
            "recovery_misuse": "UNAVAILABLE_NO_SAFE_FOREIGN_REPLENISHMENT_AT_ENGAGEMENT",
            "reserve_adequacy": "UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY",
            "assignment_exclusivity": "UNAVAILABLE_FROM_TRAJECTORY_ONLY",
            "native_assignment_memory": "UNAVAILABLE",
            "native_hysteresis": "UNAVAILABLE",
            "engagement_role": "UNAVAILABLE_CURRENT_PROBE",
        },
        "interpretation_limits": [
            "Foreign entities originate only from WH3 player-filtered visibility lists.",
            "A foreign army disappearing from the visible set is right-censored; it is not evidence of destruction, retreat, reassignment, or disbandment.",
            "Movement toward a visible anchor is a directional proxy, not evidence of a native CAI task or intent.",
            "A visible-anchor direction change is a review candidate, not task churn or hysteresis failure.",
            "Absence of an observed failure cannot establish good full-faction coverage, reserves, recovery policy, exclusivity, memory, or hysteresis.",
            "No result authorizes campaign orders or any application path.",
        ],
    }
    result["result_digest"] = digest(result)
    return deepcopy(result)
