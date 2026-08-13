from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_ROOT = REPO_ROOT / "synthetic_lab"
if str(SYNTHETIC_ROOT) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_ROOT))

from transcendence_lab.canonical import read_json, write_json  # noqa: E402
from transcendence_lab.tactical_guarded import build_trace_guarded_action_packets  # noqa: E402
from transcendence_lab.tactical_guarded_matrix import run_tactical_guarded_matrix  # noqa: E402
from transcendence_lab.tactical_pipeline_audit import run_tactical_pipeline_audit  # noqa: E402
from transcendence_lab.tactical_reservation import build_trace_endpoint_reservations  # noqa: E402
from transcendence_lab.tactical_reservation_matrix import run_tactical_reservation_matrix  # noqa: E402


def build(output_directory: Path) -> list[Path]:
    trace = read_json(SYNTHETIC_ROOT / "corpora" / "battle4_eilhart_trace_slices_v1.json")
    baseline = read_json(SYNTHETIC_ROOT / "scenarios" / "tactical_baseline_matrix_v0.1O.json")
    feasibility_suite = read_json(SYNTHETIC_ROOT / "scenarios" / "tactical_feasibility_matrix_v0.1T.json")
    guarded_suite = read_json(SYNTHETIC_ROOT / "scenarios" / "tactical_guarded_action_matrix_v0.1V.json")
    reservation_suite = read_json(SYNTHETIC_ROOT / "scenarios" / "tactical_endpoint_reservation_matrix_v0.1W.json")
    pipeline_suite = read_json(SYNTHETIC_ROOT / "scenarios" / "tactical_pipeline_adversarial_scaling_v0.1X.json")
    semantic_profile = read_json(
        REPO_ROOT / "research" / "runtime_evidence" / "ACTION_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_v0.1U.json"
    )

    artifacts = {
        "BATTLE4_EILHART_GUARDED_ACTION_PACKETS_v0.1V.json": build_trace_guarded_action_packets(
            trace, capability_profile=semantic_profile
        ),
        "TACTICAL_GUARDED_ACTION_MATRIX_REPORT_v0.1V.json": run_tactical_guarded_matrix(
            trace, baseline, feasibility_suite, guarded_suite
        ),
        "BATTLE4_EILHART_ENDPOINT_RESERVATIONS_v0.1W.json": build_trace_endpoint_reservations(
            trace, capability_profile=semantic_profile
        ),
        "TACTICAL_ENDPOINT_RESERVATION_MATRIX_REPORT_v0.1W.json": run_tactical_reservation_matrix(
            reservation_suite
        ),
        "TACTICAL_PIPELINE_ADVERSARIAL_SCALING_REPORT_v0.1X.json": run_tactical_pipeline_audit(
            trace, baseline, feasibility_suite, pipeline_suite
        ),
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, value in artifacts.items():
        path = output_directory / name
        write_json(path, value)
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic v0.1V-v0.1X tactical artifacts")
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=REPO_ROOT / "research" / "runtime_evidence",
    )
    args = parser.parse_args()
    paths = build(args.output_directory)
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
