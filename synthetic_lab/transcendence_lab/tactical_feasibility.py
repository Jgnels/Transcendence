from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Iterable

from .canonical import digest
from .tactical_assignment import build_trace_objective_assignments
from .tactical_schedule import (
    SCHEDULE_CONTRACT,
    build_trace_tactical_temporal_schedule,
)
from .tactical_state import build_tactical_state_trajectory


FEASIBILITY_ENVELOPE_CONTRACT = "TACTICAL_FEASIBILITY_ENVELOPE_V1"
FEASIBILITY_TRAJECTORY_CONTRACT = "TACTICAL_FEASIBILITY_ENVELOPE_TRAJECTORY_V1"
CAPABILITY_PROFILE_CONTRACT = "TACTICAL_FEASIBILITY_CAPABILITY_PROFILE_V1"
SEMANTIC_CAPABILITY_PROFILE_CONTRACT = "TACTICAL_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_V2"
POINT_QUERY_EVIDENCE_CONTRACT = "TACTICAL_POINT_QUERY_EVIDENCE_V1"

MAX_CANDIDATES_PER_PLAN = 3
MAX_ABSTRACT_DISPLACEMENT_M = 120.0

SELF_PRESERVATION_DISTANCES: dict[str, tuple[float, ...]] = {
    "EXTRACT_COMMANDER": (35.0, 70.0, 105.0),
    "EVACUATE_ARTILLERY": (30.0, 60.0, 90.0),
    "DISENGAGE_CAVALRY": (40.0, 80.0, 120.0),
    "REPOSITION_RANGED": (30.0, 60.0, 90.0),
    "TERMINATE_PURSUIT": (30.0, 60.0, 90.0),
    "REFORM_AND_PRESERVE": (25.0, 50.0, 75.0),
}
SUPPORT_STANDOFFS: dict[str, tuple[float, ...]] = {
    "RELIEVE_FRONTLINE": (15.0, 25.0, 35.0),
    "CONTAIN_LOCAL_ROUT": (18.0, 30.0, 42.0),
    "COMMIT_RESERVE": (20.0, 35.0, 50.0),
}

_ALLOWED_QUERY_RESULTS = {
    "QUERY_TRUE",
    "QUERY_FALSE",
    "UNAVAILABLE",
    "NOT_OBSERVED",
}


class TacticalFeasibilityError(ValueError):
    pass


