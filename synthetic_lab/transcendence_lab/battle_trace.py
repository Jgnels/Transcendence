from __future__ import annotations

from collections import defaultdict
import math
import re
from typing import Any

from .canonical import digest


class BattleTraceCorpusError(ValueError):
    pass


TACTICAL_TRACE_INPUT_CONTRACT = "BATTLE_TRACE_TACTICAL_INPUT_V2"
_ALLOWED_ROLES = {"commander", "artillery", "ranged", "cavalry", "frontline", "unknown"}
_ALLOWED_FATIGUE = {
    "threshold_fresh",
    "threshold_active",
    "threshold_winded",
    "threshold_tired",
    "threshold_very_tired",
    "threshold_exhausted",
}
_REQUIRED_UNIT_FIELDS = {
    "stable_unit_id", "unit_type", "unit_class", "role", "local_alliance",
    "visibility_source", "position_x", "position_y", "position_z",
    "ordered_position_x", "ordered_position_y", "ordered_position_z",
    "bearing", "ordered_bearing", "ordered_width", "hitpoints_fraction",
    "initial_men", "men_alive", "men_fraction", "ammo", "starting_ammo",
    "fatigue", "idle", "moving", "moving_fast", "in_melee", "routing",
    "shattered", "wavering", "leaving", "rampaging", "under_missile_attack",
    "left_flank_threatened", "right_flank_threatened", "rear_flank_threatened",
    "current_target_id", "current_target_distance", "current_target_in_range",
    "missile_range", "is_commander", "num_special_abilities",
    "strategic_value_proxy", "initial_strategic_value_proxy", "kills",
}
_BOOLEAN_UNIT_FIELDS = {
    "local_alliance", "idle", "moving", "moving_fast", "in_melee", "routing",
    "shattered", "wavering", "leaving", "rampaging", "under_missile_attack",
    "left_flank_threatened", "right_flank_threatened", "rear_flank_threatened",
    "current_target_in_range", "is_commander",
}
_FINITE_NUMBER_FIELDS = {
    "position_x", "position_y", "position_z", "ordered_position_x",
    "ordered_position_y", "ordered_position_z", "bearing", "ordered_bearing",
    "ordered_width", "hitpoints_fraction", "men_fraction",
    "current_target_distance", "missile_range", "strategic_value_proxy",
    "initial_strategic_value_proxy",
}
_INTEGER_UNIT_FIELDS = {
    "initial_men", "men_alive", "ammo", "starting_ammo",
    "num_special_abilities", "kills",
}


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value.lower())
    )


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _require_nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BattleTraceCorpusError(f"{label} must be a nonempty string")
    return value


