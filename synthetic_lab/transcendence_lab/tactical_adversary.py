from __future__ import annotations

import copy
import math
from typing import Any

from .battle_shadow import run_trace_shadow_evaluator
from .battle_trace import BattleTraceCorpusError, validate_battle_trace_slices
from .canonical import digest
from .tactical_state import build_tactical_state_trajectory


class TacticalAdversarialSuiteError(ValueError):
    pass


def _resolve_path(value: Any, path: list[Any]) -> Any:
    current = value
    for part in path:
        current = current[part]
    return current


def _resolve_parent(value: Any, path: list[Any]) -> tuple[Any, Any]:
    if not path:
        raise TacticalAdversarialSuiteError("mutation path may not be empty")
    return _resolve_path(value, path[:-1]), path[-1]


def _recompute_trace_digest(trace: dict[str, Any]) -> None:
    trace.pop("result_digest", None)
    trace["result_digest"] = digest(trace)


def _apply_mutation(trace: dict[str, Any], mutation: dict[str, Any]) -> bool:
    """Apply a fixture mutation. Returns whether the trace remains JSON-hashable."""
    mutation_type = mutation["type"]
    path = mutation.get("path", [])
    parent, key = _resolve_parent(trace, path)
    if mutation_type == "set":
        parent[key] = mutation["value"]
    elif mutation_type == "set_special":
        special = mutation["special"]
        if special == "NAN":
            parent[key] = float("nan")
        elif special == "POSITIVE_INFINITY":
            parent[key] = float("inf")
        else:
            raise TacticalAdversarialSuiteError(f"unsupported special value: {special}")
        return False
    elif mutation_type == "set_relative":
        parent[key] = _resolve_path(trace, mutation["source_path"]) + mutation["offset"]
    elif mutation_type == "delete":
        del parent[key]
    elif mutation_type == "append_duplicate":
        target = _resolve_path(trace, path)
        target.append(copy.deepcopy(target[mutation["index"]]))
    else:
        raise TacticalAdversarialSuiteError(f"unsupported mutation type: {mutation_type}")
    return True


