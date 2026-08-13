from __future__ import annotations

import copy
from typing import Any

from .canonical import digest
from .tactical_feasibility import TacticalFeasibilityError, build_tactical_feasibility_envelope
from .tactical_feasibility_matrix import (
    _build_state_schedule,
    _evidence_for_mode,
    validate_tactical_feasibility_suite,
)
from .tactical_guarded import (
    TacticalGuardedActionError,
    build_guarded_action_packet_set,
)


SUITE_CONTRACT = "TACTICAL_GUARDED_ACTION_MATRIX_V1"
REPORT_CONTRACT = "TACTICAL_GUARDED_ACTION_MATRIX_REPORT_V1"
_ALLOWED_METAMORPHIC = {
    "REVERSE_UNIT_ORDER",
    "TRANSLATE_ALL_POSITIONS",
    "REVERSE_QUERY_RESULT_ORDER",
}


class TacticalGuardedMatrixError(ValueError):
    pass


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TacticalGuardedMatrixError(f"{label} must be nonempty text")
    return value


def _text_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise TacticalGuardedMatrixError(f"{label} must be a string list")
    if len(value) != len(set(value)):
        raise TacticalGuardedMatrixError(f"{label} must be unique")
    return value


def validate_tactical_guarded_suite(
    suite: dict[str, Any],
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    feasibility_suite: dict[str, Any],
) -> dict[str, Any]:
    feasibility_suite = validate_tactical_feasibility_suite(
        feasibility_suite, trace_corpus, baseline_suite
    )
    if not isinstance(suite, dict) or suite.get("schema_version") != 1:
        raise TacticalGuardedMatrixError("unsupported guarded suite schema")
    if suite.get("suite_contract") != SUITE_CONTRACT:
        raise TacticalGuardedMatrixError("unsupported guarded suite contract")
    _text(suite.get("suite_id"), "suite_id")
    if not isinstance(suite.get("seed"), int) or isinstance(suite.get("seed"), bool):
        raise TacticalGuardedMatrixError("seed must be integer")
    if suite.get("evidence_status") != "CONTROL_SYNTHETIC":
        raise TacticalGuardedMatrixError("guarded suite must be CONTROL_SYNTHETIC")
    if suite.get("source_trace_digest") != trace_corpus["result_digest"]:
        raise TacticalGuardedMatrixError("guarded suite source trace mismatch")
    if suite.get("source_baseline_suite_digest") != baseline_suite["result_digest"]:
        raise TacticalGuardedMatrixError("guarded suite baseline mismatch")
    if suite.get("source_feasibility_suite_digest") != feasibility_suite["result_digest"]:
        raise TacticalGuardedMatrixError("guarded suite feasibility-suite mismatch")
    limits = _text_list(suite.get("interpretation_limits"), "interpretation_limits")
    if not any("order" in item.lower() and "not" in item.lower() for item in limits):
        raise TacticalGuardedMatrixError("guarded suite must disclaim order authority")

    source_by_id = {item["scenario_id"]: item for item in feasibility_suite["scenarios"]}
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 12:
        raise TacticalGuardedMatrixError("at least twelve guarded scenarios are required")
    seen: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise TacticalGuardedMatrixError("guarded scenario must be object")
        scenario_id = _text(scenario.get("scenario_id"), "scenario_id")
        if scenario_id in seen:
            raise TacticalGuardedMatrixError("duplicate guarded scenario_id")
        seen.add(scenario_id)
        source_id = _text(scenario.get("source_feasibility_scenario_id"), "source scenario")
        if source_id not in source_by_id:
            raise TacticalGuardedMatrixError("unknown source feasibility scenario")
        expectations = scenario.get("expectations")
        if not isinstance(expectations, dict):
            raise TacticalGuardedMatrixError("guarded expectations must be object")
        _text_list(expectations.get("required_readiness_classes", []), "required readiness")
        _text_list(expectations.get("forbidden_readiness_classes", []), "forbidden readiness")
        for name in ("minimum_ready", "minimum_blocked", "minimum_deferred"):
            value = expectations.get(name, 0)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise TacticalGuardedMatrixError(f"{name} must be nonnegative integer")
        if type(expectations.get("expect_error", False)) is not bool:
            raise TacticalGuardedMatrixError("expect_error must be boolean")

    checks = suite.get("metamorphic_checks")
    if not isinstance(checks, list) or len(checks) < 3:
        raise TacticalGuardedMatrixError("at least three guarded metamorphic checks required")
    check_ids: set[str] = set()
    for check in checks:
        if not isinstance(check, dict):
            raise TacticalGuardedMatrixError("metamorphic check must be object")
        check_id = _text(check.get("check_id"), "check_id")
        if check_id in check_ids:
            raise TacticalGuardedMatrixError("duplicate guarded check_id")
        check_ids.add(check_id)
        if check.get("operation") not in _ALLOWED_METAMORPHIC:
            raise TacticalGuardedMatrixError("unsupported guarded metamorphic operation")
        if check.get("scenario_id") not in seen:
            raise TacticalGuardedMatrixError("guarded metamorphic scenario unknown")

    material = dict(suite)
    claimed = material.pop("result_digest", None)
    if claimed != digest(material):
        raise TacticalGuardedMatrixError("guarded suite result_digest mismatch")
    return suite