def _rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _verified_digest(record: dict[str, Any], label: str) -> None:
    claimed = record.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise TacticalFeasibilityError(f"{label} result digest is missing or invalid")
    material = dict(record)
    material.pop("result_digest", None)
    compact = digest(material)
    newline = hashlib.sha256(
        (json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    ).hexdigest()
    if claimed not in {compact, newline}:
        raise TacticalFeasibilityError(f"{label} result digest mismatch")


def _point(value: dict[str, Any]) -> tuple[float, float, float]:
    try:
        return (
            float(value["x"]),
            float(value["y"]),
            float(value["z"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise TacticalFeasibilityError("invalid tactical point") from error


def _point_record(point: tuple[float, float, float]) -> dict[str, float]:
    return {
        "x": _rounded(point[0]),
        "y": _rounded(point[1]),
        "z": _rounded(point[2]),
    }


def _horizontal_distance(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> float:
    return math.hypot(a[0] - b[0], a[2] - b[2])


def _normalize(dx: float, dz: float) -> tuple[float, float] | None:
    length = math.hypot(dx, dz)
    if length <= 1e-9:
        return None
    return dx / length, dz / length


def _centroid(points: list[tuple[float, float, float]]) -> tuple[float, float, float] | None:
    if not points:
        return None
    return (
        sum(item[0] for item in points) / len(points),
        sum(item[1] for item in points) / len(points),
        sum(item[2] for item in points) / len(points),
    )


def _unit_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["observed"]["stable_unit_id"]: item
        for item in state.get("units", [])
    }


def _local_units(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in state.get("units", [])
        if item["observed"]["local_alliance"]
    ]


def _visible_enemy_units(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in state.get("units", [])
        if not item["observed"]["local_alliance"]
    ]


def _actor_precondition_failure(actor: dict[str, Any] | None) -> str | None:
    if actor is None:
        return "ACTOR_NOT_OBSERVED"
    observed = actor["observed"]
    if not observed["local_alliance"]:
        return "ACTOR_NOT_LOCAL_ALLIANCE"
    if observed["shattered"]:
        return "ACTOR_SHATTERED"
    if observed["routing"]:
        return "ACTOR_ROUTING"
    if observed["leaving"]:
        return "ACTOR_LEAVING_BATTLE"
    if observed["rampaging"]:
        return "ACTOR_RAMPAGING"
    return None


def _clip_from_actor(
    actor: tuple[float, float, float],
    target: tuple[float, float, float],
) -> tuple[tuple[float, float, float], bool]:
    distance = _horizontal_distance(actor, target)
    if distance <= MAX_ABSTRACT_DISPLACEMENT_M or distance <= 1e-9:
        return target, False
    ratio = MAX_ABSTRACT_DISPLACEMENT_M / distance
    return (
        actor[0] + (target[0] - actor[0]) * ratio,
        actor[1],
        actor[2] + (target[2] - actor[2]) * ratio,
    ), True


def _candidate_id(
    plan: dict[str, Any], strategy: str, rank: int, point: tuple[float, float, float]
) -> str:
    return digest(
        {
            "plan_instance_id": plan["plan_instance_id"],
            "strategy": strategy,
            "rank": rank,
            "point": _point_record(point),
        }
    )


def _retreat_direction(
    state: dict[str, Any], actor: dict[str, Any]
) -> tuple[float, float] | None:
    actor_point = _point(actor["observed"]["position"])
    enemies = _visible_enemy_units(state)
    if not enemies:
        return None
    nearest = min(
        enemies,
        key=lambda item: _horizontal_distance(
            actor_point, _point(item["observed"]["position"])
        ),
    )
    nearest_point = _point(nearest["observed"]["position"])
    away = _normalize(actor_point[0] - nearest_point[0], actor_point[2] - nearest_point[2])
    if away is None:
        return None

    friendly_points = [
        _point(item["observed"]["position"])
        for item in _local_units(state)
        if item["observed"]["stable_unit_id"]
        != actor["observed"]["stable_unit_id"]
    ]
    friendly_center = _centroid(friendly_points)
    if friendly_center is None:
        return away
    toward_friendly = _normalize(
        friendly_center[0] - actor_point[0],
        friendly_center[2] - actor_point[2],
    )
    if toward_friendly is None:
        return away
    blended = _normalize(
        0.72 * away[0] + 0.28 * toward_friendly[0],
        0.72 * away[1] + 0.28 * toward_friendly[1],
    )
    return blended or away


def _retreat_candidates(
    state: dict[str, Any], plan: dict[str, Any], actor: dict[str, Any]
) -> tuple[list[dict[str, Any]], str | None]:
    distances = SELF_PRESERVATION_DISTANCES.get(plan["objective_type"])
    if not distances:
        return [], "UNSUPPORTED_OBJECTIVE_TYPE"
    direction = _retreat_direction(state, actor)
    if direction is None:
        return [], "NO_VISIBLE_THREAT_VECTOR"
    actor_point = _point(actor["observed"]["position"])
    candidates: list[dict[str, Any]] = []
    for rank, distance in enumerate(distances[:MAX_CANDIDATES_PER_PLAN], 1):
        point = (
            actor_point[0] + direction[0] * distance,
            actor_point[1],
            actor_point[2] + direction[1] * distance,
        )
        candidates.append(
            {
                "candidate_id": _candidate_id(plan, "VISIBLE_THREAT_EGRESS", rank, point),
                "rank": rank,
                "strategy": "VISIBLE_THREAT_EGRESS",
                "point": _point_record(point),
                "horizontal_displacement_m": _rounded(distance, 3),
                "derivation": [
                    "move away from the nearest visible enemy",
                    "blend weakly toward the visible local-support centroid",
                    "preserve observed actor elevation",
                ],
                "clipped_to_abstract_displacement_bound": False,
            }
        )
    return candidates, None


def _support_candidates(
    state: dict[str, Any], plan: dict[str, Any], actor: dict[str, Any]
) -> tuple[list[dict[str, Any]], str | None]:
    standoffs = SUPPORT_STANDOFFS.get(plan["objective_type"])
    if not standoffs:
        return [], "UNSUPPORTED_OBJECTIVE_TYPE"
    units = _unit_map(state)
    subject_points = [
        _point(units[unit_id]["observed"]["position"])
        for unit_id in plan.get("subject_unit_ids", [])
        if unit_id in units
    ]
    subject_center = _centroid(subject_points)
    if subject_center is None:
        return [], "SUBJECT_POSITION_UNAVAILABLE"
    actor_point = _point(actor["observed"]["position"])
    actor_side = _normalize(
        actor_point[0] - subject_center[0],
        actor_point[2] - subject_center[2],
    )
    if actor_side is None:
        actor_side = (1.0, 0.0)
    candidates: list[dict[str, Any]] = []
    for rank, standoff in enumerate(standoffs[:MAX_CANDIDATES_PER_PLAN], 1):
        raw = (
            subject_center[0] + actor_side[0] * standoff,
            subject_center[1],
            subject_center[2] + actor_side[1] * standoff,
        )
        point, clipped = _clip_from_actor(actor_point, raw)
        candidates.append(
            {
                "candidate_id": _candidate_id(plan, "SUBJECT_SUPPORT_STANDOFF", rank, point),
                "rank": rank,
                "strategy": "SUBJECT_SUPPORT_STANDOFF",
                "point": _point_record(point),
                "horizontal_displacement_m": _rounded(
                    _horizontal_distance(actor_point, point), 3
                ),
                "derivation": [
                    "use only observed local subject positions",
                    "approach on the actor-facing side of the subject centroid",
                    "preserve observed actor elevation",
                ],
                "clipped_to_abstract_displacement_bound": clipped,
            }
        )
    return candidates, None


def _pursuit_candidates(
    state: dict[str, Any], plan: dict[str, Any], actor: dict[str, Any]
) -> tuple[list[dict[str, Any]], str | None]:
    enemies = [
        item
        for item in _visible_enemy_units(state)
        if item["observed"]["routing"] or item["observed"]["shattered"]
    ]
    if not enemies:
        return [], "NO_VISIBLE_ROUTING_ENEMY"
    actor_point = _point(actor["observed"]["position"])
    target = min(
        enemies,
        key=lambda item: _horizontal_distance(
            actor_point, _point(item["observed"]["position"])
        ),
    )
    target_point = _point(target["observed"]["position"])
    toward = _normalize(target_point[0] - actor_point[0], target_point[2] - actor_point[2])
    if toward is None:
        return [], "ROUTING_TARGET_DIRECTION_UNAVAILABLE"
    distance = _horizontal_distance(actor_point, target_point)
    stop_offsets = (35.0, 20.0, 10.0)
    candidates: list[dict[str, Any]] = []
    for rank, stop_offset in enumerate(stop_offsets, 1):
        travel = max(0.0, min(MAX_ABSTRACT_DISPLACEMENT_M, distance - stop_offset))
        point = (
            actor_point[0] + toward[0] * travel,
            actor_point[1],
            actor_point[2] + toward[1] * travel,
        )
        candidates.append(
            {
                "candidate_id": _candidate_id(plan, "VISIBLE_ROUTING_TARGET_APPROACH", rank, point),
                "rank": rank,
                "strategy": "VISIBLE_ROUTING_TARGET_APPROACH",
                "point": _point_record(point),
                "horizontal_displacement_m": _rounded(travel, 3),
                "visible_target_unit_id": target["observed"]["stable_unit_id"],
                "derivation": [
                    "use only a visible routing or shattered enemy",
                    "retain a bounded standoff from the observed target position",
                    "preserve observed actor elevation",
                ],
                "clipped_to_abstract_displacement_bound": distance - stop_offset > MAX_ABSTRACT_DISPLACEMENT_M,
            }
        )
    return candidates, None


def _generate_candidates(
    state: dict[str, Any], plan: dict[str, Any], actor: dict[str, Any]
) -> tuple[list[dict[str, Any]], str | None]:
    objective_type = plan["objective_type"]
    if objective_type in SELF_PRESERVATION_DISTANCES:
        return _retreat_candidates(state, plan, actor)
    if objective_type in SUPPORT_STANDOFFS:
        return _support_candidates(state, plan, actor)
    if objective_type == "SELECTIVE_PURSUIT":
        return _pursuit_candidates(state, plan, actor)
    return [], "UNSUPPORTED_OBJECTIVE_TYPE"


def _validate_state_schedule(
    state: dict[str, Any], schedule_slice: dict[str, Any]
) -> None:
    _verified_digest(state, "tactical state")
    _verified_digest(schedule_slice, "tactical schedule slice")
    if state.get("state_contract") != "TACTICAL_STATE_VISIBILITY_SAFE_V2":
        raise TacticalFeasibilityError("unsupported tactical state contract")
    if state.get("authority") != "NO_ORDERS":
        raise TacticalFeasibilityError("tactical state must retain NO_ORDERS authority")
    if schedule_slice.get("schedule_contract") != SCHEDULE_CONTRACT:
        raise TacticalFeasibilityError("unsupported schedule contract")
    if schedule_slice.get("authority") != "NO_ORDERS":
        raise TacticalFeasibilityError("schedule must retain NO_ORDERS authority")
    if schedule_slice.get("source_tactical_state_digest") != state.get("result_digest"):
        raise TacticalFeasibilityError("schedule source tactical-state digest mismatch")
    if schedule_slice.get("slice_id") != state.get("slice_id"):
        raise TacticalFeasibilityError("schedule slice identity mismatch")
    if schedule_slice.get("time_ms") != state.get("time_ms"):
        raise TacticalFeasibilityError("schedule time mismatch")
    for plan in schedule_slice.get("active_plans", []):
        if not isinstance(plan, dict):
            raise TacticalFeasibilityError("active plan must be an object")
        _verified_digest(plan, "active plan")
        if plan.get("authority") != "NO_ORDERS":
            raise TacticalFeasibilityError("active plan must retain NO_ORDERS authority")
        if plan.get("status") != "ABSTRACT_SCHEDULED_NOT_ISSUED":
            raise TacticalFeasibilityError("active plan is not an unissued abstract schedule")


def build_live_feasibility_capability_profile(
    live_adjudication: dict[str, Any],
) -> dict[str, Any]:
    _verified_digest(live_adjudication, "live action-authority adjudication")
    if live_adjudication.get("status") != "OBSERVED_READ_ONLY_ACTION_AUTHORITY_CALIBRATED":
        raise TacticalFeasibilityError("unsupported live calibration status")
    if live_adjudication.get("authority") != "NO_ORDERS":
        raise TacticalFeasibilityError("live calibration must retain NO_ORDERS authority")
    metrics = live_adjudication.get("session_metrics")
    if not isinstance(metrics, dict):
        raise TacticalFeasibilityError("live calibration session metrics missing")
    reachability = metrics.get("reachability_counts")
    if not isinstance(reachability, dict):
        raise TacticalFeasibilityError("live reachability counts missing")
    sample_count = metrics.get("sample_count")
    if not isinstance(sample_count, int) or isinstance(sample_count, bool) or sample_count <= 0:
        raise TacticalFeasibilityError("live sample count must be positive")
    query_true = int(reachability.get("QUERY_TRUE", -1))
    query_false = int(reachability.get("QUERY_FALSE", -1))
    unavailable = int(reachability.get("UNAVAILABLE", -1))
    not_applicable = int(reachability.get("NOT_APPLICABLE", -1))
    if min(query_true, query_false, unavailable, not_applicable) < 0:
        raise TacticalFeasibilityError("invalid live reachability counts")
    if query_true + query_false + unavailable + not_applicable != sample_count:
        raise TacticalFeasibilityError("live reachability counts do not equal sample count")
    profile: dict[str, Any] = {
        "schema_version": 1,
        "profile_contract": CAPABILITY_PROFILE_CONTRACT,
        "authority": "NO_ORDERS",
        "source_adjudication_digest": live_adjudication["result_digest"],
        "source_export_sha256": live_adjudication.get("source_export_sha256"),
        "scope": "ONE_ORDINARY_SINGLE_PLAYER_BATTLE",
        "point_reachability": {
            "classification": "OBSERVED",
            "sample_count": sample_count,
            "query_true": query_true,
            "query_false": query_false,
            "unavailable": unavailable,
            "not_applicable": not_applicable,
            "availability_rate": _rounded((query_true + query_false) / sample_count),
            "claim_boundary": "POINT_IN_TIME_QUERY_NOT_ROUTE_COMPLETION",
        },
        "state_evidence": {
            "ordered_position_match_count": metrics["state_match_counts"]["ordered_position_match"],
            "current_target_match_count": metrics["state_match_counts"]["current_target_match"],
            "movement_observed_count": metrics["state_match_counts"]["movement_observed"],
            "control_loss_observed_count": metrics["state_match_counts"]["control_lost_observed"],
        },
        "applicability_limits": [
            "The aggregate capture does not identify feasibility for any Transcendence-generated candidate point.",
            "QUERY_TRUE is not route completion, path safety, formation feasibility, command legality, acknowledgement, execution, or outcome.",
            "The observation is scoped to one ordinary vanilla single-player battle and does not certify SFO or other battle types.",
        ],
        "evidence_status": "OBSERVED_AGGREGATE_CAPABILITY_PROFILE",
    }
    profile["result_digest"] = digest(profile)
    return profile


def build_semantic_feasibility_capability_profile(
    calibration: dict[str, Any],
) -> dict[str, Any]:
    _verified_digest(calibration, "semantic action-feasibility calibration")
    if calibration.get("calibration_contract") != "OBSERVED_COMMAND_POINT_SEMANTIC_CALIBRATION_V1":
        raise TacticalFeasibilityError("unsupported semantic feasibility calibration")
    if calibration.get("status") != "OBSERVED_COMMAND_POINT_SEMANTICS_CALIBRATED":
        raise TacticalFeasibilityError("semantic feasibility calibration is not closed")
    if calibration.get("authority") != "NO_ORDERS":
        raise TacticalFeasibilityError("semantic feasibility calibration must retain NO_ORDERS authority")
    if calibration.get("project_issue_attempt_count") != 0 or calibration.get("direct_acknowledgement_count") != 0:
        raise TacticalFeasibilityError("semantic feasibility calibration may not claim issue or acknowledgement")
    explicit = calibration.get("explicit_point_observation")
    defect = calibration.get("defect_adjudication")
    qualified = calibration.get("qualified_explicit_point_reachability_counts")
    if not isinstance(explicit, dict) or not isinstance(defect, dict) or not isinstance(qualified, dict):
        raise TacticalFeasibilityError("semantic feasibility calibration fields are missing")
    query_true = int(qualified.get("QUERY_TRUE", -1))
    query_false = int(qualified.get("QUERY_FALSE", -1))
    unavailable = int(qualified.get("UNAVAILABLE", -1))
    not_applicable = int(qualified.get("NOT_APPLICABLE", -1))
    if min(query_true, query_false, unavailable, not_applicable) < 0:
        raise TacticalFeasibilityError("semantic reachability counts are invalid")
    if query_true + query_false + unavailable + not_applicable != calibration.get("sample_count"):
        raise TacticalFeasibilityError("semantic reachability counts do not equal sample count")
    if query_false != 0 or explicit.get("valid_false_point_result_status") != "UNVERIFIED_NONE_OBSERVED":
        raise TacticalFeasibilityError("semantic calibration must not retain sentinel false results as point evidence")
    profile: dict[str, Any] = {
        "schema_version": 2,
        "profile_contract": SEMANTIC_CAPABILITY_PROFILE_CONTRACT,
        "authority": "NO_ORDERS",
        "source_calibration_digest": calibration["result_digest"],
        "source_reexport_zip_sha256": calibration.get("source_reexport_zip_sha256"),
        "scope": calibration.get("scope"),
        "point_reachability": {
            "classification": "OBSERVED_EXPLICIT_POINT_TRUE_ONLY",
            "qualified_sample_count": query_true + query_false + unavailable,
            "query_true": query_true,
            "query_false": query_false,
            "unavailable": unavailable,
            "nonpoint_or_opaque_sample_count": not_applicable,
            "explicit_point_window_count": explicit.get("window_count"),
            "explicit_point_actor_count": explicit.get("actor_count"),
            "valid_false_result_status": explicit.get("valid_false_point_result_status"),
            "claim_boundary": "EXACT_EXPLICIT_MOVE_POINT_AT_OBSERVED_INSTANT_ONLY",
        },
        "state_evidence": {
            "explicit_move_actors_with_initial_ordered_position_match": explicit.get("actors_with_initial_ordered_position_match"),
            "explicit_move_actors_with_any_movement": explicit.get("actors_with_any_movement"),
            "visible_attack_actors_with_initial_current_target_match": calibration.get("visible_unit_target_observation", {}).get("actors_with_initial_current_target_match"),
        },
        "corrected_limiting_result": {
            "defect_id": defect.get("defect_id"),
            "discarded_nonpoint_query_false_count": defect.get("discarded_nonpoint_query_false_count"),
            "discarded_nonpoint_query_true_count": defect.get("discarded_nonpoint_query_true_count"),
            "valid_false_point_result_status": explicit.get("valid_false_point_result_status"),
        },
        "applicability_limits": [
            "Only explicit nonzero Move callback points qualify as observed point-query evidence in this capture.",
            "The capture observed no QUERY_FALSE result for a qualified explicit point.",
            "The calibration does not identify feasibility for any Transcendence-generated candidate point.",
            "QUERY_TRUE is not route completion, path safety, formation feasibility, command legality, acknowledgement, execution, or outcome.",
            "The observation is scoped to one ordinary vanilla single-player battle and does not certify SFO or other battle types.",
        ],
        "evidence_status": "OBSERVED_SEMANTICALLY_QUALIFIED_CAPABILITY_PROFILE",
    }
    profile["result_digest"] = digest(profile)
    return profile


def _parse_query_evidence(
    evidence: dict[str, Any] | None,
    *,
    state: dict[str, Any],
    schedule_slice: dict[str, Any],
    candidate_ids: set[str],
) -> dict[str, dict[str, Any]]:
    if evidence is None:
        return {}
    if not isinstance(evidence, dict):
        raise TacticalFeasibilityError("point-query evidence must be an object")
    _verified_digest(evidence, "point-query evidence")
    if evidence.get("evidence_contract") != POINT_QUERY_EVIDENCE_CONTRACT:
        raise TacticalFeasibilityError("unsupported point-query evidence contract")
    if evidence.get("authority") != "NO_ORDERS":
        raise TacticalFeasibilityError("point-query evidence must retain NO_ORDERS authority")
    if evidence.get("source_tactical_state_digest") != state.get("result_digest"):
        raise TacticalFeasibilityError("point-query evidence tactical-state digest mismatch")
    if evidence.get("source_schedule_digest") != schedule_slice.get("result_digest"):
        raise TacticalFeasibilityError("point-query evidence schedule digest mismatch")
    if evidence.get("project_issue_attempt_count") != 0:
        raise TacticalFeasibilityError("point-query evidence may not claim project issue attempts")
    if evidence.get("direct_acknowledgement_count") != 0:
        raise TacticalFeasibilityError("point-query evidence may not claim acknowledgements")
    records = evidence.get("candidate_results")
    if not isinstance(records, list):
        raise TacticalFeasibilityError("point-query candidate_results must be a list")
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise TacticalFeasibilityError("point-query result must be an object")
        candidate_id = record.get("candidate_id")
        if not isinstance(candidate_id, str) or candidate_id not in candidate_ids:
            raise TacticalFeasibilityError("point-query result references an unknown candidate")
        if candidate_id in result:
            raise TacticalFeasibilityError("duplicate point-query candidate result")
        status = record.get("query_result")
        if status not in _ALLOWED_QUERY_RESULTS - {"NOT_OBSERVED"}:
            raise TacticalFeasibilityError("invalid point-query result")
        source = record.get("evidence_source")
        if source not in {"OBSERVED_ENGINE_QUERY", "CONTROL_SYNTHETIC_FIXTURE"}:
            raise TacticalFeasibilityError("invalid point-query evidence source")
        result[candidate_id] = {
            "query_result": status,
            "evidence_source": source,
        }
    return result


def build_tactical_feasibility_envelope(
    state: dict[str, Any],
    schedule_slice: dict[str, Any],
    *,
    capability_profile: dict[str, Any] | None = None,
    point_query_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_state_schedule(state, schedule_slice)
    if capability_profile is not None:
        _verified_digest(capability_profile, "feasibility capability profile")
        if capability_profile.get("profile_contract") not in {CAPABILITY_PROFILE_CONTRACT, SEMANTIC_CAPABILITY_PROFILE_CONTRACT}:
            raise TacticalFeasibilityError("unsupported feasibility capability profile")
        if capability_profile.get("authority") != "NO_ORDERS":
            raise TacticalFeasibilityError("capability profile must retain NO_ORDERS authority")

    units = _unit_map(state)
    plan_material: list[tuple[dict[str, Any], dict[str, Any] | None, list[dict[str, Any]], str | None]] = []
    all_candidate_ids: set[str] = set()
    for plan in schedule_slice.get("active_plans", []):
        actor = units.get(plan["actor_unit_id"])
        failure = _actor_precondition_failure(actor)
        if failure is None and actor is not None:
            candidates, geometry_failure = _generate_candidates(state, plan, actor)
        else:
            candidates, geometry_failure = [], failure
        for candidate in candidates:
            if candidate["candidate_id"] in all_candidate_ids:
                raise TacticalFeasibilityError("candidate identity collision")
            all_candidate_ids.add(candidate["candidate_id"])
        plan_material.append((plan, actor, candidates, geometry_failure))

    query_by_candidate = _parse_query_evidence(
        point_query_evidence,
        state=state,
        schedule_slice=schedule_slice,
        candidate_ids=all_candidate_ids,
    )

    plan_envelopes: list[dict[str, Any]] = []
    for plan, actor, candidates, geometry_failure in plan_material:
        decorated: list[dict[str, Any]] = []
        for candidate in candidates:
            record = dict(candidate)
            query = query_by_candidate.get(candidate["candidate_id"])
            if query is None:
                query_result = "NOT_OBSERVED"
                evidence_source = "NONE"
                candidate_status = "POINT_QUERY_NOT_OBSERVED"
            else:
                query_result = query["query_result"]
                evidence_source = query["evidence_source"]
                if query_result == "QUERY_TRUE":
                    candidate_status = "POINT_QUERY_SUPPORTED_ONLY"
                elif query_result == "QUERY_FALSE":
                    candidate_status = "REJECTED_BY_POINT_QUERY"
                else:
                    candidate_status = "POINT_QUERY_UNAVAILABLE"
            record.update(
                {
                    "query_result": query_result,
                    "query_evidence_source": evidence_source,
                    "candidate_status": candidate_status,
                    "route_completion_status": "UNVERIFIED",
                    "formation_feasibility_status": "UNVERIFIED",
                    "collision_feasibility_status": "UNVERIFIED",
                    "command_legality_status": "UNVERIFIED",
                    "direct_acknowledgement_status": "UNAVAILABLE_NOT_OBSERVED",
                    "execution_status": "NOT_ISSUED",
                    "outcome_status": "UNVERIFIED_NOT_ATTRIBUTED",
                }
            )
            record["result_digest"] = digest(record)
            decorated.append(record)

        query_true = [item for item in decorated if item["query_result"] == "QUERY_TRUE"]
        query_false = [item for item in decorated if item["query_result"] == "QUERY_FALSE"]
        query_unavailable = [item for item in decorated if item["query_result"] == "UNAVAILABLE"]
        if geometry_failure in {
            "ACTOR_NOT_OBSERVED",
            "ACTOR_NOT_LOCAL_ALLIANCE",
            "ACTOR_SHATTERED",
            "ACTOR_ROUTING",
            "ACTOR_LEAVING_BATTLE",
            "ACTOR_RAMPAGING",
        }:
            feasibility_class = "ACTOR_PRECONDITION_FAILED"
        elif not decorated:
            feasibility_class = "CANDIDATE_GEOMETRY_UNAVAILABLE"
        elif query_true:
            feasibility_class = "POINT_QUERY_SUPPORTED_ONLY"
        elif len(query_false) == len(decorated):
            feasibility_class = "POINT_QUERY_REJECTED"
        elif query_unavailable:
            feasibility_class = "POINT_QUERY_UNVERIFIED"
        else:
            feasibility_class = "QUERY_READY_NOT_OBSERVED"

        selected_candidate_id = None
        if query_true:
            selected_candidate_id = sorted(query_true, key=lambda item: item["rank"])[0]["candidate_id"]

        envelope: dict[str, Any] = {
            "schema_version": 1,
            "feasibility_contract": FEASIBILITY_ENVELOPE_CONTRACT,
            "slice_id": state["slice_id"],
            "time_ms": state["time_ms"],
            "plan_instance_id": plan["plan_instance_id"],
            "objective_id": plan["objective_id"],
            "objective_type": plan["objective_type"],
            "actor_unit_id": plan["actor_unit_id"],
            "actor_role": plan["actor_role"],
            "subject_unit_ids": plan["subject_unit_ids"],
            "actor_precondition_status": geometry_failure
            if geometry_failure and geometry_failure.startswith("ACTOR_")
            else "SATISFIED_FROM_OBSERVED_STATE",
            "candidate_generation_status": geometry_failure or "GENERATED",
            "candidate_count": len(decorated),
            "candidate_points": sorted(decorated, key=lambda item: item["rank"]),
            "feasibility_class": feasibility_class,
            "selected_candidate_id": selected_candidate_id,
            "selected_candidate_status": (
                "ADVISORY_POINT_ONLY_NOT_ISSUED"
                if selected_candidate_id is not None
                else "NONE"
            ),
            "point_query_capability_context": (
                "OBSERVED_IN_SEPARATE_CALIBRATION_ONLY"
                if capability_profile is not None
                else "UNVERIFIED"
            ),
            "source_tactical_state_digest": state["result_digest"],
            "source_schedule_digest": schedule_slice["result_digest"],
            "source_capability_profile_digest": (
                capability_profile["result_digest"]
                if capability_profile is not None
                else None
            ),
            "authority": "NO_ORDERS",
            "project_issue_status": "NOT_ATTEMPTED",
            "direct_acknowledgement_status": "UNAVAILABLE_NOT_OBSERVED",
            "counterfactual_status": "UNVERIFIED",
            "interpretation_limits": [
                "Candidate points are deterministic geometry proposals, not WH3 orders.",
                "A QUERY_TRUE result supports only the exact point at the exact observed instant.",
                "No route, terrain safety, formation, collision, command legality, acknowledgement, execution, arrival, or outcome is established.",
                "Visible-enemy geometry excludes hidden enemy identity and state.",
            ],
        }
        envelope["result_digest"] = digest(envelope)
        plan_envelopes.append(envelope)

    result: dict[str, Any] = {
        "schema_version": 1,
        "envelope_contract": FEASIBILITY_TRAJECTORY_CONTRACT,
        "slice_id": state["slice_id"],
        "time_ms": state["time_ms"],
        "source_tactical_state_digest": state["result_digest"],
        "source_schedule_digest": schedule_slice["result_digest"],
        "source_capability_profile_digest": (
            capability_profile["result_digest"] if capability_profile is not None else None
        ),
        "active_plan_count": len(schedule_slice.get("active_plans", [])),
        "plan_envelope_count": len(plan_envelopes),
        "plan_envelopes": sorted(
            plan_envelopes,
            key=lambda item: (item["actor_unit_id"], item["objective_id"]),
        ),
        "candidate_point_count": sum(item["candidate_count"] for item in plan_envelopes),
        "point_query_supported_plan_count": sum(
            item["feasibility_class"] == "POINT_QUERY_SUPPORTED_ONLY"
            for item in plan_envelopes
        ),
        "point_query_rejected_plan_count": sum(
            item["feasibility_class"] == "POINT_QUERY_REJECTED"
            for item in plan_envelopes
        ),
        "query_ready_unobserved_plan_count": sum(
            item["feasibility_class"] == "QUERY_READY_NOT_OBSERVED"
            for item in plan_envelopes
        ),
        "authority": "NO_ORDERS",
        "evidence_status": "CONTROL_OFFLINE_GEOMETRY_ENVELOPE",
        "counterfactual_status": "UNVERIFIED",
    }
    result["result_digest"] = digest(result)
    return result


def build_trace_tactical_feasibility_envelope(
    trace_corpus: dict[str, Any],
    *,
    capability_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state_trajectory = build_tactical_state_trajectory(trace_corpus)
    assignment_trajectory = build_trace_objective_assignments(trace_corpus)
    schedule_trajectory = build_trace_tactical_temporal_schedule(trace_corpus)
    states = state_trajectory["states"]
    schedules = schedule_trajectory["schedule_slices"]
    if len(states) != len(schedules):
        raise TacticalFeasibilityError("state and schedule trajectory lengths differ")
    envelopes = [
        build_tactical_feasibility_envelope(
            state,
            schedule,
            capability_profile=capability_profile,
        )
        for state, schedule in zip(states, schedules, strict=True)
    ]
    classes: dict[str, int] = {}
    for envelope in envelopes:
        for plan in envelope["plan_envelopes"]:
            key = plan["feasibility_class"]
            classes[key] = classes.get(key, 0) + 1
    result: dict[str, Any] = {
        "schema_version": 1,
        "trajectory_contract": FEASIBILITY_TRAJECTORY_CONTRACT,
        "source_id": "BATTLE4_EILHART_VISIBILITY_SAFE_TRACE",
        "source_trace_digest": state_trajectory["source_trace_digest"],
        "source_tactical_state_trajectory_digest": state_trajectory["result_digest"],
        "source_assignment_trajectory_digest": assignment_trajectory["result_digest"],
        "source_schedule_trajectory_digest": schedule_trajectory["result_digest"],
        "source_capability_profile_digest": (
            capability_profile["result_digest"] if capability_profile is not None else None
        ),
        "slice_count": len(envelopes),
        "slice_envelopes": envelopes,
        "summary": {
            "active_plan_envelope_count": sum(item["plan_envelope_count"] for item in envelopes),
            "candidate_point_count": sum(item["candidate_point_count"] for item in envelopes),
            "feasibility_class_counts": dict(sorted(classes.items())),
            "point_query_supported_plan_count": sum(item["point_query_supported_plan_count"] for item in envelopes),
            "point_query_rejected_plan_count": sum(item["point_query_rejected_plan_count"] for item in envelopes),
            "query_ready_unobserved_plan_count": sum(item["query_ready_unobserved_plan_count"] for item in envelopes),
            "maximum_candidates_per_plan": MAX_CANDIDATES_PER_PLAN,
            "maximum_abstract_displacement_m": MAX_ABSTRACT_DISPLACEMENT_M,
        },
        "interpretation_limits": [
            "The v0.1S live capture proves query availability in a separate ordinary battle, not for these Battle 4 candidate points.",
            "The envelope generates bounded candidate geometry but performs no WH3 query and issues no order.",
            "No route, formation, collision, acknowledgement, execution, completion, casualty, or outcome claim is made.",
        ],
        "evidence_status": "CONTROL_OFFLINE_DERIVED_FROM_OBSERVED_INPUT",
        "counterfactual_status": "UNVERIFIED",
        "authority": "NO_ORDERS",
    }
    result["result_digest"] = digest(result)
    return result


def build_point_query_evidence(
    state: dict[str, Any],
    schedule_slice: dict[str, Any],
    candidate_results: Iterable[dict[str, str]],
    *,
    evidence_source: str,
) -> dict[str, Any]:
    records = []
    for item in candidate_results:
        candidate_id = item.get("candidate_id")
        query_result = item.get("query_result")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise TacticalFeasibilityError("candidate_id must be nonempty text")
        if query_result not in _ALLOWED_QUERY_RESULTS - {"NOT_OBSERVED"}:
            raise TacticalFeasibilityError("invalid query_result")
        records.append(
            {
                "candidate_id": candidate_id,
                "query_result": query_result,
                "evidence_source": evidence_source,
            }
        )
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "evidence_contract": POINT_QUERY_EVIDENCE_CONTRACT,
        "source_tactical_state_digest": state["result_digest"],
        "source_schedule_digest": schedule_slice["result_digest"],
        "candidate_results": sorted(records, key=lambda item: item["candidate_id"]),
        "project_issue_attempt_count": 0,
        "direct_acknowledgement_count": 0,
        "authority": "NO_ORDERS",
    }
    evidence["result_digest"] = digest(evidence)
    return evidence
