from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from parse_battle_log import canonical_json

EXPECTED_REPLAY_SHA256 = "76b8807f5cc2d223d454028f54fc18b791a254c3ce543aa587ad4286658e302b"


def build_dense_replay_verification(
    *,
    summary: dict[str, Any],
    report: dict[str, Any],
    manifest: dict[str, Any],
    expected_pack_sha256: str,
    expected_replay_sha256: str = EXPECTED_REPLAY_SHA256,
    battle_identity: str = "Battle of Eilhart — Reikland vs Empire Secessionists",
) -> dict[str, Any]:
    sessions = list(summary.get("sessions", []))
    reports = list(report.get("battle_reports", []))
    replay_sessions = [
        item
        for item in sessions
        if str(item.get("battle_start", {}).get("replay", "false")).lower() == "true"
    ]
    replay_reports = [
        item
        for item in reports
        if str(item.get("metadata", {}).get("replay", "false")).lower() == "true"
    ]
    battle = replay_reports[0] if replay_reports else {}
    sampling = battle.get("sampling", {})
    identity = battle.get("identity", {})
    counts = battle.get("unit_counts", {})
    commands = battle.get("commands", {})
    authority = report.get("authority", {})

    checks = {
        "exact_pack_verified": manifest.get("installed_pack_sha256") == expected_pack_sha256,
        "exact_replay_verified": manifest.get("target", {}).get("replay_sha256") == expected_replay_sha256,
        "schema2_session_observed": bool(replay_sessions)
        and all(int(item.get("schema", 0)) == 2 for item in replay_sessions),
        "completed_replay_observed": bool(replay_sessions)
        and any(item.get("complete") is True for item in replay_sessions),
        "required_capability_failures_absent": not summary.get("capability_failures"),
        "dense_interval_coverage": sampling.get("quality") == "DENSE_INTERVAL_COVERAGE"
        and sampling.get("time_series_metrics_valid") is True,
        "maximum_detail_gap_bounded": isinstance(sampling.get("maximum_sample_gap_ms"), int)
        and sampling.get("maximum_sample_gap_ms") <= 9000,
        "sampler_heartbeat_observed": bool(battle.get("sampler_heartbeats")),
        "stable_identity_without_aliases": identity.get("identity_alias_count") == 0
        and identity.get("identity_conflicts") == [],
        "local_units_observed": int(counts.get("local_canonical", 0)) > 0,
        "visible_enemy_units_observed": int(counts.get("visible_enemy_canonical", 0)) > 0,
        "terminal_coverage_reported": isinstance(
            battle.get("outcome_metrics", {}).get("local_terminal_coverage_ratio"),
            (int, float),
        ),
        "read_only_authority_preserved": bool(authority)
        and all(value is False for value in authority.values()),
        "log_volume_bounded": int(manifest.get("captured_log_size_bytes", 0)) <= 100 * 1024 * 1024,
    }
    selection_ratio = commands.get("selection_attribution_ratio")
    selection_observed = isinstance(selection_ratio, (int, float)) and selection_ratio > 0
    core_passed = all(checks.values())
    if core_passed and selection_observed:
        status = "OBSERVED_DENSE"
    elif core_passed:
        status = "OBSERVED_DENSE_SELECTION_LIMITING_RESULT"
    elif manifest.get("battle_complete_marker_observed"):
        status = "PARTIAL"
    else:
        status = "UNVERIFIED"

    result: dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "evidence_label": "OBSERVED" if status.startswith("OBSERVED_DENSE") else "UNVERIFIED",
        "target": {
            "battle_identity": battle_identity,
            "replay_sha256": expected_replay_sha256,
            "expected_pack_sha256": expected_pack_sha256,
        },
        "checks": checks,
        "selection_callback_observed": selection_observed,
        "metrics": {
            "detail_samples": sampling.get("observed_detail_samples"),
            "expected_detail_samples": sampling.get("expected_detail_samples"),
            "coverage_ratio": sampling.get("coverage_ratio"),
            "maximum_sample_gap_ms": sampling.get("maximum_sample_gap_ms"),
            "sampler_heartbeat_count": len(battle.get("sampler_heartbeats", [])),
            "aggregate_sample_count": sum(
                len(items) for items in battle.get("aggregate_timeline", {}).values()
            ),
            "canonical_unit_count": identity.get("canonical_unit_count"),
            "identity_alias_count": identity.get("identity_alias_count"),
            "selection_attribution_ratio": selection_ratio,
            "command_event_count": commands.get("command_event_count"),
            "inferred_command_count": battle.get("inferred_command_attribution", {}).get(
                "inferred_command_count"
            ),
            "captured_log_size_bytes": manifest.get("captured_log_size_bytes"),
        },
        "authority": authority,
        "warnings": [
            "Dense replay telemetry calibrates observation and SyntheticLab; it does not prove order acceptance or tactical-AI quality.",
            "Visible-enemy time series remains intentionally incomplete while units are hidden.",
            "Inferred command attribution is never an acknowledgement and must remain separately labeled.",
        ],
    }
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Battle 4 dense replay telemetry.")
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-pack-sha256", required=True)
    parser.add_argument("--expected-replay-sha256", default=EXPECTED_REPLAY_SHA256)
    parser.add_argument(
        "--battle-identity",
        default="Battle of Eilhart — Reikland vs Empire Secessionists",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_dense_replay_verification(
        summary=json.loads(args.summary.read_text(encoding="utf-8-sig")),
        report=json.loads(args.report.read_text(encoding="utf-8-sig")),
        manifest=json.loads(args.manifest.read_text(encoding="utf-8-sig")),
        expected_pack_sha256=args.expected_pack_sha256,
        expected_replay_sha256=args.expected_replay_sha256,
        battle_identity=args.battle_identity,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["status"].startswith("OBSERVED_DENSE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
