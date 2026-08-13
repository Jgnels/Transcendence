from __future__ import annotations

import math
from functools import lru_cache
from typing import Any

from .battle_shadow import SEVERITY_RANK, collect_tactical_opportunity_candidates
from .canonical import digest
from .tactical_portfolio import (
    PORTFOLIO_CONTRACT,
    build_tactical_priority_portfolio,
    build_trace_priority_portfolios,
)
from .tactical_state import build_tactical_state_trajectory


ASSIGNMENT_CONTRACT = "TACTICAL_OBJECTIVE_ASSIGNMENT_V1"
TRAJECTORY_CONTRACT = "TACTICAL_OBJECTIVE_ASSIGNMENT_TRAJECTORY_V1"

_SELF_ACTION_PRECEDENCE = {
    "COMMANDER_EXTRACTION_WINDOW": (60, "EXTRACT_COMMANDER"),
    "ARTILLERY_EVACUATION_WINDOW": (55, "EVACUATE_ARTILLERY"),
    "CAVALRY_DISENGAGEMENT_WINDOW": (50, "DISENGAGE_CAVALRY"),
    "RANGED_REPOSITION_WINDOW": (45, "REPOSITION_RANGED"),
    "PURSUIT_TERMINATION_WINDOW": (40, "TERMINATE_PURSUIT"),
    "REFORM_AND_PRESERVE_WINDOW": (35, "REFORM_AND_PRESERVE"),
}

_SUPPORT_ACTIONS = {
    "FRONTLINE_RELIEF_WINDOW": "RELIEVE_FRONTLINE",
    "LOCAL_ROUT_CONTAINMENT_WINDOW": "CONTAIN_LOCAL_ROUT",
    "RESERVE_COMMITMENT_WINDOW": "COMMIT_RESERVE",
    "SELECTIVE_PURSUIT_WINDOW": "SELECTIVE_PURSUIT",
}

_ALLOWED_ROLES = {
    "RELIEVE_FRONTLINE": {"frontline", "cavalry"},
    "CONTAIN_LOCAL_ROUT": {"frontline", "cavalry"},
    "COMMIT_RESERVE": {"frontline", "cavalry"},
    "SELECTIVE_PURSUIT": {"cavalry", "ranged"},
}


def _rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _unit_by_id(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        unit["observed"]["stable_unit_id"]: unit
        for unit in state["units"]
    }


def _position(unit: dict[str, Any]) -> tuple[float, float]:
    observed = unit["observed"]
    return float(observed["position"]["x"]), float(observed["position"]["z"])


def _centroid(units: list[dict[str, Any]]) -> dict[str, float] | None:
    if not units:
        return None
    points = [_position(unit) for unit in units]
    return {
        "x": _rounded(sum(point[0] for point in points) / len(points), 3),
        "z": _rounded(sum(point[1] for point in points) / len(points), 3),
    }


def _distance_to_anchor(unit: dict[str, Any], anchor: dict[str, float] | None) -> float | None:
    if anchor is None:
        return None
    x, z = _position(unit)
    return math.hypot(x - anchor["x"], z - anchor["z"])


def _verified_digest(record: dict[str, Any], label: str) -> None:
    claimed = record.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise ValueError(f"{label} result digest is missing or invalid")
    payload = dict(record)
    payload.pop("result_digest", None)
    if digest(payload) != claimed:
        raise ValueError(f"{label} result digest mismatch")


