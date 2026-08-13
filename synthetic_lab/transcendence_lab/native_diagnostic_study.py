from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .canonical import digest

PARSED_TRACE_CONTRACT = "NATIVE_CAI_PRIVILEGED_DIAGNOSTIC_PARSED_TRACE_V2"
RESULT_CONTRACT = "NATIVE_CAI_DIAGNOSTIC_BEHAVIOR_STUDY_RESULT_V1"
AUTHORITY = "NO_ORDERS"
APPLICATION_AUTHORITY = "PROHIBITED"
RESEARCH_VISIBILITY = "PRIVILEGED_OMNISCIENT_DIAGNOSTIC"
APPLICATION_ELIGIBLE = False

# Frozen engineering thresholds for the first confirmatory behavior study.
# These are project hypotheses, never asserted as Creative Assembly constants.
RECOVERY_HEALTH_THRESHOLD_PCT = 65.0
RECOVERY_MIN_EXPOSURE_ARMY_TURNS = 10
RECOVERY_SIGNAL_MIN_ATTACKER_ARMY_TURNS = 2
RECOVERY_SIGNAL_RATE_MIN = 0.20

MIN_DIRECTIONAL_DISTANCE = 5.0
HEADING_REVERSAL_COSINE_MAX = -0.5  # >=120 degree reversal
MAX_HEALTH_RANGE_PCT = 5.0
MAX_STRENGTH_RATIO = 1.10
MAX_UNIT_COUNT_RANGE = 1
TEMPORAL_MIN_ELIGIBLE_WINDOWS = 20
TEMPORAL_REPEATED_REVERSALS_PER_FORCE = 2


class NativeDiagnosticStudyError(ValueError):
    pass


def frozen_thresholds() -> dict[str, Any]:
    return {
        "recovery_health_threshold_pct": RECOVERY_HEALTH_THRESHOLD_PCT,
        "recovery_min_exposure_army_turns": RECOVERY_MIN_EXPOSURE_ARMY_TURNS,
        "recovery_signal_min_attacker_army_turns": RECOVERY_SIGNAL_MIN_ATTACKER_ARMY_TURNS,
        "recovery_signal_rate_min": RECOVERY_SIGNAL_RATE_MIN,
        "minimum_directional_distance": MIN_DIRECTIONAL_DISTANCE,
        "heading_reversal_cosine_max": HEADING_REVERSAL_COSINE_MAX,
        "max_health_range_pct": MAX_HEALTH_RANGE_PCT,
        "max_strength_ratio": MAX_STRENGTH_RATIO,
        "max_unit_count_range": MAX_UNIT_COUNT_RANGE,
        "temporal_min_eligible_windows": TEMPORAL_MIN_ELIGIBLE_WINDOWS,
        "temporal_repeated_reversals_per_force": TEMPORAL_REPEATED_REVERSALS_PER_FORCE,
    }


def frozen_thresholds_digest() -> str:
    return digest(frozen_thresholds())


