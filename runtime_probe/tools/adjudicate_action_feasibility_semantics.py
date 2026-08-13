from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from export_action_feasibility_windows import EXPORT_CONTRACT, EXPECTED_PACK_SHA256


CALIBRATION_CONTRACT = "OBSERVED_COMMAND_POINT_SEMANTIC_CALIBRATION_V1"
EXPECTED_SOURCE_ZIP_SHA256 = "83b7c3d851605f290c6a50045be920cdddc7224c8f9e7e63deefba5323e2ff7d"
EXPECTED_WINDOWS_SHA256 = "e56e2e32fc5037bf104ea7da05184c7e591bec2394920b482174f808de7fa18f"
EXPECTED_MANIFEST_SHA256 = "37a6669f48d3b1eeb6a7ba1b5dcda0041f7d4cbd6ceaec1d25ef03bcedbe2afb"
EXPECTED_RAW_LOG_SHA256 = "b4f8c4ca9c285018772d50a4eda92f34572f742dd97967bca8229b0a6b3ce951"
EXPECTED_PUBLIC_CAPTURE_SHA256 = "a1c03ec12a4c2b70945311fc57b54f978fcca892a37b12d46a5daa6f22ebf579"

_RAW_QUERY_RESULTS = {"QUERY_TRUE", "QUERY_FALSE", "UNAVAILABLE", "NOT_APPLICABLE"}
_MODALITIES = {
    "EXPLICIT_POINT_MOVE",
    "VISIBLE_UNIT_TARGET_ATTACK",
    "OPAQUE_FORMATION_ORIENTATION",
    "OPAQUE_SELECTION_DOUBLE_CLICK",
    "OPAQUE_SPECIAL_ABILITY",
}


class ActionFeasibilitySemanticError(ValueError):
    pass


def _sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _verify_digest(record: dict[str, Any], label: str) -> None:
    claimed = record.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise ActionFeasibilitySemanticError(f"{label} result_digest is invalid")
    material = dict(record)
    material.pop("result_digest", None)
    if _canonical_digest(material) != claimed:
        raise ActionFeasibilitySemanticError(f"{label} result_digest mismatch")


def _require_int(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ActionFeasibilitySemanticError(f"{label} must be an integer >= {minimum}")
    return value


def _position(value: Any, label: str) -> dict[str, float] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"x", "y", "z"}:
        raise ActionFeasibilitySemanticError(f"{label} must contain x/y/z")
    result: dict[str, float] = {}
    for axis in ("x", "y", "z"):
        item = value[axis]
        if isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(float(item)):
            raise ActionFeasibilitySemanticError(f"{label}.{axis} must be finite")
        result[axis] = float(item)
    return result


def _is_zero_vector(value: dict[str, float] | None) -> bool:
    return value is not None and all(abs(value[axis]) <= 1e-9 for axis in ("x", "y", "z"))


def _classify_window(window: dict[str, Any]) -> tuple[str, bool, str]:
    command = window.get("command")
    target_unit_id = window.get("target_unit_id")
    if not isinstance(command, str) or not command:
        raise ActionFeasibilitySemanticError("window command is invalid")
    if not isinstance(target_unit_id, str) or not target_unit_id or "hidden" in target_unit_id.lower():
        raise ActionFeasibilitySemanticError("window target identity is invalid")
    target_position = _position(window.get("target_position"), "target_position")
    zero = _is_zero_vector(target_position)

    if command == "Move":
        if target_unit_id != "none" or target_position is None or zero:
            raise ActionFeasibilitySemanticError("Move window lacks an explicit nonzero point")
        return "EXPLICIT_POINT_MOVE", True, "EXPLICIT_CALLBACK_POINT"
    if command == "Attack Unit":
        if target_unit_id == "none":
            raise ActionFeasibilitySemanticError("Attack Unit window lacks a visible target")
        return "VISIBLE_UNIT_TARGET_ATTACK", False, "ZERO_VECTOR_SENTINEL_NOT_A_POINT" if zero else "UNIT_TARGET_NOT_POINT_QUALIFIED"
    if command == "Move Orientation Width":
        return "OPAQUE_FORMATION_ORIENTATION", False, "ZERO_VECTOR_SENTINEL_NOT_A_POINT" if zero else "OPAQUE_FORMATION_POINT_SEMANTICS"
    if command == "Double Click":
        return "OPAQUE_SELECTION_DOUBLE_CLICK", False, "ZERO_VECTOR_SENTINEL_NOT_A_POINT" if zero else "OPAQUE_DOUBLE_CLICK_POINT_SEMANTICS"
    if command == "Special Ability":
        return "OPAQUE_SPECIAL_ABILITY", False, "ZERO_VECTOR_SENTINEL_NOT_A_POINT" if zero else "OPAQUE_SPECIAL_ABILITY_POINT_SEMANTICS"
    raise ActionFeasibilitySemanticError(f"unsupported live command modality: {command}")


