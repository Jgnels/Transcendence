from __future__ import annotations

from copy import deepcopy
from typing import Any

from .canonical import digest
from .contracts import validate_campaign_scenario, visible_scenario

CONTRACT = "CAMPAIGN_STRATEGIC_FEASIBILITY_ENVELOPE_V1"
CROSS_EVIDENCE_CONTRACT = "CAMPAIGN_STRATEGIC_FEASIBILITY_CROSS_EVIDENCE_V1"
OBSERVATION_CONTRACT = "CAMPAIGN_STRATEGIC_FEASIBILITY_OBSERVATION_V1"
ADJUDICATION_CONTRACT = "CAMPAIGN_STRATEGIC_FEASIBILITY_ADJUDICATION_V1"
AUTHORITY = "NO_ORDERS"
APPLICATION_AUTHORITY = "PROHIBITED"
QUERY_RESULT_STATUS = "UNOBSERVED_QUERY_NOT_RUN"

# These are documentation-derived capability descriptions only. They are not
# owner-build/runtime observations and do not establish command authority.
DOCUMENTED_QUERY_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "query_key": "MODEL_HAS_CHARACTER_CQI",
        "surface": "MODEL_SCRIPT_INTERFACE.has_character_command_queue_index",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "EXISTENCE_ONLY",
    },
    {
        "query_key": "MODEL_CHARACTER_FROM_CQI",
        "surface": "MODEL_SCRIPT_INTERFACE.character_for_command_queue_index",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "INTERFACE_LOOKUP_ONLY",
    },
    {
        "query_key": "MODEL_HAS_FORCE_CQI",
        "surface": "MODEL_SCRIPT_INTERFACE.has_military_force_command_queue_index",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "EXISTENCE_ONLY",
    },
    {
        "query_key": "MODEL_FORCE_FROM_CQI",
        "surface": "MODEL_SCRIPT_INTERFACE.military_force_for_command_queue_index",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "INTERFACE_LOOKUP_ONLY",
    },
    {
        "query_key": "FORCE_ACTIVE_STANCE",
        "surface": "MILITARY_FORCE_SCRIPT_INTERFACE.active_stance",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "CURRENT_STATE_ONLY",
    },
    {
        "query_key": "FORCE_CAN_ACTIVATE_STANCE",
        "surface": "MILITARY_FORCE_SCRIPT_INTERFACE.can_activate_stance",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "STANCE_ELIGIBILITY_ONLY_NOT_TARGET_REACHABILITY",
    },
    {
        "query_key": "POSITION_REACHABLE_THIS_TURN",
        "surface": "MODEL_SCRIPT_INTERFACE.character_can_reach_position",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "THIS_TURN_POINT_REACHABILITY_ONLY",
    },
    {
        "query_key": "POSITION_REACHABLE_THIS_TURN_IN_STANCE",
        "surface": "MODEL_SCRIPT_INTERFACE.character_can_reach_position_in_stance",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "THIS_TURN_POINT_REACHABILITY_IN_EXACT_STANCE_ONLY",
    },
    {
        "query_key": "POSITION_EVER_REACHABLE",
        "surface": "MODEL_SCRIPT_INTERFACE.character_can_ever_reach_position",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "LONG_HORIZON_REACHABILITY_ONLY_NO_ETA_OR_ROUTE_QUALITY",
    },
    {
        "query_key": "SETTLEMENT_REACHABLE_THIS_TURN",
        "surface": "MODEL_SCRIPT_INTERFACE.character_can_reach_settlement",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "THIS_TURN_SETTLEMENT_REACHABILITY_ONLY",
    },
    {
        "query_key": "SETTLEMENT_REACHABLE_THIS_TURN_IN_STANCE",
        "surface": "MODEL_SCRIPT_INTERFACE.character_can_reach_settlement_in_stance",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "THIS_TURN_SETTLEMENT_REACHABILITY_IN_EXACT_STANCE_ONLY",
    },
    {
        "query_key": "SETTLEMENT_EVER_REACHABLE",
        "surface": "MODEL_SCRIPT_INTERFACE.character_can_ever_reach_settlement",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "LONG_HORIZON_SETTLEMENT_REACHABILITY_ONLY_NO_ETA_OR_ROUTE_QUALITY",
    },
    {
        "query_key": "REGION_SETTLEMENT_INTERFACE",
        "surface": "REGION_SCRIPT_INTERFACE.settlement",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "REGION_TO_SETTLEMENT_INTERFACE_ONLY",
    },
    {
        "query_key": "GARRISON_UNDER_SIEGE",
        "surface": "GARRISON_RESIDENCE_SCRIPT_INTERFACE.is_under_siege",
        "classification": "DOCUMENTED_READ_QUERY_UNOBSERVED_OWNER_BUILD",
        "scope": "CURRENT_SIEGE_STATE_ONLY",
    },
    {
        "query_key": "GARRISON_CAN_ASSAULT",
        "surface": "GARRISON_RESIDENCE_SCRIPT_INTERFACE.can_assault",
        "classification": "DOCUMENTED_AMBIGUOUS_CONTEXT_NOT_PROMOTED",
        "scope": "NOT_USED_AS_ACTOR_TARGET_ATTACK_LEGALITY",
    },
    {
        "query_key": "GARRISON_CAN_BE_OCCUPIED_BY_FACTION",
        "surface": "GARRISON_RESIDENCE_SCRIPT_INTERFACE.can_be_occupied_by_faction",
        "classification": "DOCUMENTED_READ_QUERY_NOT_ACTOR_ACTION_LEGALITY",
        "scope": "RESIDENCE_FACTION_OCCUPANCY_ONLY",
    },
)

