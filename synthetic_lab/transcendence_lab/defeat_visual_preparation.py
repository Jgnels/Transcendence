from __future__ import annotations

import copy
import math
import re
from typing import Any

from .canonical import digest

VISUAL_PREPARATION_CONTRACT = "SFO_CHAOS_DEFEAT_VISUAL_PREPARATION_V1"
READINESS_CONTRACT = "SFO_CHAOS_DEFEAT_DENSE_CAPTURE_READINESS_V1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_KEYS = {
    "absolute_path",
    "local_path",
    "source_path",
    "video_path",
    "replay_path",
    "raw_video",
    "video_bytes",
    "frame_bytes",
    "replay_bytes",
    "raw_replay",
}
_FORBIDDEN_PROMOTIONS = {
    "ACKNOWLEDGED",
    "EXECUTED",
    "CAUSAL_EXECUTION",
    "OPTIMAL_POLICY",
    "TACTICAL_SUPERIORITY",
    "OBSERVED_DEFEAT_GRADE",
}
_ALLOWED_EVIDENCE = {"OBSERVED", "SUPPORTED", "HYPOTHESIS", "LIMITING_RESULT", "OWNER_ATTESTED"}
_ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}
EXPECTED_REPLAY_SHA256 = "28d780d02f2af07fe16fe4a24a27cd37f41bdb870d485f11949d5ed63f838cb5"
EXPECTED_REPLAY_SIZE_BYTES = 86067
EXPECTED_VIDEO_SHA256 = "6e008c378a8e4273ca7d2c8101ca69279839a5c21dbaf749fb5e666adde56155"
EXPECTED_VIDEO_DURATION_MS = 389533


class DefeatVisualPreparationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DefeatVisualPreparationError(message)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _validate_hash(value: object, name: str) -> str:
    _require(isinstance(value, str) and _HEX64.fullmatch(value) is not None, f"{name} must be lowercase SHA-256")
    return value


