from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))

from run_native_diagnostic_telemetry import parse_diagnostic_log, parse_diagnostic_trace
from verify_native_diagnostic_profile import build_profile_binding
from prepare_native_behavior_study import PROFILE_NAME, PLAYER_ACTION_PROTOCOL
from transcendence_lab.native_diagnostic_study import analyze_native_diagnostic_behavior_study, frozen_thresholds_digest


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def collect_behavior_study(prepared_path: Path) -> dict:
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
    if prepared.get("contract") != "NATIVE_CAI_DIAGNOSTIC_BEHAVIOR_STUDY_PREPARED_SESSION_V1":
        raise ValueError("unexpected prepared behavior-study contract")
    if prepared.get("frozen_thresholds_digest") != frozen_thresholds_digest():
        raise ValueError("behavior-study frozen threshold digest drifted after preparation")

    prior_public = json.loads(Path(prepared["profile_binding_public"]).read_text(encoding="utf-8"))
    current_public, _ = build_profile_binding(
        game_root=Path(prepared["game_root"]),
        appdata_root=Path(prepared["appdata_root"]),
        probe_path=Path(prepared["installed_probe"]),
        profile_name=PROFILE_NAME,
        player_action_protocol=PLAYER_ACTION_PROTOCOL,
    )
    if (
        current_public["game"] != prior_public["game"]
        or current_public["probe"] != prior_public["probe"]
        or current_public["launcher"] != prior_public["launcher"]
        or current_public.get("binding_sha256") != prior_public.get("binding_sha256")
    ):
        raise ValueError("behavior-study profile/hash drift detected after the run")

    log = Path(prepared["runtime_log"])
    if not log.is_file():
        raise ValueError("native diagnostic runtime log is missing")
    summary = parse_diagnostic_log(log)
    trace = parse_diagnostic_trace(log)
    turns = summary["human_turn_starts"]
    minimum = int(prepared["minimum_human_turn_starts"])
    continuity_ok = bool(turns) and summary["human_turns_consecutive"]
    if not continuity_ok:
        raise ValueError(f"human turn-start markers are non-consecutive or absent; observed {turns}")

    minimum_met = len(turns) >= minimum
    zero_capability_failures = summary["capability_failure_count"] == 0
    zero_incomplete_faction_turns = len(summary["incomplete_ai_faction_turns"]) == 0
    zero_incomplete_battles = len(trace["incomplete_battle_sequences"]) == 0
    battle_surface_observed = len(trace["battle_sequences"]) >= 1
    confirmatory_eligible = all((
        minimum_met,
        zero_capability_failures,
        zero_incomplete_faction_turns,
        zero_incomplete_battles,
        battle_surface_observed,
    ))

    study_result = analyze_native_diagnostic_behavior_study(trace) if confirmatory_eligible else None
    verification = {
        "contract": "NATIVE_CAI_DIAGNOSTIC_BEHAVIOR_STUDY_VERIFICATION_V1",
        "study_version": "v0.2N",
        "profile_checks": {"hashes_launcher_and_binding_unchanged": True},
        "campaign_checks": {
            "human_turn_starts": turns,
            "minimum_required": minimum,
            "required_full_ai_cycles": int(prepared["required_full_ai_cycles"]),
            "consecutive": True,
            "minimum_requirement_met": minimum_met,
        },
        "telemetry_checks": {
            "paired_ai_faction_turns": summary["paired_ai_faction_turns"],
            "capability_failure_count": summary["capability_failure_count"],
            "incomplete_ai_faction_turn_count": len(summary["incomplete_ai_faction_turns"]),
            "complete_battle_sequence_count": len(trace["battle_sequences"]),
            "incomplete_battle_sequence_count": len(trace["incomplete_battle_sequences"]),
            "battle_marker_surface_observed": battle_surface_observed,
        },
        "frozen_thresholds_digest": prepared["frozen_thresholds_digest"],
        "confirmatory_eligible": confirmatory_eligible,
        "verification_status": (
            "PROFILE_BOUND_FRESH_CONFIRMATORY_STUDY_COMPLETE"
            if confirmatory_eligible
            else "PROFILE_BOUND_NONCONFIRMATORY_OR_INCOMPLETE_STUDY_CAPTURE"
        ),
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
    }

    files = {
        "native_behavior_study_verification.json": (json.dumps(verification, indent=2, sort_keys=True) + "\n").encode(),
        "native_behavior_study_profile_binding.json": (json.dumps(prior_public, indent=2, sort_keys=True) + "\n").encode(),
        "native_diagnostic_summary.json": (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode(),
        "transcendence_native_diagnostic_log.txt": log.read_bytes(),
    }
    if study_result is not None:
        files["native_behavior_study_result.json"] = (json.dumps(study_result, indent=2, sort_keys=True) + "\n").encode()

    export = {
        "contract": "NATIVE_CAI_DIAGNOSTIC_BEHAVIOR_STUDY_PUBLIC_EXPORT_V1",
        "study_version": "v0.2N",
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
        "confirmatory_eligible": confirmatory_eligible,
        "contains_private_machine_paths": False,
        "files": [
            {"name": name, "size_bytes": len(blob), "sha256": sha256_bytes(blob)}
            for name, blob in sorted(files.items())
        ],
    }
    files["export_manifest.json"] = (json.dumps(export, indent=2, sort_keys=True) + "\n").encode()

    suffix = "" if confirmatory_eligible else "_NONCONFIRMATORY"
    output = prepared_path.parents[4] / f"Transcendence_NativeBehaviorStudy_VANILLA{suffix}_{stamp()}.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, blob in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, blob)
    if zipfile.ZipFile(output).testzip() is not None:
        raise ValueError("behavior-study output ZIP integrity failure")
    return {
        "output": str(output),
        "size_bytes": output.stat().st_size,
        "sha256": sha256_bytes(output.read_bytes()),
        "confirmatory_eligible": confirmatory_eligible,
        "human_turn_starts_observed": turns,
        "complete_battle_sequence_count": len(trace["battle_sequences"]),
        "study_result_digest": None if study_result is None else study_result["result_digest"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect frozen v0.2N native CAI behavior study")
    parser.add_argument("--prepared", type=Path)
    args = parser.parse_args()
    if args.prepared:
        prepared = args.prepared.resolve()
    else:
        latest = REPO_ROOT / "local_inputs/runtime_probe/native_behavior_study_sessions/latest.json"
        if not latest.is_file():
            raise ValueError("no prepared v0.2N behavior-study session found")
        prepared = Path(json.loads(latest.read_text(encoding="utf-8"))["prepared_session"])
    print(json.dumps(collect_behavior_study(prepared), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