# Names are kept as data so the authority boundary is explicit and auditable.
# No function in this module imports, resolves, or calls any of them.
PROHIBITED_MUTATION_SURFACES: tuple[str, ...] = (
    "cm:move_to",
    "campaign_manager:move_character",
    "cm:attack",
    "cm:attack_region",
    "cm:attack_queued",
    "cm:force_attack_of_opportunity",
    "cm:join_garrison",
    "cm:leave_garrison",
    "cm:force_character_force_into_stance",
    "cm:replenish_action_points",
    "cm:zero_action_points",
    "cm:disable_movement_for_character",
    "cm:enable_movement_for_character",
    "cm:disable_movement_for_faction",
    "cm:enable_movement_for_faction",
    "cm:disable_pathfinding_restriction",
)


class StrategicFeasibilityError(ValueError):
    pass


def _verified_digest(record: dict[str, Any], label: str) -> None:
    claimed = record.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise StrategicFeasibilityError(f"{label} result digest missing or invalid")
    payload = dict(record)
    payload.pop("result_digest", None)
    if digest(payload) != claimed:
        raise StrategicFeasibilityError(f"{label} result digest mismatch")


def _query_catalog_map() -> dict[str, dict[str, Any]]:
    return {item["query_key"]: deepcopy(item) for item in DOCUMENTED_QUERY_CATALOG}


def _scenario_actor(scenario: dict[str, Any], actor_id: str) -> dict[str, Any]:
    observer = scenario["controlled_faction"]
    visible = visible_scenario(scenario, observer)
    actor = next((item for item in visible["armies"] if item["id"] == actor_id and item["faction"] == observer), None)
    if actor is None:
        raise StrategicFeasibilityError(f"assignment actor absent from observer-safe controlled state: {actor_id}")
    observation = actor.get("observation")
    if not isinstance(observation, dict) or observation.get("planner_eligible") is False:
        raise StrategicFeasibilityError(f"assignment actor lacks planner-eligible observation: {actor_id}")
    return actor


def _required_positive_int(observation: dict[str, Any], key: str, actor_id: str) -> int:
    value = observation.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) <= 0 or float(value) != int(value):
        raise StrategicFeasibilityError(f"{actor_id} missing stable positive {key}")
    return int(value)


