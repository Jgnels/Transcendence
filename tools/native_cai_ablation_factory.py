from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any, Callable

from runtime_probe.tools.build_probe_packs import write_pfh5_pack

CONTRACT = "NATIVE_CAI_SINGLE_ROW_ABLATION_SPEC_V1"
FACTORY_CONTRACT = "NATIVE_CAI_SINGLE_ROW_ABLATION_BUILD_V1"
AUTHORITY = "NO_ORDERS"
APPLICATION_AUTHORITY = "PROHIBITED"
APPLICATION_STATUS = "APPLICATION_INELIGIBLE"
INSTALLATION_STATUS = "NOT_INSTALLED"


class AblationFactoryError(ValueError):
    pass


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _s8(value: Any) -> bytes:
    if not isinstance(value, str):
        raise AblationFactoryError(f"expected UTF-8 string, got {type(value).__name__}")
    blob = value.encode("utf-8")
    if len(blob) > 0xFFFF:
        raise AblationFactoryError("string is too long for decoded U8-string layout")
    return struct.pack("<H", len(blob)) + blob


def _optional_s8(value: Any) -> bytes:
    if value is None:
        return b"\x00"
    return b"\x01" + _s8(value)


def _f32(value: Any) -> bytes:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AblationFactoryError(f"expected numeric f32 value, got {value!r}")
    value = float(value)
    if not math.isfinite(value):
        raise AblationFactoryError("f32 value must be finite")
    return struct.pack("<f", value)


def _enc_cai_variables(row: dict[str, Any]) -> bytes:
    return _s8(row["key"]) + _f32(row["value"]) + _s8(row["description"])


def _enc_tms_variables(row: dict[str, Any]) -> bytes:
    return _f32(row["value"]) + _s8(row["key"])


def _enc_tms_variable_group(row: dict[str, Any]) -> bytes:
    return _s8(row["group"]) + _f32(row["value"]) + _s8(row["variable"])


def _enc_tg_variables(row: dict[str, Any]) -> bytes:
    return _s8(row["value"]) + _s8(row["key"])


def _enc_tg_variable_group(row: dict[str, Any]) -> bytes:
    return _s8(row["value"]) + _s8(row["variable"]) + _s8(row["group"])


def _enc_tg_group(row: dict[str, Any]) -> bytes:
    return _f32(row["priority"]) + _s8(row["group"]) + _s8(row["generator"]) + _optional_s8(row["variable_group"])


def _enc_variable_overrides(row: dict[str, Any]) -> bytes:
    return (
        _s8(row["key"])
        + _s8(row["campaign"])
        + _optional_s8(row["campaign_type"])
        + _optional_s8(row["difficulty"])
        + _f32(row["value"])
    )


def _enc_personality_variable_set(row: dict[str, Any]) -> bytes:
    return _s8(row["variable"]) + _s8(row["set"]) + _s8(row["value"])


def _enc_manager_behaviour(row: dict[str, Any]) -> bytes:
    return _s8(row["manager"]) + _s8(row["behaviour"]) + _f32(row["priority"])


