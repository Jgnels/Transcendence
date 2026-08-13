from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_ROOT = REPO_ROOT / "synthetic_lab"
RUNTIME_TOOLS = REPO_ROOT / "runtime_probe" / "tools"
for item in (SYNTHETIC_ROOT, RUNTIME_TOOLS):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from transcendence_lab.canonical import read_json, write_json  # noqa: E402
from transcendence_lab.tactical_feasibility import (  # noqa: E402
    build_live_feasibility_capability_profile,
    build_trace_tactical_feasibility_envelope,
)
from transcendence_lab.tactical_feasibility_matrix import (  # noqa: E402
    run_tactical_feasibility_matrix,
)
from verify_action_feasibility_reexport import (  # noqa: E402
    verify_action_feasibility_reexport_zip,
)


def build(output_directory: Path) -> list[Path]:
    trace = read_json(SYNTHETIC_ROOT / "corpora" / "battle4_eilhart_trace_slices_v1.json")
    baseline = read_json(SYNTHETIC_ROOT / "scenarios" / "tactical_baseline_matrix_v0.1O.json")
    suite = read_json(SYNTHETIC_ROOT / "scenarios" / "tactical_feasibility_matrix_v0.1T.json")
    live = read_json(
        REPO_ROOT
        / "research"
        / "runtime_evidence"
        / "ACTION_AUTHORITY_LIVE_CAPTURE_ADJUDICATION_v0.1S.json"
    )
    profile = build_live_feasibility_capability_profile(live)
    battle4 = build_trace_tactical_feasibility_envelope(
        trace,
        capability_profile=profile,
    )
    matrix = run_tactical_feasibility_matrix(trace, baseline, suite)

    fixture_zip = REPO_ROOT / "runtime_probe" / "fixtures" / "action_feasibility_reexport_valid.zip"
    fixture_raw = REPO_ROOT / "runtime_probe" / "fixtures" / "action_authority_log_valid.txt"
    import hashlib

    fixture = verify_action_feasibility_reexport_zip(
        fixture_zip,
        expected_raw_log_sha256=hashlib.sha256(fixture_raw.read_bytes()).hexdigest(),
        expected_pack_sha256="a" * 64,
        expected_source_public_capture_sha256="b" * 64,
    )
    fixture["fixture_control"] = True
    fixture["result_digest"] = None
    fixture.pop("result_digest", None)
    from transcendence_lab.canonical import digest

    fixture["result_digest"] = digest(fixture)

    outputs = [
        (
            "ACTION_AUTHORITY_LIVE_FEASIBILITY_CAPABILITY_PROFILE_v0.1T.json",
            profile,
        ),
        (
            "BATTLE4_EILHART_TACTICAL_FEASIBILITY_ENVELOPE_v0.1T.json",
            battle4,
        ),
        (
            "TACTICAL_FEASIBILITY_MATRIX_REPORT_v0.1T.json",
            matrix,
        ),
        (
            "ACTION_FEASIBILITY_REEXPORT_FIXTURE_VERIFICATION_v0.1T.json",
            fixture,
        ),
    ]
    output_directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for filename, value in outputs:
        path = output_directory / filename
        write_json(path, value)
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0.1T tactical-feasibility artifacts")
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=REPO_ROOT / "research" / "runtime_evidence",
    )
    args = parser.parse_args()
    for path in build(args.output_directory):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
