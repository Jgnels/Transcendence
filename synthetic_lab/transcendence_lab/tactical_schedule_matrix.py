from __future__ import annotations

import copy
from typing import Any

from .canonical import digest
from .tactical_assignment import build_tactical_objective_assignment
from .tactical_baselines import (
    build_synthetic_tactical_slice,
    validate_tactical_baseline_suite,
)
from .tactical_portfolio import build_tactical_priority_portfolio
from .tactical_schedule import build_tactical_temporal_schedule
from .tactical_state import build_tactical_state
from .battle_trace import validate_battle_trace_slices


SUITE_CONTRACT = "TACTICAL_TEMPORAL_SCHEDULE_MATRIX_V1"
OUTPUT_CONTRACT = "TACTICAL_TEMPORAL_SCHEDULE_MATRIX_REPORT_V1"
_ALLOWED_METAMORPHIC_OPERATIONS = {
    "REVERSE_UNIT_ORDER",
    "REVERSE_ASSIGNMENT_RECORD_ORDER",
    "TRANSLATE_ALL_POSITIONS",
}


class TacticalScheduleMatrixError(ValueError):
    pass


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TacticalScheduleMatrixError(f"{label} must be a nonempty string")
    return value


def _require_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise TacticalScheduleMatrixError(f"{label} must be a string list")
    if len(value) != len(set(value)):
        raise TacticalScheduleMatrixError(f"{label} must not contain duplicates")
    return value


