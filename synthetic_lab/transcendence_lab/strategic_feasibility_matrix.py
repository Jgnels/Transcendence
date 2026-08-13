from __future__ import annotations

from copy import deepcopy
from typing import Any

from .canonical import digest
from .strategic_assignment import build_theater_to_army_assignment
from .strategic_feasibility import (
    APPLICATION_AUTHORITY,
    AUTHORITY,
    StrategicFeasibilityError,
    adjudicate_campaign_strategic_feasibility_observation,
    build_campaign_strategic_feasibility_plan,
    build_observation_packet_template,
    semantic_feasibility_metrics,
)

CONTRACT = "CAMPAIGN_STRATEGIC_FEASIBILITY_ADVERSARIAL_MATRIX_V1"


def _rename_faction(scenario: dict[str, Any], old: str, new: str) -> dict[str, Any]:
    result = deepcopy(scenario)
    if result["controlled_faction"] == old:
        result["controlled_faction"] = new
    for army in result["armies"]:
        if army["faction"] == old:
            army["faction"] = new
        army["visible_to"] = [new if value == old else value for value in army["visible_to"]]
    for region in result["regions"]:
        if region["owner"] == old:
            region["owner"] = new
    result["wars"] = [[new if value == old else value for value in pair] for pair in result["wars"]]
    return result


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


def _first_assignment(scenario: dict[str, Any], priority_type: str | None = None) -> dict[str, Any]:
    result = build_theater_to_army_assignment(scenario)
    candidates = result["assignments"]
    if priority_type is not None:
        candidates = [item for item in candidates if item["priority_type"] == priority_type]
    if not candidates:
        raise StrategicFeasibilityError("matrix case produced no matching assignment")
    return candidates[0]