def _source_scenario(
    scenario: dict[str, Any], feasibility_suite: dict[str, Any]
) -> dict[str, Any]:
    return next(
        item
        for item in feasibility_suite["scenarios"]
        if item["scenario_id"] == scenario["source_feasibility_scenario_id"]
    )


def _run_case(
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    feasibility_suite: dict[str, Any],
    scenario: dict[str, Any],
    *,
    reverse_units: bool = False,
    translation: tuple[float, float, float] | None = None,
    reverse_query_results: bool = False,
) -> dict[str, Any]:
    source = _source_scenario(scenario, feasibility_suite)
    state, schedule = _build_state_schedule(
        trace_corpus,
        baseline_suite,
        source,
        reverse_units=reverse_units,
        translation=translation,
    )
    base = build_tactical_feasibility_envelope(state, schedule)
    mode = source["query_mode"]
    evidence = _evidence_for_mode(mode, state, schedule, base)
    if mode == "STALE_STATE_DIGEST":
        from .tactical_feasibility import build_point_query_evidence
        evidence = build_point_query_evidence(
            state, schedule, [], evidence_source="CONTROL_SYNTHETIC_FIXTURE"
        )
        evidence["source_tactical_state_digest"] = "0" * 64
        evidence.pop("result_digest", None)
        evidence["result_digest"] = digest(evidence)
    elif mode == "ALTERED_AUTHORITY":
        from .tactical_feasibility import build_point_query_evidence
        evidence = build_point_query_evidence(
            state, schedule, [], evidence_source="CONTROL_SYNTHETIC_FIXTURE"
        )
        evidence["authority"] = "CONTROL"
        evidence.pop("result_digest", None)
        evidence["result_digest"] = digest(evidence)
    if reverse_query_results and evidence is not None:
        evidence = copy.deepcopy(evidence)
        evidence["candidate_results"] = list(reversed(evidence["candidate_results"]))
        evidence.pop("result_digest", None)
        evidence["result_digest"] = digest(evidence)
    decorated = build_tactical_feasibility_envelope(
        state,
        schedule,
        point_query_evidence=evidence,
    )
    return build_guarded_action_packet_set(state, schedule, decorated)


def _signature(packet_set: dict[str, Any]) -> dict[str, Any]:
    return {
        "packet_count": packet_set["packet_count"],
        "ready_packet_count": packet_set["ready_packet_count"],
        "blocked_packet_count": packet_set["blocked_packet_count"],
        "deferred_packet_count": packet_set["deferred_packet_count"],
        "packets": sorted(
            [
                {
                    "objective_type": item["objective_type"],
                    "actor_role": item["actor_role"],
                    "severity": item["severity"],
                    "readiness_class": item["readiness_class"],
                    "eligible_candidate_count": item["eligible_candidate_count"],
                    "selected_candidate_rank": item["selected_candidate_rank"],
                }
                for item in packet_set["packets"]
            ],
            key=lambda item: (
                item["objective_type"],
                item["actor_role"],
                item["severity"],
                item["readiness_class"],
            ),
        ),
    }


