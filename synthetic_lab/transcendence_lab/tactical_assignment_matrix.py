from __future__ import annotations

import copy
from typing import Any

from .battle_trace import validate_battle_trace_slices
from .canonical import digest
from .tactical_assignment import build_tactical_objective_assignment
from .tactical_baselines import (
    build_synthetic_tactical_slice,
    validate_tactical_baseline_suite,
)
from .tactical_portfolio import build_tactical_priority_portfolio
from .tactical_state import build_tactical_state


SUITE_CONTRACT = "TACTICAL_ASSIGNMENT_MATRIX_V1"
OUTPUT_CONTRACT = "TACTICAL_ASSIGNMENT_MATRIX_REPORT_V1"
_ALLOWED_METAMORPHIC_OPERATIONS = {
    "REVERSE_UNIT_ORDER",
    "REVERSE_PORTFOLIO_PRIORITY_ORDER",
    "TRANSLATE_ALL_POSITIONS",
}


class TacticalAssignmentMatrixError(ValueError):
    pass


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TacticalAssignmentMatrixError(f"{label} must be a nonempty string")
    return value


def _require_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise TacticalAssignmentMatrixError(f"{label} must be a string list")
    if len(value) != len(set(value)):
        raise TacticalAssignmentMatrixError(f"{label} must not contain duplicates")
    return value