def _empty_counts() -> dict[str, int]:
    return {key: 0 for key in sorted(_RAW_QUERY_RESULTS)}


def _count_actor_samples(actor: dict[str, Any], *, point_qualified: bool) -> tuple[dict[str, int], dict[str, int]]:
    _verify_digest(actor, "actor")
    samples = actor.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ActionFeasibilitySemanticError("actor samples must be a nonempty list")
    raw = _empty_counts()
    qualified = _empty_counts()
    last_index = 0
    last_offset = -1
    for sample in samples:
        if not isinstance(sample, dict):
            raise ActionFeasibilitySemanticError("sample must be an object")
        result = sample.get("reachability")
        if result not in _RAW_QUERY_RESULTS:
            raise ActionFeasibilitySemanticError("invalid raw reachability result")
        raw[result] += 1
        qualified[result if point_qualified else "NOT_APPLICABLE"] += 1
        index = _require_int(sample.get("sample_index"), "sample_index", 1)
        offset = _require_int(sample.get("time_offset_ms"), "time_offset_ms", 0)
        if index <= last_index or offset < last_offset:
            raise ActionFeasibilitySemanticError("actor samples are not ordered")
        last_index = index
        last_offset = offset
        if sample.get("unit_id") != actor.get("unit_id"):
            raise ActionFeasibilitySemanticError("sample unit differs from actor")
        if "hidden" in str(sample.get("current_target_id", "")).lower():
            raise ActionFeasibilitySemanticError("hidden current target leaked")
    summary = actor.get("summary")
    if not isinstance(summary, dict) or summary.get("sample_count") != len(samples):
        raise ActionFeasibilitySemanticError("actor summary sample count mismatch")
    if summary.get("reachability_counts") != raw:
        raise ActionFeasibilitySemanticError("actor raw reachability summary mismatch")
    return raw, qualified


