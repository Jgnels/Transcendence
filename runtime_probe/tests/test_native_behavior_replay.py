from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))

from native_behavior_replay import (
    NativeBehaviorReplayError,
    compare_replays,
    replay_capture,
    write_comparison_outputs,
    write_replay_outputs,
)

VANILLA_CONTRACT = "NATIVE_CAI_DIAGNOSTIC_BEHAVIOR_STUDY_PUBLIC_EXPORT_V1"
SFO_CONTRACT = "NATIVE_CAI_DIAGNOSTIC_SFO_BEHAVIOR_BENCHMARK_PUBLIC_EXPORT_V1"


def scalar(value):
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)


def emit(event: str, **fields) -> str:
    return "TRANS_DIAG|1|" + event + "|" + "|".join(f"{key}={scalar(value)}" for key, value in fields.items())


def force_fields(turn: int, phase: str, faction: str, force_cqi: int, x: float, *, general_cqi: int = 100,
                 region: str = "r", health: float = 100.0, strength: float = 1000.0, units: int = 20):
    return dict(
        turn=turn,
        phase=phase,
        faction=faction,
        index=0,
        force_cqi=force_cqi,
        general_cqi=general_cqi,
        subtype="general",
        character_type_key="general",
        unit_count=units,
        force_strength=strength,
        average_unit_health_pct=health,
        action_points_remaining_pct=100,
        stance="MILITARY_FORCE_ACTIVE_STANCE_TYPE_DEFAULT",
        x=x,
        y=0,
        region=region,
    )


def snapshot_lines(turn: int, faction: str, phase: str, *, force_cqi: int, x: float, general_cqi: int = 100,
                   territorial: bool = True, duplicate_force: bool = False):
    lines = [emit("AI_SNAPSHOT_BEGIN", turn=turn, faction=faction, phase=phase)]
    ff = force_fields(turn, phase, faction, force_cqi, x, general_cqi=general_cqi, region=("r" if territorial else "none"))
    lines.append(emit("AI_FORCE", **ff))
    if duplicate_force:
        lines.append(emit("AI_FORCE", **ff))
    region_count = 1 if territorial else 0
    if territorial:
        lines.append(emit("AI_REGION", turn=turn, phase=phase, faction=faction, index=0, region="home", x=0, y=0))
    lines.append(emit(
        "AI_SNAPSHOT_END",
        turn=turn,
        faction=faction,
        phase=phase,
        forces_emitted=(2 if duplicate_force else 1),
        regions_emitted=region_count,
        wars_emitted=0,
    ))
    return lines


def build_log(
    positions=(0.0, 10.0, 0.0),
    *,
    faction="ai",
    force_cqi=1,
    territorial=True,
    battle_declared=True,
    include_battle=False,
    partial_turn=None,
    incomplete_battle=False,
    unknown_event=False,
    duplicate_force=False,
    general_by_turn=None,
):
    lines = [
        emit("RUNTIME_BEGIN", runtime="campaign"),
        emit(
            "PACK_LOADED",
            probe_kind="native_diagnostic",
            read_only=True,
            research_visibility="PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
            application_eligible=False,
            authority="NO_ORDERS",
            application_authority="PROHIBITED",
            battle_participant_telemetry=battle_declared,
        ),
    ]
    if unknown_event:
        lines.append(emit("AI_FUTURE_EVENT", version=2))
    for turn, x in enumerate(positions, 1):
        lines.append(emit("HUMAN_TURN_MARKER", turn=turn, phase="TURN_START"))
        general = 100 if general_by_turn is None else general_by_turn[turn - 1]
        lines.extend(snapshot_lines(
            turn, faction, "TURN_START", force_cqi=force_cqi, x=x, general_cqi=general,
            territorial=territorial, duplicate_force=duplicate_force,
        ))
        if turn == 2 and (incomplete_battle or include_battle):
            lines.append(emit("AI_BATTLE_BEGIN", battle_sequence=1, turn=turn))
            lines.append(emit(
                "AI_BATTLE_PARTICIPANT", battle_sequence=1, turn=turn, index=0,
                char_cqi=general, force_cqi=force_cqi, faction=faction, side="ATTACKER",
            ))
            if not incomplete_battle:
                lines.append(emit("AI_BATTLE_END", battle_sequence=1, turn=turn, attackers_emitted=1, defenders_emitted=0))
        if partial_turn == turn:
            continue
        lines.extend(snapshot_lines(
            turn, faction, "TURN_END", force_cqi=force_cqi, x=x, general_cqi=general,
            territorial=territorial, duplicate_force=duplicate_force,
        ))
    return ("\n".join(lines) + "\n").encode()