def _source_candidates_for_portfolio(
    state: dict[str, Any], portfolio: dict[str, Any]
) -> list[dict[str, Any]]:
    _verified_digest(state, "tactical state")
    _verified_digest(portfolio, "tactical portfolio")
    if state.get("state_contract") != "TACTICAL_STATE_VISIBILITY_SAFE_V2":
        raise ValueError("unsupported tactical state contract")
    if state.get("authority") != "NO_ORDERS":
        raise ValueError("assignment input state must retain NO_ORDERS authority")
    if portfolio.get("portfolio_contract") != PORTFOLIO_CONTRACT:
        raise ValueError("unsupported tactical portfolio contract")
    if portfolio.get("source_tactical_state_digest") != state.get("result_digest"):
        raise ValueError("portfolio source tactical-state digest mismatch")
    if portfolio.get("authority") != "NO_ORDERS":
        raise ValueError("assignment input portfolio must retain NO_ORDERS authority")
    priorities = portfolio.get("selected_priorities")
    if not isinstance(priorities, list):
        raise ValueError("portfolio selected_priorities must be a list")
    if portfolio.get("selected_priority_count") != len(priorities):
        raise ValueError("portfolio selected-priority count mismatch")
    maximum = portfolio.get("maximum_selected_priorities")
    if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 0:
        raise ValueError("portfolio maximum-selected-priorities is invalid")
    if len(priorities) > maximum:
        raise ValueError("portfolio exceeds its selected-priority limit")

    selected_ids: set[str] = set()
    for priority in priorities:
        if not isinstance(priority, dict):
            raise ValueError("portfolio priority must be an object")
        _verified_digest(priority, "tactical portfolio priority")
        if priority.get("authority") != "ADVISORY_ONLY":
            raise ValueError("portfolio priority must remain ADVISORY_ONLY")
        source_ids = priority.get("source_opportunity_ids")
        if not isinstance(source_ids, list) or not source_ids or any(
            not isinstance(source_id, str) or not source_id for source_id in source_ids
        ):
            raise ValueError("portfolio priority source IDs must be a nonempty string list")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("portfolio priority source IDs must be unique")
        selected_ids.update(source_ids)

    canonical = build_tactical_priority_portfolio(state)
    canonical_ids = {
        source_id
        for priority in canonical["selected_priorities"]
        for source_id in priority["source_opportunity_ids"]
    }
    if selected_ids != canonical_ids:
        raise ValueError("portfolio source opportunity set differs from canonical portfolio")

    available = {
        candidate["opportunity_id"]: candidate
        for candidate in collect_tactical_opportunity_candidates(state)
    }
    missing = sorted(selected_ids - available.keys())
    if missing:
        raise ValueError(f"portfolio references unavailable source opportunities: {missing}")
    return [available[source_id] for source_id in sorted(selected_ids)]


def _severity_max(items: list[dict[str, Any]]) -> str:
    return max(items, key=lambda item: SEVERITY_RANK[item["severity"]])["severity"]


def _objective_record(
    objective_id: str,
    objective_type: str,
    source_items: list[dict[str, Any]],
    subject_unit_ids: list[str],
    anchor: dict[str, float] | None,
    actor_pool_mode: str,
    actor_pool_ids: list[str] | None = None,
    preferred_actor_pool_ids: list[str] | None = None,
) -> dict[str, Any]:
    record = {
        "objective_id": objective_id,
        "objective_type": objective_type,
        "source_opportunity_ids": sorted(item["opportunity_id"] for item in source_items),
        "source_opportunity_keys": sorted(item["opportunity_key"] for item in source_items),
        "source_opportunity_types": sorted({item["opportunity_type"] for item in source_items}),
        "subject_unit_ids": sorted(set(subject_unit_ids)),
        "severity": _severity_max(source_items),
        "objective_utility": max(item["utility_score"] for item in source_items),
        "objective_anchor": anchor,
        "actor_pool_mode": actor_pool_mode,
        "actor_pool_ids": sorted(set(actor_pool_ids or [])),
        "preferred_actor_pool_ids": sorted(set(preferred_actor_pool_ids or [])),
        "required_actor_count": 1,
        "exclusive_resource": "UNIT_ACTION_SLOT",
        "counterfactual_status": "UNVERIFIED",
        "authority": "ADVISORY_ONLY",
    }
    return record


