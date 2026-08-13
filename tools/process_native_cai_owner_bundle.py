from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

EXPECTED_SCHEMA_BLOB = "232216808ff5d38edd9e056c7828afdc1700d297"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode("ascii"))
    h.update(data)
    return h.hexdigest()


def safe_extract(zip_path: Path, destination: Path) -> None:
    # Windows Compress-Archive stores backslash path separators. Python's
    # zipfile on Linux treats them as literal filename characters, so normalize
    # explicitly while retaining path-traversal protection.
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            normalized = info.filename.replace("\\", "/")
            target = (destination / normalized).resolve()
            if destination.resolve() not in target.parents and target != destination.resolve():
                raise SystemExit(f"unsafe ZIP path: {info.filename}")
            if info.is_dir() or normalized.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def validate_sha_file(root: Path) -> dict:
    sums = root / "SHA256SUMS.txt"
    if not sums.exists():
        return {"status": "MISSING_SHA256SUMS", "checked": 0, "errors": []}
    errors = []
    checked = 0
    for line in sums.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        path = root / rel
        checked += 1
        if not path.is_file():
            errors.append({"path": rel, "error": "MISSING"})
            continue
        got = sha256(path)
        if got.lower() != digest.lower():
            errors.append({"path": rel, "error": "HASH_MISMATCH", "expected": digest, "actual": got})
    return {"status": "PASS" if not errors else "FAIL", "checked": checked, "errors": errors}


def find_one(root: Path, name: str) -> Path | None:
    hits = sorted(root.rglob(name))
    return hits[0] if hits else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and pre-process a private Transcendence Native-CAI owner input bundle.")
    parser.add_argument("input", type=Path, help="Owner-input ZIP or extracted bundle directory")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    temp: tempfile.TemporaryDirectory[str] | None = None
    if args.input.is_file() and args.input.suffix.lower() == ".zip":
        temp = tempfile.TemporaryDirectory(prefix="trans_native_cai_owner_")
        root = Path(temp.name)
        safe_extract(args.input, root)
    elif args.input.is_dir():
        root = args.input
    else:
        raise SystemExit("input must be a ZIP or directory")

    integrity = validate_sha_file(root)
    schema = find_one(root, "schema_wh3.ron")
    key_spec = find_one(root, "rpfm_table_key_spec.json")
    schema_meta = find_one(root, "rpfm_table_schema_metadata.json")
    exports = find_one(root, "exports")
    # rglob('exports') is not available through find_one for dirs; locate directly.
    export_dirs = sorted(p for p in root.rglob("exports") if p.is_dir())
    export_root = export_dirs[0] if export_dirs else None

    schema_record: dict = {"status": "NOT_FOUND"}
    if schema:
        blob = git_blob_sha1(schema)
        schema_record = {
            "status": "EXACT_PATCH_8_1" if blob == EXPECTED_SCHEMA_BLOB else "BLOB_MISMATCH",
            "path": str(schema.relative_to(root)),
            "bytes": schema.stat().st_size,
            "sha256": sha256(schema),
            "git_blob_sha1": blob,
            "expected_git_blob_sha1": EXPECTED_SCHEMA_BLOB,
        }

    key_record: dict = {"status": "NOT_FOUND"}
    if key_spec:
        raw = json.loads(key_spec.read_text(encoding="utf-8-sig"))
        tables = raw.get("tables", {}) if isinstance(raw, dict) else {}
        resolved = sorted(k for k, v in tables.items() if isinstance(v, dict) and v.get("primary_keys"))
        unresolved = sorted(k for k, v in tables.items() if not (isinstance(v, dict) and v.get("primary_keys")))
        key_record = {
            "status": "FOUND",
            "path": str(key_spec.relative_to(root)),
            "resolved_table_count": len(resolved),
            "unresolved_table_count": len(unresolved),
            "resolved_tables": resolved,
            "unresolved_tables": unresolved,
        }

    validation = {
        "schema_version": 1,
        "authority": "OFFLINE_RESEARCH_ONLY",
        "input": str(args.input),
        "bundle_sha256": sha256(args.input) if args.input.is_file() else None,
        "bundle_integrity": integrity,
        "schema": schema_record,
        "key_spec": key_record,
        "schema_metadata_present": bool(schema_meta),
        "exports_present": bool(export_root),
    }
    (args.out / "OWNER_INPUT_VALIDATION.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if integrity["status"] == "FAIL":
        print("FAIL owner bundle hash validation")
        return 2
    if not export_root:
        print("OWNER BUNDLE VALIDATED; no exports directory present, so row diff is blocked")
        return 0
    # RPFM ExtractPackedFiles may return exact binary DB payloads even when the
    # request asks for TSV. Detect text TSVs rather than trusting the helper label.
    tsv_files = list(export_root.rglob("*.tsv"))
    key_tables = {}
    if key_spec and key_spec.is_file():
        try:
            raw_keys = json.loads(key_spec.read_text(encoding="utf-8-sig"))
            key_tables = raw_keys.get("tables", {}) if isinstance(raw_keys, dict) else {}
        except Exception:
            key_tables = {}

    if tsv_files and key_tables:
        diff_out = args.out / "NATIVE_CAI_ROW_DIFF.json"
        cmd = [
            sys.executable,
            str(Path(__file__).with_name("native_cai_row_diff.py")),
            "--root", str(export_root),
            "--key-spec", str(key_spec),
            "--out", str(diff_out),
        ]
    else:
        # Binary fallback is intentionally narrow/fail-closed and only decodes
        # layouts proven by complete-file consumption. Unknown tables remain inventory-only.
        diff_out = args.out / "NATIVE_CAI_BINARY_ROW_DIFF.json"
        csv_out = args.out / "NATIVE_CAI_BINARY_ROW_DIFF.csv"
        cmd = [
            sys.executable,
            str(Path(__file__).with_name("native_cai_binary_row_diff.py")),
            "--root", str(export_root),
            "--out", str(diff_out),
            "--csv", str(csv_out),
        ]
    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    (args.out / "ROW_DIFF_STDOUT.txt").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        print(f"OWNER BUNDLE VALIDATED; row diff failed closed with code {completed.returncode}")
        return completed.returncode
    print(f"PASS owner bundle validation; row diff written to {diff_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
