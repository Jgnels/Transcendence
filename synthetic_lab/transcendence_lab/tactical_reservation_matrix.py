from __future__ import annotations

import copy
from typing import Any

from .canonical import digest
from .tactical_guarded import GUARDED_PACKET_CONTRACT, GUARDED_PACKET_SET_CONTRACT
from .tactical_reservation import (
    DEFAULT_MINIMUM_ENDPOINT_SEPARATION_M,
    TacticalReservationError,
    build_endpoint_reservations,
)


SUITE_CONTRACT = "TACTICAL_ENDPOINT_RESERVATION_MATRIX_V1"
REPORT_CONTRACT = "TACTICAL_ENDPOINT_RESERVATION_MATRIX_REPORT_V1"
_ALLOWED_METAMORPHIC = {
    "REVERSE_PACKET_ORDER",
    "TRANSLATE_ALL_ENDPOINTS",
    "REVERSE_CANDIDATE_ORDER",
}
_ALLOWED_MUTATIONS = {
    "ALTER_PACKET_SET_AUTHORITY",
    "DUPLICATE_PLAN_ID",
    "NONFINITE_ENDPOINT",
}


class TacticalReservationMatrixError(ValueError):
    pass


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TacticalReservationMatrixError(f"{label} must be nonempty text")
    return value