def _evaluation_signature(evaluations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = copy.deepcopy(evaluations)
    for evaluation in result:
        evaluation.pop("source_tactical_state_digest", None)
        evaluation.pop("result_digest", None)
    return result


def _find_state_unit(
    trajectory: dict[str, Any], slice_id: str, stable_unit_id: str
) -> dict[str, Any]:
    state = next(item for item in trajectory["states"] if item["slice_id"] == slice_id)
    return next(
        item
        for item in state["units"]
        if item["observed"]["stable_unit_id"] == stable_unit_id
    )


def _reverse_unit_order(trace: dict[str, Any]) -> None:
    for item in trace["slices"]:
        item["units"] = list(reversed(item["units"]))


def _translate_xz(trace: dict[str, Any], x_offset: float, z_offset: float) -> None:
    for item in trace["slices"]:
        for unit in item["units"]:
            unit["position_x"] += x_offset
            unit["position_z"] += z_offset
            unit["ordered_position_x"] += x_offset
            unit["ordered_position_z"] += z_offset


def _worsen_local_commander(trace: dict[str, Any], slice_id: str) -> str:
    target_slice = next(item for item in trace["slices"] if item["slice_id"] == slice_id)
    commander = next(
        unit
        for unit in target_slice["units"]
        if unit["local_alliance"] and unit["role"] == "commander" and unit["is_commander"]
    )
    commander["hitpoints_fraction"] = max(0.01, commander["hitpoints_fraction"] * 0.35)
    commander["fatigue"] = "threshold_exhausted"
    commander["in_melee"] = True
    commander["under_missile_attack"] = True
    commander["left_flank_threatened"] = True
    commander["right_flank_threatened"] = True
    commander["rear_flank_threatened"] = True
    return commander["stable_unit_id"]


def _simultaneous_collapse(trace: dict[str, Any], slice_id: str) -> None:
    target_slice = next(item for item in trace["slices"] if item["slice_id"] == slice_id)
    for unit in target_slice["units"]:
        unit["routing"] = True
        unit["shattered"] = True
        unit["wavering"] = False
        unit["in_melee"] = False
        unit["hitpoints_fraction"] = 0.10
        alive = max(1, int(math.floor(unit["initial_men"] * 0.10)))
        unit["men_alive"] = alive
        unit["men_fraction"] = alive / unit["initial_men"]


def validate_tactical_adversarial_suite(
    suite: dict[str, Any], trace_corpus: dict[str, Any]
) -> dict[str, Any]:
    required = {
        "schema_version",
        "suite_id",
        "base_trace_corpus_id",
        "base_trace_result_digest",
        "seed",
        "authority",
        "invalid_input_cases",
        "metamorphic_cases",
    }
    missing = sorted(required - suite.keys())
    if missing:
        raise TacticalAdversarialSuiteError(f"adversarial suite missing: {missing}")
    if suite["schema_version"] != 1:
        raise TacticalAdversarialSuiteError("unsupported adversarial suite schema")
    if suite["authority"] != "NO_ORDERS":
        raise TacticalAdversarialSuiteError("adversarial suite may not claim order authority")
    if suite["base_trace_corpus_id"] != trace_corpus["corpus_id"]:
        raise TacticalAdversarialSuiteError("adversarial suite corpus id mismatch")
    if suite["base_trace_result_digest"] != trace_corpus["result_digest"]:
        raise TacticalAdversarialSuiteError("adversarial suite trace digest mismatch")
    if not isinstance(suite["invalid_input_cases"], list) or not suite["invalid_input_cases"]:
        raise TacticalAdversarialSuiteError("adversarial suite requires invalid-input cases")
    if not isinstance(suite["metamorphic_cases"], list) or not suite["metamorphic_cases"]:
        raise TacticalAdversarialSuiteError("adversarial suite requires metamorphic cases")
    ids = [
        item.get("case_id")
        for item in suite["invalid_input_cases"] + suite["metamorphic_cases"]
    ]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise TacticalAdversarialSuiteError("adversarial case ids must be unique nonempty strings")
    return suite


def run_tactical_adversarial_suite(
    trace_corpus: dict[str, Any], suite: dict[str, Any]
) -> dict[str, Any]:
    trace_corpus = validate_battle_trace_slices(trace_corpus)
    suite = validate_tactical_adversarial_suite(suite, trace_corpus)
    baseline_trajectory = build_tactical_state_trajectory(trace_corpus)
    baseline_evaluation = run_trace_shadow_evaluator(trace_corpus)

    invalid_results: list[dict[str, Any]] = []
    for case in suite["invalid_input_cases"]:
        mutated = copy.deepcopy(trace_corpus)
        hashable = _apply_mutation(mutated, case["mutation"])
        if hashable:
            _recompute_trace_digest(mutated)
        rejected = False
        message = None
        try:
            validate_battle_trace_slices(mutated)
        except BattleTraceCorpusError as exc:
            rejected = True
            message = str(exc)
        passed = rejected and case["expected_error"] in (message or "")
        invalid_results.append(
            {
                "case_id": case["case_id"],
                "category": "INVALID_INPUT_REJECTION",
                "passed": passed,
                "expected_error": case["expected_error"],
                "observed_error": message,
                "pre_v0_1n_result": case["pre_v0_1n_result"],
                "result": "REJECTED_FAIL_CLOSED" if rejected else "UNEXPECTEDLY_ACCEPTED",
            }
        )

    metamorphic_results: list[dict[str, Any]] = []
    for case in suite["metamorphic_cases"]:
        case_type = case["type"]
        mutated = copy.deepcopy(trace_corpus)
        details: dict[str, Any]
        passed = False

        if case_type == "REVERSE_UNIT_ORDER":
            _reverse_unit_order(mutated)
            _recompute_trace_digest(mutated)
            result = run_trace_shadow_evaluator(mutated)
            passed = result["evaluations"] == baseline_evaluation["evaluations"]
            details = {
                "evaluation_digest_baseline": digest(baseline_evaluation["evaluations"]),
                "evaluation_digest_mutated": digest(result["evaluations"]),
            }
        elif case_type == "TRANSLATE_XZ":
            _translate_xz(mutated, case["x_offset"], case["z_offset"])
            _recompute_trace_digest(mutated)
            result = run_trace_shadow_evaluator(mutated)
            baseline_signature = _evaluation_signature(baseline_evaluation["evaluations"])
            mutated_signature = _evaluation_signature(result["evaluations"])
            passed = baseline_signature == mutated_signature
            details = {
                "decision_signature_digest_baseline": digest(baseline_signature),
                "decision_signature_digest_mutated": digest(mutated_signature),
                "translation": {"x": case["x_offset"], "z": case["z_offset"]},
            }
        elif case_type == "WORSEN_LOCAL_COMMANDER":
            unit_id = _worsen_local_commander(mutated, case["slice_id"])
            _recompute_trace_digest(mutated)
            trajectory = build_tactical_state_trajectory(mutated)
            before = _find_state_unit(baseline_trajectory, case["slice_id"], unit_id)
            after = _find_state_unit(trajectory, case["slice_id"], unit_id)
            danger_ok = after["derived"]["danger_score"] >= before["derived"]["danger_score"]
            recovery_ok = (
                after["derived"]["withdrawal_recoverability_proxy"]
                <= before["derived"]["withdrawal_recoverability_proxy"]
            )
            passed = danger_ok and recovery_ok
            details = {
                "stable_unit_id": unit_id,
                "danger_before": before["derived"]["danger_score"],
                "danger_after": after["derived"]["danger_score"],
                "recoverability_before": before["derived"]["withdrawal_recoverability_proxy"],
                "recoverability_after": after["derived"]["withdrawal_recoverability_proxy"],
            }
        elif case_type == "SIMULTANEOUS_COLLAPSE":
            _simultaneous_collapse(mutated, case["slice_id"])
            _recompute_trace_digest(mutated)
            trajectory = build_tactical_state_trajectory(mutated)
            state = next(
                item for item in trajectory["states"] if item["slice_id"] == case["slice_id"]
            )
            local_state = state["battle_state"]["local_stability_state"]
            phase_state = state["battle_state"]["tactical_phase_state"]
            enemy_state = state["battle_state"]["visible_enemy_collapse_state"]
            passed = (
                local_state == "IRREVERSIBLE_COLLAPSE"
                and phase_state == "RECOVERY_REQUIRED"
                and enemy_state in {"ROUT_CASCADE", "TERMINAL_COUNTDOWN"}
            )
            details = {
                "local_stability_state": local_state,
                "tactical_phase_state": phase_state,
                "visible_enemy_collapse_state": enemy_state,
            }
        elif case_type == "ADD_HIDDEN_ENEMIES":
            target_slice = next(
                item for item in mutated["slices"] if item["slice_id"] == case["slice_id"]
            )
            target_slice["hidden_enemy_units"] = case["hidden_enemy_units"]
            _recompute_trace_digest(mutated)
            trajectory = build_tactical_state_trajectory(mutated)
            state = next(
                item for item in trajectory["states"] if item["slice_id"] == case["slice_id"]
            )
            enemy_state = state["battle_state"]["visible_enemy_collapse_state"]
            outcome_state = state["battle_state"]["outcome_state"]
            passed = (
                enemy_state != "TERMINAL_COUNTDOWN"
                and outcome_state != "VISIBLE_ENEMY_DEFEAT_EFFECTIVELY_IRREVERSIBLE"
            )
            details = {
                "hidden_enemy_unit_count": case["hidden_enemy_units"],
                "visible_enemy_collapse_state": enemy_state,
                "outcome_state": outcome_state,
            }
        elif case_type == "BASELINE_LIFECYCLE":
            budget = baseline_evaluation["command_budget_analysis"]
            passed = (
                budget["continued_advisory_priority_count"] > 0
                and budget["advisory_priority_transition_count"] < 50
                and budget["lifecycle_identity"]
                == "STABLE_OPPORTUNITY_KEY_NOT_SLICE_INSTANCE_ID"
            )
            details = {
                "pre_v0_1n_transition_count": 50,
                "post_v0_1n_transition_count": budget["advisory_priority_transition_count"],
                "continued_advisory_priority_count": budget[
                    "continued_advisory_priority_count"
                ],
                "lifecycle_identity": budget["lifecycle_identity"],
            }
        else:
            raise TacticalAdversarialSuiteError(
                f"unsupported metamorphic case type: {case_type}"
            )

        metamorphic_results.append(
            {
                "case_id": case["case_id"],
                "category": "METAMORPHIC_INVARIANT",
                "expectation": case["expectation"],
                "passed": passed,
                "details": details,
            }
        )

    all_results = invalid_results + metamorphic_results
    result: dict[str, Any] = {
        "schema_version": 1,
        "suite_id": suite["suite_id"],
        "seed": suite["seed"],
        "source_trace_corpus_id": trace_corpus["corpus_id"],
        "source_trace_result_digest": trace_corpus["result_digest"],
        "input_validation_contract": baseline_trajectory["input_validation_contract"],
        "tactical_state_contract": baseline_trajectory["trajectory_contract"],
        "invalid_input_results": invalid_results,
        "metamorphic_results": metamorphic_results,
        "summary": {
            "invalid_input_case_count": len(invalid_results),
            "invalid_input_pass_count": sum(item["passed"] for item in invalid_results),
            "metamorphic_case_count": len(metamorphic_results),
            "metamorphic_pass_count": sum(item["passed"] for item in metamorphic_results),
            "total_case_count": len(all_results),
            "total_pass_count": sum(item["passed"] for item in all_results),
            "all_passed": all(item["passed"] for item in all_results),
        },
        "defects_corrected": [
            "malformed observation values were previously coerced or clamped instead of rejected",
            "local force collapse could be masked by an enemy-rout recovery phase",
            "slice-scoped opportunity ids falsely counted persistent priorities as new transitions",
        ],
        "evidence_status": "CONTROL_OFFLINE",
        "authority": "NO_ORDERS",
    }
    result["result_digest"] = digest(result)
    return result
