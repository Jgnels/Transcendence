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
from .strategic_portfolio import (
    AGGRESSIVE_TYPES,
    SEVERITY_RANK,
    build_strategic_theater_portfolio,
)

CONTRACT = "CAMPAIGN_THEATER_TO_ARMY_ASSIGNMENT_V1"
CROSS_EVIDENCE_CONTRACT = "CAMPAIGN_THEATER_TO_ARMY_CROSS_EVIDENCE_ASSIGNMENT_V1"
ASSIGNMENT_STATUS = "SHADOW_PROPOSED_NOT_EXECUTED"
ROUTE_STATUS = "NOT_EVALUATED_GEOMETRIC_REFERENCE_ONLY"
MAX_RANKED_CANDIDATES = 16


class StrategicAssignmentError(ValueError):
    pass


def _verified_digest(record: dict[str, Any], label: str) -> None:
    claimed = record.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise StrategicAssignmentError(f"{label} result digest missing or invalid")
    payload = dict(record)
    payload.pop("result_digest", None)
    if digest(payload) != claimed:
        raise StrategicAssignmentError(f"{label} result digest mismatch")


def _at_war(wars: list[list[str]], a: str, b: str) -> bool:
    return [a, b] in wars or [b, a] in wars


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def _own_armies(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    observer = scenario["controlled_faction"]
    visible = visible_scenario(scenario, observer)
    result = []
    for army in visible["armies"]:
        if army["faction"] != observer:
            continue
        observation = army.get("observation")
        if isinstance(observation, dict) and observation.get("planner_eligible") is False:
            continue
        result.append(deepcopy(army))
    return sorted(result, key=lambda item: item["id"])


def _priority_map(portfolio: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in portfolio["candidate_priorities"]:
        result[item["portfolio_id"]] = item
    return result


def _effective_priorities(portfolio: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = _priority_map(portfolio)
    effective: list[dict[str, Any]] = []
    for selected in portfolio["selected_priorities"]:
        if selected["priority_type"] != "CRITICAL_STRATEGIC_OVERFLOW":
            item = deepcopy(selected)
            item["via_critical_overflow"] = False
            effective.append(item)
            continue
        source_ids = selected["evidence"].get("source_portfolio_ids", [])
        for source_id in source_ids:
            source = by_id.get(source_id)
            if source is None or source.get("severity") != "CRITICAL":
                raise StrategicAssignmentError("critical overflow references missing/noncritical source")
            item = deepcopy(source)
            item["via_critical_overflow"] = True
            effective.append(item)
    effective.sort(
        key=lambda item: (
            -SEVERITY_RANK[item["severity"]],
            -int(round(float(item["utility"]) * 1_000_000)),
            item["priority_type"],
            str(item.get("target_id") or ""),
            item["portfolio_id"],
        )
    )
    return effective


def _anchor_for_priority(
    scenario: dict[str, Any], challenge: dict[str, Any], priority: dict[str, Any]
) -> dict[str, Any] | None:
    target_kind = priority.get("target_kind")
    target_id = priority.get("target_id")
    if target_kind == "REGION" and target_id:
        region = next((item for item in scenario["regions"] if item["id"] == target_id), None)
        if region is None:
            raise StrategicAssignmentError(f"priority target region absent from scenario: {target_id}")
        return {"x": round(float(region["x"]), 6), "y": round(float(region["y"]), 6), "source": "OBSERVED_REGION_POINT"}

    observer = scenario["controlled_faction"]
    visible = visible_scenario(scenario, observer)
    assets: list[dict[str, float]] = []
    if target_kind == "FACTION" and target_id:
        for army in visible["armies"]:
            if army["faction"] == target_id and _at_war(visible["wars"], observer, target_id):
                assets.append({"x": float(army["x"]), "y": float(army["y"])})
        for region in visible["regions"]:
            if region["owner"] == target_id and _at_war(visible["wars"], observer, target_id):
                assets.append({"x": float(region["x"]), "y": float(region["y"])})
    elif priority["scope"] == "RIVAL_SET":
        hostile_factions = {
            b if a == observer else a
            for a, b in visible["wars"]
            if a == observer or b == observer
        }
        for army in visible["armies"]:
            if army["faction"] in hostile_factions:
                assets.append({"x": float(army["x"]), "y": float(army["y"])})
        for region in visible["regions"]:
            if region["owner"] in hostile_factions:
                assets.append({"x": float(region["x"]), "y": float(region["y"])})
    if not assets:
        return None
    return {
        "x": round(sum(item["x"] for item in assets) / len(assets), 6),
        "y": round(sum(item["y"] for item in assets) / len(assets), 6),
        "source": "OBSERVER_SAFE_VISIBLE_ASSET_CENTROID",
    }


def _front_coverage_ids(challenge: dict[str, Any], priority: dict[str, Any]) -> set[str]:
    if priority.get("target_kind") != "REGION" or not priority.get("target_id"):
        return set()
    front = next((item for item in challenge["fronts"] if item["region_id"] == priority["target_id"]), None)
    if front is None:
        return set()
    return {item["army_id"] for item in front["nearby_controlled_armies"]}


def _candidate_record(
    army: dict[str, Any],
    priority: dict[str, Any],
    anchor: dict[str, Any] | None,
    max_strength: float,
    coverage_ids: set[str],
) -> dict[str, Any]:
    recovering = float(army["replenishment"]) < RECOVERY_REPLENISHMENT_THRESHOLD
    critical = priority["severity"] == "CRITICAL"
    if recovering and not critical:
        return {
            "actor_id": army["id"],
            "eligible": False,
            "blocked_reason": "RECOVERY_PROTECTED",
            "recovering": True,
        }
    eta = None
    proximity = 0.5
    if anchor is not None:
        eta = _distance(army, anchor) / max(float(army["movement"]), 1.0)
        proximity = 1.0 / (1.0 + eta)
    strength_norm = 0.0 if max_strength <= 0 else float(army["strength"]) / max_strength
    coverage_bonus = 1.0 if army["id"] in coverage_ids else 0.0
    recovery_penalty = 0.35 if recovering else 0.0
    score = (
        0.50 * proximity
        + 0.25 * float(army["replenishment"])
        + 0.20 * strength_norm
        + 0.05 * coverage_bonus
        - recovery_penalty
    )
    return {
        "actor_id": army["id"],
        "eligible": True,
        "blocked_reason": None,
        "recovering": recovering,
        "recovery_override": bool(recovering and critical),
        "geometric_eta_turns_reference": None if eta is None else round(eta, 6),
        "existing_front_coverage": coverage_bonus == 1.0,
        "assignment_score": round(score, 6),
    }


def _rank_candidates(
    armies: list[dict[str, Any]],
    priority: dict[str, Any],
    anchor: dict[str, Any] | None,
    coverage_ids: set[str],
) -> list[dict[str, Any]]:
    max_strength = max((float(item["strength"]) for item in armies), default=0.0)
    records = [_candidate_record(item, priority, anchor, max_strength, coverage_ids) for item in armies]
    records.sort(
        key=lambda item: (
            0 if item.get("eligible") else 1,
            -int(round(float(item.get("assignment_score", -9999.0)) * 1_000_000)),
            item["actor_id"],
        )
    )
    return records


def _is_force_priority(priority: dict[str, Any]) -> bool:
    return priority["priority_type"] not in {
        "PROTECT_RECOVERING_FIELD_FORCE",
        "CONSOLIDATE_LOW_PRESSURE_POSITION",
        "CRITICAL_STRATEGIC_OVERFLOW",
    }


def _assignment_record(
    priority: dict[str, Any],
    actor: dict[str, Any],
    candidate: dict[str, Any],
    anchor: dict[str, Any] | None,
    assignment_kind: str,
) -> dict[str, Any]:
    record = {
        "priority_id": priority["portfolio_id"],
        "priority_type": priority["priority_type"],
        "severity": priority["severity"],
        "target_kind": priority.get("target_kind"),
        "target_id": priority.get("target_id"),
        "via_critical_overflow": bool(priority.get("via_critical_overflow")),
        "actor_id": actor["id"],
        "assignment_kind": assignment_kind,
        "assignment_score": candidate.get("assignment_score"),
        "geometric_eta_turns_reference": candidate.get("geometric_eta_turns_reference"),
        "reference_anchor": deepcopy(anchor),
        "recovery_override": bool(candidate.get("recovery_override", False)),
        "assignment_status": ASSIGNMENT_STATUS,
        "route_status": ROUTE_STATUS,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
    }
    record["assignment_id"] = digest(
        {
            "priority_id": record["priority_id"],
            "actor_id": record["actor_id"],
            "assignment_kind": record["assignment_kind"],
        }
    )
    record["result_digest"] = digest(record)
    return record


def _verify_inputs(
    scenario: dict[str, Any],
    challenge: dict[str, Any] | None,
    portfolio: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    expected_challenge = evaluate_campaign_snapshot(scenario)
    if challenge is not None and challenge != expected_challenge:
        raise StrategicAssignmentError("challenge envelope is stale, forged, or foreign")
    expected_portfolio = build_strategic_theater_portfolio(scenario, expected_challenge)
    if portfolio is not None and portfolio != expected_portfolio:
        raise StrategicAssignmentError("strategic portfolio is stale, forged, or foreign")
    _verified_digest(expected_challenge, "campaign challenge")
    _verified_digest(expected_portfolio, "strategic portfolio")
    if expected_portfolio.get("authority") != AUTHORITY or expected_portfolio.get("application_authority") != APPLICATION_AUTHORITY:
        raise StrategicAssignmentError("strategic portfolio crosses authority boundary")
    return expected_challenge, expected_portfolio


def build_theater_to_army_assignment(
    raw_scenario: dict[str, Any],
    challenge_envelope: dict[str, Any] | None = None,
    strategic_portfolio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scenario = validate_campaign_scenario(raw_scenario)
    challenge, portfolio = _verify_inputs(scenario, challenge_envelope, strategic_portfolio)
    armies = _own_armies(scenario)
    by_army = {item["id"]: item for item in armies}
    recovering_ids = {
        item["id"] for item in armies
        if float(item["replenishment"]) < RECOVERY_REPLENISHMENT_THRESHOLD
    }
    healthy_ids = {item["id"] for item in armies} - recovering_ids
    effective = _effective_priorities(portfolio)

    assignments: list[dict[str, Any]] = []
    unfilled: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    recovery_protections: list[dict[str, Any]] = []
    claimed: dict[str, str] = {}
    rankings: dict[str, list[dict[str, Any]]] = {}

    recovery_priority = next((item for item in effective if item["priority_type"] == "PROTECT_RECOVERING_FIELD_FORCE"), None)
    if recovery_priority is not None:
        for army_id in sorted(recovering_ids):
            record = {
                "priority_id": recovery_priority["portfolio_id"],
                "actor_id": army_id,
                "protection_status": "RECOVERY_CAPACITY_PROTECTED",
                "exclusive_resource": "ARMY_STRATEGIC_COMMITMENT_SLOT",
                "authority": AUTHORITY,
                "application_authority": APPLICATION_AUTHORITY,
            }
            record["result_digest"] = digest(record)
            recovery_protections.append(record)
            claimed[army_id] = recovery_priority["portfolio_id"]

    reserve_priority = next((item for item in effective if item["priority_type"] == "PRESERVE_STRATEGIC_RESERVE"), None)
    force_priorities = [item for item in effective if _is_force_priority(item) and item["priority_type"] != "PRESERVE_STRATEGIC_RESERVE"]

    for priority in force_priorities:
        if priority["priority_type"] in AGGRESSIVE_TYPES and not portfolio["portfolio_constraints"]["aggressive_commitment_allowed"]:
            unfilled.append({
                "priority_id": priority["portfolio_id"],
                "priority_type": priority["priority_type"],
                "severity": priority["severity"],
                "status": "UNFILLED",
                "reason": "AGGRESSIVE_COMMITMENT_VETO",
                "via_critical_overflow": bool(priority.get("via_critical_overflow")),
            })
            continue
        anchor = _anchor_for_priority(scenario, challenge, priority)
        coverage_ids = _front_coverage_ids(challenge, priority)
        ranked = _rank_candidates(armies, priority, anchor, coverage_ids)
        rankings[priority["portfolio_id"]] = deepcopy(ranked[:MAX_RANKED_CANDIDATES])
        eligible = [item for item in ranked if item.get("eligible")]
        available = [
            item for item in eligible
            if item["actor_id"] not in claimed
            or (
                priority["severity"] == "CRITICAL"
                and recovery_priority is not None
                and claimed.get(item["actor_id"]) == recovery_priority["portfolio_id"]
            )
        ]

        # Preserve one healthy strategic reserve for noncritical work whenever the portfolio asks for it.
        reserve_floor_blocked: list[str] = []
        if reserve_priority is not None and priority["severity"] != "CRITICAL":
            healthy_unclaimed = [army_id for army_id in healthy_ids if army_id not in claimed]
            if len(healthy_unclaimed) <= 1:
                reserve_floor_blocked = [item["actor_id"] for item in available if item["actor_id"] in healthy_ids]
                available = [item for item in available if item["actor_id"] not in reserve_floor_blocked]

        if not available:
            reasons: list[str] = []
            if any(item.get("blocked_reason") == "RECOVERY_PROTECTED" for item in ranked):
                reasons.append("RECOVERY_PROTECTED")
            if reserve_floor_blocked:
                reasons.append("RESERVE_FLOOR_PROTECTED")
            occupied = [item["actor_id"] for item in eligible if item["actor_id"] in claimed]
            if occupied:
                reasons.append("ARMY_SLOT_ALREADY_CLAIMED")
            reason = "+".join(reasons) if reasons else "NO_ELIGIBLE_CONTROLLED_ARMY"
            unfilled.append({
                "priority_id": priority["portfolio_id"],
                "priority_type": priority["priority_type"],
                "severity": priority["severity"],
                "status": "UNFILLED",
                "reason": reason,
                "via_critical_overflow": bool(priority.get("via_critical_overflow")),
            })
            if occupied or reserve_floor_blocked:
                conflicts.append({
                    "priority_id": priority["portfolio_id"],
                    "reason": reason,
                    "occupied_actor_ids": sorted(occupied),
                    "reserve_floor_actor_ids": sorted(reserve_floor_blocked),
                })
            continue

        chosen = available[0]
        actor = by_army[chosen["actor_id"]]
        if (
            priority["severity"] == "CRITICAL"
            and recovery_priority is not None
            and claimed.get(actor["id"]) == recovery_priority["portfolio_id"]
        ):
            for protection in recovery_protections:
                if protection["actor_id"] == actor["id"]:
                    protection["protection_status"] = "RECOVERY_PROTECTION_OVERRIDDEN_BY_CRITICAL"
                    protection.pop("result_digest", None)
                    protection["result_digest"] = digest(protection)
                    break
            claimed.pop(actor["id"], None)
            chosen["recovery_override"] = True
        record = _assignment_record(priority, actor, chosen, anchor, "THEATER_PRIORITY")
        assignments.append(record)
        claimed[actor["id"]] = priority["portfolio_id"]

    reserve_record = None
    if reserve_priority is not None:
        candidates = [
            item for item in armies
            if item["id"] not in claimed and item["id"] in healthy_ids
        ]
        candidates.sort(key=lambda item: (-float(item["strength"]), -float(item["replenishment"]), item["id"]))
        if candidates:
            actor = candidates[0]
            candidate = {
                "assignment_score": round(float(actor["replenishment"]) + float(actor["strength"]) / max(1.0, max(float(a["strength"]) for a in armies)), 6),
                "geometric_eta_turns_reference": None,
                "recovery_override": False,
            }
            reserve_record = _assignment_record(reserve_priority, actor, candidate, None, "STRATEGIC_RESERVE")
            assignments.append(reserve_record)
            claimed[actor["id"]] = reserve_priority["portfolio_id"]
        else:
            unfilled.append({
                "priority_id": reserve_priority["portfolio_id"],
                "priority_type": reserve_priority["priority_type"],
                "severity": reserve_priority["severity"],
                "status": "UNFILLED",
                "reason": "NO_UNCLAIMED_HEALTHY_ARMY_FOR_RESERVE",
                "via_critical_overflow": bool(reserve_priority.get("via_critical_overflow")),
            })

    consolidation = [item for item in effective if item["priority_type"] == "CONSOLIDATE_LOW_PRESSURE_POSITION"]
    for item in consolidation:
        unfilled.append({
            "priority_id": item["portfolio_id"],
            "priority_type": item["priority_type"],
            "severity": item["severity"],
            "status": "NO_FORCE_REQUIRED",
            "reason": "STRATEGIC_POSTURE_ONLY",
            "via_critical_overflow": bool(item.get("via_critical_overflow")),
        })

    critical_effective = [item for item in effective if item["severity"] == "CRITICAL" and item["priority_type"] != "PROTECT_RECOVERING_FIELD_FORCE"]
    assigned_priority_ids = {item["priority_id"] for item in assignments}
    critical_assigned = sum(1 for item in critical_effective if item["portfolio_id"] in assigned_priority_ids)
    critical_coverage = 1.0 if not critical_effective else round(critical_assigned / len(critical_effective), 6)

    double_booked = sorted({army_id for army_id in claimed if sum(1 for item in assignments if item["actor_id"] == army_id) > 1})
    result = {
        "schema_version": 1,
        "contract": CONTRACT,
        "scenario_id": scenario["scenario_id"],
        "turn": scenario["turn"],
        "controlled_faction": scenario["controlled_faction"],
        "scenario_digest": digest(scenario),
        "challenge_result_digest": challenge["result_digest"],
        "strategic_portfolio_result_digest": portfolio["result_digest"],
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "evidence_status": "CONTROL_OFFLINE_SHADOW_FORCE_ALLOCATION",
        "assignment_constraints": {
            "actor_resource": "ARMY_STRATEGIC_COMMITMENT_SLOT",
            "actor_exclusivity": "ONE_PRIORITY_OR_PROTECTION_PER_ARMY",
            "recovering_armies_protected_from_noncritical_assignment": True,
            "critical_recovery_override": "ALLOWED_WITH_EXPLICIT_FLAG",
            "reserve_floor": "ONE_HEALTHY_UNCLAIMED_ARMY_WHEN_POSSIBLE_FOR_NONCRITICAL_WORK",
            "overflow_sources_expanded_for_assignment": True,
            "assignment_solver": "DETERMINISTIC_SEVERITY_FIRST_GREEDY_NOT_OPTIMALITY_CLAIM",
            "route_status": ROUTE_STATUS,
            "orders_emitted": False,
        },
        "effective_priorities": [
            {
                "priority_id": item["portfolio_id"],
                "priority_type": item["priority_type"],
                "severity": item["severity"],
                "target_kind": item.get("target_kind"),
                "target_id": item.get("target_id"),
                "via_critical_overflow": bool(item.get("via_critical_overflow")),
            }
            for item in effective
        ],
        "actor_inventory": {
            "eligible_controlled_army_ids": [item["id"] for item in armies],
            "recovering_army_ids": sorted(recovering_ids),
            "healthy_army_ids": sorted(healthy_ids),
        },
        "recovery_protections": recovery_protections,
        "assignments": assignments,
        "unfilled_priorities": unfilled,
        "resource_conflicts": conflicts,
        "candidate_rankings": rankings,
        "metrics": {
            "eligible_controlled_army_count": len(armies),
            "recovering_army_count": len(recovering_ids),
            "recovery_protection_count": len(recovery_protections),
            "recovery_override_count": sum(1 for item in assignments if item.get("recovery_override")),
            "effective_priority_count": len(effective),
            "assignment_count": len(assignments),
            "unfilled_priority_count": len(unfilled),
            "resource_conflict_count": len(conflicts),
            "critical_force_priority_count": len(critical_effective),
            "critical_force_assignment_coverage": critical_coverage,
            "double_booked_actor_count": len(double_booked),
            "reserve_actor_id": None if reserve_record is None else reserve_record["actor_id"],
        },
        "guardrails": [
            "Geometric distance and movement are assignment references only; no campaign path feasibility is claimed.",
            "Recovering armies are protected from noncritical commitments; critical emergency use is explicit and remains unexecuted.",
            "A strategic reserve is an abstract capacity reservation, not a destination or stance order.",
            "Critical overflow is expanded back to exact source priorities so bounded portfolio representation cannot erase assignment conflicts.",
            "Assignments are shadow proposals only and establish neither issue, acknowledgement, execution, nor outcome.",
        ],
    }
    result["result_digest"] = digest(result)
    return result


def build_cross_evidence_theater_to_army_assignment(
    observed_report: dict[str, Any],
    late_game_scenario: dict[str, Any],
    challenge_envelope: dict[str, Any],
    strategic_portfolio_envelope: dict[str, Any],
) -> dict[str, Any]:
    from .campaign_challenge import build_campaign_challenge_envelope
    from .strategic_portfolio import build_cross_evidence_strategic_theater_portfolio

    expected_challenge = build_campaign_challenge_envelope(observed_report, late_game_scenario)
    if challenge_envelope != expected_challenge:
        raise StrategicAssignmentError("v0.2E challenge envelope does not match exact sources")
    expected_portfolio = build_cross_evidence_strategic_theater_portfolio(
        observed_report, late_game_scenario, challenge_envelope
    )
    if strategic_portfolio_envelope != expected_portfolio:
        raise StrategicAssignmentError("v0.2F strategic portfolio envelope does not match exact sources")

    observed_assignments = []
    for turn_item, challenge_turn, portfolio_turn in zip(
        observed_report["turn_results"],
        challenge_envelope["observed_turns"],
        strategic_portfolio_envelope["observed_turns"],
        strict=True,
    ):
        observed_assignments.append(
            build_theater_to_army_assignment(turn_item["scenario"], challenge_turn, portfolio_turn)
        )
    late_assignment = build_theater_to_army_assignment(
        late_game_scenario,
        challenge_envelope["synthetic_late_game_reference"],
        strategic_portfolio_envelope["synthetic_late_game_reference"],
    )
    result = {
        "schema_version": 1,
        "contract": CROSS_EVIDENCE_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "evidence_status": "CONTROL_OFFLINE_OVER_V0_2F_STRATEGIC_PORTFOLIO",
        "source_challenge_result_digest": challenge_envelope["result_digest"],
        "source_strategic_portfolio_result_digest": strategic_portfolio_envelope["result_digest"],
        "observed_assignments": observed_assignments,
        "synthetic_late_game_assignment": late_assignment,
        "generalization_limits": [
            "Observed campaign calibration still contains only one controlled Reikland field army on turns 4-7, so multi-army allocation behavior is synthetic.",
            "Straight-line geometry is not campaign pathfinding, stance legality, zone-of-control legality, or movement reachability.",
            "No economy, recruitment, diplomacy, native CAI intent, acknowledgement, execution, or causal outcome is inferred.",
        ],
    }
    result["result_digest"] = digest(result)
    return result


def semantic_assignment_metrics(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "assignment_priority_types": sorted(item["priority_type"] for item in result["assignments"]),
        "assignment_kinds": sorted(item["assignment_kind"] for item in result["assignments"]),
        "unfilled": [list(item) for item in sorted((entry["priority_type"], entry["reason"]) for entry in result["unfilled_priorities"])],
        "recovery_protection_count": result["metrics"]["recovery_protection_count"],
        "critical_force_assignment_coverage": result["metrics"]["critical_force_assignment_coverage"],
        "double_booked_actor_count": result["metrics"]["double_booked_actor_count"],
        "reserve_present": result["metrics"]["reserve_actor_id"] is not None,
    }
