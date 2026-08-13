from __future__ import annotations

import copy
import hashlib
from typing import Any

from .canonical import digest
from .tactical_feasibility import (
    TacticalFeasibilityError,
    build_point_query_evidence,
    build_tactical_feasibility_envelope,
)
from .tactical_feasibility_matrix import _build_state_schedule
from .tactical_guarded import (
    TacticalGuardedActionError,
    build_guarded_action_packet_set,
    validate_guarded_action_packet_set,
)
from .tactical_reservation import (
    TacticalReservationError,
    build_endpoint_reservations,
)
from .tactical_reservation_matrix import _packet_set as build_synthetic_packet_set


SUITE_CONTRACT = "TACTICAL_PIPELINE_ADVERSARIAL_SCALING_SUITE_V1"
REPORT_CONTRACT = "TACTICAL_PIPELINE_ADVERSARIAL_SCALING_REPORT_V1"
_ALLOWED_QUERY_MODES = {
    "NONE",
    "ALL_TRUE",
    "ALL_FALSE",
    "ALL_UNAVAILABLE",
    "CYCLIC_MIXED",
}


class TacticalPipelineAuditError(ValueError):
    pass


class _DeterministicStream:
    def __init__(self, seed: int, namespace: str) -> None:
        self.seed = seed
        self.namespace = namespace
        self.counter = 0

    def _block(self) -> bytes:
        value = hashlib.sha256(
            f"{self.seed}|{self.namespace}|{self.counter}".encode("utf-8")
        ).digest()
        self.counter += 1
        return value

    def integer(self, upper: int) -> int:
        if upper <= 0:
            raise TacticalPipelineAuditError("deterministic stream upper bound must be positive")
        return int.from_bytes(self._block()[:8], "big") % upper

    def boolean(self) -> bool:
        return bool(self.integer(2))

    def signed(self, magnitude: int) -> int:
        return self.integer(2 * magnitude + 1) - magnitude


