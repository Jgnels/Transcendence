from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from parse_probe_log import canonical_json
from verify_campaign_battle_gate import build_campaign_battle_verification
from watch_combined_runtime_log import marker_summary

EXPECTED_SFO_WORKSHOP_ID = "2792731173"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def verify_checkpoint_chain(
    *,
    log_path: Path,
    checkpoint_manifest_path: Path,
    expected_handshake_token: str | None = None,
) -> dict[str, Any]:
    manifest = load_json(checkpoint_manifest_path)
    checkpoints = manifest.get("checkpoints")
    violations = manifest.get("violations")
    schema = manifest.get("schema_version")
    token = manifest.get("handshake_token")
    checks: dict[str, bool] = {
        "manifest_schema": (schema == 1 and expected_handshake_token is None)
        or (schema == 2 and isinstance(expected_handshake_token, str)),
        "handshake_token_matches": (
            expected_handshake_token is None
            if schema == 1
            else isinstance(token, str)
            and token == expected_handshake_token
            and len(token) == 64
            and all(character in "0123456789abcdef" for character in token)
        ),
        "watcher_stopped": manifest.get("state") == "STOPPED",
        "watcher_reported_no_violations": violations == [],
        "checkpoint_list_present": isinstance(checkpoints, list) and len(checkpoints) >= 2,
    }
    checked: list[dict[str, Any]] = []
    previous = b""
    if isinstance(checkpoints, list):
        for expected_sequence, record in enumerate(checkpoints, start=1):
            if not isinstance(record, dict):
                checks["checkpoint_records_valid"] = False
                continue
            path_value = record.get("private_path")
            path = Path(path_value) if isinstance(path_value, str) else Path("__missing__")
            exists = path.is_file()
            data = path.read_bytes() if exists else b""
            record_valid = (
                exists
                and record.get("sequence") == expected_sequence
                and record.get("filename") == path.name
                and record.get("size_bytes") == len(data)
                and record.get("sha256") == hashlib.sha256(data).hexdigest()
                and (not previous or data.startswith(previous))
            )
            checked.append(
                {
                    "sequence": record.get("sequence"),
                    "reason": record.get("reason"),
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest() if exists else None,
                    "prefix_chain_valid": bool(not previous or data.startswith(previous)),
                    "record_valid": record_valid,
                    "markers": marker_summary(data) if exists else None,
                }
            )
            if not record_valid:
                checks["checkpoint_records_valid"] = False
            previous = data
    checks.setdefault("checkpoint_records_valid", True)
    final_data = log_path.read_bytes()
    final_record = checked[-1] if checked else None
    checks["final_checkpoint_matches_log"] = bool(
        final_record
        and final_record["size_bytes"] == len(final_data)
        and final_record["sha256"] == hashlib.sha256(final_data).hexdigest()
    )
    return {
        "status": "OBSERVED" if all(checks.values()) else "UNVERIFIED",
        "checks": checks,
        "checkpoint_count": len(checked),
        "checkpoints": checked,
        "final_log_size_bytes": len(final_data),
        "final_log_sha256": hashlib.sha256(final_data).hexdigest(),
    }


def transition_analysis(log_path: Path) -> dict[str, Any]:
    summary = marker_summary(log_path.read_bytes())
    events = summary["transition_events"]
    battle_indices = [index for index, event in enumerate(events) if event == "BATTLE_RUNTIME_BEGIN"]
    complete_indices = [index for index, event in enumerate(events) if event == "BATTLE_COMPLETE"]
    campaign_indices = [index for index, event in enumerate(events) if event == "CAMPAIGN_RUNTIME_BEGIN"]
    first_campaign_before_battle = bool(battle_indices and campaign_indices and campaign_indices[0] < battle_indices[0])
    complete_has_campaign_return: list[bool] = []
    for complete_index in complete_indices:
        next_battle_index = next((index for index in battle_indices if index > complete_index), None)
        complete_has_campaign_return.append(
            any(
                campaign_index > complete_index
                and (next_battle_index is None or campaign_index < next_battle_index)
                for campaign_index in campaign_indices
            )
        )
    return {
        **summary,
        "first_campaign_before_first_battle": first_campaign_before_battle,
        "battle_complete_followed_by_campaign_return": complete_has_campaign_return,
        "all_battles_returned_to_campaign": bool(complete_indices)
        and len(complete_indices) == len(battle_indices)
        and all(complete_has_campaign_return),
    }


