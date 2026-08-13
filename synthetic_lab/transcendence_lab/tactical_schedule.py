from __future__ import annotations

from typing import Any, Iterable

from .battle_shadow import SEVERITY_RANK
from .canonical import digest
from .tactical_assignment import (
    ASSIGNMENT_CONTRACT,
    build_tactical_objective_assignment,
    build_trace_objective_assignments,
)
from .tactical_state import build_tactical_state_trajectory


SCHEDULE_CONTRACT = "TACTICAL_TEMPORAL_SCHEDULE_V1"
TRAJECTORY_CONTRACT = "TACTICAL_TEMPORAL_SCHEDULE_TRAJECTORY_V1"
CONTINUITY_HORIZON_MS = 30_000

# These are bounded observation/review windows, not movement-time estimates.
# They intentionally do not claim terrain, formation, or command feasibility.
ACTION_POLICIES: dict[str, dict[str, Any]] = {
    "EXTRACT_COMMANDER": {
        "urgency_rank": 100,
        "minimum_commitment_ms": 4_000,
        "review_interval_ms": 8_000,
        "maximum_commitment_ms": 20_000,
        "cooldown_ms": 6_000,
        "desired_transition": [
            "commander danger should not increase",
            "commander withdrawal recoverability should not decrease",
        ],
    },
    "EVACUATE_ARTILLERY": {
        "urgency_rank": 95,
        "minimum_commitment_ms": 5_000,
        "review_interval_ms": 10_000,
        "maximum_commitment_ms": 25_000,
        "cooldown_ms": 8_000,
        "desired_transition": [
            "artillery visible pressure should not increase",
            "artillery withdrawal recoverability should not decrease",
        ],
    },
    "DISENGAGE_CAVALRY": {
        "urgency_rank": 90,
        "minimum_commitment_ms": 3_000,
        "review_interval_ms": 7_000,
        "maximum_commitment_ms": 18_000,
        "cooldown_ms": 6_000,
        "desired_transition": [
            "cavalry danger should not increase",
            "cavalry isolation should not worsen",
        ],
    },
    "REPOSITION_RANGED": {
        "urgency_rank": 80,
        "minimum_commitment_ms": 4_000,
        "review_interval_ms": 9_000,
        "maximum_commitment_ms": 22_000,
        "cooldown_ms": 7_000,
        "desired_transition": [
            "ranged visible pressure should not increase",
            "ranged firing potential should remain available",
        ],
    },
    "TERMINATE_PURSUIT": {
        "urgency_rank": 85,
        "minimum_commitment_ms": 2_000,
        "review_interval_ms": 5_000,
        "maximum_commitment_ms": 12_000,
        "cooldown_ms": 4_000,
        "desired_transition": [
            "pursuer isolation should not increase",
            "cohesion should recover or remain stable",
        ],
    },
    "REFORM_AND_PRESERVE": {
        "urgency_rank": 70,
        "minimum_commitment_ms": 4_000,
        "review_interval_ms": 8_000,
        "maximum_commitment_ms": 20_000,
        "cooldown_ms": 6_000,
        "desired_transition": [
            "local cohesion should not decrease",
            "unnecessary exposure should not increase",
        ],
    },
    "RELIEVE_FRONTLINE": {
        "urgency_rank": 92,
        "minimum_commitment_ms": 5_000,
        "review_interval_ms": 9_000,
        "maximum_commitment_ms": 20_000,
        "cooldown_ms": 7_000,
        "desired_transition": [
            "protected frontline danger should not increase",
            "local support balance should not worsen",
        ],
    },
    "CONTAIN_LOCAL_ROUT": {
        "urgency_rank": 94,
        "minimum_commitment_ms": 4_000,
        "review_interval_ms": 8_000,
        "maximum_commitment_ms": 18_000,
        "cooldown_ms": 6_000,
        "desired_transition": [
            "local routing fraction should not increase",
            "local stability should not deteriorate",
        ],
    },
    "COMMIT_RESERVE": {
        "urgency_rank": 88,
        "minimum_commitment_ms": 4_000,
        "review_interval_ms": 8_000,
        "maximum_commitment_ms": 18_000,
        "cooldown_ms": 6_000,
        "desired_transition": [
            "reserve commitment should address a still-present crisis",
            "reserve danger should remain bounded",
        ],
    },
    "SELECTIVE_PURSUIT": {
        "urgency_rank": 60,
        "minimum_commitment_ms": 3_000,
        "review_interval_ms": 7_000,
        "maximum_commitment_ms": 16_000,
        "cooldown_ms": 5_000,
        "desired_transition": [
            "visible coherent enemy combat power may decrease",
            "pursuer preservation constraints must remain satisfied",
        ],
    },
}