def _query(
    assignment: dict[str, Any],
    query_key: str,
    parameters: dict[str, Any],
    *,
    target_semantics: str,
) -> dict[str, Any]:
    catalog = _query_catalog_map()
    if query_key not in catalog:
        raise StrategicFeasibilityError(f"unknown documented query: {query_key}")
    base = catalog[query_key]
    record = {
        "query_key": query_key,
        "surface": base["surface"],
        "documented_classification": base["classification"],
        "documented_scope": base["scope"],
        "parameters": deepcopy(parameters),
        "target_semantics": target_semantics,
        "result_status": QUERY_RESULT_STATUS,
        "observed_result": None,
        "action_legality": "NOT_ESTABLISHED",
        "route_details": "NOT_ESTABLISHED",
        "acknowledgement": "NOT_ESTABLISHED",
        "execution": "NOT_ESTABLISHED",
        "outcome": "NOT_ESTABLISHED",
    }
    record["query_id"] = digest({
        "assignment_id": assignment["assignment_id"],
        "query_key": query_key,
        "parameters": record["parameters"],
        "target_semantics": target_semantics,
    })
    return record


def _validate_assignment_record(assignment: dict[str, Any]) -> None:
    if assignment.get("assignment_status") != "SHADOW_PROPOSED_NOT_EXECUTED":
        raise StrategicFeasibilityError("assignment is not a shadow-unexecuted proposal")
    if assignment.get("authority") != AUTHORITY or assignment.get("application_authority") != APPLICATION_AUTHORITY:
        raise StrategicFeasibilityError("assignment authority promoted or malformed")
    if assignment.get("route_status") != "NOT_EVALUATED_GEOMETRIC_REFERENCE_ONLY":
        raise StrategicFeasibilityError("assignment route status is not the v0.2G limiting state")
    claimed = assignment.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise StrategicFeasibilityError("assignment result digest missing")
    payload = dict(assignment)
    payload.pop("result_digest", None)
    if digest(payload) != claimed:
        raise StrategicFeasibilityError("assignment result digest mismatch")


