from __future__ import annotations

from copy import deepcopy
from typing import Any

from .canonical import digest
from .strategic_portfolio import (
    APPLICATION_AUTHORITY,
    AUTHORITY,
    build_strategic_theater_portfolio,
    semantic_portfolio_metrics,
)

CONTRACT = "CAMPAIGN_STRATEGIC_THEATER_PORTFOLIO_ADVERSARIAL_MATRIX_V1"


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
    result["wars"] = [[new if x == old else x for x in pair] for pair in result["wars"]]
    return result


def _case_passes(result: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    selected_types = [item["priority_type"] for item in result["selected_priorities"]]
    checks = {
        "posture": result["strategic_posture"] == expected.get("strategic_posture", result["strategic_posture"]),
        "required_selected_types": all(item in selected_types for item in expected.get("required_selected_types", [])),
        "forbidden_selected_types": all(item not in selected_types for item in expected.get("forbidden_selected_types", [])),
        "critical_coverage": result["metrics"]["critical_source_coverage"] >= float(expected.get("minimum_critical_source_coverage", 1.0)),
        "bounded": result["metrics"]["selected_priority_count"] <= int(expected.get("maximum_selected_priority_count", 6)),
        "aggression": result["portfolio_constraints"]["aggressive_commitment_allowed"] == expected.get("aggressive_commitment_allowed", result["portfolio_constraints"]["aggressive_commitment_allowed"]),
        "authority": result["authority"] == AUTHORITY and result["application_authority"] == APPLICATION_AUTHORITY,
    }
    return all(checks.values()), checks


def run_strategic_portfolio_matrix(suite: dict[str, Any]) -> dict[str, Any]:
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("strategic portfolio matrix cases missing")
    records = []
    for case in cases:
        result = build_strategic_theater_portfolio(case["scenario"])
        passed, checks = _case_passes(result, case.get("expected", {}))
        records.append({
            "case_id": case["case_id"],
            "passed": passed,
            "checks": checks,
            "result_digest": result["result_digest"],
            "semantic_metrics": semantic_portfolio_metrics(result),
        })

    base = deepcopy(suite["metamorphic_base"])
    base_result = build_strategic_theater_portfolio(base)
    base_semantic = semantic_portfolio_metrics(base_result)
    metamorphic = []

    hidden = deepcopy(base)
    hidden["armies"].append({
        "id": "hidden_probe",
        "faction": "player_empire",
        "strength": 9999.0,
        "movement": 50.0,
        "replenishment": 1.0,
        "x": 0.0,
        "y": 0.0,
        "visible_to": [],
    })
    metamorphic.append(("hidden_enemy_injection", semantic_portfolio_metrics(build_strategic_theater_portfolio(hidden)) == base_semantic))

    renamed = _rename_faction(base, "player_empire", "npc_empire")
    metamorphic.append(("player_label_to_npc_label", semantic_portfolio_metrics(build_strategic_theater_portfolio(renamed)) == base_semantic))

    reordered = deepcopy(base)
    reordered["armies"] = list(reversed(reordered["armies"]))
    reordered["regions"] = list(reversed(reordered["regions"]))
    reordered["wars"] = list(reversed(reordered["wars"]))
    metamorphic.append(("input_order", semantic_portfolio_metrics(build_strategic_theater_portfolio(reordered)) == base_semantic))

    translated = deepcopy(base)
    for item in translated["armies"] + translated["regions"]:
        item["x"] = float(item["x"]) + 1234.5
        item["y"] = float(item["y"]) - 987.25
    metamorphic.append(("coordinate_translation", semantic_portfolio_metrics(build_strategic_theater_portfolio(translated)) == base_semantic))

    scaled = deepcopy(base)
    for army in scaled["armies"]:
        army["strength"] = float(army["strength"]) * 10.0
    for region in scaled["regions"]:
        region["garrison_strength"] = float(region["garrison_strength"]) * 10.0
    metamorphic.append(("uniform_strength_scale", semantic_portfolio_metrics(build_strategic_theater_portfolio(scaled)) == base_semantic))

    extra_war = deepcopy(base)
    extra_war["wars"].append([extra_war["controlled_faction"], "empty_war_faction"])
    metamorphic.append(("empty_war_edge", semantic_portfolio_metrics(build_strategic_theater_portfolio(extra_war)) == base_semantic))

    checks = [{"check_id": key, "passed": passed} for key, passed in metamorphic]
    result = {
        "schema_version": 1,
        "contract": CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "scenario_count": len(records),
        "scenario_pass_count": sum(1 for item in records if item["passed"]),
        "metamorphic_pass_count": sum(1 for item in checks if item["passed"]),
        "scenarios": records,
        "metamorphic_checks": checks,
    }
    result["result_digest"] = digest(result)
    return result
