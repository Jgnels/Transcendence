from __future__ import annotations

import copy
from collections import defaultdict
from itertools import combinations
from typing import Any, Callable

from .battle_shadow import evaluate_tactical_state
from .battle_trace import validate_battle_trace_slices, validate_tactical_slice_record
from .canonical import digest
from .tactical_state import build_tactical_state
from .tactical_portfolio import build_tactical_priority_portfolio


class TacticalBaselineSuiteError(ValueError):
    pass


SUITE_CONTRACT = "TACTICAL_BASELINE_MATRIX_V1"
OUTPUT_CONTRACT = "TACTICAL_BASELINE_COMPARISON_V1"
POLICY_IDS = (
    "ROLE_AWARE_PORTFOLIO_V1",
    "LEGACY_ROLE_AWARE_V2",
    "UNIFORM_DANGER_045",
    "PRESERVATION_ONLY_035",
    "PRESSURE_ONLY",
    "PASSIVE_HOLD",
)

OPPORTUNITY_TO_INTENT = {
    "COMMANDER_EXTRACTION_WINDOW": "EXTRACT_COMMANDER",
    "ARTILLERY_EVACUATION_WINDOW": "EVACUATE_ARTILLERY",
    "RANGED_REPOSITION_WINDOW": "REPOSITION_RANGED",
    "CAVALRY_DISENGAGEMENT_WINDOW": "DISENGAGE_CAVALRY",
    "FRONTLINE_RELIEF_WINDOW": "RELIEVE_FRONTLINE",
    "LOCAL_ROUT_CONTAINMENT_WINDOW": "CONTAIN_LOCAL_ROUT",
    "RESERVE_COMMITMENT_WINDOW": "COMMIT_RESERVE",
    "SELECTIVE_PURSUIT_WINDOW": "SELECTIVE_PURSUIT",
    "PURSUIT_TERMINATION_WINDOW": "TERMINATE_PURSUIT",
    "REFORM_AND_PRESERVE_WINDOW": "REFORM_AND_PRESERVE",
}

ROLE_TO_PRESERVATION_INTENT = {
    "commander": "EXTRACT_COMMANDER",
    "artillery": "EVACUATE_ARTILLERY",
    "ranged": "REPOSITION_RANGED",
    "cavalry": "DISENGAGE_CAVALRY",
    "frontline": "RELIEVE_FRONTLINE",
    "unknown": "PRESERVE_UNIT",
}

_ALLOWED_MUTATIONS = {
    "SET_HIDDEN_ENEMY_UNITS",
    "SET_UNIT_FIELDS",
    "MOVE_UNIT_RELATIVE",
    "SET_ALLIANCE_FIELDS",
    "SET_ROLE_FIELDS",
    "REMOVE_UNITS",
}


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TacticalBaselineSuiteError(f"{label} must be a nonempty string")
    return value


def _require_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise TacticalBaselineSuiteError(f"{label} must be a string list")
    if len(value) != len(set(value)):
        raise TacticalBaselineSuiteError(f"{label} must not contain duplicates")
    return value