def build_campaign_strategic_feasibility_plan(
    raw_scenario: dict[str, Any], assignment: dict[str, Any]
) -> dict[str, Any]:
    scenario = validate_campaign_scenario(raw_scenario)
    _validate_assignment_record(assignment)
    actor = _scenario_actor(scenario, assignment["actor_id"])
    observation = actor["observation"]
    character_cqi = _required_positive_int(observation, "general_cqi", assignment["actor_id"])
    force_cqi = _required_positive_int(observation, "force_cqi", assignment["actor_id"])
    stance = observation.get("stance")
    if stance is not None and not isinstance(stance, str):
        raise StrategicFeasibilityError("actor stance must be a string or null")

    queries: list[dict[str, Any]] = []
    common = {"character_cqi": character_cqi, "force_cqi": force_cqi}
    queries.append(_query(assignment, "MODEL_HAS_CHARACTER_CQI", {"character_cqi": character_cqi}, target_semantics="ACTOR_BINDING"))
    queries.append(_query(assignment, "MODEL_CHARACTER_FROM_CQI", {"character_cqi": character_cqi}, target_semantics="ACTOR_BINDING"))
    queries.append(_query(assignment, "MODEL_HAS_FORCE_CQI", {"force_cqi": force_cqi}, target_semantics="ACTOR_BINDING"))
    queries.append(_query(assignment, "MODEL_FORCE_FROM_CQI", {"force_cqi": force_cqi}, target_semantics="ACTOR_BINDING"))
    queries.append(_query(assignment, "FORCE_ACTIVE_STANCE", {"force_cqi": force_cqi}, target_semantics="CURRENT_ACTOR_STATE"))

    target_kind = assignment.get("target_kind")
    target_id = assignment.get("target_id")
    anchor = assignment.get("reference_anchor")
    target_boundary: dict[str, Any] = {
        "assignment_target_kind": target_kind,
        "assignment_target_id": target_id,
        "concrete_attack_target_promoted": False,
        "settlement_target_promoted": False,
        "settlement_interface_query_permitted": False,
        "faction_centroid_is_attack_target": False,
    }

    if isinstance(anchor, dict):
        x = float(anchor["x"])
        y = float(anchor["y"])
        point_parameters = {**common, "x": round(x, 6), "y": round(y, 6)}
        queries.append(_query(
            assignment,
            "POSITION_REACHABLE_THIS_TURN",
            point_parameters,
            target_semantics="REFERENCE_POINT_ONLY_NOT_ATTACK_TARGET",
        ))
        if stance:
            queries.append(_query(
                assignment,
                "POSITION_REACHABLE_THIS_TURN_IN_STANCE",
                {**point_parameters, "stance": stance},
                target_semantics="REFERENCE_POINT_ONLY_NOT_ATTACK_TARGET",
            ))
        queries.append(_query(
            assignment,
            "POSITION_EVER_REACHABLE",
            point_parameters,
            target_semantics="REFERENCE_POINT_ONLY_NOT_ATTACK_TARGET",
        ))

    if target_kind == "REGION" and isinstance(target_id, str) and target_id:
        region = next((item for item in scenario["regions"] if item["id"] == target_id), None)
        if region is None:
            raise StrategicFeasibilityError(f"region target absent from source scenario: {target_id}")
        target_boundary["settlement_interface_query_permitted"] = True
        target_boundary["settlement_query_scope"] = "REGION_KEY_TO_ITS_SETTLEMENT_INTERFACE_ONLY_NO_ACTION_TARGET_PROMOTION"
        queries.append(_query(
            assignment,
            "REGION_SETTLEMENT_INTERFACE",
            {"region_key": target_id},
            target_semantics="EXACT_REGION_SETTLEMENT_INTERFACE",
        ))
        settlement_parameters = {**common, "region_key": target_id}
        queries.append(_query(
            assignment,
            "SETTLEMENT_REACHABLE_THIS_TURN",
            settlement_parameters,
            target_semantics="EXACT_REGION_SETTLEMENT_REACHABILITY_NOT_ATTACK_ORDER",
        ))
        if stance:
            queries.append(_query(
                assignment,
                "SETTLEMENT_REACHABLE_THIS_TURN_IN_STANCE",
                {**settlement_parameters, "stance": stance},
                target_semantics="EXACT_REGION_SETTLEMENT_REACHABILITY_NOT_ATTACK_ORDER",
            ))
        queries.append(_query(
            assignment,
            "SETTLEMENT_EVER_REACHABLE",
            settlement_parameters,
            target_semantics="EXACT_REGION_SETTLEMENT_LONG_HORIZON_REACHABILITY_ONLY",
        ))
        if bool(region.get("under_siege")):
            queries.append(_query(
                assignment,
                "GARRISON_UNDER_SIEGE",
                {"region_key": target_id},
                target_semantics="CONTEXT_CONFIRMATION_ONLY",
            ))
    elif target_kind == "FACTION":
        target_boundary["faction_centroid_is_attack_target"] = False
        target_boundary["faction_target_limitation"] = (
            "FACTION priority retains only observer-safe visible-asset centroid reachability; "
            "it does not select a character, settlement, or attack target."
        )
    elif target_kind is None:
        target_boundary["posture_or_capacity_only"] = True
    else:
        raise StrategicFeasibilityError(f"unsupported v0.2G target kind: {target_kind}")

    plan = {
        "schema_version": 1,
        "contract": CONTRACT,
        "evidence_status": "CONTROL_OFFLINE_QUERY_PLAN_UNOBSERVED_RUNTIME",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "scenario_id": scenario["scenario_id"],
        "turn": scenario["turn"],
        "source_scenario_digest": digest(scenario),
        "source_assignment_id": assignment["assignment_id"],
        "source_assignment_result_digest": assignment["result_digest"],
        "actor": {
            "actor_id": assignment["actor_id"],
            "character_cqi": character_cqi,
            "force_cqi": force_cqi,
            "observed_stance_reference": stance,
        },
        "target_boundary": target_boundary,
        "query_count": len(queries),
        "queries": queries,
        "capability_boundary": {
            "documented_queries_only": True,
            "owner_runtime_queries_observed": False,
            "route_path_observed": False,
            "zone_of_control_observed": False,
            "interception_observed": False,
            "movement_or_action_order_emitted": False,
            "acknowledgement_observed": False,
            "execution_observed": False,
            "causal_outcome_observed": False,
        },
        "guardrails": [
            "A documented query surface is not an observed owner-build capability until a read-only live packet records it.",
            "A true can-reach query is scoped to the exact actor, target representation, stance when supplied, and observation instant.",
            "Point reachability to a faction centroid does not create a character, settlement, or attack target.",
            "Can-ever-reach is not an ETA, route-quality, safety, interception, or eventual-success claim.",
            "No feasibility result grants application authority; campaign mutation surfaces remain prohibited.",
        ],
    }
    plan["result_digest"] = digest(plan)
    return plan


