from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = REPO_ROOT / "runtime_probe"
sys.path.insert(0, str(RUNTIME_ROOT / "tools"))
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))

from build_probe_packs import ProbeBuildError, build_all, normalize_internal_path, write_pfh5_pack
from parse_probe_log import ALLOWED_EVENTS, ProbeLogError, parse_logs, summarize
from verify_observer_runs import build_replication_report
from verify_persistence_roundtrip import build_persistence_report
from run_shadow_assignment import ShadowPipelineError, build_shadow_scenario, run_shadow_pipeline
from run_shadow_campaign import run_shadow_campaign
from verify_shadow_campaign import build_campaign_shadow_verification
from parse_battle_log import BattleLogError, parse_battle_logs, summarize_battle
from parse_action_authority_log import (
    ActionAuthorityLogError,
    parse_action_logs,
    summarize_action_events,
)
from verify_action_authority_capture import (
    ActionAuthorityVerificationError,
    build_action_authority_verification,
)
from adjudicate_action_authority_export import (
    EXPECTED_PACK_SHA256 as ACTION_AUTHORITY_EXPECTED_PACK_SHA256,
    ActionAuthorityExportError,
    adjudicate_action_authority_documents,
    adjudicate_action_authority_zip,
)
from export_action_feasibility_windows import (
    ActionFeasibilityExportError,
    build_action_feasibility_window_export,
)
from adjudicate_action_feasibility_semantics import (
    ActionFeasibilitySemanticError,
    adjudicate_action_feasibility_documents,
)
from verify_action_feasibility_reexport import (
    ActionFeasibilityVerificationError,
    verify_action_feasibility_reexport_zip,
)
from run_battle_report import build_battle_report
from verify_campaign_battle_gate import build_campaign_battle_verification
from capture_sfo_environment import (
    build_environment_manifests,
    classify_probe_entry,
    discover_used_mods_path,
    parse_used_mods,
    parse_vdf,
)
from watch_combined_runtime_log import (
    marker_summary,
    run_watcher,
    take_checkpoint,
    write_json as write_control_json,
)
from build_sfo_combined_preparation_artifact import build_artifact
from verify_sfo_combined_session import (
    build_sfo_combined_verification,
    transition_analysis,
    verify_checkpoint_chain,
)
from adjudicate_recovery_inventory import adjudicate_inventory
from adjudicate_sfo_observed_baseline import (
    SfoObservedBaselineError,
    build_capability_matrix as build_sfo_observed_capability_matrix,
    validate_sfo_observed_baseline,
)
from build_public_evidence_zip import (
    PublicEvidenceZipError,
    build_deterministic_zip as build_public_evidence_zip,
)
import capture_sfo_replay_deep_dive as replay_capture
from capture_sfo_replay_deep_dive import (
    classify_battle_observer_entry,
    classify_replay_probe_entry,
    deterministic_zip as build_private_replay_zip,
    validate_sfo_replay_mod_state,
)
from verify_battle4_dense_replay import (
    EXPECTED_REPLAY_SHA256,
    build_dense_replay_verification,
)
from build_battle_corpus import build_corpus
from reprocess_battle4_dense_capture import reprocess_capture
from transcendence_lab.mod_audit import parse_pfh5_index
from transcendence_lab.observed_battle import validate_observed_battle_corpus, derive_reality_regressions
from watch_campaign_feasibility import derive_current_plan, _request_text
from build_campaign_feasibility_live_artifact import CampaignFeasibilityLiveError, build_live_artifacts
from build_embedded_campaign_feasibility_probe import EmbeddedProbeBuildError, build_embedded_probe
from run_native_visible_behavior import (
    NativeVisiblePipelineError,
    build_player_visible_native_trace,
    run_player_visible_native_behavior,
)
from reprocess_native_visible_behavior_evidence import build_reprocess as build_native_visible_reprocess
from run_native_visible_churn import (
    discover_observed_ai_factions,
    run_native_visible_churn_batch,
)
from reprocess_native_visible_churn_evidence import build_reprocess as build_native_visible_churn_reprocess
from verify_native_churn_profile import (
    NativeChurnProfileError,
    build_profile_binding as build_native_churn_profile_binding,
)
from verify_native_churn_capture import (
    NativeChurnCaptureError,
    verify_capture as verify_native_churn_capture,
)
from compare_native_churn_captures import (
    NativeChurnComparisonError,
    build_comparison as build_native_churn_comparison,
)
from prepare_native_churn_capture import (
    prepare_session as prepare_native_churn_session,
    resolve_game_root as resolve_native_churn_game_root,
)
from collect_native_churn_capture import collect_session as collect_native_churn_session
from build_native_churn_owner_kit import build_owner_kit as build_native_churn_owner_kit


def _make_native_churn_fake_environment(root: Path, profile: str) -> dict[str, Path]:
    steamapps = root / "steamapps"
    game_root = steamapps / "common" / "Total War WARHAMMER III"
    appdata_root = root / "AppData" / "Roaming"
    data_root = game_root / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    appdata_root.mkdir(parents=True, exist_ok=True)
    exe = game_root / "Warhammer3.exe"
    exe.write_bytes(b"fake-wh3-executable-v02l")
    probe = data_root / "transcendence_shadow_probe.pack"
    probe.write_bytes(b"fake-read-only-shadow-probe-v02l")
    entries = [probe.name]
    sfo_pack = root / "missing_sfo.pack"
    if profile.upper() == "SFO":
        sfo_pack = steamapps / "workshop" / "content" / "1142710" / "2792731173" / "sfo_grimhammer_3.pack"
        sfo_pack.parent.mkdir(parents=True, exist_ok=True)
        sfo_pack.write_bytes(b"fake-sfo-v02l")
        entries.insert(0, sfo_pack.name)
    used_mods = game_root / "used_mods.txt"
    used_mods.write_text("".join(f'mod "{name}";\n' for name in entries), encoding="utf-8")
    return {
        "steamapps": steamapps,
        "game_root": game_root,
        "appdata_root": appdata_root,
        "exe": exe,
        "probe": probe,
        "sfo_pack": sfo_pack,
        "used_mods": used_mods,
    }


