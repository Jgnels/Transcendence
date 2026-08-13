from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_ROOT = REPO_ROOT / "synthetic_lab"
if str(SYNTHETIC_ROOT) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_ROOT))

from adjudicate_action_feasibility_semantics import (  # noqa: E402
    EXPECTED_SOURCE_ZIP_SHA256,
    adjudicate_action_feasibility_documents,
)
from transcendence_lab.tactical_feasibility import (  # noqa: E402
    build_semantic_feasibility_capability_profile,
    build_trace_tactical_feasibility_envelope,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build(output_dir: Path) -> dict[str, str]:
    evidence = REPO_ROOT / "research" / "runtime_evidence"
    windows_path = evidence / "ACTION_FEASIBILITY_WINDOWS_OBSERVED_v0.1U.json"
    manifest_path = evidence / "ACTION_FEASIBILITY_REEXPORT_MANIFEST_OBSERVED_v0.1U.json"
    windows = json.loads(windows_path.read_text(encoding="utf-8-sig"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    calibration = adjudicate_action_feasibility_documents(
        windows,
        manifest,
        source_zip_sha256=EXPECTED_SOURCE_ZIP_SHA256,
        windows_sha256=_sha256(windows_path),
        manifest_sha256=_sha256(manifest_path),
    )
    profile = build_semantic_feasibility_capability_profile(calibration)
    trace = json.loads(
        (REPO_ROOT / "synthetic_lab" / "corpora" / "battle4_eilhart_trace_slices_v1.json").read_text(
            encoding="utf-8"
        )
    )
    battle4 = build_trace_tactical_feasibility_envelope(trace, capability_profile=profile)

    outputs = {
        "ACTION_FEASIBILITY_SEMANTIC_CALIBRATION_v0.1U.json": calibration,
        "ACTION_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_v0.1U.json": profile,
        "BATTLE4_EILHART_TACTICAL_FEASIBILITY_ENVELOPE_v0.1U.json": battle4,
    }
    hashes: dict[str, str] = {}
    for name, value in outputs.items():
        path = output_dir / name
        _write(path, value)
        hashes[name] = _sha256(path)
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic v0.1U semantic feasibility artifacts")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "research" / "runtime_evidence")
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
