from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))
from transcendence_lab.native_diagnostic_benchmark import benchmark_spec_digest
FILES = (
    "runtime_probe/tools/Prepare-NativeSFOBehaviorBenchmark.ps1",
    "runtime_probe/tools/Collect-NativeSFOBehaviorBenchmark.ps1",
    "runtime_probe/tools/prepare_native_sfo_behavior_benchmark.py",
    "runtime_probe/tools/collect_native_sfo_behavior_benchmark.py",
    "runtime_probe/tools/verify_native_behavior_sfo_profile.py",
    "runtime_probe/tools/prepare_native_diagnostic_capture.py",
    "runtime_probe/tools/verify_native_diagnostic_profile.py",
    "runtime_probe/tools/run_native_diagnostic_telemetry.py",
    "runtime_probe/tools/build_probe_packs.py",
    "runtime_probe/manifests/native_diagnostic_pack.json",
    "runtime_probe/source/script/campaign/mod/transcendence_native_diagnostic_probe.lua",
    "synthetic_lab/transcendence_lab/__init__.py",
    "synthetic_lab/transcendence_lab/canonical.py",
    "synthetic_lab/transcendence_lab/native_diagnostic.py",
    "synthetic_lab/transcendence_lab/native_diagnostic_study.py",
    "synthetic_lab/transcendence_lab/native_diagnostic_benchmark.py",
    "synthetic_lab/transcendence_lab/native_sfo_mechanistic.py",
    "research/native_cai/SFO_NATIVE_CAI_MECHANISTIC_REGISTRY_v0.2P_2026-08-04.json",
    "research/native_cai/NATIVE_CAI_ABLATION_CANDIDATE_REGISTRY_v0.2P_2026-08-04.json",
    "research/native_cai/SFO_POST_BENCHMARK_DECISION_TABLE_v0.2P_2026-08-04.json",
    "research/runtime_evidence/NATIVE_VANILLA_TERRITORIAL_CLUSTER_REFERENCE_v0.2P_2026-08-04.json",
    "research/runtime_evidence/NATIVE_BEHAVIOR_STUDY_VANILLA_REFERENCE_v0.2O_2026-08-03.json",
)
README = "intake/NATIVE_SFO_BEHAVIOR_BENCHMARK_OWNER_HANDOFF_v0.2P.md"


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def build(root: Path, output: Path) -> dict:
    rows = []
    blobs: list[tuple[str, bytes]] = []
    for relative in FILES:
        blob = (root / relative).read_bytes()
        blobs.append((relative, blob))
        rows.append({"path": relative, "size_bytes": len(blob), "sha256": sha(blob)})
    readme = (root / README).read_bytes()
    blobs.append(("README_FIRST.md", readme))
    rows.append({"path": "README_FIRST.md", "size_bytes": len(readme), "sha256": sha(readme)})
    manifest = {
        "contract": "NATIVE_CAI_SFO_BEHAVIOR_BENCHMARK_OWNER_KIT_V1",
        "study_version": "v0.2P",
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
        "benchmark_spec_digest": benchmark_spec_digest(),
        "sfo_workshop_id": "2792731173",
        "sfo_expected_sha256": "ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603",
        "contains_private_machine_paths": False,
        "contains_raw_game_or_workshop_pack_bytes": False,
        "files": sorted(rows, key=lambda row: row["path"]),
    }
    manifest["manifest_digest"] = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    blobs.append(("OWNER_KIT_MANIFEST.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, blob in sorted(blobs):
            if name.lower().endswith(".pack"):
                raise ValueError("owner kit must not contain pack bytes")
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, blob)
    if zipfile.ZipFile(output).testzip() is not None:
        raise ValueError("SFO behavior owner kit ZIP integrity failed")
    return {
        "output": str(output),
        "size_bytes": output.stat().st_size,
        "sha256": sha(output.read_bytes()),
        "entry_count": len(blobs),
        "manifest_digest": manifest["manifest_digest"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.repo_root.resolve(), args.output.resolve()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