def _validate_unit(unit: dict[str, Any], slice_id: str) -> None:
    missing = sorted(_REQUIRED_UNIT_FIELDS - unit.keys())
    if missing:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit missing required fields: {missing}"
        )

    unit_id = _require_nonempty_string(
        unit.get("stable_unit_id"), f"slice {slice_id} stable_unit_id"
    )
    if not re.fullmatch(r"\d+:u\d+", unit_id):
        raise BattleTraceCorpusError(
            f"invalid stable unit identity in {slice_id}: {unit_id}"
        )

    for field in ("unit_type", "unit_class"):
        _require_nonempty_string(
            unit.get(field), f"slice {slice_id} unit {unit_id} {field}"
        )

    role = _require_nonempty_string(
        unit.get("role"), f"slice {slice_id} unit {unit_id} role"
    )
    if role not in _ALLOWED_ROLES:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} has unsupported role: {role}"
        )

    fatigue = _require_nonempty_string(
        unit.get("fatigue"), f"slice {slice_id} unit {unit_id} fatigue"
    )
    if fatigue not in _ALLOWED_FATIGUE:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} has unsupported fatigue: {fatigue}"
        )

    for field in sorted(_BOOLEAN_UNIT_FIELDS):
        if type(unit.get(field)) is not bool:
            raise BattleTraceCorpusError(
                f"slice {slice_id} unit {unit_id} {field} must be boolean"
            )

    expected_visibility = (
        "LOCAL_ALLIANCE" if unit["local_alliance"] else "VISIBLE_TO_LOCAL_ALLIANCE"
    )
    if unit.get("visibility_source") != expected_visibility:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} visibility_source must be {expected_visibility}"
        )

    for field in sorted(_FINITE_NUMBER_FIELDS):
        if not _is_finite_number(unit.get(field)):
            raise BattleTraceCorpusError(
                f"slice {slice_id} unit {unit_id} {field} must be a finite number"
            )

    for field in sorted(_INTEGER_UNIT_FIELDS):
        if not _is_plain_int(unit.get(field)):
            raise BattleTraceCorpusError(
                f"slice {slice_id} unit {unit_id} {field} must be an integer"
            )

    hp = float(unit["hitpoints_fraction"])
    men_fraction = float(unit["men_fraction"])
    if not 0.0 <= hp <= 1.0:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} hitpoints_fraction outside [0,1]"
        )
    if not 0.0 <= men_fraction <= 1.0:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} men_fraction outside [0,1]"
        )

    initial_men = unit["initial_men"]
    men_alive = unit["men_alive"]
    if initial_men <= 0:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} initial_men must be positive"
        )
    if not 0 <= men_alive <= initial_men:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} men_alive outside [0, initial_men]"
        )
    if abs(men_fraction - men_alive / initial_men) > 1e-5:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} men_fraction inconsistent with model counts"
        )

    ammo = unit["ammo"]
    starting_ammo = unit["starting_ammo"]
    if starting_ammo < 0 or not 0 <= ammo <= starting_ammo:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} ammo outside [0, starting_ammo]"
        )
    if unit["kills"] < 0:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} kills must be nonnegative"
        )
    if unit["num_special_abilities"] < -1:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} num_special_abilities below unavailable sentinel"
        )

    for field in ("bearing", "ordered_bearing"):
        if not 0.0 <= float(unit[field]) <= 360.0:
            raise BattleTraceCorpusError(
                f"slice {slice_id} unit {unit_id} {field} outside [0,360]"
            )
    if float(unit["ordered_width"]) <= 0.0:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} ordered_width must be positive"
        )
    if float(unit["missile_range"]) < 0.0:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} missile_range must be nonnegative"
        )
    for field in ("strategic_value_proxy", "initial_strategic_value_proxy"):
        if float(unit[field]) < 0.0:
            raise BattleTraceCorpusError(
                f"slice {slice_id} unit {unit_id} {field} must be nonnegative"
            )

    target_id = unit["current_target_id"]
    target_distance = float(unit["current_target_distance"])
    if target_id is not None and (not isinstance(target_id, str) or not target_id):
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} current_target_id must be null or nonempty string"
        )
    if target_distance < 0.0:
        if target_distance != -1.0 or target_id is not None:
            raise BattleTraceCorpusError(
                f"slice {slice_id} unit {unit_id} invalid no-target sentinel"
            )
    elif target_id is None:
        raise BattleTraceCorpusError(
            f"slice {slice_id} unit {unit_id} target distance requires target identity"
        )


def validate_tactical_slice_record(
    item: dict[str, Any], *, require_enemy_scope: bool = True
) -> dict[str, Any]:
    """Validate one visibility-safe tactical slice without assigning evidence status.

    Observed Tier 4R corpora and project-owned synthetic fixtures share this exact
    unit/scope boundary. Evidence classification remains the responsibility of the
    enclosing corpus or fixture suite.
    """
    if not isinstance(item, dict):
        raise BattleTraceCorpusError("each battle trace slice must be an object")
    slice_id = item.get("slice_id")
    if not isinstance(slice_id, str) or not slice_id:
        raise BattleTraceCorpusError("slice_id must be a nonempty string")
    time_ms = item.get("time_ms")
    if not _is_plain_int(time_ms) or time_ms < 0:
        raise BattleTraceCorpusError("slice time must be a nonnegative integer")
    units = item.get("units")
    if not isinstance(units, list) or not units:
        raise BattleTraceCorpusError(f"slice {slice_id} requires unit state")
    ids = [unit.get("stable_unit_id") if isinstance(unit, dict) else None for unit in units]
    if len(ids) != len(set(ids)):
        raise BattleTraceCorpusError(f"duplicate unit identity in slice {slice_id}")
    for unit in units:
        if not isinstance(unit, dict):
            raise BattleTraceCorpusError(f"slice {slice_id} unit must be an object")
        _validate_unit(unit, slice_id)

    hidden = item.get("hidden_enemy_units")
    if not _is_plain_int(hidden) or hidden < 0:
        raise BattleTraceCorpusError(f"invalid hidden-enemy count in {slice_id}")
    local_count = sum(unit["local_alliance"] for unit in units)
    visible_enemy_count = len(units) - local_count
    if local_count == 0:
        raise BattleTraceCorpusError(f"slice {slice_id} has no local-alliance units")
    if require_enemy_scope and slice_id != "battle_complete" and visible_enemy_count == 0 and hidden == 0:
        raise BattleTraceCorpusError(
            f"slice {slice_id} has no observed or hidden enemy scope"
        )
    return item


