from __future__ import annotations

import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
from build_probe_packs import build_manifest
from run_native_diagnostic_telemetry import parse_diagnostic_log
from prepare_native_diagnostic_capture import prepare
from collect_native_diagnostic_capture import collect


class NativeDiagnosticRuntimeTests(unittest.TestCase):
    def test_manifest_builds_read_only_application_ineligible_pack(self) -> None:
        manifest_path = REPO_ROOT / "runtime_probe" / "manifests" / "native_diagnostic_pack.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertFalse(manifest["save_mutation"])
        self.assertFalse(manifest["gameplay_mutation"])
        self.assertFalse(manifest["application_eligible"])
        self.assertEqual(manifest["research_visibility"], "PRIVILEGED_OMNISCIENT_DIAGNOSTIC")
        with tempfile.TemporaryDirectory() as temp:
            record = build_manifest(REPO_ROOT, manifest_path, Path(temp))
            self.assertEqual(record["probe_kind"], "native_diagnostic")
            self.assertEqual(record["file_count"], 1)

    def test_lua_probe_is_explicitly_privileged_but_has_no_mutation_surface(self) -> None:
        source = (REPO_ROOT / "runtime_probe" / "source" / "script" / "campaign" / "mod" / "transcendence_native_diagnostic_probe.lua").read_text(encoding="utf-8")
        self.assertIn("PRIVILEGED_OMNISCIENT_DIAGNOSTIC", source)
        self.assertIn("application_eligible", source)
        self.assertIn("military_force_list", source)
        self.assertIn('"FactionTurnStart"', source)
        self.assertIn('"FactionTurnEnd"', source)
        for forbidden in ("cm:move_to", "cm:attack", "force_character_force_into_stance", "create_force", "kill_character", "modify_faction"):
            self.assertNotIn(forbidden, source)

    def test_runtime_parser_qualifies_dense_synthetic_log(self) -> None:
        lines = [
            "TRANS_DIAG|1|PACK_LOADED|probe_kind=native_diagnostic|read_only=true|research_visibility=PRIVILEGED_OMNISCIENT_DIAGNOSTIC|application_eligible=false|authority=NO_ORDERS|application_authority=PROHIBITED|battle_participant_telemetry=true"
        ]
        # 25 turns x 3 forces => thresholds are crossed.
        for turn in range(1, 26):
            lines.append(f"TRANS_DIAG|1|HUMAN_TURN_MARKER|turn={turn}|phase=TURN_START|faction=human")
            for phase in ("TURN_START", "TURN_END"):
                lines.append(f"TRANS_DIAG|1|AI_SNAPSHOT_BEGIN|turn={turn}|phase={phase}|faction=ai")
                for cqi in (1, 2, 3):
                    x = turn - 1 if phase == "TURN_START" else turn
                    if cqi != 1:
                        x = cqi * 10
                    lines.append(
                        f"TRANS_DIAG|1|AI_FORCE|turn={turn}|phase={phase}|faction=ai|force_cqi={cqi}|x={x}|y=0|average_unit_health_pct=100"
                    )
                lines.append(f"TRANS_DIAG|1|AI_SNAPSHOT_END|turn={turn}|phase={phase}|faction=ai|forces_emitted=3|regions_emitted=0|wars_emitted=0")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "diag.txt"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = parse_diagnostic_log(path)
        self.assertEqual(result["human_turn_starts"], list(range(1, 26)))
        self.assertTrue(result["human_turns_consecutive"])
        self.assertEqual(result["paired_ai_faction_turns"], 25)
        self.assertEqual(result["analysis"]["qualification_status"], "QUALIFIED_FOR_FUTURE_PREREGISTERED_DIAGNOSTIC_STUDY")

    def test_runtime_parser_has_no_assignment_or_order_application_imports(self) -> None:
        path = REPO_ROOT / "runtime_probe" / "tools" / "run_native_diagnostic_telemetry.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        executable = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module: imports.append(node.module)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): executable.add(node.name.lower())
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name): executable.add(node.func.id.lower())
                elif isinstance(node.func, ast.Attribute): executable.add(node.func.attr.lower())
        self.assertFalse(any("strategic_assignment" in item or "strategic_commitment" in item for item in imports))
        self.assertFalse({"issue_order", "execute_order", "send_order", "apply_order"} & executable)


    def test_prepare_collect_fake_owner_workflow_is_profile_bound_and_upload_safe(self) -> None:
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "game"
            app = root / "app"
            (game / "data").mkdir(parents=True)
            app.mkdir()
            (game / "Warhammer3.exe").write_bytes(b"fake-wh3-exe")
            (game / "used_mods.txt").write_text('mod "transcendence_native_diagnostic_probe.pack";\n', encoding="utf-8")
            prepared = prepare(game, app, assume_yes=True)
            lines = [
                "TRANS_DIAG|1|PACK_LOADED|probe_kind=native_diagnostic|read_only=true|research_visibility=PRIVILEGED_OMNISCIENT_DIAGNOSTIC|application_eligible=false|authority=NO_ORDERS|application_authority=PROHIBITED|battle_participant_telemetry=true"
            ]
            for turn in range(1, 7):
                lines.append(f"TRANS_DIAG|1|HUMAN_TURN_MARKER|turn={turn}|phase=TURN_START|faction=wh_main_emp_empire")
                for faction_index in range(10):
                    faction = f"ai_{faction_index}"
                    for phase in ("TURN_START", "TURN_END"):
                        lines.append(f"TRANS_DIAG|1|AI_SNAPSHOT_BEGIN|turn={turn}|phase={phase}|faction={faction}")
                        x = (turn - 1) * 2 + faction_index if phase == "TURN_START" else turn * 2 + faction_index
                        lines.append(f"TRANS_DIAG|1|AI_FORCE|turn={turn}|phase={phase}|faction={faction}|force_cqi={100+faction_index}|x={x}|y={faction_index}|average_unit_health_pct=100")
                        lines.append(f"TRANS_DIAG|1|AI_SNAPSHOT_END|turn={turn}|phase={phase}|faction={faction}|forces_emitted=1|regions_emitted=0|wars_emitted=0")
            Path(prepared["runtime_log"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
            latest = json.loads((REPO_ROOT / "local_inputs/runtime_probe/native_diagnostic_sessions/latest.json").read_text(encoding="utf-8"))
            result = collect(Path(latest["prepared_session"]))
            output = Path(result["output"])
            try:
                with zipfile.ZipFile(output) as archive:
                    self.assertIsNone(archive.testzip())
                    self.assertEqual(set(archive.namelist()), {
                        "export_manifest.json",
                        "native_diagnostic_capture_verification.json",
                        "native_diagnostic_profile_binding.json",
                        "native_diagnostic_summary.json",
                        "transcendence_native_diagnostic_log.txt",
                    })
                    manifest = json.loads(archive.read("export_manifest.json"))
                    self.assertFalse(manifest["contains_private_machine_paths"])
                    self.assertFalse(manifest["application_eligible"])
                self.assertEqual(result["qualification_status"], "QUALIFIED_FOR_FUTURE_PREREGISTERED_DIAGNOSTIC_STUDY")
            finally:
                output.unlink(missing_ok=True)

    def test_windows_wrappers_contain_no_business_logic(self) -> None:
        for name in ("Prepare-NativeDiagnosticCapture.ps1", "Collect-NativeDiagnosticCapture.ps1"):
            source = (REPO_ROOT / "runtime_probe/tools" / name).read_text(encoding="utf-8")
            self.assertLess(len(source.splitlines()), 25)
            self.assertIn("python.exe", source)
            self.assertNotIn("[ordered]@", source)
            self.assertNotIn("military_force_list", source)


class NativeDiagnosticBehaviorStudyRuntimeTests(unittest.TestCase):
    def _battle_log(self) -> str:
        return "\n".join([
            "TRANS_DIAG|1|PACK_LOADED|probe_kind=native_diagnostic|read_only=true|research_visibility=PRIVILEGED_OMNISCIENT_DIAGNOSTIC|application_eligible=false|authority=NO_ORDERS|application_authority=PROHIBITED|battle_participant_telemetry=true",
            "TRANS_DIAG|1|HUMAN_TURN_MARKER|turn=1|phase=TURN_START|faction=human",
            "TRANS_DIAG|1|AI_SNAPSHOT_BEGIN|turn=1|phase=TURN_START|faction=ai",
            "TRANS_DIAG|1|AI_FORCE|turn=1|phase=TURN_START|faction=ai|force_cqi=7|x=0|y=0|average_unit_health_pct=50|force_strength=1000|unit_count=20|stance=default|region=A",
            "TRANS_DIAG|1|AI_SNAPSHOT_END|turn=1|phase=TURN_START|faction=ai|forces_emitted=1|regions_emitted=0|wars_emitted=0",
            "TRANS_DIAG|1|AI_BATTLE_BEGIN|turn=1|battle_sequence=1|attacker_count=1|defender_count=1",
            "TRANS_DIAG|1|AI_BATTLE_PARTICIPANT|turn=1|battle_sequence=1|side=ATTACKER|index=1|char_cqi=70|force_cqi=7|faction=ai",
            "TRANS_DIAG|1|AI_BATTLE_PARTICIPANT|turn=1|battle_sequence=1|side=DEFENDER|index=1|char_cqi=80|force_cqi=8|faction=enemy",
            "TRANS_DIAG|1|AI_BATTLE_END|turn=1|battle_sequence=1|attackers_emitted=1|defenders_emitted=1",
            "TRANS_DIAG|1|AI_SNAPSHOT_BEGIN|turn=1|phase=TURN_END|faction=ai",
            "TRANS_DIAG|1|AI_FORCE|turn=1|phase=TURN_END|faction=ai|force_cqi=7|x=10|y=0|average_unit_health_pct=45|force_strength=900|unit_count=19|stance=default|region=B",
            "TRANS_DIAG|1|AI_SNAPSHOT_END|turn=1|phase=TURN_END|faction=ai|forces_emitted=1|regions_emitted=0|wars_emitted=0",
        ]) + "\n"

    def test_parser_preserves_complete_pending_battle_participants(self) -> None:
        from run_native_diagnostic_telemetry import parse_diagnostic_trace
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "diag.txt"
            path.write_text(self._battle_log(), encoding="utf-8")
            parsed = parse_diagnostic_trace(path)
        self.assertEqual(len(parsed["battle_sequences"]), 1)
        battle = parsed["battle_sequences"][0]
        self.assertEqual([p["side"] for p in battle["participants"]], ["ATTACKER", "DEFENDER"])
        self.assertEqual(str(battle["participants"][0]["force_cqi"]), "7")
        self.assertEqual(parsed["incomplete_battle_sequences"], [])

    def test_parser_flags_incomplete_pending_battle_sequence(self) -> None:
        from run_native_diagnostic_telemetry import parse_diagnostic_trace
        text = self._battle_log().replace(
            "TRANS_DIAG|1|AI_BATTLE_END|turn=1|battle_sequence=1|attackers_emitted=1|defenders_emitted=1\n", ""
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "diag.txt"
            path.write_text(text, encoding="utf-8")
            parsed = parse_diagnostic_trace(path)
        self.assertEqual(len(parsed["battle_sequences"]), 0)
        self.assertEqual(len(parsed["incomplete_battle_sequences"]), 1)

    def test_lua_probe_uses_documented_pending_battle_cache_and_remains_read_only(self) -> None:
        source = (REPO_ROOT / "runtime_probe/source/script/campaign/mod/transcendence_native_diagnostic_probe.lua").read_text(encoding="utf-8")
        for required in (
            '"ScriptEventPendingBattle"',
            "pending_battle_cache_num_attackers",
            "pending_battle_cache_get_attacker",
            "pending_battle_cache_num_defenders",
            "pending_battle_cache_get_defender",
            '"AI_BATTLE_PARTICIPANT"',
            'if faction_name == "rebels" then',
        ):
            self.assertIn(required, source)
        for forbidden in ("cm:move_to", "cm:attack", "create_force", "kill_character", "modify_faction"):
            self.assertNotIn(forbidden, source)

    def test_behavior_study_wrappers_are_thin_and_threshold_digest_is_bound(self) -> None:
        from transcendence_lab.native_diagnostic_study import frozen_thresholds_digest
        for name in ("Prepare-NativeBehaviorStudy.ps1", "Collect-NativeBehaviorStudy.ps1"):
            source = (REPO_ROOT / "runtime_probe/tools" / name).read_text(encoding="utf-8")
            self.assertLess(len(source.splitlines()), 25)
            self.assertIn("python.exe", source)
            self.assertNotIn("pending_battle_cache", source)
        builder = (REPO_ROOT / "runtime_probe/tools/build_native_behavior_study_owner_kit.py").read_text(encoding="utf-8")
        self.assertIn(frozen_thresholds_digest(), builder)

    def test_behavior_study_prepare_collect_end_to_end(self) -> None:
        import zipfile
        from prepare_native_behavior_study import prepare_behavior_study
        from collect_native_behavior_study import collect_behavior_study
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "game"
            app = root / "app"
            (game / "data").mkdir(parents=True)
            app.mkdir()
            (game / "Warhammer3.exe").write_bytes(b"fake-wh3-exe-v02n")
            (game / "used_mods.txt").write_text('mod "transcendence_native_diagnostic_probe.pack";\n', encoding="utf-8")
            prepared = prepare_behavior_study(game, app, assume_yes=True)
            lines = [
                "TRANS_DIAG|1|PACK_LOADED|probe_kind=native_diagnostic|read_only=true|research_visibility=PRIVILEGED_OMNISCIENT_DIAGNOSTIC|application_eligible=false|authority=NO_ORDERS|application_authority=PROHIBITED|battle_participant_telemetry=true"
            ]
            for turn in range(1, 12):
                lines.append(f"TRANS_DIAG|1|HUMAN_TURN_MARKER|turn={turn}|phase=TURN_START|faction=human")
                for phase in ("TURN_START", "TURN_END"):
                    lines.append(f"TRANS_DIAG|1|AI_SNAPSHOT_BEGIN|turn={turn}|phase={phase}|faction=ai")
                    x = 0 if turn % 2 else 10
                    lines.append(f"TRANS_DIAG|1|AI_FORCE|turn={turn}|phase={phase}|faction=ai|force_cqi=7|x={x}|y=0|average_unit_health_pct=100|force_strength=1000|unit_count=20|stance=default|region={'A' if x == 0 else 'B'}")
                    lines.append(f"TRANS_DIAG|1|AI_SNAPSHOT_END|turn={turn}|phase={phase}|faction=ai|forces_emitted=1|regions_emitted=0|wars_emitted=0")
                if turn == 2:
                    lines.extend([
                        "TRANS_DIAG|1|AI_BATTLE_BEGIN|turn=2|battle_sequence=1|attacker_count=1|defender_count=1",
                        "TRANS_DIAG|1|AI_BATTLE_PARTICIPANT|turn=2|battle_sequence=1|side=ATTACKER|index=1|char_cqi=70|force_cqi=70|faction=other_ai",
                        "TRANS_DIAG|1|AI_BATTLE_PARTICIPANT|turn=2|battle_sequence=1|side=DEFENDER|index=1|char_cqi=80|force_cqi=80|faction=enemy_ai",
                        "TRANS_DIAG|1|AI_BATTLE_END|turn=2|battle_sequence=1|attackers_emitted=1|defenders_emitted=1",
                    ])
            Path(prepared["runtime_log"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
            latest = json.loads((REPO_ROOT / "local_inputs/runtime_probe/native_behavior_study_sessions/latest.json").read_text(encoding="utf-8"))
            result = collect_behavior_study(Path(latest["prepared_session"]))
            self.assertTrue(result["confirmatory_eligible"])
            self.assertEqual(result["human_turn_starts_observed"], list(range(1, 12)))
            output = Path(result["output"])
            try:
                self.assertIsNone(zipfile.ZipFile(output).testzip())
                with zipfile.ZipFile(output) as archive:
                    self.assertIn("native_behavior_study_result.json", archive.namelist())
                    export = json.loads(archive.read("export_manifest.json"))
                    self.assertFalse(export["application_eligible"])
                    self.assertFalse(export["contains_private_machine_paths"])
            finally:
                output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