# These layouts are the exact narrow layouts already proven by full binary
# consumption in tools/native_cai_binary_row_diff.py. Key certification is a
# separate gate: decoding a table does not by itself prove a currently pinned
# game-schema primary key.
LAYOUTS: dict[str, dict[str, Any]] = {
    "cai_variables_tables": {
        "fields": ("key", "value", "description"),
        "key_fields": ("key",),
        "encoder": _enc_cai_variables,
        "key_status": "CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING",
    },
    "cai_task_management_system_variables_tables": {
        "fields": ("key", "value"),
        "key_fields": ("key",),
        "encoder": _enc_tms_variables,
        "key_status": "CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING",
    },
    "cai_task_management_system_variable_group_junctions_tables": {
        "fields": ("group", "variable", "value"),
        "key_fields": ("group", "variable"),
        "encoder": _enc_tms_variable_group,
        "key_status": "CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING",
    },
    "cai_task_management_system_task_generator_variables_tables": {
        "fields": ("key", "value"),
        "key_fields": ("key",),
        "encoder": _enc_tg_variables,
        "key_status": "CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING",
    },
    "cai_task_management_system_task_generator_variable_group_junctions_tables": {
        "fields": ("group", "variable", "value"),
        "key_fields": ("group", "variable"),
        "encoder": _enc_tg_variable_group,
        "key_status": "CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING",
    },
    "cai_task_management_system_task_generator_groups_generators_junctions_tables": {
        "fields": ("group", "generator", "variable_group", "priority"),
        "key_fields": ("group", "generator", "variable_group"),
        "encoder": _enc_tg_group,
        "key_status": "PROVISIONAL_COMPOSITE_KEY_SCHEMA_CERTIFICATION_PENDING",
    },
    "cai_variables_overides_tables": {
        "fields": ("key", "campaign", "campaign_type", "difficulty", "value"),
        "key_fields": ("key", "campaign", "campaign_type", "difficulty"),
        "encoder": _enc_variable_overrides,
        "key_status": "CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING",
    },
    "cai_personality_variable_set_junctions_tables": {
        "fields": ("set", "variable", "value"),
        "key_fields": ("set", "variable"),
        "encoder": _enc_personality_variable_set,
        "key_status": "CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING",
    },
    "campaign_ai_manager_behaviour_junctions_tables": {
        "fields": ("manager", "behaviour", "priority"),
        "key_fields": ("manager", "behaviour"),
        "encoder": _enc_manager_behaviour,
        "key_status": "CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING",
    },
}


def _encode_db_header(header: dict[str, Any], *, rows: int) -> bytes:
    allowed = {"guid", "version", "mysterious", "version_marker_present"}
    extra = sorted(set(header) - allowed)
    if extra:
        raise AblationFactoryError(f"unsupported source_header fields: {extra}")
    guid = header.get("guid")
    version = header.get("version", 0)
    mysterious = header.get("mysterious")
    marker_present = header.get("version_marker_present", bool(version))
    if guid is not None and not isinstance(guid, str):
        raise AblationFactoryError("source_header.guid must be string or null")
    if isinstance(version, bool) or not isinstance(version, int):
        raise AblationFactoryError("source_header.version must be integer")
    if not isinstance(mysterious, bool):
        raise AblationFactoryError("source_header.mysterious must be boolean")
    if not isinstance(marker_present, bool):
        raise AblationFactoryError("source_header.version_marker_present must be boolean")
    if version != 0 and not marker_present:
        raise AblationFactoryError("non-zero table version requires a version marker")
    out = bytearray()
    if guid is not None:
        encoded = guid.encode("utf-16le")
        out += b"\xfd\xfe\xfc\xff" + struct.pack("<H", len(guid)) + encoded
    if marker_present:
        out += b"\xfc\xfd\xfe\xff" + struct.pack("<i", version)
    out += b"\x01" if mysterious else b"\x00"
    out += struct.pack("<I", rows)
    return bytes(out)