def _require_string_map(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise TacticalScheduleMatrixError(f"{label} must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        result[_require_string(key, f"{label} key")] = _require_string(
            item, f"{label} value"
        )
    return result


def _require_map_of_string_lists(
    value: object, label: str
) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise TacticalScheduleMatrixError(f"{label} must be an object")
    return {
        _require_string(key, f"{label} key"): _require_string_list(
            item, f"{label} {key}"
        )
        for key, item in value.items()
    }


def validate_tactical_schedule_suite(
    suite: dict[str, Any],
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
) -> dict[str, Any]:
    trace_corpus = validate_battle_trace_slices(trace_corpus)
    baseline_suite = validate_tactical_baseline_suite(baseline_suite, trace_corpus)
    if not isinstance(suite, dict):
        raise TacticalScheduleMatrixError("schedule suite must be an object")
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
        raise TacticalScheduleMatrixError(f"schedule suite missing: {missing}")
    if suite["schema_version"] != 1:
        raise TacticalScheduleMatrixError("unsupported schedule suite schema")
    if suite["suite_contract"] != SUITE_CONTRACT:
        raise TacticalScheduleMatrixError("unsupported schedule suite contract")
    _require_string(suite.get("suite_id"), "suite_id")
    if not isinstance(suite.get("seed"), int) or isinstance(
        suite.get("seed"), bool
    ):
        raise TacticalScheduleMatrixError("seed must be an integer")
    if suite.get("evidence_status") != "CONTROL_SYNTHETIC":
        raise TacticalScheduleMatrixError("schedule suite must be CONTROL_SYNTHETIC")
    if suite.get("source_trace_digest") != trace_corpus["result_digest"]:
        raise TacticalScheduleMatrixError("schedule suite source trace digest mismatch")
    if suite.get("source_baseline_suite_digest") != baseline_suite["result_digest"]:
        raise TacticalScheduleMatrixError(
            "schedule suite source baseline digest mismatch"
        )
    limits = _require_string_list(
        suite.get("interpretation_limits"), "interpretation_limits"
    )
    if not any("order" in item.lower() and "not" in item.lower() for item in limits):
        raise TacticalScheduleMatrixError(
            "interpretation limits must disclaim live-order authority"
        )

    known_baselines = {item["scenario_id"] for item in baseline_suite["scenarios"]}
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 10:
        raise TacticalScheduleMatrixError(
            "schedule suite requires at least ten temporal scenarios"
        )
    seen_scenarios: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise TacticalScheduleMatrixError("each schedule scenario must be an object")
        scenario_id = _require_string(scenario.get("scenario_id"), "scenario_id")
        if scenario_id in seen_scenarios:
            raise TacticalScheduleMatrixError(f"duplicate scenario_id: {scenario_id}")
        seen_scenarios.add(scenario_id)
        _require_string(scenario.get("description"), f"{scenario_id} description")
        start_time_ms = scenario.get("start_time_ms", 100_000)
        if not isinstance(start_time_ms, int) or isinstance(start_time_ms, bool) or start_time_ms < 0:
            raise TacticalScheduleMatrixError(
                f"{scenario_id} start_time_ms must be a nonnegative integer"
            )
        steps = scenario.get("steps")
        if not isinstance(steps, list) or not steps:
            raise TacticalScheduleMatrixError(f"{scenario_id} steps must be nonempty")
        seen_steps: set[str] = set()
        previous_offset: int | None = None
        for step in steps:
            if not isinstance(step, dict):
                raise TacticalScheduleMatrixError(
                    f"{scenario_id} step must be an object"
                )
            step_id = _require_string(step.get("step_id"), f"{scenario_id} step_id")
            if step_id in seen_steps:
                raise TacticalScheduleMatrixError(
                    f"{scenario_id} duplicate step_id: {step_id}"
                )
            seen_steps.add(step_id)
            baseline_id = _require_string(
                step.get("source_baseline_scenario_id"),
                f"{scenario_id} {step_id} source baseline",
            )
            if baseline_id not in known_baselines:
                raise TacticalScheduleMatrixError(
                    f"{scenario_id} {step_id} references unknown baseline: {baseline_id}"
                )
            offset = step.get("time_offset_ms")
            if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
                raise TacticalScheduleMatrixError(
                    f"{scenario_id} {step_id} time_offset_ms must be nonnegative"
                )
            if previous_offset is not None and offset <= previous_offset:
                raise TacticalScheduleMatrixError(
                    f"{scenario_id} step offsets must be strictly increasing"
                )
            previous_offset = offset
            mutations = step.get("additional_mutations", [])
            if not isinstance(mutations, list):
                raise TacticalScheduleMatrixError(
                    f"{scenario_id} {step_id} additional_mutations must be a list"
                )

        expectations = scenario.get("expectations")
        if not isinstance(expectations, dict):
            raise TacticalScheduleMatrixError(
                f"{scenario_id} expectations must be an object"
            )
        for field in (
            "required_event_types_by_step",
            "forbidden_event_types_by_step",
            "required_blocked_reasons_by_step",
        ):
            mapping = _require_map_of_string_lists(
                expectations.get(field, {}), f"{scenario_id} {field}"
            )
            unknown = sorted(set(mapping) - seen_steps)
            if unknown:
                raise TacticalScheduleMatrixError(
                    f"{scenario_id} {field} references unknown steps: {unknown}"
                )
        for field in (
            "required_continuity_class_by_step",
            "required_active_plan_actor_by_step_and_objective",
        ):
            mapping = _require_string_map(
                expectations.get(field, {}), f"{scenario_id} {field}"
            )
            for key in mapping:
                step_id = key.split("::", 1)[0]
                if step_id not in seen_steps:
                    raise TacticalScheduleMatrixError(
                        f"{scenario_id} {field} references unknown step: {step_id}"
                    )
        _require_string_list(
            expectations.get("require_no_active_plans_by_step", []),
            f"{scenario_id} require_no_active_plans_by_step",
        )
        maximum = expectations.get("maximum_double_booked_active_actor_count", 0)
        if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 0:
            raise TacticalScheduleMatrixError(
                f"{scenario_id} maximum double-booked count must be nonnegative"
            )

    checks = suite.get("metamorphic_checks")
    if not isinstance(checks, list) or len(checks) < 3:
        raise TacticalScheduleMatrixError(
            "schedule suite requires at least three metamorphic checks"
        )
    seen_checks: set[str] = set()
    for check in checks:
        if not isinstance(check, dict):
            raise TacticalScheduleMatrixError("metamorphic check must be an object")
        check_id = _require_string(check.get("check_id"), "check_id")
        if check_id in seen_checks:
            raise TacticalScheduleMatrixError(f"duplicate check_id: {check_id}")
        seen_checks.add(check_id)
        scenario_id = _require_string(check.get("scenario_id"), f"{check_id} scenario")
        if scenario_id not in seen_scenarios:
            raise TacticalScheduleMatrixError(
                f"{check_id} references unknown scenario: {scenario_id}"
            )
        operation = check.get("operation")
        if operation not in _ALLOWED_METAMORPHIC_OPERATIONS:
            raise TacticalScheduleMatrixError(
                f"{check_id} unsupported operation: {operation}"
            )
        if operation == "TRANSLATE_ALL_POSITIONS":
            for axis in ("offset_x", "offset_z"):
                value = check.get(axis)
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise TacticalScheduleMatrixError(
                        f"{check_id} {axis} must be numeric"
                    )

    claimed = suite.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise TacticalScheduleMatrixError("invalid schedule suite result digest")
    payload = dict(suite)
    payload.pop("result_digest", None)
    if digest(payload) != claimed:
        raise TacticalScheduleMatrixError("schedule suite result digest mismatch")
    return suite


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


def _scenario_inputs(
    scenario: dict[str, Any],
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    *,
    operation: str | None = None,
    offset_x: float = 0.0,
    offset_z: float = 0.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    slices = {item["slice_id"]: item for item in trace_corpus["slices"]}
    baselines = {item["scenario_id"]: item for item in baseline_suite["scenarios"]}
    states: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    start_time = scenario.get("start_time_ms", 100_000)
    for step in scenario["steps"]:
        baseline = baselines[step["source_baseline_scenario_id"]]
        synthetic = build_synthetic_tactical_slice(
            slices[baseline["base_slice_id"]], baseline["mutations"]
        )
        if step.get("additional_mutations"):
            synthetic = build_synthetic_tactical_slice(
                synthetic, step["additional_mutations"]
            )
        synthetic = copy.deepcopy(synthetic)
        synthetic["time_ms"] = start_time + step["time_offset_ms"]
        if operation == "REVERSE_UNIT_ORDER":
            synthetic["units"] = list(reversed(synthetic["units"]))
        elif operation == "TRANSLATE_ALL_POSITIONS":
            synthetic = _translate_slice(synthetic, offset_x, offset_z)
        state = build_tactical_state(synthetic)
        portfolio = build_tactical_priority_portfolio(state)
        assignment = build_tactical_objective_assignment(state, portfolio)
        if operation == "REVERSE_ASSIGNMENT_RECORD_ORDER":
            assignment = copy.deepcopy(assignment)
            assignment["objectives"] = list(reversed(assignment["objectives"]))
            assignment["assignments"] = list(reversed(assignment["assignments"]))
            assignment.pop("result_digest", None)
            assignment["result_digest"] = digest(assignment)
        states.append(state)
        assignments.append(assignment)
    return states, assignments


def _contract_result(
    schedule: dict[str, Any], expectations: dict[str, Any], scenario: dict[str, Any]
) -> dict[str, Any]:
    by_step = {
        step["step_id"]: item
        for step, item in zip(
            scenario["steps"], schedule["schedule_slices"], strict=True
        )
    }
    mismatches: list[dict[str, Any]] = []
    for step_id, required in expectations.get(
        "required_event_types_by_step", {}
    ).items():
        observed = {event["event_type"] for event in by_step[step_id]["events"]}
        missing = sorted(set(required) - observed)
        if missing:
            mismatches.append(
                {
                    "field": "required_event_types",
                    "step_id": step_id,
                    "missing": missing,
                }
            )
    for step_id, forbidden in expectations.get(
        "forbidden_event_types_by_step", {}
    ).items():
        observed = {event["event_type"] for event in by_step[step_id]["events"]}
        present = sorted(set(forbidden) & observed)
        if present:
            mismatches.append(
                {
                    "field": "forbidden_event_types",
                    "step_id": step_id,
                    "present": present,
                }
            )
    for step_id, required in expectations.get(
        "required_blocked_reasons_by_step", {}
    ).items():
        observed = {
            item["reason"] for item in by_step[step_id]["blocked_assignments"]
        }
        missing = sorted(set(required) - observed)
        if missing:
            mismatches.append(
                {
                    "field": "required_blocked_reasons",
                    "step_id": step_id,
                    "missing": missing,
                }
            )
    for step_id, expected in expectations.get(
        "required_continuity_class_by_step", {}
    ).items():
        observed = by_step[step_id]["continuity_class"]
        if observed != expected:
            mismatches.append(
                {
                    "field": "continuity_class",
                    "step_id": step_id,
                    "expected": expected,
                    "observed": observed,
                }
            )
    for key, expected_actor in expectations.get(
        "required_active_plan_actor_by_step_and_objective", {}
    ).items():
        step_id, objective_id = key.split("::", 1)
        plans = {
            item["objective_id"]: item["actor_unit_id"]
            for item in by_step[step_id]["active_plans"]
        }
        observed_actor = plans.get(objective_id)
        if observed_actor != expected_actor:
            mismatches.append(
                {
                    "field": "active_plan_actor",
                    "step_id": step_id,
                    "objective_id": objective_id,
                    "expected": expected_actor,
                    "observed": observed_actor,
                }
            )
    for step_id in expectations.get("require_no_active_plans_by_step", []):
        if by_step[step_id]["active_plans"]:
            mismatches.append(
                {
                    "field": "active_plans",
                    "step_id": step_id,
                    "expected": [],
                    "observed_count": len(by_step[step_id]["active_plans"]),
                }
            )
    maximum = expectations.get("maximum_double_booked_active_actor_count", 0)
    observed_double = schedule["summary"]["double_booked_active_actor_count"]
    if observed_double > maximum:
        mismatches.append(
            {
                "field": "double_booked_active_actor_count",
                "expected_maximum": maximum,
                "observed": observed_double,
            }
        )
    return {"passed": not mismatches, "mismatches": mismatches}


def _semantic_signature(schedule: dict[str, Any]) -> dict[str, Any]:
    slices = []
    for item in schedule["schedule_slices"]:
        slices.append(
            {
                "sequence_index": item["sequence_index"],
                "continuity_class": item["continuity_class"],
                "events": sorted(
                    (
                        event["event_type"],
                        event["actor_unit_id"],
                        event["objective_id"],
                    )
                    for event in item["events"]
                ),
                "blocked": sorted(
                    (
                        blocked["objective_id"],
                        blocked["actor_unit_id"],
                        blocked["reason"],
                    )
                    for blocked in item["blocked_assignments"]
                ),
                "active": sorted(
                    (
                        plan["objective_id"],
                        plan["objective_type"],
                        plan["actor_unit_id"],
                        plan["observed_age_ms"],
                        plan["status"],
                    )
                    for plan in item["active_plans"]
                ),
            }
        )
    return {"slices": slices, "summary": schedule["summary"]}


def run_tactical_schedule_matrix(
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    schedule_suite: dict[str, Any],
) -> dict[str, Any]:
    trace_corpus = validate_battle_trace_slices(trace_corpus)
    baseline_suite = validate_tactical_baseline_suite(baseline_suite, trace_corpus)
    schedule_suite = validate_tactical_schedule_suite(
        schedule_suite, trace_corpus, baseline_suite
    )

    scenario_results = []
    contexts: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for scenario in schedule_suite["scenarios"]:
        states, assignments = _scenario_inputs(
            scenario, trace_corpus, baseline_suite
        )
        schedule = build_tactical_temporal_schedule(
            states,
            assignments,
            source_id=scenario["scenario_id"],
            evidence_status="CONTROL_SYNTHETIC",
        )
        contract = _contract_result(
            schedule, scenario["expectations"], scenario
        )
        record = {
            "scenario_id": scenario["scenario_id"],
            "schedule": schedule,
            "contract": contract,
            "authority": "NO_ORDERS",
        }
        record["result_digest"] = digest(record)
        scenario_results.append(record)
        contexts[scenario["scenario_id"]] = (scenario, schedule)

    metamorphic_results = []
    for check in schedule_suite["metamorphic_checks"]:
        scenario, baseline_schedule = contexts[check["scenario_id"]]
        operation = check["operation"]
        states, assignments = _scenario_inputs(
            scenario,
            trace_corpus,
            baseline_suite,
            operation=operation,
            offset_x=float(check.get("offset_x", 0.0)),
            offset_z=float(check.get("offset_z", 0.0)),
        )
        transformed = build_tactical_temporal_schedule(
            states,
            assignments,
            source_id=scenario["scenario_id"],
            evidence_status="CONTROL_SYNTHETIC",
        )
        passed = _semantic_signature(transformed) == _semantic_signature(
            baseline_schedule
        )
        record = {
            "check_id": check["check_id"],
            "scenario_id": check["scenario_id"],
            "operation": operation,
            "passed": passed,
            "comparison": "SEMANTIC_SCHEDULE_EQUIVALENCE",
            "baseline_semantic_digest": digest(
                _semantic_signature(baseline_schedule)
            ),
            "transformed_semantic_digest": digest(_semantic_signature(transformed)),
            "authority": "NO_ORDERS",
        }
        record["result_digest"] = digest(record)
        metamorphic_results.append(record)

    result: dict[str, Any] = {
        "schema_version": 1,
        "output_contract": OUTPUT_CONTRACT,
        "suite_id": schedule_suite["suite_id"],
        "seed": schedule_suite["seed"],
        "source_trace_digest": trace_corpus["result_digest"],
        "source_baseline_suite_digest": baseline_suite["result_digest"],
        "source_schedule_suite_digest": schedule_suite["result_digest"],
        "scenario_count": len(scenario_results),
        "scenario_pass_count": sum(
            item["contract"]["passed"] for item in scenario_results
        ),
        "metamorphic_check_count": len(metamorphic_results),
        "metamorphic_pass_count": sum(
            item["passed"] for item in metamorphic_results
        ),
        "scenario_results": scenario_results,
        "metamorphic_results": metamorphic_results,
        "gate_measurements": {
            "scenario_contract_pass_count": sum(
                item["contract"]["passed"] for item in scenario_results
            ),
            "metamorphic_check_pass_count": sum(
                item["passed"] for item in metamorphic_results
            ),
            "all_scenarios_passed": all(
                item["contract"]["passed"] for item in scenario_results
            ),
            "all_metamorphic_checks_passed": all(
                item["passed"] for item in metamorphic_results
            ),
            "all_outputs_no_orders": all(
                item["schedule"]["authority"] == "NO_ORDERS"
                for item in scenario_results
            ),
            "double_booked_active_actor_count": sum(
                item["schedule"]["summary"]["double_booked_active_actor_count"]
                for item in scenario_results
            ),
            "total_plan_start_count": sum(
                item["schedule"]["summary"]["plan_start_count"]
                for item in scenario_results
            ),
            "total_plan_continue_count": sum(
                item["schedule"]["summary"]["plan_continue_count"]
                for item in scenario_results
            ),
            "total_plan_retained_count": sum(
                item["schedule"]["summary"]["plan_retained_count"]
                for item in scenario_results
            ),
            "total_cooldown_block_count": sum(
                item["schedule"]["summary"]["cooldown_block_count"]
                for item in scenario_results
            ),
            "total_continuity_reset_count": sum(
                item["schedule"]["summary"]["continuity_reset_count"]
                for item in scenario_results
            ),
        },
        "interpretation_limits": list(schedule_suite["interpretation_limits"]),
        "evidence_status": "CONTROL_SYNTHETIC",
        "counterfactual_status": "UNVERIFIED",
        "authority": "NO_ORDERS",
    }
    result["result_digest"] = digest(result)
    return result