def _validate_observed_report(report: dict[str, Any]) -> None:
    if report.get("mode") != "SHADOW_NO_ORDERS":
        raise StrategicFeasibilityError("observed report must be SHADOW_NO_ORDERS")
    authority = report.get("authority")
    if not isinstance(authority, dict) or authority.get("game_orders_emitted") is not False or authority.get("save_values_written") is not False:
        raise StrategicFeasibilityError("observed report authority is not read-only shadow evidence")
    turns = report.get("turn_results")
    if not isinstance(turns, list) or not turns:
        raise StrategicFeasibilityError("observed report turn_results missing")
    parsed = []
    for item in turns:
        if not isinstance(item, dict) or not isinstance(item.get("scenario"), dict):
            raise StrategicFeasibilityError("observed report contains malformed turn result")
        scenario = validate_campaign_scenario(item["scenario"])
        if int(item.get("turn", scenario["turn"])) != scenario["turn"]:
            raise StrategicFeasibilityError("observed report turn/scenario mismatch")
        parsed.append(scenario["turn"])
    if parsed != sorted(parsed) or len(set(parsed)) != len(parsed):
        raise StrategicFeasibilityError("observed report turns must be unique and ordered")


def _validate_force_allocation(force_allocation: dict[str, Any]) -> None:
    _verified_digest(force_allocation, "v0.2G force allocation")
    if force_allocation.get("contract") != "CAMPAIGN_STRATEGIC_FORCE_ALLOCATION_CROSS_EVIDENCE_V1":
        raise StrategicFeasibilityError("unexpected force-allocation contract")
    if force_allocation.get("authority") != AUTHORITY or force_allocation.get("application_authority") != APPLICATION_AUTHORITY:
        raise StrategicFeasibilityError("force-allocation authority promoted")
    envelope = force_allocation.get("assignment_envelope")
    if not isinstance(envelope, dict):
        raise StrategicFeasibilityError("force-allocation assignment envelope missing")
    _verified_digest(envelope, "v0.2G assignment envelope")
    if envelope.get("authority") != AUTHORITY or envelope.get("application_authority") != APPLICATION_AUTHORITY:
        raise StrategicFeasibilityError("assignment-envelope authority promoted")


