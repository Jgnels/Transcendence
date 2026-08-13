from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))

from run_native_diagnostic_telemetry import parse_diagnostic_trace
from transcendence_lab.canonical import digest
from transcendence_lab.native_diagnostic_benchmark import temporal_cluster_diagnostics
from transcendence_lab.native_sfo_mechanistic import (
    build_ablation_candidate_registry,
    build_sfo_mechanistic_registry,
    post_sfo_decision_table,
)

ROW_DIFF = REPO_ROOT / "research/native_cai/NATIVE_CAI_ROW_DIFFS_2026-08-02.json"
OUT_DIR = REPO_ROOT / "research/native_cai"
EVIDENCE_DIR = REPO_ROOT / "research/runtime_evidence"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_static() -> dict[str, Path]:
    row_diff = json.loads(ROW_DIFF.read_text(encoding="utf-8"))
    mechanism = build_sfo_mechanistic_registry(row_diff)
    ablation = build_ablation_candidate_registry(mechanism)
    decision = post_sfo_decision_table()
    paths = {
        "mechanism": OUT_DIR / "SFO_NATIVE_CAI_MECHANISTIC_REGISTRY_v0.2P_2026-08-04.json",
        "ablation": OUT_DIR / "NATIVE_CAI_ABLATION_CANDIDATE_REGISTRY_v0.2P_2026-08-04.json",
        "decision": OUT_DIR / "SFO_POST_BENCHMARK_DECISION_TABLE_v0.2P_2026-08-04.json",
    }
    write_json(paths["mechanism"], mechanism)
    write_json(paths["ablation"], ablation)
    write_json(paths["decision"], decision)
    return paths


def build_vanilla_cluster(bundle: Path) -> dict[str, Path]:
    bundle = bundle.resolve()
    source_sha = sha256(bundle)
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None:
            raise ValueError("vanilla behavior bundle ZIP integrity failure")
        name = "transcendence_native_diagnostic_log.txt"
        if name not in archive.namelist():
            raise ValueError(f"{name} missing from vanilla behavior bundle")
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / name
            log.write_bytes(archive.read(name))
            trace = parse_diagnostic_trace(log)
    cluster = temporal_cluster_diagnostics(trace, "territorial")
    source = {
        "filename": bundle.name,
        "sha256": source_sha,
        "zip_integrity": "PASS",
        "trace_contract": trace.get("contract"),
    }
    reference = {
        "contract": "NATIVE_CAI_VANILLA_TERRITORIAL_CLUSTER_REFERENCE_V1",
        "study_version": "v0.2P",
        "source_bundle": source,
        "cluster_diagnostics": cluster,
        "frozen_use": "DESCRIPTIVE_CLUSTER_SENSITIVITY_REFERENCE_FOR_FRESH_SFO_ONLY",
        "not_a_confidence_interval": True,
        "not_randomized_causal_baseline": True,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
    }
    reference["reference_digest"] = digest(reference)
    atlas = {
        "contract": "NATIVE_CAI_VANILLA_TERRITORIAL_REVERSAL_CAUSAL_ATLAS_V1",
        "study_version": "v0.2P",
        "source_bundle": source,
        "population": "TERRITORIAL",
        "candidate_window_count": len(cluster["candidate_windows"]),
        "candidate_windows": cluster["candidate_windows"],
        "interpretation": [
            "These are single stable-context battle-free reversal candidates from the hash-frozen vanilla cohort.",
            "No territorial force met the v0.2N repeated non-overlapping reversal criterion.",
            "The atlas is for causal review and matched-profile comparison; it is not a list of proven AI mistakes.",
        ],
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "application_eligible": False,
    }
    atlas["atlas_digest"] = digest(atlas)
    paths = {
        "cluster": EVIDENCE_DIR / "NATIVE_VANILLA_TERRITORIAL_CLUSTER_REFERENCE_v0.2P_2026-08-04.json",
        "atlas": EVIDENCE_DIR / "NATIVE_VANILLA_TERRITORIAL_REVERSAL_CAUSAL_ATLAS_v0.2P_2026-08-04.json",
    }
    write_json(paths["cluster"], reference)
    write_json(paths["atlas"], atlas)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vanilla-bundle", type=Path)
    args = parser.parse_args()
    paths = build_static()
    if args.vanilla_bundle:
        paths.update(build_vanilla_cluster(args.vanilla_bundle))
    result = {key: str(path.relative_to(REPO_ROOT)) for key, path in paths.items()}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
