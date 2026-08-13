from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "NATIVE_CAI_DIRECTIONAL_CHURN_OWNER_KIT_V1"

OWNER_KIT_FILES: tuple[str, ...] = (
    "runtime_probe/tools/Prepare-NativeChurnCapture.ps1",
    "runtime_probe/tools/Collect-NativeChurnCapture.ps1",
    "runtime_probe/tools/prepare_native_churn_capture.py",
    "runtime_probe/tools/collect_native_churn_capture.py",
    "runtime_probe/tools/build_probe_packs.py",
    "runtime_probe/tools/verify_native_churn_profile.py",
    "runtime_probe/tools/verify_native_churn_capture.py",
    "runtime_probe/tools/compare_native_churn_captures.py",
    "runtime_probe/tools/capture_sfo_environment.py",
    "runtime_probe/tools/parse_probe_log.py",
    "runtime_probe/tools/run_native_visible_behavior.py",
    "runtime_probe/tools/run_native_visible_churn.py",
    "runtime_probe/manifests/shadow_pack.json",
    "runtime_probe/source/script/campaign/mod/transcendence_shadow_probe.lua",
    "runtime_probe/source/script/battle/mod/transcendence_battle_probe.lua",
    "synthetic_lab/transcendence_lab/__init__.py",
    "synthetic_lab/transcendence_lab/canonical.py",
    "synthetic_lab/transcendence_lab/native_visible_behavior.py",
    "synthetic_lab/transcendence_lab/native_churn.py",
)


def _sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def build_owner_kit(repo_root: Path, output: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    files: list[tuple[str, bytes]] = []
    records: list[dict[str, Any]] = []
    for relative in OWNER_KIT_FILES:
        path = repo_root / relative
        if not path.is_file():
            raise ValueError(f"owner-kit source file is missing: {relative}")
        blob = path.read_bytes()
        files.append((relative, blob))
        records.append({"path": relative, "size_bytes": len(blob), "sha256": _sha256_bytes(blob)})

    handoff = repo_root / "intake" / "NATIVE_CHURN_OWNER_HANDOFF_v0.2L.md"
    if not handoff.is_file():
        raise ValueError("owner handoff is missing")
    handoff_blob = handoff.read_bytes()
    files.append(("README_FIRST.md", handoff_blob))
    records.append({"path": "README_FIRST.md", "size_bytes": len(handoff_blob), "sha256": _sha256_bytes(handoff_blob)})

    manifest: dict[str, Any] = {
        "contract": CONTRACT,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "profile_sequence": "VANILLA_FIRST_SFO_CONDITIONAL_ON_ELIGIBLE_VANILLA_EXPOSURE",
        "contains_raw_pack_bytes": False,
        "contains_private_machine_paths": False,
        "files": sorted(records, key=lambda row: row["path"]),
    }
    manifest["manifest_digest"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    manifest_blob = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    files.append(("OWNER_KIT_MANIFEST.json", manifest_blob))

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, blob in sorted(files, key=lambda item: item[0]):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, blob)

    result = {
        "contract": CONTRACT,
        "output": str(output),
        "size_bytes": output.stat().st_size,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "entry_count": len(files),
        "manifest_digest": manifest["manifest_digest"],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic standalone v0.2L native-churn owner kit.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_owner_kit(args.repo_root, args.output.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