def _build_objectives(
    state: dict[str, Any], source_items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    units = _unit_by_id(state)
    objectives: list[dict[str, Any]] = []

    self_by_subject: dict[str, list[dict[str, Any]]] = {}
    for item in source_items:
        if item["opportunity_type"] not in _SELF_ACTION_PRECEDENCE:
            continue
        for subject_id in item["subject_unit_ids"]:
            self_by_subject.setdefault(subject_id, []).append(item)
    for subject_id, items in sorted(self_by_subject.items()):
        dominant = max(
            items,
            key=lambda item: (
                _SELF_ACTION_PRECEDENCE[item["opportunity_type"]][0],
                SEVERITY_RANK[item["severity"]],
                item["utility_score"],
                item["opportunity_id"],
            ),
        )
        action = _SELF_ACTION_PRECEDENCE[dominant["opportunity_type"]][1]
        subject = units.get(subject_id)
        objectives.append(
            _objective_record(
                f"SELF:{subject_id}",
                action,
                items,
                [subject_id],
                _centroid([subject] if subject else []),
                "EXACT_SUBJECT",
                [subject_id],
            )
        )

    relief_by_subject: dict[str, list[dict[str, Any]]] = {}
    containment_items: list[dict[str, Any]] = []
    reserve_items: list[dict[str, Any]] = []
    pursuit_items: list[dict[str, Any]] = []
    for item in source_items:
        opportunity_type = item["opportunity_type"]
        if opportunity_type == "FRONTLINE_RELIEF_WINDOW":
            for subject_id in item["subject_unit_ids"]:
                relief_by_subject.setdefault(subject_id, []).append(item)
        elif opportunity_type == "LOCAL_ROUT_CONTAINMENT_WINDOW":
            containment_items.append(item)
        elif opportunity_type == "RESERVE_COMMITMENT_WINDOW":
            reserve_items.append(item)
        elif opportunity_type == "SELECTIVE_PURSUIT_WINDOW":
            pursuit_items.append(item)

    containment_subjects = {
        subject_id
        for item in containment_items
        for subject_id in item["subject_unit_ids"]
    }
    reserve_pool = sorted(
        {
            subject_id
            for item in reserve_items
            for subject_id in item["subject_unit_ids"]
        }
    )
    crisis_objective_created = False
    for subject_id, relief_items in sorted(relief_by_subject.items()):
        merged_sources = list(relief_items)
        if subject_id in containment_subjects:
            merged_sources.extend(containment_items)
        merged_sources.extend(reserve_items)
        merged_sources = list({item["opportunity_id"]: item for item in merged_sources}.values())
        subject = units.get(subject_id)
        objectives.append(
            _objective_record(
                f"RELIEVE:{subject_id}",
                "RELIEVE_FRONTLINE",
                merged_sources,
                [subject_id],
                _centroid([subject] if subject else []),
                "ELIGIBLE_LOCAL_SUPPORT",
                preferred_actor_pool_ids=reserve_pool,
            )
        )
        crisis_objective_created = True

    remaining_containment = sorted(containment_subjects - set(relief_by_subject))
    if containment_items and remaining_containment:
        subjects = [units[item_id] for item_id in remaining_containment if item_id in units]
        merged_sources = containment_items + reserve_items
        merged_sources = list({item["opportunity_id"]: item for item in merged_sources}.values())
        objectives.append(
            _objective_record(
                "CONTAIN_LOCAL_ROUT:BATTLE",
                "CONTAIN_LOCAL_ROUT",
                merged_sources,
                remaining_containment,
                _centroid(subjects),
                "ELIGIBLE_LOCAL_SUPPORT",
                preferred_actor_pool_ids=reserve_pool,
            )
        )
        crisis_objective_created = True

    if reserve_items and not crisis_objective_created:
        endangered = [
            unit
            for unit in units.values()
            if unit["observed"]["local_alliance"]
            and (
                unit["derived"]["danger_score"] >= 0.45
                or unit["observed"]["routing"]
                or unit["observed"]["wavering"]
            )
        ]
        objectives.append(
            _objective_record(
                "COMMIT_RESERVE:BATTLE",
                "COMMIT_RESERVE",
                reserve_items,
                [],
                _centroid(endangered),
                "SOURCE_SUBJECT_POOL",
                reserve_pool,
                preferred_actor_pool_ids=reserve_pool,
            )
        )

    if pursuit_items:
        actor_pool = sorted(
            {
                subject_id
                for item in pursuit_items
                for subject_id in item["subject_unit_ids"]
            }
        )
        coherent_enemy = [
            unit
            for unit in units.values()
            if not unit["observed"]["local_alliance"]
            and not unit["observed"]["routing"]
            and not unit["observed"]["shattered"]
        ]
        objectives.append(
            _objective_record(
                "SELECTIVE_PURSUIT:BATTLE",
                "SELECTIVE_PURSUIT",
                pursuit_items,
                [],
                _centroid(coherent_enemy),
                "SOURCE_SUBJECT_POOL",
                actor_pool,
                preferred_actor_pool_ids=actor_pool,
            )
        )

    unique: dict[str, dict[str, Any]] = {}
    for objective in objectives:
        existing = unique.get(objective["objective_id"])
        if existing is not None and existing != objective:
            raise ValueError(f"conflicting objective identity: {objective['objective_id']}")
        unique[objective["objective_id"]] = objective
    return sorted(
        unique.values(),
        key=lambda objective: (
            -SEVERITY_RANK[objective["severity"]],
            -objective["objective_utility"],
            objective["objective_id"],
        ),
    )


def _availability_rejection(unit: dict[str, Any]) -> str | None:
    observed = unit["observed"]
    if not observed["local_alliance"]:
        return "FOREIGN_UNIT"
    if observed["routing"]:
        return "ROUTING"
    if observed["shattered"]:
        return "SHATTERED"
    if observed["leaving"]:
        return "LEAVING_BATTLE"
    if observed["rampaging"]:
        return "RAMPAGING"
    return None


def _candidate_score(
    objective: dict[str, Any], unit: dict[str, Any], distance_m: float | None
) -> float:
    derived = unit["derived"]
    observed = unit["observed"]
    role = observed["role"]
    role_score = {
        "RELIEVE_FRONTLINE": {"frontline": 1.0, "cavalry": 0.82},
        "CONTAIN_LOCAL_ROUT": {"frontline": 1.0, "cavalry": 0.78},
        "COMMIT_RESERVE": {"frontline": 0.95, "cavalry": 0.90},
        "SELECTIVE_PURSUIT": {"cavalry": 1.0, "ranged": 0.72},
    }.get(objective["objective_type"], {}).get(role, 1.0)
    distance_score = 0.5 if distance_m is None else max(0.0, 1.0 - min(distance_m, 240.0) / 240.0)
    score = (
        0.26 * (1.0 - derived["danger_score"])
        + 0.22 * derived["withdrawal_recoverability_proxy"]
        + 0.18 * derived["marginal_engagement_value_proxy"]
        + 0.14 * (1.0 - derived["fatigue_severity"])
        + 0.12 * role_score
        + 0.08 * distance_score
    )
    if actor_id := observed.get("stable_unit_id"):
        if actor_id in objective.get("preferred_actor_pool_ids", []):
            score += 0.08
    if observed["idle"]:
        score += 0.05
    if observed["in_melee"] and objective["objective_type"] != "SELECTIVE_PURSUIT":
        score -= 0.12
    return max(0.0, min(1.0, score))


def _evaluate_actor(
    objective: dict[str, Any],
    unit: dict[str, Any],
    protected_subjects: set[str],
) -> tuple[dict[str, Any] | None, str | None]:
    observed = unit["observed"]
    actor_id = observed["stable_unit_id"]
    rejection = _availability_rejection(unit)
    if rejection:
        return None, rejection

    mode = objective["actor_pool_mode"]
    if mode == "EXACT_SUBJECT":
        if actor_id not in objective["actor_pool_ids"]:
            return None, "NOT_EXACT_SUBJECT"
    else:
        if actor_id in protected_subjects:
            return None, "PROTECTED_SUBJECT"
        if actor_id in objective["subject_unit_ids"]:
            return None, "OBJECTIVE_SUBJECT"
        if observed["role"] not in _ALLOWED_ROLES[objective["objective_type"]]:
            return None, "ROLE_INCOMPATIBLE"
        if mode == "SOURCE_SUBJECT_POOL" and actor_id not in objective["actor_pool_ids"]:
            return None, "OUTSIDE_SOURCE_ACTOR_POOL"
        if unit["derived"]["danger_score"] >= 0.55:
            return None, "ACTOR_TOO_ENDANGERED"
        if unit["derived"]["withdrawal_recoverability_proxy"] < 0.35:
            return None, "ACTOR_LOW_RECOVERABILITY"
        if objective["objective_type"] == "SELECTIVE_PURSUIT" and unit["derived"]["fatigue_severity"] >= 0.75:
            return None, "ACTOR_TOO_FATIGUED"

    distance_m = _distance_to_anchor(unit, objective["objective_anchor"])
    score = _candidate_score(objective, unit, distance_m)
    candidate = {
        "actor_unit_id": actor_id,
        "actor_role": observed["role"],
        "assignment_score": _rounded(score),
        "straight_line_distance_m": None if distance_m is None else _rounded(distance_m, 3),
        "danger_score": derived_value(unit, "danger_score"),
        "withdrawal_recoverability_proxy": derived_value(unit, "withdrawal_recoverability_proxy"),
        "fatigue_severity": derived_value(unit, "fatigue_severity"),
    }
    return candidate, None


def derived_value(unit: dict[str, Any], key: str) -> float:
    return _rounded(unit["derived"][key])


def _attach_candidates(
    objectives: list[dict[str, Any]], state: dict[str, Any]
) -> list[dict[str, Any]]:
    local_units = sorted(
        (unit for unit in state["units"] if unit["observed"]["local_alliance"]),
        key=lambda unit: unit["observed"]["stable_unit_id"],
    )
    protected_subjects = {
        subject_id
        for objective in objectives
        if objective["objective_type"] not in {"COMMIT_RESERVE", "SELECTIVE_PURSUIT"}
        for subject_id in objective["subject_unit_ids"]
    }
    results: list[dict[str, Any]] = []
    for objective in objectives:
        candidates: list[dict[str, Any]] = []
        rejections: dict[str, int] = {}
        for unit in local_units:
            candidate, rejection = _evaluate_actor(objective, unit, protected_subjects)
            if candidate is not None:
                candidates.append(candidate)
            else:
                rejections[rejection or "UNKNOWN"] = rejections.get(rejection or "UNKNOWN", 0) + 1
        result = dict(objective)
        result["candidate_actors"] = sorted(
            candidates,
            key=lambda item: (-item["assignment_score"], item["actor_unit_id"]),
        )
        result["candidate_actor_count"] = len(candidates)
        result["rejected_actor_counts"] = dict(sorted(rejections.items()))
        results.append(result)
    return results


def _assignment_weight(objective: dict[str, Any], candidate: dict[str, Any]) -> int:
    return (
        SEVERITY_RANK[objective["severity"]] * 1_000_000_000
        + int(round(objective["objective_utility"] * 1_000_000)) * 100
        + int(round(candidate["assignment_score"] * 1_000_000))
    )


def _solve_assignment(objectives: list[dict[str, Any]]) -> dict[str, str]:
    actors = sorted(
        {
            candidate["actor_unit_id"]
            for objective in objectives
            for candidate in objective["candidate_actors"]
        }
    )
    actor_bits = {actor_id: 1 << index for index, actor_id in enumerate(actors)}

    @lru_cache(maxsize=None)
    def solve(index: int, used_mask: int) -> tuple[int, int, tuple[tuple[str, str], ...]]:
        if index >= len(objectives):
            return 0, 0, ()
        objective = objectives[index]
        best = solve(index + 1, used_mask)
        for candidate in objective["candidate_actors"]:
            actor_id = candidate["actor_unit_id"]
            bit = actor_bits[actor_id]
            if used_mask & bit:
                continue
            child_weight, child_count, child_signature = solve(index + 1, used_mask | bit)
            option = (
                _assignment_weight(objective, candidate) + child_weight,
                1 + child_count,
                ((objective["objective_id"], actor_id),) + child_signature,
            )
            if option[0] > best[0] or (
                option[0] == best[0]
                and (
                    option[1] > best[1]
                    or (option[1] == best[1] and option[2] < best[2])
                )
            ):
                best = option
        return best

    return dict(solve(0, 0)[2])


def build_tactical_objective_assignment(
    state: dict[str, Any], portfolio: dict[str, Any] | None = None
) -> dict[str, Any]:
    portfolio = portfolio or build_tactical_priority_portfolio(state)
    source_items = _source_candidates_for_portfolio(state, portfolio)
    objectives = _attach_candidates(_build_objectives(state, source_items), state)
    selected = _solve_assignment(objectives)

    assignments: list[dict[str, Any]] = []
    objective_results: list[dict[str, Any]] = []
    for objective in objectives:
        actor_id = selected.get(objective["objective_id"])
        result = dict(objective)
        if actor_id is None:
            result["assignment_status"] = "UNFILLED"
            if objective["candidate_actors"]:
                reason = "RESOURCE_CONFLICT_WITH_HIGHER_VALUE_OBJECTIVE"
            elif objective["actor_pool_mode"] == "EXACT_SUBJECT":
                reason = "SUBJECT_NOT_CONTROLLABLE"
            else:
                reason = "NO_LEGAL_CANDIDATE"
            result["unfilled_reason"] = reason
            result["assigned_actor_unit_id"] = None
        else:
            candidate = next(
                item for item in objective["candidate_actors"] if item["actor_unit_id"] == actor_id
            )
            result["assignment_status"] = "ASSIGNED"
            result["unfilled_reason"] = None
            result["assigned_actor_unit_id"] = actor_id
            assignment = {
                "objective_id": objective["objective_id"],
                "objective_type": objective["objective_type"],
                "actor_unit_id": actor_id,
                "actor_role": candidate["actor_role"],
                "subject_unit_ids": objective["subject_unit_ids"],
                "severity": objective["severity"],
                "objective_utility": objective["objective_utility"],
                "assignment_score": candidate["assignment_score"],
                "straight_line_distance_m": candidate["straight_line_distance_m"],
                "exclusive_resource": "UNIT_ACTION_SLOT",
                "status": "PROPOSED_NOT_EXECUTED",
                "authority": "ADVISORY_ONLY",
            }
            assignment["result_digest"] = digest(assignment)
            assignments.append(assignment)
        result["result_digest"] = digest(result)
        objective_results.append(result)

    assigned_actors = [item["actor_unit_id"] for item in assignments]
    assignable_objectives = [item for item in objective_results if item["candidate_actor_count"] > 0]
    critical_objectives = [item for item in objective_results if item["severity"] == "CRITICAL"]
    critical_assignable = [item for item in critical_objectives if item["candidate_actor_count"] > 0]
    critical_assigned = [item for item in critical_objectives if item["assignment_status"] == "ASSIGNED"]
    critical_assignable_assigned = [
        item for item in critical_assignable if item["assignment_status"] == "ASSIGNED"
    ]
    result: dict[str, Any] = {
        "schema_version": 1,
        "assignment_contract": ASSIGNMENT_CONTRACT,
        "slice_id": state["slice_id"],
        "time_ms": state["time_ms"],
        "source_tactical_state_digest": state["result_digest"],
        "source_portfolio_digest": portfolio["result_digest"],
        "source_opportunity_count": len(source_items),
        "objective_count": len(objective_results),
        "assignment_count": len(assignments),
        "unfilled_objective_count": len(objective_results) - len(assignments),
        "unassignable_objective_count": sum(
            item["candidate_actor_count"] == 0 for item in objective_results
        ),
        "uncontrollable_subject_objective_count": sum(
            item["unfilled_reason"] == "SUBJECT_NOT_CONTROLLABLE"
            for item in objective_results
        ),
        "resource_conflict_unfilled_count": sum(
            item["unfilled_reason"] == "RESOURCE_CONFLICT_WITH_HIGHER_VALUE_OBJECTIVE"
            for item in objective_results
        ),
        "assignable_objective_count": len(assignable_objectives),
        "assignable_objective_coverage": _rounded(
            len(assignments) / len(assignable_objectives) if assignable_objectives else 1.0
        ),
        "critical_objective_count": len(critical_objectives),
        "critical_objective_assignment_coverage": _rounded(
            len(critical_assigned) / len(critical_objectives) if critical_objectives else 1.0
        ),
        "critical_assignable_objective_count": len(critical_assignable),
        "critical_assignable_objective_coverage": _rounded(
            len(critical_assignable_assigned) / len(critical_assignable)
            if critical_assignable
            else 1.0
        ),
        "double_booked_actor_count": len(assigned_actors) - len(set(assigned_actors)),
        "objectives": objective_results,
        "assignments": sorted(assignments, key=lambda item: item["objective_id"]),
        "constraints": [
            "Each local unit has at most one advisory unit-action slot per slice.",
            "Routing, shattered, leaving, or rampaging units are not treated as controllable responders.",
            "Units that are themselves protected subjects cannot be reassigned as support responders.",
            "Role-incompatible responders are rejected before optimization.",
            "Straight-line distance is a ranking proxy, not terrain-aware route feasibility.",
            "Unfilled objectives remain explicit; the solver does not fabricate a feasible actor.",
            "Assignments are proposals only and do not establish issue, acceptance, acknowledgement, execution, or outcome.",
        ],
        "evidence_status": "CONTROL_OFFLINE",
        "counterfactual_status": "UNVERIFIED",
        "authority": "NO_ORDERS",
    }
    result["result_digest"] = digest(result)
    return result


def build_trace_objective_assignments(trace_corpus: dict[str, Any]) -> dict[str, Any]:
    trajectory = build_tactical_state_trajectory(trace_corpus)
    portfolios = build_trace_priority_portfolios(trace_corpus)
    assignments = [
        build_tactical_objective_assignment(state, portfolio)
        for state, portfolio in zip(trajectory["states"], portfolios["portfolios"], strict=True)
    ]
    result: dict[str, Any] = {
        "schema_version": 1,
        "assignment_contract": TRAJECTORY_CONTRACT,
        "source_trace_digest": trajectory["source_trace_digest"],
        "source_tactical_state_trajectory_digest": trajectory["result_digest"],
        "source_portfolio_trajectory_digest": portfolios["result_digest"],
        "assignment_slice_count": len(assignments),
        "assignment_slices": assignments,
        "summary": {
            "objective_count": sum(item["objective_count"] for item in assignments),
            "assignment_count": sum(item["assignment_count"] for item in assignments),
            "unfilled_objective_count": sum(item["unfilled_objective_count"] for item in assignments),
            "unassignable_objective_count": sum(item["unassignable_objective_count"] for item in assignments),
            "uncontrollable_subject_objective_count": sum(
                item["uncontrollable_subject_objective_count"] for item in assignments
            ),
            "resource_conflict_unfilled_count": sum(item["resource_conflict_unfilled_count"] for item in assignments),
            "minimum_assignable_objective_coverage": min(
                (item["assignable_objective_coverage"] for item in assignments),
                default=1.0,
            ),
            "minimum_critical_objective_assignment_coverage": min(
                (item["critical_objective_assignment_coverage"] for item in assignments),
                default=1.0,
            ),
            "minimum_critical_assignable_objective_coverage": min(
                (item["critical_assignable_objective_coverage"] for item in assignments),
                default=1.0,
            ),
            "maximum_assignments_in_one_slice": max(
                (item["assignment_count"] for item in assignments), default=0
            ),
            "double_booked_actor_count": sum(item["double_booked_actor_count"] for item in assignments),
        },
        "evidence_status": "CONTROL_OFFLINE_DERIVED_FROM_OBSERVED_INPUT",
        "counterfactual_status": "UNVERIFIED",
        "authority": "NO_ORDERS",
    }
    result["result_digest"] = digest(result)
    return result
