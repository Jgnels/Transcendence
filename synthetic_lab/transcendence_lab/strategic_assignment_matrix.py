from __future__ import annotations

from copy import deepcopy
from typing import Any

from .campaign_challenge import APPLICATION_AUTHORITY, AUTHORITY
from .canonical import digest
from .strategic_assignment import build_theater_to_army_assignment, semantic_assignment_metrics
from .strategic_commitment import build_strategic_temporal_commitment, semantic_commitment_metrics

CONTRACT = "CAMPAIGN_THEATER_ASSIGNMENT_AND_COMMITMENT_ADVERSARIAL_MATRIX_V1"


def _rename_faction(scenario: dict[str, Any], old: str, new: str) -> dict[str, Any]:
    result = deepcopy(scenario)
    if result["controlled_faction"] == old:
        result["controlled_faction"] = new
    for army in result["armies"]:
        if army["faction"] == old:
            army["faction"] = new
        army["visible_to"] = [new if item == old else item for item in army["visible_to"]]
    for region in result["regions"]:
        if region["owner"] == old:
            region["owner"] = new
    result["wars"] = [[new if item == old else item for item in pair] for pair in result["wars"]]
    return result


def _assignment_case_passes(result: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    assigned_types = [item["priority_type"] for item in result["assignments"]]
    unfilled = [(item["priority_type"], item["reason"]) for item in result["unfilled_priorities"]]
    checks = {
        "required_assignment_types": all(item in assigned_types for item in expected.get("required_assignment_types", [])),
        "forbidden_assignment_types": all(item not in assigned_types for item in expected.get("forbidden_assignment_types", [])),
        "required_unfilled_reasons": all(
            any(priority_type == req.get("priority_type") and req.get("reason_contains", "") in reason for priority_type, reason in unfilled)
            for req in expected.get("required_unfilled", [])
        ),
        "critical_coverage": result["metrics"]["critical_force_assignment_coverage"] >= float(expected.get("minimum_critical_force_assignment_coverage", 0.0)),
        "max_double_booked": result["metrics"]["double_booked_actor_count"] <= int(expected.get("maximum_double_booked_actor_count", 0)),
        "minimum_recovery_protections": result["metrics"]["recovery_protection_count"] >= int(expected.get("minimum_recovery_protection_count", 0)),
        "minimum_recovery_overrides": result["metrics"]["recovery_override_count"] >= int(expected.get("minimum_recovery_override_count", 0)),
        "reserve": (result["metrics"]["reserve_actor_id"] is not None) == expected.get("reserve_present", result["metrics"]["reserve_actor_id"] is not None),
        "authority": result["authority"] == AUTHORITY and result["application_authority"] == APPLICATION_AUTHORITY,
    }
    return all(checks.values()), checks


def _temporal_case_passes(result: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    event_types = [item["event_type"] for item in result["events"]]
    reasons = [item["reason"] for item in result["events"]]
    final_types = [item["priority_type"] for item in result["final_active_plans"]]
    checks = {
        "required_event_types": all(item in event_types for item in expected.get("required_event_types", [])),
        "forbidden_event_types": all(item not in event_types for item in expected.get("forbidden_event_types", [])),
        "required_reason_fragments": all(any(fragment in reason for reason in reasons) for fragment in expected.get("required_reason_fragments", [])),
        "required_final_priority_types": all(item in final_types for item in expected.get("required_final_priority_types", [])),
        "max_double_booked": max((item["metrics"]["double_booked_actor_count"] for item in result["schedule_slices"]), default=0) <= int(expected.get("maximum_double_booked_actor_count", 0)),
        "authority": result["authority"] == AUTHORITY and result["application_authority"] == APPLICATION_AUTHORITY,
    }
    return all(checks.values()), checks


def _translate(scenario: dict[str, Any], dx: float, dy: float) -> dict[str, Any]:
    result = deepcopy(scenario)
    for item in result["armies"] + result["regions"]:
        item["x"] = float(item["x"]) + dx
        item["y"] = float(item["y"]) + dy
    return result


def _scale(scenario: dict[str, Any], factor: float) -> dict[str, Any]:
    result = deepcopy(scenario)
    for item in result["armies"]:
        item["strength"] = float(item["strength"]) * factor
    for item in result["regions"]:
        item["garrison_strength"] = float(item["garrison_strength"]) * factor
    return result


def run_strategic_assignment_commitment_matrix(suite: dict[str, Any]) -> dict[str, Any]:
    assignment_cases = suite.get("assignment_cases")
    temporal_cases = suite.get("temporal_cases")
    if not isinstance(assignment_cases, list) or not assignment_cases:
        raise ValueError("assignment_cases missing")
    if not isinstance(temporal_cases, list) or not temporal_cases:
        raise ValueError("temporal_cases missing")

    assignment_records = []
    for case in assignment_cases:
        result = build_theater_to_army_assignment(case["scenario"])
        passed, checks = _assignment_case_passes(result, case.get("expected", {}))
        assignment_records.append({
            "case_id": case["case_id"],
            "passed": passed,
            "checks": checks,
            "result_digest": result["result_digest"],
            "semantic_metrics": semantic_assignment_metrics(result),
        })

    temporal_records = []
    for case in temporal_cases:
        result = build_strategic_temporal_commitment(case["scenarios"])
        passed, checks = _temporal_case_passes(result, case.get("expected", {}))
        temporal_records.append({
            "case_id": case["case_id"],
            "passed": passed,
            "checks": checks,
            "result_digest": result["result_digest"],
            "semantic_metrics": semantic_commitment_metrics(result),
        })

    base = deepcopy(suite["metamorphic_assignment_base"])
    base_semantic = semantic_assignment_metrics(build_theater_to_army_assignment(base))
    metamorphic: list[tuple[str, bool]] = []

    hidden = deepcopy(base)
    hidden["armies"].append({
        "id": "hidden_enemy_probe", "faction": "player_empire", "strength": 99999.0,
        "x": 0.0, "y": 0.0, "movement": 99.0, "replenishment": 1.0, "visible_to": [],
    })
    metamorphic.append(("hidden_enemy_injection", semantic_assignment_metrics(build_theater_to_army_assignment(hidden)) == base_semantic))

    renamed = _rename_faction(base, "player_empire", "npc_empire")
    metamorphic.append(("player_label_to_npc_label", semantic_assignment_metrics(build_theater_to_army_assignment(renamed)) == base_semantic))

    reordered = deepcopy(base)
    reordered["armies"] = list(reversed(reordered["armies"]))
    reordered["regions"] = list(reversed(reordered["regions"]))
    reordered["wars"] = list(reversed(reordered["wars"]))
    metamorphic.append(("input_order", semantic_assignment_metrics(build_theater_to_army_assignment(reordered)) == base_semantic))

    translated = _translate(base, 4321.25, -912.5)
    metamorphic.append(("coordinate_translation", semantic_assignment_metrics(build_theater_to_army_assignment(translated)) == base_semantic))

    scaled = _scale(base, 10.0)
    metamorphic.append(("uniform_strength_scale", semantic_assignment_metrics(build_theater_to_army_assignment(scaled)) == base_semantic))

    temporal_base = deepcopy(suite["metamorphic_temporal_base"])
    temporal_semantic = semantic_commitment_metrics(build_strategic_temporal_commitment(temporal_base))
    temporal_reordered = deepcopy(temporal_base)
    for scenario in temporal_reordered:
        scenario["armies"] = list(reversed(scenario["armies"]))
        scenario["regions"] = list(reversed(scenario["regions"]))
        scenario["wars"] = list(reversed(scenario["wars"]))
    metamorphic.append(("temporal_input_order", semantic_commitment_metrics(build_strategic_temporal_commitment(temporal_reordered)) == temporal_semantic))

    temporal_translated = [_translate(item, -333.0, 777.0) for item in temporal_base]
    metamorphic.append(("temporal_coordinate_translation", semantic_commitment_metrics(build_strategic_temporal_commitment(temporal_translated)) == temporal_semantic))

    checks = [{"check_id": name, "passed": passed} for name, passed in metamorphic]
    result = {
        "schema_version": 1,
        "contract": CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "assignment_case_count": len(assignment_records),
        "assignment_pass_count": sum(1 for item in assignment_records if item["passed"]),
        "temporal_case_count": len(temporal_records),
        "temporal_pass_count": sum(1 for item in temporal_records if item["passed"]),
        "metamorphic_pass_count": sum(1 for item in checks if item["passed"]),
        "assignment_cases": assignment_records,
        "temporal_cases": temporal_records,
        "metamorphic_checks": checks,
    }
    result["result_digest"] = digest(result)
    return result