def build_cross_evidence_campaign_strategic_feasibility(
    observed_report: dict[str, Any], force_allocation: dict[str, Any]
) -> dict[str, Any]:
    _validate_observed_report(observed_report)
    _validate_force_allocation(force_allocation)
    scenarios = {item["scenario"]["scenario_id"]: item["scenario"] for item in observed_report["turn_results"]}

    plans: list[dict[str, Any]] = []
    empty_turns: list[int] = []
    for assignment_result in force_allocation["assignment_envelope"]["observed_assignments"]:
        scenario_id = assignment_result["scenario_id"]
        scenario = scenarios.get(scenario_id)
        if scenario is None:
            raise StrategicFeasibilityError(f"force allocation references foreign scenario: {scenario_id}")
        if digest(validate_campaign_scenario(scenario)) != assignment_result["scenario_digest"]:
            raise StrategicFeasibilityError(f"force allocation scenario digest mismatch: {scenario_id}")
        if not assignment_result["assignments"]:
            empty_turns.append(int(assignment_result["turn"]))
            continue
        for assignment in assignment_result["assignments"]:
            plans.append(build_campaign_strategic_feasibility_plan(scenario, assignment))

    catalog = [deepcopy(item) for item in DOCUMENTED_QUERY_CATALOG]
    result = {
        "schema_version": 1,
        "contract": CROSS_EVIDENCE_CONTRACT,
        "evidence_status": "CONTROL_OFFLINE_DOCUMENTED_QUERY_ENVELOPE",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "source_observed_report_digest": observed_report["result_digest"],
        "source_force_allocation_digest": force_allocation["result_digest"],
        "documented_query_catalog": catalog,
        "prohibited_mutation_surfaces": list(PROHIBITED_MUTATION_SURFACES),
        "observed_feasibility_plans": plans,
        "turns_without_force_assignment": sorted(empty_turns),
        "metrics": {
            "documented_query_surface_count": len(catalog),
            "prohibited_mutation_surface_count": len(PROHIBITED_MUTATION_SURFACES),
            "observed_assignment_plan_count": len(plans),
            "planned_query_count": sum(item["query_count"] for item in plans),
            "live_query_result_count": 0,
            "owner_runtime_capability_promotions": 0,
            "campaign_orders_emitted": 0,
        },
        "live_observation_requirement": {
            "status": "OPEN_DISTINCT_READ_ONLY_GATE",
            "reason": "Documentation establishes query surfaces but cannot prove the exact owner build/runtime semantics or results.",
            "minimum_packet": [
                "bind one current planner-eligible controlled army by exact character and force CQI",
                "record its current active stance",
                "evaluate only query ids generated from a current shadow assignment",
                "preserve each boolean/string result with turn/scenario/assignment binding",
                "emit no campaign mutation call before, during, or after the query packet",
            ],
            "historical_turn_7_replay_required": False,
            "new_campaign_session_required_now": False,
        },
        "nonpromotions": [
            "No documented query is promoted to owner-runtime OBSERVED in v0.2H.",
            "No straight-line assignment ETA is promoted to WH3 path feasibility.",
            "No faction centroid is promoted to a concrete attack target.",
            "No reachability result can imply movement/attack order legality, acknowledgement, execution, or outcome.",
            "No ambiguous garrison can_assault surface is used as actor-target attack legality.",
        ],
    }
    result["result_digest"] = digest(result)
    return result


def build_observation_packet_template(plan: dict[str, Any]) -> dict[str, Any]:
    _verified_digest(plan, "feasibility plan")
    if plan.get("contract") != CONTRACT or plan.get("authority") != AUTHORITY or plan.get("application_authority") != APPLICATION_AUTHORITY:
        raise StrategicFeasibilityError("invalid feasibility plan")
    packet = {
        "schema_version": 1,
        "contract": OBSERVATION_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "source_plan_digest": plan["result_digest"],
        "scenario_id": plan["scenario_id"],
        "turn": plan["turn"],
        "results": [
            {"query_id": item["query_id"], "query_key": item["query_key"], "observed": False, "value": None}
            for item in plan["queries"]
        ],
        "orders_emitted": False,
        "save_values_written": False,
    }
    packet["result_digest"] = digest(packet)
    return packet


