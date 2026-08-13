from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

LAB_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LAB_ROOT.parent
sys.path.insert(0, str(LAB_ROOT))
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))

from transcendence_lab.action_authority import (
    build_action_authority_matrix,
    build_battle4_authority_boundary_report,
)
from transcendence_lab.canonical import read_json
from parse_action_authority_log import parse_action_logs, summarize_action_events
from verify_action_authority_capture import build_action_authority_verification


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build(output_directory: Path) -> list[Path]:
    dense = read_json(LAB_ROOT / "corpora" / "battle4_eilhart_observed_dense_v2.json")
    schedule = read_json(
        REPO_ROOT / "research" / "runtime_evidence" / "BATTLE4_EILHART_TACTICAL_TEMPORAL_SCHEDULE_v0.1Q.json"
    )
    suite = read_json(LAB_ROOT / "scenarios" / "action_authority_matrix_v0.1R.json")
    boundary = build_battle4_authority_boundary_report(dense, schedule)
    matrix = build_action_authority_matrix(suite)
    template = {
        "schema_version": 1,
        "template_contract": "ACTION_AUTHORITY_LIVE_CAPTURE_PACKET_TEMPLATE_V1",
        "authority": "NO_ORDERS",
        "capture_kind": "ordinary_single_player_battle",
        "required_sections": [
            "prepared_session_manifest",
            "public_action_authority_summary",
            "action_authority_verification",
            "public_capture_manifest",
        ],
        "private_local_only_sections": [
            "raw_transcendence_runtime_log",
            "machine_profile",
            "installed_game_path",
            "used_mods_path",
        ],
        "required_claim_separation": [
            "CANDIDATE_ACTION",
            "GAME_COMMAND_EVENT_OBSERVED",
            "PROJECT_ISSUE_ATTEMPT",
            "DIRECT_ACKNOWLEDGEMENT",
            "STATE_MATCH_EVIDENCE",
            "INTERRUPTION_OR_CANCELLATION",
            "OUTCOME_ATTRIBUTION",
        ],
        "fixed_v0_1r_values": {
            "project_issue_attempt": "NOT_ATTEMPTED",
            "direct_acknowledgement": "UNAVAILABLE_NOT_OBSERVED",
            "acknowledgement_claim": "NOT_ACKNOWLEDGED",
            "outcome_attribution": "UNVERIFIED_NOT_ATTRIBUTED",
        },
        "interpretation_limits": [
            "The command callback does not identify player-versus-script origin.",
            "Selection binding is observational and may be absent.",
            "Reachability is a point-in-time query, not proof of a valid completed route.",
            "State matches do not establish direct acknowledgement or causal execution.",
        ],
    }
    from transcendence_lab.canonical import digest
    template["result_digest"] = digest(template)
    fixture_summary = summarize_action_events(
        parse_action_logs([REPO_ROOT / "runtime_probe" / "fixtures" / "action_authority_log_valid.txt"])
    )
    fixture_manifest = read_json(
        REPO_ROOT / "runtime_probe" / "fixtures" / "action_authority_prepared_manifest_valid.json"
    )
    fixture_verification = build_action_authority_verification(
        summary=fixture_summary,
        prepared_manifest=fixture_manifest,
        expected_pack_sha256="a" * 64,
        fixture_control=True,
    )
    outputs = [
        output_directory / "BATTLE4_EILHART_ACTION_AUTHORITY_BOUNDARY_v0.1R.json",
        output_directory / "ACTION_AUTHORITY_MATRIX_REPORT_v0.1R.json",
        output_directory / "ACTION_AUTHORITY_LIVE_CAPTURE_PACKET_TEMPLATE_v0.1R.json",
        output_directory / "ACTION_AUTHORITY_CAPTURE_VERIFICATION_FIXTURE_v0.1R.json",
    ]
    _write(outputs[0], boundary)
    _write(outputs[1], matrix)
    _write(outputs[2], template)
    _write(outputs[3], fixture_verification)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=REPO_ROOT / "research" / "runtime_evidence",
    )
    args = parser.parse_args()
    for path in build(args.output_directory):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
