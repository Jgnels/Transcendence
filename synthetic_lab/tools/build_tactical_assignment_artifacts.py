from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

LAB_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LAB_ROOT.parent
sys.path.insert(0, str(LAB_ROOT))

from transcendence_lab.canonical import read_json
from transcendence_lab.tactical_assignment import build_trace_objective_assignments
from transcendence_lab.tactical_assignment_matrix import run_tactical_assignment_matrix


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build(output_directory: Path) -> list[Path]:
    trace = read_json(LAB_ROOT / "corpora" / "battle4_eilhart_trace_slices_v1.json")
    baseline_suite = read_json(
        LAB_ROOT / "scenarios" / "tactical_baseline_matrix_v0.1O.json"
    )
    assignment_suite = read_json(
        LAB_ROOT / "scenarios" / "tactical_assignment_matrix_v0.1P.json"
    )
    battle4 = build_trace_objective_assignments(trace)
    matrix = run_tactical_assignment_matrix(trace, baseline_suite, assignment_suite)
    outputs = [
        output_directory
        / "BATTLE4_EILHART_TACTICAL_OBJECTIVE_ASSIGNMENTS_v0.1P.json",
        output_directory / "TACTICAL_ASSIGNMENT_MATRIX_REPORT_v0.1P.json",
    ]
    _write(outputs[0], battle4)
    _write(outputs[1], matrix)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
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
