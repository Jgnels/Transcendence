from __future__ import annotations

from copy import deepcopy
from typing import Any

from .campaign_challenge import APPLICATION_AUTHORITY, AUTHORITY, RECOVERY_REPLENISHMENT_THRESHOLD
from .canonical import digest
from .contracts import validate_campaign_scenario
from .strategic_assignment import build_theater_to_army_assignment
from .strategic_portfolio import SEVERITY_RANK

CONTRACT = "CAMPAIGN_STRATEGIC_TEMPORAL_COMMITMENT_V1"
MIN_COMMITMENT_TURNS = 2
MAX_COMMITMENT_TURNS = 4
REASSIGN_SCORE_MARGIN = 0.15


class StrategicCommitmentError(ValueError):
    pass


def _army_map(scenario: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in scenario["armies"]
        if item["faction"] == scenario["controlled_faction"]
        and not (isinstance(item.get("observation"), dict) and item["observation"].get("planner_eligible") is False)
    }


def _priority_map(assignment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["priority_id"]: item for item in assignment["effective_priorities"]}


def _ranking_for(assignment: dict[str, Any], priority_id: str) -> list[dict[str, Any]]:
    return assignment.get("candidate_rankings", {}).get(priority_id, [])


def _candidate_for_actor(assignment: dict[str, Any], priority_id: str, actor_id: str) -> dict[str, Any] | None:
    return next((item for item in _ranking_for(assignment, priority_id) if item["actor_id"] == actor_id), None)


def _fresh_assignment_map(assignment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["priority_id"]: item for item in assignment["assignments"]}


def _event(event_type: str, turn: int, priority_id: str, actor_id: str | None, reason: str) -> dict[str, Any]:
    record = {
        "event_type": event_type,
        "turn": turn,
        "priority_id": priority_id,
        "actor_id": actor_id,
        "reason": reason,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
    }
    record["result_digest"] = digest(record)
    return record


def _plan(priority: dict[str, Any], assignment: dict[str, Any], turn: int) -> dict[str, Any]:
    record = {
        "priority_id": priority["priority_id"],
        "priority_type": priority["priority_type"],
        "severity": priority["severity"],
        "actor_id": assignment["actor_id"],
        "assignment_kind": assignment["assignment_kind"],
        "started_turn": turn,
        "last_review_turn": turn,
        "commitment_age_turns": 0,
        "status": "ACTIVE_SHADOW_COMMITMENT_NOT_EXECUTED",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
    }
    record["plan_id"] = digest({"priority_id": record["priority_id"], "actor_id": record["actor_id"], "started_turn": turn})
    return record


