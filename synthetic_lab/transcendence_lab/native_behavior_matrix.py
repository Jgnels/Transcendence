from __future__ import annotations

from copy import deepcopy
from typing import Any

from .canonical import digest
from .native_behavior import NativeBehaviorError, analyze_native_behavior_trace

CONTRACT = "NATIVE_CAI_BEHAVIOR_ADVERSARIAL_MATRIX_V1"


def _assert_expectations(result: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    metrics = result["metrics"]
    for key, value in expected.get("metric_equals", {}).items():
        if metrics.get(key) != value:
            failures.append(f"{key}: expected {value!r}, got {metrics.get(key)!r}")
    for key, value in expected.get("metric_max", {}).items():
        actual = metrics.get(key)
        if actual is None or actual > value:
            failures.append(f"{key}: expected <= {value!r}, got {actual!r}")
    for key, value in expected.get("metric_min", {}).items():
        actual = metrics.get(key)
        if actual is None or actual < value:
            failures.append(f"{key}: expected >= {value!r}, got {actual!r}")
    if expected.get("assignment_exclusivity_unavailable") and result["assignment_exclusivity_visibility"] != "UNAVAILABLE_FROM_TRAJECTORY_ONLY":
        failures.append("assignment exclusivity was overclaimed")
    return failures


def run_native_behavior_adversarial_matrix(suite: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(suite, dict) or not isinstance(suite.get("cases"), list):
        raise NativeBehaviorError("native behavior matrix suite must contain cases")
    case_results = []
    pass_count = 0
    for case in suite["cases"]:
        case_id = case["case_id"]
        try:
            result = analyze_native_behavior_trace(deepcopy(case["trace"]))
            failures = _assert_expectations(result, case.get("expected", {}))
            passed = not failures
            if passed:
                pass_count += 1
            case_results.append(
                {
                    "case_id": case_id,
                    "passed": passed,
                    "failures": failures,
                    "result_digest": result["result_digest"],
                    "metrics": result["metrics"],
                    "assignment_exclusivity_visibility": result["assignment_exclusivity_visibility"],
                }
            )
        except Exception as exc:
            case_results.append({"case_id": case_id, "passed": False, "failures": [f"{type(exc).__name__}: {exc}"]})
    output = {
        "contract": CONTRACT,
        "case_count": len(case_results),
        "pass_count": pass_count,
        "all_passed": pass_count == len(case_results),
        "case_results": case_results,
    }
    output["result_digest"] = digest(output)
    return output