def authority_object(contract: str, **extra):
    return {
        "contract": contract,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
        **extra,
    }


def make_capture(
    path: Path,
    *,
    contract=VANILLA_CONTRACT,
    log_blob=None,
    tamper_payload=False,
    duplicate_zip_member=False,
):
    if log_blob is None:
        log_blob = build_log()
    if contract == VANILLA_CONTRACT:
        binding_name = "native_behavior_study_profile_binding.json"
        verify_name = "native_behavior_study_verification.json"
        binding = authority_object("NATIVE_CAI_DIAGNOSTIC_PROFILE_BINDING_V1", profile="VANILLA_TEST")
        verification = authority_object("NATIVE_CAI_DIAGNOSTIC_BEHAVIOR_STUDY_VERIFICATION_V1")
    elif contract == SFO_CONTRACT:
        binding_name = "native_sfo_behavior_profile_binding.json"
        verify_name = "native_sfo_behavior_benchmark_verification.json"
        binding = authority_object("NATIVE_CAI_DIAGNOSTIC_SFO_PROFILE_BINDING_V1", profile="SFO_TEST")
        verification = authority_object("NATIVE_CAI_DIAGNOSTIC_SFO_BEHAVIOR_BENCHMARK_VERIFICATION_V1")
    else:
        binding_name = "native_diagnostic_profile_binding.json"
        verify_name = "native_diagnostic_capture_verification.json"
        binding = authority_object("NATIVE_CAI_DIAGNOSTIC_PROFILE_BINDING_V1", profile="GENERIC_TEST")
        verification = authority_object("NATIVE_CAI_DIAGNOSTIC_CAPTURE_VERIFICATION_V1")

    files = {
        binding_name: (json.dumps(binding, indent=2, sort_keys=True) + "\n").encode(),
        verify_name: (json.dumps(verification, indent=2, sort_keys=True) + "\n").encode(),
        "native_diagnostic_summary.json": b"{}\n",
        "transcendence_native_diagnostic_log.txt": log_blob,
    }
    if contract == SFO_CONTRACT:
        files["vanilla_reference.json"] = (
            REPO_ROOT / "research/runtime_evidence/NATIVE_BEHAVIOR_STUDY_VANILLA_REFERENCE_v0.2O_2026-08-03.json"
        ).read_bytes()
    manifest = authority_object(
        contract,
        confirmatory_eligible=True,
        contains_private_machine_paths=False,
        files=[
            {"name": name, "size_bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
            for name, blob in sorted(files.items())
        ],
    )
    manifest_blob = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("export_manifest.json", manifest_blob)
        for name, blob in sorted(files.items()):
            archive.writestr(name, blob)
        if duplicate_zip_member:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr("native_diagnostic_summary.json", b"{}\n")
    if tamper_payload:
        # Rebuild with one changed payload while preserving the original manifest.
        with zipfile.ZipFile(path) as archive:
            members = {info.filename: archive.read(info) for info in archive.infolist()}
        members["transcendence_native_diagnostic_log.txt"] += b"#tampered\n"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, blob in members.items():
                archive.writestr(name, blob)
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NativeBehaviorReplayLabTests(unittest.TestCase):
    def test_manifest_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, tamper_payload=True)
            with self.assertRaisesRegex(NativeBehaviorReplayError, "manifest (SHA-256|size) mismatch"):
                replay_capture(path)

    def test_external_capture_sha_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path)
            with self.assertRaisesRegex(NativeBehaviorReplayError, "capture SHA-256 mismatch"):
                replay_capture(path, expected_sha256="0" * 64)

    def test_duplicate_zip_member_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, duplicate_zip_member=True)
            with self.assertRaisesRegex(NativeBehaviorReplayError, "duplicate ZIP members"):
                replay_capture(path)

    def test_unknown_future_event_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(unknown_event=True))
            with self.assertRaisesRegex(NativeBehaviorReplayError, "unknown future diagnostic event"):
                replay_capture(path)

    def test_missing_battle_telemetry_never_becomes_no_battle_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(battle_declared=False))
            out = replay_capture(path)
            self.assertFalse(out["telemetry_completeness"]["frozen_metric_replay_eligible"])
            self.assertIn("DO_NOT_INFER_NO_BATTLE", out["telemetry_completeness"]["battle_absence_interpretation"])
            self.assertIsNone(out["frozen_metric_replay"])

    def test_partial_turn_is_preserved_as_incomplete_not_silently_dropped(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(partial_turn=2))
            out = replay_capture(path)
            self.assertEqual(out["telemetry_completeness"]["incomplete_ai_faction_turn_count"], 1)
            self.assertFalse(out["telemetry_completeness"]["frozen_metric_replay_eligible"])

    def test_incomplete_battle_sequence_blocks_frozen_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(incomplete_battle=True))
            out = replay_capture(path)
            self.assertEqual(out["telemetry_completeness"]["incomplete_battle_sequence_count"], 1)
            self.assertIn("INCOMPLETE_BATTLE_SEQUENCE", out["telemetry_completeness"]["battle_absence_interpretation"])
            self.assertIsNone(out["frozen_metric_replay"])

    def test_duplicate_force_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(duplicate_force=True))
            with self.assertRaisesRegex(NativeBehaviorReplayError, "duplicate force_cqi"):
                replay_capture(path)

    def test_destroyed_recreated_cqi_identity_change_is_flagged(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(general_by_turn=(100, 200, 200)))
            out = replay_capture(path)
            flags = out["exploratory_diagnostics"]["force_cqi_identity_discontinuities"]
            self.assertEqual(len(flags), 1)
            self.assertEqual(flags[0]["classification"], "FORCE_CQI_CONSECUTIVE_IDENTITY_CHANGE")

    def test_stationary_army_is_represented_without_directional_window(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(positions=(0.0, 0.0, 0.0)))
            out = replay_capture(path)
            self.assertEqual(out["exploratory_diagnostics"]["movement_distance_distribution"]["stationary_force_turn_count"], 3)
            self.assertEqual(
                out["frozen_metric_replay"]["base_v0_2n_behavior_result"]["metrics"]["eligible_battle_free_stable_context_directional_windows"],
                0,
            )

    def test_roaming_faction_is_nonterritorial(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(territorial=False))
            out = replay_capture(path)
            self.assertTrue(all(not row["territorial"] for row in out["timeline"]))
            strat = out["frozen_metric_replay"]["temporal_stratification"]
            self.assertGreaterEqual(strat["nonterritorial"]["eligible_windows"], 1)
            self.assertEqual(strat["territorial"]["eligible_windows"], 0)

    def test_overlapping_reversal_windows_do_not_become_repeated_signal(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(positions=(0.0, 10.0, 0.0, 10.0)))
            out = replay_capture(path)
            base = out["frozen_metric_replay"]["base_v0_2n_behavior_result"]
            self.assertEqual(base["metrics"]["heading_reversal_candidate_count"], 2)
            self.assertEqual(base["metrics"]["repeated_reversal_force_count"], 0)

    def test_one_faction_candidate_concentration_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(positions=(0.0, 10.0, 0.0, 10.0, 0.0)))
            out = replay_capture(path)
            concentration = out["frozen_metric_replay"]["territorial_cluster_diagnostics"]["candidate_concentration"]
            self.assertEqual(concentration["candidate_bearing_faction_count"], 1)
            self.assertEqual(concentration["max_faction_candidate_share"], 1.0)

    def test_insufficient_denominator_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(positions=(0.0, 10.0, 0.0, 10.0)))
            out = replay_capture(path)
            territorial = out["frozen_metric_replay"]["temporal_stratification"]["territorial"]
            self.assertFalse(territorial["exposure_sufficient_for_primary_interpretation"])

    def test_disappearing_faction_does_not_create_synthetic_future_rows(self):
        # A three-turn capture can legitimately contain only the observed faction-turn rows.
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture.zip"
            make_capture(path, log_blob=build_log(positions=(0.0, 10.0)))
            out = replay_capture(path)
            observed_turns = {row["turn"] for row in out["timeline"]}
            self.assertEqual(observed_turns, {1, 2})

    def test_replay_output_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "capture.zip"
            make_capture(path)
            out = replay_capture(path)
            first, second = root / "a", root / "b"
            h1 = write_replay_outputs(out, first)
            h2 = write_replay_outputs(out, second)
            self.assertEqual(h1, h2)
            for name in h1:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

    def test_vanilla_sfo_comparison_separates_preregistered_causal_and_exploratory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vanilla_path, sfo_path = root / "vanilla.zip", root / "sfo.zip"
            make_capture(vanilla_path, contract=VANILLA_CONTRACT, log_blob=build_log(positions=(0, 10, 0, 10, 0)))
            make_capture(sfo_path, contract=SFO_CONTRACT, log_blob=build_log(positions=(0, 10, 0, 10, 0)))
            vanilla = replay_capture(vanilla_path)
            sfo = replay_capture(sfo_path)
            comparison = compare_replays(vanilla, sfo, sfo_role="original")
            self.assertEqual(comparison["preregistered_result"]["label"], "PREREGISTERED_RESULT")
            self.assertEqual(comparison["causal_review"]["label"], "CAUSAL_REVIEW")
            self.assertEqual(comparison["exploratory_result"]["label"], "EXPLORATORY")
            self.assertFalse(comparison["mechanism_nomination_eligibility"]["eligible"])
            self.assertIsNone(comparison["preregistered_result"]["stage_a_adjudication"])

    def test_stage_a_role_applies_frozen_policy_but_never_earns_ablation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vanilla_path, sfo_path = root / "vanilla.zip", root / "sfo.zip"
            positions = tuple(0.0 if turn % 2 else 10.0 for turn in range(1, 24))
            make_capture(vanilla_path, contract=VANILLA_CONTRACT, log_blob=build_log(positions=positions))
            make_capture(sfo_path, contract=SFO_CONTRACT, log_blob=build_log(positions=positions))
            comparison = compare_replays(replay_capture(vanilla_path), replay_capture(sfo_path), sfo_role="stage-a")
            stage = comparison["preregistered_result"]["stage_a_adjudication"]
            self.assertIsNotNone(stage)
            self.assertFalse(stage["native_row_ablation_earned"])
            self.assertFalse(comparison["mechanism_nomination_eligibility"]["native_row_ablation_earned"])

    def test_frozen_v02q_reference_numbers_and_policy_digest_are_unchanged(self):
        vanilla = json.loads((REPO_ROOT / "research/runtime_evidence/NATIVE_BEHAVIOR_STUDY_VANILLA_REFERENCE_v0.2O_2026-08-03.json").read_text(encoding="utf-8"))
        sfo = json.loads((REPO_ROOT / "research/runtime_evidence/NATIVE_SFO_BEHAVIOR_BENCHMARK_OWNER_RESULT_v0.2Q_2026-08-04.json").read_text(encoding="utf-8"))
        policy = json.loads((REPO_ROOT / "research/native_cai/NATIVE_SFO_REPLICATION_DECISION_POLICY_v0.2Q_2026-08-04.json").read_text(encoding="utf-8"))
        self.assertEqual(vanilla["recovery"]["recovering_army_turn_count"], 38)
        self.assertEqual(vanilla["recovery"]["recovering_attacker_side_army_turn_count"], 6)
        self.assertEqual(vanilla["recovery"]["recovering_attacker_side_rate"], 0.157895)
        self.assertEqual(vanilla["temporal_stratification"]["territorial"]["eligible_windows"], 48)
        self.assertEqual(vanilla["temporal_stratification"]["territorial"]["reversal_candidates"], 13)
        self.assertEqual(vanilla["temporal_stratification"]["territorial"]["reversal_candidate_rate"], 0.270833)
        comparison = sfo["comparison_to_hash_frozen_vanilla_reference"]
        self.assertEqual(comparison["recovery_attacker_side_rate_sfo"], 0.142857)
        self.assertEqual(comparison["territorial_eligible_windows_sfo"], 39)
        self.assertEqual(sfo["territorial_cluster_diagnostics"]["reversal_candidates"], 18)
        self.assertEqual(comparison["territorial_reversal_candidate_rate_sfo"], 0.461538)
        self.assertEqual(policy["policy_digest"], "3171982731ca16a635723f5d5a788c6ce5fb397590f82a60cabb221e26ac0120")

    def test_game_side_lua_probes_remain_byte_identical_to_sealed_v02q(self):
        diagnostic = REPO_ROOT / "runtime_probe/source/script/campaign/mod/transcendence_native_diagnostic_probe.lua"
        shadow = REPO_ROOT / "runtime_probe/source/script/campaign/mod/transcendence_shadow_probe.lua"
        self.assertEqual(hashlib.sha256(diagnostic.read_bytes()).hexdigest(), "0acb4e186a4f4077801a763dbbf5cacc8ae21a9d47ecc76d54fefe5c023ec203")
        self.assertEqual(hashlib.sha256(shadow.read_bytes()).hexdigest(), "4f8c80fb67efe288e4b7b4eeacc0c48578707a0e554f2dd8a454aa669b50ed98")

    def test_comparison_output_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vanilla_path, sfo_path = root / "vanilla.zip", root / "sfo.zip"
            make_capture(vanilla_path, contract=VANILLA_CONTRACT)
            make_capture(sfo_path, contract=SFO_CONTRACT)
            comparison = compare_replays(replay_capture(vanilla_path), replay_capture(sfo_path))
            a, b = root / "a", root / "b"
            self.assertEqual(write_comparison_outputs(comparison, a), write_comparison_outputs(comparison, b))
            self.assertEqual((a / "comparison.json").read_bytes(), (b / "comparison.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
