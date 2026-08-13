from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class ActionAuthorityVerificationError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ActionAuthorityVerificationError(f"{label} must be a lowercase SHA-256 digest")
    return value


def build_action_authority_verification(
    *,
    summary: dict[str, Any],
    prepared_manifest: dict[str, Any],
    expected_pack_sha256: str,
    fixture_control: bool = False,
) -> dict[str, Any]:
    expected_pack_sha256 = _require_sha(expected_pack_sha256, "expected pack SHA-256")
    if summary.get("schema_version") != 1 or summary.get("authority") != "NO_ORDERS":
        raise ActionAuthorityVerificationError("summary is not a v0.1R NO_ORDERS action-authority summary")
    if prepared_manifest.get("schema_version") != 1:
        raise ActionAuthorityVerificationError("unsupported prepared-session manifest schema")
    if prepared_manifest.get("capture_kind") != "action_authority":
        raise ActionAuthorityVerificationError("prepared manifest has wrong capture kind")

    staged_sha = _require_sha(prepared_manifest.get("staged_pack_sha256"), "staged pack SHA-256")
    installed_sha = _require_sha(prepared_manifest.get("installed_pack_sha256"), "installed pack SHA-256")
    sessions = summary.get("sessions")
    if not isinstance(sessions, list):
        raise ActionAuthorityVerificationError("summary sessions must be a list")

    checks = {
        "exact_expected_pack": staged_sha == expected_pack_sha256 == installed_sha,
        "runtime_log_was_cleared_before_capture": prepared_manifest.get("runtime_log_cleared") is True,
        "active_mod_list_not_modified_by_preparer": prepared_manifest.get("active_mod_list_modified") is False,
        "save_not_modified_by_preparer": prepared_manifest.get("wh3_save_modified") is False,
        "single_complete_session": len(sessions) == 1 and sessions[0].get("complete") is True,
        "required_capabilities_available": len(sessions) == 1 and not sessions[0].get("capability_failures"),
        "at_least_one_command_window": len(sessions) == 1 and int(sessions[0].get("window_count", 0)) >= 1,
        "project_issue_attempts_zero": len(sessions) == 1 and int(sessions[0].get("project_issue_attempt_count", -1)) == 0,
        "direct_acknowledgements_zero": len(sessions) == 1 and int(sessions[0].get("direct_acknowledgement_count", -1)) == 0,
        "authority_remains_no_orders": summary.get("authority") == "NO_ORDERS",
    }
    passed = all(checks.values())
    status = (
        "CONTROL_FIXTURE_READ_ONLY_ACTION_AUTHORITY"
        if fixture_control and passed
        else "OBSERVED_READ_ONLY_ACTION_AUTHORITY"
        if passed
        else "UNVERIFIED_ACTION_AUTHORITY_CAPTURE"
    )
    result = {
        "schema_version": 1,
        "verification_contract": "ACTION_AUTHORITY_CAPTURE_VERIFICATION_V1",
        "status": status,
        "authority": "NO_ORDERS",
        "fixture_control": bool(fixture_control),
        "expected_pack_sha256": expected_pack_sha256,
        "prepared_manifest_pack_sha256": installed_sha,
        "checks": checks,
        "session_count": len(sessions),
        "window_count": sum(int(item.get("window_count", 0)) for item in sessions),
        "bound_window_count": sum(int(item.get("bound_window_count", 0)) for item in sessions),
        "unbound_window_count": sum(int(item.get("unbound_window_count", 0)) for item in sessions),
        "sample_count": sum(int(item.get("sample_count", 0)) for item in sessions),
        "reachability_counts": sessions[0].get("reachability_counts", {}) if len(sessions) == 1 else {},
        "state_match_counts": sessions[0].get("state_match_counts", {}) if len(sessions) == 1 else {},
        "close_reason_counts": sessions[0].get("close_reason_counts", {}) if len(sessions) == 1 else {},
        "project_issue_attempt_count": 0,
        "direct_acknowledgement_count": 0,
        "acknowledgement_claim": "NOT_ACKNOWLEDGED",
        "execution_attribution": "OBSERVED_STATE_ONLY_NOT_CAUSALLY_ATTRIBUTED",
        "outcome_attribution": "UNVERIFIED_NOT_ATTRIBUTED",
        "limiting_results": [
            "Game command callbacks do not identify player-versus-script origin.",
            "State matches are not direct acknowledgement.",
            "Reachability is a point-in-time query and not proof of route completion.",
            "No project order was issued, accepted, acknowledged, executed, or credited with an outcome.",
        ],
    }
    result["result_digest"] = _sha256_bytes(_canonical_json(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify one prepared Transcendence action-authority capture")
    parser.add_argument("summary", type=Path)
    parser.add_argument("prepared_manifest", type=Path)
    parser.add_argument("--expected-pack-sha256", required=True)
    parser.add_argument("--fixture-control", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8-sig"))
    manifest = json.loads(args.prepared_manifest.read_text(encoding="utf-8-sig"))
    result = build_action_authority_verification(
        summary=summary,
        prepared_manifest=manifest,
        expected_pack_sha256=args.expected_pack_sha256,
        fixture_control=args.fixture_control,
    )
    blob = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(blob, encoding="utf-8")
    print(blob, end="")
    return 0 if all(result["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