def validate_tactical_baseline_suite(
    suite: dict[str, Any], trace_corpus: dict[str, Any]
) -> dict[str, Any]:
    trace_corpus = validate_battle_trace_slices(trace_corpus)
    if not isinstance(suite, dict):
        raise TacticalBaselineSuiteError("baseline suite must be an object")
    required = {
        "schema_version",
        "suite_contract",
        "suite_id",
        "seed",
        "evidence_status",
        "source_trace_digest",
        "policies",
        "scenarios",
        "interpretation_limits",
        "result_digest",
    }
    missing = sorted(required - suite.keys())
    if missing:
        raise TacticalBaselineSuiteError(f"baseline suite missing: {missing}")
    if suite["schema_version"] != 1:
        raise TacticalBaselineSuiteError("unsupported baseline suite schema")
    if suite["suite_contract"] != SUITE_CONTRACT:
        raise TacticalBaselineSuiteError("unsupported baseline suite contract")
    _require_string(suite.get("suite_id"), "suite_id")
    if not isinstance(suite.get("seed"), int) or isinstance(suite.get("seed"), bool):
        raise TacticalBaselineSuiteError("seed must be an integer")
    if suite.get("evidence_status") != "CONTROL_SYNTHETIC":
        raise TacticalBaselineSuiteError("baseline suite must be CONTROL_SYNTHETIC")
    if suite.get("source_trace_digest") != trace_corpus["result_digest"]:
        raise TacticalBaselineSuiteError("baseline suite source trace digest mismatch")
    if suite.get("policies") != list(POLICY_IDS):
        raise TacticalBaselineSuiteError("baseline suite policy list mismatch")
    limits = _require_string_list(
        suite.get("interpretation_limits"), "interpretation_limits"
    )
    if not any("not" in item.lower() and "quality" in item.lower() for item in limits):
        raise TacticalBaselineSuiteError(
            "interpretation limits must disclaim tactical-quality proof"
        )

    slices_by_id = {item["slice_id"]: item for item in trace_corpus["slices"]}
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 10:
        raise TacticalBaselineSuiteError(
            "baseline suite requires at least ten heterogeneous scenarios"
        )
    seen: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise TacticalBaselineSuiteError("each scenario must be an object")
        scenario_id = _require_string(scenario.get("scenario_id"), "scenario_id")
        if scenario_id in seen:
            raise TacticalBaselineSuiteError(f"duplicate scenario_id: {scenario_id}")
        seen.add(scenario_id)
        _require_string(scenario.get("description"), f"{scenario_id} description")
        base_slice_id = _require_string(
            scenario.get("base_slice_id"), f"{scenario_id} base_slice_id"
        )
        if base_slice_id not in slices_by_id:
            raise TacticalBaselineSuiteError(
                f"{scenario_id} references unknown base slice: {base_slice_id}"
            )
        mutations = scenario.get("mutations")
        if not isinstance(mutations, list):
            raise TacticalBaselineSuiteError(
                f"{scenario_id} mutations must be a list"
            )
        for mutation in mutations:
            if not isinstance(mutation, dict):
                raise TacticalBaselineSuiteError(
                    f"{scenario_id} mutation must be an object"
                )
            operation = mutation.get("operation")
            if operation not in _ALLOWED_MUTATIONS:
                raise TacticalBaselineSuiteError(
                    f"{scenario_id} unsupported mutation: {operation}"
                )
        expectations = scenario.get("expectations")
        if not isinstance(expectations, dict):
            raise TacticalBaselineSuiteError(
                f"{scenario_id} expectations must be an object"
            )
        _require_string_list(
            expectations.get("required_intents", []),
            f"{scenario_id} required_intents",
        )
        _require_string_list(
            expectations.get("forbidden_intents", []),
            f"{scenario_id} forbidden_intents",
        )
        subject_expectations = expectations.get("required_subjects_by_intent", {})
        if not isinstance(subject_expectations, dict):
            raise TacticalBaselineSuiteError(
                f"{scenario_id} required_subjects_by_intent must be an object"
            )
        for intent, subjects in subject_expectations.items():
            _require_string(intent, f"{scenario_id} required intent subject key")
            _require_string_list(
                subjects, f"{scenario_id} required subjects for {intent}"
            )
        equivalence_group = scenario.get("equivalence_group")
        if equivalence_group is not None:
            _require_string(equivalence_group, f"{scenario_id} equivalence_group")
        maximum = expectations.get("maximum_selected_intents", 6)
        if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 0:
            raise TacticalBaselineSuiteError(
                f"{scenario_id} maximum_selected_intents must be nonnegative"
            )

    expected_digest = suite.get("result_digest")
    if not isinstance(expected_digest, str) or len(expected_digest) != 64:
        raise TacticalBaselineSuiteError("invalid baseline suite result digest")
    without_digest = dict(suite)
    without_digest.pop("result_digest", None)
    if digest(without_digest) != expected_digest:
        raise TacticalBaselineSuiteError("baseline suite result digest mismatch")
    return suite


