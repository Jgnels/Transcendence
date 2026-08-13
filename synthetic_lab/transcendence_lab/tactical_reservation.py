from __future__ import annotations

import math
from typing import Any

from .canonical import digest
from .tactical_guarded import (
    GUARDED_PACKET_SET_CONTRACT,
    TacticalGuardedActionError,
    validate_guarded_action_packet_set,
)


RESERVATION_CONTRACT = "TACTICAL_ENDPOINT_RESERVATION_V1"
RESERVATION_SET_CONTRACT = "TACTICAL_ENDPOINT_RESERVATION_SET_V1"
RESERVATION_TRAJECTORY_CONTRACT = "TACTICAL_ENDPOINT_RESERVATION_TRAJECTORY_V1"
DEFAULT_MINIMUM_ENDPOINT_SEPARATION_M = 12.0
MAX_EXACT_READY_PACKETS = 16
MAX_EXACT_SEARCH_NODES = 250_000

_SEVERITY_WEIGHT = {
    "LOW": 1,
    "MEDIUM": 10,
    "HIGH": 100,
    "CRITICAL": 1000,
}


class TacticalReservationError(ValueError):
    pass


def _point(candidate: dict[str, Any]) -> tuple[float, float, float]:
    try:
        values = (
            float(candidate["point"]["x"]),
            float(candidate["point"]["y"]),
            float(candidate["point"]["z"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise TacticalReservationError("invalid reservation endpoint") from error
    if not all(math.isfinite(value) for value in values):
        raise TacticalReservationError("reservation endpoint must be finite")
    return values


def _horizontal_distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.hypot(a[0] - b[0], a[2] - b[2])


def _packet_weight(packet: dict[str, Any]) -> int:
    severity = packet.get("severity")
    if severity not in _SEVERITY_WEIGHT:
        raise TacticalReservationError("invalid packet severity")
    utility = packet.get("objective_utility")
    if not isinstance(utility, (int, float)) or isinstance(utility, bool) or not math.isfinite(float(utility)):
        raise TacticalReservationError("invalid packet objective utility")
    return _SEVERITY_WEIGHT[severity] * 10**12 + int(round(float(utility) * 10**9))


def _candidate_weight(packet: dict[str, Any], candidate: dict[str, Any]) -> int:
    rank = candidate.get("rank")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        raise TacticalReservationError("candidate rank must be positive integer")
    return _packet_weight(packet) + max(0, 100 - rank)


def _conflicts(
    point: tuple[float, float, float],
    selected: list[tuple[float, float, float]],
    minimum_separation_m: float,
) -> bool:
    return any(_horizontal_distance(point, other) < minimum_separation_m - 1e-9 for other in selected)


def _packet_signature(packet: dict[str, Any], candidate: dict[str, Any]) -> tuple[str, int]:
    # Candidate ids include coordinates. Using them as an optimization tie-break
    # made equal decisions sensitive to a uniform battlefield translation. Rank
    # is the canonical within-packet preference and is translation invariant.
    return packet["packet_id"], int(candidate["rank"])


def _canonical_ready_packets(packet_set: dict[str, Any]) -> list[dict[str, Any]]:
    ready = [
        item
        for item in packet_set["packets"]
        if item["readiness_class"] == "READY_POINT_SUPPORTED_SHADOW_ONLY"
    ]
    for packet in ready:
        candidates = packet.get("eligible_candidates", [])
        if not candidates:
            raise TacticalReservationError("ready packet has no eligible endpoint")
        for candidate in candidates:
            _point(candidate)
    return sorted(
        ready,
        key=lambda item: (
            -_SEVERITY_WEIGHT[item["severity"]],
            -float(item["objective_utility"]),
            item["packet_id"],
        ),
    )


def _greedy(
    packets: list[dict[str, Any]], minimum_separation_m: float
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], int]:
    selected: list[tuple[dict[str, Any], dict[str, Any]]] = []
    points: list[tuple[float, float, float]] = []
    nodes = 0
    for packet in packets:
        options = sorted(
            packet["eligible_candidates"],
            key=lambda item: (
                -_candidate_weight(packet, item),
                item["rank"],
                item["candidate_id"],
            ),
        )
        for candidate in options:
            nodes += 1
            point = _point(candidate)
            if not _conflicts(point, points, minimum_separation_m):
                selected.append((packet, candidate))
                points.append(point)
                break
    return selected, nodes


def _exact_branch_and_bound(
    packets: list[dict[str, Any]], minimum_separation_m: float
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], int, bool]:
    options = [
        sorted(
            packet["eligible_candidates"],
            key=lambda item: (
                -_candidate_weight(packet, item),
                item["rank"],
                item["candidate_id"],
            ),
        )
        for packet in packets
    ]
    maxima = [max(_candidate_weight(packet, item) for item in candidates) for packet, candidates in zip(packets, options, strict=True)]
    suffix_upper = [0] * (len(packets) + 1)
    for index in range(len(packets) - 1, -1, -1):
        suffix_upper[index] = suffix_upper[index + 1] + maxima[index]

    best_weight = -1
    best_count = -1
    best_signature: tuple[tuple[str, str], ...] | None = None
    best_selection: list[tuple[dict[str, Any], dict[str, Any]]] = []
    nodes = 0
    exhausted = False

    def visit(
        index: int,
        selected: list[tuple[dict[str, Any], dict[str, Any]]],
        points: list[tuple[float, float, float]],
        weight: int,
    ) -> None:
        nonlocal best_weight, best_count, best_signature, best_selection, nodes, exhausted
        if exhausted:
            return
        nodes += 1
        if nodes > MAX_EXACT_SEARCH_NODES:
            exhausted = True
            return
        if weight + suffix_upper[index] < best_weight:
            return
        if index >= len(packets):
            signature = tuple(sorted(_packet_signature(packet, candidate) for packet, candidate in selected))
            count = len(selected)
            if (
                weight > best_weight
                or (weight == best_weight and count > best_count)
                or (
                    weight == best_weight
                    and count == best_count
                    and (best_signature is None or signature < best_signature)
                )
            ):
                best_weight = weight
                best_count = count
                best_signature = signature
                best_selection = list(selected)
            return
        packet = packets[index]
        for candidate in options[index]:
            point = _point(candidate)
            if _conflicts(point, points, minimum_separation_m):
                continue
            selected.append((packet, candidate))
            points.append(point)
            visit(
                index + 1,
                selected,
                points,
                weight + _candidate_weight(packet, candidate),
            )
            points.pop()
            selected.pop()
        visit(index + 1, selected, points, weight)

    visit(0, [], [], 0)
    return best_selection, nodes, exhausted


def build_endpoint_reservations(
    packet_set: dict[str, Any],
    *,
    minimum_endpoint_separation_m: float = DEFAULT_MINIMUM_ENDPOINT_SEPARATION_M,
) -> dict[str, Any]:
    try:
        validate_guarded_action_packet_set(packet_set)
    except TacticalGuardedActionError as error:
        raise TacticalReservationError(str(error)) from error
    if packet_set.get("packet_set_contract") != GUARDED_PACKET_SET_CONTRACT:
        raise TacticalReservationError("unsupported guarded packet source")
    if not isinstance(minimum_endpoint_separation_m, (int, float)) or isinstance(minimum_endpoint_separation_m, bool):
        raise TacticalReservationError("minimum endpoint separation must be numeric")
    minimum_endpoint_separation_m = float(minimum_endpoint_separation_m)
    if not math.isfinite(minimum_endpoint_separation_m) or minimum_endpoint_separation_m <= 0:
        raise TacticalReservationError("minimum endpoint separation must be finite and positive")

    ready = _canonical_ready_packets(packet_set)
    solver_mode = "EXACT_BRANCH_AND_BOUND"
    optimality_status = "EXACT_WITHIN_BOUNDED_PACKET_LIMIT"
    if len(ready) <= MAX_EXACT_READY_PACKETS:
        selected, nodes, exhausted = _exact_branch_and_bound(ready, minimum_endpoint_separation_m)
        if exhausted:
            selected, greedy_nodes = _greedy(ready, minimum_endpoint_separation_m)
            nodes += greedy_nodes
            solver_mode = "DETERMINISTIC_GREEDY_SEARCH_BUDGET_FALLBACK"
            optimality_status = "UNVERIFIED_FALLBACK"
    else:
        selected, nodes = _greedy(ready, minimum_endpoint_separation_m)
        solver_mode = "DETERMINISTIC_GREEDY_PACKET_LIMIT_FALLBACK"
        optimality_status = "UNVERIFIED_FALLBACK"

    selected_by_packet = {packet["packet_id"]: candidate for packet, candidate in selected}
    selected_points = [_point(candidate) for _, candidate in selected]
    reservations: list[dict[str, Any]] = []
    for packet, candidate in selected:
        record: dict[str, Any] = {
            "schema_version": 1,
            "reservation_contract": RESERVATION_CONTRACT,
            "reservation_id": digest(
                {
                    "source_packet_id": packet["packet_id"],
                    "candidate_id": candidate["candidate_id"],
                }
            ),
            "source_packet_id": packet["packet_id"],
            "plan_instance_id": packet["plan_instance_id"],
            "objective_id": packet["objective_id"],
            "objective_type": packet["objective_type"],
            "actor_unit_id": packet["actor_unit_id"],
            "severity": packet["severity"],
            "objective_utility": packet["objective_utility"],
            "candidate_id": candidate["candidate_id"],
            "candidate_rank": candidate["rank"],
            "endpoint": candidate["point"],
            "reservation_status": "SHADOW_ENDPOINT_RESERVED_NOT_ISSUED",
            "route_status": "UNVERIFIED",
            "formation_status": "UNVERIFIED",
            "collision_status": "ENDPOINT_SEPARATION_ONLY",
            "command_legality_status": "UNVERIFIED",
            "project_issue_status": "NOT_ATTEMPTED",
            "direct_acknowledgement_status": "UNAVAILABLE_NOT_OBSERVED",
            "execution_status": "NOT_ISSUED",
            "outcome_status": "UNVERIFIED_NOT_ATTRIBUTED",
            "authority": "NO_ORDERS",
        }
        record["result_digest"] = digest(record)
        reservations.append(record)
    reservations.sort(key=lambda item: (item["actor_unit_id"], item["objective_id"]))

    unreserved: list[dict[str, Any]] = []
    for packet in ready:
        if packet["packet_id"] in selected_by_packet:
            continue
        any_nonconflicting = any(
            not _conflicts(_point(candidate), selected_points, minimum_endpoint_separation_m)
            for candidate in packet["eligible_candidates"]
        )
        reason = (
            "SOLVER_FALLBACK_SKIPPED_WITHOUT_CONFLICT_PROOF"
            if optimality_status == "UNVERIFIED_FALLBACK" and any_nonconflicting
            else "ENDPOINT_CONFLICT_WITH_HIGHER_VALUE_PACKET"
        )
        record = {
            "source_packet_id": packet["packet_id"],
            "plan_instance_id": packet["plan_instance_id"],
            "objective_id": packet["objective_id"],
            "actor_unit_id": packet["actor_unit_id"],
            "severity": packet["severity"],
            "reason": reason,
            "eligible_candidate_count": packet["eligible_candidate_count"],
        }
        record["result_digest"] = digest(record)
        unreserved.append(record)
    unreserved.sort(key=lambda item: (item["actor_unit_id"], item["objective_id"]))

    pair_distances = [
        _horizontal_distance(selected_points[i], selected_points[j])
        for i in range(len(selected_points))
        for j in range(i + 1, len(selected_points))
    ]
    result: dict[str, Any] = {
        "schema_version": 1,
        "reservation_set_contract": RESERVATION_SET_CONTRACT,
        "slice_id": packet_set["slice_id"],
        "time_ms": packet_set["time_ms"],
        "source_guarded_packet_set_digest": packet_set["result_digest"],
        "minimum_endpoint_separation_m": round(minimum_endpoint_separation_m, 6),
        "ready_packet_count": len(ready),
        "reservation_count": len(reservations),
        "unreserved_ready_packet_count": len(unreserved),
        "nonready_packet_count": packet_set["packet_count"] - len(ready),
        "reservations": reservations,
        "unreserved_ready_packets": unreserved,
        "solver_mode": solver_mode,
        "optimality_status": optimality_status,
        "search_node_count": nodes,
        "minimum_selected_endpoint_separation_m": (
            round(min(pair_distances), 6) if pair_distances else None
        ),
        "endpoint_conflict_count": sum(
            item["reason"] == "ENDPOINT_CONFLICT_WITH_HIGHER_VALUE_PACKET"
            for item in unreserved
        ),
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_OFFLINE_ENDPOINT_RESERVATION",
        "counterfactual_status": "UNVERIFIED",
        "interpretation_limits": [
            "The reservation solver separates endpoints only; it does not inspect route crossings or formation footprints.",
            "The minimum separation is a project-owned collision-avoidance development contract, not measured unit width.",
            "A reservation is a simultaneous shadow-plan record, not a WH3 order or acknowledgement.",
            "Fallback mode is deterministic but does not claim global optimality.",
        ],
    }
    result["result_digest"] = digest(result)
    return result


def build_trace_endpoint_reservations(
    trace_corpus: dict[str, Any],
    *,
    capability_profile: dict[str, Any] | None = None,
    minimum_endpoint_separation_m: float = DEFAULT_MINIMUM_ENDPOINT_SEPARATION_M,
) -> dict[str, Any]:
    from .tactical_guarded import build_trace_guarded_action_packets

    guarded = build_trace_guarded_action_packets(
        trace_corpus,
        capability_profile=capability_profile,
    )
    reservation_sets = [
        build_endpoint_reservations(
            packet_set,
            minimum_endpoint_separation_m=minimum_endpoint_separation_m,
        )
        for packet_set in guarded["packet_sets"]
    ]
    solver_modes: dict[str, int] = {}
    for item in reservation_sets:
        solver_modes[item["solver_mode"]] = solver_modes.get(item["solver_mode"], 0) + 1
    result: dict[str, Any] = {
        "schema_version": 1,
        "trajectory_contract": RESERVATION_TRAJECTORY_CONTRACT,
        "source_id": "BATTLE4_EILHART_VISIBILITY_SAFE_TRACE",
        "source_trace_digest": guarded["source_trace_digest"],
        "source_guarded_action_trajectory_digest": guarded["result_digest"],
        "slice_count": len(reservation_sets),
        "reservation_sets": reservation_sets,
        "summary": {
            "ready_packet_count": sum(item["ready_packet_count"] for item in reservation_sets),
            "reservation_count": sum(item["reservation_count"] for item in reservation_sets),
            "unreserved_ready_packet_count": sum(item["unreserved_ready_packet_count"] for item in reservation_sets),
            "nonready_packet_count": sum(item["nonready_packet_count"] for item in reservation_sets),
            "endpoint_conflict_count": sum(item["endpoint_conflict_count"] for item in reservation_sets),
            "solver_mode_counts": dict(sorted(solver_modes.items())),
            "minimum_endpoint_separation_m": round(float(minimum_endpoint_separation_m), 6),
        },
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_OFFLINE_DERIVED_FROM_OBSERVED_INPUT",
        "counterfactual_status": "UNVERIFIED",
        "interpretation_limits": [
            "Battle 4 contains no candidate-level QUERY_TRUE evidence, so it produces no endpoint reservations.",
            "The absence of reservations is an evidence abstention, not proof that the objectives are infeasible.",
            "Endpoint separation does not establish route, formation, collision, legality, execution, or outcome.",
        ],
    }
    result["result_digest"] = digest(result)
    return result
