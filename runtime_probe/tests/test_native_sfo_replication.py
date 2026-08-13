from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))


class NativeSfoReplicationRuntimeTests(unittest.TestCase):
    def test_replication_windows_wrappers_are_thin(self):
        for name in ("Prepare-NativeSFOReplication.ps1", "Collect-NativeSFOReplication.ps1"):
            source = (REPO_ROOT / "runtime_probe/tools" / name).read_text(encoding="utf-8")
            self.assertLess(len(source.splitlines()), 15)
            self.assertIn("python.exe", source)
            self.assertNotIn("military_force_list", source)
            self.assertNotIn("[ordered]@", source)

    def test_replication_owner_kit_has_policy_and_no_pack_bytes(self):
        from build_native_sfo_replication_owner_kit import build
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "kit.zip"
            result = build(REPO_ROOT, output)
            self.assertGreater(result["entry_count"], 15)
            with zipfile.ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
                self.assertFalse(any(name.lower().endswith(".pack") for name in names))
                self.assertIn("README_FIRST.md", names)
                self.assertIn("research/native_cai/NATIVE_SFO_REPLICATION_DECISION_POLICY_v0.2Q_2026-08-04.json", names)
                manifest = json.loads(archive.read("OWNER_KIT_MANIFEST.json"))
                self.assertEqual(manifest["study_version"], "v0.2Q")
                self.assertEqual(manifest["stage"], "A_FRESH_SFO_REPLICATION_ONLY")
                self.assertFalse(manifest["application_eligible"])
                self.assertFalse(manifest["contains_raw_game_or_workshop_pack_bytes"])


if __name__ == "__main__":
    unittest.main()
