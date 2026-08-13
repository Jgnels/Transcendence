from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))

from run_native_diagnostic_telemetry import parse_diagnostic_trace, parse_line
from transcendence_lab.canonical import digest
from transcendence_lab.native_diagnostic_benchmark import (
    analyze_sfo_benchmark,
    stratify_temporal_trace,
    temporal_cluster_diagnostics,
)
from transcendence_lab.native_diagnostic_study import analyze_native_diagnostic_behavior_study
from transcendence_lab.native_sfo_causal_review import (
    adjudicate_sfo_replication_stage_a,
    build_causal_review,
    replication_policy,
)

AUTHORITY = "NO_ORDERS"
APPLICATION_AUTHORITY = "PROHIBITED"
RESEARCH_VISIBILITY = "PRIVILEGED_OMNISCIENT_DIAGNOSTIC"
APPLICATION_ELIGIBLE = False
NORMALIZED_CONTRACT = "NATIVE_CAI_BEHAVIOR_REPLAY_NORMALIZED_V1"
COMPARISON_CONTRACT = "NATIVE_CAI_BEHAVIOR_REPLAY_COMPARISON_V1"
STUDY_VERSION = "v0.2R"

KNOWN_DIAGNOSTIC_EVENTS = {
    "RUNTIME_BEGIN",
    "PACK_LOADED",
    "CAPABILITY",
    "HUMAN_TURN_MARKER",
    "AI_FACTION_SKIPPED",
    "AI_SNAPSHOT_BEGIN",
    "AI_FORCE",
    "AI_REGION",
    "AI_WAR",
    "AI_SNAPSHOT_END",
    "AI_BATTLE_BEGIN",
    "AI_BATTLE_PARTICIPANT",
    "AI_BATTLE_END",
}

SUPPORTED_EXPORTS: dict[str, dict[str, str | None]] = {
    "NATIVE_CAI_DIAGNOSTIC_BEHAVIOR_STUDY_PUBLIC_EXPORT_V1": {
        "profile": "VANILLA",
        "stored_result": "native_behavior_study_result.json",
        "profile_binding": "native_behavior_study_profile_binding.json",
        "verification": "native_behavior_study_verification.json",
    },
    "NATIVE_CAI_DIAGNOSTIC_SFO_BEHAVIOR_BENCHMARK_PUBLIC_EXPORT_V1": {
        "profile": "SFO",
        "stored_result": "native_sfo_behavior_benchmark_result.json",
        "profile_binding": "native_sfo_behavior_profile_binding.json",
        "verification": "native_sfo_behavior_benchmark_verification.json",
    },
    "NATIVE_CAI_DIAGNOSTIC_PUBLIC_EXPORT_V1": {
        "profile": "UNSPECIFIED_DIAGNOSTIC",
        "stored_result": None,
        "profile_binding": "native_diagnostic_profile_binding.json",
        "verification": "native_diagnostic_capture_verification.json",
    },
}

TIMELINE_FIELDS = [
    "faction",
    "force_cqi",
    "turn",
    "present_start",
    "present_end",
    "start_x",
    "start_y",
    "end_x",
    "end_y",
    "movement_distance",
    "start_region",
    "end_region",
    "start_stance",
    "end_stance",
    "start_unit_count",
    "end_unit_count",
    "start_average_unit_health_pct",
    "end_average_unit_health_pct",
    "start_force_strength",
    "end_force_strength",
    "start_action_points_remaining_pct",
    "end_action_points_remaining_pct",
    "wars",
    "owned_regions",
    "territorial",
    "battle_sequences",
    "battle_roles",
    "telemetry_complete",
    "identity_discontinuity",
]


class NativeBehaviorReplayError(ValueError):
    pass


def _sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _authority_fields() -> dict[str, Any]:
    return {
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": APPLICATION_ELIGIBLE,
    }


def _safe_zip_name(name: str) -> bool:
    if not name or "\\" in name:
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return False
    return True


