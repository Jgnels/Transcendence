from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from .canonical import digest
from .native_visible_behavior import (
    APPLICATION_AUTHORITY,
    AUTHORITY,
    TRACE_CONTRACT,
    VISIBILITY_SOURCE,
    _anchors,
    _movement_proxy,
    _validate_trace,
)

PREREGISTRATION_CONTRACT = "NATIVE_CAI_VISIBLE_DIRECTIONAL_CHURN_PREREGISTRATION_V1"
RESULT_CONTRACT = "NATIVE_CAI_VISIBLE_DIRECTIONAL_CHURN_ANALYSIS_V1"
COHORT_RESULT_CONTRACT = "NATIVE_CAI_VISIBLE_DIRECTIONAL_CHURN_COHORT_COMPARISON_V1"
PRIMARY_ENDPOINT = "REPEATED_STABLE_CONTEXT_REGION_OSCILLATION_CLUSTER"
WINDOW_INTERVAL_COUNT = 3
WINDOW_FRAME_COUNT = WINDOW_INTERVAL_COUNT + 1
HEADING_REVERSAL_COSINE_MAX = -0.5  # >=120 degree change in movement heading.
MIN_NONOVERLAPPING_EPISODES_PER_CLUSTER = 2


class NativeChurnError(ValueError):
    pass


def _vector(left: dict[str, Any], right: dict[str, Any]) -> tuple[float, float]:
    return float(right["x"]) - float(left["x"]), float(right["y"]) - float(left["y"])


def _cosine(left: tuple[float, float], right: tuple[float, float]) -> float | None:
    left_norm = math.hypot(*left)
    right_norm = math.hypot(*right)
    if left_norm == 0.0 or right_norm == 0.0:
        return None
    value = (left[0] * right[0] + left[1] * right[1]) / (left_norm * right_norm)
    return max(-1.0, min(1.0, value))


def _anchor_context_signature(frame: dict[str, Any], target_faction: str) -> tuple[tuple[Any, ...], ...]:
    """Exact player-visible non-target context for the conservative primary endpoint.

    The signature intentionally includes coordinates. A player-owned or other visible
    foreign army moving is an observed-context change and therefore excludes the
    four-frame window from the primary stable-context endpoint. This is strict by
    design; hidden context can still change and is never claimed stable.
    """
    rows: list[tuple[Any, ...]] = []
    for army in frame["visible_armies"]:
        if army["faction"] == target_faction:
            continue
        rows.append(("ARMY", army["id"], army["faction"], float(army["x"]), float(army["y"])))
    for region in frame["visible_regions"]:
        rows.append(("REGION", region["id"], region["owner"], float(region["x"]), float(region["y"])))
    return tuple(sorted(rows))


def _actor(frame: dict[str, Any], target_faction: str, actor_id: str) -> dict[str, Any] | None:
    for army in frame["visible_armies"]:
        if army["faction"] == target_faction and army["id"] == actor_id:
            return army
    return None


def _anchor_kind(anchor_id: str | None) -> str | None:
    if not anchor_id or ":" not in anchor_id:
        return None
    return anchor_id.split(":", 1)[0]