def validate_battle_trace_slices(corpus: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(corpus, dict):
        raise BattleTraceCorpusError("battle trace corpus must be an object")
    required = {
        "schema_version", "corpus_id", "tier", "fidelity_label",
        "evidence_status", "source", "battle_identity", "duration_ms",
        "visibility_contract", "slices", "evaluation_questions",
        "forbidden_inferences", "result_digest",
    }
    missing = sorted(required - corpus.keys())
    if missing:
        raise BattleTraceCorpusError(f"battle trace corpus missing: {missing}")
    if corpus["schema_version"] != 1:
        raise BattleTraceCorpusError("unsupported battle trace corpus schema")
    if corpus["tier"] != "4R" or corpus["evidence_status"] != "OBSERVED":
        raise BattleTraceCorpusError("battle trace corpus must be observed tier 4R")
    _require_nonempty_string(corpus.get("corpus_id"), "corpus_id")
    if corpus.get("visibility_contract") != (
        "Foreign unit state appears only when visibility_source=VISIBLE_TO_LOCAL_ALLIANCE; "
        "hidden enemies are counted but omitted."
    ):
        raise BattleTraceCorpusError("unsupported battle trace visibility contract")
    duration_ms = corpus.get("duration_ms")
    if not _is_plain_int(duration_ms) or duration_ms < 0:
        raise BattleTraceCorpusError("duration_ms must be a nonnegative integer")

    source = corpus["source"]
    if not isinstance(source, dict):
        raise BattleTraceCorpusError("battle trace source must be an object")
    for key in (
        "replay_sha256", "raw_trans_battle_log_sha256",
        "capture_verification_result_digest", "dense_corpus_result_digest",
    ):
        if not _is_sha256(source.get(key)):
            raise BattleTraceCorpusError(f"invalid source digest: {key}")
    if source.get("raw_replay_committed") is not False:
        raise BattleTraceCorpusError("raw replay must not be committed")
    if source.get("raw_log_committed") is not False:
        raise BattleTraceCorpusError("raw log must not be committed")

    slices = corpus["slices"]
    if not isinstance(slices, list) or len(slices) < 5:
        raise BattleTraceCorpusError("battle trace corpus requires multiple state slices")
    times = [item.get("time_ms") if isinstance(item, dict) else None for item in slices]
    if any(not _is_plain_int(value) or value < 0 for value in times):
        raise BattleTraceCorpusError("slice time must be a nonnegative integer")
    if times != sorted(times) or len(times) != len(set(times)):
        raise BattleTraceCorpusError("slice times must be unique and increasing")
    if times[-1] > duration_ms:
        raise BattleTraceCorpusError("slice time exceeds declared battle duration")

    slice_ids: set[str] = set()
    for item in slices:
        validate_tactical_slice_record(item)
        slice_id = item["slice_id"]
        if slice_id in slice_ids:
            raise BattleTraceCorpusError(f"duplicate slice_id: {slice_id}")
        slice_ids.add(slice_id)

    expected_digest = corpus["result_digest"]
    if not _is_sha256(expected_digest):
        raise BattleTraceCorpusError("invalid battle trace result digest")
    without_digest = dict(corpus)
    without_digest.pop("result_digest", None)
    if digest(without_digest) != expected_digest:
        raise BattleTraceCorpusError("battle trace result digest mismatch")
    return corpus


def _group_local_role_outcomes(dense_corpus: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {
            "unit_count": 0,
            "initial_models": 0,
            "casualties_observed_lower_bound": 0,
            "kills_observed_max_sum": 0,
            "ammo_spent_observed_lower_bound": 0,
            "distance_travelled_observed_m": 0.0,
        }
    )
    for unit in dense_corpus["battle"]["units"]:
        if not unit["local_alliance"]:
            continue
        role = unit["role"]
        row = grouped[role]
        row["unit_count"] += 1
        row["initial_models"] += unit["initial_men"]
        row["casualties_observed_lower_bound"] += unit["casualties_observed_lower_bound"]
        row["kills_observed_max_sum"] += unit["kills_observed_max"]
        row["ammo_spent_observed_lower_bound"] += (
            unit.get("ammo_spent_observed_lower_bound") or 0
        )
        row["distance_travelled_observed_m"] += (
            unit.get("distance_travelled_observed_m") or 0.0
        )

    result: dict[str, Any] = {}
    for role in sorted(grouped):
        row = grouped[role]
        initial = int(row["initial_models"])
        casualties = int(row["casualties_observed_lower_bound"])
        ammo = int(row["ammo_spent_observed_lower_bound"])
        kills = int(row["kills_observed_max_sum"])
        result[role] = {
            **row,
            "casualty_lower_bound_ratio": round(casualties / initial, 6) if initial else None,
            "kills_per_100_ammo_observed": (
                round(kills / (ammo / 100.0), 6) if ammo else None
            ),
            "distance_travelled_observed_m": round(
                float(row["distance_travelled_observed_m"]), 3
            ),
        }
    return result


def derive_tactical_trace_benchmarks(
    dense_corpus: dict[str, Any],
    trace_slices: dict[str, Any],
) -> dict[str, Any]:
    # Import locally to avoid a circular dependency at module import time.
    from .observed_battle import validate_observed_battle_corpus

    dense_corpus = validate_observed_battle_corpus(dense_corpus)
    trace_slices = validate_battle_trace_slices(trace_slices)
    if dense_corpus["result_digest"] != trace_slices["source"]["dense_corpus_result_digest"]:
        raise BattleTraceCorpusError("trace slices do not match dense corpus digest")
    if not dense_corpus["battle"]["sampling"]["time_series_metrics_valid"]:
        raise BattleTraceCorpusError("tactical trace benchmarks require dense coverage")

    units = dense_corpus["battle"]["units"]
    local = [unit for unit in units if unit["local_alliance"]]
    enemy = [unit for unit in units if not unit["local_alliance"]]

    endangered_characters = sorted(
        unit["stable_unit_id"]
        for unit in local
        if unit["role"] == "commander"
        and 0 <= unit["last_observed_hitpoints_fraction"] < 0.25
    )
    collapsed_frontline = sorted(
        unit["stable_unit_id"]
        for unit in local
        if unit["role"] == "frontline"
        and unit["initial_men"] > 0
        and unit["casualties_observed_lower_bound"] / unit["initial_men"] >= 0.5
    )
    endangered_ranged = sorted(
        unit["stable_unit_id"]
        for unit in local
        if unit["role"] == "ranged"
        and unit["initial_men"] > 0
        and (
            unit["casualties_observed_lower_bound"] / unit["initial_men"] >= 0.5
            or unit["last_observed_hitpoints_fraction"] < 0.25
        )
    )
    cavalry_overextension = sorted(
        unit["stable_unit_id"]
        for unit in local
        if unit["role"] == "cavalry"
        and (
            unit["casualties_observed_lower_bound"] / max(unit["initial_men"], 1) >= 0.5
            or unit["last_observed_flags"].get("routing")
            or unit["last_observed_flags"].get("shattered")
        )
    )
    artillery_overrun = sorted(
        unit["stable_unit_id"]
        for unit in local
        if unit["role"] == "artillery"
        and (
            unit["casualties_observed_lower_bound"] / max(unit["initial_men"], 1) >= 0.5
            or unit["last_observed_flags"].get("routing")
            or unit["last_observed_flags"].get("shattered")
        )
    )
    routed_visible_enemy = sorted(
        unit["stable_unit_id"]
        for unit in enemy
        if unit["last_observed_flags"].get("routing")
        or unit["last_observed_flags"].get("shattered")
    )

    slice_by_id = {item["slice_id"]: item for item in trace_slices["slices"]}
    required_milestones = [
        "deployment_complete",
        "first_contact",
        "local_melee_commitment",
        "local_crisis",
        "enemy_break",
        "enemy_rout_majority",
        "victory_countdown",
        "battle_complete",
    ]
    missing = [key for key in required_milestones if key not in slice_by_id]
    if missing:
        raise BattleTraceCorpusError(f"missing tactical milestones: {missing}")

    episodes = [
        {
            "episode_id": "deployment_and_reserve_design",
            "source_slice_id": "deployment_complete",
            "evaluation_axes": [
                "formation depth and firing lanes",
                "cavalry reserve placement",
                "artillery protection",
                "hidden-enemy uncertainty",
            ],
        },
        {
            "episode_id": "ranged_contact_and_target_priority",
            "source_slice_id": "first_contact",
            "evaluation_axes": [
                "legal visible target priority",
                "ranged exposure",
                "ammunition discipline",
                "reserve patience",
            ],
        },
        {
            "episode_id": "melee_commitment_control",
            "source_slice_id": "local_melee_commitment",
            "evaluation_axes": [
                "frontline commitment",
                "ranged line-of-fire preservation",
                "commander exposure",
                "flank response",
            ],
        },
        {
            "episode_id": "local_crisis_triage",
            "source_slice_id": "local_crisis",
            "evaluation_axes": [
                "routing containment",
                "commander survival",
                "frontline relief",
                "artillery and ranged evacuation",
            ],
        },
        {
            "episode_id": "enemy_break_exploitation",
            "source_slice_id": "enemy_break",
            "evaluation_axes": [
                "selective pursuit",
                "fresh-unit preservation",
                "high-value target isolation",
                "avoidance of pyrrhic cleanup losses",
            ],
        },
        {
            "episode_id": "rout_cascade_termination",
            "source_slice_id": "enemy_rout_majority",
            "evaluation_axes": [
                "pursuit stopping rule",
                "ranged cease-fire discipline",
                "reforming scattered units",
                "survivor preservation",
            ],
        },
    ]

    commands = dense_corpus["battle"]["command_analysis"]
    inferred = dense_corpus["battle"]["inferred_command_attribution"]
    result: dict[str, Any] = {
        "schema_version": 1,
        "tier": "4R",
        "fidelity_label": "OBSERVED_TRACE_BENCHMARKS_NOT_GOLD_POLICY",
        "corpus_id": dense_corpus["corpus_id"],
        "trace_slice_corpus_id": trace_slices["corpus_id"],
        "source_dense_corpus_digest": dense_corpus["result_digest"],
        "source_trace_slices_digest": trace_slices["result_digest"],
        "milestones": [
            {
                "slice_id": slice_id,
                "time_ms": slice_by_id[slice_id]["time_ms"],
                "hidden_enemy_units": slice_by_id[slice_id]["hidden_enemy_units"],
                "summary": slice_by_id[slice_id]["summary"],
            }
            for slice_id in required_milestones
        ],
        "episodes": episodes,
        "local_role_outcomes": _group_local_role_outcomes(dense_corpus),
        "stress_cases": {
            "endangered_characters": endangered_characters,
            "collapsed_frontline": collapsed_frontline,
            "endangered_ranged": endangered_ranged,
            "cavalry_overextension": cavalry_overextension,
            "artillery_overrun": artillery_overrun,
            "routed_or_shattered_visible_enemy": routed_visible_enemy,
        },
        "control_load": {
            "command_event_count": commands["command_event_count"],
            "median_command_interval_ms": commands["median_command_interval_ms"],
            "sub_500ms_interval_count": commands["sub_500ms_interval_count"],
            "direct_selection_attribution_ratio": commands["selection_attribution_ratio"],
            "inferred_command_count": inferred["inferred_command_count"],
            "high_confidence_inferred_count": inferred["high_confidence_count"],
            "inference_status": inferred["status"],
        },
        "contracts": {
            "dense_interval_coverage": (
                dense_corpus["battle"]["sampling"]["quality"]
                == "DENSE_INTERVAL_COVERAGE"
            ),
            "maximum_sample_gap_bounded": (
                dense_corpus["battle"]["sampling"]["maximum_sample_gap_ms"] <= 9000
            ),
            "stable_identity_without_aliases": (
                dense_corpus["battle"]["identity_reconciliation"][
                    "identity_alias_count"
                ]
                == 0
            ),
            "hidden_information_boundary_preserved": all(
                unit["local_alliance"]
                or unit["visibility_source"] == "VISIBLE_TO_LOCAL_ALLIANCE"
                for item in trace_slices["slices"]
                for unit in item["units"]
            ),
            "selection_limitation_explicit": (
                commands["selection_attribution_ratio"] == 0.0
                and inferred["status"] == "INFERRED_NOT_ACKNOWLEDGED"
            ),
            "owner_trace_not_gold_policy": any(
                "optimal" in warning.lower()
                for warning in dense_corpus["forbidden_inferences"]
            ),
        },
        "planner_invariants": [
            "Never consume hidden enemy identity or state.",
            "Treat direct selection attribution and inferred attribution as different evidence types.",
            "Preserve endangered commanders and productive ranged assets when continued engagement has low marginal value.",
            "Prevent rout cascades by recognizing local morale failure before terminal collapse.",
            "Do not chase a routed army with exhausted or shattered high-value units merely to maximize kills.",
            "Do not imitate the 397-command owner trace as a required control rate; optimize for bounded, explainable orders.",
            "Do not treat this single vanilla battle as SFO or cross-faction proof.",
        ],
        "evidence_status": "OBSERVED",
    }
    result["result_digest"] = digest(result)
    return result