def _write_native_churn_binding_and_evidence(
    root: Path,
    env: dict[str, Path],
    public: dict,
    private: dict,
) -> tuple[Path, Path, Path]:
    public_path = root / "profile_binding_public.json"
    private_path = root / "profile_binding_private.json"
    public_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    private_path.write_text(json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    used_copy = root / "used_mods_private.txt"
    shutil.copy2(env["used_mods"], used_copy)
    probe_sha = hashlib.sha256(env["probe"].read_bytes()).hexdigest()
    evidence = {
        "schema_version": 1,
        "evidence_phase": "campaign_shadow",
        "loaded_probe_kinds": ["shadow"],
        "unexpected_loaded_probe_kinds": [],
        "installed_probe_packs": [
            {
                "name": "transcendence_shadow_probe.pack",
                "installed_sha256": probe_sha,
                "staged_sha256": probe_sha,
                "matches_staged": True,
                "loaded_in_log": True,
            }
        ],
        "used_mods": {
            "private_copy": str(used_copy),
            "sha256": hashlib.sha256(used_copy.read_bytes()).hexdigest(),
        },
    }
    evidence_path = root / "evidence_manifest_private.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return public_path, private_path, evidence_path


class RuntimeProbeTests(unittest.TestCase):
    def test_repository_validator_ignores_only_repository_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp) / "tmp" / "Transcendence"
            tools = checkout / "tools"
            tools.mkdir(parents=True)
            validator_source = REPO_ROOT / "tools" / "validate_repository.py"
            validator_copy = tools / "validate_repository.py"
            shutil.copy2(validator_source, validator_copy)
            tracked = checkout / "tracked.txt"
            tracked.write_text("tracked", encoding="utf-8")
            ignored = checkout / "dist" / "ignored.txt"
            ignored.parent.mkdir()
            ignored.write_text("ignored", encoding="utf-8")

            spec = importlib.util.spec_from_file_location(
                "transcendence_validator_under_tmp", validator_copy
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            relative = {
                path.relative_to(checkout).as_posix()
                for path in module.tracked_files()
            }
            self.assertIn("tracked.txt", relative)
            self.assertIn("tools/validate_repository.py", relative)
            self.assertNotIn("dist/ignored.txt", relative)

    def test_internal_path_rejects_traversal(self) -> None:
        with self.assertRaises(ProbeBuildError):
            normalize_internal_path("script/campaign/../secret")

    def test_probe_pack_build_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = build_all(REPO_ROOT, Path(first_dir))
            second = build_all(REPO_ROOT, Path(second_dir))
            self.assertEqual(first["result_digest"], second["result_digest"])
            for pack in first["packs"]:
                first_blob = (Path(first_dir) / pack["pack_name"]).read_bytes()
                second_blob = (Path(second_dir) / pack["pack_name"]).read_bytes()
                self.assertEqual(first_blob, second_blob)

    def test_probe_packs_are_valid_uncompressed_pfh5_mod_packs(self) -> None:
        with tempfile.TemporaryDirectory() as output:
            result = build_all(REPO_ROOT, Path(output))
            self.assertEqual(len(result["packs"]), 7)
            diagnostic = next(record for record in result["packs"] if record["probe_kind"] == "native_diagnostic")
            self.assertFalse(diagnostic["save_mutation"])
            self.assertFalse(diagnostic["gameplay_mutation"])
            for record in result["packs"]:
                parsed = parse_pfh5_index(Path(output) / record["pack_name"])
                self.assertEqual(parsed["pack_type"], 3)
                self.assertEqual(parsed["dependency_count"], 0)
                self.assertEqual(parsed["timestamp_raw"], 0)
                expected_count = 2 if record["probe_kind"] == "shadow" else 1
                self.assertEqual(parsed["file_count"], expected_count)
                paths = {entry["path"] for entry in parsed["entries"]}
                if record["probe_kind"] == "battle_replay":
                    self.assertEqual(paths, {"script/battle/mod/transcendence_battle_probe.lua"})
                elif record["probe_kind"] == "action_authority":
                    self.assertEqual(
                        paths,
                        {"script/battle/mod/transcendence_action_authority_probe.lua"},
                    )
                else:
                    self.assertIn(
                        f"script/campaign/mod/transcendence_{record['probe_kind']}_probe.lua",
                        paths,
                    )
                    if record["probe_kind"] == "shadow":
                        self.assertIn(
                            "script/battle/mod/transcendence_battle_probe.lua",
                            paths,
                        )

    def test_observer_probe_contains_no_campaign_mutation_calls(self) -> None:
        source = (RUNTIME_ROOT / "source/script/campaign/mod/transcendence_observer_probe.lua").read_text(encoding="utf-8")
        prohibited = (
            "cm:set_saved_value",
            "cm:save_named_value",
            "cm:treasury_mod",
            "cm:create_force",
            "cm:transfer_region_to_faction",
            "cm:force_declare_war",
            "cm:force_make_peace",
            "cm:force_alliance",
            "cm:force_confederation",
            "cm:apply_effect_bundle",
            "CampaignUI.TriggerCampaignScriptEvent",
            "cm:random_number",
            "math.random",
        )
        for token in prohibited:
            self.assertNotIn(token, source)
        self.assertIn("get_foreign_visible_characters_for_player", source)
        self.assertIn("get_foreign_visible_regions_for_player", source)

    def test_persistence_probe_mutation_is_narrow(self) -> None:
        source = (RUNTIME_ROOT / "source/script/campaign/mod/transcendence_persistence_probe.lua").read_text(encoding="utf-8")
        self.assertEqual(source.count("cm:set_saved_value"), 1)
        self.assertEqual(source.count("cm:get_saved_value"), 1)
        for token in (
            "cm:treasury_mod",
            "cm:create_force",
            "cm:transfer_region_to_faction",
            "cm:force_declare_war",
            "cm:apply_effect_bundle",
            "cm:random_number",
            "math.random",
        ):
            self.assertNotIn(token, source)

    def test_valid_observer_log_promotes_observation_capabilities(self) -> None:
        events = parse_logs([RUNTIME_ROOT / "fixtures/observer_log_valid.txt"])
        result = summarize(events)
        promotions = result["capability_promotions"]
        self.assertEqual(promotions["campaign_mod_pack_loaded"], "OBSERVED")
        self.assertEqual(promotions["campaign_first_tick_callback"], "OBSERVED")
        self.assertEqual(promotions["local_army_observation"], "OBSERVED")
        self.assertEqual(promotions["local_region_observation"], "OBSERVED")
        self.assertEqual(promotions["visibility_filtered_foreign_characters"], "OBSERVED")
        self.assertEqual(promotions["visibility_filtered_foreign_regions"], "OBSERVED")
        self.assertEqual(promotions["save_reload_saved_value_roundtrip"], "UNVERIFIED")

    def test_valid_persistence_log_promotes_roundtrip(self) -> None:
        events = parse_logs([RUNTIME_ROOT / "fixtures/persistence_log_roundtrip.txt"])
        result = summarize(events)
        self.assertEqual(result["capability_promotions"]["save_reload_saved_value_roundtrip"], "REPLICATED")

    def test_repeated_records_across_snapshots_are_not_duplicates(self) -> None:
        events = parse_logs([RUNTIME_ROOT / "fixtures/observer_log_lifecycle_valid.txt"])
        result = summarize(events)
        session = result["sessions"][0]
        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(session["duplicate_event_count"], 0)
        self.assertEqual(session["repeated_across_snapshot_count"], 2)
        self.assertEqual(session["snapshot_count"], 2)
        self.assertEqual(result["canonical_planner_snapshot_reason"], "LOCAL_FACTION_TURN_START")
        self.assertTrue(result["lifecycle_deltas"][0]["different"])
        self.assertEqual(
            result["capability_promotions"]["campaign_local_faction_turn_start_snapshot"],
            "OBSERVED",
        )

    def test_probe_scripts_define_loader_entrypoints(self) -> None:
        observer = (RUNTIME_ROOT / "source/script/campaign/mod/transcendence_observer_probe.lua").read_text(encoding="utf-8")
        persistence = (RUNTIME_ROOT / "source/script/campaign/mod/transcendence_persistence_probe.lua").read_text(encoding="utf-8")
        shadow = (RUNTIME_ROOT / "source/script/campaign/mod/transcendence_shadow_probe.lua").read_text(encoding="utf-8")
        battle = (RUNTIME_ROOT / "source/script/battle/mod/transcendence_battle_probe.lua").read_text(encoding="utf-8")
        self.assertIn("function transcendence_observer_probe()", observer)
        self.assertIn("function transcendence_persistence_probe()", persistence)
        self.assertIn("function transcendence_shadow_probe()", shadow)
        self.assertIn("function transcendence_battle_probe()", battle)

    def test_semantic_digest_ignores_filename_and_non_probe_line_offsets(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/observer_log_lifecycle_valid.txt").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first_name.txt"
            second = Path(temp) / "renamed_copy.txt"
            first.write_text(source, encoding="utf-8")
            second.write_text(
                "unrelated loader text\nsecond unrelated line\n" + source,
                encoding="utf-8",
            )
            first_summary = summarize(parse_logs([first]))
            second_summary = summarize(parse_logs([second]))
            self.assertNotEqual(first_summary["result_digest"], second_summary["result_digest"])
            self.assertEqual(first_summary["semantic_digest"], second_summary["semantic_digest"])

    def test_observer_replication_requires_exact_pack_identity(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/observer_log_lifecycle_valid.txt").read_text(encoding="utf-8")
        success = (
            "Executing mod function transcendence_observer_probe()\n"
            "transcendence_observer_probe() executed successfully\n"
        )
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "run_a.txt"
            second = Path(temp) / "run_b.txt"
            first.write_text(success + source, encoding="utf-8")
            second.write_text("noise\n" + success + source, encoding="utf-8")
            report = build_replication_report(
                [first, second],
                collection_ids=["collection-a", "collection-b"],
            )
            self.assertEqual(report["status"], "SUPPORTED_CROSS_REVISION")
            self.assertFalse(report["checks"]["exact_pack_verified"])

    def test_observer_replication_passes_for_same_verified_pack(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/observer_log_lifecycle_valid.txt").read_text(encoding="utf-8")
        success = (
            "Executing mod function transcendence_observer_probe()\n"
            "transcendence_observer_probe() executed successfully\n"
        )
        expected = "a" * 64
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "run_a.txt"
            second = Path(temp) / "run_b.txt"
            first.write_text(success + source, encoding="utf-8")
            second.write_text("noise\n" + success + source, encoding="utf-8")
            report = build_replication_report(
                [first, second],
                pack_sha256s=[expected, expected],
                expected_pack_sha256=expected,
                collection_ids=["collection-a", "collection-b"],
            )
            self.assertEqual(report["status"], "REPLICATED")
            self.assertTrue(report["checks"]["exact_pack_verified"])
            self.assertTrue(report["checks"]["loader_entrypoint_clean"])

    def test_private_log_field_rejected(self) -> None:
        with self.assertRaises(ProbeLogError):
            parse_logs([RUNTIME_ROOT / "fixtures/log_private_field_invalid.txt"])

    def test_out_of_order_log_rejected(self) -> None:
        events = parse_logs([RUNTIME_ROOT / "fixtures/log_out_of_order_invalid.txt"])
        with self.assertRaises(ProbeLogError):
            summarize(events)

    def test_pack_builder_rejects_duplicate_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ProbeBuildError):
                write_pfh5_pack(
                    [("script/a.lua", b"a"), ("script/a.lua", b"b")],
                    Path(temp) / "bad.pack",
                )


    def test_identical_observer_logs_from_distinct_collections_can_replicate(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/observer_log_lifecycle_valid.txt").read_text(encoding="utf-8")
        success = (
            "Executing mod function transcendence_observer_probe()\n"
            "transcendence_observer_probe() executed successfully\n"
        )
        expected = "b" * 64
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "run_a.txt"
            second = root / "run_b.txt"
            first.write_text(success + source, encoding="utf-8")
            second.write_text(success + source, encoding="utf-8")
            self.assertEqual(first.read_bytes(), second.read_bytes())

            manifests = []
            for index, log in enumerate((first, second), 1):
                manifest = root / f"manifest_{index}.json"
                manifest.write_text(
                    json.dumps(
                        {
                            "schema_version": 2,
                            "collected_at_utc": f"2026-07-29T21:0{index}:00Z",
                            "logs": [
                                {
                                    "sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                                }
                            ],
                            "installed_probe_packs": [
                                {
                                    "name": "transcendence_observer_probe.pack",
                                    "installed_sha256": expected,
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                manifests.append(manifest)

            report = build_replication_report(
                [first, second],
                expected_pack_sha256=expected,
                evidence_manifest_paths=manifests,
            )
            self.assertEqual(report["status"], "REPLICATED")
            self.assertTrue(report["checks"]["byte_identical_raw_logs"])
            self.assertTrue(report["checks"]["independent_collections_verified"])

    def test_observer_replication_rejects_reused_collection_manifest(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/observer_log_lifecycle_valid.txt").read_text(encoding="utf-8")
        success = (
            "Executing mod function transcendence_observer_probe()\n"
            "transcendence_observer_probe() executed successfully\n"
        )
        expected = "c" * 64
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "run_a.txt"
            second = root / "run_b.txt"
            first.write_text(success + source, encoding="utf-8")
            second.write_text(success + source, encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "collected_at_utc": "2026-07-29T21:01:00Z",
                        "logs": [
                            {
                                "sha256": hashlib.sha256(first.read_bytes()).hexdigest(),
                            }
                        ],
                        "installed_probe_packs": [
                            {
                                "name": "transcendence_observer_probe.pack",
                                "installed_sha256": expected,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = build_replication_report(
                [first, second],
                expected_pack_sha256=expected,
                evidence_manifest_paths=[manifest, manifest],
            )
            self.assertEqual(report["status"], "UNVERIFIED")
            self.assertFalse(report["checks"]["independent_collections_verified"])

    def test_observer_manifest_must_match_supplied_log(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/observer_log_lifecycle_valid.txt").read_text(encoding="utf-8")
        success = (
            "Executing mod function transcendence_observer_probe()\n"
            "transcendence_observer_probe() executed successfully\n"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "run_a.txt"
            second = root / "run_b.txt"
            first.write_text(success + source, encoding="utf-8")
            second.write_text(success + source, encoding="utf-8")
            bad_manifest = root / "bad_manifest.json"
            bad_manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "collected_at_utc": "2026-07-29T21:01:00Z",
                        "logs": [{"sha256": "0" * 64}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                build_replication_report(
                    [first, second],
                    evidence_manifest_paths=[bad_manifest, bad_manifest],
                )

    def test_persistence_roundtrip_verifier_accepts_exact_isolated_chain(self) -> None:
        lines = (RUNTIME_ROOT / "fixtures/persistence_log_roundtrip.txt").read_text(encoding="utf-8").splitlines()
        first_text = "\n".join(lines[:4]) + "\n"
        second_text = "\n".join(lines[4:]) + "\n"
        expected = "d" * 64

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "write.txt"
            second = root / "reload.txt"
            first.write_text(first_text, encoding="utf-8")
            second.write_text(second_text, encoding="utf-8")
            manifests = []
            for index, log in enumerate((first, second), 1):
                manifest = root / f"manifest_{index}.json"
                manifest.write_text(
                    json.dumps(
                        {
                            "schema_version": 3,
                            "collected_at_utc": f"2026-07-29T22:0{index}:00Z",
                            "logs": [
                                {
                                    "sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                                }
                            ],
                            "installed_probe_packs": [
                                {
                                    "name": "transcendence_persistence_probe.pack",
                                    "installed_sha256": expected,
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                manifests.append(manifest)

            report = build_persistence_report(
                [first, second],
                evidence_manifest_paths=manifests,
                expected_pack_sha256=expected,
            )
            self.assertEqual(report["status"], "REPLICATED")
            self.assertTrue(report["checks"]["saved_value_chain_valid"])
            self.assertTrue(report["checks"]["same_campaign_and_faction"])

    def test_persistence_roundtrip_rejects_nonfresh_write_phase(self) -> None:
        lines = (RUNTIME_ROOT / "fixtures/persistence_log_roundtrip.txt").read_text(encoding="utf-8").splitlines()
        first_text = ("\n".join(lines[:4]) + "\n").replace("is_new_game=true", "is_new_game=false")
        second_text = "\n".join(lines[4:]) + "\n"
        expected = "e" * 64

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "write.txt"
            second = root / "reload.txt"
            first.write_text(first_text, encoding="utf-8")
            second.write_text(second_text, encoding="utf-8")
            manifests = []
            for index, log in enumerate((first, second), 1):
                manifest = root / f"manifest_{index}.json"
                manifest.write_text(
                    json.dumps(
                        {
                            "schema_version": 3,
                            "collected_at_utc": f"2026-07-29T22:1{index}:00Z",
                            "logs": [
                                {
                                    "sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                                }
                            ],
                            "installed_probe_packs": [
                                {
                                    "name": "transcendence_persistence_probe.pack",
                                    "installed_sha256": expected,
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                manifests.append(manifest)

            report = build_persistence_report(
                [first, second],
                evidence_manifest_paths=manifests,
                expected_pack_sha256=expected,
            )
            self.assertEqual(report["status"], "UNVERIFIED")
            self.assertFalse(report["checks"]["write_state_valid"])


    def test_shadow_probe_contains_no_mutation_or_privileged_foreign_enumeration(self) -> None:
        source = (
            RUNTIME_ROOT
            / "source/script/campaign/mod/transcendence_shadow_probe.lua"
        ).read_text(encoding="utf-8")
        prohibited = (
            "cm:set_saved_value",
            "cm:save_named_value",
            "cm:treasury_mod",
            "cm:create_force",
            "cm:transfer_region_to_faction",
            "cm:force_declare_war",
            "cm:force_make_peace",
            "cm:force_alliance",
            "cm:force_confederation",
            "cm:apply_effect_bundle",
            "CampaignUI.TriggerCampaignScriptEvent",
            "cm:random_number",
            "math.random",
            "world():faction_list()",
            "world():region_manager():region_list()",
        )
        for token in prohibited:
            self.assertNotIn(token, source)
        self.assertIn("get_foreign_visible_characters_for_player", source)
        self.assertIn("get_foreign_visible_regions_for_player", source)
        self.assertIn("action_points_remaining_percent", source)
        self.assertIn("percentage_proportion_of_full_strength", source)
        self.assertIn("is_under_siege", source)

    def test_shadow_log_promotes_only_observed_input_capabilities(self) -> None:
        result = summarize(
            parse_logs([RUNTIME_ROOT / "fixtures/shadow_log_valid.txt"])
        )
        promotions = result["capability_promotions"]
        self.assertEqual(promotions["shadow_local_turn_snapshot"], "OBSERVED")
        self.assertEqual(
            promotions["shadow_own_army_strength_movement_health"],
            "OBSERVED",
        )
        self.assertEqual(
            promotions["shadow_war_identity_observation"],
            "OBSERVED",
        )
        self.assertEqual(
            promotions["shadow_region_structure_and_siege"],
            "OBSERVED",
        )
        self.assertEqual(
            promotions["save_reload_saved_value_roundtrip"],
            "UNVERIFIED",
        )

    def test_shadow_pipeline_is_deterministic_and_orderless(self) -> None:
        log = RUNTIME_ROOT / "fixtures/shadow_log_valid.txt"
        profile = REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json"
        first = run_shadow_pipeline([log], profile)
        second = run_shadow_pipeline([log], profile)
        self.assertEqual(first["result_digest"], second["result_digest"])
        self.assertEqual(first["mode"], "SHADOW_NO_ORDERS")
        self.assertNotIn("orders", first)
        self.assertEqual(
            first["metadata"]["provenance"]["foreign_entity_source"],
            "WH3_PLAYER_FILTERED_LISTS",
        )
        scenario = first["scenario"]
        self.assertEqual(scenario["controlled_faction"], "wh_main_emp_empire")
        self.assertEqual(len([a for a in scenario["armies"] if a["faction"] == "wh_main_emp_empire"]), 2)
        enemy = next(
            army
            for army in scenario["armies"]
            if army["faction"] == "wh_main_emp_empire_separatists"
        )
        self.assertEqual(enemy["strength"], 80.0)
        foreign_region = next(
            region
            for region in scenario["regions"]
            if region["owner"] == "wh_main_emp_empire_separatists"
        )
        self.assertEqual(
            foreign_region["observation"]["garrison_source"],
            "SETTLEMENT_STRUCTURE_PROXY",
        )
        self.assertEqual(
            first["decision"]["evidence_status"],
            "HYPOTHESIS",
        )

    def test_shadow_pipeline_rejects_noncanonical_snapshot(self) -> None:
        source = (
            RUNTIME_ROOT / "fixtures/shadow_log_valid.txt"
        ).read_text(encoding="utf-8")
        source = source.replace(
            "reason=LOCAL_FACTION_TURN_START",
            "reason=FIRST_TICK",
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad_shadow.txt"
            path.write_text(source, encoding="utf-8")
            with self.assertRaises(ShadowPipelineError):
                run_shadow_pipeline(
                    [path],
                    REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json",
                )

    def test_persistence_semantic_digest_ignores_uploaded_filenames(self) -> None:
        lines = (RUNTIME_ROOT / "fixtures/persistence_log_roundtrip.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        write_text = "\n".join(lines[:4]) + "\n"
        reload_text = "\n".join(lines[4:]) + "\n"
        expected = "f" * 64

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pair_reports = []
            for prefix in ("original", "renamed"):
                write_log = root / f"{prefix}_write.txt"
                reload_log = root / f"{prefix}_reload.txt"
                write_log.write_text(write_text, encoding="utf-8")
                reload_log.write_text(reload_text, encoding="utf-8")
                manifests = []
                for index, log in enumerate((write_log, reload_log), 1):
                    manifest = root / f"{prefix}_manifest_{index}.json"
                    manifest.write_text(
                        json.dumps(
                            {
                                "schema_version": 3,
                                "collected_at_utc": f"2026-07-29T23:0{index}:00Z",
                                "logs": [
                                    {
                                        "sha256": hashlib.sha256(
                                            log.read_bytes()
                                        ).hexdigest(),
                                    }
                                ],
                                "installed_probe_packs": [
                                    {
                                        "name": "transcendence_persistence_probe.pack",
                                        "installed_sha256": expected,
                                    }
                                ],
                            }
                        ),
                        encoding="utf-8",
                    )
                    manifests.append(manifest)
                pair_reports.append(
                    build_persistence_report(
                        [write_log, reload_log],
                        evidence_manifest_paths=manifests,
                        expected_pack_sha256=expected,
                    )
                )

            self.assertNotEqual(
                pair_reports[0]["result_digest"],
                pair_reports[1]["result_digest"],
            )
            self.assertEqual(
                pair_reports[0]["semantic_digest"],
                pair_reports[1]["semantic_digest"],
            )



    def test_shadow_scenario_coalesces_owned_visible_region_overlap(self) -> None:
        result = run_shadow_pipeline(
            [RUNTIME_ROOT / "fixtures/shadow_log_owned_visible_overlap_valid.txt"],
            REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json",
        )

        regions = result["scenario"]["regions"]
        ids = [region["id"] for region in regions]
        self.assertEqual(len(ids), len(set(ids)))
        altdorf = next(
            region
            for region in regions
            if region["id"] == "wh3_main_combi_region_altdorf"
        )
        self.assertEqual(altdorf["observation"]["record_source"], "OWN")
        self.assertEqual(
            altdorf["observation"]["garrison_source"],
            "SETTLEMENT_STRUCTURE_PROXY",
        )
        self.assertEqual(result["metadata"]["region_overlap_resolution_count"], 1)

    def test_shadow_pipeline_filters_nonfield_forces_and_aligns_strength_scale(self) -> None:
        result = run_shadow_pipeline(
            [RUNTIME_ROOT / "fixtures/shadow_log_proxy_alignment_valid.txt"],
            REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json",
        )

        controlled = [
            army
            for army in result["scenario"]["armies"]
            if army["faction"] == "wh_main_emp_empire"
        ]
        self.assertEqual([army["id"] for army in controlled], ["force:65"])
        self.assertAlmostEqual(controlled[0]["strength"], 180.0)
        self.assertEqual(
            controlled[0]["observation"]["exact_force_strength"],
            2500000.0,
        )
        enemy = next(
            army
            for army in result["scenario"]["armies"]
            if army["faction"] == "wh_main_emp_marienburg"
        )
        self.assertEqual(enemy["strength"], 180.0)
        self.assertEqual(result["metadata"]["filtered_force_count"], 1)

        altdorf = next(
            region
            for region in result["scenario"]["regions"]
            if region["id"] == "wh3_main_combi_region_altdorf"
        )
        self.assertEqual(
            altdorf["observation"]["garrison_source"],
            "SETTLEMENT_STRUCTURE_PROXY",
        )
        self.assertLess(altdorf["garrison_strength"], 100.0)
        self.assertEqual(
            result["metadata"]["field_army_garrison_exclusion_count"],
            1,
        )

        assignment = result["decision"]["assignments"][0]
        self.assertNotIn("14537", " ".join(assignment["rationale"]))
        self.assertLess(max(item["score"] for item in assignment["alternatives"] + [assignment]), 20.0)

    def test_shadow_scripts_use_append_only_cross_runtime_log(self) -> None:
        campaign = (
            RUNTIME_ROOT
            / "source/script/campaign/mod/transcendence_shadow_probe.lua"
        ).read_text(encoding="utf-8-sig")
        battle = (
            RUNTIME_ROOT
            / "source/script/battle/mod/transcendence_battle_probe.lua"
        ).read_text(encoding="utf-8-sig")
        for source in (campaign, battle):
            self.assertIn("transcendence_runtime_log.txt", source)
            self.assertIn('pcall(io.open', source)
            self.assertIn(', "a")', source)
            self.assertIn("RUNTIME_BEGIN", source)
        self.assertIn('{"runtime", "campaign"}', campaign)
        self.assertIn('{"runtime", "battle"}', battle)

    def test_collectors_prefer_combined_runtime_log(self) -> None:
        collector = (RUNTIME_ROOT / "tools/collect_probe_logs.ps1").read_text(
            encoding="utf-8-sig"
        )
        combined = (RUNTIME_ROOT / "tools/collect_campaign_battle.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("transcendence_runtime_log.txt", collector)
        self.assertIn("Combined-session manifest missing", collector)
        self.assertIn("required append-only combined runtime log", collector)
        self.assertIn("combined_session_manifest", collector)
        self.assertIn("$InitialManifest.logs", combined)
        self.assertNotIn('Join-Path $GameRoot "lua_mod_log.txt"', combined)
        self.assertIn("[int]$MinimumCompletedBattles = 2", combined)

    def test_prepare_combined_session_archives_runtime_log(self) -> None:
        source = (RUNTIME_ROOT / "tools/prepare_combined_session.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("runtime_log_archives", source)
        self.assertIn("transcendence_runtime_log.txt", source)
        self.assertIn("Remove-Item -LiteralPath $RuntimeLog", source)
        self.assertIn("expected_runtime_markers", source)

    def test_recovery_adjudication_excludes_fixtures_reexports_and_history(self) -> None:
        inventory = {
            "segments": [
                {
                    "segment": "live-current",
                    "source_filename": "lua_mod_log.txt",
                    "source_kind": "game_install",
                    "source_sha256": "a" * 64,
                    "source_last_write_utc": "2026-07-30T00:59:40Z",
                    "canonical_snapshot_turns": [4, 5, 6, 7],
                    "trans_probe_record_count": 182,
                    "trans_battle_record_count": 0,
                    "battle_complete_count": 0,
                },
                {
                    "segment": "historical",
                    "source_filename": "lua_mod_log.txt",
                    "source_kind": "project_private_logs",
                    "source_sha256": "b" * 64,
                    "source_last_write_utc": "2026-07-29T20:28:36Z",
                    "canonical_snapshot_turns": [1],
                    "trans_probe_record_count": 55,
                    "trans_battle_record_count": 0,
                    "battle_complete_count": 0,
                },
                {
                    "segment": "fixture",
                    "source_filename": "project.zip::battle_log_valid.txt",
                    "source_kind": "project_runtime_probe",
                    "source_sha256": "c" * 64,
                    "source_last_write_utc": "2026-07-30T01:00:00Z",
                    "canonical_snapshot_turns": [],
                    "trans_probe_record_count": 0,
                    "trans_battle_record_count": 36,
                    "battle_complete_count": 1,
                },
                {
                    "segment": "segment_001_lua_mod_log.txt",
                    "source_filename": "segment_001_lua_mod_log.txt",
                    "source_kind": "project_runtime_probe",
                    "source_sha256": "d" * 64,
                    "source_last_write_utc": "2026-07-30T01:25:00Z",
                    "canonical_snapshot_turns": [4, 5, 6, 7],
                    "trans_probe_record_count": 182,
                    "trans_battle_record_count": 0,
                    "battle_complete_count": 0,
                },
            ]
        }
        from datetime import datetime, timezone

        report = adjudicate_inventory(
            inventory,
            session_start_utc=datetime(2026, 7, 29, 23, 34, 29, tzinfo=timezone.utc),
        )
        self.assertEqual(report["current_session_campaign_turns_recovered"], [4, 5, 6, 7])
        self.assertEqual(report["current_session_early_turns_recovered"], [])
        self.assertEqual(report["current_session_trans_battle_record_count"], 0)
        self.assertEqual(report["fixture_trans_battle_record_count_excluded"], 36)
        self.assertEqual(report["historical_campaign_turns_recovered"], [1])
        self.assertEqual(report["class_counts"]["RECOVERY_REEXPORT"], 1)

    def test_shadow_scenario_rejects_conflicting_region_owners(self) -> None:
        with self.assertRaisesRegex(ShadowPipelineError, "conflicting owners"):
            run_shadow_pipeline(
                [
                    RUNTIME_ROOT
                    / "fixtures/shadow_log_owned_visible_owner_conflict_invalid.txt"
                ],
                REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json",
            )

    def test_campaign_shadow_pipeline_batches_five_turns_deterministically(self) -> None:
        log = RUNTIME_ROOT / "fixtures/shadow_campaign_5_turns_valid.txt"
        profile = REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json"
        first = run_shadow_campaign([log], profile)
        second = run_shadow_campaign([log], profile)

        self.assertEqual(first["result_digest"], second["result_digest"])
        self.assertEqual(first["mode"], "SHADOW_NO_ORDERS")
        self.assertEqual(first["metrics"]["turn_count"], 5)
        self.assertEqual(first["metrics"]["turns"], [1, 2, 3, 4, 5])
        self.assertTrue(first["metrics"]["consecutive_turns"])
        self.assertEqual(first["metrics"]["foreign_proxy_violation_count"], 0)
        self.assertFalse(first["authority"]["game_orders_emitted"])
        self.assertFalse(first["authority"]["save_values_written"])
        self.assertNotIn("orders", first)
        self.assertEqual(len(first["turn_results"]), 5)

    def test_campaign_shadow_verifier_accepts_exact_five_turn_run(self) -> None:
        source_log = RUNTIME_ROOT / "fixtures/shadow_campaign_5_turns_valid.txt"
        profile = REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json"
        expected = (
            "bec692bb96c04205e93e97f1e3a60c6b8fcfc7424b540eef8139b7fceaf28261"
        )

        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            log = temp_root / "lua_mod_log.txt"
            log.write_bytes(source_log.read_bytes())

            summary = summarize(parse_logs([log]))
            summary_path = temp_root / "probe_summary.json"
            summary_path.write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            campaign = run_shadow_campaign([log], profile)
            campaign_path = temp_root / "campaign_shadow_report.json"
            campaign_path.write_text(
                json.dumps(campaign, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            manifest = {
                "schema_version": 3,
                "collected_at_utc": "2026-07-29T23:30:00Z",
                "evidence_phase": "campaign_shadow",
                "loaded_probe_kinds": ["shadow"],
                "expected_loaded_probe_kinds": ["shadow"],
                "unexpected_loaded_probe_kinds": [],
                "logs": [
                    {
                        "sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                    }
                ],
                "installed_probe_packs": [
                    {
                        "name": "transcendence_shadow_probe.pack",
                        "installed_sha256": expected,
                        "staged_sha256": expected,
                        "matches_staged": True,
                        "loaded_in_log": True,
                    }
                ],
                "processing": {
                    "collection_and_parse_ms": 100.0,
                    "campaign_pipeline_ms": 20.0,
                },
            }
            manifest_path = temp_root / "evidence_manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n",
                encoding="utf-8",
            )

            report = build_campaign_shadow_verification(
                log_path=log,
                summary_path=summary_path,
                manifest_path=manifest_path,
                campaign_report_path=campaign_path,
                expected_pack_sha256=expected,
                minimum_turns=5,
            )
            self.assertEqual(report["status"], "OBSERVED")
            self.assertTrue(all(report["checks"].values()))

    def test_campaign_shadow_verifier_rejects_too_few_turns(self) -> None:
        source_log = RUNTIME_ROOT / "fixtures/shadow_log_valid.txt"
        profile = REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json"
        expected = "bec692bb96c04205e93e97f1e3a60c6b8fcfc7424b540eef8139b7fceaf28261"

        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            log = temp_root / "lua_mod_log.txt"
            log.write_bytes(source_log.read_bytes())
            summary_path = temp_root / "probe_summary.json"
            summary_path.write_text(
                json.dumps(summarize(parse_logs([log])), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            campaign_path = temp_root / "campaign_shadow_report.json"
            campaign_path.write_text(
                json.dumps(run_shadow_campaign([log], profile), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            manifest_path = temp_root / "evidence_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 3,
                        "loaded_probe_kinds": ["shadow"],
                        "expected_loaded_probe_kinds": ["shadow"],
                        "unexpected_loaded_probe_kinds": [],
                        "logs": [{"sha256": hashlib.sha256(log.read_bytes()).hexdigest()}],
                        "installed_probe_packs": [
                            {
                                "name": "transcendence_shadow_probe.pack",
                                "installed_sha256": expected,
                                "staged_sha256": expected,
                                "matches_staged": True,
                                "loaded_in_log": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = build_campaign_shadow_verification(
                log_path=log,
                summary_path=summary_path,
                manifest_path=manifest_path,
                campaign_report_path=campaign_path,
                expected_pack_sha256=expected,
                minimum_turns=5,
            )
            self.assertEqual(report["status"], "UNVERIFIED")
            self.assertFalse(report["checks"]["minimum_turns_observed"])

    def test_campaign_shadow_pipeline_flags_foreign_strength_policy_violation(self) -> None:
        source = (
            RUNTIME_ROOT / "fixtures/shadow_campaign_5_turns_valid.txt"
        ).read_text(encoding="utf-8")
        source = source.replace(
            "strength_source=VISIBLE_UNIT_COUNT_PROXY",
            "strength_source=EXACT_FORCE_STRENGTH",
            1,
        )
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "bad_foreign_source.txt"
            log.write_text(source, encoding="utf-8")
            result = run_shadow_campaign(
                [log],
                REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json",
            )
            self.assertGreater(
                result["metrics"]["foreign_proxy_violation_count"],
                0,
            )


    def test_campaign_shadow_verifier_rejects_gap_and_wrong_pack(self) -> None:
        source_log = RUNTIME_ROOT / "fixtures/shadow_campaign_5_turns_valid.txt"
        profile = REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json"
        expected = "bec692bb96c04205e93e97f1e3a60c6b8fcfc7424b540eef8139b7fceaf28261"

        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            log = temp_root / "lua_mod_log.txt"
            log.write_bytes(source_log.read_bytes())
            summary_path = temp_root / "probe_summary.json"
            summary_path.write_text(
                json.dumps(summarize(parse_logs([log])), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            campaign = run_shadow_campaign([log], profile)
            campaign["metrics"]["turns"] = [1, 2, 4, 5, 6]
            campaign["metrics"]["consecutive_turns"] = False
            campaign_path = temp_root / "campaign_shadow_report.json"
            campaign_path.write_text(
                json.dumps(campaign, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            manifest_path = temp_root / "evidence_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 3,
                        "loaded_probe_kinds": ["shadow"],
                        "expected_loaded_probe_kinds": ["shadow"],
                        "unexpected_loaded_probe_kinds": [],
                        "logs": [{"sha256": hashlib.sha256(log.read_bytes()).hexdigest()}],
                        "installed_probe_packs": [
                            {
                                "name": "transcendence_shadow_probe.pack",
                                "installed_sha256": "0" * 64,
                                "staged_sha256": "0" * 64,
                                "matches_staged": True,
                                "loaded_in_log": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = build_campaign_shadow_verification(
                log_path=log,
                summary_path=summary_path,
                manifest_path=manifest_path,
                campaign_report_path=campaign_path,
                expected_pack_sha256=expected,
                minimum_turns=5,
            )
            self.assertEqual(report["status"], "UNVERIFIED")
            self.assertFalse(report["checks"]["turns_are_consecutive"])
            self.assertFalse(report["checks"]["exact_shadow_pack_verified"])


    def test_battle_probe_is_read_only_and_visibility_guarded(self) -> None:
        source = (
            RUNTIME_ROOT
            / "source/script/battle/mod/transcendence_battle_probe.lua"
        ).read_text(encoding="utf-8")
        prohibited = (
            "create_unitcontroller",
            ":goto_location(",
            ":attack(",
            ":halt(",
            "modify_battle_speed",
            "force_battle_end",
            "kill_number_of_men",
            "reduce_hitpoints_unary",
            "heal_hitpoints_unary",
            "set_current_ammo",
            "set_always_visible",
            "math.random",
            ":random_number(",
            "cm:set_saved_value",
        )
        for token in prohibited:
            self.assertNotIn(token, source)
        self.assertIn("is_visible_to_alliance", source)
        self.assertIn("VISIBLE_TO_LOCAL_ALLIANCE_ONLY", source)
        self.assertIn("register_command_handler_callback", source)
        self.assertIn("register_unit_selection_callback", source)
        self.assertNotIn("register_unit_selection_handler", source)
        self.assertIn("repeat_real_callback", source)
        self.assertIn("repeat_callback", source)
        self.assertIn("SAMPLER_HEARTBEAT", source)
        self.assertIn('tostring(alliance_index) .. ":u" .. tostring(unique_ui_id)', source)

    def test_battle_log_and_report_are_deterministic(self) -> None:
        log = RUNTIME_ROOT / "fixtures/battle_log_valid.txt"
        first_events = parse_battle_logs([log])
        first_summary = summarize_battle(first_events)
        first_report = build_battle_report(first_events)
        second_report = build_battle_report(parse_battle_logs([log]))
        self.assertEqual(first_report["result_digest"], second_report["result_digest"])
        self.assertEqual(first_summary["completed_battle_count"], 1)
        self.assertEqual(first_report["completed_battle_count"], 1)
        self.assertEqual(first_report["mode"], "BATTLE_OBSERVATION_NO_ORDERS")
        battle = first_report["battle_reports"][0]
        self.assertEqual(battle["unit_counts"]["local_canonical"], 2)
        self.assertEqual(battle["unit_counts"]["visible_enemy_canonical"], 1)
        self.assertEqual(battle["commands"]["command_event_count"], 1)
        self.assertGreater(battle["outcome_metrics"]["local_kills_observed_max_sum"], 0)
        self.assertFalse(battle["sampling"]["time_series_metrics_valid"])
        self.assertFalse(first_report["authority"]["orders_emitted"])


    def test_schema1_identity_churn_is_reconciled_by_unique_ui_id(self) -> None:
        log = RUNTIME_ROOT / "fixtures/battle_log_identity_churn_v1_valid.txt"
        report = build_battle_report(parse_battle_logs([log]))
        battle = report["battle_reports"][0]
        self.assertEqual(battle["identity"]["raw_unit_static_count"], 4)
        self.assertEqual(battle["identity"]["canonical_unit_count"], 3)
        self.assertEqual(battle["identity"]["identity_alias_count"], 1)
        self.assertEqual(battle["identity"]["identity_conflicts"], [])

    def test_dense_schema2_enables_time_series_and_stable_identity(self) -> None:
        log = RUNTIME_ROOT / "fixtures/battle_log_dense_v2_valid.txt"
        report = build_battle_report(parse_battle_logs([log]))
        battle = report["battle_reports"][0]
        self.assertEqual(battle["source_schema"], 2)
        self.assertTrue(battle["sampling"]["time_series_metrics_valid"])
        self.assertEqual(battle["sampling"]["quality"], "DENSE_INTERVAL_COVERAGE")
        self.assertEqual(battle["identity"]["identity_alias_count"], 0)
        self.assertEqual(battle["commands"]["selection_attribution_ratio"], 1.0)
        local = next(unit for unit in battle["unit_metrics"] if unit["stable_unit_id"] == "1:u101")
        self.assertIsNotNone(local["distance_travelled_observed_m"])
        self.assertGreater(local["time_series_metrics"]["observed_duration_ms"], 0)
        self.assertTrue(battle["sampler_heartbeats"])


    def test_schema2_hierarchy_discovery_may_precede_static(self) -> None:
        log = RUNTIME_ROOT / "fixtures/battle_log_dense_setup_abort_v2_partial.txt"
        summary = summarize_battle(parse_battle_logs([log]))
        report = build_battle_report(parse_battle_logs([log]))
        self.assertEqual(summary["battle_session_count"], 1)
        self.assertEqual(summary["completed_battle_count"], 1)
        self.assertEqual(report["battle_reports"][0]["identity"]["canonical_unit_count"], 1)
        self.assertEqual(report["battle_reports"][0]["identity"]["identity_alias_count"], 0)

    def test_schema2_hierarchy_without_static_is_rejected(self) -> None:
        source = (
            RUNTIME_ROOT / "fixtures/battle_log_dense_setup_abort_v2_partial.txt"
        ).read_text(encoding="utf-8")
        source = "\n".join(
            line for line in source.splitlines()
            if "|UNIT_STATIC|" not in line and "|UNIT_STATE|" not in line
        ) + "\n"
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "unresolved_hierarchy.txt"
            log.write_text(source, encoding="utf-8")
            with self.assertRaisesRegex(BattleLogError, "never received UNIT_STATIC"):
                summarize_battle(parse_battle_logs([log]))

    def test_dense_setup_abort_fixture_is_partial_not_unparseable(self) -> None:
        log = RUNTIME_ROOT / "fixtures/battle_log_dense_setup_abort_v2_partial.txt"
        events = parse_battle_logs([log])
        summary = summarize_battle(events)
        report = build_battle_report(events)
        expected_pack = "c" * 64
        result = build_dense_replay_verification(
            summary=summary,
            report=report,
            manifest={
                "installed_pack_sha256": expected_pack,
                "target": {"replay_sha256": EXPECTED_REPLAY_SHA256},
                "captured_log_size_bytes": log.stat().st_size,
                "battle_complete_marker_observed": True,
            },
            expected_pack_sha256=expected_pack,
        )
        self.assertEqual(result["status"], "PARTIAL")
        self.assertTrue(result["checks"]["schema2_session_observed"])
        self.assertTrue(result["checks"]["completed_replay_observed"])
        self.assertFalse(result["checks"]["dense_interval_coverage"])
        self.assertFalse(result["checks"]["sampler_heartbeat_observed"])

    def test_sparse_phase_fixture_withholds_time_series_and_inference(self) -> None:
        report = build_battle_report(
            parse_battle_logs([RUNTIME_ROOT / "fixtures/battle_log_valid.txt"])
        )
        battle = report["battle_reports"][0]
        self.assertFalse(battle["sampling"]["time_series_metrics_valid"])
        self.assertEqual(
            battle["inferred_command_attribution"]["status"],
            "WITHHELD_SPARSE_SAMPLING",
        )
        self.assertIsNone(battle["unit_metrics"][0]["time_series_metrics"])

    def test_battle_replay_pack_is_battle_only_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as output:
            build = build_all(REPO_ROOT, Path(output))
            record = next(
                pack for pack in build["packs"] if pack["probe_kind"] == "battle_replay"
            )
            self.assertFalse(record["save_mutation"])
            self.assertFalse(record["gameplay_mutation"])
            parsed = parse_pfh5_index(Path(output) / record["pack_name"])
            self.assertEqual(
                {item["path"] for item in parsed["entries"]},
                {"script/battle/mod/transcendence_battle_probe.lua"},
            )

    def test_optional_battle_capability_unavailable_is_disclosed_not_fatal(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/battle_log_valid.txt").read_text(
            encoding="utf-8"
        )
        source = source.replace(
            "TRANS_BATTLE|1|BATTLE_START|",
            "TRANS_BATTLE|1|CAPABILITY|name=unit.optional_example|available=false|required=false|error=missing\nTRANS_BATTLE|1|BATTLE_START|",
            1,
        )
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "optional.txt"
            log.write_text(source, encoding="utf-8")
            summary = summarize_battle(parse_battle_logs([log]))
            self.assertEqual(summary["capability_failures"], [])
            self.assertEqual(summary["optional_unavailable"], ["unit.optional_example"])

    def test_required_battle_capability_unavailable_fails_gate_minimum(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/battle_log_valid.txt").read_text(
            encoding="utf-8"
        )
        source = source.replace(
            "TRANS_BATTLE|1|BATTLE_START|",
            "TRANS_BATTLE|1|CAPABILITY|name=battle.required_example|available=false|required=true|error=missing\nTRANS_BATTLE|1|BATTLE_START|",
            1,
        )
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "required.txt"
            log.write_text(source, encoding="utf-8")
            summary = summarize_battle(parse_battle_logs([log]))
            self.assertEqual(summary["capability_failures"], ["battle.required_example"])
            self.assertEqual(summary["optional_unavailable"], [])

    def test_battle_parser_rejects_hidden_enemy_unit_leak(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/battle_log_valid.txt").read_text(
            encoding="utf-8"
        )
        source = source.replace(
            "local_alliance=false|visibility_source=VISIBLE_TO_LOCAL_ALLIANCE",
            "local_alliance=false|visibility_source=HIDDEN_FROM_LOCAL_ALLIANCE",
            1,
        )
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "hidden_leak.txt"
            log.write_text(source, encoding="utf-8")
            with self.assertRaises(BattleLogError):
                summarize_battle(parse_battle_logs([log]))

    def test_battle_parser_rejects_unclosed_sample(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/battle_log_valid.txt").read_text(
            encoding="utf-8"
        )
        source = source.replace(
            "TRANS_BATTLE|1|SAMPLE_END|time_ms=8000|sample_index=4|reason=PHASE_Complete|observed_units=3|hidden_enemy_units=1|total_units_seen_by_hierarchy=4|unit_cap=240\n",
            "",
        )
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "open_sample.txt"
            log.write_text(source, encoding="utf-8")
            with self.assertRaises(BattleLogError):
                summarize_battle(parse_battle_logs([log]))

    def test_combined_campaign_battle_verifier_accepts_batched_fixture(self) -> None:
        source = RUNTIME_ROOT / "fixtures/campaign_battle_5_turns_valid.txt"
        profile = REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build = build_all(REPO_ROOT, root / "packs")
            shadow = next(
                pack for pack in build["packs"] if pack["probe_kind"] == "shadow"
            )
            expected = shadow["pack_sha256"]
            log = root / "lua_mod_log.txt"
            log.write_bytes(source.read_bytes())
            campaign_summary = summarize(parse_logs([log]))
            battle_summary = summarize_battle(parse_battle_logs([log]))
            campaign_report = run_shadow_campaign([log], profile)
            battle_report = build_battle_report(parse_battle_logs([log]))

            paths = {
                "campaign_summary": root / "campaign_summary.json",
                "battle_summary": root / "battle_summary.json",
                "campaign_report": root / "campaign_report.json",
                "battle_report": root / "battle_report.json",
            }
            for key, value in (
                ("campaign_summary", campaign_summary),
                ("battle_summary", battle_summary),
                ("campaign_report", campaign_report),
                ("battle_report", battle_report),
            ):
                paths[key].write_text(
                    json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            manifest = {
                "schema_version": 4,
                "collected_at_utc": "2026-07-30T00:00:00Z",
                "evidence_phase": "campaign_battle",
                "loaded_probe_kinds": ["shadow"],
                "expected_loaded_probe_kinds": ["shadow"],
                "unexpected_loaded_probe_kinds": [],
                "battle_probe_loaded": True,
                "combined_session_manifest": {
                    "sha256": "9" * 64,
                    "prepared_at_utc": "2026-07-29T23:59:00Z",
                    "staged_shadow_pack_sha256": expected,
                    "installed_shadow_pack_sha256": expected,
                },
                "logs": [{"sha256": hashlib.sha256(log.read_bytes()).hexdigest()}],
                "installed_probe_packs": [
                    {
                        "name": "transcendence_shadow_probe.pack",
                        "installed_sha256": expected,
                        "staged_sha256": expected,
                        "matches_staged": True,
                        "loaded_in_log": True,
                    }
                ],
                "processing": {"collection_and_parse_ms": 100.0},
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = build_campaign_battle_verification(
                log_path=log,
                campaign_summary_path=paths["campaign_summary"],
                battle_summary_path=paths["battle_summary"],
                manifest_path=manifest_path,
                campaign_report_path=paths["campaign_report"],
                battle_report_path=paths["battle_report"],
                expected_pack_sha256=expected,
                minimum_turns=5,
                minimum_completed_battles=1,
            )
            self.assertEqual(report["status"], "OBSERVED")
            self.assertTrue(all(report["campaign_checks"].values()))
            self.assertTrue(all(report["battle_checks"].values()))
            self.assertTrue(all(report["session_checks"].values()))

    def test_combined_verifier_marks_no_battle_as_partial(self) -> None:
        source = RUNTIME_ROOT / "fixtures/shadow_campaign_5_turns_valid.txt"
        profile = REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build = build_all(REPO_ROOT, root / "packs")
            expected = next(
                pack["pack_sha256"]
                for pack in build["packs"]
                if pack["probe_kind"] == "shadow"
            )
            log = root / "log.txt"
            log.write_bytes(source.read_bytes())
            campaign_summary_path = root / "campaign_summary.json"
            campaign_report_path = root / "campaign_report.json"
            battle_summary_path = root / "battle_summary.json"
            battle_report_path = root / "battle_report.json"
            campaign_summary_path.write_text(
                json.dumps(summarize(parse_logs([log]))), encoding="utf-8"
            )
            campaign_report_path.write_text(
                json.dumps(run_shadow_campaign([log], profile)), encoding="utf-8"
            )
            battle_summary_path.write_text(
                json.dumps(
                    {
                        "battle_session_count": 0,
                        "completed_battle_count": 0,
                        "capability_failures": ["battle_probe_not_observed"],
                    }
                ),
                encoding="utf-8",
            )
            battle_report_path.write_text(
                json.dumps(
                    {
                        "completed_battle_count": 0,
                        "battle_reports": [],
                        "authority": {
                            "unitcontrollers_created": False,
                            "orders_emitted": False,
                            "battle_speed_modified": False,
                            "save_values_written": False,
                            "visibility_modified": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "loaded_probe_kinds": ["shadow"],
                        "expected_loaded_probe_kinds": ["shadow"],
                        "unexpected_loaded_probe_kinds": [],
                        "battle_probe_loaded": False,
                        "combined_session_manifest": {
                            "sha256": "9" * 64,
                            "prepared_at_utc": "2026-07-29T23:59:00Z",
                            "staged_shadow_pack_sha256": expected,
                            "installed_shadow_pack_sha256": expected,
                        },
                        "logs": [{"sha256": hashlib.sha256(log.read_bytes()).hexdigest()}],
                        "installed_probe_packs": [
                            {
                                "name": "transcendence_shadow_probe.pack",
                                "installed_sha256": expected,
                                "staged_sha256": expected,
                                "matches_staged": True,
                                "loaded_in_log": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = build_campaign_battle_verification(
                log_path=log,
                campaign_summary_path=campaign_summary_path,
                battle_summary_path=battle_summary_path,
                manifest_path=manifest_path,
                campaign_report_path=campaign_report_path,
                battle_report_path=battle_report_path,
                expected_pack_sha256=expected,
            )
            self.assertEqual(report["status"], "PARTIAL_NO_BATTLE")


    def test_powershell_collectors_do_not_resolve_repo_in_param_defaults(self) -> None:
        for name in ("collect_campaign_battle.ps1", "collect_campaign_shadow.ps1"):
            source = (RUNTIME_ROOT / "tools" / name).read_text(encoding="utf-8-sig")
            parameter_section = source.split("Set-StrictMode", 1)[0]
            self.assertNotIn("$PSScriptRoot", parameter_section, name)
            self.assertIn('if ([string]::IsNullOrWhiteSpace($RepoRoot))', source, name)


    def test_campaign_battle_collector_accepts_preserved_input_log(self) -> None:
        source = (
            RUNTIME_ROOT / "tools/collect_campaign_battle.ps1"
        ).read_text(encoding="utf-8-sig")
        self.assertIn('[string]$InputLogPath = ""', source)
        self.assertIn("-LogPaths $InputLogPath", source)
        self.assertIn("Resolve-Path -LiteralPath $InputLogPath", source)


    def test_dense_battle4_verifier_accepts_complete_schema2_replay(self) -> None:
        log = RUNTIME_ROOT / "fixtures/battle_log_dense_v2_valid.txt"
        events = parse_battle_logs([log])
        summary = summarize_battle(events)
        report = build_battle_report(events)
        expected_pack = "a" * 64
        manifest = {
            "installed_pack_sha256": expected_pack,
            "target": {"replay_sha256": EXPECTED_REPLAY_SHA256},
            "captured_log_size_bytes": log.stat().st_size,
            "battle_complete_marker_observed": True,
        }
        result = build_dense_replay_verification(
            summary=summary,
            report=report,
            manifest=manifest,
            expected_pack_sha256=expected_pack,
        )
        self.assertEqual(result["status"], "OBSERVED_DENSE")
        self.assertTrue(all(result["checks"].values()))
        self.assertTrue(result["selection_callback_observed"])

    def test_dense_battle4_verifier_preserves_selection_limiting_result(self) -> None:
        log = RUNTIME_ROOT / "fixtures/battle_log_dense_v2_valid.txt"
        events = parse_battle_logs([log])
        summary = summarize_battle(events)
        report = build_battle_report(events)
        report["battle_reports"][0]["commands"]["selection_attribution_ratio"] = 0.0
        expected_pack = "b" * 64
        manifest = {
            "installed_pack_sha256": expected_pack,
            "target": {"replay_sha256": EXPECTED_REPLAY_SHA256},
            "captured_log_size_bytes": log.stat().st_size,
            "battle_complete_marker_observed": True,
        }
        result = build_dense_replay_verification(
            summary=summary,
            report=report,
            manifest=manifest,
            expected_pack_sha256=expected_pack,
        )
        self.assertEqual(result["status"], "OBSERVED_DENSE_SELECTION_LIMITING_RESULT")
        self.assertTrue(all(result["checks"].values()))
        self.assertFalse(result["selection_callback_observed"])

    def test_dense_observed_corpus_preserves_timeline_and_inference_contract(self) -> None:
        log = RUNTIME_ROOT / "fixtures/battle_log_dense_v2_valid.txt"
        report = build_battle_report(parse_battle_logs([log]))
        corpus = build_corpus(
            report,
            corpus_id="dense_fixture_v2",
            replay_sha256="1" * 64,
            raw_log_sha256="2" * 64,
            capture_verification_digest="3" * 64,
            owner_context="Dense deterministic fixture.",
        )
        self.assertEqual(
            corpus["fidelity_label"],
            "OBSERVED_WH3_REPLAY_CORPUS_DENSE_TIMELINE",
        )
        self.assertTrue(corpus["battle"]["sampling"]["time_series_metrics_valid"])
        self.assertIn("aggregate_timeline", corpus["battle"])
        self.assertIn("inferred_command_attribution", corpus["battle"])
        self.assertIn("time_series_metrics", corpus["battle"]["units"][0])
        self.assertNotIn(
            "Sparse phase samples establish exact engagement, routing, reserve, fatigue, or flank timing.",
            corpus["forbidden_inferences"],
        )
        validate_observed_battle_corpus(corpus)
        regression = derive_reality_regressions(corpus)
        self.assertTrue(regression["checks"]["stable_identity_contract_holds"])

    def test_dense_replay_source_has_dual_sampler_stable_identity_and_selection(self) -> None:
        source = (
            RUNTIME_ROOT / "source/script/battle/mod/transcendence_battle_probe.lua"
        ).read_text(encoding="utf-8")
        self.assertIn("TRANS_BATTLE_SCHEMA = 2", source)
        self.assertIn("repeat_callback", source)
        self.assertIn("repeat_real_callback", source)
        self.assertIn("SAMPLER_HEARTBEAT", source)
        self.assertIn("unit:unique_ui_id()", source)
        self.assertIn("register_unit_selection_callback(unit", source)
        self.assertIn("function transcendence_battle_probe_selection_handler(unit, is_selected)", source)
        self.assertIn('io.open, TRANS_BATTLE_RUNTIME_LOG, "a"', source)
        self.assertIn('{"name", "battle.setup"}', source)
        self.assertNotIn("math.max(0, trans_battle_safe(", source)
        self.assertIn("tonumber(aggregate_ammo) or 0", source)
        self.assertLess(
            source.index('trans_battle_emit("SAMPLER_START"'),
            source.index('trans_battle_aggregate_sample("DIRECT")'),
        )
        for prohibited in (
            ":create_unitcontroller",
            ":goto_location",
            ":attack_unit",
            ":set_current_ammo_unary",
            ":kill_number_of_men",
            ":reduce_hitpoints_unary",
            ":heal_hitpoints_unary",
        ):
            self.assertNotIn(prohibited, source.lower())

    def test_dense_capture_watcher_uses_append_log_and_exact_replay(self) -> None:
        source = (RUNTIME_ROOT / "tools/capture_battle4_dense_replay.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('LOG_NAME = "transcendence_runtime_log.txt"', source)
        self.assertIn("EXPECTED_REPLAY_SHA256", source)
        self.assertIn("TRANS_BATTLE|2|BATTLE_COMPLETE", source)
        self.assertIn("build_dense_replay_verification", source)
        self.assertIn("build_corpus", source)
        self.assertNotIn("lua_mod_log.txt", source)


    def test_preserved_dense_capture_can_be_reprocessed_without_raw_log_export(self) -> None:
        fixture = RUNTIME_ROOT / "fixtures/battle_log_dense_setup_abort_v2_partial.txt"
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            capture = repo / "local_inputs/runtime_probe/battle4_dense/capture_test"
            capture.mkdir(parents=True)
            shutil.copy2(fixture, capture / "battle4_dense_trans_battle_log.txt")
            expected_pack = "d" * 64
            (capture / "capture_manifest.json").write_text(
                json.dumps(
                    {
                        "expected_pack_sha256": expected_pack,
                        "installed_pack_sha256": expected_pack,
                        "target": {"replay_sha256": EXPECTED_REPLAY_SHA256},
                        "captured_log_size_bytes": fixture.stat().st_size,
                        "battle_complete_marker_observed": True,
                    }
                ),
                encoding="utf-8",
            )
            result = reprocess_capture(repo, capture)
            self.assertEqual(result["status"], "PARTIAL")
            self.assertTrue(Path(result["zip_path"]).is_file())
            with zipfile.ZipFile(result["zip_path"]) as archive:
                names = set(archive.namelist())
                self.assertNotIn("battle4_dense_trans_battle_log.txt", names)
                self.assertIn("reprocess_manifest.json", names)



    def test_action_authority_probe_is_read_only_and_has_no_controller(self) -> None:
        source = (
            RUNTIME_ROOT / "source/script/battle/mod/transcendence_action_authority_probe.lua"
        ).read_text(encoding="utf-8")
        self.assertIn("TRANS_ACTION_SCHEMA = 1", source)
        self.assertIn("GAME_COMMAND_EVENT_ORIGIN_UNRESOLVED", source)
        self.assertIn("OBSERVED_COMMAND_EVENT_NOT_PROJECT_ISSUE", source)
        self.assertIn("unit:can_reach_position", source)
        self.assertIn("unit:ordered_position", source)
        self.assertIn("unit:current_target", source)
        self.assertIn("register_command_handler_callback", source)
        self.assertIn("register_unit_selection_callback", source)
        for prohibited in (
            ":create_unit_controller",
            ":create_unitcontroller",
            ":take_control",
            ":goto_location",
            ":attack_unit",
            ":withdraw()",
            ":halt()",
            "set_battle_speed",
            "set_saved_value",
            "math.random",
        ):
            self.assertNotIn(prohibited, source.lower())

    def test_valid_action_authority_log_is_strictly_read_only(self) -> None:
        events = parse_action_logs(
            [RUNTIME_ROOT / "fixtures/action_authority_log_valid.txt"]
        )
        summary = summarize_action_events(events)
        self.assertEqual(summary["authority"], "NO_ORDERS")
        session = summary["sessions"][0]
        self.assertTrue(session["complete"])
        self.assertEqual(session["window_count"], 2)
        self.assertEqual(session["bound_window_count"], 1)
        self.assertEqual(session["unbound_window_count"], 1)
        self.assertEqual(session["project_issue_attempt_count"], 0)
        self.assertEqual(session["direct_acknowledgement_count"], 0)
        self.assertEqual(session["command_event_count"], 2)
        self.assertEqual(session["selection_event_count"], 2)
        self.assertEqual(session["reachability_counts"]["QUERY_TRUE"], 2)
        self.assertEqual(session["state_match_counts"]["ordered_position_match"], 2)
        self.assertEqual(session["close_reason_counts"]["WINDOW_TIMEOUT"], 1)
        self.assertEqual(session["close_reason_counts"]["UNBOUND_SELECTION"], 1)

    def test_action_authority_parser_rejects_issue_ack_and_hidden_target(self) -> None:
        for name in (
            "action_authority_log_project_issue_invalid.txt",
            "action_authority_log_direct_ack_invalid.txt",
            "action_authority_log_hidden_target_invalid.txt",
        ):
            with self.assertRaises(ActionAuthorityLogError, msg=name):
                summarize_action_events(parse_action_logs([RUNTIME_ROOT / "fixtures" / name]))

    def test_action_authority_manifest_is_battle_only_and_nonmutating(self) -> None:
        manifest = json.loads(
            (RUNTIME_ROOT / "manifests/action_authority_pack.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["probe_kind"], "action_authority")
        self.assertFalse(manifest["save_mutation"])
        self.assertFalse(manifest["gameplay_mutation"])
        self.assertEqual(len(manifest["entries"]), 1)
        self.assertTrue(
            manifest["entries"][0]["internal_path"].startswith("script/battle/")
        )

    def test_action_authority_capture_verifier_accepts_exact_read_only_fixture(self) -> None:
        summary = summarize_action_events(
            parse_action_logs([RUNTIME_ROOT / "fixtures/action_authority_log_valid.txt"])
        )
        manifest = json.loads(
            (RUNTIME_ROOT / "fixtures/action_authority_prepared_manifest_valid.json").read_text(encoding="utf-8")
        )
        result = build_action_authority_verification(
            summary=summary,
            prepared_manifest=manifest,
            expected_pack_sha256="a" * 64,
            fixture_control=True,
        )
        self.assertEqual(result["status"], "CONTROL_FIXTURE_READ_ONLY_ACTION_AUTHORITY")
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["project_issue_attempt_count"], 0)
        self.assertEqual(result["direct_acknowledgement_count"], 0)

    def test_action_authority_capture_verifier_rejects_pack_mismatch(self) -> None:
        summary = summarize_action_events(
            parse_action_logs([RUNTIME_ROOT / "fixtures/action_authority_log_valid.txt"])
        )
        manifest = json.loads(
            (RUNTIME_ROOT / "fixtures/action_authority_prepared_manifest_valid.json").read_text(encoding="utf-8")
        )
        result = build_action_authority_verification(
            summary=summary,
            prepared_manifest=manifest,
            expected_pack_sha256="b" * 64,
            fixture_control=True,
        )
        self.assertEqual(result["status"], "UNVERIFIED_ACTION_AUTHORITY_CAPTURE")
        self.assertFalse(result["checks"]["exact_expected_pack"])

    def test_action_authority_capture_scripts_are_batched_and_private_safe(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_action_authority_capture.ps1").read_text(encoding="utf-8")
        collect = (RUNTIME_ROOT / "tools/collect_action_authority_capture.ps1").read_text(encoding="utf-8")
        rollback = (RUNTIME_ROOT / "tools/rollback_action_authority_probe.ps1").read_text(encoding="utf-8")
        self.assertIn("active_mod_list_modified = $false", prepare)
        self.assertIn("wh3_save_modified = $false", prepare)
        self.assertIn("project_orders_enabled = $false", prepare)
        self.assertIn("raw_log_included_in_export = $false", collect)
        self.assertIn("verify_action_authority_capture.py", collect)
        self.assertNotIn("used_mods.txt", collect)
        self.assertNotIn("lua_mod_log.txt", prepare + collect + rollback)
        self.assertIn("Refusing rollback without -Force", rollback)
        self.assertIn("The active mod list and saves were not modified", rollback)



    def test_v01s_live_action_authority_capture_adjudicates_exact_public_documents(self) -> None:
        evidence = REPO_ROOT / "research/runtime_evidence/action_authority_live_capture_v0.1S"
        summary = json.loads((evidence / "action_authority_summary.json").read_text(encoding="utf-8-sig"))
        verification = json.loads((evidence / "action_authority_verification.json").read_text(encoding="utf-8-sig"))
        manifest = json.loads((evidence / "public_capture_manifest.json").read_text(encoding="utf-8-sig"))
        result = adjudicate_action_authority_documents(
            summary=summary,
            verification=verification,
            manifest=manifest,
            source_export_sha256="a1c03ec12a4c2b70945311fc57b54f978fcca892a37b12d46a5daa6f22ebf579",
        )
        frozen = json.loads(
            (REPO_ROOT / "research/runtime_evidence/ACTION_AUTHORITY_LIVE_CAPTURE_ADJUDICATION_v0.1S.json").read_text(encoding="utf-8")
        )
        self.assertEqual(result, frozen)
        self.assertEqual(result["status"], "OBSERVED_READ_ONLY_ACTION_AUTHORITY_CALIBRATED")
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertEqual(result["session_metrics"]["window_count"], 89)
        self.assertEqual(result["session_metrics"]["bound_window_count"], 89)
        self.assertEqual(result["session_metrics"]["selection_binding_rate"], 1.0)
        self.assertEqual(result["session_metrics"]["sample_count"], 1287)
        self.assertEqual(
            result["capability_adjudications"]["point_reachability_query"]["classification"],
            "OBSERVED",
        )
        self.assertEqual(
            result["capability_adjudications"]["leaving_battle_state_visibility"]["classification"],
            "UNVERIFIED",
        )
        self.assertEqual(
            result["capability_adjudications"]["shattered_state_visibility"]["classification"],
            "UNVERIFIED",
        )
        self.assertFalse(result["next_gate_boundary"]["live_capture_repeat_required"])

    def test_v01s_public_export_rejects_tampered_member_hash(self) -> None:
        evidence = REPO_ROOT / "research/runtime_evidence/action_authority_live_capture_v0.1S"
        with tempfile.TemporaryDirectory() as temp:
            capture = Path(temp) / "capture.zip"
            with zipfile.ZipFile(capture, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name in (
                    "action_authority_summary.json",
                    "action_authority_verification.json",
                    "public_capture_manifest.json",
                ):
                    blob = (evidence / name).read_bytes()
                    if name == "action_authority_summary.json":
                        blob += b"\n"
                    archive.writestr(name, blob)
            with self.assertRaises(ActionAuthorityExportError):
                adjudicate_action_authority_zip(capture)

    def test_v01s_schema2_public_preparation_attestation_is_independently_bound(self) -> None:
        evidence = REPO_ROOT / "research/runtime_evidence/action_authority_live_capture_v0.1S"
        summary_blob = (evidence / "action_authority_summary.json").read_bytes()
        verification_blob = (evidence / "action_authority_verification.json").read_bytes()
        manifest = json.loads((evidence / "public_capture_manifest.json").read_text(encoding="utf-8-sig"))
        attestation = {
            "schema_version": 1,
            "capture_kind": "action_authority",
            "prepared_at_utc": "2026-07-30T07:55:00+00:00",
            "pack_name": "transcendence_action_authority_probe.pack",
            "staged_pack_sha256": ACTION_AUTHORITY_EXPECTED_PACK_SHA256,
            "installed_pack_sha256": ACTION_AUTHORITY_EXPECTED_PACK_SHA256,
            "runtime_log_cleared": True,
            "active_mod_list_modified": False,
            "wh3_save_modified": False,
            "project_orders_enabled": False,
        }
        attestation_blob = (json.dumps(attestation, indent=2, sort_keys=True) + "\n").encode("utf-8")
        manifest["schema_version"] = 2
        manifest["preparation_attestation_sha256"] = hashlib.sha256(attestation_blob).hexdigest()
        manifest_blob = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as temp:
            capture = Path(temp) / "capture_v2.zip"
            with zipfile.ZipFile(capture, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("action_authority_summary.json", summary_blob)
                archive.writestr("action_authority_verification.json", verification_blob)
                archive.writestr("public_preparation_attestation.json", attestation_blob)
                archive.writestr("public_capture_manifest.json", manifest_blob)
            result = adjudicate_action_authority_zip(capture)
            self.assertEqual(
                result["public_preparation_attestation"],
                "PUBLIC_SANITIZED_ATTESTATION_VERIFIED",
            )

    def test_v01s_collector_exports_sanitized_preparation_attestation(self) -> None:
        collect = (RUNTIME_ROOT / "tools/collect_action_authority_capture.ps1").read_text(encoding="utf-8")
        self.assertIn('schema_version = 2', collect)
        self.assertIn('public_preparation_attestation.json', collect)
        self.assertIn('preparation_attestation_sha256', collect)
        self.assertIn('runtime_log_cleared = [bool]$Prepared.runtime_log_cleared', collect)
        self.assertIn('active_mod_list_modified = [bool]$Prepared.active_mod_list_modified', collect)
        self.assertNotIn('runtime_log = [string]$Prepared.runtime_log', collect)
        self.assertNotIn('installed_pack_backup = [string]$Prepared.installed_pack_backup', collect)


    def test_repository_validator_accepts_powershell_utf8_bom_json(self) -> None:
        validator_path = REPO_ROOT / "tools/validate_repository.py"
        spec = importlib.util.spec_from_file_location(
            "transcendence_validator_bom_json", validator_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "powershell.json"
            evidence.write_bytes(b"\xef\xbb\xbf{\"schema_version\":1}\r\n")
            self.assertEqual(module.load_json_file(evidence), {"schema_version": 1})

    def test_v01t_detailed_feasibility_export_matches_fixture(self) -> None:
        raw = RUNTIME_ROOT / "fixtures/action_authority_log_valid.txt"
        prepared = RUNTIME_ROOT / "fixtures/action_authority_prepared_manifest_valid.json"
        result = build_action_feasibility_window_export(
            raw,
            prepared,
            expected_raw_log_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
            expected_pack_sha256="a" * 64,
        )
        frozen = json.loads(
            (RUNTIME_ROOT / "fixtures/action_feasibility_windows_valid.json").read_text(encoding="utf-8")
        )
        self.assertEqual(result, frozen)
        self.assertEqual(result["window_count"], 2)
        self.assertEqual(result["sample_count"], 2)
        self.assertFalse(result["raw_log_in_export"])
        self.assertEqual(result["authority"], "NO_ORDERS")

    def test_v01t_detailed_reexport_verifier_accepts_exact_fixture(self) -> None:
        raw = RUNTIME_ROOT / "fixtures/action_authority_log_valid.txt"
        result = verify_action_feasibility_reexport_zip(
            RUNTIME_ROOT / "fixtures/action_feasibility_reexport_valid.zip",
            expected_raw_log_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
            expected_pack_sha256="a" * 64,
            expected_source_public_capture_sha256="b" * 64,
        )
        frozen = json.loads(
            (RUNTIME_ROOT / "fixtures/action_feasibility_reexport_verification_valid.json").read_text(encoding="utf-8")
        )
        self.assertEqual(result, frozen)
        self.assertEqual(result["status"], "VERIFIED_PUBLIC_SAFE_DETAILED_REEXPORT")

    def test_v01t_detailed_reexport_rejects_tampered_member(self) -> None:
        source = RUNTIME_ROOT / "fixtures/action_feasibility_reexport_valid.zip"
        raw = RUNTIME_ROOT / "fixtures/action_authority_log_valid.txt"
        with tempfile.TemporaryDirectory() as temp:
            tampered = Path(temp) / "tampered.zip"
            with zipfile.ZipFile(source) as input_archive, zipfile.ZipFile(
                tampered, "w", compression=zipfile.ZIP_DEFLATED
            ) as output_archive:
                for name in input_archive.namelist():
                    blob = input_archive.read(name)
                    if name == "action_feasibility_windows.json":
                        blob += b"\n"
                    output_archive.writestr(name, blob)
            with self.assertRaises(ActionFeasibilityVerificationError):
                verify_action_feasibility_reexport_zip(
                    tampered,
                    expected_raw_log_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                    expected_pack_sha256="a" * 64,
                    expected_source_public_capture_sha256="b" * 64,
                )

    def test_v01t_detailed_export_rejects_hidden_target_and_raw_hash_mismatch(self) -> None:
        prepared = RUNTIME_ROOT / "fixtures/action_authority_prepared_manifest_valid.json"
        with self.assertRaises(ActionFeasibilityExportError):
            build_action_feasibility_window_export(
                RUNTIME_ROOT / "fixtures/action_authority_log_hidden_target_invalid.txt",
                prepared,
                expected_pack_sha256="a" * 64,
            )
        with self.assertRaises(ActionFeasibilityExportError):
            build_action_feasibility_window_export(
                RUNTIME_ROOT / "fixtures/action_authority_log_valid.txt",
                prepared,
                expected_raw_log_sha256="0" * 64,
                expected_pack_sha256="a" * 64,
            )

    def test_v01t_reexport_workflow_is_read_only_private_safe_and_no_replay(self) -> None:
        script = (RUNTIME_ROOT / "tools/reexport_action_feasibility_capture.ps1").read_text(encoding="utf-8")
        self.assertIn("ExpectedRawLogSha256", script)
        self.assertIn("export_action_feasibility_windows.py", script)
        self.assertIn("source_raw_log_in_export = $false", script)
        self.assertIn("personal_paths_in_export = $false", script)
        self.assertIn("No WH3 run", script)
        self.assertNotIn("prepare_action_authority_capture.ps1", script)
        self.assertNotIn("Copy-Item -LiteralPath $BuiltPack", script)
        self.assertNotIn("unitcontroller", script.lower())

    def test_v01u_live_semantic_calibration_matches_current_implementation(self) -> None:
        windows_path = REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_WINDOWS_OBSERVED_v0.1U.json"
        manifest_path = REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_REEXPORT_MANIFEST_OBSERVED_v0.1U.json"
        windows_blob = windows_path.read_bytes()
        manifest_blob = manifest_path.read_bytes()
        result = adjudicate_action_feasibility_documents(
            json.loads(windows_blob.decode("utf-8-sig")),
            json.loads(manifest_blob.decode("utf-8-sig")),
            source_zip_sha256="83b7c3d851605f290c6a50045be920cdddc7224c8f9e7e63deefba5323e2ff7d",
            windows_sha256=hashlib.sha256(windows_blob).hexdigest(),
            manifest_sha256=hashlib.sha256(manifest_blob).hexdigest(),
        )
        frozen = json.loads(
            (REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_SEMANTIC_CALIBRATION_v0.1U.json").read_text(encoding="utf-8")
        )
        self.assertEqual(result, frozen)

    def test_v01u_nonpoint_zero_vector_false_results_are_disqualified(self) -> None:
        calibration = json.loads(
            (REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_SEMANTIC_CALIBRATION_v0.1U.json").read_text(encoding="utf-8")
        )
        self.assertEqual(calibration["raw_probe_reachability_counts"]["QUERY_FALSE"], 38)
        self.assertEqual(calibration["qualified_explicit_point_reachability_counts"]["QUERY_FALSE"], 0)
        self.assertEqual(calibration["defect_adjudication"]["affected_window_ids"], ["w5"])
        self.assertEqual(calibration["defect_adjudication"]["discarded_nonpoint_query_false_count"], 38)
        self.assertEqual(calibration["explicit_point_observation"]["window_count"], 16)
        self.assertEqual(calibration["explicit_point_observation"]["query_true"], 191)

    def test_v01u_semantic_adjudicator_rejects_zero_vector_move_and_issue_claim(self) -> None:
        windows_path = REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_WINDOWS_OBSERVED_v0.1U.json"
        manifest_path = REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_REEXPORT_MANIFEST_OBSERVED_v0.1U.json"
        source = json.loads(windows_path.read_text(encoding="utf-8-sig"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))

        zero_move = json.loads(json.dumps(source))
        move = next(item for item in zero_move["windows"] if item["command"] == "Move")
        move["target_position"] = {"x": 0.0, "y": 0.0, "z": 0.0}
        move_material = dict(move)
        move_material.pop("result_digest")
        move["result_digest"] = hashlib.sha256(
            json.dumps(move_material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        top_material = dict(zero_move)
        top_material.pop("result_digest")
        zero_move["result_digest"] = hashlib.sha256(
            json.dumps(top_material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        zero_blob = (json.dumps(zero_move, indent=2, sort_keys=True) + "\n").encode("utf-8")
        zero_manifest = dict(manifest)
        zero_manifest["action_feasibility_windows_sha256"] = hashlib.sha256(zero_blob).hexdigest()
        with self.assertRaises(ActionFeasibilitySemanticError):
            adjudicate_action_feasibility_documents(
                zero_move, zero_manifest, source_zip_sha256="0" * 64,
                windows_sha256=hashlib.sha256(zero_blob).hexdigest(),
                manifest_sha256="1" * 64,
            )

        issue = json.loads(json.dumps(source))
        issue["project_issue_attempt_count"] = 1
        issue_material = dict(issue)
        issue_material.pop("result_digest")
        issue["result_digest"] = hashlib.sha256(
            json.dumps(issue_material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        issue_blob = (json.dumps(issue, indent=2, sort_keys=True) + "\n").encode("utf-8")
        issue_manifest = dict(manifest)
        issue_manifest["action_feasibility_windows_sha256"] = hashlib.sha256(issue_blob).hexdigest()
        with self.assertRaises(ActionFeasibilitySemanticError):
            adjudicate_action_feasibility_documents(
                issue, issue_manifest, source_zip_sha256="0" * 64,
                windows_sha256=hashlib.sha256(issue_blob).hexdigest(),
                manifest_sha256="1" * 64,
            )


    def test_v01y_preparation_control_artifact_matches_current_implementation(self) -> None:
        current = build_artifact(REPO_ROOT)
        frozen = json.loads(
            (REPO_ROOT / "research/runtime_evidence/SFO_COMBINED_SESSION_PREPARATION_CONTROL_v0.1Y.json").read_text(encoding="utf-8")
        )
        self.assertEqual(current, frozen)
        self.assertTrue(all(current["checks"].values()))

    def test_v01y_r2_discovers_game_root_used_mods_when_appdata_copy_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "steamapps" / "common" / "Total War WARHAMMER III"
            appdata = root / "AppData" / "Roaming"
            game.mkdir(parents=True)
            appdata.mkdir(parents=True)
            used = game / "used_mods.txt"
            used.write_text(
                'mod "@sfo_grimhammer_3.pack";\nmod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            selected, source_kind, entries = discover_used_mods_path(
                game_root=game, appdata_root=appdata
            )
            self.assertEqual(selected, used.resolve())
            self.assertEqual(source_kind, "GAME_ROOT")
            self.assertEqual(entries, ["@sfo_grimhammer_3.pack", "transcendence_shadow_probe.pack"])

    def test_v01y_r2_falls_back_to_steam_appdata_used_mods(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "steamapps" / "common" / "Total War WARHAMMER III"
            appdata = root / "AppData" / "Roaming"
            used = appdata / "The Creative Assembly" / "Warhammer3" / "scripts" / "used_mods.txt"
            game.mkdir(parents=True)
            used.parent.mkdir(parents=True)
            used.write_text(
                'mod "@sfo_grimhammer_3.pack";\nmod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            selected, source_kind, _ = discover_used_mods_path(
                game_root=game, appdata_root=appdata
            )
            self.assertEqual(selected, used.resolve())
            self.assertEqual(source_kind, "APPDATA_STEAM")

    def test_v01y_r2_prefers_game_root_when_supported_copies_agree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "steamapps" / "common" / "Total War WARHAMMER III"
            appdata = root / "AppData" / "Roaming"
            legacy = appdata / "The Creative Assembly" / "Warhammer3" / "scripts" / "used_mods.txt"
            game.mkdir(parents=True)
            legacy.parent.mkdir(parents=True)
            content = 'mod "@sfo_grimhammer_3.pack";\nmod "transcendence_shadow_probe.pack";\n'
            (game / "used_mods.txt").write_text(content, encoding="utf-8")
            legacy.write_text(content.upper(), encoding="utf-8")
            selected, source_kind, _ = discover_used_mods_path(
                game_root=game, appdata_root=appdata
            )
            self.assertEqual(selected, (game / "used_mods.txt").resolve())
            self.assertEqual(source_kind, "GAME_ROOT")

    def test_v01y_r2_rejects_conflicting_used_mods_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "steamapps" / "common" / "Total War WARHAMMER III"
            appdata = root / "AppData" / "Roaming"
            legacy = appdata / "The Creative Assembly" / "Warhammer3" / "scripts" / "used_mods.txt"
            game.mkdir(parents=True)
            legacy.parent.mkdir(parents=True)
            (game / "used_mods.txt").write_text(
                'mod "@sfo_grimhammer_3.pack";\nmod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            legacy.write_text(
                'mod "other.pack";\nmod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "conflicting used_mods.txt copies"):
                discover_used_mods_path(game_root=game, appdata_root=appdata)

    def test_v01y_sfo_environment_profile_binds_exact_two_pack_load_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            steamapps = root / "steamapps"
            game = steamapps / "common" / "Total War WARHAMMER III"
            data = game / "data"
            workshop = steamapps / "workshop" / "content" / "1142710" / "2792731173"
            data.mkdir(parents=True)
            workshop.mkdir(parents=True)
            (game / "Warhammer3.exe").write_bytes(b"fake-wh3-exe")
            probe = data / "transcendence_shadow_probe.pack"
            probe.write_bytes(b"read-only-probe")
            sfo = workshop / "@sfo_grimhammer_3.pack"
            sfo.write_bytes(b"exact-sfo-pack")
            used = root / "used_mods.txt"
            used.write_text(
                'mod "@sfo_grimhammer_3.pack";\nmod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            acf = steamapps / "workshop" / "appworkshop_1142710.acf"
            acf.parent.mkdir(parents=True, exist_ok=True)
            acf.write_text(
                '"AppWorkshop"\n{\n"WorkshopItemDetails"\n{\n"2792731173"\n{\n'
                '"manifest" "123456789"\n"timeupdated" "1785360000"\n"size" "14"\n'
                '}\n}\n}\n',
                encoding="utf-8",
            )
            private, public = build_environment_manifests(
                game_root=game,
                used_mods_path=used,
                shadow_pack_path=probe,
                steamapps_root=steamapps,
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                ironman=True,
                battle_realism=True,
                battlefield_limitations="ENABLED",
                faction="Karl Franz / Reikland",
            )
            self.assertEqual(public["profile_id"], "SFO_ONLY_PLUS_READ_ONLY_PROBE")
            self.assertEqual(public["active_mod_count"], 2)
            self.assertEqual(public["sfo"]["workshop_id"], "2792731173")
            self.assertEqual(public["sfo"]["manifest_id"], "123456789")
            self.assertEqual(public["active_mods"][0]["role"], "SFO_TOTAL_OVERHAUL")
            self.assertEqual(public["active_mods"][1]["role"], "READ_ONLY_TRANSCENDENCE_PROBE")
            self.assertNotIn("private_paths", public)
            self.assertIn("private_paths", private)
            self.assertEqual(parse_used_mods(used.read_text()), ["@sfo_grimhammer_3.pack", "transcendence_shadow_probe.pack"])
            self.assertEqual(parse_vdf(acf.read_text())["AppWorkshop"]["WorkshopItemDetails"]["2792731173"]["manifest"], "123456789")


    def test_v01y_r4_parses_current_wh3_launch_directive_format(self) -> None:
        entries = parse_used_mods(
            'add_working_directory "C:/Program Files (x86)/Steam/steamapps/workshop/content/1142710/2792731173";\n'
            'mod "@sfo_grimhammer_3.pack";\n'
            'add_working_directory "C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III/data";\n'
            'mod "transcendence_shadow_probe.pack";\n'
        )
        self.assertEqual(
            entries,
            ["@sfo_grimhammer_3.pack", "transcendence_shadow_probe.pack"],
        )

    def test_v01y_r5_watcher_status_is_bound_to_random_handshake_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "transcendence_runtime_log.txt"
            checkpoints = root / "checkpoints"
            stop = root / "stop.request"
            status = root / "status.json"
            manifest = root / "manifest.json"
            log.write_text(
                "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n",
                encoding="utf-8",
            )
            token = "owner-session-token-0123456789abcdef"
            outcome: dict[str, int] = {}

            def target() -> None:
                outcome["code"] = run_watcher(
                    log_path=log,
                    checkpoint_root=checkpoints,
                    stop_file=stop,
                    status_path=status,
                    manifest_path=manifest,
                    poll_seconds=0.01,
                    interval_seconds=0.05,
                    growth_bytes=1024,
                    handshake_token=token,
                )

            worker = threading.Thread(target=target, daemon=True)
            worker.start()
            for _ in range(200):
                if status.is_file():
                    state = json.loads(status.read_text(encoding="utf-8"))
                    if state.get("handshake_token") == token:
                        break
                time.sleep(0.01)
            else:
                self.fail("watcher did not publish the handshake-bound status")
            self.assertEqual(state["schema_version"], 2)
            self.assertEqual(state["handshake_token"], token)
            stop.touch()
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(outcome.get("code"), 0)
            final_state = json.loads(status.read_text(encoding="utf-8"))
            self.assertEqual(final_state["state"], "STOPPED")
            self.assertEqual(final_state["handshake_token"], token)

    def test_v01y_r5_preparer_stops_only_incomplete_orphan_watchers(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_sfo_combined_session.ps1").read_text(encoding="utf-8-sig")
        self.assertIn('Get-ChildItem -LiteralPath $ExistingSessionsRoot -Directory -Filter "sfo_combined_*"', prepare)
        self.assertIn('session_manifest_private.json', prepare)
        self.assertIn('(-not (Test-Path -LiteralPath $PriorManifest -PathType Leaf))', prepare)
        self.assertIn('@("WAITING_FOR_LOG", "WATCHING")', prepare)
        self.assertIn('New-Item -ItemType File -Force -Path $PriorStop', prepare)

    def test_v01y_r5_preparer_does_not_require_launcher_pid_equality(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_sfo_combined_session.ps1").read_text(encoding="utf-8-sig")
        watcher = (RUNTIME_ROOT / "tools/watch_combined_runtime_log.py").read_text(encoding="utf-8")
        self.assertIn("--handshake-token", prepare)
        self.assertIn("watcher_handshake_token", prepare)
        self.assertIn("RedirectStandardError", prepare)
        self.assertIn("launcher_exit_code", prepare)
        self.assertNotIn("[int]$WatcherState.pid -eq $Watcher.Id", prepare)
        self.assertIn('parser.add_argument("--handshake-token", required=True)', watcher)
        self.assertIn('"handshake_token": handshake_token', watcher)

    def test_v01y_r5_checkpoint_verifier_rejects_wrong_handshake_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "combined.txt"
            log.write_text(
                "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n",
                encoding="utf-8",
            )
            checkpoint_root = root / "checkpoints"
            record1 = take_checkpoint(
                data=log.read_bytes(),
                checkpoint_root=checkpoint_root,
                sequence=1,
                reason="FIRST_LOG_OBSERVATION",
            )
            record2 = take_checkpoint(
                data=log.read_bytes(),
                checkpoint_root=checkpoint_root,
                sequence=2,
                reason="STOP_REQUESTED",
            )
            correct = "a" * 64
            manifest = root / "checkpoint_manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "handshake_token": correct,
                        "state": "STOPPED",
                        "checkpoints": [record1, record2],
                        "violations": [],
                    }
                ),
                encoding="utf-8",
            )
            accepted = verify_checkpoint_chain(
                log_path=log,
                checkpoint_manifest_path=manifest,
                expected_handshake_token=correct,
            )
            self.assertEqual(accepted["status"], "OBSERVED")
            rejected = verify_checkpoint_chain(
                log_path=log,
                checkpoint_manifest_path=manifest,
                expected_handshake_token="b" * 64,
            )
            self.assertEqual(rejected["status"], "UNVERIFIED")
            self.assertFalse(rejected["checks"]["handshake_token_matches"])

    def test_v01y_r4_rejects_unsupported_launch_directive(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported used_mods.txt line"):
            parse_used_mods(
                'add_working_directory "C:/safe";\n'
                'load_order "other.pack";\n'
                'mod "transcendence_shadow_probe.pack";\n'
            )

    def test_v01y_r4_rejects_relative_or_traversing_working_directory(self) -> None:
        with self.assertRaisesRegex(ValueError, "absolute Windows path"):
            parse_used_mods(
                'add_working_directory "workshop/content/1142710/2792731173";\n'
                'mod "sfo.pack";\n'
            )
        with self.assertRaisesRegex(ValueError, "traversal"):
            parse_used_mods(
                'add_working_directory "C:/safe/../unsafe";\n'
                'mod "sfo.pack";\n'
            )

    def test_v01y_r4_environment_accepts_current_wh3_launch_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            steamapps = root / "steamapps"
            game = steamapps / "common" / "Total War WARHAMMER III"
            data = game / "data"
            workshop = steamapps / "workshop" / "content" / "1142710" / "2792731173"
            data.mkdir(parents=True)
            workshop.mkdir(parents=True)
            (game / "Warhammer3.exe").write_bytes(b"exe")
            probe = data / "transcendence_shadow_probe.pack"
            probe.write_bytes(b"probe")
            (workshop / "@sfo_grimhammer_3.pack").write_bytes(b"sfo")
            used = game / "used_mods.txt"
            used.write_text(
                f'add_working_directory "{workshop.as_posix()}";\n'
                'mod "@sfo_grimhammer_3.pack";\n'
                f'add_working_directory "{data.as_posix()}";\n'
                'mod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            # Convert the synthetic POSIX-root paths into the Windows-drive grammar
            # required by the launch-script parser without changing filesystem lookup.
            used.write_text(
                'add_working_directory "C:/Steam/workshop/content/1142710/2792731173";\n'
                'mod "@sfo_grimhammer_3.pack";\n'
                'add_working_directory "C:/Steam/common/Total War WARHAMMER III/data";\n'
                'mod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            _, public = build_environment_manifests(
                game_root=game,
                used_mods_path=used,
                shadow_pack_path=probe,
                steamapps_root=steamapps,
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                ironman=True,
                battle_realism=True,
                battlefield_limitations="ENABLED",
                faction="Karl Franz / Reikland",
            )
            self.assertEqual(public["profile_id"], "SFO_ONLY_PLUS_READ_ONLY_PROBE")
            self.assertEqual(public["active_mod_count"], 2)

    def test_v01y_r4_ready_confirmation_is_trimmed_and_case_insensitive(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_sfo_combined_session.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn(').Trim()', prepare)
        self.assertIn('$Confirmation -ine "READY"', prepare)
        self.assertNotIn('$Confirmation -cne "READY"', prepare)

    def test_v01y_r3_accepts_decorated_probe_alias_bound_to_exact_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            steamapps = root / "steamapps"
            game = steamapps / "common" / "Total War WARHAMMER III"
            data = game / "data"
            workshop = steamapps / "workshop" / "content" / "1142710" / "2792731173"
            data.mkdir(parents=True)
            workshop.mkdir(parents=True)
            (game / "Warhammer3.exe").write_bytes(b"exe")
            probe = data / "transcendence_shadow_probe.pack"
            probe.write_bytes(b"probe")
            (workshop / "@sfo_grimhammer_3.pack").write_bytes(b"sfo")
            used = root / "used_mods.txt"
            used.write_text(
                'mod "@sfo_grimhammer_3.pack";\nmod "@transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            _, public = build_environment_manifests(
                game_root=game,
                used_mods_path=used,
                shadow_pack_path=probe,
                steamapps_root=steamapps,
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                ironman=True,
                battle_realism=True,
                battlefield_limitations="ENABLED",
                faction="Karl Franz / Reikland",
            )
            self.assertEqual(public["profile_id"], "SFO_ONLY_PLUS_READ_ONLY_PROBE")
            self.assertEqual(public["probe_binding"]["status"], "DECORATED_ACTIVE_ALIAS")
            self.assertEqual(public["active_mods"][1]["canonical_pack_name"], "transcendence_shadow_probe.pack")
            self.assertEqual(public["active_mods"][1]["sha256"], hashlib.sha256(b"probe").hexdigest())

    def test_v01y_r3_defers_absent_prelaunch_probe_to_runtime_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            steamapps = root / "steamapps"
            game = steamapps / "common" / "Total War WARHAMMER III"
            data = game / "data"
            workshop = steamapps / "workshop" / "content" / "1142710" / "2792731173"
            data.mkdir(parents=True)
            workshop.mkdir(parents=True)
            (game / "Warhammer3.exe").write_bytes(b"exe")
            probe = data / "transcendence_shadow_probe.pack"
            probe.write_bytes(b"probe")
            (workshop / "@sfo_grimhammer_3.pack").write_bytes(b"sfo")
            used = root / "used_mods.txt"
            used.write_text('mod "@sfo_grimhammer_3.pack";\n', encoding="utf-8")
            _, public = build_environment_manifests(
                game_root=game,
                used_mods_path=used,
                shadow_pack_path=probe,
                steamapps_root=steamapps,
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                ironman=True,
                battle_realism=True,
                battlefield_limitations="ENABLED",
                faction="Karl Franz / Reikland",
            )
            self.assertEqual(public["profile_id"], "SFO_ONLY_PLUS_READ_ONLY_PROBE_RUNTIME_DEFERRED")
            self.assertEqual(public["active_mod_count"], 1)
            self.assertEqual(public["probe_binding"]["status"], "DEFERRED_RUNTIME_MARKER")
            self.assertTrue(public["probe_binding"]["runtime_confirmation_required"])
            self.assertEqual(public["expected_probe"]["pack_sha256"], hashlib.sha256(b"probe").hexdigest())

    def test_v01y_r3_rejects_duplicate_probe_aliases(self) -> None:
        with self.assertRaisesRegex(ValueError, "multiple Transcendence shadow probe entries"):
            classify_probe_entry([
                "transcendence_shadow_probe.pack",
                "@transcendence_shadow_probe.pack",
            ])

    def test_v01y_sfo_environment_rejects_extra_active_mod(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            steamapps = root / "steamapps"
            game = steamapps / "common" / "Total War WARHAMMER III"
            data = game / "data"
            workshop = steamapps / "workshop" / "content" / "1142710" / "2792731173"
            data.mkdir(parents=True)
            workshop.mkdir(parents=True)
            (game / "Warhammer3.exe").write_bytes(b"exe")
            probe = data / "transcendence_shadow_probe.pack"
            probe.write_bytes(b"probe")
            (workshop / "sfo.pack").write_bytes(b"sfo")
            used = root / "used_mods.txt"
            used.write_text(
                'mod "sfo.pack";\nmod "transcendence_shadow_probe.pack";\nmod "other.pack";\n',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                build_environment_manifests(
                    game_root=game,
                    used_mods_path=used,
                    shadow_pack_path=probe,
                    steamapps_root=steamapps,
                    campaign_difficulty="Legendary",
                    battle_difficulty="Very Hard",
                    ironman=True,
                    battle_realism=True,
                    battlefield_limitations="ENABLED",
                    faction="Karl Franz / Reikland",
                )

    def test_v01y_checkpoint_chain_proves_append_only_prefixes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            checkpoint_root = root / "checkpoints"
            pieces = [
                b"TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n",
                b"TRANS_BATTLE|1|RUNTIME_BEGIN|probe_kind=battle_replay_shadow|runtime=battle\n",
                b"TRANS_BATTLE|1|BATTLE_COMPLETE|time_ms=10\nTRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n",
            ]
            data = b""
            records = []
            for sequence, piece in enumerate(pieces, start=1):
                data += piece
                records.append(take_checkpoint(data=data, checkpoint_root=checkpoint_root, sequence=sequence, reason="TEST"))
            log = root / "transcendence_runtime_log.txt"
            log.write_bytes(data)
            manifest = root / "checkpoint_manifest.json"
            manifest.write_text(
                json.dumps({"schema_version": 1, "state": "STOPPED", "checkpoints": records, "violations": []}),
                encoding="utf-8",
            )
            verified = verify_checkpoint_chain(log_path=log, checkpoint_manifest_path=manifest)
            self.assertEqual(verified["status"], "OBSERVED")
            self.assertTrue(all(verified["checks"].values()))
            transitions = transition_analysis(log)
            self.assertTrue(transitions["all_battles_returned_to_campaign"])

            second = Path(records[1]["private_path"])
            second.write_bytes(b"not-a-prefix")
            rejected = verify_checkpoint_chain(log_path=log, checkpoint_manifest_path=manifest)
            self.assertEqual(rejected["status"], "UNVERIFIED")
            self.assertFalse(rejected["checks"]["checkpoint_records_valid"])

    def test_v01y_current_battle_probe_identifier_is_collected(self) -> None:
        collector = (RUNTIME_ROOT / "tools/collect_probe_logs.ps1").read_text(encoding="utf-8-sig")
        battle_source = (RUNTIME_ROOT / "source/script/battle/mod/transcendence_battle_probe.lua").read_text(encoding="utf-8")
        self.assertIn("battle_replay_shadow", battle_source)
        self.assertIn("(battle_shadow|battle_replay_shadow)", collector)

    def test_v01y_sfo_workflow_is_batched_checkpointed_and_private_safe(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_sfo_combined_session.ps1").read_text(encoding="utf-8-sig")
        collect = (RUNTIME_ROOT / "tools/collect_sfo_combined_session.ps1").read_text(encoding="utf-8-sig")
        rollback = (RUNTIME_ROOT / "tools/rollback_sfo_combined_session.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("watch_combined_runtime_log.py", prepare)
        self.assertIn("Return fully to the campaign map after each battle", prepare)
        self.assertIn("You do not need to save and quit after battles", prepare)
        self.assertIn("verify_sfo_combined_session.py", collect)
        self.assertIn("raw_log_included = $false", collect)
        self.assertIn("private_paths_included = $false", collect)
        self.assertIn("Remove the older generic upload ZIP", collect)
        self.assertNotIn("transcendence_runtime_log.txt\" },", collect)
        self.assertIn("SFO pack, active mod list, and saves were not modified", rollback)

    def test_v01y_r1_probe_install_invocation_binds_confirm_in_process(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_sfo_combined_session.ps1").read_text(encoding="utf-8-sig")
        self.assertIn('$PrepareLiveProbe = Join-Path $PSScriptRoot "prepare_live_probe.ps1"', prepare)
        self.assertIn("$PrepareLiveProbeParameters = @{", prepare)
        self.assertIn("Confirm = $false", prepare)
        self.assertIn("& $PrepareLiveProbe @PrepareLiveProbeParameters", prepare)
        self.assertNotIn('-File (Join-Path $PSScriptRoot "prepare_live_probe.ps1")', prepare)
        self.assertNotIn("-InstallShadow -Force -Confirm:$false", prepare)

    def test_v01y_r2_preparer_uses_multi_location_used_mods_discovery(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_sfo_combined_session.ps1").read_text(encoding="utf-8-sig")
        capture = (RUNTIME_ROOT / "tools/capture_sfo_environment.py").read_text(encoding="utf-8")
        self.assertIn("--appdata-root $env:APPDATA", prepare)
        self.assertNotIn('Join-Path $env:APPDATA "The Creative Assembly\\Warhammer3\\scripts\\used_mods.txt"', prepare)
        self.assertIn('("GAME_ROOT", game_root / "used_mods.txt")', capture)
        self.assertIn('"APPDATA_STEAM"', capture)
        self.assertIn('"APPDATA_EOS"', capture)
        self.assertIn('"APPDATA_GDK"', capture)
        self.assertIn("conflicting used_mods.txt copies were found", capture)


    def test_v01y_r3_preparer_discloses_runtime_deferred_probe_binding(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_sfo_combined_session.ps1").read_text(encoding="utf-8-sig")
        capture = (RUNTIME_ROOT / "tools/capture_sfo_environment.py").read_text(encoding="utf-8")
        verifier = (RUNTIME_ROOT / "tools/verify_sfo_combined_session.py").read_text(encoding="utf-8")
        self.assertIn("PRELAUNCH PROBE ENTRY DEFERRED", prepare)
        self.assertIn("DEFERRED_RUNTIME_MARKER", capture)
        self.assertIn("DECORATED_ACTIVE_ALIAS", capture)
        self.assertIn("runtime_probe_confirmed", verifier)

    def test_v01y_each_battle_requires_its_own_campaign_return(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "combined.txt"
            log.write_text(
                "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n"
                "TRANS_BATTLE|1|RUNTIME_BEGIN|probe_kind=battle_replay_shadow|runtime=battle\n"
                "TRANS_BATTLE|1|BATTLE_COMPLETE|time_ms=1000\n"
                "TRANS_BATTLE|1|RUNTIME_BEGIN|probe_kind=battle_replay_shadow|runtime=battle\n"
                "TRANS_BATTLE|1|BATTLE_COMPLETE|time_ms=1200\n"
                "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n",
                encoding="utf-8",
            )
            analysis = transition_analysis(log)
            self.assertEqual(analysis["battle_complete_followed_by_campaign_return"], [False, True])
            self.assertFalse(analysis["all_battles_returned_to_campaign"])

    def test_v01y_sfo_combined_verifier_accepts_one_complete_cycle_fixture(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/campaign_battle_5_turns_valid.txt").read_bytes()
        first_newline = source.find(b"\n")
        source = (
            source[: first_newline + 1]
            + b"TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n"
            + source[first_newline + 1 :]
        )
        battle_marker = b"TRANS_BATTLE|1|PACK_LOADED|"
        battle_start = source.find(battle_marker)
        battle_line_end = source.find(b"\n", battle_start)
        source = (
            source[: battle_line_end + 1]
            + b"TRANS_BATTLE|1|RUNTIME_BEGIN|probe_kind=battle_replay_shadow|runtime=battle\n"
            + source[battle_line_end + 1 :]
        )
        source += (
            b"TRANS_PROBE|1|PACK_LOADED|probe_kind=shadow|script=transcendence_shadow_probe|read_only=true\n"
            b"TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n"
        )
        profile = REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build = build_all(REPO_ROOT, root / "packs")
            expected = next(pack["pack_sha256"] for pack in build["packs"] if pack["probe_kind"] == "shadow")
            log = root / "transcendence_runtime_log.txt"
            log.write_bytes(source)
            campaign_summary = summarize(parse_logs([log]))
            battle_summary = summarize_battle(parse_battle_logs([log]))
            campaign_report = run_shadow_campaign([log], profile)
            battle_report = build_battle_report(parse_battle_logs([log]))
            paths = {name: root / f"{name}.json" for name in ("campaign_summary", "battle_summary", "campaign_report", "battle_report")}
            for name, payload in (("campaign_summary", campaign_summary), ("battle_summary", battle_summary), ("campaign_report", campaign_report), ("battle_report", battle_report)):
                paths[name].write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            evidence_manifest = root / "evidence_manifest.json"
            evidence_manifest.write_text(json.dumps({
                "schema_version": 4,
                "collected_at_utc": "2026-07-30T00:00:00Z",
                "evidence_phase": "campaign_battle",
                "loaded_probe_kinds": ["shadow"],
                "expected_loaded_probe_kinds": ["shadow"],
                "unexpected_loaded_probe_kinds": [],
                "battle_probe_loaded": True,
                "combined_session_manifest": {
                    "sha256": "9" * 64,
                    "prepared_at_utc": "2026-07-29T23:59:00Z",
                    "staged_shadow_pack_sha256": expected,
                    "installed_shadow_pack_sha256": expected,
                },
                "logs": [{"sha256": hashlib.sha256(source).hexdigest()}],
                "installed_probe_packs": [{"name": "transcendence_shadow_probe.pack", "installed_sha256": expected, "staged_sha256": expected, "matches_staged": True, "loaded_in_log": True}],
            }), encoding="utf-8")
            env = root / "environment.json"
            env.write_text(json.dumps({
                "schema_version": 1,
                "profile_id": "SFO_ONLY_PLUS_READ_ONLY_PROBE",
                "game": {"executable_sha256": "1" * 64},
                "sfo": {"workshop_id": "2792731173", "pack_name": "sfo.pack", "pack_sha256": "2" * 64, "manifest_id": "3", "time_updated_unix": 1},
                "active_mods": [
                    {"load_order_index": 0, "name": "sfo.pack", "sha256": "2" * 64, "role": "SFO_TOTAL_OVERHAUL"},
                    {"load_order_index": 1, "name": "transcendence_shadow_probe.pack", "sha256": expected, "role": "READ_ONLY_TRANSCENDENCE_PROBE"},
                ],
                "settings": {"campaign_difficulty": "Legendary", "battle_difficulty": "Very Hard", "ironman": True, "battle_realism": True, "battlefield_limitations": "ENABLED", "faction": "Karl Franz / Reikland"},
            }), encoding="utf-8")
            checkpoint_root = root / "checkpoints"
            split = source.find(b"TRANS_BATTLE|1|RUNTIME_BEGIN")
            first = take_checkpoint(data=source[:split], checkpoint_root=checkpoint_root, sequence=1, reason="CAMPAIGN")
            second = take_checkpoint(data=source, checkpoint_root=checkpoint_root, sequence=2, reason="FINAL")
            checkpoint_manifest = root / "checkpoint_manifest.json"
            checkpoint_manifest.write_text(json.dumps({"schema_version": 1, "state": "STOPPED", "checkpoints": [first, second], "violations": []}), encoding="utf-8")
            result = build_sfo_combined_verification(
                log_path=log,
                campaign_summary_path=paths["campaign_summary"],
                battle_summary_path=paths["battle_summary"],
                evidence_manifest_path=evidence_manifest,
                campaign_report_path=paths["campaign_report"],
                battle_report_path=paths["battle_report"],
                environment_profile_path=env,
                checkpoint_manifest_path=checkpoint_manifest,
                expected_pack_sha256=expected,
                minimum_turns=5,
                minimum_completed_battles=1,
            )
            self.assertEqual(result["status"], "OBSERVED_SFO_COMBINED_CONTINUITY")
            self.assertTrue(all(result["environment_checks"].values()))
            self.assertTrue(all(result["transition_checks"].values()))

            deferred_environment = {
                "schema_version": 2,
                "profile_id": "SFO_ONLY_PLUS_READ_ONLY_PROBE_RUNTIME_DEFERRED",
                "game": {"executable_sha256": "1" * 64},
                "sfo": {"workshop_id": "2792731173", "pack_name": "sfo.pack", "pack_sha256": "2" * 64, "manifest_id": "3", "time_updated_unix": 1},
                "active_mods": [
                    {"load_order_index": 0, "name": "sfo.pack", "sha256": "2" * 64, "role": "SFO_TOTAL_OVERHAUL"},
                ],
                "probe_binding": {
                    "status": "DEFERRED_RUNTIME_MARKER",
                    "launcher_entry": None,
                    "runtime_confirmation_required": True,
                },
                "expected_probe": {
                    "canonical_pack_name": "transcendence_shadow_probe.pack",
                    "pack_sha256": expected,
                },
                "settings": {"campaign_difficulty": "Legendary", "battle_difficulty": "Very Hard", "ironman": True, "battle_realism": True, "battlefield_limitations": "ENABLED", "faction": "Karl Franz / Reikland"},
            }
            env.write_text(json.dumps(deferred_environment), encoding="utf-8")
            deferred_result = build_sfo_combined_verification(
                log_path=log,
                campaign_summary_path=paths["campaign_summary"],
                battle_summary_path=paths["battle_summary"],
                evidence_manifest_path=evidence_manifest,
                campaign_report_path=paths["campaign_report"],
                battle_report_path=paths["battle_report"],
                environment_profile_path=env,
                checkpoint_manifest_path=checkpoint_manifest,
                expected_pack_sha256=expected,
                minimum_turns=5,
                minimum_completed_battles=1,
            )
            self.assertEqual(deferred_result["status"], "OBSERVED_SFO_COMBINED_CONTINUITY")
            self.assertTrue(all(deferred_result["environment_checks"].values()))
            self.assertTrue(deferred_result["profile_summary"]["runtime_probe_confirmed"])


    def test_v01z_schema2_transition_markers_are_counted(self) -> None:
        payload = (
            "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n"
            "TRANS_BATTLE|2|RUNTIME_BEGIN|probe_kind=battle_replay_shadow|runtime=battle\n"
            "TRANS_BATTLE|2|BATTLE_COMPLETE|time_ms=1000\n"
            "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign\n"
        ).encode("utf-8")
        summary = marker_summary(payload)
        self.assertEqual(summary["campaign_runtime_begin"], 2)
        self.assertEqual(summary["battle_runtime_begin"], 1)
        self.assertEqual(summary["battle_complete"], 1)
        self.assertEqual(
            summary["transition_events"],
            [
                "CAMPAIGN_RUNTIME_BEGIN",
                "BATTLE_RUNTIME_BEGIN",
                "BATTLE_COMPLETE",
                "CAMPAIGN_RUNTIME_BEGIN",
            ],
        )

    def test_v01z_transition_analysis_accepts_three_schema2_cycles(self) -> None:
        lines = ["TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign"]
        for _ in range(3):
            lines.extend(
                [
                    "TRANS_BATTLE|2|RUNTIME_BEGIN|probe_kind=battle_replay_shadow|runtime=battle",
                    "TRANS_BATTLE|2|BATTLE_COMPLETE|time_ms=1000",
                    "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign",
                ]
            )
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "combined.txt"
            log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = transition_analysis(log)
        self.assertEqual(result["battle_runtime_begin"], 3)
        self.assertEqual(result["battle_complete"], 3)
        self.assertEqual(result["battle_complete_followed_by_campaign_return"], [True, True, True])
        self.assertTrue(result["all_battles_returned_to_campaign"])

    def test_v01z_atomic_control_json_is_nonzero_and_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "watcher_status.json"
            payload = {"schema_version": 2, "state": "STOPPED", "violations": []}
            for _ in range(20):
                write_control_json(target, payload)
                blob = target.read_bytes()
                self.assertTrue(blob)
                self.assertTrue(any(blob))
                self.assertEqual(json.loads(blob.decode("utf-8")), payload)
            self.assertFalse(list(target.parent.glob("*.tmp")))

    def test_v01z_collector_uses_checkpoint_manifest_as_authority(self) -> None:
        collect = (RUNTIME_ROOT / "tools/collect_sfo_combined_session.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("$Session.checkpoint_manifest", collect)
        self.assertIn("WATCHER_STATUS_UNREADABLE_IGNORED_CHECKPOINT_MANIFEST_AUTHORITATIVE", collect)
        self.assertIn("watcher_handshake_token", collect)
        mandatory_block = collect.split("foreach ($Path in @(", 1)[1].split("))", 1)[0]
        self.assertNotIn("watcher_status", mandatory_block)
        self.assertIn("build_public_evidence_zip.py", collect)
        self.assertNotIn("Compress-Archive -Path (Join-Path $Bundle", collect)

    def test_v01z_prepare_uses_checkpoint_manifest_for_readiness(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_sfo_combined_session.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("The checkpoint manifest is authoritative", prepare)
        self.assertIn("$CheckpointManifest", prepare)
        self.assertIn("[int]$WatcherState.pid", prepare)
        self.assertNotIn("Get-Content -LiteralPath $WatcherStatus -Raw | ConvertFrom-Json", prepare)
        self.assertIn("TRANS_BATTLE|2|RUNTIME_BEGIN", prepare)

    def test_v01z_public_zip_is_deterministic_and_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / "bundle"
            bundle.mkdir()
            member = bundle / "result.json"
            member.write_text('{"status":"OBSERVED"}\n', encoding="utf-8")
            manifest = bundle / "export_manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "raw_log_included": False,
                        "private_paths_included": False,
                        "files": [
                            {
                                "name": member.name,
                                "size_bytes": member.stat().st_size,
                                "sha256": hashlib.sha256(member.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            first = root / "first.zip"
            second = root / "second.zip"
            result = build_public_evidence_zip(bundle, first, manifest)
            build_public_evidence_zip(bundle, second, manifest)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(result["status"], "VERIFIED_PUBLIC_EVIDENCE_ZIP")
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.testzip(), None)
                self.assertEqual(sorted(archive.namelist()), ["export_manifest.json", "result.json"])

    def test_v01z_r1_public_zip_fsync_uses_writable_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / "bundle"
            bundle.mkdir()
            member = bundle / "result.json"
            member.write_text('{"status":"OBSERVED"}\n', encoding="utf-8")
            manifest = bundle / "export_manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "raw_log_included": False,
                        "private_paths_included": False,
                        "files": [
                            {
                                "name": member.name,
                                "size_bytes": member.stat().st_size,
                                "sha256": hashlib.sha256(member.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            real_fsync = os.fsync
            checked = {"writable": False}

            def require_writable_descriptor(file_descriptor: int) -> None:
                # A zero-length write changes no bytes but fails with EBADF when
                # the descriptor was opened read-only, including on Windows.
                os.write(file_descriptor, b"")
                checked["writable"] = True
                real_fsync(file_descriptor)

            with mock.patch(
                "build_public_evidence_zip.os.fsync",
                side_effect=require_writable_descriptor,
            ):
                result = build_public_evidence_zip(
                    bundle, root / "windows-compatible.zip", manifest
                )

            self.assertTrue(checked["writable"])
            self.assertEqual(result["status"], "VERIFIED_PUBLIC_EVIDENCE_ZIP")

    def test_v01z_public_zip_rejects_zero_filled_member(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / "bundle"
            bundle.mkdir()
            member = bundle / "result.json"
            member.write_bytes(b"\x00" * 32)
            manifest = bundle / "export_manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "raw_log_included": False,
                        "private_paths_included": False,
                        "files": [
                            {
                                "name": member.name,
                                "size_bytes": 32,
                                "sha256": hashlib.sha256(member.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(PublicEvidenceZipError):
                build_public_evidence_zip(bundle, root / "bad.zip", manifest)

    def test_v01z_observed_sfo_baseline_is_frozen_and_public_safe(self) -> None:
        fixture_path = RUNTIME_ROOT / "fixtures/sfo_observed_combined_v0.1Z.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        validated = validate_sfo_observed_baseline(fixture)
        self.assertEqual(validated["campaign"]["turn_count"], 6)
        self.assertEqual(validated["continuity"]["completed_battle_count"], 3)
        self.assertEqual(validated["continuity"]["checkpoint_count"], 130)
        self.assertEqual(validated["aggregate_metrics"]["battle_command_events"], 683)
        matrix = build_sfo_observed_capability_matrix(validated)
        self.assertEqual(matrix["capabilities"]["sfo_campaign_observation"], "OBSERVED")
        self.assertEqual(matrix["capabilities"]["order_acknowledgement"], "UNOBSERVED")
        self.assertEqual(matrix["capabilities"]["tactical_superiority"], "UNPROVEN")

    def test_v01z_observed_sfo_baseline_rejects_promotion_or_metric_tamper(self) -> None:
        fixture = json.loads(
            (RUNTIME_ROOT / "fixtures/sfo_observed_combined_v0.1Z.json").read_text(encoding="utf-8")
        )
        fixture["aggregate_metrics"]["battle_command_events"] = 684
        with self.assertRaises(SfoObservedBaselineError):
            validate_sfo_observed_baseline(fixture)

    def test_v01z_replay_cohort_binds_exact_save_and_two_replays(self) -> None:
        cohort = json.loads(
            (RUNTIME_ROOT / "fixtures/sfo_replay_deep_dive_cohort_v0.1Z.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(cohort["shared_campaign"]["persistent_session_id"], "239641785461549")
        self.assertEqual([item["battle_name"] for item in cohort["replays"]], [
            "Battle of Ubersreik",
            "Battle of Marienburg",
        ])
        self.assertEqual(
            [item["sha256"] for item in cohort["replays"]],
            [
                "e96c160ce8ca83463407d2008c676da1bcad2a0e0d2ec1f03b475097b4c4ea89",
                "844d2efc4434c18d09d5958fc5cf9c60bf21201d5ca2af2e254077666ba0c902",
            ],
        )
        self.assertFalse(cohort["capture_contract"]["replay_binary_committed"])
        self.assertFalse(cohort["capture_contract"]["raw_log_committed"])

    def test_v02a_visual_alignment_is_hash_bound_and_public_safe(self) -> None:
        path = (
            REPO_ROOT
            / "synthetic_lab"
            / "corpora"
            / "sfo_reikland_dual_replay_visual_alignment_v0.2A.json"
        )
        alignment = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(alignment["authority"], "NO_ORDERS")
        self.assertEqual(
            alignment["result_digest"],
            "ff763fa5ade5de8bae7f465a54017e07bd7263c09765a0da9c1dde0d3ac32783",
        )
        videos = {
            video["artifact_id"]: video
            for battle in alignment["battles"]
            for video in battle["video_artifacts"]
        }
        self.assertEqual(
            videos["ubersreik_full_recording"]["sha256"],
            "e3a48d3f74ebd2aca9f477f2dcc5957a447e28c03002189771ed9d6704275ba1",
        )
        self.assertEqual(
            videos["marienburg_segment_1"]["sha256"],
            "c7482eea91bed31322355586c373160f6cbbc89005659412565b0768f290fee6",
        )
        self.assertEqual(
            videos["marienburg_segment_2"]["sha256"],
            "67d7cdb053d281f0a23e033d561508d880e034713652f206a0f2eedbaf952997",
        )
        self.assertTrue(all(video["committed"] is False for video in videos.values()))
        serialized = json.dumps(alignment, sort_keys=True).lower()
        self.assertNotIn("c:\\users", serialized)
        self.assertNotIn('"video_path"', serialized)
        self.assertNotIn('"video_bytes"', serialized)
        self.assertNotIn('"replay_bytes"', serialized)

    def test_v02a_dense_replay_corpora_preserve_observation_authority(self) -> None:
        expected = {
            "ubersreik": {
                "replay": "e96c160ce8ca83463407d2008c676da1bcad2a0e0d2ec1f03b475097b4c4ea89",
                "log": "8ae4ee9736283755b0af4777a2738daf66e7fed84502c703d637bd6b8cd2b08f",
                "digest": "a93340421c1c7a0623f21381d6d83de209299276e93c418ed193adb65ca8a5ec",
            },
            "marienburg": {
                "replay": "844d2efc4434c18d09d5958fc5cf9c60bf21201d5ca2af2e254077666ba0c902",
                "log": "e78dbdff7322be33407bb03330d34df803e1d8dc213bafc6c9d46df66b60ceb4",
                "digest": "058f10ad125b554d3d63a0c1f768ed58ef8a9818473c2aebf515ac1458f957c0",
            },
        }
        for battle_id, identities in expected.items():
            corpus_path = (
                REPO_ROOT
                / "synthetic_lab"
                / "corpora"
                / f"sfo_{battle_id}_observed_dense_v0.2A.json"
            )
            corpus = validate_observed_battle_corpus(
                json.loads(corpus_path.read_text(encoding="utf-8"))
            )
            self.assertEqual(corpus["evidence_status"], "OBSERVED")
            self.assertEqual(corpus["result_digest"], identities["digest"])
            self.assertEqual(corpus["source"]["replay_sha256"], identities["replay"])
            self.assertEqual(
                corpus["source"]["raw_trans_battle_log_sha256"], identities["log"]
            )
            self.assertFalse(corpus["source"]["raw_log_committed"])
            self.assertFalse(corpus["source"]["raw_replay_committed"])
            joined = " ".join(corpus["forbidden_inferences"]).lower()
            self.assertIn("prove command acceptance", joined)
            self.assertIn("optimal tactical policy", joined)
            self.assertIn("general tactical-ai quality", joined)

    def test_v01z_replay_probe_alias_classifier_is_exact(self) -> None:
        self.assertEqual(
            classify_replay_probe_entry(["sfo.pack", "@transcendence_battle_replay_probe.pack"]),
            "@transcendence_battle_replay_probe.pack",
        )
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            classify_replay_probe_entry(["sfo.pack"])
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            classify_replay_probe_entry(
                ["sfo.pack", "transcendence_battle_replay_probe.pack", "@transcendence_battle_replay_probe.pack"]
            )

    def test_v01z_sfo_replay_mod_state_requires_exact_two_pack_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            steamapps = root / "steamapps"
            game = steamapps / "common" / "Total War WARHAMMER III"
            data = game / "data"
            workshop = steamapps / "workshop" / "content" / "1142710" / "2792731173"
            appdata = root / "appdata"
            data.mkdir(parents=True)
            workshop.mkdir(parents=True)
            appdata.mkdir()
            probe = data / "transcendence_battle_replay_probe.pack"
            sfo = workshop / "sfo_grimhammer_3_main.pack"
            probe.write_bytes(b"probe")
            sfo.write_bytes(b"sfo")
            (game / "used_mods.txt").write_text(
                'add_working_directory "C:/Steam/workshop/content/1142710/2792731173";\n'
                'mod "sfo_grimhammer_3_main.pack";\n'
                'add_working_directory "C:/Steam/common/Total War WARHAMMER III/data";\n'
                'mod "transcendence_battle_replay_probe.pack";\n',
                encoding="utf-8",
            )
            result = validate_sfo_replay_mod_state(
                game_root=game,
                appdata_root=appdata,
                installed_pack=probe,
                expected_pack_sha256=hashlib.sha256(b"probe").hexdigest(),
                expected_sfo_pack_sha256=hashlib.sha256(b"sfo").hexdigest(),
            )
            self.assertEqual(result["profile_id"], "SFO_PLUS_READ_ONLY_BATTLE_REPLAY_PROBE")
            self.assertEqual(result["active_mod_count"], 2)
            self.assertFalse(result["authority"]["orders_emitted"])

    def test_v01z_dense_verifier_accepts_arbitrary_exact_replay_identity(self) -> None:
        events = parse_battle_logs([RUNTIME_ROOT / "fixtures/battle_log_dense_v2_valid.txt"])
        summary = summarize_battle(events)
        report = build_battle_report(events)
        replay_sha = "d" * 64
        pack_sha = "e" * 64
        manifest = {
            "target": {"replay_sha256": replay_sha},
            "installed_pack_sha256": pack_sha,
            "battle_complete_marker_observed": True,
            "captured_log_size_bytes": 1000,
        }
        result = build_dense_replay_verification(
            summary=summary,
            report=report,
            manifest=manifest,
            expected_pack_sha256=pack_sha,
            expected_replay_sha256=replay_sha,
            battle_identity="Synthetic SFO Replay",
        )
        self.assertTrue(result["checks"]["exact_replay_verified"])
        self.assertEqual(result["target"]["battle_identity"], "Synthetic SFO Replay")

    def test_v01z_replay_private_zip_is_deterministic_and_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "log.txt").write_text("TRANS_BATTLE|2|BATTLE_COMPLETE|\n", encoding="utf-8")
            (bundle / "report.json").write_text('{"status":"OBSERVED"}\n', encoding="utf-8")
            first = root / "first.zip"
            second = root / "second.zip"
            build_private_replay_zip(bundle, first)
            build_private_replay_zip(bundle, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.testzip(), None)
                self.assertTrue(all(any(archive.read(name)) for name in archive.namelist()))

    def test_v01z_replay_workflow_is_read_only_and_rollback_is_in_process(self) -> None:
        capture = (RUNTIME_ROOT / "tools/capture_sfo_replay_deep_dive.py").read_text(encoding="utf-8")
        prepare = (RUNTIME_ROOT / "tools/prepare_sfo_replay_deep_dive.ps1").read_text(
            encoding="utf-8-sig"
        )
        rollback = (RUNTIME_ROOT / "tools/rollback_sfo_replay_deep_dive.ps1").read_text(
            encoding="utf-8-sig"
        )
        combined_rollback = (RUNTIME_ROOT / "tools/rollback_sfo_combined_session.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn('"orders_emitted": False', capture)
        self.assertIn('"save_modified": False', capture)
        self.assertNotIn("unitcontroller:", capture.lower())
        self.assertIn("InstallBattleReplay = $true", prepare)
        self.assertNotIn("powershell.exe", rollback)
        self.assertNotIn("powershell.exe", combined_rollback)
        self.assertIn("@RollbackParameters", combined_rollback)

    def test_v02b_chaos_defeat_contract_binds_exact_private_sources(self) -> None:
        contract = json.loads(
            (RUNTIME_ROOT / "fixtures" / "sfo_chaos_defeat_replay_contract_v0.2B.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["status"], "READY_FOR_OWNER_READ_ONLY_REPLAY_CAPTURE")
        self.assertEqual(contract["authority"], "NO_ORDERS")
        self.assertEqual(
            contract["replay"]["sha256"],
            "28d780d02f2af07fe16fe4a24a27cd37f41bdb870d485f11949d5ed63f838cb5",
        )
        self.assertEqual(contract["replay"]["size_bytes"], 86067)
        self.assertEqual(
            contract["visual_binding"]["recording_sha256"],
            "6e008c378a8e4273ca7d2c8101ca69279839a5c21dbaf749fb5e666adde56155",
        )
        self.assertFalse(contract["replay"]["binary_committed"])
        self.assertFalse(contract["visual_binding"]["recording_committed"])
        self.assertFalse(contract["capture"]["replay_binary_exported"])
        signed = dict(contract)
        claimed = signed.pop("result_digest")
        canonical = json.dumps(signed, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertEqual(claimed, hashlib.sha256(canonical).hexdigest())
        serialized = json.dumps(contract, sort_keys=True).lower()
        self.assertNotIn("c:\\users", serialized)
        self.assertNotIn('"replay_bytes"', serialized)
        self.assertNotIn('"video_bytes"', serialized)

    def test_v02b_battle_observer_classifier_accepts_exact_script_equivalent_pack(self) -> None:
        dedicated = classify_battle_observer_entry([
            "sfo_grimhammer_3_main.pack",
            "transcendence_battle_replay_probe.pack",
        ])
        self.assertEqual(dedicated["container_kind"], "DEDICATED_REPLAY_PACK")
        equivalent = classify_battle_observer_entry([
            "sfo_grimhammer_3_main.pack",
            "@transcendence_shadow_probe.pack",
        ])
        self.assertEqual(equivalent["container_kind"], "SCRIPT_EQUIVALENT_SHADOW_PACK")
        with self.assertRaisesRegex(RuntimeError, "exactly one accepted"):
            classify_battle_observer_entry([
                "sfo_grimhammer_3_main.pack",
                "transcendence_battle_replay_probe.pack",
                "transcendence_shadow_probe.pack",
            ])

    def test_v02b_sfo_replay_mod_state_accepts_exact_shadow_container_only_by_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            steamapps = root / "steamapps"
            game = steamapps / "common" / "Total War WARHAMMER III"
            data = game / "data"
            workshop = steamapps / "workshop" / "content" / "1142710" / "2792731173"
            appdata = root / "appdata"
            data.mkdir(parents=True)
            workshop.mkdir(parents=True)
            appdata.mkdir()
            replay_probe = data / "transcendence_battle_replay_probe.pack"
            shadow_probe = data / "transcendence_shadow_probe.pack"
            sfo = workshop / "sfo_grimhammer_3_main.pack"
            replay_probe.write_bytes(b"replay-probe")
            shadow_probe.write_bytes(b"shadow-probe")
            sfo.write_bytes(b"sfo")
            (game / "used_mods.txt").write_text(
                'add_working_directory "C:/Steam/workshop/content/1142710/2792731173";\n'
                'mod "sfo_grimhammer_3_main.pack";\n'
                'add_working_directory "C:/Steam/common/Total War WARHAMMER III/data";\n'
                'mod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            result = validate_sfo_replay_mod_state(
                game_root=game,
                appdata_root=appdata,
                installed_pack=replay_probe,
                expected_pack_sha256=hashlib.sha256(b"replay-probe").hexdigest(),
                expected_equivalent_pack_sha256=hashlib.sha256(b"shadow-probe").hexdigest(),
                expected_sfo_pack_sha256=hashlib.sha256(b"sfo").hexdigest(),
            )
            self.assertEqual(
                result["profile_id"],
                "SFO_PLUS_READ_ONLY_SCRIPT_EQUIVALENT_BATTLE_OBSERVER",
            )
            observer = result["active_mods"][1]
            self.assertEqual(observer["container_kind"], "SCRIPT_EQUIVALENT_SHADOW_PACK")
            self.assertEqual(
                observer["shared_battle_script_sha256"],
                "86e18ec655c4a45a4a062d1dae7d10e6fd9a1cb77af5557757fbca9ed896562e",
            )
            shadow_probe.write_bytes(b"tampered")
            with self.assertRaisesRegex(RuntimeError, "active battle observer pack hash changed"):
                validate_sfo_replay_mod_state(
                    game_root=game,
                    appdata_root=appdata,
                    installed_pack=replay_probe,
                    expected_pack_sha256=hashlib.sha256(b"replay-probe").hexdigest(),
                    expected_equivalent_pack_sha256=hashlib.sha256(b"shadow-probe").hexdigest(),
                    expected_sfo_pack_sha256=hashlib.sha256(b"sfo").hexdigest(),
                )
            shadow_probe.write_bytes(b"shadow-probe")
            (game / "used_mods.txt").write_text(
                'add_working_directory "C:/Steam/common/Total War WARHAMMER III/data";\n'
                'mod "transcendence_shadow_probe.pack";\n'
                'add_working_directory "C:/Steam/workshop/content/1142710/2792731173";\n'
                'mod "sfo_grimhammer_3_main.pack";\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "exact load order"):
                validate_sfo_replay_mod_state(
                    game_root=game,
                    appdata_root=appdata,
                    installed_pack=replay_probe,
                    expected_pack_sha256=hashlib.sha256(b"replay-probe").hexdigest(),
                    expected_equivalent_pack_sha256=hashlib.sha256(b"shadow-probe").hexdigest(),
                    expected_sfo_pack_sha256=hashlib.sha256(b"sfo").hexdigest(),
                )

    def test_v02b_chaos_defeat_runner_is_exact_hash_bound_and_read_only(self) -> None:
        runner = (RUNTIME_ROOT / "tools" / "run_sfo_chaos_defeat_deep_dive.ps1").read_text(encoding="utf-8-sig")
        prepare = (RUNTIME_ROOT / "tools" / "prepare_sfo_chaos_defeat_deep_dive.ps1").read_text(encoding="utf-8-sig")
        capture = (RUNTIME_ROOT / "tools" / "capture_sfo_replay_deep_dive.py").read_text(encoding="utf-8")
        self.assertIn("sfo_chaos_defeat_replay_contract_v0.2B.json", runner)
        self.assertIn("--expected-replay-sha256", runner)
        self.assertIn("--source-contract-digest", runner)
        self.assertIn("--corpus-version", runner)
        self.assertIn("prepare_sfo_replay_deep_dive.ps1", prepare)
        self.assertIn("SCRIPT_EQUIVALENT_SHADOW_PACK", capture)
        self.assertIn('"orders_emitted": False', capture)
        self.assertNotIn("unitcontroller:", capture.lower())

    def test_v02c_incomplete_battle_report_never_observes_terminal_outcome(self) -> None:
        source = (RUNTIME_ROOT / "fixtures" / "battle_log_dense_v2_valid.txt").read_text(encoding="utf-8")
        source = "\n".join(
            line for line in source.splitlines() if "|BATTLE_COMPLETE|" not in line
        ) + "\n"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "incomplete.txt"
            path.write_text(source, encoding="utf-8")
            report = build_battle_report(parse_battle_logs([path]))
        battle = report["battle_reports"][0]
        self.assertFalse(battle["complete"])
        self.assertEqual(report["completed_battle_count"], 0)
        self.assertEqual(
            battle["interpretation_status"]["terminal_outcome"],
            "UNVERIFIED_INCOMPLETE_SESSION",
        )

    def test_v02c_complete_battle_report_preserves_observed_terminal_outcome(self) -> None:
        report = build_battle_report(
            parse_battle_logs([RUNTIME_ROOT / "fixtures" / "battle_log_dense_v2_valid.txt"])
        )
        battle = report["battle_reports"][0]
        self.assertTrue(battle["complete"])
        self.assertEqual(battle["interpretation_status"]["terminal_outcome"], "OBSERVED")

    def test_v02c_post_exit_log_stabilization_preserves_late_append_without_completion_promotion(self) -> None:
        with mock.patch.object(
            replay_capture,
            "read_shared",
            side_effect=[b"TRANS_BATTLE|2|PACK_LOADED|", b"TRANS_BATTLE|2|PACK_LOADED|late", b"TRANS_BATTLE|2|PACK_LOADED|late"],
        ):
            payload, stable_reads, stabilized = replay_capture.stabilize_runtime_log(
                Path("unused"), poll_seconds=0.0, timeout_seconds=0.1
            )
        self.assertTrue(stabilized)
        self.assertEqual(stable_reads, 2)
        self.assertTrue(payload.endswith(b"late"))
        self.assertNotIn(replay_capture.COMPLETE_MARKER, payload)

    def test_v02c_chaos_replay_public_fixtures_are_exact_and_private_safe(self) -> None:
        capture_path = RUNTIME_ROOT / "fixtures" / "sfo_chaos_replay_stream_capture_v0.2C.json"
        units_path = RUNTIME_ROOT / "fixtures" / "sfo_chaos_replay_unit_findings_v0.2C.json"
        capture = json.loads(capture_path.read_text(encoding="utf-8"))
        units = json.loads(units_path.read_text(encoding="utf-8"))
        self.assertEqual(capture["result_digest"], "3febf48a92ce7309d912634b1540d29e1051a30835622b847b8da360aa6e74dc")
        self.assertEqual(units["result_digest"], "12609e324eec28eed50ee2d79ca3e42d3f71787597d2ce28362257bbb40c7ae0")
        self.assertEqual(hashlib.sha256(units_path.read_bytes()).hexdigest(), "4ae757f2258eb3d983c7953167dbcec3ff57e292316d146fb350b6e13d8b43c0")
        serialized = json.dumps({"capture": capture, "units": units}, sort_keys=True).lower()
        self.assertNotIn("c:\\users", serialized)
        self.assertNotIn("/mnt/", serialized)
        self.assertNotIn('"raw_log"', serialized)
        self.assertNotIn('"replay_bytes"', serialized)

    def test_v02c_capture_process_exit_is_not_battle_completion(self) -> None:
        source = (RUNTIME_ROOT / "tools" / "capture_sfo_replay_deep_dive.py").read_text(encoding="utf-8")
        self.assertIn('"process_exit_promoted_to_battle_complete": False', source)
        self.assertIn("stabilize_runtime_log", source)
        self.assertIn("saw_complete = COMPLETE_MARKER in latest", source)
        self.assertNotIn("saw_complete = process_exit_observed", source)



    def test_v02d_policy_module_has_no_runtime_or_order_adapter(self) -> None:
        import ast
        source_path = REPO_ROOT / "synthetic_lab" / "transcendence_lab" / "tactical_policy.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_import_roots = {"subprocess", "socket", "ctypes", "winreg"}
        imported_roots = set()
        executable_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                executable_names.add(node.name.lower())
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    executable_names.add(func.id.lower())
                elif isinstance(func, ast.Attribute):
                    executable_names.add(func.attr.lower())
        self.assertFalse(imported_roots & forbidden_import_roots)
        self.assertFalse({"issue_order", "execute_order", "send_order", "apply_order"} & executable_names)
        self.assertNotIn("runtime_probe", imported_roots)
        self.assertIn('"project_orders_emitted": False', source)
        self.assertIn('"application_authority": "PROHIBITED"', source)

    def test_v02d_runtime_identity_alias_is_explicit_provenance_not_rewrite(self) -> None:
        policy = json.loads(
            (REPO_ROOT / "research" / "runtime_evidence" / "REIKLAND_CROSS_CORPUS_TACTICAL_POLICY_ENVELOPE_v0.2D.json").read_text(encoding="utf-8")
        )
        boundary = policy["identity_provenance_boundary"]
        self.assertTrue(boundary["silent_identity_reconciliation_prohibited"])
        self.assertEqual(boundary["known_runtime_identity_alias_cohort"], ["ubersreik", "marienburg", "chaos"])
        by_id = {item["battle_id"]: item for item in policy["battle_summaries"]}
        for battle_id in boundary["known_runtime_identity_alias_cohort"]:
            identity = by_id[battle_id]["identity"]
            self.assertEqual(identity["runtime_battlefield_identity"], "Battle of Eilhart — Reikland vs Empire Secessionists")
            self.assertFalse(identity["source_layers_agree"])
        self.assertEqual(by_id["ubersreik"]["identity"]["display_identity"], "Battle of Ubersreik")
        self.assertEqual(by_id["marienburg"]["identity"]["display_identity"], "Battle of Marienburg")
        self.assertEqual(by_id["chaos"]["identity"]["display_identity"], "An Ogre's Folly")

    def test_v02e_campaign_challenge_module_has_no_runtime_order_or_player_identity_adapter(self) -> None:
        import ast
        source_path = REPO_ROOT / "synthetic_lab" / "transcendence_lab" / "campaign_challenge.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_import_roots = {"subprocess", "socket", "ctypes", "winreg"}
        imported_roots = set()
        executable_names = set()
        function_args = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                executable_names.add(node.name.lower())
                function_args[node.name] = [arg.arg.lower() for arg in node.args.args]
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    executable_names.add(func.id.lower())
                elif isinstance(func, ast.Attribute):
                    executable_names.add(func.attr.lower())
        self.assertFalse(imported_roots & forbidden_import_roots)
        self.assertFalse({"issue_order", "execute_order", "send_order", "apply_order"} & executable_names)
        self.assertNotIn("runtime_probe", imported_roots)
        self.assertNotIn("human_faction", function_args["evaluate_campaign_snapshot"])
        self.assertNotIn("player_faction", function_args["evaluate_campaign_snapshot"])
        self.assertIn('"human_or_player_identity_consumed": False', source)
        self.assertIn('APPLICATION_AUTHORITY = "PROHIBITED"', source)

    def test_v02e_campaign_challenge_matrix_preserves_no_orders_and_player_label_invariance(self) -> None:
        suite = json.loads(
            (REPO_ROOT / "synthetic_lab" / "scenarios" / "campaign_challenge_adversarial_matrix_v0.2E.json").read_text(encoding="utf-8")
        )
        from transcendence_lab.campaign_challenge_matrix import run_campaign_challenge_matrix
        result = run_campaign_challenge_matrix(suite)
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertEqual(result["application_authority"], "PROHIBITED")
        checks = {item["check_id"]: item for item in result["metamorphic_checks"]}
        self.assertTrue(checks["hidden_enemy_injection"]["passed"])
        self.assertTrue(checks["player_label_to_npc_label"]["passed"])

    def test_v02f_strategic_portfolio_module_has_no_runtime_order_or_assignment_adapter(self) -> None:
        import ast
        source_path = REPO_ROOT / "synthetic_lab" / "transcendence_lab" / "strategic_portfolio.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_import_roots = {"subprocess", "socket", "ctypes", "winreg"}
        imported_roots = set()
        executable_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                executable_names.add(node.name.lower())
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    executable_names.add(func.id.lower())
                elif isinstance(func, ast.Attribute):
                    executable_names.add(func.attr.lower())
        self.assertFalse(imported_roots & forbidden_import_roots)
        self.assertFalse({"issue_order", "execute_order", "send_order", "apply_order", "assign_army"} & executable_names)
        self.assertNotIn("runtime_probe", imported_roots)
        self.assertIn('"force_assignment_status": "NOT_PERFORMED"', source)
        self.assertIn('"human_or_player_identity_consumed": False', source)

    def test_v02f_strategic_portfolio_matrix_preserves_no_orders_and_invariance(self) -> None:
        suite = json.loads(
            (REPO_ROOT / "synthetic_lab" / "scenarios" / "campaign_strategic_theater_portfolio_adversarial_matrix_v0.2F.json").read_text(encoding="utf-8")
        )
        from transcendence_lab.strategic_portfolio_matrix import run_strategic_portfolio_matrix
        result = run_strategic_portfolio_matrix(suite)
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertEqual(result["application_authority"], "PROHIBITED")
        self.assertEqual(result["scenario_pass_count"], result["scenario_count"])
        self.assertEqual(result["metamorphic_pass_count"], 6)
        checks = {item["check_id"]: item for item in result["metamorphic_checks"]}
        self.assertTrue(checks["hidden_enemy_injection"]["passed"])
        self.assertTrue(checks["player_label_to_npc_label"]["passed"])
        self.assertTrue(checks["empty_war_edge"]["passed"])


    def test_v02g_force_allocation_modules_have_no_runtime_or_order_adapter(self) -> None:
        import ast
        forbidden_import_roots = {"subprocess", "socket", "ctypes", "winreg"}
        forbidden_calls = {"issue_order", "execute_order", "send_order", "apply_order", "move_to", "attack", "siege"}
        for filename in ("strategic_assignment.py", "strategic_commitment.py"):
            source_path = REPO_ROOT / "synthetic_lab" / "transcendence_lab" / filename
            source = source_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported_roots = set()
            executable_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    executable_names.add(node.name.lower())
                elif isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name):
                        executable_names.add(func.id.lower())
                    elif isinstance(func, ast.Attribute):
                        executable_names.add(func.attr.lower())
            self.assertFalse(imported_roots & forbidden_import_roots, filename)
            self.assertFalse(forbidden_calls & executable_names, filename)
            self.assertNotIn("runtime_probe", imported_roots, filename)
            self.assertIn('APPLICATION_AUTHORITY', source)
        assignment_source = (REPO_ROOT / "synthetic_lab" / "transcendence_lab" / "strategic_assignment.py").read_text(encoding="utf-8")
        commitment_source = (REPO_ROOT / "synthetic_lab" / "transcendence_lab" / "strategic_commitment.py").read_text(encoding="utf-8")
        self.assertIn('ASSIGNMENT_STATUS = "SHADOW_PROPOSED_NOT_EXECUTED"', assignment_source)
        self.assertIn('"orders_emitted": False', assignment_source)
        self.assertIn('"No commitment emits a WH3 order', commitment_source)

    def test_v02g_force_allocation_matrix_preserves_no_orders_and_invariance(self) -> None:
        suite = json.loads(
            (REPO_ROOT / "synthetic_lab" / "scenarios" / "campaign_theater_assignment_commitment_adversarial_matrix_v0.2G.json").read_text(encoding="utf-8")
        )
        from transcendence_lab.strategic_assignment_matrix import run_strategic_assignment_commitment_matrix
        result = run_strategic_assignment_commitment_matrix(suite)
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertEqual(result["application_authority"], "PROHIBITED")
        self.assertEqual(result["assignment_pass_count"], result["assignment_case_count"])
        self.assertEqual(result["temporal_pass_count"], result["temporal_case_count"])
        self.assertEqual(result["metamorphic_pass_count"], 7)
        checks = {item["check_id"]: item["passed"] for item in result["metamorphic_checks"]}
        for name in ("hidden_enemy_injection", "player_label_to_npc_label", "input_order", "coordinate_translation", "uniform_strength_scale", "temporal_input_order", "temporal_coordinate_translation"):
            self.assertTrue(checks[name])


    def test_v02h_strategic_feasibility_modules_have_no_runtime_mutation_adapter(self) -> None:
        import ast
        forbidden_import_roots = {"subprocess", "socket", "ctypes", "winreg"}
        forbidden_executable_names = {
            "move_to", "move_character", "attack", "attack_region", "attack_queued",
            "force_attack_of_opportunity", "join_garrison", "leave_garrison",
            "force_character_force_into_stance", "replenish_action_points", "zero_action_points",
            "disable_movement_for_character", "enable_movement_for_character",
            "disable_movement_for_faction", "enable_movement_for_faction",
            "disable_pathfinding_restriction",
        }
        for filename in ("strategic_feasibility.py", "strategic_feasibility_matrix.py"):
            source_path = REPO_ROOT / "synthetic_lab" / "transcendence_lab" / filename
            source = source_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported_roots = set()
            executable_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    executable_names.add(node.name.lower())
                elif isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name):
                        executable_names.add(func.id.lower())
                    elif isinstance(func, ast.Attribute):
                        executable_names.add(func.attr.lower())
            self.assertFalse(imported_roots & forbidden_import_roots, filename)
            self.assertFalse(executable_names & forbidden_executable_names, filename)
            self.assertNotIn("runtime_probe", imported_roots, filename)
        source = (REPO_ROOT / "synthetic_lab" / "transcendence_lab" / "strategic_feasibility.py").read_text(encoding="utf-8")
        self.assertIn('APPLICATION_AUTHORITY = "PROHIBITED"', source)
        self.assertIn('QUERY_RESULT_STATUS = "UNOBSERVED_QUERY_NOT_RUN"', source)

    def test_v02h_strategic_feasibility_matrix_preserves_read_only_boundary(self) -> None:
        suite = json.loads(
            (REPO_ROOT / "synthetic_lab" / "scenarios" / "campaign_strategic_feasibility_adversarial_matrix_v0.2H.json").read_text(encoding="utf-8")
        )
        from transcendence_lab.strategic_feasibility_matrix import run_strategic_feasibility_matrix
        result = run_strategic_feasibility_matrix(suite)
        self.assertTrue(result["passed"])
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertEqual(result["application_authority"], "PROHIBITED")
        self.assertTrue(result["synthetic_observation_checks"]["no_orders"])
        self.assertTrue(result["synthetic_observation_checks"]["no_execution"])
        self.assertTrue(result["tamper_checks"]["authority_promotion_rejected"])
        self.assertTrue(result["tamper_checks"]["stale_turn_rejected"])
        self.assertTrue(result["tamper_checks"]["foreign_query_rejected"])


    def test_v02i_campaign_feasibility_probe_is_read_only_first_tick_and_whitelisted(self) -> None:
        source = (RUNTIME_ROOT / "source/script/campaign/mod/transcendence_campaign_feasibility_probe.lua").read_text(encoding="utf-8")
        self.assertIn('LOCAL_FACTION_FIRST_TICK', source)
        self.assertIn('{"script", "transcendence_campaign_feasibility_probe"}', source)
        self.assertNotIn('{"script", "transcendence_shadow_probe"}', source)
        self.assertNotIn("ok and value or nil", source)
        self.assertIn("emitted_value = value", source)
        self.assertIn('header.authority ~= "NO_ORDERS"', source)
        self.assertIn('header.application_authority ~= "PROHIBITED"', source)
        self.assertIn('cm:repeat_real_callback(trans_feas_poll, 250', source)
        self.assertNotIn('cm:repeat_callback(trans_feas_poll', source)
        self.assertIn('trans_feas_poll()\n    cm:repeat_real_callback', source)
        self.assertIn('FEASIBILITY_POLL_TICK', source)
        self.assertIn('character_can_reach_position', source)
        self.assertIn('character_can_ever_reach_settlement', source)
        for forbidden in (
            'cm:move_to', 'cm:attack(', 'cm:attack_region', 'cm:force_attack_of_opportunity',
            'cm:force_character_force_into_stance', 'cm:zero_action_points', 'cm:replenish_action_points',
            'cm:join_garrison', 'cm:leave_garrison', 'cm:disable_pathfinding_restriction',
        ):
            self.assertNotIn(forbidden, source)
        manifest = json.loads((RUNTIME_ROOT / "manifests/campaign_feasibility_pack.json").read_text())
        self.assertFalse(manifest["save_mutation"])
        self.assertFalse(manifest["gameplay_mutation"])
        self.assertEqual(manifest["probe_kind"], "campaign_feasibility")
        prepare = (RUNTIME_ROOT / "tools/prepare_campaign_feasibility_observation.ps1").read_text(encoding="utf-8-sig")
        self.assertNotIn("powershell.exe -NoProfile -ExecutionPolicy Bypass -File", prepare)
        self.assertIn("& $PrepareLiveProbe @PrepareArguments", prepare)


    def test_v02i_r1_preparation_control_artifact_matches_current_sources(self) -> None:
        artifact_path = REPO_ROOT / "research/runtime_evidence/CAMPAIGN_STRATEGIC_FEASIBILITY_LIVE_PREPARATION_v0.2I-r1.json"
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        claimed = artifact.pop("result_digest")
        canonical = json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.assertEqual(claimed, hashlib.sha256(canonical).hexdigest())
        artifact["result_digest"] = claimed
        self.assertEqual(artifact["policy_authority"], "NO_ORDERS")
        self.assertEqual(artifact["application_authority"], "PROHIBITED")
        self.assertEqual(artifact["transport"]["maximum_query_count"], 16)
        self.assertEqual(len(artifact["query_whitelist"]), 13)
        lua_path = RUNTIME_ROOT / "source/script/campaign/mod/transcendence_campaign_feasibility_probe.lua"
        self.assertEqual(artifact["probe"]["lua_source_sha256"], hashlib.sha256(lua_path.read_bytes()).hexdigest())
        sidecar_path = RUNTIME_ROOT / "tools/watch_campaign_feasibility.py"
        self.assertEqual(artifact["transport"]["sidecar_sha256"], hashlib.sha256(sidecar_path.read_bytes()).hexdigest())
        prepare_path = RUNTIME_ROOT / "tools/prepare_campaign_feasibility_observation.ps1"
        collect_path = RUNTIME_ROOT / "tools/collect_campaign_feasibility_observation.ps1"
        self.assertEqual(artifact["transport"]["prepare_script_sha256"], hashlib.sha256(prepare_path.read_bytes()).hexdigest())
        self.assertEqual(artifact["transport"]["collector_script_sha256"], hashlib.sha256(collect_path.read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory() as temp:
            build = build_all(REPO_ROOT, Path(temp))
        feasibility = next(pack for pack in build["packs"] if pack["pack_name"] == "transcendence_campaign_feasibility_probe.pack")
        self.assertEqual(artifact["probe"]["pack_sha256"], feasibility["pack_sha256"])
        self.assertFalse(feasibility["save_mutation"])
        self.assertFalse(feasibility["gameplay_mutation"])


    def test_v02i_r1_idle_campaign_polling_uses_real_timer_not_model_timer(self) -> None:
        source = (RUNTIME_ROOT / "source/script/campaign/mod/transcendence_campaign_feasibility_probe.lua").read_text(encoding="utf-8")
        self.assertIn('cm:repeat_real_callback(trans_feas_poll, 250, "TranscendenceCampaignFeasibilityReadOnlyPoll")', source)
        self.assertIn('cm:remove_real_callback("TranscendenceCampaignFeasibilityReadOnlyPoll")', source)
        self.assertIn('{"timer_kind", "REAL_UI_TIMER"}', source)
        self.assertNotIn('cm:repeat_callback(trans_feas_poll, 1, "TranscendenceCampaignFeasibilityReadOnlyPoll")', source)
        self.assertLess(source.index('trans_feas_poll()\n    cm:repeat_real_callback'), source.index('cm:add_post_first_tick_callback(trans_feas_start_polling)'))


    def test_v02i_r2_campaign_feasibility_emitted_events_are_parser_allowlisted(self) -> None:
        source = (RUNTIME_ROOT / "source/script/campaign/mod/transcendence_campaign_feasibility_probe.lua").read_text(encoding="utf-8")
        emitted = set(re.findall(r'trans_probe_emit\("([A-Z0-9_]+)"', source))
        self.assertIn("FEASIBILITY_POLL_TICK", emitted)
        self.assertIn("FEASIBILITY_REQUEST_SEEN", emitted)
        self.assertFalse(emitted - ALLOWED_EVENTS, sorted(emitted - ALLOWED_EVENTS))

    def test_v02i_r2_parser_summarizes_campaign_feasibility_diagnostics(self) -> None:
        lines = [
            "TRANS_PROBE|1|PACK_LOADED|probe_kind=campaign_feasibility|script=transcendence_campaign_feasibility_probe|read_only=true",
            "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=campaign_feasibility|runtime=campaign",
            "TRANS_PROBE|1|FIRST_TICK|probe_kind=campaign_feasibility|campaign=wh3_main_combi|turn=6|local_faction=wh_main_emp_empire|is_new_game=false|is_multiplayer=false",
            "TRANS_PROBE|1|SNAPSHOT_BEGIN|reason=LOCAL_FACTION_FIRST_TICK|turn=6|local_faction=wh_main_emp_empire",
            "TRANS_PROBE|1|SNAPSHOT_END|reason=LOCAL_FACTION_FIRST_TICK|turn=6|local_faction=wh_main_emp_empire|own_armies_emitted=3|visible_armies_emitted=6|visible_armies_available=true|own_regions_emitted=6|visible_regions_emitted=19|visible_regions_available=true|wars_emitted=3|item_cap=64",
            "TRANS_PROBE|1|FEASIBILITY_EXECUTOR_READY|request_file=RELATIVE_GAME_ROOT_REQUEST_FILE|maximum_queries=16|orders_emitted=false|save_values_written=false|read_only=true",
            "TRANS_PROBE|1|FEASIBILITY_POLL_TICK|timer_kind=REAL_UI_TIMER|orders_emitted=false|save_values_written=false|read_only=true",
            "TRANS_PROBE|1|FEASIBILITY_REQUEST_SEEN|plan_digest=abc|turn=6|query_count=5|orders_emitted=false|save_values_written=false|read_only=true",
        ]
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "runtime.txt"
            log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            events = parse_logs([log])
            report = summarize(events)
        self.assertEqual(len(report["sessions"]), 1)
        self.assertEqual(report["sessions"][0]["probe_kind"], "campaign_feasibility")
        self.assertEqual(report["sessions"][0]["event_counts"]["FEASIBILITY_POLL_TICK"], 1)
        self.assertEqual(report["sessions"][0]["event_counts"]["FEASIBILITY_REQUEST_SEEN"], 1)

    def test_v02i_r2_preparation_and_limiting_artifacts_match_parser_contract(self) -> None:
        limiting_path = REPO_ROOT / "research/runtime_evidence/CAMPAIGN_FEASIBILITY_LIVE_OBSERVATION_LIMITING_RESULT_v0.2I-r2.json"
        limiting = json.loads(limiting_path.read_text(encoding="utf-8"))
        limiting_claimed = limiting.pop("result_digest")
        limiting_canonical = json.dumps(limiting, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.assertEqual(limiting_claimed, hashlib.sha256(limiting_canonical).hexdigest())
        self.assertTrue(limiting["owner_runtime_observation"]["poll_tick_observed"])
        self.assertFalse(limiting["owner_runtime_observation"]["request_seen_observed"])
        self.assertEqual(limiting["policy_authority"], "NO_ORDERS")
        self.assertEqual(limiting["application_authority"], "PROHIBITED")

        artifact_path = REPO_ROOT / "research/runtime_evidence/CAMPAIGN_STRATEGIC_FEASIBILITY_LIVE_PREPARATION_v0.2I-r2.json"
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        claimed = artifact.pop("result_digest")
        canonical = json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.assertEqual(claimed, hashlib.sha256(canonical).hexdigest())
        parser_path = RUNTIME_ROOT / "tools/parse_probe_log.py"
        collector_path = RUNTIME_ROOT / "tools/collect_campaign_feasibility_observation.ps1"
        self.assertEqual(artifact["transport"]["log_parser_sha256"], hashlib.sha256(parser_path.read_bytes()).hexdigest())
        self.assertEqual(artifact["transport"]["collector_script_sha256"], hashlib.sha256(collector_path.read_bytes()).hexdigest())
        self.assertEqual(artifact["probe"]["pack_sha256"], "86843cb3bbed02ddb99f90fe084b45ca784fc0e5e70d03dfea99cab613b2236d")
        self.assertEqual(artifact["policy_authority"], "NO_ORDERS")
        self.assertEqual(artifact["application_authority"], "PROHIBITED")

    def test_v02i_r3_embedded_probe_build_is_deterministic_and_read_only(self) -> None:
        log = RUNTIME_ROOT / "fixtures/campaign_feasibility_first_tick_valid.txt"
        plan, _ = derive_current_plan(parse_logs([log]))
        self.assertIsNotNone(plan)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_path = root / "plan.json"
            request_path = root / "request.txt"
            plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            request_path.write_text(_request_text(plan), encoding="utf-8", newline="\n")
            first = build_embedded_probe(plan_path=plan_path, request_path=request_path, output_dir=root / "a")
            second = build_embedded_probe(plan_path=plan_path, request_path=request_path, output_dir=root / "b")
            self.assertEqual(first["pack_sha256"], second["pack_sha256"])
            self.assertEqual((root / "a" / first["pack_name"]).read_bytes(), (root / "b" / second["pack_name"]).read_bytes())
            generated = (root / "a" / "transcendence_campaign_feasibility_probe.generated.lua").read_text(encoding="utf-8")
            self.assertIn('local TRANS_FEAS_EMBEDDED_REQUEST_LINES = {', generated)
            self.assertIn('{"request_file", "NOT_USED_EMBEDDED_REQUEST"}', generated)
            self.assertNotIn('pcall(io.open, TRANS_FEAS_REQUEST_FILE, "r")', generated)
            self.assertIn(plan["result_digest"], generated)
            self.assertEqual(first["policy_authority"], "NO_ORDERS")
            self.assertEqual(first["application_authority"], "PROHIBITED")
            self.assertFalse(first["gameplay_mutation"])
            self.assertFalse(first["save_mutation"])
            for forbidden in ('cm:move_to', 'cm:attack(', 'cm:attack_region', 'cm:force_attack_of_opportunity', 'cm:zero_action_points'):
                self.assertNotIn(forbidden, generated)

    def test_v02i_r3_embedded_probe_rejects_request_or_authority_tamper(self) -> None:
        log = RUNTIME_ROOT / "fixtures/campaign_feasibility_first_tick_valid.txt"
        plan, _ = derive_current_plan(parse_logs([log]))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_path = root / "plan.json"
            request_path = root / "request.txt"
            plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            request_path.write_text(_request_text(plan) + "tamper\n", encoding="utf-8")
            with self.assertRaises(EmbeddedProbeBuildError):
                build_embedded_probe(plan_path=plan_path, request_path=request_path, output_dir=root / "bad_request")
            forged = dict(plan)
            forged["application_authority"] = "ALLOWED"
            plan_path.write_text(json.dumps(forged, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            request_path.write_text(_request_text(plan), encoding="utf-8")
            with self.assertRaises(EmbeddedProbeBuildError):
                build_embedded_probe(plan_path=plan_path, request_path=request_path, output_dir=root / "bad_authority")

    def test_v02i_r3_embedded_retry_scripts_are_two_phase_read_only_and_restore_probe(self) -> None:
        prepare = (RUNTIME_ROOT / "tools/prepare_campaign_feasibility_embedded_retry.ps1").read_text(encoding="utf-8-sig")
        collect = (RUNTIME_ROOT / "tools/collect_campaign_feasibility_embedded_retry.ps1").read_text(encoding="utf-8-sig")
        self.assertIn('WAITING_FOR_QUERY_RESULTS', prepare)
        self.assertIn('build_embedded_campaign_feasibility_probe.py', prepare)
        self.assertIn('policy_authority = "NO_ORDERS"', prepare)
        self.assertIn('application_authority = "PROHIBITED"', prepare)
        self.assertIn('pre_retry_probe_backup_private.pack', prepare)
        self.assertIn('Restored the pre-retry campaign feasibility probe pack.', collect)
        self.assertIn('FEASIBILITY_REQUEST_SEEN', collect)
        self.assertIn('FEASIBILITY_PACKET_END', collect)
        for forbidden in ('attack_region', 'move_to', 'force_attack_of_opportunity', 'zero_action_points'):
            self.assertNotIn(forbidden, prepare.lower())
            self.assertNotIn(forbidden, collect.lower())

    def test_v02i_r3_limiting_and_embedded_preparation_artifacts_are_hash_bound(self) -> None:
        for relative in (
            "research/runtime_evidence/CAMPAIGN_FEASIBILITY_LIVE_OBSERVATION_LIMITING_RESULT_v0.2I-r3.json",
            "research/runtime_evidence/CAMPAIGN_STRATEGIC_FEASIBILITY_EMBEDDED_RETRY_PREPARATION_v0.2I-r3.json",
        ):
            artifact = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
            claimed = artifact.pop("result_digest")
            canonical = json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.assertEqual(claimed, hashlib.sha256(canonical).hexdigest(), relative)
            self.assertEqual(artifact["policy_authority"], "NO_ORDERS")
            self.assertEqual(artifact["application_authority"], "PROHIBITED")
            self.assertFalse(artifact["orders_emitted"])
            self.assertFalse(artifact["save_values_written"])
        prep = json.loads((REPO_ROOT / "research/runtime_evidence/CAMPAIGN_STRATEGIC_FEASIBILITY_EMBEDDED_RETRY_PREPARATION_v0.2I-r3.json").read_text())
        for record in prep["files"].values():
            self.assertEqual(record["sha256"], hashlib.sha256((REPO_ROOT / record["path"]).read_bytes()).hexdigest())
        self.assertFalse(prep["transport"]["runtime_created_inbound_file_required"])
        self.assertTrue(prep["evidence_acceptance"]["current_snapshot_must_reproduce_saved_plan_exactly"])

    def test_v02i_sidecar_derives_exact_plan_and_request_deterministically(self) -> None:
        log = RUNTIME_ROOT / "fixtures/campaign_feasibility_first_tick_valid.txt"
        events = parse_logs([log])
        first_plan, first_context = derive_current_plan(events)
        second_plan, second_context = derive_current_plan(events)
        self.assertIsNotNone(first_plan)
        self.assertEqual(first_plan, second_plan)
        self.assertEqual(first_context["selected_assignment"], second_context["selected_assignment"])
        self.assertEqual(first_plan["authority"], "NO_ORDERS")
        self.assertEqual(first_plan["application_authority"], "PROHIBITED")
        request_a = _request_text(first_plan)
        request_b = _request_text(second_plan)
        self.assertEqual(request_a, request_b)
        self.assertEqual(request_a.count("TRANS_FEAS_REQ|1|QUERY|"), first_plan["query_count"])
        self.assertNotIn("attack_region", request_a)
        self.assertNotIn("move_to", request_a)
        for query in first_plan["queries"]:
            self.assertIn(query["query_id"], request_a)

    def test_v02i_live_artifact_reconstructs_plan_and_preserves_no_orders(self) -> None:
        base_log = (RUNTIME_ROOT / "fixtures/campaign_feasibility_first_tick_valid.txt").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "transcendence_runtime_log.txt"
            log.write_text(base_log, encoding="utf-8")
            plan, _ = derive_current_plan(parse_logs([log]))
            self.assertIsNotNone(plan)
            lines = []
            false_injected = False
            for query in plan["queries"]:
                value = "true"
                if query["query_key"] == "FORCE_ACTIVE_STANCE":
                    value = plan["actor"]["observed_stance_reference"]
                elif not false_injected:
                    value = "false"
                    false_injected = True
                lines.append(
                    "TRANS_PROBE|1|FEASIBILITY_QUERY_RESULT|"
                    f"plan_digest={plan['result_digest']}|scenario_id={plan['scenario_id']}|turn={plan['turn']}|"
                    f"assignment_id={plan['source_assignment_id']}|query_id={query['query_id']}|query_key={query['query_key']}|"
                    f"observed=true|value={value}|read_only=true"
                )
            lines.append(
                "TRANS_PROBE|1|FEASIBILITY_PACKET_END|"
                f"plan_digest={plan['result_digest']}|scenario_id={plan['scenario_id']}|turn={plan['turn']}|"
                f"assignment_id={plan['source_assignment_id']}|query_count={plan['query_count']}|"
                "orders_emitted=false|save_values_written=false|read_only=true"
            )
            log.write_text(base_log + "\n".join(lines) + "\n", encoding="utf-8")
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            expected_pack = "c" * 64
            env = json.loads((RUNTIME_ROOT / "fixtures/campaign_feasibility_environment_valid.json").read_text())
            env["expected_probe"]["pack_sha256"] = expected_pack
            env_path = root / "env.json"
            env_path.write_text(json.dumps(env, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            artifacts = build_live_artifacts(
                log_path=log,
                saved_plan_path=plan_path,
                environment_public_path=env_path,
                expected_pack_sha256=expected_pack,
            )
            self.assertEqual(artifacts["verification"]["status"], "OBSERVED_READ_ONLY")
            self.assertEqual(artifacts["verification"]["bindings"]["observed_query_count"], plan["query_count"])
            self.assertTrue(any(item["observed"] and item["value"] is False for item in artifacts["observation"]["results"]))
            self.assertFalse(artifacts["verification"]["orders_emitted"])
            self.assertFalse(artifacts["verification"]["save_values_written"])
            self.assertEqual(artifacts["adjudication"]["application_authority"], "PROHIBITED")

    def test_v02i_live_artifact_rejects_foreign_query_result(self) -> None:
        base_log = (RUNTIME_ROOT / "fixtures/campaign_feasibility_first_tick_valid.txt").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "log.txt"
            log.write_text(base_log, encoding="utf-8")
            plan, _ = derive_current_plan(parse_logs([log]))
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
            log.write_text(base_log + (
                "TRANS_PROBE|1|FEASIBILITY_QUERY_RESULT|"
                f"plan_digest={plan['result_digest']}|scenario_id={plan['scenario_id']}|turn={plan['turn']}|"
                f"assignment_id={plan['source_assignment_id']}|query_id={'f'*64}|query_key=MODEL_HAS_CHARACTER_CQI|"
                "observed=true|value=true|read_only=true\n"
                "TRANS_PROBE|1|FEASIBILITY_PACKET_END|"
                f"plan_digest={plan['result_digest']}|scenario_id={plan['scenario_id']}|turn={plan['turn']}|"
                f"assignment_id={plan['source_assignment_id']}|query_count={plan['query_count']}|"
                "orders_emitted=false|save_values_written=false|read_only=true\n"
            ), encoding="utf-8")
            env = json.loads((RUNTIME_ROOT / "fixtures/campaign_feasibility_environment_valid.json").read_text())
            env["expected_probe"]["pack_sha256"] = "c" * 64
            env_path = root / "env.json"; env_path.write_text(json.dumps(env))
            with self.assertRaises(CampaignFeasibilityLiveError):
                build_live_artifacts(log_path=log, saved_plan_path=plan_path, environment_public_path=env_path, expected_pack_sha256="c"*64)

    def test_v02i_sfo_environment_capture_accepts_custom_probe_name(self) -> None:
        active = ["@sfo_grimhammer_3.pack", "@transcendence_campaign_feasibility_probe.pack"]
        entry, status = classify_probe_entry(active, "transcendence_campaign_feasibility_probe.pack")
        self.assertEqual(entry, "@transcendence_campaign_feasibility_probe.pack")
        self.assertEqual(status, "DECORATED_ACTIVE_ALIAS")

    def test_v02j_native_behavior_detector_has_no_runtime_or_order_adapter(self) -> None:
        import ast
        source_path = REPO_ROOT / "synthetic_lab" / "transcendence_lab" / "native_behavior.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_import_roots = {"subprocess", "socket", "ctypes", "winreg"}
        imported_roots = set()
        executable_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                executable_names.add(node.name.lower())
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    executable_names.add(func.id.lower())
                elif isinstance(func, ast.Attribute):
                    executable_names.add(func.attr.lower())
        self.assertFalse(imported_roots & forbidden_import_roots)
        self.assertFalse({"issue_order", "execute_order", "send_order", "apply_order"} & executable_names)
        self.assertNotIn("runtime_probe", imported_roots)
        self.assertIn('assignment_exclusivity_visibility": "UNAVAILABLE_FROM_TRAJECTORY_ONLY"', source)
        self.assertIn('"application_authority": APPLICATION_AUTHORITY', source)


    def test_v02k_existing_shadow_log_builds_player_visible_partial_native_trace(self) -> None:
        log = RUNTIME_ROOT / "fixtures/shadow_campaign_5_turns_valid.txt"
        result = run_player_visible_native_behavior([log], "wh_main_emp_empire_separatists")
        expected = json.loads((RUNTIME_ROOT / "fixtures/native_visible_behavior_5_turns_expected.json").read_text(encoding="utf-8"))
        self.assertEqual(result, expected)
        analysis = result["analysis"]
        self.assertEqual(analysis["observation_scope"], "PLAYER_VISIBLE_PARTIAL_FOREIGN_AI")
        self.assertEqual(analysis["metrics"]["frame_count"], 5)
        self.assertEqual(analysis["metrics"]["comparable_actor_intervals"], 4)
        self.assertEqual(analysis["metrics"]["ambiguous_anchor_intervals"], 4)
        self.assertEqual(analysis["metrics"]["visible_anchor_direction_change_candidate_count"], 0)
        self.assertEqual(analysis["availability"]["front_coverage"], "UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY")
        self.assertEqual(analysis["availability"]["recovery_misuse"], "UNAVAILABLE_NO_SAFE_FOREIGN_REPLENISHMENT_AT_ENGAGEMENT")
        self.assertEqual(analysis["authority"], "NO_ORDERS")
        self.assertEqual(analysis["application_authority"], "PROHIBITED")

    def test_v02k_runtime_adapter_rejects_unavailable_player_filtered_lists(self) -> None:
        source = (RUNTIME_ROOT / "fixtures/shadow_campaign_5_turns_valid.txt").read_text(encoding="utf-8")
        tampered = source.replace("visible_armies_available=true", "visible_armies_available=false", 1)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "log.txt"
            path.write_text(tampered, encoding="utf-8")
            with self.assertRaises(NativeVisiblePipelineError):
                build_player_visible_native_trace(parse_logs([path]), "wh_main_emp_empire_separatists")

    def test_v02k_partial_native_observer_has_no_order_or_privileged_enumeration_path(self) -> None:
        import ast
        tool_path = RUNTIME_ROOT / "tools/run_native_visible_behavior.py"
        source = tool_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        executable_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                executable_names.add(node.name.lower())
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    executable_names.add(node.func.id.lower())
                elif isinstance(node.func, ast.Attribute):
                    executable_names.add(node.func.attr.lower())
        self.assertFalse({"issue_order", "execute_order", "send_order", "apply_order"} & executable_names)
        self.assertNotIn("military_force_list", source)
        self.assertNotIn("factions_at_war_with", source)
        self.assertNotIn("run_shadow_campaign", source)
        self.assertNotIn("run_shadow_assignment", source)
        self.assertIn("VISIBILITY_SOURCE", source)
        visibility_module = (REPO_ROOT / "synthetic_lab/transcendence_lab/native_visible_behavior.py").read_text(encoding="utf-8")
        self.assertIn('VISIBILITY_SOURCE = "WH3_PLAYER_FILTERED_LISTS"', visibility_module)

    def test_v02k_owner_turns_4_7_reprocess_is_deterministic_and_frozen(self) -> None:
        source = REPO_ROOT / "research/runtime_evidence/CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json"
        first = build_native_visible_reprocess(source)
        second = build_native_visible_reprocess(source)
        frozen = json.loads((REPO_ROOT / "research/runtime_evidence/PLAYER_VISIBLE_NATIVE_BEHAVIOR_REPROCESS_v0.2K.json").read_text(encoding="utf-8"))
        self.assertEqual(first, second)
        self.assertEqual(first, frozen)
        self.assertEqual(first["evidence_label"], "SUPPORTED_DERIVED_OWNER_EVIDENCE")
        self.assertEqual(first["aggregate_metrics"]["foreign_faction_count"], 7)
        self.assertEqual(first["aggregate_metrics"]["comparable_actor_intervals"], 37)
        self.assertEqual(first["aggregate_metrics"]["position_idle_intervals"], 36)
        self.assertEqual(first["aggregate_metrics"]["movement_intervals"], 1)
        self.assertEqual(first["aggregate_metrics"]["ambiguous_anchor_intervals"], 1)
        self.assertEqual(first["aggregate_metrics"]["directional_anchor_proxy_intervals"], 0)
        self.assertEqual(first["policy_authority"], "NO_ORDERS")
        self.assertEqual(first["application_authority"], "PROHIBITED")

    def test_v02l_existing_shadow_fixture_produces_frozen_insufficient_churn_exposure(self) -> None:
        log = RUNTIME_ROOT / "fixtures/shadow_campaign_5_turns_valid.txt"
        result = run_native_visible_churn_batch([log], profile="VANILLA", minimum_frames=4)
        expected = json.loads((RUNTIME_ROOT / "fixtures/native_visible_churn_5_turns_expected.json").read_text(encoding="utf-8"))
        self.assertEqual(result, expected)
        self.assertEqual(result["observed_ai_faction_count"], 1)
        self.assertEqual(result["aggregate_metrics"]["eligible_stable_context_region_windows"], 0)
        self.assertEqual(result["aggregate_metrics"]["repeated_oscillation_cluster_count"], 0)
        analysis = result["factions"][0]["analysis"]
        self.assertEqual(analysis["status"], "INSUFFICIENT_ELIGIBLE_EXPOSURE")
        self.assertEqual(analysis["availability"]["native_hysteresis"], "UNAVAILABLE_ENGINE_INTERNAL")

    def test_v02l_runtime_batch_discovers_only_sufficiently_observed_foreign_factions(self) -> None:
        log = RUNTIME_ROOT / "fixtures/shadow_campaign_5_turns_valid.txt"
        events = parse_logs([log])
        self.assertEqual(discover_observed_ai_factions(events, minimum_frames=4), ["wh_main_emp_empire_separatists"])
        self.assertEqual(discover_observed_ai_factions(events, minimum_frames=6), [])

    def test_v02l_runtime_churn_tool_has_no_order_or_assignment_application_surface(self) -> None:
        import ast
        tool_path = RUNTIME_ROOT / "tools/run_native_visible_churn.py"
        source = tool_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        executable_names = set()
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                executable_names.add(node.name.lower())
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    executable_names.add(node.func.id.lower())
                elif isinstance(node.func, ast.Attribute):
                    executable_names.add(node.func.attr.lower())
        self.assertFalse({"issue_order", "execute_order", "send_order", "apply_order"} & executable_names)
        self.assertFalse(any("strategic_assignment" in item or "strategic_commitment" in item for item in imports))
        self.assertNotIn("military_force_list", source)
        self.assertIn("WH3_PLAYER_FILTERED_LISTS", (REPO_ROOT / "synthetic_lab/transcendence_lab/native_visible_behavior.py").read_text(encoding="utf-8"))

    def test_v02l_historical_owner_reprocess_is_frozen_insufficient_exposure(self) -> None:
        source = REPO_ROOT / "research/runtime_evidence/CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json"
        first = build_native_visible_churn_reprocess(source)
        second = build_native_visible_churn_reprocess(source)
        frozen = json.loads((REPO_ROOT / "research/runtime_evidence/PLAYER_VISIBLE_NATIVE_DIRECTIONAL_CHURN_REPROCESS_v0.2L.json").read_text(encoding="utf-8"))
        self.assertEqual(first, second)
        self.assertEqual(first, frozen)
        self.assertEqual(first["aggregate_metrics"]["eligible_stable_context_region_windows"], 0)
        self.assertEqual(first["aggregate_metrics"]["oscillation_candidate_count"], 0)
        self.assertEqual(first["aggregate_metrics"]["repeated_oscillation_cluster_count"], 0)
        self.assertEqual(first["evidence_label"], "SUPPORTED_DERIVED_OWNER_EVIDENCE_LIMITING_RESULT")
        self.assertEqual(first["policy_authority"], "NO_ORDERS")
        self.assertEqual(first["application_authority"], "PROHIBITED")


    def test_v02l_vanilla_profile_binding_accepts_only_probe_and_rejects_extra_mod(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = _make_native_churn_fake_environment(root, "VANILLA")
            public, private = build_native_churn_profile_binding(
                profile="VANILLA",
                game_root=env["game_root"],
                appdata_root=env["appdata_root"],
                probe_path=env["probe"],
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                observer_faction="wh_main_emp_empire",
                campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
            )
            self.assertEqual(public["profile"], "VANILLA")
            self.assertIsNone(public["sfo"])
            self.assertEqual(public["launcher"]["active_pack_entries"], ["transcendence_shadow_probe.pack"])
            self.assertEqual(public["authority"], "NO_ORDERS")
            self.assertEqual(public["application_authority"], "PROHIBITED")
            self.assertEqual(private["sfo_pack_path"], None)

            env["used_mods"].write_text(
                'mod "extra_ai_mod.pack";\nmod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            with self.assertRaises(NativeChurnProfileError):
                build_native_churn_profile_binding(
                    profile="VANILLA",
                    game_root=env["game_root"],
                    appdata_root=env["appdata_root"],
                    probe_path=env["probe"],
                    campaign_difficulty="Legendary",
                    battle_difficulty="Very Hard",
                    observer_faction="wh_main_emp_empire",
                    campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
                )

    def test_v02l_sfo_profile_binding_binds_exact_pack_and_rejects_extra_mod(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = _make_native_churn_fake_environment(root, "SFO")
            public, private = build_native_churn_profile_binding(
                profile="SFO",
                game_root=env["game_root"],
                appdata_root=env["appdata_root"],
                probe_path=env["probe"],
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                observer_faction="wh_main_emp_empire",
                campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
            )
            self.assertEqual(public["profile"], "SFO")
            self.assertEqual(public["sfo"]["workshop_id"], "2792731173")
            self.assertEqual(public["sfo"]["pack_name"], env["sfo_pack"].name)
            self.assertEqual(public["sfo"]["sha256"], hashlib.sha256(env["sfo_pack"].read_bytes()).hexdigest())
            self.assertEqual(Path(private["sfo_pack_path"]), env["sfo_pack"].resolve())

            env["used_mods"].write_text(
                f'mod "{env["sfo_pack"].name}";\nmod "other_mod.pack";\nmod "transcendence_shadow_probe.pack";\n',
                encoding="utf-8",
            )
            with self.assertRaises(NativeChurnProfileError):
                build_native_churn_profile_binding(
                    profile="SFO",
                    game_root=env["game_root"],
                    appdata_root=env["appdata_root"],
                    probe_path=env["probe"],
                    campaign_difficulty="Legendary",
                    battle_difficulty="Very Hard",
                    observer_faction="wh_main_emp_empire",
                    campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
                )

    def test_v02l_deferred_local_probe_may_materialize_after_profile_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = _make_native_churn_fake_environment(root, "VANILLA")
            env["used_mods"].write_text("", encoding="utf-8")
            public, private = build_native_churn_profile_binding(
                profile="VANILLA",
                game_root=env["game_root"],
                appdata_root=env["appdata_root"],
                probe_path=env["probe"],
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                observer_faction="wh_main_emp_empire",
                campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
            )
            self.assertEqual(public["probe"]["launcher_binding"], "DEFERRED_RUNTIME_MARKER")
            self.assertEqual(public["launcher"]["active_pack_entries"], [])
            env["used_mods"].write_text('mod "transcendence_shadow_probe.pack";\n', encoding="utf-8")
            public_path, private_path, evidence_path = _write_native_churn_binding_and_evidence(root, env, public, private)
            result = verify_native_churn_capture(
                log_path=RUNTIME_ROOT / "fixtures/native_churn_12_turns_valid.txt",
                evidence_manifest_path=evidence_path,
                public_binding_path=public_path,
                private_binding_path=private_path,
                minimum_turns=12,
                owner_protocol_attested=True,
            )
            detail = result["profile_checks"]["launcher_profile_detail"]
            self.assertTrue(detail["deferred_probe_materialized_after_binding"])
            self.assertEqual(detail["expected_probe_launcher_status"], "DEFERRED_RUNTIME_MARKER")
            self.assertEqual(detail["observed_probe_launcher_status"], "EXACT_ACTIVE_ENTRY")
            self.assertEqual(result["verification_status"], "PROFILE_BOUND_CAPTURE_OBSERVED_PRIMARY_ENDPOINT_EVALUABLE")


    def test_v02l_profile_bound_capture_detects_sfo_pack_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = _make_native_churn_fake_environment(root, "SFO")
            public, private = build_native_churn_profile_binding(
                profile="SFO",
                game_root=env["game_root"],
                appdata_root=env["appdata_root"],
                probe_path=env["probe"],
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                observer_faction="wh_main_emp_empire",
                campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
            )
            public_path, private_path, evidence_path = _write_native_churn_binding_and_evidence(root, env, public, private)
            log_path = RUNTIME_ROOT / "fixtures/native_churn_12_turns_valid.txt"
            result = verify_native_churn_capture(
                log_path=log_path,
                evidence_manifest_path=evidence_path,
                public_binding_path=public_path,
                private_binding_path=private_path,
                minimum_turns=12,
                owner_protocol_attested=True,
            )
            self.assertEqual(result["verification_status"], "PROFILE_BOUND_CAPTURE_OBSERVED_PRIMARY_ENDPOINT_EVALUABLE")
            self.assertEqual(result["churn_batch"]["aggregate_metrics"]["repeated_oscillation_cluster_count"], 1)

            env["sfo_pack"].write_bytes(b"mutated-sfo-after-binding")
            with self.assertRaises(NativeChurnCaptureError):
                verify_native_churn_capture(
                    log_path=log_path,
                    evidence_manifest_path=evidence_path,
                    public_binding_path=public_path,
                    private_binding_path=private_path,
                    minimum_turns=12,
                    owner_protocol_attested=True,
                )

    def test_v02l_owner_protocol_nonattestation_is_nonconfirmatory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = _make_native_churn_fake_environment(root, "VANILLA")
            public, private = build_native_churn_profile_binding(
                profile="VANILLA",
                game_root=env["game_root"],
                appdata_root=env["appdata_root"],
                probe_path=env["probe"],
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                observer_faction="wh_main_emp_empire",
                campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
            )
            public_path, private_path, evidence_path = _write_native_churn_binding_and_evidence(root, env, public, private)
            result = verify_native_churn_capture(
                log_path=RUNTIME_ROOT / "fixtures/native_churn_12_turns_valid.txt",
                evidence_manifest_path=evidence_path,
                public_binding_path=public_path,
                private_binding_path=private_path,
                minimum_turns=12,
                owner_protocol_attested=False,
            )
            self.assertEqual(result["verification_status"], "PROFILE_BOUND_CAPTURE_OBSERVED_PROTOCOL_DEVIATION_NONCONFIRMATORY")
            self.assertEqual(result["campaign_checks"]["owner_action_protocol"], "OWNER_PROTOCOL_NOT_ATTESTED_NONCONFIRMATORY")
            self.assertEqual(result["churn_batch"]["aggregate_metrics"]["repeated_oscillation_cluster_count"], 1)

    def test_v02l_vanilla_sfo_comparison_accepts_matched_protocol_and_rejects_mismatch(self) -> None:
        captures = {}
        bindings = {}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for profile in ("VANILLA", "SFO"):
                profile_root = root / profile.lower()
                profile_root.mkdir(parents=True)
                env = _make_native_churn_fake_environment(profile_root, profile)
                public, private = build_native_churn_profile_binding(
                    profile=profile,
                    game_root=env["game_root"],
                    appdata_root=env["appdata_root"],
                    probe_path=env["probe"],
                    campaign_difficulty="Legendary",
                    battle_difficulty="Very Hard",
                    observer_faction="wh_main_emp_empire",
                    campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
                )
                public_path, private_path, evidence_path = _write_native_churn_binding_and_evidence(profile_root, env, public, private)
                capture = verify_native_churn_capture(
                    log_path=RUNTIME_ROOT / "fixtures/native_churn_12_turns_valid.txt",
                    evidence_manifest_path=evidence_path,
                    public_binding_path=public_path,
                    private_binding_path=private_path,
                    minimum_turns=12,
                    owner_protocol_attested=True,
                )
                captures[profile] = capture
                bindings[profile] = public

            comparison = build_native_churn_comparison(
                vanilla_capture=captures["VANILLA"],
                vanilla_binding=bindings["VANILLA"],
                sfo_capture=captures["SFO"],
                sfo_binding=bindings["SFO"],
            )
            self.assertEqual(comparison["comparison_status"], "DESCRIPTIVE_ONLY_NO_CAUSAL_OR_SIGNIFICANCE_CLAIM")
            self.assertEqual(comparison["profiles"]["VANILLA"]["repeated_oscillation_cluster_count"], 1)
            self.assertEqual(comparison["profiles"]["SFO"]["repeated_oscillation_cluster_count"], 1)
            self.assertEqual(comparison["authority"], "NO_ORDERS")
            self.assertEqual(comparison["application_authority"], "PROHIBITED")

            mismatched = json.loads(json.dumps(bindings["SFO"]))
            mismatched["campaign_protocol"]["battle_difficulty"] = "Normal"
            with self.assertRaises(NativeChurnComparisonError):
                build_native_churn_comparison(
                    vanilla_capture=captures["VANILLA"],
                    vanilla_binding=bindings["VANILLA"],
                    sfo_capture=captures["SFO"],
                    sfo_binding=mismatched,
                )

    def test_v02l_owner_capture_tools_have_no_order_application_surface(self) -> None:
        import ast
        names = [
            "verify_native_churn_profile.py",
            "verify_native_churn_capture.py",
            "compare_native_churn_captures.py",
            "prepare_native_churn_capture.py",
            "collect_native_churn_capture.py",
        ]
        forbidden = {"issue_order", "execute_order", "send_order", "apply_order"}
        for name in names:
            source = (RUNTIME_ROOT / "tools" / name).read_text(encoding="utf-8")
            tree = ast.parse(source)
            executable_names = set()
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    executable_names.add(node.name.lower())
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        executable_names.add(node.func.id.lower())
                    elif isinstance(node.func, ast.Attribute):
                        executable_names.add(node.func.attr.lower())
            self.assertFalse(forbidden & executable_names, name)
            self.assertFalse(any("strategic_assignment" in item or "strategic_commitment" in item for item in imports), name)
            self.assertNotIn("military_force_list", source, name)


    def test_v02l_prepare_game_root_autodiscovery_uses_steam_programfiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            program_files = root / "Program Files (x86)"
            game_root = program_files / "Steam" / "steamapps" / "common" / "Total War WARHAMMER III"
            game_root.mkdir(parents=True)
            (game_root / "Warhammer3.exe").write_bytes(b"fake-wh3")
            repo_root = root / "repo"
            repo_root.mkdir()
            with mock.patch.dict(os.environ, {"PROGRAMFILES(X86)": str(program_files), "PROGRAMFILES": ""}, clear=False):
                resolved = resolve_native_churn_game_root(None, repo_root=repo_root)
            self.assertEqual(resolved, game_root.resolve())


    def test_v02l_prepare_session_binds_profile_and_archives_prior_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = _make_native_churn_fake_environment(root, "VANILLA")
            repo_root = root / "repo"
            repo_root.mkdir(parents=True)
            old_log = env["game_root"] / "transcendence_runtime_log.txt"
            old_log.write_text("prior-log", encoding="utf-8")

            def fake_build_manifest(_repo_root: Path, _manifest_path: Path, stage_root: Path) -> dict:
                stage_root.mkdir(parents=True, exist_ok=True)
                pack = stage_root / "transcendence_shadow_probe.pack"
                pack.write_bytes(b"deterministic-v02l-shadow-probe")
                return {
                    "probe_kind": "shadow",
                    "pack_name": pack.name,
                    "save_mutation": False,
                    "gameplay_mutation": False,
                }

            with mock.patch("prepare_native_churn_capture.build_manifest", side_effect=fake_build_manifest):
                prepared = prepare_native_churn_session(
                    profile="VANILLA",
                    game_root=env["game_root"],
                    appdata_root=env["appdata_root"],
                    minimum_turns=12,
                    campaign_difficulty="Legendary",
                    battle_difficulty="Very Hard",
                    assume_yes=True,
                    repo_root=repo_root,
                )
            self.assertEqual(prepared["profile"], "VANILLA")
            self.assertEqual(prepared["minimum_turns"], 12)
            self.assertEqual(prepared["authority"], "NO_ORDERS")
            self.assertEqual(prepared["application_authority"], "PROHIBITED")
            self.assertFalse(old_log.exists())
            self.assertIsNotNone(prepared["previous_runtime_log"])
            self.assertTrue(Path(prepared["previous_runtime_log"]["path"]).is_file())
            self.assertTrue(Path(prepared["profile_binding_public"]).is_file())
            self.assertTrue(Path(prepared["profile_binding_private"]).is_file())
            self.assertEqual(
                hashlib.sha256(Path(prepared["installed_probe"]).read_bytes()).hexdigest(),
                prepared["staged_probe_sha256"],
            )

    def test_v02l_collect_session_packages_only_public_safe_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = _make_native_churn_fake_environment(root, "VANILLA")
            repo_root = root / "repo"
            repo_root.mkdir(parents=True)
            public, private = build_native_churn_profile_binding(
                profile="VANILLA",
                game_root=env["game_root"],
                appdata_root=env["appdata_root"],
                probe_path=env["probe"],
                campaign_difficulty="Legendary",
                battle_difficulty="Very Hard",
                observer_faction="wh_main_emp_empire",
                campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
            )
            binding_root = root / "bindings"
            binding_root.mkdir()
            public_path = binding_root / "profile_binding_public.json"
            private_path = binding_root / "profile_binding_private.json"
            public_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            private_path.write_text(json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            staged_probe = root / "staged" / env["probe"].name
            staged_probe.parent.mkdir()
            shutil.copy2(env["probe"], staged_probe)
            runtime_log = env["game_root"] / "transcendence_runtime_log.txt"
            shutil.copy2(RUNTIME_ROOT / "fixtures/native_churn_12_turns_valid.txt", runtime_log)
            prepared = {
                "contract": "NATIVE_CAI_DIRECTIONAL_CHURN_PREPARED_SESSION_V1",
                "profile": "VANILLA",
                "minimum_turns": 12,
                "runtime_log": str(runtime_log),
                "profile_binding_public": str(public_path),
                "profile_binding_private": str(private_path),
                "installed_probe": str(env["probe"]),
                "staged_probe": str(staged_probe),
            }
            prepared_path = root / "prepared_session_private.json"
            prepared_path.write_text(json.dumps(prepared, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            verification, zip_path = collect_native_churn_session(
                prepared_path=prepared_path,
                owner_protocol_attested=True,
                repo_root=repo_root,
            )
            self.assertEqual(verification["verification_status"], "PROFILE_BOUND_CAPTURE_OBSERVED_PRIMARY_ENDPOINT_EVALUABLE")
            self.assertTrue(zip_path.is_file())
            with zipfile.ZipFile(zip_path) as archive:
                self.assertIsNone(archive.testzip())
                names = sorted(archive.namelist())
            self.assertEqual(
                names,
                [
                    "export_manifest.json",
                    "native_churn_capture_verification.json",
                    "native_churn_profile_binding.json",
                    "probe_summary.json",
                    "transcendence_runtime_log.txt",
                ],
            )
            self.assertNotIn("used_mods_private.txt", names)
            self.assertNotIn("profile_binding_private.json", names)


    def test_v02l_owner_kit_is_deterministic_public_and_pack_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first.zip"
            second = root / "second.zip"
            result_a = build_native_churn_owner_kit(REPO_ROOT, first)
            result_b = build_native_churn_owner_kit(REPO_ROOT, second)
            self.assertEqual(result_a["sha256"], result_b["sha256"])
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
                manifest = json.loads(archive.read("OWNER_KIT_MANIFEST.json"))
            self.assertIn("README_FIRST.md", names)
            self.assertIn("runtime_probe/tools/Prepare-NativeChurnCapture.ps1", names)
            self.assertIn("runtime_probe/tools/Collect-NativeChurnCapture.ps1", names)
            self.assertFalse(any(name.lower().endswith(".pack") for name in names))
            self.assertFalse(any("private" in name.casefold() for name in names))
            self.assertFalse(manifest["contains_raw_pack_bytes"])
            self.assertFalse(manifest["contains_private_machine_paths"])
            self.assertEqual(manifest["authority"], "NO_ORDERS")
            self.assertEqual(manifest["application_authority"], "PROHIBITED")


    def test_v02l_windows_owner_wrappers_are_minimal_python_launchers(self) -> None:
        wrappers = {
            "Prepare-NativeChurnCapture.ps1": "prepare_native_churn_capture.py",
            "Collect-NativeChurnCapture.ps1": "collect_native_churn_capture.py",
        }
        for name, target in wrappers.items():
            source = (RUNTIME_ROOT / "tools" / name).read_text(encoding="utf-8")
            self.assertIn(target, source)
            self.assertIn("Get-Command python.exe", source)
            self.assertIn("Get-Command py.exe", source)
            self.assertNotIn("[ordered]@{", source)
            self.assertNotIn(" -replace ", source)
            self.assertNotIn("Invoke-Expression", source)
            self.assertNotIn("Start-Process", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