def _load_json_blob(blobs: dict[str, bytes], name: str, *, required: bool = True) -> dict[str, Any] | None:
    blob = blobs.get(name)
    if blob is None:
        if required:
            raise NativeBehaviorReplayError(f"capture member missing: {name}")
        return None
    try:
        value = json.loads(blob.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NativeBehaviorReplayError(f"invalid JSON member {name}: {exc}") from exc
    if not isinstance(value, dict):
        raise NativeBehaviorReplayError(f"JSON member must be an object: {name}")
    return value


def _validate_authority(value: dict[str, Any], label: str) -> None:
    expected = _authority_fields()
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise NativeBehaviorReplayError(
                f"{label} authority boundary drifted for {key}: expected {wanted!r}, got {value.get(key)!r}"
            )


def _read_capture(path: Path, expected_sha256: str | None) -> tuple[dict[str, bytes], dict[str, Any], dict[str, Any]]:
    blob = path.read_bytes()
    capture_sha = _sha256(blob)
    if expected_sha256 is not None and capture_sha.casefold() != expected_sha256.casefold():
        raise NativeBehaviorReplayError(
            f"capture SHA-256 mismatch: expected {expected_sha256.casefold()}, got {capture_sha}"
        )
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise NativeBehaviorReplayError("capture is not a valid ZIP archive") from exc
    with archive:
        if archive.testzip() is not None:
            raise NativeBehaviorReplayError("capture ZIP CRC/integrity check failed")
        infos = [info for info in archive.infolist() if not info.is_dir()]
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
            raise NativeBehaviorReplayError(f"capture contains duplicate ZIP members: {duplicates}")
        unsafe = sorted(name for name in names if not _safe_zip_name(name))
        if unsafe:
            raise NativeBehaviorReplayError(f"capture contains unsafe member paths: {unsafe}")
        blobs = {info.filename: archive.read(info) for info in infos}

    manifest = _load_json_blob(blobs, "export_manifest.json")
    assert manifest is not None
    contract = str(manifest.get("contract", ""))
    if contract not in SUPPORTED_EXPORTS:
        raise NativeBehaviorReplayError(f"unsupported capture export contract: {contract!r}")
    _validate_authority(manifest, "export manifest")
    if manifest.get("contains_private_machine_paths") is not False:
        raise NativeBehaviorReplayError("capture is not declared privacy-safe")
    rows = manifest.get("files")
    if not isinstance(rows, list):
        raise NativeBehaviorReplayError("export manifest files must be a list")
    expected_members: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise NativeBehaviorReplayError("export manifest file row must be an object")
        name = str(row.get("name", ""))
        if not _safe_zip_name(name):
            raise NativeBehaviorReplayError(f"invalid manifest file name: {name!r}")
        if name == "export_manifest.json" or name in expected_members:
            raise NativeBehaviorReplayError(f"duplicate/reserved manifest file row: {name}")
        expected_members[name] = row
    actual_payload = set(blobs) - {"export_manifest.json"}
    if set(expected_members) != actual_payload:
        missing = sorted(set(expected_members) - actual_payload)
        extra = sorted(actual_payload - set(expected_members))
        raise NativeBehaviorReplayError(f"manifest/archive member mismatch; missing={missing}; extra={extra}")
    for name, row in sorted(expected_members.items()):
        member = blobs[name]
        if int(row.get("size_bytes", -1)) != len(member):
            raise NativeBehaviorReplayError(f"manifest size mismatch: {name}")
        if str(row.get("sha256", "")).casefold() != _sha256(member):
            raise NativeBehaviorReplayError(f"manifest SHA-256 mismatch: {name}")

    provenance = {
        "capture_file_name": path.name,
        "capture_size_bytes": len(blob),
        "capture_sha256": capture_sha,
        "external_sha256_bound": expected_sha256 is not None,
        "export_contract": contract,
        "export_manifest_sha256": _sha256(blobs["export_manifest.json"]),
        "manifest_payload_file_count": len(expected_members),
        "zip_member_count": len(blobs),
        "zip_integrity": "PASS",
        "manifest_integrity": "PASS",
    }
    return blobs, manifest, provenance


def _scan_log_events(log_blob: bytes) -> list[str]:
    try:
        text = log_blob.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise NativeBehaviorReplayError("diagnostic log is not valid UTF-8") from exc
    unknown: set[str] = set()
    for line in text.splitlines():
        parsed = parse_line(line)
        if parsed is None:
            continue
        event, _ = parsed
        if event not in KNOWN_DIAGNOSTIC_EVENTS:
            unknown.add(event)
    return sorted(unknown)


def _parse_trace_from_blob(log_blob: bytes) -> dict[str, Any]:
    unknown = _scan_log_events(log_blob)
    if unknown:
        raise NativeBehaviorReplayError(
            f"unknown future diagnostic event(s) encountered; replay fails closed: {unknown}"
        )
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "transcendence_native_diagnostic_log.txt"
        path.write_bytes(log_blob)
        try:
            return parse_diagnostic_trace(path)
        except (ValueError, KeyError, TypeError) as exc:
            raise NativeBehaviorReplayError(f"diagnostic log parse failed: {exc}") from exc


def _force_map(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for force in snapshot.get("forces", []):
        force_id = str(force.get("force_cqi", ""))
        if not force_id or force_id == "-1":
            continue
        if force_id in out:
            raise NativeBehaviorReplayError(f"duplicate force_cqi in snapshot: {force_id}")
        out[force_id] = force
    return out


def _position(force: dict[str, Any] | None) -> tuple[float, float] | None:
    if force is None:
        return None
    try:
        x, y = float(force.get("x", -1)), float(force.get("y", -1))
    except (TypeError, ValueError):
        return None
    if x < 0 or y < 0:
        return None
    return x, y


def _force_identity(force: dict[str, Any] | None) -> tuple[str, str, str] | None:
    if force is None:
        return None
    general = str(force.get("general_cqi", "-1"))
    subtype = str(force.get("subtype", "unknown"))
    char_type = str(force.get("character_type_key", "unknown"))
    if general in {"", "-1"} and subtype == "unknown" and char_type == "unknown":
        return None
    return general, subtype, char_type


def _between_battles(
    battles: list[dict[str, Any]],
    faction: str,
    force_cqi: str,
    left_event_index: int,
    right_event_index: int,
) -> tuple[list[int], list[str]]:
    sequences: list[int] = []
    roles: set[str] = set()
    for battle in battles:
        index = int(battle["begin_event_index"])
        if not (left_event_index < index < right_event_index):
            continue
        matched = [
            row for row in battle.get("participants", [])
            if str(row.get("faction")) == faction and str(row.get("force_cqi")) == force_cqi
        ]
        if matched:
            sequences.append(int(battle["battle_sequence"]))
            roles.update(str(row.get("side")) for row in matched)
    return sorted(sequences), sorted(roles)


def build_force_timeline(trace: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    identity_flags: list[dict[str, Any]] = []
    previous_identity: dict[tuple[str, str], tuple[int, tuple[str, str, str]]] = {}
    battles = sorted(trace.get("battle_sequences", []), key=lambda row: int(row["begin_event_index"]))

    for observation in sorted(trace.get("observations", []), key=lambda row: (int(row["turn"]), str(row["faction"]))):
        turn = int(observation["turn"])
        faction = str(observation["faction"])
        start, end = observation["start"], observation["end"]
        start_forces, end_forces = _force_map(start), _force_map(end)
        wars = sorted(str(row.get("enemy")) for row in end.get("wars", []) if row.get("enemy"))
        owned_regions = sorted(str(row.get("region")) for row in end.get("regions", []) if row.get("region"))
        for force_cqi in sorted(set(start_forces) | set(end_forces), key=lambda value: (len(value), value)):
            start_force = start_forces.get(force_cqi)
            end_force = end_forces.get(force_cqi)
            start_pos, end_pos = _position(start_force), _position(end_force)
            movement = None
            if start_pos is not None and end_pos is not None:
                movement = round(math.hypot(end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]), 6)
            sequences, roles = _between_battles(
                battles,
                faction,
                force_cqi,
                int(start["end_event_index"]),
                int(end["begin_event_index"]),
            )
            identity = _force_identity(end_force or start_force)
            discontinuity = False
            if identity is not None:
                key = (faction, force_cqi)
                prior = previous_identity.get(key)
                if prior is not None and prior[0] + 1 == turn and prior[1] != identity:
                    discontinuity = True
                    identity_flags.append({
                        "faction": faction,
                        "force_cqi": force_cqi,
                        "prior_turn": prior[0],
                        "turn": turn,
                        "prior_identity": list(prior[1]),
                        "current_identity": list(identity),
                        "classification": "FORCE_CQI_CONSECUTIVE_IDENTITY_CHANGE",
                    })
                previous_identity[key] = (turn, identity)

            def get(force: dict[str, Any] | None, key: str) -> Any:
                return None if force is None else force.get(key)

            rows.append({
                "faction": faction,
                "force_cqi": force_cqi,
                "turn": turn,
                "present_start": start_force is not None,
                "present_end": end_force is not None,
                "start_x": None if start_pos is None else start_pos[0],
                "start_y": None if start_pos is None else start_pos[1],
                "end_x": None if end_pos is None else end_pos[0],
                "end_y": None if end_pos is None else end_pos[1],
                "movement_distance": movement,
                "start_region": get(start_force, "region"),
                "end_region": get(end_force, "region"),
                "start_stance": get(start_force, "stance"),
                "end_stance": get(end_force, "stance"),
                "start_unit_count": get(start_force, "unit_count"),
                "end_unit_count": get(end_force, "unit_count"),
                "start_average_unit_health_pct": get(start_force, "average_unit_health_pct"),
                "end_average_unit_health_pct": get(end_force, "average_unit_health_pct"),
                "start_force_strength": get(start_force, "force_strength"),
                "end_force_strength": get(end_force, "force_strength"),
                "start_action_points_remaining_pct": get(start_force, "action_points_remaining_pct"),
                "end_action_points_remaining_pct": get(end_force, "action_points_remaining_pct"),
                "wars": wars,
                "owned_regions": owned_regions,
                "territorial": bool(owned_regions),
                "battle_sequences": sequences,
                "battle_roles": roles,
                "telemetry_complete": True,
                "identity_discontinuity": discontinuity,
            })
    return rows, identity_flags


def _capture_completeness(trace: dict[str, Any]) -> dict[str, Any]:
    capability_failures = [row for row in trace.get("capabilities", []) if row.get("available") is False]
    incomplete_turns = list(trace.get("incomplete_ai_faction_turns", []))
    incomplete_battles = list(trace.get("incomplete_battle_sequences", []))
    battle_declared = trace.get("battle_participant_telemetry_declared") is True
    consecutive = trace.get("human_turns_consecutive") is True
    human_turns = list(trace.get("human_turn_starts", []))
    human_turns_present = bool(human_turns)
    complete_battles = len(trace.get("battle_sequences", []))
    analysis_eligible = all((battle_declared, consecutive, human_turns_present, not capability_failures, not incomplete_turns, not incomplete_battles))
    return {
        "battle_participant_telemetry_declared": battle_declared,
        "complete_battle_sequence_count": complete_battles,
        "incomplete_battle_sequence_count": len(incomplete_battles),
        "incomplete_battle_sequences": incomplete_battles,
        "incomplete_ai_faction_turn_count": len(incomplete_turns),
        "incomplete_ai_faction_turns": incomplete_turns,
        "capability_failure_count": len(capability_failures),
        "capability_failures": capability_failures,
        "human_turn_starts": human_turns,
        "human_turns_present": human_turns_present,
        "human_turns_consecutive": consecutive,
        "frozen_metric_replay_eligible": analysis_eligible,
        "battle_surface_observed": complete_battles > 0,
        "battle_absence_interpretation": (
            "BATTLE_TELEMETRY_MISSING_OR_UNDECLARED; DO_NOT_INFER_NO_BATTLE"
            if not battle_declared
            else (
                "INCOMPLETE_BATTLE_SEQUENCE_PRESENT; DO_NOT_INFER_NO_BATTLE_FROM_MISSING_END"
                if incomplete_battles
                else "DECLARED_BATTLE_TELEMETRY_SURFACE_VALID"
            )
        ),
    }


def _stored_result_check(
    blobs: dict[str, bytes],
    result_name: str | None,
    recomputed: dict[str, Any] | None,
) -> dict[str, Any]:
    if result_name is None:
        return {"stored_result_present": False, "recomputed_match": None}
    stored = _load_json_blob(blobs, result_name, required=False)
    if stored is None:
        return {"stored_result_present": False, "recomputed_match": None}
    if recomputed is None:
        return {
            "stored_result_present": True,
            "stored_result_digest": stored.get("result_digest"),
            "recomputed_match": None,
            "reason": "REPLAY_INELIGIBLE_CAPTURE; STORED_RESULT_NOT_USED_AS_SUBSTITUTE",
        }
    matches = stored == recomputed
    if not matches:
        raise NativeBehaviorReplayError(
            f"stored frozen result {result_name} does not exactly match deterministic replay"
        )
    return {
        "stored_result_present": True,
        "stored_result_digest": stored.get("result_digest"),
        "recomputed_result_digest": recomputed.get("result_digest"),
        "recomputed_match": True,
    }


def _exploratory_diagnostics(
    timeline: list[dict[str, Any]],
    frozen: dict[str, Any] | None,
    identity_flags: list[dict[str, Any]],
) -> dict[str, Any]:
    movements = [float(row["movement_distance"]) for row in timeline if row.get("movement_distance") is not None]
    battle_adjacent = [row for row in timeline if row.get("battle_sequences")]
    battle_free = [row for row in timeline if not row.get("battle_sequences")]
    per_force_turns: dict[tuple[str, str], int] = Counter((row["faction"], row["force_cqi"]) for row in timeline)
    faction_turns: dict[str, set[int]] = defaultdict(set)
    for row in timeline:
        faction_turns[str(row["faction"])].add(int(row["turn"]))
    faction_rows = []
    for faction, turns in sorted(faction_turns.items()):
        ordered = sorted(turns)
        gaps = [[a, b] for a, b in zip(ordered, ordered[1:]) if b - a > 1]
        faction_rows.append({"faction": faction, "observed_turns": ordered, "gaps": gaps})

    cluster = None if frozen is None else frozen.get("territorial_cluster_diagnostics")
    reversal_by_force: dict[tuple[str, str], int] = Counter()
    if isinstance(cluster, dict):
        for row in cluster.get("candidate_windows", []):
            reversal_by_force[(str(row.get("faction")), str(row.get("force_cqi")))] += 1

    return {
        "label": "EXPLORATORY",
        "movement_distance_distribution": {
            "count": len(movements),
            "minimum": None if not movements else round(min(movements), 6),
            "median": None if not movements else round(float(statistics.median(movements)), 6),
            "maximum": None if not movements else round(max(movements), 6),
            "stationary_force_turn_count": sum(value == 0.0 for value in movements),
        },
        "battle_adjacency": {
            "battle_participating_force_turn_count": len(battle_adjacent),
            "battle_free_force_turn_count": len(battle_free),
        },
        "force_turn_counts": [
            {"faction": faction, "force_cqi": force, "force_turn_count": count}
            for (faction, force), count in sorted(per_force_turns.items())
        ],
        "territorial_reversal_counts_by_force": [
            {"faction": faction, "force_cqi": force, "reversal_candidate_count": count}
            for (faction, force), count in sorted(reversal_by_force.items())
        ],
        "faction_observation_continuity": faction_rows,
        "force_cqi_identity_discontinuities": identity_flags,
        "territorial_cluster_concentration": None if not isinstance(cluster, dict) else cluster.get("candidate_concentration"),
        "interpretation": "EXPLORATORY_ONLY; DOES_NOT_CHANGE_FROZEN_THRESHOLDS_OR_EARN_APPLICATION_AUTHORITY",
    }


def replay_capture(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    path = path.resolve()
    blobs, manifest, provenance = _read_capture(path, expected_sha256)
    config = SUPPORTED_EXPORTS[str(manifest["contract"])]
    profile = str(config["profile"])
    log_blob = blobs.get("transcendence_native_diagnostic_log.txt")
    if log_blob is None:
        raise NativeBehaviorReplayError("capture lacks transcendence_native_diagnostic_log.txt")
    trace = _parse_trace_from_blob(log_blob)
    _validate_authority(trace, "parsed trace")
    completeness = _capture_completeness(trace)
    timeline, identity_flags = build_force_timeline(trace)

    profile_binding_name = config.get("profile_binding")
    profile_binding = None
    if isinstance(profile_binding_name, str):
        profile_binding = _load_json_blob(blobs, profile_binding_name, required=False)
        if profile_binding is not None:
            _validate_authority(profile_binding, "profile binding")
    verification_name = config.get("verification")
    verification = None
    if isinstance(verification_name, str):
        verification = _load_json_blob(blobs, verification_name, required=False)
        if verification is not None:
            _validate_authority(verification, "capture verification")

    frozen: dict[str, Any] | None = None
    recomputed_result: dict[str, Any] | None = None
    if completeness["frozen_metric_replay_eligible"]:
        base = analyze_native_diagnostic_behavior_study(trace)
        stratification = stratify_temporal_trace(trace)
        territorial_cluster = temporal_cluster_diagnostics(trace, "territorial")
        nonterritorial_cluster = temporal_cluster_diagnostics(trace, "nonterritorial")
        frozen = {
            "base_v0_2n_behavior_result": base,
            "temporal_stratification": stratification,
            "territorial_cluster_diagnostics": territorial_cluster,
            "nonterritorial_cluster_diagnostics": nonterritorial_cluster,
        }
        if profile == "VANILLA":
            recomputed_result = base
        elif profile == "SFO":
            vanilla_reference = _load_json_blob(blobs, "vanilla_reference.json")
            assert vanilla_reference is not None
            recomputed_result = analyze_sfo_benchmark(trace, vanilla_reference)
            frozen["sfo_v0_2p_benchmark_result"] = recomputed_result

    stored_check = _stored_result_check(blobs, config.get("stored_result"), recomputed_result)
    exploratory = _exploratory_diagnostics(timeline, frozen, identity_flags)

    result: dict[str, Any] = {
        "contract": NORMALIZED_CONTRACT,
        "study_version": STUDY_VERSION,
        **_authority_fields(),
        "profile": profile,
        "capture_provenance": provenance,
        "profile_binding": profile_binding,
        "capture_verification": verification,
        "telemetry_completeness": completeness,
        "timeline_schema": {
            "contract": "NATIVE_CAI_FORCE_LONGITUDINAL_TIMELINE_V1",
            "fields": TIMELINE_FIELDS,
            "row_count": len(timeline),
        },
        "timeline": timeline,
        "frozen_metric_replay": frozen,
        "stored_result_reproduction": stored_check,
        "exploratory_diagnostics": exploratory,
        "mechanism_nomination_eligible": False,
        "mechanism_nomination_reason": "CAPTURE_REPLAY_ALONE_CANNOT_EARN_NATIVE_ROW_MECHANISM_SELECTION_OR_APPLICATION",
        "interpretation_limits": [
            "Frozen v0.2N/v0.2P evaluators are reused; Replay Lab does not alter their thresholds or semantics.",
            "Missing or undeclared battle telemetry is never interpreted as evidence that no battle occurred.",
            "Force CQI identity discontinuities are flagged for causal review; Replay Lab does not silently rewrite frozen historical metrics.",
            "Privileged telemetry remains permanently application-ineligible.",
            "Exploratory diagnostics cannot overwrite preregistered results.",
        ],
    }
    result["normalized_digest"] = digest(result)
    return result


def _shared_faction_comparison(vanilla_cluster: dict[str, Any], sfo_cluster: dict[str, Any]) -> dict[str, Any]:
    def rows(cluster: dict[str, Any]) -> dict[str, tuple[int, int]]:
        return {
            str(row["faction"]): (int(row["eligible_windows"]), int(row["reversal_candidates"]))
            for row in cluster.get("faction_rows", [])
            if int(row.get("eligible_windows", 0)) > 0
        }

    vanilla_rows, sfo_rows = rows(vanilla_cluster), rows(sfo_cluster)
    shared = sorted(set(vanilla_rows) & set(sfo_rows))

    def pooled(source: dict[str, tuple[int, int]]) -> dict[str, Any]:
        eligible = sum(source[f][0] for f in shared)
        candidates = sum(source[f][1] for f in shared)
        return {
            "eligible_windows": eligible,
            "reversal_candidates": candidates,
            "reversal_candidate_rate": None if eligible == 0 else round(candidates / eligible, 6),
        }

    return {
        "label": "CAUSAL_REVIEW_POST_HOC",
        "shared_factions": shared,
        "vanilla": pooled(vanilla_rows),
        "sfo": pooled(sfo_rows),
        "interpretation": "POST_HOC_COMPOSITION_REVIEW; CANNOT_ERASE_PREREGISTERED_AGGREGATE_RESULT",
    }


def compare_replays(
    vanilla: dict[str, Any],
    sfo: dict[str, Any],
    *,
    sfo_role: str = "original",
) -> dict[str, Any]:
    if vanilla.get("profile") != "VANILLA":
        raise NativeBehaviorReplayError("comparison vanilla input is not a VANILLA behavior-study export")
    if sfo.get("profile") != "SFO":
        raise NativeBehaviorReplayError("comparison SFO input is not an SFO behavior-study export")
    if sfo_role not in {"original", "stage-a"}:
        raise NativeBehaviorReplayError("sfo_role must be 'original' or 'stage-a'")
    vf = vanilla.get("frozen_metric_replay")
    sf = sfo.get("frozen_metric_replay")
    if not isinstance(vf, dict) or not isinstance(sf, dict):
        raise NativeBehaviorReplayError("both captures must be complete enough for frozen metric replay")
    sfo_benchmark = sf.get("sfo_v0_2p_benchmark_result")
    if not isinstance(sfo_benchmark, dict):
        raise NativeBehaviorReplayError("SFO frozen benchmark result is unavailable")
    vanilla_cluster = vf["territorial_cluster_diagnostics"]
    sfo_cluster = sf["territorial_cluster_diagnostics"]
    synthetic_reference = {
        "reference_digest": digest({"replay_vanilla_cluster": vanilla_cluster}),
        "cluster_diagnostics": vanilla_cluster,
    }
    causal_review = build_causal_review(sfo_benchmark, synthetic_reference)
    shared = _shared_faction_comparison(vanilla_cluster, sfo_cluster)
    stage_a = None
    if sfo_role == "stage-a":
        stage_a = adjudicate_sfo_replication_stage_a(sfo_benchmark)

    preregistered = {
        "label": "PREREGISTERED_RESULT",
        "sfo_role": sfo_role,
        "sfo_v0_2p_decision": sfo_benchmark.get("precommitted_post_sfo_decision"),
        "recovery_status": sfo_benchmark.get("recovery_status"),
        "primary_territorial_temporal_status": sfo_benchmark.get("primary_territorial_temporal_status"),
        "stage_a_adjudication": stage_a,
        "stage_a_policy_digest": replication_policy()["policy_digest"],
        "note": (
            "v0.2Q Stage-A policy applied because the caller explicitly declared this SFO capture role."
            if sfo_role == "stage-a"
            else "v0.2Q Stage-A policy not applied; capture is treated as the original/ordinary SFO benchmark."
        ),
    }
    exploratory = {
        "label": "EXPLORATORY",
        "vanilla": vanilla.get("exploratory_diagnostics"),
        "sfo": sfo.get("exploratory_diagnostics"),
        "aggregate_territorial_rate_delta_sfo_minus_vanilla": (
            None
            if vanilla_cluster.get("reversal_candidate_rate") is None or sfo_cluster.get("reversal_candidate_rate") is None
            else round(float(sfo_cluster["reversal_candidate_rate"]) - float(vanilla_cluster["reversal_candidate_rate"]), 6)
        ),
    }
    result: dict[str, Any] = {
        "contract": COMPARISON_CONTRACT,
        "study_version": STUDY_VERSION,
        **_authority_fields(),
        "inputs": {
            "vanilla_capture_sha256": vanilla["capture_provenance"]["capture_sha256"],
            "sfo_capture_sha256": sfo["capture_provenance"]["capture_sha256"],
            "sfo_role": sfo_role,
        },
        "preregistered_result": preregistered,
        "causal_review": {
            "label": "CAUSAL_REVIEW",
            "shared_faction_comparison": shared,
            "composition_review": causal_review,
        },
        "exploratory_result": exploratory,
        "mechanism_nomination_eligibility": {
            "eligible": False,
            "native_row_ablation_earned": False,
            "application_authority_change_earned": False,
            "reason": (
                "Stage A can at most request fresh vanilla replication; it never earns row ablation."
                if sfo_role == "stage-a"
                else "One vanilla/SFO pair cannot establish profile-level causation or row-level mechanism eligibility."
            ),
        },
        "policy_boundary": {
            "copy_sfo_priority_increases": "PROHIBITED",
            "privileged_telemetry_application_input": "PROHIBITED",
            "project_owned_campaign_orders": "PROHIBITED",
            "v0_2g_v0_2i_revival": "NOT_EARNED",
        },
    }
    result["comparison_digest"] = digest(result)
    return result


def _timeline_csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    import io

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=TIMELINE_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        serialized = dict(row)
        for key in ("wars", "owned_regions", "battle_sequences", "battle_roles"):
            serialized[key] = json.dumps(serialized.get(key), sort_keys=True, separators=(",", ":"))
        writer.writerow(serialized)
    return stream.getvalue().encode("utf-8")


def _capture_summary(normalized: dict[str, Any]) -> dict[str, Any]:
    frozen = normalized.get("frozen_metric_replay") or {}
    base = frozen.get("base_v0_2n_behavior_result") or {}
    strat = frozen.get("temporal_stratification") or {}
    return {
        "contract": "NATIVE_CAI_BEHAVIOR_REPLAY_SUMMARY_V1",
        "study_version": STUDY_VERSION,
        **_authority_fields(),
        "profile": normalized["profile"],
        "capture_sha256": normalized["capture_provenance"]["capture_sha256"],
        "normalized_digest": normalized["normalized_digest"],
        "telemetry_completeness": normalized["telemetry_completeness"],
        "recovery_status": base.get("recovery_status"),
        "temporal_status": base.get("temporal_status"),
        "recovery_metrics": None if not base else {
            key: base["metrics"].get(key)
            for key in (
                "recovering_army_turn_count",
                "recovering_attacker_side_army_turn_count",
                "recovering_attacker_side_rate",
            )
        },
        "territorial_temporal": strat.get("territorial"),
        "nonterritorial_temporal": strat.get("nonterritorial"),
        "mechanism_nomination_eligible": False,
    }


def _capture_markdown(summary: dict[str, Any]) -> str:
    completeness = summary["telemetry_completeness"]
    territorial = summary.get("territorial_temporal") or {}
    lines = [
        "# Native CAI Behavior Replay Lab",
        "",
        f"- Study: `{summary['study_version']}`",
        f"- Profile: `{summary['profile']}`",
        f"- Capture SHA-256: `{summary['capture_sha256']}`",
        f"- Authority: `{summary['authority']}` / application `{summary['application_authority']}`",
        f"- Application eligible: `{str(summary['application_eligible']).lower()}`",
        f"- Frozen replay eligible: `{str(completeness['frozen_metric_replay_eligible']).lower()}`",
        "",
        "## Preregistered replay",
        "",
        f"- Recovery status: `{summary.get('recovery_status')}`",
        f"- Temporal status: `{summary.get('temporal_status')}`",
        f"- Territorial eligible windows: `{territorial.get('eligible_windows')}`",
        f"- Territorial reversal candidates: `{territorial.get('reversal_candidates')}`",
        f"- Territorial reversal rate: `{territorial.get('reversal_candidate_rate')}`",
        f"- Territorial repeated reversal forces: `{territorial.get('repeated_reversal_force_count')}`",
        "",
        "## Telemetry completeness",
        "",
        f"- Complete battles: `{completeness['complete_battle_sequence_count']}`",
        f"- Incomplete battles: `{completeness['incomplete_battle_sequence_count']}`",
        f"- Incomplete AI faction turns: `{completeness['incomplete_ai_faction_turn_count']}`",
        f"- Capability failures: `{completeness['capability_failure_count']}`",
        f"- Battle interpretation: `{completeness['battle_absence_interpretation']}`",
        "",
        "## Boundary",
        "",
        "This replay is research-only. It does not earn a native-row ablation, copy SFO priority increases, make privileged telemetry application-eligible, or authorize project-owned campaign orders.",
        "",
    ]
    return "\n".join(lines)


def _comparison_markdown(comparison: dict[str, Any]) -> str:
    p = comparison["preregistered_result"]
    c = comparison["causal_review"]["shared_faction_comparison"]
    eligibility = comparison["mechanism_nomination_eligibility"]
    temporal = (p.get("sfo_v0_2p_decision") or {}).get("temporal", {})
    stage_a = p.get("stage_a_adjudication") or {}
    lines = [
        "# Native CAI Vanilla ↔ SFO Replay Comparison",
        "",
        f"- Study: `{comparison['study_version']}`",
        f"- Authority: `{comparison['authority']}` / application `{comparison['application_authority']}`",
        f"- SFO role: `{p['sfo_role']}`",
        "",
        "## Preregistered result",
        "",
        f"- v0.2P temporal branch: `{temporal.get('branch')}`",
        f"- v0.2P action: `{temporal.get('action')}`",
        f"- Stage-A branch: `{stage_a.get('branch')}`",
        f"- Stage-A action: `{stage_a.get('action')}`",
        "",
        "## Causal review",
        "",
        f"- Shared factions: `{len(c['shared_factions'])}`",
        f"- Shared-faction vanilla rate: `{c['vanilla']['reversal_candidate_rate']}`",
        f"- Shared-faction SFO rate: `{c['sfo']['reversal_candidate_rate']}`",
        "- Shared-faction restriction is post-hoc and cannot erase the preregistered aggregate result.",
        "",
        "## Exploratory result",
        "",
        f"- Aggregate territorial SFO-minus-vanilla rate delta: `{comparison['exploratory_result']['aggregate_territorial_rate_delta_sfo_minus_vanilla']}`",
        "- Exploratory diagnostics do not change frozen thresholds or decision branches.",
        "",
        "## Mechanism nomination eligibility",
        "",
        f"- Eligible: `{str(eligibility['eligible']).lower()}`",
        f"- Native-row ablation earned: `{str(eligibility['native_row_ablation_earned']).lower()}`",
        f"- Reason: {eligibility['reason']}",
        "",
    ]
    return "\n".join(lines)


def write_replay_outputs(normalized: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = _capture_summary(normalized)
    files = {
        "normalized.json": _json_bytes(normalized),
        "summary.json": _json_bytes(summary),
        "timeline.csv": _timeline_csv_bytes(normalized["timeline"]),
        "report.md": _capture_markdown(summary).encode("utf-8"),
    }
    for name, blob in files.items():
        (output_dir / name).write_bytes(blob)
    return {name: _sha256(blob) for name, blob in sorted(files.items())}


def write_comparison_outputs(comparison: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "comparison.json": _json_bytes(comparison),
        "comparison.md": _comparison_markdown(comparison).encode("utf-8"),
    }
    for name, blob in files.items():
        (output_dir / name).write_bytes(blob)
    return {name: _sha256(blob) for name, blob in sorted(files.items())}


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic v0.2R native CAI Behavior Replay Lab")
    sub = parser.add_subparsers(dest="command", required=True)

    replay = sub.add_parser("replay", help="Normalize and replay one diagnostic capture ZIP")
    replay.add_argument("capture", type=Path)
    replay.add_argument("--expected-sha256")
    replay.add_argument("--output-dir", type=Path, required=True)

    compare = sub.add_parser("compare", help="Compare one vanilla capture with one SFO capture")
    compare.add_argument("--vanilla", type=Path, required=True)
    compare.add_argument("--sfo", type=Path, required=True)
    compare.add_argument("--vanilla-sha256")
    compare.add_argument("--sfo-sha256")
    compare.add_argument("--sfo-role", choices=("original", "stage-a"), default="original")
    compare.add_argument("--output-dir", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "replay":
        normalized = replay_capture(args.capture, expected_sha256=args.expected_sha256)
        output_hashes = write_replay_outputs(normalized, args.output_dir.resolve())
        out = {
            "contract": "NATIVE_CAI_BEHAVIOR_REPLAY_CLI_RESULT_V1",
            "study_version": STUDY_VERSION,
            **_authority_fields(),
            "profile": normalized["profile"],
            "capture_sha256": normalized["capture_provenance"]["capture_sha256"],
            "normalized_digest": normalized["normalized_digest"],
            "output_hashes": output_hashes,
        }
    else:
        vanilla = replay_capture(args.vanilla, expected_sha256=args.vanilla_sha256)
        sfo = replay_capture(args.sfo, expected_sha256=args.sfo_sha256)
        comparison = compare_replays(vanilla, sfo, sfo_role=args.sfo_role)
        output_hashes = write_comparison_outputs(comparison, args.output_dir.resolve())
        out = {
            "contract": "NATIVE_CAI_BEHAVIOR_REPLAY_COMPARISON_CLI_RESULT_V1",
            "study_version": STUDY_VERSION,
            **_authority_fields(),
            "comparison_digest": comparison["comparison_digest"],
            "output_hashes": output_hashes,
        }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
