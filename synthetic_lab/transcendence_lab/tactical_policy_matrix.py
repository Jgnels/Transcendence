from __future__ import annotations

import copy
from typing import Any

from .canonical import digest
from .tactical_policy import (
    TacticalPolicyError,
    evaluate_tactical_policy,
    validate_cross_corpus_policy_envelope,
)

SUITE_CONTRACT = "TACTICAL_POLICY_ADVERSARIAL_SUITE_V1"
REPORT_CONTRACT = "TACTICAL_POLICY_ADVERSARIAL_REPORT_V1"


class TacticalPolicyMatrixError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TacticalPolicyMatrixError(message)


def validate_tactical_policy_suite(value: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, dict), "policy suite must be an object")
    claimed = value.get("result_digest")
    payload = copy.deepcopy(value)
    payload.pop("result_digest", None)
    _require(isinstance(claimed, str) and claimed == digest(payload), "policy suite digest mismatch")
    _require(value.get("schema_version") == 1, "policy suite schema_version must be 1")
    _require(value.get("contract") == SUITE_CONTRACT, "unexpected policy suite contract")
    _require(value.get("authority") == "NO_ORDERS", "policy suite authority must remain NO_ORDERS")
    scenarios = value.get("scenarios")
    _require(isinstance(scenarios, list) and scenarios, "policy suite scenarios are required")
    ids = [item.get("scenario_id") for item in scenarios]
    _require(len(ids) == len(set(ids)), "duplicate policy scenario id")
    checks = value.get("metamorphic_checks")
    _require(isinstance(checks, list), "metamorphic checks must be a list")
    return copy.deepcopy(value)


def _run_case(policy: dict[str, Any], scenario: dict[str, Any], operation: str | None = None) -> dict[str, Any]:
    snapshot = copy.deepcopy(scenario["snapshot"])
    policy_input = copy.deepcopy(policy)
    if operation == "REVERSE_ASSET_ORDER":
        snapshot["local_assets"] = list(reversed(snapshot["local_assets"]))
    elif operation == "SCALE_MODEL_COUNTS_X10":
        for asset in snapshot["local_assets"]:
            asset["initial_models"] *= 10
            asset["casualties_observed_lower_bound"] *= 10
    elif operation == "REVERSE_POLICY_RULE_ORDER":
        policy_input["policy_rules"] = list(reversed(policy_input["policy_rules"]))
        policy_input.pop("result_digest", None)
        policy_input["result_digest"] = digest(policy_input)
    elif operation is not None:
        raise TacticalPolicyMatrixError(f"unsupported metamorphic operation: {operation}")

    mutation = scenario.get("mutation")
    if mutation == "AUTHORITY_PROMOTION":
        snapshot["authority"] = "CONTROL"
    elif mutation == "HIDDEN_ENEMY_FIELD":
        snapshot["hidden_enemy_state"] = {"unit": "forbidden"}
    elif mutation == "FOREIGN_POLICY_DIGEST":
        policy_input["source_provenance"]["dense_result_digests"]["eilhart"] = "0" * 64
        policy_input.pop("result_digest", None)
        policy_input["result_digest"] = digest(policy_input)
    elif mutation is not None:
        raise TacticalPolicyMatrixError(f"unsupported scenario mutation: {mutation}")
    return evaluate_tactical_policy(policy_input, snapshot)


def _semantic_signature(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "local_crisis_detected": output["local_crisis_detected"],
        "priority_ordering": output["priority_ordering"],
        "reviews": [
            {
                "review_id": item["review_id"],
                "priority": item["priority"],
                "status": item["status"],
                "asset_id": item.get("asset_id"),
            }
            for item in output["reviews"]
        ],
        "abstentions": output["abstentions"],
        "terminal_outcome_label": output["terminal_outcome_label"],
    }