def _candidate_windows_for_actor(
    frames: list[dict[str, Any]], target: str, actor_id: str
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    candidates: list[dict[str, Any]] = []
    counters = {
        "actor_four_frame_windows": 0,
        "excluded_nonconsecutive_turns": 0,
        "excluded_visibility_censoring": 0,
        "excluded_non_directional_interval": 0,
        "excluded_non_region_anchor": 0,
        "excluded_observed_context_change": 0,
        "eligible_stable_context_region_windows": 0,
        "eligible_non_aba_pattern": 0,
        "aba_without_heading_reversal": 0,
    }

    for start in range(0, max(0, len(frames) - WINDOW_FRAME_COUNT + 1)):
        window = frames[start : start + WINDOW_FRAME_COUNT]
        counters["actor_four_frame_windows"] += 1
        turns = [frame["turn"] for frame in window]
        if any(right - left != 1 for left, right in zip(turns, turns[1:])):
            counters["excluded_nonconsecutive_turns"] += 1
            continue

        actors = [_actor(frame, target, actor_id) for frame in window]
        if any(actor is None for actor in actors):
            counters["excluded_visibility_censoring"] += 1
            continue
        actor_rows = [actor for actor in actors if actor is not None]

        proxies: list[dict[str, Any]] = []
        for previous_frame, previous_actor, current_actor in zip(window, actor_rows, actor_rows[1:]):
            proxies.append(_movement_proxy(previous_actor, current_actor, _anchors(previous_frame, target)))
        if any(proxy["proxy_status"] != "VISIBLE_ANCHOR_DIRECTION_PROXY" for proxy in proxies):
            counters["excluded_non_directional_interval"] += 1
            continue

        anchors = [proxy.get("anchor_proxy") for proxy in proxies]
        if any(_anchor_kind(anchor) != "VISIBLE_REGION" for anchor in anchors):
            counters["excluded_non_region_anchor"] += 1
            continue

        contexts = [_anchor_context_signature(frame, target) for frame in window]
        if any(context != contexts[0] for context in contexts[1:]):
            counters["excluded_observed_context_change"] += 1
            continue

        counters["eligible_stable_context_region_windows"] += 1
        if not (anchors[0] == anchors[2] and anchors[0] != anchors[1]):
            counters["eligible_non_aba_pattern"] += 1
            continue

        vectors = [_vector(left, right) for left, right in zip(actor_rows, actor_rows[1:])]
        heading_cosines = [_cosine(left, right) for left, right in zip(vectors, vectors[1:])]
        if any(value is None or value > HEADING_REVERSAL_COSINE_MAX for value in heading_cosines):
            counters["aba_without_heading_reversal"] += 1
            continue

        pair = sorted({str(anchors[0]), str(anchors[1])})
        candidates.append(
            {
                "actor_id": actor_id,
                "from_turn": turns[0],
                "to_turn": turns[-1],
                "anchor_sequence": anchors,
                "anchor_pair": pair,
                "heading_cosines": [round(float(value), 6) for value in heading_cosines if value is not None],
                "observed_context_exactly_stable": True,
                "actor_continuously_player_visible": True,
                "classification": "STABLE_OBSERVED_CONTEXT_REGION_ABA_OSCILLATION_CANDIDATE",
                "interpretation": "PLAYER_VISIBLE_DIRECTIONAL_PROXY_NOT_NATIVE_TASK_IDENTITY",
            }
        )
    return candidates, counters


def _nonoverlapping(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    last_to_turn: int | None = None
    for candidate in sorted(candidates, key=lambda item: (int(item["from_turn"]), int(item["to_turn"]))):
        if last_to_turn is None or int(candidate["from_turn"]) >= last_to_turn:
            selected.append(candidate)
            last_to_turn = int(candidate["to_turn"])
    return selected


def _build_clusters(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, tuple[str, ...]], list[dict[str, Any]]] = {}
    for candidate in candidates:
        key = (str(candidate["actor_id"]), tuple(candidate["anchor_pair"]))
        grouped.setdefault(key, []).append(candidate)

    clusters: list[dict[str, Any]] = []
    for (actor_id, anchor_pair), rows in sorted(grouped.items()):
        selected = _nonoverlapping(rows)
        if len(selected) < MIN_NONOVERLAPPING_EPISODES_PER_CLUSTER:
            continue
        clusters.append(
            {
                "actor_id": actor_id,
                "anchor_pair": list(anchor_pair),
                "nonoverlapping_episode_count": len(selected),
                "episodes": selected,
                "from_turn": selected[0]["from_turn"],
                "to_turn": selected[-1]["to_turn"],
                "classification": PRIMARY_ENDPOINT,
                "causal_status": "REQUIRES_REVIEW_HIDDEN_CONTEXT_REMAINS_UNOBSERVED",
            }
        )
    return clusters


def analyze_visible_directional_churn(raw_trace: dict[str, Any]) -> dict[str, Any]:
    trace = _validate_trace(raw_trace)
    target = trace["observed_ai_faction"]
    frames = trace["frames"]
    actor_ids = sorted(
        {
            army["id"]
            for frame in frames
            for army in frame["visible_armies"]
            if army["faction"] == target
        }
    )

    all_candidates: list[dict[str, Any]] = []
    aggregate_counters: dict[str, int] = {
        "actor_four_frame_windows": 0,
        "excluded_nonconsecutive_turns": 0,
        "excluded_visibility_censoring": 0,
        "excluded_non_directional_interval": 0,
        "excluded_non_region_anchor": 0,
        "excluded_observed_context_change": 0,
        "eligible_stable_context_region_windows": 0,
        "eligible_non_aba_pattern": 0,
        "aba_without_heading_reversal": 0,
    }
    actor_results: list[dict[str, Any]] = []
    for actor_id in actor_ids:
        candidates, counters = _candidate_windows_for_actor(frames, target, actor_id)
        all_candidates.extend(candidates)
        for key, value in counters.items():
            aggregate_counters[key] += int(value)
        actor_results.append(
            {
                "actor_id": actor_id,
                "candidate_count": len(candidates),
                "counters": counters,
            }
        )

    clusters = _build_clusters(all_candidates)
    eligible = aggregate_counters["eligible_stable_context_region_windows"]
    if clusters:
        status = "PREREGISTERED_VISIBLE_CHURN_SIGNAL_PRESENT_REQUIRES_CAUSAL_REVIEW"
    elif eligible == 0:
        status = "INSUFFICIENT_ELIGIBLE_EXPOSURE"
    else:
        status = "NO_REPEATED_SIGNAL_OBSERVED_NOT_PROOF_OF_NATIVE_HYSTERESIS"

    result: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "preregistration_contract": PREREGISTRATION_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "foreign_visibility_source": VISIBILITY_SOURCE,
        "observation_scope": "PLAYER_VISIBLE_PARTIAL_FOREIGN_AI",
        "observer_faction": trace["observer_faction"],
        "observed_ai_faction": target,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "primary_endpoint_parameters": {
            "window_interval_count": WINDOW_INTERVAL_COUNT,
            "window_frame_count": WINDOW_FRAME_COUNT,
            "required_anchor_pattern": "A->B->A",
            "required_anchor_kind": "VISIBLE_REGION_ONLY",
            "heading_reversal_cosine_max": HEADING_REVERSAL_COSINE_MAX,
            "minimum_heading_change_degrees": 120.0,
            "required_nonoverlapping_episodes_per_cluster": MIN_NONOVERLAPPING_EPISODES_PER_CLUSTER,
            "observed_context_rule": "EXACT_NON_TARGET_VISIBLE_ANCHOR_SET_AND_POSITIONS_STABLE_ACROSS_WINDOW",
        },
        "status": status,
        "metrics": {
            **aggregate_counters,
            "oscillation_candidate_count": len(all_candidates),
            "repeated_oscillation_cluster_count": len(clusters),
            "candidate_rate_per_eligible_window": round(len(all_candidates) / eligible, 6) if eligible else None,
        },
        "actor_results": actor_results,
        "oscillation_candidates": all_candidates,
        "repeated_oscillation_clusters": clusters,
        "availability": {
            "visible_directional_churn_proxy": "OBSERVE_PREREGISTERED",
            "native_task_identity": "UNAVAILABLE",
            "native_assignment_memory": "UNAVAILABLE",
            "native_hysteresis": "UNAVAILABLE_ENGINE_INTERNAL",
            "hidden_context_stability": "UNAVAILABLE",
        },
        "interpretation_limits": [
            "The primary endpoint is deliberately stricter than a simple direction-change count: it requires region-anchor A->B->A oscillation, two >=120-degree heading reversals, continuous player visibility, consecutive turns, and exact stability of all observed non-target anchors.",
            "Exact observed-context stability does not imply hidden-context stability; unseen armies, native tasks, diplomacy, recruitment, and engine-internal state may change.",
            "One qualifying A->B->A window is a candidate only. The preregistered primary signal requires at least two non-overlapping episodes for the same actor and anchor pair.",
            "A detected cluster is evidence of repeated player-visible directional oscillation under stable observed context, not direct evidence of native task reassignment or missing engine-internal hysteresis.",
            "No detected cluster is not proof that native CAI has adequate assignment memory or hysteresis, especially when eligible exposure is low.",
            "No result authorizes campaign orders, DB mutation, save mutation, or a project-owned strategic planner.",
        ],
    }
    result["result_digest"] = digest(result)
    return deepcopy(result)


