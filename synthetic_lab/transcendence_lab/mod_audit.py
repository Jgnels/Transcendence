from __future__ import annotations

import hashlib
import json
import re
import struct
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .canonical import file_digest

DIRECT_AI_PREFIXES = (
    "cai_",
    "campaign_ai_manager_",
    "cdir_military_generator_",
)
BATTLE_AI_PREFIXES = (
    "battle_personalities",
    "land_units_to_battle_personalities",
    "autoresolver_",
)
DIFFICULTY_PREFIXES = (
    "campaign_difficulty_",
    "faction_potential_",
)
DIPLOMACY_MARKERS = (
    "diplom",
    "cultural_relations",
    "deal_evaluation",
    "deal_generation",
    "treacher",
    "empire_rivalry",
)
ENVIRONMENT_MARKERS = (
    "building",
    "recruit",
    "unit_",
    "main_units",
    "land_units",
    "effect_bundle",
    "econom",
    "income",
    "budget",
    "technology",
    "pooled_resource",
)

SCRIPT_CALL_PATTERNS = {
    "force_declare_war": re.compile(r"\bcm:force_declare_war\b"),
    "force_make_peace": re.compile(r"\bcm:force_make_peace\b"),
    "force_alliance": re.compile(r"\bcm:force_alliance\b"),
    "force_confederation": re.compile(r"\bcm:force_confederation\b"),
    "transfer_region": re.compile(r"\bcm:transfer_region_to_faction\b"),
    "treasury_mod": re.compile(r"\bcm:treasury_mod\b"),
    "create_force": re.compile(r"\bcm:create_force\b"),
    "apply_effect_bundle": re.compile(r"\bcm:apply_(?:custom_)?effect_bundle"),
    "spawn_character": re.compile(r"\bcm:spawn_character_to_pool\b"),
    "teleport": re.compile(r"\bcm:teleport_to\b"),
    "random_number": re.compile(r"\bcm:random_number\b"),
    "human_branch": re.compile(r"\bis_human\s*\("),
    "listener": re.compile(r"\bcore:add_listener\b"),
    "saved_value": re.compile(r"\bcm:(?:get|set)_saved_value\b"),
}


class PackFormatError(ValueError):
    pass


def classify_table(table_name: str) -> str:
    name = table_name.lower()
    if name.startswith(DIRECT_AI_PREFIXES):
        if any(marker in name for marker in DIPLOMACY_MARKERS):
            return "DIRECT_AI_DIPLOMACY"
        return "DIRECT_NATIVE_CAI"
    if name.startswith(BATTLE_AI_PREFIXES):
        return "BATTLE_OR_AUTORESOLVE"
    if name.startswith(DIFFICULTY_PREFIXES):
        return "DIFFICULTY_OR_POTENTIAL"
    if any(marker in name for marker in DIPLOMACY_MARKERS):
        return "DIPLOMACY_ENVIRONMENT"
    if any(marker in name for marker in ENVIRONMENT_MARKERS):
        return "INDIRECT_AI_ENVIRONMENT"
    return "OTHER_GAME_DATA"


def _safe_name(path: str) -> str:
    return path.replace("\\", "/")


