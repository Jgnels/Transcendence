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
from prepare_native_sfo_behavior_benchmark import PROFILE_NAME, PLAYER_ACTION_PROTOCOL
from verify_native_behavior_sfo_profile import build_sfo_profile_binding
from transcendence_lab.native_diagnostic_benchmark import analyze_sfo_benchmark, benchmark_spec_digest

VANILLA_REFERENCE = REPO_ROOT / "research/runtime_evidence/NATIVE_BEHAVIOR_STUDY_VANILLA_REFERENCE_v0.2O_2026-08-03.json"
CLUSTER_REFERENCE = REPO_ROOT / "research/runtime_evidence/NATIVE_VANILLA_TERRITORIAL_CLUSTER_REFERENCE_v0.2P_2026-08-04.json"
MECHANISTIC_REGISTRY = REPO_ROOT / "research/native_cai/SFO_NATIVE_CAI_MECHANISTIC_REGISTRY_v0.2P_2026-08-04.json"
ABLATION_REGISTRY = REPO_ROOT / "research/native_cai/NATIVE_CAI_ABLATION_CANDIDATE_REGISTRY_v0.2P_2026-08-04.json"
DECISION_TABLE = REPO_ROOT / "research/native_cai/SFO_POST_BENCHMARK_DECISION_TABLE_v0.2P_2026-08-04.json"


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def collect_sfo_benchmark(prepared_path: Path) -> dict:
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
    if prepared.get("contract") != "NATIVE_CAI_DIAGNOSTIC_SFO_BEHAVIOR_BENCHMARK_PREPARED_SESSION_V1":
        raise ValueError("unexpected prepared SFO benchmark contract")
    if prepared.get("benchmark_spec_digest") != benchmark_spec_digest():
        raise ValueError("SFO benchmark spec drifted after preparation")

    prior_public = json.loads(Path(prepared["profile_binding_public"]).read_text(encoding="utf-8"))
    current_public, _ = build_sfo_profile_binding(
        game_root=Path(prepared["game_root"]),
        appdata_root=Path(prepared["appdata_root"]),
        probe_path=Path(prepared["installed_probe"]),
        sfo_pack_path=Path(prepared["sfo_pack_path"]),
        profile_name=PROFILE_NAME,
        player_action_protocol=PLAYER_ACTION_PROTOCOL,
    )
    for key in ("game", "probe", "sfo", "launcher", "binding_sha256"):
        if current_public.get(key) != prior_public.get(key):
            raise ValueError(f"SFO benchmark profile/hash drift detected after the run: {key}")

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
    confirmatory_eligible = all((minimum_met, zero_capability_failures, zero_incomplete_faction_turns, zero_incomplete_battles, battle_surface_observed))

    vanilla_reference = json.loads(VANILLA_REFERENCE.read_text(encoding="utf-8"))
    benchmark_result = analyze_sfo_benchmark(trace, vanilla_reference) if confirmatory_eligible else None
    verification = {
        "contract": "NATIVE_CAI_DIAGNOSTIC_SFO_BEHAVIOR_BENCHMARK_VERIFICATION_V1",
        "study_version": "v0.2P",
        "profile_checks": {"game_probe_sfo_launcher_binding_unchanged": True},
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
        "benchmark_spec_digest": prepared["benchmark_spec_digest"],
        "confirmatory_eligible": confirmatory_eligible,
        "verification_status": (
            "PROFILE_BOUND_FRESH_SFO_BENCHMARK_COMPLETE" if confirmatory_eligible
            else "PROFILE_BOUND_NONCONFIRMATORY_OR_INCOMPLETE_SFO_BENCHMARK_CAPTURE"
        ),
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
    }

    files = {
        "native_sfo_behavior_benchmark_verification.json": (json.dumps(verification, indent=2, sort_keys=True) + "\n").encode(),
        "native_sfo_behavior_profile_binding.json": (json.dumps(prior_public, indent=2, sort_keys=True) + "\n").encode(),
        "native_diagnostic_summary.json": (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode(),
        "vanilla_reference.json": (json.dumps(vanilla_reference, indent=2, sort_keys=True) + "\n").encode(),
        "vanilla_territorial_cluster_reference_v0.2P.json": CLUSTER_REFERENCE.read_bytes(),
        "sfo_mechanistic_registry_v0.2P.json": MECHANISTIC_REGISTRY.read_bytes(),
        "native_cai_ablation_candidate_registry_v0.2P.json": ABLATION_REGISTRY.read_bytes(),
        "post_sfo_decision_table_v0.2P.json": DECISION_TABLE.read_bytes(),
        "transcendence_native_diagnostic_log.txt": log.read_bytes(),
    }
    if benchmark_result is not None:
        files["native_sfo_behavior_benchmark_result.json"] = (json.dumps(benchmark_result, indent=2, sort_keys=True) + "\n").encode()

    export = {
        "contract": "NATIVE_CAI_DIAGNOSTIC_SFO_BEHAVIOR_BENCHMARK_PUBLIC_EXPORT_V1",
        "study_version": "v0.2P",
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
        "confirmatory_eligible": confirmatory_eligible,
        "contains_private_machine_paths": False,
        "contains_sfo_pack_bytes": False,
        "files": [{"name": name, "size_bytes": len(blob), "sha256": sha256_bytes(blob)} for name, blob in sorted(files.items())],
    }
    files["export_manifest.json"] = (json.dumps(export, indent=2, sort_keys=True) + "\n").encode()

    suffix = "" if confirmatory_eligible else "_NONCONFIRMATORY"
    output = prepared_path.parents[4] / f"Transcendence_NativeBehaviorStudy_SFO{suffix}_{stamp()}.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, blob in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, blob)
    if zipfile.ZipFile(output).testzip() is not None:
        raise ValueError("SFO benchmark output ZIP integrity failure")
    return {
        "output": str(output),
        "size_bytes": output.stat().st_size,
        "sha256": sha256_bytes(output.read_bytes()),
        "confirmatory_eligible": confirmatory_eligible,
        "human_turn_starts_observed": turns,
        "complete_battle_sequence_count": len(trace["battle_sequences"]),
        "benchmark_result_digest": None if benchmark_result is None else benchmark_result["result_digest"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect frozen v0.2P matched SFO behavior benchmark")
    parser.add_argument("--prepared", type=Path)
    args = parser.parse_args()
    if args.prepared:
        prepared = args.prepared.resolve()
    else:
        latest = REPO_ROOT / "local_inputs/runtime_probe/native_sfo_behavior_sessions/latest.json"
        if not latest.is_file():
            raise ValueError("no prepared v0.2O SFO behavior benchmark session found")
        prepared = Path(json.loads(latest.read_text(encoding="utf-8"))["prepared_session"])
    print(json.dumps(collect_sfo_benchmark(prepared), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
