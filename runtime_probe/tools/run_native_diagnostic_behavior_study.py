from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))

from run_native_diagnostic_telemetry import parse_diagnostic_trace
from transcendence_lab.native_diagnostic_study import analyze_native_diagnostic_behavior_study


def run_study(log: Path) -> dict:
    trace = parse_diagnostic_trace(log)
    return analyze_native_diagnostic_behavior_study(trace)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen v0.2N research-only native CAI behavior study.")
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_study(args.log)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