def _find_unit(slice_record: dict[str, Any], unit_id: str) -> dict[str, Any]:
    for unit in slice_record["units"]:
        if unit["stable_unit_id"] == unit_id:
            return unit
    raise TacticalBaselineSuiteError(f"mutation references unknown unit: {unit_id}")


def _apply_mutations(
    base_slice: dict[str, Any], mutations: list[dict[str, Any]]
) -> dict[str, Any]:
    result = copy.deepcopy(base_slice)
    for mutation in mutations:
        operation = mutation["operation"]
        if operation == "SET_HIDDEN_ENEMY_UNITS":
            value = mutation.get("value")
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise TacticalBaselineSuiteError(
                    "SET_HIDDEN_ENEMY_UNITS requires a nonnegative integer"
                )
            result["hidden_enemy_units"] = value
        elif operation == "SET_UNIT_FIELDS":
            unit = _find_unit(result, _require_string(mutation.get("unit_id"), "unit_id"))
            fields = mutation.get("fields")
            if not isinstance(fields, dict) or not fields:
                raise TacticalBaselineSuiteError(
                    "SET_UNIT_FIELDS requires nonempty fields"
                )
            unit.update(copy.deepcopy(fields))
        elif operation == "MOVE_UNIT_RELATIVE":
            unit = _find_unit(result, _require_string(mutation.get("unit_id"), "unit_id"))
            reference = _find_unit(
                result,
                _require_string(mutation.get("reference_unit_id"), "reference_unit_id"),
            )
            for axis in ("x", "y", "z"):
                offset = mutation.get(f"offset_{axis}", 0.0)
                if not isinstance(offset, (int, float)) or isinstance(offset, bool):
                    raise TacticalBaselineSuiteError(
                        f"MOVE_UNIT_RELATIVE offset_{axis} must be numeric"
                    )
                unit[f"position_{axis}"] = reference[f"position_{axis}"] + offset
        elif operation == "SET_ALLIANCE_FIELDS":
            local_alliance = mutation.get("local_alliance")
            if type(local_alliance) is not bool:
                raise TacticalBaselineSuiteError(
                    "SET_ALLIANCE_FIELDS local_alliance must be boolean"
                )
            fields = mutation.get("fields")
            if not isinstance(fields, dict) or not fields:
                raise TacticalBaselineSuiteError(
                    "SET_ALLIANCE_FIELDS requires nonempty fields"
                )
            for unit in result["units"]:
                if unit["local_alliance"] is local_alliance:
                    unit.update(copy.deepcopy(fields))
        elif operation == "SET_ROLE_FIELDS":
            role = _require_string(mutation.get("role"), "role")
            local_alliance = mutation.get("local_alliance")
            if type(local_alliance) is not bool:
                raise TacticalBaselineSuiteError(
                    "SET_ROLE_FIELDS local_alliance must be boolean"
                )
            fields = mutation.get("fields")
            if not isinstance(fields, dict) or not fields:
                raise TacticalBaselineSuiteError(
                    "SET_ROLE_FIELDS requires nonempty fields"
                )
            for unit in result["units"]:
                if unit["local_alliance"] is local_alliance and unit["role"] == role:
                    unit.update(copy.deepcopy(fields))
        elif operation == "REMOVE_UNITS":
            unit_ids = _require_string_list(mutation.get("unit_ids"), "unit_ids")
            known = {unit["stable_unit_id"] for unit in result["units"]}
            unknown = sorted(set(unit_ids) - known)
            if unknown:
                raise TacticalBaselineSuiteError(
                    f"REMOVE_UNITS references unknown units: {unknown}"
                )
            result["units"] = [
                unit for unit in result["units"] if unit["stable_unit_id"] not in unit_ids
            ]
        else:  # pragma: no cover - validator owns this path
            raise TacticalBaselineSuiteError(f"unsupported mutation: {operation}")
    validate_tactical_slice_record(result)
    return result


def build_synthetic_tactical_slice(
    base_slice: dict[str, Any], mutations: list[dict[str, Any]]
) -> dict[str, Any]:
    """Apply validated project-owned mutations to a public-safe tactical slice."""
    return _apply_mutations(base_slice, mutations)


