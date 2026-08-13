from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from tools.audit_native_first_architecture import run


ROOT = Path(__file__).resolve().parents[2]


class NativeFirstArchitectureAuditTests(unittest.TestCase):
    def test_active_document_invariants_pass(self):
        report = run(ROOT)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(item["passed"] for item in report["checks"]))

    def test_game_side_probe_hashes_remain_frozen(self):
        expected = {
            "runtime_probe/source/script/campaign/mod/transcendence_native_diagnostic_probe.lua": "0acb4e186a4f4077801a763dbbf5cacc8ae21a9d47ecc76d54fefe5c023ec203",
            "runtime_probe/source/script/campaign/mod/transcendence_shadow_probe.lua": "4f8c80fb67efe288e4b7b4eeacc0c48578707a0e554f2dd8a454aa669b50ed98",
        }
        for relative, digest in expected.items():
            with self.subTest(relative=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
