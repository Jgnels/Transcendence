from __future__ import annotations

from copy import deepcopy
from typing import Any

from .canonical import digest
from .native_churn import NativeChurnError, analyze_visible_directional_churn

CONTRACT = "NATIVE_CAI_VISIBLE_DIRECTIONAL_CHURN_ADVERSARIAL_MATRIX_V1"


def _expect(result: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if "status" in expected and result.get("status") != expected["status"]:
        failures.append(f"status: expected {expected['status']!r}, got {result.get('status')!r}")
    metrics = result.get("metrics", {})
    for key, value in expected.get("metric_equals", {}).items():
        if metrics.get(key) != value:
            failures.append(f"{key}: expected {value!r}, got {metrics.get(key)!r}")
    for key, value in expected.get("metric_min", {}).items():
        actual = metrics.get(key)
        if actual is None or actual < value:
            failures.append(f"{key}: expected >= {value!r}, got {actual!r}")
    if expected.get("hysteresis_unavailable") and result.get("availability", {}).get("native_hysteresis") != "UNAVAILABLE_ENGINE_INTERNAL":
        failures.append("native hysteresis was overclaimed")
    if expected.get("no_application_authority") and result.get("application_authority") != "PROHIBITED":
        failures.append("application authority was promoted")
    return failures


def run_native_churn_adversarial_matrix(suite: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(suite, dict) or not isinstance(suite.get("cases"), list):
        raise NativeChurnError("native churn matrix suite must contain cases")
    case_results: list[dict[str, Any]] = []
    pass_count = 0
    for case in suite["cases"]:
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise NativeChurnError("native churn matrix case_id must be a nonempty string")
        expect_error = case.get("expect_error")
        try:
            result = analyze_visible_directional_churn(deepcopy(case["trace"]))
            if expect_error:
                failures = [f"expected error {expect_error!r}, analysis succeeded"]
            else:
                failures = _expect(result, case.get("expected", {}))
            passed = not failures
            if passed:
                pass_count += 1
            case_results.append(
                {
                    "case_id": case_id,
                    "passed": passed,
                    "failures": failures,
                    "result_digest": result.get("result_digest"),
                    "status": result.get("status"),
                    "metrics": result.get("metrics"),
                }
            )
        except Exception as exc:
            if expect_error and type(exc).__name__ == expect_error:
                pass_count += 1
                case_results.append(
                    {
                        "case_id": case_id,
                        "passed": True,
                        "failures": [],
                        "observed_error": type(exc).__name__,
                    }
                )
            else:
                case_results.append(
                    {
                        "case_id": case_id,
                        "passed": False,
                        "failures": [f"{type(exc).__name__}: {exc}"],
                    }
                )
    output: dict[str, Any] = {
        "contract": CONTRACT,
        "case_count": len(case_results),
        "pass_count": pass_count,
        "all_passed": pass_count == len(case_results),
        "case_results": case_results,
    }
    output["result_digest"] = digest(output)
    return output