def build_strategic_temporal_commitment(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(scenarios, list) or not scenarios:
        raise StrategicCommitmentError("scenario sequence must be nonempty")
    validated = [validate_campaign_scenario(item) for item in scenarios]
    factions = {item["controlled_faction"] for item in validated}
    if len(factions) != 1:
        raise StrategicCommitmentError("scenario sequence must keep one controlled faction")
    turns = [item["turn"] for item in validated]
    if turns != sorted(turns) or len(turns) != len(set(turns)):
        raise StrategicCommitmentError("scenario turns must be unique and increasing")

    active: dict[str, dict[str, Any]] = {}
    slices: list[dict[str, Any]] = []
    all_events: list[dict[str, Any]] = []
    previous_turn: int | None = None

    for scenario in validated:
        turn = scenario["turn"]
        assignment = build_theater_to_army_assignment(scenario)
        priorities = _priority_map(assignment)
        fresh = _fresh_assignment_map(assignment)
        armies = _army_map(scenario)
        events: list[dict[str, Any]] = []

        if previous_turn is not None and turn != previous_turn + 1:
            for plan in sorted(active.values(), key=lambda item: (item["priority_id"], item["actor_id"])):
                events.append(_event("CONTINUITY_RESET", turn, plan["priority_id"], plan["actor_id"], "TURN_GAP_BREAKS_COMMITMENT_CONTINUITY"))
            active = {}

        # Retire or cancel plans whose source/actor no longer supports continuity.
        for priority_id, plan in list(active.items()):
            priority = priorities.get(priority_id)
            actor = armies.get(plan["actor_id"])
            if priority is None:
                events.append(_event("RETIRE", turn, priority_id, plan["actor_id"], "PRIORITY_NO_LONGER_PRESENT_NO_CAUSAL_CREDIT"))
                del active[priority_id]
                continue
            if actor is None:
                events.append(_event("CANCEL", turn, priority_id, plan["actor_id"], "ACTOR_UNAVAILABLE"))
                del active[priority_id]
                continue
            if float(actor["replenishment"]) < RECOVERY_REPLENISHMENT_THRESHOLD and priority["severity"] != "CRITICAL":
                events.append(_event("CANCEL", turn, priority_id, plan["actor_id"], "ACTOR_ENTERED_RECOVERY_PROTECTION"))
                del active[priority_id]
                continue
            fresh_unfilled = next((item for item in assignment["unfilled_priorities"] if item["priority_id"] == priority_id), None)
            if fresh_unfilled is not None and "AGGRESSIVE_COMMITMENT_VETO" in fresh_unfilled["reason"]:
                events.append(_event("CANCEL", turn, priority_id, plan["actor_id"], "AGGRESSIVE_COMMITMENT_VETO"))
                del active[priority_id]

        # Higher-severity fresh work can supersede a lower-severity active claim on the same actor.
        fresh_by_actor = {item["actor_id"]: item for item in assignment["assignments"]}
        for priority_id, plan in list(active.items()):
            incoming = fresh_by_actor.get(plan["actor_id"])
            if incoming is None or incoming["priority_id"] == priority_id:
                continue
            if incoming["priority_id"] in active and incoming["priority_id"] != priority_id:
                # The higher-scoring fresh proposal is already covered by another retained plan; do not steal this actor merely because geometry changed.
                continue
            current_priority = priorities.get(priority_id)
            incoming_priority = priorities.get(incoming["priority_id"])
            if current_priority is None or incoming_priority is None:
                continue
            if SEVERITY_RANK[incoming_priority["severity"]] > SEVERITY_RANK[current_priority["severity"]]:
                events.append(_event("SUPERSEDE", turn, priority_id, plan["actor_id"], f"HIGHER_SEVERITY:{incoming_priority['priority_type']}"))
                del active[priority_id]

        claimed_actors = {plan["actor_id"] for plan in active.values()}

        # Continue active commitments when valid. This is the primary anti-thrashing rule.
        for priority_id, plan in sorted(active.items()):
            priority = priorities[priority_id]
            candidate = _candidate_for_actor(assignment, priority_id, plan["actor_id"])
            fresh_item = fresh.get(priority_id)
            age = turn - int(plan["started_turn"])
            plan["commitment_age_turns"] = age
            plan["last_review_turn"] = turn
            if candidate is not None and candidate.get("eligible"):
                if fresh_item is not None and fresh_item["actor_id"] != plan["actor_id"]:
                    fresh_score = float(fresh_item.get("assignment_score") or 0.0)
                    old_score = float(candidate.get("assignment_score") or 0.0)
                    if age >= MAX_COMMITMENT_TURNS and fresh_score - old_score >= REASSIGN_SCORE_MARGIN and fresh_item["actor_id"] not in claimed_actors:
                        old_actor = plan["actor_id"]
                        plan["actor_id"] = fresh_item["actor_id"]
                        plan["started_turn"] = turn
                        plan["commitment_age_turns"] = 0
                        plan["plan_id"] = digest({"priority_id": priority_id, "actor_id": plan["actor_id"], "started_turn": turn})
                        claimed_actors.discard(old_actor)
                        claimed_actors.add(plan["actor_id"])
                        events.append(_event("REASSIGN_AFTER_REVIEW", turn, priority_id, plan["actor_id"], "MAX_WINDOW_AND_MATERIAL_SCORE_MARGIN"))
                    else:
                        events.append(_event("CONTINUE", turn, priority_id, plan["actor_id"], "ANTI_THRASH_RETAIN_EXISTING_ACTOR"))
                else:
                    events.append(_event("CONTINUE", turn, priority_id, plan["actor_id"], "PRIORITY_AND_ACTOR_REMAIN_VALID"))
            else:
                # Candidate ranking can omit actors only above the output bound; controlled actor validity still permits continuity.
                actor = armies.get(plan["actor_id"])
                if actor is not None and (float(actor["replenishment"]) >= RECOVERY_REPLENISHMENT_THRESHOLD or priority["severity"] == "CRITICAL"):
                    events.append(_event("CONTINUE", turn, priority_id, plan["actor_id"], "ACTOR_VALID_OUTSIDE_RANKING_WINDOW"))
                else:
                    events.append(_event("CANCEL", turn, priority_id, plan["actor_id"], "ACTOR_NO_LONGER_ELIGIBLE"))
                    claimed_actors.discard(plan["actor_id"])
                    del active[priority_id]

        # Start current proposals not already covered, respecting active actor exclusivity.
        for item in sorted(
            assignment["assignments"],
            key=lambda x: (-SEVERITY_RANK[x["severity"]], -int(round(float(x.get("assignment_score") or 0.0) * 1_000_000)), x["priority_id"], x["actor_id"]),
        ):
            priority_id = item["priority_id"]
            if priority_id in active:
                continue
            actor_id = item["actor_id"]
            if actor_id in claimed_actors:
                # Try next eligible candidate not already claimed for the same priority.
                replacement = next(
                    (
                        cand for cand in _ranking_for(assignment, priority_id)
                        if cand.get("eligible") and cand["actor_id"] not in claimed_actors
                    ),
                    None,
                )
                if replacement is None:
                    events.append(_event("BLOCKED", turn, priority_id, None, "TEMPORAL_ACTOR_CONFLICT"))
                    continue
                item = deepcopy(item)
                item["actor_id"] = replacement["actor_id"]
                item["assignment_score"] = replacement.get("assignment_score")
                actor_id = item["actor_id"]
            priority = priorities[priority_id]
            active[priority_id] = _plan(priority, item, turn)
            claimed_actors.add(actor_id)
            events.append(_event("START", turn, priority_id, actor_id, "NEW_SHADOW_COMMITMENT"))

        double_booked = sorted(
            actor_id
            for actor_id in {plan["actor_id"] for plan in active.values()}
            if sum(1 for plan in active.values() if plan["actor_id"] == actor_id) > 1
        )
        slice_record = {
            "turn": turn,
            "scenario_id": scenario["scenario_id"],
            "assignment_result_digest": assignment["result_digest"],
            "events": events,
            "active_plans": sorted(deepcopy(list(active.values())), key=lambda item: (item["priority_id"], item["actor_id"])),
            "metrics": {
                "active_plan_count": len(active),
                "double_booked_actor_count": len(double_booked),
                "start_count": sum(1 for item in events if item["event_type"] == "START"),
                "continue_count": sum(1 for item in events if item["event_type"] == "CONTINUE"),
                "cancel_count": sum(1 for item in events if item["event_type"] == "CANCEL"),
                "retire_count": sum(1 for item in events if item["event_type"] == "RETIRE"),
                "supersede_count": sum(1 for item in events if item["event_type"] == "SUPERSEDE"),
                "continuity_reset_count": sum(1 for item in events if item["event_type"] == "CONTINUITY_RESET"),
            },
        }
        slice_record["result_digest"] = digest(slice_record)
        slices.append(slice_record)
        all_events.extend(events)
        previous_turn = turn

    result = {
        "schema_version": 1,
        "contract": CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "evidence_status": "CONTROL_OFFLINE_SHADOW_TEMPORAL_COMMITMENT",
        "controlled_faction": validated[0]["controlled_faction"],
        "turns": turns,
        "engineering_windows": {
            "minimum_commitment_turns": MIN_COMMITMENT_TURNS,
            "maximum_commitment_turns_before_reassignment_review": MAX_COMMITMENT_TURNS,
            "material_reassignment_score_margin": REASSIGN_SCORE_MARGIN,
            "status": "PROJECT_OWNED_ANTI_THRASH_THRESHOLDS_NOT_EMPIRICAL_WH3_TIMING",
        },
        "schedule_slices": slices,
        "events": all_events,
        "final_active_plans": sorted(deepcopy(list(active.values())), key=lambda item: (item["priority_id"], item["actor_id"])),
        "guardrails": [
            "Commitment windows are turn-count state-machine rules, not campaign movement-time predictions.",
            "A disappearing priority is observational retirement, never causal credit for an unexecuted proposal.",
            "Turn gaps reset continuity rather than implying hidden execution or completion.",
            "Higher-severity obligations may supersede lower-severity shadow commitments; every supersession is explicit.",
            "No commitment emits a WH3 order or claims acknowledgement, execution, route feasibility, or outcome.",
        ],
    }
    result["result_digest"] = digest(result)
    return result


def semantic_commitment_metrics(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn_count": len(result["schedule_slices"]),
        "event_types": [item["event_type"] for item in result["events"]],
        "event_reasons": [item["reason"] for item in result["events"]],
        "active_counts": [item["metrics"]["active_plan_count"] for item in result["schedule_slices"]],
        "double_booked_counts": [item["metrics"]["double_booked_actor_count"] for item in result["schedule_slices"]],
        "final_active_priority_types": sorted(item["priority_type"] for item in result["final_active_plans"]),
    }

CROSS_EVIDENCE_CONTRACT = "CAMPAIGN_STRATEGIC_FORCE_ALLOCATION_CROSS_EVIDENCE_V1"


def build_cross_evidence_campaign_force_allocation(
    observed_report: dict[str, Any],
    late_game_scenario: dict[str, Any],
    challenge_envelope: dict[str, Any],
    strategic_portfolio_envelope: dict[str, Any],
) -> dict[str, Any]:
    from .strategic_assignment import build_cross_evidence_theater_to_army_assignment

    assignment_envelope = build_cross_evidence_theater_to_army_assignment(
        observed_report,
        late_game_scenario,
        challenge_envelope,
        strategic_portfolio_envelope,
    )
    observed_scenarios = [item["scenario"] for item in observed_report["turn_results"]]
    observed_schedule = build_strategic_temporal_commitment(observed_scenarios)
    result = {
        "schema_version": 1,
        "contract": CROSS_EVIDENCE_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "evidence_status": "CONTROL_OFFLINE_OVER_V0_2F_PORTFOLIO_AND_OBSERVER_SAFE_CAMPAIGN_STATE",
        "source_assignment_envelope_digest": assignment_envelope["result_digest"],
        "source_strategic_portfolio_result_digest": strategic_portfolio_envelope["result_digest"],
        "assignment_envelope": assignment_envelope,
        "observed_temporal_schedule": observed_schedule,
        "calibration_limits": [
            "Observed Reikland turns 4-7 contain only one controlled field army, so multi-army exclusivity, reserve allocation, overflow, and anti-thrashing are supported by synthetic adversarial fixtures rather than live campaign observation.",
            "The observed sequence ends on the first coherent-rival assignment, so it cannot empirically calibrate the project-owned 2/4-turn commitment windows.",
            "Geometric assignment references are not WH3 path feasibility or action authority.",
            "No order, acknowledgement, execution, causal outcome, economy, recruitment, diplomacy, or owner enjoyment claim is promoted.",
        ],
    }
    result["result_digest"] = digest(result)
    return result