def _require_string_map(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise TacticalAssignmentMatrixError(f"{label} must be an object")
    for key, item in value.items():
        _require_string(key, f"{label} key")
        _require_string(item, f"{label}[{key}]")
    return value


def validate_tactical_assignment_suite(
    suite: dict[str, Any],
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
) -> dict[str, Any]:
    trace_corpus = validate_battle_trace_slices(trace_corpus)
    baseline_suite = validate_tactical_baseline_suite(baseline_suite, trace_corpus)
    if not isinstance(suite, dict):
        raise TacticalAssignmentMatrixError("assignment suite must be an object")
    required = {
        "schema_version",
        "suite_contract",
        "suite_id",
        "seed",
        "evidence_status",
        "source_trace_digest",
        "source_baseline_suite_digest",
        "scenarios",
        "metamorphic_checks",
        "interpretation_limits",
        "result_digest",
    }
    missing = sorted(required - suite.keys())
    if missing:
        raise TacticalAssignmentMatrixError(f"assignment suite missing: {missing}")
    if suite["schema_version"] != 1:
        raise TacticalAssignmentMatrixError("unsupported assignment suite schema")
    if suite["suite_contract"] != SUITE_CONTRACT:
        raise TacticalAssignmentMatrixError("unsupported assignment suite contract")
    _require_string(suite.get("suite_id"), "suite_id")
    if not isinstance(suite.get("seed"), int) or isinstance(suite.get("seed"), bool):
        raise TacticalAssignmentMatrixError("seed must be an integer")
    if suite.get("evidence_status") != "CONTROL_SYNTHETIC":
        raise TacticalAssignmentMatrixError("assignment suite must be CONTROL_SYNTHETIC")
    if suite.get("source_trace_digest") != trace_corpus["result_digest"]:
        raise TacticalAssignmentMatrixError("assignment suite source trace digest mismatch")
    if suite.get("source_baseline_suite_digest") != baseline_suite["result_digest"]:
        raise TacticalAssignmentMatrixError("assignment suite baseline digest mismatch")

    limits = _require_string_list(
        suite.get("interpretation_limits"), "interpretation_limits"
    )
    required_limit_terms = ("pathfinding", "orders", "outcome")
    limits_text = " ".join(limits).lower()
    for term in required_limit_terms:
        if term not in limits_text:
            raise TacticalAssignmentMatrixError(
                f"interpretation limits must disclose {term} uncertainty"
            )

    baseline_ids = {item["scenario_id"] for item in baseline_suite["scenarios"]}
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 10:
        raise TacticalAssignmentMatrixError(
            "assignment suite requires at least ten heterogeneous scenarios"
        )
    seen_scenarios: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise TacticalAssignmentMatrixError("each assignment scenario must be an object")
        scenario_id = _require_string(scenario.get("scenario_id"), "scenario_id")
        if scenario_id in seen_scenarios:
            raise TacticalAssignmentMatrixError(f"duplicate scenario_id: {scenario_id}")
        seen_scenarios.add(scenario_id)
        source_id = _require_string(
            scenario.get("source_baseline_scenario_id"),
            f"{scenario_id} source_baseline_scenario_id",
        )
        if source_id not in baseline_ids:
            raise TacticalAssignmentMatrixError(
                f"{scenario_id} references unknown baseline scenario: {source_id}"
            )
        expectations = scenario.get("expectations")
        if not isinstance(expectations, dict):
            raise TacticalAssignmentMatrixError(
                f"{scenario_id} expectations must be an object"
            )
        _require_string_list(
            expectations.get("required_objective_types", []),
            f"{scenario_id} required_objective_types",
        )
        _require_string_list(
            expectations.get("forbidden_objective_types", []),
            f"{scenario_id} forbidden_objective_types",
        )
        _require_string_map(
            expectations.get("required_assignments", {}),
            f"{scenario_id} required_assignments",
        )
        _require_string_map(
            expectations.get("required_unfilled_reasons", {}),
            f"{scenario_id} required_unfilled_reasons",
        )
        for field in (
            "required_objective_count",
            "required_assignment_count",
            "maximum_double_booked_actor_count",
        ):
            value = expectations.get(field)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                raise TacticalAssignmentMatrixError(
                    f"{scenario_id} {field} must be a nonnegative integer"
                )
        for field in (
            "minimum_assignable_objective_coverage",
            "minimum_critical_assignable_objective_coverage",
        ):
            value = expectations.get(field)
            if value is not None and (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not 0.0 <= float(value) <= 1.0
            ):
                raise TacticalAssignmentMatrixError(
                    f"{scenario_id} {field} must be within [0, 1]"
                )

    checks = suite.get("metamorphic_checks")
    if not isinstance(checks, list) or len(checks) < 3:
        raise TacticalAssignmentMatrixError(
            "assignment suite requires at least three metamorphic checks"
        )
    seen_checks: set[str] = set()
    for check in checks:
        if not isinstance(check, dict):
            raise TacticalAssignmentMatrixError("metamorphic check must be an object")
        check_id = _require_string(check.get("check_id"), "check_id")
        if check_id in seen_checks:
            raise TacticalAssignmentMatrixError(f"duplicate check_id: {check_id}")
        seen_checks.add(check_id)
        scenario_id = _require_string(check.get("scenario_id"), f"{check_id} scenario_id")
        if scenario_id not in seen_scenarios:
            raise TacticalAssignmentMatrixError(
                f"{check_id} references unknown assignment scenario: {scenario_id}"
            )
        operation = check.get("operation")
        if operation not in _ALLOWED_METAMORPHIC_OPERATIONS:
            raise TacticalAssignmentMatrixError(
                f"{check_id} unsupported operation: {operation}"
            )
        if operation == "TRANSLATE_ALL_POSITIONS":
            for axis in ("offset_x", "offset_z"):
                value = check.get(axis)
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise TacticalAssignmentMatrixError(
                        f"{check_id} {axis} must be numeric"
                    )

    claimed = suite.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise TacticalAssignmentMatrixError("invalid assignment suite result digest")
    payload = dict(suite)
    payload.pop("result_digest", None)
    if digest(payload) != claimed:
        raise TacticalAssignmentMatrixError("assignment suite result digest mismatch")
    return suite


def _contract_result(
    assignment: dict[str, Any], expectations: dict[str, Any]
) -> dict[str, Any]:
    objectives = {item["objective_id"]: item for item in assignment["objectives"]}
    objective_types = {item["objective_type"] for item in assignment["objectives"]}
    missing_types = sorted(
        set(expectations.get("required_objective_types", [])) - objective_types
    )
    forbidden_types = sorted(
        set(expectations.get("forbidden_objective_types", [])) & objective_types
    )
    assignment_mismatches = []
    for objective_id, expected_actor in expectations.get(
        "required_assignments", {}
    ).items():
        observed = objectives.get(objective_id)
        actual_actor = None if observed is None else observed["assigned_actor_unit_id"]
        if actual_actor != expected_actor:
            assignment_mismatches.append(
                {
                    "objective_id": objective_id,
                    "expected_actor_unit_id": expected_actor,
                    "observed_actor_unit_id": actual_actor,
                }
            )
    unfilled_mismatches = []
    for objective_id, expected_reason in expectations.get(
        "required_unfilled_reasons", {}
    ).items():
        observed = objectives.get(objective_id)
        actual_reason = None if observed is None else observed["unfilled_reason"]
        if actual_reason != expected_reason:
            unfilled_mismatches.append(
                {
                    "objective_id": objective_id,
                    "expected_reason": expected_reason,
                    "observed_reason": actual_reason,
                }
            )

    scalar_mismatches = []
    for field in ("objective_count", "assignment_count"):
        expected = expectations.get(f"required_{field}")
        if expected is not None and assignment[field] != expected:
            scalar_mismatches.append(
                {"field": field, "expected": expected, "observed": assignment[field]}
            )
    maximum_double = expectations.get("maximum_double_booked_actor_count", 0)
    if assignment["double_booked_actor_count"] > maximum_double:
        scalar_mismatches.append(
            {
                "field": "double_booked_actor_count",
                "expected_maximum": maximum_double,
                "observed": assignment["double_booked_actor_count"],
            }
        )
    for field in (
        "assignable_objective_coverage",
        "critical_assignable_objective_coverage",
    ):
        minimum = expectations.get(f"minimum_{field}")
        if minimum is not None and assignment[field] < float(minimum):
            scalar_mismatches.append(
                {
                    "field": field,
                    "expected_minimum": float(minimum),
                    "observed": assignment[field],
                }
            )
    if expectations.get("require_no_assignments", False) and assignment["assignments"]:
        scalar_mismatches.append(
            {
                "field": "assignments",
                "expected": [],
                "observed_count": len(assignment["assignments"]),
            }
        )
    passed = not (
        missing_types
        or forbidden_types
        or assignment_mismatches
        or unfilled_mismatches
        or scalar_mismatches
    )
    return {
        "passed": passed,
        "missing_required_objective_types": missing_types,
        "forbidden_objective_types_present": forbidden_types,
        "assignment_mismatches": assignment_mismatches,
        "unfilled_reason_mismatches": unfilled_mismatches,
        "scalar_mismatches": scalar_mismatches,
    }


def _semantic_signature(assignment: dict[str, Any]) -> dict[str, Any]:
    objectives = [
        {
            "objective_id": item["objective_id"],
            "objective_type": item["objective_type"],
            "source_opportunity_ids": item["source_opportunity_ids"],
            "subject_unit_ids": item["subject_unit_ids"],
            "severity": item["severity"],
            "candidate_actor_ids": [
                candidate["actor_unit_id"] for candidate in item["candidate_actors"]
            ],
            "assignment_status": item["assignment_status"],
            "assigned_actor_unit_id": item["assigned_actor_unit_id"],
            "unfilled_reason": item["unfilled_reason"],
        }
        for item in assignment["objectives"]
    ]
    return {
        "objective_count": assignment["objective_count"],
        "assignment_count": assignment["assignment_count"],
        "unfilled_objective_count": assignment["unfilled_objective_count"],
        "unassignable_objective_count": assignment["unassignable_objective_count"],
        "resource_conflict_unfilled_count": assignment[
            "resource_conflict_unfilled_count"
        ],
        "double_booked_actor_count": assignment["double_booked_actor_count"],
        "objectives": objectives,
    }


def _translate_slice(
    slice_record: dict[str, Any], offset_x: float, offset_z: float
) -> dict[str, Any]:
    result = copy.deepcopy(slice_record)
    for unit in result["units"]:
        unit["position_x"] += offset_x
        unit["position_z"] += offset_z
        unit["ordered_position_x"] += offset_x
        unit["ordered_position_z"] += offset_z
    return result


def run_tactical_assignment_matrix(
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    assignment_suite: dict[str, Any],
) -> dict[str, Any]:
    trace_corpus = validate_battle_trace_slices(trace_corpus)
    baseline_suite = validate_tactical_baseline_suite(baseline_suite, trace_corpus)
    assignment_suite = validate_tactical_assignment_suite(
        assignment_suite, trace_corpus, baseline_suite
    )
    slices_by_id = {item["slice_id"]: item for item in trace_corpus["slices"]}
    baseline_by_id = {
        item["scenario_id"]: item for item in baseline_suite["scenarios"]
    }

    scenario_results = []
    scenario_context: dict[str, dict[str, Any]] = {}
    for scenario in assignment_suite["scenarios"]:
        source = baseline_by_id[scenario["source_baseline_scenario_id"]]
        synthetic_slice = build_synthetic_tactical_slice(
            slices_by_id[source["base_slice_id"]], source["mutations"]
        )
        state = build_tactical_state(synthetic_slice)
        portfolio = build_tactical_priority_portfolio(state)
        assignment = build_tactical_objective_assignment(state, portfolio)
        contract = _contract_result(assignment, scenario["expectations"])
        record = {
            "scenario_id": scenario["scenario_id"],
            "source_baseline_scenario_id": source["scenario_id"],
            "source_slice_id": source["base_slice_id"],
            "source_tactical_state_digest": state["result_digest"],
            "source_portfolio_digest": portfolio["result_digest"],
            "assignment": assignment,
            "contract": contract,
            "authority": "NO_ORDERS",
        }
        record["result_digest"] = digest(record)
        scenario_results.append(record)
        scenario_context[scenario["scenario_id"]] = {
            "slice": synthetic_slice,
            "state": state,
            "portfolio": portfolio,
            "assignment": assignment,
        }

    metamorphic_results = []
    for check in assignment_suite["metamorphic_checks"]:
        context = scenario_context[check["scenario_id"]]
        baseline_assignment = context["assignment"]
        operation = check["operation"]
        if operation == "REVERSE_UNIT_ORDER":
            transformed_slice = copy.deepcopy(context["slice"])
            transformed_slice["units"] = list(reversed(transformed_slice["units"]))
            state = build_tactical_state(transformed_slice)
            portfolio = build_tactical_priority_portfolio(state)
            transformed_assignment = build_tactical_objective_assignment(
                state, portfolio
            )
            comparison_mode = "EXACT_ASSIGNMENT_OUTPUT"
            passed = transformed_assignment == baseline_assignment
        elif operation == "REVERSE_PORTFOLIO_PRIORITY_ORDER":
            portfolio = copy.deepcopy(context["portfolio"])
            portfolio["selected_priorities"] = list(
                reversed(portfolio["selected_priorities"])
            )
            portfolio.pop("result_digest", None)
            portfolio["result_digest"] = digest(portfolio)
            transformed_assignment = build_tactical_objective_assignment(
                context["state"], portfolio
            )
            comparison_mode = "SEMANTIC_ASSIGNMENT_SIGNATURE"
            passed = _semantic_signature(transformed_assignment) == _semantic_signature(
                baseline_assignment
            )
        elif operation == "TRANSLATE_ALL_POSITIONS":
            transformed_slice = _translate_slice(
                context["slice"], float(check["offset_x"]), float(check["offset_z"])
            )
            state = build_tactical_state(transformed_slice)
            portfolio = build_tactical_priority_portfolio(state)
            transformed_assignment = build_tactical_objective_assignment(
                state, portfolio
            )
            comparison_mode = "SEMANTIC_ASSIGNMENT_SIGNATURE"
            passed = _semantic_signature(transformed_assignment) == _semantic_signature(
                baseline_assignment
            )
        else:  # pragma: no cover - validator owns this path
            raise TacticalAssignmentMatrixError(f"unsupported operation: {operation}")
        metamorphic_record = {
            "check_id": check["check_id"],
            "scenario_id": check["scenario_id"],
            "operation": operation,
            "comparison_mode": comparison_mode,
            "passed": passed,
            "baseline_semantic_digest": digest(_semantic_signature(baseline_assignment)),
            "transformed_semantic_digest": digest(
                _semantic_signature(transformed_assignment)
            ),
            "authority": "NO_ORDERS",
        }
        metamorphic_record["result_digest"] = digest(metamorphic_record)
        metamorphic_results.append(metamorphic_record)

    all_assignments = [
        item["assignment"] for item in scenario_results
    ]
    result: dict[str, Any] = {
        "schema_version": 1,
        "output_contract": OUTPUT_CONTRACT,
        "suite_id": assignment_suite["suite_id"],
        "seed": assignment_suite["seed"],
        "source_trace_digest": trace_corpus["result_digest"],
        "source_baseline_suite_digest": baseline_suite["result_digest"],
        "source_assignment_suite_digest": assignment_suite["result_digest"],
        "scenario_count": len(scenario_results),
        "metamorphic_check_count": len(metamorphic_results),
        "scenario_results": scenario_results,
        "metamorphic_results": metamorphic_results,
        "gate_measurements": {
            "scenario_contract_pass_count": sum(
                item["contract"]["passed"] for item in scenario_results
            ),
            "metamorphic_check_pass_count": sum(
                item["passed"] for item in metamorphic_results
            ),
            "total_objective_count": sum(
                item["objective_count"] for item in all_assignments
            ),
            "total_assignment_count": sum(
                item["assignment_count"] for item in all_assignments
            ),
            "total_unassignable_objective_count": sum(
                item["unassignable_objective_count"] for item in all_assignments
            ),
            "total_resource_conflict_unfilled_count": sum(
                item["resource_conflict_unfilled_count"] for item in all_assignments
            ),
            "double_booked_actor_count": sum(
                item["double_booked_actor_count"] for item in all_assignments
            ),
            "all_outputs_no_orders": all(
                item["authority"] == "NO_ORDERS" for item in all_assignments
            ),
        },
        "interpretation_limits": assignment_suite["interpretation_limits"],
        "evidence_status": "CONTROL_SYNTHETIC",
        "counterfactual_status": "UNVERIFIED",
        "authority": "NO_ORDERS",
    }
    result["gate_measurements"]["all_scenarios_passed"] = (
        result["gate_measurements"]["scenario_contract_pass_count"]
        == result["scenario_count"]
    )
    result["gate_measurements"]["all_metamorphic_checks_passed"] = (
        result["gate_measurements"]["metamorphic_check_pass_count"]
        == result["metamorphic_check_count"]
    )
    result["result_digest"] = digest(result)
    return result