def _validate_suite(suite: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(suite, dict) or suite.get("schema_version") != 1:
        raise TacticalReservationMatrixError("unsupported reservation suite schema")
    if suite.get("suite_contract") != SUITE_CONTRACT:
        raise TacticalReservationMatrixError("unsupported reservation suite contract")
    _text(suite.get("suite_id"), "suite_id")
    if not isinstance(suite.get("seed"), int) or isinstance(suite.get("seed"), bool):
        raise TacticalReservationMatrixError("seed must be integer")
    if suite.get("evidence_status") != "CONTROL_SYNTHETIC":
        raise TacticalReservationMatrixError("reservation suite must be CONTROL_SYNTHETIC")
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 12:
        raise TacticalReservationMatrixError("at least twelve reservation scenarios required")
    seen: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise TacticalReservationMatrixError("reservation scenario must be object")
        scenario_id = _text(scenario.get("scenario_id"), "scenario_id")
        if scenario_id in seen:
            raise TacticalReservationMatrixError("duplicate reservation scenario")
        seen.add(scenario_id)
        packets = scenario.get("packets")
        if not isinstance(packets, list):
            raise TacticalReservationMatrixError("scenario packets must be list")
        for packet in packets:
            if not isinstance(packet, dict):
                raise TacticalReservationMatrixError("packet spec must be object")
            _text(packet.get("packet_key"), "packet_key")
            if packet.get("severity") not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                raise TacticalReservationMatrixError("invalid packet severity")
            if not isinstance(packet.get("utility"), (int, float)) or isinstance(packet.get("utility"), bool):
                raise TacticalReservationMatrixError("packet utility must be numeric")
            readiness = packet.get("readiness", "READY")
            if readiness not in {"READY", "DEFERRED"}:
                raise TacticalReservationMatrixError("invalid packet readiness")
            points = packet.get("points", [])
            if readiness == "READY" and (not isinstance(points, list) or not points):
                raise TacticalReservationMatrixError("ready packet requires points")
            for point in points:
                if not isinstance(point, list) or len(point) != 3:
                    raise TacticalReservationMatrixError("endpoint must be [x,y,z]")
        mutation = scenario.get("mutation")
        if mutation is not None and mutation not in _ALLOWED_MUTATIONS:
            raise TacticalReservationMatrixError("unsupported reservation mutation")
        expectations = scenario.get("expectations")
        if not isinstance(expectations, dict):
            raise TacticalReservationMatrixError("reservation expectations must be object")
        for name in ("reservation_count", "unreserved_count"):
            if name in expectations and (
                not isinstance(expectations[name], int)
                or isinstance(expectations[name], bool)
                or expectations[name] < 0
            ):
                raise TacticalReservationMatrixError(f"{name} must be nonnegative integer")
        if type(expectations.get("expect_error", False)) is not bool:
            raise TacticalReservationMatrixError("expect_error must be boolean")
    checks = suite.get("metamorphic_checks")
    if not isinstance(checks, list) or len(checks) < 3:
        raise TacticalReservationMatrixError("at least three reservation metamorphic checks required")
    for check in checks:
        if check.get("operation") not in _ALLOWED_METAMORPHIC:
            raise TacticalReservationMatrixError("unsupported reservation metamorphic operation")
        if check.get("scenario_id") not in seen:
            raise TacticalReservationMatrixError("reservation metamorphic scenario unknown")
    material = dict(suite)
    claimed = material.pop("result_digest", None)
    if claimed != digest(material):
        raise TacticalReservationMatrixError("reservation suite digest mismatch")
    return suite


def _candidate(plan_id: str, rank: int, point: list[Any]) -> dict[str, Any]:
    candidate_id = digest({"plan_instance_id": plan_id, "rank": rank, "point": point})
    record: dict[str, Any] = {
        "candidate_id": candidate_id,
        "rank": rank,
        "strategy": "SYNTHETIC_ENDPOINT_FIXTURE",
        "point": {"x": point[0], "y": point[1], "z": point[2]},
        "horizontal_displacement_m": 10.0 * rank,
        "derivation": ["synthetic endpoint reservation fixture"],
        "clipped_to_abstract_displacement_bound": False,
        "query_result": "QUERY_TRUE",
        "query_evidence_source": "CONTROL_SYNTHETIC_FIXTURE",
        "candidate_status": "POINT_QUERY_SUPPORTED_ONLY",
        "route_completion_status": "UNVERIFIED",
        "formation_feasibility_status": "UNVERIFIED",
        "collision_feasibility_status": "UNVERIFIED",
        "command_legality_status": "UNVERIFIED",
        "direct_acknowledgement_status": "UNAVAILABLE_NOT_OBSERVED",
        "execution_status": "NOT_ISSUED",
        "outcome_status": "UNVERIFIED_NOT_ATTRIBUTED",
    }
    record["result_digest"] = digest(record)
    return record


def _packet(spec: dict[str, Any], index: int) -> dict[str, Any]:
    key = spec["packet_key"]
    plan_id = digest({"synthetic_plan": key})
    ready = spec.get("readiness", "READY") == "READY"
    candidates = [_candidate(plan_id, rank, point) for rank, point in enumerate(spec.get("points", []), 1)] if ready else []
    candidates.sort(key=lambda item: (item["rank"], item["candidate_id"]))
    source_feasibility_plan_digest = digest({"source": key})
    packet_id = digest(
        {
            "plan_instance_id": plan_id,
            "source_feasibility_plan_digest": source_feasibility_plan_digest,
        }
    )
    packet: dict[str, Any] = {
        "schema_version": 1,
        "packet_contract": GUARDED_PACKET_CONTRACT,
        "packet_id": packet_id,
        "slice_id": "v01w_synthetic",
        "time_ms": 100_000,
        "plan_instance_id": plan_id,
        "objective_id": f"OBJ:{key}",
        "objective_type": spec.get("objective_type", "RELIEVE_FRONTLINE"),
        "actor_unit_id": f"actor:{key}",
        "actor_role": spec.get("actor_role", "reserve"),
        "subject_unit_ids": [f"subject:{key}"],
        "severity": spec["severity"],
        "objective_utility": float(spec["utility"]),
        "readiness_class": "READY_POINT_SUPPORTED_SHADOW_ONLY" if ready else "DEFERRED_POINT_UNOBSERVED",
        "eligible_candidate_count": len(candidates),
        "eligible_candidates": candidates,
        "selected_candidate_id": candidates[0]["candidate_id"] if candidates else None,
        "selected_candidate_point": candidates[0]["point"] if candidates else None,
        "selected_candidate_rank": candidates[0]["rank"] if candidates else None,
        "application_status": "PROHIBITED_NO_ORDER_AUTHORITY",
        "shadow_review_status": "READY_FOR_SIMULTANEOUS_CONFLICT_REVIEW" if ready else "NOT_READY",
        "actor_precondition_status": "SATISFIED_FROM_OBSERVED_STATE",
        "candidate_generation_status": "GENERATED" if ready else "NO_QUERY_EVIDENCE",
        "point_evidence_status": "EXACT_POINT_QUERY_TRUE_ONLY" if ready else "NO_SUPPORTED_EXACT_POINT",
        "route_status": "UNVERIFIED",
        "formation_status": "UNVERIFIED",
        "collision_status": "UNVERIFIED",
        "command_legality_status": "UNVERIFIED",
        "project_issue_status": "NOT_ATTEMPTED",
        "direct_acknowledgement_status": "UNAVAILABLE_NOT_OBSERVED",
        "execution_status": "NOT_ISSUED",
        "outcome_status": "UNVERIFIED_NOT_ATTRIBUTED",
        "source_feasibility_plan_digest": source_feasibility_plan_digest,
        "source_schedule_plan_digest": digest({"schedule": key}),
        "authority": "NO_ORDERS",
        "evidence_status": "CONTROL_SYNTHETIC_GUARDED_FIXTURE",
        "interpretation_limits": [
            "synthetic fixture only",
            "not an order",
        ],
    }
    packet["result_digest"] = digest(packet)
    return packet


def _rebuild_packet_digest(packet: dict[str, Any]) -> None:
    packet.pop("result_digest", None)
    packet["result_digest"] = digest(packet)


def _packet_set(specs: list[dict[str, Any]]) -> dict[str, Any]:
    packets = [_packet(spec, index) for index, spec in enumerate(specs)]
    classes: dict[str, int] = {}
    for packet in packets:
        classes[packet["readiness_class"]] = classes.get(packet["readiness_class"], 0) + 1
    result: dict[str, Any] = {
        "schema_version": 1,
        "packet_set_contract": GUARDED_PACKET_SET_CONTRACT,
        "slice_id": "v01w_synthetic",
        "time_ms": 100_000,
        "source_tactical_state_digest": "1" * 64,
        "source_schedule_digest": "2" * 64,
        "source_feasibility_envelope_digest": "3" * 64,
        "packet_count": len(packets),
        "ready_packet_count": sum(item["readiness_class"] == "READY_POINT_SUPPORTED_SHADOW_ONLY" for item in packets),
        "blocked_packet_count": 0,
        "deferred_packet_count": sum(item["readiness_class"].startswith("DEFERRED_") for item in packets),
        "readiness_class_counts": dict(sorted(classes.items())),
        "packets": packets,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_SYNTHETIC_GUARDED_FIXTURE",
        "counterfactual_status": "UNVERIFIED",
    }
    result["result_digest"] = digest(result)
    return result


def _rebuild_packet_set_digest(packet_set: dict[str, Any]) -> None:
    classes: dict[str, int] = {}
    for packet in packet_set["packets"]:
        classes[packet["readiness_class"]] = classes.get(packet["readiness_class"], 0) + 1
    packet_set["packet_count"] = len(packet_set["packets"])
    packet_set["ready_packet_count"] = sum(item["readiness_class"] == "READY_POINT_SUPPORTED_SHADOW_ONLY" for item in packet_set["packets"])
    packet_set["blocked_packet_count"] = sum(item["readiness_class"].startswith("BLOCKED_") for item in packet_set["packets"])
    packet_set["deferred_packet_count"] = sum(item["readiness_class"].startswith("DEFERRED_") for item in packet_set["packets"])
    packet_set["readiness_class_counts"] = dict(sorted(classes.items()))
    packet_set.pop("result_digest", None)
    packet_set["result_digest"] = digest(packet_set)


def _build_case(
    scenario: dict[str, Any],
    *,
    reverse_packets: bool = False,
    translate: tuple[float, float, float] | None = None,
    reverse_candidates: bool = False,
) -> dict[str, Any]:
    packet_set = _packet_set(scenario["packets"])
    if reverse_packets:
        packet_set["packets"] = list(reversed(packet_set["packets"]))
    if translate is not None:
        dx, dy, dz = translate
        for packet in packet_set["packets"]:
            for candidate in packet["eligible_candidates"]:
                candidate["point"]["x"] = float(candidate["point"]["x"]) + dx
                candidate["point"]["y"] = float(candidate["point"]["y"]) + dy
                candidate["point"]["z"] = float(candidate["point"]["z"]) + dz
                candidate["candidate_id"] = digest(
                    {
                        "plan_instance_id": packet["plan_instance_id"],
                        "rank": candidate["rank"],
                        "point": [candidate["point"]["x"], candidate["point"]["y"], candidate["point"]["z"]],
                    }
                )
                candidate.pop("result_digest", None)
                candidate["result_digest"] = digest(candidate)
            canonical = sorted(packet["eligible_candidates"], key=lambda item: (item["rank"], item["candidate_id"]))
            packet["selected_candidate_id"] = canonical[0]["candidate_id"] if canonical else None
            packet["selected_candidate_point"] = canonical[0]["point"] if canonical else None
            _rebuild_packet_digest(packet)
    if reverse_candidates:
        for packet in packet_set["packets"]:
            packet["eligible_candidates"] = list(reversed(packet["eligible_candidates"]))
            _rebuild_packet_digest(packet)
    mutation = scenario.get("mutation")
    if mutation == "ALTER_PACKET_SET_AUTHORITY":
        packet_set["authority"] = "CONTROL"
    elif mutation == "DUPLICATE_PLAN_ID" and len(packet_set["packets"]) >= 2:
        packet_set["packets"][1]["plan_instance_id"] = packet_set["packets"][0]["plan_instance_id"]
        _rebuild_packet_digest(packet_set["packets"][1])
    elif mutation == "NONFINITE_ENDPOINT" and packet_set["packets"]:
        packet_set["packets"][0]["eligible_candidates"][0]["point"]["x"] = "NaN"
        candidate = packet_set["packets"][0]["eligible_candidates"][0]
        candidate.pop("result_digest", None)
        candidate["result_digest"] = digest(candidate)
        packet_set["packets"][0]["selected_candidate_point"] = candidate["point"]
        _rebuild_packet_digest(packet_set["packets"][0])
    _rebuild_packet_set_digest(packet_set)
    return packet_set


def _signature(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "reservation_count": result["reservation_count"],
        "unreserved_ready_packet_count": result["unreserved_ready_packet_count"],
        "solver_mode": result["solver_mode"],
        "optimality_status": result["optimality_status"],
        "reservations": sorted(
            [
                {
                    "objective_id": item["objective_id"],
                    "severity": item["severity"],
                    "candidate_rank": item["candidate_rank"],
                }
                for item in result["reservations"]
            ],
            key=lambda item: item["objective_id"],
        ),
        "unreserved": sorted(
            [
                {
                    "objective_id": item["objective_id"],
                    "severity": item["severity"],
                    "reason": item["reason"],
                }
                for item in result["unreserved_ready_packets"]
            ],
            key=lambda item: item["objective_id"],
        ),
    }


def run_tactical_reservation_matrix(suite: dict[str, Any]) -> dict[str, Any]:
    suite = _validate_suite(suite)
    results: list[dict[str, Any]] = []
    passed = 0
    for scenario in suite["scenarios"]:
        output: dict[str, Any] | None = None
        error: str | None = None
        try:
            output = build_endpoint_reservations(_build_case(scenario))
        except (TacticalReservationError, ValueError, KeyError) as exc:
            error = str(exc)
        expectations = scenario["expectations"]
        expected_solver = expectations.get("solver_mode")
        expected_winners = sorted(expectations.get("reserved_objective_ids", []))
        actual_winners = sorted(item["objective_id"] for item in (output or {}).get("reservations", []))
        checks = {
            "error_expectation": (error is not None) is expectations.get("expect_error", False),
            "reservation_count": output is None or expectations.get("reservation_count") is None or output["reservation_count"] == expectations["reservation_count"],
            "unreserved_count": output is None or expectations.get("unreserved_count") is None or output["unreserved_ready_packet_count"] == expectations["unreserved_count"],
            "solver_mode": output is None or expected_solver is None or output["solver_mode"] == expected_solver,
            "reserved_objectives": output is None or not expected_winners or actual_winners == expected_winners,
            "separation_contract": output is None or output["minimum_selected_endpoint_separation_m"] is None or output["minimum_selected_endpoint_separation_m"] + 1e-9 >= output["minimum_endpoint_separation_m"],
            "authority_prohibited": output is None or (output["authority"] == "NO_ORDERS" and output["application_authority"] == "PROHIBITED"),
            "no_execution_claim": output is None or all(item["execution_status"] == "NOT_ISSUED" for item in output["reservations"]),
        }
        case_passed = all(checks.values())
        passed += int(case_passed)
        results.append(
            {
                "scenario_id": scenario["scenario_id"],
                "passed": case_passed,
                "checks": checks,
                "error": error,
                "reservation_count": int((output or {}).get("reservation_count", 0)),
                "unreserved_count": int((output or {}).get("unreserved_ready_packet_count", 0)),
                "solver_mode": (output or {}).get("solver_mode"),
                "search_node_count": int((output or {}).get("search_node_count", 0)),
                "result_digest": output.get("result_digest") if output else None,
            }
        )

    by_id = {item["scenario_id"]: item for item in suite["scenarios"]}
    metamorphic: list[dict[str, Any]] = []
    for check in suite["metamorphic_checks"]:
        scenario = by_id[check["scenario_id"]]
        base = build_endpoint_reservations(_build_case(scenario))
        operation = check["operation"]
        transformed = build_endpoint_reservations(
            _build_case(
                scenario,
                reverse_packets=operation == "REVERSE_PACKET_ORDER",
                translate=(907.0, 13.0, -611.0) if operation == "TRANSLATE_ALL_ENDPOINTS" else None,
                reverse_candidates=operation == "REVERSE_CANDIDATE_ORDER",
            )
        )
        check_passed = _signature(base) == _signature(transformed)
        metamorphic.append(
            {
                "check_id": check["check_id"],
                "operation": operation,
                "passed": check_passed,
                "base_digest": base["result_digest"],
                "transformed_digest": transformed["result_digest"],
            }
        )

    report: dict[str, Any] = {
        "schema_version": 1,
        "report_contract": REPORT_CONTRACT,
        "suite_id": suite["suite_id"],
        "seed": suite["seed"],
        "scenario_count": len(results),
        "scenario_pass_count": passed,
        "metamorphic_check_count": len(metamorphic),
        "metamorphic_pass_count": sum(item["passed"] for item in metamorphic),
        "scenarios": results,
        "metamorphic_checks": metamorphic,
        "minimum_endpoint_separation_m": DEFAULT_MINIMUM_ENDPOINT_SEPARATION_M,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_SYNTHETIC",
        "interpretation_limits": [
            "Endpoint separation does not model route crossing, unit footprint, terrain, or collision simulation.",
            "Synthetic endpoints are fixtures and do not establish live feasibility.",
            "Reservations are shadow records and are not WH3 orders.",
        ],
    }
    report["result_digest"] = digest(report)
    return report