def build_sfo_combined_verification(
    *,
    log_path: Path,
    campaign_summary_path: Path,
    battle_summary_path: Path,
    evidence_manifest_path: Path,
    campaign_report_path: Path,
    battle_report_path: Path,
    environment_profile_path: Path,
    checkpoint_manifest_path: Path,
    expected_pack_sha256: str,
    minimum_turns: int,
    minimum_completed_battles: int,
    expected_handshake_token: str | None = None,
) -> dict[str, Any]:
    combined = build_campaign_battle_verification(
        log_path=log_path,
        campaign_summary_path=campaign_summary_path,
        battle_summary_path=battle_summary_path,
        manifest_path=evidence_manifest_path,
        campaign_report_path=campaign_report_path,
        battle_report_path=battle_report_path,
        expected_pack_sha256=expected_pack_sha256,
        minimum_turns=minimum_turns,
        minimum_completed_battles=minimum_completed_battles,
    )
    environment = load_json(environment_profile_path)
    mods = environment.get("active_mods")
    sfo = environment.get("sfo") if isinstance(environment.get("sfo"), dict) else {}
    game = environment.get("game") if isinstance(environment.get("game"), dict) else {}
    settings = environment.get("settings") if isinstance(environment.get("settings"), dict) else {}
    probe_binding = (
        environment.get("probe_binding")
        if isinstance(environment.get("probe_binding"), dict)
        else {}
    )
    expected_probe = (
        environment.get("expected_probe")
        if isinstance(environment.get("expected_probe"), dict)
        else {}
    )
    profile_id = environment.get("profile_id")
    exact_profile = profile_id == "SFO_ONLY_PLUS_READ_ONLY_PROBE"
    deferred_profile = profile_id == "SFO_ONLY_PLUS_READ_ONLY_PROBE_RUNTIME_DEFERRED"
    exact_probe_record = isinstance(mods, list) and any(
        isinstance(record, dict)
        and record.get("role") == "READ_ONLY_TRANSCENDENCE_PROBE"
        and record.get("sha256") == expected_pack_sha256
        for record in mods
    )
    sfo_record_count = (
        sum(
            1
            for record in mods
            if isinstance(record, dict) and record.get("role") == "SFO_TOTAL_OVERHAUL"
        )
        if isinstance(mods, list)
        else 0
    )
    runtime_probe_confirmed = (
        combined.get("status") == "OBSERVED"
        and combined.get("session_checks", {}).get("prepared_session_pack_matches_expected") is True
        and combined.get("battle_checks", {}).get("battle_probe_loaded") is True
    )
    deferred_binding_valid = (
        deferred_profile
        and environment.get("schema_version") == 2
        and isinstance(mods, list)
        and len(mods) == 1
        and sfo_record_count == 1
        and probe_binding.get("status") == "DEFERRED_RUNTIME_MARKER"
        and probe_binding.get("runtime_confirmation_required") is True
        and expected_probe.get("pack_sha256") == expected_pack_sha256
        and runtime_probe_confirmed
    )
    environment_checks = {
        "profile_schema": (exact_profile and environment.get("schema_version") in (1, 2))
        or (deferred_profile and environment.get("schema_version") == 2),
        "sfo_only_profile": exact_profile or deferred_profile,
        "sfo_workshop_id": sfo.get("workshop_id") == EXPECTED_SFO_WORKSHOP_ID,
        "sfo_full_pack_hash_present": isinstance(sfo.get("pack_sha256"), str) and len(sfo.get("pack_sha256", "")) == 64,
        "game_executable_hash_present": isinstance(game.get("executable_sha256"), str)
        and len(game.get("executable_sha256", "")) == 64,
        "two_pack_scope_certified": (
            exact_profile and isinstance(mods, list) and len(mods) == 2 and exact_probe_record
        )
        or deferred_binding_valid,
        "shadow_probe_hash_matches": exact_probe_record or deferred_binding_valid,
        "sfo_pack_present": sfo_record_count == 1,
        "owner_settings_recorded": all(
            key in settings
            for key in (
                "campaign_difficulty",
                "battle_difficulty",
                "ironman",
                "battle_realism",
                "battlefield_limitations",
                "faction",
            )
        ),
    }
    checkpoint = verify_checkpoint_chain(
        log_path=log_path,
        checkpoint_manifest_path=checkpoint_manifest_path,
        expected_handshake_token=expected_handshake_token,
    )
    transitions = transition_analysis(log_path)
    transition_checks = {
        "campaign_started_before_battle": transitions["first_campaign_before_first_battle"],
        "minimum_battle_runtime_count": transitions["battle_runtime_begin"] >= minimum_completed_battles,
        "minimum_battle_complete_count": transitions["battle_complete"] >= minimum_completed_battles,
        "campaign_return_after_every_battle": transitions["all_battles_returned_to_campaign"],
        "minimum_turn_snapshots": transitions["campaign_turn_end_snapshots"] >= minimum_turns,
    }
    status = (
        "OBSERVED_SFO_COMBINED_CONTINUITY"
        if combined.get("status") == "OBSERVED"
        and all(environment_checks.values())
        and checkpoint.get("status") == "OBSERVED"
        and all(transition_checks.values())
        else "UNVERIFIED"
    )
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "evidence_label": "OBSERVED" if status.startswith("OBSERVED") else "UNVERIFIED",
        "combined_gate": combined,
        "environment_checks": environment_checks,
        "checkpoint_verification": checkpoint,
        "transition_checks": transition_checks,
        "transition_summary": transitions,
        "profile_summary": {
            "profile_id": environment.get("profile_id"),
            "probe_binding": probe_binding,
            "expected_probe": expected_probe,
            "runtime_probe_confirmed": runtime_probe_confirmed,
            "game_executable_sha256": game.get("executable_sha256"),
            "sfo_workshop_id": sfo.get("workshop_id"),
            "sfo_pack_name": sfo.get("pack_name"),
            "sfo_pack_sha256": sfo.get("pack_sha256"),
            "sfo_manifest_id": sfo.get("manifest_id"),
            "sfo_time_updated_unix": sfo.get("time_updated_unix"),
            "active_mods": mods,
            "settings": settings,
        },
        "authority": {
            "campaign_orders_emitted": False,
            "battle_orders_emitted": False,
            "save_values_written": False,
            "active_mod_list_modified_by_collector": False,
        },
        "inputs": {
            "log_sha256": sha256(log_path),
            "environment_profile_sha256": sha256(environment_profile_path),
            "checkpoint_manifest_sha256": sha256(checkpoint_manifest_path),
        },
        "warnings": [
            "This result certifies one exact owner-machine SFO-only plus read-only-probe session.",
            (
                "The local probe entry was absent from the prelaunch launcher-state file and was certified only by the exact prepared-pack hash plus observed runtime markers."
                if deferred_profile
                else "The prelaunch launcher-state file directly bound the active probe entry."
            ),
            "It does not generalize to later SFO or WH3 updates, the owner's full mod stack, other factions, or unobserved battle types.",
            "Campaign and battle observations do not establish order authority, acknowledgement, execution, or tactical superiority.",
        ],
    }
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify one exact SFO campaign+battle continuity session.")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--campaign-summary", type=Path, required=True)
    parser.add_argument("--battle-summary", type=Path, required=True)
    parser.add_argument("--evidence-manifest", type=Path, required=True)
    parser.add_argument("--campaign-report", type=Path, required=True)
    parser.add_argument("--battle-report", type=Path, required=True)
    parser.add_argument("--environment-profile", type=Path, required=True)
    parser.add_argument("--checkpoint-manifest", type=Path, required=True)
    parser.add_argument("--expected-pack-sha256", required=True)
    parser.add_argument("--expected-handshake-token")
    parser.add_argument("--minimum-turns", type=int, default=5)
    parser.add_argument("--minimum-completed-battles", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_sfo_combined_verification(
        log_path=args.log,
        campaign_summary_path=args.campaign_summary,
        battle_summary_path=args.battle_summary,
        evidence_manifest_path=args.evidence_manifest,
        campaign_report_path=args.campaign_report,
        battle_report_path=args.battle_report,
        environment_profile_path=args.environment_profile,
        checkpoint_manifest_path=args.checkpoint_manifest,
        expected_pack_sha256=args.expected_pack_sha256,
        minimum_turns=args.minimum_turns,
        minimum_completed_battles=args.minimum_completed_battles,
        expected_handshake_token=args.expected_handshake_token,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"].startswith("OBSERVED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