def _validate_suite(
    suite: dict[str, Any],
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    feasibility_suite: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(suite, dict) or suite.get("schema_version") != 1:
        raise TacticalPipelineAuditError("unsupported pipeline audit suite schema")
    if suite.get("suite_contract") != SUITE_CONTRACT:
        raise TacticalPipelineAuditError("unsupported pipeline audit suite contract")
    if not isinstance(suite.get("seed"), int) or isinstance(suite.get("seed"), bool):
        raise TacticalPipelineAuditError("pipeline audit seed must be integer")
    case_count = suite.get("case_count")
    if not isinstance(case_count, int) or isinstance(case_count, bool) or case_count < 128:
        raise TacticalPipelineAuditError("pipeline audit requires at least 128 cases")
    if suite.get("source_trace_digest") != trace_corpus.get("result_digest"):
        raise TacticalPipelineAuditError("pipeline audit trace digest mismatch")
    if suite.get("source_baseline_suite_digest") != baseline_suite.get("result_digest"):
        raise TacticalPipelineAuditError("pipeline audit baseline digest mismatch")
    if suite.get("source_feasibility_suite_digest") != feasibility_suite.get("result_digest"):
        raise TacticalPipelineAuditError("pipeline audit feasibility-suite digest mismatch")
    source_ids = suite.get("source_feasibility_scenario_ids")
    if not isinstance(source_ids, list) or not source_ids or len(source_ids) != len(set(source_ids)):
        raise TacticalPipelineAuditError("pipeline audit source scenarios must be unique nonempty list")
    known = {item["scenario_id"] for item in feasibility_suite["scenarios"]}
    if any(item not in known for item in source_ids):
        raise TacticalPipelineAuditError("pipeline audit references unknown feasibility scenario")
    modes = suite.get("query_modes")
    if not isinstance(modes, list) or set(modes) != _ALLOWED_QUERY_MODES:
        raise TacticalPipelineAuditError("pipeline audit query modes incomplete")
    scales = suite.get("scale_packet_counts")
    if not isinstance(scales, list) or not scales or any(
        not isinstance(item, int) or isinstance(item, bool) or item < 1 for item in scales
    ):
        raise TacticalPipelineAuditError("pipeline scale packet counts invalid")
    if max(scales) < 80:
        raise TacticalPipelineAuditError("pipeline scaling must reach at least 80 packets")
    limits = suite.get("interpretation_limits")
    if not isinstance(limits, list) or not any("not" in str(item).lower() and "outcome" in str(item).lower() for item in limits):
        raise TacticalPipelineAuditError("pipeline suite must disclaim outcome proof")
    material = dict(suite)
    claimed = material.pop("result_digest", None)
    if claimed != digest(material):
        raise TacticalPipelineAuditError("pipeline audit suite digest mismatch")
    return suite


def _query_records(mode: str, envelope: dict[str, Any]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    candidate_rows: list[tuple[str, int, str, str]] = []
    for plan in envelope["plan_envelopes"]:
        for candidate in plan["candidate_points"]:
            candidate_rows.append(
                (
                    candidate["candidate_id"],
                    int(candidate["rank"]),
                    plan["objective_type"],
                    plan["actor_role"],
                )
            )
    candidate_rows.sort(key=lambda item: (item[2], item[3], item[1], item[0]))
    for index, (candidate_id, rank, _objective_type, _actor_role) in enumerate(candidate_rows):
        if mode == "ALL_TRUE":
            result = "QUERY_TRUE"
        elif mode == "ALL_FALSE":
            result = "QUERY_FALSE"
        elif mode == "ALL_UNAVAILABLE":
            result = "UNAVAILABLE"
        elif mode == "CYCLIC_MIXED":
            result = ("QUERY_TRUE", "QUERY_FALSE", "UNAVAILABLE")[(rank + index) % 3]
        else:
            continue
        records.append({"candidate_id": candidate_id, "query_result": result})
    return records


def _run_pipeline_case(
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    source_scenario: dict[str, Any],
    query_mode: str,
    *,
    reverse_units: bool,
    translation: tuple[float, float, float] | None,
) -> dict[str, Any]:
    state, schedule = _build_state_schedule(
        trace_corpus,
        baseline_suite,
        source_scenario,
        reverse_units=reverse_units,
        translation=translation,
    )
    base = build_tactical_feasibility_envelope(state, schedule)
    records = _query_records(query_mode, base)
    evidence = None
    if query_mode != "NONE":
        evidence = build_point_query_evidence(
            state,
            schedule,
            records,
            evidence_source="CONTROL_SYNTHETIC_FIXTURE",
        )
    envelope = build_tactical_feasibility_envelope(
        state,
        schedule,
        point_query_evidence=evidence,
    )
    guarded = build_guarded_action_packet_set(state, schedule, envelope)
    reservations = build_endpoint_reservations(guarded)
    return {
        "state": state,
        "schedule": schedule,
        "envelope": envelope,
        "guarded": guarded,
        "reservations": reservations,
    }


def _semantic_signature(result: dict[str, Any]) -> dict[str, Any]:
    guarded = result["guarded"]
    reservations = result["reservations"]
    return {
        "guarded": sorted(
            [
                {
                    "objective_type": item["objective_type"],
                    "actor_role": item["actor_role"],
                    "severity": item["severity"],
                    "readiness_class": item["readiness_class"],
                    "eligible_candidate_count": item["eligible_candidate_count"],
                    "selected_candidate_rank": item["selected_candidate_rank"],
                }
                for item in guarded["packets"]
            ],
            key=lambda item: (
                item["objective_type"],
                item["actor_role"],
                item["severity"],
                item["readiness_class"],
                item["eligible_candidate_count"],
                item["selected_candidate_rank"] or -1,
            ),
        ),
        "reservation_count": reservations["reservation_count"],
        "unreserved_ready_packet_count": reservations["unreserved_ready_packet_count"],
        "reservations": sorted(
            [
                {
                    "objective_type": item["objective_type"],
                    "severity": item["severity"],
                    "candidate_rank": item["candidate_rank"],
                }
                for item in reservations["reservations"]
            ],
            key=lambda item: (item["objective_type"], item["severity"], item["candidate_rank"]),
        ),
        "unreserved": sorted(
            [
                {
                    "severity": item["severity"],
                    "reason": item["reason"],
                }
                for item in reservations["unreserved_ready_packets"]
            ],
            key=lambda item: (item["severity"], item["reason"]),
        ),
    }


def _invariant_checks(result: dict[str, Any]) -> dict[str, bool]:
    envelope = result["envelope"]
    guarded = result["guarded"]
    reservations = result["reservations"]
    actors = [item["actor_unit_id"] for item in reservations["reservations"]]
    return {
        "authority_no_orders": envelope["authority"] == guarded["authority"] == reservations["authority"] == "NO_ORDERS",
        "application_prohibited": guarded["application_authority"] == reservations["application_authority"] == "PROHIBITED",
        "no_issue_or_execution": all(
            item["project_issue_status"] == "NOT_ATTEMPTED"
            and item["execution_status"] == "NOT_ISSUED"
            and item["direct_acknowledgement_status"] == "UNAVAILABLE_NOT_OBSERVED"
            for item in guarded["packets"]
        ) and all(item["execution_status"] == "NOT_ISSUED" for item in reservations["reservations"]),
        "candidate_bounds": all(
            plan["candidate_count"] <= 3
            and all(float(candidate["horizontal_displacement_m"]) <= 120.000001 for candidate in plan["candidate_points"])
            for plan in envelope["plan_envelopes"]
        ),
        "reservation_cardinality": reservations["reservation_count"] <= guarded["ready_packet_count"],
        "actor_exclusivity": len(actors) == len(set(actors)),
        "endpoint_separation": reservations["minimum_selected_endpoint_separation_m"] is None
        or reservations["minimum_selected_endpoint_separation_m"] + 1e-9 >= reservations["minimum_endpoint_separation_m"],
    }


def _duplicate_plan_attack(result: dict[str, Any]) -> bool:
    envelope = result["envelope"]
    if not envelope["plan_envelopes"]:
        return True
    forged = copy.deepcopy(envelope)
    forged["plan_envelopes"].append(copy.deepcopy(forged["plan_envelopes"][0]))
    forged["plan_envelope_count"] = len(forged["plan_envelopes"])
    forged["candidate_point_count"] = sum(item["candidate_count"] for item in forged["plan_envelopes"])
    forged["point_query_supported_plan_count"] = sum(item["feasibility_class"] == "POINT_QUERY_SUPPORTED_ONLY" for item in forged["plan_envelopes"])
    forged["point_query_rejected_plan_count"] = sum(item["feasibility_class"] == "POINT_QUERY_REJECTED" for item in forged["plan_envelopes"])
    forged["query_ready_unobserved_plan_count"] = sum(item["feasibility_class"] == "QUERY_READY_NOT_OBSERVED" for item in forged["plan_envelopes"])
    forged.pop("result_digest", None)
    forged["result_digest"] = digest(forged)
    try:
        build_guarded_action_packet_set(result["state"], result["schedule"], forged)
    except TacticalGuardedActionError:
        return True
    return False


def _authority_attack(result: dict[str, Any]) -> bool:
    forged = copy.deepcopy(result["guarded"])
    forged["authority"] = "CONTROL"
    forged.pop("result_digest", None)
    forged["result_digest"] = digest(forged)
    try:
        build_endpoint_reservations(forged)
    except TacticalReservationError:
        return True
    return False


def _packet_identity_attack(result: dict[str, Any]) -> bool:
    guarded = result["guarded"]
    if not guarded["packets"]:
        return True
    forged = copy.deepcopy(guarded)
    forged["packets"][0]["packet_id"] = "f" * 64
    forged["packets"][0].pop("result_digest", None)
    forged["packets"][0]["result_digest"] = digest(forged["packets"][0])
    forged.pop("result_digest", None)
    forged["result_digest"] = digest(forged)
    try:
        validate_guarded_action_packet_set(forged)
    except TacticalGuardedActionError:
        return True
    return False


def _duplicate_actor_attack(result: dict[str, Any]) -> bool:
    guarded = result["guarded"]
    if len(guarded["packets"]) < 2:
        return True
    forged = copy.deepcopy(guarded)
    forged["packets"][1]["actor_unit_id"] = forged["packets"][0]["actor_unit_id"]
    forged["packets"][1].pop("result_digest", None)
    forged["packets"][1]["result_digest"] = digest(forged["packets"][1])
    forged.pop("result_digest", None)
    forged["result_digest"] = digest(forged)
    try:
        validate_guarded_action_packet_set(forged)
    except TacticalGuardedActionError:
        return True
    return False


def _scale_packet_specs(count: int, *, clustered: bool) -> list[dict[str, Any]]:
    specs = []
    for index in range(count):
        if clustered:
            x = float((index % 8) * 4)
            z = float((index // 8) * 4)
        else:
            x = float(index * 20)
            z = 0.0
        specs.append(
            {
                "packet_key": f"scale_{count}_{'cluster' if clustered else 'line'}_{index:03d}",
                "severity": ("LOW", "MEDIUM", "HIGH", "CRITICAL")[index % 4],
                "utility": round(0.2 + ((index * 37) % 700) / 1000, 6),
                "points": [[x, 0.0, z], [x + 14.0, 0.0, z]],
                "readiness": "READY",
                "objective_type": "RELIEVE_FRONTLINE",
            }
        )
    return specs


def _legacy_translation_tie_signature(packet_set: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    # Preserved model of the pre-v0.1X tie-break: candidate ids contain point
    # coordinates, so equal-weight solutions can change under translation.
    packets = sorted(packet_set["packets"], key=lambda item: item["packet_id"])
    if len(packets) != 2:
        raise TacticalPipelineAuditError("legacy tie fixture must contain two packets")
    solutions = []
    for left in packets[0]["eligible_candidates"]:
        for right in packets[1]["eligible_candidates"]:
            dx = float(left["point"]["x"]) - float(right["point"]["x"])
            dz = float(left["point"]["z"]) - float(right["point"]["z"])
            if (dx * dx + dz * dz) ** 0.5 < 12.0 - 1e-9:
                continue
            rank_score = (100 - int(left["rank"])) + (100 - int(right["rank"]))
            signature = tuple(sorted(((packets[0]["packet_id"], left["candidate_id"]), (packets[1]["packet_id"], right["candidate_id"]))))
            solutions.append((rank_score, signature))
    if not solutions:
        return ()
    best_score = max(item[0] for item in solutions)
    return min(item[1] for item in solutions if item[0] == best_score)


def _translation_tie_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    specs = [
        {
            "packet_key": "tie_left",
            "severity": "HIGH",
            "utility": 0.5,
            "points": [[0.0, 0.0, 0.0], [20.0, 0.0, 0.0]],
            "readiness": "READY",
            "objective_type": "RELIEVE_FRONTLINE",
        },
        {
            "packet_key": "tie_right",
            "severity": "HIGH",
            "utility": 0.5,
            "points": [[0.0, 0.0, 0.0], [-20.0, 0.0, 0.0]],
            "readiness": "READY",
            "objective_type": "RELIEVE_FRONTLINE",
        },
    ]
    base = build_synthetic_packet_set(specs)
    translated_specs = copy.deepcopy(specs)
    for spec in translated_specs:
        for point in spec["points"]:
            point[0] += 431.0
            point[1] += 7.0
            point[2] -= 283.0
    translated = build_synthetic_packet_set(translated_specs)
    return base, translated


def run_tactical_pipeline_audit(
    trace_corpus: dict[str, Any],
    baseline_suite: dict[str, Any],
    feasibility_suite: dict[str, Any],
    audit_suite: dict[str, Any],
) -> dict[str, Any]:
    audit_suite = _validate_suite(
        audit_suite, trace_corpus, baseline_suite, feasibility_suite
    )
    source_by_id = {item["scenario_id"]: item for item in feasibility_suite["scenarios"]}
    source_ids = audit_suite["source_feasibility_scenario_ids"]
    modes = audit_suite["query_modes"]
    cases: list[dict[str, Any]] = []
    all_passed = True
    total_packets = 0
    total_candidates = 0
    total_reservations = 0
    exact_solver_cases = 0
    fallback_solver_cases = 0
    max_search_nodes = 0
    for case_index in range(audit_suite["case_count"]):
        stream = _DeterministicStream(audit_suite["seed"], f"case:{case_index}")
        source_id = source_ids[stream.integer(len(source_ids))]
        source = source_by_id[source_id]
        mode = modes[stream.integer(len(modes))]
        reverse = stream.boolean()
        translation = (
            float(stream.signed(2000)),
            float(stream.signed(50)),
            float(stream.signed(2000)),
        )
        result = _run_pipeline_case(
            trace_corpus,
            baseline_suite,
            source,
            mode,
            reverse_units=reverse,
            translation=translation,
        )
        replay = _run_pipeline_case(
            trace_corpus,
            baseline_suite,
            source,
            mode,
            reverse_units=reverse,
            translation=translation,
        )
        checks = _invariant_checks(result)
        checks["deterministic_replay"] = result["reservations"]["result_digest"] == replay["reservations"]["result_digest"]
        transformed = _run_pipeline_case(
            trace_corpus,
            baseline_suite,
            source,
            mode,
            reverse_units=not reverse,
            translation=(translation[0] + 317.0, translation[1] + 5.0, translation[2] - 227.0),
        )
        checks["representation_invariance"] = _semantic_signature(result) == _semantic_signature(transformed)
        if case_index % 17 == 0:
            checks["duplicate_plan_attack_rejected"] = _duplicate_plan_attack(result)
        if case_index % 19 == 0:
            checks["authority_attack_rejected"] = _authority_attack(result)
        if case_index % 23 == 0:
            checks["packet_identity_attack_rejected"] = _packet_identity_attack(result)
        if case_index % 29 == 0:
            checks["duplicate_actor_attack_rejected"] = _duplicate_actor_attack(result)
        passed = all(checks.values())
        all_passed = all_passed and passed
        reservation = result["reservations"]
        exact_solver_cases += int(reservation["solver_mode"] == "EXACT_BRANCH_AND_BOUND")
        fallback_solver_cases += int("FALLBACK" in reservation["solver_mode"])
        max_search_nodes = max(max_search_nodes, reservation["search_node_count"])
        total_packets += result["guarded"]["packet_count"]
        total_candidates += result["envelope"]["candidate_point_count"]
        total_reservations += reservation["reservation_count"]
        cases.append(
            {
                "case_id": f"case_{case_index:04d}",
                "source_scenario_id": source_id,
                "query_mode": mode,
                "passed": passed,
                "checks": checks,
                "packet_count": result["guarded"]["packet_count"],
                "candidate_point_count": result["envelope"]["candidate_point_count"],
                "ready_packet_count": result["guarded"]["ready_packet_count"],
                "reservation_count": reservation["reservation_count"],
                "solver_mode": reservation["solver_mode"],
                "search_node_count": reservation["search_node_count"],
                "result_digest": reservation["result_digest"],
            }
        )

    scale_results: list[dict[str, Any]] = []
    for count in audit_suite["scale_packet_counts"]:
        for clustered in (False, True):
            packet_set = build_synthetic_packet_set(
                _scale_packet_specs(count, clustered=clustered)
            )
            result = build_endpoint_reservations(packet_set)
            check = (
                result["reservation_count"] <= count
                and result["ready_packet_count"] == count
                and result["authority"] == "NO_ORDERS"
                and (
                    result["minimum_selected_endpoint_separation_m"] is None
                    or result["minimum_selected_endpoint_separation_m"] + 1e-9 >= result["minimum_endpoint_separation_m"]
                )
            )
            all_passed = all_passed and check
            scale_results.append(
                {
                    "packet_count": count,
                    "layout": "CLUSTERED_GRID" if clustered else "SEPARATED_LINE",
                    "passed": check,
                    "reservation_count": result["reservation_count"],
                    "unreserved_count": result["unreserved_ready_packet_count"],
                    "solver_mode": result["solver_mode"],
                    "optimality_status": result["optimality_status"],
                    "search_node_count": result["search_node_count"],
                    "result_digest": result["result_digest"],
                }
            )

    tie_base, tie_translated = _translation_tie_fixture()
    legacy_base = _legacy_translation_tie_signature(tie_base)
    legacy_translated = _legacy_translation_tie_signature(tie_translated)
    corrected_base = build_endpoint_reservations(tie_base)
    corrected_translated = build_endpoint_reservations(tie_translated)
    corrected_signature_equal = _semantic_signature(
        {"guarded": tie_base, "reservations": corrected_base}
    ) == _semantic_signature(
        {"guarded": tie_translated, "reservations": corrected_translated}
    )
    defect_regressions = {
        "duplicate_plan_identity_collapse": {
            "before_status": "ACCEPTED_FORGED_DUPLICATE_PLAN",
            "after_status": "REJECTED_FAIL_CLOSED",
            "regression_passed": all(
                item["checks"].get("duplicate_plan_attack_rejected", True)
                for item in cases
            ),
        },
        "coordinate_hash_tie_break": {
            "before_translation_signature_changed": legacy_base != legacy_translated,
            "after_semantic_signature_stable": corrected_signature_equal,
            "regression_passed": legacy_base != legacy_translated and corrected_signature_equal,
        },
    }
    attack_regressions = {
        "guarded_packet_identity_forgery": all(
            item["checks"].get("packet_identity_attack_rejected", True)
            for item in cases
        ),
        "guarded_actor_double_booking": all(
            item["checks"].get("duplicate_actor_attack_rejected", True)
            for item in cases
        ),
    }
    all_passed = (
        all_passed
        and all(item["regression_passed"] for item in defect_regressions.values())
        and all(attack_regressions.values())
    )

    report: dict[str, Any] = {
        "schema_version": 1,
        "report_contract": REPORT_CONTRACT,
        "suite_id": audit_suite["suite_id"],
        "seed": audit_suite["seed"],
        "case_count": len(cases),
        "case_pass_count": sum(item["passed"] for item in cases),
        "all_cases_passed": all_passed,
        "cases": cases,
        "scale_case_count": len(scale_results),
        "scale_pass_count": sum(item["passed"] for item in scale_results),
        "scale_results": scale_results,
        "defect_regressions": defect_regressions,
        "attack_regressions": attack_regressions,
        "summary": {
            "total_guarded_packets": total_packets,
            "total_candidate_points": total_candidates,
            "total_endpoint_reservations": total_reservations,
            "exact_solver_case_count": exact_solver_cases,
            "fallback_solver_case_count": fallback_solver_cases,
            "maximum_search_node_count": max_search_nodes,
            "maximum_scale_packet_count": max(audit_suite["scale_packet_counts"]),
        },
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_SYNTHETIC_ADVERSARIAL_AND_SCALING",
        "counterfactual_status": "UNVERIFIED",
        "interpretation_limits": [
            "Randomized cases are deterministic contract fuzzing, not WH3 battle simulations or optimal action labels.",
            "Structural scale results report solver mode and search work, not live turn-time or frame-time performance.",
            "No route, formation, command legality, acknowledgement, execution, casualty, or outcome claim is made.",
        ],
    }
    report["result_digest"] = digest(report)
    return report
