from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe/tools"))
from run_native_diagnostic_telemetry import parse_diagnostic_log
from verify_native_diagnostic_profile import build_profile_binding


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def collect(prepared_path: Path) -> dict:
    prepared=json.loads(prepared_path.read_text(encoding="utf-8"))
    prior_public=json.loads(Path(prepared["profile_binding_public"]).read_text(encoding="utf-8"))
    current_public,_=build_profile_binding(
        game_root=Path(prepared["game_root"]),
        appdata_root=Path(prepared["appdata_root"]),
        probe_path=Path(prepared["installed_probe"]),
    )
    if current_public["game"] != prior_public["game"] or current_public["probe"] != prior_public["probe"] or current_public["launcher"] != prior_public["launcher"]:
        raise ValueError("diagnostic profile/hash drift detected after the run")
    log=Path(prepared["runtime_log"])
    if not log.is_file(): raise ValueError("native diagnostic runtime log is missing")
    summary=parse_diagnostic_log(log)
    turns=summary["human_turn_starts"]
    minimum=int(prepared["minimum_human_turn_starts"])
    minimum_met=len(turns)>=minimum
    continuity_ok=bool(turns) and summary["human_turns_consecutive"]
    if not continuity_ok:
        raise ValueError(f"human turn-start markers are non-consecutive or absent; observed {turns}")
    incomplete_capture=not minimum_met
    analysis=summary["analysis"]
    verification={
        "contract":"NATIVE_CAI_DIAGNOSTIC_CAPTURE_VERIFICATION_V1",
        "profile_checks":{"hashes_and_launcher_unchanged":True},
        "campaign_checks":{
            "human_turn_starts":turns,
            "minimum_required":minimum,
            "consecutive":True,
            "minimum_requirement_met":minimum_met,
            "capture_incomplete_or_aborted":incomplete_capture,
        },
        "telemetry_checks":{
            "paired_ai_faction_turns":summary["paired_ai_faction_turns"],
            "incomplete_ai_faction_turn_count":len(summary["incomplete_ai_faction_turns"]),
            "capability_failure_count":summary["capability_failure_count"],
            "qualification_status":analysis["qualification_status"],
        },
        "authority":"NO_ORDERS",
        "application_authority":"PROHIBITED",
        "research_visibility":"PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible":False,
        "verification_status":("PROFILE_BOUND_INCOMPLETE_DIAGNOSTIC_CAPTURE_OBSERVED" if incomplete_capture else "PROFILE_BOUND_DIAGNOSTIC_CAPTURE_OBSERVED"),
    }
    files={
        "native_diagnostic_capture_verification.json":(json.dumps(verification,indent=2,sort_keys=True)+"\n").encode(),
        "native_diagnostic_profile_binding.json":(json.dumps(prior_public,indent=2,sort_keys=True)+"\n").encode(),
        "native_diagnostic_summary.json":(json.dumps(summary,indent=2,sort_keys=True)+"\n").encode(),
        "transcendence_native_diagnostic_log.txt":log.read_bytes(),
    }
    export={
        "contract":"NATIVE_CAI_DIAGNOSTIC_PUBLIC_EXPORT_V1",
        "authority":"NO_ORDERS",
        "application_authority":"PROHIBITED",
        "research_visibility":"PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible":False,
        "contains_private_machine_paths":False,
        "files":[{"name":name,"size_bytes":len(blob),"sha256":sha256_bytes(blob)} for name,blob in sorted(files.items())],
    }
    files["export_manifest.json"]=(json.dumps(export,indent=2,sort_keys=True)+"\n").encode()
    suffix="_ABORTED" if incomplete_capture else ""
    output=prepared_path.parents[4] / f"Transcendence_NativeDiagnostic_VANILLA{suffix}_{stamp()}.zip"
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,blob in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
            z.writestr(info,blob)
    if zipfile.ZipFile(output).testzip() is not None: raise ValueError("output ZIP integrity failure")
    return {
        "output":str(output),
        "size_bytes":output.stat().st_size,
        "sha256":sha256_bytes(output.read_bytes()),
        "qualification_status":analysis["qualification_status"],
        "capture_incomplete_or_aborted":incomplete_capture,
        "human_turn_starts_observed":turns,
    }


def main() -> int:
    parser=argparse.ArgumentParser(description="Collect v0.2M native diagnostic capture")
    parser.add_argument("--prepared", type=Path)
    args=parser.parse_args()
    if args.prepared:
        prepared=args.prepared.resolve()
    else:
        latest=REPO_ROOT / "local_inputs/runtime_probe/native_diagnostic_sessions/latest.json"
        if not latest.is_file(): raise ValueError("no prepared diagnostic session found")
        prepared=Path(json.loads(latest.read_text(encoding="utf-8"))["prepared_session"])
    result=collect(prepared)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