def _load_single_spec(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AblationFactoryError(f"cannot read JSON spec: {exc}") from exc
    if isinstance(value, list):
        raise AblationFactoryError("multiple row specifications are prohibited; supply exactly one object")
    if not isinstance(value, dict):
        raise AblationFactoryError("spec must be one JSON object")
    if "rows" in value:
        raise AblationFactoryError("multi-row 'rows' payload is prohibited; supply original_row and experimental_row only")
    return value


def _validate_spec(
    spec: dict[str, Any],
    *,
    allow_earned_build: bool,
    allow_provisional_key_schema: bool,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    if spec.get("contract") != CONTRACT:
        raise AblationFactoryError(f"unsupported contract: {spec.get('contract')!r}")
    table = spec.get("table")
    if table not in LAYOUTS:
        raise AblationFactoryError(f"unsupported/unverified table layout: {table!r}")
    layout = LAYOUTS[table]

    original = spec.get("original_row")
    experimental = spec.get("experimental_row")
    if not isinstance(original, dict) or not isinstance(experimental, dict):
        raise AblationFactoryError("original_row and experimental_row must be objects")
    expected_fields = set(layout["fields"])
    for label, row in (("original_row", original), ("experimental_row", experimental)):
        missing = sorted(expected_fields - set(row))
        extra = sorted(set(row) - expected_fields)
        if missing or extra:
            raise AblationFactoryError(f"{label} field mismatch; missing={missing}; extra={extra}")

    declared_keys = tuple(spec.get("key_fields") or ())
    if declared_keys != tuple(layout["key_fields"]):
        raise AblationFactoryError(
            f"key_fields mismatch: expected {list(layout['key_fields'])}, got {list(declared_keys)}"
        )
    for key in layout["key_fields"]:
        if original.get(key) != experimental.get(key):
            raise AblationFactoryError(f"key field changed: {key}")

    changed = [name for name in layout["fields"] if original.get(name) != experimental.get(name)]
    if len(changed) != 1:
        raise AblationFactoryError(f"exactly one row value may change; changed_fields={changed}")
    if changed[0] in layout["key_fields"]:
        raise AblationFactoryError("primary/composite key fields may not be changed")
    if spec.get("changed_field") != changed[0]:
        raise AblationFactoryError(f"changed_field must exactly name {changed[0]!r}")

    header = spec.get("source_header")
    if not isinstance(header, dict):
        raise AblationFactoryError("source_header object is required")
    _encode_db_header(header, rows=1)

    provenance = spec.get("provenance")
    if not isinstance(provenance, dict):
        raise AblationFactoryError("provenance object is required")
    required_provenance = {"evidence_label", "source_reference", "source_sha256"}
    missing_prov = sorted(required_provenance - set(provenance))
    if missing_prov:
        raise AblationFactoryError(f"provenance missing fields: {missing_prov}")
    digest = provenance.get("source_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
        raise AblationFactoryError("provenance.source_sha256 must be a 64-character hex digest")

    key_certification = spec.get("key_schema_certification")
    if key_certification == "VERIFIED_PINNED_SCHEMA_KEY":
        pass
    elif key_certification in {
        "CURRENT_PINNED_SCHEMA_KEY_CERTIFICATION_PENDING",
        "PROVISIONAL_COMPOSITE_KEY_SCHEMA_CERTIFICATION_PENDING",
    }:
        if not allow_provisional_key_schema:
            raise AblationFactoryError(
                "current pinned-schema key is not certified; fail closed unless explicit provisional-key authorization is supplied"
            )
        approval = spec.get("approval") or {}
        if approval.get("provisional_key_schema_authorized") is not True:
            raise AblationFactoryError("spec approval does not authorize provisional key schema")
    else:
        raise AblationFactoryError(f"unrecognized key_schema_certification: {key_certification!r}")

    experiment_status = spec.get("experiment_status")
    if experiment_status == "FACTORY_VALIDATION_NOT_EARNED":
        if provenance.get("synthetic_fixture") is not True:
            raise AblationFactoryError("NOT_EARNED builds are restricted to synthetic factory-validation fixtures")
    elif experiment_status == "EARNED_SINGLE_ROW_ABLATION":
        if not allow_earned_build:
            raise AblationFactoryError("earned experiment build requires explicit --allow-earned-build")
        approval = spec.get("approval")
        if not isinstance(approval, dict) or approval.get("owner_authorized") is not True:
            raise AblationFactoryError("earned experiment requires explicit owner authorization in spec")
        evidence_digest = approval.get("evidence_digest")
        if not isinstance(evidence_digest, str) or len(evidence_digest) != 64:
            raise AblationFactoryError("earned experiment approval requires a 64-character evidence_digest")
    else:
        raise AblationFactoryError(f"unsupported experiment_status: {experiment_status!r}")

    # Ensure encoder itself accepts the row before any output is written.
    encoder: Callable[[dict[str, Any]], bytes] = layout["encoder"]
    encoder(experimental)
    return layout, header, changed[0]


def build_single_row_ablation(
    spec: dict[str, Any],
    output_dir: Path,
    *,
    allow_earned_build: bool = False,
    allow_provisional_key_schema: bool = False,
) -> dict[str, Any]:
    layout, header, changed_field = _validate_spec(
        spec,
        allow_earned_build=allow_earned_build,
        allow_provisional_key_schema=allow_provisional_key_schema,
    )
    table = spec["table"]
    encoder: Callable[[dict[str, Any]], bytes] = layout["encoder"]
    row_blob = encoder(spec["experimental_row"])
    db_blob = _encode_db_header(header, rows=1) + row_blob

    output_dir.mkdir(parents=True, exist_ok=True)
    pack_path = output_dir / "transcendence_native_cai_single_row_ablation.pack"
    internal_path = f"db/{table}/transcendence_single_row_ablation"
    pack_record = write_pfh5_pack([(internal_path, db_blob)], pack_path, pack_type=3, timestamp=0)

    record: dict[str, Any] = {
        "contract": FACTORY_CONTRACT,
        "deterministic": True,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "application_status": APPLICATION_STATUS,
        "application_eligible": False,
        "installation_status": INSTALLATION_STATUS,
        "install_action_performed": False,
        "workshop_action_performed": False,
        "game_directory_action_performed": False,
        "experiment_status": spec["experiment_status"],
        "table": table,
        "key_fields": list(layout["key_fields"]),
        "key": [spec["experimental_row"].get(k) for k in layout["key_fields"]],
        "key_schema_certification": spec["key_schema_certification"],
        "changed_field": changed_field,
        "original_value": spec["original_row"][changed_field],
        "experimental_value": spec["experimental_row"][changed_field],
        "original_row": spec["original_row"],
        "experimental_row": spec["experimental_row"],
        "source_header": header,
        "provenance": spec["provenance"],
        "internal_db_path": internal_path,
        "db_payload_size": len(db_blob),
        "db_payload_sha256": sha256_bytes(db_blob),
        "pack": pack_record,
        "rollback": {
            "kind": "REMOVE_EXPERIMENTAL_OVERRIDE_ONLY",
            "instructions": [
                "Do not install this factory output automatically.",
                "If a future explicitly authorized test places the pack in a test load order, disable/remove only this generated pack before the next run.",
                "Verify the generated pack is absent from the active test load order; native/SFO source packs remain untouched.",
                "Re-run the applicable baseline/replication check before interpreting any subsequent campaign as rollback-clean evidence.",
            ],
        },
    }
    record["build_digest"] = sha256_bytes(canonical_json_bytes(record))
    (output_dir / "ablation_manifest.json").write_bytes(canonical_json_bytes(record))
    rollback = (
        "# Single-row native CAI ablation rollback\n\n"
        "**Authority:** `NO_ORDERS`  \n"
        "**Application authority:** `PROHIBITED`  \n"
        "**Application eligibility:** `APPLICATION_INELIGIBLE`\n\n"
        "This factory never installs the pack. If a future separately authorized experiment manually activates it, rollback is removal of this generated override from that experimental load order only. Do not modify native, SFO, or other source packs. Verify the test load order is clean before collecting rollback evidence.\n"
    )
    (output_dir / "ROLLBACK.md").write_text(rollback, encoding="utf-8", newline="\n")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed deterministic single-row native CAI ablation pack factory.")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-earned-build", action="store_true", help="Future explicit gate for an evidence-earned, owner-authorized ablation.")
    parser.add_argument("--allow-provisional-key-schema", action="store_true", help="Dangerous research-only override; requires matching explicit authorization in the spec.")
    args = parser.parse_args()
    try:
        spec = _load_single_spec(args.spec)
        record = build_single_row_ablation(
            spec,
            args.output,
            allow_earned_build=args.allow_earned_build,
            allow_provisional_key_schema=args.allow_provisional_key_schema,
        )
    except AblationFactoryError as exc:
        print(f"FAIL_CLOSED: {exc}")
        return 2
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
