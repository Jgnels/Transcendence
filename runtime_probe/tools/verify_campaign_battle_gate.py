from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from parse_probe_log import canonical_json
from verify_shadow_campaign import build_campaign_shadow_verification

EXPECTED_SHADOW_PACK = "bec692bb96c04205e93e97f1e3a60c6b8fcfc7424b540eef8139b7fceaf28261"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_campaign_battle_verification(
    *,
    log_path: Path,
    campaign_summary_path: Path,
    battle_summary_path: Path,
    manifest_path: Path,
    campaign_report_path: Path,
    battle_report_path: Path,
    expected_pack_sha256: str,
    minimum_turns: int = 5,
    minimum_completed_battles: int = 2,
) -> dict[str, object]:
    campaign_verification = build_campaign_shadow_verification(
        log_path=log_path,
        summary_path=campaign_summary_path,
        manifest_path=manifest_path,
        campaign_report_path=campaign_report_path,
        expected_pack_sha256=expected_pack_sha256,
        minimum_turns=minimum_turns,
    )
    battle_summary = json.loads(battle_summary_path.read_text(encoding="utf-8-sig"))
    battle_report = json.loads(battle_report_path.read_text(encoding="utf-8-sig"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))

    session = manifest.get("combined_session_manifest")
    session_checks = {
        "prepared_session_manifest_bound": isinstance(session, dict)
        and isinstance(session.get("sha256"), str)
        and len(session.get("sha256", "")) == 64,
        "prepared_session_pack_matches_expected": isinstance(session, dict)
        and session.get("staged_shadow_pack_sha256") == expected_pack_sha256
        and session.get("installed_shadow_pack_sha256") == expected_pack_sha256,
        "prepared_session_timestamp_present": isinstance(session, dict)
        and isinstance(session.get("prepared_at_utc"), str)
        and bool(session.get("prepared_at_utc")),
    }

    battle_loaded = manifest.get("battle_probe_loaded") is True
    completed = battle_report.get("completed_battle_count", 0)
    battle_sessions = battle_summary.get("battle_session_count", 0)
    capability_failures = battle_summary.get("capability_failures", [])
    authority = battle_report.get("authority", {})
    required_start_fields = {
        "from_campaign",
        "battle_type",
        "local_alliance",
        "unit_scale_factor",
    }
    metadata_complete = all(
        required_start_fields.issubset(set(report.get("metadata", {})))
        for report in battle_report.get("battle_reports", [])
    )
    local_units_observed = any(
        report.get("unit_counts", {}).get("local_canonical", 0) > 0
        for report in battle_report.get("battle_reports", [])
    )
    enemy_units_observed = any(
        report.get("unit_counts", {}).get("visible_enemy_canonical", 0) > 0
        for report in battle_report.get("battle_reports", [])
    )
    samples_observed = any(
        report.get("sampling", {}).get("observed_detail_samples", 0) >= 2
        for report in battle_report.get("battle_reports", [])
    )

    battle_checks = {
        "battle_probe_loaded": battle_loaded,
        "battle_session_observed": isinstance(battle_sessions, int) and battle_sessions >= 1,
        "minimum_completed_battles": isinstance(completed, int) and completed >= minimum_completed_battles,
        "battle_metadata_observed": metadata_complete,
        "local_units_observed": local_units_observed,
        "visible_enemy_units_observed": enemy_units_observed,
        "multiple_battle_samples_observed": samples_observed,
        "battle_capability_failures_absent": capability_failures == [],
        "battle_authority_remained_read_only": (
            authority.get("unitcontrollers_created") is False
            and authority.get("orders_emitted") is False
            and authority.get("battle_speed_modified") is False
            and authority.get("save_values_written") is False
            and authority.get("visibility_modified") is False
        ),
        "combined_log_volume_bounded": log_path.stat().st_size <= 30_000_000,
    }

    campaign_passed = campaign_verification.get("status") == "OBSERVED"
    battle_passed = all(battle_checks.values())
    session_passed = all(session_checks.values())
    if campaign_passed and battle_passed and session_passed:
        status = "OBSERVED"
    elif campaign_passed and completed == 0:
        status = "PARTIAL_NO_BATTLE"
    else:
        status = "UNVERIFIED"

    result: dict[str, object] = {
        "schema_version": 1,
        "status": status,
        "evidence_label": "OBSERVED" if status == "OBSERVED" else "UNVERIFIED",
        "expected_pack_sha256": expected_pack_sha256,
        "campaign_status": campaign_verification.get("status"),
        "battle_status": "OBSERVED" if battle_passed else "UNVERIFIED",
        "campaign_checks": campaign_verification.get("checks", {}),
        "battle_checks": battle_checks,
        "session_checks": session_checks,
        "metrics": {
            "turn_count": campaign_verification.get("metrics", {}).get("turn_count"),
            "completed_battle_count": completed,
            "battle_session_count": battle_sessions,
            "combined_log_size_bytes": log_path.stat().st_size,
            "objective_churn_rate": campaign_verification.get("metrics", {}).get("objective_churn_rate"),
            "battle_command_event_count": sum(
                int(item.get("commands", {}).get("command_event_count", 0))
                for item in battle_report.get("battle_reports", [])
            ),
            "battle_unit_static_count": sum(
                int(item.get("identity", {}).get("raw_unit_static_count", 0))
                for item in battle_report.get("battle_reports", [])
            ),
        },
        "inputs": {
            "log_sha256": sha256(log_path),
            "campaign_summary_sha256": sha256(campaign_summary_path),
            "battle_summary_sha256": sha256(battle_summary_path),
            "manifest_sha256": sha256(manifest_path),
            "campaign_report_sha256": sha256(campaign_report_path),
            "battle_report_sha256": sha256(battle_report_path),
        },
        "authority": {
            "campaign_orders_emitted": False,
            "battle_orders_emitted": False,
            "save_values_written": False,
        },
        "warnings": [
            "This gate observes campaign and ordinary-battle state but does not control either.",
            "Battle telemetry is visibility-filtered and therefore intentionally incomplete for hidden enemies.",
            "Observed player commands are not order acknowledgements and do not prove command success.",
            "Two battles establish interface feasibility and telemetry variety, not tactical-AI quality or SFO compatibility.",
        ],
    }
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the consolidated WH3 campaign+battle gate.")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--campaign-summary", type=Path, required=True)
    parser.add_argument("--battle-summary", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--campaign-report", type=Path, required=True)
    parser.add_argument("--battle-report", type=Path, required=True)
    parser.add_argument("--expected-pack-sha256", required=True)
    parser.add_argument("--minimum-turns", type=int, default=5)
    parser.add_argument("--minimum-completed-battles", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_campaign_battle_verification(
        log_path=args.log,
        campaign_summary_path=args.campaign_summary,
        battle_summary_path=args.battle_summary,
        manifest_path=args.manifest,
        campaign_report_path=args.campaign_report,
        battle_report_path=args.battle_report,
        expected_pack_sha256=args.expected_pack_sha256,
        minimum_turns=args.minimum_turns,
        minimum_completed_battles=args.minimum_completed_battles,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["status"] == "OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
