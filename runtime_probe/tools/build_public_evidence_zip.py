from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

PRIVATE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/home/|/Users/|\\\\)")


class PublicEvidenceZipError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _walk_json_public(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in {
                "private_path",
                "absolute_path",
                "repository_path",
                "runtime_log_path",
                "checkpoint_root_private_path",
                "log_private_path",
            }:
                raise PublicEvidenceZipError(f"private field prohibited in public evidence: {path}.{key}")
            _walk_json_public(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_json_public(item, f"{path}[{index}]")
    elif isinstance(value, str) and PRIVATE_PATH_RE.search(value):
        raise PublicEvidenceZipError(f"private path-like value prohibited in public evidence: {path}")


def validate_source_file(path: Path) -> bytes:
    if not path.is_file():
        raise PublicEvidenceZipError(f"public evidence file is missing: {path}")
    data = path.read_bytes()
    if not data:
        raise PublicEvidenceZipError(f"public evidence file is empty: {path.name}")
    if not any(data):
        raise PublicEvidenceZipError(f"public evidence file is zero-filled: {path.name}")
    if path.suffix.lower() != ".json":
        raise PublicEvidenceZipError(f"only JSON is allowed in a public evidence bundle: {path.name}")
    try:
        value = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PublicEvidenceZipError(f"invalid public JSON: {path.name}: {error}") from error
    _walk_json_public(value)
    return data


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or not isinstance(value.get("files"), list):
        raise PublicEvidenceZipError("export manifest must contain a files list")
    if value.get("raw_log_included") is not False:
        raise PublicEvidenceZipError("public export manifest must explicitly exclude the raw log")
    if value.get("private_paths_included") is not False:
        raise PublicEvidenceZipError("public export manifest must explicitly exclude private paths")
    return value


def build_deterministic_zip(source_dir: Path, output: Path, manifest_path: Path) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    manifest_path = manifest_path.resolve()
    manifest = load_manifest(manifest_path)
    expected_records = manifest["files"]
    expected_names = [record.get("name") for record in expected_records if isinstance(record, dict)]
    if len(expected_names) != len(expected_records) or any(not isinstance(name, str) for name in expected_names):
        raise PublicEvidenceZipError("manifest file names are invalid")
    if len(expected_names) != len(set(expected_names)):
        raise PublicEvidenceZipError("manifest contains duplicate file names")

    actual_paths = sorted(path for path in source_dir.iterdir() if path.is_file())
    actual_names = [path.name for path in actual_paths]
    allowed = sorted(expected_names + [manifest_path.name])
    if actual_names != allowed:
        raise PublicEvidenceZipError(
            f"public bundle path set mismatch; expected {allowed}, found {actual_names}"
        )

    blobs: dict[str, bytes] = {}
    records_by_name = {record["name"]: record for record in expected_records}
    for path in actual_paths:
        data = validate_source_file(path)
        blobs[path.name] = data
        if path.name == manifest_path.name:
            continue
        record = records_by_name[path.name]
        if record.get("size_bytes") != len(data):
            raise PublicEvidenceZipError(f"manifest size mismatch: {path.name}")
        if record.get("sha256") != sha256_bytes(data):
            raise PublicEvidenceZipError(f"manifest hash mismatch: {path.name}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", prefix=f".{output.name}.", suffix=".tmp", dir=output.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in sorted(blobs):
                info = zipfile.ZipInfo(name)
                info.date_time = (1980, 1, 1, 0, 0, 0)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, blobs[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        # Windows rejects fsync on a read-only CRT descriptor with EBADF.
        # Reopen the completed temporary archive read/write solely for the
        # durability barrier; no archive bytes are changed.
        with temporary_path.open("r+b") as stream:
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)

    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
        if names != sorted(blobs):
            raise PublicEvidenceZipError("ZIP member order or path set mismatch")
        bad = archive.testzip()
        if bad is not None:
            raise PublicEvidenceZipError(f"ZIP CRC failure: {bad}")
        for name in names:
            data = archive.read(name)
            if data != blobs[name]:
                raise PublicEvidenceZipError(f"ZIP member bytes changed: {name}")
            if not any(data):
                raise PublicEvidenceZipError(f"ZIP member is zero-filled: {name}")

    return {
        "schema_version": 1,
        "status": "VERIFIED_PUBLIC_EVIDENCE_ZIP",
        "output_name": output.name,
        "size_bytes": output.stat().st_size,
        "sha256": sha256_path(output),
        "member_count": len(blobs),
        "members": [
            {"name": name, "size_bytes": len(blobs[name]), "sha256": sha256_bytes(blobs[name])}
            for name in sorted(blobs)
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and verify a deterministic path-free evidence ZIP.")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    result = build_deterministic_zip(args.source_dir, args.output, args.manifest)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