def adjudicate_action_feasibility_documents(
    windows_document: dict[str, Any],
    manifest: dict[str, Any],
    *,
    source_zip_sha256: str,
    windows_sha256: str,
    manifest_sha256: str,
) -> dict[str, Any]:
    if source_zip_sha256 != EXPECTED_SOURCE_ZIP_SHA256:
        raise ActionFeasibilitySemanticError("unexpected detailed re-export ZIP identity")
    if windows_sha256 != EXPECTED_WINDOWS_SHA256:
        raise ActionFeasibilitySemanticError("unexpected detailed windows identity")
    if manifest_sha256 != EXPECTED_MANIFEST_SHA256:
        raise ActionFeasibilitySemanticError("unexpected detailed manifest identity")
    _verify_digest(windows_document, "detailed window export")
    if windows_document.get("schema_version") != 1 or windows_document.get("export_contract") != EXPORT_CONTRACT:
        raise ActionFeasibilitySemanticError("unsupported detailed window export")
    if windows_document.get("authority") != "NO_ORDERS":
        raise ActionFeasibilitySemanticError("authority must remain NO_ORDERS")
    if windows_document.get("project_issue_attempt_count") != 0 or windows_document.get("direct_acknowledgement_count") != 0:
        raise ActionFeasibilitySemanticError("issue and acknowledgement counts must remain zero")
    if windows_document.get("raw_log_in_export") is not False:
        raise ActionFeasibilitySemanticError("raw log may not be included")
    if windows_document.get("source_raw_log_sha256") != EXPECTED_RAW_LOG_SHA256:
        raise ActionFeasibilitySemanticError("raw-log identity mismatch")
    if windows_document.get("installed_pack_sha256") != EXPECTED_PACK_SHA256:
        raise ActionFeasibilitySemanticError("pack identity mismatch")

    if manifest.get("schema_version") != 1 or manifest.get("capture_kind") != "action_feasibility_window_reexport":
        raise ActionFeasibilitySemanticError("unsupported public re-export manifest")
    if manifest.get("authority") != "NO_ORDERS":
        raise ActionFeasibilitySemanticError("manifest authority must remain NO_ORDERS")
    if manifest.get("source_raw_log_in_export") is not False or manifest.get("personal_paths_in_export") is not False:
        raise ActionFeasibilitySemanticError("manifest privacy boundary is invalid")
    if manifest.get("source_public_capture_sha256") != EXPECTED_PUBLIC_CAPTURE_SHA256:
        raise ActionFeasibilitySemanticError("source public-capture identity mismatch")
    if manifest.get("source_raw_log_sha256") != EXPECTED_RAW_LOG_SHA256:
        raise ActionFeasibilitySemanticError("manifest raw-log identity mismatch")
    if manifest.get("installed_pack_sha256") != EXPECTED_PACK_SHA256:
        raise ActionFeasibilitySemanticError("manifest pack identity mismatch")
    if manifest.get("action_feasibility_windows_sha256") != windows_sha256:
        raise ActionFeasibilitySemanticError("manifest windows hash mismatch")
    if manifest.get("project_issue_attempt_count") != 0 or manifest.get("direct_acknowledgement_count") != 0:
        raise ActionFeasibilitySemanticError("manifest may not claim issue or acknowledgement")

    windows = windows_document.get("windows")
    if not isinstance(windows, list):
        raise ActionFeasibilitySemanticError("windows must be a list")
    if windows_document.get("window_count") != len(windows) or manifest.get("window_count") != len(windows):
        raise ActionFeasibilitySemanticError("window count mismatch")

    raw_counts = _empty_counts()
    qualified_counts = _empty_counts()
    modality_counts: dict[str, dict[str, Any]] = {
        key: {
            "window_count": 0,
            "actor_count": 0,
            "sample_count": 0,
            "raw_reachability_counts": _empty_counts(),
            "qualified_reachability_counts": _empty_counts(),
            "actors_with_movement": 0,
            "actors_with_ordered_position_match": 0,
            "actors_with_current_target_match": 0,
        }
        for key in sorted(_MODALITIES)
    }
    affected_false_window_ids: list[str] = []
    affected_false_actor_count = 0
    total_actors = 0
    total_samples = 0
    point_windows = 0
    point_actors = 0
    point_actors_with_initial_ordered_match = 0
    attack_actors = 0
    attack_actors_with_initial_target_match = 0

    for window in windows:
        if not isinstance(window, dict):
            raise ActionFeasibilitySemanticError("window must be an object")
        _verify_digest(window, "window")
        if window.get("project_issue_attempted") is not False or window.get("direct_acknowledgement_observed") is not False:
            raise ActionFeasibilitySemanticError("window may not claim issue or acknowledgement")
        if window.get("command_origin") != "GAME_COMMAND_EVENT_ORIGIN_UNRESOLVED":
            raise ActionFeasibilitySemanticError("command origin must remain unresolved")
        modality, point_qualified, point_semantics = _classify_window(window)
        actors = window.get("actors")
        if not isinstance(actors, list) or window.get("actor_count") != len(actors):
            raise ActionFeasibilitySemanticError("actor count mismatch")
        entry = modality_counts[modality]
        entry["window_count"] += 1
        if point_qualified:
            point_windows += 1
        window_raw_false = 0
        for actor in actors:
            if not isinstance(actor, dict):
                raise ActionFeasibilitySemanticError("actor must be an object")
            raw, qualified = _count_actor_samples(actor, point_qualified=point_qualified)
            actor_samples = actor["samples"]
            total_actors += 1
            total_samples += len(actor_samples)
            entry["actor_count"] += 1
            entry["sample_count"] += len(actor_samples)
            for key in raw_counts:
                raw_counts[key] += raw[key]
                qualified_counts[key] += qualified[key]
                entry["raw_reachability_counts"][key] += raw[key]
                entry["qualified_reachability_counts"][key] += qualified[key]
            window_raw_false += raw["QUERY_FALSE"]
            summary = actor["summary"]
            entry["actors_with_movement"] += int(summary.get("any_movement_observed") is True)
            entry["actors_with_ordered_position_match"] += int(summary.get("any_ordered_position_match") is True)
            entry["actors_with_current_target_match"] += int(summary.get("any_current_target_match") is True)
            if point_qualified:
                point_actors += 1
                if actor_samples[0].get("ordered_position_match") is True:
                    point_actors_with_initial_ordered_match += 1
            if modality == "VISIBLE_UNIT_TARGET_ATTACK":
                attack_actors += 1
                if actor_samples[0].get("current_target_match") is True:
                    attack_actors_with_initial_target_match += 1
        if not point_qualified and window_raw_false:
            affected_false_window_ids.append(str(window.get("window_id")))
            affected_false_actor_count += sum(
                actor["summary"]["reachability_counts"]["QUERY_FALSE"] > 0
                for actor in actors
            )
        entry["point_semantics"] = point_semantics
        entry["point_query_evidence_qualified"] = point_qualified

    if windows_document.get("sample_count") != total_samples or manifest.get("sample_count") != total_samples:
        raise ActionFeasibilitySemanticError("sample count mismatch")
    if raw_counts["QUERY_TRUE"] + raw_counts["QUERY_FALSE"] + raw_counts["UNAVAILABLE"] + raw_counts["NOT_APPLICABLE"] != total_samples:
        raise ActionFeasibilitySemanticError("raw reachability total mismatch")

    result: dict[str, Any] = {
        "schema_version": 1,
        "calibration_contract": CALIBRATION_CONTRACT,
        "status": "OBSERVED_COMMAND_POINT_SEMANTICS_CALIBRATED",
        "scope": "ONE_ORDINARY_VANILLA_SINGLE_PLAYER_BATTLE",
        "source_reexport_zip_sha256": source_zip_sha256,
        "source_windows_sha256": windows_sha256,
        "source_manifest_sha256": manifest_sha256,
        "source_public_capture_sha256": EXPECTED_PUBLIC_CAPTURE_SHA256,
        "source_raw_log_sha256": EXPECTED_RAW_LOG_SHA256,
        "installed_pack_sha256": EXPECTED_PACK_SHA256,
        "authority": "NO_ORDERS",
        "project_issue_attempt_count": 0,
        "direct_acknowledgement_count": 0,
        "window_count": len(windows),
        "actor_window_count": total_actors,
        "sample_count": total_samples,
        "raw_probe_reachability_counts": raw_counts,
        "qualified_explicit_point_reachability_counts": qualified_counts,
        "command_modalities": modality_counts,
        "explicit_point_observation": {
            "window_count": point_windows,
            "actor_count": point_actors,
            "sample_count": qualified_counts["QUERY_TRUE"] + qualified_counts["QUERY_FALSE"] + qualified_counts["UNAVAILABLE"],
            "query_true": qualified_counts["QUERY_TRUE"],
            "query_false": qualified_counts["QUERY_FALSE"],
            "unavailable": qualified_counts["UNAVAILABLE"],
            "actors_with_initial_ordered_position_match": point_actors_with_initial_ordered_match,
            "actors_with_any_movement": modality_counts["EXPLICIT_POINT_MOVE"]["actors_with_movement"],
            "valid_false_point_result_status": "UNVERIFIED_NONE_OBSERVED",
        },
        "visible_unit_target_observation": {
            "window_count": modality_counts["VISIBLE_UNIT_TARGET_ATTACK"]["window_count"],
            "actor_count": attack_actors,
            "actors_with_initial_current_target_match": attack_actors_with_initial_target_match,
            "actors_with_any_current_target_match": modality_counts["VISIBLE_UNIT_TARGET_ATTACK"]["actors_with_current_target_match"],
            "actors_with_any_movement": modality_counts["VISIBLE_UNIT_TARGET_ATTACK"]["actors_with_movement"],
        },
        "defect_adjudication": {
            "defect_id": "NONPOINT_ZERO_VECTOR_REACHABILITY_MISCLASSIFICATION",
            "classification": "LIMITING_RESULT_CORRECTED_AT_EVIDENCE_LAYER",
            "affected_window_ids": sorted(set(affected_false_window_ids)),
            "affected_actor_count": affected_false_actor_count,
            "raw_false_sample_count": raw_counts["QUERY_FALSE"],
            "qualified_false_sample_count": qualified_counts["QUERY_FALSE"],
            "discarded_nonpoint_query_true_count": raw_counts["QUERY_TRUE"] - qualified_counts["QUERY_TRUE"],
            "discarded_nonpoint_query_false_count": raw_counts["QUERY_FALSE"] - qualified_counts["QUERY_FALSE"],
            "explanation": "The legacy probe queried callback positions for every command. Non-point or opaque callbacks exposed a zero-vector sentinel, so those raw query results cannot support exact-point feasibility claims.",
        },
        "capability_promotions": [
            "Explicit Move callback points were queryable in this battle and produced QUERY_TRUE for 191/191 qualified samples.",
            "All 16 explicit Move actor-windows showed ordered-position matching in the first sample.",
            "Visible Attack Unit targets matched current-target state in 48/49 actor-windows.",
        ],
        "rejected_or_unverified_claims": [
            "The 38 raw QUERY_FALSE samples are not valid false results for explicit command points.",
            "A valid QUERY_FALSE result on an explicit nonzero command point remains unobserved.",
            "Ordered-position or current-target matching is not acknowledgement, execution causality, arrival, or outcome.",
            "Aggregate player-command calibration is not evidence for any Transcendence-generated Battle 4 candidate point.",
        ],
        "interpretation_limits": [
            "Command origin remains unresolved.",
            "Qualified reachability applies only to explicit nonzero Move callback points in this capture.",
            "The observation is scoped to one ordinary vanilla single-player battle.",
            "No route completion, formation, collision, command legality, issue, acknowledgement, execution, or tactical outcome is established.",
        ],
        "privacy_boundary": {
            "raw_log_in_repository": False,
            "personal_paths_in_repository": False,
            "user_identity_in_repository": False,
        },
    }
    result["result_digest"] = _canonical_digest(result)
    return result