def adjudicate_campaign_strategic_feasibility_observation(
    plan: dict[str, Any], packet: dict[str, Any]
) -> dict[str, Any]:
    _verified_digest(plan, "feasibility plan")
    _verified_digest(packet, "observation packet")
    if packet.get("contract") != OBSERVATION_CONTRACT:
        raise StrategicFeasibilityError("unexpected observation contract")
    if packet.get("source_plan_digest") != plan["result_digest"]:
        raise StrategicFeasibilityError("observation packet is stale or foreign")
    if packet.get("scenario_id") != plan["scenario_id"] or packet.get("turn") != plan["turn"]:
        raise StrategicFeasibilityError("observation packet scenario/turn mismatch")
    if packet.get("authority") != AUTHORITY or packet.get("application_authority") != APPLICATION_AUTHORITY:
        raise StrategicFeasibilityError("observation packet authority promoted")
    if packet.get("orders_emitted") is not False or packet.get("save_values_written") is not False:
        raise StrategicFeasibilityError("observation packet is not read-only")

    expected = {item["query_id"]: item for item in plan["queries"]}
    results = packet.get("results")
    if not isinstance(results, list) or len(results) != len(expected):
        raise StrategicFeasibilityError("observation packet query cardinality mismatch")
    seen: set[str] = set()
    adjudicated: list[dict[str, Any]] = []
    observed_count = 0
    for item in results:
        query_id = item.get("query_id")
        if query_id in seen or query_id not in expected:
            raise StrategicFeasibilityError("duplicate or foreign query id")
        seen.add(query_id)
        source = expected[query_id]
        if item.get("query_key") != source["query_key"]:
            raise StrategicFeasibilityError("query key does not match query id")
        observed = item.get("observed")
        if not isinstance(observed, bool):
            raise StrategicFeasibilityError("observed must be boolean")
        value = item.get("value")
        if observed:
            observed_count += 1
            if source["query_key"] == "FORCE_ACTIVE_STANCE":
                if not isinstance(value, str) or not value:
                    raise StrategicFeasibilityError("active stance observation must be a nonempty string")
            else:
                if not isinstance(value, bool):
                    raise StrategicFeasibilityError("query observation must be boolean")
        elif value is not None:
            raise StrategicFeasibilityError("unobserved query must have null value")
        record = deepcopy(source)
        record["result_status"] = "OBSERVED_QUERY_RESULT" if observed else QUERY_RESULT_STATUS
        record["observed_result"] = value if observed else None
        adjudicated.append(record)

    result = {
        "schema_version": 1,
        "contract": ADJUDICATION_CONTRACT,
        "evidence_status": "CONTROL_OFFLINE_ADJUDICATION_OF_SUPPLIED_READ_ONLY_QUERY_PACKET",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "source_plan_digest": plan["result_digest"],
        "source_observation_digest": packet["result_digest"],
        "observed_query_count": observed_count,
        "queries": adjudicated,
        "capability_boundary": {
            "query_results_observed": observed_count,
            "route_path_observed": False,
            "zone_of_control_observed": False,
            "interception_observed": False,
            "orders_emitted": False,
            "acknowledgement_observed": False,
            "execution_observed": False,
            "causal_outcome_observed": False,
        },
    }
    result["result_digest"] = digest(result)
    return result


def semantic_feasibility_metrics(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "query_keys": sorted(item["query_key"] for item in plan["queries"]),
        "target_kind": plan["target_boundary"]["assignment_target_kind"],
        "concrete_attack_target_promoted": plan["target_boundary"]["concrete_attack_target_promoted"],
        "settlement_target_promoted": plan["target_boundary"]["settlement_target_promoted"],
        "settlement_interface_query_permitted": plan["target_boundary"]["settlement_interface_query_permitted"],
        "faction_centroid_is_attack_target": plan["target_boundary"]["faction_centroid_is_attack_target"],
        "query_count": plan["query_count"],
        "authority": plan["authority"],
        "application_authority": plan["application_authority"],
    }