def _intent_record(
    intent: str,
    subjects: list[str],
    score: float,
    reason: str,
) -> dict[str, Any]:
    return {
        "intent": intent,
        "subject_unit_ids": sorted(set(subjects)),
        "priority_score": round(max(0.0, min(1.0, score)), 6),
        "reason": reason,
        "authority": "ADVISORY_ONLY",
    }


def _dedupe_and_bound(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for record in records:
        key = (record["intent"], tuple(record["subject_unit_ids"]))
        current = best.get(key)
        if current is None or record["priority_score"] > current["priority_score"]:
            best[key] = record
    return sorted(
        best.values(),
        key=lambda item: (-item["priority_score"], item["intent"], item["subject_unit_ids"]),
    )[:6]


def _legacy_role_aware_policy(state: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evaluation = evaluate_tactical_state(state)
    records = []
    for opportunity in evaluation["selected_decision_opportunities"]:
        intent = OPPORTUNITY_TO_INTENT.get(opportunity["opportunity_type"])
        if intent is None:
            continue
        records.append(
            _intent_record(
                intent,
                opportunity["subject_unit_ids"],
                opportunity["utility_score"],
                f"mapped from {opportunity['opportunity_type']}",
            )
        )
    return _dedupe_and_bound(records), evaluation


def _portfolio_role_aware_policy(
    state: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    portfolio = build_tactical_priority_portfolio(state)
    records: list[dict[str, Any]] = []
    for priority in portfolio["selected_priorities"]:
        intent = OPPORTUNITY_TO_INTENT.get(priority["opportunity_type"])
        if intent is None:
            if priority["opportunity_type"] == "CRITICAL_PORTFOLIO_OVERFLOW":
                intent = "REVIEW_CRITICAL_OVERFLOW"
            else:
                continue
        records.append(
            _intent_record(
                intent,
                priority["subject_unit_ids"],
                priority["utility_score"],
                f"mapped from portfolio {priority['portfolio_id']}",
            )
        )
    return _dedupe_and_bound(records), portfolio


def _local_units(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [unit for unit in state["units"] if unit["observed"]["local_alliance"]]


def _preservation_records(
    state: dict[str, Any], *, danger_threshold: float, include_low_hp: bool
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for unit in _local_units(state):
        observed = unit["observed"]
        derived = unit["derived"]
        trigger = derived["danger_score"] >= danger_threshold
        if include_low_hp:
            trigger = trigger or observed["hitpoints_fraction"] < 0.50
        trigger = trigger or observed["routing"] or observed["shattered"]
        if not trigger:
            continue
        intent = ROLE_TO_PRESERVATION_INTENT.get(observed["role"], "PRESERVE_UNIT")
        score = (
            0.62 * derived["danger_score"]
            + 0.28 * derived["asset_value_score"]
            + 0.10 * (1.0 - derived["withdrawal_recoverability_proxy"])
        )
        records.append(
            _intent_record(
                intent,
                [observed["stable_unit_id"]],
                score,
                f"uniform preservation threshold {danger_threshold:.2f}",
            )
        )
    return _dedupe_and_bound(records)


def _uniform_danger_policy(state: dict[str, Any]) -> list[dict[str, Any]]:
    return _preservation_records(state, danger_threshold=0.45, include_low_hp=False)


def _preservation_only_policy(state: dict[str, Any]) -> list[dict[str, Any]]:
    records = _preservation_records(
        state, danger_threshold=0.35, include_low_hp=True
    )
    enemy_collapse = state["battle_state"]["visible_enemy_collapse_state"]
    if enemy_collapse in {"ROUT_CASCADE", "TERMINAL_COUNTDOWN"}:
        endangered = [
            unit["observed"]["stable_unit_id"]
            for unit in _local_units(state)
            if unit["derived"]["danger_score"] >= 0.35
        ]
        if endangered:
            records.append(
                _intent_record(
                    "REFORM_AND_PRESERVE",
                    endangered,
                    0.70,
                    "preservation-only rout-cascade response",
                )
            )
    return _dedupe_and_bound(records)


def _pressure_only_policy(state: dict[str, Any]) -> list[dict[str, Any]]:
    if state["battle_state"]["local_stability_state"] == "TERMINAL":
        return []
    enemy_collapse = state["battle_state"]["visible_enemy_collapse_state"]
    coherent_enemy = [
        unit["observed"]["stable_unit_id"]
        for unit in state["units"]
        if not unit["observed"]["local_alliance"]
        and not unit["observed"]["shattered"]
    ]
    if enemy_collapse in {"BREAKING", "ROUT_CASCADE", "TERMINAL_COUNTDOWN"}:
        return [
            _intent_record(
                "SELECTIVE_PURSUIT",
                coherent_enemy,
                0.75,
                "pressure-only baseline continues exploitation",
            )
        ]
    return [
        _intent_record(
            "PRESS_VISIBLE_THREAT",
            coherent_enemy,
            0.60,
            "pressure-only baseline prioritizes visible combat pressure",
        )
    ]


def _passive_policy(state: dict[str, Any]) -> list[dict[str, Any]]:
    del state
    return []


_POLICY_FUNCTIONS: dict[str, Callable[[dict[str, Any]], list[dict[str, Any]]]] = {
    "UNIFORM_DANGER_045": _uniform_danger_policy,
    "PRESERVATION_ONLY_035": _preservation_only_policy,
    "PRESSURE_ONLY": _pressure_only_policy,
    "PASSIVE_HOLD": _passive_policy,
}


def _state_contract_result(
    state: dict[str, Any], expectations: dict[str, Any]
) -> dict[str, Any]:
    observed = {
        "local_stability_state": state["battle_state"]["local_stability_state"],
        "tactical_phase_state": state["battle_state"]["tactical_phase_state"],
        "visible_enemy_collapse_state": state["battle_state"][
            "visible_enemy_collapse_state"
        ],
        "outcome_state": state["battle_state"]["outcome_state"],
    }
    mismatches = []
    for key in observed:
        expected = expectations.get(f"required_{key}")
        if expected is not None and observed[key] != expected:
            mismatches.append(
                {"field": key, "expected": expected, "observed": observed[key]}
            )
    return {
        "passed": not mismatches,
        "observed": observed,
        "mismatches": mismatches,
    }


def _policy_contract_result(
    records: list[dict[str, Any]], expectations: dict[str, Any]
) -> dict[str, Any]:
    selected = {record["intent"] for record in records}
    required = set(expectations.get("required_intents", []))
    forbidden = set(expectations.get("forbidden_intents", []))
    missing = sorted(required - selected)
    violations = sorted(forbidden & selected)
    subjects_by_intent: dict[str, set[str]] = defaultdict(set)
    for record in records:
        subjects_by_intent[record["intent"]].update(record["subject_unit_ids"])
    subject_mismatches = []
    for intent, required_subjects in expectations.get(
        "required_subjects_by_intent", {}
    ).items():
        missing_subjects = sorted(
            set(required_subjects) - subjects_by_intent.get(intent, set())
        )
        if missing_subjects:
            subject_mismatches.append(
                {"intent": intent, "missing_subject_unit_ids": missing_subjects}
            )
    maximum = expectations.get("maximum_selected_intents", 6)
    terminal_violation = (
        expectations.get("require_no_action", False) and bool(records)
    )
    return {
        "passed": (
            not missing
            and not violations
            and not subject_mismatches
            and len(records) <= maximum
            and not terminal_violation
        ),
        "selected_intents": sorted(selected),
        "missing_required_intents": missing,
        "forbidden_intent_violations": violations,
        "required_subject_mismatches": subject_mismatches,
        "selected_intent_count": len(records),
        "maximum_selected_intents": maximum,
        "no_action_violation": terminal_violation,
    }


def _aggregate_policy(
    policy_id: str, scenario_results: list[dict[str, Any]]
) -> dict[str, Any]:
    policy_results = [item["policies"][policy_id] for item in scenario_results]
    required_total = sum(
        len(item["expectations"]["required_intents"]) for item in scenario_results
    )
    required_missing = sum(
        len(item["contract"]["missing_required_intents"])
        for item in policy_results
    )
    forbidden_total = sum(
        len(item["expectations"]["forbidden_intents"]) for item in scenario_results
    )
    forbidden_violations = sum(
        len(item["contract"]["forbidden_intent_violations"])
        for item in policy_results
    )
    return {
        "policy_id": policy_id,
        "scenario_contract_pass_count": sum(
            item["contract"]["passed"] for item in policy_results
        ),
        "scenario_count": len(policy_results),
        "required_intent_recall": round(
            (required_total - required_missing) / required_total
            if required_total
            else 1.0,
            6,
        ),
        "forbidden_intent_safety": round(
            (forbidden_total - forbidden_violations) / forbidden_total
            if forbidden_total
            else 1.0,
            6,
        ),
        "total_selected_intents": sum(
            item["contract"]["selected_intent_count"] for item in policy_results
        ),
        "distinct_intents": sorted(
            {
                intent
                for item in policy_results
                for intent in item["contract"]["selected_intents"]
            }
        ),
        "interpretation": (
            "Synthetic contract alignment only; not evidence of battle outcomes, "
            "causal casualty reduction, or tactical superiority."
        ),
    }


def _pairwise_disagreement(
    scenario_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for left, right in combinations(POLICY_IDS, 2):
        disagreements = 0
        total_distance = 0.0
        for scenario in scenario_results:
            left_set = set(
                scenario["policies"][left]["contract"]["selected_intents"]
            )
            right_set = set(
                scenario["policies"][right]["contract"]["selected_intents"]
            )
            union = left_set | right_set
            distance = 0.0 if not union else 1.0 - len(left_set & right_set) / len(union)
            if distance > 0.0:
                disagreements += 1
            total_distance += distance
        results.append(
            {
                "left_policy": left,
                "right_policy": right,
                "scenario_disagreement_count": disagreements,
                "mean_jaccard_distance": round(
                    total_distance / len(scenario_results), 6
                ),
            }
        )
    return results


def _equivalence_checks(
    scenario_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for scenario in scenario_results:
        group = scenario.get("equivalence_group")
        if group:
            groups[group].append(scenario)
    checks: list[dict[str, Any]] = []
    for group, items in sorted(groups.items()):
        if len(items) < 2:
            checks.append(
                {
                    "equivalence_group": group,
                    "passed": False,
                    "reason": "equivalence group requires at least two scenarios",
                    "scenario_ids": [item["scenario_id"] for item in items],
                }
            )
            continue
        signatures = []
        for item in items:
            policy = item["policies"]["ROLE_AWARE_PORTFOLIO_V1"]
            signatures.append(
                {
                    "intents": policy["contract"]["selected_intents"],
                    "state": item["state_contract"]["observed"],
                }
            )
        checks.append(
            {
                "equivalence_group": group,
                "passed": all(signature == signatures[0] for signature in signatures[1:]),
                "scenario_ids": [item["scenario_id"] for item in items],
                "signature_digest": digest(signatures[0]),
            }
        )
    return checks


def run_tactical_baseline_matrix(
    trace_corpus: dict[str, Any], suite: dict[str, Any]
) -> dict[str, Any]:
    trace_corpus = validate_battle_trace_slices(trace_corpus)
    suite = validate_tactical_baseline_suite(suite, trace_corpus)
    slices_by_id = {item["slice_id"]: item for item in trace_corpus["slices"]}

    scenario_results: list[dict[str, Any]] = []
    for scenario in suite["scenarios"]:
        slice_record = _apply_mutations(
            slices_by_id[scenario["base_slice_id"]], scenario["mutations"]
        )
        state = build_tactical_state(slice_record)
        state_contract = _state_contract_result(state, scenario["expectations"])

        portfolio_records, portfolio_evaluation = _portfolio_role_aware_policy(state)
        legacy_records, legacy_evaluation = _legacy_role_aware_policy(state)
        policies: dict[str, Any] = {}
        for policy_id in POLICY_IDS:
            if policy_id == "ROLE_AWARE_PORTFOLIO_V1":
                records = portfolio_records
                source_digest = portfolio_evaluation["result_digest"]
                diagnostics = {
                    "critical_source_coverage": portfolio_evaluation[
                        "critical_source_coverage"
                    ],
                    "critical_overflow_used": portfolio_evaluation[
                        "critical_overflow_used"
                    ],
                    "grouped_priority_count": portfolio_evaluation[
                        "grouped_priority_count"
                    ],
                }
            elif policy_id == "LEGACY_ROLE_AWARE_V2":
                records = legacy_records
                source_digest = legacy_evaluation["result_digest"]
                diagnostics = {
                    "critical_source_coverage": legacy_evaluation[
                        "command_budget"
                    ]["critical_opportunity_coverage"],
                    "critical_overflow_used": False,
                    "grouped_priority_count": None,
                }
            else:
                records = _POLICY_FUNCTIONS[policy_id](state)
                source_digest = None
                diagnostics = None
            policies[policy_id] = {
                "policy_id": policy_id,
                "selected": records,
                "contract": _policy_contract_result(
                    records, scenario["expectations"]
                ),
                "source_evaluation_digest": source_digest,
                "diagnostics": diagnostics,
                "authority": "OFFLINE_ADVISORY_BASELINE_ONLY",
            }

        scenario_result: dict[str, Any] = {
            "scenario_id": scenario["scenario_id"],
            "description": scenario["description"],
            "base_slice_id": scenario["base_slice_id"],
            "equivalence_group": scenario.get("equivalence_group"),
            "synthetic_slice_digest": digest(slice_record),
            "tactical_state_digest": state["result_digest"],
            "expectations": copy.deepcopy(scenario["expectations"]),
            "state_contract": state_contract,
            "policies": policies,
            "evidence_status": "CONTROL_SYNTHETIC",
            "counterfactual_status": "NOT_A_BATTLE_OUTCOME_SIMULATION",
        }
        scenario_result["result_digest"] = digest(scenario_result)
        scenario_results.append(scenario_result)

    policy_summary = [
        _aggregate_policy(policy_id, scenario_results) for policy_id in POLICY_IDS
    ]
    equivalence_checks = _equivalence_checks(scenario_results)
    role_aware = next(
        item for item in policy_summary if item["policy_id"] == "ROLE_AWARE_PORTFOLIO_V1"
    )
    state_pass_count = sum(
        item["state_contract"]["passed"] for item in scenario_results
    )
    result: dict[str, Any] = {
        "schema_version": 1,
        "output_contract": OUTPUT_CONTRACT,
        "suite_id": suite["suite_id"],
        "suite_seed": suite["seed"],
        "source_trace_digest": trace_corpus["result_digest"],
        "scenario_count": len(scenario_results),
        "policies": list(POLICY_IDS),
        "scenario_results": scenario_results,
        "policy_summary": policy_summary,
        "pairwise_policy_disagreement": _pairwise_disagreement(scenario_results),
        "equivalence_checks": equivalence_checks,
        "gate_measurements": {
            "state_contract_pass_count": state_pass_count,
            "role_aware_scenario_pass_count": role_aware[
                "scenario_contract_pass_count"
            ],
            "role_aware_required_intent_recall": role_aware[
                "required_intent_recall"
            ],
            "role_aware_forbidden_intent_safety": role_aware[
                "forbidden_intent_safety"
            ],
            "equivalence_check_pass_count": sum(
                item["passed"] for item in equivalence_checks
            ),
            "equivalence_check_count": len(equivalence_checks),
            "all_outputs_no_orders": all(
                record["authority"] == "ADVISORY_ONLY"
                for scenario in scenario_results
                for policy in scenario["policies"].values()
                for record in policy["selected"]
            ),
        },
        "claims": {
            "established": [
                "deterministic synthetic fixture construction",
                "policy disagreement is measurable without issuing orders",
                "role-aware contract alignment across the preserved fixture matrix",
            ],
            "not_established": [
                "tactical superiority",
                "causal casualty reduction",
                "action feasibility or acknowledgement",
                "ordinary-live, SFO, siege, ambush, or reinforcement generalization",
            ],
        },
        "evidence_status": "CONTROL_SYNTHETIC",
        "authority": "NO_ORDERS",
    }
    result["result_digest"] = digest(result)
    return result
