from __future__ import annotations

import math
from typing import Any

from .canonical import digest

TRACE_CONTRACT = "NATIVE_CAI_PRIVILEGED_DIAGNOSTIC_TRACE_V1"
RESULT_CONTRACT = "NATIVE_CAI_PRIVILEGED_DIAGNOSTIC_EXPOSURE_RESULT_V1"
AUTHORITY = "NO_ORDERS"
APPLICATION_AUTHORITY = "PROHIBITED"
RESEARCH_VISIBILITY = "PRIVILEGED_OMNISCIENT_DIAGNOSTIC"
APPLICATION_ELIGIBLE = False

QUALIFICATION_THRESHOLDS = {
    "paired_faction_turn_count": 20,
    "matched_force_turn_pairs": 50,
    "moved_force_turn_pairs": 10,
    "trajectory_exposure_pairs": 5,
}
HEADING_REVERSAL_COSINE_MAX = -0.5


class NativeDiagnosticError(ValueError):
    pass


def _force_map(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for force in snapshot.get("forces", []):
        key = str(force.get("force_cqi", ""))
        if not key or key == "-1":
            raise NativeDiagnosticError("diagnostic force must have a stable force_cqi")
        if key in rows:
            raise NativeDiagnosticError(f"duplicate force_cqi in one snapshot: {key}")
        rows[key] = force
    return rows


def _vector(left: dict[str, Any], right: dict[str, Any]) -> tuple[float, float]:
    return float(right["x"]) - float(left["x"]), float(right["y"]) - float(left["y"])


def _cosine(left: tuple[float, float], right: tuple[float, float]) -> float | None:
    a = math.hypot(*left)
    b = math.hypot(*right)
    if a == 0.0 or b == 0.0:
        return None
    return max(-1.0, min(1.0, (left[0] * right[0] + left[1] * right[1]) / (a * b)))


def _validate_trace(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("contract") != TRACE_CONTRACT:
        raise NativeDiagnosticError("unexpected diagnostic trace contract")
    if raw.get("authority") != AUTHORITY:
        raise NativeDiagnosticError("diagnostic trace must remain NO_ORDERS")
    if raw.get("application_authority") != APPLICATION_AUTHORITY:
        raise NativeDiagnosticError("diagnostic trace application authority must remain PROHIBITED")
    if raw.get("research_visibility") != RESEARCH_VISIBILITY:
        raise NativeDiagnosticError("diagnostic trace must declare privileged research visibility")
    if raw.get("application_eligible") is not False:
        raise NativeDiagnosticError("privileged diagnostic traces are never application eligible")
    observations = raw.get("observations")
    if not isinstance(observations, list):
        raise NativeDiagnosticError("observations must be a list")
    seen: set[tuple[int, str]] = set()
    for row in observations:
        turn = int(row["turn"])
        faction = str(row["faction"])
        key = (turn, faction)
        if key in seen:
            raise NativeDiagnosticError(f"duplicate faction-turn observation: {key}")
        seen.add(key)
        if not faction:
            raise NativeDiagnosticError("faction key cannot be empty")
        for phase in ("start", "end"):
            snapshot = row.get(phase)
            if not isinstance(snapshot, dict):
                raise NativeDiagnosticError(f"paired observation missing {phase} snapshot")
            _force_map(snapshot)
    return raw


def analyze_native_diagnostic_exposure(raw_trace: dict[str, Any]) -> dict[str, Any]:
    trace = _validate_trace(raw_trace)
    observations = sorted(trace["observations"], key=lambda row: (int(row["turn"]), str(row["faction"])))
    matched_pairs = 0
    moved_pairs = 0
    stationary_pairs = 0
    health_observed_pairs = 0
    endpoint_absence_from_end = 0
    endpoint_new_at_end = 0
    per_force_end: dict[tuple[str, str], list[tuple[int, dict[str, Any]]]] = {}

    for row in observations:
        start = _force_map(row["start"])
        end = _force_map(row["end"])
        shared = sorted(set(start) & set(end))
        matched_pairs += len(shared)
        endpoint_absence_from_end += len(set(start) - set(end))
        endpoint_new_at_end += len(set(end) - set(start))
        for force_id in shared:
            left, right = start[force_id], end[force_id]
            dx, dy = _vector(left, right)
            if dx == 0.0 and dy == 0.0:
                stationary_pairs += 1
            else:
                moved_pairs += 1
            if float(left.get("average_unit_health_pct", -1)) >= 0 and float(right.get("average_unit_health_pct", -1)) >= 0:
                health_observed_pairs += 1
        for force_id, force in end.items():
            per_force_end.setdefault((str(row["faction"]), force_id), []).append((int(row["turn"]), force))

    trajectory_exposure_pairs = 0
    heading_reversal_candidates = 0
    force_with_three_or_more_endpoints = 0
    for rows in per_force_end.values():
        rows.sort(key=lambda item: item[0])
        if len(rows) >= 3:
            force_with_three_or_more_endpoints += 1
        vectors: list[tuple[int, int, tuple[float, float]]] = []
        for (left_turn, left), (right_turn, right) in zip(rows, rows[1:]):
            if right_turn - left_turn != 1:
                continue
            vector = _vector(left, right)
            if vector == (0.0, 0.0):
                vectors.append((left_turn, right_turn, vector))
            else:
                vectors.append((left_turn, right_turn, vector))
        for left, right in zip(vectors, vectors[1:]):
            if left[1] != right[0]:
                continue
            if left[2] == (0.0, 0.0) or right[2] == (0.0, 0.0):
                continue
            trajectory_exposure_pairs += 1
            cosine = _cosine(left[2], right[2])
            if cosine is not None and cosine <= HEADING_REVERSAL_COSINE_MAX:
                heading_reversal_candidates += 1

    metrics = {
        "paired_faction_turn_count": len(observations),
        "distinct_ai_faction_count": len({str(row["faction"]) for row in observations}),
        "matched_force_turn_pairs": matched_pairs,
        "moved_force_turn_pairs": moved_pairs,
        "stationary_force_turn_pairs": stationary_pairs,
        "health_observed_force_turn_pairs": health_observed_pairs,
        "start_force_absent_at_turn_end_count": endpoint_absence_from_end,
        "end_force_absent_at_turn_start_count": endpoint_new_at_end,
        "forces_with_three_or_more_turn_end_observations": force_with_three_or_more_endpoints,
        "trajectory_exposure_pairs": trajectory_exposure_pairs,
        "heading_reversal_candidates_descriptive_only": heading_reversal_candidates,
    }
    checks = {key: metrics[key] >= threshold for key, threshold in QUALIFICATION_THRESHOLDS.items()}
    qualified = all(checks.values())
    result: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "trace_contract": TRACE_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": APPLICATION_ELIGIBLE,
        "purpose": "INSTRUMENTATION_EXPOSURE_QUALIFICATION_ONLY",
        "metrics": metrics,
        "qualification_thresholds": dict(QUALIFICATION_THRESHOLDS),
        "qualification_checks": checks,
        "qualification_status": "QUALIFIED_FOR_FUTURE_PREREGISTERED_DIAGNOSTIC_STUDY" if qualified else "INSUFFICIENT_DIAGNOSTIC_EXPOSURE_REDESIGN_REQUIRED",
        "interpretation_limits": [
            "This result qualifies telemetry density only; it is not a native-CAI quality verdict.",
            "Privileged diagnostic data is development evidence and is permanently ineligible as an application-time input.",
            "Heading-reversal candidates are descriptive exposure counters only; no v0.2L churn threshold is reused or post-hoc relaxed.",
            "A force absent from one turn endpoint is not labeled destroyed, disbanded, merged, recruited, or reassigned without a dedicated event contract.",
            "No result authorizes campaign orders, DB mutation, save mutation, or a project-owned strategic planner.",
        ],
    }
    result["result_digest"] = digest(result)
    return result