def _case_passes(plan: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    keys = {item["query_key"] for item in plan["queries"]}
    checks = {
        "required_queries": all(item in keys for item in expected.get("required_queries", [])),
        "forbidden_queries": all(item not in keys for item in expected.get("forbidden_queries", [])),
        "target_kind": plan["target_boundary"]["assignment_target_kind"] == expected.get("target_kind", plan["target_boundary"]["assignment_target_kind"]),
        "settlement_not_promoted": plan["target_boundary"]["settlement_target_promoted"] is False,
        "settlement_query_permission": plan["target_boundary"]["settlement_interface_query_permitted"] == expected.get("settlement_interface_query_permitted", plan["target_boundary"]["settlement_interface_query_permitted"]),
        "faction_centroid_not_attack": plan["target_boundary"]["faction_centroid_is_attack_target"] is False,
        "unobserved": all(item["result_status"] == "UNOBSERVED_QUERY_NOT_RUN" for item in plan["queries"]),
        "authority": plan["authority"] == AUTHORITY and plan["application_authority"] == APPLICATION_AUTHORITY,
    }
    return all(checks.values()), checks


def run_strategic_feasibility_matrix(suite: dict[str, Any]) -> dict[str, Any]:
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases missing")
    records: list[dict[str, Any]] = []
    for case in cases:
        assignment = _first_assignment(case["scenario"], case.get("priority_type"))
        plan = build_campaign_strategic_feasibility_plan(case["scenario"], assignment)
        passed, checks = _case_passes(plan, case.get("expected", {}))
        records.append({
            "case_id": case["case_id"],
            "passed": passed,
            "checks": checks,
            "result_digest": plan["result_digest"],
            "semantic_metrics": semantic_feasibility_metrics(plan),
        })

    base = deepcopy(suite["metamorphic_base"])
    priority_type = suite.get("metamorphic_priority_type")
    base_plan = build_campaign_strategic_feasibility_plan(base, _first_assignment(base, priority_type))
    base_semantic = semantic_feasibility_metrics(base_plan)
    metamorphic: list[tuple[str, bool]] = []

    hidden = deepcopy(base)
    hidden["armies"].append({
        "id": "hidden_enemy_feasibility_probe", "faction": "player_empire", "strength": 999999.0,
        "x": -500.0, "y": 200.0, "movement": 99.0, "replenishment": 1.0, "visible_to": [],
    })
    hidden_plan = build_campaign_strategic_feasibility_plan(hidden, _first_assignment(hidden, priority_type))
    metamorphic.append(("hidden_enemy_injection", semantic_feasibility_metrics(hidden_plan) == base_semantic))

    renamed = _rename_faction(base, "player_empire", "npc_empire")
    renamed_plan = build_campaign_strategic_feasibility_plan(renamed, _first_assignment(renamed, priority_type))
    metamorphic.append(("player_label_to_npc_label", semantic_feasibility_metrics(renamed_plan) == base_semantic))

    reordered = deepcopy(base)
    reordered["armies"] = list(reversed(reordered["armies"]))
    reordered["regions"] = list(reversed(reordered["regions"]))
    reordered["wars"] = list(reversed(reordered["wars"]))
    reordered_plan = build_campaign_strategic_feasibility_plan(reordered, _first_assignment(reordered, priority_type))
    metamorphic.append(("input_order", semantic_feasibility_metrics(reordered_plan) == base_semantic))

    translated = _translate(base, 777.0, -333.0)
    translated_plan = build_campaign_strategic_feasibility_plan(translated, _first_assignment(translated, priority_type))
    metamorphic.append(("coordinate_translation", semantic_feasibility_metrics(translated_plan) == base_semantic))

    scaled = _scale(base, 10.0)
    scaled_plan = build_campaign_strategic_feasibility_plan(scaled, _first_assignment(scaled, priority_type))
    metamorphic.append(("uniform_strength_scale", semantic_feasibility_metrics(scaled_plan) == base_semantic))

    # Synthetic observation semantics: observed query booleans may change query evidence,
    # but must never promote application authority or causal execution.
    observation_plan = base_plan
    packet = build_observation_packet_template(observation_plan)
    for item in packet["results"]:
        item["observed"] = True
        item["value"] = "MILITARY_FORCE_ACTIVE_STANCE_TYPE_DEFAULT" if item["query_key"] == "FORCE_ACTIVE_STANCE" else True
    packet.pop("result_digest", None)
    packet["result_digest"] = digest(packet)
    adjudicated = adjudicate_campaign_strategic_feasibility_observation(observation_plan, packet)
    observation_checks = {
        "all_queries_observed": adjudicated["observed_query_count"] == observation_plan["query_count"],
        "application_prohibited": adjudicated["application_authority"] == APPLICATION_AUTHORITY,
        "no_orders": adjudicated["capability_boundary"]["orders_emitted"] is False,
        "no_execution": adjudicated["capability_boundary"]["execution_observed"] is False,
        "no_outcome": adjudicated["capability_boundary"]["causal_outcome_observed"] is False,
    }

    tamper_checks: dict[str, bool] = {}
    forged = deepcopy(observation_plan)
    forged["application_authority"] = "ALLOWED"
    forged.pop("result_digest", None)
    forged["result_digest"] = digest(forged)
    try:
        build_observation_packet_template(forged)
        tamper_checks["authority_promotion_rejected"] = False
    except StrategicFeasibilityError:
        tamper_checks["authority_promotion_rejected"] = True

    stale = deepcopy(packet)
    stale["turn"] = int(stale["turn"]) + 1
    stale.pop("result_digest", None)
    stale["result_digest"] = digest(stale)
    try:
        adjudicate_campaign_strategic_feasibility_observation(observation_plan, stale)
        tamper_checks["stale_turn_rejected"] = False
    except StrategicFeasibilityError:
        tamper_checks["stale_turn_rejected"] = True

    foreign = deepcopy(packet)
    foreign["results"][0]["query_id"] = "0" * 64
    foreign.pop("result_digest", None)
    foreign["result_digest"] = digest(foreign)
    try:
        adjudicate_campaign_strategic_feasibility_observation(observation_plan, foreign)
        tamper_checks["foreign_query_rejected"] = False
    except StrategicFeasibilityError:
        tamper_checks["foreign_query_rejected"] = True

    metamorphic_checks = [{"check_id": name, "passed": passed} for name, passed in metamorphic]
    result = {
        "schema_version": 1,
        "contract": CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "case_count": len(records),
        "case_pass_count": sum(1 for item in records if item["passed"]),
        "cases": records,
        "metamorphic_check_count": len(metamorphic_checks),
        "metamorphic_pass_count": sum(1 for item in metamorphic_checks if item["passed"]),
        "metamorphic_checks": metamorphic_checks,
        "synthetic_observation_checks": observation_checks,
        "tamper_checks": tamper_checks,
    }
    result["passed"] = (
        result["case_pass_count"] == result["case_count"]
        and result["metamorphic_pass_count"] == result["metamorphic_check_count"]
        and all(observation_checks.values())
        and all(tamper_checks.values())
    )
    result["result_digest"] = digest(result)
    return result