class TacticalScheduleError(ValueError):
    pass


def _rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _verified_digest(record: dict[str, Any], label: str) -> None:
    claimed = record.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise TacticalScheduleError(f"{label} result digest is missing or invalid")
    payload = dict(record)
    payload.pop("result_digest", None)
    if digest(payload) != claimed:
        raise TacticalScheduleError(f"{label} result digest mismatch")


def _assignment_semantic_signature(assignment: dict[str, Any]) -> dict[str, Any]:
    objectives = []
    for item in assignment.get("objectives", []):
        objectives.append(
            {
                "objective_id": item.get("objective_id"),
                "objective_type": item.get("objective_type"),
                "source_opportunity_ids": item.get("source_opportunity_ids"),
                "subject_unit_ids": item.get("subject_unit_ids"),
                "severity": item.get("severity"),
                "objective_utility": item.get("objective_utility"),
                "candidate_actors": [
                    {
                        "actor_unit_id": candidate.get("actor_unit_id"),
                        "assignment_score": candidate.get("assignment_score"),
                    }
                    for candidate in item.get("candidate_actors", [])
                ],
                "assignment_status": item.get("assignment_status"),
                "assigned_actor_unit_id": item.get("assigned_actor_unit_id"),
                "unfilled_reason": item.get("unfilled_reason"),
            }
        )
    assignments = []
    for item in assignment.get("assignments", []):
        assignments.append(
            {
                "objective_id": item.get("objective_id"),
                "objective_type": item.get("objective_type"),
                "actor_unit_id": item.get("actor_unit_id"),
                "subject_unit_ids": item.get("subject_unit_ids"),
                "severity": item.get("severity"),
                "objective_utility": item.get("objective_utility"),
                "assignment_score": item.get("assignment_score"),
            }
        )
    return {
        "slice_id": assignment.get("slice_id"),
        "time_ms": assignment.get("time_ms"),
        "objective_count": assignment.get("objective_count"),
        "assignment_count": assignment.get("assignment_count"),
        "unfilled_objective_count": assignment.get("unfilled_objective_count"),
        "objectives": sorted(objectives, key=lambda item: str(item["objective_id"])),
        "assignments": sorted(
            assignments,
            key=lambda item: (str(item["objective_id"]), str(item["actor_unit_id"])),
        ),
    }


def validate_tactical_assignment_for_schedule(
    state: dict[str, Any], assignment: dict[str, Any]
) -> dict[str, Any]:
    _verified_digest(state, "tactical state")
    _verified_digest(assignment, "tactical assignment")
    if state.get("state_contract") != "TACTICAL_STATE_VISIBILITY_SAFE_V2":
        raise TacticalScheduleError("unsupported tactical state contract")
    if state.get("authority") != "NO_ORDERS":
        raise TacticalScheduleError("schedule input state must retain NO_ORDERS authority")
    if assignment.get("assignment_contract") != ASSIGNMENT_CONTRACT:
        raise TacticalScheduleError("unsupported tactical assignment contract")
    if assignment.get("authority") != "NO_ORDERS":
        raise TacticalScheduleError(
            "schedule input assignment must retain NO_ORDERS authority"
        )
    if assignment.get("source_tactical_state_digest") != state.get("result_digest"):
        raise TacticalScheduleError("assignment source tactical-state digest mismatch")
    if assignment.get("slice_id") != state.get("slice_id"):
        raise TacticalScheduleError("assignment slice identity mismatch")
    if assignment.get("time_ms") != state.get("time_ms"):
        raise TacticalScheduleError("assignment time mismatch")

    for objective in assignment.get("objectives", []):
        if not isinstance(objective, dict):
            raise TacticalScheduleError("assignment objective must be an object")
        _verified_digest(objective, "assignment objective")
    for proposed in assignment.get("assignments", []):
        if not isinstance(proposed, dict):
            raise TacticalScheduleError("assignment proposal must be an object")
        _verified_digest(proposed, "assignment proposal")
        if proposed.get("status") != "PROPOSED_NOT_EXECUTED":
            raise TacticalScheduleError(
                "assignment proposal must remain PROPOSED_NOT_EXECUTED"
            )
        if proposed.get("authority") != "ADVISORY_ONLY":
            raise TacticalScheduleError("assignment proposal must remain ADVISORY_ONLY")

    canonical = build_tactical_objective_assignment(state)
    if _assignment_semantic_signature(assignment) != _assignment_semantic_signature(
        canonical
    ):
        raise TacticalScheduleError(
            "assignment semantics differ from the canonical state-derived assignment"
        )
    return assignment


