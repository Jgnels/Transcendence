from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from .canonical import digest
from .tactical_feasibility import (
    FEASIBILITY_TRAJECTORY_CONTRACT,
    TacticalFeasibilityError,
    build_tactical_feasibility_envelope,
    build_trace_tactical_feasibility_envelope,
)
from .tactical_schedule import build_trace_tactical_temporal_schedule
from .tactical_state import build_tactical_state_trajectory


GUARDED_PACKET_CONTRACT = "TACTICAL_GUARDED_ACTION_PACKET_V1"
GUARDED_PACKET_SET_CONTRACT = "TACTICAL_GUARDED_ACTION_PACKET_SET_V1"
GUARDED_TRAJECTORY_CONTRACT = "TACTICAL_GUARDED_ACTION_TRAJECTORY_V1"

_ALLOWED_READINESS = {
    "READY_POINT_SUPPORTED_SHADOW_ONLY",
    "DEFERRED_POINT_UNOBSERVED",
    "DEFERRED_QUERY_UNAVAILABLE",
    "BLOCKED_POINT_QUERY_FALSE",
    "BLOCKED_ACTOR_PRECONDITION",
    "BLOCKED_GEOMETRY_UNAVAILABLE",
    "BLOCKED_MIXED_NO_SUPPORTED_POINT",
}


class TacticalGuardedActionError(ValueError):
    pass