def compare_visible_directional_churn_cohorts(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(runs, list) or not runs:
        raise NativeChurnError("cohort comparison requires at least one run")
    grouped: dict[str, list[dict[str, Any]]] = {}
    run_results: list[dict[str, Any]] = []
    for index, run in enumerate(runs):
        if not isinstance(run, dict):
            raise NativeChurnError("cohort run must be an object")
        profile = run.get("profile")
        run_id = run.get("run_id")
        trace = run.get("trace")
        if profile not in {"VANILLA", "SFO"}:
            raise NativeChurnError("cohort profile must be VANILLA or SFO")
        if not isinstance(run_id, str) or not run_id:
            raise NativeChurnError("cohort run_id must be a nonempty string")
        if not isinstance(trace, dict):
            raise NativeChurnError("cohort trace must be an object")
        analysis = analyze_visible_directional_churn(trace)
        row = {"index": index, "run_id": run_id, "profile": profile, "analysis": analysis}
        run_results.append(row)
        grouped.setdefault(profile, []).append(row)

    profile_results: dict[str, Any] = {}
    for profile in ("VANILLA", "SFO"):
        rows = grouped.get(profile, [])
        eligible = sum(row["analysis"]["metrics"]["eligible_stable_context_region_windows"] for row in rows)
        candidates = sum(row["analysis"]["metrics"]["oscillation_candidate_count"] for row in rows)
        clusters = sum(row["analysis"]["metrics"]["repeated_oscillation_cluster_count"] for row in rows)
        profile_results[profile] = {
            "run_count": len(rows),
            "eligible_stable_context_region_windows": eligible,
            "oscillation_candidate_count": candidates,
            "repeated_oscillation_cluster_count": clusters,
            "candidate_rate_per_eligible_window": round(candidates / eligible, 6) if eligible else None,
        }

    output: dict[str, Any] = {
        "contract": COHORT_RESULT_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "runs": run_results,
        "profiles": profile_results,
        "comparison_status": "DESCRIPTIVE_ONLY_NO_CAUSAL_OR_SIGNIFICANCE_CLAIM",
        "decision_rule": {
            "native_tuning_candidate_elevated_when": "A repeated stable-context oscillation cluster is observed and a bounded native-row treatment has a preregistered mechanism plausibly related to the observed failure.",
            "project_planner_not_earned_when": "This observational endpoint alone cannot justify project-owned strategic planning, even if clusters are observed.",
            "zero_signal_interpretation": "No observed clusters does not prove native hysteresis, particularly when eligible exposure is zero or small.",
        },
    }
    output["result_digest"] = digest(output)
    return deepcopy(output)
