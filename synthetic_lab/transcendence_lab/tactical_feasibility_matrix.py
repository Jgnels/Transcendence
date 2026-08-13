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
from .tactical_feasibility import (
    TacticalFeasibilityError,
    build_point_query_evidence,
    build_tactical_feasibility_envelope,
)
from .tactical_schedule import build_tactical_temporal_schedule
from .tactical_state import build_tactical_state


SUITE_CONTRACT = "TACTICAL_FEASIBILITY_MATRIX_V1"
REPORT_CONTRACT = "TACTICAL_FEASIBILITY_MATRIX_REPORT_V1"
_ALLOWED_QUERY_MODES = {
    "NONE",
    "ALL_TRUE",
    "ALL_FALSE",
    "ALL_UNAVAILABLE",
    "FIRST_TRUE_REST_FALSE",
    "FORGED_CANDIDATE",
    "STALE_STATE_DIGEST",
    "ALTERED_AUTHORITY",
}
_ALLOWED_METAMORPHIC = {
    "REVERSE_UNIT_ORDER",
    "TRANSLATE_ALL_POSITIONS",
    "REVERSE_QUERY_RESULT_ORDER",
}


class TacticalFeasibilityMatrixError(ValueError):
    pass


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TacticalFeasibilityMatrixError(f"{label} must be nonempty text")
    return value


def _require_text_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise TacticalFeasibilityMatrixError(f"{label} must be a string list")
    if len(value) != len(set(value)):
        raise TacticalFeasibilityMatrixError(f"{label} must be unique")
    return value


def validate_tactical_feasibility_suite(
    suite: dict[str, Any],
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
) -> dict[str, Any]:
    trace_corpus = validate_battle_trace_slices(trace_corpus)
    baseline_suite = validate_tactical_baseline_suite(baseline_suite, trace_corpus)
    if not isinstance(suite, dict):
        raise TacticalFeasibilityMatrixError("feasibility suite must be an object")
    if suite.get("schema_version") != 1:
        raise TacticalFeasibilityMatrixError("unsupported feasibility suite schema")
    if suite.get("suite_contract") != SUITE_CONTRACT:
        raise TacticalFeasibilityMatrixError("unsupported feasibility suite contract")
    _require_text(suite.get("suite_id"), "suite_id")
    if not isinstance(suite.get("seed"), int) or isinstance(suite.get("seed"), bool):
        raise TacticalFeasibilityMatrixError("seed must be an integer")
    if suite.get("evidence_status") != "CONTROL_SYNTHETIC":
        raise TacticalFeasibilityMatrixError("feasibility suite must be CONTROL_SYNTHETIC")
    if suite.get("source_trace_digest") != trace_corpus["result_digest"]:
        raise TacticalFeasibilityMatrixError("feasibility suite source trace mismatch")
    if suite.get("source_baseline_suite_digest") != baseline_suite["result_digest"]:
        raise TacticalFeasibilityMatrixError("feasibility suite source baseline mismatch")
    limits = _require_text_list(suite.get("interpretation_limits"), "interpretation_limits")
    if not any("route" in item.lower() and "not" in item.lower() for item in limits):
        raise TacticalFeasibilityMatrixError("suite must disclaim route proof")

    known = {item["scenario_id"] for item in baseline_suite["scenarios"]}
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 12:
        raise TacticalFeasibilityMatrixError("at least twelve feasibility scenarios are required")
    seen: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise TacticalFeasibilityMatrixError("scenario must be an object")
        scenario_id = _require_text(scenario.get("scenario_id"), "scenario_id")
        if scenario_id in seen:
            raise TacticalFeasibilityMatrixError(f"duplicate scenario_id: {scenario_id}")
        seen.add(scenario_id)
        baseline_id = _require_text(scenario.get("source_baseline_scenario_id"), f"{scenario_id} baseline")
        if baseline_id not in known:
            raise TacticalFeasibilityMatrixError(f"unknown baseline scenario: {baseline_id}")
        mode = scenario.get("query_mode")
        if mode not in _ALLOWED_QUERY_MODES:
            raise TacticalFeasibilityMatrixError(f"unsupported query mode: {mode}")
        if not isinstance(scenario.get("additional_mutations", []), list):
            raise TacticalFeasibilityMatrixError("additional_mutations must be a list")
        expectations = scenario.get("expectations")
        if not isinstance(expectations, dict):
            raise TacticalFeasibilityMatrixError("scenario expectations must be an object")
        _require_text_list(expectations.get("required_feasibility_classes", []), "required classes")
        _require_text_list(expectations.get("forbidden_feasibility_classes", []), "forbidden classes")
        expect_error = expectations.get("expect_error", False)
        if type(expect_error) is not bool:
            raise TacticalFeasibilityMatrixError("expect_error must be boolean")
        minimum = expectations.get("minimum_candidate_count", 0)
        if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 0:
            raise TacticalFeasibilityMatrixError("minimum_candidate_count must be nonnegative")

    checks = suite.get("metamorphic_checks")
    if not isinstance(checks, list) or len(checks) < 3:
        raise TacticalFeasibilityMatrixError("at least three metamorphic checks are required")
    check_ids: set[str] = set()
    for check in checks:
        if not isinstance(check, dict):
            raise TacticalFeasibilityMatrixError("metamorphic check must be an object")
        check_id = _require_text(check.get("check_id"), "check_id")
        if check_id in check_ids:
            raise TacticalFeasibilityMatrixError(f"duplicate check_id: {check_id}")
        check_ids.add(check_id)
        if check.get("operation") not in _ALLOWED_METAMORPHIC:
            raise TacticalFeasibilityMatrixError("unsupported metamorphic operation")
        if check.get("scenario_id") not in seen:
            raise TacticalFeasibilityMatrixError("metamorphic check references unknown scenario")

    claimed = suite.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise TacticalFeasibilityMatrixError("suite result_digest invalid")
    material = dict(suite)
    material.pop("result_digest", None)
    if digest(material) != claimed:
        raise TacticalFeasibilityMatrixError("suite result_digest mismatch")
    return suite