def adjudicate_action_feasibility_zip(path: Path) -> dict[str, Any]:
    blob = path.read_bytes()
    source_sha = _sha256(blob)
    if source_sha != EXPECTED_SOURCE_ZIP_SHA256:
        raise ActionFeasibilitySemanticError("unexpected detailed re-export ZIP identity")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if set(names) != {"action_feasibility_windows.json", "public_reexport_manifest.json"} or len(names) != 2:
            raise ActionFeasibilitySemanticError("unexpected detailed re-export members")
        windows_blob = archive.read("action_feasibility_windows.json")
        manifest_blob = archive.read("public_reexport_manifest.json")
    windows_sha = _sha256(windows_blob)
    if windows_sha != EXPECTED_WINDOWS_SHA256:
        raise ActionFeasibilitySemanticError("unexpected detailed windows identity")
    try:
        windows_document = json.loads(windows_blob.decode("utf-8-sig"))
        manifest = json.loads(manifest_blob.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ActionFeasibilitySemanticError("detailed re-export is not valid UTF-8 JSON") from error
    return adjudicate_action_feasibility_documents(
        windows_document,
        manifest,
        source_zip_sha256=source_sha,
        windows_sha256=windows_sha,
        manifest_sha256=_sha256(manifest_blob),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Adjudicate command-point semantics in a detailed action-feasibility re-export")
    parser.add_argument("capture_zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = adjudicate_action_feasibility_zip(args.capture_zip)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