def run_tactical_guarded_matrix(
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    feasibility_suite: dict[str, Any],
    guarded_suite: dict[str, Any],
) -> dict[str, Any]:
    guarded_suite = validate_tactical_guarded_suite(
        guarded_suite, trace_corpus, baseline_suite, feasibility_suite
    )
    results: list[dict[str, Any]] = []
    passed = 0
    for scenario in guarded_suite["scenarios"]:
        error: str | None = None
        output: dict[str, Any] | None = None
        try:
            output = _run_case(trace_corpus, baseline_suite, feasibility_suite, scenario)
        except (TacticalFeasibilityError, TacticalGuardedActionError, ValueError, KeyError) as exc:
            error = str(exc)
        expectations = scenario["expectations"]
        classes = sorted((output or {}).get("readiness_class_counts", {}).keys())
        checks = {
            "error_expectation": (error is not None) is expectations.get("expect_error", False),
            "required_readiness": all(item in classes for item in expectations.get("required_readiness_classes", [])),
            "forbidden_readiness": all(item not in classes for item in expectations.get("forbidden_readiness_classes", [])),
            "minimum_ready": int((output or {}).get("ready_packet_count", 0)) >= expectations.get("minimum_ready", 0),
            "minimum_blocked": int((output or {}).get("blocked_packet_count", 0)) >= expectations.get("minimum_blocked", 0),
            "minimum_deferred": int((output or {}).get("deferred_packet_count", 0)) >= expectations.get("minimum_deferred", 0),
            "authority_prohibited": output is None or (
                output.get("authority") == "NO_ORDERS"
                and output.get("application_authority") == "PROHIBITED"
                and all(item["application_status"] == "PROHIBITED_NO_ORDER_AUTHORITY" for item in output["packets"])
            ),
            "no_execution_claim": output is None or all(
                item["project_issue_status"] == "NOT_ATTEMPTED"
                and item["execution_status"] == "NOT_ISSUED"
                and item["direct_acknowledgement_status"] == "UNAVAILABLE_NOT_OBSERVED"
                for item in output["packets"]
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
                "readiness_classes": classes,
                "packet_count": int((output or {}).get("packet_count", 0)),
                "ready_packet_count": int((output or {}).get("ready_packet_count", 0)),
                "blocked_packet_count": int((output or {}).get("blocked_packet_count", 0)),
                "deferred_packet_count": int((output or {}).get("deferred_packet_count", 0)),
                "result_digest": output.get("result_digest") if output else None,
            }
        )

    by_id = {item["scenario_id"]: item for item in guarded_suite["scenarios"]}
    metamorphic: list[dict[str, Any]] = []
    for check in guarded_suite["metamorphic_checks"]:
        scenario = by_id[check["scenario_id"]]
        base = _run_case(trace_corpus, baseline_suite, feasibility_suite, scenario)
        operation = check["operation"]
        if operation == "REVERSE_UNIT_ORDER":
            transformed = _run_case(
                trace_corpus, baseline_suite, feasibility_suite, scenario, reverse_units=True
            )
        elif operation == "TRANSLATE_ALL_POSITIONS":
            transformed = _run_case(
                trace_corpus,
                baseline_suite,
                feasibility_suite,
                scenario,
                translation=(773.0, 11.0, -419.0),
            )
        else:
            transformed = _run_case(
                trace_corpus,
                baseline_suite,
                feasibility_suite,
                scenario,
                reverse_query_results=True,
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
        "suite_id": guarded_suite["suite_id"],
        "seed": guarded_suite["seed"],
        "scenario_count": len(results),
        "scenario_pass_count": passed,
        "metamorphic_check_count": len(metamorphic),
        "metamorphic_pass_count": sum(item["passed"] for item in metamorphic),
        "scenarios": results,
        "metamorphic_checks": metamorphic,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_SYNTHETIC",
        "interpretation_limits": [
            "Synthetic QUERY_TRUE fixtures prove guarded contract behavior, not live point feasibility.",
            "A ready packet is eligible only for simultaneous shadow review and cannot issue an order.",
            "No route, formation, collision, legality, acknowledgement, execution, or outcome is established.",
        ],
    }
    report["result_digest"] = digest(report)
    return report