def _build_state_schedule(
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    scenario: dict[str, Any],
    *,
    reverse_units: bool = False,
    translation: tuple[float, float, float] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    baseline_by_id = {item["scenario_id"]: item for item in baseline_suite["scenarios"]}
    source = baseline_by_id[scenario["source_baseline_scenario_id"]]
    trace_by_id = {item["slice_id"]: item for item in trace_corpus["slices"]}
    mutations = list(source.get("mutations", [])) + list(scenario.get("additional_mutations", []))
    slice_record = build_synthetic_tactical_slice(trace_by_id[source["base_slice_id"]], mutations)
    slice_record = copy.deepcopy(slice_record)
    if source["base_slice_id"] != "battle_complete":
        slice_record["slice_id"] = f"v01t_{scenario['scenario_id']}"
    slice_record["time_ms"] = 100_000
    if translation is not None:
        dx, dy, dz = translation
        for unit in slice_record["units"]:
            unit["position_x"] += dx
            unit["position_y"] += dy
            unit["position_z"] += dz
            unit["ordered_position_x"] += dx
            unit["ordered_position_y"] += dy
            unit["ordered_position_z"] += dz
    if reverse_units:
        slice_record["units"] = list(reversed(slice_record["units"]))
    state = build_tactical_state(slice_record)
    assignment = build_tactical_objective_assignment(state)
    schedule = build_tactical_temporal_schedule(
        [state],
        [assignment],
        source_id=f"V01T_SYNTHETIC_{scenario['scenario_id']}",
        evidence_status="CONTROL_SYNTHETIC",
    )["schedule_slices"][0]
    return state, schedule


def _evidence_for_mode(
    mode: str,
    state: dict[str, Any],
    schedule: dict[str, Any],
    envelope: dict[str, Any],
) -> dict[str, Any] | None:
    candidate_ids = [
        candidate["candidate_id"]
        for plan in envelope["plan_envelopes"]
        for candidate in plan["candidate_points"]
    ]
    if mode == "NONE":
        return None
    if mode == "FORGED_CANDIDATE":
        records = [{"candidate_id": "f" * 64, "query_result": "QUERY_TRUE"}]
    elif mode == "ALL_TRUE":
        records = [{"candidate_id": item, "query_result": "QUERY_TRUE"} for item in candidate_ids]
    elif mode == "ALL_FALSE":
        records = [{"candidate_id": item, "query_result": "QUERY_FALSE"} for item in candidate_ids]
    elif mode == "ALL_UNAVAILABLE":
        records = [{"candidate_id": item, "query_result": "UNAVAILABLE"} for item in candidate_ids]
    elif mode == "FIRST_TRUE_REST_FALSE":
        records = [
            {"candidate_id": item, "query_result": "QUERY_TRUE" if index == 0 else "QUERY_FALSE"}
            for index, item in enumerate(candidate_ids)
        ]
    else:
        return None
    evidence = build_point_query_evidence(
        state,
        schedule,
        records,
        evidence_source="CONTROL_SYNTHETIC_FIXTURE",
    )
    if mode == "STALE_STATE_DIGEST":
        evidence["source_tactical_state_digest"] = "0" * 64
        evidence.pop("result_digest", None)
        evidence["result_digest"] = digest(evidence)
    if mode == "ALTERED_AUTHORITY":
        evidence["authority"] = "CONTROL"
        evidence.pop("result_digest", None)
        evidence["result_digest"] = digest(evidence)
    return evidence


def _semantic_signature(result: dict[str, Any]) -> dict[str, Any]:
    plans = []
    for plan in result["plan_envelopes"]:
        plans.append(
            {
                "objective_type": plan["objective_type"],
                "actor_role": plan["actor_role"],
                "candidate_count": plan["candidate_count"],
                "feasibility_class": plan["feasibility_class"],
                "candidate_shapes": [
                    {
                        "rank": candidate["rank"],
                        "strategy": candidate["strategy"],
                        "horizontal_displacement_m": candidate["horizontal_displacement_m"],
                        "query_result": candidate["query_result"],
                        "candidate_status": candidate["candidate_status"],
                    }
                    for candidate in plan["candidate_points"]
                ],
            }
        )
    return {
        "active_plan_count": result["active_plan_count"],
        "candidate_point_count": result["candidate_point_count"],
        "plans": sorted(plans, key=lambda item: (item["objective_type"], item["actor_role"])),
    }


def _run_case(
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    scenario: dict[str, Any],
    *,
    reverse_units: bool = False,
    translation: tuple[float, float, float] | None = None,
    reverse_query_results: bool = False,
) -> dict[str, Any]:
    state, schedule = _build_state_schedule(
        trace_corpus,
        baseline_suite,
        scenario,
        reverse_units=reverse_units,
        translation=translation,
    )
    initial = build_tactical_feasibility_envelope(state, schedule)
    mode = scenario["query_mode"]
    evidence = _evidence_for_mode(mode, state, schedule, initial)
    if mode == "STALE_STATE_DIGEST":
        evidence = build_point_query_evidence(
            state,
            schedule,
            [],
            evidence_source="CONTROL_SYNTHETIC_FIXTURE",
        )
        evidence["source_tactical_state_digest"] = "0" * 64
        evidence.pop("result_digest", None)
        evidence["result_digest"] = digest(evidence)
    elif mode == "ALTERED_AUTHORITY":
        evidence = build_point_query_evidence(
            state,
            schedule,
            [],
            evidence_source="CONTROL_SYNTHETIC_FIXTURE",
        )
        evidence["authority"] = "CONTROL"
        evidence.pop("result_digest", None)
        evidence["result_digest"] = digest(evidence)
    if reverse_query_results and evidence is not None:
        evidence = copy.deepcopy(evidence)
        evidence["candidate_results"] = list(reversed(evidence["candidate_results"]))
        evidence.pop("result_digest", None)
        evidence["result_digest"] = digest(evidence)
    return build_tactical_feasibility_envelope(
        state,
        schedule,
        point_query_evidence=evidence,
    )


def run_tactical_feasibility_matrix(
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    suite: dict[str, Any],
) -> dict[str, Any]:
    suite = validate_tactical_feasibility_suite(suite, trace_corpus, baseline_suite)
    results: list[dict[str, Any]] = []
    passed = 0
    for scenario in suite["scenarios"]:
        expectations = scenario["expectations"]
        error: str | None = None
        output: dict[str, Any] | None = None
        try:
            output = _run_case(trace_corpus, baseline_suite, scenario)
        except (TacticalFeasibilityError, KeyError, ValueError) as exc:
            error = str(exc)
        classes = sorted(
            {
                item["feasibility_class"]
                for item in (output or {}).get("plan_envelopes", [])
            }
        )
        candidate_count = int((output or {}).get("candidate_point_count", 0))
        expect_error = expectations.get("expect_error", False)
        checks = {
            "error_expectation": (error is not None) is expect_error,
            "required_classes": all(item in classes for item in expectations.get("required_feasibility_classes", [])),
            "forbidden_classes": all(item not in classes for item in expectations.get("forbidden_feasibility_classes", [])),
            "minimum_candidate_count": candidate_count >= expectations.get("minimum_candidate_count", 0),
            "authority_no_orders": output is None or output.get("authority") == "NO_ORDERS",
            "no_acknowledgement_or_execution_claim": output is None or all(
                plan["direct_acknowledgement_status"] == "UNAVAILABLE_NOT_OBSERVED"
                and plan["project_issue_status"] == "NOT_ATTEMPTED"
                for plan in output["plan_envelopes"]
            ),
        }
        case_passed = all(checks.values())
        passed += int(case_passed)
        results.append(
            {
                "scenario_id": scenario["scenario_id"],
                "passed": case_passed,
                "checks": checks,
                "error": error,
                "feasibility_classes": classes,
                "candidate_point_count": candidate_count,
                "result_digest": output.get("result_digest") if output else None,
            }
        )

    by_id = {item["scenario_id"]: item for item in suite["scenarios"]}
    metamorphic_results: list[dict[str, Any]] = []
    for check in suite["metamorphic_checks"]:
        scenario = by_id[check["scenario_id"]]
        base = _run_case(trace_corpus, baseline_suite, scenario)
        operation = check["operation"]
        if operation == "REVERSE_UNIT_ORDER":
            transformed = _run_case(trace_corpus, baseline_suite, scenario, reverse_units=True)
        elif operation == "TRANSLATE_ALL_POSITIONS":
            transformed = _run_case(
                trace_corpus,
                baseline_suite,
                scenario,
                translation=(431.0, 17.0, -283.0),
            )
        else:
            transformed = _run_case(
                trace_corpus,
                baseline_suite,
                scenario,
                reverse_query_results=True,
            )
        passed_check = _semantic_signature(base) == _semantic_signature(transformed)
        metamorphic_results.append(
            {
                "check_id": check["check_id"],
                "operation": operation,
                "passed": passed_check,
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
        "metamorphic_check_count": len(metamorphic_results),
        "metamorphic_pass_count": sum(item["passed"] for item in metamorphic_results),
        "scenarios": results,
        "metamorphic_checks": metamorphic_results,
        "authority": "NO_ORDERS",
        "evidence_status": "CONTROL_SYNTHETIC",
        "interpretation_limits": [
            "The matrix tests project-owned geometry and query semantics, not WH3 route or formation feasibility.",
            "Synthetic QUERY_TRUE records are fixtures and do not establish live candidate reachability.",
            "No scenario issues an order or claims acknowledgement, execution, arrival, or outcome.",
        ],
    }
    report["result_digest"] = digest(report)
    return report
