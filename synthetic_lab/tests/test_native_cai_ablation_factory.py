from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from runtime_probe.tools.build_probe_packs import PACK_MAGIC
from tools.native_cai_ablation_factory import AblationFactoryError, build_single_row_ablation


def _spec(**overrides):
    value = {
        "contract": "NATIVE_CAI_SINGLE_ROW_ABLATION_SPEC_V1",
        "experiment_status": "FACTORY_VALIDATION_NOT_EARNED",
        "table": "cai_task_management_system_variables_tables",
        "key_fields": ["key"],
        "key_schema_certification": "VERIFIED_PINNED_SCHEMA_KEY",
        "source_header": {
            "guid": "d97d0a9e-4302-4dd3-a795-b854f9beb065",
            "version": 0,
            "mysterious": True,
            "version_marker_present": False,
        },
        "original_row": {"key": "SYNTHETIC_ALLOCATOR_TEST", "value": 2.0},
        "experimental_row": {"key": "SYNTHETIC_ALLOCATOR_TEST", "value": 3.0},
        "changed_field": "value",
        "provenance": {
            "evidence_label": "HYPOTHESIS",
            "source_reference": "synthetic factory validation fixture",
            "source_sha256": "0" * 64,
            "synthetic_fixture": True,
        },
    }
    value.update(overrides)
    return value


def _pack_entries(pack: bytes):
    if pack[:4] != PACK_MAGIC:
        raise AssertionError("not PFH5")
    pack_type, flags, deps, count, index_size, timestamp = struct.unpack_from("<6I", pack, 4)
    offset = 28
    entries = []
    for _ in range(count):
        size = struct.unpack_from("<I", pack, offset)[0]
        compression = pack[offset + 4]
        offset += 5
        end = pack.index(b"\x00", offset)
        path = pack[offset:end].decode("utf-8").replace("\\", "/")
        entries.append((path, size, compression))
        offset = end + 1
    data_offset = 28 + index_size
    blobs = []
    for path, size, compression in entries:
        blobs.append((path, pack[data_offset:data_offset + size], compression))
        data_offset += size
    return (pack_type, flags, deps, count, timestamp), blobs


class NativeCaiAblationFactoryTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)

    def tearDown(self):
        self._temp.cleanup()

    def test_factory_build_is_byte_deterministic_and_single_entry(self):
        one = build_single_row_ablation(_spec(), self.root / "one")
        two = build_single_row_ablation(_spec(), self.root / "two")
        p1 = (self.root / "one" / "transcendence_native_cai_single_row_ablation.pack").read_bytes()
        p2 = (self.root / "two" / "transcendence_native_cai_single_row_ablation.pack").read_bytes()
        self.assertEqual(p1, p2)
        self.assertEqual(one["pack"]["pack_sha256"], two["pack"]["pack_sha256"])
        self.assertEqual(one["pack"]["pack_sha256"], hashlib.sha256(p1).hexdigest())
        header, blobs = _pack_entries(p1)
        self.assertEqual(header, (3, 0, 0, 1, 0))
        self.assertEqual(len(blobs), 1)
        self.assertEqual(blobs[0][0], "db/cai_task_management_system_variables_tables/transcendence_single_row_ablation")
        self.assertEqual(blobs[0][2], 0)

    def test_db_payload_contains_exactly_one_experimental_row(self):
        record = build_single_row_ablation(_spec(), self.root)
        pack = (self.root / "transcendence_native_cai_single_row_ablation.pack").read_bytes()
        _, blobs = _pack_entries(pack)
        payload = blobs[0][1]
        self.assertEqual(payload[:4], b"\xfd\xfe\xfc\xff")
        self.assertEqual(payload[78], 1)
        self.assertEqual(struct.unpack_from("<I", payload, 79)[0], 1)
        self.assertAlmostEqual(struct.unpack_from("<f", payload, 83)[0], 3.0)
        n = struct.unpack_from("<H", payload, 87)[0]
        self.assertEqual(payload[89:89+n].decode("utf-8"), "SYNTHETIC_ALLOCATOR_TEST")
        self.assertEqual(record["db_payload_sha256"], hashlib.sha256(payload).hexdigest())

    def test_manifest_records_provenance_authority_and_rollback(self):
        record = build_single_row_ablation(_spec(), self.root)
        manifest = json.loads((self.root / "ablation_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest, record)
        self.assertEqual(record["original_value"], 2.0)
        self.assertEqual(record["experimental_value"], 3.0)
        self.assertEqual(record["authority"], "NO_ORDERS")
        self.assertEqual(record["application_authority"], "PROHIBITED")
        self.assertEqual(record["application_status"], "APPLICATION_INELIGIBLE")
        self.assertFalse(record["application_eligible"])
        self.assertEqual(record["installation_status"], "NOT_INSTALLED")
        self.assertFalse(record["install_action_performed"])
        self.assertFalse(record["workshop_action_performed"])
        self.assertFalse(record["game_directory_action_performed"])
        self.assertEqual(record["experiment_status"], "FACTORY_VALIDATION_NOT_EARNED")
        self.assertTrue(record["provenance"]["synthetic_fixture"])
        self.assertEqual(record["rollback"]["kind"], "REMOVE_EXPERIMENTAL_OVERRIDE_ONLY")
        self.assertIn("PROHIBITED", (self.root / "ROLLBACK.md").read_text(encoding="utf-8"))

    def test_factory_fails_closed_on_invalid_single_row_contracts(self):
        cases = []
        def add(label, mutate, expected): cases.append((label, mutate, expected))
        add("unknown table", lambda s: s.update({"table":"unknown_table"}), "unsupported/unverified")
        add("wrong key declaration", lambda s: s.update({"key_fields":["wrong"]}), "key_fields mismatch")
        add("key changed", lambda s: s["experimental_row"].update({"key":"CHANGED"}), "key field changed")
        add("no value change", lambda s: s["experimental_row"].update({"value":2.0}), "exactly one row value")
        add("wrong changed field", lambda s: s.update({"changed_field":"key"}), "changed_field")
        add("missing provenance hash", lambda s: s["provenance"].pop("source_sha256"), "provenance missing")
        for label, mutate, expected in cases:
            with self.subTest(label=label):
                spec=_spec(); mutate(spec)
                with self.assertRaisesRegex(AblationFactoryError, expected):
                    build_single_row_ablation(spec, self.root / label.replace(" ","_"))

    def test_multiple_field_change_fails_closed(self):
        spec={**_spec(),"table":"cai_variables_tables","key_fields":["key"],
              "original_row":{"key":"X","value":1.0,"description":"before"},
              "experimental_row":{"key":"X","value":2.0,"description":"after"}}
        with self.assertRaisesRegex(AblationFactoryError, "exactly one row value"):
            build_single_row_ablation(spec, self.root)

    def test_provisional_key_schema_requires_two_part_override(self):
        spec=_spec(key_schema_certification="CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING")
        with self.assertRaisesRegex(AblationFactoryError, "current pinned-schema key is not certified"):
            build_single_row_ablation(spec, self.root / "blocked")
        spec["approval"]={"provisional_key_schema_authorized":True}
        record=build_single_row_ablation(spec,self.root/"authorized",allow_provisional_key_schema=True)
        self.assertTrue(record["key_schema_certification"].endswith("PENDING"))

    def test_earned_real_ablation_requires_gate_owner_authorization_and_evidence_digest(self):
        spec=_spec(experiment_status="EARNED_SINGLE_ROW_ABLATION",provenance={
            "evidence_label":"VERIFIED_REPO_FACT","source_reference":"future exact approved row evidence","source_sha256":"1"*64})
        with self.assertRaisesRegex(AblationFactoryError, "--allow-earned-build"):
            build_single_row_ablation(spec,self.root/"blocked")
        spec["approval"]={"owner_authorized":True,"evidence_digest":"2"*64}
        record=build_single_row_ablation(spec,self.root/"earned",allow_earned_build=True)
        self.assertEqual(record["experiment_status"],"EARNED_SINGLE_ROW_ABLATION")
        self.assertFalse(record["application_eligible"])

    def test_not_earned_real_source_is_rejected(self):
        spec=_spec(); spec["provenance"]["synthetic_fixture"]=False
        with self.assertRaisesRegex(AblationFactoryError,"restricted to synthetic"):
            build_single_row_ablation(spec,self.root)


if __name__ == "__main__":
    unittest.main()