def _force_map(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for force in snapshot.get("forces", []):
        key = str(force.get("force_cqi", ""))
        if not key or key == "-1":
            continue
        if key in rows:
            raise NativeDiagnosticStudyError(f"duplicate force_cqi in snapshot: {key}")
        rows[key] = force
    return rows


def _war_set(snapshot: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(str(row.get("enemy")) for row in snapshot.get("wars", []) if row.get("enemy")))


def _region_set(snapshot: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(str(row.get("region")) for row in snapshot.get("regions", []) if row.get("region")))


def _distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    return math.hypot(float(right["x"]) - float(left["x"]), float(right["y"]) - float(left["y"]))


def _vector(left: dict[str, Any], right: dict[str, Any]) -> tuple[float, float]:
    return float(right["x"]) - float(left["x"]), float(right["y"]) - float(left["y"])


def _cosine(left: tuple[float, float], right: tuple[float, float]) -> float | None:
    a = math.hypot(*left)
    b = math.hypot(*right)
    if a == 0.0 or b == 0.0:
        return None
    return max(-1.0, min(1.0, (left[0] * right[0] + left[1] * right[1]) / (a * b)))


def _health(force: dict[str, Any]) -> float | None:
    value = float(force.get("average_unit_health_pct", -1))
    return value if value >= 0 else None


def _strength(force: dict[str, Any]) -> float | None:
    value = float(force.get("force_strength", -1))
    return value if value > 0 else None


def _unit_count(force: dict[str, Any]) -> int | None:
    value = int(force.get("unit_count", -1))
    return value if value >= 0 else None


def _battle_participation_between(
    battles: list[dict[str, Any]],
    faction: str,
    force_id: str,
    left_event_index: int,
    right_event_index: int,
) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for battle in battles:
        index = int(battle["begin_event_index"])
        if not (left_event_index < index < right_event_index):
            continue
        participants = [
            row for row in battle.get("participants", [])
            if str(row.get("faction")) == faction and str(row.get("force_cqi")) == force_id
        ]
        if participants:
            matched.append({
                "battle_sequence": int(battle["battle_sequence"]),
                "turn": int(battle["turn"]),
                "sides": sorted({str(row.get("side")) for row in participants}),
            })
    return matched


def _validate_trace(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("contract") != PARSED_TRACE_CONTRACT:
        raise NativeDiagnosticStudyError("unexpected parsed diagnostic trace contract")
    if raw.get("authority") != AUTHORITY or raw.get("application_authority") != APPLICATION_AUTHORITY:
        raise NativeDiagnosticStudyError("diagnostic study authority changed")
    if raw.get("research_visibility") != RESEARCH_VISIBILITY or raw.get("application_eligible") is not False:
        raise NativeDiagnosticStudyError("diagnostic study visibility/application boundary changed")
    if raw.get("battle_participant_telemetry_declared") is not True:
        raise NativeDiagnosticStudyError("confirmatory study requires the preregistered battle-participant telemetry surface")
    observations = raw.get("observations")
    battles = raw.get("battle_sequences")
    if not isinstance(observations, list) or not isinstance(battles, list):
        raise NativeDiagnosticStudyError("parsed diagnostic trace missing observations/battles")
    if raw.get("incomplete_battle_sequences"):
        raise NativeDiagnosticStudyError("confirmatory study refuses incomplete battle sequences")
    return raw


def _nearest_enemy_context(
    observations_by_turn_faction: dict[tuple[int, str], dict[str, Any]],
    turn: int,
    faction: str,
    force: dict[str, Any],
) -> dict[str, Any]:
    subject = observations_by_turn_faction.get((turn, faction))
    if not subject:
        return {"nearest_enemy_force": None, "nearest_enemy_region": None}
    enemies = set(_war_set(subject["end"]))
    x, y = float(force["x"]), float(force["y"])
    force_candidates: list[tuple[float, str, str]] = []
    region_candidates: list[tuple[float, str, str]] = []
    for enemy in sorted(enemies):
        row = observations_by_turn_faction.get((turn, enemy))
        if not row:
            continue
        for other_id, other in _force_map(row["end"]).items():
            ox, oy = float(other.get("x", -1)), float(other.get("y", -1))
            if ox < 0 or oy < 0:
                continue
            force_candidates.append((math.hypot(ox - x, oy - y), enemy, other_id))
        for region in row["end"].get("regions", []):
            rx, ry = float(region.get("x", -1)), float(region.get("y", -1))
            if rx < 0 or ry < 0:
                continue
            region_candidates.append((math.hypot(rx - x, ry - y), enemy, str(region.get("region"))))
    force_row = min(force_candidates) if force_candidates else None
    region_row = min(region_candidates) if region_candidates else None
    return {
        "nearest_enemy_force": None if force_row is None else {
            "distance": round(force_row[0], 3), "faction": force_row[1], "force_cqi": force_row[2]
        },
        "nearest_enemy_region": None if region_row is None else {
            "distance": round(region_row[0], 3), "faction": region_row[1], "region": region_row[2]
        },
    }


def analyze_native_diagnostic_behavior_study(raw_trace: dict[str, Any]) -> dict[str, Any]:
    trace = _validate_trace(raw_trace)
    observations = sorted(trace["observations"], key=lambda row: (int(row["turn"]), str(row["faction"])))
    battles = sorted(trace["battle_sequences"], key=lambda row: int(row["begin_event_index"]))
    observations_by_turn_faction = {(int(row["turn"]), str(row["faction"])): row for row in observations}

    # Recovery-side endpoint: only attacker-side battle participation during the
    # faction's own start->end interval counts toward the signal. Defender-side
    # participation is reported separately and never promoted to offensive misuse.
    recovering_army_turns = 0
    recovering_attacker_army_turns = 0
    recovering_defender_army_turns = 0
    recovering_attacker_battles = 0
    recovery_candidates: list[dict[str, Any]] = []
    for row in observations:
        faction = str(row["faction"])
        turn = int(row["turn"])
        start, end = row["start"], row["end"]
        left_index = int(start["end_event_index"])
        right_index = int(end["begin_event_index"])
        for force_id, force in sorted(_force_map(start).items()):
            health = _health(force)
            if health is None or health >= RECOVERY_HEALTH_THRESHOLD_PCT:
                continue
            recovering_army_turns += 1
            relevant = _battle_participation_between(battles, faction, force_id, left_index, right_index)
            attacker = [battle for battle in relevant if "ATTACKER" in battle["sides"]]
            defender = [battle for battle in relevant if "DEFENDER" in battle["sides"]]
            if attacker:
                recovering_attacker_army_turns += 1
                recovering_attacker_battles += len(attacker)
                recovery_candidates.append({
                    "turn": turn,
                    "faction": faction,
                    "force_cqi": force_id,
                    "start_average_unit_health_pct": round(health, 3),
                    "start_unit_count": _unit_count(force),
                    "battle_sequences": [battle["battle_sequence"] for battle in attacker],
                    "classification": "RECOVERING_ATTACKER_SIDE_BATTLE_REENTRY_CANDIDATE",
                })
            if defender:
                recovering_defender_army_turns += 1

    recovery_rate = None if recovering_army_turns == 0 else recovering_attacker_army_turns / recovering_army_turns
    if recovering_army_turns < RECOVERY_MIN_EXPOSURE_ARMY_TURNS:
        recovery_status = "INSUFFICIENT_RECOVERY_EXPOSURE"
    elif (
        recovering_attacker_army_turns >= RECOVERY_SIGNAL_MIN_ATTACKER_ARMY_TURNS
        and recovery_rate is not None
        and recovery_rate >= RECOVERY_SIGNAL_RATE_MIN
    ):
        recovery_status = "RECOVERING_ATTACKER_SIDE_REENTRY_SIGNAL_OBSERVED"
    else:
        recovery_status = "NO_PREREGISTERED_RECOVERY_SIGNAL_IN_COHORT"

    # Temporal endpoint: compare each force's TURN_END trajectory because that
    # represents realized post-action position. Every eligible window must be
    # battle-free and stable across the subject's observed own-context fields.
    tracks: dict[tuple[str, str], list[tuple[int, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for row in observations:
        faction = str(row["faction"])
        for force_id, force in _force_map(row["end"]).items():
            tracks[(faction, force_id)].append((int(row["turn"]), force, row))

    eligible_windows = 0
    reversal_candidates: list[dict[str, Any]] = []
    reversal_intervals_by_force: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    exact_ababa: list[dict[str, Any]] = []

    def stable_window(window: list[tuple[int, dict[str, Any], dict[str, Any]]]) -> tuple[bool, str | None]:
        turns = [item[0] for item in window]
        if any(b - a != 1 for a, b in zip(turns, turns[1:])):
            return False, "NONCONSECUTIVE_TURNS"
        forces = [item[1] for item in window]
        if any(_health(force) is None for force in forces):
            return False, "HEALTH_UNAVAILABLE"
        if any(_strength(force) is None for force in forces):
            return False, "STRENGTH_UNAVAILABLE"
        if any(_unit_count(force) is None for force in forces):
            return False, "UNIT_COUNT_UNAVAILABLE"
        if len({_war_set(item[2]["end"]) for item in window}) != 1:
            return False, "WAR_SET_CHANGED"
        if len({_region_set(item[2]["end"]) for item in window}) != 1:
            return False, "OWNED_REGION_SET_CHANGED"
        if len({str(force.get("stance")) for force in forces}) != 1:
            return False, "STANCE_CHANGED"
        healths = [_health(force) for force in forces]
        if max(healths) - min(healths) > MAX_HEALTH_RANGE_PCT:  # type: ignore[arg-type]
            return False, "HEALTH_CHANGED"
        strengths = [_strength(force) for force in forces]
        if max(strengths) / min(strengths) > MAX_STRENGTH_RATIO:  # type: ignore[arg-type]
            return False, "STRENGTH_CHANGED"
        units = [_unit_count(force) for force in forces]
        if max(units) - min(units) > MAX_UNIT_COUNT_RANGE:  # type: ignore[arg-type]
            return False, "UNIT_COUNT_CHANGED"
        return True, None

    for (faction, force_id), rows in tracks.items():
        rows.sort(key=lambda item: item[0])
        for i in range(len(rows) - 2):
            window = rows[i:i + 3]
            stable, _ = stable_window(window)
            if not stable:
                continue
            first, middle, last = window
            v1 = _vector(first[1], middle[1])
            v2 = _vector(middle[1], last[1])
            if math.hypot(*v1) < MIN_DIRECTIONAL_DISTANCE or math.hypot(*v2) < MIN_DIRECTIONAL_DISTANCE:
                continue
            battles_in_window = _battle_participation_between(
                battles, faction, force_id, int(first[2]["end"]["end_event_index"]), int(last[2]["end"]["end_event_index"])
            )
            if battles_in_window:
                continue
            eligible_windows += 1
            cosine = _cosine(v1, v2)
            if cosine is None or cosine > HEADING_REVERSAL_COSINE_MAX:
                continue
            turns = [item[0] for item in window]
            regions = [str(item[1].get("region", "none")) for item in window]
            candidate = {
                "faction": faction,
                "force_cqi": force_id,
                "turns": turns,
                "cosine": round(cosine, 6),
                "regions": regions,
                "at_peace": len(_war_set(middle[2]["end"])) == 0,
                "nearest_enemy_context": [
                    {"turn": turn, **_nearest_enemy_context(observations_by_turn_faction, turn, faction, force)}
                    for turn, force, _ in window
                ],
                "classification": "BATTLE_FREE_STABLE_CONTEXT_HEADING_REVERSAL_CANDIDATE",
            }
            reversal_candidates.append(candidate)
            reversal_intervals_by_force[(faction, force_id)].append((turns[0], turns[-1]))

        for i in range(len(rows) - 4):
            window = rows[i:i + 5]
            stable, _ = stable_window(window)
            if not stable:
                continue
            regions = [str(item[1].get("region", "none")) for item in window]
            if regions[0] == "none" or regions[1] == "none":
                continue
            if not (regions[0] == regions[2] == regions[4] and regions[1] == regions[3] and regions[0] != regions[1]):
                continue
            vectors = [_vector(a[1], b[1]) for a, b in zip(window, window[1:])]
            if any(math.hypot(*vector) < MIN_DIRECTIONAL_DISTANCE for vector in vectors):
                continue
            if any((_cosine(a, b) is None or _cosine(a, b) > HEADING_REVERSAL_COSINE_MAX) for a, b in zip(vectors, vectors[1:])):
                continue
            battles_in_window = _battle_participation_between(
                battles, faction, force_id, int(window[0][2]["end"]["end_event_index"]), int(window[-1][2]["end"]["end_event_index"])
            )
            if battles_in_window:
                continue
            exact_ababa.append({
                "faction": faction,
                "force_cqi": force_id,
                "turns": [item[0] for item in window],
                "regions": regions,
                "classification": "EXACT_BATTLE_FREE_STABLE_CONTEXT_REGION_ABABA_SIGNAL",
            })

    repeated_forces: list[dict[str, Any]] = []
    for (faction, force_id), intervals in sorted(reversal_intervals_by_force.items()):
        selected: list[tuple[int, int]] = []
        for interval in sorted(intervals, key=lambda item: (item[1], item[0])):
            if not selected or interval[0] > selected[-1][1]:
                selected.append(interval)
        if len(selected) >= TEMPORAL_REPEATED_REVERSALS_PER_FORCE:
            repeated_forces.append({
                "faction": faction,
                "force_cqi": force_id,
                "candidate_count": len(intervals),
                "non_overlapping_candidate_count": len(selected),
                "selected_non_overlapping_turn_intervals": [list(interval) for interval in selected],
            })
    if eligible_windows < TEMPORAL_MIN_ELIGIBLE_WINDOWS:
        temporal_status = "INSUFFICIENT_TEMPORAL_EXPOSURE"
    elif repeated_forces or exact_ababa:
        temporal_status = "REPEATED_BATTLE_FREE_REVERSAL_SIGNAL_OBSERVED"
    else:
        temporal_status = "NO_PREREGISTERED_TEMPORAL_SIGNAL_IN_COHORT"

    metrics = {
        "complete_battle_sequence_count": len(battles),
        "recovering_army_turn_count": recovering_army_turns,
        "recovering_attacker_side_army_turn_count": recovering_attacker_army_turns,
        "recovering_defender_side_army_turn_count": recovering_defender_army_turns,
        "recovering_attacker_side_battle_count": recovering_attacker_battles,
        "recovering_attacker_side_rate": None if recovery_rate is None else round(recovery_rate, 6),
        "eligible_battle_free_stable_context_directional_windows": eligible_windows,
        "heading_reversal_candidate_count": len(reversal_candidates),
        "repeated_reversal_force_count": len(repeated_forces),
        "exact_region_ababa_signal_count": len(exact_ababa),
    }
    result: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": APPLICATION_ELIGIBLE,
        "purpose": "PREREGISTERED_NATIVE_RECOVERY_AND_TEMPORAL_BEHAVIOR_STUDY",
        "frozen_thresholds": frozen_thresholds(),
        "frozen_thresholds_digest": frozen_thresholds_digest(),
        "metrics": metrics,
        "recovery_status": recovery_status,
        "temporal_status": temporal_status,
        "recovery_candidates": recovery_candidates,
        "temporal_reversal_candidates": reversal_candidates,
        "repeated_reversal_forces": repeated_forces,
        "exact_region_ababa_signals": exact_ababa,
        "interpretation_limits": [
            "Attacker-side pending-battle participation is a stronger offensive-use proxy than movement, but ambush/interception/special battle mechanics may still require causal review.",
            "The 65% recovery threshold is an inherited project engineering hypothesis, not a discovered native WH3 constant.",
            "A battle-free stable-context reversal signal does not reveal native task identity, assignment memory, or engine-internal hysteresis.",
            "Privileged diagnostic state is permanently ineligible as an application-time input.",
            "A positive signal can earn causal review and the smallest plausible native-row ablation; it cannot directly authorize v0.2G/v0.2I or project-owned strategic planning.",
            "A negative cohort result is not proof that native recovery or temporal commitment is generally good outside the observed campaign/time window.",
        ],
        "architecture_action_if_positive": "CAUSAL_REVIEW_THEN_NARROW_NATIVE_ROW_ABLATION_ONLY",
        "architecture_action_if_negative": "NO_APPLICATION_AUTHORITY_CHANGE",
    }
    result["result_digest"] = digest(result)
    return result
