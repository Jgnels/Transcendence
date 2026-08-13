from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from parse_action_authority_log import (
    ActionAuthorityLogError,
    as_bool,
    as_int,
    parse_action_logs,
    validate_action_events,
)


EXPORT_CONTRACT = "ACTION_FEASIBILITY_WINDOW_EXPORT_V1"
EXPECTED_PACK_SHA256 = "3acf60520b60f87f8c18e13532512324cb7a539626996ce19897fad94cf2d25d"


class ActionFeasibilityExportError(ValueError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _position(fields: dict[str, str], prefix: str) -> dict[str, float] | None:
    available_key = f"{prefix}_available"
    if available_key in fields and not as_bool(fields[available_key]):
        return None
    keys = [f"{prefix}_{axis}" for axis in ("x", "y", "z")]
    if not all(key in fields for key in keys):
        return None
    try:
        return {
            axis: round(float(fields[f"{prefix}_{axis}"]), 6)
            for axis in ("x", "y", "z")
        }
    except ValueError as error:
        raise ActionFeasibilityExportError(f"invalid {prefix} coordinate") from error


def _sample_record(sample: Any, opened_ms: int) -> dict[str, Any]:
    fields = sample.fields
    target_id = fields.get("current_target_id", "none")
    if "hidden" in target_id.lower():
        raise ActionFeasibilityExportError("hidden current-target identity is prohibited")
    record: dict[str, Any] = {
        "time_offset_ms": as_int(fields["time_ms"]) - opened_ms,
        "sample_index": as_int(fields["sample_index"]),
        "unit_id": fields["unit_id"],
        "controllable": as_bool(fields["controllable"]),
        "player_controlled": as_bool(fields["player_controlled"]),
        "ai_controlled": as_bool(fields["ai_controlled"]),
        "script_controlled": as_bool(fields["script_controlled"]),
        "moving": as_bool(fields["moving"]),
        "idle": as_bool(fields["idle"]),
        "leaving": as_bool(fields["leaving"]),
        "routing": as_bool(fields["routing"]),
        "shattered": as_bool(fields["shattered"]),
        "reachability": fields["reachability"],
        "ordered_position_match": as_bool(fields["ordered_position_match"]),
        "current_target_match": as_bool(fields["current_target_match"]),
        "current_target_id": target_id,
        "ordered_position": _position(fields, "ordered_position"),
    }
    return record


def _actor_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    if not samples:
        raise ActionFeasibilityExportError("bound actor has no samples")
    reachability: dict[str, int] = {
        "QUERY_TRUE": 0,
        "QUERY_FALSE": 0,
        "UNAVAILABLE": 0,
        "NOT_APPLICABLE": 0,
    }
    for sample in samples:
        reachability[sample["reachability"]] += 1
    return {
        "sample_count": len(samples),
        "reachability_counts": reachability,
        "any_ordered_position_match": any(item["ordered_position_match"] for item in samples),
        "any_current_target_match": any(item["current_target_match"] for item in samples),
        "any_movement_observed": any(item["moving"] for item in samples),
        "any_control_loss_observed": any(not item["controllable"] for item in samples),
        "any_routing_observed": any(item["routing"] for item in samples),
        "any_shattered_observed": any(item["shattered"] for item in samples),
        "any_leaving_observed": any(item["leaving"] for item in samples),
        "first_query_result": samples[0]["reachability"],
        "last_query_result": samples[-1]["reachability"],
    }


def build_action_feasibility_window_export(
    raw_log: Path,
    prepared_manifest: Path,
    *,
    expected_raw_log_sha256: str | None = None,
    expected_pack_sha256: str = EXPECTED_PACK_SHA256,
) -> dict[str, Any]:
    raw_sha = _sha256(raw_log)
    if expected_raw_log_sha256 is not None and raw_sha != expected_raw_log_sha256:
        raise ActionFeasibilityExportError("raw action-authority log hash mismatch")
    prepared = json.loads(prepared_manifest.read_text(encoding="utf-8-sig"))
    if prepared.get("capture_kind") != "action_authority":
        raise ActionFeasibilityExportError("prepared manifest has wrong capture kind")
    if prepared.get("installed_pack_sha256") != expected_pack_sha256:
        raise ActionFeasibilityExportError("prepared manifest pack mismatch")
    if prepared.get("project_orders_enabled") is not False:
        raise ActionFeasibilityExportError("prepared manifest must keep project orders disabled")
    if prepared.get("active_mod_list_modified") is not False:
        raise ActionFeasibilityExportError("prepared manifest may not modify the active mod list")
    if prepared.get("wh3_save_modified") is not False:
        raise ActionFeasibilityExportError("prepared manifest may not modify saves")

    try:
        sessions = validate_action_events(parse_action_logs([raw_log]))
    except ActionAuthorityLogError as error:
        raise ActionFeasibilityExportError(str(error)) from error
    complete = [item for item in sessions if item.get("complete")]
    if len(complete) != 1:
        raise ActionFeasibilityExportError("exactly one complete action-authority session is required")
    session = complete[0]
    windows = session.get("windows", [])
    public_windows: list[dict[str, Any]] = []
    total_samples = 0
    for window in windows:
        command = window["command"]
        opened = window["open"]
        closed = window["close"]
        command_fields = command.fields
        target_id = command_fields.get("target_unit_id", "none")
        if "hidden" in target_id.lower():
            raise ActionFeasibilityExportError("hidden command target identity is prohibited")
        opened_ms = as_int(opened.fields["time_ms"])
        closed_ms = as_int(closed.fields["time_ms"])
        samples_by_actor: dict[str, list[dict[str, Any]]] = {
            actor: [] for actor in window["actors"]
        }
        for raw_sample in window["samples"]:
            sample = _sample_record(raw_sample, opened_ms)
            samples_by_actor[sample["unit_id"]].append(sample)
            total_samples += 1
        actors = []
        for actor_id in sorted(samples_by_actor):
            actor_samples = sorted(
                samples_by_actor[actor_id],
                key=lambda item: (item["time_offset_ms"], item["sample_index"]),
            )
            summary = _actor_summary(actor_samples)
            actor_record: dict[str, Any] = {
                "unit_id": actor_id,
                "summary": summary,
                "samples": actor_samples,
            }
            actor_record["result_digest"] = _canonical_digest(actor_record)
            actors.append(actor_record)
        record: dict[str, Any] = {
            "window_id": opened.fields["window_id"],
            "command_index": as_int(command_fields["command_index"]),
            "command": command_fields["command"],
            "opened_time_ms": opened_ms,
            "duration_ms": closed_ms - opened_ms,
            "selected_unit_ids": sorted(window["actors"]),
            "target_unit_id": target_id,
            "target_position": _position(command_fields, "target_position"),
            "close_reason": closed.fields["reason"],
            "actor_count": len(actors),
            "actors": actors,
            "project_issue_attempted": False,
            "direct_acknowledgement_observed": False,
            "command_origin": "GAME_COMMAND_EVENT_ORIGIN_UNRESOLVED",
            "interpretation": "OBSERVED_STATE_WINDOW_NOT_CAUSALLY_ATTRIBUTED",
        }
        record["result_digest"] = _canonical_digest(record)
        public_windows.append(record)

    result: dict[str, Any] = {
        "schema_version": 1,
        "export_contract": EXPORT_CONTRACT,
        "capture_kind": "action_feasibility_window_reexport",
        "source_raw_log_sha256": raw_sha,
        "source_raw_log_size_bytes": raw_log.stat().st_size,
        "raw_log_in_export": False,
        "source_prepared_manifest_sha256": _sha256(prepared_manifest),
        "installed_pack_sha256": expected_pack_sha256,
        "session_count": 1,
        "window_count": len(public_windows),
        "sample_count": total_samples,
        "windows": public_windows,
        "authority": "NO_ORDERS",
        "project_issue_attempt_count": 0,
        "direct_acknowledgement_count": 0,
        "privacy_boundary": {
            "raw_lines_included": False,
            "machine_paths_included": False,
            "user_identity_included": False,
            "game_install_path_included": False,
        },
        "interpretation_limits": [
            "The re-export preserves local unit and visible target identities from one read-only capture but excludes raw lines and machine paths.",
            "Command origin remains unresolved and state matches are not acknowledgement.",
            "Reachability is a point-in-time query, not route completion, formation feasibility, arrival, execution, or outcome.",
        ],
    }
    result["result_digest"] = _canonical_digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a public-safe detailed action-feasibility window re-export")
    parser.add_argument("raw_log", type=Path)
    parser.add_argument("prepared_manifest", type=Path)
    parser.add_argument("--expected-raw-log-sha256")
    parser.add_argument("--expected-pack-sha256", default=EXPECTED_PACK_SHA256)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_action_feasibility_window_export(
        args.raw_log,
        args.prepared_manifest,
        expected_raw_log_sha256=args.expected_raw_log_sha256,
        expected_pack_sha256=args.expected_pack_sha256,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
