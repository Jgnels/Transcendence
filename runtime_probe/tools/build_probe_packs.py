from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Iterable

PACK_MAGIC = b"PFH5"
DEFAULT_PACK_TYPE = 3


class ProbeBuildError(ValueError):
    pass


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def normalize_internal_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip("/")
    if not normalized or normalized.startswith("/") or ":" in normalized:
        raise ProbeBuildError(f"invalid internal path: {path!r}")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ProbeBuildError(f"unsafe internal path: {path!r}")
    if "\x00" in normalized:
        raise ProbeBuildError("internal path contains NUL")
    return normalized


def write_pfh5_pack(
    entries: Iterable[tuple[str, bytes]],
    destination: Path,
    *,
    pack_type: int = DEFAULT_PACK_TYPE,
    timestamp: int = 0,
) -> dict[str, object]:
    normalized: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for internal_path, blob in entries:
        safe_path = normalize_internal_path(internal_path)
        if safe_path in seen:
            raise ProbeBuildError(f"duplicate internal path: {safe_path}")
        seen.add(safe_path)
        normalized.append((safe_path, bytes(blob)))

    if not normalized:
        raise ProbeBuildError("a pack must contain at least one entry")

    normalized.sort(key=lambda item: item[0])
    index_parts: list[bytes] = []
    entry_records: list[dict[str, object]] = []
    for internal_path, blob in normalized:
        encoded_path = internal_path.replace("/", "\\").encode("utf-8")
        index_parts.append(struct.pack("<I", len(blob)) + b"\x00" + encoded_path + b"\x00")
        entry_records.append(
            {
                "path": internal_path,
                "size": len(blob),
                "sha256": sha256_bytes(blob),
                "compression_flag": 0,
            }
        )

    index = b"".join(index_parts)
    header = PACK_MAGIC + struct.pack(
        "<6I",
        int(pack_type),
        0,  # flags
        0,  # dependencies
        len(normalized),
        len(index),
        int(timestamp),
    )
    pack_blob = header + index + b"".join(blob for _, blob in normalized)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(pack_blob)

    return {
        "format": "PFH5",
        "pack_type": int(pack_type),
        "flags": 0,
        "dependency_count": 0,
        "file_count": len(normalized),
        "index_size": len(index),
        "timestamp_raw": int(timestamp),
        "pack_name": destination.name,
        "pack_size": len(pack_blob),
        "pack_sha256": sha256_bytes(pack_blob),
        "entries": entry_records,
    }


def load_manifest(repo_root: Path, manifest_path: Path) -> dict[str, object]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "pack_name",
        "pack_type",
        "deterministic_timestamp",
        "probe_kind",
        "save_mutation",
        "gameplay_mutation",
        "entries",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ProbeBuildError(f"manifest missing fields: {missing}")
    if data["schema_version"] != 1:
        raise ProbeBuildError("unsupported manifest schema")
    if not isinstance(data["entries"], list) or not data["entries"]:
        raise ProbeBuildError("manifest entries must be a non-empty list")
    for entry in data["entries"]:
        source = repo_root / entry["source"]
        if not source.is_file():
            raise ProbeBuildError(f"manifest source missing: {entry['source']}")
        normalize_internal_path(entry["internal_path"])
    return data


def build_manifest(repo_root: Path, manifest_path: Path, output_dir: Path) -> dict[str, object]:
    manifest = load_manifest(repo_root, manifest_path)
    entries: list[tuple[str, bytes]] = []
    for item in manifest["entries"]:
        source_path = repo_root / item["source"]
        entries.append((item["internal_path"], source_path.read_bytes()))

    output_path = output_dir / manifest["pack_name"]
    pack_record = write_pfh5_pack(
        entries,
        output_path,
        pack_type=manifest["pack_type"],
        timestamp=manifest["deterministic_timestamp"],
    )
    record = {
        "schema_version": 1,
        "probe_kind": manifest["probe_kind"],
        "save_mutation": bool(manifest["save_mutation"]),
        "gameplay_mutation": bool(manifest["gameplay_mutation"]),
        "manifest_path": manifest_path.relative_to(repo_root).as_posix(),
        **pack_record,
    }
    return record


def build_all(repo_root: Path, output_dir: Path) -> dict[str, object]:
    manifest_dir = repo_root / "runtime_probe" / "manifests"
    manifests = sorted(manifest_dir.glob("*_pack.json"))
    if not manifests:
        raise ProbeBuildError("no probe manifests found")

    output_dir.mkdir(parents=True, exist_ok=True)
    records = [build_manifest(repo_root, path, output_dir) for path in manifests]
    aggregate = {
        "schema_version": 1,
        "builder": "runtime_probe/tools/build_probe_packs.py",
        "deterministic": True,
        "packs": records,
    }
    aggregate["result_digest"] = sha256_bytes(canonical_json(aggregate))
    (output_dir / "probe_build_manifest.json").write_bytes(canonical_json(aggregate))
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic Transcendence WH3 probe packs.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_dir = (args.output or repo_root / "dist" / "runtime_probe").resolve()
    result = build_all(repo_root, output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