def _expectations_pass(output: dict[str, Any] | None, error: str | None, expectations: dict[str, Any]) -> dict[str, bool]:
    review_ids = [item["review_id"] for item in (output or {}).get("reviews", [])]
    review_status = {item["review_id"]: item["status"] for item in (output or {}).get("reviews", [])}
    abstentions = (output or {}).get("abstentions", [])
    checks = {
        "error_expectation": (error is not None) is bool(expectations.get("expect_error", False)),
        "required_reviews": all(item in review_ids for item in expectations.get("required_reviews", [])),
        "forbidden_reviews": all(item not in review_ids for item in expectations.get("forbidden_reviews", [])),
        "required_abstentions": all(item in abstentions for item in expectations.get("required_abstentions", [])),
        "priority_ordering": output is None or expectations.get("priority_ordering") is None or output["priority_ordering"] == expectations["priority_ordering"],
        "terminal_label": output is None or expectations.get("terminal_outcome_label") is None or output["terminal_outcome_label"] == expectations["terminal_outcome_label"],
        "authority_boundary": output is None or (
            output["authority"] == "NO_ORDERS"
            and output["application_authority"] == "PROHIBITED"
            and output["project_orders_emitted"] is False
            and output["direct_acknowledgement_claimed"] is False
            and output["causal_execution_claimed"] is False
        ),
        "review_status": output is None or all(review_status.get(key) == value for key, value in expectations.get("review_status", {}).items()),
    }
    return checks


def run_tactical_policy_matrix(
    policy_value: dict[str, Any],
    suite_value: dict[str, Any],
) -> dict[str, Any]:
    policy = validate_cross_corpus_policy_envelope(policy_value)
    suite = validate_tactical_policy_suite(suite_value)
    _require(suite.get("source_policy_digest") == policy["result_digest"], "policy suite is stale or foreign")

    results: list[dict[str, Any]] = []
    passed = 0
    by_id: dict[str, dict[str, Any]] = {}
    for scenario in suite["scenarios"]:
        by_id[scenario["scenario_id"]] = scenario
        output: dict[str, Any] | None = None
        error: str | None = None
        try:
            output = _run_case(policy, scenario)
        except (TacticalPolicyError, TacticalPolicyMatrixError, ValueError, KeyError) as exc:
            error = str(exc)
        checks = _expectations_pass(output, error, scenario["expectations"])
        case_passed = all(checks.values())
        passed += int(case_passed)
        results.append({
            "scenario_id": scenario["scenario_id"],
            "passed": case_passed,
            "checks": checks,
            "error": error,
            "review_ids": [item["review_id"] for item in (output or {}).get("reviews", [])],
            "abstentions": (output or {}).get("abstentions", []),
            "priority_ordering": (output or {}).get("priority_ordering"),
            "terminal_outcome_label": (output or {}).get("terminal_outcome_label"),
            "result_digest": output.get("result_digest") if output else None,
        })

    metamorphic: list[dict[str, Any]] = []
    for check in suite["metamorphic_checks"]:
        scenario = by_id[check["scenario_id"]]
        base = _run_case(policy, scenario)
        transformed = _run_case(policy, scenario, operation=check["operation"])
        check_passed = _semantic_signature(base) == _semantic_signature(transformed)
        metamorphic.append({
            "check_id": check["check_id"],
            "scenario_id": check["scenario_id"],
            "operation": check["operation"],
            "passed": check_passed,
            "base_digest": base["result_digest"],
            "transformed_digest": transformed["result_digest"],
        })

    report: dict[str, Any] = {
        "schema_version": 1,
        "contract": REPORT_CONTRACT,
        "suite_id": suite["suite_id"],
        "seed": suite["seed"],
        "source_policy_digest": policy["result_digest"],
        "scenario_count": len(results),
        "passed_case_count": passed,
        "metamorphic_check_count": len(metamorphic),
        "metamorphic_pass_count": sum(item["passed"] for item in metamorphic),
        "scenarios": results,
        "metamorphic_checks": metamorphic,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_SYNTHETIC",
        "interpretation_limits": [
            "This matrix tests deterministic policy contracts, not WH3 command quality.",
            "No synthetic fixture promotes hidden information, acknowledgement, execution, causality, or tactical superiority.",
            "Ratio-scale invariance is an engineering property of the policy evaluator, not a faction-general empirical threshold.",
        ],
    }
    report["result_digest"] = digest(report)
    return report