def parse_pfh5_index(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    data = source.read_bytes()
    if len(data) < 28 or data[:4] != b"PFH5":
        raise PackFormatError("only PFH5 packs are supported by this audit reader")
    pack_type, flags, dependency_count, file_count, index_size, timestamp = struct.unpack_from("<6I", data, 4)
    if dependency_count != 0:
        raise PackFormatError("dependency-bearing PFH5 packs require a fuller parser")
    pos = 28
    index_end = pos + index_size
    if index_end > len(data):
        raise PackFormatError("file index extends beyond pack length")
    entries: list[dict[str, Any]] = []
    for _ in range(file_count):
        if pos + 5 > index_end:
            raise PackFormatError("truncated file index")
        size = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        compression_flag = data[pos]
        pos += 1
        if compression_flag != 0:
            raise PackFormatError(f"compressed PFH5 entry is unsupported: flag={compression_flag}")
        try:
            nul = data.index(0, pos, index_end + 1)
        except ValueError as error:
            raise PackFormatError("unterminated file path in pack index") from error
        name = data[pos:nul].decode("utf-8", errors="strict")
        pos = nul + 1
        entries.append({"path": _safe_name(name), "size": size, "compression_flag": compression_flag})
    if pos != index_end:
        raise PackFormatError(f"unexpected index remainder: {index_end - pos} bytes")
    data_pos = index_end
    for entry in entries:
        size = entry["size"]
        end = data_pos + size
        if end > len(data):
            raise PackFormatError(f"entry exceeds pack length: {entry['path']}")
        blob = data[data_pos:end]
        entry["sha256"] = hashlib.sha256(blob).hexdigest()
        data_pos = end
    if data_pos != len(data):
        raise PackFormatError(f"unexpected trailing data: {len(data) - data_pos} bytes")
    return {
        "format": "PFH5",
        "pack_type": pack_type,
        "flags": flags,
        "dependency_count": dependency_count,
        "file_count": file_count,
        "index_size": index_size,
        "timestamp_raw": timestamp,
        "source_size": len(data),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "entries": entries,
    }


def audit_pack(path: str | Path, source_id: str) -> dict[str, Any]:
    parsed = parse_pfh5_index(path)
    tables: list[dict[str, Any]] = []
    metadata: list[dict[str, Any]] = []
    for entry in parsed["entries"]:
        parts = entry["path"].split("/")
        if len(parts) >= 3 and parts[0] == "db":
            table = parts[1]
            tables.append(
                {
                    "table": table,
                    "internal_file": "/".join(parts[2:]),
                    "classification": classify_table(table),
                    "size": entry["size"],
                    "sha256": entry["sha256"],
                }
            )
        else:
            metadata.append(entry)
    category_counts = Counter(item["classification"] for item in tables)
    return {
        "schema_version": 1,
        "source_id": source_id,
        "source_kind": "PFH5_PACK",
        "source_sha256": parsed["source_sha256"],
        "source_size": parsed["source_size"],
        "pack_metadata": {key: parsed[key] for key in ("format", "pack_type", "flags", "dependency_count", "file_count", "index_size", "timestamp_raw")},
        "table_count": len(tables),
        "table_families": sorted({item["table"] for item in tables}),
        "classification_counts": dict(sorted(category_counts.items())),
        "tables": sorted(tables, key=lambda item: (item["table"], item["internal_file"])),
        "non_db_entries": metadata,
        "evidence_status": "OBSERVED",
        "limitations": [
            "Table membership and file hashes are observed directly from the pack index.",
            "Row semantics are not decoded without pinned WH3 schemas and remain unverified.",
        ],
    }


def _iter_zip_files(path: str | Path) -> Iterable[tuple[str, bytes]]:
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            normalized = info.filename.replace("\\", "/")
            yield normalized, archive.read(info)


def _strip_common_root(names: list[str]) -> dict[str, str]:
    split = [name.split("/") for name in names]
    common = split[0][0] if split and all(parts and parts[0] == split[0][0] for parts in split) else None
    return {name: "/".join(name.split("/")[1:]) if common else name for name in names}


def audit_extracted_zip(path: str | Path, source_id: str) -> dict[str, Any]:
    files = list(_iter_zip_files(path))
    names = [name for name, _ in files]
    normalized_map = _strip_common_root(names)
    records: list[dict[str, Any]] = []
    table_families: set[str] = set()
    classification_counts: Counter[str] = Counter()
    script_records: list[dict[str, Any]] = []
    root_counts: Counter[str] = Counter()
    for original, blob in files:
        name = normalized_map[original]
        root = name.split("/", 1)[0] if "/" in name else name
        root_counts[root] += 1
        record = {"path": name, "size": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
        records.append(record)
        parts = name.split("/")
        if len(parts) >= 3 and parts[0] == "db":
            table = parts[1]
            table_families.add(table)
            classification_counts[classify_table(table)] += 1
        if name.lower().endswith(".lua"):
            text = blob.decode("utf-8", errors="replace")
            calls = {key: len(pattern.findall(text)) for key, pattern in SCRIPT_CALL_PATTERNS.items()}
            calls = {key: value for key, value in calls.items() if value}
            direct_mutations = sum(
                calls.get(key, 0)
                for key in (
                    "force_declare_war",
                    "force_make_peace",
                    "force_alliance",
                    "force_confederation",
                    "transfer_region",
                    "treasury_mod",
                    "create_force",
                    "apply_effect_bundle",
                    "spawn_character",
                    "teleport",
                )
            )
            script_records.append(
                {
                    "path": name,
                    "size": len(blob),
                    "sha256": record["sha256"],
                    "observed_calls": calls,
                    "direct_mutation_call_count": direct_mutations,
                    "classification": "SCRIPTED_STATE_INTERVENTION" if direct_mutations else "MECHANIC_OR_UI_SCRIPT",
                }
            )
    return {
        "schema_version": 1,
        "source_id": source_id,
        "source_kind": "EXTRACTED_AUDIT_ZIP",
        "source_sha256": file_digest(path),
        "source_size": Path(path).stat().st_size,
        "file_count": len(records),
        "root_counts": dict(sorted(root_counts.items())),
        "table_family_count": len(table_families),
        "table_families": sorted(table_families),
        "classification_counts": dict(sorted(classification_counts.items())),
        "script_count": len(script_records),
        "scripts": sorted(script_records, key=lambda item: item["path"]),
        "files": sorted(records, key=lambda item: item["path"]),
        "evidence_status": "OBSERVED",
        "limitations": [
            "Database row semantics require pinned WH3 schemas and are not inferred from binary payloads.",
            "Call-pattern classification identifies possible interventions, not proof that every path executes in a campaign.",
        ],
    }


def compare_audits(audits: list[dict[str, Any]]) -> dict[str, Any]:
    family_sets = {audit["source_id"]: set(audit.get("table_families", [])) for audit in audits}
    ids = sorted(family_sets)
    pairwise: list[dict[str, Any]] = []
    for index, left in enumerate(ids):
        for right in ids[index + 1 :]:
            overlap = sorted(family_sets[left] & family_sets[right])
            pairwise.append(
                {
                    "left": left,
                    "right": right,
                    "overlap_count": len(overlap),
                    "overlapping_table_families": overlap,
                }
            )
    all_sources = sorted(set.intersection(*(family_sets[source] for source in ids))) if ids else []
    owners: defaultdict[str, list[str]] = defaultdict(list)
    for source, families in family_sets.items():
        for family in families:
            owners[family].append(source)
    conflicts = [
        {"table_family": family, "sources": sorted(sources), "risk": "LOAD_ORDER_OR_ROW_CONFLICT_UNVERIFIED"}
        for family, sources in sorted(owners.items())
        if len(sources) > 1
    ]
    return {
        "schema_version": 1,
        "source_ids": ids,
        "pairwise": pairwise,
        "shared_by_all_count": len(all_sources),
        "shared_by_all": all_sources,
        "potential_conflicts": conflicts,
        "evidence_status": "SUPPORTED",
        "limitations": ["Shared table families indicate conflict potential, not row-level conflict proof."],
    }
