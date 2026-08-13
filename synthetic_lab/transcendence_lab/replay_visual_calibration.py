from __future__ import annotations

import copy
import math
import re
from typing import Any

from .canonical import digest
from .observed_battle import validate_observed_battle_corpus

VISUAL_ALIGNMENT_CONTRACT = "SFO_REPLAY_VISUAL_ALIGNMENT_V1"
CALIBRATION_CONTRACT = "SFO_DUAL_REPLAY_TACTICAL_CALIBRATION_V1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_KEYS = {
    "absolute_path",
    "local_path",
    "source_path",
    "video_path",
    "replay_path",
    "filename",
    "file_name",
    "raw_video",
    "video_bytes",
    "frame_bytes",
    "replay_bytes",
}
_FORBIDDEN_PROMOTIONS = {
    "ACKNOWLEDGED",
    "EXECUTED",
    "CAUSAL_EXECUTION",
    "OPTIMAL_POLICY",
    "TACTICAL_SUPERIORITY",
}
_ALLOWED_EVIDENCE = {"OBSERVED", "SUPPORTED", "HYPOTHESIS", "LIMITING_RESULT"}
_ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}


class ReplayVisualCalibrationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReplayVisualCalibrationError(message)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _walk_private(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in _FORBIDDEN_KEYS or lowered.endswith("_path"):
                raise ReplayVisualCalibrationError(f"private or binary field is prohibited at {path}.{key}")
            _walk_private(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_private(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if "c:\\users\\" in lowered or "/users/" in lowered or "/home/" in lowered:
            raise ReplayVisualCalibrationError(f"private path string is prohibited at {path}")


def _validate_hash(value: object, name: str) -> str:
    _require(isinstance(value, str) and _HEX64.fullmatch(value) is not None, f"{name} must be lowercase SHA-256")
    return value


def _validate_result_digest(value: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(value)
    claimed = payload.pop("result_digest", None)
    _validate_hash(claimed, "result_digest")
    _require(claimed == digest(payload), "result_digest does not match canonical payload")
    return value


def validate_replay_visual_alignment(value: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, dict), "visual alignment corpus must be an object")
    _walk_private(value)
    _validate_result_digest(value)
    _require(value.get("schema_version") == 1, "schema_version must be 1")
    _require(value.get("contract") == VISUAL_ALIGNMENT_CONTRACT, "unexpected visual alignment contract")
    _require(value.get("authority") == "NO_ORDERS", "visual alignment authority must remain NO_ORDERS")
    _require(value.get("evidence_status") == "OBSERVED_VISUAL_ALIGNMENT", "unexpected evidence status")
    battles = value.get("battles")
    _require(isinstance(battles, list) and len(battles) == 2, "exactly two replay battles are required")
    seen_battles: set[str] = set()
    seen_replays: set[str] = set()
    for battle in battles:
        _require(isinstance(battle, dict), "battle record must be an object")
        battle_id = battle.get("battle_id")
        _require(isinstance(battle_id, str) and battle_id, "battle_id is required")
        _require(battle_id not in seen_battles, "duplicate battle_id")
        seen_battles.add(battle_id)
        replay_hash = _validate_hash(battle.get("replay_sha256"), f"{battle_id}.replay_sha256")
        _require(replay_hash not in seen_replays, "duplicate replay identity")
        seen_replays.add(replay_hash)
        _validate_hash(battle.get("dense_corpus_result_digest"), f"{battle_id}.dense_corpus_result_digest")
        _require(isinstance(battle.get("visual_title"), str) and battle["visual_title"].startswith("Battle of "), "visual title is required")
        _require(isinstance(battle.get("runtime_identity"), str) and battle["runtime_identity"], "runtime identity is required")
        _require(battle.get("identity_resolution") == "VISUAL_TITLE_FOR_DISPLAY_RUNTIME_IDENTITY_RETAINED", "identity provenance must remain explicit")
        outcome = battle.get("outcome")
        _require(isinstance(outcome, dict), "outcome is required")
        _require(outcome.get("visual_winner") == "Reikland", "visual winner must be exact")
        _require(outcome.get("telemetry_victorious_alliance") == "1", "telemetry winner must remain alliance 1")
        _require(outcome.get("evidence_label") == "OBSERVED", "outcome must be observed")
        videos = battle.get("video_artifacts")
        _require(isinstance(videos, list) and videos, "at least one private video artifact descriptor is required")
        video_ids: set[str] = set()
        for video in videos:
            video_id = video.get("artifact_id")
            _require(isinstance(video_id, str) and video_id and video_id not in video_ids, "video artifact ids must be unique")
            video_ids.add(video_id)
            _validate_hash(video.get("sha256"), f"{battle_id}.{video_id}.sha256")
            _require(_is_number(video.get("duration_ms")) and 1 <= int(video["duration_ms"]) <= 7_200_000, "video duration is invalid")
            _require(video.get("width") == 1920 and video.get("height") == 1080, "visual evidence must preserve 1080p dimensions")
            _require(video.get("fps_num") == 30 and video.get("fps_den") == 1, "visual evidence must preserve 30 FPS")
            _require(video.get("committed") is False, "video bytes may not be committed")
        facts = battle.get("visual_facts")
        _require(isinstance(facts, list) and facts, "visual facts are required")
        fact_ids: set[str] = set()
        for fact in facts:
            fact_id = fact.get("fact_id")
            _require(isinstance(fact_id, str) and fact_id and fact_id not in fact_ids, "visual fact ids must be unique")
            fact_ids.add(fact_id)
            _require(fact.get("evidence_label") in _ALLOWED_EVIDENCE, "invalid visual fact evidence label")
            _require(fact.get("confidence") in _ALLOWED_CONFIDENCE, "invalid visual fact confidence")
            _require(not (_FORBIDDEN_PROMOTIONS & {str(fact.get("claim_status", ""))}), "forbidden visual promotion")
            _require(isinstance(fact.get("statement"), str) and fact["statement"], "visual fact statement is required")
        phases = battle.get("phase_windows")
        _require(isinstance(phases, list) and phases, "phase windows are required")
        last_telemetry_end = -1
        for phase in phases:
            _require(phase.get("evidence_label") in _ALLOWED_EVIDENCE, "invalid phase evidence label")
            _require(phase.get("confidence") in _ALLOWED_CONFIDENCE, "invalid phase confidence")
            start = phase.get("telemetry_start_ms")
            end = phase.get("telemetry_end_ms")
            _require(isinstance(start, int) and isinstance(end, int) and 0 <= start < end, "invalid telemetry phase range")
            _require(start >= last_telemetry_end, "telemetry phase windows must be ordered and non-overlapping")
            last_telemetry_end = end
            recordings = phase.get("recording_windows")
            _require(isinstance(recordings, list) and recordings, "phase must have recording windows")
            for window in recordings:
                _require(window.get("artifact_id") in video_ids, "recording window references unknown artifact")
                rstart = window.get("start_ms")
                rend = window.get("end_ms")
                _require(isinstance(rstart, int) and isinstance(rend, int) and 0 <= rstart < rend, "invalid recording window")
        limits = battle.get("interpretation_limits")
        _require(isinstance(limits, list) and limits, "battle interpretation limits are required")
        joined = " ".join(str(item) for item in limits).lower()
        _require("not acknowledgement" in joined and "not causal" in joined, "authority limits must reject acknowledgement and causality")
    _require(seen_battles == {"ubersreik", "marienburg"}, "exact Ubersreik and Marienburg cohort is required")
    return copy.deepcopy(value)


def _first_local_force_times(dense: dict[str, Any]) -> tuple[int, int, int]:
    local = sorted(
        int(unit["first_observed_time_ms"])
        for unit in dense["battle"]["units"]
        if bool(unit["local_alliance"])
    )
    return sum(time <= 100 for time in local), min(local), max(local)


def _first_aggregate_time(dense: dict[str, Any], alliance: str, predicate) -> int | None:
    for item in dense["battle"]["aggregate_timeline"][alliance]:
        if predicate(item):
            return int(item["time_ms"])
    return None


def _role_summary(dense: dict[str, Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for unit in dense["battle"]["units"]:
        if not unit["local_alliance"]:
            continue
        role = str(unit["role"])
        bucket = result.setdefault(role, {"units": 0, "kills_observed_max_sum": 0, "casualties_observed_lower_bound": 0, "routing_units_observed": 0})
        bucket["units"] += 1
        bucket["kills_observed_max_sum"] += int(unit["kills_observed_max"])
        bucket["casualties_observed_lower_bound"] += int(unit["casualties_observed_lower_bound"])
        if float(unit["time_series_metrics"]["routing_sample_ratio"]) > 0.0:
            bucket["routing_units_observed"] += 1
    return dict(sorted(result.items()))


def _build_battle_summary(visual: dict[str, Any], dense: dict[str, Any]) -> dict[str, Any]:
    initial_count, first_seen, full_force_time = _first_local_force_times(dense)
    battle = dense["battle"]
    duration_ms = int(battle["duration_ms"])
    commands = int(battle["command_analysis"]["command_event_count"])
    first_engagement = _first_aggregate_time(
        dense,
        "1",
        lambda item: int(item["kills"]) > 0 or int(item["units_in_melee"]) > 0,
    )
    first_local_route = _first_aggregate_time(dense, "1", lambda item: int(item["units_routing"]) > 0)
    first_enemy_route = _first_aggregate_time(dense, "2", lambda item: int(item["units_routing"]) > 0)
    return {
        "battle_id": visual["battle_id"],
        "visual_title": visual["visual_title"],
        "runtime_identity": visual["runtime_identity"],
        "identity_resolution": visual["identity_resolution"],
        "outcome": copy.deepcopy(visual["outcome"]),
        "telemetry": {
            "duration_ms": duration_ms,
            "detail_samples": int(battle["sampling"]["observed_detail_samples"]),
            "aggregate_records": sum(len(items) for items in battle["aggregate_timeline"].values()),
            "canonical_units": int(battle["identity_reconciliation"]["canonical_unit_count"]),
            "local_units": int(battle["unit_counts"]["local_canonical"]),
            "visible_enemy_units": int(battle["unit_counts"]["visible_enemy_canonical"]),
            "command_events": commands,
            "commands_per_minute": round(commands * 60000.0 / duration_ms, 3),
            "local_casualties_observed_lower_bound": int(battle["outcome_metrics"]["local_casualties_observed_lower_bound"]),
            "visible_enemy_casualties_observed_lower_bound": int(battle["outcome_metrics"]["visible_enemy_casualties_observed_lower_bound"]),
            "local_kills_observed_max_sum": int(battle["outcome_metrics"]["local_kills_observed_max_sum"]),
            "initial_local_units_observed": initial_count,
            "first_local_unit_observed_ms": first_seen,
            "full_local_force_observed_ms": full_force_time,
            "first_engagement_observed_ms": first_engagement,
            "first_local_route_observed_ms": first_local_route,
            "first_visible_enemy_route_observed_ms": first_enemy_route,
            "role_summary": _role_summary(dense),
        },
        "visual_phase_windows": copy.deepcopy(visual["phase_windows"]),
        "visual_facts": copy.deepcopy(visual["visual_facts"]),
        "interpretation_limits": copy.deepcopy(visual["interpretation_limits"]),
    }


def build_dual_replay_calibration(
    visual_alignment: dict[str, Any],
    dense_corpora: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    visual = validate_replay_visual_alignment(visual_alignment)
    summaries: list[dict[str, Any]] = []
    dense_digests: dict[str, str] = {}
    for record in visual["battles"]:
        battle_id = record["battle_id"]
        _require(battle_id in dense_corpora, f"missing dense corpus for {battle_id}")
        dense = validate_observed_battle_corpus(dense_corpora[battle_id])
        _require(dense["source"]["replay_sha256"] == record["replay_sha256"], f"replay hash mismatch for {battle_id}")
        _require(dense["result_digest"] == record["dense_corpus_result_digest"], f"dense result digest mismatch for {battle_id}")
        _require(dense["battle"]["identity"] == record["runtime_identity"], f"runtime identity mismatch for {battle_id}")
        dense_digests[battle_id] = dense["result_digest"]
        summaries.append(_build_battle_summary(record, dense))
    summaries.sort(key=lambda item: item["battle_id"])
    by_id = {item["battle_id"]: item for item in summaries}
    u = by_id["ubersreik"]["telemetry"]
    m = by_id["marienburg"]["telemetry"]
    output: dict[str, Any] = {
        "schema_version": 1,
        "contract": CALIBRATION_CONTRACT,
        "calibration_id": "sfo_reikland_dual_replay_tactical_calibration_v0.2A",
        "evidence_status": "OBSERVED_WITH_BOUNDED_VISUAL_INTERPRETATION",
        "authority": "NO_ORDERS",
        "source_visual_alignment_digest": visual["result_digest"],
        "source_dense_result_digests": dense_digests,
        "battles": summaries,
        "cross_battle_contrast": {
            "outcome_grades": {
                "ubersreik": by_id["ubersreik"]["outcome"]["visual_grade"],
                "marienburg": by_id["marienburg"]["outcome"]["visual_grade"],
            },
            "duration_ratio_marienburg_to_ubersreik": round(m["duration_ms"] / u["duration_ms"], 6),
            "local_casualty_lower_bound_ratio_marienburg_to_ubersreik": round(m["local_casualties_observed_lower_bound"] / u["local_casualties_observed_lower_bound"], 6),
            "command_count_ratio_marienburg_to_ubersreik": round(m["command_events"] / u["command_events"], 6),
            "command_rate_difference_per_minute": round(m["commands_per_minute"] - u["commands_per_minute"], 3),
            "initial_force_patterns": {
                "ubersreik": f"{u['initial_local_units_observed']} initial of {u['local_units']} final local units",
                "marienburg": f"{m['initial_local_units_observed']} initial of {m['local_units']} final local units",
            },
            "interpretation": "Victory grade and tactical cost diverge; win/loss alone is not a sufficient tactical-quality benchmark.",
            "evidence_label": "SUPPORTED",
        },
        "calibration_updates": [
            {
                "update_id": "force_completeness_guard",
                "status": "SUPPORTED",
                "rule": "Do not treat the initially observed local hierarchy as the complete force while reinforcement discovery is still changing.",
                "authority": "ADVISORY_ONLY",
            },
            {
                "update_id": "outcome_grade_cost_separation",
                "status": "SUPPORTED",
                "rule": "Evaluate preservation, role losses, and crisis exposure separately from victory status.",
                "authority": "ADVISORY_ONLY",
            },
            {
                "update_id": "local_crisis_independent_of_enemy_collapse",
                "status": "SUPPORTED",
                "rule": "Retain local crisis and recovery priorities even after a visible enemy rout cascade begins.",
                "authority": "ADVISORY_ONLY",
            },
            {
                "update_id": "terminal_commitment_abstention",
                "status": "SUPPORTED",
                "rule": "After outcome-decided or victory-countdown evidence, prohibit new high-commitment objectives; allow only bounded pursuit, disengagement, and reformation hypotheses.",
                "authority": "ADVISORY_ONLY",
            },
            {
                "update_id": "identity_provenance_separation",
                "status": "OBSERVED",
                "rule": "Use the visually confirmed replay title for display while retaining the runtime battlefield identity as a separate source field.",
                "authority": "NO_ORDERS",
            },
        ],
        "rejected_promotions": [
            "Observed owner commands are not optimal-policy labels.",
            "Observed command events are not acknowledgements.",
            "Visual movement is not proof that a particular command caused execution.",
            "Two land-battle replays do not establish broad SFO compatibility or tactical superiority.",
            "The outer Transcendence pack container remains unverified even though the loaded battle script is byte-identical.",
        ],
        "next_evidence_gaps": [
            "ordinary siege battle",
            "ambush or interception battle",
            "reinforcement battle with independently controlled allied army",
            "flying-heavy engagement",
            "large multi-army battle",
            "separate command acknowledgement and execution-causality probe",
        ],
    }
    output["result_digest"] = digest(output)
    return output