def _walk_private(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in _FORBIDDEN_KEYS or lowered.endswith("_path"):
                raise DefeatVisualPreparationError(f"private or binary field is prohibited at {path}.{key}")
            _walk_private(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_private(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if "c:\\users\\" in lowered or "/users/" in lowered or "/home/" in lowered:
            raise DefeatVisualPreparationError(f"private path string is prohibited at {path}")


def _validate_result_digest(value: dict[str, Any]) -> None:
    payload = copy.deepcopy(value)
    claimed = payload.pop("result_digest", None)
    _validate_hash(claimed, "result_digest")
    _require(claimed == digest(payload), "result_digest does not match canonical payload")


def validate_chaos_defeat_visual_preparation(value: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, dict), "visual preparation must be an object")
    _walk_private(value)
    _validate_result_digest(value)
    _require(value.get("schema_version") == 1, "schema_version must be 1")
    _require(value.get("contract") == VISUAL_PREPARATION_CONTRACT, "unexpected visual preparation contract")
    _require(value.get("authority") == "NO_ORDERS", "authority must remain NO_ORDERS")
    _require(value.get("evidence_status") == "OBSERVED_VISUAL_DEFEAT_TELEMETRY_PENDING", "unexpected evidence status")

    replay = value.get("replay")
    _require(isinstance(replay, dict), "replay descriptor is required")
    _validate_hash(replay.get("sha256"), "replay.sha256")
    _require(replay.get("sha256") == EXPECTED_REPLAY_SHA256, "replay identity does not match the frozen Chaos defeat")
    _require(replay.get("size_bytes") == EXPECTED_REPLAY_SIZE_BYTES, "replay size does not match the frozen Chaos defeat")
    _require(replay.get("committed") is False, "replay bytes may not be committed")
    _require(replay.get("display_title") == "An Ogre's Folly", "display title must remain exact")
    _require(replay.get("battle_type") == "LAND_BATTLE", "battle type must remain exact")
    _require(replay.get("local_faction") == "Reikland", "local faction must remain exact")
    _require(replay.get("enemy_display") == "Warhost of the Apocalypse", "enemy display must remain exact")

    video = value.get("visual_artifact")
    _require(isinstance(video, dict), "visual artifact descriptor is required")
    _validate_hash(video.get("sha256"), "visual_artifact.sha256")
    _require(video.get("sha256") == EXPECTED_VIDEO_SHA256, "video identity does not match the frozen Chaos defeat recording")
    _require(video.get("duration_ms") == EXPECTED_VIDEO_DURATION_MS, "video duration does not match the frozen recording")
    _require(video.get("width") == 1920 and video.get("height") == 1080, "visual evidence must preserve 1080p")
    _require(video.get("fps_num") == 30 and video.get("fps_den") == 1, "visual evidence must preserve 30 FPS")
    _require(video.get("committed") is False, "video bytes may not be committed")

    outcome = value.get("outcome")
    _require(isinstance(outcome, dict), "outcome descriptor is required")
    _require(outcome.get("result_screen_observed") is False, "result screen was not observed")
    _require(outcome.get("status") == "OWNER_ATTESTED_DEFEAT_VISUALLY_CONSISTENT", "defeat must remain owner-attested")
    _require(outcome.get("evidence_label") == "OWNER_ATTESTED", "defeat outcome must not be promoted to OBSERVED")

    phases = value.get("visual_phase_windows")
    _require(isinstance(phases, list) and len(phases) >= 5, "visual phase windows are required")
    seen: set[str] = set()
    last_end = -1
    for phase in phases:
        phase_id = phase.get("phase_id")
        _require(isinstance(phase_id, str) and phase_id and phase_id not in seen, "phase ids must be unique")
        seen.add(phase_id)
        start = phase.get("recording_start_ms")
        end = phase.get("recording_end_ms")
        _require(isinstance(start, int) and isinstance(end, int) and 0 <= start < end, "invalid visual phase range")
        _require(start >= last_end, "visual phase windows must be ordered and non-overlapping")
        last_end = end
        _require(phase.get("evidence_label") in _ALLOWED_EVIDENCE, "invalid phase evidence label")
        _require(phase.get("confidence") in _ALLOWED_CONFIDENCE, "invalid phase confidence")
        _require(isinstance(phase.get("note"), str) and phase["note"], "phase note is required")

    hypotheses = value.get("bounded_hypotheses")
    _require(isinstance(hypotheses, list) and hypotheses, "bounded hypotheses are required")
    for item in hypotheses:
        _require(item.get("evidence_label") in {"SUPPORTED", "HYPOTHESIS"}, "diagnosis must remain bounded")
        _require(item.get("confidence") in _ALLOWED_CONFIDENCE, "invalid diagnosis confidence")
        _require(not (_FORBIDDEN_PROMOTIONS & {str(item.get("claim_status", ""))}), "forbidden diagnosis promotion")
        _require(isinstance(item.get("statement"), str) and item["statement"], "diagnosis statement is required")

    missing = value.get("telemetry_required")
    _require(isinstance(missing, list) and missing, "telemetry requirements are required")
    joined_missing = " ".join(str(item) for item in missing).lower()
    for token in ("health", "morale", "ammunition", "command", "routing", "casualt"):
        _require(token in joined_missing, f"telemetry requirements must include {token}")

    limits = value.get("interpretation_limits")
    _require(isinstance(limits, list) and limits, "interpretation limits are required")
    joined = " ".join(str(item) for item in limits).lower()
    _require("not acknowledgement" in joined, "authority limits must reject acknowledgement")
    _require("not causal" in joined, "authority limits must reject causality")
    _require("not an optimal-policy" in joined or "not optimal-policy" in joined, "owner trace must not become an optimal-policy label")
    return copy.deepcopy(value)


def build_chaos_defeat_capture_readiness(value: dict[str, Any]) -> dict[str, Any]:
    validated = validate_chaos_defeat_visual_preparation(value)
    replay = validated["replay"]
    output: dict[str, Any] = {
        "schema_version": 1,
        "contract": READINESS_CONTRACT,
        "status": "READY_FOR_EXACT_READ_ONLY_DENSE_CAPTURE",
        "authority": "NO_ORDERS",
        "source_visual_preparation_digest": validated["result_digest"],
        "exact_replay": {
            "sha256": replay["sha256"],
            "size_bytes": replay["size_bytes"],
            "display_title": replay["display_title"],
            "battle_type": replay["battle_type"],
            "local_faction": replay["local_faction"],
            "enemy_display": replay["enemy_display"],
        },
        "visual_outcome": copy.deepcopy(validated["outcome"]),
        "visual_phase_sequence": [phase["phase_id"] for phase in validated["visual_phase_windows"]],
        "bounded_hypotheses": [
            {
                "hypothesis_id": item["hypothesis_id"],
                "evidence_label": item["evidence_label"],
                "confidence": item["confidence"],
            }
            for item in validated["bounded_hypotheses"]
        ],
        "capture_requirements": {
            "exact_replay_hash_required": True,
            "schema2_battle_complete_required": True,
            "stable_unit_identity_required": True,
            "exact_sfo_hash_required": True,
            "read_only_battle_observer_required": True,
            "raw_log_private": True,
            "replay_binary_exported": False,
            "video_exported": False,
        },
        "telemetry_required": copy.deepcopy(validated["telemetry_required"]),
        "claims_withheld_until_capture": [
            "exact casualty and kill totals",
            "health, morale, fatigue, ammunition, and routing trajectories",
            "exact command timing and targets",
            "unit-stable defeat phase boundaries",
            "whether any alternative would have changed the outcome",
            "command acknowledgement, execution causality, tactical optimality, or superiority",
        ],
    }
    output["result_digest"] = digest(output)
    return output
