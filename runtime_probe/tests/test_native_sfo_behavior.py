from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
from verify_native_behavior_sfo_profile import (
    NativeDiagnosticSfoProfileError,
    SFO_PACK_NAME,
    build_sfo_profile_binding,
)


class NativeSfoBehaviorRuntimeTests(unittest.TestCase):
    def test_sfo_profile_binds_exact_two_pack_profile_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "game"
            app = root / "app"
            game.mkdir(); app.mkdir()
            (game / "Warhammer3.exe").write_bytes(b"fake-wh3")
            probe = game / "transcendence_native_diagnostic_probe.pack"
            probe.write_bytes(b"probe")
            sfo = root / SFO_PACK_NAME
            sfo.write_bytes(b"fake-sfo")
            (game / "used_mods.txt").write_text(
                f'mod "{SFO_PACK_NAME}";\nmod "{probe.name}";\n', encoding="utf-8"
            )
            sfo_hash = hashlib.sha256(sfo.read_bytes()).hexdigest()
            public, private = build_sfo_profile_binding(
                game_root=game,
                appdata_root=app,
                probe_path=probe,
                sfo_pack_path=sfo,
                profile_name="TEST",
                player_action_protocol="TEST",
                expected_sfo_sha256=sfo_hash,
            )
            self.assertEqual(set(public["launcher"]["active_pack_entries"]), {SFO_PACK_NAME, probe.name})
            self.assertEqual(public["sfo"]["sha256"], sfo_hash)
            self.assertFalse(public["application_eligible"])
            self.assertNotIn(str(root), str(public))
            self.assertIn(str(root), str(private))

    def test_sfo_profile_rejects_pack_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "game"; app = root / "app"
            game.mkdir(); app.mkdir()
            (game / "Warhammer3.exe").write_bytes(b"fake-wh3")
            probe = game / "transcendence_native_diagnostic_probe.pack"; probe.write_bytes(b"probe")
            sfo = root / SFO_PACK_NAME; sfo.write_bytes(b"fake-sfo")
            (game / "used_mods.txt").write_text(f'mod "{SFO_PACK_NAME}";\nmod "{probe.name}";\n', encoding="utf-8")
            with self.assertRaises(NativeDiagnosticSfoProfileError):
                build_sfo_profile_binding(
                    game_root=game,
                    appdata_root=app,
                    probe_path=probe,
                    sfo_pack_path=sfo,
                    profile_name="TEST",
                    player_action_protocol="TEST",
                    expected_sfo_sha256="0" * 64,
                )

    def test_sfo_profile_rejects_extra_mod(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "game"; app = root / "app"
            game.mkdir(); app.mkdir()
            (game / "Warhammer3.exe").write_bytes(b"fake-wh3")
            probe = game / "transcendence_native_diagnostic_probe.pack"; probe.write_bytes(b"probe")
            sfo = root / SFO_PACK_NAME; sfo.write_bytes(b"fake-sfo")
            (game / "used_mods.txt").write_text(
                f'mod "{SFO_PACK_NAME}";\nmod "{probe.name}";\nmod "extra.pack";\n', encoding="utf-8"
            )
            sfo_hash = hashlib.sha256(sfo.read_bytes()).hexdigest()
            with self.assertRaises(NativeDiagnosticSfoProfileError):
                build_sfo_profile_binding(
                    game_root=game,
                    appdata_root=app,
                    probe_path=probe,
                    sfo_pack_path=sfo,
                    profile_name="TEST",
                    player_action_protocol="TEST",
                    expected_sfo_sha256=sfo_hash,
                )

    def test_sfo_windows_wrappers_are_thin(self) -> None:
        for name in ("Prepare-NativeSFOBehaviorBenchmark.ps1", "Collect-NativeSFOBehaviorBenchmark.ps1"):
            source = (REPO_ROOT / "runtime_probe/tools" / name).read_text(encoding="utf-8")
            self.assertLess(len(source.splitlines()), 25)
            self.assertIn("python.exe", source)
            self.assertNotIn("military_force_list", source)
            self.assertNotIn("[ordered]@", source)


    def test_v0_2p_owner_kit_contains_precommit_artifacts_and_no_pack_bytes(self) -> None:
        sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
        from build_native_sfo_behavior_owner_kit import build
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "kit.zip"
            result = build(REPO_ROOT, output)
            self.assertGreater(result["entry_count"], 10)
            with zipfile.ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
                self.assertFalse(any(name.lower().endswith(".pack") for name in names))
                self.assertIn("synthetic_lab/transcendence_lab/native_sfo_mechanistic.py", names)
                self.assertIn("research/native_cai/SFO_POST_BENCHMARK_DECISION_TABLE_v0.2P_2026-08-04.json", names)
                manifest = json.loads(archive.read("OWNER_KIT_MANIFEST.json"))
                self.assertEqual(manifest["study_version"], "v0.2P")
                self.assertFalse(manifest["application_eligible"])
                self.assertFalse(manifest["contains_raw_game_or_workshop_pack_bytes"])


if __name__ == "__main__":
    unittest.main()