def _unit_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        unit["observed"]["stable_unit_id"]: unit
        for unit in state.get("units", [])
    }


def _actor_precondition_failure(
    state: dict[str, Any], actor_unit_id: str
) -> str | None:
    unit = _unit_map(state).get(actor_unit_id)
    if unit is None:
        return "ACTOR_NOT_OBSERVED"
    observed = unit["observed"]
    if not observed["local_alliance"]:
        return "ACTOR_NOT_LOCAL"
    if observed["routing"]:
        return "ACTOR_ROUTING"
    if observed["shattered"]:
        return "ACTOR_SHATTERED"
    if observed["leaving"]:
        return "ACTOR_LEAVING_BATTLE"
    if observed["rampaging"]:
        return "ACTOR_RAMPAGING"
    return None


def _candidate_ids(objective: dict[str, Any]) -> set[str]:
    return {
        item["actor_unit_id"]
        for item in objective.get("candidate_actors", [])
        if isinstance(item, dict) and isinstance(item.get("actor_unit_id"), str)
    }


def _objective_priority(objective: dict[str, Any]) -> tuple[int, int, int, str]:
    action = ACTION_POLICIES.get(objective["objective_type"])
    if action is None:
        raise TacticalScheduleError(
            f"unsupported objective type for scheduling: {objective['objective_type']}"
        )
    return (
        SEVERITY_RANK[objective["severity"]],
        int(round(float(objective["objective_utility"]) * 1_000_000)),
        int(action["urgency_rank"]),
        str(objective["objective_id"]),
    )


def _plan_priority(plan: dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        SEVERITY_RANK[plan["severity"]],
        int(round(float(plan["objective_utility"]) * 1_000_000)),
        int(ACTION_POLICIES[plan["objective_type"]]["urgency_rank"]),
        str(plan["objective_id"]),
    )


def _event(
    *,
    slice_id: str,
    time_ms: int,
    event_type: str,
    actor_unit_id: str | None,
    objective_id: str | None,
    plan_instance_id: str | None,
    reason: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "event_type": event_type,
        "slice_id": slice_id,
        "time_ms": time_ms,
        "actor_unit_id": actor_unit_id,
        "objective_id": objective_id,
        "plan_instance_id": plan_instance_id,
        "reason": reason,
        "details": details or {},
        "causal_attribution": "NOT_ESTABLISHED",
        "authority": "ADVISORY_ONLY",
    }
    record["event_id"] = digest(record)
    return record