def _verified_digest(record: dict[str, Any], label: str) -> None:
    claimed = record.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise TacticalGuardedActionError(f"{label} result digest is missing or invalid")
    material = dict(record)
    material.pop("result_digest", None)
    compact = digest(material)
    newline = hashlib.sha256(
        (json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    ).hexdigest()
    if claimed not in {compact, newline}:
        raise TacticalGuardedActionError(f"{label} result digest mismatch")


def _canonical_candidate_shape(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "rank": candidate["rank"],
        "strategy": candidate["strategy"],
        "point": candidate["point"],
        "horizontal_displacement_m": candidate["horizontal_displacement_m"],
        "derivation": candidate["derivation"],
        "clipped_to_abstract_displacement_bound": candidate["clipped_to_abstract_displacement_bound"],
    }


def _canonical_plan_shape(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_instance_id": plan["plan_instance_id"],
        "objective_id": plan["objective_id"],
        "objective_type": plan["objective_type"],
        "actor_unit_id": plan["actor_unit_id"],
        "actor_role": plan["actor_role"],
        "subject_unit_ids": plan["subject_unit_ids"],
        "actor_precondition_status": plan["actor_precondition_status"],
        "candidate_generation_status": plan["candidate_generation_status"],
        "candidate_count": plan["candidate_count"],
        "candidate_points": [
            _canonical_candidate_shape(item)
            for item in sorted(plan["candidate_points"], key=lambda item: item["rank"])
        ],
    }


def _validate_source(
    state: dict[str, Any],
    schedule_slice: dict[str, Any],
    feasibility_envelope: dict[str, Any],
) -> dict[str, Any]:
    _verified_digest(state, "tactical state")
    _verified_digest(schedule_slice, "tactical schedule")
    _verified_digest(feasibility_envelope, "tactical feasibility envelope")
    if feasibility_envelope.get("envelope_contract") != FEASIBILITY_TRAJECTORY_CONTRACT:
        raise TacticalGuardedActionError("unsupported feasibility envelope contract")
    if feasibility_envelope.get("authority") != "NO_ORDERS":
        raise TacticalGuardedActionError("feasibility envelope must retain NO_ORDERS authority")
    if feasibility_envelope.get("source_tactical_state_digest") != state["result_digest"]:
        raise TacticalGuardedActionError("feasibility envelope state digest mismatch")
    if feasibility_envelope.get("source_schedule_digest") != schedule_slice["result_digest"]:
        raise TacticalGuardedActionError("feasibility envelope schedule digest mismatch")
    if feasibility_envelope.get("slice_id") != state.get("slice_id"):
        raise TacticalGuardedActionError("feasibility envelope slice mismatch")
    if feasibility_envelope.get("time_ms") != state.get("time_ms"):
        raise TacticalGuardedActionError("feasibility envelope time mismatch")

    try:
        canonical = build_tactical_feasibility_envelope(state, schedule_slice)
    except TacticalFeasibilityError as error:
        raise TacticalGuardedActionError(str(error)) from error
    canonical_plans = canonical["plan_envelopes"]
    supplied_plans = feasibility_envelope.get("plan_envelopes", [])
    if not isinstance(supplied_plans, list):
        raise TacticalGuardedActionError("feasibility plan envelopes must be a list")
    expected_ids = [item["plan_instance_id"] for item in canonical_plans]
    supplied_ids = [item.get("plan_instance_id") for item in supplied_plans]
    if len(expected_ids) != len(set(expected_ids)):
        raise TacticalGuardedActionError("canonical feasibility source contains duplicate plan identity")
    if len(supplied_ids) != len(set(supplied_ids)):
        raise TacticalGuardedActionError("duplicate feasibility plan identity")
    if feasibility_envelope.get("plan_envelope_count") != len(supplied_plans):
        raise TacticalGuardedActionError("feasibility plan-envelope count mismatch")
    if len(supplied_plans) != len(canonical_plans):
        raise TacticalGuardedActionError("feasibility plan-envelope cardinality mismatch")
    if feasibility_envelope.get("candidate_point_count") != sum(
        int(item.get("candidate_count", -1)) for item in supplied_plans
    ):
        raise TacticalGuardedActionError("feasibility candidate-point count mismatch")
    expected = {
        item["plan_instance_id"]: _canonical_plan_shape(item)
        for item in canonical_plans
    }
    supplied = {
        item["plan_instance_id"]: _canonical_plan_shape(item)
        for item in supplied_plans
    }
    if expected != supplied:
        raise TacticalGuardedActionError("feasibility envelope candidate geometry or plan source mismatch")
    if feasibility_envelope.get("active_plan_count") != len(schedule_slice.get("active_plans", [])):
        raise TacticalGuardedActionError("feasibility envelope active-plan count mismatch")
    return canonical


def _readiness(plan: dict[str, Any]) -> str:
    feasibility_class = plan.get("feasibility_class")
    if feasibility_class == "ACTOR_PRECONDITION_FAILED":
        return "BLOCKED_ACTOR_PRECONDITION"
    if feasibility_class == "CANDIDATE_GEOMETRY_UNAVAILABLE":
        return "BLOCKED_GEOMETRY_UNAVAILABLE"
    candidates = plan.get("candidate_points", [])
    true_count = sum(item.get("query_result") == "QUERY_TRUE" for item in candidates)
    false_count = sum(item.get("query_result") == "QUERY_FALSE" for item in candidates)
    unavailable_count = sum(item.get("query_result") == "UNAVAILABLE" for item in candidates)
    unobserved_count = sum(item.get("query_result") == "NOT_OBSERVED" for item in candidates)
    if true_count:
        return "READY_POINT_SUPPORTED_SHADOW_ONLY"
    if candidates and false_count == len(candidates):
        return "BLOCKED_POINT_QUERY_FALSE"
    if candidates and unavailable_count == len(candidates):
        return "DEFERRED_QUERY_UNAVAILABLE"
    if candidates and unobserved_count == len(candidates):
        return "DEFERRED_POINT_UNOBSERVED"
    if candidates:
        return "BLOCKED_MIXED_NO_SUPPORTED_POINT"
    return "BLOCKED_GEOMETRY_UNAVAILABLE"


def _build_packet(plan: dict[str, Any], schedule_plan: dict[str, Any]) -> dict[str, Any]:
    readiness = _readiness(plan)
    eligible = [
        copy.deepcopy(item)
        for item in plan.get("candidate_points", [])
        if item.get("query_result") == "QUERY_TRUE"
    ]
    eligible.sort(key=lambda item: (item["rank"], item["candidate_id"]))
    selected = eligible[0] if eligible else None
    packet: dict[str, Any] = {
        "schema_version": 1,
        "packet_contract": GUARDED_PACKET_CONTRACT,
        "packet_id": digest(
            {
                "plan_instance_id": plan["plan_instance_id"],
                "source_feasibility_plan_digest": plan["result_digest"],
            }
        ),
        "slice_id": plan["slice_id"],
        "time_ms": plan["time_ms"],
        "plan_instance_id": plan["plan_instance_id"],
        "objective_id": plan["objective_id"],
        "objective_type": plan["objective_type"],
        "actor_unit_id": plan["actor_unit_id"],
        "actor_role": plan["actor_role"],
        "subject_unit_ids": plan["subject_unit_ids"],
        "severity": schedule_plan["severity"],
        "objective_utility": schedule_plan["objective_utility"],
        "readiness_class": readiness,
        "eligible_candidate_count": len(eligible),
        "eligible_candidates": eligible,
        "selected_candidate_id": selected["candidate_id"] if selected else None,
        "selected_candidate_point": selected["point"] if selected else None,
        "selected_candidate_rank": selected["rank"] if selected else None,
        "application_status": "PROHIBITED_NO_ORDER_AUTHORITY",
        "shadow_review_status": (
            "READY_FOR_SIMULTANEOUS_CONFLICT_REVIEW"
            if readiness == "READY_POINT_SUPPORTED_SHADOW_ONLY"
            else "NOT_READY"
        ),
        "actor_precondition_status": plan["actor_precondition_status"],
        "candidate_generation_status": plan["candidate_generation_status"],
        "point_evidence_status": (
            "EXACT_POINT_QUERY_TRUE_ONLY"
            if eligible
            else "NO_SUPPORTED_EXACT_POINT"
        ),
        "route_status": "UNVERIFIED",
        "formation_status": "UNVERIFIED",
        "collision_status": "UNVERIFIED",
        "command_legality_status": "UNVERIFIED",
        "project_issue_status": "NOT_ATTEMPTED",
        "direct_acknowledgement_status": "UNAVAILABLE_NOT_OBSERVED",
        "execution_status": "NOT_ISSUED",
        "outcome_status": "UNVERIFIED_NOT_ATTRIBUTED",
        "source_feasibility_plan_digest": plan["result_digest"],
        "source_schedule_plan_digest": schedule_plan["result_digest"],
        "authority": "NO_ORDERS",
        "evidence_status": "CONTROL_OFFLINE_GUARDED_ADJUDICATION",
        "interpretation_limits": [
            "Readiness means only that one or more exact candidate points returned QUERY_TRUE in bound evidence.",
            "No route, formation, collision, legality, issue, acknowledgement, execution, arrival, or outcome is established.",
            "A blocked point does not make the broader tactical objective infeasible.",
            "This packet is a shadow-review record and cannot be applied to WH3.",
        ],
    }
    packet["result_digest"] = digest(packet)
    return packet


def build_guarded_action_packet_set(
    state: dict[str, Any],
    schedule_slice: dict[str, Any],
    feasibility_envelope: dict[str, Any],
) -> dict[str, Any]:
    _validate_source(state, schedule_slice, feasibility_envelope)
    schedule_plans = {
        item["plan_instance_id"]: item
        for item in schedule_slice.get("active_plans", [])
    }
    packets: list[dict[str, Any]] = []
    for plan in feasibility_envelope.get("plan_envelopes", []):
        schedule_plan = schedule_plans.get(plan["plan_instance_id"])
        if schedule_plan is None:
            raise TacticalGuardedActionError("feasibility plan missing from source schedule")
        packets.append(_build_packet(plan, schedule_plan))
    packets.sort(key=lambda item: (item["actor_unit_id"], item["objective_id"]))
    classes: dict[str, int] = {}
    for packet in packets:
        if packet["readiness_class"] not in _ALLOWED_READINESS:
            raise TacticalGuardedActionError("unsupported readiness class")
        classes[packet["readiness_class"]] = classes.get(packet["readiness_class"], 0) + 1
    result: dict[str, Any] = {
        "schema_version": 1,
        "packet_set_contract": GUARDED_PACKET_SET_CONTRACT,
        "slice_id": state["slice_id"],
        "time_ms": state["time_ms"],
        "source_tactical_state_digest": state["result_digest"],
        "source_schedule_digest": schedule_slice["result_digest"],
        "source_feasibility_envelope_digest": feasibility_envelope["result_digest"],
        "packet_count": len(packets),
        "ready_packet_count": sum(
            item["readiness_class"] == "READY_POINT_SUPPORTED_SHADOW_ONLY"
            for item in packets
        ),
        "blocked_packet_count": sum(item["readiness_class"].startswith("BLOCKED_") for item in packets),
        "deferred_packet_count": sum(item["readiness_class"].startswith("DEFERRED_") for item in packets),
        "readiness_class_counts": dict(sorted(classes.items())),
        "packets": packets,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_OFFLINE_GUARDED_ADJUDICATION",
        "counterfactual_status": "UNVERIFIED",
    }
    result["result_digest"] = digest(result)
    return result


def validate_guarded_action_packet_set(packet_set: dict[str, Any]) -> dict[str, Any]:
    _verified_digest(packet_set, "guarded action packet set")
    if packet_set.get("packet_set_contract") != GUARDED_PACKET_SET_CONTRACT:
        raise TacticalGuardedActionError("unsupported guarded packet-set contract")
    if packet_set.get("authority") != "NO_ORDERS" or packet_set.get("application_authority") != "PROHIBITED":
        raise TacticalGuardedActionError("guarded packet set must prohibit order authority")
    packets = packet_set.get("packets")
    if not isinstance(packets, list):
        raise TacticalGuardedActionError("guarded packets must be a list")
    seen_packet_ids: set[str] = set()
    seen_plan_ids: set[str] = set()
    seen_actor_ids: set[str] = set()
    for packet in packets:
        if not isinstance(packet, dict):
            raise TacticalGuardedActionError("guarded packet must be an object")
        _verified_digest(packet, "guarded action packet")
        if packet.get("packet_contract") != GUARDED_PACKET_CONTRACT:
            raise TacticalGuardedActionError("unsupported guarded packet contract")
        if packet.get("authority") != "NO_ORDERS" or packet.get("application_status") != "PROHIBITED_NO_ORDER_AUTHORITY":
            raise TacticalGuardedActionError("guarded packet exceeds authority")
        packet_id = packet.get("packet_id")
        plan_id = packet.get("plan_instance_id")
        actor_id = packet.get("actor_unit_id")
        source_plan_digest = packet.get("source_feasibility_plan_digest")
        if not isinstance(packet_id, str) or packet_id in seen_packet_ids:
            raise TacticalGuardedActionError("duplicate or invalid packet identity")
        if not isinstance(plan_id, str) or plan_id in seen_plan_ids:
            raise TacticalGuardedActionError("duplicate or invalid plan identity")
        if not isinstance(actor_id, str) or actor_id in seen_actor_ids:
            raise TacticalGuardedActionError("duplicate or invalid actor identity")
        if not isinstance(source_plan_digest, str) or len(source_plan_digest) != 64:
            raise TacticalGuardedActionError("invalid source feasibility-plan digest")
        expected_packet_id = digest(
            {
                "plan_instance_id": plan_id,
                "source_feasibility_plan_digest": source_plan_digest,
            }
        )
        if packet_id != expected_packet_id:
            raise TacticalGuardedActionError("guarded packet identity does not match its canonical source")
        seen_packet_ids.add(packet_id)
        seen_plan_ids.add(plan_id)
        seen_actor_ids.add(actor_id)
        readiness = packet.get("readiness_class")
        if readiness not in _ALLOWED_READINESS:
            raise TacticalGuardedActionError("invalid guarded readiness class")
        eligible = packet.get("eligible_candidates")
        if not isinstance(eligible, list):
            raise TacticalGuardedActionError("eligible_candidates must be a list")
        ids = [item.get("candidate_id") for item in eligible]
        if len(ids) != len(set(ids)):
            raise TacticalGuardedActionError("duplicate eligible candidate identity")
        if any(item.get("query_result") != "QUERY_TRUE" for item in eligible):
            raise TacticalGuardedActionError("only QUERY_TRUE candidates may be eligible")
        if packet.get("eligible_candidate_count") != len(eligible):
            raise TacticalGuardedActionError("eligible candidate count mismatch")
        if readiness == "READY_POINT_SUPPORTED_SHADOW_ONLY":
            canonical_eligible = sorted(eligible, key=lambda item: (item.get("rank", 0), item.get("candidate_id", "")))
            if not canonical_eligible or packet.get("selected_candidate_id") != canonical_eligible[0]["candidate_id"]:
                raise TacticalGuardedActionError("ready packet selected candidate mismatch")
            if packet.get("selected_candidate_point") != canonical_eligible[0].get("point"):
                raise TacticalGuardedActionError("ready packet selected point mismatch")
            if packet.get("selected_candidate_rank") != canonical_eligible[0].get("rank"):
                raise TacticalGuardedActionError("ready packet selected rank mismatch")
        elif (
            eligible
            or packet.get("selected_candidate_id") is not None
            or packet.get("selected_candidate_point") is not None
            or packet.get("selected_candidate_rank") is not None
        ):
            raise TacticalGuardedActionError("non-ready packet cannot retain eligible candidate")
    if packet_set.get("packet_count") != len(packets):
        raise TacticalGuardedActionError("packet count mismatch")
    if packet_set.get("ready_packet_count") != sum(
        item["readiness_class"] == "READY_POINT_SUPPORTED_SHADOW_ONLY" for item in packets
    ):
        raise TacticalGuardedActionError("ready packet count mismatch")
    return packet_set


def build_trace_guarded_action_packets(
    trace_corpus: dict[str, Any],
    *,
    capability_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state_trajectory = build_tactical_state_trajectory(trace_corpus)
    schedule_trajectory = build_trace_tactical_temporal_schedule(trace_corpus)
    feasibility_trajectory = build_trace_tactical_feasibility_envelope(
        trace_corpus,
        capability_profile=capability_profile,
    )
    states = state_trajectory["states"]
    schedules = schedule_trajectory["schedule_slices"]
    envelopes = feasibility_trajectory["slice_envelopes"]
    if not (len(states) == len(schedules) == len(envelopes)):
        raise TacticalGuardedActionError("trajectory lengths differ")
    packet_sets = [
        build_guarded_action_packet_set(state, schedule, envelope)
        for state, schedule, envelope in zip(states, schedules, envelopes, strict=True)
    ]
    classes: dict[str, int] = {}
    for packet_set in packet_sets:
        for key, value in packet_set["readiness_class_counts"].items():
            classes[key] = classes.get(key, 0) + value
    result: dict[str, Any] = {
        "schema_version": 1,
        "trajectory_contract": GUARDED_TRAJECTORY_CONTRACT,
        "source_id": "BATTLE4_EILHART_VISIBILITY_SAFE_TRACE",
        "source_trace_digest": state_trajectory["source_trace_digest"],
        "source_tactical_state_trajectory_digest": state_trajectory["result_digest"],
        "source_schedule_trajectory_digest": schedule_trajectory["result_digest"],
        "source_feasibility_trajectory_digest": feasibility_trajectory["result_digest"],
        "slice_count": len(packet_sets),
        "packet_sets": packet_sets,
        "summary": {
            "packet_count": sum(item["packet_count"] for item in packet_sets),
            "ready_packet_count": sum(item["ready_packet_count"] for item in packet_sets),
            "blocked_packet_count": sum(item["blocked_packet_count"] for item in packet_sets),
            "deferred_packet_count": sum(item["deferred_packet_count"] for item in packet_sets),
            "readiness_class_counts": dict(sorted(classes.items())),
        },
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_OFFLINE_DERIVED_FROM_OBSERVED_INPUT",
        "counterfactual_status": "UNVERIFIED",
        "interpretation_limits": [
            "Battle 4 candidate points remain unqueried, so no packet is ready for simultaneous review.",
            "Readiness never creates command authority or proves route, formation, execution, or outcome.",
        ],
    }
    result["result_digest"] = digest(result)
    return result
