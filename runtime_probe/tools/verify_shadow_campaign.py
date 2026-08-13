from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from parse_probe_log import canonical_json


EXPECTED_SHADOW_PACK = (
    "c23b8187dde9e0f162b1564b47910714501b9d088b756cb95dfe16cad470b551"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _find_pack(manifest: dict[str, object], name: str) -> dict[str, object] | None:
    packs = manifest.get("installed_probe_packs")
    if not isinstance(packs, list):
        return None
    for item in packs:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def build_campaign_shadow_verification(
    *,
    log_path: Path,
    summary_path: Path,
    manifest_path: Path,
    campaign_report_path: Path,
    expected_pack_sha256: str = EXPECTED_SHADOW_PACK,
    minimum_turns: int = 5,
) -> dict[str, object]:
    summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    campaign = json.loads(campaign_report_path.read_text(encoding="utf-8-sig"))

    log_sha = _sha256(log_path)
    manifest_logs = manifest.get("logs")
    manifest_log_sha = None
    if isinstance(manifest_logs, list) and len(manifest_logs) == 1:
        item = manifest_logs[0]
        if isinstance(item, dict):
            manifest_log_sha = item.get("sha256")

    shadow_pack = _find_pack(
        manifest,
        "transcendence_shadow_probe.pack",
    )
    turns = campaign.get("metrics", {}).get("turns", [])
    turn_count = campaign.get("metrics", {}).get("turn_count")
    sessions = summary.get("sessions")
    shadow_sessions = [
        session
        for session in sessions
        if isinstance(session, dict) and session.get("probe_kind") == "shadow"
    ] if isinstance(sessions, list) else []

    orders_absent = (
        campaign.get("mode") == "SHADOW_NO_ORDERS"
        and "orders" not in campaign
        and campaign.get("authority", {}).get("game_orders_emitted") is False
        and campaign.get("authority", {}).get("save_values_written") is False
    )

    expected_kinds = manifest.get("expected_loaded_probe_kinds")
    loaded_kinds = manifest.get("loaded_probe_kinds")
    unexpected_kinds = manifest.get("unexpected_loaded_probe_kinds")

    processing = manifest.get("processing")
    total_processing_ms = None
    if isinstance(processing, dict):
        values = [
            processing.get("collection_and_parse_ms"),
            processing.get("parse_ms"),
            processing.get("campaign_pipeline_ms"),
            processing.get("verification_ms"),
        ]
        numeric = [
            float(value)
            for value in values
            if isinstance(value, (int, float))
        ]
        total_processing_ms = round(sum(numeric), 3)

    checks = {
        "manifest_binds_raw_log": manifest_log_sha == log_sha,
        "exact_shadow_pack_verified": (
            isinstance(shadow_pack, dict)
            and shadow_pack.get("installed_sha256") == expected_pack_sha256
            and shadow_pack.get("staged_sha256") == expected_pack_sha256
            and shadow_pack.get("matches_staged") is True
            and shadow_pack.get("loaded_in_log") is True
        ),
        "isolated_shadow_session": (
            loaded_kinds == ["shadow"]
            and expected_kinds == ["shadow"]
            and unexpected_kinds == []
            and len(shadow_sessions) >= 1
        ),
        "minimum_turns_observed": (
            isinstance(turn_count, int) and turn_count >= minimum_turns
        ),
        "turns_are_consecutive": (
            isinstance(turns, list)
            and len(turns) == turn_count
            and all(
                isinstance(left, int)
                and isinstance(right, int)
                and right == left + 1
                for left, right in zip(turns, turns[1:])
            )
        ),
        "no_within_snapshot_duplicates": (
            len(shadow_sessions) >= 1
            and all(session.get("duplicate_event_count") == 0 for session in shadow_sessions)
        ),
        "no_capability_failures": (
            summary.get("capability_failures") == []
            and campaign.get("metrics", {}).get("capability_failure_count") == 0
        ),
        "foreign_information_policy_preserved": (
            campaign.get("metrics", {}).get("foreign_proxy_violation_count") == 0
        ),
        "shadow_pipeline_orderless": orders_absent,
        "report_turn_count_matches_summary": (
            len(shadow_sessions) >= 1
            and sum(int(session.get("snapshot_count", 0)) for session in shadow_sessions) == turn_count
        ),
        "log_volume_bounded": log_path.stat().st_size <= 30_000_000,
        "offline_processing_bounded": (
            total_processing_ms is None or total_processing_ms <= 60_000
        ),
    }

    status = "OBSERVED" if all(checks.values()) else "UNVERIFIED"
    result: dict[str, object] = {
        "schema_version": 1,
        "status": status,
        "evidence_label": status,
        "expected_pack_sha256": expected_pack_sha256,
        "minimum_turns": minimum_turns,
        "checks": checks,
        "inputs": {
            "log_sha256": log_sha,
            "summary_sha256": _sha256(summary_path),
            "manifest_sha256": _sha256(manifest_path),
            "campaign_report_sha256": _sha256(campaign_report_path),
        },
        "metrics": {
            "turn_count": turn_count,
            "turns": turns,
            "objective_churn_rate": campaign.get("metrics", {}).get(
                "objective_churn_rate"
            ),
            "hold_rate": campaign.get("metrics", {}).get("hold_rate"),
            "scenario_state_change_count": campaign.get("metrics", {}).get(
                "scenario_state_change_count"
            ),
            "log_size_bytes": log_path.stat().st_size,
            "offline_processing_ms": total_processing_ms,
        },
        "warnings": [
            "This proves an orderless multi-turn observation and proposal pipeline only.",
            "It does not prove that any proposed objective can be issued, accepted, or completed in WH3.",
            "Planner weights and foreign-strength proxies remain uncalibrated.",
        ],
    }
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify one consolidated multi-turn WH3 shadow campaign run."
    )
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--campaign-report", type=Path, required=True)
    parser.add_argument(
        "--expected-pack-sha256",
        default=EXPECTED_SHADOW_PACK,
    )
    parser.add_argument("--minimum-turns", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = build_campaign_shadow_verification(
        log_path=args.log,
        summary_path=args.summary,
        manifest_path=args.manifest,
        campaign_report_path=args.campaign_report,
        expected_pack_sha256=args.expected_pack_sha256,
        minimum_turns=args.minimum_turns,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["status"] == "OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