def _blocked_assignment(
    proposal: dict[str, Any], reason: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    record = {
        "objective_id": proposal["objective_id"],
        "objective_type": proposal["objective_type"],
        "actor_unit_id": proposal["actor_unit_id"],
        "severity": proposal["severity"],
        "reason": reason,
        "details": details or {},
        "status": "NOT_SCHEDULED",
        "authority": "ADVISORY_ONLY",
    }
    record["result_digest"] = digest(record)
    return record


def _new_plan(
    proposal: dict[str, Any], objective: dict[str, Any], time_ms: int
) -> dict[str, Any]:
    policy = ACTION_POLICIES[proposal["objective_type"]]
    identity = {
        "actor_unit_id": proposal["actor_unit_id"],
        "objective_id": proposal["objective_id"],
        "objective_type": proposal["objective_type"],
        "start_time_ms": time_ms,
    }
    plan = {
        "plan_instance_id": digest(identity),
        "plan_key": f"{proposal['actor_unit_id']}|{proposal['objective_id']}",
        "actor_unit_id": proposal["actor_unit_id"],
        "actor_role": proposal["actor_role"],
        "objective_id": proposal["objective_id"],
        "objective_type": proposal["objective_type"],
        "subject_unit_ids": proposal["subject_unit_ids"],
        "severity": proposal["severity"],
        "objective_utility": proposal["objective_utility"],
        "source_assignment_digest": proposal["result_digest"],
        "start_time_ms": time_ms,
        "last_observed_time_ms": time_ms,
        "observed_age_ms": 0,
        "minimum_commitment_ms": policy["minimum_commitment_ms"],
        "review_interval_ms": policy["review_interval_ms"],
        "maximum_commitment_ms": policy["maximum_commitment_ms"],
        "cooldown_ms": policy["cooldown_ms"],
        "next_review_time_ms": time_ms + policy["review_interval_ms"],
        "minimum_commitment_until_ms": time_ms + policy["minimum_commitment_ms"],
        "maximum_commitment_until_ms": time_ms + policy["maximum_commitment_ms"],
        "review_due": False,
        "transition_envelope": {
            "model": "DIRECTIONAL_OBSERVATION_ONLY",
            "desired_transition": list(policy["desired_transition"]),
            "predicted_position": None,
            "predicted_casualties": None,
            "predicted_success_probability": None,
            "terrain_pathfinding_available": False,
            "formation_feasibility_available": False,
        },
        "preconditions": [
            "actor remains observed on the local alliance",
            "actor remains non-routing, non-shattered, non-leaving, and non-rampaging",
            "objective remains present in a canonical state-derived assignment",
            "actor remains a legal objective candidate unless a higher-priority objective supersedes it",
        ],
        "cancellation_conditions": [
            "terminal battle observation",
            "actor control-state precondition failure",
            "objective retirement by later observation",
            "higher-priority supersession",
            "continuity gap beyond the bounded horizon",
            "maximum commitment requires explicit replan",
        ],
        "status": "ABSTRACT_SCHEDULED_NOT_ISSUED",
        "runtime_feasibility": "UNVERIFIED",
        "counterfactual_status": "UNVERIFIED",
        "authority": "NO_ORDERS",
    }
    return plan


def _plan_output(plan: dict[str, Any], current_time_ms: int) -> dict[str, Any]:
    result = dict(plan)
    result["last_observed_time_ms"] = current_time_ms
    result["observed_age_ms"] = current_time_ms - int(plan["start_time_ms"])
    result["review_due"] = current_time_ms >= int(plan["next_review_time_ms"])
    result["minimum_commitment_remaining_ms"] = max(
        0, int(plan["minimum_commitment_until_ms"]) - current_time_ms
    )
    result["maximum_commitment_remaining_ms"] = max(
        0, int(plan["maximum_commitment_until_ms"]) - current_time_ms
    )
    result["result_digest"] = digest(result)
    return result


def _set_cooldown(
    cooldowns: dict[tuple[str, str], int], plan: dict[str, Any], time_ms: int
) -> None:
    cooldowns[(plan["actor_unit_id"], plan["objective_type"])] = max(
        cooldowns.get((plan["actor_unit_id"], plan["objective_type"]), 0),
        time_ms + int(plan["cooldown_ms"]),
    )


def build_tactical_temporal_schedule(
    states: Iterable[dict[str, Any]],
    assignments: Iterable[dict[str, Any]],
    *,
    source_id: str,
    evidence_status: str,
) -> dict[str, Any]:
    state_list = list(states)
    assignment_list = list(assignments)
    if len(state_list) != len(assignment_list):
        raise TacticalScheduleError("state and assignment sequence lengths differ")
    if not source_id:
        raise TacticalScheduleError("source_id must be nonempty")

    active_by_actor: dict[str, dict[str, Any]] = {}
    cooldowns: dict[tuple[str, str], int] = {}
    schedule_slices: list[dict[str, Any]] = []
    previous_time_ms: int | None = None

    for index, (state, assignment) in enumerate(
        zip(state_list, assignment_list, strict=True)
    ):
        validate_tactical_assignment_for_schedule(state, assignment)
        time_ms = state.get("time_ms")
        if not isinstance(time_ms, int) or isinstance(time_ms, bool) or time_ms < 0:
            raise TacticalScheduleError("state time_ms must be a nonnegative integer")
        if previous_time_ms is not None and time_ms <= previous_time_ms:
            raise TacticalScheduleError("schedule observations must be strictly increasing")
        gap_ms = None if previous_time_ms is None else time_ms - previous_time_ms
        slice_id = state["slice_id"]
        events: list[dict[str, Any]] = []
        blocked: list[dict[str, Any]] = []
        consumed_objectives: set[str] = set()

        if previous_time_ms is None:
            continuity_class = "INITIAL_OBSERVATION"
        elif gap_ms is not None and gap_ms > CONTINUITY_HORIZON_MS:
            continuity_class = "CONTINUITY_RESET_OBSERVATION_GAP"
            for actor_id, plan in sorted(active_by_actor.items()):
                events.append(
                    _event(
                        slice_id=slice_id,
                        time_ms=time_ms,
                        event_type="CONTINUITY_RESET_OBSERVATION_GAP",
                        actor_unit_id=actor_id,
                        objective_id=plan["objective_id"],
                        plan_instance_id=plan["plan_instance_id"],
                        reason="The observation gap exceeds the bounded continuity horizon; continuation, completion, and cancellation are unknown.",
                        details={
                            "observation_gap_ms": gap_ms,
                            "continuity_horizon_ms": CONTINUITY_HORIZON_MS,
                        },
                    )
                )
            active_by_actor.clear()
            cooldowns.clear()
        else:
            continuity_class = "WITHIN_BOUNDED_HORIZON"

        objectives = {
            item["objective_id"]: item for item in assignment["objectives"]
        }
        proposals = {
            item["objective_id"]: item for item in assignment["assignments"]
        }
        proposal_by_actor = {
            item["actor_unit_id"]: item for item in assignment["assignments"]
        }
        if len(proposal_by_actor) != len(assignment["assignments"]):
            raise TacticalScheduleError("assignment double-books an actor")

        terminal = (
            state["battle_state"]["local_stability_state"] == "TERMINAL"
            or state["battle_state"]["outcome_state"] == "TERMINAL"
        )

        if terminal:
            continuity_class = "TERMINAL_OBSERVATION"
            for actor_id, plan in sorted(active_by_actor.items()):
                events.append(
                    _event(
                        slice_id=slice_id,
                        time_ms=time_ms,
                        event_type="PLAN_CANCELLED_TERMINAL",
                        actor_unit_id=actor_id,
                        objective_id=plan["objective_id"],
                        plan_instance_id=plan["plan_instance_id"],
                        reason="A terminal battle observation ends all abstract advisory commitments.",
                    )
                )
            active_by_actor.clear()
            cooldowns.clear()
        else:
            for actor_id, plan in list(sorted(active_by_actor.items())):
                objective = objectives.get(plan["objective_id"])
                proposal = proposals.get(plan["objective_id"])
                actor_proposal = proposal_by_actor.get(actor_id)
                failure = _actor_precondition_failure(state, actor_id)
                age_ms = time_ms - int(plan["start_time_ms"])

                if failure is not None:
                    events.append(
                        _event(
                            slice_id=slice_id,
                            time_ms=time_ms,
                            event_type="PLAN_CANCELLED_PRECONDITION_FAILED",
                            actor_unit_id=actor_id,
                            objective_id=plan["objective_id"],
                            plan_instance_id=plan["plan_instance_id"],
                            reason="The observed actor no longer satisfies the bounded control-state preconditions.",
                            details={"precondition_failure": failure},
                        )
                    )
                    _set_cooldown(cooldowns, plan, time_ms)
                    active_by_actor.pop(actor_id, None)
                    continue

                if objective is None:
                    events.append(
                        _event(
                            slice_id=slice_id,
                            time_ms=time_ms,
                            event_type="PLAN_RESOLVED_BY_OBSERVATION_NOT_ATTRIBUTED",
                            actor_unit_id=actor_id,
                            objective_id=plan["objective_id"],
                            plan_instance_id=plan["plan_instance_id"],
                            reason="The objective is absent from the later canonical observation; no causal credit is assigned to the advisory plan.",
                        )
                    )
                    _set_cooldown(cooldowns, plan, time_ms)
                    active_by_actor.pop(actor_id, None)
                    continue

                if objective["objective_type"] != plan["objective_type"]:
                    replacement_priority = _objective_priority(objective)
                    if proposal is not None and proposal["actor_unit_id"] == actor_id:
                        event_type = (
                            "PLAN_SUPERSEDED_HIGHER_PRIORITY"
                            if replacement_priority > _plan_priority(plan)
                            else "PLAN_REDEFINED_AFTER_OBSERVATION"
                        )
                        events.append(
                            _event(
                                slice_id=slice_id,
                                time_ms=time_ms,
                                event_type=event_type,
                                actor_unit_id=actor_id,
                                objective_id=plan["objective_id"],
                                plan_instance_id=plan["plan_instance_id"],
                                reason="The same stable objective identity now requires a different observed action class.",
                                details={
                                    "previous_objective_type": plan["objective_type"],
                                    "replacement_objective_type": objective[
                                        "objective_type"
                                    ],
                                },
                            )
                        )
                        _set_cooldown(cooldowns, plan, time_ms)
                        active_by_actor.pop(actor_id, None)
                        continue
                    events.append(
                        _event(
                            slice_id=slice_id,
                            time_ms=time_ms,
                            event_type="PLAN_CANCELLED_OBJECTIVE_REDEFINED",
                            actor_unit_id=actor_id,
                            objective_id=plan["objective_id"],
                            plan_instance_id=plan["plan_instance_id"],
                            reason="The objective action class changed and the prior actor is not the current canonical responder.",
                        )
                    )
                    _set_cooldown(cooldowns, plan, time_ms)
                    active_by_actor.pop(actor_id, None)
                    continue

                if age_ms >= int(plan["maximum_commitment_ms"]):
                    events.append(
                        _event(
                            slice_id=slice_id,
                            time_ms=time_ms,
                            event_type="PLAN_REVIEW_REQUIRED_MAX_COMMITMENT",
                            actor_unit_id=actor_id,
                            objective_id=plan["objective_id"],
                            plan_instance_id=plan["plan_instance_id"],
                            reason="The bounded maximum advisory commitment elapsed; persistence requires a fresh canonical plan instance.",
                            details={"observed_age_ms": age_ms},
                        )
                    )
                    active_by_actor.pop(actor_id, None)
                    continue

                if proposal is not None and proposal["actor_unit_id"] == actor_id:
                    plan["last_observed_time_ms"] = time_ms
                    plan["severity"] = objective["severity"]
                    plan["objective_utility"] = objective["objective_utility"]
                    plan["source_assignment_digest"] = proposal["result_digest"]
                    events.append(
                        _event(
                            slice_id=slice_id,
                            time_ms=time_ms,
                            event_type="PLAN_CONTINUED",
                            actor_unit_id=actor_id,
                            objective_id=plan["objective_id"],
                            plan_instance_id=plan["plan_instance_id"],
                            reason="The same canonical objective and actor remain selected within the bounded continuity horizon.",
                            details={"observed_age_ms": age_ms},
                        )
                    )
                    consumed_objectives.add(plan["objective_id"])
                    continue

                if actor_proposal is not None and actor_proposal["objective_id"] != plan[
                    "objective_id"
                ]:
                    replacement_objective = objectives[actor_proposal["objective_id"]]
                    higher_priority = _objective_priority(
                        replacement_objective
                    ) > _plan_priority(plan)
                    critical_override = replacement_objective["severity"] == "CRITICAL"
                    self_protection_override = (
                        replacement_objective.get("actor_pool_mode") == "EXACT_SUBJECT"
                    )
                    if (higher_priority or self_protection_override) and (
                        age_ms >= int(plan["minimum_commitment_ms"])
                        or critical_override
                        or self_protection_override
                    ):
                        events.append(
                            _event(
                                slice_id=slice_id,
                                time_ms=time_ms,
                                event_type="PLAN_SUPERSEDED_HIGHER_PRIORITY",
                                actor_unit_id=actor_id,
                                objective_id=plan["objective_id"],
                                plan_instance_id=plan["plan_instance_id"],
                                reason="The canonical assignment gives the actor a higher-priority objective under the bounded supersession rule.",
                                details={
                                    "replacement_objective_id": actor_proposal[
                                        "objective_id"
                                    ],
                                    "critical_override": critical_override,
                                    "self_protection_override": self_protection_override,
                                },
                            )
                        )
                        _set_cooldown(cooldowns, plan, time_ms)
                        active_by_actor.pop(actor_id, None)
                        continue
                    if actor_id in _candidate_ids(objective):
                        consumed_objectives.add(plan["objective_id"])
                        blocked.append(
                            _blocked_assignment(
                                actor_proposal,
                                "ACTIVE_MINIMUM_COMMITMENT",
                                {
                                    "retained_objective_id": plan["objective_id"],
                                    "minimum_commitment_until_ms": plan[
                                        "minimum_commitment_until_ms"
                                    ],
                                },
                            )
                        )
                        events.append(
                            _event(
                                slice_id=slice_id,
                                time_ms=time_ms,
                                event_type="PLAN_RETAINED_MINIMUM_COMMITMENT",
                                actor_unit_id=actor_id,
                                objective_id=plan["objective_id"],
                                plan_instance_id=plan["plan_instance_id"],
                                reason="The prior legal actor remains committed; the lower-priority reassignment is deferred.",
                            )
                        )
                        continue

                if actor_id in _candidate_ids(objective) and age_ms < int(
                    plan["minimum_commitment_ms"]
                ):
                    consumed_objectives.add(plan["objective_id"])
                    if proposal is not None:
                        blocked.append(
                            _blocked_assignment(
                                proposal,
                                "MINIMUM_COMMITMENT_RETAINS_PRIOR_ACTOR",
                                {
                                    "retained_actor_unit_id": actor_id,
                                    "minimum_commitment_until_ms": plan[
                                        "minimum_commitment_until_ms"
                                    ],
                                },
                            )
                        )
                    events.append(
                        _event(
                            slice_id=slice_id,
                            time_ms=time_ms,
                            event_type="PLAN_RETAINED_MINIMUM_COMMITMENT",
                            actor_unit_id=actor_id,
                            objective_id=plan["objective_id"],
                            plan_instance_id=plan["plan_instance_id"],
                            reason="The same objective persists and the prior actor remains legal during the minimum commitment window.",
                        )
                    )
                    continue

                events.append(
                    _event(
                        slice_id=slice_id,
                        time_ms=time_ms,
                        event_type="PLAN_REASSIGNED_AFTER_REVIEW",
                        actor_unit_id=actor_id,
                        objective_id=plan["objective_id"],
                        plan_instance_id=plan["plan_instance_id"],
                        reason="The minimum commitment elapsed or the prior actor is no longer a legal candidate; the current canonical assignment may replace it.",
                        details={
                            "replacement_actor_unit_id": None
                            if proposal is None
                            else proposal["actor_unit_id"]
                        },
                    )
                )
                _set_cooldown(cooldowns, plan, time_ms)
                active_by_actor.pop(actor_id, None)

            proposals_in_priority_order = sorted(
                assignment["assignments"],
                key=lambda item: (
                    -SEVERITY_RANK[item["severity"]],
                    -float(item["objective_utility"]),
                    item["objective_id"],
                    item["actor_unit_id"],
                ),
            )
            for proposal in proposals_in_priority_order:
                objective_id = proposal["objective_id"]
                actor_id = proposal["actor_unit_id"]
                objective = objectives[objective_id]
                if objective_id in consumed_objectives:
                    continue
                if actor_id in active_by_actor:
                    blocked.append(
                        _blocked_assignment(
                            proposal,
                            "ACTOR_HAS_ACTIVE_COMMITMENT",
                            {
                                "active_objective_id": active_by_actor[actor_id][
                                    "objective_id"
                                ]
                            },
                        )
                    )
                    continue
                cooldown_until = cooldowns.get(
                    (actor_id, proposal["objective_type"]), 0
                )
                if time_ms < cooldown_until:
                    if proposal["severity"] == "CRITICAL":
                        events.append(
                            _event(
                                slice_id=slice_id,
                                time_ms=time_ms,
                                event_type="PLAN_COOLDOWN_OVERRIDDEN_CRITICAL",
                                actor_unit_id=actor_id,
                                objective_id=objective_id,
                                plan_instance_id=None,
                                reason="A critical canonical objective overrides the same-action cooldown.",
                                details={"cooldown_until_ms": cooldown_until},
                            )
                        )
                    else:
                        blocked.append(
                            _blocked_assignment(
                                proposal,
                                "SAME_ACTION_COOLDOWN",
                                {"cooldown_until_ms": cooldown_until},
                            )
                        )
                        events.append(
                            _event(
                                slice_id=slice_id,
                                time_ms=time_ms,
                                event_type="PLAN_BLOCKED_COOLDOWN",
                                actor_unit_id=actor_id,
                                objective_id=objective_id,
                                plan_instance_id=None,
                                reason="The same actor/action pair remains inside its bounded cooldown.",
                                details={"cooldown_until_ms": cooldown_until},
                            )
                        )
                        continue
                plan = _new_plan(proposal, objective, time_ms)
                active_by_actor[actor_id] = plan
                events.append(
                    _event(
                        slice_id=slice_id,
                        time_ms=time_ms,
                        event_type="PLAN_STARTED",
                        actor_unit_id=actor_id,
                        objective_id=objective_id,
                        plan_instance_id=plan["plan_instance_id"],
                        reason="A canonical per-slice assignment becomes a bounded abstract advisory commitment; no order is issued.",
                    )
                )

        active_outputs = [
            _plan_output(plan, time_ms)
            for _, plan in sorted(active_by_actor.items())
        ]
        active_actor_ids = [item["actor_unit_id"] for item in active_outputs]
        record: dict[str, Any] = {
            "schema_version": 1,
            "schedule_contract": SCHEDULE_CONTRACT,
            "sequence_index": index,
            "slice_id": slice_id,
            "time_ms": time_ms,
            "observation_gap_ms": gap_ms,
            "continuity_class": continuity_class,
            "continuity_horizon_ms": CONTINUITY_HORIZON_MS,
            "source_tactical_state_digest": state["result_digest"],
            "source_assignment_digest": assignment["result_digest"],
            "raw_assignment_count": assignment["assignment_count"],
            "active_plan_count": len(active_outputs),
            "blocked_assignment_count": len(blocked),
            "double_booked_active_actor_count": len(active_actor_ids)
            - len(set(active_actor_ids)),
            "events": events,
            "blocked_assignments": sorted(
                blocked,
                key=lambda item: (
                    item["objective_id"],
                    item["actor_unit_id"],
                    item["reason"],
                ),
            ),
            "active_plans": active_outputs,
            "abstract_transition_model": {
                "state_machine": [
                    "START",
                    "CONTINUE",
                    "RETAIN",
                    "REVIEW",
                    "SUPERSEDE",
                    "RESOLVE_BY_OBSERVATION",
                    "CANCEL",
                    "COOLDOWN",
                    "CONTINUITY_UNKNOWN",
                ],
                "numeric_state_prediction": False,
                "path_prediction": False,
                "formation_prediction": False,
                "causal_credit": False,
            },
            "evidence_status": evidence_status,
            "counterfactual_status": "UNVERIFIED",
            "authority": "NO_ORDERS",
        }
        record["result_digest"] = digest(record)
        schedule_slices.append(record)
        previous_time_ms = time_ms

    event_counts: dict[str, int] = {}
    for schedule_slice in schedule_slices:
        for item in schedule_slice["events"]:
            event_counts[item["event_type"]] = event_counts.get(item["event_type"], 0) + 1
    result: dict[str, Any] = {
        "schema_version": 1,
        "schedule_contract": TRAJECTORY_CONTRACT,
        "source_id": source_id,
        "source_state_digests": [state["result_digest"] for state in state_list],
        "source_assignment_digests": [
            assignment["result_digest"] for assignment in assignment_list
        ],
        "schedule_slice_count": len(schedule_slices),
        "schedule_slices": schedule_slices,
        "summary": {
            "raw_assignment_count": sum(
                item["raw_assignment_count"] for item in schedule_slices
            ),
            "plan_start_count": event_counts.get("PLAN_STARTED", 0),
            "plan_continue_count": event_counts.get("PLAN_CONTINUED", 0),
            "plan_retained_count": event_counts.get(
                "PLAN_RETAINED_MINIMUM_COMMITMENT", 0
            ),
            "plan_reassignment_count": event_counts.get(
                "PLAN_REASSIGNED_AFTER_REVIEW", 0
            ),
            "plan_supersession_count": event_counts.get(
                "PLAN_SUPERSEDED_HIGHER_PRIORITY", 0
            ),
            "plan_resolution_count": event_counts.get(
                "PLAN_RESOLVED_BY_OBSERVATION_NOT_ATTRIBUTED", 0
            ),
            "plan_precondition_cancellation_count": event_counts.get(
                "PLAN_CANCELLED_PRECONDITION_FAILED", 0
            ),
            "plan_terminal_cancellation_count": event_counts.get(
                "PLAN_CANCELLED_TERMINAL", 0
            ),
            "plan_maximum_commitment_review_count": event_counts.get(
                "PLAN_REVIEW_REQUIRED_MAX_COMMITMENT", 0
            ),
            "cooldown_block_count": event_counts.get("PLAN_BLOCKED_COOLDOWN", 0),
            "critical_cooldown_override_count": event_counts.get(
                "PLAN_COOLDOWN_OVERRIDDEN_CRITICAL", 0
            ),
            "continuity_reset_count": event_counts.get(
                "CONTINUITY_RESET_OBSERVATION_GAP", 0
            ),
            "maximum_active_plans_in_one_slice": max(
                (item["active_plan_count"] for item in schedule_slices), default=0
            ),
            "double_booked_active_actor_count": sum(
                item["double_booked_active_actor_count"]
                for item in schedule_slices
            ),
            "event_counts": dict(sorted(event_counts.items())),
        },
        "interpretation_limits": [
            "The scheduler reconciles advisory proposals; it does not issue WH3 orders.",
            "Commitment, review, and cooldown windows are project-owned bounded control contracts, not measured movement times.",
            "Objective disappearance is resolution by observation only and receives no causal credit.",
            "Observation gaps beyond the continuity horizon erase lifecycle certainty rather than fabricating completion.",
            "The transition envelope predicts no coordinates, path, casualties, success probability, or formation feasibility.",
        ],
        "evidence_status": evidence_status,
        "counterfactual_status": "UNVERIFIED",
        "authority": "NO_ORDERS",
    }
    result["result_digest"] = digest(result)
    return result


def build_trace_tactical_temporal_schedule(
    trace_corpus: dict[str, Any]
) -> dict[str, Any]:
    trajectory = build_tactical_state_trajectory(trace_corpus)
    assignments = build_trace_objective_assignments(trace_corpus)
    result = build_tactical_temporal_schedule(
        trajectory["states"],
        assignments["assignment_slices"],
        source_id="BATTLE4_EILHART_VISIBILITY_SAFE_TRACE",
        evidence_status="CONTROL_OFFLINE_DERIVED_FROM_OBSERVED_INPUT",
    )
    result["source_trace_digest"] = trajectory["source_trace_digest"]
    result["source_tactical_state_trajectory_digest"] = trajectory["result_digest"]
    result["source_assignment_trajectory_digest"] = assignments["result_digest"]
    result.pop("result_digest", None)
    result["result_digest"] = digest(result)
    return result
