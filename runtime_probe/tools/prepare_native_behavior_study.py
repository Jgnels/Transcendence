from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))

from build_probe_packs import build_manifest
from prepare_native_diagnostic_capture import resolve_game_root, stamp
from verify_native_diagnostic_profile import PROBE_NAME, build_profile_binding, sha256
from transcendence_lab.native_diagnostic_study import frozen_thresholds, frozen_thresholds_digest

# Ten complete AI end-turn cycles require observing Reikland turn-start markers 1..11.
MINIMUM_HUMAN_TURN_STARTS = 11
REQUIRED_FULL_AI_CYCLES = 10
PROFILE_NAME = "VANILLA_DIAGNOSTIC_BEHAVIOR_STUDY_v0.2N"
PLAYER_ACTION_PROTOCOL = "UNRESTRICTED_NORMAL_PLAY_FRESH_CONFIRMATORY_COHORT"


def prepare_behavior_study(game_root: Path, appdata_root: Path, assume_yes: bool = False) -> dict:
    stage = REPO_ROOT / "local_inputs" / "runtime_probe" / "native_behavior_study_staged"
    record = build_manifest(REPO_ROOT, REPO_ROOT / "runtime_probe/manifests/native_diagnostic_pack.json", stage)
    if (
        record["probe_kind"] != "native_diagnostic"
        or record["save_mutation"]
        or record["gameplay_mutation"]
    ):
        raise ValueError("behavior-study diagnostic probe authority changed")

    staged = stage / PROBE_NAME
    installed = game_root / "data" / PROBE_NAME
    installed.parent.mkdir(parents=True, exist_ok=True)
    if not installed.is_file() or sha256(installed) != sha256(staged):
        if not assume_yes:
            answer = input("Copy the read-only, research-only v0.2N diagnostic probe into WH3\\data? Type YES: ").strip()
            if answer != "YES":
                raise ValueError("owner confirmation not provided")
        shutil.copy2(staged, installed)

    if not assume_yes:
        print(f"\nOpen the WH3 launcher and enable ONLY {PROBE_NAME}. Disable every other mod, then close the launcher.")
        if input("Type READY when the launcher profile is saved: ").strip().upper() != "READY":
            raise ValueError("launcher profile not confirmed")

    public, private = build_profile_binding(
        game_root=game_root,
        appdata_root=appdata_root,
        probe_path=installed,
        profile_name=PROFILE_NAME,
        player_action_protocol=PLAYER_ACTION_PROTOCOL,
    )
    run_root = REPO_ROOT / "local_inputs/runtime_probe/native_behavior_study_sessions" / f"vanilla_{stamp()}"
    run_root.mkdir(parents=True, exist_ok=True)
    pub_path = run_root / "profile_binding_public.json"
    priv_path = run_root / "profile_binding_private.json"
    pub_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    priv_path.write_text(json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    log = game_root / "transcendence_native_diagnostic_log.txt"
    archived = None
    if log.is_file():
        archive_dir = REPO_ROOT / "local_inputs/runtime_probe/native_diagnostic_log_archives"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive = archive_dir / f"before_behavior_study_{stamp()}.txt"
        shutil.copy2(log, archive)
        archived = {"sha256": sha256(archive), "size_bytes": archive.stat().st_size}
        log.unlink()

    prepared = {
        "contract": "NATIVE_CAI_DIAGNOSTIC_BEHAVIOR_STUDY_PREPARED_SESSION_V1",
        "study_version": "v0.2N",
        "profile_binding_public": str(pub_path),
        "profile_binding_private": str(priv_path),
        "game_root": str(game_root),
        "appdata_root": str(appdata_root),
        "installed_probe": str(installed),
        "runtime_log": str(log),
        "minimum_human_turn_starts": MINIMUM_HUMAN_TURN_STARTS,
        "required_full_ai_cycles": REQUIRED_FULL_AI_CYCLES,
        "requires_battle_marker_surface_observed": True,
        "frozen_thresholds": frozen_thresholds(),
        "frozen_thresholds_digest": frozen_thresholds_digest(),
        "previous_log": archived,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
        "fresh_data_requirement": "LOG_CLEARED_AFTER_PROFILE_BINDING_BEFORE_CONFIRMATORY_RUN",
    }
    prepared_path = run_root / "prepared_session_private.json"
    prepared_path.write_text(json.dumps(prepared, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    latest = REPO_ROOT / "local_inputs/runtime_probe/native_behavior_study_sessions/latest.json"
    latest.write_text(json.dumps({"prepared_session": str(prepared_path)}, indent=2) + "\n", encoding="utf-8")
    return prepared


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare frozen v0.2N native CAI confirmatory behavior study")
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--appdata-root", type=Path, default=Path(os.environ.get("APPDATA", "")))
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    if not str(args.appdata_root):
        raise ValueError("APPDATA unavailable")
    game_root = resolve_game_root(args.game_root)
    result = prepare_behavior_study(game_root, args.appdata_root.resolve(), args.yes)
    print("\nV0.2N NATIVE BEHAVIOR STUDY PREPARED")
    print("Start a NEW disposable Karl Franz Immortal Empires campaign on Legendary / Very Hard.")
    print(f"Reach at least Reikland turn-start marker {result['minimum_human_turn_starts']} (10 complete AI cycles).")
    print("Play normally; autoresolve is allowed. Do not enable any other mod.")
    print("Exit WH3 completely, then run Collect-NativeBehaviorStudy.ps1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
